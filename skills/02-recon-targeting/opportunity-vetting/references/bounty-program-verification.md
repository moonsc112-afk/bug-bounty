# Verifying Bug Bounty Programs (reward figures & status)

Shared posts aggregate bounties and routinely misquote them. Verify each
program against its platform page. All routes below were tested and work.

## Fast path: email-only, token-paying bounty

Run these in order and keep two verdicts separate throughout: "is there a real
software project?" and "can it be trusted to pay a claim?".

1. Mirror the announcement with fxtwitter status JSON; record author reach.
2. Fetch the security page BOTH directly and through Jina, then diff the payout
   asset, PGP fingerprint, reporting email and SLA (see variant check below).
3. Date the published PGP key with `gpg --show-keys --with-colons`.
4. Confirm deployment (`eth_getCode`) and quantify real liquidity with all
   GeckoTerminal pool pages plus CoinGecko simple price.
5. Sample ERC-20 Transfer logs in small RPC windows; report the sampled coverage.
6. Date the domain via RDAP and reconcile the legal entity across terms,
   whitepaper and investor deck.
7. Test founder identity uniqueness (LinkedIn duplicates, GitHub absence) and
   date the public trail with PullPush Reddit history.
8. Extract PDFs locally with `pypdf` and compare allocation tables and claims.
9. Read the project's own KOL/airdrop pages and compare official X claims with
   live chain figures.
10. Date social liveness: fxtwitter user endpoint, Discord `with_counts`,
    Telegram preview message dates.

## Direct fetch vs reader: catch variant content

A project's docs page can serve different content to a direct HTTP fetch and
to the Jina reader. In one case the direct fetch and search index showed
"paid in PAX token" with PGP fingerprint `1E95...`, while the reader returned
"paid in USDT", a different insurance-pool narrative, a different reporting
email and fingerprint `D5A2...`. Resolve it with an independent anchor:
download the published PGP key and compare its actual fingerprint with each
variant. Use the variant matching the real key and the direct fetch. Still
report the discrepancy, because unstable security terms are themselves a
signal. Never average the two payout assets into one figure.

## X/Twitter source

`https://api.fxtwitter.com/<user>/status/<id>` (screen name optional:
`/status/<id>`). Gives full text, author follower count, engagement. The
post's attached image often carries the real numbers — download
`media.all[].url` (add `?name=orig`) and read it; a screenshot of the
program page is a valid primary source for what the platform displayed.

## bugbounty.fyi change feed (reconstruct a digest window)

An aggregator post summarising "the last 24 hours" gives editorial counts,
not the full feed. Build the window from the change log:

- `https://bugbounty.fyi/changes` and `https://bugbounty.fyi/changes.rss` each
  return at most 100 events. Paginate the HTML with `?page=2`, `?page=3`, ...
  until the oldest `datetime=` predates the post's UTC window; dedupe rows
  because pages overlap.
- Parse each `<li class="row-link...?</li>` block with regex: program name from
  the `font-semibold after:absolute` anchor, timestamp from `datetime=`, change
  type from the `pill pill-*` class (`Launched`, `Back`, `Paused`, `Scope +`,
  `Scope −`, `Raised`, `Closed`), platform from the `.truncate` span, and the
  human description from the `leading-snug` paragraph.
- Take `created_at` from the fxtwitter status JSON as the window's UTC upper
  bound; the time shown in an attached post is viewer-local.
- Check the post's claims against the categories instead of trusting them: a
  "1 back open" can map to several Back rows and "1 big scope drop" to
  several Scope − rows in the same window. Report the ambiguity and keep named
  highlights separate from counted categories.

## Immunefi program pages

JS-heavy. Route through the Jina reader:

```
https://r.jina.ai/https://immunefi.com/bug-bounty/<slug>/information/
```

Extract, in order of importance:

| Field | Where it sits | Why |
| --- | --- | --- |
| Maximum Bounty | top summary card | the real ceiling; aggregators understate it |
| Reward tiers | per-severity table (Critical/High/Medium/Low, sometimes split "smart contract" vs "websites and applications") | the actual payout ladder |
| Payout asset | "provides rewards in **X** on **<chain>**" | "denominated in USD" ≠ paid in USD; project token = speculative |
| Live Since / dates | summary card | program age; a very recent date = fresh, less-audited surface |
| Total paid | summary card, when present | the only public proof the program actually pays |
| Assets in scope / known issues | scope tab | what is eligible; audit reports listed as known issues are dead ground |

Notes:
- Immunefi pages do not expose an explicit "accepting reports" badge through
  the reader; a live program page is the default state. A program that has
  paused or closed is usually delisted from `/bug-bounty/`.
- Reward text is often "% of funds directly affected, capped at $X, minimum
  $Y" — record the formula, not just the cap; the cap alone misleads.
- The rendered scope tab is not the full `assets[]` array. The raw Next.js HTML
  carries the complete set in the escaped `\"assets\":[{...}]` flight payload;
  unescape it and decode from that marker with `json.JSONDecoder().raw_decode()`.
  Compare the decoded count with the rendered rows and with the local guard. A
  page can render a subset and hide entire chains. Deliver the gap as an operator
  decision packet with chain, address, source URL and confidence; do not add the
  entries to the guard or test them until the operator approves. Label non-EVM
  entries and unresolved host chain ids instead of coercing them into
  `evm:<chain>:<address>` rules.

## HackerOne (hackerone.com/<team>)

The rendered program page is a JS shell for plain `urllib` fetches and for
`browser_exec` (body innerText can be ~100 chars), while the Jina reader
returns the full policy text including Rewards, severity examples and rules of
engagement:

```
https://r.jina.ai/https://hackerone.com/<team>
```

For scope, do not trust the rendered `/policy_scopes` table: a text extract can
show 7 rows while the page itself says "1-49 of 49". Fetch the platform's own
exports instead:

```
https://hackerone.com/teams/<team>/assets/download_csv.csv
https://hackerone.com/teams/<team>/assets/download_burp_project_file.json
```

Parse the CSV with `csv.DictReader`. Columns: `identifier`, `asset_type`,
`instruction`, `eligible_for_bounty`, `eligible_for_submission`,
`availability_requirement`, `confidentiality_requirement`,
`integrity_requirement`, `max_severity`, `system_tags`, `created_at`,
`updated_at`. Count only rows with both eligibility flags true. `max_severity:
critical` means an eligible asset may reach Critical, not that the program
pays a fixed Critical bounty. The Burp JSON carries include/exclude rules and
is the authoritative source for paths that are intentionally out.

Checks that change the verdict:

- **Asset named in a post**: grep `identifier` for the exact host or path
  before confirming the claim. A named endpoint can be its own `URL` asset
  added years after the program launched, rather than covered by a wildcard.
  Report that row's `updated_at` as the date the program added the asset.
- **"Tier N"**: look up the row. Tier 1/2/3 are commonly `OTHER` assets with no
  reward meaning. Do not convert them into payout bands. If the policy has no
  numeric reward table, say so and label any quoted dollar ceiling as history
  from the original announcement, with its date and source.
- **Known issues kill the easy path**: grep the policy text for the exact
  endpoint or pattern. A section saying access on dev stores is intentional
  while "paid stores remain in scope" is a blacklist, not a scope expansion.
  The post can be literally accurate and still describe ground the program
  refuses to pay. Pair it with the disclosed report that triggered the policy
  when one is available.
- Platform metadata beside the policy carries real gates: Signal requirement,
  response/triage/bounty times, total bounties paid and the severity reward
  table when published. An Early Access invite rule (N reports over two years
  plus a success-rate threshold) is a separate gate from the public program.

## Immunefi audit competitions

Different animal from a bug bounty. One pool, and the pool's size is decided
by the highest-severity valid finding (a table like Critical → full pool,
High → half, Medium → a third, none → a floor). It is then distributed among
all participating researchers per Immunefi's formula, not paid per bug.

Extract: the pool split (primary / all-stars / podium), the severity→pool
table, and the full timeline — announcement, **launch**, **competition ends**,
project resolution deadline, results, payment. The window between launch and
end is usually days to weeks; convert to WIB and call out the remaining time.
Codebase size (nSLOC) is stated and drives the workload estimate.

## Mantis (mantis.inverse.finance and siblings)

Go straight to the JSON API. The UI is client-rendered and can sit on
"Loading..." under a plain fetch, a text extractor, or a reader, while the API
always answers. From a browser tab on the host (or `curl`):

```
GET https://mantis.inverse.finance/api/v1/bounties                # list: bounties[], pagination
GET https://mantis.inverse.finance/api/v1/bounties/<slug>         # detail: one bounty object
```

In the browser tool the equivalent is
`js("fetch('/api/v1/bounties').then(r => r.json())")`. When the Mantis MCP is
connected, prefer `mcp__mantis__list_bounties` (filters: `status`, `asset_type`,
`reward_min`, `verified`, `q`, `updated_since`) and `mcp__mantis__get_bounty`
(`bountyIdOrSlug`) over hand-built HTTP calls. For shortlisting, query
`status: "published"` with `verified: true` first; `verified: false` may return
an empty set. These tools return the whole JSON inside one tool result, so save
the output to scratch and rank the bounties in Python instead of re-requesting
them.

`status: "published"` with `hiddenAt: null` is the authoritative
accepting-reports signal; `updatedAt` plays the status card's "Updated"
timestamp. Each `rewards[]` tier carries `minAmount` and `maxAmount` as DECIMAL
STRINGS, never `amount`: reading `r["amount"]` silently yields zero for every
tier and makes a funded program look unpaid. `assets[]` gives address
plus notes plus `inScope` (count only `inScope: true`: 2 means deep-dive
target, 90 means surfacing problem). `org.verified` / `verifiedAt` is the
legitimacy signal. `inScopeRules`, `outOfScopeRules`, `disclosureRules` and
`contactRules` carry the real program terms; read them before recommending a
target.

When the given URL is only `/bounties` with no slug, enumerate the list
endpoint first and use each `slug` for the detail calls. Guessed routes such
as `/api/bounties`, `/api/v1/findings` and `/api/v1/reports` return 404;
`/api/v1/bounties/<slug>/submissions` and `/api/v1/orgs` require auth.

### `knownIssues[]` is not a list of payable bugs

Classify every entry before answering "are there bugs there?":

| Kind | Signal | How to report it |
| --- | --- | --- |
| Real disclosed bug | concrete impact, affected contract, repro/PoC link, often a severity label | real vulnerability but already-known ground, a resubmission is a duplicate |
| Invalid-report blacklist | "by design", "deliberate", "not a valid report", "documented powers", "expected outcome" | not a bug, the program is pre-rejecting a pattern hunters misreport |
| Already-public or retired | incident disclosure with date, "shut down", "retired", "deprecated", revoked deployments | dead ground, do not propose a PoC |

Report the count per kind, not one raw total. Fifteen entries that are mostly
blacklist items mean zero claimable bugs; one medium known issue with a
reproduction test is still a real bug, just not payable to this researcher.
Pair the classification with the next step: hunt adjacent code, not the
listed ground.

## Sherlock (audits.sherlock.xyz)

Reader returns the "Impacts and rewards" table (severity × impact × reward,
often "% of funds affected, min/max") plus explicit **eligibility** and
**KYC and payment** sections. Two rules that recur: KYC is not needed to
submit but is required before payout; premature public disclosure can
disqualify a report. Out-of-scope sections name the trusted roles — read them
before proposing anything privileged.

When the Jina reader is unavailable but the raw Next.js HTML is served, the
full program JSON is embedded in the page. Find the escaped marker
`\\"payout\\":<amount>`, walk backward to the opening brace and forward to the
matching close, then `replace('\\"','"')` and `json.loads(...)`. The object
carries `payout`, `displayCurrency`, `liveSinceTimestamp`,
`lastUpdatedTimestamp`, `severities[].depositAmount`, and `scope.contracts` as
`[CHAIN, [entries]]` with `address` and `displayName`; `scope.urls` holds the
product links. Transcribe one `evm:<chain-id>:<address>` rule per entry into
the scope guard instead of regexing addresses from rendered text, which loses
the chain assignment.

### Audit Engine (audit-engine.sherlock.xyz) is a different product

Do not transfer contest or bug-bounty assumptions to Audit Engine. It has no
public program page: `/engagements` redirects to `/sign-in` and the engagement
card with repo, branch, commit, known issues, severity table and dates is
visible only to approved participants. Label that material "not publicly
verifiable", never "does not exist", and do not start PoC work before the
account state and scope are confirmed.

To make that negative auditable, probe the obvious public entry routes with
`curl -sL -o /dev/null -w '%{http_code} %{url_effective}'`: `/apply`,
`/researcher-application`, `/join`, `/researchers`, `/onboarding`, `/engage`
return 404 while `/engagements` redirects to sign-in. A "sign up below" or
"participate below" link in the announcement, including a LinkedIn
`lnkd.in/...` short link, resolves to that same gated engagements page rather
than a form. Fetch the short link's response body and regex `https?://` out of
it, because a HEAD request returns 200 with no `Location` redirect.

A platform status page (`status-audit-engine.sherlock.xyz`) reports Website
and API health only. It cannot settle whether applications or a specific
engagement are open, so label it infra health and never cite it as registration
status. When no public source settles the application-window question, the
honest answer is "check the account", not a guessed window.

Verify terms from the docs, not the announcement post:
`https://docs.sherlock.xyz/audit-engine/for-participants`,
`/how-audit-engine-works`, `/faq` and `/about-audit-engine`, plus
`https://sherlock.xyz/solutions/audit-engine` for product framing.

Rules that decide whether the engagement is worth entering:
- Entry is application or invitation. Only approved researchers see the
  engagement in their Engagements tab and can commit. KYC and NDA are required
  before commit on most engagements, once total, every member on a team account.
- The pool pays on Accepted findings, not per bug at a fixed price. Severity,
  uniqueness and speed can change the share.
- Payout eligibility: at least 2 Accepted issues and Issues Ratio >= 20%.
  Issues Ratio = Accepted / (Accepted + Dismissed); Neutral counts 0/0; a
  rewrite adds 0.5 to the denominator, max 5 rewrites; duplicates inherit the
  original verdict. Past Audit Contest history can be imported to seed the
  ratio. A dismissed report therefore costs real payout eligibility, so fewer
  well-evidenced reports beat volume.
- Payouts below the threshold are held, claimable for 12 months after the
  engagement ends, with no guarantee of a later chance to unlock them.
- Findings are exclusive to Audit Engine under the NDA. No public disclosure
  or cross-posting to another bounty during the restricted period.
- Judging is optimised for speed (AI judge -> Lead Judge -> protocol team), so
  accuracy is explicitly not guaranteed in complex cases. Use the preliminary
  AI verdict and Rewrite and Resubmit during the submission window.
- AI-assisted research is the intended mode; the docs run "AI-native security
  researchers" alongside frontier models and AI auditors, so this operator's
  agent-driven workflow is on-format here.

### Audit Engine NDA under login

When asked what the NDA is or to read its contents, do not claim to have read a
document you cannot open. The NDA is account-level and signed through DocuSign:
`/engagements` redirects to Clerk sign-in, the "Sign it now" action opens
DocuSign, and the signed PDF is served only by
`GET https://api-audit-engine.sherlock.xyz/v1/account/nda/document`, which
answers `401 authentication_required` without a session and has no document
available until the member signs. No public copy surfaced in the docs index or
the public reports repo, so reconstruct instead of hunting for one.

Reconstruct from two public sources and label the answer as a reconstruction:
- Official docs: `https://docs.sherlock.xyz/audit-engine/for-participants` and
  `/for-protocol-teams`. Append `.md` to any docs URL for clean markdown and
  read `llms.txt` / `llms-full.txt` for the index. These state that findings are
  exclusive to Audit Engine under the NDA, that in-scope findings must not go to
  public bug bounties, social channels or other vendors during the restricted
  period, that breaches can mean disqualification, revoked unpaid rewards, bans
  and legal action, and that even under Open Communication participants may
  share only their own performance after results publish, never vulnerability
  details or finding totals. Under Closed Communication they may not
  acknowledge the engagement or their participation without approved language.
- Frontend bundle schema descriptions (recipe in blocked-page-recovery section
  4b): the NDA is account-level, one signed envelope binds the whole account;
  status runs SENT -> PENDING (member signed, awaiting Sherlock's manual
  countersignature in DocuSign) -> COMPLETED (`nda_accepted` flips true), or
  DECLINED / VOIDED. A new envelope needs none or a latest DECLINED/VOIDED one.
  NDA API routes on the `api-audit-engine.sherlock.xyz` subdomain are
  `/v1/account/nda`, POST `/v1/account/nda/envelope` and
  `/v1/account/nda/document` for the signed PDF.

Login, OTP, DocuSign review and signing stay with the operator per the standing
division of labor. Give numbered steps to reach the DocuSign view (log in with
the signup email, open Engagements, press "Sign it now"), ask them to confirm
when the document is on screen, and only then read and summarize it. Never type
credentials or OTP, and never press the signature control. If the session ends
before the document is visible, report the reconstruction with its sources and
say plainly that the signed document itself was not read.

## HackenProof program pages

The Jina reader returns the policy prose but can drop the requirement chips
and the structured metadata. Fetch the raw HTML and decode its Nuxt payload:

1. Fetch with a browser User-Agent, take the first
   `<script type="application/json"[^>]*>(.*?)</script>` block and `json.loads`
   it.
2. The payload is devalue-encoded: a dict maps field names to integer indices
   into a surrounding flat array. Walk the arrays until a dict contains
   `minReputation`, then resolve each index by reading `payload[index]`.
   Key fields: `minReputation`, `kycRequired`, `kycRequiredForPayment`,
   `pocRequired`, `submissionFee` (null means no published fee, not unknown),
   `maxReward`, `rewards` (`critical_max` etc.), `startDate`, `endDate`,
   `repoLink`, `status` (`LIVE`), `publishedDate`, `submittedReports`,
   `totalRewards`, `sla`, `scopes`.
3. Cross-check the same gates in rendered HTML: grep the `<dt>Reputation</dt>`
   / `<dd>N points required</dd>` pairs plus `KYC`, `PoC` and `Contest is:`.
   Report both when they disagree.

For DualDefense audit contests, read the grading clauses before recommending
entry: only Critical pays, the pool is split equally among unique issues and
duplicates share an issue's allocation, a runnable PoC is required at
submission, and high impact can add floors such as more than 2% of protocol
TVL plus more than 1% of a user's deposit. Compute those floors against live
TVL before planning a PoC. If the token has no indexed DEX pair and the explorer
reports `price: false`, label the percentage-of-TVL floor unverifiable rather
than met or impossible. Why: a missing price feed is not a measurable asset
base. AI-generated reports without a runnable PoC are explicitly rejected, so
agent-drafted findings still need human review. Keep login, KYC and submission
with the operator.

## Intigriti (app.intigriti.com)

- Public index: `GET https://app.intigriti.com/api/core/public/programs` returns every listed program with `handle`, `companyHandle`, `status`, `confidentialityLevel`, `minBounty`/`maxBounty`, `lastUpdatedAt`, `lastSubmissionAt`, `twoFactorRequired`. In observed data `status: 3` marked open programs and `4` a program independently documented as paused; cross-check with `lastSubmissionAt` before declaring a program open. A submission timestamp later than a claimed reopen is the strongest public proof that reports are being accepted.
- Application-gated programs hide scope and policy until approval: their page redirects to `/programs/<company>/<handle>/preview/detail` and the badge reads Application. `confidentialityLevel: 2` marked the gated program, `4` the ordinary public ones. The only public detail is `GET /api/core/public/programs/<company>/<handle>/preview`, which contains `bountyTable.content.bountyRows` (score band -> min/max per asset tier), `awardRep`, `allowCollaboration`, `skipTriage`, `twoFactorRequired`, `programId`.
- Jina reader on app.intigriti.com returns cookie-consent boilerplate instead of program detail. Load the program page in a named browser tab and fetch the preview endpoint same-origin: `js("fetch('/api/core/public/programs/<company>/<handle>/preview').then(r=>r.text())")`. Direct cross-origin requests to the non-preview API path can 403, and guessed `/stats` routes 404; do not build the verdict on missing stats endpoints.
- Tier tables are per score band and per asset tier. The headline maximum applies only to the top score band of the top tier, so transcribe every band instead of repeating the aggregator's "up to".
- Gate: Intigriti policy now puts ID verification at submission creation for reward-eligible programs, not only at payout. Application approval gates scope visibility on top of that. Check both before promising the hunter can test or submit.
- A sibling VDP with no bounty often sits beside the paid program and may list the paid program's assets as out of scope for the VDP. Treat that list as a hunting hint only; re-read the paid program's own policy once the application is approved.
- The public detail page in a browser exposes more than the preview API. Read `document.body.innerText` for the per-asset Tier 2/Tier 3 map, the Rules of engagement block (required request header, alias email, automated tooling cap), the Activity feed (suspend/unsuspend events), and payout totals and response times. Do not infer liveness from the `status` field alone: a program can be suspended and unsuspended within hours and still show the open state at the moment you check.
- When the rules block and the policy prose give different request caps, enforce the lower one and report both. The live rules block is the platform's operational limit, while the prose can state a higher ceiling for what is merely "not accepted".
- Aggregator tables collapse per-asset tiers into one severity ladder. Use the preview API's `bountyRows[]` with `bountyTierId` together with the live page's asset-to-tier mapping; a wildcard sitting in Tier 3 does not earn the Tier 2 headline.

## Bugcrowd (bugcrowd.com/engagements/<slug>)

- The public engagement page renders without login. Open it in the browser and read the status block at the top before anything else: whether it says "In progress" or "This engagement has been paused", plus the pause timestamp, the stated resume date and the reason. A fresh scope addition or an active listing on bugbounty.fyi can coexist with a paused engagement, and testing during a pause violates the program policy. WHY: scope contents and triage state are separate fields, so an aggregator's freshness timestamp describes the listing, not whether reports are being accepted.
- Transcribe from that page: status and pause dates, the "No collaboration" badge, the P1-P4 reward chart, the mandatory traffic attribution header (for example `X-Bugcrowd-Ninja: <username>`), staging and alias account rules, and the disclosure policy. Note whether "Submit report" appears active and whether an invite/apply gate exists; leave the login itself to the operator.
- When the post names only the program, try `/engagements/<slug>`: the shorter `/<slug>` route redirects there and a wrong slug 404s.

## Target screening (TVL and page freshness)

A quick pass before the full liveness audit. Pair the platform's own date with
an independent money signal; neither alone decides go/no-go.

- DefiLlama protocol endpoint: `https://api.llama.fi/protocol/<slug>` returns
  a `tvl[]` series of `{date, totalLiquidityUSD}`. The last usable point is
  current TVL; find the point nearest `last.date - 30*86400` for the 30-day
  change. Record the series' own last date instead of assuming it is today.
  Try several plausible slugs (`pancakeswap-amm` and `pancakeswap`, `veda` and
  `veda-finance`): an HTTP 400 means wrong slug, not zero TVL.
- Immunefi reader output puts "Live Since" and "Last Updated" on separate
  lines after the label; grep with `-A3` to read the value. When several
  unrelated programs all show the same Last Updated date, treat it as a
  platform-wide sync, not evidence each program was actively revised.
- Mantis list API exposes `updatedAt` per bounty alongside `status`; use it
  rather than scraping the rendered status card.
- Interpret TVL change against peers: a 20-30% 30-day drop across several
  unrelated large protocols is a market move, not a wind-down. Only a drop far
  outside the peer range or a near-zero TVL justifies a skip. Near-zero TVL is
  decisive even when the program page was updated recently: page freshness and
  protocol size are separate verdicts.
- When the headline maximum is a percentage of assets at risk (for example
  "1% of assets at risk, min $X, max $Y"), compute the assets at risk required
  to reach the cap and compare with live TVL before calling the reward
  plannable. `https://api.llama.fi/protocol/<slug>` gives the TVL series and
  `https://api.llama.fi/protocols` enumerates candidate slugs. If the TVL entry
  describes a different product or chain set than the bounty, label the entity
  mapping as unconfirmed and use the figure only as a scale signal, never as
  proof the payout is impossible.
- A contest page that renders as a sub-1KB stub through the reader cannot
  settle dates. Reuse the last verified page data and label it with the date
  it was verified, rather than reporting "no data found".
- Pair TVL with scope size: a billion-dollar protocol with a huge, crowded
  surface is a harder hunt than a small protocol with two in-scope contracts.

## Self-hosted bounties: eligibility lives on the main site, not the policy page

A responsible-disclosure policy page can state rewards, scope and testing rules
while omitting country or geo eligibility entirely. Before telling the operator
he is eligible, read the operator's own Terms of Use on the main product domain:

- The policy doc and the Terms of Use are different pages on different hosts
  (`docs.<domain>` versus `www.<domain>`), and the Terms URL is often singular
  (`/term-of-use`, not `/terms`). Take the canonical URL from the signup page or
  footer link instead of guessing; a guessed `/terms` can 404.
- A JS-rendered Terms page can come back empty through the Jina reader. Fetch
  the raw HTML directly, strip tags in Python, unescape entities, then grep the
  visible text for `Restricted Jurisdictions`, `ELIGIBILITY`, `residing in`,
  `citizen of`, `VPN`, `18 years`, and each named country. The full list is in
  that HTML even when the reader sees nothing.
- Treat a social post's country list as partial until the Terms corroborate it.
  Quote the complete list and state plainly whether the operator's country is
  on it; a post naming five countries can hide a list three times longer.
- The ToS adds gates the policy never mentions (minimum age, one account only,
  no OFAC/UN sanctions, no VPN to bypass geo restrictions). Report the whole
  gate set, not just the country list.
- Date the Terms' own "Last Updated" separately from the policy doc's date and
  the sitemap `lastmod`; these pages are edited on different schedules.

## Self-hosted / repo-hosted bounties (doc lives in a GitHub repo)

No platform escrow, no published payout history, and no platform-enforced
severity contract. The announcement points at a Markdown file in a repo; that
file is a claim to verify, not the last word. Work in this order:

1. Fetch the raw doc (`raw.githubusercontent.com/<o>/<r>/<branch>/<path>`)
   and transcribe the reward tiers, pinned program ID / commit, in-scope paths
   and reporting rules. Compare every figure against the post and report any
   mismatch explicitly.
2. Date the terms:
   `GET https://api.github.com/repos/<o>/<r>/commits?path=<doc>&per_page=5`.
   Compare the doc's last commit with the repo's `pushed_at`. A doc that has
   not moved since before a documented deployment change is stale.
3. Cross-read the repo's own operational record: `SECURITY.md`, a security log
   (`docs/security-log.md`), known-issues file. A doc saying "devnet /
   pre-mainnet / no real funds at risk" while the security log records a
   mainnet launch with real deposits is an authoritative scope conflict.
   Surface both sides with each source labeled; do not pick one.
4. Listen to the repo's issue tracker:
   `https://api.github.com/search/issues?q=repo:<o>/<r> <term>&per_page=5`
   with terms like `bounty payment`, `unpaid`, `clarify scope`, `mainnet`.
   Unanswered clarification requests plus unmerged PRs are the tell: payout
   rails, KYC policy and AI-assisted-research policy proposed in an OPEN PR
   are NOT program terms. Only merged docs count.
5. Read repo shape from `GET https://api.github.com/repos/<o>/<r>` — stars,
   forks, open issues, `pushed_at`. A high fork/issue count against few stars
   can mean a report farm; record it as a signal, not a verdict.
6. If the post claims an on-chain loss of funds, verify the chain state
   read-only before repeating the claim (below).

### Project liveness audit ("masih hidup tidak")

An open bounty doc and a busy issue tracker do not mean the project is alive.
Separate machine activity from human maintainer activity, then say which one
you are reporting. Use authenticated `gh api` instead of anonymous
`api.github.com` calls — a liveness audit needs many calls, and the CLI's
token gives a far higher rate limit. `--jq` keeps each result to one line.

```bash
# Last commits on the default branch: date, author, subject
gh api "repos/<o>/<r>/commits?per_page=30" \
  --jq '.[] | [.sha[0:8], .commit.author.date, (.author.login // "?"), (.commit.message | split("\n")[0][:80])] | @tsv'
# Most recent merge and who merged it
gh api "search/issues?q=repo:<o>/<r>+is:pr+is:merged&sort=updated&order=desc&per_page=10" \
  --jq '.items[] | [.number, .closed_at, (.user.login//"?"), .title[:60]] | @tsv'
# Last maintainer comment: search by login, not by general repo activity
gh api "search/issues?q=repo:<o>/<r>+commenter:<maintainer>&sort=updated&order=desc&per_page=10" \
  --jq '.items[] | [.number, .updated_at, .state, .title[:60]] | @tsv'
# Size and authorship of the backlog
gh api "search/issues?q=repo:<o>/<r>+is:pr+is:open" --jq '.total_count'
gh api "repos/<o>/<r>/events?per_page=100" \
  --jq '.[] | [.created_at, .type, (.actor.login//"?"), (.payload.ref // .payload.action // "")] | @tsv'
# CI actor + conclusion: scheduled runs vs fork PRs awaiting approval
gh api "repos/<o>/<r>/actions/runs?per_page=25" \
  --jq '.workflow_runs[] | [.created_at, .name, (.actor.login//"?"), .event, (.head_branch//"?"), (.conclusion//"?")] | @tsv'
# Whole org: whether all repos went quiet together
gh api "orgs/<o>/repos?per_page=100" \
  --jq '.[] | [.name, .pushed_at, (.open_issues_count|tostring)] | @tsv'
```

Decision rules:
- Call it "maintainer alive" only on a recent human commit, merge or comment
  by the maintainer. A recent `pushed_at` from a bot branch, scheduled fuzz
  runs, `action_required` fork PRs and fresh hunter issues are all compatible
  with an absent maintainer — list them separately, never as signs of life.
- Bulk GitBook export commits and mass reverts are documentation sync, not
  maintainer work. Date the human merge or comment underneath them instead of
  counting the export wave as fresh development activity.
- Treat `WatchEvent` and `ForkEvent` entries in org events as public attention,
  not maintainer activity. They inflate an otherwise quiet repo.
- Probe a health endpoint twice, minutes apart. Increasing `uptime` with the
  same commit hash shows a stable recent deploy; a changed hash shows a redeploy.
  Neither alone is evidence of an incident.
- Compare the registry publish time of the newest package version with the
  repo's newest release. A newer npm or PyPI publish after an older release shows
  distribution continuing even when the source repo looks quiet.
- A high open-PR count with almost no merges is a backlog, not throughput.
  A scheduled workflow that keeps failing unattended is automation, not triage.
- Cross-check the project's own site/blog and social account last-post dates.
  A narrative pivot (new product, token, launchpad) while the audited code and
  deployed program are stale means the bounty scope is likely abandoned.
- A 404 on the docs' source-repo or one-line installer URL is not the end of
  the liveness audit. Read the project's own main site (routes like `/get-app`
  or `/download-app`; the bare `/download` often redirects to the homepage)
  for a desktop or binary installer hosted on its static CDN. Verify it
  read-only: `curl -sIL <url>` for status, `Content-Length`, `Last-Modified`,
  `ETag` and `x-amz-meta-sha256`, then stream the bytes through Python's
  `hashlib` to compare real SHA-256 and MD5 with those headers without writing
  the large file to disk. A matching header hash proves CDN integrity, and a
  recent `Last-Modified` is independent liveness evidence. Then download the
  installer to the operator's large-file drive and verify identity with
  `powershell.exe -NoProfile -Command "Get-AuthenticodeSignature -FilePath '<path>' |
  Format-List Status,StatusMessage; \$_.SignerCertificate | Format-List
  Subject,Issuer,NotBefore,NotAfter,Thumbprint"`. A valid signature plus a hash
  match closes both integrity and publisher identity; do not stop at the CDN
  hash when the download is going to be executed. The signer subject is often
  the first concrete legal entity available when the Terms name no company;
  record it as the signer of the official installer, not as proof that the
  signer and the product brand are the same legal entity without a separate
  source. State separately that a desktop build may not expose the CLI REPL or
  `audit_log` the docs describe, so PoC observability has to be adapted rather
  than assumed.
- When the project has no public repo, date its live operational endpoints
  instead: public audit-log event/batch counts and last event timestamp,
  published SDK package versions on npm/PyPI, contract bytecode via
  `eth_getCode`, and MCP/health endpoints. These prove infrastructure is
  running, which is separate from proving the program can pay. Report the two
  verdicts separately.
- Lead with the liveness verdict and its dates, then the chain evidence, then
  the implication for payout. Offer to hold off on the PoC until the
  maintainer confirms in writing.

### Read-only Solana claim verification

POST JSON-RPC to `https://api.mainnet-beta.solana.com` (or the devnet
endpoint). No wallet, no signing, no transactions sent.

- `getAccountInfo` on a program ID: an upgradeable program account holds
  `[u32 little-endian version][32-byte ProgramData pubkey]` = **36 bytes**.
  Slice the pubkey from `data[4:]`, never `data[1:]` — starting at byte 1
  yields a wrong base58 key with spurious leading `1`s and sends you chasing
  an account that does not exist. Decode the 32 bytes with base58, not as a
  base64 string.
- `getAccountInfo` on that ProgramData: `value: null` means the program was
  closed. A program account can still show `executable: true` while its
  ProgramData is gone; that combination is a dead program, not a live one, and
  is exactly what a BPF-loader `close` leaves behind.
- `getTransaction` on the reported close/upgrade signature with
  `encoding: "jsonParsed"` gives the actual instruction type, authority,
  recipient and `blockTime`. Decode the timestamp instead of trusting the
  date written in the report.
- Only figures confirmed this way get stated as fact; everything from the
  report remains a claim until confirmed.
- `getSignaturesForAddress` on the program ID measures usage, not just
  existence. Read `blockTime` for the newest N signatures: if all N fall
  inside a few minutes, call it a burst (a test run), not ongoing activity.
  `getBalance` on the vault addresses named in a fund-loss report confirms or
  refutes the locked amount without trusting the report's arithmetic.
- Cross-check any explorer that names a cluster: take a signature it displays
  and call `getTransaction` on both mainnet and devnet. A signature found only
  on devnet means the "mainnet" explorer actually reads devnet, so its TVL and
  validator counts are not evidence about mainnet.

```python
import json, urllib.request, base64
ALPHA = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
def b58(b):
    n = int.from_bytes(b, 'big'); s = ''
    while n:
        n, r = divmod(n, 58); s = ALPHA[r] + s
    return '1' * (len(b) - len(b.lstrip(b'\0'))) + s

def rpc(method, params, url='https://api.mainnet-beta.solana.com'):
    req = urllib.request.Request(
        url,
        data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(),
        headers={'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=25))

prog = '<program id>'
raw = base64.b64decode(rpc('getAccountInfo', [prog, {'encoding': 'base64'}])['result']['value']['data'][0])
programdata = b58(raw[4:])                       # 4-byte version, then 32-byte pubkey
print(programdata, rpc('getAccountInfo', [programdata])['result']['value'])
```

## Payout asset reality check (token-denominated bounties)

"Critical $10,000-$25,000 USD equivalent, paid in TOKEN" is a nominal figure,
not cash. Before ranking the program, check whether the token can actually be
sold:

1. Pull the contract address from the program's own terms and confirm the token
   is deployed read-only: POST `eth_getCode` with `["<address>", "latest"]` to
   a public chain RPC. A non-empty `result` confirms a contract exists; it says
   nothing about liquidity. If one public RPC rejects the request, retry with
   another public RPC endpoint rather than dropping the check.
2. Check the token's market page (CoinGecko etc.) for 24h volume and trading
   pairs. `$0.00` volume or "does not have any trading pairs" means a $25k
   reward is an illiquid token position, not $25k. Say this explicitly in the
   verdict instead of repeating the headline number. Then quantify the real
   market with the DEX pools API, not the market page alone:

   ```
   https://api.geckoterminal.com/api/v2/networks/<network_id>/tokens/<address>/pools?page=1
   ```

   Paginate while `links.next` exists. Sum `attributes.reserve_in_usd` across
   all pools for the addressable liquidity, and sum `attributes.volume_usd.h24`
   plus `transactions.h24.buys/sells` for actual activity. A total reserve of
   tens of dollars against a five-figure bounty is decisive on its own. Record
   the spread of `token_price_usd` across pools: a 10x spread means there is no
   unified market and no reliable conversion rate. A CoinGecko quote can stay
   high while every pool is empty, so treat the market-page price as an
   unverified quote, never as evidence the reward is cashable.

   A 404 from that per-token pools endpoint is not a failed fetch and not proof
   the recipe is wrong: a token with no indexed pools can answer 404 while its
   contract is deployed. Corroborate with the keyless
   `/api/v2/search/pools?query=<symbol>` route (zero results is the answer) and
   with the explorer token page's price and transaction count, then label the
   reward unpriceable instead of stopping at the HTTP status. A program that
   explicitly promises token quantity and schedule but not market value, with
   payout after a future launch, is unpriceable today: never convert its token
   count to USD or imply cash.
3. Cross-check an independent token-risk page and record its score and the
   concrete signals (liquidity, team, holder distribution). Label it as that
   site's assessment, not a proven fact.
4. Note payout mechanics separately: email-only submission, no platform escrow,
   empty hall of fame and no on-chain payout evidence mean there is no public
   proof the program pays. Keep this risk distinct from token liquidity and
   report both. To check payout activity read-only, POST `eth_getLogs` to a
   public RPC with the ERC-20 Transfer topic
   `0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef` and
   the token as `address`, decode `topics[1]`/`topics[2]` as addresses and
   `data` as uint256. Wide block ranges are often rejected by public RPCs, so
   sample many small windows (for example 2,000-block windows spread across
   ten days) and report the sampled coverage honestly; zero transfers in a
   10% sample is evidence of no *visible* distribution, not proof none ever
   happened. Confirm the token with `eth_call` on `name()` `0x06fdde03`,
   `symbol()` `0x95d89b41`, `decimals()` `0x313ce567` and `totalSupply()`
   `0x18160ddd`. Decode dynamic string returns by reading the offset word,
   then the length word, then the data at that offset; decoding from a fixed
   position returns null padding. A missing `owner()` just means no standard
   Ownable interface, not that no treasury exists.

## Operator / company legitimacy check (self-hosted bounties)

When the program lives on the project's own domain instead of a bounty
platform, verify the counterparty as well as the token. Keep two verdicts
separate: "is there a real software project?" and "can it be trusted to pay a
claim?". A live product and a named founder do not imply a payable bounty.

1. **Date the domain** with RDAP, no whois binary needed:
   `https://rdap.org/domain/<domain>` → `events[].eventAction == "registration"`.
   Record registrar and nameservers. Compare with the project's own "in
   production since" claim: a claim predating the domain is false. Earliest
   archive snapshot: `https://archive.org/wayback/available?url=<domain>&timestamp=<early-date>`.
2. **Reconcile the legal entity across documents.** Search terms/TnC,
   whitepaper and investor deck for "operator", "domiciled",
   "incorporation". Three jurisdictions for one entity (Cayman in terms,
   Singapore in the whitepaper, SG/BVI "planned" in the deck) with no entity
   name, registration number, registered address or named directors means no
   identifiable counterparty to claim against. State that; do not merge the
   jurisdictions into one. Read the Terms of Use PDF too: a service liability
   cap plus a party named only as "we" leaves no identifiable counterparty
   for a bounty claim. A service cap does not govern bounty awards, so report
   it as diligence context, never as a bounty term.
3. **Identify the humans.** `web_search "<project> founder LinkedIn"` and
   Jina-read the profile; record location and join date. A bare LinkedIn
   profile commonly returns an authwall through the reader: use search-result
   snippets for follower/connection counts and Jina-read individual public
   post URLs for dated content. Verify uniqueness, not just presence: a common
   name with dozens of unlinked profiles cannot serve as a KYC anchor. A
   Reddit/dev-post self-disclosure ("I am the builder and token deployer")
   dates the public trail. A whitepaper that says team identities are
   "available on request" while naming no founder, co-founder or advisor is
   a diligence gap, not a privacy virtue.
4. **Cross-check the investor PDFs.** Download whitepaper, deck and overview
   and extract locally with `pypdf` (`PdfReader(path).pages`, join
   `extract_text()`). Compare numeric claims across documents and against
   live data: token allocation tables, engine counts, advertised pool
   addresses. Conflicting tables in the project's own PDFs beat any single
   flattering figure. `web_extract` truncates long PDFs at 50K chars; parse
   locally for full text.
5. **Verify published code artifacts.** Query
   `https://sourcify.dev/server/v2/contract/<chainId>/<address>` for `match`
   and `verifiedAt`. The `repo.sourcify.dev/contracts/full_match/<chain>/<address>/metadata.json`
   path 404s because files are stored under a matchId directory, so a 404
   there does NOT disprove a "Sourcify full-match" claim. Correct any earlier
   tentative doubt when the API confirms it.
6. **Date the security key.** Download the published PGP key and read the
   `pub:` line's sixth colon field with `gpg --show-keys --with-colons <file>`
   (epoch seconds). A disclosure key minted minutes or hours after the bounty
   announcement is a process red flag for a security program.
7. **Check holder concentration**, not just supply. Aggregator token pages
   often publish a top-holders table; compare the largest holder's prefix with
   any "founder address" in the deck. Two-thirds of supply in five wallets
   confirms an insider-heavy allocation even when the whitepaper admits it in
   prose.
8. **Check GitHub provenance before calling a repo missing.** A repo named
   after the company can be an automated API Evangelist third-party profile;
   read its README first. Do not cite it as company source code, and do not
   infer from it that the project has no code.

### Social account and community liveness

- **Find the official X handle from the project's own site before guessing it.** Support or docs pages often list an "official domains" block with the exact X and Discord links. A guessed `@<project>` that returns `User not found` is not evidence of inactivity; resolve the handle from that block first, then read the fxtwitter user endpoint and recent posts.
- **X suspension is explicit at the user endpoint.** Fetch
  `https://api.fxtwitter.com/<handle>`: a suspended account returns
  `{"code":404,"message":"User is suspended","reason":"suspended","id":"..."}`,
  distinct from `User not found`. Decode the account creation date from the
  returned ID with `datetime.fromtimestamp(((int(id)>>22)+1288834974657)/1000,
  tz=UTC)`; an account created a day before it published large liquidity
  claims is itself a signal. A direct `x.com/<handle>` fetch returns 200 HTML
  for suspended accounts, so HTTP status proves nothing here.
- **Discord depth:** `https://discord.com/api/v10/invites/<code>?with_counts=true`
  returns `guild.name`, `approximate_member_count`,
  `approximate_presence_count` and `inviter.username`. Omitting
  `with_counts` leaves the member fields absent. A server with a few dozen
  members and one online is a dead community.
- **Telegram depth:** `https://t.me/s/<channel>` returns a public preview whose
  HTML carries `tgme_channel_info_counter` blocks (subscriber count) and
  `datetime="..."` attributes on recent messages. Parse the last messages'
  dates to date the most recent post; preview availability alone only proves
  the channel exists. A bare `@name` can be a personal contact account rather
  than a channel, and channel growth can be near zero over months.
- Instagram-style profile pages supply follower counts through search
  snippets; tiny follower counts alongside an aggressive KOL or airdrop
  campaign are worth reporting as context, not as proof of inability to pay.

### Promotion footprint and marketing-claim cross-checks

- **Reddit archive via PullPush.** Reddit's own pages and JSON endpoints can
  return 403 to automated reads. Fetch
  `https://api.pullpush.io/reddit/search/submission/?author=<user>&size=100`
  and the parallel `/comment/` route: the archive carries `created_utc`,
  `score`, `subreddit` and `selftext`. Sort ascending to date the account's
  first activity, then count near-identical posts per day. A burst of ten
  duplicate promotional submissions in one day, all score 1, is an aggressive
  manual campaign, not organic traction; an account with months of unrelated
  discussion is at least a pre-existing account.
- **Date X posts from the snowflake ID.** When a status cannot be fetched from
  the mirror, decode it:
  `datetime.fromtimestamp(((int(sid) >> 22) + 1288834974657)/1000, tz=UTC)`.
  Use the decoded date to order marketing claims against later chain data.
  Repeated mirror 404s on known status IDs plus a search snippet labelling a
  post as from a suspended account are a hint to check account liveness, not
  proof by themselves.
- **Compare claims to chain, not to each other.** Search the operator's own X
  account for liquidity, holder-count and treasury statements. An advertised
  "$X liquidity" that now resolves to a near-empty pool, or a post offering
  the token at a discount for runway, is a signal about the operator's cash
  position. Report it with the claim's date, the live figure that contradicts
  it, and a separate verdict from the bounty terms.
- **Paid promotion programs.** A KOL/referral page paying commission in the
  project token explains third-party promotion of the program, including
  bounty announcements. Record the program's existence and mechanics; do not
  assert that a particular announcer enrolled unless a link or disclosure
  proves it.

## AI-agent bounty scoping

Agentic-product bounties publish much of their threat model in product docs,
not only on the program page. Fetch the security/threat-model chapter, the
individual layer pages it links, and the program's classification examples
before suggesting where to hunt.

- Separate declared boundaries from detection tripwires. Docs that call a
  regex denylist a "tripwire" and a syscall or OS jail the "physical boundary"
  are telling you which layer is worth attacking and which failures another
  layer is expected to contain.
- Harvest the "what we do not protect" and out-of-scope sections into an
  explicit exclusion list in the verdict. Runtime-built payloads, user-confirmed
  transactions, deliberately enabled local capabilities and an assumed-compromised
  administrator are pre-rejected report patterns, not lead material.
- Trace every named bypass path: env kill switches, policy exemptions, audit
  overrides, handlers that skip the central gate. Each is a test hypothesis,
  but only counts when the report shows impact crossing an intended boundary,
  not that the switch merely exists.
- Use scenario-to-severity examples as the target spec. A headline ceiling can
  be negotiated with no guaranteed payout while lower tiers are fixed amounts;
  transcribe both and say plainly which figure can be planned around.
- A self-hosted agent bounty can link a source repo that returns 404 because
  it is private. Report "public source unavailable, docs and live endpoints
  only", not "no source code exists". Check sibling public repos for readable
  execution code before calling the surface docs-only.
- State the automation gate explicitly. A ban on high-volume or indiscriminate
  scanning is not a ban on agent-driven analysis, but say what the policy
  actually permits before planning a workflow.

### MCP endpoint as a bounty asset

When a post names an MCP URL as bounty-eligible, verify the exact row in the
platform's scope export first (on HackerOne the `identifier` can be the full
`https://host/mcp` as its own `URL` asset with `max_severity: critical`). Then
probe read-only, in this order:

1. `POST <mcp-url>` with a JSON-RPC `initialize` and headers
   `Content-Type: application/json`, `Accept: application/json, text/event-stream`.
   A `401` with `WWW-Authenticate: Bearer` and `{"error":"invalid_token"}`
   means the tool inventory is gated and `tools/list` cannot be fetched
   anonymously. Say so plainly; never present a guessed tool list as live.
2. Fetch OAuth discovery even when the MCP handshake is gated. These commonly
   answer 200 without credentials: `/.well-known/oauth-protected-resource`,
   `/.well-known/oauth-authorization-server`, `/.well-known/openid-configuration`.
   Transcribe `authorization_endpoint`, `token_endpoint`, `registration_endpoint`,
   `scopes_supported`, `grant_types_supported`,
   `code_challenge_methods_supported` and
   `token_endpoint_auth_methods_supported`. Dynamic client registration plus
   an auth method of `none` is a boundary to map, not by itself a finding.
3. If the official repo contains only a README with feature categories and no
   manifest or tool schemas, get a candidate tool list from public MCP
   registries (for example `manufact.com/leaderboard/<name>`, `mcpservers.org`,
   `mcp.so`) and label it as third-party observation, unverified against the
   live server. Do not promote registry tool names into confirmed scope. Date
   the repo with `gh api repos/<o>/<r> --jq '{pushed_at,size}'` and note a
   missing license as context, not as a verdict.
4. Map tools by impact: user-scoped reads (saved addresses, order history,
   tracking) are IDOR candidates; phone bind plus OTP verification is an ATO
   candidate; cart and checkout are state-change and financial-impact
   candidates; catalog reads are usually low-impact tripwires. State the
   validation bar: a 200 or a public metadata response is not a finding; show
   data read or state changed outside the intended account boundary using
   test accounts.
5. Mine the policy's "informative", "known issues" and out-of-scope sections
   into a do-not-report list. On commerce MCPs, promo abuse, cashback logic,
   referral abuse, rate limiting and brute force are commonly pre-rejected, so
   an OTP issue must demonstrate ATO rather than just repeated requests. Keep
   account-side work (login, OAuth consent, two test accounts, submission) with
   the operator.

## Output discipline

- Report the platform's own figures; when the aggregator disagrees, show both
  and label which is which.
- Flag the payout asset: stablecoin/USD > project token (mark *spekulatif*).
  For token payouts run the reality check above and report realisability, not
  just the headline figure.
- Cross-check the project's own compliance/security page against its changelog.
  A control listed as Live on one page and retired on the other is a docs
  contradiction; when the direction removes a control (dual approval, time
  lock, KYT), say which way it moved instead of averaging the two.
- When the escrow platform's program page and the project's own docs disagree
  on reward tiers, loss floors or submission channel, treat the platform page
  as authoritative for submission and flag the conflict before any deep work.
  A docs page pointing at a company email while the platform requires its own
  report thread removes escrow, so do not submit by email until the operator
  confirms. Date both pages: a newer project docs page does not override the
  platform that actually holds the funds.
- Compare the payout asset across the project's sibling programs. If grants or
  hackathon tracks pay USDT while the bug bounty pays the project token, the
  token choice is deliberate, not a technical constraint; state that.
- KYC-before-payout is the norm on Sherlock/Immunefi; note it as a gate, not
  a blocker.
- A short-window competition on a large codebase is a workload claim — pair
  it with the cloud-offload recommendation rather than a plain "go for it".
