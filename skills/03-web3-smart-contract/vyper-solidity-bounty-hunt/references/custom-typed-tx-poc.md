# Custom EIP-2718 typed transactions for PoC

Use when the target defines its own transaction type (for example a 0x79 Base Transaction) and `cast send` / ethers cannot construct it. The goal is a raw signed bytestring accepted by `eth_sendRawTransaction`.

## Procedure

1. Read the consensus crate's canonical field encoder (search for `rlp_encode_fields`) and copy the field ORDER exactly. JSON or ABI names are not the wire order. Also read the auth tail: usually `rlp_list(fields + [sender_auth, payer_auth])` prefixed by the type byte.
2. Read the signature domain prefixes and the signature preimage. Auth blobs are normally excluded. A named sender/payer hash substitutes the resolved address into the sender slot rather than using the nullable wire slot.
3. Build RLP in Python with stdlib only: minimal big-endian integers, `0x80` for empty bytes, `0xc0` for an empty list, long-form length headers past 55 bytes.
4. Hash the domain-prefixed RLP list with `cast keccak 0x<domain><hex>`.
5. Sign with `cast wallet sign --no-hash --private-key <key> 0x<hash>`. `--no-hash` is mandatory: the default prefixes the EIP-191 message header, so recovery yields a different address and the failure surfaces misleadingly as an unfunded sender (for example `insufficient funds ... have 0`).
6. Assemble `bytes([type]) + rlp_list(fields + [sender_auth, payer_auth])` and submit via JSON-RPC `eth_sendRawTransaction`.
7. Verify with `cast receipt <hash> --json`: check `type`, `status`, and any protocol-specific fields (payer, committed phases, billed gas). A receipt type that matches the target type proves the node decoded and executed the custom envelope, not merely that the bytes were relayed.

## Adversarial variants

- Change only a fee field to get a different tx hash while keeping the replay identifier constant; the second submission must be rejected as a replay. This isolates replay protection from simple duplicate-hash rejection.
- A signature `v` byte must be 27 or 28; other values are rejected by strict parsers even when the curve math is valid.
- Named authentication is `K1_AUTHENTICATOR || r || s || v` and must recover exactly to the named account; the equality check is the auth boundary worth testing.
- Validity bounds committed as raw values may normalize to the same millisecond time while producing different replay identifiers. Treat that as intended unless the target's spec says otherwise; it is not automatically a finding.

Never use funded mainnet keys for these probes; burner test keys only.
