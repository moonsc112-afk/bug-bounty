# Curating bug-bounty writeup precedents

Use when building a payout/precedent corpus for negotiation, or a bug-class reading list.
Primary source: **bugbountyhunting.com** (community index, ~7.000 writeups, categories
including a Web3 section).

## 1. Get the corpus (don't scrape rendered HTML)

The site's `?q=<keyword>` is client-side search over ONE data array; the results are
NOT in the served HTML (the page shell is ~16 KB with no writeups).

- Fetch `https://www.bugbountyhunting.com/script.js` (large, ~1.4 MB).
- It begins with `var data = [ {"title": ..., "link": ...}, ... ];`.
- Parse from the first `[` after `var data`:
  `json.JSONDecoder().raw_decode(s[s.find('[', s.find('var data')):])`.
- Entries are `{title, link}` only. Filter by keyword on `title + link`
  (e.g. `web3`, `solana`, `audit`), then dedupe by `link`.

## 2. Extract payout amounts from titles

Order matters — check ETH before the generic "worth" pattern:

```
([\d][\d,\.]*)\s*ETH
worth\s+\$?\s*([\d][\d,\.]*)\s*([kKmM])?
\$\s*([\d][\d,\.]*)\s*([kKmM])?\s*(?:(?:bug\s+)?bounty|payout)
for\s+\$\s*([\d][\d,\.]*)
([\d][\d,\.]*)\s*([kKmM])\s*(?:(?:bug\s+)?bounty|payout)
```

Pitfalls:
- **TVL is not a bounty.** Reject `with $20 mil` / `$20 million` style mentions.
- `1M+50k` needs an explicit rule -> 1,050,000 (the generic pattern reads only `1M`).
- Titles are self-reported; many postmortems carry no amount at all. Keep the
  no-amount set separately as methodology reading.

## 3. Read in depth without flooding context

- Fetch each writeup once via `https://r.jina.ai/<url>` into scratch (works for
  medium / mirror.xyz / gist / github; x.com may hit a login wall).
- Delegate summarization to **parallel subagents** (`delegate_task`) with a JSON
  schema per item: `idx, title, link, payout, protocol, bug_class, root_cause,
  impact, severity, lesson, content_status`. Compile their JSON into one reference.
- Mark `content_status` = `ok` / `thin` / `blocked`; never invent detail for a
  blocked page — record the gap instead.

## 4. Pitfalls

- **mirror.xyz migrates to paragraph.com** and old posts 404, destroying the
  technical detail. Prefer GitHub/gist sources, or archive the page before it moves.
- **x.com/twitter threads truncate** at the login wall; use fxtwitter/vxtwitter or
  the Jina reader for the text, and treat payout claims there as unverified.
- Median disclosed payout is far more useful than the mean (power-law tail).

## 5. Output shape that works

Rank into **worth-it tiers** (payout + bug class + effort + relevance to the
user's stack), keep a status table of every source, and deliver as a markdown
reference; offer a PDF report on request.
