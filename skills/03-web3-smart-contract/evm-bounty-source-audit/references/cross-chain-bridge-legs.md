# Cross-chain bridge / intents legs — audit checklist

Use when the target is a bridge, omnichain token, or intents/settlement protocol with
one leg per chain. Legs are usually written by different hands in different languages,
so the bugs live in the DIFFERENCES between legs, not in any one leg.

## The invariant set every money path must satisfy

Check each leg's inbound (finalize/mint/release) and outbound (init/lock/burn) path
against all of these; a leg that satisfies four of five is where the bug is:

1. **The signed payload binds the destination chain id.** If the hash omits it, a
   signature minted for chain A replays on chain B. Some legs encode the chain id twice
   (once for the token's chain, once for the recipient's) — both must be the local id.
2. **The signed payload binds the accounts actually used**, not just payload fields.
   The strongest pattern passes the on-chain account keys as serialization parameters
   (Solana: `serialize_for_near((mint.key(), recipient.key()))`), so substituting an
   account invalidates the signature. A leg that signs only struct fields is weaker.
3. **Replay is guarded by an atomic nonce marker**, checked-and-set before any value
   moves. Marking the nonce before verifying the signature is safe ONLY because a
   failed verification reverts the whole transaction — confirm that, do not assume it.
4. **Privileged bypass paths are role-gated.** A "finalize without proof" recovery
   entry point is legitimate if it is DAO/admin-only AND reuses the same callback as
   the proven path. Check the role macro, not the function name.
5. **Amount width conversions are checked.** u128 payload → u64 chain amount must
   assert/cast-checked, and a SafeCast that reverts is what keeps the moved amount and
   the committed amount identical.

Signature verification: prefer legs that reject high-`s` (malleability). Where a leg
omits it, that is NOT a finding if the nonce — not the signature hash — is the replay
guard; say so explicitly instead of reporting it.

## Per-leg encoding gotchas (these are correct, not bugs)

- **Starknet/Cairo**: the keccak digest must be byte-reversed before `verify_eth_signature`
  (felt endianness), and a nonce bitmap uses **251 bits per word** (`nonce / 251`,
  `pow2(nonce % 251)`) because a felt is 251 bits. A deploy salt truncated to the hash's
  low 128 bits is fine: a collision needs ~2^64 work and differing constructor calldata
  still yields a different address.
- **Aptos/Move**: FA amounts are u64, so amounts are capped and decimals clamped (to 8);
  the event carries both normalized and origin decimals so the counterparty can rescale.
  Bitmap width 128 matches the u128 word. Bridge-token status may have a single source of
  truth (a ref on the object) rather than a reverse mapping — do not report the missing table.
- **Solana/Anchor**: `Option<vault>` selects the model — vault present = lock/release of a
  real token, vault absent = mint/burn of a bridged token whose `mint_authority` is the
  bridge PDA. A fake mint can set the bridge as authority; that is acknowledged and
  harmless because the counterparty chain ignores unregistered tokens.
- **EVM**: payout branch order (native → ERC1155 via a derived-address mapping → custom
  minter → bridge mint → plain ERC20) is keyed on distinct mappings. A permissionless
  first-writer-wins metadata registration is safe when the key is a hash preimage of
  (token, tokenId) — an existing mapping cannot be hijacked.
- **NEAR/Rust**: `signer_account_id == predecessor_account_id` is the guard that stops a
  vote/governance call being forwarded through another contract the participant signs for.
  `#[private]` restricts to self-calls; `#[init]` cannot be re-invoked to flip a config flag.

## Two-step commit/submit (system-transaction legs)

On chains where a system/core callback's logs are absent from the block's logsBloom,
guardians never attest a message published inline. The leg therefore splits into
`preInitTransfer` (commit a hash, callable only by the token) and a permissionless
`triggerPendingInitTransfer` (match the commitment exactly, delete it, then burn/submit).
Audit points: the commitment must use `abi.encode` not `encodePacked` (adjacent dynamic
strings collide), the fee/pause checks may legitimately live in step two, and a
`fee >= amount` commitment strands only the initiator's own tokens.

## Light-client / SPV legs

A deprecated inclusion-proof API that does not bind the coinbase proof lets an attacker
present an INTERNAL merkle node as a transaction id. Before reporting it, grep the
consumer for which version it actually calls — bridges usually call the v2/`with_heights`
variant that requires equal proof lengths (which pins leaf depth) and enforces
confirmations. A vulnerable-but-uncalled public method is a third-party integrator
footgun, not an in-scope loss-of-funds path.

## Accounting state that looks like a bug

`locked_tokens`-style counters legitimately behave differently per token class:
bound token → counted; deployed token (address mapped, no counter entry) → skipped,
because it uses mint/burn; not-yet-bound → counted from zero so pre-registration
transfers are not lost. Verify all three states before calling an undercount.

## Settlement / intents engines

The core property is global token conservation: per-account deltas are applied, then a
finalize step matches deposits against withdrawals per token and fails the WHOLE
execution on any unmatched remainder. Read the matcher (usually a greedy two-pointer
over sorted lists) and confirm per-account totals are preserved and each
(sender, receiver, token) pair is emitted once — that is what justifies an
`unreachable!()` on overflow. Also confirm the per-intent gate chain: signature →
domain/verifying-contract → deadline → signer holds the recovered key → nonce verified
AND committed.
