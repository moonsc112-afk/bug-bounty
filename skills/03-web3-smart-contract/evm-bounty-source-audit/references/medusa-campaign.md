# Medusa campaign (EVM second fuzzing engine)

Use after the static read and the repo's own Foundry invariant suites (Foundry harness recipe: `references/solana-and-fuzz-harness.md`): Medusa is a different, coverage-guided engine aimed at the same fund-holding cluster. On a 16-core host a 6-worker campaign runs ~4k calls/s — a 15-minute run is millions of calls. Always smoke-run first.

## Where the harness lives (the one that costs a cycle)

- crytic-compile (Medusa's compiler) builds forge with `--skip ./test/** ./script/**`: a harness placed in `test/` compiles for forge but never reaches Medusa's artifacts, and the campaign exits with "no assertion, property, optimization, or custom tests were found to fuzz". Put the harness under `src/` (e.g. `src/fuzz/`).
- Diagnostic for that message: inspect the exporter's combined artifact (`crytic-export/combined_solc.json` -> `contracts` keys) and confirm your harness contract name is present.
- Harness the tree that CONTAINS the target file: a tag checkout from before the file was added cannot compile the import (`Source ... not found`). When the deployed set mixes a release tag with contracts deployed from untagged main, build those in the main clone.

## Config (medusa.json) essentials

- `fuzzing.targetContracts`: contract NAMES as they appear in artifacts; Medusa deploys them itself, so they need no-arg constructors (or `constructorArgs` entries).
- `testing.propertyTesting.testPrefixes: ["property_"]`; keep `assertionTesting.enabled: true` with the panic flags OFF (`failOnAssertion: true`; arithmetic/array/out-of-bounds panics false) — expected reverts are pruning (Medusa discards them), so only a failed assert or a `property_` returning false counts.
- On the crytic-compile Foundry path, avoid cheatcodes: `blockTimestampDelayMax` is the only time control, so size it to the protocol's windows to reach closed-by-time paths within a 100-call sequence. On the flattened-solc fallback below, cheatcodes ARE dispatched to the HEVM address and `vm.prank`/`vm.warp` work; do not strip them there.
- `chainConfig.codeSizeCheckDisabled: true` for large harnesses; `slither.useSlither: false` (slither already ran — saves a compile pass).
- Smoke config = the same file with `timeout: 90`; re-run it after every harness edit.

## Harness pattern that worked

- One contract owns the whole fixture in its constructor: mock tokens, the real contracts under test imported from `src/`, and owner/guardian/brain set to the harness itself so privileged handlers are callable.
- Bounded status-picker handlers (`for i in 1..count: if status(i)==X`) so each fuzz call finds an eligible object instead of reverting on a stale id.
- **Accounts that must be `msg.sender`** on the crytic-compile Foundry path cannot be pranked in: deploy tiny bot contracts exposing `call<Method>(target, args)` — the bot address IS the account, and constructor-set approvals live on the bot. On the flattened-solc fallback, `vm.prank` is dispatched normally, so bots are optional there.
- Properties = conservation equations computable from live state alone: contract balance == Sum(open obligations) + Sum(open bonds); hold counters == in-flight item count; per-account stake sums vs token balance; books vs balances. `property_*() external view returns (bool)`; re-evaluated after every sequence.
- Expected reverts (window closed, cap, threshold) are normal — do not try/catch them out; pruning is the fuzzer working.

## Run

```
forge build                                # catch harness compile errors first
medusa fuzz --config medusa.smoke.json     # ~90 s; expect all properties PASS
medusa fuzz --config medusa.json           # full campaign -> log file (background)
```

Report results per campaign (never aggregate across runs) and quote the final "Test summary: N passed" line verbatim.

## Foundry 1.9 fallback: flatten + solc platform

When crytic-compile calls `forge clean` / `forge build --build-info` and the installed Foundry rejects those flags, Medusa cannot compile the project through its normal path. Do not park the campaign. Flatten the harness with `forge flatten <harness path> -o <flat.sol>` (this inlines the whole import graph, including forge-std) and point Medusa at the single file:

```json
"compilation": {
  "platform": "solc",
  "platformConfig": {
    "target": "<flat.sol>",
    "solcVersion": "0.8.28",
    "args": ["--optimize", "--optimize-runs", "200"]
  }
}
```

- Verify the flat file first with a direct `solc <flat.sol> --bin` compile; the flattened pragma conjunction is satisfiable even though it looks malformed.
- The solc platform does NOT call `setUp()`. Build the fixture in the harness `constructor` (tokens, proxy, role grants, caps). Otherwise the fuzzer reports misleading one-call property failures against `address(0)`.
- Echidna consumes the same flattened file directly: `echidna <flat.sol> --contract <Harness> --config echidna.yaml` with `testMode: "foundry"`, `seqLen`, `sender` and `deployer` set. This sidesteps the broken forge compile path for both engines.
- Re-flatten after every harness edit; treat the flat file as a build artifact, not as the source of truth.

## Pitfalls

- **A property that fails on a 1-call sequence is almost always a HARNESS decode bug, not a contract bug.** Read the printed call sequence + property trace and check struct field ORDER in composite destructuring (`(, uint256 x,,) = getter(i)` — the 4th slot of a 4-field struct is not the 2nd) and event data-word offsets before writing anything down. Reproduce the claimed sequence in a Foundry unit test against the real contract; only a reproducible Foundry failure is a candidate finding.
- If the failing call's trace shows it only reading state and returning (early return), the property's own arithmetic is the suspect, not the contract.
- Medusa recompiles on start each run and replaces the previous `crytic-export/`; after moving or renaming the harness file, re-check the artifact before trusting "no tests found" again.
