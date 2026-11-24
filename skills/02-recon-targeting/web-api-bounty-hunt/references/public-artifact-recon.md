# Public artifact recon (docs, SDKs, embedded forms)

Use during workflow steps 1 and 2, before any request against the target. Every
recipe here is read-only. Save what you fetch to a local scratch directory so
later rounds re-read instead of re-fetching and the exact wording stays available
as evidence.

## Mintlify docs: harvest source, do not parse rendered HTML

A Mintlify site embeds an AI-assistant script that floods any regex-to-text pass.
Its source is exposed directly instead:

- `curl -sL https://<docs-host>/llms.txt` returns the complete page index with
  `.md` URLs. Take those URLs; never guess slugs.
- Each `<page>.md` returns clean markdown. Loop the index in one Python/urllib
  pass, write each page to a file named from its slug, and space requests ~0.25s.
- Grep the saved files for endpoint literals (`/api/v1/...`, `/graphql/...`),
  `BAD_REQUEST` / validation rules, and the `NOTE`, `WARNING`, `Known and
  accepted` and `documented behavior` sections. Those are the intended checks:
  a finding is a deviation from them, not the documented case itself.
- Probes then test validation edges (malformed ids, wrong-case prefixes, depth
  limits, testnet-only routes on mainnet) rather than re-reading prose.

```python
import urllib.request, time
index = urllib.request.urlopen(f"https://{host}/llms.txt", timeout=30).read().decode()
for url in re.findall(r"https://[^\s)]+\.md", index):
    name = url.split("/")[-1]
    open(name, "wb").write(urllib.request.urlopen(url, timeout=30).read())
    time.sleep(0.25)
```

Use the Jina reader only for docs hosts without this convention.

## Published SDK source when the repo is private

A 404 on the SDK's GitHub repo does not mean the source is unavailable: registry
artifacts contain it, and reading a published package is legitimate recon.

- npm: `https://registry.npmjs.org/<pkg>/latest` gives version, repository and
  `dist.tarball`; download and `tar -xzf` it.
- PyPI: `https://pypi.org/pypi/<pkg>/<version>/json`, take the `urls[]` entry with
  `packagetype == "sdist"`. This is the form that keeps readable source.
- crates.io: `https://crates.io/api/v1/crates/<crate>` gives version and
  repository; docs.rs serves per-file source for deeper reads.
- Download two adjacent versions and diff them first. A fix already shipped
  closes that hypothesis class: for example a signed-broadcast retry guard,
  signer/public-key verification, or market-id decoding now accepting both hex
  and base64.
- Grep for `retry`, `backoff`, `broadcast`, `sequence`, `timeout`, `recover`,
  address conversion and monetary-unit handling. Signed writes must never be
  retried blindly, because a lost response does not imply rejection. A guard
  there means the double-submit class is already handled.

## Embedded submission forms

Program pages often present a "Submit a report" card with no `<form>` element.
The real form is a third-party widget, and its fields tell you what identity and
payout data the program collects before the operator submits anything.

- Grep the raw HTML for `iframe`, `data-src`, `data-form-id`, and
  `form_embed.js`. The iframe's `data-src` is the widget URL.
- Fetch that widget URL directly with a browser User-Agent.
- Strip `<script>` and `<style>` blocks, HTML-unescape, collapse whitespace to
  read the visible labels; separately extract `data-q` and `name` attributes for
  the machine field names.
- Typical findings: required handles, an EVM wallet address, severity radios,
  attachments and a recording link, with no KYC field. Report the collected
  fields as part of program verification. Never fill or submit the form.

## Passive subdomain enumeration before probing

Map `*.domain` from read-only sources before sending requests:

- CertSpotter: `https://api.certspotter.com/v1/issuances?domain=<domain>&include_subdomains=true&expand=dns_names` returns JSON with `dns_names[]`; strip `*.` and dedupe.
- Wayback CDX: `https://web.archive.org/cdx/search/cdx?url=*.<domain>/*&output=json&collapse=urlkey&fl=original&limit=500` catches hosts no longer present in certificates.
- Host strings already present in fetched JS bundles and page HTML.
- A certificate-transparency source can return a transient 502; move to the next source instead of reporting "no subdomains". Union the sources and record which one produced each host.

Treat the result as scope candidates, not confirmed live assets.

## Public-by-design reads are not IDOR

When the API docs state that reads need no credential and accept any owner
address, querying another address is intended behavior. Drop the IDOR hypothesis
and spend the request budget on deviations from the documented validation rules.