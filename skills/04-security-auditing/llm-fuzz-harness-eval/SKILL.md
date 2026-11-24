---
name: llm-fuzz-harness-eval
description: "Vet/run LLM fuzz harnesses like STITCH vs libFuzzer."
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [fuzzing, libfuzzer, stitching, llm, android, evidence]
---

# LLM fuzz harness evaluation (STITCH and friends)

Use when a post, paper, or tool claims an LLM-generated fuzz harness beats a
conventional fuzzer, or when setting up a local STITCH vs libFuzzer comparison.

## When to Use

- A forwarded post or paper claims an LLM-written harness beats libFuzzer.
- Setting up a local STITCH vs libFuzzer comparison on a C/C++ library.
- Choosing between STITCH and LibAFL Frida mode for an Android native target.

## Procedure

1. **Separate the paper from the replication.** Record both dates and versions.
   STITCH: arXiv 2602.18689v1 (21 Feb 2026) says 131 bugs / 73 patched; the
   CCS '26 abstract (14 Nov 2026) says 142 / 103. A post quoting v1 in Nov 2026
   is stale by nine months. Say which version each number comes from.
2. **Recompute chart claims from the dataset.** Data-driven articles often ship
   the raw runs in a companion JS file (for example `article.js`). Parse it.
   KPI tiles may compute mean-of-per-config-ratios rather than ratio-of-means,
   so never quote the headline multiplier without checking how it was formed.
3. **Check what precision actually includes.** STITCH's reported 70% precision
   follows an aggressive Triage Agent (221 of 265 crashes filtered) plus manual
   dedup. Without that step, most crashes are harness or oracle errors. Report
   the number with that condition attached.
4. **Set up the local baseline first.** Pin the target commit, build the library
   with `-fsanitize=fuzzer-no-link,address`, then link the harness with
   `-fsanitize=fuzzer,address`. If the library is not instrumented, libFuzzer
   only measures the harness file and the comparison is meaningless. Generate
   a benign seed with the target's own encoder when one exists; starting from
   the known crashing input measures replay, not fuzzing.
5. **Compare like with like.** Same duration, same CPU budget, and same
   coverage replay (for example `llvm-cov` on both saved corpora). Do not compare
   the two fuzzers' own edge counters; their instrumentation differs.
6. **Classify every crash by free site.** A free inside `exec_shim_*` is a
   generated-harness bug. A free inside the library source is a candidate real
   bug. LLM-written `FUZZ_ASSERT` failures are oracle findings, not bugs.
7. **For Android native targets:** STITCH needs source, Docker `linux/amd64`,
   compile-time SanitizerCoverage/ASan, and `fork()`. It fuzzes a host x86_64
   rebuild, not the phone. For closed-source `.so` targets, use LibAFL Frida
   mode on the device (no source, no root, ~6k exec/s one core, ~30k eight).
   Frida ASan on Android 16 has known shadow-bit, TLS-register, and deadlock
   issues; use crash detection plus an ASan reproducer instead.

## Pitfalls

- For Solidity and Foundry harnesses, apply the oracle-calibration rules in `foundry-audit-harness` before calling a failing property a protocol bug. WHY: the same harness/oracle error class appears there with contract-configuration, token-unit and setter-specific cases.
- Windows git checkout writes CRLF into `configure`, shell, and CMake files.
  Inside WSL, normalize `*.c`, `*.h`, `configure`, `Makefile*`, `*.sh`,
  `CMakeLists.txt`, and `*.cmake` with `sed -i 's/\r$//'` before configure.
  WHY: CRLF shell or CMake files fail with "required file not found" or stray
  `\r` tokens.
- Export `CC=clang CXX=clang++` before `cmake` when `CMAKE_C_FLAGS` carries
  clang-only sanitizer flags. WHY: CMake passes those flags to its compiler
  probe, and the default `cc` rejects `-fsanitize=fuzzer-no-link` before the
  harness is ever reached.
- Add the CMake build tree's generated-header directory to the harness include
  path. WHY: configure-time headers such as `opj_config.h` live in the build
  tree, not the source tree.
- Host git-bash may have no clang and no Docker while WSL has only gcc. Install
  clang in WSL; keep Docker and API keys as explicit prerequisites, never type
  or store a credential in a helper script.
- `hgarrereyn/STITCH` has no LICENSE on GitHub, none in the repo tree, none in
  PyPI metadata, and none in the sdist. Internal research is fine; commercial
  use, bundling, or redistribution needs written permission from the author.
  LibAFL itself is dual Apache-2.0/MIT.
- STITCH's advantage comes from API reach, not speed. Expect roughly 500x to
  2800x fewer executions per second than libFuzzer. A bad spec can cut off the
  parser entirely by replacing fuzzed file bytes with a fixed literal.
- Phone throttling drops LibAFL Frida throughput from ~30k to ~9k exec/s in
  minutes. Fewer steady cores can beat eight throttled ones.
- Write the comparison report in casual Indonesian, no em-dash, and end with
  numbered next-step options.

## Field artifacts

Example package: `E:/audit/stitch-poc` (pinned zlib, harness, baseline and
STITCH scripts). Notes: `Documents/stitch-paper-vs-replikasi-dan-android.md`,
`Documents/android-native-fuzz-workflow-quram-frida.md`, and
`Documents/stitch-license-status.md`.
