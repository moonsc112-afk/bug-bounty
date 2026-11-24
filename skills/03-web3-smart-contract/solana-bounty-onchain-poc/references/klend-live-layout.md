# KLend live layout, GPA shapes, and program fixtures

Everything here was measured on live mainnet accounts (Nov 2026). Use it instead of re-deriving.

## Program id, verified

`KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD` (note `1mQq`). A single wrong character here
(`1mMq`) produces clean empty `getProgramAccounts` results on every endpoint and invites a false
"the provider blocks this program" conclusion. Always compare the `owner` field of a known account
against your constant character by character.

The Kamino Lending programdata account is `9uSbGW1y9H5Av6H5TKxQ1wnFApSq2t3oEpfF2YfjDQGA`;
the Scope programdata is `DuKtB88SQGJbow5jxmUSwgJWmC7zma8mX3Nodz1Gsjs2`.

## Account sizes, discriminators, offsets

| account | size | 8-byte discriminator | market pubkey at |
|---|---|---|---|
| Reserve | 8,624 | `2bf2ccca1af73b7f` | 32 |
| Obligation | 3,344 | `a8ce8d6a584caca7` | 32 |

`OBLIGATION_SIZE = 3336` in `klend/programs/klend/src/utils/consts.rs` plus the discriminator = 3,344
on chain.

Obligation file offsets (discriminator included):

| field | offset |
|---|---|
| `tag` (u64) | 8 |
| `last_update` (16 B) | 16 |
| `lending_market` | 32 |
| `owner` | 64 |
| `deposits[8]` | 96 + 136·i (validated: a live deposit reserve landed at @232, slot 1) |
| deposit `market_value_sf` | entry + 40 |
| `deposited_value_sf` | 1,192 |
| borrow entries[8] | 1,184 + 128·i; the borrow's reserve pubkey at entry **+24** (settled by a whole-body ownership scan, not by field guesses) |
| `borrow_factor_adjusted_debt_value_sf` | 2,208 |
| `borrowed_assets_market_value_sf` | 2,224 |
| `allowed_borrow_value_sf` | 2,240 |
| `unhealthy_borrow_value_sf` | 2,256 |

The borrow array resisted field-position guesses: probing the entry head and +32/+48/+64/+80/+96 all failed, because bytes 0..24 of an entry are a `LastUpdate` plus rate/amount data that pre-decode into plausible-but-nonexistent pubkeys, and the reserve pubkey actually sits at **entry+24**. Settle such an offset with a whole-body ownership scan — enumerate every 8-aligned 32-byte window, batch them through `getMultipleAccounts`, keep the windows that resolve to lender-owned accounts — which named a $48M obligation's debt reserve in one pass. Independently, resolve the debt reserve from the obligation's own `refresh_obligation` transaction (remaining accounts = deposits then borrows, in the deployed build's counting order) — and treat that count as authoritative over the stored aggregate: a stored non-zero debt with `borrow_count=0` from the program means no liquidatable debt, so screen candidates before building a liquidation PoC. A `0xff` byte at the head of a borrow region is an invalidated/foreign-format entry marker — a tell of layout drift between builds, not an empty slot.

Reserve offsets (account discriminator included): `last_update.slot` sits at **16** (offset 8 is `version`, a u64 reading 2, so reading the slot at 8 yields a nonsense clock), then `mint` 128, `supply_vault` 160, `fee_vault` 192,
`total_available_amount` 224, `borrowed_amount_sf` 232, `price` (u128, 2^60 fixed point) 248,
limit-crossed timestamps 280 (deposit) and 288 (borrow); account 8,624 B = 8 B discriminator + 8,616 B
struct. `ReserveConfig` sits at **4,856**, with these verified relative offsets: `status` +0,
`min_deleveraging_bonus_bps` +4, `protocol_order_execution_fee_pct` +13, `loan_to_value_pct` +16,
`liquidation_threshold_pct` +17, `min_liquidation_bonus_bps` +18, `max_liquidation_bonus_bps` +20,
`deleveraging_margin_call_period_secs` +24, `deleveraging_threshold_decrease_bps_per_day` +32,
`deposit_limit` +160, `borrow_limit` +168, `autodeleverage_enabled` +646,
`deleveraging_bonus_increase_bps_per_day` +912.

**How that base was found (reuse when a struct walker drifts).** A text walk of the source gives relative
offsets reliably but mis-sizes nested structs, so absolute bases drift — reading a nested `LastUpdate` as
8 B instead of 16 shifted every later field by 8 and put `mint` at 120 instead of 128. Calibrate against a
value pair that is unique and self-describing: scanning a live reserve for the byte pair
`(loan_to_value_pct, liquidation_threshold_pct) = (85, 87)` hit exactly one offset, 4,872, fixing the config
base at 4,856 (a 16-byte pair at +16 of a 16-aligned base is not a coincidence). Then cross-check with
values the deployed program enforced itself and with population plausibility: on the USD1 reserve the bonus
range read 200/500 bps (matching a divergence cap derived independently), limits read 1e12, and across all
reserves the deleveraging rate distribution came out 24/50/100/7200 bps/day against grace periods of
0/86400/259200/345600/604800 s.

SBF alignment is 8, not 16, so u128 fields inside `repr(C)` account structs take no extra padding —
which is why hand-computing offsets from the source on a host gives the wrong answer for any struct
whose u128 follows a u64.

**Calibration method (reuse this).** Derive the same quantity twice and match: Σ(deposit market
value × the reserve's liquidation threshold) from the deposits and Reserve accounts gave
17,022.3826 for one live position, and offset 2,256 held exactly 17,022.3826. Neighbour fields then
confirmed the interpretation by their required ordering (adjusted debt 7,961.78 ≥ debt 7,945.73;
unhealthy 17,022.38 ≥ allowed 16,809.60).

## RPC shapes on Helius

- `getProgramAccounts` — 10 credits a call. Works, including on programs with a million accounts
  (Whirlpool returned 1,186,917). Programs that are genuinely too large are refused with
  `Too many accounts requested (Large number of pubkeys)`; an empty list means "nothing matched".
- `getProgramAccountsV2` — 1 credit a call, paginated. `limit` (1..10,000) and `paginationKey` are
  TOP-LEVEL config fields; putting them inside `{"pagination": {...}}` is silently ignored (default
  1,000-account page, cursor echoed back). Request shape: provider OpenAPI at
  `https://www.helius.dev/openapi/rpc-http.json`.
- Sweep pattern that works: one paginated query per market, filtering
  `{"dataSize": 3344}` + `{"memcmp": {"offset": 32, "bytes": <market>}}`. All 52 markets of Kamino's
  own config yield 133,910 obligations (65,034 UI-visible) against 642 reserves; a global unfiltered
  call would return ~602k accounts and is not worth paying for.
- When paging with `dataSlice`, the slice must cover the deepest field you read. Reading past the end of
  a slice returns **zeros, not an error**: a 2,240-byte slice silently hid `unhealthy_borrow_value_sf`
  at 2,256 and every parsed obligation was discarded as debt-free. Use at least 2,272 bytes (2,304 for
  margin). The tell was a run that reported 133,904 obligations found but zero rows parsed.

## Program fixtures

A fixture fetched from the programdata account is the account **minus its 45-byte loader header**
(`ProgramData`: 4-byte enum + 8-byte slot + 1-byte option tag + 32-byte upgrade authority).
Programdata accounts are allocated at exactly 10,485,760 bytes (10 MiB) with a zero tail, so an image
of 10,485,715 bytes is complete, not truncated. Verify by hashing `account_data[45:]` against the
fixture — Kamino Lending (`6482390f…`), Scope (`0d4a3bcd…`) and Whirlpool (`c422b22f…`) all match
their live accounts.

## Sweeping positions for exposure (the severity gate)

Query shape: one paginated `getProgramAccountsV2` per market, filtered `{"dataSize": 3344}` +
`{"memcmp": {"offset": 32, "bytes": <market>}}`, plus one `dataSize 8624` call for all reserves.
Then compute, per obligation, `headroom = (unhealthy − borrowed_assets_market_value) / unhealthy`
(offsets 2,256 / 2,224) and, per deposit, `required_drop = headroom_usd / deposit_value` — the price
fall on that deposit reserve which would consume the headroom. Aggregate per reserve: the number of
positions and the DEBT that becomes liquidatable at each threshold (0.5 %, 1 %, 2 %, 5 %). Join each
reserve with its price-protection class (clamp bound vs `MostRecentOf` divergence vs non-market feed)
and keep only reserves a manipulation you have proven can actually move.

The gate that decides the rating: compare the cost of producing the required drop (pool depth — a
few percent of the shallow side per percent of price for a DEX pool; the whole NAV of a perps/LP
book) against the payoff (liquidator bonus, typically 5-10 % of the debt, or the extra borrowing
capacity the inflated price unlocks). Real mechanism + unreachable-at-a-profit = High, and quoting
both sides is what makes the rating credible.

Reference numbers from the live sweep (Nov 2026), useful as a sanity baseline: 133,903 obligations
across the 52 configured markets, 102,518 rows parsed, 55,186 carrying debt against 642 reserves;
headroom median 29.4 %, 8,304 rows already below their own stored unhealthy line, 1,294 within 5 %.
Across all reserves a 0.5 % drop reaches 62 positions / $366k of debt and a 5 % drop 1,601 / $80.1M —
but those totals are dominated by Pyth/Chainlink-fed reserves no swap can move. Of the 22 reserves
whose price path can reach a DEX or LP feed, exactly one carried live positions close enough to
matter (JLP, JLP Market, LTV 84 %): 1,932 positions, $30.18M collateral, smallest required drop
0.388 %, and the 5 % divergence band reaches $743,906 of debt. Publishing that boundary is what keeps
the severity claim honest instead of asserting "live funds at risk" or hiding the exposure entirely.

Quote the program's own computed values where available (a `refresh_obligation` log prints each entry's amount and USD value) — a sweep figure that disagrees with them by an order of magnitude means the hand-scaled price math is wrong, and the program's number is the one to publish.

Limits to state with any such table: stored obligation values are snapshots (they move only when
someone refreshes the position), and an internal consistency check is worth reporting — for this run,
93.5 % of rows had the borrow-entry sum within 2 % of the stored debt field.
