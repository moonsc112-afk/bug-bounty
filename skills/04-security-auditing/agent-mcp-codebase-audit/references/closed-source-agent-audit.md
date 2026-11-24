# Closed-source agent audit from public docs

Use when the agent source is private but the product publishes a security chapter, env-var reference and a bug bounty policy.

## Sources to harvest, in order

- Security or threat-model chapter.
- Each layer detail page it links: sandbox, fund confirmation, script or command risk gate, audit and overrides.
- Tool registry and permission tiers.
- Env-var reference, especially kill switches, policy exemptions and process-wide bypasses.
- HTTP gateway page, auth defaults and admin routes.
- Bounty policy out-of-scope list and scenario-to-severity examples.
- Research-tool eligibility page and its gating criteria, because testrun plans may depend on access the operator does not yet have.

Keep the exact wording of gate contracts and exclusions. A sentence saying a caller-supplied confirmation counts as consent evidence is a specification lead. A sentence saying runtime-built payloads are a scope boundary kills a lead.

## Verify the quotes stay live

Small stdlib probe, no dependencies:

```python
import html, re, urllib.request
text = urllib.request.urlopen(url, timeout=20).read().decode("utf-8", "ignore")
text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text)))
assert phrase in text
```

Check a handful of robust substrings, not whole formatted sentences. Markdown emphasis and inline code produce different raw HTML across sites, so including backticks or `**` in the matcher creates false negatives. If raw HTML contains only CSS/JS bootstrap, repeat the probe through a rendered-text route (`r.jina.ai/<url>` or `web_extract`) and record which route was used.

## Hypothesis record

- Location: doc URL and section, plus the exact quoted sentence.
- Attack: untrusted entry point, model tool call, gate path, sink.
- Impact: what crosses an intended boundary.
- Confirm: observable product behavior, for example tool-call arguments plus absence of a consent card plus a transaction hash.
- Refute: the safe behavior that kills the hypothesis.
- Fix: architecture change, not a prompt tweak.

Rank fixed payout tiers above negotiated ceilings. If a program pre-rejects theoretical issues without a reproduction path, label the output as hypotheses and stop short of calling them findings. Before drafting, collapse hypotheses with the same root cause into one entry at the highest payout tier.

## PoC plan file shapes

Matrix entries: id, rank, surface, entry, payload, steps, evidence, expected_bug, expected_safe. Emit one payload file per hypothesis plus a run order. Keep the matrix script stdlib-only and offline by default; a separate verify mode may fetch the cited pages through the rendered-text route. State plainly that the kit prepares evidence and does not execute the attack.

## Work split

Operator: account, login, KYC, funding, any consent click, public submission.
Agent: doc verification, attack surface map, payloads, step matrix, report draft, duplicate-root-cause check across hypotheses.

## Installer source recovery

Use when the documented source repo is unavailable but the vendor publishes a desktop installer.

- Locate the download from the vendor's own site. `/download-app` and `/get-app` style routes often render the direct CDN links only in the rendered page; Jina-read the page if raw HTML hides them. Do not guess repository or release URLs when the documented one returns 404.
- Verify before unpacking. `curl -sIL <file>` records `Content-Length`, `Last-Modified`, `ETag`, `x-amz-meta-sha256` and cache headers. Stream the bytes through a Python SHA-256/MD5 reader and compare both values with the header and ETag. In PowerShell, `Get-AuthenticodeSignature -FilePath <file>` returns `Status`, `SignerCertificate.Subject`, `Issuer`, validity dates and thumbprint. The signer subject is a primary-source entity claim, but do not equate it with the product brand unless another source links them.
- `file <exe>` distinguishes an NSIS self-extracting archive from other installers. `7zr l <exe>` lists NSIS content; `7zr x <exe> "resources\\agent\\dist\\gateway\\server.js" -o<out> -y` extracts selected paths. A full agent bundle can approach 1 GB, so filter the listing for `node_modules`-free paths before extracting.
- Compiled bundles often keep readable names through esbuild's `s(fn, "name")` calls. Search for the resolver that returns `satisfied: true`, then walk its callers and each evidence field to its origin. Inspect both the resolver and its callers: a resolver can look permissive while every caller supplies only server-derived values.
- Do not run the installer to answer a static question. Archive extraction is read-only; executing the installer is not.

## Refuting consent-confusion leads

A docs sentence naming a "caller-supplied confirm" is a lead, not a finding. Determine what the gate actually accepts as consent:

- If satisfaction comes from a persisted grant lookup (`consentStore.findActiveGrant` or equivalent), a session token, a preview receipt or an automation policy resolver, then a boolean in the model's tool arguments is not the trust boundary.
- Check the autonomy predicate as well. When an `isAutonomous` style helper returns false for interactive user turns, the standing-grant path is inert and the interactive confirmation path still runs.
- Record the refutation with the resolver name, the origin of every evidence field and the interactive-turn predicate. Mark every dependent draft, runbook and payload RETRACTED in the same pass so stale text cannot be submitted by accident.
- Label the docs sentence as misleading rather than as a vulnerability when the shipped code implements the safer design. The corrected claim belongs in the refutation list, not in a report.
- Treat documented UI controls as stale until the current screen confirms them. A docs flow naming buttons such as `Schedule on` and an `I understand` checkbox may not exist in a redesigned app whose Automations surface only offers `Create automation`; build the PoC around the screen that actually renders and require screenshots of the live preview instead of assuming the documented one. WHY: a UI redesign leaves security docs describing a flow users no longer see, so a consent-mismatch hypothesis aimed at the old control tests nothing.
