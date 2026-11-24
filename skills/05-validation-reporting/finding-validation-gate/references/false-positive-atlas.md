# False-positive atlas and retraction template

Condensed from the `triage-validation` skill in
`elementalsouls/Claude-BugHunter` (CC BY 4.0), rewritten for this workspace.

## Four shapes that repeatedly fool validation

1. **URL echo as reflection.** The payload appears in the response because the
   response body IS the URL. Q1 kills it: nothing executed server-side.
2. **Word collision as marker hit.** A canary string matches an unrelated CSS
   class or a literal word already in the page. Use a unique marker and confirm
   the exact bytes you injected.
3. **Server policy as state oracle.** A download endpoint always returns
   "blocked" for a file extension whether or not the file exists. There is no
   oracle, only a deny-list. Q6 kills it.
4. **Status code as impact.** Baseline 403, probe 200, but the response body is
   byte-identical. Always diff bodies, not only status codes.

Two more from live engagements:

- A header reflection claim across four pages was the literal word `javascript`
  in help-link hrefs. The marker was not unique.
- A Host header bypass showed 200 on a normally 403 path, but the body matched
  the baseline byte for byte. The load balancer normalized the injected part.

## Deployed Solana/Anchor state-layout false positives

- Derive every struct offset from the source declaration, padding fields
  included, then confirm against raw fixture bytes. Never treat a run of `0xff`
  as a marker: padding arrays are commonly initialized to 255. WHY: a read that
  is off by one field turns padding into a fake "unrecognised borrow" marker.
- A repaid obligation can retain stale cached aggregate totals while its debt
  flag is cleared and its update state is stale. Check the flag and the real
  borrow-slot array at the verified offset before claiming hidden debt; a later
  refresh legitimately recomputes those totals to zero.
- Confirm a handler is dispatchable in the deployed ELF and that its log strings
  are present before treating a source-only handler as live. WHY: source and
  deployment diverge, and a clean source-level story can target an instruction
  mainnet never executes.

## Statistical claims

A single timing sample is not evidence. One engagement saw 1527 ms against a
700 ms control on a login endpoint; 80 interleaved runs collapsed every group
into 685 to 716 ms. Use interleaved samples and report the distribution.

## Retraction template

```markdown
### Retracted: <finding name>

- Original signal: <one line on what looked like a bug>
- Disproving evidence: <concrete reproduction step and observation>
- Why it looked like a bug: <root cause of the false positive>
- Retraction date: <YYYY-MM-DD>
```

## Severity reference (program matrix always wins)

| Finding | Score | Severity |
|---|---|---|
| IDOR read PII, auth required | 6.5 | Medium |
| IDOR write or delete, any user | 7.5 | High |
| Auth bypass to admin panel | 9.8 | Critical |
| Stored XSS with cookie theft | 8.5 | High |
| SQLi full DB dump | 9.1 | Critical |
| SSRF to cloud metadata | 9.1 | Critical |
| Race to double spend | 7.5 | High |
| JWT alg:none to ATO | 9.1 | Critical |

CVSS metric quick guide: internet exploitable AV:N; no special timing AC:L; free
account PR:L; no login PR:N; admin PR:H; no victim action UI:N; victim click
UI:R; all data read C:H; all data modified I:H; service crash A:H; app only
S:U; browser, OS, or cloud impact S:C.

Stored XSS UI is a judgment call. NVD/FIRST often uses UI:R, which lowers the
above row to about 7.6. Defend the choice or re-score before copying it.
