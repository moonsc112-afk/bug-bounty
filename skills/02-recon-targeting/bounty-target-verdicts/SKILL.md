---
name: bounty-target-verdicts
description: "Use when picking a bounty target: check past verdicts."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [bug-bounty, audit, target-selection, verdicts]
    related_skills: [audit-competition-hunt, new-feature-bug-hunt, bugbounty-target-selection]
---

# Bounty target verdict register

## When to Use

Load this before choosing or starting a bug-bounty / audit-contest target, and before re-auditing
any surface of a previously examined protocol. It records what has already been verified-negative
so a session is not spent re-deriving the same dismissals.

Consult this BEFORE spending a session on a target. Each entry lists surfaces already
verified-negative with evidence, so they are not re-audited. Re-open an entry only when the
target ships NEW code touching that surface (check commit dates, not listing dates).

Companion skills: `audit-competition-hunt` (acquisition/build/campaign procedure),
`new-feature-bug-hunt` (freshness verification), `bugbounty-target-selection` (rep gates).

## Parallel (Immunefi) — CLOSED 2026-11-24, no payable finding

Program: `parallel` on Immunefi. Rewards paid in USDp on Ethereum, denominated USD.
Critical SC = 10% of funds directly affected, floor $50k, cap $250k. High $10k-$50k.
PoC required at all severities, KYC at payout, Primacy of Rules. Live 2025-10-02,
page last updated 2026-06-30.

Do not reopen unless a NEW facet deployment, new source commit, official scope or
reward change, or written project confirmation that the post-audit facet
redeployment was reviewed.

- Scope: `E:/audit/parallel/programs/parallel.md`, 215 active EVM rules on 25
  chains. The page's 217 assets are 216 addresses plus one web app URL, with one
  duplicate sUSDp Base entry. All 215 had bytecode on their own chain.
- Audits: Immunefi page lists only 6 reports but the project docs list Certora,
  Cyfrin, Bailsec, Zenith and Quantstamp through Sep 2026. Treat the docs list as
  the audit-depth authority. Known issues array has 37 entries ending 2026-01-31.
- Funds at risk: DefiLlama TVL about $1.16M, scoped token holdings about $956k,
  largest contracts Hyperliquid Parallelizer $344k, Base Parallelizer $232k,
  Ethereum Parallelizer $168k, Hyperliquid sUSDp $123k, Avalanche sUSDp $84k.
  Realistic Critical payout is the $50k floor to about $116k, not $250k.
- Source: `HEAD:contracts` and audit commit `518cb914:contracts` both equal
  `a5dc899a9832bcfc85b219e7976d022e0971a830`. No post-audit source change.
  Deployment JSONs changed after audit for four facets on three diamonds.
- Bytecode drift: 12 facet instances on mainnet, Base and Hyperliquid run
  Getters, SettersGovernor, RewardHandler and Redeemer bytecode matching the
  post-audit HEAD artifact, not the audited-commit artifact. This is a
  provenance and audit-coverage gap, not a vulnerability by itself. The other
  facets and both savings implementations match.
- Verified negatives: Savings donation accounting, first-depositor inflation,
  pause yield, EIP-3009 replay, surplus post-CR, issued-within-surplus, release
  conservation and proportionality, collateral-surplus bound, RewardHandler
  auth and collateral/tokenP checks, managed-collateral branches, chain config
  variants, zero-fee bridge DoS (known issue 26), negative-fee arbitrage
  (known issues 13 and 16), userDeviation snapping (fixed).
- Harnesses: Foundry 256-run campaigns and Echidna foundry-mode 10,000-call
  campaigns all pass, with negative controls and deliberately wrong self-checks.
  Slither 134 INFO results on parallelizer and 14 INFO on tokens, no
  Medium or High; one parser error in `LibSetters.adjustStablecoins` means that
  function was not covered by Slither.
- Local conflict resolution: wildcard out-of-scope rules in metric, flex,
  base-everest and klima program files were removed with operator approval.
  Backups in `E:/audit/parallel/backups/scope-conflict-2026-11-24/`.
- Artifacts: `E:/audit/parallel/findings/three-lane-consolidated.md`,
  `static-review-2026-11-24.md`, `surplus-harness-results.md`,
  `echidna-surplus-results.md`, `reward-harness-results.md`,
  `bytecode-drift-results.md`, `managed-collateral-results.md`,
  `chain-config-fuzz-results.md`, `live-config-20-chains.md`.

## NEAR Intents (HackenProof, 2 programs x $300k) — PARKED, 5 passes, no Critical

Artifacts: `E:/audit/near-intents/NEAR-INTENTS-TRACE.md` (full 5-pass evidence),
`ftv-review.txt` (extracted ToB audit), `survey_launched30.json`.
Repos: `E:/audit/near-intents/intents` (Windows); WSL `Ubuntu-24.04`
`~/audit/near-intents/{omni-bridge,btc-bridge,mpc}`.

Do not re-audit these — each was closed with evidence:

- **defuse engine core** (`contracts/defuse`): signature -> verifying_contract -> deadline ->
  key ownership -> nonce verify+commit chain is complete; `Deltas::finalize()` enforces global
  token conservation (greedy two-pointer matcher, leftover => `UnmatchedDeltas` => whole tx fails).
- **defuse payload/signature layer**: 7-standard dispatch maps curves correctly, per-standard
  digests give domain separation; WebAuthn implements the W3C steps incl. challenge binding.
- **BTC light client**: the deprecated `verify_transaction_inclusion` v1 internal-merkle-node
  weakness is real but the bridge calls **v2** (`satoshi-bridge/src/btc_light_client/mod.rs:240`).
  U256 carry algebra post-fix #683 is correct; ETH2 merkle depth/index come from fork constants,
  not attacker input; Dogecoin AuxPOW shift-wrap is gated by `#[trusted_relayer]`.
- **omni-bridge NEAR**: `fin_transfer_as_dao` is DAO-role-gated; `TokenDeployer` restricts
  bind_token/log_metadata; the `locked_tokens` fix is coherent across bound/deployed/pre-bind states.
- **omni-bridge EVM** (core, Wormhole, Hyperliquid, BridgeToken, SelectivePausable): chain id +
  nonce + accounts bound into the signed payload; slither on Box = 65 contracts / 64 detectors /
  **2 informational** (one a false positive). `SECURITY.md` lists known issues H-01/H-02/L-01..05.
- **omni-bridge Solana**: signature params bind the ACTUAL on-chain mint+recipient keys,
  malleability checked, serialization complete, nonce bitset atomic. The `used_nonces`
  `init_if_needed` front-running edge is **refuted at Anchor-source level** (see lesson below).
- **omni-bridge Aptos/Starknet**: both fin/init/deploy paths sound; Starknet reverses keccak
  endianness and uses 251-bit nonce words correctly.
- **near/mpc**: `threshold-signatures` is a CRATE inside mpc (standalone repo 404s). Five audits.
  ToB-NEARFTV-4 (HIGH, vote spoofing) is **fixed soundly** via `assert_caller_is_signer()`
  (signer == predecessor). A full scan of mutating API methods found **no sibling gap** — the 5
  unguarded ones are permissionless-by-design; `clean_invalid_attestations` protects in-use nodes.

Why parked: mature code (5 MPC audits, SECURITY.md on two legs), every money path consistently
guarded. Odds of a solo Critical are low relative to the effort.

## Aero / dromos-labs metadex — detail pass 1–2 (superseded by PARKED entry below)

Artifacts for the pass-1/2 detail: `E:/audit/aero/AERO-TRACE.md`. Repo
`dromos-labs/metadex-public` @ `2ce1816`, Foundry, solc 0.8.36, ~44.5k LOC in `V3/src`;
`V3/test` is NOT exported. Genuinely fresh code (versioned public releases, relay released most
recently) but six prior audits. The PARKED entry below is the authoritative verdict; everything in
this section is pre-pass-3 evidence kept only for the individual reasoning trails.

Relay surfaces closed with evidence — do not re-derive:

- **Reward accumulator** (`RelayRewardsLib`, `RelayToken`, `RelayBase.onRelayTokenTransfer`):
  hook settles pre-change balances; PT returns early so only YT settles; new holder accrues
  zero and checkpoints at the current index; `notifyReward` reserves with `ceilDiv` so the
  accounted balance covers merged-delta claims; `removeRewardToken` is gated on `index == 0`,
  which closes the checkpoint-underflow/re-add freeze; `claimSettled` is CEI; `pull`/`sweep`
  bounded to the un-accounted balance.
- **Deposit/exit queue** (`QueueLib`): the `toUint128` share cast cannot overflow at realistic
  magnitudes (needs `supply/backing > 2^128/amount`); `registerExit` takes the WHOLE processed
  record and there is NO withdrawal floor (the config NatSpec says so explicitly; the
  `BelowMinimumWithdrawal` error is dead code), so the "holder can always queue its whole free
  position" boundary holds; destinations above `uint72.max` are refused, not truncated.
- **`AllocationLib.extendLock`**: monotonic, touches no backing/supply/index — the accepted
  permissionless lock refresh moves no value.
- **Caller-ordered overdue admission**: real ordering effect, keeper-controlled by design; not
  a conservation break.
- **Whole-V3 slither (Box)**: 295 contracts / 61 detectors / 8 results, ALL
  `msg-value-in-nonpayable` on delegatecall-reached library functions = false positives.

Pass 2 closed these as well:

- **Entrypoints** (`BaseEntrypoint`, `MultiEntrypoint`): KEEPER-gated, router must be
  registry-approved, `tokenIn != tokenOut`, output measured as the entrypoint's own balance
  delta (router untrusted), approval force-reset to 0, leftover read by balance, and idle
  balance bounded by `balanceOf - accountedBalance` so owed rewards/rake are never spent.
  Target/excluded token sets are mutually exclusive and owner-gated.
- **`RelayIcaModule`**: keeper/leaf-config changes are admin + timelock; `_buildApprovals`
  approves exactly the summed per-token leg amounts (the unlimited allowance only wraps the
  sweep leg and is revoked after the batch); the plan is pinned by Hyperlane's
  `keccak(salt || calls)` commitment.
- **`RelayFactory` / `RelayLeafModuleDeployer`**: CREATE2 not clones (immutable bindings would
  otherwise be shared custody); deploy is permissionless and idempotent; factory salt is
  scoped to `msg.sender`, entrypoints must be bound to the predicted address, clone+initialize
  are atomic, and an inert-clone guard reverts if `principalToken()` is zero afterwards.
- **`RelayGovernanceLib`**: slice reads holder principal, Relay VE weight and total supply all
  at the proposal snapshot; per-(governor, proposal, holder) used-weight ledger with CEI;
  fractional params must be exactly 48 bytes and cannot exceed the remaining slice; the cast
  selector is pinned AND payloads under 4 bytes are rejected. `RelayTape` is fail-open
  observability with no fund custody.
- **Pools** (`Pool.sol`, `StablePool`): fees are transferred OUT to `PoolFees`, so balances are
  fee-free and the `_k(balance) >= _k(reserve)` swap check is tight; balances re-read after the
  fee transfer; burn runs the `KIsZero` threshold and mint the `MINIMUM_K` + `MINIMUM_LIQUIDITY`
  floors; `_updateFor` gives a zero-balance user the current index (no retroactive fees).
  `sync()` has no k check but can only RAISE reserves, so the accepted "k==0 drains for free"
  state is unreachable through it.

Unexplored: `gauges`/`voter`/`vpm` (weight routing and fee claims), `metarouter` (command
decoding and the cross-chain leg), `migration` (Aerodrome/Velodrome), `tokenRegistry`,
`splitter`, `hooks`, `art`, and the leaf-side `RelayLeafModule` claim path.

## Aero / dromos-labs metadex (Sherlock bounty 437, $500k Critical) — PARKED, 4 passes

Artifact: `E:/audit/aero/AERO-TRACE.md`; harnesses under `metadex-public/test/`.
Repo `dromos-labs/metadex-public` @ `2ce1816`, Foundry, solc 0.8.36; V3/src = 44.5k LOC;
`V3/test` is NOT published, so harnesses had to be written from scratch. npm on Windows fails with
`spawn EPERM` on git deps — install registry deps separately and clone the 3 git deps manually.

Do not re-audit these surfaces — each was closed with evidence:

- **Relay core** (queue, rewards, governance, ICA, entrypoints, factory, deployer): reward index
  accounting is solvency-safe (ceil-div accounted balance, pre-change settle, index-gated token
  removal); `_processEntry` share overflow needs an unreachable 3.4e11x backing collapse; there is no
  withdrawal floor by design (an exit takes one deposit whole); `extendLock` moves no accounting;
  the cast selector is pinned with a `<4-byte` guard; clone/deployer races are closed by caller-scoped
  salts, atomic create+initialize, and an inert-clone guard.
- **Pools + voters**: hardened Aerodrome pattern — fees transferred out before the k check, `KIsZero`
  burn guard, `MINIMUM_K` mint guard, `sync` only raises reserves; `withdrawToNFT` conserves weight
  exactly (dust to fee accumulator); `spendableSurplus` is non-decreasing.
- **Metarouter, leaf module, migration, small modules**: transient locker + child-frame allow-revert,
  NFT custody check, bridge-token binding, budget checks, CEI in `Splitter`, hash-bound registry
  review, `LeafVoter` orchestrator/operator gate. All sound.
- **Static**: full-V3 slither = 295 contracts, 61 detectors, 8 results, ALL `msg-value-in-nonpayable`
  on delegatecall library functions from payable entrypoints — false positives.
- **Fuzzing**: two Foundry invariant harnesses (`AeroRewards`, `AeroQueue`) = **409,600 calls**,
  0 violations, with non-vacuous handler counts and sanity tests.

Why parked: six prior audits, every documented invariant held, and the re-survey found no new
fresh-code program (watchlist 534 entries, 0 new launches in 30 days).

## Inverse Finance (Mantis, Ethereum) — CLOSED: JD-01 rejected as intended behaviour

Artifacts: `E:/audit/inverse/findings/inverse-coverage.md` (90-asset scope extraction + full
static verdict map), `JD01-report-en.md`, `Laporan-Temuan-Inverse-Finance-JD01.pdf`.
Repos: `E:/audit/inverse/FiRM` (branch `dev` @ 78272d8), `JuniorDola` (cac656c), plus 20 others.
Scope extracted from the Mantis RSC payload: 89 in-scope, DebtConverter is the only out.
Ale v5 deployed == FiRM dev `ALEV2.sol` byte-identical; JDola deployed is POST maxDbrPrice fix.

CONFIRMED (Medium, TWO fork PoCs PASS): **JD-01** — `FiRMSlashingModule.slash()`
nets bad debt against `Market.getCollateralValue` (pessimistic 2-day-low `viewPrice`), then
`Market.repay()` reduces debt WITHOUT seizing collateral; slash is permissionless so the
borrower self-calls. PRIMARY PoC: `FiRM/test/slashing/JD01Light.t.sol` (dip only 32.5% on
CF 8500, >15% suffices on CF 9200 markets): borrow 3000, repay to 100, withdrawMax repeatedly
to 0.0616 WETH, dip+recover, pessCV 97.77 < debt 100 < cap 100, juniors pay 2.22 DOLA,
collateral intact. SECONDARY: `FiRM/test/slashing/JD01.t.sol` (98% dip, juniors pay 2905 DOLA).
Fuzzing: 500 runs PASS, observed slashed 541.97 DOLA on 1000 DOLA debt, so `maxCollateralValue` caps `pessCV`, NOT the payout (corrected earlier wrong claim of a 100 DOLA cap). Net-profit PoC `FiRM/test/slashing/JD01NetProfit.t.sol` PASS: DOLA/WETH/escrow balances unchanged, debt drops by exactly the junior payout, net worth gain equals payout.

**FINAL VERDICT (2026-11-23): REJECTED by the platform.** Team reply: slash() intentionally covers only debt above collateral value; absorbing bad debt after a price drop is jrDOLA's role and junior depositors earn revenue for it; pessimistic-oracle low valuation is intended; the scenario needs a market move the borrower cannot cause; the pattern was reviewed before. Submission `cmwqr8chg000a08jrhjxgm52w` status `rejected`. Three follow-ups were sent (net-profit, escalation with developer comments, and a hunter acknowledgement); all failed to change the call. Do NOT re-report JD-01 or re-argue this mechanism on this program: the owner has explicitly classified it as intended. The developer comments in `FiRMSlashingModule.sol` ('avoid unliquidateable debt used to drain jDOLA depositors', 'want positions liquidated before repaying bad debt') were presented and still rejected, so an intended-behaviour rebuttal from source comments has no traction here. Historical fork PoC without mock could not be produced: on 21 Aug 2026 (block 25798000) `viewPrice` was dampened only 3.8%, far below the >15% needed at CF 8500; other scanned blocks showed ratio 10000.

**New-surface re-pass (2026-11-23, after rejection):** all 9 `src/` commits since Oct 2025 were checked. Fresh surfaces `StakingRewardsEscrow` (CEI + nonReentrant + onlyMarket pay + onlyBeneficiary/allowlist claim, tokens immutable and validated at constructor), `StakeDaoEscrow`, `DynamicFeeCurveFeed`, `ClampedPriceFeed`, `FeedSwitchV2`, `PTDiscountedNAVFeed`, ALE ad-hoc approvals, `Curve coin-0 wind-down feed`, `DBR helpers` are all already in the verified-negative list above. Additional permissionless helpers read and closed: `DbrHelper.claimAndSell` (escrow bound to msg.sender via `INV_MARKET.escrows`, sell/repay amounts derived from claimed DBR, cleanup sweeps leftovers; no cross-user value), `DbrDistributor` (claim/stake/unstake gated by `onlyINVEscrow` post-check that re-validates market + INV collateral + escrow ownership, reentrancy guarded), `ERC4626Helper` (market-bound vault/underlying, share balance checked before deposit; permissionless wrap/unwrap moves caller's own funds only), `PendlePTHelper` (callData selector allowlist, market-bound PT/YT, `user` vs `recipient` flows consistent, ALE-gated paths distinct), `Fed.takeProfit` (permissionless but sends profit to `gov`, not caller; no attacker gain). `sDOLA-earn` commit 9a20e44 is frontend only. Factory contracts are NOT in Mantis scope. NO NEW FINDING from this re-pass. Treat Inverse Finance as fully exhausted unless a new audited-relevant contract ships.

Verified-negative surfaces (do not re-derive): Market EIP-712 permits (domain binds chain +
market, nonce inside hash, typehash distinct); BorrowController rolling limit + edge-case DBR
mint (economically neutral); Oracle 2-day-low dampening; ALEV2 ad-hoc approvals + NM-002 fix
deployed; balance-based helpers/escrows sweep full balances (donation residual only);
ERC4626Feed/ClampedPriceFeed/DynamicFeeCurveFeed/PTDiscountedNAVFeed conservative rounding;
FeedSwitchV2/OneDolaFeedSwitch guardian-gated with live staleness 82900 s on sSwanUSD;
StakingRewardsEscrow/StakeDaoEscrow CEI + nonReentrant; INVEscrow xINV donation is expensive
griefing only; JDola slash unit math and MIN_ASSETS buffer correct; XinvVester linear vesting
incremental math correct; PSM USDS is 18 decimals and currently empty; sINV xy=k auction
consistent; Auction has no shares so the JDola ratio-cap rationale does not apply.

## Exactly Protocol (Cantina, Optimism + Base) — PARKED 2026-11-23, no payable finding

Program: `exactly-bug-bounty`, top reward $25k Critical (10% economic damage, needs about $250k loss), High $5-10k. 54 contracts, self-triaged, $50 deposit refundable for legitimate reports, KYC required, PoC mandatory for High/Critical. Busy competition (60-67 submissions in 11 days). Full evidence: `E:/audit/exactly/verdict-exactly-2026-11-23.md`, fork PoC `E:/audit/exactly/poc/` (6 tests pass at Base block 61058483), scope guard `E:/audit/scope-programs/exactly-cantina.md` (54 active rules).

**The shortlist claim that Oct 2026 commits were fresh functional code was wrong.** `8ac093a1` (15 Oct setup wARS), `13d99979` (19 Oct upgrade auditor/debt roller, deploy flash loaner), `80c28e11` (22 Oct tokenized stock setup) and `86b3a641` (28 Oct deploy stock markets) changed only deployment JSON, hardhat config, `.openzeppelin` state and changesets. No `.sol` source. `Market.sol` last changed 21 Apr 2026, `Auditor.sol` 15 Sep 2026 (NatSpec only), `InterestRateModel.sol` 22 Oct 2025. The features behind the deployments were audited by ABDK: Non-Collateral Markets (17 Sep 2026, PR #815 `6c022f3`, 0 Critical/Major/Moderate) and Flash Loan Adapter + Inverse Price Feed (19 Oct 2026, `371e41a` fixed in `9bf6024`, 16 Minor only). Both PDFs are linked from the program page as known issues, so CVF-1..6, adjustFactor 0, inverse-price staleness and FlashLoanAdapter leftover sweep are all known and non-payable.

**Lead `ProposalManager.checkLiquidity` was tested and retracted.** It ignores `nonCollateral` (source unchanged since 1 Oct 2025, selector `0xcd36d9fc` present in Base `0xB92E0A6E...` bytecode) and passes for a wARS-only or empty account on Base fork block 61058483. But `Auditor.accountLiquidity` gives wARS zero borrowing power, a real floating borrow at Base USDC reverts `0x15d58176` (`InsufficientAccountLiquidity`), `ExaPlugin.collectCredit` forwards `msg.sender` as borrower so there is no caller bypass, and `preExecutionChecker` never calls `checkLiquidity`. Impact stops at a failed card transaction or over-broad server authorisation; griefing and best practice are excluded. The observation is also published in ABDK p.26. No value can be stolen, frozen or borrowed unbacked. Do NOT re-report.

Other rejected angles: PriceFeedInverse/PriceFeedwARS staleness and inverse error (ABDK CVF-3/CVF-5), FlashLoanAdapter no return check (CVF-1, client says both callers repay exact amount), DebtRoller vs Auditor markets() tuple order (admin/governance), `adjustFactor=0` freeze (admin-only), `deploy/mocks/Assets.ts` missing live-network guard (config/test file). Remaining untested corner: inverse USD/ARS feed under extreme peso move, but that is ABDK CVF-3/CVF-5 so expected payout is low. Reopen only on a new implementation or scope change after 23 Nov 2026.

## LOVEH (AEREDIUM) and RAAC — surveyed 2026-11-21, no finding

Artifact: `E:/audit/targets-2026-11-21-verdicts.md`. Repos: `E:/audit/loveh/LOVEH` @ `6daa861`,
`E:/audit/raac/repo` @ `97587ed`.

- **LOVEH**: the only genuinely fresh (repo created 2026-11-04), unaudited, immutable lending
  codebase found (core 1,035 LOC, no owner/admin/pause/upgrade). Build green, all functional tests
  and 10k-run fuzz pass; the single failing test is a gas-budget assertion (`borrowableOf` 42k >= 30k
  cap), not a functional bug. Slither 16 results all LOW/INFO; the flagged `withdraw` reentrancy is
  closed by `nonReentrant` + set-aside/restore of fee accounting. Money paths read clean.
  Deep pass 2 added two harnesses at `test/`: `LovehConservation.t.sol` (512x300 = 153,600 calls,
  0 violations on `U+L==D+F` and token backing) and `LovehBorrowable.t.sol` (10,000 fuzz runs
  proving the docs' promise that `borrowable` is accepted and `+1` refused). Algebraic dismissals
  in `E:/audit/loveh/DEEP-HUNT.md`: the liquidation cap can never deliver more than
  `repaid*incentive`; `_writeOff`'s fee leg cannot underflow because `loans - deposits <= feeOwed`
  follows from the accounting identity. FINAL deep run: repo invariant suite 2 suites x 1,000,000
  calls = **2,000,000 calls, 0 violations**, taking the campaign to ~2.16M fuzzed calls with no
  finding; a stateful price source cannot desync anything because `_price()` is called once per
  function. The only failing test is a gas-budget assertion that PASSES in the repo's own committed
  `reports/lv2a/test.log` (compiler/EVM-version difference, not fund-safety). DO NOT re-fuzz;
  see `E:/audit/loveh/DEEP-HUNT.md` before touching this target again.
  **Pays only 10,000 AERX airdrop points with unspecified conversion — not a real payout.**
- **RAAC**: Aave V3 fork, ~6,345 LOC in 19 files. Guardian-funded $100k pool, but Critical-only and
  >20% of total funds, ~30 prior audits, an attached 1.2MB audit report whose findings are invalid,
  and many exclusions. RAAC's own math additions (`rayPow`, `rayMulDown`, 7-term `rayExp`) checked:
  `rayExp` under-approximation needs an impossible exponent at the admin-bounded max rate. No finding.
  Audit PDF is auth-gated and could not be read.
- **Do not re-survey**: Immunefi/Cantina/Sherlock had zero new contests; Proofline's
  "Tidal Bridge v2"/"Lumen DVT" are DEMO data (preview page, contradictory dates).

## Hastra (self-hosted + HackenProof-style, up to $100k) — surveyed 22 Nov 2026, no finding

Artifact: `E:/audit/hastra/hastra-recon-pass1.md`. Repos: `E:/audit/hastra/eth-vault` @ `6bebe3b`, `E:/audit/hastra/sol-vault` @ `8c75c34`, `E:/audit/hastra/provenance` @ `c6396e3a` (shallow sparse: x/marker, x/feegrant, x/ibchooks, app). Audits read: OtterSec Aug 2026 (16 findings, all Low), Sherlock Mar/Apr 2026 (15 findings, 4 Medium), OtterSec Solana summary.

Do not re-derive these surfaces without new code:

- Known issues explicitly Ack'd and excluded by policy: NAV timing / yield-sandwich (`OS-HES-ADV-01`), frozen-redemption lock (`OS-HES-SUG-01`), reward-distribution MEV and EVM/Solana semantic drift (Sherlock themes). Yield-timing arbitrage is itself an out-of-scope impact in the central policy.
- EVM V2 role split and cap: `initializeV2` one-shot, EPOCH_ADMIN/REDEEM_OPERATOR separation, per-epoch claim cap, `firstCappedEpoch = 3`. Local harness proved pre-cap epochs can overclaim vs declared `totalRewards`, but it needs a malicious EPOCH_ADMIN root (privileged-role misuse, excluded). Post-cap claims are blocked.
- NavEngineV2: V2 dropped V1's TVL-difference guard and uses a 5% rate-delta guard + cooldown; a 5% NAV step moves StakingVault share price 5%, 20 steps reach ~1.98x under a 2e18 cap. Requires UPDATER EOA `0xD5a287...`; no public key leak found. `initializeV2` has no caller check but `_initialized = 2` on all three mainnet proxies.
- Stale-NAV idea is already public: gist `hadramaut/33cb0ffa...` (14 Nov 2026) contains a Foundry PoC for stale NAV dilution on both V1 and V2. Treat as duplicate.
- Role state: TimelockController `0x4Acd...` (24h delay) holds admin/upgrader/EPOCH_ADMIN; proposer is SafeProxy `0x8D358...` (4-of-7). Pauser/freezer EOA `0x8571De...` is not a Safe owner. Ops EOA `0xA8C3CF...` was revoked on YieldVault but still holds StakingVault REWARDS_ADMIN and calls `distributeRewards` hourly (301 of 400 recent txs); this is the documented FACD operator layout, not a leftover.
- Verification: `forge test --offline --summary` = 26/26 across 8 harness suites. Static linter warnings (`unsafe-typecast` in NAV engines) are guarded false positives. No finding eligible under the "loss of funds without privileged misuse" rule.

Provenance Cosmos (in Hastra scope): the 17-18 Nov 2026 fresh commits (`MaxSupply` enforcement, ibchooks v2 error ack, trigger module removal, feegrant fork bump) were reviewed statically. Go tests were offloaded to Simular Box (`cb-eb5b8f648241`, Go 1.27.3) because this host has no Go and Docker sbx's 30 GB overlay filled during linking. `go test ./x/marker/... -count=1` passed `x/marker`, `x/marker/keeper`, `x/marker/simulation`, `x/marker/types`; only `x/marker/client/cli` failed due to sandbox egress denial to `http://0.0.0.0:...` (environment, not code). No finding. Follow-up on `x/name`, `x/sanction`, `x/registry`, `x/metadata`: no functional commits since 15 Oct 2026 (only lint/dependency bumps); static review found authority gating and signer binding intact; Box test run passed every keeper/types/cli package, with only integration suites failing from the same `egress denied: 0.0.0.0` sandbox restriction. Do not re-audit these six modules without new functional commits.

## GMTrade / gmsol-labs/gmx-solana (Immunefi, $100k) — surveyed 22 Nov 2026, no finding

Artifact: `E:/audit/gmtrade/RECON.md`. Repo `3e0a4115` (21 Nov 2026), Rust/Anchor 0.31.1. Cloud build on Docker sbx: `cargo check --workspace` PASSED after installing `libudev-dev` (41 s, only unused-dependency warnings); full SBF build not attempted because Solana CLI/Anchor were absent and disk was low.

Verified-negative surfaces (do not re-derive without new commits): `complete_gt_exchange_v2` validates owner by CPI, rent receiver against recorded exchange value, token targets as owner ATAs, and vault as GT-bank ATA; `close_gt_exchange_v2` validates owner/store/vault/receiver/PDA seeds; new `claim_rent` requires the rent receiver to sign and derives the collector PDA from that signer. Pass 4 closed the creative price-impact/virtual-inventory hunt: sub-unit exponent threshold is ~1e-6 USD (irrelevant); VI grouping validates decimals but not token mint identity (MARKET_KEEPER-gated, excluded); VI penalty is skipped when local pool impact is positive, which is the acknowledged cross-market/partial-mitigation risk and matches GMX V2, so not novel. No commits touched swap math since September. Oct 9 2026 Zenith audit reviewed separately; its VI-adjacent L-7 is acknowledged.

Pass 3 verified GLV shift (`only_order_keeper` gate, oracle-time check, vault-balance invariants before/after) and EVM proxy scaffold (24-line greeting-only `initialize`; program ID `Dodg22E8...` is undeployed on mainnet, `getAccountInfo` returns null). No finding.

Pass 2 also verified: keeper execution-fee clamp (`max_execution_lamports`, `saturating_sub`) and `ExecuteIncreaseOrSwapOrderV2` ordering; README known issues already exclude the common keeper/price-impact vectors. Full `anchor build` on Simular Box succeeded after installing Rust 1.100.0, Solana CLI 2.1.21, Anchor 0.31.1, `pkg-config`/`libssl-dev` and clearing stale Go caches: 9 `.so` + 9 matching IDLs. Only non-fatal unused-dependency warnings and an SBF stack-offset note on `Account::try_from` remain.

## Stake DAO (Mantis, new program 16 Nov 2026) - fork pass verified-negative

Artifact: `E:/audit/stakedao/STAKE-DAO-FORK-TRACE.md`. Tests: `E:/audit/stakedao/fork/StakeDaoForkTest.t.sol` and `E:/audit/stakedao/fork/StakeDaoForkEdgesTest.t.sol`.
Fork `eth-mainnet.public.blastapi.io` block 26,474,953, Foundry 1.9.0, `forge test -vv` = **10 passed, 0 failed** across 2 suites.

Do not re-run these six without new code or config: delegation unstake invariant
(`amount + delegatedOut <= balance`), expired-delegation capacity release,
`withdrawEarly` penalty formula (2500 bps max, 56-day delay, 7 days elapsed ->
2187 bps and routed to PenaltyForwarder), `claimable()` vs `claim()` equality
after checkpoint, fresh staker gets no retroactive epoch, and `deposit()`
accounting. Later pass also closed multi-epoch rounding (two holders at 1:2
within 0.1%, total claims <= deposits), stale BoostMarketplace
`committedBalance` after a seller unstake and withdraw (documented limitation,
fill reverts atomically so no payable loss), and `claimWithPermanentEpochSkip`
forfeiting earlier epochs plus its startEpoch validation. Source read via
Blockscout verified sources: vlSDT, FeeDistributor (USDC and SDT),
PenaltyForwarder, vlBoost, BoostMarketplace; compiler 0.8.28.

Later pass added `StakeDaoForkNewEdgesTest.t.sol`: claim while later epochs are still empty
does NOT forfeit their future rewards, and a 25-epoch checkpoint gap stays fully accounted
(only wei-level floor dust) after repeated `checkpointToken()`. Full suite is now **12 passed,
0 failed** across 3 suites. Scope guard rechecked 23 Nov 2026: `in_scope_total: 0`,
`out_scope_total: 9`, 0 parse errors, 0 conflicts. Do not re-run these twelve tests without new
code or config. Remaining unused surfaces (`scheduleUnstakeDelayUpdate`,
`applyUnstakeDelayUpdate`, `scheduleMaxPenaltyUpdate`, `applyMaxPenaltyUpdate`,
`setOperatorAuthorization`, `kill`, `recoverToken`) are owner/operator-gated and therefore not
unvetted payable paths.

Program-level blockers remain OUTSIDE the code: Mantis page says Mantis-only
submission, Critical/High only, >= $10k demonstrated loss; docs.stakedao.org/bug-bounty
(modified 20 Nov 2026) still lists Medium/Low and email submission. Scope is
named by product families, not addresses, so address-book addresses are NOT
authorized for PoC. Guard file `E:/audit/stakedao/programs/stakedao.md` has an
empty In Scope and 9 explicit exclusions; `--explain` denies every address tested.

## Zircuit Finance (self-hosted, up to $100k USDC Critical) - CLOSED 23 Nov 2026, no finding

Artifacts: `E:/audit/zircuit-finance/workflow/` (scope, requirements, spec, checks,
check-results, report-draft marked NOT SUBMITTED, trace, lessons). Source:
`E:/audit/zircuit-finance/src/tree/contracts`, no git metadata; source came from a Blockscout
Ethereum verification bundle and Base implementation bytecode was NOT matched against it.

Static pass closed six candidates before any PoC was built, so do not re-derive them without
new code: asymmetric `nonReentrant` on `VaultToken.processWithdrawals` has no reentrant callback
path (`this.send` is guarded and `fulfilled` is written before the external call); compose refund
failure only delays the refund because `composeFrom` receives the tokens and LayerZero retains the
message for retry; `cancelWithdrawal` native refund is self-griefing since only the initiator can
call it; `reportDelta` dust touches NAV, which the program explicitly excludes; the fee-on-transfer
assumption needs an asset not currently in scope; `tx.origin` as refund address sends only excess
native fee to the executor while tokens still go to the user. `forge build --offline` green, lint
warnings only.

Dynamic phase closed 23 Nov 2026 with no finding. Final verdict: `E:/audit/zircuit-finance/ZIRCUIT-FINAL-VERDICT.md`; verified source and four harnesses in `E:/audit/zircuit-finance/sourcify-base/`.

Source provenance was corrected before any claim. The original tree came from an Ethereum Blockscout verification bundle and does NOT byte-match the Base implementations: all five core contracts differed at the dispatcher, lengths differed, and CBOR metadata source hashes differed. Correct source was found on Sourcify chain 8453 with `exact_match` for AccountingReceiver `0xbfaebf5e...` (matchId 33931798), StrategyManager `0x2f17b8f1...` (33459198), UnderlyingOFT `0xb2e30c33...` (36045267), VaultComposer `0xfea5ce04...` (40428350), and Vault `0xfefa9a81...` (38036585). Recompiling that source produced executable bytecode identical to onchain after stripping the 43-byte CBOR tail. All dynamic work used the Sourcify source.

Dynamic results, do not re-derive without new code:

- Core Vault + UnderlyingOFT accounting: 500,000 invariant calls, 0 violations, ~8,500 successful calls per handler.
- VaultComposer withdrawal queue: 500,000 invariant calls, 0 violations; double-process and cancel-after-fulfill revert; rounding favors the vault.
- Compose handler on a Base fork at block 61,083,824 with the real endpoint `0x1a44076050125825900e736c501f859c50fE728c` read from composer ERC-7201 storage: deposit compose credits shares, non-endpoint caller reverts. Caveat: `vm.prank` was used, so endpoint-internal validation was not exercised.
- AccountingReceiver + StrategyManager: deploy/free/report paths each exercised ~1,000 times; GUID replay reverts.
- Negative NAV delta: 20 percent drop gives `mint = false`, `delta = 20e6`, OFT burned from the vault, `underlyingByStrategy` follows NAV, and recovery mints it back. NAV is explicitly out of scope, so this is not reportable.
- Combined after harness fixes: 4 suites, 10 tests passed, 0 failed, four 500,000-call invariant campaigns (about 2M calls total).

Harness trap worth reusing: `IFactory.getDeployedOrRevert` takes `(ContractType,string,string,uint32)` and `ContractType.STRATEGY_MANAGER == 5`. An earlier harness used a wrong three-argument signature, so most handlers reverted early and its accounting invariants were partly vacuous. Fixed and re-run with call-count evidence. Check call counts before trusting any invariant result.

Do not re-audit unless new implementation bytecode appears at those five addresses or the scope changes.

## Enzyme Onyx (Immunefi, scope pinned 2026-10) — recon verified-negative, 3 passes

Artifacts: `C:/Users/TUF-GAMING/Documents/onyx-sync-redeem-dan-aliran-dana-2026-11-23.md`,
`onyx-proxy-live-dan-hook-ace-2026-11-23.md`, `onyx-hook-dan-stale-price-2026-11-23.md`.
Proxy list: `C:/Users/TUF-GAMING/AppData/Local/hermes/onyx-proxies.json`.

Do not re-derive without new code or a published live address:

- `SyncRedeemHandler` has NO published deployment. It appears twice in scope pinned to commit
  `d8a522d6`, one entry pointing at a private 404 repo, and appears in NO onyx-sdk deployment
  manifest across 7 networks. ChainSecurity QA exists for it. Third-party notes call its live
  address UNKNOWN. Treat as 'Latest audited', not a fork target. Other hunters already
  falsified cross-user redemption, reentrancy, and exit-fee paths on it.
- SDK deployment addresses (Shares `0x4fdb...`, SyncDepositHandler `0x3039...`, queues
  `0x78fc...`/`0xbdbb...`) are UNINITIALIZED implementations: name/symbol/owner/getFeeHandler/
  asset all return zero. Real state lives in beacon proxies from `SharesFactory`
  `ProxyDeployed(address)` logs (40 collected). Always fork the proxy, never the manifest address.
- Chainlink ACE validators at pinned commit `7b48d243` are thin wrappers with `onlyShares` +
  `runPolicy` and empty function bodies; extractors are `pure` with no external calls. Direct
  reentrancy via these files is not payable, and the only external call (`runPolicy` -> Chainlink
  PolicyEngine) is a third-party dependency. Also NOT attached to the funds checked: the
  Hashrock fund's `addDepositHandler` added a `SharesMintHandler` proxy with `getPreMintHook()==0`,
  and live SyncDepositHandler proxies `0x84f298...`/`0x3d7e18...` have `postDepositHook==0`.
- Stale-price lead CONFIRMED read-only but NOT payable: live prices are 3.36 and 2.28 days old
  while SyncDepositHandler `maxStaleness` is 86,400 s, and the direct deposit path validates the
  timestamp while `DepositQueue.executeDepositRequests` discards it. Execution is
  `onlyAdminOrOwner`, a trusted role the program excludes. Re-open only with a path where a
  non-privileged caller can trigger execution or manipulate the price update.

- Stale-price lead FINALLY CLOSED as non-payable: `updateShareValue` in `ValuationHandler.sol`
  is `onlyAdminOrOwner`; all observed calls on Hashrock (1) and XPrime (3) valuation handlers
  came from the same owner EOA `0x427Dc1b1...`, which is also the fund owner. A ChainSecurity QA
  note on `CreWorkflowConsumer` retry pushing stale values concerns a third-party Chainlink
  component and was not observed on these funds. Do not re-open without new code.
- Arbitrum: 58 fund proxies from SharesFactory, but all nine ACE validator factories emitted
  only `ImplementationSet` and ZERO `ProxyDeployed`, so no ACE validators are deployed there.
  Base remains UNVERIFIED: its Blockscout API returns 403/503, explorer endpoints serve HTML,
  and public RPCs cap eth_getLogs at 10-1000 blocks (publicnode wants an archive token).
  Artifact: `C:/Users/TUF-GAMING/Documents/onyx-chain-lain-dan-update-harga-2026-11-23.md`.
- Overall: seven passes produced no payable finding. Park Enzyme Onyx until new code, a real
  ACE hook installation, or a published `SyncRedeemHandler` address appears.

## Flex (Mantis) — ALREADY WORKED, submission filed 22 Nov 2026

Artifacts: `E:/audit/flex/findings/` (FX01/FX02/FX03 drafts, PDF reports, Mantis payloads,
`submission-receipt.md`, `coverage-negatives.md`, `all-poc-fresh.log`). Repos pinned:
`flex-contracts` @ `ac0835f`, `flex-allocator` @ `1055ddc`.

Do NOT reopen Flex as a 'new shortlist target'. A High submission already exists:
`cmwr9uq58003207ldaoozaelx`, asset `cmwm61wsf001008l662ofvn8n`, status `new` at filing.
FX01 `_maxLoss` unusability and FX03 APR oracle wrap are Medium/Low; FX02 multi-strategy
exit shortfall was escalated to High with a measured 299,877 USDC cross-depositor loss
(`ExitRouterCrossDepositorLossPoC.t.sol`, block 25,043,786, gas ~1.99e9).

Twelve more candidates are falsified in `coverage-negatives.md`, including FX01 funds-loss
escalation, `disableHealthCheck` persistence, `_harvestAndReport` underflow, leverage zapper
zero-buffer (published M-06), Infinifi/Locked yvUSD cooldown seams, SwapExecutor reentrancy
(no in-scope router path, whitelist empty at 10 deployed zappers), and DebtInFrontHelper.
Scope is repo-only with no on-chain address list; guard file `E:/audit/flex/scope-programs/flex.md`.

## CapyFi (Immunefi) — initial recon, not yet hunted

Artifact: `C:/Users/TUF-GAMING/Documents/capyfi-recon-awal-2026-11-23.md`. Guard:
`E:/audit/capyfi/scope-programs/capyfi.md` (9 in-scope EVM addresses, 0 parse errors,
0 conflicts; the Coinspect oracle `0xfba2712d...` is correctly denied).

Program pays USDC, max $1M, PoC + KYC required, arbitration, no rep gate. Scope has 9
Ethereum addresses plus Capyfi App and two Primacy-of-Impact placeholders. All 9 verified;
7 are CErc20Delegator proxies whose six distinct CErc20Delegate implementations have
IDENTICAL source (sha256 prefix `309e4e40f07c6960`, solc 0.8.10), so there is no
version-diff surface. Code last pushed 2025-07-28, two audits July 2025 (Coinspect,
OpenZeppelin), so this is NOT fresh code. Already acknowledged/excluded: CAPY-02 stale
oracle check, hardcoded `blocksPerYear`, Whitelist admin powers, caUXD fixed-price drain
(fixed). Remaining lead is active Comptroller configuration vs `ProdConfig.sol` and whether
the whitelist is actually wired into cTokens (Coinspect found it unwired at audit time).
- Follow-up 23 Nov 2026 CLOSED these three: read state via **Unitroller** `0x0b9af1fd...`, NOT
  the Comptroller implementation (which returns zeros). Live CF: caUSDT/caUSDC 0.85 vs
  ProdConfig 0; caLAC 0.6 vs 0.5; 13 markets total, only 9 in scope. Whitelist active only on
  caRPC and caLAC (`0x302a893b...`), absent on the other five; `CToken._checkWhitelist` skips
  when unset. All `fixedPrice` are 0 so CAPY-01 is gone; caRPC custom feed `0x5da9a0bc...`
  is 3.36 days stale but acknowledged CAPY-02 and third-party/centralization, both excluded.
  Markets are non-empty, so first-minter inflation is not live. Correction: CapyFi DOES pay
  Medium $5,001-$10k and Low $1k-$5k. Artifact:
  `C:/Users/TUF-GAMING/Documents/capyfi-konfigurasi-whitelist-oracle-2026-11-23.md`.
  Park CapyFi unless code/config/scope changes.

## Robinhood Chain (Cantina) — ACTIVE CANDIDATE, fresh code, recon started 23 Nov 2026

Artifact: `C:/Users/TUF-GAMING/Documents/shortlist-target-baru-2026-11-23.md`. Guard:
`E:/audit/robinhood/scope-programs/robinhood.md` (3 EVM rules on chain 4663, 0 parse errors,
0 conflicts; the L2 bridge addresses from Robinhood docs are correctly denied).

Program: started 2026-09-08, $30 deposit, KYC to join, 155 findings at review time.
Critical up to $1M (proposed maximum, Robinhood sign-off pending). Chain 4663, EVM/Arbitrum
Nitro, explorer `robinhoodchain.blockscout.com`. Scope: tokenized stock contracts
(StockFactory `0x4783C67b...`, AccessControlsRegistry `0xe10b6f6b...`) and JustInTimeFunding
`0xd4A91E50...`. JITFunding holds >$34.5M across >50 tokens with 404,666 transfers, so funds
are real. Source verified and saved at `C:/Users/TUF-GAMING/AppData/Local/hermes/JITFunding.sol`.
First-pass read of JITFunding: nonce/expiry checked before transfer, EIP-191 hash binds
address(this)+chainid+account+asset+amount+nonce+expiry, signer needs AUTHORIZER_ROLE,
emergency withdrawal goes only to immutable vault. No obvious bug there; focus next on the
stock contracts' mint/burn/seize/pause/multiplier authority and role state.
All other Nov-2026 "fresh" listings checked and rejected: Beanstalk (UI-only commits),
SYMMIO/Midas/Reserve/Euler/Uniswap/Polymarket (audit/CI/docs/proposal commits or stale repos).
Live contest window is empty for Solidity: Base Everest already worked, Revert v4lend judging
ended 3 Nov, BattleChain in judging.
- Follow-up 23 Nov: source mapped for StockFactory (UUPS, TOKEN_DEPLOYER_ROLE deploy,
  FACTORY_UPGRADER_ROLE upgrade), Stock (mint/burn/pause/multiplier/metadata all role-gated;
  `adminBurn` intentionally bypasses pause and blocklist), AccessControlsRegistry (IBeacon,
  pause/upgrade/block role-gated). Verified EIP-1967 slot of StockFactory proxy points to the
  published implementation; registry `implementation()` returning the Stock implementation is
  EXPECTED because registry is the beacon, not a misconfiguration. 100 stock tokens deployed;
  sample is live with supply and no pause. 17 active role grants verified with direct
  `hasRole` calls; deployer's admin and beacon-upgrader roles were revoked after setup.
  Remaining leads: non-privileged path to `adminBurn`, and overwriting a pending multiplier
  schedule to exploit `uiMultiplier()` switch. Both still need an unprivileged trigger.
  Artifact: `C:/Users/TUF-GAMING/Documents/robinhood-authority-proxy-role-2026-11-23.md`.
- Three leads CLOSED 23 Nov: no unprivileged path to `adminBurn` (ADMIN_BURNER is an EOA;
  only two MINTER holders are unverified minimal proxies); Foundry fork harness
  `E:/audit/robinhood/fork` with `forge test --fork-url https://robinhood.drpc.org -vv` =
  **4 passed, 0 failed**, proving schedule overwrite discards the earlier pending multiplier,
  past effectiveAt reverts, and non-role callers cannot update; Chainlink's Robinhood equity
  feeds ALREADY include `uiMultiplier()` per official docs, so the third-party clubytech claim
  that Morpho drops the multiplier contradicts Chainlink and is unverified. Artifact:
  `C:/Users/TUF-GAMING/Documents/robinhood-tiga-lead-2026-11-23.md`. Do not re-run these three
  without new role holders, new verified source, or Morpho oracle config evidence.
- Latest: Sourcify has NO match for either minter implementation (chain 4663); arbitrary-EOA
  `eth_call` to `mint` and `hasRole` on both proxies reverts. Morpho Blue `0x9D53d5E3...` has
  43 createMarket txs, five with Robinhood stock collateral, but all four unique collateral
  tokens have uiMultiplier == 1.0, so the Chainlink-vs-clubytech multiplier contradiction
  cannot be settled with live data; Morpho is third-party and out of scope. Role state
  unchanged: 20 grants, 3 revokes, 17 active, last event block 111,198,347. Artifact:
  `C:/Users/TUF-GAMING/Documents/robinhood-tindak-lanjut-2026-11-23.md`.
- Monitoring installed 23 Nov: AAPL `0xaF3D76f1...` has live uiMultiplier 1.00109 but is NOT
  in any of the 43 Morpho markets; all five stock-collateral markets use multiplier 1.0.
  Cron job `a1233f454e19` "Robinhood Morpho multiplier watch" runs every 6h with monitor
  script `rh_morpho_multiplier_monitor.py` (deterministic JSON baseline `[]`), so the agent
  only wakes when a non-unity multiplier stock token enters a Morpho market. Artifact:
  `C:/Users/TUF-GAMING/Documents/robinhood-monitor-morpho-multiplier-2026-11-23.md`.

## Klima Protocol v2 (self-hosted docs bounty, Base) — SUBMITTED 2026-11-21

Artifact: `E:/audit/klima-protocol-v2/NOTES.md` (PASS 1–12), submission bundle `E:/audit/klima-protocol-v2/bundle/` (17+ files, MANIFEST.sha256), scope guard `E:/audit/klima-protocol-v2/scope-programs/klima-v2.md` (6 active rules, 0 parse errors, report addresses all authorized with disclosed deviation: program page has no address book, rules derived from official deployment manifests).

**SUBMITTED (one finding, H2):** `deallocateKvcm` (KvcmStakingFacet.sol:231-294) drops the raw class allocation instantly with no rate-limiter/zkMe/maturity gate, while the AAM RETIRE quote reads that raw allocation (QuoterRouterFacet.sol:407-415); an existing large allocation holder can drop → retire cheaply (measured 76.77% discount, 2500 t for 1819.85 kVCM vs 7834.17 kVCM formula price) → re-allocate exactly, fully reversible. Asserted PoC `test/fork/H2Atomic.t.sol` 3/3 PASS on pinned block 60,030,512; deployed bytecode pin verified. Prior-art check 2026-11-21: repo created 2026-10-19, single commit, no audit PDF/known-issues file, no public writeup for this mechanism. Negative control (negative-control fork, deallocate mock-reverted) FAILS as expected. Gate: fresh 1 t UCR retirement from payout wallet ≤30 min before email to security@klimaprotocol.com.

Verified negatives, do NOT re-derive without new code: H1 forward-swap discount factors all zero live (feature off); H3 coupons dormant; H6 supply oracle = V2 (not V1); R5 marketplace `fillListing` validates caller unitPrice (fork-tested, wrong price reverts 0xfbfe3e2a); dead-code `_settleExpiringMaturityRoll` → `cleanUpAllocationsForMaturity` unreachable (QA note, not payout); ghost-drop lead on matured/redeemed locks REFUTED empirically (30 matured locks, 24 REDEEMED, all deallocate attempts revert `KvcmLockAllocationNotFound` 0xe33fc5cb); all slither results filtered to FPs by direct source reads. Class vault deposit/withdraw, CarbonLedger migration, OperationsFacet lifecycle reviewed clean by a second-opinion pass.

Residual surfaces CLOSED 2026-11-23 (all clean, evidence E:/audit/klima-protocol-v2/bundle/evidence/fresh-facets-review.md + residual-checks.md): K2StakingFacet, KvcmLPStakingFacet and RiskyYieldFacet were deep-reviewed by three read-only subagents, 0 fund-loss findings (symmetric share/balance accounting, role gates, nonReentrant, live module parity, sequential yield guards). ProtocolSupplyOracleV2 has NO cache/heartbeat (pure live reads, UUPS impl bytecode 4378 B == repo artifact); flash-loan-funded retirement works with same-tx repayment (appendix/FlashLoanH2.t.sol PASS); PoC reproduces identically at fork blocks 60,031,000 and 60,035,000 (a far later block only fails the test's 70% drop threshold because new allocations raised the class total to 966k). QA-only note, NOT a second report: RMLPRewardsFacet.sol:221 zeroes ryPosition.shares without decrementing lpRYieldGlobal.totalShares (reachable via claimLPRewards by an active LP staker); yield under-distribution, no attacker profit, principal safe. Category 15 deque keeper-lapse liveness closed: live roll lag 0, not attacker-triggerable.

## OnRe (Immunefi, Solana) — ACTIVE CANDIDATE, recon started 23 Nov 2026

Artifact: `C:/Users/TUF-GAMING/Documents/sweep-dan-onre-recon-2026-11-23.md`. Guard:
`E:/audit/onre/scope-programs/onre.md` (one Solana mainnet rule, 0 parse errors, 0 conflicts;
devnet ID correctly denied). Program ID `onreuGhHHgVzMWSkj2oQDLDtvvGvoepBPkqyaubFcwe`,
max $100k USDC, PoC all severities via solana-program-test/anchor-bankrun/LiteSVM, KYC at
payout, no rep gate. Six audits, latest OtterSec 29 Jul 2026; known issue `update_offer_fee`
10000bps-vs-1000bps already fixed and boss-gated, do not re-report.
Fresh surface: Sep 2026 commits changed 8 source files (70+/41-) around redemption requests,
offers and excluded-owner lists, AFTER the last audit. Repo `onre-finance/onre-sol` cloned to
`E:/audit/onre/onre-sol`. Source build was FIXED with cargo-build-sbf 4.6 + `--force-tools-install`; the source-built .so
passed 54/54 tests on both v1.54 and v1.58 builds. The earlier live-binary dump also passed 54/54
but is only a baseline. Source-build hashes never matched the live dump, so use the 1 Oct 2026
on-chain upgrade timestamp (after the 21 Sep source commit) as scope evidence, not hash equality.
Do not re-run the 54-test suite without a source-built .so.
LiteSVM fuzz harness `programs/onreapp/tests/redemption_fuzz.rs` added 23 Nov 2026: 4 tests
(12 duplicate-ID, 10 re-cancel, 8 wrong-fulfill-order, 40-ID lifecycle) all PASS against the
source-built v1.58 .so. Request-ID duplication, re-cancel and fulfill ordering are therefore
verified-negative; do not re-test them without new invariants.
OtterSec Jul 2026 (commit 8aceb86) had 16 findings, none Critical/High. Still ACKNOWLEDGED and
therefore duplicate-prone: ADV-01 stale exclusion cache, ADV-07 daily compounding NAV gap,
SUG-01 withdraw_configurable_vault missing boss auth, SUG-02 old/new interface drift,
SUG-03 per-partial fee rounding confiscation, SUG-05 external ONyc deflating circulating supply.
Immunefi also lists `update_offer_fee` 10000bps-vs-1000bps as an explicit known issue.
Artifact: `C:/Users/TUF-GAMING/Documents/onre-fuzz-dan-known-issues-2026-11-23.md`.
Second harness `programs/onreapp/tests/fee_excluded_fuzz.rs` (4/4 PASS, 23 Nov 2026):
fee rounding differs from a single full fulfill by at most one unit per partial call; vault
stays solvent; one-unit fulfill at max fee REVERTS because the SUG-00 zero-output guard landed,
so the extreme SUG-03 confiscation path is mitigated. Excluded-accounts Vec works, duplicates
are rejected, ATA count is exact, and the excluded-balance cache is verified stale until a
permissionless refresh (matches acknowledged ADV-01). Both surfaces are verified-negative for
NEW payable impact; do not repeat without a new invariant. Remaining untested angle: Prop AMM
sell fee with `minimum_sell_haircut_onyc`.
Artifact: `C:/Users/TUF-GAMING/Documents/onre-fee-dan-excluded-2026-11-23.md`.
Final OnRe pass 23 Nov 2026: prop_amm suite 48/48 PASS after adding minimum-haircut and
settle-buffer tests. Minimum haircut rejects dust, fee lands once in fee vault, failed dust does
not move sell count. All accrual callers reviewed: take_offer v2, permissionless v2, prop buy,
prop sell and redemption use canonical/main offer; settlement after a main-offer change accrues
from the new offer with the (gross_yield - apr) formula. ADV-05 patch is consistent. OnRe is now
CLOSED as a target until a new deploy or source change: every reachable issue is either an
Immunefi known issue, an OtterSec resolved item, or an acknowledged excluded impact.
Artifact: `C:/Users/TUF-GAMING/Documents/onre-prop-amm-dan-adv05-2026-11-23.md`.

## Merkl (Angle Labs, self-hosted `security@merkl.xyz`) — 4 findings SUBMITTED 20 Nov 2026; addendum status with operator

Artifacts: `E:/C-relocated/Users/TUF-GAMING/.gemini/antigravity/scratch/merkl-bug-bounty/report.txt`/`.age`,
`MERKL_VALIDATION_GATE.md`, `addendum_body.txt` (original, 2 Low), `addendum_body_ops_only.txt` (revised, notes only),
`E:/audit/scope-programs/merkl.md` + `merkl-guard-results.md`. Repo frozen at `cdce25d`, no new commits as of 2026-11-22.
Submitted: F-01 Medium (wrapper retains unburnt tokens on allowed-recipient claims, live Base/Mainnet),
F-02 Low (PublicWrapperBase non-exclusive if branches, live TokenTGEWrapper), F-03 conditional Low
(Aave `ATOKEN_REVISION <= 4` rounding, third-party trigger), F-DEEP-01 Medium (predeposit wrapper tokens
burnt on transfer into DC while `creatorBalance` credits a phantom balance).
Gate result: all four pass the 7-question gate; Gate 0 negative controls 3/3 pass (fix patched in, PoC fails,
source restored byte-clean). Addendum's two severity-labelled items were KILLED at Q3/Q4 (no live instances;
holder-only privileged action) and recast as ops notes in `addendum_body_ops_only.txt`.
Do not re-audit these closed surfaces with evidence:
- XEF `0x4399aad9...`: partner (Xeffy) wrapper, unverified, out of scope (third-party). `totalLocked()` equals
  the XEF balance held by the wrapper to the wei (1,011,804.4265), `totalReleased()==0` = mid-cliff, so the
  "locked > mXEF supply" anomaly is fully backed, NOT a bug.
- ERC-4626 zero-share rounding in the vault wrapper: zero-share threshold = share price in asset-wei,
  manipulation cost scales linearly with total shares = economically impossible.
- AaveDebt Ink wrapper: debt-clip/consume pattern by design (repo's own `test_Success_NoDebtPullsNothingAndBurnsWrapper`,
  `test_Success_ClaimHigherThanDebtOnlyPullsTheDebt`); F-03 needs a third-party Aave revision, which the
  official scope excludes as a third-party-protocol issue.
- 18 pre-refactor 5458-byte instances: only semantic delta vs HEAD is the `amountToTransfer` refactor;
  no extra bug, but remediation must cover them.
- Code4rena 2025-11-merkl (`b7bd0e6`, 604 LOC core) M-01..M-03/L-01..L-05 and C4 2023-06 Angle
  H-01..H-03/M-01..M-07/L-01..L-07: read the DO-NOT-REPORT list in `MERKL_VALIDATION_GATE.md` before
  re-opening anything. `tokenWrappers` was OUT of C4 scope; current immutables postdate the audited commit.
Official scope is CLASS-based (named contracts + repo path), not an address list: in scope = audited deployed
DC/Distributor, deployed tokenWrappers (deprecated excluded), app/studio/API, reward computation; out =
third-party protocols/vendors, privileged access, DoS, known/prior-audit, non-production code, best-practice
without impact. Re-open only on a new repo commit or a Merkl reply; no production testing.

## BrainChain (self-hosted, security@usebrainchain.com / GitHub advisory) — SUBMITTED 23 Nov 2026, 2 LOW

Operator confirmed the email was sent to security@usebrainchain.com with the v3 report and SUBMISSION_BRAINCHAIN.zip attached. Exact send time and date: [TOFILL], no receipt captured. The program states a 22 Nov 2026 23:59 UTC deadline; do not claim timeliness until the operator pastes the delivery receipt or GitHub advisory ID. Unblocking condition: receipt or advisory ID. Do not re-open the hunt before a reply, a new commit, or a fresh deployment.

Artifacts: `E:/audit/bc-analysis/brainchain-result/` (laporan v3 PDF, patches, PoC + fixed-behaviour tests, email draft, SUBMISSION_BRAINCHAIN.zip), `E:/audit/bc-analysis/x402_api_audit/` + `api_sweep/` (raw HTTP evidence), `E:/audit/bc-api-tests/` (testnet/mainnet x402 probes), `E:/audit/bc-tools-audit/TOOLS_AUDIT.md` (MCP + worker source trace). Repo `usebrainchain/brainchain` @ `aca6c5f`, TaskBoard = tag v3.5.0 and 17 other deployed contracts = HEAD, byte-verified 18/18. Scope guard: `E:/audit/brainchain/scope-programs/brainchain.md`, active, 0 parse errors, 0 conflicts, ZERO chain rules by design because the official scope is repo-path + service URLs, not an address book. `--explain` denies every deployed address tested; the source/address-book conflict is disclosed in the file, so no on-chain target was treated as guard-authorized.

CONFIRMED, two LOW logic findings, both reproduced on deployed sources with passing Foundry tests (`ScratchAuditFindings.t.sol`, sha256 b1bf1eec…, 3/3 PASS):
- `ProposalBonds.expire()` returns the bond although an in-window keep exists, once a later out-of-window decision about the same call supersedes it: settle(K1) reverts StaleDecision, settle(K2) reverts BadDecision, expire() sees only K2 and refunds. Bond belongs to the proposer, no third-party funds. Live `count()==2`, both closed, not exercised.
- `WorkerStaking.release()` is not scoped to the slasher that placed the hold: a second listed slasher frees another board's hold, worker withdraws mid-task, slash burns 0. Live has one slasher only, so it needs an admin action first.

Both are hardening/credit tier by the program's own table (no third-party funds lost, no working exploit taking or locking money). Additive patches + fixed-behaviour tests: 9/9 pass, repo suite 396/396 still green on the patched tree, total 407/408 where the single failing test is our own pre-fix repro (reverts NotHeld as expected). Patches apply cleanly with `git apply --check`.

Dedup Q5 DONE: round 1's 10 paid bugs are tool/docs bugs (brainchain-mcp market-open flag, bond tool, verify formatting, CLI process handling, Node version floor etc.), listed on https://docs.usebrainchain.com/bug-hunt; none concerns ProposalBonds or WorkerStaking contract logic. The bug-hunt brief explicitly routes contract, brain API and x402 desk reports to the private channel, so these are not duplicates.

Verified-negative surfaces, do not re-derive without new code: all 14 in-scope contracts read in full, slither 0 real findings, repo suite 396/396, ~480k reviewer invariant calls, Medusa 6.92M calls / 33/33 properties, full event reconciliation of both chains (13.6k logs) with zero anomalies, live config exact match to docs. x402/brain API read-only (grades, tasks, /v1 chat, records, network.json): 400-before-pay on invalid bodies, fake payment payloads rejected with facilitator reason codes, challenge consistent with network.json and deployments, official `brainchain-verify` decision 962 = match. Mainnet was later in maintenance (503 "Nothing was charged") and testnet grading backend returned 502/524 after settlement; a bounded sandbox probe remains armed in the background, no funds charged so far. No findings payable from the tools: a 12-lead read-only trace of brainchain-mcp 0.23.1 and brainchain-worker 0.21.1 found no attacker-controlled path from brief/result/tool args to pay/sign/key/shell with attacker-directed recipient or exposed key. Payee, asset and network are pinned by `ours()` (`payments.js:142`) and the x402 policy (`payments.js:343-348`), amount is capped by `maxPrice` and `limits.take` before signing (`payments.js:341,354-360`), bond refunds are validated to the first-party desk (`bonds.js:121-141`). Key files are mode 600 with no echo (`server.js:46-88`), worker `--exec` shell uses the operator command with brief on stdin and a dynamic backtick fence (`work.js:83-96,322,398`), worker strips key vars from child env and scans output before upload (`work.js:98-104,419-468`). Prompt injection into the agent is real but cannot redirect funds or keys. DNS rebinding at `chain.js:641` is a theoretical residual with no funds/key sink. Full evidence: `E:/audit/bc-tools-audit/TOOLS_AUDIT.md`, independent REA pass in `REA_REPORT.md` (REA 6.10.1, 7 files, IPC/contextBridge nodes refuted by direct source cross-check).

## X roundup 23 Nov 2026: USDT0, Cap, Hyperlane Mailbox, BlazePhoenix - pass 1 only

Do not re-run pass 1 without new code or a newly resolved scope question. These are PARTIAL recon negatives, not full target closures.

- **USDT0 (Immunefi)**: `E:/audit/usdt0/PASS1-RECON.md`, guard `E:/audit/scope-programs/usdt0.md` (4 unambiguous addresses, 0 parse errors). Ethereum OAdapterUpgradeable `0x6c96de...` is a thin LayerZero OFTAdapter holding 3,768,925,328,571,754 USDT; destination Arbitrum OUpgradeable mints only through token `onlyAuthorizedSender` with live `oftContract()` == the scope OApp. `lzReceive` checks endpoint and peer. No unbacked-mint path found on the two representative legs. 35 of 47 scope assets and multi-chain addresses with ambiguous chain assignment are NOT covered.
- **Cap (Sherlock #114)**: `E:/audit/cap/PASS1-RECON.md`, guard `E:/audit/scope-programs/cap-sherlock.md` (repo-path scope, empty In Scope). Repo HEAD `695c828` matches remote main; npm install + forge build green; Slither 348 contracts / 110 results ALL INFO (`E:/audit/cap/slither-pass1.txt`); partial Forge run 5 passed on a 128,000-call Vault invariant before the 600 s local timeout. TVL $139.2M on 23 Nov 2026, down 31.6% in 30 days, inside the Spark/Compound peer range. Max reward needs ~$10M funds at risk at the 10% formula, arithmetically reachable. Full suite is the cloud-offload candidate.
- **Hyperlane (Immunefi)**: `E:/audit/hyperlane/PASS1-MAILBOX-RECON.md`, guard `E:/audit/scope-programs/hyperlane.md` (12 Arbitrum entries). Mailbox proxy `0x979Ca5...` impl `0x4826ce...` matches scope. `process()` checks version, destination and delivered id before ISM verification, writes effects before interactions; setters are onlyOwner. Default ISM `0xE09D...` is unverified on Sourcify with `moduleType()==2` and is NOT on the rendered scope list. That ISM, not Mailbox, is the next target.
- **BlazePhoenix**: `E:/audit/blazephoenix/PASS1-RECON.md`. Five repos cloned, heads 20-23 Nov 2026. Staking suite: 567 PASS / 0 FAIL in the first 600 s plus all 12 remaining files re-run individually with `Suite result: ok`; Slither 9 contracts / 161 results ALL INFO. `test/formal/MathLibFormalSpec.t.sol` uses Halmos `check*` and was NOT run. Author claims 2,074 tests pass at DEX commit `b9db56d` and 62 Hall-of-Fame credits. First-party conflict: campaign page and DEX SECURITY.md say payout after 15 Dec 2026, staking SECURITY.md lines 110-112 say after October 2026. BZPX had USD 0.00 on Basescan and no indexed GeckoTerminal pool, so reward value is unpriceable. Draft clarification emails: `C:/Users/TUF-GAMING/Documents/draft-pertanyaan-polymesh-blazephoenix-2026-11-23.md`.
- **BlazePhoenix API, MCP, SDK web pass (23 Nov 2026)**: `E:/audit/blazephoenix/web-scope.json` and `E:/audit/blazephoenix/WEB-P3-LEDGER.md`, raw live probes in `E:/audit/blazephoenix/web-evidence/`. Eight coverage classes recorded, no payable finding. 15 Worker API paths, 5 hosted MCP tools (all pure, no RPC or signing), 8 local MCP tools, SDK `verifySwapExactIn` and Worker `decodeQuote` both verify calldata field by field. No object/role/authz surface exists, so the authz matrix is N/A with evidence. `Access-Control-Allow-Origin: *` on read-only JSON with no cookies is not a finding. `/api/verify` takes only a fact id from the caller; the RPC URL comes from committed `/facts.json`, not from HTTP input. Observation, not payable: `quoteCacheKey` omits `nativeIn`/`nativeOut`, but `cachedExec` is only used by `handleQuoteFirstParty`, which the Worker never routes. Not covered: website with no published source, off-repo build of `/facts.json`, Halmos `check*` suite, Certora and mutant guard.

## Kamino #433 (Sherlock, Solana, $1M) — S1/S2/S5 filed, S4b proven, pass 4 open

Rules: PoC on LiteSVM/validator with signatures, faithful mainnet accounts, listed instances only, KYC, loss-of-funds only. Live since 16 Oct 2026.

Do not redo: scope TWAP tracker aliasing (S1), raw DEX price consumer (S2), deployed collateral release (S5), platform 6 patterns, obligation/borrow orders, autodeleverage victim hunt via debt reserve flags, elevation groups, flash fee, kvault/farms CPI, kfarms+kvault fuzz.

Pass 4 (2026-11-23) corrected the prior "no autodeleverage victim" line and found the real class: the deployed build parses `borrow_count=0` for 74,313 obligations, refresh zeroes their debt, and `liquidate` reverts `ObligationBorrowsZero` — 8,245 positions / $936,768 debt, 1,887 past threshold today. PoC `poc-onchain/s4b_liquidate_poc`, finding `findings/S4b-ghost-obligations-unliquidatable.md`. Evidence is two victims (one far below threshold, one already past it, `s4d_second_victim_poc`) plus a complement control that reaches the liquidation math and fails only `ObligationHealthy` (`s4c_liquidate_control_poc`); all three runs and hashes are in `poc-onchain/`. Same root cause as S5, so addendum rather than new submission unless Sherlock splits it. Second verified finding in pass 4: `deposit_and_withdraw` snapshots `initial_ltv` before refresh, so a stale (favourable-price) snapshot passes the `WorseLtvBlocked` gate. A/B on deployed bytecode: pristine 0.7061/0.6640 reverts 6093, stale 0.8035 succeeds at LTV 0.7061. Bounded Low because the unhealthy-LTV gate still holds. Finding `findings/S4h-deposit-withdraw-stale-ltv.md`, bundle `findings/submission/bundle-addendum/`.

Fixed-term rollover arithmetic is CLEAN so far, do not re-walk without new code: the window check uses `saturating_sub` (post-expiry rollover allowed by design), open->open is rejected so the `(None, None)` panic is unreachable, and the cross-reserve post-check requires `borrowed - repaid` < 1 unit with exact reserve deltas (`lending_checks.rs:757-900`, `state/obligation.rs:1236-1316`).

Lanes closed in pass 4: reserve-config integrity validator (thorough), instruction-set delta (no deployed-only handler; IDL 66 vs source 67, only `execute_obligation_order` is source-only), kvault as a scope-price lever (AUM in asset units, not USD, so S1/S2 do not move share price). Open/parked: scope consumers beyond kvault, S2 escalation (its demo market is not among the 52 listed markets). KLiquidity/yvault recon closed negative: the public audits repository held the current audit PDFs even though the source repo is private; the deployed ELF carries the audited fixes, all live withdrawal caps are far from exhausted, and invest/withdraw argument sweeps plus multi-withdraw splices produced no new bypass. Evidence: E:/audit/kamino/findings/yvault-recon-2026-11-24.md and yvault-semantic-probe-2026-11-24.md.

## Four previously untouched targets, pass 1 only (23 Nov 2026)

- **Noir Wallet (HackenProof)**: `E:/audit/noir-wallet/PASS1-RECON.md`. Four repos cloned, heads 20 Nov (extension), 17 Nov (zcash-wallet-wasm), 11 Nov (adapter), 26 Oct (SDK). Rep 50 gate passes for operator rep 60. Rewards USD 100-5.000, 90 business day reward SLA. Excluded known issues: BlockSec June 2026 Finding 10 (broadcast error handling) and Finding 12 (recovery scan start date balance sync). Signing-summary validation is schema, family, namespace, chain and operation bound with strict keys and bounded lengths. No build or dApp differential run, so no payable finding. Next gate is a signing-summary versus actual-transaction differential in the extension.
- **Paradex (Sherlock #344)**: `E:/audit/paradex/PASS1-RECON.md`. PARK on two named unblockers: Cairo toolchain absent (`scarb`, `starknet` missing in Windows and WSL) and no public Cairo contract repo under `tradeparadex`. Six Starknet addresses transcribed in the note; chain-scope-guard does not support Starknet. Audit depth is high (Cairo Security Clan x5, Zellic, Trail of Bits, HackerOne pentest) plus explicit Immunefi overlap exclusions. Do not spend more time until snforge and verified class source are available.
- **Spark (Immunefi)**: `E:/audit/spark/PASS1-RECON.md`, guard `E:/audit/scope-programs/spark.md` (12 rendered of 386 assets, chosen component SPARK_VAULT_V2_SPUSDT `0xe2e7a17d...`, guard authorized true). Deployed `SparkVault` implementation `0x1b992302...` source is normalized-identical to repo HEAD. Static read of `drip`, deposit/mint/redeem/withdraw, `_mint`, `_burn`, `take` and `setVsr` found no unprivileged path to value. `forge test` did not compile because nested submodules ship two conflicting `forge-std` copies. No fuzz run at pass 1. Pay in DAI via Maker executive spell, no KYC.
  Pass 2 unblocked the build in a scratch copy (`E:/audit/spark/vaults-clean`): six nested
  `forge-std` copies removed and an explicit `remappings.txt` written; `forge build` green.
  Full suite 98 pass / 2 fail, both failures missing table fixtures (harness debt, not protocol).
  Shipped invariant 30 runs x depth 100 = 3,000 calls, 0 violations, all ten handlers non-vacuous.
  Added harnesses: `test/DeepEdges.t.sol` (5,000-run tiny-deposit rounding plus an extreme
  warp/rate probe; `drip()` only fails after ~50 years at admin-set 100% APY, non-payable),
  `test/FiniteCap.t.sol` (10,000 runs on maxDeposit/maxMint boundaries, clean; accrual pushing
  totalAssets above a deposit cap is by design), `test/CoverageClosure.t.sol` (8 tests covering
  EIP-712 permit, ERC-1271, transfer/transferFrom, referral overloads, dynamic roles and upgrade,
  all pass). Two read-only subagents found no unprivileged funds-loss path. Verdict: verified
  negative on all cheap surfaces, no payable finding. Ledger: `E:/audit/spark/PASS2-BUILD-AND-FUZZ.md`.
  Remaining: a deeper cloud invariant campaign and reading the four audit PDFs in `audits/` for
  the DO-NOT-REPORT list.
- **Polymesh (self-hosted)**: `E:/audit/polymesh/PASS1-RECON.md`. Previously only a clarification draft, now recon done. Live release v8.2.0 on 13 Nov 2026, recent fresh commits in `pallets/confidential-assets` and DART v1.0.0. Up to USD 40k, case-by-case and discretionary, no minimum, email submission, strict personal-validation rule for AI-assisted work. WSL Rust 1.100 exists but `wasm32-unknown-unknown` and Substrate tooling are absent. No clone or build. Do not install the heavy stack before the operator confirms the AI rule.

## Other parked targets (brief)

- **Metric** (Immunefi $500k): oracle pusher delegation already audited by Zellic x2; pool solvency
  + binTotals invariants verified-negative over **~2.84M calls** (local + Box). Artifacts:
  `E:/audit/metric/{FORK-ORACLE-TRACE.md,POOL-INVARIANT-TRACE.md}`. SwapMath "fix pending" = out.
- **Base Everest** (Cantina $250k): Solidity scope exhausted (9 prior audits, Slither clean);
  Rust/devnet PoC path heavy and blocked. `E:/audit/base-everest/`.
- **Arcadia**: 5 surfaces verified-negative (CowSwapper, Metadex03, slippage math 600k evals,
  fork-state 5120 ops, debt side). `E:/audit/arcadia/*-TRACE.md`.
- **rNEAR / Rhea**: verified-negative pre-hack; post-hack burrowland is KYC-gated and needs a paid
  Medium report. `E:/audit/rhea/RNEAR-TRACE.md`.

## Cross-checking a shared target list against prior work

When handed a pasted list of bounty programs and asked which ones are untouched,
classify every entry from evidence, not from memory:

1. Parse each entry into (program name, platform, announcement URL or status id).
   Match by that identity, not by project name: a build/integration bounty and a
   bug bounty for the same protocol are different programs, and a closed build
   bounty does not mark the bug bounty as worked. One org can host several live
   bounties with different slugs and scope, so a rejection or parked verdict on
   one slug says nothing about a sibling slug: compare the exact slug and the
   in-scope assets before transferring a verdict.
2. Batch the history check. For more than a few targets, query the Hermes
   `state.db` read-only with sqlite3 (`sqlite3.connect('file:' + path +
   '?mode=ro', uri=True)`) and group `messages` by anchor, session and role
   instead of issuing one `session_search` call per name.
3. Anchor on distinctive strings: platform + program name, an announcement
   status id, or a repo path. Never substring-scan short generic tokens like
   `exactly`, `cosmos`, `metric` or `raac` — case-insensitive matches hit
   ordinary prose and unrelated strings, so every hit needs context checked.
4. Promote a hit to "worked on" only with artifact evidence: a clone under
   `E:/audit` or `E:/bug bounty`, a TRACE/notes/verdict file, a fuzz harness, a
   PoC, or an entry in this register. A mention in a research PDF, aggregator
   dump or scouting list is a mention, not work.
5. Report both buckets with counts and evidence paths, and label depth
   separately: surveyed with no finding, active campaign, or finding submitted.
   State plainly when a program appears only in a list.
6. Close with a short numbered set of next actions (vet one target, rank the
   untouched ones by PoC feasibility, or resume the active campaign); this user
   picks from numbered options.

Absence from this register is not proof a target is untouched: confirm with
session history and repo directories before telling the user it has never been
worked on.

## Procedure lives in the companion skills

Do not re-derive campaign procedure from this register. It is in `audit-competition-hunt`:
acquisition and build (Windows npm git-dep workaround, public exports missing the test tree),
reading `SECURITY.md`/`Known_issues`/`audits/` first and mining accepted-behaviour entries for the
invariants they assert, working an audit finding as a lead plus the sibling-gap guard scan,
non-vacuous invariant campaigns, Anchor `init_if_needed` semantics, and Box offload quirks.
Code-age vs listing-age verification is in `new-feature-bug-hunt`; rep/KYC/deposit gates in
`bugbounty-target-selection`.

Register-specific rules:
- Before recording "no source available" for a target, search the protocol's public audits repository and read its newest PDF. Audit reports supply function names, patch references, known-issue status and live-state coordinates even when the source repo is private; skipping that step parks a target on a false premise. Confirm the newest audited patches are present in the deployed ELF by grepping distinctive error strings, and treat acknowledged findings as coordinates for a NEW variant, never as findings themselves. When a PDF has no text layer, render its pages with `pymupdf` from the project venv and read the rendered images with vision analysis before closing the known-issues list; an unreadable audit is not the same as an absent audit.
- Record a verdict with its EVIDENCE PATH and the call/evaluation count, so a future session can
  trust the negative without re-running it.
- When the fresh-target survey yields no payable target, say so plainly and offer monitoring
  instead of forcing a weak one. A demo/preview contest, a post-audit Critical-only contest, or a
  points-based reward is not a substitute for a freshly deployed, unaudited, payable scope —
  spending a session on one is worse than reporting that the window is empty.
- An empty 30-day launch survey is not automatically an empty window: also check live payable
  programs outside the aggregator and watchlist that already have local source and an unfinished
  phase. A self-hosted program qualifies when its official docs state both a reward and a smart
  contract scope; verify those from the docs, not from an aggregator. Prefer that over forcing a
  weak fresh listing, because the code and the reconnaissance work are already on disk.
- Before starting a target whose source is not already local, check verified-source availability
  for its in-scope addresses and record `exact_match` status plus the bytecode-match result.
  A tree that does not byte-match deployment makes the target unauditable until verified source
  is obtained; do not spend a session deriving findings from it. If Sourcify returns 400 and the
  address is not a proxy, check Blockscout's smart-contract API before calling the contract
  unidentified — a scope can mix Sourcify-verified and Blockscout-only entries.
- When new code re-opens a parked target, extend that protocol's existing entry with the new
  surface's verdict; do not create a second entry for the same protocol. Search the register for
  the protocol name before inserting anything: long register files make an existing entry easy to
  miss, and a duplicate section leaves contradictory verdicts for the same protocol.
- A target whose listing is new but whose pinned code is old is not a fresh surface — note the
  code age in the entry so the next selection pass does not shortlist it again.
