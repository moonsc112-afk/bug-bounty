# On-chain PoC against DEPLOYED Solana bytecode (no program build)

Proven on Kamino Scope TWAP finding (Nov 2026): demonstrate a logic bug end-to-end through the real deployed program without compiling the Anchor workspace.

## Core approach: dump + solana-program-test fixture
1. `solana program dump <PROGRAM_ID> scope.so --url mainnet-beta` — dumps the deployed ELF from the programdata account. Record provenance: programdata address, deploy slot, upgrade authority, fetched-at slot, sha256 of the ELF; `getBlockTime(deploy_slot)` via RPC gives the deploy date (sanity-check vs the source release tag).
2. Minimal Rust bin crate: `solana-program-test = "2"`, `solana-sdk = "2"`, `sha2`, `tokio` (macros + rt-multi-thread). `[profile.release] overflow-checks = true`.
3. Load the ELF: `ProgramTest::new("<name>", program_id, None)` + `pt.prefer_bpf(true)`; place the dump at `harness/tests/fixtures/<name>.so` — **fixture filename must match the program name string**. `start_with_context().await` runs the real production bytecode.
4. Create protocol state via the program's OWN instructions (e.g. `initialize` + `update_mapping_and_metadata`) — the test payer becomes admin; no mocked state. Use a fully controllable price source (Kamino: `SplBalance` oracle = token-account balance written directly via `ctx.set_account`, exp = mint decimals).
5. Drive time with `ctx.set_sysvar(&Clock { slot, unix_timestamp, .. })` per step; assert the program-recorded timestamp equals the injected one (catches silent clock-override failure).
6. **Differential design**: MAIN run (bug-triggering parameter) vs CONTROL run (parameter shifted just past the boundary, e.g. gap 3580s vs 3600s). Opposite outcomes prove causation on production bytecode, not correlation.

## solana-program-test 2.3.x API (differs from older tutorials — cost us a failed build)
- `ProgramTest::new(program_name: &'static str, program_id: Pubkey, builtin_function: Option<BuiltinFunctionWithContext>)` — program_id is NOT Option; new() already registers the program (don't also call add_program with a different name).
- `ProgramTestContext` fields: `banks_client`, `payer`, `last_blockhash` — there is NO `.client`.
- `ctx.set_account(&pk, &AccountSharedData)` — SYNCHRONOUS, takes AccountSharedData (`Account{..}.into()`).
- `ctx.set_sysvar(&T)` — SYNCHRONOUS (`&self`); calls `bank.set_sysvar_for_tests` → updates account + resets/refills sysvar cache. Works for per-step Clock control.
- `ctx.warp_to_slot(slot)` — sync; default genesis tick = 100µs × 64 ticks/slot = 6.4ms/slot, creation_time 0, and 2.3.13 has NO genesis-config setter → warping cannot produce arbitrary unix timestamps; prefer set_sysvar.
- Send txs with `banks_client.process_transaction_with_metadata(tx).await` → `res.result` (Option<Result<..>>) + `res.metadata.logs`. OBSERVED: `process_transaction_with_commitment_and_context(tx, Processed)` lost the Clock override (program read ts=0); the metadata variant preserved it. Use the metadata variant when injecting sysvars.
- `banks_client.get_latest_blockhash()` / `get_account(pk)` — async.
- When unsure, read the exact crate source: `/root/.cargo/registry/src/*/solana-program-test-2.3.13/src/lib.rs` (grep signatures) — faster than a failed build cycle.

## Hand-built SPL accounts (byte offsets matter)
- Token account (165 B): mint@0, owner@32, amount@64, delegate COption@72(4+32), **state@108 (1=Initialized, 2=Frozen)**, is_native COption@109(4+8), delegated_amount@121, close_authority COption@129(4+32). Writing the state byte at the wrong offset (e.g. 76) leaves the account Uninitialized → oracle/account parse failures.
- Mint (82 B): mint_authority COption@0(4+32), supply@36, decimals@44, is_initialized@45, freeze_authority COption@46.
- COption tag: 0=None, 1=Some (little-endian u32).

## Hand-encoded Anchor instructions — verify against source FIRST
- Discriminator: `sha256("global:<instruction_name>")[..8]`; args borsh (String = u32 len + bytes; Vec = u32 count + items; enum = u8 variant index).
- Enum variant index = DECLARATION order. Kamino OracleType keeps deprecated placeholders so declaration index == explicit discriminant (SplBalance=44, ScopeTwap1h=12) — verify this per enum, don't assume.
- Read the handler's `#[derive(Accounts)]` struct for exact account order + `has_one` constraints + remaining-accounts rules (Kamino update_mapping: one remaining account per entry — real price account for MappingConfig, crate::ID for others).
- **Take the discriminator from the `#[program]` function name in `lib.rs`, not the handler filename, the IDL camelCase name, or an abbreviated form.** Compute `sha256("global:<exact_fn_name>")[..8]`. A wrong name returns `InstructionFallbackNotFound (101)` from the program, which reads like "the instruction is not deployed" and has produced false KILL verdicts in coverage ledgers. Confirm a hit by finding `Program log: Instruction: <Name>` in the run log; fix the discriminator before drawing any reachability conclusion. IDL names can use a different word order from the Rust function.
- **Count remaining accounts from the program's own parser, not from the number of fixtures you loaded.** Parsers such as `ObligationRemainingAccounts::parse` reject with `InvalidAccountInput` when `remaining.len()` differs from active deposits + active borrows (+ referral states). Read that function and its `expected_remaining_accounts=` log before adding or removing an account. A mismatch is a harness error, not a protocol finding.
- zero_copy account sizes: take them from the program's own consts (Kamino `utils/consts.rs`: ORACLE_MAPPING_SIZE 29696, ORACLE_PRICES_SIZE 28704, ORACLE_TWAPS_SIZE 344128, TOKEN_METADATA_SIZE 86016) and add 8-byte discriminator. PDA seeds from `utils/pdas.rs` (CONFIG = b"conf").
- Field offsets for reading state back: derive from the struct definitions (repr(C) alignment — u128 aligns to 16). Kamino EmaTwap: slot@0, ts@8, ema_1h u128@16, tracker_1h@32; DatedPrice: value@0, exp@8, slot@16, ts@24 (56 B).

## Build/run logistics (WSL, 6 GB RAM cap)
- Script files only (`wsl.exe -d Ubuntu-24.04 -- bash /mnt/e/WSL/run-poc.sh`); `. "$HOME/.cargo/env"`; `CARGO_TARGET_DIR=/root/.cache/poc-target` (native ext4); `CARGO_BUILD_JOBS=4`.
- First build compiles solana-program-test deps (minutes); afterwards incremental crate rebuild ≈ 8 s — iterate freely.
- Capture full output to a log file; grep the step table + VERDICT lines. Anchor custom errors = 6000 + enum variant index (count variants in errors.rs to name the code, e.g. 6023 = TwapNotEnoughSamplesInPeriod).

## Coordination pitfall
Parallel agent sessions may edit the same harness. The patch tool warns when a sibling modified the file after your last read — RE-READ before patching, apply only what's still broken, and never start a competing cargo build on the same target dir while one is running (cargo lock serializes, but runs race). Verify the final result by running the binary yourself and reading the log, regardless of who wrote the last edit.
