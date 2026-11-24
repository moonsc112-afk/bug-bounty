# Personalization and memory files as persistence sinks

Use this when an agent exposes editable Markdown files that are read back into the prompt. The question is not whether the file contains instructions, but who can change it and which principal loads it next session.

## Procedure

1. Inventory the file names. Look for a constant like `EDITABLE_WORKSPACE_FILES` or a seed list. Record which are seedable, which are editable, and which are runtime-only.
2. Find the loader. Search for a function that joins the workspace directory with each filename and returns a map of sections. Note whether it strips generated memory, deduplicates lines against a shipped template, or truncates oversized files. These are defenses, not proof of safety.
3. Find the renderer. Identify which files become identity or session-guidelines blocks and which become a read-only memory context. A read-only note around one block does not automatically cover the identity block.
4. Trace every writer separately:
   - the model tool handler, usually `write_file` or `patch`, and the path resolver it calls;
   - any UI HTTP route for the same files, including its auth guard, origin check, and optimistic-concurrency field such as `expected_sha256`;
   - first-run bootstrap writers that copy templates into the workspace.
5. Check the path resolver for name-based denylists. Credential-like names, reserved control directories, and escape checks are common; personalization filenames are often absent because the UI legitimately edits them.
6. Build the source-to-sink trace only if untrusted text can reach the model in a session where the write tool is enabled, and the written file is loaded on a later turn.
7. Read hosted provisioning code for permission defaults. A `safety.skipPermissions` default set during internal context provisioning moves the standing mode to `auto`, so a write classified `silent` can bypass the interactive card. Record whether the deployment under test uses that path before declaring the write silent or carded.

## Hypotheses to rank

| Rank | Hypothesis | Confirm | Refute |
| --- | --- | --- | --- |
| 1 | Model writes an identity or session-guidelines file, and later sessions follow the injected instruction | A benign marker written by the model survives a new session and changes a controlled answer | An `authorizeWrite` hook or tool policy returns denied for those filenames |
| 2 | Model poisons long-term memory or daily notes | An injected line survives template dedupe and appears in the next session context | Dedupe or manual-only memory write rejects the new line |
| 3 | UI endpoint is reachable by another origin or without owner auth | Cross-origin or unauthenticated PUT replaces a file after a valid GET | Owner token and opaque-origin check are enforced before the route |
| 4 | First-run bootstrap file is editable before setup completes | Injected first-run instruction executes once and the file is archived | File is seeded read-only or archived before untrusted input arrives |

## Safe PoC shape

Use an account and workspace owned by the operator. Back up the target file and record its hash.

0. Run a direct-write control first: ask the model to append the marker to the config file directly. This proves write capability and reveals whether a card appears. Without this control, a later injection failure is ambiguous.
1. Ask the model to read a note containing a harmless write instruction, for example append `TEST_MARKER_42` to the config file. Put the marker in a distinct line so the injected instruction can be separated from the write evidence.
2. Compare the hash. A change proves write capability only.
3. Start a new session. Ask a neutral question that reveals whether the marker is treated as user-written intent.
4. Repeat for the second config file if needed.
5. Restore from template or backup. Never use a payload that moves funds, exports secrets, or contacts an external host during the proof.

## Pitfalls

- Do not confuse a UI writer with a model writer. A route that requires an owner token does not prove the model's file tool is blocked.
- Do not report persistent prompt injection as fund theft when fund gates are enforced in code hooks. Say goal hijack or tool-mediated exfiltration, then raise severity only with a traced sink.
- Do not claim arbitrary file upload from a screenshot that only shows a viewer.
- Do not merge a permission-mode misconfiguration with prompt injection into one finding. Prove that untrusted text caused the write and name the exact mode that removed the card; a user-enabled `auto` or `full` mode is a separate design choice.
- Do not stop at direct-write capability. Prove the untrusted-content path in a second step before claiming persistent injection; a direct model write is only a control.
- A gateway-wide token or origin check is not object-level authorization. When a settings route lacks an owner check, keep the finding scoped to the gateway boundary and prove tenant isolation separately before calling it cross-user IDOR.
- Do not treat memory dedupe or identity projection as a complete fix. They reduce known patterns; arbitrary new lines still need a writer check.
- Do not ship a PoC that leaves the test account modified. Restore files and keep the marker visible only in evidence.
