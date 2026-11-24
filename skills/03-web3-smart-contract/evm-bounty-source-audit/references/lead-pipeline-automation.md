# Lead pipeline automation for AI-assisted bounty hunts

Use when building or running a reusable stage machine that takes a human impact
hypothesis, verifies it with agents, builds a PoC, and drafts a report. This is
the workflow layer on top of the static/fuzz audit described in SKILL.md.

## 1. Core rule: agent verifies, human hypothesizes

Keep the agent as a verifier of a named human hypothesis, never as a generic
pattern generator. Feed it a sentence of the form "if X then Y so victim loses
Z", not "find bugs in file A". Generic prompts find valid issues that everyone
else finds, and duplicates pay nothing. Encode the "never submit" list and
kill-fast rules in the validator; do NOT seed the generator with common bug
patterns. Those two roles are easy to conflate.

## 2. Stage machine

```
NEW -> DEDUP -> STATIC_REACH -> DYNAMIC_POC -> NEGATIVE_CONTROL
     -> GENERALIZE -> IMPACT_GATE -> REPORT_DRAFT -> HUMAN_TRIAGE
     -> SUBMITTED | KILLED | RETRACTED
```

Store every stage as an attempt row with tool, command, output reference, exit
code and verdict. Store evidence separately with a type (scope, dedup, static,
poc, diff, generalize). Persist to SQLite with WAL and foreign keys. Retraction
must keep the original signal and the disproving observation, never silently
drop a killed lead.

## 3. DEDUP before any PoC

1. Scan only the program directory plus all `*/findings/*.md`. Exclude `lib`,
   `node_modules`, `target`, `out`, `vendor`, `cache`.
2. Tokenize the impact class, target and hypothesis. Do NOT score on the program
   name; every document in the same program would look like a duplicate.
3. Drop tokens whose document frequency exceeds about 30 percent of the corpus.
   Words such as vault, loss, funds and until otherwise mark everything as dup.
4. Collapse identical documents by content checksum and keep a copy count, so
   worktree mirrors do not flood the result.
5. Require at least two distinctive tokens to register a hit; raise the kill
   threshold rather than accepting small overlaps. Cap stored evidence and keep
   the full hit list in a JSON report.

## 4. STATIC_REACH

EVM: run slither to JSON for detector evidence, and read the target function's
visibility and modifiers from source with a regex. An internal or private
function is a warning about a missing public caller, not an automatic kill.

Solana: run `cargo check --workspace` and emit the six-pattern platform coverage
table from `solana-vulnerability-scanner`. Strip Rust comments before scanning;
a comment naming `invoke()` or `create_program_address()` otherwise produces a
false `found` verdict.

## 5. DYNAMIC_POC and NEGATIVE_CONTROL

Run the PoC with a machine-readable output and assert on an asset delta. A
green test alone is weak evidence; require an explicit impact marker in the log
when the test can emit one.

Negative control proves the PoC tests the bug rather than the setup: make a
detached git worktree, apply a patch that installs the missing guard, run the
same test there, and require it to fail. Clean up the worktree in all paths.
If the patch cannot be applied, report that the control was not run and leave
the status at DYNAMIC_POC. Never convert a failed patch into a KILLED finding.

## 6. GENERALIZE

Re-run the same PoC under multiple variants: different fork blocks for EVM,
different amounts, mints or env values for Solana. Every variant must pass; one
failure means the exploit only works in the setup it was developed against.
Keep an explicit variant list in the report so the claim is reviewable.

## 7. Report gate

Draft with the title formula `[Bug class] in [contract/function] allows [actor]
to [impact]`. Run the five pre-severity questions from `finding-validation-gate`
before claiming High or Critical. If any answer is missing, downgrade one level
and list the gap. Never let the tool upgrade severity.

## 8. Execution environment rules that cost time to rediscover

- Invoke WSL with a script file: `wsl -d <distro> -- bash /mnt/c/.../script.sh`.
  Inline `bash -c '...$var...'` loses variables and quotes through git-bash.
- From native Python on Windows, call the native git at
  `C:/Program Files/Git/cmd/git.exe`. The MSYS git on PATH raises WinError 5
  when launched by CreateProcess.
- Prepend the Foundry bin directory to PATH for any process that spawns `forge`.
  The default PATH may resolve `forge` to an unrelated CLI.
- Set `CARGO_TARGET_DIR` to a persistent path under the WSL home. Do not use
  `/tmp`; it is cleared between WSL invocations on this host.
- WSL does not forward custom environment variables to Windows `node.exe`.
  Tests that read `ANCHOR_PROVIDER_URL` or `ANCHOR_WALLET` need a Linux node.
- Anchor CLI 1.2 defaults to surfpool. Use `--validator legacy` for
  `solana-test-validator`, and export provider URL and wallet explicitly.
- `anchor test --skip-build` needs artifacts in the repo: copy generated IDL
  JSON into `target/idl/` and provide minimal `target/types/*.ts` stubs for TS
  imports.
- Build keypairs are random and will not match `declare_id!`. In a disposable
  copy, generate the keypair, set `declare_id!`, the `[programs.localnet]` entry
  and the IDL address, then rebuild before trusting a suite result.
- Old Solana crates pin ahash versions that use `feature(stdsimd)`, removed by
  newer SBF toolchains. Move ahash 0.7 to 0.7.8 or newer and strip the
  `cfg_attr(feature = "stdsimd", feature(stdsimd))` line in the local registry
  copy of ahash 0.8 before building.
- When the installed anchor CLI is newer than the program's anchor-lang, IDL
  generation can fail with `IDL doesn't exist`. Install the matching CLI with
  avm rather than treating the compiled .so as a failed build.
- A suite that still fails on `PriceNotInitialized` or `InvalidAmount` after
  program IDs are aligned points at oracle or validator setup, not at a PoC.
  Verify the environment before reporting any of it as a finding.

## 9. Offload rule

Heavy builds (multiple Anchor programs, SBF compilation, large dependency
installs) are expensive on the capped WSL instance. Recommend Simular Box or
Kaggle for the build step before running it locally, and keep the local machine
for verification and reporting.
