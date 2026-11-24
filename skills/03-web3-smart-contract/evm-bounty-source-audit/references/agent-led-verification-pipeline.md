# Agent-led verification pipeline (lead to PoC to report)

Design pattern for a small local tool (UI + orchestrator + SQLite + agent workers)
that keeps the human as the idea source and the agent as verifier. Derived from a
top Ethereum consensus hunter's public method. A working reference implementation
exists; see Implementation notes at the end of this file. Follow the pattern even
when individual stages are still manual.

## Standing rules for agent-assisted hunting

- Drive agents with a NAMED IMPACT HYPOTHESIS, not a generic "find bugs here"
  prompt: state the impact, the attacker, and the suspected path. Generic pattern
  prompts find the same bugs everyone reports, and duplicates pay little or
  nothing. The human supplies the unique idea; the agent verifies, expands,
  builds the PoC and drafts the report.
- Write a short threat model (actor, asset that can be lost, guard that should
  stop it) BEFORE handing code to an agent. One impact per hypothesis. Keep the
  agreed priorities sequential; do not spread thin across many targets at once.
- Run dedup BEFORE investing in a PoC: known issues, disclosed reports, GitHub
  issues, and the last five reports for this program. A proven bug that is
  already known is a wasted PoC, not a win.
- When the operator names a target to hunt, inventory YOUR OWN prior work first:
  `E:/audit/*/findings/`, submission receipts in Documents, and the platform's
  `get_submission` for any existing report id. If the bug is already submitted,
  report its status and re-verify the cheapest PoC instead of re-auditing from
  scratch, because the target may already be in triage. A fresh clone proves
  source acquisition, not that no one filed the finding yet.
- Stop rule: when no new idea appears for about a week, or the target starts to
  feel like burnout, switch program or take a break instead of grinding out more
  duplicates. Continuing after ideas run out is the main duplicate factory.
- Treat AI coverage at scale as a baseline that everyone will have, not as a
  differentiator. The durable edge is the human's unique perspective on the
  protocol and the ideas they bring to the agent.

## Invariants

- Never seed the GENERATOR with common bug patterns. Hardcoded "never submit"
  and kill-fast rules belong in the VALIDATOR (a filter), not in the generator.
  Mixing the two turns the tool into a duplicate machine.
- One lead = one named impact hypothesis from the human. Input is "impact X may
  be reachable via Y because Z", not "find bugs in file F".
- The human keeps three decisions: write the hypothesis, triage the final report,
  submit. Everything between those points is automatable.

## State machine

```
NEW -> SCOPE_CHECK -> DEDUP -> STATIC_REACH -> DYNAMIC_POC -> NEGATIVE_CONTROL
     -> GENERALIZE -> IMPACT_GATE -> REPORT_DRAFT -> HUMAN_TRIAGE
     -> SUBMITTED / KILLED / RETRACTED
```

Each stage emits a verdict `{stage, pass, reason, evidence_refs[], command, exit_code}`
and has a time budget. Timeout kills that finding, not an unbounded retry.

## Minimal SQLite schema

```sql
leads(id, program, target, impact_class, hypothesis, attacker_model,
      status, created_at, owner)
attempts(id, lead_id, stage, tool, command, output_ref, exit_code, verdict, ts)
evidence(id, lead_id, type, path_or_ref, checksum, note)
-- type: scope | dedup | static | poc | assert | diff | generalize
reports(id, lead_id, version, title, severity, body_path, checksum)
retractions(id, lead_id, original_signal, disproving_obs, reason, ts)
```

## Stage notes

- DEDUP before DYNAMIC_POC: SECURITY.md, known issues, disclosed reports, GitHub
  issues, and the last five reports for this program.
- NEGATIVE_CONTROL: re-run the PoC against a patched copy (add the missing check).
  It must fail. Green on both means the PoC tests the setup, not the bug.
- GENERALIZE: re-run on another fork state / asset pair / mint / account owner.
- IMPACT_GATE: hand off to `finding-validation-gate` (7 questions, 4 gates,
  pre-severity gate). Do not reimplement those rules here.
- Scope and audit-depth checks stay manual and stay on the live program page.

## Adapters

- EVM: slither + Foundry (`forge test` with fork), medusa/echidna for invariants.
  The PoC asserts an asset delta, not just a revert.
- Solana (WSL, `bash -lc`): `anchor build`, `solana-test-validator` + `anchor test`.
  The PoC asserts a token-account or state-field delta.

## Implementation order

DB + CLI first (`lead new/status/triage`), then DEDUP, then NEGATIVE_CONTROL +
GENERALIZE, then the EVM adapter, then Solana, then REPORT_DRAFT + severity gate.
Do not start with a fancy UI.

## Implementation notes (verified in practice)

A working reference implementation is `E:/audit/tools/leadctl/leadctl.py`, with
SQLite ledger plus `new/status/dedup/static/poc/report/triage/import-inventory`.
Reuse its patterns instead of re-deriving them.

### Native toolchain calls from Python

- Prepend the **native Windows** Foundry bin directory to `subprocess` `env["PATH"]`
  before running slither. Slither shells out to `forge`, and the ambient PATH can
  resolve that name to an unrelated CLI; a POSIX `/c/...` PATH entry works in bash
  but not when a native Python process creates the child.
- Launch git from Python through the native `git.exe` under `Program Files/Git/cmd`.
  An MSYS POSIX git on PATH cannot be spawned by native Python; use the native exe
  for worktree add/apply/remove.
- Keep a pure-Python unified-diff applier as fallback when `git apply` is unavailable.

### Tool output parsing

- Slither 0.11.x writes `{success, error, results: {detectors | printers}}`.
  Requesting `--print function-summary` suppresses `detectors` in the same run; use
  one run for detectors and regex the source for the function visibility/modifiers.
- `forge test --json` returns a dict keyed `test/File.sol:Contract`, each holding
  `test_results` -> `{status, gas, logs, decoded_logs}`. Treat all statuses `Success`
  as pass and read the impact marker from the logs. Require an explicit marker only
  when the PoC convention guarantees it; otherwise emit a warning, not a kill.

### Dedup that does not cry wolf

- Exclude `lib/`, `node_modules/`, `target/`, `out/`, `vendor/`, `deps/` from the local
  markdown scan: dependency READMEs and changelogs otherwise swamp the hit list.
- Drop query tokens present in more than about 30% of scanned documents, and never
  score with the program-name token, or every doc in that program looks duplicated.
- Collapse byte-identical documents by checksum (worktrees, mirrors) and keep a
  `copies` count. Cap stored evidence rows; keep the full hit list in a JSON report
  so `status` stays readable.

### Negative control

- Implement as: detached git worktree in temp, symlink or copy `lib`, apply the patch,
  rerun the SAME test, require failure, then remove the worktree in cleanup.
- If the patch fails to apply, do NOT mark the finding KILLED. Leave it at
  `DYNAMIC_POC` with a warning; an unapplied patch proves nothing.

### Report generation

- Title formula: `[Bug class] in [contract/function] allows [actor] to [impact]`.
- Feed the five pre-severity answers as explicit flags. Any blank or negative answer
  downgrades severity one level and is listed in a `Gate warnings` section; the tool
  never upgrades severity.
