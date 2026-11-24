# Auditing TEE attestation verifiers

Use with `evm-bounty-source-audit` when the target validates enclave attestations, especially AWS Nitro with COSE/CBOR, X.509 chains and off-chain inverse hints.

## Order of work

1. Map the four layers separately: parser (CBOR/ASN.1), certificate cache and revocation, signature verification with hints, and the consuming contract's policy. A clean verifier says nothing about a caller that ignores the fields the verifier returns.
2. Compare the audit PDF's pinned commit with the current commit before calling a surface fresh. A changelog `[Unreleased]` section is usually audit fixes; enumerate the post-audit commits and map each change back to a finding instead of treating every changelog line as new unaudited code.
3. Read the caller before hunting the verifier. The verifier often documents that image and freshness policy belong to the caller. If the caller binds only one measurement, verify that against the program's reward definition rather than assuming a broader policy.
4. Record a negative with the exact invariants tested. Most TEE verifier surfaces are hardened and yield no payable finding.

## Fuzz harness pattern

Inherit the repo's existing test contract instead of rebuilding fixtures. This reuses certificate caches, synthetic TBS builders and hint collectors.

- Add a sanity test that the valid fixture actually verifies. Without it, every malformed-input test can pass simply because the harness is broken.
- For malformed input, set a `bool accepted` inside `try` and assert it afterwards. Never call `fail()` inside a `try` block: the catch swallows the failure and the test passes.
- Use `vm.expectRevert("<exact reason>")` when the reason is contractual, and make the test non-`view` because cheatcode state changes.
- Mutate one byte of a valid indefinite CBOR TBS and assert parsed PCR slots stay null or 48 bytes. Fuzz arbitrary unprotected COSE headers and assert a successful decode leaves the payload and signature at the minimal fixed offsets.
- Grep the log for each `testFuzz_` line. A harness that extends a test contract reruns inherited tests, so the suite total can look healthy while the new fuzz case never ran.

## Hint soundness invariants

Off-chain inverse hints are safe only if every value is rechecked before use.

- Every hint must satisfy `b * inv = 1 mod m` for the modulus actually used at that consumption point.
- `verifyWithHints` must require consumed bytes to equal supplied bytes; extra or truncated hints revert.
- A non-canonical inverse `inv + k*m` is acceptable only if reduction yields the same result. Test this explicitly at the modular-arithmetic layer.
- Reject a hint computed for the scalar modulus where the field modulus is expected.
- Mutating a hint, swapping two hint chunks, or appending trailing bytes must not accept a corrupted signature or TBS.

## PCR and journal integration

- A fixed 32-slot PCR bank using a CBOR null sentinel cannot collide with a real byte string if the byte-string parser always emits type `0x40` and a start index of at least one. Verify this from `elementAt` rather than assuming it.
- Registration may be intentionally measurement-agnostic. Check whether the consumer stores `keccak(PCR0)` and compares it with an immutable image hash at proof time; PCR1 and PCR2 may never be checked.
- Verify a debug-mode constant by hashing the all-zero measurement directly, for example `cast keccak <48 zero bytes as raw hex, no 0x prefix>`. Do not trust the hex constant from a comment.
- A proof journal binds state only if it includes the proposer, L1 origin, starting and ending roots and sequence numbers, intermediate roots, config hash, image hash and schedule id. The dispute-game address may be absent: identical journal fields describe the same logical claim.
- Domain separation across deployments may rely entirely on `CONFIG_HASH`. When the generator is absent from the audited repos, state that it is an unverified deployment assumption rather than a finding.

## Cross-layer traps

- A low-S check against `n-1` is not a low-S policy; it permits both signature twins. Check the actual constant before repeating a NatSpec claim about malleability.
- An untagged COSE wrapper byte that is ignored produces encoding malleability but does not change the signed payload. Classify it as informational at most.
- Truncated indefinite CBOR containers may loop until out-of-gas instead of reverting with a named error. If the function still reverts and no state changes, treat it as a gas-griefing property, not a false accept.
- Absence of off-chain enclave source in the audited repos means journal-format agreement cannot be proven. Say so plainly.
