# Live-consumer survey: from a proven oracle bug to funds-at-risk

Goal: prove a proven oracle/price bug has a LIVE consumer path — enumerate production consumers of the buggy primitive, classify the protection each relies on, and quantify manipulation economics. One consumer whose guard derives from the same manipulable source as its price is the escalation from "conditional" to a live path.

## Step 1 — Reference graph (build from the protocol's synced config JSONs)
- refs(entry) = twap_source ∪ source_entry ∪ cap_entry ∪ floor_entry ∪ pyth_lazer_ema_source_entry ∪ source_entries[]
- BFS the closure of every consumer chain entry. Primitive types to flag as terminal:
  - spot: OrcaWhirlpoolAtoB/BtoA, RaydiumAmmV3AtoB/BtoA, MeteoraDlmmAtoB/BtoA
  - LP: JupiterLpFetch, AdrenaLp, FlashtradeLp, ExponentTranching
  - TotalMintSupply (reads raw `mint.supply`; the code's own listing comment says user-triggerable-issuance entries must be consumed ONLY through a TWAP — check for direct consumption)
- One hop is not enough: wrapper chains keep the primitive reachable; chained entries MULTIPLY their sources when consumed (a conversion chain).
- Resolve entry types per the CONSUMER's own feed — the same index is a different type in another feed (index collisions are common).

## Step 2 — Account layouts (Solana, little-endian; all anchor accounts carry an 8-byte discriminator)

### Lending reserve (dataSize 8+8616)
- Locate ScopeConfiguration by byte-searching the feed pubkey; at offset i: price_feed(32) @i, price_chain[u16;4] @i+32, twap_chain[u16;4] @i+40 (65535 = unset). mint @128:160.
- TokenInfo base = feed_offset − 80 (price_feed sits at TokenInfo-relative 80): name[32] @base, max_twap_divergence_bps u64 @base+56, max_age_price_seconds @base+64, max_age_twap_seconds @base+72.
- ReserveConfig block — locate it, never compute it blind: status u8 @config (ReserveStatus: 0=Active, 1=Obsolete, 2=Hidden), loan_to_value_pct @config+16, liquidation_threshold_pct @config+17. (Verified on the current layout: config base 4856, so LTV @4872, liq_thr @4873; treat absolute offsets as version-dependent.) PITFALL: a wrong config base reads LTV = 0 for EVERY reserve including blue-chips — the tell. Find it by scanning the data for the pattern (status ∈ {0,1,2}, LTV ∈ [40,90], liq_thr ≥ LTV) and CONFIRM against known referents (SOL/USDC reserves must read ~70-90% / 75-95%). Same discipline for any hand-derived offset: validate against an account whose value is publicly known before drawing conclusions from it.
- Activity fields: liquidity.total_available_amount u64 @224, liquidity.borrowed_amount_sf (scaled-fraction, /2^60) @232; collateral.mint_total_supply u64 @2608.

### Scope OraclePrices (8+28704; 512 entries)
- oracle_mappings pubkey @8:40. Entry i @ 40 + i*56: value u64, exp u64, last_updated_slot u64, unix_timestamp u64, generic[24].

### Scope OracleMappings (8+29696)
- price_types @8+16384+i (bit7 = frozen, low 7 bits = type); twap_src_or_ref_tol u16 @8+16896+2i; twap_enabled_bitmask @8+17920+i; ref_price u16 @8+18432+2i; generic[20] @8+19456+20i (NOT 18944 — the 512-byte bitmask array must be counted; verified against live account length 29704).
- For a TWAP-type entry the u16 is the source index; otherwise it is the ref-price tolerance in bps.

### Scope OracleTwaps (8+344128; locate via memcmp oracle_mappings @40)
- EmaTwap per entry @ 72 + i*672: last_update_slot u64, last_update_ts u64, ema1h u128, tracker_1h u64 (one bit per period/64 window).
- TWAP state lives on the SOURCE entry (the one with the enabled bitmask), NOT on the ScopeTwap reader entry — reader entries' own EmaTwap slots stay zero. Read tracker/EMA at twap_source index.

### Orca Whirlpool (653 B) — never trust remembered offsets
- Layout varies (Token-2022 pools differ from classic). Robust recipe: fetch the pool, then for every 32-byte window in data[8..620] fetch candidates with getMultipleAccounts (MAX 100 addresses per call — chunk) and identify by the returned account: mint (82 B classic / larger Token-2022; decimals @44, supply u64 @36), token account (165 B / 186 B Token-2022; amount u64 @64), pool config (owner = the Orca program).
- Pool depth = both vault balances (convert by mint decimals) — the manipulation-cost basis. Rough cost: a swap of ~5% of the shallow side moves the price ~5%.

## Step 3 — Consumer semantics: which guard actually protects the price
- price = price_chain value (RAW; multi-entry chains = product)
- twap = twap_chain value, fetched only if the config enables it; check is |price − twap| < twap-divergence-bps
- The twap requirement is a config scalar (twap-divergence bps > 0), NOT twap-chain presence. No requirement → twap flags set unconditionally → raw price used with no guard.
- Usage is flag-gated (ALL_CHECKS on borrow/liquidate): requirement present but no twap fetched leaves flags UNSET and blocks usage — safe direction, a config inconsistency to report as such.

| Class | Shape | Reading |
|---|---|---|
| F1 | DEX-derived price, no twap requirement (divergence bps = 0) | if the consumer is Active with LTV > 0 this is a direct-manipulation finding in its own right (no tracker bug, no lull needed) — rank it by LTV alongside F3, not as a mere observation; moot when Hidden or LTV = 0 |
| F2 | twap chain == price chain | degenerate self-check; moot when no requirement |
| F3 | twap required AND derived from the SAME manipulable source as the price | **escalation class for tracker/stateful bugs** — the bug moves price and guard together |
| F4 | DEX-derived price, twap from a separate aggregated source | partial protection; manipulation bounded by the tolerance |

Worked shape (generic): a lending consumer with price = most-recent-of(aggregated feed, DEX spot) and required twap = the 1h EMA of that SAME entry — the guard is exactly the EMA whose tracker a mod-window erase bug corrupts, so the aliased-injection primitive defeats the consumer's protection.

Monetization gate — check BEFORE naming the escalation target: consumer status = Active AND LTV > 0. Structural reachability without LTV (e.g. Active reserves whose chains match the bug's shape but whose LTV is 0 — not collateral) is NOT funds-at-risk; such reserves may still matter only as DEBT assets (manipulating a debt price shifts obligation health) — state that framing separately and rank it lower. LTV 0 is also the outcome to expect for stablecoin-ish assets, so verify per reserve rather than assuming.

## Step 4 — Listing status and the real bound, per candidate

Reachability is not payability: a covered instance is a scope condition, so classify every candidate before ranking any of them.

- Market of a reserve: bytes 32..64 of the Reserve account. Market owner: bytes 24..56 of the LendingMarket (version u64 @8, bump u64 @16). Markets of one protocol reuse a small set of authority wallets, so an owner seen nowhere else is a third-party/experimental signal.
- Listing test via the protocol's own config API (Kamino: `GET https://api.kamino.finance/v2/kamino-market` lists every market with `isVisibleInUi`; `GET /v2/kamino-market/<addr>` answers `{"error":"Market <addr> not found in config"}` for anything unlisted). Three distinct outcomes: listed + UI-visible (covered); listed but `isVisibleInUi:false` (not reachable through the normal UI workflow); absent (not covered at all).
- Clamp bound: `CappedFloored` with `cap_entry == floor_entry` serves THAT bound's value, so the served price is pinned exactly when the bound entry is not market-derived. Decode the bound's type from OracleMappings: 23 FixedPrice, 27 DiscountToMaturity, 29/48 PythLazer, 34-38 Chainlink* → deterministic or independent feeds (pinned, a genuine mitigation); a bound that is Orca/Raydium/Meteora/JupiterLpFetch → the band follows the market.
- Inner divergence: `MostRecentOf` (type 28; generic = source_entries[4] u16, max_divergence_bps u16, sources_max_age_s u64) returns the most recent source, but rejects the entry when the min and max source differ by more than `max_divergence_bps`, or when a source is older than `sources_max_age_s`. Read that bps number before claiming manipulability — it is often the binding cap, tighter than the lending-side twap tolerance. Observed live span across a lending protocol's reserves: 30 bps to 1200 bps.
- Publish the enumeration as a table (reserve | market | listing status | LTV | lending tolerance | price path | real protection). "Nine covered reserves at 50-88% LTV are held only by degenerate clamps onto deterministic feeds" is a class statement a reviewer can check; one tested reserve is an anecdote.
- A candidate-based fallback keeps the enumeration alive when the heavy `getProgramAccounts` scan is unavailable: `getMultipleAccounts` on the reserve keys already collected (~8624 B each, cheap to batch) plus the config API for market metadata.

## Step 4b — classify by the CLOSURE, never by the consumer chain's shape

A consumer row reading `price_chain=[X], twap_chain=[]` looks unprotected — and three such rows sitting in
listed, UI-visible markets at LTV 60-65 read as direct findings until the closure walk showed the served
value is pinned by a `CappedFloored` AT X whose cap and floor both point at a deterministic feed
(`DiscountToMaturity`). The consumer's own chain says nothing about clamps inside it, and the four class
labels in Step 3 are only a starting point.

Recipe: from each consumer chain entry, walk every referenced entry (source, twap_source, cap_entry,
floor_entry, sources[], pyth_lazer_ema_source_entry) resolving type + 20-byte generic from the CONSUMER's
own feed mappings, down to the terminals (DEX/LP spot, FixedPrice, DiscountToMaturity, PythLazer,
Chainlink*). Publish a small ASCII closure per candidate so a reviewer re-derives it, then call a reserve
manipulable — or not.

Two clamp shapes fall out of that walk, and both belong in the report:

- `cap == floor` onto a non-market feed ⇒ pinned; state it as a genuine mitigation (the local clamp demo
  — source +5.11 %, clamped entry 0.0000 % — is the one-table proof).
- **cap-only** (`floor = None`) over a deterministic source ⇒ harmless today, unbounded downside the
  moment a market-derived source goes under it (upside capped, downside free). Name it as a fix
  requirement ("require a floored, non-degenerate clamp wherever a market-derived source is reachable"),
  not as a finding.

## Step 5 — Live-verification discipline (severity claims)
- Re-parse every claimed consumer from LIVE accounts; record scan-vs-live drift (0 drift = the saved scan is faithful; report it as evidence).
- Re-run the consumer scan fresh each session (getProgramAccounts + dataSize) — a saved scan can miss reserves.
- Refresh cadence: compare the source entry's last_update ts vs now; minute-scale cadence means a gap-based attack needs a keeper incident — state that as the precondition, not as "live exploit".
- Quantify the required lull from the tracker geometry, then test it live: a mod-window alias needs Δt ≈ one full period ± one window (≈59-60 min for a 1h period), and the 1h tracker bitmap is readable on-chain — popcount + the positions of zero windows expose the real cadence (e.g. 57/64 coverage with only single-window holes = no lull exists in the last period). Historical lull frequency is NOT observable from a snapshot (no archive indexer) — say so explicitly instead of implying steady-state exploitability.
- Quote pool depth + the consumer's tolerance/ref bounds so severity has economic grounding.
