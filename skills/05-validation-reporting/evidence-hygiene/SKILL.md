---
name: evidence-hygiene
description: "Use before capturing or attaching PoC evidence with cookies or PII. Redact, verify."
sources: community, operator_experience
---

# EVIDENCE HYGIENE — PoC Capture & Redaction Discipline

> Use this skill BEFORE capturing any screenshot, exporting any HAR, or attaching any evidence to a bug-bounty submission. It catches the most common evidence-hygiene mistakes that cause cookies to leak, PII to be shared without consent, or screenshots to be unsuitable for triage.

The core principle: **Bug-bounty evidence is meant to convince a triager. Anything beyond that — live cookies, real-user PII, internal trace IDs that aren't useful — should not be in the evidence.**

---

## 1. Two Categories of Sensitive Data

Every PoC artifact (screenshot, HAR, raw HTTP request, terminal transcript) potentially contains data that needs different treatment.

| Category | Examples | Treatment |
|---|---|---|
| **Your-account secrets** | Session cookies, OAuth tokens, refresh tokens, API keys | Always redact. Even in private bug-bounty platform attachments. Your account, your session — protect it. |
| **Other users' PII** | Real names, emails, phone numbers, addresses, profile photos, account IDs | Redact unless explicitly demonstrating cross-account impact. Even then, mask faces and minimize the data you display. |
| **Triager-useful metadata** | Trace IDs (`x-datadog-trace-id`), request IDs, server timestamps, your test account UID/email, GraphQL operation names, response shapes | **Leave visible** — these help the triager correlate to logs and reproduce. |
| **Test-account passwords (limited use)** | Throwaway passwords on a test account (e.g., `Testing@5678`) | Acceptable in screenshots if you rotate immediately after submission so the value shown is dead. Don't leave real-use passwords in evidence. |

---

## 2. Cookie Redaction Protocol

### 2.1 What must be masked

The session cookie value is the highest-value secret in any PoC. Mask:

- The session cookie (`authn`, `session`, `sid`, `__Secure-id`, etc. — name varies per target)
- `csrf-token` if it's bound to your session
- `Authorization` headers (Bearer tokens, JWT)
- `Cookie` request header values for any session-bearing cookie
- `Set-Cookie` response header values for any session-bearing cookie

### 2.2 What's safe to leave visible

- Cloudflare cookies (`__cf_bm`, `_cfuvid`) — these are bot-management, not session-bearing
- Analytics cookies (`ajs_anonymous_id`, `_ga`)
- Trace correlation IDs (`x-datadog-trace-id`, `x-request-id`)
- Server / framework headers (`Server: cloudflare`, `X-Frame-Options`)
- Your test account email/UID (per Bugcrowdninja alias section in `bugcrowd-reporting`)

### 2.3 Redaction methods (ranked by practicality)

**Method A — Don't capture the cookies in the first place** (preferred when possible)
- For DevTools Console PoCs: use `credentials: 'include'` so the browser sends cookies automatically. Console output won't echo the cookie. Screenshot the Console output, never the Network tab Headers panel.
- For Burp Repeater PoCs: drag the bottom request/response panel divider DOWN to hide the request body before screenshotting. Capture only the Results table for Intruder runs.

**Method B — Black-bar in image editor** (when capture inevitably includes cookies)
- macOS: Open screenshot in Preview → Tools → Annotate → Rectangle → set fill color to black → drag rectangle over the cookie value → save
- Windows: Use Snip & Sketch's annotation tools or any image editor (Paint.NET, etc.)
- Burp itself: in Burp's Proxy → Match and Replace, you can pre-emptively redact cookie values to placeholder strings before screenshotting

**Method C — Find/replace in raw text** (for HAR files, terminal transcripts)
- See §4 for the sanitize_har.py command

### 2.4 Pre-screenshot checklist

Before clicking Capture:

```
[ ] Network tab Headers panel is collapsed or out of frame
[ ] Burp's Request panel is hidden behind the divider drag
[ ] No "Copy as cURL" output is visible on screen
[ ] DevTools Application → Storage → Cookies tab is closed
[ ] Browser URL bar doesn't show a session token in query string (rare but possible)
```

After capturing:

```
[ ] Open the screenshot at full resolution before saving
[ ] Search for the session cookie name substring in any visible text — if present, redact
[ ] Search for the literal first 6 chars of your cookie value — if present, redact
[ ] Compare to the previous PoC screenshot in the same engagement — same redaction discipline
```

---

## 3. PII Black-Bar Protocol

When a PoC necessarily exposes another user's data (e.g., demonstrating IDOR by showing the victim's email in an attacker-session response), redact the actual PII even in private attachments.

### 3.1 What to mask (other-user data)

- First name, last name (full or partial)
- Email address (mask the local part; can leave domain if non-identifying)
- Phone number (mask the last 7 digits, optionally leave country code)
- Physical address (mask everything below city)
- Date of birth (mask the year, optionally the month)
- Government IDs (SSN, passport — mask everything)
- Profile photos / face images (black-bar the face entirely)
- Account IDs that the user could correlate to public profiles

### 3.2 What to leave visible (proves the bug, not the user)

- The fact that the field was returned (the JSON key name)
- The shape / type of the field (`"first_name": "<REDACTED>"`)
- Your own (attacker session's) UID / email — this proves cross-account
- The endpoint URL and request method
- The trace ID

### 3.3 Worked example — IDOR PoC body

**Bad (leaks victim's full PII):**
```json
{"data":{"contact":{"first_name":"Nadene","last_name":"Afton","email":"nadene.afton@example.com","phone":"+1-555-867-5309"}}}
```

**Good (proves the bug, masks the PII):**
```json
{"data":{"contact":{"first_name":"<REDACTED — real first name>","last_name":"<REDACTED — real last name>","email":"<REDACTED>@example.com","phone":"<REDACTED>"}}}
```

In screenshot form, black-bar each value with a rectangle annotation labeled "REAL PII REDACTED" if there's space.

### 3.4 In the report body

Reference the redaction explicitly:

```markdown
## Proof of Concept

The screenshot below demonstrates the IDOR. The attacker session (uid 12345678) successfully retrieves the victim's profile data (uid 99887766). **Real PII fields in the response are masked with black rectangles to limit unauthorized exposure of victim data, per responsible-disclosure hygiene.** The unredacted response is available privately on request.
```

This signals the triager that you're disciplined and gives them a clear path to the unredacted version if they need it for verification.

---

## 4. HAR File Sanitization

HAR (HTTP Archive) files are JSON dumps of network traffic with full request/response bodies and headers. They include cookies, auth tokens, and any PII that was in transit.

### 4.1 Generate the HAR

Chrome DevTools → Network tab → right-click anywhere in the request list → "Save all as HAR with content"

### 4.2 Sanitize before attaching

Use the bundled Python stdlib script. It needs no `jq` and no third-party packages, so it works on this host.

```bash
python3 scripts/sanitize_har.py /path/to/exported.har
# Output: /path/to/exported.sanitized.har
# The script verifies its own output and exits 2 if any sensitive value remains.
```

The script redacts request headers `cookie`, `authorization`, `x-csrf-token`, response header `set-cookie`, and every entry in `request.cookies` and `response.cookies`. Edit the sets at the top of the script if a program uses another header name.

### 4.3 Verify before attaching

The script already verifies headers and cookies. Add a text search for values that live elsewhere in the HAR, especially inside bodies:

```bash
grep -i 'authn\|"cookie"\|authorization' /path/to/exported.sanitized.har | head -20
python3 scripts/sanitize_har.py /path/to/exported.sanitized.har --verify-only
```

If your real cookie value or victim data still appears, add a redaction rule and rerun. Do not attach a HAR that fails verification.

### 4.4 Remove other-user PII (if applicable)

If the HAR captured cross-account data (e.g., during an IDOR demo), scrub the response bodies too. Pass a regex per value:

```bash
python3 scripts/sanitize_har.py exported.har \
  --redact-text 'real\.first\.name\.example' \
  --redact-text 'victim@example\.com'
```

Regexes are applied to `response.content.text` whether the body is plain text or JSON text, so no `fromjson` step is needed. Customize the patterns to the specific captured data and verify the output before attaching.

---

## 4b. Credential-bearing request runners

When a proof needs API keys or session tokens the agent must not handle, ship a
runner script the operator executes in their own shell. The script reads
credentials from environment variables, checks for missing variables before any
request, prints only presence (`SET` / `MISSING`) and never values, and writes
results to disk with every secret value and `Bearer` token replaced by a
placeholder. Keep the request count fixed and sequential, with no retry loop.
Decode or unescape captured text BEFORE replacing secrets, never after: an
entity encoded token survives a plain string replacement and becomes plaintext
when a later `html.unescape` runs, landing in the artifact the runner promised
was redacted. Verify the runner with a crafted encoded-secret fixture and
assert the literal secret is absent from its output, alongside a plaintext
control that must be redacted. WHY: redaction that decodes after masking turns
a hidden credential back into visible text at the point it is written to disk.

WHY: chat and tool transcripts are logged and become part of the evidence chain;
a pasted key contaminates every artifact and cannot be redacted retrospectively.
A missing-variable check also fails before a half-configured run sends malformed
authenticated traffic.

## 5. Burp Suite Screenshot Hygiene

### 5.1 Repeater (single request demo)

1. In the Repeater request panel, the Cookie header is on its own line — drag the panel divider DOWN to hide everything below the request line / target line
2. Or: temporarily delete the Cookie header text from the Repeater pane (it doesn't affect the original captured request) before screenshotting, then restore
3. Capture only the response panel (right side) showing the JSON / HTML response that demonstrates the bug

### 5.2 Intruder Results table (rate-limit / brute-force demos)

The Results window is the strongest evidence for rate-limit findings. To capture cleanly:

1. After the attack finishes, drag the horizontal divider between the Results table and the Request/Response panels DOWN, until only the Results table is visible
2. Screenshot only the columns: `Request#`, `Payload`, `Status code`, `Response received`, `Length`
3. Don't include the Request / Response sub-panels — they contain the cookie

### 5.3 Proxy HTTP history (capture demo)

Almost never the right screenshot — it shows entire request/response pairs with cookies. Use Repeater for demos instead.

### 5.4 Scanner findings (if applicable)

The Scanner tab's Issues panel is generally safe to screenshot — it shows finding summaries without the underlying request bodies. Click into a specific finding before screenshotting only if you've redacted its evidence first.

---

## 6. Chrome DevTools Console PoC Patterns

### 6.1 The clean-PoC pattern

```js
fetch('/api/endpoint', {
  method: 'POST',
  headers: {'content-type': 'application/json'},
  credentials: 'include',  // sends cookies automatically — they won't appear in your code
  body: JSON.stringify({ /* your payload */ })
}).then(r => r.json()).then(j => console.log("LABEL:", JSON.stringify(j)))
```

Why this is clean:
- `credentials: 'include'` means the browser sends cookies. Your code never references them. They never appear in screenshots.
- `console.log("LABEL:", ...)` produces a labeled output line you can search for in the screenshot
- `JSON.stringify(j)` formats the response on a single line — easier to crop tightly

### 6.2 Multi-step PoCs (clear console between calls)

For a 4-step PoC (verify before / change / verify after / revert), clear the console between calls so each screenshot only shows ONE call and ONE response:

- Mac: `Cmd+K`
- Windows / Linux: `Ctrl+L`

Take the screenshot immediately after the response prints — don't wait for unrelated framework warnings to appear.

### 6.3 Long responses (truncate for screenshot)

If the response body is too long for a clean screenshot, log a summary instead:

```js
fetch('/api/endpoint', { /* ... */ })
  .then(r => r.json())
  .then(j => {
    console.log("RESPONSE SHAPE:", Object.keys(j.data || {}));
    console.log("CRITICAL FIELD:", j.data?.victim_id, j.data?.email);
    // (Don't dump the full j — your screenshot becomes unreadable)
  })
```

### 6.4 Allow-pasting reminder

Chrome blocks paste into DevTools Console as anti-self-XSS protection. Type `allow pasting` (literal phrase) once at the start of each session. Do this BEFORE you take any "running PoC" screenshot — otherwise the warning text appears in the screenshot.

---

## 7. Screenshot Capture Order Discipline

### 7.1 The 5-step PoC pattern (for state-change findings)

For findings like "password change without step-up," the canonical 5-screenshot pattern is:

1. **Pre-state verification** — `verify_password("current") → true`. Proves you knew the starting state.
2. **The bug itself** — `update_password(...)` succeeds without step-up. THE most important screenshot.
3. **Post-state verification (negative)** — `verify_password("old") → false`. Proves the change took effect.
4. **Post-state verification (positive)** — `verify_password("new") → true`. Proves the new credential is active.
5. **Out-of-band side effects** — inbox screenshot showing whether a notification email arrived. Proves whether passive defense exists.

### 7.2 Filename conventions

Numbered, descriptive, hyphen-separated:

```
{finding-#}-step{step-#}-{description}.png

Examples:
04-step1-verify-true-before.png
04-step2-update-password-no-stepup.png
04-step3-verify-false-after.png
04-step4-verify-true-new-pw.png
04-step5-inbox-notification-check.png
```

In the report body, reference each by filename:

```markdown
- **Screenshot 1 (`04-step1-verify-true-before.png`)** — verify_password returns true with the current password.
- **Screenshot 2 (`04-step2-update-password-no-stepup.png`)** — update_password returns User with no StepUpRequiredError. THIS IS THE BUG.
- **Screenshot 3 (`04-step3-verify-false-after.png`)** — verify_password with old password returns false.
- **Screenshot 4 (`04-step4-verify-true-new-pw.png`)** — verify_password with new password returns true.
- **Screenshot 5 (`04-step5-inbox-notification-check.png`)** — inbox showing whether out-of-band notification was sent.
```

### 7.3 Capture timing

- Take all screenshots in one sitting, not across multiple sessions. Mid-session inconsistencies (different browser sizes, different cookie values) are confusing for the triager.
- Don't reload pages between screenshots if avoidable. Reloads regenerate cookies and may invalidate prior captures.

---

## 7.4 On-chain bounty evidence and submission audit

For on-chain bounties, treat RPC endpoint files with embedded API keys, wallet private keys, and KYC
documents as report-forbidden; public program IDs, addresses, transaction signatures, and recorded log
lines are safe to quote. KYC goes through the platform's designated process, never through a vulnerability
report. WHY: submission bodies are logged permanently and program rules commonly forbid identity
documents there.

Before submission, re-hash every artifact quoted in the report and confirm every referenced path exists.
Regenerate the hash manifest in the same step as the final edit to any deliverable it covers. WHY: editing
a report or helper after manifest creation leaves stale hashes that break the evidence chain a triager
checks first.

Confirm what a cited artifact actually SAYS before letting a claim depend on it: existence is not support.
When a report attributes an independent verification, a second-person replay or a measured result to a
file, open that file and match the SPECIFIC assertion; a file can exist while documenting something much
narrower (a configuration cross-check instead of a PoC replay). Delete the unsupported claim rather than
softening it. WHY: an overclaim with a real-looking path beside it survives existence checks and is the
first thing an independent cross-checker overturns, taking the rest of the report's credibility with it.

Write hash manifests with LF line endings on Windows hosts. WHY: `sha256sum -c` treats a trailing CR as
part of the filename and reports every entry as unreadable.

Run `sha256sum -c <manifest>` from the exact root the manifest paths were written against, not from a
nested findings directory. WHY: manifest entries are relative paths, so a verification from the wrong
cwd reports every entry as unreadable even though every file exists.

Patch the manifest hash entry in the SAME edit pass as any post-submission change to a listed file
(coverage ledger after a triage verdict, corrected rebuttal note, rewritten report). WHY: the ledger
and the report are part of the evidence chain a triager re-hashes first, and a stale entry makes an
otherwise intact kit look tampered with.

Use `scripts/evidence_recorder.py` to turn operator observations into a structured
markdown plus JSON record and to regenerate the LF-terminated `SHA256SUMS` in the
same pass. Its `--sample` mode writes clearly labelled non-evidence files for
checking the tool itself. Never attach a sample file to a submission.

---

## 8. Post-Submission Hygiene

After clicking Submit on the bug-bounty platform:

### 8.1 Rotate the test account credentials

```
1. Log out of the target
2. Log back in (this rotates the session cookie — any cookie shown in your screenshots is now dead)
3. Change the password to a fresh value not used elsewhere (any password shown in your screenshots is now dead)
```

### 8.2 Save the unredacted artifacts privately

Keep your unredacted HARs / screenshots in a local folder accessible only to you. The triager may ask for the unredacted version during verification. **Never share unredacted artifacts via email — use the platform's private attachment system on the existing submission thread.**

### 8.3 Don't post about the finding publicly

Most platforms' confidentiality applies to BOTH unresolved and resolved issues. Don't tweet, blog, or discuss the finding in any forum until the program explicitly says you can.

### 8.4 Audit your local artifacts

Quarterly, sweep your `~/security-research/` and `~/Downloads/` for stale HARs / screenshots from old engagements. Either move them to a properly-encrypted archive or delete them. Bug-bounty engagement artifacts are sensitive — they accumulate fast and become a liability.

---

## 9. Pairing with Other Skills

| For this question / task | Use this skill |
|---|---|
| "Should I report this finding at all?" | `finding-validation-gate` |
| "What's the report body template?" | `report-writing` |
| "What VRT / severity / OOS rebuttal for Bugcrowd?" | `bugcrowd-reporting` |
| "How do I redact / sanitize this evidence?" | This skill (`evidence-hygiene`) |
| "How do I demonstrate the bug actually fires?" | `finding-validation-gate` |
| "Where are the recon probes for this asset class?" | `bounty-hunt-pipeline` (P2 Recon) |

---

## Notes on usage

This skill is meant to be loaded together with `report-writing` and (for Bugcrowd) `bugcrowd-reporting` when preparing a submission. It does NOT cover:

- **What** to capture (that's `finding-validation-gate` and `report-writing`'s job — they tell you what evidence is required for the report to be accepted)
- **How** to demonstrate exploitation (that's `web-api-bounty-hunt` for web or `evm-bounty-source-audit` for contracts, payloads to send)
- **Where** to find the assets (that's `bounty-hunt-pipeline` P2 Recon's job)

This skill covers ONLY the redaction / sanitization / hygiene layer that sits between "I have evidence" and "I'm attaching it to the platform."

---

## Related Skills & Chains

- **`report-writing`** — When evidence is redacted and ready for the report body. Workflow primitive: after redaction passes the pre-screenshot checklist, hand off to `report-writing` for the platform-specific report template (H1 / Bugcrowd / Intigriti / Immunefi).
- **`bugcrowd-reporting`** — When the redacted evidence is destined for Bugcrowd specifically. Workflow primitive: redacted screenshots + sanitized HARs become attachments referenced in `bugcrowd-reporting`'s VRT-mapped submission body.
- **`finding-validation-gate`** — When deciding which evidence is required at all. Workflow primitive: `finding-validation-gate` says "you need a 5-screenshot PoC for password-change-without-step-up"; this skill says "here's how to capture and redact those 5 screenshots cleanly."
- **`web-api-bounty-hunt`** — When the payload that produced the evidence is being documented. Workflow primitive: the payload goes in the report verbatim; its output / response (handled by this skill) gets cookie / PII redacted before screenshotting.
- **`bounty-hunt-pipeline`** — When P5 Evidence needs evidence captured. Workflow primitive: P5 routes through this skill before P6 Deliver drafts the report.
