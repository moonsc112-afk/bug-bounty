---
name: bugcrowd-reporting
description: "Use on a Bugcrowd submission: VRT and severity ask."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Bugcrowd, VRT, Reporting, Severity, Triage]
    related_skills: [report-writing, triage-validation, finding-validation-gate, evidence-hygiene]
---

# Bugcrowd reporting

Overlay for `report-writing` when the destination is Bugcrowd. `report-writing` owns the body, the impact paragraph and the tone. This file owns the Bugcrowd-specific layer: VRT category selection, the severity-request paragraph, out-of-scope rebuttals, and the attachment shape Bugcrowd triagers expect.

Order: validate with `finding-validation-gate`, write with `report-writing`, redact with `evidence-hygiene`, then apply this file.

## When to Use

- The destination platform is Bugcrowd, and you are about to pick a VRT category, write a severity request, or answer an out-of-scope objection.
- A Bugcrowd triager re-mapped the severity downward and you are deciding whether to contest.
- Not for HackerOne, Intigriti, Immunefi or Mantis: those use their own severity scales and `report-writing` alone.

## Why a separate layer exists

Bugcrowd scores on the Vulnerability Rating Taxonomy (VRT), a public P1 to P5 taxonomy. The researcher does not set severity through a field: the VRT selection plus the severity request in the description decide it. A correct finding with the wrong VRT category is downgraded before anyone reads the impact. So the VRT row comes first and the request argues upward from it with evidence, never with adjectives.

VRT churns. The live taxonomy gained AI Application Security and DeFi Security branches, so confirm the row exists in the selector during submission instead of trusting any table copy, including the one below.

## Submission shape

1. **Title**: `[VRT category] <component> <defect> leads to <impact>`, no clickbait.
2. **VRT category**: the most specific matching row, at the lowest severity that still fits the demonstrated impact.
3. **Severity request**: first paragraph of the description, before the technical body.
4. **Body**: the `report-writing` template, unmodified.
5. **Attachments**: sanitized per `evidence-hygiene`. Redacted HAR, labelled screenshots, `sha256sum` manifest when there is a bundle.

## Severity request paragraph (template)

```
Severity request: <P#>, VRT "<category> > <name>" (default <P#>).
The default assumes <default assumption>. This report shows <measured fact>
instead: <one sentence with the number, account pair, or transaction hash>.
Impact is <asset amount or account class>, reproduced <N> times from a clean
account, and step <X> is in the attached log at <line or timestamp>.
Rated on that evidence the finding sits at <P#>, not <default>.
```

Rules: one request, one paragraph, no hedging words. If the default P already matches the demonstrated impact, still state the VRT row and skip the escalation sentence. Never request P1 on a Critical+1 basis; request P1 only for full compromise, cross-tenant fund or PII exposure, or node-level DoS, which is what the VRT reserves P1 for.

## VRT quick map for the classes this operator actually files

| Finding | VRT row | Default | What earns the escalation |
|---|---|---|---|
| Reentrancy draining a pool | Decentralized App Misconfiguration > DeFi Security > Function-Level Accounting Error | Varies | Quote the loss amount and the caller path; `Varies` rows are decided on evidence |
| Flash-loan price manipulation | ... > DeFi Security > Flash Loan Attack | Varies | Price source and the manipulated window |
| Broken access control, fund move | Decentralized App > Marketplace Security > Unauthorized Asset Transfer | P1 | Already P1, keep evidence tight |
| Signature replay | Smart Contract Misconfiguration > Improper Use of Modifier | P4 | Escalate with the cross-account replay only |
| Decimal or rounding loss | Smart Contract Misconfiguration > Improper Decimals Implementation | P4 | Quantify per-call loss times call frequency |
| Integer wrap on a balance | Smart Contract Misconfiguration > Integer Overflow / Underflow | P2 | Show the wrap is reachable, not theoretical |
| SSRF reaching internal metadata | Server Security Misconfiguration > SSRF > Internal Secrets Exposure | P2 | Show the secret class returned |
| OAuth redirect to ATO | Server Security Misconfiguration > OAuth Misconfiguration > Account Takeover | P2 | Prove token capture, not just redirect |
| Stored XSS, non-privileged to anyone | Cross-Site Scripting (XSS) > Stored > Non-Privileged User to Anyone | P2 | Shows session or action impact |
| Race on a one-use coupon | Server Security Misconfiguration > Race Condition | Varies | Two 200s for one code plus final balance |
| Missing cookie flags | Server Security Misconfiguration > Missing Secure or HTTPOnly Cookie Flag > Session Token | P4 | Only with a concrete XSS in the same account |
| Exposed stack trace | Sensitive Data Exposure > Visible Detailed Error/Debug Page > Descriptive Stack Trace | P5 | Only if the trace names internal infra |

## Out-of-scope rebuttal catalog

Triagers raise the same five objections. Counter each with a fact, once, then stop arguing.

| Objection | Counter that works |
|---|---|
| "Known issue / duplicate" | Public report or commit that fixes it; if the fix postdates the target, say so with the date |
| "Best practice only" | The concrete consequence: who loses what, measured |
| "No PoC / theoretical" | The request and response lines, the tx hash, or the failing assertion |
| "Requires user interaction" | Count the interactions and name the victim class; interaction is not an automatic downgrade in the web2 VRT |
| "Third-party component" | The program's own wrapper that misuses the component, with `file:line` |
| "Works as intended" | The program's documented invariant that the code violates |
| "Informational" | Only contest if a fund or account boundary is crossed; otherwise accept |

## Test-account discipline

A Bugcrowd program that offers a research alias (a Bugcrowdninja-style `@bugcrowdninja.com` mailbox) expects findings made from it. Use that alias for the test account, keep the password in the operator's vault, and label the account in every screenshot. Without an alias, prefix the account email `bc+<date>-<case>` so dedup is obvious.

Never submit from an account created before the engagement with real data, and never mix two findings in one test account.

## Attachments

- Screenshot of the raw request and response with the cookie bar cropped per `evidence-hygiene`.
- HAR only when headers carry the proof; sanitize `Cookie`, `Set-Cookie`, `Authorization`.
- Code targets: the PoC test file, plus the verbatim command and its output in a log.
- Name files `01-<case>-<surface>-request.png` style so the triager can order them.

## Pitfalls

- Do not escalate a `Varies` row without a number. Varies means the reporter supplies the severity, so an empty argument defaults to the bottom.
- Do not attach a HAR that still carries a live session cookie; the target rotates and the triager cannot reproduce against a dead cookie.
- Do not copy the VRT tree by hand into a report title; link or name the exact row, including the parent category.
- A P5 that duplicates an existing P5 costs the same triage time as a P2 and earns nothing. Check the program's known-issues list before filing P4/P5.
- Bugcrowd allows the triager to re-map the VRT downward after the fact. Keep the request paragraph factual so a re-map still reads as coherent.
- Reward tables differ per program and per currency; read the live brief before promising a number in the report.
