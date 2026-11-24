---
name: security-detection-research
description: "Use when auditing detection rules or IOCs from a repo."
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [security, threat-intel, detection-rules, verification, ioc]
---

# Security Detection Research

Use when the user points at a post, blog, or GitHub repo of detection rules, hunting queries, or IOCs and asks what it is, whether its claims are true, or how usable the rules are. The deliverable is a verified finding plus a usable artifact (CSV, rule file), not a feature tour.

## When to Use

- User shares a post or link about a detection framework, threat-intel feed, or IOC set and asks what it is.
- User asks whether a third-party claim about a tool is true, checked against the tool's source.
- User asks how usable or noisy a set of detection rules is, or wants IOCs extracted into a usable file.

## Procedure

1. Locate the canonical repo from the link with `web_extract`, then read its root README and the folder that concerns the user. For a social post, extract the linked URL before assuming the post's summary is accurate.
2. Pin the version. Note the exact commit the authors say they reviewed and fetch files from `raw.githubusercontent.com/<owner>/<repo>/<sha>/<path>`, never from `main`, so later edits do not shift the evidence. Confirm a path exists with `https://api.github.com/repos/<owner>/<repo>/contents/<path>?ref=<sha>` before quoting it. When the audit targets current `main`, also diff the last reviewed release tag to `main` with the `compare/<tag>...main` API saved to a file, restricted to the framework and docs folders. State whether detection logic changed: a SID renumber or doc edit does not invalidate a finding, a changed `condition` or `where` clause does.
3. Verify claims against upstream source at the pinned commit: check the path exists, grep the cited line, and read the upstream default-state doc. Only then repeat a claim as fact. See `references/rule-specificity.md` for the audit decision table.
4. Download every rule file in the folder with one batched curl loop. Inventory by type: KQL hunts, analytics, Sigma, Suricata, YARA, Zeek intel. Lead the report with counts.
5. Audit rule specificity before recommending deployment. Compare each rule's `falsepositives` text against its actual `condition` or `where` clause; text often promises filtering the logic does not do. Separate campaign-specific indicators from detections of a legitimate tool's normal features. Use `references/rule-specificity.md` to classify each rule.
6. Test the rules when asked how usable or noisy they are. Clone the upstream tool at the pinned full SHA, compile its YARA file with `yara-python`, and scan two targets: the pinned source tree and a synthetic clean profile. Also probe each suspect Sigma/KQL branch with sample command lines through the rule's own regex. Report matches per rule and per file, and say plainly when a clean-profile match is a real false positive. See `references/rule-testing-recipes.md`.
7. Build hardened rule copies when asked for something deployable: write them into a separate report folder, add suppression or context to the noisy branches, and include a unified diff against the upstream files. Never edit the upstream repo.
8. Export IOCs by filtering the source CSV on the framework tag as a substring, because rows are shared across frameworks. Dedupe on `(type, value, framework)`, sort, write with `utf-8-sig` so Excel reads it, and save under a durable path. Also produce platform import formats (Sentinel watchlist, Zeek intel) using the repo's own feed generator as the schema authority, and verify at least one generated file against the checked-in generated file by SHA-256. Report counts by type, confidence, source, and framework tag, plus which types the target format cannot represent.
9. Bundle all artifacts into one zip and deliver that single `MEDIA:/absolute/path`, with a short README inside describing each file.
10. Report in Indonesian, casual register, no em-dash. Lead with the verdict, then the grouped findings with evidence (SID, rule id, `path:line`), then the artifact. Treat the authors' own caveats (experimental, untested on captured intrusions) as part of the verdict, not as a closing disclaimer. State exactly which validation gates actually ran. When asked what the work is for, answer in one concrete sentence tied to the user's actual line of work, say plainly when it has no operational use for them, and never answer with a process recap.
11. End with 3-4 short numbered next-action options. The user answers by number and expects the chosen items carried through to completion.
12. On a cleanup request, delete only the exact paths this task created, verify unrelated sibling files survived, and `cd` back to a stable directory before further destructive commands if the shell was sitting inside a deleted scratch folder.

## Pitfalls

- Write large API JSON to a file with curl `-o` and parse the file: terminal output is auto-truncated around 50 KB, and `json.loads(..., strict=False)` accepts the truncated prefix, returning a partial tree with zero matches.
- Use native `C:/...` paths for native curl `-o` on Windows: an MSYS `/tmp/...` path makes curl fail with error 23 while writing nothing.
- Do not trust a third party's word "bundled" for an optional skill: read the upstream `optional-skills/DESCRIPTION.md`, because shipped in the repository does not mean copied into the active skills folder.
- Do not infer a rule is clean from its `falsepositives` section: check the detection condition itself for an unscoped branch such as a jailbreak script match with no parent-process constraint.
- Do not copy a SID range from a cached search snippet: read the checked-in docs and the rule header at the pinned commit, because release renumbering makes older ranges stale.
- Do not treat shared-behavior rules as equivalent to framework-specific rules: they are deliberately broad, so they need their own baseline before alerting.
- Fetch the full commit SHA from `api.github.com/repos/<owner>/<repo>/commits/<short-sha>` before `git fetch --depth 1 origin <sha>`: git rejects an abbreviated SHA as a remote ref. If an earlier fetch was killed, remove a stale `.git/index.lock` before checkout.
- Install `yara-python` into a scratch `--target` directory and import it with `sys.path.insert`: it avoids a global install. Always scan a synthetic clean profile alongside the source tree, because a match on a skill shipped in the source is expected while a match on a clean profile is the actual false positive.
- Use the repository's own feed generator as schema authority for import formats, and verify a generated artifact against the checked-in generated file by SHA-256: hand-mapped column names and type mappings drift from what the rules actually read. Report types the format cannot carry instead of dropping them silently.
- Claim only the validation that actually ran: passing a syntax lint when a file is written is not the same as running the repository's validator and test suite.

## References

- `references/rule-specificity.md`: decision table for classifying detection rules and reporting false-positive risk.
- `references/rule-testing-recipes.md`: commands for pinned source scans, YARA clean-profile baselines, branch probes, hardened copies, and import-format verification.
