# Verifying the fresh surface of an audited target

Use this when a target has published audit reports and a README section that summarizes changes since the last audit.

## Rule 1: the README change summary is a claim

- Read the named audit tags in the repo README, then run `git diff -w <audit-tag>..HEAD -- contracts`.
- Filter comment-only lines before counting changed code; a large diff stat can be mostly NatSpec and formatting, but it can also hide real logic changes behind a short prose summary.
- Sweep only the verified fresh surface. Re-reading heavily audited core code produces verified negatives, not findings.

## Rule 2: trust differential suites over manual equivalence

- If a refactor ships a frozen pre-refactor implementation in `test/helpers/` plus parity or differential tests, run those suites as the primary verification.
- Manual reasoning about equivalence is a secondary check; a passing differential fuzz run with meaningful runs is stronger evidence for a close-out.

## Rule 3: re-read live parameters before reusing an older constraint

- Before using a prior session's oracle floor, cap, threshold, or activation flag as a bound, read it again from the live contract or a fresh fork.
- Governance can change such values; a stale bound can wrongly exclude an entire bug class or produce an invalid severity ceiling.
- When a fresh read falsifies a value recorded in an earlier draft, ledger, or report body, correct that artifact as well as the current analysis. Do not let a retracted constraint survive in a delivered file.

## Rule 4: measure propagation, not just source movement

- When testing oracle manipulation, measure both the upstream value and the value the consumer actually reads. A large upstream move can fail to reach the market's price if a daily low or dampening rule overrides it.
- State the propagation result explicitly; an upstream-only movement is not a funds-loss path.
