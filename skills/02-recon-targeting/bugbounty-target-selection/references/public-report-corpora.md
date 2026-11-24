# Public report corpora

Use a disclosed-report corpus to find the discovery path for a bug class or
program before committing to a target. The value is not the CVE number, it is
the recon to impact chain and the weakness distribution across real reports.
The same recipe applies to any corpus with a public API.

## Query order

1. Hit the live stats endpoint first to confirm the corpus is current and to
   get report/class/weakness/program counts. Treat numbers from the announcing
   post as claims; the live endpoint is the fact.
2. Pull the class and weakness taxonomy, then filter reports by class,
   weakness, program, severity and year. Read the discovery-path annotations,
   not just the titles.
3. Cross-check any specific report against its original linked source.
   Corpus annotations may be AI-generated, so they are leads, not evidence.
4. Record the pattern as a hypothesis for the chosen target, then run the
   normal target vetting gates: rep gate, scope, audit depth, grading clauses.

## POJIA (concrete recipe, other corpora follow the same shape)

- REST base: `https://cve.pojia.ai/api/v1`, GET only, snake_case JSON.
  Endpoints: `/stats`, `/classes`, `/classes/{key}`, `/weaknesses?class=x`,
  `/weaknesses/{slug}`, `/programs?q=&sort=reports|bounty|name`,
  `/programs/{handle}`,
  `/reports?q=&class=&weakness=&program=&severity=&year=&has_cve=&sort=&limit=&cursor=`,
  `/reports/{id}`, `/reports/{id}/similar`, `/search?q=`, `/cves?year=&q=`,
  `/cves/{cve}`, `/payloads?class=x`, `/bypasses?class=x`, `/openapi.json`.
  List endpoints return `data`, `next_cursor`, `total`; pass `next_cursor` back
  as `cursor`. Anonymous 60 req/min per IP, `Authorization: Bearer *** 600/min.
  The anonymous tier is enough for a first query.
- MCP: `https://cve.pojia.ai/mcp`, all tools read-only.
  `claude mcp add --transport http pojia https://cve.pojia.ai/mcp`
  Claude Desktop / Cursor JSON uses `type: http`, `url`, and an optional
  `Authorization: Bearer *** header. Anonymous 30 req/min, key 90/min and
  5,000/day. Any MCP client can use the same endpoint, including Hermes.
- `https://cve.pojia.ai/bypasses` groups recurring control failures with
  concrete examples per class: XSS, SSRF, open redirect, path traversal, rate
  limiting, 2FA, access control, SQLi, file upload. Use as a candidate test
  list, not as proof that a given target is vulnerable.

## Caveats

- Some annotations are model-generated and vector search is third-party. A
  plausible annotation is not evidence; open the original report.
- The corpus serves excerpts plus links, not full report text by default.
- Indexed sources are public disclosures only. Absence from the corpus is not
  evidence that a bug class never occurs in a program.
- Self-service key issuance can depend on account or sign-in configuration
  that is not yet live. Do not block a first query on obtaining a key.
