# Cross-field relationship validation in contract audits

A class of business-logic bug where every identifier is individually valid but
the combination is wrong. The UI keeps the pair consistent; the contract does
not. Use this when a writeup or a lead describes "a balance check that read
the wrong account" or "a valid ID pointed at the wrong resource".

## Procedure

1. List every caller-supplied identifier in the handler: token, account,
   product, source and destination account, stem, field id, input and output
   token, custodian, amount, chain id.
2. Write down the pairs that MUST agree for the call to be meaningful. Examples:
   order book vs source asset, unripe token vs custodian vs backing amount,
   token vs stem in a deposit key, input vs output token in a convert, field id
   vs field count, signature domain vs chain id.
3. For each pair, find the exact line where the binding is enforced. A binding
   that lives only in the frontend is not a control.
4. Check whether the token or counterparty is implicit from storage rather than
   caller-supplied. If it is implicit, the attacker cannot desynchronise the
   pair through this handler; record that as a verified negative with the line
   reference, not as a finding.
5. Check reconfiguration paths that could break a previously valid pair.
   Setters that rewrite the underlying token or the counterparty after backing
   is established are worth tracing, but they usually fail as findings when
   they are owner-only and the program excludes privileged assumptions.
6. Where value is recomputed after an external step, verify it is recomputed
   from the asset actually received, not from the asset the caller named.
   Reading the full balance of a shared pipeline or escrow address is a
   separate residual QA item, not automatic fund loss.

## Verdict framing

- State the pairs examined and the line that binds each one. A table with
  `pair / location / result` is enough.
- An honest negative is a valid result. Do not manufacture a finding to show
  progress; say which pair is bound and how.
- Keep residual QA notes (griefing, shared-address leftovers, owner-only
  reconfiguration) in a separate section explicitly labelled as not payable.
- Do not run a PoC when no candidate survives the pair analysis. Say that no
  PoC was run because there was no candidate.
