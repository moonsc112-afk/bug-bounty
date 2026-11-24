# Campaign ledger (verifiable outcomes, not to be repeated)

Each entry is a completed engagement backed by files under `E:/audit/<target>/`.
Before resuming any of these, re-read the LIVE program page: gates and scope
change. A parked verified-negative is not an invitation to re-run the same hunt.

## Maple (Immunefi, 22 Nov 2026)

- Scope: 40 assets, max $500k, PoC + KYC required, live since Jan 2022.
- Audits: Sherlock Sep 2026 (4 low/info), Cantina Oct 2026 (5 low + 4 info).
- Post-audit commits were formatting or fixes already in the reports.
- Baseline: 1,702 core tests passed (strategy-manager 283, allocation 348,
  defi 390, globals 202, pool 357, withdrawal queue 122).
- Negative PoCs: 4/4 in each of two repos, expected trusted-role reverts.
- Fuzz: Medusa 14/14, Echidna 13/13 (50k calls, 16,959 unique instructions).
- Deployment: 18 active Strategy Managers, caps and registry consistent.
- Yield/multi-pool integration test passed with 1-unit rounding tolerance.
- Artifacts: `E:/audit/maple/maple-deep-dive-2026-11-22.md`,
  `maple-final-2026-11-22.md`, `maple-yield-multipool-2026-11-22.md`.

## Metric (22 Nov 2026)

- No KYC, PoC not required, $50 submission fee, novice gate, max $500k.
- Rule: local forks only; no testing with pricing oracles or third-party contracts.
- Parked at recon: lighter gate than Paxos but no work completed. Do not claim
  a verdict without running the fork tests.
- Artifact: `E:/audit/metric/VERDICT-METRIC.md` plus oracle/pool invariant traces.

## Veda / Boring Vault (Sherlock, live 17 Nov 2026, 22 Nov 2026)

- Max $1M, $250 stake per report, PoC against live fork, KYC at payout.
- 122 scope entries, 86 unique addresses, 11 chains. Config and code both in
  scope; trusted-role-only bugs are out of scope, but giving an unprivileged
  address a trusted capability IS in scope.
- Known issues close yield-streaming asymmetry, empty-vault states,
  performance-fee net posting, queue pricing, hashed requests, frozen
  deny-listed shares, `shareLockPeriod=0`, rate pause, redeem-mint path,
  independent cross-chain rates.
- Largest mapped vault: Optimism Ether.Fi Liquid ETH, $74.8M.
- Verified negative: EOA has no trusted capability on manager vault control;
  decoder semantic tests 7/7 passed (OFT/CCIP/MPortal under-pin checks);
  decoder used by the live vault actually pins every address-bearing argument.
- Deployed vs HEAD: vault 13/13 files same, manager 16/18, decoder 0/27,
  accountant 15/16, teller 17/19, delayed withdraw 18/19, lens 16/19.
  Deployed decoder is OLDER: rejects OFT compose and has no SVM CCIP.
- Accountant fee math identical despite managementFee→platformFee rename.
- Old Teller is covered by Seven Seas A-10 (SHA256 match to commit
  `35433417`), A-7 (`9c6e1e44`) and Arctic/A-4 (deny list, supported assets).
  All its authority capabilities were revoked at Optimism block 149878153;
  owner is zero. No callable surface remains.
- Artifacts: `E:/audit/veda/veda-recon-2026-11-22.md`,
  `veda-decoder-semantic-2026-11-22.md`,
  `veda-deployed-vs-head-2026-11-22.md`,
  `veda-deployed-components-2026-11-22.md`,
  `veda-teller-old-audit-coverage-2026-11-22.md`.

## Exactly (Cantina, recon 23 Nov 2026)

- Program: $10k-$25k Critical (10% of damage cap), $5k-$10k High, $50 refundable deposit, KYC to join, PoC required, self-triaged, 60-67 reports in first 11 days. TVL ~$10.6M.
- Oct 2026 commits are deployment artifacts only (deployments/base/*.json, .openzeppelin/base.json, hardhat config), NOT new .sol logic. Market.sol last functional change Apr 2026; Auditor.sol Sep 2026 NatSpec only.
- The genuinely new code (Auditor non-collateral PR #815, Morpho FlashLoanAdapter + PriceFeedInverse) was audited by ABDK on 17 Sep and 19 Oct 2026; both PDFs are public and linked by the program page as known issues. Do not re-report acknowledged CVF items.
- Scope guard: E:/audit/scope-programs/exactly-cantina.md, 54 active rules, audit clean.
- PoC EXECUTED (6 tests pass, Base fork block 61058483, E:/audit/exactly/poc): checkLiquidity does pass for a wARS-only account and even an empty account, BUT Auditor.accountLiquidity returns 0/0 and a real floating borrow reverts 0x15d58176 InsufficientAccountLiquidity. collectCredit forwards msg.sender as borrower, so on-chain Auditor check always applies. No theft, freeze or unbacked debt possible. RETRACTED the earlier High/Critical hypothesis.
- Artifact: E:/audit/exactly/verdict-exactly-2026-11-23.md. PARKED. No payable finding. Reopen only on new deployment/implementation/scope.

## Yearn (Sherlock, sweep 23 Nov 2026)

- Scope guard E:/audit/scope-programs/yearn-sherlock.md, 63 rules active. TVL top: USDS-1 $18.3M, USDC-1 $13.5M, DOLA-sUSDe $9.3M.
- Live versions 3.0.2/3.0.3/3.0.4, no 3.1.1. Transfer-hook commit 89ab996 is NOT deployed.
- Deployed USDC-1 source byte-matches repo commit 104a2b233b (3.0.4), so the "in-scope contracts unaudited" program claim does not hold for core code. ChainSecurity audit read: no High/Critical, 2 Medium fixed, accepted risks listed.
- Static pass over _redeem/deposit/mint/withdraw plus live config: no unprivileged payable candidate. No PoC, no $250 staked.
- Artifact: E:/audit/yearn/sweep-2026-11-23.md. PARKED.
- Follow-up EXECUTED: compiled 3.0.4 bytecode + EIP-1167 clone harness (E:/audit/yearn/harness). 4 tests pass locally and on mainnet fork, incl. 1000 fuzz runs over payout/multiplier/gain/queue order. Redeem bound holds; no over-withdraw. Artifact E:/audit/yearn/redeem-bound-results-2026-11-23.md. Still PARKED, no $250 staked.
- Second follow-up EXECUTED: withdrawn > current_debt reproduced (200M surplus unaccounted after unreported gain), oracle-dependent maxRedeem mock fuzz 1000 runs. 6 tests pass local + fork. No payable path; live oracle PoC blocked by program rule. Artifact E:/audit/yearn/redeem-bound-followup-2026-11-23.md.
- Third follow-up EXECUTED: verified 3.0.4 has NO sweep() entrypoint (78 external funcs, selector 0x01681a62 reverts), so the proposed two-step capture via sweep is invalid. Alternative next-depositor path tested: surplus stays stranded, later depositor cannot realize it. 8 tests pass local + fork. Same artifact updated. Yearn remains PARKED.
- Version check: 3.0.2 (f869f7e4ef, 74 funcs), 3.0.3 (92716ed729, 78 funcs), 3.0.4 (104a2b233b, 78 funcs) all lack sweep in source and ABI; eth_call 0x01681a62 reverts on live USDS-1/DOLA-sUSDe/USDC-1. Artifact E:/audit/yearn/sweep-version-check-2026-11-23.md.
- 0.4.x check: six in-scope 0.4.3/0.4.5/0.4.6 vaults are EIP-1167 clones of implementation 0x910e6E8c... (testVault, Vyper 0.3.3). It DOES have sweep(address,uint256), but `assert msg.sender == governance` and proceeds go to governance, never to total_idle. Governance = 0xfeb4acf3... trusted. No unprivileged capture path. Artifact E:/audit/yearn/sweep-04x-check-2026-11-23.md. Yearn PARKED.
- WATCH INSTALLED: cron job 16d941be2970 'Yearn deployment watch (Sherlock #30)', every 360m Asia/Jakarta, no_agent script yearn_watch.py. Silent unless 7 watched addresses' code/impl/apiVersion, 2 repo HEADs, or yearn.fi/v3 address set change; on change reruns forge fork tests. Baseline verified, quiet tick and simulated-change tick both tested. README E:/audit/yearn/watch/README.md.

## Beanstalk (Sherlock)

- Scope guard `E:/audit/scope-programs/beanstalk-sherlock.md`, 20 active rules:
  1 Ethereum and 19 Arbitrum addresses. Sherlock triage and mediation only;
  Beanstalk pays directly in BEAN on Arbitrum, no KYC, $250 deposit per report.
- Fresh source is the EBIP-21 sync in `UnripeFacet`, `EnrootFacet`, `LibUnripe`,
  `LibLockedUnderlying`, `System` and new `InitProtectedUnderlying`. Beanstalk's
  public audit list stops before this change; Basin audits are 2023.
- Baseline in Docker sandbox: 7/7 protected-underlying tests pass, with two
  test-only fixes for case-sensitive imports and nested diamond revert data.
- Enroot validation harness: 6/6 pass, including fuzz 256 runs for phantom stem
  and stem above tip. Duplicate stem, mismatched lengths, amount zero and
  cross-user enroot all revert. Happy path NOT verified because the mock
  deposit invariant blocks it; do not claim enroot validity from this harness.
- Protected-boundary harness: 9/9 pass, including fuzz 256 runs. A chop whose
  quote exceeds remaining local backing reverts; a small chop still pays its
  full quote. Confirms liveness/freeze, not over-withdraw. Custodian can restore,
  so permanent-freeze severity is weak.
- Deployed bytecode: all 20 scope addresses have nonzero code on the correct
  chain and recorded keccak hashes, but none matches local Foundry artifacts.
  Etherscan V2 verified 19/20; the diamond's verified `System.sol` is stale and
  lacks `protectedUnderlying`, but `getProtectedUnderlying` on the live diamond
  returns nonzero. EBIP-21 is live; do not park on stale verified source.
- Custodian is a Safe 1.4.1 (2-of-3); Beanstalk owner is a Safe 1.3.0 (5-of-9)
  with no overlapping owners. Only `InitProtectedUnderlying` writes the
  custodian and it refuses replacement; no public replacement proposal found.
- Hardhat suite: baseline 21/21 pass; with a 50% protected split added through
  `InitProtectedUnderlying`, 23/23 pass. Small urLP convert succeeds, a large
  chop reverts on local backing. Same liveness bound on the native fixture; no
  over-withdraw.
- Artifacts: `E:/audit/beanstalk/TARGET-VETTING-2026-11-23.md`,
  `E:/audit/beanstalk/ebip21-intake-2026-11-23.md`,
  `E:/audit/beanstalk/ebip21-validation-2026-11-23.md`,
  `E:/audit/beanstalk/hardhat-protected-final-2026-11-23.md`.
  PARKED, no finding and no $250 staked. Reopen only on a new deployment,
  implementation change, or scope change.

## Rhea Finance SC (HackenProof, recon 20 Nov, rechecked 24 Nov 2026)

- Rep 50, fee $10, PoC, 24h, first reporter. Program rules add KYC plus at
  least 1 paid Medium-or-higher report to access `hackenproof-public/burrowland`
  and the other three scope repos. Extra KYC at payout. This gate is invisible
  in the dashboard's `b_by_kyc=false` filter.
- rNEAR LST is a VERIFIED NEGATIVE: U256 share rounding, `#[private]` validator
  callbacks, conserved reward shares, symmetric validator accounting.
- The April 2026 $18.4M slippage double-count in `margin_trading.rs` is public
  and out of scope. The only value left is the post-hack burrowland fix, which
  is KYC-gated.
- Artifacts: `E:/audit/rhea/RHEA-SCOPE.md`, `E:/audit/rhea/RNEAR-TRACE.md`.
  PARKED until the operator completes KYC and earns a paid Medium report.

## Flow EVM Bridge (HackenProof, recon 24 Nov 2026)

- No rep or KYC gate, $1 fee, PoC, 24h first reporter. Only Critical pays $10k;
  the Flow EVM Bridge target is capped at $5k and High/Medium/Low pay $0.
- Repro must use latest Flow CLI emulator or FLITE localnet, full logs, exact
  commit hashes, attacker-only signed transaction. Unit tests, static-only,
  front-run-only, imported contracts and AI reports without PoC are rejected.
- PauseType bypass issues #198/#199 and #203/#204 are public and fixed in
  `main` (`isTypePaused(updatedCadenceAssociation)` in `FlowEVMBridge.cdc`).
  PR #211 is open and shows mainnet contracts still differ from `main`, with
  that pause check only coming in the next upgrade. Do not submit disclosed
  variants.
- Flow CLI v2.19.0 is installed at `E:/tools/flow-cli/flow-cli.exe`; source pinned
  at commit `8cdf3189` in `E:/audit/flow/flow-evm-bridge`. The bundled `flow test`
  harness cannot resolve core-contract imports on Windows: mainnet:// sources
  are mapped to local `imports/<address>/`, then emulator accounts are still
  missing even with `--fork=mainnet`. The real blocker is that `flow test`'s
  in-memory backend has no `InternalEVM`, so EVM-dependent contracts cannot load.
  WORKAROUND VERIFIED: run `flow emulator --contracts --evm-test-helpers`, create
  `flow-poc.json` with deployable contracts, then use scripts or transactions.
  `FlowEVMBridge` and `FlowEVMBridgeUtils` deploy to `0xf8d6e0586b0a20c7`; the
  conversion script returns 24244814 for 24.24481405 at 6 decimals and
  25470000000000 for 0.00002547 at 18 decimals. Next: real bridging transaction
  with compliant 6/18-decimal ERC20. BLOCKER: `flow evm gateway` runs on port 3000
  (chainId 0x286) but `forge create` returns `-32000 no signing keys available` or
  `contract was not deployed`; `cadence/transactions/evm/deploy.cdc` with ExampleERC20
  bytecode fails with EVM error 302. Funded the derived EVM address with 5 FLOW,
  did not help. Fix COA/EVM signing or use FLITE before attempting bridging tx.
- Artifact: `E:/audit/bedah-rhea-flow-hyperbridge-2026-11-24.md`.

## Hyperbridge / solidity-merkle-trees (HackenProof, recon 24 Nov 2026)

- No rep or KYC gate, $5 fee, PoC, 24h first reporter, platform-only disclosure.
  Critical $7k-$10k, High $3k-$3.5k, Medium $500-$700, Low $0.
- SRLabs Solidity audit found 14 issues (1 critical duplicate-leaf multi-proof
  bypass, 3 high, 5 medium, 4 low, 1 info) against hyperbridge `4580218` and
  SMT `135f2251`. ISMP baseline found 1 high, 3 medium, 1 low, 3 info at
  `922aafb`, mostly trusted-role items risk-accepted.
- FIX VERIFIED: SMT HEAD `6bbc83d` adds `UnsortedLeaves` / `UnconsumedLeaves`.
  Cloned to `E:/audit/hyperbridge/solidity-merkle-trees`, installed forge-std,
  ran `forge test`: 22/22 passed including duplicate-leaf and MMR forgery
  regressions. The merkle library is a verified negative for those classes.
- EVM baseline: sparse clone at `E:/audit/hyperbridge/hyperbridge`. npm install
  fails on git deps (EPERM) and pnpm rejects unsigned git tarballs; registry
  deps were installed in `E:/audit/hyperbridge/npmdeps` and copied in, forge-std
  v1.16.1 cloned separately, and 7 files needing unavailable git packages were
  renamed `.skip` locally. `forge build` succeeds; with
  `MAINNET_FORK_URL=https://ethereum-rpc.publicnode.com`, `forge test
  `--match-path 'tests/foundry/IntentGateway*'` gives 307/307 passing.
- Unprivileged probe: `tests/foundry/IntentGatewayV2UnprivilegedProbe.sol` tests
  partial-fill then third-party cancel conservation, input-token relabeling, and
  over-quote escrow. All pass, no exploit found. Full regressor now 311/311.
  Fresh hypothesis still needed for a payable finding. Next area: `SolverAccount.sol`
  and the post-audit ERC-4337 validation code. Slither 0.11.6 + solc 0.8.30 flags
  `_withdraw` reentrancy, but all reachable entry points are `nonReentrant`, so it
  is a false positive.
- Fresh surface is the post-audit EVM rewrite: Sep-Oct 2026 per-leg escrow,
  owner pause, solver quotes, relayer whitelist, gateway release 4 with
  ERC-4337 and Permit2. Audit does not cover it.
- Repo pins Rust 1.99.1 (WSL has 1.100, 1.96, nightly). Monorepo is large;
  offload full Rust campaigns. Artifact:
  `E:/audit/bedah-rhea-flow-hyperbridge-2026-11-24.md`.

## Practical rule

When a ledger entry shows a verified negative with both negative PoCs and a
dead authority, stop. Re-open only if a NEW deployment, new commit, or new
scope entry appears. Do not re-read the same source looking for a different
answer.
