# Liquidation PoC against refresh-gated deployed bytecode

Depth behind the SKILL.md rules on `check_refresh`, the ghost-obligation screen and Token-2022 fixtures. Worked on KLend V1 (`liquidate_obligation_and_redeem_reserve_collateral`) with live mainnet accounts.

## The refresh contract is printed in reverse

A rejection logs `Required ix <N> <Kind>` with the `(pubkey, index_of_account_in_that_ix)` pairs the instruction must carry. Two properties decide whether building it succeeds:

- The checker maps `Required[0]` to `current_idx − 1`, `Required[1]` to `current_idx − 2`, and so on (`utils/refresh_ix_utils.rs`: `current_idx.checked_sub(i + 1)`). So the transaction order is the REVERSE of the printed order. Building the list in printed order fails 6051 at the gated instruction.
- `required_pre_ixs` is reversed but `required_post_ixs` is checked at `current_idx + i + 1`, and the farms refresh is pushed into BOTH. Every `RefreshFarmsForObligationForReserve` therefore appears twice: once in the pre sequence and once AFTER the gated instruction. A run whose last instruction is the liquidation aborts inside `load_instruction_at(current+1)` with a bare `IncorrectInstructionInPosition` (no `Required ix` dump, since that print only fires on a discriminator mismatch).

Correct tx shape for a KLend V1 liquidation of a farmed collateral (compute-budget first, then):

1. `refresh_reserve(collateral)`
2. `refresh_reserve(debt)`
3. `refresh_obligation` (remaining accounts = deposit reserves only)
4. `refresh_obligation_farms_for_reserve(collateral, mode 0)`
5. `liquidate_obligation_and_redeem_reserve_collateral`
6. `refresh_obligation_farms_for_reserve(collateral, mode 0)` again

The account-position pairs are asserted, so the farms instruction must keep `[crank_signer, obligation, market_authority, reserve, farm_state, farm_user, market, farms_program, rent, system]` (reserve at 3, obligation at 1, farm state at 4) and `refresh_obligation` must keep `[market, obligation, reserves…]` (obligation at 1). Warm the reserve in its own transaction first when the program demands a same-slot `last_update` (KLend does: `ReserveStale`).

## Token-2022 reserves

When the debt (or collateral) reserve's mint and vaults are owned by `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb`, pass T22 for that side's token-program slot and own the liquidator's source ATA with it.

`pt.add_program(name, id, None)` loads `tests/fixtures/{name}.so` and program-test warns-then-panics on a name it cannot recognise: a fixture called `token2022.so` fails with `Program file data not available`. Fetch the program's ELF and save it under a recognised name (`tokenzq.so`). The fixture must be the real deployed program: `getAccountInfo(T22)` → programdata address at `[4:36]` → `getAccountInfo(programdata)` → ELF at `data[45:]`.

## Derive field offsets from the SDK IDL, not from the repo struct

`npm view @kamino-finance/klend-sdk dist.tarball`, download, read `dist/idl/klend.json`. Account structs live under `accounts[]` (with their `type.fields`), named types under `types[]`; a `defined` type whose `kind` is `enum` is 1 byte. Walk the fields accumulating borsh sizes to get offsets, then validate two known ones before trusting the rest (a reserve's `(loanToValuePct, liquidationThresholdPct)` pair pinned the config base; `LastUpdate` is 16 bytes, not 8). Corroborate a scalar's meaning with a value the program itself stored elsewhere (`lowestReserveDepositLiquidationLtv` on an obligation equals the min threshold over its deposits).

**`dataSlice` offsets are relative to the slice.** A reader that keeps absolute offsets (deposit entries at 96 + i·136, then slices from 96) and forgets the base reads 96 bytes early: the values stay plausible, the deposit list is garbage, and every join silently misses. Either slice from offset 0 or subtract the slice base from every constant, and validate one row end to end against the full account before trusting a scan.

## Screen candidates through the build's own view before building

A `hasDebt = 0` obligation (offset 2287) with a non-zero stored debt field is usually the intended result of a completed repay, not a ghost defect: its refresh prints the deposit and no borrow line, and liquidation dies at `assert_obligation_liquidatable` with `ObligationBorrowsZero` (6023) after the whole refresh contract is satisfied. Byte-verify the borrow-slot region count and the stale flag before classifying it; a cleared flag, empty slots, and `stale=1` close the candidate as expected behaviour. Only an occupied borrow entry the current build cannot read survives to PoC.

Cheap screens, in order: GPA with `memcmp` on the `hasDebt` byte (`"1"` = 0x00 in base58) to list ghosts against `"2"` for the rest; count the class with a `dataSlice` over `depositedValueSf…unhealthyBorrowValueSf`; for a deleverage lane, GPA `memcmp` per deposit slot (offsets 96 + i·136, 8 calls) on each clock-running reserve and re-run the ghost screen on the hit list — a reserve whose depositors are all ghosts has no liquidatable victim whatever its threshold reads.

Read the borrow array from the IDL, not from an older empirical note: `borrows` starts at **1208** with **stride 200**, first field reserved 32 B, the reserve pubkey in the entry body — a `1184 / stride 128 / entry+24` reading belongs to a different drift and yields plausible-but-wrong keys. Count entries as `any(bytes)`, keep `hasDebt` @2287 as the build's own verdict, and cross-check a deposit list against the account's own `refresh_obligation` transaction rather than against offsets you re-derived.

Pick victims with ONE deposit. `refresh_obligation` demands exactly `deposit_count + borrow_count` remaining accounts in the obligation's deposit-SLOT order, and on a two-deposit ghost the deployed build passed its count check with the correct pair and still errored in the deposit iterator; a single-deposit ghost needs one account and reproduces 6023 cleanly. Screen `deposit_count` (non-empty slots at 96 + i·136) before choosing.

Do not quote class totals from a stored-debt scan: in one large population the apparent ghosts were repaid obligations whose aggregates were left behind, and deposits in sunset (status 1) reserves were benign too. Attribute every member by the byte-level check before quoting any count; only an occupied borrow entry the current build cannot read survives. On a confirmed repaid member the three-refresh, farmless path still reverts 6023, which is evidence that the failure is expected, not a defect witness. When a byte-level check retracts the class, rewrite the finding, coverage ledger, drafts, addenda, send guide, and checksum manifest in one pass and re-verify with `sha256sum -c`.

Sweep RPC mechanics: `getMultipleAccounts` takes ~50 keys per call, not 100; a `memcmp` `bytes` value is **base58** while account data comes back base64 (feeding base64 to `memcmp` yields `Base58DecodeError`); and a 429 clears by itself, so give the helper two-try backoff instead of re-planning the sweep. Keep every derived offset in one small shared module that the sweep, the PoC generator and the reader all import, so the three cannot drift apart.

## Harness hygiene

- Fixture names are all loaded through the same `tests/fixtures/{file}` literal: a generated variant that renames files must rename the literals too, and a fixture the PoC forgets to add surfaces as `AccountOwnedByWrongProgram` against the system program (an unset account), not as a missing file.
- The **clock source paths are file literals too**. A variant that reuses another target's clock derivation (`fixture_slot("…/ld_coll_reserve.bin")` while its own fixtures are `ld4_*`) sets the bank clock from the OLD accounts and the run dies with `MathOverflow` in `last_update.rs`, which reads like a broken toolchain. Substitute the clock paths with the fixture prefix in the same generator and assert the rendered file contains no stale prefix before building.
- When the class is defined by the deployed build's own counter, the complement member IS the control: same call, same account wiring, later error. Both arms must reach the bug's own assertion and diverge only there; a different instruction order, token program or farms shape between the two makes the runs incomparable.
- `warm reserve -> Ok` before the gated transaction, then the harness prints the obligation's before/after (`deposited`, `borrowed`, `unhealthy`) — quote those in the finding instead of hand-scaling prices.
- Keep the run's log and the PoC source hashed next to the finding.
- A sunset collateral carries a 0 `liquidation_threshold_pct`, so the handler rejects it with `CollateralNonLiquidatable` before the borrow assertion. Quote the pair (`hasDebt`, threshold) when classifying candidates and treat this as an additional expected block on a repaid member, not a second finding.
