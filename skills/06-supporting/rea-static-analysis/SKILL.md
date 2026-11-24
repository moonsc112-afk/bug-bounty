---
name: rea-static-analysis
description: "Use when analyzing code with REA MCP. Scope and verify."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [rea, static-analysis, electron, reverse-engineering, code-audit]
---

# REA Static Code Analysis

Use when the user asks to analyze code, an Electron app, an archive, or a binary with REA. The deliverable is a short evidence-backed findings report with concrete facts and `path:line` references, never a raw graph dump.

## When to Use

- User asks to analyze code or an application with REA, for example in Indonesian.
- Need architecture, IPC, preload, or security-surface facts without executing the target.
- Need to inspect an obfuscated codebase where normal source reading is insufficient.
- Need passive facts about a live web/JS surface (script bundles, endpoint candidates, browser targets) without mutating the page.

REA tools are deferred here: load schemas with `tool_describe`, then invoke with `tool_call`. Do not assume a tool exists just because its name appears in another tool's description.

## Procedure

0. **Check version freshness first.** Read the installed version from `mcp__rea__binary_session` (`server_identity.package.version`) or the installed `rea-agents/package.json`, then compare with `npm view rea-agents version dist-tags`. State which version produced an analysis; tool catalogs and schemas change between releases.
1. **Check the REA session and capabilities first.** Call `mcp__rea__binary_session`. Its response can exceed the inline budget and spill to a file; parse that saved JSON once with `json.JSONDecoder().raw_decode(...)` and ignore the trailing `<mcp-result-metadata>` block instead of re-requesting it. From it read `capabilities`, `analysis_provider_candidates` and `tool_availability.groups` to learn which providers and operations are actually available.
2. **Pick the right target and scope.** For an unpacked Electron app, analyze the JS application root, not the large launcher EXE. Call `mcp__rea__analyze_javascript_application` with absolute `input_path`, `detail: "summary"`, and an explicit `source_paths` list of exact relative paths. Use separate scoped passes for vendor or obfuscated core and for first-party modules; this makes the architecture split visible. Omitting `source_paths` analyzes thousands of inventoried files; globs are rejected.
3. **Read the summary fields rather than the graph.** `normalized_result.summary` gives `statistics` (files, AST nodes, findings, parse failures) and `electron` (contextBridge APIs, exposed members, IPC operations, literal channels, main handlers, sender validation observations). `coverage` and `limitations` tell you what REA could not resolve. Record those limits in the report.
4. **Get detail via export when the inline budget is exceeded.** `detail: "complete"` on analyze or evidence bundle can exceed REA's stdio response cap. Use `mcp__rea__export_evidence_bundle` with a caller-chosen absolute scratch path, then parse the file locally with Python. `get_evidence_bundle` filters require `detail: "summary"`; a filtered complete request is rejected. If `inspect_analysis_view` is absent from your tool subset, export plus local parsing is the working route.
5. **Extract concrete facts from the exported bundle.** Read `records[].normalized_result.graph.nodes` for high-level facts (`ipc-channel`, `ipc-handler`, `context-bridge-api` nodes carry channel names and exposed members in `observations[].properties`) and `.semantic_graph.nodes` for file/line/column in `evidence.location.value`. Build a node-id map before walking `relations`. See `references/javascript-application-graph.md` for field details and a parsing pattern.
6. **Cross-check every REA claim against real source.** REA is static and conservative. Read `preload.js`, the `ipcMain.handle` wrapper and `webPreferences` directly; decode obfuscated JS booleans by hand (`!![]` is true). Phrase negative results as static observations, not runtime proofs, for example no sender-validation observation rather than no validation exists.
7. **Report for this user.** Indonesian, casual register, no em-dash. Lead with a compact results table, then 3 to 5 concrete findings with `path:line`, then explicit analysis limits, then 3 to 4 numbered next-action options. Include the exported evidence path as a verifiable handle. Offer heavy native or Ghidra work as an offload recommendation, not as a local default.

## Web and JS browser surfaces

- Discover the browser CDP endpoint from the host (`netstat -ano | grep LISTEN`,
  then `curl <endpoint>/json/version`) and pass it plus an explicit
  `allowed_origins` list to `mcp__rea__list_browser_targets`; use the returned
  `target_id` in later calls.
- `mcp__rea__analyze_web_bundle` requires a `view` object. On a fresh call its
  projection accepts only `collection` values `summary`, `endpoints`, or
  `inferences`; richer views need retained evidence. Ask for `summary` first,
  then a narrow projection.
- Treat bundle endpoint lists as candidates: unresolved fetch sites and lazy
  chunks appear as coverage limits, not proof of absence. Cross-check live call
  shape with a CDP fetch/XHR recorder when it matters (see web-api-bounty-hunt,
  `references/js-bundle-recon.md`).
- `inspect_web_page` and `observe_web_session` collect only after attach. A page
  that already navigated yields `attach_limited` with an empty network or
  timeline section; arm REA before navigation or use direct CDP for live flows.

## Pitfalls

- Do not assume the live MCP server matches the installed package after `npm install -g`: the running process keeps its old version and `binary_session` reports `alignment.state = mcp_server_restart_required`. Restart by killing the `rea.mjs` node processes, then calling `manage_connections` with `action: enable`, `connectors: [{name: "rea", mcp: true}]`. Hermes does not auto-respawn a killed stdio server.
- Do not plan Ghidra work on REA 6.10.1 with Ghidra 12.1.x or JDK 21: the provider requires Ghidra >= 12.2 AND a 64-bit JDK 25+, and reports `unsupported_version` otherwise. `rea doctor` with explicit `GHIDRA_INSTALL_DIR` and `JAVA_HOME` is the cheapest check.
- Confirm the engine supports the target's binary format BEFORE paying for toolchain setup: read the ELF `e_machine` first. A Solana SBPF/eBPF ELF (machine 247) is rejected by the Ghidra route at file-format level with `retryable: false`, however current Ghidra/JDK/Node are; use the behavioural program-test PoC for such programs (see solana-bounty-onchain-poc, Binary-level RE limits).
- When `binary_session` reports `inspect_evm_interface` as `unsupported_host` on win32, do not conclude EVM analysis is impossible. Run the REA CLI from a Linux x64 environment (WSL on this host) with a Node version above the CLI floor against the same installed `rea.mjs`, using the evmole provider, and label any standalone EVMole CLI output as a cross-check rather than as REA. Why: the bundled EVM interface profile is real-verified on Linux x64 only, while the CLI path follows the Node runtime instead of the MCP host.
- The REA CLI enforces a Node floor (>22.23.4 on 22.x, >24.22.1 on 24.x, or 26.12.1+); `rea doctor` prints the exact requirement. In a fresh Linux sandbox with an older system Node, install a supported Node tarball under the workspace and export its `bin` in the SAME script that runs `rea.mjs`, because each `sbx --cloud exec` starts a new shell.
- Do not read `target_support: unknown` in `binary_session` as a capability verdict when no target is open. The response explicitly means nothing has been opened yet; open the target and recheck candidates before telling the user a format can or cannot be analyzed.
- When editing `mcp_servers.rea.env` via `hermes config set`, a killed/respawned MCP server can still inherit the daemon's cached old environment. A directory junction from the old configured path to the new tool version fixes this without restarting the whole desktop app; verify the effective version with `binary_session` or `rea doctor`.
- If after reconnecting REA the tools vanish from `tool_search`/`tool_describe` (`manage_connections` reports `tools: []`), use the REA CLI directly with explicit env: `node <rea.mjs> inspect <path> --provider ghidra --format json`. Gateway `reload.mcp` can fail because of an unrelated disconnected server, so it is not a reliable repair inside a live session.
- Do not assume the live MCP server matches npm latest: Hermes registers a fixed tool subset from the installed version, and an upgrade needs a server restart plus tool re-discovery.
- When a second scoped pass through MCP fails with `resource_constraint` (retained representation allowance exhausted, retention never evicts earlier Evidence), do not retry the same MCP call. Export the existing bundle, then run the CLI in a fresh process: `node <rea.mjs> analyze-javascript-application <path> --source-paths-json <paths.json> --detail summary --evidence_output <bundle.json> --format json`, with SYSTEMROOT/COMSPEC/TEMP/APPDATA/USERPROFILE passed explicitly on Windows. The CLI writes its own evidence file and avoids the MCP session budget.
- Do not re-request a large `binary_session` result after it spills to disk; parse the saved file once.
- Do not analyze an entire app root without `source_paths`: thousands of unselected files become explicit unknowns and burn time.
- Do not call `get_evidence_bundle` with `detail: complete` plus filters; the guard rejects it. Use summary filters or export the full bundle.
- Do not treat static absence as runtime absence: dynamic IPC channels are never paired and runtime registration is never evaluated, so say what REA did not observe.
- Do not read zero `electron.*` summary counters as proof of no IPC surface: conditional findings with an unknown module loader are excluded from summary counts but still appear as `ipc-handler` and `ipc-channel` nodes in the exported graph, so cross-check the nodes and the source before reporting.
- Do not report IPC/contextBridge nodes at face value on a non-Electron target. `context-bridge-api`, `ipc-channel` and `ipc-handler` emitted by `rea-javascript-artifact-reconstruction` with confidence low and no matching literal in the package text are reconstruction artifacts, not an attack surface. Grep the literal channel and member names in the raw source before believing any IPC observation.
- Do not assume REA's browser tools can retroactively see traffic from before attach; an empty timeline means the observation window missed the activity, not that the page made no calls.
- Do not pass a `view.collection` value that is only valid on a projected evidence id into a fresh `analyze_web_bundle` call; the guard rejects it with `invalid_input`.
- Do not paste graph nodes or evidence JSON into chat; summarize counts and named observations, keep the full evidence on disk.
- Do not start Ghidra on a 100 MB plus Electron executable locally without first warning about cost and recommending the cloud or Docker sandbox offload.

## References

- `references/javascript-application-graph.md` - evidence bundle layout, node kinds, Electron surface checklist, obfuscation notes.
