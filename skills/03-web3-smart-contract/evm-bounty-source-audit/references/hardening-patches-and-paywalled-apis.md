# Hardening patches + paywalled API (x402) recon — lessons

## Proposing hardening fixes (when the submission should carry a patch)
- Before writing a fix, grep the project's own tests for regression guards of PAST fixes (comments/names like "v2 let anyone settle with an older decision", `test_onlyTheLatest...`). The intended hardening must survive your patch; a fix that silently reverts their earlier fix gets rejected on sight.
- Prove the patch is additive, not a semantics change: run the repo's FULL suite on the patched tree. Expect exactly your own pre-fix repro tests to fail (they encode the vulnerable behaviour); any other failure means you altered intended behaviour — redesign, don't rationalize.
- Deliver patches as `git diff` against the tag that matches the DEPLOYED bytecode, and verify with `git apply --check` on a pristine clone (native git needs `E:/...` paths, not `/e/...`).
- If the contract cannot observe the needed history on-chain (e.g. a log keeps only the latest entry per key), do not invent state that pretends it can: add a permissionless pin/latch plus a guard, and state the residual limitation honestly in the write-up.
- Prefer a write_file to a NEW test filename over overwriting an existing test file when a stale-content guard blocks the write; remove the old file afterwards so duplicate contract names don't break compilation.

## Paywalled API endpoints (x402-style) — read-only recon order
- Docs first (llms.txt, sitemap.xml), then decode the `PAYMENT-REQUIRED` header (base64 JSON) and cross-check payTo/asset/network against the project's own network.json and deployments.
- Sweep the product's remaining docs pages once the main paid endpoint is mapped (the docs index /
  llms.txt names them): products often answer an OpenAI-compatible variant (`GET /v1/models`,
  `POST /v1/chat/completions`, one price per request) and run a testnet host that shares the code
  paths and validation order. Partner/escrow integrations (being a provider on a third-party job
  protocol) escrow in contracts outside the repo — bound them out of scope, don't audit them.
- Test pre-payment validation field by field: validators check sizes and message lists yet skip
  other fields (a `model` id); a skipped field still returns the payment challenge, so its
  post-payment behaviour is a paid-test candidate, not a confirmed bug.
- On Windows, a large probe body passed inline to `curl --data` through subprocess dies on the
  command-line length limit (WinError 206 "filename or extension is too long"): write the JSON to
  a scratch file and pass `--data-binary @file`.
- Validation order is free to test: an invalid body must 400 BEFORE payment, a valid body with no/bad payment must 402 with a reason code; out-of-window/unknown status ids must 404 cleanly.
- For the exact wire schema `npm pack` the official client (@x402/core, @x402/evm) and read it: v2 payloads must echo the chosen `accepted` requirement, EIP-3009 fields are `{authorization, signature}`. A crafted random-signature payload must be rejected with a signature reason code (e.g. invalid_exact_evm_payload_signature) — nothing can settle without a valid signature, so this is safe.
- Content-addressed record endpoints: filename = keccak(content); docs may define \"served without its work → hash checks skip\" — verify with the project's own verifier (e.g. `npx brainchain-verify mainnet <id>`) instead of guessing.
- Replay / underpayment-with-valid-signature / sandbox-escape (user-supplied `checks` code) need ONE real payment ($0.25-class): these are the only payout-grade tests left when the contracts are clean — ask the operator before spending.
- Before spending on paid tests, confirm the backend can actually deliver: a desk may SETTLE the payment on-chain (tokens pulled) then return Cloudflare 502/524 with no service and no refund because its grading worker is down. That blocks replay/sandbox/model tests. Distinguish environment outage (502/524 infra errors, no-payment paths healthy) from a code bug; "settle-before-work with no refund on worker failure" is itself a reportable funds-safety hardening note, but a testnet-only outage is usually credit-tier, not payable — mainnet impact needs mainnet confirmation (real money, operator consent).
- Match the `accepted` requirement to the ENDPOINT: grades and chat/completions offer different `amount`s; echoing the grades accept on a chat request yields "No matching payment requirements" (a harness bug, not a target bug). When a testnet host exists, run them there first:
  faucet test tokens make all of these free (its desk accepts test-USDC / test-UDG); only a
  confirmed finding needs a mainnet re-run.

## Funding a payer for paid (x402) tests
- EIP-3009 `transferWithAuthorization` payments are gasless for the payer — the facilitator submits and pays gas (verified: testnet payments settled with the payer holding 0 ETH). Fund the payer with the payment TOKEN only. The Permit2 accept option needs a one-time on-chain approval that DOES cost gas — prefer the EIP-3009 option to keep funding gasless.
- Generate a throwaway payer key to a file (viem `generatePrivateKey` + `privateKeyToAccount`); print only the address, never the key, and never take a key through chat. Funding the address (faucet for testnet, real token for mainnet) is the operator's account-side step.
- A wallet UI can reject a freshly generated external address as "invalid" / not detected even though it is valid (observed with OKX Web3). Before assuming the address is wrong, cross-verify independently: viem `isAddress`/`getAddress`, a manual keccak EIP-55 checksum, and `cast to-check-sum-address`. EVM addresses are chain-agnostic — there is no separate "mainnet address"; the rejection is the wallet's network context or fresh-address detection, not the address.
- Because of that friction, funding a brand-new external payer through the operator's wallet can stall (and an outbound transfer also needs gas the wallet may lack). Since EIP-3009 is gasless, paying directly from an account that already holds the token avoids any transfer: for a low-value/fresh account the operator can export its key to the payer file and the script pays from it. Never export the key of a wallet holding the operator's real funds; if only such a wallet is available, treat the paid mainnet test as blocked and fall back to the free testnet route or submit the findings already in hand.

## Running paid tests against a live desk
- A paid endpoint can enter a maintenance window: HTTP 503 with an "updating, nothing was charged" body and a `Retry-After` header (seconds). It charges nothing — confirm the payer balance is unchanged. This is distinct from the 502/524 settle-then-fail case above, which DOES pull tokens.
- Don't burn turns sleeping through a long maintenance window, and never submit the payment twice: arm a background loop that polls the cheap challenge request (valid body, no payment header) every ~60s and fires the paid probe EXACTLY ONCE when the normal challenge code (402) returns, then exits. Write probe results to files so the evidence survives even if you stop watching; analyse them on the next ping.
- Guard the probe script against a missing `PAYMENT-REQUIRED` header (maintenance returns none): print the status/body and exit cleanly instead of crashing on `Buffer.from(null)`. Handle an async 202 by polling the returned status URL until the grade settles, then capture the `checks` output.
