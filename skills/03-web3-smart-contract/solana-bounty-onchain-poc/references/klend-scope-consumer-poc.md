# KLend (consumer) PoC against a manipulated Scope price

Verified end-to-end on deployed bytecode (Nov 2026): deposit -> refresh -> borrow, differential
manipulated vs honest price. Companion to the scope-side PoC recipe in SKILL.md.

## Step 0 - NEVER trust hand-computed account offsets: derive them empirically

Most offset bugs are silent (a wrong LTV offset reads 0 and looks like "no config"). Recipe:

1. Take one real account (e.g. a reserve). Enumerate every 8-aligned 32-byte window.
2. Batch them through `getMultipleAccounts` (100/call) and keep the windows that resolve to an
existing account; print its dataSize + owner.
   Mint -> 82 B Tokenkeg; token vault -> 165 B Tokenkeg; scope feed -> 28712 B owned by the scope
   program; lending market / reserve / obligation -> owned by KLend. That labels the layout.
3. Cross-check scalar fields against a reserve whose values are known-good (SOL/USDC LTV 70-90 %).

The two offset sets that cost hours here (both WRONG in the source-of-truth table):
`lending_market` is at 32 (Reserve LastUpdate = 24 B), and the collateral mint/supply are at
2560/2600 (not 2576/2616). A `has_one = lending_market` failure prints the value the program
really read - use it to locate the true field.

## Reserve layout (KLend, dataSize 8624, source of truth = the window scan)

| field | off | | field | off |
|---|---|---|---|---|
| lending_market | 32 | | collateral mint | 2560 |
| farm_collateral | 64 | | collateral total_supply | 2592 |
| farm_debt | 96 | | collateral supply_vault | 2600 |
| liquidity mint | 128 | | ReserveConfig base | 4856 |
| liquidity supply_vault | 160 | | status | 4856 |
| liquidity fee_vault | 192 | | loan_to_value_pct | 4872 |
| total_available | 224 | | liquidation_threshold_pct | 4873 |
| borrowed_amount_sf | 232 | | borrow_factor_pct | 5008 |
| market_price_sf (u128, /2^60) | 248 | | deposit_limit | 5016 |
| market_price_last_updated_ts | 264 | | borrow_limit | 5024 |
| mint_decimals | 272 | | TokenInfo base | 5032 |
| token_program | 408 | | max_twap_divergence_bps | 5088 |
| | | | max_age_price / max_age_twap | 5096 / 5104 |
| | | | scope price_feed | 5112 |
| | | | scope price_chain / twap_chain | 5144 / 5152 |
| | | | switchboard agg / twap | 5160 / 5192 |
| | | | pyth price | 5224 |

TokenInfo NULL_PUBKEY sentinel = `nu11111111111111111111111111111111111111111` (a *disabled*
oracle), distinct from Pubkey::default(). `is_enabled()` = "not default AND not NULL_PUBKEY".

Obligation (zero-copy, size 3336+8): tag@8, last_update@16 (**16 B**, unlike the Reserve's 24 B),
lending_market@32, owner@64, deposits[8]@96 (136 B each: deposit_reserve@96,
deposited_amount@128, market_value_sf@136). Deposits are cTokens; `refresh_obligation`
recomputes the values from the reserve's exchange rate and stored market price, so seeding
`{deposit_reserve, deposited_amount}` is enough to fabricate a funded obligation.

## Choosing a market pair (the setup that blocks most attempts)

- **Farms**: `farm_collateral`/`farm_debt` != default => that path's `check_refresh_ixs` ALSO
  requires RefreshFarms pre+post ix, i.e. the farms program + user-state PDAs. Pick a reserve with
  both farm fields default (295/554 have a farm) or the deposit/borrow tx will not validate.
- **Limits**: `deposit_limit == 0` and `borrow_limit == 0` mean *closed* (many fresh isolated
  markets are empty like this). Check both before designing amounts.
- **Pyth**: if `pyth_configuration.price` is enabled the refresh REQUIRES that exact pyth account
  (key match only; a dump of the real account is enough - the parse fails and the scope price wins).
  Switchboard configs behave the same; a *disabled* config requires `None` (pass the program id).
- Amounts: the borrow must be <= the borrow reserve's idle liquidity while the *true-price* limit
  is below it, or the control's rejection is ambiguous (liquidity vs LTV).

## Transaction pipelines (anchor `check_refresh_ixs` introspection)

```
deposit : [refresh_reserve(coll), refresh_obligation, deposit_reserve_liquidity_and_obligation_collateral(amount)]
borrow  : [refresh_reserve(coll), refresh_reserve(borrow), refresh_obligation, borrow_obligation_liquidity(amount)]
          + pass the collateral reserve as a REMAINING account of both refresh_obligation and borrow
```
Rule: the ix checked at `current_idx-1` is the FIRST required pre-ix after the internal reverse,
so RefreshObligation must sit IMMEDIATELY before the borrow and RefreshReserve(borrow_reserve)
exactly before that (its account 0 must be the borrow reserve). Extra refreshes earlier are fine.
`borrow_obligation_liquidity` wants RefreshReserve written LAST in its RefreshObligation requirement;
an extra coll refresh at idx-3 is unchecked and harmless (and it is what pushes the manipulated price
into the collateral reserve before the obligation is valued).

## Harness pitfalls (anchor client conventions)

- owner == fee_payer on the same pubkey => the compiler DEDUPES the accounts and the program
  receives one fewer account => `InstructionDidNotDeserialize` (102). Use distinct keypairs.
- `Transaction::sign` fails with `KeypairPubkeyMismatch` if you pass a keypair that is NOT in the
  message; pass exactly the required signers per tx (a refresh-only tx needs the payer only).
- Anchor reads accounts POSITIONALLY from the compiled message (payer first, then metas regrouped by
  signer/writable), so hand-built ixs are fragile for `init_*`; for a PoC the obligation can be
  seeded as zero-copy state (correct discriminator = sha256("account:Obligation")[..8] + owner +
  lending_market) and the following deposit/borrow are fully real. Declare the substitution.
- Price fixtures: write the target entry's `value`/`exp` AND a fresh `slot`/`ts` on every entry you
  touch (`max_age_slot` ~165, `max_age_s` 180-600). Pin the Clock so that the reserve's stored
  `market_price_last_updated_ts` is old enough to trip `is_price_refresh_needed`
  (= max_age_price_seconds * market.price_refresh_trigger_to_max_age_pct / 100) - otherwise the
  program keeps its old stored price and the manipulation never enters.
- Evidence to print: the program's own refresh log (`Token: X Price: ...`), the obligation's
  collateral value, and the borrow rejection text (`Borrow value A cannot exceed maximum borrow
  value B`). Those three lines are the whole finding; B = collateral_value x LTV proves the ratio.

## Live-mitigation gate: degenerate CappedFloored clamps

Before claiming a DEX-derived reserve price is manipulable, resolve the entries it feeds and check
for `CappedFloored` where `cap_entry == floor_entry` (or bounds that already contain the source):
deployed example - PT-ONyc-10JAN27 price 287 = clamp(src 349 = 1.1648, cap 421 = 0.9648,
floor 421 = 0.9648) -> the served price stays 0.9648 no matter what the Orca source does. Same for
ONyc(350), AUTO(451), PST(353). This is why a proven manipulation primitive can still be
non-monetizable: report the clamp as the live mitigation instead of inflating severity.
