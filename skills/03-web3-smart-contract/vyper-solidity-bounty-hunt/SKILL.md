---
name: vyper-solidity-bounty-hunt
description: "Use for Vyper/Solidity EVM bounty hunts: build, PoC, report."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [EVM, Vyper, Solidity, Foundry, bugbounty, PoC]
    related_skills: [chain-scope-guard, evm-bounty-source-audit, pdf, hermes-mcp-mantis-login]
---

# Vyper/Solidity EVM bounty hunt

## When to Use
Use when a target is a source-available EVM protocol with Vyper core and Solidity periphery or allocator repos. Pair with `chain-scope-guard` (load before any on-chain probing), `evm-bounty-source-audit`, and `pdf` for delivery. The operator communicates in Indonesian, dislikes em-dash, and picks numbered options. When several options are chosen at once, honor an explicit ordering word and finish one before starting the next; with no ordering word, execute every selected item to completion before replying. Keep reports honest: a falsified claim must be rewritten in every artifact that carried it.

## 1. Gate and acquire
- Read the live platform page in a real browser, then fetch the authoritative record through the platform MCP (`get_bounty` on Mantis). The MCP `inScopeRules`/`outOfScopeRules` are more detailed than the rendered page and can exclude code not deployed on mainnet and unendorsed markets; reconcile both before hunting.
- Transcribe scope into `chain-scope-guard`; run `--audit` and `--explain` on candidate addresses. Repo-only scope means no live address is authorized; work on forks only.
- Clone with native Windows git into `E:/audit/<name>`. Record HEAD SHA. `git submodule update --init --force --depth 1` is enough; recursive init can hang for 400s on deep chains.
- When deployed bytecode does not match HEAD, recover the historical source before disassembling: `git fetch --unshallow`, `git log --all --oneline -- <path>`, `git show <commit>:<path>`. Compile each candidate in isolation and compare the executable bytes; a difference only in the metadata IPFS hash still means an exact code match. Compile with stubs if needed and state that the stubs caused the metadata difference.
- If a nested `lib/<repo>/out` is missing for `deployCode` tests, copy the built `out/` from the main clone rather than rebuilding the nested repo (Vyper import paths break there).

## 2. Build and test
- **Preflight binary identity before any build or cast call, cheaply.** `forge`/`cast` are Foundry through the `~/bin` shims on this host, in git-bash and in WSL both; the Atlassian CLI answers to `forge-atl`. Still assert `forge --version | grep -q 'forge Version:'` and `cast sig 'transfer(address,uint256)'` returning a selector at the start of a shell. A bare `15.1.0`, a `manifest.yml` line, or a `No such file or directory` that names `/mnt/c` means the shim was bypassed, not that the repo is broken.
- Any helper wrapper dropped in `~/bin` must be dual-mode, because `~/bin` precedes `~/.foundry/bin` for git-bash and WSL alike. The existing `_foundry-dispatch` tests the Windows-side `/c/...` path first and falls back to `/mnt/c/...`, which is the order that works in both shells; copy that shape, and never hard-code a single mount prefix.
- Install Vyper on this host with `uv tool install vyper` (0.4.3). Bare `forge` is Foundry via the shim; there is no PATH export needed, and prefixing `.foundry/bin` is still harmless.
- Run `forge build` and `forge test` from the directory that contains `foundry.toml`. A top-level clone can hold several independent Foundry projects, and invoking forge from the parent produces source-not-found errors that look like a broken toolchain.
- Generate checksummed address literals with `cast to-check-sum-address <lowercase-hex>`. Lowercase literals are rejected as invalid checksum even when wrapped in `vm.addr(uint160(0x...))`, and a batch of twenty such literals produces twenty misleading syntax errors. Declare `interface` blocks at file scope, never nested inside a contract. If Foundry reports stack-too-deep, drop redundant locals and repeated terms inside `assertEq`; the first compile often uses native test linking and hides it until cache is cleared.
- Heavy fork PoCs can exceed Foundry's default 2^30 gas limit; the pinned forge-std has no `vm.txGasLimit`, so set `FOUNDRY_GAS_LIMIT=10000000000` in the shell before `forge test` instead of putting a cheatcode in the test. With a high gas limit, 1900-trove fork setups finish in minutes rather than timing out.
- `forge build` both repos. Then `forge test` with an archive RPC. `https://eth.drpc.org` serves historical state but rate-limits large suites; `https://rpc.flashbots.net` prunes old blocks. Tame suites with `FOUNDRY_FUZZ_RUNS=4` and run contracts one at a time.
- Run Slither on the Solidity repo and filter to protocol-owned files. Published audit PDFs can be text-extracted with pypdf; mine their finding headings before hunting. Also sweep hidden in-repo review directories (`.audit/findings/`, `audit/`, `reviews/`) and the test tree for pinned regression names: internal verified findings never published as PDFs are still prior art, and a repo test that locks in the behaviour makes a 'new' finding a duplicate.

## 3. Hunt in parallel, verify sequentially
- Dispatch 3-4 READ-ONLY reviewers with distinct lenses (core Vyper, Lender/ERC4626, allocator/periphery), an explicit exclusion list of already published findings, and a JSON schema. Tell them not to run forge build/test.
- Give each agent that BUILDS or TESTS its own isolated copy of the repo. Parallel `forge build`/`forge test` runs sharing one `cache/` and `out/` collide; read-only reviewers may share the source tree, build-running agents (PoC, fuzz campaign) must not. Verify their result by rerunning it from a clean build in that agent's own copy.
- Treat every reviewer result as a claim. Reproduce with a focused PoC before writing anything.
- When the protocol defines its own EIP-2718 transaction type that standard tooling cannot build, construct the signed envelope from the consensus field encoder and sign the domain hash with `cast wallet sign --no-hash`; the recipe and the misleading 'unfunded sender' failure mode are in `references/custom-typed-tx-poc.md`.
- Bound stress experiments before paying for them. A fork test that must create over a thousand stateful positions can consume several billion gas and tens of minutes of CPU; run a cheap mock-based differential PoC first and only scale up when the cheap version already shows a loss mechanism. An unchanged victim balance is a negative only AFTER the triggering condition is verified; check ordering, request size, metric freshness and gas budget before writing a retraction.
- In redemption-frontier PoCs that rely on a per-call trove cap, give the drain position the HIGHEST interest rate so the walk reaches the low-rate frontier first, and size the redemption above the debt held by the capped frontier. A low-rate oversized drain absorbs the whole request and makes the cap never fire. Measure the victim on underlying assets (`balance + total_debt - unclaimed_fees`) divided by total supply, not on cached `convertToAssets`; a cached PPS has not moved inside the same transaction even when the true claim has.
- Strong PoC pattern: first a mock-only test isolating control flow, then a fork test with real contracts. If a claimed impact cannot be measured (cash shortfall, cross-user divergence), retract the severity claim and record the negative.
- Before using a deployed address in a fork PoC, call `eth_getCode` at the pinned fork block. On the CLI the subcommand is `cast code <addr> --rpc-url ...`; `cast eth_getCode` is not valid in forge 1.9. Repo harnesses often cache a block that predates the deployment; override the harness `setUp` with a later block when needed.
- When a strategy constructor stores a router immutable, a locally deployed factory creates strategies pointing at the local router, so calls fail with `!exitRouter` even after the test variable is repointed at the live router. Swap in the live factory as well, so the constructed contract stores the live address.
- Check reachability through live configuration, not just code existence. Read the consumer's config getter on the deployed instances (e.g. `EXIT_ROUTER()`, `DUTCH_DESK()`), then confirm the vulnerable function's selector is present in THAT implementation's `eth_getCode` (`cast sig` plus a hex grep). An audited contract sitting unused while live consumers point at an older build closes the finding even when the code-level defect is real; record the getter, live address, bytecode length and selector check as the reachability evidence. When comparing bytecode hashes, hash the hex text with the trailing newline stripped: a shell redirect from `cast code` adds a newline and produces a different hash from the same bytes.
- Absence of on-chain setup events (for example zero `SetRouter` events on all deployed zappers) can close a code-level issue completely. Inactive deployments with zero activation and zero debt do not make a shared-component collision reachable either.

## 4. Deliverable
- One English paste-ready draft per distinct ROOT CAUSE: Title / Severity / Vulnerability detail with `file:line` / Impact / PoC with verbatim commands and output / Recommendation / Honest bounds / Evidence. If the operator asks to append a secondary finding, include it as a clearly labelled "related observation" that is explicitly not part of the severity claim; keep the primary root cause single so triage stays focused.
- Machine-verify every `file:line` citation with a script before shipping. Verify PoC line references too.
- Indonesian PDF via the `pdf` skill from a JSON spec, render a page and vision-check for clipping. One operator README in Indonesian is the only file with instructions. Add a judge appendix with facts only.
- Generate `MANIFEST.sha256` by script over all bundle files and verify with `sha256sum -c` in the same call. Report the OK count and zero FAILED.
- Default to letting the operator handle accounts, KYC, deposits and public submission; show the complete paste-ready draft first. If the operator explicitly delegates a specific submission after reviewing that draft, post it through the platform MCP and report the returned submission ID. For the Mantis payload shape, use the Mantis submission reference in the evm-bounty-source-audit skill.
- `submit_report` rejects severities absent from the bounty reward table. Flex offers only critical and high, so a medium payload returns `invalid_severity`; never silently upgrade severity to force a submission.
- For rating disputes, prior-art rebuttals, and PoC proof-strength upgrades, follow `references/severity-and-evidence.md`. Record every follow-up ID next to the submission ID so the audit trail is complete.

## Flex-specific pitfalls already paid for
For a scope-compliant fork harness that uses live routers, factories and endorsed markets, see `references/fork-harness-recipes.md`.
- Known Mantis issue: partial redemption burns more shares than collateral auctioned due to the 1000-trove cap in `trove_manager.vy`. It is excluded; many other candidates (underwater redemption DoS, re-kick repricing, upfront-fee manipulation, stale-PPS callback) are published in bundled audits.
- `flex-allocator` is the fresher surface. Its `ExitRouter` snapshots a shared DutchDesk nonce once per strategy, so multi-strategy exits check every collateral minimum against one stale auction id.
- `Lender._preWithdrawHook` redirects auction proceeds to the user; `TokenizedStrategy` books a synthetic ~100% loss, forcing `_maxLoss = MAX_BPS` on the curated exit path.
- `StrategyAprOracle` uses `uint256(int256(totalAssets) + delta)`; explicit cast wraps instead of reverting.
- SwapExecutor reentrancy is real at primitive level but unreachable: no deployed zapper has a whitelisted router.
- Before building a multi-strategy PoC, verify from the team's docs or triage history that a curated vault can actually hold several strategies wrapping the SAME Lender. Flex triage closed the ExitRouter nonce-aliasing finding as duplicate partly on the ruling that curated vaults will not have that topology, so a PoC built around it can be terminal-negative regardless of the measured loss.
