# Submission PoC appendix ("PoC Required" attachment)

Assemble ONE PDF per submission set that carries the reproducible evidence for every
PoC it cites. Keep the operator-facing narrative in the Indonesian report; this is the
reviewer-facing artifact.

## Sections that work

1. **Harness** — what the Foundry project deploys and why it is faithful: the verified
   source of the LIVE implementations (impl addresses read from the EIP-1967 slot), the
   production call shape (e.g. liquidate inside the Timelock leverage bracket so the
   position fee is the bracketed value), and which invariants the assertions encode.
2. **Reproduction** — the exact `forge test --match-contract … -vv` command(s).
3. **Test run (verbatim)** — the `[PASS]`/`[FAIL]`/`Suite result` lines from a run made
   for this build, plus one embedded full-output block per suite (3.1, 3.2, 3.3 …).
   Each of those blocks must come from a run made NOW — never a stored log file.
4. **Live on-chain reads (raw output)** — a table of Item / Command / Output with the
   real stdout, including the zeros (`feeReserves = 0` is evidence, not noise).
5. **Hash manifest** — sha256 + size for every test file, `foundry.toml` and log.
6. **Scope targets exercised** — proxy/impl table limited to addresses on the program's
   in-scope list, so triage can map the PoC to the scope entry.

## Build steps

1. Run the full suite fresh and capture stdout (a variable, not a file a previous run may
   have written), then extract the PASS/FAIL/Suite/Ran lines.
2. Re-run each suite whose output you intend to embed and embed THAT stdout.
3. Capture the live-read commands' raw output by calling the binaries directly
   (`C:\Users\<user>\.foundry\bin\cast.exe` + `shlex.split`) — shelling out through a
   subprocess `bash` on Windows lands in WSL and silently produces `command not found`
   cells in the appendix.
4. Hash the artifacts, then emit HTML with print CSS (`@page { size: A4 }`) and render
   with Playwright using the explicit chromium executable path
   (`E:/tools/playwright-browsers/chromium-1255/chrome-win64/chrome.exe`),
   `page.pdf(format="A4", print_background=True)`.

## Gates before sending

* Grep the generated HTML/text for `[FAIL]`, `[stderr]`, `Error:`, `command not found` —
  any hit means a stale log or a broken command slipped in.
* Confirm the embedded test counts sum to the suite total on the summary line.
* Screenshot one page containing a table and look at it: a vision pass that reports
  mojibake in long hex numbers (e.g. `5e38` where the value is `5e30`) means digits were
  lost in the render — re-check the source value programmatically instead of trusting
  the image.
* Only the test files and logs actually cited by a draft belong in the appendix;
  anything else is a surface for a reviewer question.
* A PoC that only logs is not evidence: every cited suite must carry `assert*` on its
  impact (outputs moved, balance/supply deltas, restored state == baseline) — a program
  that requires "a PoC that asserts it" bounces console-only tests, and a reviewer cannot
  tell a vacuous pass from a real one. Embed the assert-carrying log lines, not just the
  PASS totals.
