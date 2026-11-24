# Rule testing and packaging recipes

Commands and fixtures for the test, harden, and export steps in SKILL.md. Adapt paths and names to the repo under audit.

## Pin the source before a full-tree scan

An abbreviated commit SHA is not a valid remote ref. Save the commit API response to a file with `curl -sSL -o <file> https://api.github.com/repos/<owner>/<tool>/commits/<short-sha>`, read the `sha` field from that file, then clone only that commit:

```bash
D=<scratch>/<tool>-src
mkdir -p "$D" && cd "$D" && git init -q && git remote add origin https://github.com/<owner>/<tool>.git
git fetch -q --depth 1 origin "$FULL_SHA" && git checkout -q FETCH_HEAD && git rev-parse HEAD
```

If an earlier fetch was interrupted, remove a stale `.git/index.lock` before checkout. A checkout that leaves files on disk but no `HEAD` still scans fine, but resolving the lock gives a cleaner evidence handle.

## YARA baseline

Install `yara-python` into a scratch target directory with the host Python package installer and the `--target <scratch>/yara_lib` option, then import it by inserting that directory at the front of `sys.path`. This avoids a global install. Compile the rule file once, then walk two roots. Skip `.git`, catch per-file exceptions such as timeouts, and print hits as `rule -> relative path`. Scanning ten thousand files takes minutes, so give the command a generous timeout.

Targets:

1. The pinned source tree. A match here on a skill that ships in the repository is expected by design, not a defect. Read the rule's `meta` note before calling it noise.
2. A synthetic clean profile in scratch. Minimal `config.yaml` with approvals in ask mode, a generic persona file, empty skills directory, no prefill or loot files. Any match here is a real false positive.

## Behavioral branch probe

Reimplement each suspect `CommandLine|re` or KQL `matches regex` in Python and feed it a small set of sample lines: the intended malicious command, the same script run from the repository source tree, an ordinary tool invocation, and a bare tool name. A branch is unscoped when a benign sample satisfies it. State the exact sample that fires and the rule id.

## Hardened copies

Write copies into a report folder, never into the upstream checkout. Typical fixes:

- Require the installed skill path, not just the script filename, in a jailbreak branch.
- Exclude the tool itself and its interpreter as writers of a persona file when editing that file is a normal feature.
- Add an empty allowlist dynamic or list at the top of a hunt and apply it to every branch, with a comment that an empty list preserves upstream behavior.
- Demote rules that only observe a normal UI or server header from `policy-violation` to `not-suspicious`; keep campaign-specific rules untouched.

Generate one unified diff with `diff -u --label upstream/<name> --label hardened/<name>` per file. Include a README listing the problem, the fix per file, the scan evidence, and an explicit note on which validators were not run.

## Import formats and verification

Read the repository's feed generator before producing import files. It is the authority for column order, type mapping, URL normalization, and metadata field names. For Zeek intel, copy the `#fields` header and the type map exactly; find the checked-in generated file and compare SHA-256 after generating your filtered copy. A hash mismatch caused only by row order is acceptable, but generating from the source CSV in its original order usually makes them identical, which is a strong correctness check.

Keep the deduped sorted CSV for humans and a second copy in source order for format generation. Report how many rows the target format cannot carry, by type, and confirm those rows remain in the CSV.

A filtered watchlist cannot be hash-identical to an upstream all-framework watchlist. Verify it by matching the column list exactly and checking that every filtered row, keyed on `(value, type, framework)`, exists in the upstream watchlist.

## Release drift check

Before calling a finding current, save `https://api.github.com/repos/<owner>/<repo>/compare/<reviewed-tag>...main` to a file and list only paths under the framework folder and docs. Classify each change as cosmetic (titles, SID renumbering, regenerated feeds) or substantive (a detection `condition`, `where` clause, or an added or removed branch). Only substantive changes affect whether an earlier finding still stands.

## Delivery

Zip the CSV, hardened rules, diff, import files, and README into a single archive. Deliver with one `MEDIA:/absolute/path` line. Keep the extracted files on disk as well so later turns can patch them without regenerating everything.
