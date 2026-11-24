# <Program>: <root cause in one line> — <observable consequence>

<!-- Copy this skeleton per finding. Delete comments before filing. -->

## Severity

**High** | **Critical** | **Medium** — one line, plus WHY (proven on the deployed
bytecode? impact conditional on config/liquidity?). State the escalation condition
if the severity is bounded by a live limit.

## Relevant links

- Repo: <url> @ `<commit>` (release/tag)
- Deployed program: `<program id>` (programdata `<addr>`, deploy slot `<n>`, upgrade authority `<addr>`)
- Code: `<path/to/file.rs>` — `<function>` (lines `<a-b>`), consumed by `<caller>` (lines `<c-d>`)

## Vulnerability detail

Root cause, mechanism step by step, and the consumer path that turns it into
impact. Include the offending code verbatim (short) and the exact file:line refs
for the guard that is skipped/bypassed. State the precondition the attacker needs
and whether it is reachable in steady state.

## Impact

What the attacker gains, in units of funds at risk, with the program's OWN
arithmetic showing the numbers. Separate: (a) mechanism proven, (b) live target(s)
classified Active/LTV, (c) what bounds the live impact today.

## Proof of concept

All PoCs run locally against the DEPLOYED programs with real mainnet accounts as
fixtures; no transaction is sent to mainnet.

### A. <oracle/source-side> PoC

```bash
<exact command>
```

Observed (log `<path>`, sha256 `<hash>`):

```
<verbatim log lines proving the claim>
```

### B. <consumer/lender-side> PoC

```bash
<exact command>
```

Observed (log `<path>`, sha256 `<hash>`):

```
<verbatim log lines, including the rejection text with the program's own arithmetic>
```

Declare every synthetic input and every setup substitution (seeded accounts,
rewritten timestamps) explicitly in this section.

## Honest bounds

- Which comparable targets are protected (clamp/guard) and why this one is not.
- Liquidity/limits that cap the demonstrated amount today, and what funding would do.
- No claim that funds were moved on mainnet.

## Recommendation

1. <fix in the root-cause program — the guard/config change>
2. <defence in the consumer, e.g. reject the risky config at update time>
3. <monitoring/guard>

## Evidence

| artifact | sha256 |
|---|---|
| `<log path>` | `<hash>` |
| `<harness source>` | `<hash>` |
| deployed ELF (fixture) | `<hash>` |

<one line: which independent verification pass re-ran what, and where its record lives>
