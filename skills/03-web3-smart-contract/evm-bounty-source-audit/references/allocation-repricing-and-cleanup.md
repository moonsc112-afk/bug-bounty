# Allocation repricing, cleanup reachability, host quirks (Klima v2 session)

## Symmetric gating of price-stake mutations (the H2 pattern)
- When quotes price against a staked/allocated balance, enumerate every DECREASE vs INCREASE path of that balance and diff their guards (rate limiter / KYC / maturity / status).
- A decrease path missing the increase path's gates reprices quotes instantly AND reversibly. Klima v2: `deallocateKvcm` had none of `allocateKvcm`'s whenVerified/maturity guards and never notified the rate limiter; a pre-existing holder dropped 76.5% of the Wind class allocation, retired 2,500 t at 76.77% below the exact formula price (binary-search exact), then restored the allocation EXACTLY — zero cost, fully reversible. Bounty category: "pricing manipulation".
- Reachability bound to state explicitly: outsiders cannot manufacture the drop (allocate->deallocate nets zero; owner fixed at mint; lock NFT non-transferable) — the actor must be a pre-existing large allocation holder or a cohort exit. Triage will penalize overclaiming this.
- Fuzz the mechanism with invariants: per-class conservation (class total == baseline + ghost deltas of your ops), quote monotonicity in the input, auth-zero (non-owner deallocate count == 0), getter consistency.

## Cleanup/settlement reachability proof
- Slither `dead-code` + a repo-wide grep of the function name proves a cleanup/settlement path never runs in the revision you hold; combine with the deployed-revision byte-length pin before writing it down (dead code only matters if deployed == source).
- Klima case: `RollUpdateFacet._settleExpiringMaturityRoll` (sole caller of `cleanUpAllocationsForMaturity`) is dead -> expired-maturity allocations are never cleaned (stale pricing; the view-layer lag compensation steps at rollovers).

## Host quirks (Windows / git-bash, this machine)
- A Foundry fork-suite `--match-path` run can print ALL suite results then never exit (observed once): judge completion from the log content + an end marker you append yourself, not from process liveness; prefer per-file commands; kill a leftover hung forge with `taskkill /PID <pid> /F` (`//PID` is rejected in git-bash).
- git-bash-only tools are not spawnable from Windows Python (`sha256sum` -> WinError 5): hash/verify manifests in pure Python or run them through the bash shell.
- Blockscout v1 logs (`?module=logs&action=getLogs&address=&topic0=&page=&offset=`) work same-origin from a browser on base.blockscout.com (direct curl stays CF-blocked). A topic0 computed from a guessed ABI can silently return ZERO rows while the deployed event uses a different topic0 — when a filter looks empty, pull unfiltered and histogram `topics[0]`.
