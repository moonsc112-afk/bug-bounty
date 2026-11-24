# Pattern harness while engagement scope is gated

Use when the engagement is confirmed live but the repo, commit and known issues sit behind
a login the operator has not cleared yet. Output is a runnable, self-contained Foundry
project that encodes the testable properties, not a fake audit of the target.

## Build order

1. Mine the public site, launch posts, poster image and platform docs for **named features**
   (whitelists, custom IRMs, "any oracle", configurable liquidation, upgradable/immutable,
   factory-launched apps). Each named feature becomes a surface and a hypothesis. Treat a
   same-name repo from a different project as a lead at most: verify the exact project
   name before using any of its code.
2. Write one minimal reference contract per surface with a defect switch per hypothesis.
   Keep switches OFF by default so the reference implementation is sound. Name them after
   the break (`bugSkipZeroCheckpoint`, `bugFloorAccounted`, `bugCrossAdmin`, `bugPreseed`).
3. Write a Handler that owns every state-changing action. Set `targetContract(address(handler))`
   in `setUp()` so a mock's public `mint` is never fuzzed directly. Add a ghost success
   counter per action and a `test_sanityActionsExecute` that drives each path once.
4. Write invariant properties, then one deterministic negative control per defect switch.
   A property with no negative control is unverified: it may be vacuously true.
5. Run `forge build && forge test`. Report run count, call count, revert count and the
   sanity assert. A green suite with zero executed actions proves nothing.
6. When scope opens: read security notes and audits PDFs FIRST, then write a thin adapter
   over the real contracts exposing the same function names, replace `PatternLending` /
   `PatternFactory` in `setUp()`, and rerun the negative controls. Only then run long campaigns.

## Properties worth encoding for lending

- Solvency identity: `unlent + loans == deposits + feeOwed`. Track `unlent`, `loans`,
  `deposits`, `feeOwed` explicitly and assert the equality after every action. Derive the
  identity algebraically before fuzzing so dismissals hold for every input.
- Cash backing: `asset.balanceOf(pool) >= unlent`. This catches an unbounded sweep that
  moves reserved cash while leaving `unlent` untouched.
- Ledger: `sum(borrowed[i]) == totalBorrowed`, and `totalBorrowed <= borrowCap`.
- Accrual: `sum(pending[i]) <= accounted`, `claimedTotal <= notifiedTotal`, and
  `accounted + claimedTotal <= notifiedTotal`. Reserve with `ceil` on notify; a `floor`
  reserve is short after several small distributions merged into one holder claim.
- Checkpoint: `checkpoint[i] <= index`, and the checkpoint must be written even when the
  accrued amount is zero, otherwise a new holder claims the whole historical index.

## Properties worth encoding for factory / clone / admin

- Every deployed app has `initialized == true`. A call to `initialize` against a codeless
  predicted address returns success without executing, so a preseed can be stranded while
  the caller believes init ran. Assert a value only the real initializer writes.
- Salt must be scoped to `msg.sender`. With a raw caller-supplied salt, one account can
  occupy another's predicted address; add a `predictFor(caller, salt)` view and assert the
  addresses differ.
- Factory admin must not reconfigure an app it does not own. Record the violation in the
  handler with try/catch and a ghost counter, because the fixed path is expected to revert.
- No duplicate app addresses; a duplicate prediction means a salt-occupation window.

## Self-contained Foundry setup (no network, no compiler download)

- Copy `forge-std` from any existing checkout into `lib/forge-std` and drop its `.git`.
- In `foundry.toml`: `solc = "solc"` to use the installed system compiler, and pin
  `evm_version` to a version that compiler accepts. Verify with `forge --version` first.
- Solidity address literals must be EIP-55 checksummed; if the compiler reports error 9429,
  use the checksummed form it prints rather than an all-caps or all-lowercase guess.
- `vm.prank` is one-shot. Setup that performs two external calls per actor needs
  `startPrank`/`stopPrank`, otherwise the second call comes from the test contract and the
  conservation invariant shows `sum(debts) == 0` against a nonzero total.
- A vendored forge-std may expose `expectRevert` only for `bytes`/`bytes4`, not `string`.
  Use `vm.expectRevert(abi.encodeWithSignature("Error(string)", "reason"))` when a string
  literal is reported ambiguous or not visible. Narrow integer casts may need the explicit
  two-step form `int256(uint256(x))`.
- `FOUNDRY_INVARIANT_RUNS=64 FOUNDRY_FUZZ_RUNS=64 forge test` gives a fast whole-suite
  gate; run the default 256-run campaigns afterwards for the reportable numbers.
- Keep the harness out of the audited repo. It is scaffolding, not a change to the target.

## Properties worth encoding for oracle / liquidation

- decimals: a 6-decimal answer of `1e6` must normalize to `1e18`; assuming 8 decimals makes
  it `1e16` and a liquidator seizes 100x too much collateral. Plant a `bugIgnoreDecimals`
  switch and assert both values.
- freshness and sign: reject an answer older than `stalenessWindow`, and reject zero or
  negative answers. Assert the sound mode reverts and the defect mode accepts the bad feed.
- close factor: `debtToCover <= debt * closeFactorBps / 10000`; record breaches at execution
  time so a later state change cannot fake a violation.
- incentive direction: correct seize is `repaid * (10000 + incentiveBps) / 10000`; a
  subtracted incentive under-pays the liquidator. Compare correct and defective seized
  amounts on identical state.
- dust: after liquidation, remaining debt must be zero or at least `minDebt`. To test it,
  first raise the close factor so the dust path is actually reachable.
- unit mismatch: pack a deliberately wrong seconds-into-milliseconds observation and assert
  the decoded timestamp differs from the correctly converted one.
- conservation: `sum(collateral[i]) == totalCollateral` and `sum(debt[i]) == totalDebt`
  catch a setup where two setup calls came from different senders.

## Design negative controls for reachability and both modes

Each control must prove two things: the sound reference honors the property, and the
defect switch breaks it. A control that only expects the buggy outcome will fail when run
against the sound contract and says nothing about the property. For salt scoping, assert
two callers using the same raw salt get different addresses in sound mode, then enable the
global-salt defect and assert the second caller collides. For guards ordered ahead of the
target, set the earlier parameter so it does not fire.

## Cross-feature hypotheses worth a checklist column

Record both a critical condition and a dismiss condition for each before the repo opens:

- **Shared liquidity, per-app debt.** If apps share a pool but keep separate risk config, an attacker-created app with a permissive oracle can drain common liquidity and socialize the bad debt. Dismiss when each app owns its pool or cross-app caps are documented.
- **Upgrade or admin role capture.** An updatable app whose upgrade role is reachable through initialize, reinitializer, or a role granted at clone time lets the holder swap implementation and strand depositors. Dismiss when the role is timelocked and known issues name it as trusted.
- **First-depositor donation inflation.** Direct transfers that raise cash without minting shares, combined with accepting zero-share mints, let the first depositor take a later depositor's funds. Dismiss with locked minimum liquidity or donation-proof share accounting.
- **Arbitrary-token callback.** Any collateral token may have a transfer hook. Test CEI with a mock token that observes state during the callback; a proportionally correct accounting model alone can hide a broken CEI. Dismiss only when state is written before every external transfer and reentrancy guards span all entry points.

## Package the artifact set

When a gated hunt spans several documents plus a runnable harness, finish in one folder: move the notes, checklist, PoC drafts and harness under a single `<target>-audit/` directory, and write an `INDEX.md` that maps every file, states what is verified versus hypothetical, and gives the exact `forge` commands. Then sweep the whole tree for absolute paths pointing at the old location, rewrite them, and re-run `forge build` plus the fast whole-suite gate FROM THE NEW PATH. A move that is not re-verified leaves docs pointing at dead paths while the tests still pass. Keep hypothetical PoC drafts visibly marked as templates with unfilled placeholders; packaging must not make them look like findings.

## Report shape

Lead with whether the harness is ready and the real `forge test` numbers. Then give a short
list of the properties encoded and which defect switch each negative control proves.
End with numbered next-step options; account, KYC and public submission stay with the
operator.
