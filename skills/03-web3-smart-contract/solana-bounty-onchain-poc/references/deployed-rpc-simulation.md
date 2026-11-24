# Deployed-bytecode semantic probes through RPC simulation

Use when a Solana program has no public source or its SDK lags the deployed build, and the question
is narrow: what does a scalar argument do, which guard rejects it, does a cap gate fire. This
exercises the REAL deployed bytecode against CURRENT accounts without a validator or a compile.

## Procedure

1. Find a current mined instruction: `getSignaturesForAddress(programId, {limit:100..200})`, skip
   errored signatures, `getTransaction(sig, {encoding:"json"})`. Resolve the instruction's program
   via `accountKeys[ix.programIdIndex]`; filtering on a literal program id without that resolution
   matches nothing. Decode `ix.data` from base58 (leading `1` characters are zero bytes and must be
   restored) and compare its first 8 bytes to `sha256("global:<snake_case_name>")[:8]`.
2. Fetch the SAME signature with `encoding:"base64"`, `maxSupportedTransactionVersion:0`, and find
   those 8 discriminator bytes in the raw transaction. The bytes following them are the argument.
   Infer its width from the payload length instead of trusting an SDK codec.
3. Patch only the argument bytes in a copy of the raw transaction, then call:
   `simulateTransaction(base64(raw), {encoding:"base64", sigVerify:false, replaceRecentBlockhash:true})`.
   For state reads add `accounts:{addresses:[<state account>], encoding:"base64"}`, but VERIFY that
   the returned bytes actually moved before calling them post-state: with some RPC builds the
   requested accounts came back unchanged even though the logs showed two successful executions.
   Calibrate on a field the single-call control must change, and otherwise take the before/after
   value from ProgramTest. Simulation ignores signature validity, so the original signer and
   blockhash need no re-signing.
4. Parse `value.err` and the `Program log: Error Code: <Name>. Error Number: <n>` line. Program
   `msg!` lines often print the very values the guard compared (prices, caps, timestamps, balances);
   quote those instead of recomputing them. Sweep zero, the original value, original +/- 1, and a few
   extreme values, keeping the original as the success control.
5. Persist every sweep row (arg, err, error name, printed logs, post-state fields) to JSON next to
   the probe script. A negative result is a result only if the control row succeeded.

## Pitfalls

- Compare DECODED discriminator bytes. The base58 string of a 12/16-byte payload does not start
  with the base58 string of the first 8 bytes, so prefix matching on the encoded text misses real
  instructions and produces a false "no recent usage" conclusion.
- Do not hand-serialize the transaction from its JSON account list. A single base58 pubkey decoded
  one byte short (a leading `1` case) shifts every later field and the RPC rejects the transaction
  with a nonsensical "Attempting to read N bytes". Patching a mined raw tx preserves the exact
  header, signer flags and account indices.
- The name can be dispatched while the SDK's argument shape is stale: a recognized name plus
  `InstructionDidNotDeserialize (102)` in ProgramTest is an ABI gap. Re-derive the shape from the
  mined tx; do not conclude the instruction is unavailable.
- A previously successful tx often fails when replayed later: cooldowns, price-divergence guards,
  caps and balances are live state. Report the guard that fired; that is information about the
  deployed build, not a broken probe.
- The state account in an old transaction may have been closed, so no post-state diff is possible.
  Re-select a currently live account before claiming a before/after measurement.
- Do not search the ELF for the 8 discriminator bytes to prove a dispatch exists. eBPF splits
  64-bit immediates into two 32-bit halves, so the contiguous constant is absent even for handlers
  the program dispatches. Use execution (or the log literals) instead.
- A narrow sweep that only reverts on caller-extreme arguments proves the guards HOLD. Say so
  plainly and keep the verified findings separate; do not promote a negative probe into a claim.

## Multi-instruction splices (repeat the same call inside one transaction)

Use this when a single-call argument sweep cannot reach the state transition of interest, e.g. a
rate accumulator that only changes across several withdrawals. Build it from the mined raw tx,
never from a hand-serialized message.

1. Parse the raw v0 transaction in WIRE ORDER: byte 0 = signature count, then 64 bytes per
   signature, then `0x80` version byte, then the 3-byte header, then `account_keys`, then the 32-byte
   recent blockhash (it comes AFTER the keys), then the instruction vector, then the address-table
   lookups. A versioned tx whose loaded keys are referenced by index > static-key count is normal;
   keep the lookup tail byte-identical when splicing.
2. To duplicate an instruction, copy its complete byte run: `program_id_index (1)`, `account count
   (1)`, account indices (N), `data length (1)`, data bytes. The scalar argument inside an Anchor
   payload with M account metas starts at `ix_start + 1 + 1 + M + 1 + 8` for a u64. An off-by-four
   here writes past the data length and corrupts the following instruction, which surfaces as a
   generic deserialize failure, not a field error.
3. Increment the instruction count byte in place, insert the copies before the address-table tail,
   and raise the existing compute-budget limit (tag `0x02` + u32, patched to 1,400,000) because
   several program invocations in one tx blow the original budget and show up as
   `ProgramFailedToComplete` on the SECOND copy.
4. Rank candidate state accounts by the ratio of the guard threshold to the balance the caller can
   actually move (e.g. withdrawal cap divided by shares outstanding), then test that a mined tx for
   that account still REPLAYS before investing in the splice. A tiny-ratio account whose tx now
   reverts for unrelated state cannot be used, while the only replayable account may have its cap
   far above the available balance.
5. Keep the original single-call transaction as the success control. If the second copy reverts on
   a downstream balance or transfer constraint after you removed the trailing instructions, that is
   an incomplete splice, NOT a cap bypass. Duplicating an instruction that closes an ATA also needs
   the ATA-create instructions repeated before each copy; without them the second call fails at an
   `AccountNotInitialized` constraint, and with them several invocations can exhaust the 1.4M CU
   ceiling as `ProgramFailedToComplete`. Count the `Instruction: <Name>` log lines to confirm that
   every appended copy really executed; a corrupt splice can return `err: None` with only the
   original call in the log. Say that the variant is inconclusive and name what would be needed
   rather than reporting a negative as a finding.

## Cap-gate probes: denomination and candidate cost

- Before reading "cumulative requested amount > cap" as a bypass, identify the cap's DENOMINATION
  from the program's own printed values. A handler may print a cap capacity and running total in
  TOKEN units while the caller sweeps SHARE counts; a strategy with almost no token A available
  keeps that cap total near zero after any number of share withdrawals. Quote both printed numbers
  and call it cap semantics, not a bypass.
- Rank candidate accounts by threshold ratio AND instruction cost together. A live account whose
  withdraw path invokes no CLMM/AMM disinvest CPI avoids the large per-call CU cost and lets several
  copies fit the 1.4M transaction budget; a perfect ratio on an account whose path needs that CPI
  fails on compute and answers nothing.
- Read the target accumulator before and after the SUCCESSFUL control row. A gate that never fires
  while the accumulator still moves by the expected delta is a held gate, and belongs in the report
  as a negative result with the two numbers, not as an omitted row.
