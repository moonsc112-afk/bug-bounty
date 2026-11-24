# Lending-protocol money paths (beyond the oracle leg)

Once the platform patterns and the oracle survey are done, the money leaves through these six surfaces.
Review them in this order — the first two price collateral from values the oracle supplies, so they inherit
any proven manipulation and convert it into a direct transfer; the last (combined deposit+withdraw) is a
risk-boundary regression rather than a transfer.

## 1. Obligation/limit orders (execution is permissionless by design)

**Deployed status first: confirm the build actually carries the execute instruction.** Kamino's mainnet KLend
carries `SetObligationOrder` but no `ExecuteObligationOrder` (nor the master branch's execute handler), so the
path below is source-level there and its `premium/(1 − δ)` gain is unpayable until an execute instruction exists
on chain — run the inventory test from SKILL.md before spending a session on this surface.

`executor: Signer` on order execution means anyone may execute; the terms are the owner's (order + condition
set under `has_one = owner`) and the fill path is guarded by account matching (the borrow reserve's mint and
the destination must equal what the order recorded — that is the theft check for limit-order fills).

### Borrow orders (fixed-rate) — the live sibling, guards verified

The obligation-order path above can be dead on chain while its sibling is live: on Kamino's KLend the two
market flags that are actually set are the borrow-order pair, and `FillBorrowOrderV2` is the reachable
funds-moving instruction. Its fill is driven by the FILLER (`From<FillBorrowOrderAccounts> for
BorrowObligationLiquidity` sets `owner = payer`), i.e. a lender executes the borrow on the borrower's
obligation without the borrower's signature — by design for a standing order — so audit the bounds the
borrower pre-set and check each is enforced at fill time. Verified guard inventory:

- destination: `check_accounts_match_order` compares live accounts against the order's stored
  `debt_liquidity_mint` and `filled_debt_destination` (liquidity cannot be redirected);
- expiry: `current_timestamp > fillable_until_timestamp` rejects;
- amount: `BorrowSize::AtMost(remaining_debt_amount)` plus `min_borrow_order_fill_value` and
  `check_order_remaining_debt_value` for partial fills (dust fills rejected);
- rate: `reserve_constraint().check_satisfying(&reserve.config, ts)` rejects when
  `reserve_config.max_borrow_rate_bps() > order.max_borrow_rate_bps`. Note the comparison is against the
  reserve's CONFIGURED maximum, not the instantaneous rate — conservative, and sound in the safe direction:
  raising the configured maximum can only make fills harder, so a filler cannot open a loan above the
  borrower's ceiling;
- term and maturity: `is_term_satisfied(min_debt_term_seconds, reserve_config.get_debt_term_seconds())` plus
  `check_maturity_satisfying` against `seconds_until_maturity` (an order with no minimum term is refused
  outright against a maturing reserve);
- gating: `check_borrow_order_execution_enabled`; placement validated by `check_order_config_valid`.

Residual (not read): the body of `handler_rollover_fixed_term_borrow.rs` (permissionless payer; the borrower's
stored rollover config carries its own rate ceiling and minimum term, arithmetic uninspected) and the state of
`obligationBorrowRolloverConfigurationEnabled` / `MigrationToFixedExecutionEnabled`, whose bytes fall outside
the mapped flag block.

What to read: the pricing of the **collateral leg**. When the payout is computed from the obligation's
stored oracle values (`deposited_amount × settled_value / collateral.market_value_sf`), the executor is paid
at the oracle's own price — so a distortion δ of the collateral price buys `1/(1−δ)` more tokens for the same
settled value, and after the distortion unwinds the gain on the debt repaid is

    premium/(1 − δ) − 1        (premium = (1+penalty)(1+bonus))

| δ | premium 1.05 | true gain |
|---|---|---|
| 0 % | 1.05 | +5 % |
| 5 % | 1.05 | +10.5 % |
| 10 % | 1.05 | +16.7 % |
| 20 % | 1.05 | +31.3 % |

The owner's caps (bonus-range, and `max_bonus_rate = (1 − user_no_bf_ltv − penalty)/(1 + penalty)`) bound the
`premium` term only — never δ — which is exactly why the price term is the one worth checking. Two things
make it reachable: the freshness guard usually only requires the reserves and obligation to be refreshed **in
the current slot** (a swap-then-refresh transaction satisfies it), and an LTV-based order condition is
*satisfied by the same move* that depresses the collateral price.

## 2. Autodeleverage — two paths, only one of them needs the owner

**Individual** (`check_individual_autodeleverage_obligation`): the obligation must be marked with a target
LTV, `user_ltv > target_ltv` **at execution time**, and the margin-call period must have elapsed. The last
two are satisfied by the manipulative transaction itself when the timestamp is already old enough, so the
finding shape is "a target LTV below the liquidation threshold plus an aged timestamp", not "a liquidator
chose a bad price". The mark is market-owner-gated (`markObligationForDeleveraging` is signed by the market
owner), so this path alone is a governance risk, not an attacker lever.

**Market-wide** (`check_market_wide_autodeleverage_obligation`): needs **no mark and no consent** — it fires
when the reserve has `autodeleverage_enabled`, the market has it enabled, and the reserve's deposit limit
(collateral side) or borrow limit (debt side) is crossed. Its eligibility threshold is computed from TIME,
not from the reserve's risk parameters:

    eligible_ltv_threshold = 1.0 − (deleveraging_threshold_decrease_bps_per_day / 10_000) × days_since_grace

measured from **100 % LTV**, not from `liquidation_threshold_pct`, and with `saturating_sub` — i.e. **no
floor**: once the reduction exceeds 1 the threshold is 0 %, and then every obligation using that reserve on
either side satisfies `user_ltv >= threshold` however healthy it is by the reserve's own numbers. The clock
starts at the reserve's `*_limit_crossed_timestamp`, which a refresh clears only while the limit is *not*
crossed, and every liquidation refreshes the reserve first, so the state is fresh at execution. The caller's
bonus is `min_deleveraging_bonus_bps + bonus_increase_bps_per_day × days`, capped at
`min(max_liquidation_bonus_bps, 1 − no_bf_ltv)` — the caps are sound; the eligibility is what to attack.
Because repayment only LOWERS the victim's LTV while the threshold stays 0 %, the caller can repeat until
the position is dismantled.

Scan shape: read those six fields out of the reserve's `ReserveConfig` (live offsets in
references/klend-live-layout.md), intersect reserves with a running clock (timestamp ≠ 0) with the ones the
feature is enabled on, subtract the grace period, and compute the threshold per reserve. Confirm the
formula is the deployed one by grepping the .so for the path's own log phrase before quoting any threshold.
Between that number and a finding stand two pieces of evidence: the victim-side count (healthy obligations
on those reserves, from the obligation sweep) and an execution PoC that liquidates one healthy live position
— a revert refutes the claim, so build it before writing the report.

Two screening rules learned the hard way, both about not counting a position the deployed build will not
take: (a) the deployed build's own counter wins over stored aggregates, and the usual benign cause is a
completed repay, so byte-verify `hasDebt`, the occupancy of the borrow-slot region, and the stale flag on
every candidate before calling it a ghost; a cleared flag, empty slots, and `stale=1` describe the intended
post-repay state, where zero-value refresh, full withdrawal, and `ObligationBorrowsZero (6023)` are expected
behaviour; word any unattributed count as "positions carrying stored debt", never as victims; (b) the clock is
re-read at execution because a liquidation refreshes the reserve first, so a reserve that has fallen back
inside its limit carries a cleared timestamp — re-read the crossed timestamps at PoC time rather than
reusing a sweep, and treat a running clock as a condition that must hold *then*, not as a property of the
market; (c) a crossed limit has a SIDE — a deposit-limit clock fires on positions using the reserve as
collateral (wherever they borrow) and a borrow-limit clock fires on positions borrowing it, so scan the
matching side, and remember that a debt-free depositor population says nothing about the borrow side.

## 3. Elevation groups

Verdict `clear` requires citing the **four** paths where the group's LTV *and* liquidation threshold are
applied — borrow, deposit cap, refresh, withdraw — through one helper (`get_max_ltv_and_liquidation_threshold`
or equivalent); grep the helper's call sites and count them. Add: per-deposit membership enforcement, the single
debt reserve per group (`…HasAnotherDebtReserve`), and the per-reserve debt trackers decremented on full
withdraw. Because the group's thresholds stay binding after entry, a position cannot withdraw its way back to
base-LTV territory even if nothing auto-exits the group.

## 4. Flash-loan fees

Two things decide this surface. The fee must be **exclusive** (borrower owes principal + fee) — read the
fee-calculation mode, not the bps. And the strongest guard to look for is a **vault balance delta** check
after the transfer (`post_transfer_vault_balance_…`): if the handler verifies the vault moved by exactly the
expected delta, rounding direction cannot leak value (a floor/ceil slip fails the transaction instead). With
that present the row is `clear` on evidence, not on arithmetic.

## 5. CPI integrations (vaults, farms, callback programs)

Trace the CPI **target**. A raw `Instruction { program_id: x.key(), … }` is safe when the account itself is
pinned by a stored value: `#[account(address = state.stored_field)]`, or an address derived from an enum the
*user's own* record carries (`withdraw_ticket.progress_callback_type().program_address()`) — that pattern is
the fix to look for. The dangerous shape is an *unpinned* program account passed by the caller into
`invoke_signed` with the program's own PDA seeds: that is arbitrary CPI with the program's signature. Typed
`Program<'info, Farms>` = pinned; `farms::id()` in the instruction = pinned.

## 6. Combined deposit+withdraw handler — stale `initial_ltv` (source-confirmed, integration unproven)

A single transaction that deposits into one reserve and withdraws from another. Read the ORDER: the handler
snapshots `initial_ltv` from the obligation's STORED values, deposits, refreshes the obligation, withdraws, and
only then enforces `new_ltv > initial_ltv` -> `WorseLtvBlocked` plus `new_ltv >= new_unhealthy_ltv` ->
`WorseLtvThanUnhealthyLtv` (`post_deposit_and_withdraw_obligation_enforcements`). Since the snapshot predates
the refresh, a position whose stored values are stale (prices moved in the borrower's favour since the last
refresh) is withdrawn against a number that no longer describes it: the "net improving" rule passes on a
withdrawal that worsens the live position. The second gate is the floor, so the worst end state is just under
the liquidation threshold — a Low, not a fund loss.

Reproduce as an A/B on one live obligation: arm 1 multiplies only the four stored value fields (2208/2224/2240/
2256) so the stored LTV reads absurdly high while the live one is unchanged; arm 2 runs the identical amounts
on the pristine account. Expect arm 1 to pass and arm 2 to revert `WorseLtvBlocked`. Amount: withdraw ~10% of
the collateral's cTokens and deposit a token dust amount into a THIRD reserve (deposit and withdraw reserves
must differ).

Integration traps, partly solved. Rebuilding the account order from the IDL's nested
`depositAccounts`/`withdrawAccounts` type graph (not the source struct) yields 33 slots, and three wiring
facts that the source does not show: the two token programs plus the instruction sysvar sit at the END of
EACH side block (deposit block 11-13, withdraw block 25-27), the deposit's destination collateral is the
reserve's cToken supply vault rather than a user ATA, and a `None` farm slot still needs an account owned by
the farms program (the system program is rejected 3007). The obligation must ALSO be refreshed in the same
slot before the combined instruction — the handler's deposit leg rejects a stale obligation with
`ObligationStale` (6017) — while its own internal `refresh_obligation` then re-parses the remaining accounts
and answers `InvalidAccountInput` (6006) unless the count matches its own view exactly. That remaining-account
contract is the open problem: two reserves (deposit, borrow) trip the parse, one reserve gives the stale
revert, and extra trailing accounts are read as reserves for the deposit leg and panic
(`Remaining account is not a valid …Reserve`) when the last one is not a reserve. Mirror the deployed
revision's split of `ctx.remaining_accounts` (it passes `.last()` into the deposit leg and the slice into its
internal refresh) or lift the account list from a real on-chain `depositAndWithdraw` transaction instead of
tuning it by hand. Keep the substituted owner writable as well as signer.

### The stale-snapshot pattern has more than one call site

Do not stop at the combined handler. Search the whole operations module for `loan_to_value()` reads that
precede a refresh, then trace each into its enforcement helper. KLend's `lending_operations.rs` also
snapshots in `repay_and_withdraw_redeem` before repay/refresh and feeds `initial_ltv` into
`post_repay_and_withdraw_obligation_enforcements`, which repeats the same `new_ltv > initial_ltv` check
followed by the `new_ltv >= new_unhealthy_ltv` floor; `request_elevation_group` snapshots before its
refresh as well. Each call site is a separate SUSPECT with its own instruction and its own A/B PoC, not a
restatement of the combined-handler finding. Before spending PoC time, confirm the deployed build carries the
path is DISPATCHED, not merely present as text. A snake_case handler name and a distinctive enforcement
log phrase can both appear in a source-only build while the instruction is unreachable. Check in order: the
CamelCase `<Name>Instruction` dispatch string in the .so, the instruction in the official SDK IDL, and an
execution attempt with the discriminator derived from the IDL name. Derive snake_case from the IDL's
camelCase entry and the repo's `pub fn`, not from the handler filename: a wrong name produces `Custom(101)
InstructionFallbackNotFound` on a dispatched handler and fakes a source-only kill. Only a 101 after both
names agree, plus a missing dispatch name, justifies KILLED (not deployed) in the coverage ledger; do not
build the A/B PoC in that case.

Dispatch is necessary but not sufficient. `request_elevation_group` IS dispatched, yet its operation calls
`check_obligation_fully_refreshed_and_not_null(obligation, clock.slot)` BEFORE `loan_to_value()`, so its
snapshot is pinned to the current slot and cannot be stale. Kill that call site on the freshness guard,
not on dispatch; reserve A/B PoC time for snapshot sites with no same-slot refresh requirement.

## 7. Admin / emergency surface (market-owner gated)

`SocializeLoss`, `MarkObligationForDeleveraging`, and market/reserve config updates carry a
`lending_market_owner: Signer` plus `has_one = lending_market_owner` on the market account. Before auditing
their arithmetic as an attacker lever, read a sample of markets from chain (KLend layout: owner at bytes
16..48) and confirm the owners are distinct real addresses, never default, system, or null signers. Note
the guards that remain even for the owner: `socialize_loss` requires both reserve and obligation refreshed
in the current slot and rejects obligations with active deposits; `mark_obligation_for_deleveraging` bounds
the target LTV at 100 and uses a separate unmark sentinel. With those present, close the class on evidence
in the coverage ledger instead of continuing a source audit for an actor who cannot sign.

## Reporting

Give each surface a verdict with `file:line` citations a reviewer can re-run, and keep the arithmetic honest:
the position-side numbers (what collateral the payout buys) are measured from live accounts, while the cost
side (what producing δ costs in the underlying pool) is an argument from depth — label which is which.
