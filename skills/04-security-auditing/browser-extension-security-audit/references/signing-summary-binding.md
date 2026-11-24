# Signing summary to payload binding

Use this recipe for each signing family in a wallet extension. The question is
always the same: can the summary the user approves diverge from the payload that
is signed or broadcast?

## Locate the four anchors

1. Summary generator: grep for `create<Chain>SigningSummary` or equivalent.
   Record the object it reads. A generator that reads the prepared transaction or
   prepared PSBT is the good shape; one that reads a separate UI model is a lead.
2. Binding assertion: grep for `assert<Chain>SigningSummaryMatchesPrepared`,
   `summary does not match`, or the chain preparer's equivalence check.
3. Approval call site: the UI request that carries both the summary and the
   payload fingerprint, and the `validate` callback that runs immediately before
   signing.
4. Confirmation path: what is actually signed and broadcast after approval.

## Compare the field lists

Write down every security-relevant field of the prepared payload (recipient,
amount, asset, nonce, chain, gas caps, calldata, calldata hash, method selector,
access list, destination domain, recipient bytes). Tick each one that appears in
the binding assertion. A field missing from the assertion is a lead: check the
parser's exact-key enforcement, the signed-transaction integrity check, and any
constant enforced at construction before treating it as a gap.

## Prove a divergence, do not assert one

- Run the repo's own test file for the summary builder and binding assertion.
- Mutation-test it: change one summary field in a copy of the fixture and confirm
  the assertion throws. A green suite whose mutations are never rejected proves
  nothing about the binding.
- If a candidate gap survives, build a runnable local test that shows a prepared
payload P and an approved summary S with a meaningful difference, then show that
  S is accepted and P (or a different payload) is signed. Without both halves,
  the result is an observation, not a finding.

## Hardware path

The hardware flow usually carries a payload fingerprint and a request digest in
persisted state. Verify that the pre-signing callback re-reads the request and
rejects when derivation path, account, chain, fingerprint, or expiry changed.
A summary schema check alone does not bind the displayed values to the Ledger
request.

## Persisted state

Pending-transfer stores reparse a saved summary on recovery. The expectation
must come from the prepared command or payload fingerprint in storage, not from
the summary's own fields; otherwise a tampered stored summary can validate itself.
