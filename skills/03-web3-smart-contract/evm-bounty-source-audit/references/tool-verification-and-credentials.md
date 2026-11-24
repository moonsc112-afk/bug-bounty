# Tool verification and credential handoff

## Verify an open-source audit tool before relying on it

- Clone it into scratch, install dependencies in an isolated venv, run `--help`, mock the API responses offline to exercise proxy resolution and import rewriting, then do exactly one real authenticated fetch. A published tool is a claim until its code and output have been counted.

## Hand secrets to the operator, never to chat

- Never ask the operator to paste an API key or any secret into chat. Give one Git Bash command that writes the tool's expected `.env` path, for example `printf 'ETHERSCAN_API_KEY=*** 'their_key' > ~/.claude/skills/clone-contracts/.env`, and let them run it in their own terminal.
- Do not suggest Notepad Save As for dotfiles: a Save As dialog that is not set to "All files" can put the intended line into the FILENAME instead of the file, so the tool never sees the key. Verify presence with `grep -c`, never `cat`.

## Static analysis when Slither cannot parse the target

- Try the mechanical fix first: set `build_info = true` in `foundry.toml` and run `forge build` to emit `out/build-info/*.json` (Foundry 1.9 removed the `forge build --build-info` flag that older Slither calls), then `slither . --ignore-compile`. If Slither still fails on a newer solc AST, switch analyzers rather than repeating upgrades.
- Use `forge lint --json` as the static substitute. It emits **JSONL**, one diagnostic object per line, not one JSON array; parse line by line. Triage its categories before treating any as a finding: `calls-loop` and `require-revert-in-loop` on constructor/detection code, `unsafe-typecast` on deliberate byte packing, `reentrancy-events`, and `unused-return` on low-level calls are usually design, not bugs. A `non-reentrant-not-first` warning is harmless when the preceding modifier is a pure `require` with no external call.
- Record the substitute in the coverage ledger and state plainly that detector-based static coverage was not obtained. A tool that exits before emitting results is a blocker, never a CLEAN class.
