# Pre-hunt inventory and submission status

Run this BEFORE opening a new deep dive on a target. A fresh audit can silently repeat work that is already proven or already filed.

## Steps

1. Inventory prior work on the machine: `E:/audit/*/findings/`, notes under Documents matching the target slug, and any guard files for the same program. Read the finding drafts and coverage-negatives files, not just their filenames.
2. Check a cloned repo's `git status --short` for UNTRACKED PoCs. Prior sessions often leave repro files outside git history; they are evidence, not dirt. Read them before declaring a surface clean.
3. Check the platform for an existing submission (Mantis: `get_submission` with the id from a receipt file; read-only). Report the current status, status-history count and message count instead of assuming the finding is still unclaimed.
4. If a finding is already submitted, do NOT reopen the hunt on the same root cause. Verify its evidence still matches the pinned commit: re-run the cheapest PoCs (mock-based first, then a light fork test) and compare gas numbers and outcomes against the submitted report. State plainly that the deep dive was already completed.
5. Heavy repro tests with billion-scale gas are not worth re-running locally for a status check; recommend cloud offload and say which exact claim would be re-verified.

## Pitfalls

- An inventory that only greps the current session's own artifacts produces false "zero findings" verdicts; prior agents' output counts as the same operator's work.
- A submission sitting at `new` with no triage messages means filed and waiting, not withdrawn. Account-side actions (clarification requests, KYC, public messaging) stay with the operator; the agent supplies drafts and verified evidence.
- Re-auditing an already-submitted bug can produce a duplicate report and wastes the whole session. Lead with the existing submission id and status.
