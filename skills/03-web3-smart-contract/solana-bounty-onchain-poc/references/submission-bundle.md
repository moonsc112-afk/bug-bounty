# Paste-ready submission bundle

Packaging step, done only after the findings are frozen. The deliverable is a directory a reviewer can
verify and an operator can paste from — not another draft.

## Layout (`findings/submission/bundle/` or equivalent)

| file | role |
|---|---|
| `S1-paste.md`, `S2-paste.md`, … | one file per finding; its WHOLE body pastes into the form's description box |
| `APPENDIX.md` | rule-by-rule table, the candidate enumeration, the live-position sweep, and the explicit "what we do not claim" list |
| `MANIFEST.sha256` | hash of every quoted artifact, so a reviewer verifies in one command |
| `README-SUBMIT.md` | operator-facing: what to paste where, the checklist, and the answers to the questions judges ask |
| `PLATFORM-SCAN.md` | optional: a clean, evidenced scan of the platform patterns — shows the audit had breadth |

## Field mapping (Sherlock-style forms)

1. Title = the file's first line with the leading `#` removed.
2. Severity = the rating argued INSIDE the file, never a higher one.
3. Description = the entire file from `Severity: …` down, code blocks and tables included. Do not trim the
   limitations section: it is what makes the report reviewable.
4. Appendix = appended at the tail of the description, or a gist link when the form caps length.
5. One form per finding. Two mechanisms under one title reads as duplicate-bait and loses both.

## Pre-submit checklist

- No claim that funds moved on mainnet.
- No sentence about tooling, process, or who wrote the report.
- Build and refresh the manifest with `scripts/make_manifest.py`, not a hand-rolled loop: it preserves the
  header, writes LF endings (a text-mode write emits CRLF that `sha256sum -c` rejects), and refreshes in place.
- Manifest paths are relative to the base used when generating them. Decide the base explicitly (repository
  root or bundle directory), record it in the README, and verify from that same base. A bundle-local manifest
  with bundle-relative paths verifies correctly from the bundle directory; a root-relative manifest does not.
  If writing the manifest without the helper script, open the file with `newline="\n"`: text-mode CRLF makes
  every line end in a stray `\r` and `sha256sum -c` reports FAILED for all entries.
- Refresh the manifest AFTER the last edit to any hashed file (README and report files are edited last);
  one stale hash is the usual residue of a manifest generated before the final wording patch.
- Verify with `--check` (or sha256sum) → N/N OK, 0 FAILED before declaring the bundle finished.
- Keep the exact text that was submitted — a frozen file is evidence, a re-edited one is not.

## Severity: say which numbers are measured and which are argued

Put the split inside the report. Measured: the mechanism (a control case flipping), the positions
reachable, the price drop that reaches them. Argued: the cost of producing that drop (pool depth, market
impact). A report that labels its own bound survives a reviewer's first attack; one that blends measured
and argued numbers is the first thing that gets discounted.

## Assembling without losing the frozen drafts

Copy the frozen draft to `<ID>-paste.md` and patch ONLY factual refinements into the copy (a corrected
hash row, a new evidence paragraph). Re-run the manifest afterwards: the evidence files' hashes are
stable, the report file's own hash is expected to change, and a manifest left stale is worse than none.

## Cross-document consistency pass (before freezing)

Extract every headline figure from each paste file and the appendix, compare them in one table, and recompute
the arithmetic rather than trusting the prose: class subtotals must sum to the stated total, percentages must
follow from their counts, and the same scan generation must back every copy of a figure. Why: a number copied
into two reports from different scan generations reads as two independent measurements, and the reviewer's
first cross-check is exactly that table.

Make every coverage claim match the cases actually executed. When a report says all N candidates showed a
behaviour, count only the candidates that produced the relevant log before a gate blocked them; a run that
died at a prerequisite gate has no evidence for the claim. Why: the manifest links the logs, so an
overstatement is one click away from refutation, and the honest version (two produced it, the rest were
blocked) costs nothing.

After a finding is added, grep the operator README and appendix for words meaning "two" or "both" and for
file lists that omit the new paste file. Why: checklists and Q&A are written for the earlier count and
survive silent edits to the file table, leaving the operator to paste three findings from a two-finding
inguide.

## Retractions and superseding an inherited bundle

Before freezing a package, read the newest final audit or retraction note in the workspace and re-check the
raw victim state with the deployed build's own counters. An inherited bundle can still carry a finding that
was formally retracted after it was written. If that happens, do not patch the old bundle in place: create a
new, clearly named final bundle, state in its README that the old one is superseded and must not be
submitted, and carry the retraction reasoning into the final report. Why: an amended old bundle leaves the
false-positive artifacts available to be pasted by mistake, while an explicit supersession makes the
operator's choice unambiguous.

## Pre-submit jury simulation

Run one pass as the judge before handing the bundle over, and write the answers next to the questions:
"is this a stale/repaid-state artifact?", "is the substituted signer an invented authority?", "the defect
is not in the audited source — why payable?", "the precondition was never observed live — is it
theoretical?", "is the demo instance even covered?". Every answer must point to a sentence ALREADY in
the report. If an answer needs new wording, put that wording in the report first, then re-run the manifest.
