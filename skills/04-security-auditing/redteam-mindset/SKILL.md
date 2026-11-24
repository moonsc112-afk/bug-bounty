---
name: redteam-mindset
description: "Use to hold coverage: breadth vs depth, no early stop."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [BugBounty, Coverage, Method, Discipline]
    related_skills: [triage-validation, finding-validation-gate, new-feature-bug-hunt, web-api-bounty-hunt]
---

# Red-team mindset: coverage discipline

Owns the coverage axis. `finding-validation-gate` kills individual findings; this file decides what happens to the engagement after a kill. Load it whenever a test class comes back empty, when the session feels finished, or before reporting a negative verdict.

## When to Use

- A test class just came back empty and the pull to stop is strong.
- Before writing any negative verdict or close-out.
- When several leads are open at once and depth versus breadth has to be decided.
- Not for validating one finding (`finding-validation-gate`) or choosing a target (`bounty-target-selection`).

## DO NOT STOP primary directive

A failed finding is not a failed engagement. Every kill returns to the test matrix and takes the next class. The only valid reasons to stop are listed in Exit conditions.

The failure mode this rule exists for: one empty class is read as "target is clean", the verdict is written from three tests, and a payable bug two classes over is never touched. Depth is earned after breadth has been swept, not instead of it.

## Sweep order

Breadth first, one pass, in cost order. Record every class before going deep on any of them.

1. Scope and invariants: what the code promises users, where the money sits.
2. Entry points: every external, permissionless function reachable with attacker capital.
3. State and accounting: shares, debt, fees, rounding, decimals, caps.
4. Access control: who may call what, and what a compromised role buys.
5. Oracle and price paths: what the protocol trusts and how it is fed.
6. Cross-contract and cross-chain legs: the boundaries the protocol assumes hold.
7. Upgrade, pause, config, migration paths.
8. Failure handling: reverts, partial fills, liquidation edges, DoS with workaround.

Only after all eight are recorded do you rank and descend into the top two by expected value.

## Depth rule

While descending, keep one lead in focus at a time: trace the handler, the access control on it, and a focused PoC or fuzz case before switching. Two half-traced leads lose to one finished PoC. A lead that dies takes its depth with it and returns you to the matrix, not to another lead.

## Coverage ledger

Write it to the target workspace, not into chat, and update per class:

```
Class | Surface | Result | Evidence | Confidence
3 accounting | Pool.totalAssets | SUSPECT | totalAssets ignores pending fee, pool.sol:412 | high
5 oracle | StaleTwapAdapter | CLEAN | twap 30m + 2 confirmations, adapter.sol:88 | med
```

A class is only CLEAN with the artifact that closes it. Confidence `low` on a CLEAN means it reopens on any new commit touching that surface.

## Kill versus park

- **Kill**: the gate's Q1 to Q7 fails and the code cannot change the answer. Record the class and its evidence, never the paragraph of reasoning.
- **Park**: plausible but blocked on an asset, deployment, credential or block range you can get later. Park with the unblocking condition named.
- **Chain**: valid only with another finding. Keep it in the matrix until the primary lands.

Killing the same class twice in one engagement is a logging error, not diligence. Check the ledger first.

Before parking a row because its proof seems to need RPC or a fork, grep the repo's test tree and fixtures for the same derivation or preconditions. A correctness test that asserts an extracted value against live chain state using an identical key derivation is a static KILL: record its `file:line` as the closing artifact instead of requesting scope access. Say explicitly that the test was read, not re-run. Why: proof and storage-layout hypotheses are often already refuted by the project's own tests, and spending the operator's scope authorization on them widens testing permission for no gain.

An unpopulated protective field is not evidence of a bypass. Before promoting an absent snapshot, unset flag, or apparently disabled guard to SUSPECT, run a local A/B control against the deployed artifact with the field fresh, stale, and empty, and record whether the program rejects or proceeds. Why: absence on live accounts usually means those accounts cannot take the guarded action, so a population count measures usage rather than enforcement.

Treat a stored aggregate as cached until the account's live-state flag agrees. A non-zero borrowed, owed, or value total can survive a full repayment until the next refresh, so the total alone is not evidence of an outstanding liability; read the live flag and the entry array before promoting the aggregate to a loss-of-funds claim. Why: the aggregate describes a past state, and a withdrawal against a genuinely repaid position is legitimate behavior that a false claim would misreport as an exploit.

A SUSPECT imported from an external writeup is not CLEAN until its exact precondition is measured on live state across every in-scope instance, or every sibling implementation is diffed and the external call's callback control is established. Why: a writeup proves the pattern existed somewhere, not that this deployment carries the precondition; an unmeasured config drift or an assumed callback window turns a historical finding into a false positive.

Before writing an addendum or closing a package around an INHERITED finding, re-verify the claim against raw account bytes and the newest final audit or retraction note in the workspace. A prior evidence bundle can still carry a finding that was later retracted; closing the engagement on it publishes a false positive. Re-read the victim state through the deployed build's own counters and flag bytes, and supersede the old bundle with a clearly marked final bundle instead of silently editing it. Why: retractions live in later reports, not in the bundle you inherited.

A KILL recorded as "not deployed" requires an exact-ABI check: take the instruction name from the official SDK IDL and the program's exposed `pub fn`, then call it. `InstructionFallbackNotFound` on a hand-guessed snake_case name is a client ABI error, not evidence that the handler is absent. Why: a fabricated discriminator manufactures a false not-deployed verdict; the cross-check recipe is in `new-feature-bug-hunt`.

A KILL whose evidence is a constraint failure from a locally rebuilt harness must be reopened when the harness discriminator or account list is later corrected. Edit the existing row with the corrected result and evidence instead of adding a second row for the same class. Why: the ledger is read by later sessions as the engagement's verdict, and two rows for one class hide which result supersedes which.

## Time and effort

Daily: pick the sweep classes not yet touched, mirroring the program's own scope order. Per class: two hours without a live signal, park it. A parked class with a named unblock beats an hour of grep roulette on a class already swept.

## Exit conditions (all five must hold)

1. All eight sweep classes recorded with a result and an artifact.
2. Every SUSPECT either has a PoC or a named park condition.
3. Newest commit touching an in-scope surface is older than the last full sweep, or was diffed.
4. The published-audit and known-issues lists were checked against the candidates.
5. Prior sessions and the workspace were searched for newer reports, retractions, and stale submission guides, and the final finding count was reconciled against the newest artifact rather than the current conversation. Why: a parallel session can publish a later verdict while an old send kit keeps naming retracted findings.

When all five hold, the negative verdict is legitimate. Write it as a coverage ledger plus the top three carry-overs, not as prose about trying hard.

## Negative verdict wording

Write every negative as `verified negative on the classes actually swept` plus the advanced classes deliberately not run. A clean pass over cheap checks is not a claim that the target is exhausted. Name the skills loaded, the non-default probes executed, and the remaining advanced checks with their unblocking condition; answer a coverage question with that ledger rather than only `no bug found`. Keep the distinction visible in both the report file and the chat summary so a later session does not inherit an overstated verdict.

After a negative verdict, inventory the same release for in-scope components on the paying network that were NOT swept. A clean pass over a component the program cannot pay for is not a result. Re-rank the unswept components by payable surface before closing, and name a brutal hypothesis for the highest one. When the operator asks for a wild or brutal angle, put each hypothesis into the ledger as a testable row and kill or park it with one cheap on-chain or source probe in the same turn; return the KILL/PARK ledger, not a narrative of cleverness. Run brutal mode as aggressive hypotheses with conservative execution: when the chain-scope guard denies every deployed target, kill rows with static source probes and park rows whose proof needs RPC or fork, naming the exact authorization required. A parked row is not a negative verdict. Why: the guard is a hard gate, and a parked hypothesis with a named unblock is more useful than an unauthorized probe or a claim that the surface is clean. When the operator asks what was missed, answer with that surface and the hypothesis, not with a restatement of the clean classes.

## Anti-patterns

- Closing a release on the freshest module without checking its deployment network and the rest of the release's changed-file list on the paying network.
- Reporting a negative after one class because it was the interesting one.
- Re-testing a class already CLEAN without new code to justify it.
- Descending into a fourth lead while three sit half-traced.
- Reading a parked verdict in `bounty-target-verdicts` as permission to not sweep.
- Treating a subagent's "looks clean" as a CLEAN row with an artifact. It is a lead until you run the check. When fanning out breadth across parallel branches, require each branch to write an evidence file and verify the highest-impact claim directly against source and deployed artifact before it enters the verdict. A branch summary is a lead, not a result.
- Killing a finding for scope and killing the engagement with it.
- Clearing a two-sided predicate by measuring one side. A gate that fires on `X` OR `Y` (collateral limit or borrow limit, sender or recipient, mint or vault) is only CLEAN when both sides were matched; a one-sided sweep returns a confident zero that the next pass contradicts, and the earlier verdict then has to be retracted instead of extended.
- Writing a negative without a positive control on the same harness. Run one known-good instance through the identical path: a control that reaches the deeper assertion (and fails there for its own reason) is what proves a zero belongs to the code rather than to the wiring, and it is the difference between a refutation and a stuck harness.
- Calling a passing invariant campaign evidence before reading the handler call-count table. Foundry prints Calls/Reverts/Discards per handler; a handler with zero calls never reached its surface, so PASS says nothing about that class.
- Treating a fuzz PASS as success-path coverage when the harness low-level-calls the target and catches reverts. Log the number of successful calls; if it is zero, report only that reverted calls left state unchanged and mark the success path UNTESTED with the setup needed to reach it. Why: a target whose preconditions are never satisfied can pass thousands of runs with every interesting branch unreachable, and the PASS then overstates coverage to the next session.
- Recording a failing fuzz test as a protocol finding before tracing the revert. Insufficient token balance, a cap already filled by setUp, or a prank consumed by contract creation is harness debt: fix the fixture, rerun, and only then interpret the result.
- Declaring a route closed on a missing private key or credential before checking whether the harness can substitute the actor and re-derive its dependent accounts. The blocker is usually a fixture gap, not a capability limit: try substitution first, then park only if a program-level constraint still binds. Telling the operator a route is impossible before that check invites the correction that it was possible all along.
