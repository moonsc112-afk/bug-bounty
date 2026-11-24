# Scope feed internals: live protections, and building a feed inside program-test

Verified against the deployed Scope program (`HFn8GnPADiny6XqUoWE8uRPPxb29ikn4yTuPa9MF2fWJ`) and live
mainnet accounts, Nov 2026. Feed refresh entry point for the main feed's prices account is
`refresh_price_list`; the MAIN feed's prices account is `3t4JZcueEzTbVP6kLxXrL3VpWx45jDer4eqysweBchNH`
and its twaps account is `6L6vUts9tYqxHVUCEFVc2mzZw6yxMn8C6a44cp5ga7e9` (ISOLATED feed twaps:
`3NJYftD5sjVfxSnUdZ1wVML8f3aC6mp1CXCL6L7TnU8C`).

## Live clamp and divergence numbers (what decides severity)

`MostRecentOf` (oracle type 28) rejects its whole entry when the smallest and largest source differ by
more than its own `max_divergence_bps`, so that number is the binding cap against any source a swap
cannot move. Observed live: PRIME 30 bps, AUTO and Obligate 50, EUROP and OnRe-ONyc 100, Apyx 400,
JLP 500, STRCx 1200.

`CappedFloored` (type 33) generic data is borsh `{u16 source_entry, Option<u16> cap_entry,
Option<u16> floor_entry, u64 sources_max_age_s}` occupying 16 of the 20 generic bytes. When cap and
floor point at the *same* entry the served price is pinned to that bound, and every live bound decodes
to a non-market feed (ChainlinkExchangeRate, ChainlinkNAV, ChainlinkX, PythLazer, or
`DiscountToMaturity` for PT-ONyc). Concretely: entry 287 == entry 421 == 0.964815767 while the Orca
source underneath (entry 349) sits at 1.1647093; the same shape holds for 350/246. Nine covered,
UI-visible Kamino markets carry DEX-derived collateral at 50-88% LTV and all nine are held by one of
these two mechanisms — by configuration, not by code.

## Oracle type families: what a swap moves, what a transfer moves, what nothing moves

Take the enum from the program source (`states/oracle_type.rs`, values 0-53) and enumerate the whole
thing before classifying any population. Classifying with a partial type map is the failure mode: every
type missing from the map falls into whatever default the script picked, and a default of "movable"
produces a table that flatters the hypothesis (a first draft of exactly this check labelled Pyth-fed
reserves such as SOL as depth-bound, i.e. manipulable). The families:

| family | types | moved by |
|---|---|---|
| swap-movable market prices | 11 JupiterLpFetch, 13/14 Orca A/B, 15/16 Raydium A/B, 18/19 Meteora A/B, 31 AdrenaLp, 36 FlashtradeLp | trading against the pool; cost = pool depth, not configuration |
| transfer-movable balance/supply | 44 SplBalance, 45 StakedSolBalance, 46 TotalMintSupply | sending tokens to the account, or minting; Scope's own comment on TotalMintSupply requires this family to be consumed ONLY through a ScopeTwap |
| epoch- or CPI-set rates | 5 SplStake, 8 MsolStake, 25 JitoRestaking, 49 KlendCTokenExchangeRate, 50 Token2022Multiplier, 52 ExponentTranching | staking/restaking flows on an epoch cadence, a CPI into another program, or admin action — never a token transfer; their documented weakness is staleness at epoch boundaries, not manipulability |
| deterministic / independent | 23 FixedPrice, 26 Chainlink, 27 DiscountToMaturity, 29 PythLazer, 30 RedStone, 32 Securitize, 34/35/37/38 Chainlink variants, 48 PythLazerEMA | nothing a transaction can do |
| wrappers (recurse into their sources) | 12/40/41/42 ScopeTwap*, 28 MostRecentOf, 33 CappedFloored, 39 CappedMostRecentOf, 43 MultiplicationChain | inherit: MostRecentOf contributes its `max_divergence_bps` as the allowance, MultiplicationChain's relative moves ADD, and a CappedFloored whose cap == floor points at a deterministic bound is pinned to 0 |

Entry types worth naming from memory, for quick reads: 12 ScopeTwap1h, 13/14 OrcaWhirlpoolAtoB/BtoA,
23 FixedPrice, 27 DiscountToMaturity, 28 MostRecentOf, 33 CappedFloored, 43 MultiplicationChain,
52 ExponentTranching. Resolve an index in the feed the CONSUMER points to — indices collide across feeds.

## Two population checks to run before writing a severity claim

Both join against a position sweep (headroom per obligation), and both are cheap once the enum work
above is done.

1. **Configuration allowance vs live positions.** Reduce every reserve's chain to the largest distortion
a swap can produce (0 for pinned or deterministic; the bps allowance for a MostRecentOf band;
"depth-bound" for a raw DEX/LP top), then compare it with the smallest move that pushes a LIVE obligation
into liquidation range — computed on BOTH legs, because the sweep naturally covers only the collateral
side: a collateral price falling (`required_drop% = headroom_usd / deposit_value × 100`) and a borrowed
price rising (`required_up% = headroom_usd / debt_value × 100`), with positions already below the line
(headroom < 0, stored values) excluded from the "required move" ranking. On Kamino's 554-reserve
population this collapses to: pinned, or depth-bound, with JLP the single covered reserve whose
configuration admits any distortion — which is what makes a class claim provable instead of anecdotal.
2. **TWAP-aware family scan.** Walk every covered reserve's chain with a `guarded by a ScopeTwap
ancestor` flag and list which family members it reaches. In a covered set, zero consumers of the
transfer-movable family closes that lead outright (donation/mint angles die here cheaply), while the
epoch-rate families that ARE reached are harmless for a swap-based story — say so with the flag, so a
reviewer does not have to ask why 30 reserves "reach a balance oracle".

## Constructing a feed inside program-test (verified end to end)

1. Create the mappings/prices/twaps accounts as zeroed accounts owned by the Scope program, sizes
   51,200 / 32,256 / 2,560 bytes; `initialize` with the payer as signer.
2. `update_mapping_and_metadata` data: `{u32 entry_count, then per entry (u16 index, u32 update_count,
   {tag, payload}*)}`. Tags: 1 = MappingConfig (oracle type as u8, then 20 generic bytes),
   5 = MetadataName (string), 6 = MetadataMaxPriceAgeSlots (u64).
   Remaining accounts: **one per entry, in entry order** — the whirlpool account for an Orca entry,
   the Scope program id as a placeholder for TWAP and CappedFloored entries.
3. `refresh_price_list` takes the prices/mappings/twaps accounts, the instructions sysvar, then
   consumes per token what its handler needs: an Orca entry wants pool + mint_a + mint_b, placeholder
   entries want one account. A wrong total fails with **ScopeError 6006** ("the number of tokens is
   different from the number of received accounts").
4. EWMA state lives at the **source** entry index inside the twaps account, not at the twap entry's own
   index (sampling the twap entry returns zeros). Each entry is 672 bytes: slot @0, timestamp @8,
   ema_1h @16, tracker_1h @32, tracker_7d @40, ema_8h @48, ema_24h @64, tracker_8h @80,
   tracker_24h @88, ema_7d @96.
5. A healthy live 1h tracker reads **56-57 of 64 bits** at a 1-2 minute refresh cadence. The aliasing
   precondition is an update age inside **[3544, 3600) s** (period 3600 s, window 56.25 s); an age at
   or beyond the period takes the safe reset path, and a popcount collapse to 0 marks that reset.

## Demonstrating that a clamp holds

Feed three entries — `source` (a real Orca pool), `bound` (a second, undisturbed pool), and
`CappedFloored(source, cap == bound, floor == bound)` — then execute a real SPL swap against the
source pool and refresh all three. Measured result: the source moved **+5.11%** while the clamped
entry printed **0.0000%** movement, pinned to the bound. For how to run the swap itself (deployed
Whirlpool ELF, account order, argument shape, clock and tick-array traps), see the swap recipe in
SKILL.md.
