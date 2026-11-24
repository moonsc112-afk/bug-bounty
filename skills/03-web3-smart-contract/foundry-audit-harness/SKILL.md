---
name: foundry-audit-harness
description: "Use when building Foundry invariant harnesses for audits."
version: 1.0.0
author: Hermes Agent
license: MIT
yaml_schema: 1
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [BugBounty, Foundry, Invariants, SmartContract]
---

# Foundry Audit Harness Builder

## When to use

Load for ANY smart-contract audit engagement where reusable invariant and fuzz harnesses are useful before or alongside scope access: Sherlock Audit Engine, Immunefi, Cantina, CodeHawks, HackenProof. Also load when adapting an existing harness to a pinned repo commit.

## Core idea

Build pattern-only reference mocks FIRST, with every suspected defect behind a toggle. Prove the invariants catch every defect using negative controls. Only then point an adapter at real code. Never point a defect-injecting mock at live code.

## Workflow

1. Derive surfaces from public docs and the engagement announcement. Treat each as a hypothesis, not a finding. When a supplied file list accompanies the task, diff it as a SET against `in_scope_files` in the scope manifest before any analysis: report the exact symmetric difference and confirm every file exists on disk. Read the known-issue statements (dimension `known`) before writing a PoC so effort is not spent rediscovering accepted behavior.
2. Build ONE module per surface: mock contract, handler, invariants, sanity test, negative controls.
3. Make the handler the only fuzz target. Call `targetContract(address(handler))` in `setUp()` so a mock's public `mint` cannot be fuzzed directly.
4. Write invariants as properties, not single-path tests. Derive the accounting identity algebraically first, for example `unlent + loans == deposits + feeOwed` or `cash + totalDebt == totalDeposited + totalAppCollateral`.
5. Add ghost counters for each action and a `test_sanityActionsExecute` that asserts every counter moved. A green run with zero executed actions proves nothing.
6. Add one negative control per defect toggle. If a negative control fails, the invariant has no teeth; fix the harness before reading real code.
7. Build a single adapter stub with `TODO(verify)` markers. Keep handler-facing names stable so only forwarding lines change when the real ABI differs.
8. Write hypothetical PoC drafts with explicit `[ISI]` placeholders for file:line, amounts, and why it is not a known issue. Never present a template as a finding.
9. Verify with `forge build`, then a quick regression, then one full 256-run campaign per invariant.
10. When several campaigns are ready, give each subagent its OWN full repo copy before any parallel work; concurrent `forge build` in one tree rewrites the same `out/` and cache. After a child reports, copy its final test files into the parent repo and re-run the whole suite yourself. Child summaries are self-reports, not evidence.
11. Record each campaign outcome as verified negative, open, or not reproducible. A documented known-issue variant that the harness cannot reproduce stays OPEN; do not silently promote it to confirmed because an adjacent condition was tested.

## Module checklist

- Lending core: borrow ledger, whitelist boundary, accrual index/checkpoint, solvency identity, cash backing.
- Factory: create2 salt scoped to caller, initialize after code exists, post-init assertion, seed cover, cross-app admin boundary.
- Oracle and liquidation: decimal normalization, staleness, zero and negative prices, close factor, incentive direction, dust, CEI through a callback token.
- Share vault: first-depositor inflation via direct donation and zero-share deposits.
- Multi-tenant: shared cash with isolated debt, write-off consuming the correct tenant collateral.
- Shared managed contracts: two lending apps against one fee registry or yield adapter, proving isolation between operators.
- Authorisation and IRM conditions: delegated actor grant and revoke, whitelist and token-balance conditions, external-module boundary, cap enforcement.
- Yield adapters: tracked APR freshness, donation spike reported as yield, publisher trust, feed-decimal pinning.

For ERC-4626 lending specifics (rounding residues, organic supply caps, accrual overflow, donation and flash-loan boundaries), see `references/erc4626-lending-recipes.md`.

## Pitfalls discovered on the Windows host (verified)

- `forge install` can fail with `Access is denied. (os error 5)` on Windows even with git on PATH; clone dependencies directly instead: `git clone --depth 1 --branch <tag> https://github.com/foundry-rs/forge-std.git lib/forge-std`. Why: the submodule/install path hits a Windows permission boundary that a plain clone does not.
- Install npm Solidity deps in a scratch dir, then mirror them into `<project>/lib/node_modules` with `cmd.exe /c robocopy "<src>\node_modules" "<project>\lib\node_modules" /MIR /NFL /NDL /NJH /NJS /NP` and remap every import root to `lib/node_modules/...`. Why: Foundry rejects sources outside the project root and its `lib/`, and git-bash `cp -r` over a large dependency tree is impractically slow on this host.
- Keep the forge-std remapping pointed at the lib root (`forge-std/=lib/forge-std/`); repo imports written as `forge-std/src/Script.sol` then resolve correctly, and new tests should import `forge-std/src/Test.sol`. Why: mapping `forge-std/=lib/forge-std/src/` turns `forge-std/src/...` into a doubled `src/src` path and breaks the repo's own scripts.
- Override auto-detected package remappings that add their own subdirectory, e.g. write `solidity-bytes-utils/=lib/node_modules/solidity-bytes-utils/` explicitly. Why: Foundry's auto remap appends `/contracts/`, so `solidity-bytes-utils/contracts/BytesLib.sol` resolves to a nonexistent `contracts/contracts/` path.
- For a repo mixing 0.6.x and 0.8.x pragmas, remove `solc`/`solc_version` from `foundry.toml` entirely and add `skip = ["path/to/vendor/*.vy"]` for Vyper sources. Why: a pinned compiler refuses the old pragmas and an unpinned one stops on `.vy` files it cannot compile.
- Distinguish the two initializer patterns before wiring a harness. If the constructor calls `_disableInitializers()`, a fresh instance cannot be `initialize()`d; set only the state you need with `vm.store` after confirming the slot via `forge inspect <Contract> storage`. If the constructor itself runs `constructor() initializer {}`, the fresh instance is ALREADY initialized, so `initializer` functions will revert; deploy the implementation behind an `ERC1967Proxy(impl, abi.encodeWithSelector(...init...))` instead of trying to store around the guard. Why: applying the storage workaround to the wrong pattern either reverts in `setUp()` or leaves domain separators, fee roots and component caches unset, so the exercised code is not the real configuration.
- Check the vendored forge-std `Vm` interface before using `expectRevert` with a string literal. Some copies expose only `bytes`/`bytes4` overloads, so a bare string is reported as ambiguous or not visible. The portable form is `vm.expectRevert(abi.encodeWithSignature("Error(string)", "reason"))`.
- `CHEATS.prank` is one-shot. Two consecutive pranked calls must be wrapped in `startPrank` and `stopPrank`, otherwise the second call comes from the test contract. Symptom: invariant reports `debt: 0 != 1500` and liquidation reverts "healthy".
- Foundry calls `setUp()` ONLY on the test contract, never on a handler created with `new`. Call `handler.setUp()` manually in the test `setUp()` before `targetContract(address(handler))`. Symptom: every invariant view reverts because the handler's pool/token fields are address(0).
- Keep `vm.prank` and `vm.startPrank` OUT of fuzz handler actions. Mint tokens to the handler in `setUp()` and let it act with its own address. A prank left active by a reverting action corrupts the invariant checker and produces garbage revert reasons on every property. Guard precondition-failing actions instead: check `maxWithdraw`, `debtOf != 0`, and `idleLiquidity >= amount` before calling, so `fail_on_revert = true` does not turn a normal revert into a failure.
- `ERC4626.withdraw(assets, ...)` returns SHARES burned, not assets paid out; `redeem(shares, ...)` returns assets. When a ghost counter models idle-liquidity movement, compare against the requested `assets` on `withdraw`, not against its return value. Symptom: a reproducible tiny shortfall of a few wei that looks like a protocol leak but is harness bookkeeping.
- When the engagement bundle includes the real scope, statements and a `test/poc/PoCBase.t.sol` deployment harness, discard pattern mocks and build on `PoCBase` instead. Pattern harnesses prove only that injected defects are detectable, not that the target is vulnerable.
- Try to reach supply caps (`MAX_TOTAL_SHARES`, `MAX_DEPOSIT_SHARES`) with real operation cycles FIRST. Repeated borrow, price-crash, liquidate and write-off cycles can reach `MAX_DEPOSIT_SHARES` in a handful of cycles, so a shim is not automatically justified. Only when organic cycles are genuinely infeasible, use `vm.store` on the specific slot after confirming it with `forge inspect <Contract> storage`, record the slot plus reasoning in the README, and label the boundary as shim evidence rather than proof that the organic path can reach it.
- A known-issue variant whose exact mechanism did not reproduce is NOT a verified negative. Write "not reproducible, needs a sharper angle" in the ledger. Testing an adjacent condition, for example a residue of real collateral instead of a rounding residue, closes a different case.
- Before brute-forcing sizes for a rounding-residue scenario, derive the bound from the conversion formula. If the residue `k` satisfies `k * price < 1 unit` by construction, record the claim as algebraically dismissed and stop varying inputs. WHY: the statement can assert a threshold that the composition of floor and ceil makes unreachable, and a brute force will only keep rediscovering the same bound.
- When an invariant reports a discrepancy of a few units, add per-action diagnostic ghosts to the handler (last action id, observed delta, expected delta, actual return) and rerun with the failing seed. WHY: tiny differences almost always come from harness bookkeeping, such as using a shares-denominated return as an assets-denominated delta, and without action attribution a bookkeeping error reads like a protocol leak.
- Read the request semantics of a liquidation engine before swapping engines in a harness. An engine that always closes the whole loan treats request amounts as bounds but still requires every borrow pool to be named with a maximum covering the debt; a partial repayment request reverts. WHY: the same request shape works on a partial engine and fails on a full-close engine, which looks like a harness bug until the engine contract is read.
- Check the trust statements before reporting an exploit whose precondition is a malicious hook receiver or custom module. When the operator is fully trusted and custom modules are trusted, that path is outside the threat model, so test and report the permission boundary instead of filing a finding. WHY: the mechanics can be real while the finding is still dismissed for relying on an excluded precondition.
- Solidity address literals must be checksummed. Let solc print the correct form from its error, for example `0x...A11cE`, not an arbitrary mixed-case guess.
- Before signing an EIP-712 order in a PoC, check whether the target's own hash helper already applies `_hashTypedDataV4` (common name: `hashOrder()`); sign that returned digest directly with `vm.sign`. Why: re-wrapping it in `\x19\x01 || domainSeparator || digest` yields `bad signature`, which reads like a chain-id or ABI bug and costs a full debug cycle. For signature flows, prefer the deployed, already-initialized instance on a fork over a fresh deployment: its domain separator and fee/config storage are already set, while a fresh implementation behind `_disableInitializers()` has neither.
- In a reentrancy PoC assert BOTH that the nested call succeeded AND that value moved during the callback (a balance delta on the payment token), not merely that the contract reentered. Why: a nested call that completes its own payment proves the missing guard and the callback-before-payment ordering, but not theft; a nesting-only claim gets downgraded or rejected.
- To test a guard from a hook callback, catch the nested call INSIDE the callback and assert recorded flags, not `vm.expectRevert` on the outer call. Why: a caught inner revert lets the outer operation finish, so expecting an outer revert reports a false failure; recording `reenterReverted` and `reenterSucceeded` proves the guard without depending on the callback's error policy.
- Prove a state transition by its emitting event, using `vm.recordLogs` and scanning the topic selector, not only by end state. Why: the same end state can be reached by a different route, so a state-only assertion cannot show that the write-off or liquidation path actually ran.
- When checking an internal-only entry point in a hook-enabled setup, enable that action's hook bit and still call the function externally; the `onlyCaller` guard must revert. Why: the presence of a hook does not grant external access, and an end-state-only test cannot detect the missing boundary.
- Before grading a `free assets` result from a signed-order flow, read every skip condition in the payment loop (`if (payer == order.receiver) continue`, fee-on-transfer branches, allowlisted payer checks) and identify WHO controls the skipped parameter. Why: when the victim signs the filler as their receiver, the code legitimately skips payment, but the precondition is a victim-signed bad order, which most programs exclude as unlikely user behavior or social engineering.
- `int256(uint64)` is not allowed. Use `int256(uint256(x))`.
- Passing a concrete contract where an interface is expected can fail. Either declare `contract X is IToken` with `override`, or accept `address` in the constructor and cast internally, then pass `address(token)` at the call site.
- Invariant functions must guard any condition that makes a view call revert. Do not call `price()` on a stale feed; check feed age first.
- Negative controls need correct models. A global-salt collision test must run two phases: sound mode shows no collision, bug mode shows the collision. Expecting a revert in sound mode fails.
- In a randomized sequence harness, read the entitlement you assert from authoritative storage for the concrete object under test, not from a shadow variable updated after successful calls. WHY: the shadow variable goes stale when an unmodeled call succeeds, so the invariant reports a violation that is only harness bookkeeping error; retract such a signal in writing before continuing the campaign.
- Re-check the property SPEC against source semantics before calling a fuzz failure a product bug. Common harness errors are zero-input precedence (a `0` check before a sentinel check changes the expected result), an intended revert on out-of-bounds arithmetic, and a guard that itself divides by zero. WHY: a wrong expectation produces a clean counterexample that looks exactly like a protocol violation until the spec is matched to the code.
- Set every fuzzed governance parameter ON the contract under test before exercising the formula; a test-local variable with the same name does not configure the target. Resolve token-unit semantics before asserting exact transfer amounts: fixed-point `{tok}` balances need conversion to qTok, and a FLOOR <= observed <= CEIL band derived with the target's own math library is a safer oracle than a hand-computed equality. WHY: the contract silently uses its initialized default, often zero, so a plausible formula mismatch is harness configuration or unit drift, not a protocol bug.
- Donation and share inflation needs an explicit `bugAllowZeroShares` toggle. Without it the victim's deposit reverts instead of being drained.
- CEI reentrancy is best proven with a callback token that OBSERVES state at transfer time, comparing stale versus updated values. A naive nested withdraw often balances out in a proportional vault and proves nothing.
- Pyth exponent normalization: price `1e8` with exponent `-8` is one dollar and must become `1e18`, so scale by `10^(18+expo)`, not `10^expo`.
- On Windows, `vm.ffi` via `sh -c 'forge inspect ... 2>/dev/null'` fails with `Access is denied. (os error 5)`. In a scratch copy only, call `forge inspect <contract> methodIdentifiers --json` as four or five separate argv entries and strip any leading warning bytes up to the first `{` before `vm.parseJsonKeys`. Keep the audited repo untouched and record the scratch-only edit in the engagement report.
  - For a scratch Foundry mirror of a repo with no `node_modules`, copying `forge-std` from another local project may be necessary. Verify the dependency layout: some `@prb/math` packages expose `src/UD60x18.sol`, others only `contracts/`; pick the copy whose layout matches the repo's remappings before running `forge build`.
- Full 256-run invariant suites across five modules take roughly fifteen minutes. Use `FOUNDRY_INVARIANT_RUNS=64 FOUNDRY_FUZZ_RUNS=64` for quick regression, and keep one full campaign per invariant as evidence.
  - A 256-run campaign on a deep Foundry adapter can take three to four minutes per property on this host. Run long campaigns as separate foreground calls or in two parallel batches, and confirm each log contains its own `runs: 256` and `Suite result: ok` line; a truncated `tee` log that only shows the startup warning is not evidence.
- `solc = "solc"` in foundry.toml picks whatever is on PATH. Both 0.8.19 and 0.8.28 were observed on the same host. Pin the compiler if byte-for-byte reproducibility matters, except on a tree with mixed old/new pragmas, where no pin at all is required (see the pragma bullet above).
- Foundry lint may flag the defect you are intentionally modeling, such as `reentrancy-no-eth` on a preseed transfer before `deployed` is updated. Treat that as confirmation the mock reproduces the pattern, not as something to silently fix.
- Echidna in foundry mode fuzzes EVERY deployed contract in the flattened file, not just the named harness, so a mock token's public `mint` can be called directly and break an unrelated property such as `noDust`. Restrict the fuzz target to the handler, restrict mock minting to the deployer, and keep `test_*` self-checks in a Foundry wrapper that is not a fuzz target. WHY: a failure produced by the fuzzer calling a mock is a harness artifact and hides whether the real property holds.

## Medusa and Echidna on a Foundry repo

When a second fuzzer is wanted, do not assume crytic-compile can drive the project. On Foundry 1.9 it calls `forge clean` and `forge build --build-info`, both removed, so compilation fails before any property runs.

1. `forge flatten test/fuzz/<Harness>.sol -o <scratch>/<Harness>-flat.sol`.
2. Write a minimal medusa config with `compilation.platform: "solc"`, `platformConfig.target` pointing at the flattened file, `solcVersion` matching the file pragma, and `args: ["--optimize", "--optimize-runs", "200"]` when the repo builds optimized.
3. Keep a separate `echidna.yaml` with `testMode: foundry`, `seqLen`, `testLimit`, and run `echidna <flat>.sol --contract <Harness> --config echidna.yaml` from the directory holding the file.
   - With crytic-compile 2.x and Foundry 1.9, auto compilation still fails by invoking removed `forge clean` and `forge build --build-info`. Add `--crytic-args "--compile-force-framework solc"` and keep `testMode: foundry`; `setUp()` then runs and standard `vm.startPrank`, `vm.stopPrank`, `vm.deal(address,uint256)`, `vm.label` and `vm.addr` work.
   - HEVM in foundry mode rejects `vm.ffi` plus `vm.parseJsonKeys` (`invalid hex bytestring`) and forge-std's stdStorage `deal(token,to,give)` (`BadCheatCode` on `vm.record`/`vm.accesses`). In a generated evidence copy only, precompute selectors offline with `forge inspect <facet> methodIdentifiers --json` and replace ERC20 `deal` with a direct `vm.store` to verified balance and totalSupply slots. Record every shim in a README and never edit the audited repo.
   - Echidna accepts Foundry's `targetContract(handler)` but may still fuzz public helpers on the test contract. Add thin forwarding wrappers on the harness and use `filterBlacklist: false` with a `filterFunctions` allowlist naming only the wrappers and the view invariant checks. Zero-argument wrappers can be skipped; give the release wrapper a dummy `uint256` argument. Check the campaign log lists the four wrappers plus the named invariant as passing, and run a deliberately wrong copy to prove a named failure is reported.
4. Deploy the system under test in the harness CONSTRUCTOR, not `setUp()`. Medusa's solc platform does not call `setUp()`; a harness relying on it fuzzes `address(0)` and reports failures whose traces show calls to address 0. Fix that before reading any property result. In Echidna foundry mode with forced solc, `setUp()` DOES run, so this rule applies to solc-platform Medusa, not to that Echidna path.
5. Expose each property under both prefixes, `property_*` for Medusa and `echidna_*` for Echidna, both delegating to one internal function.
6. For true Medusa property testing, write no-arg `property_()` functions returning `bool` and drive state through setter functions. A parameterized `property_f(uint x)` is reported as an assertion test, not a property test; it still runs, but label the evidence with the mode actually used.
7. If the campaign reports `no assertion, property, optimization, or custom tests were found to fuzz` while Slither's echidna printer lists the properties, treat it as a targeting problem and retry with `testAllContracts: true` and `targetContracts: []`. Confirm the named `[PASSED]` lines appear before quoting any counts. WHY: `targetContracts` filtering can suppress discovery even though the properties exist, so a green aggregate after zero discovered tests proves nothing.
8. Record the per-test summary for every property; an aggregate exit code does not prove a named property ran. For Echidna, quote the per-property `passing` lines, not just the aggregate exit status.
9. Verify a property with a deliberately wrong value once before trusting a green campaign.
10. If the DUT hardcodes collaborator addresses and the harness uses `vm.etch` to place tokens there, Medusa's solc platform can fail at deployment with a stack-underflow on a later call to an etched token. Copy the DUT source into the harness project and change ONLY the address wiring to `onlyGov` setters (for example `setDola`, `setTokens`, `setFlash`), leave business logic untouched, and deploy every dependency in the handler constructor. State in the README that this proves the logic under injected collaborators, not byte-identical deployed bytecode.
11. When a `forge flatten`ed handler file fails to compile under solc 0.8.28 with duplicate `IERC20_0`/`IERC20_1` interface names from SafeERC20, rename the duplicate interface consistently in the flattened file only; keep the edit mechanical, document it in the README, and never change harness logic to make it compile.

## Verification contract

Before claiming the harness works:

- `forge build` succeeds with the adapter file included.
- Every module suite passes, and the all-suite count matches the number of tests actually written.
- Each invariant passed at least one 256-run campaign.
- Every negative control passes, proving the related invariant detects the injected defect.
- Prove a focused test on REAL source has teeth by mutating the exact line it guards (flip `Math.Rounding.Ceil` to `Floor`, invert a comparison, change `== 0` to `!= 0`), confirming the guarding test fails, then restoring the file. Verify the restored SHA-256 equals the original and `touch` the file before recompiling. WHY: `shutil.copy2` restore preserves the original mtime, so Foundry's cache can keep serving the mutated artifact and a green rerun proves nothing.
  - Use `scripts/mutation_check.py` for a batch of mutations; it backs up, mutates, tests, restores, verifies the hash and touches the file in one pass.
- The adapter stub compiles but is clearly marked unverified until checked against the pinned repo.
- After moving or renaming the project directory, re-run `forge build` and the quick whole-suite gate from the NEW path, then grep the tree for stale absolute paths in the docs.

## Handoff to the operator

Account steps (sign up, KYC, NDA, commit, submit) stay with the operator. The agent owns analysis, PoC, drafts, and evidence. Keep all drafts under the engagement NDA and submit only through the official platform.

Write the campaign report in Indonesian with no em-dashes. Group by campaign, quote exact `forge test` counts and invariant call tables, list limitations and storage shims explicitly, and end with the file inventory. Deliver the report with a `MEDIA:/absolute/path` link. When more work remains, offer a short numbered list and treat every number the operator picks as work to finish and verify in that same pass; do not stop after one item. When asked directly what bug was found, answer plainly if there is none: separate verified negatives and reproduced known issues from payable findings, and never inflate the former into the latter. When asked what is still missing, write a reflection report that separates methodology gaps from unexplored combinations and states plainly that a null finding is not a safety certificate. Propose combined or differential approaches rather than more tests in the same family.
