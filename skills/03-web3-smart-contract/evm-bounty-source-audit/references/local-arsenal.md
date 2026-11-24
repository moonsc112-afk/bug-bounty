# Local arsenal & bounty workspace

Machine map for hunt planning and capability audits. Installs drift — verify with `command -v` (native) or `wsl.exe -d Ubuntu-24.04 bash -lc 'command -v ...'` before relying on a tool. Prefer plain `command -v a b c` over shell loops through wsl.exe from git-bash (loop variables can arrive mangled), and never put `$(...)` or backticks inside the `bash -lc '...'` argument: an outer shell layer expands them BEFORE the inner command — and before any `cd` in the same string — runs, yielding empty substitutions and misleading "file not found" errors. Use absolute paths, recipients files (e.g. `age -R merkl.keys`), or separate invocations instead.

## Tool map
- Native Windows: Foundry (forge/cast), full Slither suite in ~/.local/bin (slither, slither-check-erc, slither-check-upgradeability, slither-read-storage, slither-simil, slither-mutate, slither-prop, slither-find-paths, slither-flat), Medusa fuzzer (medusa.exe), crytic-compile, solc + solc-select, uv/uvx.
- WSL Ubuntu-24.04 (root; E:\WSL\Ubuntu-24.04): cargo, anchor, solana/Agave. EVM tools are not in WSL and Solana tools are not native — route each path to its environment.
- REA (`rea-agents` npm global, CLI `rea`): skill `reverse-engineer-anything` (~229 MCP tools) for native/managed/Electron/firmware/browser targets and AgentEnv web-app bundles. Engines: Ghidra 12.1.4 at E:\berkah hoki\ghidra_12.1.4_PUBLIC with JDK 21 alongside; JADX headless MCP jar under ~/.local/share/rea/android. Hopper is macOS-only — its absence on Windows is expected, not a fault. Diagnostics: `rea doctor --json`. MCP registration lives in ~/.config/opencode/opencode.jsonc (env: GHIDRA_INSTALL_DIR, JAVA_HOME, REA_JADX_MCP_JAR); other clients need their own registration.
- craft-anything: investigation MCP + skill (~/.claude/skills/craft-anything) enforcing brief → plan → hypotheses → findings → handoff with evidence; portable CLI under E:\tools\craft-anything-app. Good scaffold for digging one lead deep.
- Other agents on this machine (Claude Code, Gemini/Antigravity, opencode, Cline, Zed, Qoder, WorkBuddy) carry predominantly creative/video skills (hyperframes, media-use, chatcut, OpenMontage, impeccable, shuohao novels, creator-generalist) — not security; no need to re-audit them from scratch. Security-relevant exceptions: REA, craft-anything, and generic dev skills under E:\projects\_skillsrc\ffmpeg-skill\.claude\skills (code-review, defect-reports, verifying-external-behavior).

## Bounty workspace layout
- E:\bug bounty\ — target-selection/ranking PDFs, report-builder scripts, and pulled target repos (<protocol>-contracts).
- E:\audit\<protocol>\ — reading/working copies (e.g. kamino, tenbin, zircuit-finance).
- Target repos often ship audit/ with prior auditor PDFs (Spearbit, Zellic, Fuzzland, Cantina, scope docs) plus echidna.yaml + echidna.sh, slither.config.json, certora/ specs. Read prior reports FIRST to avoid re-reporting known issues; they also show which bug classes were already fuzzed.
- Run shipped harnesses only after confirming their tool exists: echidna/certora-run may be absent while Medusa is installed. Check foundry.toml profile `skip` rules — invariant harnesses are often excluded from the default profile and need FOUNDRY_PROFILE=<name>.

## Progress status cross-reference (what's been worked / what's left)
The operator runs several agents in parallel and treats their combined output as "your work". Reconcile every agent's artifacts against the target universe in the attached research/progress PDFs before answering a status question or picking the next target.

Where each agent's work lives:
- Hermes: E:\audit\<protocol>\ (NOTES.md, findings/, fuzz-* harnesses) + WSL ~/audit build copies. session_search browse (no args) first — a parallel session may be auditing a target right now; discovery accepts OR queries ("Pendle OR Rain OR Mezo") for multi-target checks.
- Merkl (AngleProtocol/merkl-contracts cdce25d): workspace at C:\Users\TUF-GAMING\.gemini\antigravity\scratch\merkl-bug-bounty\ — repo clone, phase2/ (app+studio bundles, openapi.json, Halborn PDF), AuditPoC/AuditFork/AuditInvariant + AuditDeepPoC/AuditDeepFork test files, MERKL_DEEP_AUDIT_2_ID.pdf, EMAIL_REPORTS.md (+ EMAIL_REPORT_4_F_DEEP_01.md). FINAL submission set: report.txt + report.age (age-encrypted to Merkl's key with the payout filled) + SUBMISSION_README.md; the C: path now resolves through a symlink into E:\C-relocated\Users\TUF-GAMING\.gemini\... (both paths work). On-chain wrapper-inventory scripts + evidence JSONs + mirrored backups in Hermes scratch merkl_recon/. Status: SUBMITTED — operator sent report.age from their own mail client to security@merkl.xyz (subject "Security report (age-encrypted) - 4 verified findings"); awaiting triage, do NOT resend. Agent-send fallback: generic sender in this skill (scripts/send_report_email.py) + user-filled app-password ini at C:\Users\TUF-GAMING\merkl_mail_cred.ini; report.age also copied to the Desktop.
- AutoClaw (opencode): the progress-report PDF the user attaches IS that agent's work record (rounds, triage, monitor tables). Its hunting/ workspace may not exist on disk — don't burn time hunting for it. A repo in the daily-monitor table is tracked, NOT audited.
- Gemini Antigravity: clones under ~/.gemini/antigravity/scratch/<target>/ (several repos per target; derived artifacts like diff files show delta prep, not a completed audit). Conversations: ~/.gemini/antigravity/brain/<uuid>/.system_generated/logs/transcript.jsonl (also check the antigravity-ide/ and antigravity-backup/ brain roots).

Classify each target, then answer as a status table over the PDFs' priority targets + grouped untouched tiers + pending next steps:
audited (notes/findings/report present) → partial (named pending sessions/unread surfaces) → blocked (private source, KYC gate, ABI-only repo) → monitor-only → cloned-only (source acquired, zero review artifacts) → untouched.
Findings awaiting human gates (on-chain PoC, deposit/KYC, submit decision) are PENDING, not done.

Parsing Antigravity transcripts (JSONL, one object per step: {step_index, source, type, status, created_at, content, thinking, tool_calls}):
- type=USER_INPUT: task text is wrapped in <USER_REQUEST>...</USER_REQUEST> — regex-extract.
- source=MODEL, type=PLANNER_RESPONSE: agent turns (thinking + tool_calls; final summaries in content).
- type=GENERIC: tool output — skip when summarizing intent.
Recipe: per uuid, print date range + user requests + last MODEL non-GENERIC contents; that identifies each conversation's task and conclusion in one pass.

## Pitfalls
- A standalone clone of a monorepo subdir keeps AGENTS.md references to a root index (@../../AGENTS.md) and named skills that are absent from the clone — resolve them from the upstream GitHub repo instead of assuming they exist locally.
- Repo docs and harness scripts drift apart (test paths, profile names) — trust the script/config actually present over prose, and read the script before running it.
- Recursive grep over a whole brain/ tree times out — browser_sandbox outputs and media dominate it. Glob only */.system_generated/logs/transcript*.jsonl and grep those; bounded find -maxdepth misses them (the path sits ~7 levels under ~/.gemini) — glob the known layout instead.
- A target keyword in a transcript's GENERIC tool output or injected system context is not evidence of work on that target — confirm via USER_INPUT and the final MODEL summary. Clone timestamps ≠ audit timestamps: require review artifacts before upgrading cloned-only to audited.
- Vyper-source Foundry repos need a `vyper` executable on PATH before any `forge build`: install with `uv tool install vyper` and export `PATH="$HOME/.local/bin:$HOME/.foundry/bin:$PATH"`, otherwise the build stops at the Vyper sources. For submodules, run top-level `git submodule update --init --force --depth 1` first and verify a known lib file exists; `--recursive` can chase deeply nested chains (forge-std inside OZ inside tokenized-strategy) and exhaust a multi-minute timeout. Go recursive only when a build names a missing nested import.
- Fork tests pinned to a historical block: probe each candidate RPC with one `eth_getBalance` at that exact block before choosing it, because head-only and token-gated endpoints answer chain-ID calls but fail when the fork fetches old accounts. Run targeted test files rather than the whole fork suite, since repeated `vm.createFork` setups can exhaust a public endpoint's request cap and bury real results under 429s.
