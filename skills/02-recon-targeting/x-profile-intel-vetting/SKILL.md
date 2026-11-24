---
name: x-profile-intel-vetting
description: "Use when vetting X hunter posts. Verify ID, cards, payloads."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [BugBounty, X, Twitter, OSINT, Vetting, Payload]
    related_skills: [writeup-intel-digest, blocked-page-recovery, web-api-bounty-hunt]
---

# X profile intel vetting

Turn one eye-catching X post from a security account into a verified profile
assessment. Answers: is the account real, is the post fresh, is the payload
original, and what can safely be learned from it.

## When to Use

Load when the operator sends an X post from a bug-bounty or security account
and asks to dig into the profile, check similar posts, or judge credibility.
Also load when a post is just a one-liner with a payload and the operator wants
to know whether it is real research or engagement farming. Do not use for
choosing a bounty target (opportunity-vetting) or validating the operator's own
finding (finding-validation-gate).

For this operator write the chat answer and any report in casual Indonesian,
without em-dashes, and close with short numbered next-step options.

## Governing rule

A post is a CLAIM. The account may be a genuine researcher and the post may
still recycle an old reward card. Verify identity, date and payload on three
separate axes before giving a verdict. Never infer dishonesty from follower
count or from a templated caption alone.

## Workflow

### 1. Get the post

- Strip `?s=` and `?a=` share junk from the URL and keep the status id.
- `curl -sL https://api.fxtwitter.com/<handle>/status/<id>` first. The id-only
  route `https://api.fxtwitter.com/status/<id>` also works. Verify the returned
  `tweet.id` equals the requested id, because the mirror cache can serve a
  different post with HTTP 200.
- Cross-check with `curl -sL https://r.jina.ai/https://x.com/<handle>/status/<id>`.
  Jina exposes the Conversation section, where the interesting reply often is.
  A reply asking about the author's workflow is evidence of public perception,
  not proof of automation; say so if the author never answered.
- Inspect `raw_text.facets` for the expanded t.co URLs and `media.all[]` for
  attached reward cards. Download the card with `?name=orig` and read it with
  vision_analyze.
- Use a nitter profile render (`r.jina.ai/https://nitter.gq/<handle>`) to get a
  longer feed than Jina on x.com gives. The load-more cursor frequently returns
  a login stub, so report only the posts actually observed. Jina keeps post text
  but flattens dates and engagement into bare number lines. When the verdict
  needs dates or an engagement-ranked sample, curl the nitter profile HTML
  directly with a browser User-Agent and parse the `timeline-item` blocks
  (recipe in `blocked-page-recovery`, section 4 X/Twitter).
- A teaser that says a tool drops "today" without a link has no payload in
  `facets` or `card`. Identify it before answering: resolve the GitHub login
  from the author's bio links or a web search of his name plus known site, since
  the X handle and the GitHub login often differ. Then fetch
  `https://api.github.com/users/<owner>/repos?sort=created&direction=desc`,
  compare `created_at` with the post timestamp, then read the author's Nitter
  feed for the follow-up post naming the repo. State that identification method
  in the report; never present the repo name as if the teaser itself linked it.

### 2. Verify identity independently

- Read the bare profile via Jina. Record join date, post count, followers and
  every external link in the bio.
- Follow platform links to the hunter profile. On YesWeHack, Jina markdown
  returns only the hacktivity table and hides the header stats. Fetch the raw
  HTML with a browser User-Agent, strip `<script>` and `<style>`, strip tags,
  then regex `KYC verified`, `Reports`, `Points`, `Rank`, `Impact`, and
  `Joined YesWeHack in`.
- Cross-check the real name and track record on LinkedIn or the platform's own
  ranking when linked. A KYC badge plus a non-trivial report count is strong
  evidence the account is a real researcher.
- Do not call an account a content farm when the platform profile confirms KYC
  and real reports. Low followers relative to views is normal for a small
  hunter account.

### 3. Recycled-card test

This is the check that actually separates a fresh post from a promo feed.

- Download every reward card attached to the sampled posts.
- For each card, transcribe username, date, severity, CVSS, CWE, amount and
  points with vision_analyze. Save the transcription into a JSON or CSV file in
  the scratch dir, then aggregate in Python. Do not compare dates in your head.
- Compare the card date with the X post date. Cards dated weeks or months
  earlier under a caption saying "Just got a reward" are recycled.
- State the sample size honestly: "four of five cards read were old" is correct;
  "all posts are recycled" is not if three cards were never inspected.
- A card date can be a reward date rather than a report date. A nearby CVE
  publication date is not proof that the post refers to that CVE, especially
  when the CVSS differs (for example card 9.1 versus CVE 9.8). Label that as a
  mismatch, not an identification.

### 4. Similar-post sweep (when asked about other accounts)

- Web-search the exact caption phrase with `site:x.com` and collect status IDs
  and handles into a JSON file. Deduplicate in Python.
- Batch `api.fxtwitter.com/status/<id>` for every candidate, verify each
  returned id, and filter by an exact substring of the template text. Save the
  full result; do not keep only the first screen of search output.
- For each hit, extract the linked hunter handle, fetch the X profile and the
  hunter profile, then produce a verdict table: verified real, no verifiable
  platform link, or recycled-feed signal. Count the hits and assert the count
  against the table before answering.
- A caption template shared by many hunters is usually the platform's own
  share format. Report that explicitly instead of treating it as a farm
  signature. The differentiator is card date, payload embellishment and post
  cadence.

### 5. Payload triage

- URL-decode encoded payloads before interpreting them. Keep the raw and the
  decoded form in the report.
- Map each payload to a known mechanism and corroborate with a primary source:
  NVD or cve.org for the CVE, the vendor advisory, the upstream GitHub issue,
  or a PoC repo. Keep the author's target and score as claims.
- Where the exact gadget chain is not documented in the sources read, say so.
  Example: ONLYOFFICE `ZipFileAsString` and `GetFontBinary` are documented
  native file reads (DocumentBuilder issue 147, closed December 2025), but a
  `Function("return this")().GetNativeEngine()` prefix was not found in those
  sources, so it stays an author claim.
- Hand reusable Web/API patterns to `web-api-bounty-hunt` as hypotheses only.
  Require a minimal read-only differential on an in-scope host before calling a
  pattern applicable. Check the scope store under `E:/audit/<target>/scope*` and
  re-read the live policy; a stored scope file is a snapshot.

### 6. Deliver

- Chat answer: verdict on credibility, the post pattern table, card-date
  findings, payload verdicts, and explicit limits of verification.
- A durable report under `<home>/reports/`, delivered with `MEDIA:/absolute/path`.
  When a reusable field test is produced, merge it into the canonical Web/API
  checklist (`<home>/checklists/web-api-checklist.md`) and mirror it byte-for-byte
  to the Web/API template in the `writeup-intel-digest` skill's references
  directory, patching
  the body, the condensed index and the provenance table in one pass.
- Close with short numbered next-step options.

## Pitfalls

- Jina on `x.com/<handle>/with_replies` and on `nitter/<handle>/media` often hits
  a login wall while nitter's main profile render works. Use the working route,
  do not conclude the account has no history.
- A rotating "Comment KEYWORD for the link/toolkit" CTA, with the keyword
  changed each post while the headline stays ALL-CAPS with a leading emoji, is
  an engagement-farm signature, not a research feed. Count the ratio in the
  sampled posts and state the sample size. High-volume accounts have too many
  posts to read all of them, so report the observed ratio, never "all posts".
- A reward card's severity and amount are platform-displayed claims in a public
  share graphic, not an independently verified rating.
- A burst of many reports in one day is consistent with automation but does not
  prove AI use. Report the observation and the public question about workflow
  separately, and never present speculation as the author's method.
- Account-side steps (login, KYC, submission) belong to the operator. Give
  step-by-step instructions and never type credentials or codes.
- Before recommending a self-hosted tool, check its runtime prerequisites on
  the operator's machine (`docker`, `docker compose`, `go`, an open port) and
  its platform coverage against the programs they actually hunt. A good tool
  can still be wrong for this workflow. Give a defer verdict with the reason
  instead of an install walkthrough when either check fails.
- Writing the report: scan for CJK characters, em-dashes and stray English
  connectors before delivery, and fix every hit.

## References

- `writeup-intel-digest` - retrieval ladder and writeup triage buckets
- `blocked-page-recovery` - X mirrors, Jina, archive fallbacks, fake-success detection
- `web-api-bounty-hunt` - scope-gated field testing of borrowed payload patterns
- `scripts/profile_sweep.py` - batch fxtwitter status fetch with id verification
