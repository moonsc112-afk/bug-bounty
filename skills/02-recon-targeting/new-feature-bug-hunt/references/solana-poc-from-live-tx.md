# Solana PoC from a live transaction

Use when a deployed program has no source or its SDK is stale, and the PoC must run against the deployed ELF with real account state.

## Procedure

1. Obtain the real transaction first, not a cached meta dump. Enumerate recent signatures for the program, fetch candidates with JSON encoding, decode instruction data as base58, and keep a successful tx whose first eight bytes equal `sha256("global:<snake_case>")[:8]`. Confirm its account count matches the SDK IDL's flattened account list.
2. Dump every instruction account with `getAccountInfo` using base64 encoding. Save raw bytes and the owner pubkey; the owner string is needed to reconstruct `Account` metadata.
3. In `ProgramTest`, register every program key with `add_program`. Never add a program key with `add_account(executable=false)` — that produces `InvalidProgramId` on `Program<'info, T>` even when the key is correct.
4. If the live signer is unavailable, replace its pubkey bytes inside the dumped account data with your generated payer's pubkey and substitute the signer. Anchor `has_one` constraints read the stored pubkey, so patching only the signer list fails.
5. Give non-critical program accounts a valid executable placeholder by adding an existing `.so` via `add_program` under that key. A read-only memo program should not block the constraint chain.
6. Set the `Clock` to a time that clears cooldown gates, then define every field under test relative to that clock. A stale field timestamp must be stale relative to the clock you set, not to the original block time.
7. Calibrate numeric instruction arguments against the pool/oracle state in the fixture. An argument copied from the live tx can be far outside tolerance once the fixture state drifts, returning an unrelated price error that looks like the field under test.
8. Treat each distinct Anchor constraint error as a harness checkpoint. Keep adjusting wiring until the transaction reaches the assertion you actually want to test; only then interpret pass or fail.

## Pitfalls

- Do not trust a cached instruction dump whose discriminator or account count differs from the SDK IDL. It is a different instruction; its constraint failures are harness debt and will manufacture a false verdict.
- Do not classify an unpopulated protective field as a bypass from population counts alone. First run an A/B with fresh, stale, and future values and record the exact error codes.
