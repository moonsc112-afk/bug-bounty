---
name: browser-poc-verification
description: "Use when verifying browser PoCs; reproduce and cross-check."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Security, Research, Verification, Browser, Exploit]
    related_skills: [docker-agentic-offload, writeup-intel-digest]
---

# Browser PoC verification

## When to use

A post, repo, or report claims that a browser or V8 exploit works, that a benchmark
score was reached, or that a model produced a working chain. Use this before
repeating the claim, before writing a report, and before spending local compute.

## Ground rules

- Never run the PoC on the operator PC. Use a cloud sandbox.
- A README score is a claim, not a result. Always record claim versus actual.
- One hypothesis at a time. Use a fresh grader process per grade because
  capabilities can accumulate inside one server.
- Evidence needs two independent sources: an application beacon and an OS-level
  observation such as `/proc/<pid>/maps` or an exact process-name check.
- If the artifact is incomplete, say so. Do not fill gaps with plausible code.
- The operator handles accounts and public submissions. The agent prepares PoCs,
  logs, and drafts.

## Tooling on this machine

- `sbx` CLI controls cloud sandboxes. The shell opens in `/home/agent/workspace`.
- Host tools used for triage: `curl`, `gh search code`, `python3`, `git`.
- For benchmark images and MCP grading, follow `references/runtime-setups.md`.
- For real Chrome builds, follow the same reference file.
- For a web3 UI-versus-wallet signing differential, follow
  `references/web3-wallet-differential.md`.
- For a flow that depends on the operator's own logged-in browser, use
  `computer_use` to drive the real desktop Chrome window; the browser tool's
  local profile is a managed copy and does not share the operator's sessions.
- For debugging low scores and hidden defects, follow
  `references/failure-patterns.md`.
- Keep durable artifacts under
  `C:/Users/TUF-GAMING/AppData/Local/hermes/reports/<target>/`.

## Workflow

0. Capture provenance. Save post ID, timestamp, repo commit, and how the content
   was fetched. Separate the poster's marketing claim from the technical artifact.
1. Pin the target. Write down exact version, V8 commit, architecture, flags, and
   a hash of the build. Any offset without a build hash is worthless.
2. Inventory the artifact. List every file and size. Flag wrappers that reference
   missing files, placeholders such as `0x111111`, and deliberate holds such as
   `__HOLD = 1` or `while (true)`.
3. Choose isolation. A benchmark image needs selective OCI extraction and the MCP
   server. A real browser needs a dedicated VM with Xvfb and a local HTTP server.
4. Define the oracle before running. Decide what observable means success: a
   beacon, a grader pipe line, a process name, or a capability flag.
5. Reproduce. Run the PoC and capture stdout, stderr, grader fd 3, and HTTP logs.
   Use a fresh server process for every grade call.
6. Cross-check. Compare leaked bases against `/proc/<pid>/maps`, confirm payload
   processes with `pgrep -x`, and read `cmdline` to identify the renderer.
7. Triage failure. Read the full log before blaming the harness. Check temporal
   dead zones, wrong symbol offsets, truncated compact output, and missing files.
8. Report. Produce a claim versus actual table, exact commands, evidence paths,
   and a list of remaining unknowns.

### Driving the operator's real browser

Use this when the operator logs into an account personally and the PoC must run
in that exact session:

1. `computer_use list_windows`, then identify the visible Chrome window by title.
   Capture with `action='capture', mode='som', pid=..., window_id=...` and act on
   the numbered element indices, not screenshot coordinates.
2. Read state from the capture's element labels and `vision_analysis`. Do not
   infer the real browser's state from a `browser_exec` profile; it is a separate
   browser copy.
3. Re-capture after every state-changing action. Input delivery can be reported
   as unverifiable, so the next capture is the only confirmation.
4. Chrome windows can drop background keystrokes and wheel events. When the
   tool's `verdict` says `escalate` with `foreground`, reissue that one input with
   `delivery_mode='foreground'`; do not repeat a background input that was
   silently dropped.
5. For a consent dialog whose confirm button stays disabled until the user
   scrolls, scroll the dialog container, re-capture, and click the button only
   after its label changes to the enabled action.
6. Keep account actions (login, password, email change) with the operator. Drive
   navigation and consent only, and record the resulting page text as the oracle.
7. When an external observation tool attaches after navigation and returns an
   empty network/timeline with `attach_limited`, reconstruct the redirect chain
   from the browser's own `Page.getNavigationHistory` session instead of re-arming
   the observer; a late attachment cannot recover events it never saw.

## Evidence contract

Every verification folder must contain:

- `claim-vs-actual.md` with one row per claim and the measured result.
- `commands.txt` with the exact commands used.
- `evidence/` with raw logs, `maps` snapshots, and process listings.
- `patches/` with any modified PoC plus a diff from the original.
- `lessons.md` containing only confirmed lessons.

## Reporting template

```markdown
| Claim | Source | Actual | Evidence | Status |
|---|---|---|---|---|
| 15/16 | README | 0/16 | evidence/fd3.txt | NOT REPRODUCIBLE |
```

Use one of these statuses: MATCH, PARTIAL, NOT REPRODUCIBLE, FIXED, UNVERIFIABLE.
Do not promote a hypothesis to a finding without evidence.

## Notes

This skill is about verification, not about discovering new vulnerabilities. It
was distilled from auditing three ExploitBench chains and one Chrome for Testing
chain, where two published scores did not survive reproduction and one chain
passed only after two defects in the published PoC were corrected.
