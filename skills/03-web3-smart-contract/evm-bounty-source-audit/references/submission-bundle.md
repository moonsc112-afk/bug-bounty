# Assembling the final submission bundle

Goal: hand the operator a directory where every file is final and paste-ready, so submitting is
copy/paste and clicking — and where the reviewer-visible text is literally the text that was
verified. One bundle per program, assembled last, once the drafts and evidence are frozen.

## Layout

```
findings/submission/bundle/
  README-SUBMIT.md     operator language: what to paste where, click order, checklist, FAQ
  <FindingA>-paste.md  judge language: the finding ALONE (title line, severity line, body, code, tables, bounds)
  <FindingB>-paste.md  same, one file per distinct root cause
  APPENDIX.md          judge language: rule-by-rule table, enumeration, exposure numbers, "what we do not claim"
  MANIFEST.sha256      every cited artifact (logs, fixtures, harness sources, data files, the paste files)
```

The paste files are the paste units: the operator copies a whole file into the platform's finding
text box. Never concatenate two findings into one file or split one across files — a reviewer who
sees two mechanisms in one submission reads it as a duplicate, and an operator pasting the wrong
file loses a valid finding.

## Pre-flight: scope gate before assembly
Before assembling the bundle, run the `chain-scope-guard` validator against the program's live asset
list: build a program .md from the extracted scope (in-scope + out-of-scope entries verbatim,
`Status: Active`, review date), run `--audit` (expect zero parse errors and conflicts), then
`--explain evm:<chain>:<address>` on EVERY address cited in the paste, appendix and PoC. Keep the
authorized verdicts as evidence. A finding against an address absent from the live scope is
worthless no matter how strong the PoC, and scope lists drift between recon and filing.

## Build it by copying, not re-typing

`cp` the delivered drafts into `bundle/` and patch only what the newest evidence changes. A bundle
assembly is the LAST verification pass, not a formatting job:

- Re-check each factual claim against the artifacts as they stand now, and rewrite the sentence
  instead of the hash when the wording is what is imprecise. "Byte-identical to the live program
  account" was subtly wrong until it named the range: the fixture is the program-data account's
  bytes after the loader's 45-byte header, and re-hashing THAT range against the live account turned
a weak caveat into a strong claim. State the range that makes an identity claim true.
- Add evidence that arrived after the draft was written (a position sweep, a new log) as a short
  paragraph in the section it strengthens, with the file it lives in — a bundle that omits the
  strongest number in the case looks like the draft was never revisited.
- Re-hash every fixture/identity claim at assembly time against the live source; an upgrade between
  PoC and submission silently invalidates a reproduction. For chain targets the same rule covers
  live-state claims: re-read counts, balances and flags with a fresh call before a sentence is
  final — notes drafted mid-audit go stale (a "never used, count()==0" line survived two report
  revisions until a fresh read showed the counter at 2).

## Judge-facing vs internal

Judge-facing files carry facts about the target, never narrative about the agent's own process.
Internal corrections (a wrong constant that was fixed, a retracted claim, a tool that misbehaved)
belong in `findings/`; a bundle that narrates its own tooling history spends the reviewer's
attention on the wrong thing and reads as a draft. Keep the honest-bounds sections ("what we do not
claim") in the judge-facing text — those are about the target, and they are what make the severity
rating credible.

## Manifest, verified before delivery

Generate it with a script over an explicit path list (include the paste files themselves), then
verify in the same call and report the count:

```bash
python - <<'PY'   # sha256 every path in a list, write MANIFEST.sha256 (paths relative to audit root)
PY
sha256sum -c findings/submission/bundle/MANIFEST.sha256 | grep -c ': OK'      # expect == number of entries
sha256sum -c findings/submission/bundle/MANIFEST.sha256 | grep -i FAILED      # expect empty
```

A manifest whose numbers were never recomputed is the cheapest thing for a reviewer to falsify. If a
cited artifact does not exist, fix the citation rather than dropping the line. Write the manifest with
an explicit LF (`open(path, 'w', encoding='utf-8', newline='\n')`): a text-mode write on Windows turns
every separator into CRLF and `sha256sum -c` then reports FAILED for every entry even though all hashes
are correct — verify the OK count in the same call and treat a zero count as a line-ending bug before
suspecting the hashes.

## The operator README (start from `templates/operator-submit-readme.md`)

Operator language, and it is the only file with instructions in it:

- click order for the platform form, with the field each file goes into;
- the severity decision stated once, with its reason (a rating higher than the evidence is the
  fastest way to lose a valid finding);
- a pre-submit checklist (read the paste text once, confirm the honest claims, save a copy of what
  was actually sent, note the finding id);
- the gates that are the operator's alone: login, deposit, KYC, posting. Never spend money or accept
  credentials; present the deposit/severity trade-off and let them decide.

## Prepare the FAQ before they ask

The operator will be questioned during triage. Write the answers in the README, phrased exactly as
the report states them, so the operator never improvises a stronger claim than the evidence:

1. why this severity and not higher (the binding limit, with the number behind it);
2. what is synthetic in the PoC (funding models, local credits) and what is real (programs, accounts);
3. whether funds moved on the mainnet state (no, unless they did);
4. whether the mechanism is instance-specific or a class (which reserves/markets share the shape,
   and which are protected by what).

## Versioned report PDFs (user's language) — build, render, verify

The long-form report is an HTML file generated by a per-version build script, never hand-edited:

- `build_vN.py` reads `laporan_v(N-1).html` and applies `sub(old, new)` substitutions whose helper
  asserts `s.count(old) == 1`, so a drifted anchor fails loud instead of silently dropping a
  section. Corrections go into the build script as a new version (fix the sentence in place, bump
  the revision note in the header) — no "UPDATE: actually..." trail for the reviewer.
- Render to PDF with Playwright and the explicit chrome executable path (`format="A4"`,
  `print_background=True`), one render script per version so the PDF stays reproducible.
- Visual QA for each new section: compute its rect via `page.evaluate` (`querySelectorAll('h2')` +
  `getBoundingClientRect().top + scrollY`), take `page.screenshot(full_page=True, clip=...)` crops,
  then vision-check each crop. Vision misreads downscaled text as typos — grep the HTML to confirm
  before "fixing" phantom words.
- The report is in the user's language (Indonesian here); the judge/team email draft is in English
  and cites sha256 for every attached artifact (patches, tests, logs). Deliverables go to the
  operator as MEDIA chat attachments.

## Final verification pass (run on the on-disk state at handoff)

- Re-run EVERY PoC the report cites, in its current on-disk state, and diff the printed numbers against the report's text. A PoC that passed before the last edit is not evidence for the edited version; patch the prose to the new figures rather than the reverse. When there are two PoCs (maximum-impact and realistic-precondition), run both and label which one the headline number comes from.
- Scan every deliverable for stray tokens from another language and for duplicate words introduced by edits: `grep -oP '[\x{4e00}-\x{9fff}\x{3040}-\x{30ff}\x{ac00}-\x{d7af}]+' *.md` plus a check for doubled connectives. Fix the sentence in place, then re-run the scan until it is empty. Why: a targeted patch can leave a CJK fragment or a doubled word behind, and the operator pastes that prose verbatim into the platform.
- Verify rendered PDFs by extracting text with a PDF reader and grepping for the headline figures and the PoC filename, not just by checking the file exists. Why: a build can succeed while a stale section means the PDF still shows superseded numbers.

## Handing it over

Deliver the files to the operator as chat attachments (MEDIA paths) plus a short index of the
directory. Do not paste two full findings into the chat body as well: it doubles what the operator
must scroll past, and the attached files are the artifact.
