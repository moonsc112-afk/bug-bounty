---
name: finding-validation-gate
description: "Use before submitting a bounty finding: validate and score."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [bug-bounty, triage, validation, poc, severity, reporting]
    related_skills: [defi-bounty-predive, evm-bounty-source-audit, bounty-target-verdicts, grounded-citations]
---

# Finding validation gate

> **Single gate owner on this host.** This is the operator-adapted gate (loss-of-funds programs, Solidity/Anchor PoCs, and web2 HTTP PoCs). Load this file for every candidate finding. `triage-validation` is now reference-only: open it only for the extended CVSS 3.1 tables, anti-pattern list, and retraction templates. Never run its gate list as a second gate. If any file disagrees about who owns validation, this file wins because it carries the operator's corrections.

## When to Use

Load this the moment a candidate finding appears, before drafting any report,
and again before changing a severity label to High or Critical. Run it on smart
contract findings (Foundry/Anchor PoCs) and on web2 findings (HTTP PoCs).
A failed gate kills **that finding only**, not the engagement: move to the next
test class. Do not use it to re-open a target parked in `bounty-target-verdicts`.

Adapted from the `triage-validation` skill in
`elementalsouls/Claude-BugHunter` (CC BY 4.0), rewritten for Solidity/Anchor
work and the operator rule that only loss of funds is paid.

## Ground rule for this operator

Most programs in scope pay only demonstrable loss of funds and require a PoC
plus KYC. Prefer a concrete asset amount and reproduce it when the setup allows.
Do NOT treat "no realized cash shortfall measured yet" as an automatic kill: when
the program scope says an in-scope vulnerability "causes or worsens the impact",
a permissionless bypass of the only guard against a documented loss scenario is
a valid chain. The operator corrected an over-conservative standard: preventive
control bypass matters. Build the chain as acknowledged loss + named guard + PoC
showing the guard fails, keep any missing measurement in honest bounds, and never
inflate severity beyond what that chain proves. A DoS with a working workaround
and no bypassed guard stays Medium, not High.

## 1. The 7-question gate

Ask in order. One wrong answer stops this finding. If the gate kills it but you
still believe it, gather more evidence and re-run; never bypass the gate.

**Q1. Can an attacker exploit this right now, step by step?**

Fill the template before doing anything else:

```
1. Setup:   what the attacker needs (key, account, position, token amount)
2. PoC:     the single command that runs it (forge test --match-test X / anchor test)
3. Result:  exact state change (balance delta, minted amount, corrupted field)
4. Impact:  concrete asset loss, in token units and USD
5. Cost:    capital required, gas/fees, and any precondition
```

If you cannot write step 2 as a real runnable command, kill it. Code reading
alone is not a reproduction.

**Q2. Is the impact on the program's accepted impact list?**

Open the program page. Find accepted vulnerability types and out-of-scope.
For this operator, confirm the path to a payable severity: direct economic
loss, not centralization risk, not governance design, not informational.
If it maps to an exclusion, kill it.

**Q3. Is the root cause in an in-scope asset?**

Check the deployed address or program ID against the scope list, confirm the
version matches the pinned code, and confirm it is production code rather than
a dependency or a third-party service the protocol merely uses. Out of scope
means kill.

**Q4. Does it need an authority an attacker cannot realistically get?**

"Admin can drain" is centralization risk on almost every program. Kill it.
"A non-admin can trigger what only admin should be able to do" is valid.
The same applies to a solver, sequencer, keeper, or oracle updater role: if
the exploit assumes that role is hostile, check the exclusion list first.

**Q5. Is this already known or accepted behavior?**

Search in order: the program's `SECURITY.md` and known-issues file, disclosed
reports for the same contract and bug class, GitHub issues on the target repo,
and the changelog. Also web-search the exact bug class with the target name and
open public gists/writeups; a published PoC for the same mechanism is prior art
and likely a duplicate even if yours is independent. An acknowledged design
decision kills the finding. New code touching the same surface re-opens it;
check commit age, not listing age.

A documented configuration choice is not a code defect. When the protocol's own
docs say a parameter disables a guard, a PoC showing the consequence of that
value proves a config risk, not a bug. Kill it unless the docs promise the
guard is mandatory and the affected instance is in the covered production set.
Read the live config and listing of every affected instance before treating a
mechanism demo as a payable finding.

Before calling a non-zero stored field a defect, byte-verify the state flags and
array occupancy that the deployed program itself checks. A cleared active-debt
flag, an empty borrow-slot region, and a stale timestamp are the intended
post-repay state, so the resulting zero-value refresh and the later liquidation
rejection are expected behaviour. Derive the field offsets from the SDK IDL's
account type order: a source struct walk or a sentinel-byte pattern can land in
padding and manufacture a fake defect region. An unattributed aggregate is a
lead, never a victim count.

When public material is near but not the same mechanism, answer the objection in
the report. Name each adjacent item, the file and function it concerns, and the
precondition that differs from this finding. WHY: triagers group adjacent public
research on the same program with a new report, and an unstated distinction is
read as an undisclosed duplicate.

### Scoring a local findings corpus for duplicates

When dedup is automated over a local findings directory instead of a web search,
the scoring index has to be cleaned or every candidate looks like a duplicate:

- Exclude dependency directories (`lib/`, `node_modules/`, `target/`, `out/`,
  `vendor/`) from the scan. Vendored READMEs and CHANGELOGs otherwise dominate
  the hit list with irrelevant token matches.
- Never score tokens from the program name. Every document in that program
  matches and is reported as a duplicate.
- Drop query tokens that appear in more than roughly 30% of scanned documents,
  and keep an English stopword list. Generic words such as `vault`, `loss`,
  `funds`, `until` otherwise turn every finding into a duplicate.
- Collapse byte-identical documents by content hash and keep a copy count.
  Worktrees and mirrored repos otherwise inflate the apparent evidence.
- Cap the evidence rows written back to the ledger so the status view stays
  readable; keep the full ranked hit list in a JSON report.
- Design network-backed sources as best-effort: record the source as
  unavailable and continue on local results rather than failing the stage.
- Test the gate with both a known duplicate AND a novel hypothesis. A
  positive-only test cannot reveal false positives.
- Seed any agent doing the dedup with a named impact hypothesis, not a generic
  "find bugs in this file" instruction. Generic exploration reproduces the
  same non-duplicate-free results everyone else gets.

**Q6. Can you prove impact beyond "technically possible"?**

Assert on the thing that matters: `assertEq(vault.balanceOf(attacker), X)`,
the stolen token balance, or the corrupted accounting total. A revert that
"should" be exploitable, a primitive confirmed in the middle of a chain, and
a status-code-only difference are all downgrades, not Criticals.

For findings whose loss requires moving a market price, compute the cost of the
cheapest source move and the cap on extractable payout (liquidation bonus,
borrow capacity, redeemable collateral) before calling the impact funds at risk.
If the move costs materially more than the maximum payout, report a mechanism bug
with discretionary or informational exposure, never a loss-of-funds claim. State
both figures and the depth assumption in the report. Why: a valid oracle bypass
can still be unprofitable, and programs pay the extractable loss, not the
existence of a theoretical price path.

**Q7. Is this a known-invalid class?**

Check the never-submit list below. If it appears there with no working chain,
kill it.

## 2. The layer-ordering trap (web2)

A validation error does not prove authentication was passed. Many stacks run a
schema filter or WAF before auth middleware, so a malformed body trips the
parser first. Re-send with the simplest well-formed body. If a well-formed
`{}` returns 401 while `{` returned a validation 400, you were talking to a
parser, not to business logic. Error text about input shape or character class
means parser. Error text naming a domain field that persists with a valid body
is a real signal. Edge blocks are not origin responses.

## 3. Four pre-submission gates

All four must pass.

- **Gate 0, reality (30s):** reproduced with a real command, scope checked
  explicitly, reproducible from a fresh checkout or session, evidence saved.
  Add a negative control: run the same PoC against a throwaway patched copy of
  the contract. If it still passes, the green result was never evidence and the
  PoC is testing the setup, not the bug. Re-run once on a different fork state
  or asset pair so the exploit is not an artifact of the one setup it was
  developed against; a PoC that survives the fix and generalizes is the bar.
  A fuzz or invariant PASS is evidence only after checking handler call counts:
  require non-zero successful calls for every handler and a sanity assertion that
  a handler changed state. Green suites with early-reverting mocks prove nothing.
- **Gate 1, impact (2m):** answer "what can the attacker do that they could
  not before?"; the answer names a victim and an asset, not "non-sensitive
  data seen"; it does not depend on unlikely victim behavior.
- **Gate 2, dedup (5m):** searched known issues, disclosed reports, GitHub
  issues, and the last five reports for this program; not documented behavior.
- **Gate 3, report (10m):** title in the formula below; PoC is one command;
  evidence shows the impact rather than a status code; severity matches both
  the matrix and the program's definitions; remediation is 1 to 2 concrete
  sentences; no "could potentially" or "may allow".

Title formula: `[Bug class] in [contract/function] allows [actor] to [impact]`.

### Report deliverables for this operator

The agent drafts and verifies; the operator submits. Never submit, push, or file
on a platform on the user's behalf. Keep the submission draft in English and write
a separate Indonesian summary for the operator. Store drafts under
`E:/audit/<program>/findings/` so they sit beside the PoC and evidence.

Generate the draft from the gate answers instead of retyping the finding. Put the
five pre-severity answers in the report itself; a missing or vague answer must lower
the severity by one level rather than being left as prose. A severity that survives
the gate stays unchanged. Use no em-dashes in any report or written summary.

A report is only ready when it names the victim and asset with units, gives one
runnable PoC command, lists the artifact paths and hashes, states the honest limit
of the proof, and names the exact remediation. Copy program IDs and hashes from the
artifact files, never from memory.

When asked to draft before a live PoC exists, mark every unfilled field with
`[TOFILL]` and keep the draft out of any send kit. State in the Indonesian summary
that it is not submittable. A draft with placeholders is a work artifact, not a
report, and the gate has not passed.

### Gate 0 implementation (Foundry)

Run the negative control as a deterministic, reversible script: copy each target source file to a scratch backup, assert the patch anchor occurs exactly once, replace it with the fix, run `forge test --match-path <suite> --match-test <test>`, require `Suite result: FAILED`, restore every file in a `finally` block, then confirm the source is byte-clean (`git diff --stat` on those files) and re-run the suite green. A failing PoC plus a clean restore is the evidence; neither alone is enough.

Aim the fix at the exact line that produces the PoC's revert, not a neighbouring branch. Read the PoC's `expectRevert` and the hook's branch order first. Why: with several independent `if` branches, editing a sibling leaves the fatal branch intact and the negative control passes vacuously, which reads like confirmation when it proves nothing.

If the trigger lives in a third-party protocol state, mark the negative control N/A explicitly instead of silently skipping it.

Confirm the PoC appears in the harness test list before trusting a filtered run. A test compiled as an inner item is silently filtered out, so a green `0 passed` run proves nothing. Put a new PoC in its own top-level module declared in the crate root rather than appending it to an existing private module.

Never turn a source-level reading of framework internals into a state-outcome claim. The absence of `with_transaction` in an executive or dispatch function is not proof that a failed call leaves partial state. Build the harness, observe the state after the failed call with a public getter, and run a single-item positive control first to prove the setup succeeds. Retract the candidate when the observed outcome contradicts the source inference; record the original signal and the disproving observation in the trace.

## 4. Never submit without a chain

Smart contract side: centralization or admin-malice claims; rounding dust with
no aggregatable gain; revert-only griefing with no loss; gas griefing; a bug
in a dependency that is out of scope; theoretical overflow at impossible
magnitudes; a finding that needs the victim to sign something unreasonable;
"missing check" with no reachable state that reaches it.

Before building a PoC around an external call that can revert, read the caller for
`try/catch` that refunds or otherwise returns the user's asset. If the failure is
converted into a refund, the user keeps their funds and the candidate has no loss
of funds; kill it before spending time on the harness. Why: a caught `assert` Panic
is a revert like any other, so a mismatch that looks like a broken accounting path
can be the designed refund branch.

Web2 side: missing security headers, CSP, HSTS, SPF/DKIM/DMARC; banner or
version disclosure without a working exploit; self-XSS; logout CSRF;
clickjacking on a non-sensitive page; open redirect alone; GraphQL
introspection alone; CORS wildcard without credentialed exfil; SSRF DNS
callback only; host header injection without reset poisoning; rate limiting on
non-critical forms; internal IP in an error message; mixed content; weak
ciphers; missing cookie flags alone; autocomplete on password fields.

## 5. Conditionally valid: build the chain first

| Primitive alone | Chain needed | Valid result |
|---|---|---|
| Open redirect | OAuth redirect_uri abuse, auth code theft | ATO, Critical |
| CORS wildcard | Credentialed request exfiltrating user PII | High |
| SSRF DNS only | Internal service access returning data | Medium |
| Self-XSS | CSRF delivering it to a victim | Medium |
| Subdomain takeover | OAuth redirect_uri registered there | Critical |
| Rounding dust | Repeated calls aggregating to a payable loss | Severity by proven amount |
| Revert griefing | Locks funds permanently or blocks withdrawals | High/Critical by loss |
| Oracle staleness | Stale price drives an actual bad liquidation | High/Critical by loss |
| Guard bypass | Documented loss scenario + the guard named as mitigation + PoC showing the guard does not fire | High by expected risk; state the missing measurement in honest bounds |

Prove the chain end to end before reporting. Never report A and B as one
finding when they are separate bugs with separate payouts.

## 6. Pre-severity gate before claiming High or Critical

Write one line for each question against the **severity claim**, not the
generic "is this a bug" claim:

1. Is the full chain to attacker-attainable impact validated, or only one
   primitive in the middle?
2. What does the attacker walk away with, in one concrete sentence with units?
3. Have I personally reproduced the full chain end to end at least twice, once
   for discovery and once for the report PoC?
4. Is there an inheritance gate, signature check, audience check, timelock, or
   other validation still gating the chain? If yes, the chain is not Critical.
5. Has the program rejected this severity class before? Read the scope.

If any answer is not concrete, downgrade. Critical means impact demonstrated,
not impact inferable.

**Class findings are graded on executed members, not on a scan count.** When one defect affects many instances (positions, accounts, markets), a scan that counts them is a lead: attribute every non-conforming member to a named cause first (benign drift, retired instance, unreadable state) and quote totals only for the attributed class. Prove at least two members across the range (the extreme and a marginal one) plus a COMPLEMENT control that differs only in the trigger condition and must reach the bug's assertion from the other side; one execution is an anecdote, and a control that fails earlier than the victim means the two runs are not comparable. Do not enter a control violation in the same run as the claim without running them separately. Same root cause with a new impact is an ADDENDUM to the filed report, not a new submission: lead with the new impact, name the shared root cause, and expect dedup unless the platform splits impacts.

**A precondition the attacker cannot cause is a severity ceiling, not a detail.**
When the exploit needs an external market move, a third-party price change, or a
competitor's action, the program can fairly call the result intended behaviour no
matter how clean the PoC is: the loss only materialises when the market happens to
move. Grade such a chain Medium, state the external trigger in the report, and do
not spend follow-ups arguing it up to High. Prefer finding a variant where the
attacker controls the triggering condition (position restructuring, repeated calls,
self-initiated state change) before escalating. Why: a triager's standard rebuttal
is "these scenarios depend on a market move the attacker cannot cause", and once
that is written the evidence volume no longer matters.

Keep ELIGIBILITY separate from SEVERITY when the program's rules explicitly say an
attacker-reachable state "need not have occurred previously on mainnet". That clause
stops a reviewer from rejecting a rare-precondition PoC as artificial; it does not
lift the severity ceiling above. Report the state as reproducible under controlled
clock, name the natural precondition as unobserved, then still apply the
attacker-control rule above to the rating.

## 7. Kill fast

- Cannot fill Q1 in five minutes: move on.
- More than two preconditions required simultaneously: kill.
- No tangible asset on the impact line: kill.
- Admin-malice assumption: kill immediately.
- No live instance of the affected variant, or the only caller is a holder/governor/privileged role: kill as a severity-labelled finding and keep it as an engineering/ops note. Why: programs commonly exclude non-production code and privileged access, so even a clean PoC has no payable path.
- Documented behavior: kill immediately.
- Thirty minutes on Q6 with no reproducible PoC: kill.

## 8. Retraction discipline

If a claimed finding stops reproducing, never silently drop it. Append a
retraction entry to the trace with the original signal, the disproving
observation, why it looked like a bug, and the date. When a corrected setup later
reverses the retraction, or when a gate kills an item after a draft and its send
instructions were already prepared, rewrite every draft, addendum body, send kit,
appendix, report spec and checksum manifest that carried the old claim in the same
pass; stale kit text is what the operator actually sends, and a stale retraction
in one artifact undermines the whole submission. A self-retraction reads as
self-validation; a triager retraction reads as submitted noise. Concrete
false-positive shapes and the template are in
`references/false-positive-atlas.md`.

**An explicit intended-behaviour ruling is terminal for that finding.** A `duplicate` ruling that names a deployment-topology or design precondition is the same class of terminal verdict: the trigger condition is ruled out for the deployed configuration, so stop and do not re-litigate it with a tighter PoC.
When the
platform says the behaviour is by design, stop: record the verdict with the exact
reason in `bounty-target-verdicts`, pause any status-watch cron for that
submission, and record the negative in the local coverage file. Do NOT argue back
with source comments that appear to contradict the ruling, a tighter PoC, or a
net-profit proof — once the owner has ruled, those artifacts do not change the
call. Why: follow-ups after an intended-behaviour decision consume time and signal
noise; the owner's classification is the ground truth for that program.

When a retraction touches an already prepared send kit, move the stale files into a `_retired/` directory beside the live kit instead of deleting them, rewrite the submit guide so it names only surviving findings, update every sha256 manifest entry whose path or content changed, and re-verify with `sha256sum -c` before telling the operator the kit is ready. WHY: the operator submits from the guide, so a retracted draft still sitting in the active bundle becomes a submitted duplicate even when the report body was corrected.

Run `sha256sum -c` from the directory the manifest paths are relative to, not from the folder holding the manifest. Read the first path entry first: entries starting with `findings/...` mean the manifest lives one level above that folder, and running it in place reports every file as missing although the artifacts are intact. Recompute an entry after an intentional post-verdict edit to the coverage ledger; that mismatch is expected drift, not a corrupted kit, but refreshing it keeps the manifest trustworthy.

When asked to re-check a closed finding, verify the platform state rather than trusting the local ledger: fetch the submission and `list_status_history`, quote the triager's note verbatim, then list cron jobs to confirm no status watcher for it is still scheduled. Report the terminal verdict and stop; a clean PoC and a net-profit proof do not reopen a behaviour the owner called intended.

## Related skills

`defi-bounty-predive` (target economics and class hit-list),
`evm-bounty-source-audit` (finding and PoC workflow),
`bounty-target-verdicts` (record the negative in the register),
`grounded-citations` (scope and known-issue sourcing).
