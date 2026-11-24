---
name: shared-security-post-vetting
description: "Use when a shared post links a security repo/writeup. Vet."
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [security, x-twitter, repo, writeup, vetting, cheatsheet, 403]
---

# Shared security post vetting and field notes

A user forwards a social post promoting a security tool, cheatsheet, wordlist,
repo, or a bug-bounty writeup, often with a vague "ultimate" or "$X payout"
headline. The deliverable is a verified verdict first, then an optional
up-to-date working note or reference set that replaces the stale or templated
shared content. Do NOT treat this as an opportunity/tier list
(`opportunity-vetting`) or a promo (`promo-deal-verification`).

## When to Use

- A forwarded X/social post links a GitHub repo, cheatsheet, wordlist, tool,
  or a writeup and asks what it is, whether it is worth keeping, or whether the
  claim is real.
- The user picks the follow-up to turn stale shared material into a current
  working note or a set of verified primary-source references.
- Not for bounty program tier lists, promo codes, or a single blocked page.

## Procedure

1. **Get the post in full.** Use `https://api.fxtwitter.com/<user>/status/<id>`
   (strip tracking query). Save raw JSON. Record author, timestamp, text,
   engagement and `community_note`. Jina-render the post URL for the
   conversation/replies and the expanded t.co target. Fallback routes in
   `blocked-page-recovery`.
2. **Fetch the primary artifact.** Resolve the link to the real repo/file.
   Fetch raw file content, not just the README. Use authenticated `gh api`
   first, unauthenticated api.github.com hits rate limits fast. Recover metadata
   with `gh api repos/<org>/<repo> --jq '{stargazers_count,forks_count,pushed_at,size,license:.license.spdx_id}'`
   and `gh api 'repos/<org>/<repo>/commits?per_page=5'` for real maintainer dates.
   Jina-render the GitHub blob page when the API is blocked.
   For a writeup, resolve the short link to the article, fetch the full text
   with `web_extract` (a Medium member-only story is often readable in full
   through that route or a public mirror), and record the article's own
   publication date. Compare it with the post date; a months-old article posted
   as new is a freshness finding. If the article's charts are client-rendered
   (empty chart `<div>`s in the HTML), follow the Benchmark and replication
   writeups section below to get the numbers from the embedded dataset.
3. **Verify the image, if any.** The post image is usually a screenshot of the
   same doc, not extra payload. Use `vision_analyze`; on a 429 fall back to the
   Windows OCR helper in `blocked-page-recovery/scripts/windows_ocr.ps1` with
   native backslash paths. Pass the image as an explicit native `C:/...` path:
   a bash `/tmp/foo.jpg` reaches vision_analyze as `\tmp\foo.jpg` and fails as
   `media file not found` even though curl wrote the file, because the image
   loader resolves paths natively on this host. Compare transcribed text
   against the raw file.
4. **Author-template check.** Jina-read `https://x.com/<handle>` and scan recent
   posts for a rotating headline with different money figures or a Telegram
   funnel. If the post claims earnings, that template is the verdict by itself.
   If the Jina profile read returns a login wall or 404, pull author metadata
   from `https://api.fxtwitter.com/<handle>` instead and use it to size up the
   account. Separate the curator from the actual author; credit the repo's real
   author even when the poster is a content farm. A direct free link means no
   monetised gate for this resource, say so plainly.
5. **Artifact verdict.** State: is the artifact real, who made it, how fresh it
   is, what is actually inside, and where the post's wording misrepresents it
   (common: "wordlist" for a markdown cheatsheet, or a templated retelling for
   an original report).
   Verify the license instead of assuming it: `gh api repos/<org>/<repo>
   --jq .license.spdx_id`, list the repo tree for LICENSE/COPYING/NOTICE, and
   for a PyPI tool check both the JSON metadata and the sdist PKG-INFO. A paper
   saying "we plan to release as open source" is intent, not a grant. No license
   means no permission to reuse or ship the code commercially. Also flag
   obsolete techniques, empty TODO sections, and genai-assisted content. For a
   writeup, separate the verified
   facts from the claims that lack a primary report ID, named target, or proof
   artifact. Answer the user's real question first, usually whether it matters
   for their stack or whether the money figure can be trusted. Give a direct
   no when it does not.
6. **Offer the fresh-note upgrade.** When the user picks it, research CURRENT
   technique status from primary sources, do not paraphrase the stale repo.
   Good sources: PortSwigger KB/labs, OWASP WSTG, vendor advisories (F5, Apache
   mailing lists), CVE announcements, recent parser/writeup research. Quote the
   version/date that proves each technique is still alive.
7. **Deliver the note as a durable file.** Write to `Documents/` with a clear
   name, then deliver a `MEDIA:` line plus a short chat summary. End with
   numbered next-step options; the user answers with picks like "1" or "2".

## Writeup credibility check

Apply when the shared link is an article rather than a repo. A writeup is a
lead, not evidence, until it survives these gates:

- Read the author's profile and recent post/article titles. A rotating
  "payout for bug class" shell with a different amount on each item is a
  content-farm signal, not proof of several paid reports.
- Require a primary anchor before citing a payout or chain as precedent: a
  platform report ID, a named target, a vendor page, attachments, or a dated
  disclosure. An amount in the article body alone stays a claim.
- Treat placeholder hostnames, anonymous example domains, duplicated code
  blocks, malformed HTTP snippets with spaces around `=`, and a stock-photo
  cover as template artifacts. Do not quote their payloads as a working PoC.
- Compare the article's own date with the social post date. Reposting an old
  writeup as a fresh find is a common aggregator pattern; say how old it is.
- When the user wants usable evidence, fetch the primary public reports or
  vendor disclosures and build the reference set from those, not from the
  shared summary. For OAuth ATO specifically, `hunt-oauth` already carries a
  verified case list; vet any NEW writeup here before adding it.
- Deliver a claim-versus-evidence table in chat, with each row's status tied
  to the marker that proves it. Unverified rows stay labelled unverified.

## Benchmark and replication writeups

When the shared article is a comparison (fuzzer A vs B, tool X vs Y), the post
almost always quotes only the favourable headline. Verify every number against
the article's own data before repeating it:

1. Curl the article HTML and look for empty chart containers. If charts are
   client-rendered, find the script the page loads (`<script src=article.js>`),
   fetch that JS, and parse the embedded dataset (for example
   `re.search(r'const DATA = (\{.*?\});', src, re.S)` then `json.loads`).
   Compute claims from those rows, not from the prose or rendered stat tiles.
2. Map each headline to its exact configuration. One library often has a
   "latest" build and a "known-vulnerable" build; the coverage ratio and the
   bug finding frequently come from different ones. Name the version beside
   every number in the verdict.
3. Reproduce the article's aggregation method before calling its number wrong.
   A stat tile may be `mean(per-config ratios)` where the reader assumes
   `ratio-of-means`. Read the rendering helpers and mirror the same reduction.
4. Check the dataset's status flags (`findings.pending`, "live draft", unfinished
   campaigns) before treating figures as final.
5. Check whether a claimed "found bug" is already public:
   `gh api repos/<org>/<repo>/issues/<n> --jq '{title,state,created_at,closed_at}'`.
   A closed, fixed issue is a rediscovery, not a new finding. Count
   harness-induced crashes separately from real ones; an ASan stack inside the
   library does not prove a library bug when the free site sits in generated
   harness code.
6. Deliver a claim-versus-evidence table with each row naming the exact config,
   the status, and what the post omitted (speed, cost, false positives, draft
   state). End with numbered next-step options.
7. Compare the preprint the post cites with the final proceedings abstract.
   Bug and patch counts are often updated before publication; name both
   versions in the verdict so a stale headline is not reported as current.

## Field-note shape

Principle (which two layers disagree) → payload blocks grouped by mechanism →
concrete 2025/2026 cases with version numbers → six-step workflow (scope,
baseline, identify layer, one variable at a time, compare status/length/body,
prove impact) → "do not report" list → source links. Include the validation
bar: a 200 alone is not a finding; show data read or state change in scope.

A worked 403-bypass note for 2026 is in `references/403-bypass-2026.md`.

## Pitfalls

- Never quote the post's headline count or category as fact. Count the actual
  entries in the fetched file.
- A stale repo is not automatically wrong, but flag the last commit age beside
  each obsolete payload ("%00", overlong UTF-8, TRACE).
- `vision_analyze` can hit a fair-share 429; do not conclude the image is empty.
- A post whose only link is "Comment KEYWORD for the repo/guide" has no payload
  in `facets` and usually no author self-reply either. The resource is almost
  always public and free elsewhere. Identify the real author from the screenshot
  or README (an app title bar or version string often names him), then state that
  the CTA is engagement bait, not a gate. Do not write the keyword as if it were
  a real access step.
- GitHub API via urllib gets 403 rate limit; switch to `gh api` immediately.
- CJK ideographs can slip into Indonesian prose while writing fast. Run
  `re.findall(r'[\u4e00-\u9fff]+', text)` and a dash check before delivering.
- Write casual Indonesian with no em-dash. Replace with comma or colon.
- Account-side work (login, install, submit) stays with the user; give steps.
- Never promote a secondary writeup's payout figure to data without a primary
  report ID or platform reward table, because aggregator headlines rotate the
  amount while keeping the same headline shell.
- Flag placeholder domains, duplicated code blocks, and malformed request
  snippets as unverified template artifacts, because those are generated
  filler, not request evidence.
- Do not merge a ratio from the current release with a bug from an older
  vulnerable release into one sentence. WHY: the numbers come from different
  dataset rows, and the combined claim overstates what either run showed.
- Treat client-rendered KPI tiles on a page labelled live draft as provisional.
  WHY: the tiles are computed at load time from a dataset that may still be
  changing, so the headline can lag the shipped rows.
