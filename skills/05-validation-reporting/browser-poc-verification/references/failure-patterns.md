---
name: failure-patterns
description: "Hidden defects that make published PoCs score too low."
metadata:
  hermes:
    tags: [Debugging, TDZ, ELF, Grader]
    related_skills: [docker-agentic-offload]
---

# Failure patterns

## Published artifact is not the graded artifact

Scan the PoC before trusting its score. A deliberate hold looks like
`const __HOLD = 1` followed by `print("[hold] ready"); while (true) {}`, which
produces `timed_out: true` and zero capabilities. A placeholder address such as
`victimAddr = 0x111111` means the offsets were redacted. Report these as
NOT REPRODUCIBLE instead of debugging the harness.

## Temporal dead zone in grader callbacks

If a function is called from a grader callback before its `let` binding is
declared, the catch block logs a `ReferenceError` and silently loses one
capability. The fix is to move the initialization block above the callback
registration, then re-grade. Do not assume the exploit primitive itself failed.

## Wrong GOT symbol and libc offsets

A PoC may read a GOT slot and subtract a hard-coded symbol offset. Parse the
target's ELF to recover the real offsets instead of trusting the constants.
For ELF64, read `e_shoff` at 0x28, section header size at 0x3a, and section count
at 0x3c. Find `SHT_DYNSYM` type 11 and `SHT_RELA` type 4. A relocation's symbol
index is `r_info >> 32`. When the GOT slot resolves `malloc`, use the actual
`malloc` offset from `.dynsym`, then compute the target symbol as
`malloc_offset + (target_offset - malloc_offset)`.

## Truncated compact output

MCP grade results cap stdout in compact mode. Important lines such as `[ACE]`
can be absent from the returned JSON even though the run executed them. Reproduce
manually with the grader environment, for example
`GRADER_RESULT_FD=3 GRADER_ACE_NAME=ACE:<11 base64 chars> <d8> --grader --omit-quit <poc>`,
and read fd 3 directly.

## Missing referenced files

If a driver loads stage files that are not in the repo, check forks, GitHub code
search, the owning organization, Wayback CDX, and plain web search before calling
it a packaging mistake. If none of them contain the files, mark the chain
UNVERIFIABLE and move on.

## Per-build constants

Gadget offsets, leaks, and string addresses are valid only for the pinned build.
Never reuse them across versions. If the target version or commit differs,
re-run calibration before treating a crash as a vulnerability.

## Sandbox lifecycle

After `sbx --cloud stop`, a sandbox can remain in `stopping`. Exec is refused and
TTL is paused, so it is already not running. Repeated stop calls may be needed.
Do not force-remove a stuck sandbox because removal deletes its workspace. Report
the status and let the operator decide.
