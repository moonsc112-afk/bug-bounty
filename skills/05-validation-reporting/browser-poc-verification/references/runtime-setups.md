---
name: runtime-setups
description: "Isolation recipes for benchmark images and real browsers."
metadata:
  hermes:
    tags: [Runtime, Sandbox, OCI, Chrome]
    related_skills: [docker-agentic-offload]
---

# Runtime setups

## Benchmark image without pulling it

ExploitBench `ghcr.io/exploitbench/v8-r1` tags are about 20-23 GB compressed and
roughly 70 GB expanded, which does not fit a 30 GB sandbox. Fetch OCI blobs
selectively instead of running `docker pull`.

1. Get an anonymous token from
   `https://ghcr.io/token?scope=repository:exploitbench/v8-r1:pull&service=ghcr.io`.
2. GET `manifests/<tag>` with the OCI index Accept header, pick the `linux/amd64`
   entry, then GET its digest with the image manifest Accept header.
3. Stream each layer with `urllib`, `gzip.GzipFile`, and
   `tarfile.open(mode="r|")`. Extract only matching members.

Extract `rlenv/problem/*`, `rlenv/mcp/server`, binaries under
`rlenv/binaries/{vuln,fixed}/{release,release-asan,coverage}`, and
`usr/local/bin/llvm-{cov,profdata,symbolizer}`. Create users `agent` 1000,
`grader` 1001, and `grader-diff` 1002. Directories `/rlenv/grader-run` and
`/rlenv/grader-diff-run` need mode 0700 and the matching grader owner or
preflight aborts.

Drive the server over stdio with newline-delimited JSON-RPC: `initialize`,
`notifications/initialized`, then `tools/call` for `setup` and `grade`. Use a new
server process for each `grade` call. `llvm-profdata` and `llvm-cov` must be on
PATH or the coverage sub-grader fails.

## Real browser VM

Create a dedicated shell sandbox, then install Chrome for Testing, Xvfb, xcalc,
gdb, and the Chrome library set. Install `libnspr4` explicitly and verify with
`ldd <chrome> | grep 'not found'`.

Serve the exploit page and every fetched file from one directory with
`python3 -m http.server`, start `Xvfb :99`, and launch Chrome with
`--headless=new --no-sandbox --disable-gpu --user-data-dir=<fresh>` plus the JS
flags the PoC requires. Beacons sent as `fetch("/leak?v=...")` land in the HTTP
server log. Use `grep -a` because encoded query strings can make grep classify
the log as binary.

Confirm payload execution with `pgrep -x <name>` or `ps -e -o comm= | grep -x
<name>`. A loose `pgrep -a <name>` can match the controlling shell's own command
line. A missing final beacon is acceptable when the exploit corrupts the stack
it returns through, provided the payload process is observed.

To verify a leaked module base, poll the HTTP log for the base value, scan
`/proc/<pid>/maps` for the browser binary, and compare the first mapping address.
Read `cmdline` for each match to identify the renderer. Forked children of one
zygote share the same base, so multiple matching PIDs are normal.

## Background processes

Use `setsid` for Xvfb and HTTP server. A plain `&` child of a short `sbx --cloud
exec` shell can bereaped when the shell exits. Do not use broad `pkill -f <pattern>` for cleanup
because the pattern can match the controlling shell and abort the setup. Kill by
exact PID or start a fresh sandbox.
