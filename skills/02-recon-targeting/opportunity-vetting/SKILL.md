---
name: opportunity-vetting
description: "Use when vetting shared posts, bounty terms, or liveness."
version: 1.5.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [research, crypto, airdrop, ambassador, creator-program, hackathon, grants, tier-list, x-twitter]
    related_skills: [blocked-page-recovery, airdrop-agent, promo-deal-verification]
---

# Opportunity Vetting & Tier Lists

The user drops one or more social posts (usually X) aggregating programs —
ambassador openings, creator programs, contests, hackathons, grants, bounties —
and asks which are worth it as a tier list on **newbie-friendliness + payment +
difficulty**, or simply what a shared post says and what its full requirements
are.
Those three are the fixed axes. The deliverable is a *verified* list: every
entry checked against its primary source, deduped, tiered, delivered both in
chat and as a durable file. Reposting the aggregator's reward figures without
verification is the failure mode this task exists to prevent.

## When to Use

Load when the user shares one or more links/posts (X, Telegram, newsletters)
that announce or aggregate earning opportunities — ambassador/creator
programs, contests, hackathons, grants/RFPs, bounties, quests — and asks which
are worth it, for a "tier list", for a checked/deduped version, or just to
open the details and read the full requirements ("cek isinya", "buka syarat
lengkapnya"). Also load for the follow-up "is this project still alive"
("masih hidup tidak") on a bounty already vetted: a liveness audit decides
whether the hunt is worth starting. A single bounty announcement pointing at a repo doc is in scope. Do NOT load for driving the `aa` CLI
itself (use `airdrop-agent`) or for recovering a single blocked page (use
`blocked-page-recovery`).

## Procedure

1. **Fetch the source posts** via the X mirror
   (`https://api.fxtwitter.com/<user>/status/<id>` — full text, expanded URLs,
   follower/engagement counts; screen name optional). Never fight x.com
   directly. Batch all posts in one execute_code/urllib loop and save the raw
   JSON to scratch so later rounds re-read instead of re-fetching. Fallbacks:
   blocked-page-recovery section 4. If the deep-dive post never names its
   target, read `tweet.quote` first: a quoted list post by the SAME author
   carries candidate names and links. Match by the figures in the post, then
   verify the target's own page; never treat the quote as the target's terms.
1b. **When a shared post promotes a tool/repo instead of an opportunity, give
   a tool verdict, not a tier list.** If the post also claims personal earnings,
   run the author-template check FIRST, before verifying any repo: Jina-read the
   bare profile (`r.jina.ai/https://x.com/<handle>`) and scan the last handful of
   posts for the same headline shell with a different money figure and item
   count. A rotating "$XK in N repos" across consecutive days is the verdict by
   itself; confirm the sibling posts via the mirror for exact dates and views,
   then lead with that evidence. Verify any named model or product against its
   primary docs before calling the claim fabricated, a future-dated name can be
   genuine.   Clone into scratch and verify the
   headline claim against the code: count real registry/tool entries rather
   than README badges, run the repo's own test suite in an environment where
   its paths resolve, and scan network-facing code for hardcoded secrets or
   phone-home calls.
   When a live demo needs an API key the user has not supplied, do not stop at
   "cannot verify" and do not claim a live test: prove endpoint reachability
   with a deliberately invalid key (a structured auth error means the endpoint
   is alive), then exercise the real parsing and writing code by
   monkeypatching its HTTP call with canned provider responses. Report the
   authenticated call as untested. Install into a scratch venv and invoke the
   script directly rather than running a setup.sh that hardcodes
   `~/.claude/skills` and a POSIX `.venv/bin/python` path; on Windows the
   interpreter is `.venv/Scripts/python.exe`. Expect a proxy-cloning tool to
   write only the resolved implementation source, never the proxy's own file,
   and derive expected rewritten import paths from the destination file's
   directory instead of guessing how many `../` levels to use. When mocking an
   Etherscan V2 `getsourcecode` response, wrap the serialized standard-json
   object in exactly ONE extra brace pair: two extra pairs send the parser
   down the monolithic-splitting path and silently yield one file instead of
   the full source map.
   For account-wide numeric claims ("N repos, +X stars"),
   enumerate with `gh api "users/<org>/repos?per_page=100&type=owner" --paginate`
   and sum stars in Python; never repeat the post's totals unverified. Sample
   the READMEs: a short file that is mostly external links is an INDEX, not
   self-contained documentation, so say the value is the links and extract
   them into a durable file. State plainly when the collection has zero items
   in the user's actual stack (e.g. no EVM/Solana content for a contract hunter).
   Skip oversized asset-heavy repos from a bulk clone, name the size, and offer
   cloud offload instead of filling local disk. Answer the user's real question
   first (do I need this for my stack?), then the evidence, then numbered
   next-step options. State directly when the answer is no; do not pad the
   verdict with generic praise.
2. **Dedupe across posts first.** Aggregator lists recycle the same programs
   across accounts; build the unique set and state "N program unik" up front.
3. **Verify every entry against its primary sources — never rank from the
   aggregator text alone.** Rewards there are partial ("pool not listed") and
   requirements are absent. Collect per program:
   - *Announcement tweet* → reward, payer, requirements, deadline.
   - *Application page/form* → the **real gates**. JS-heavy pages (Fillout,
     app dashboards) → Jina reader. Typeform needs neither: the served HTML
     embeds the full form definition, and `window.rendererData.form.fields`
     gives it as clean JSON (every question, choice, required flag, and
     track-branching statement) — open the form in the browser tool and
     `JSON.stringify` that path instead of clicking through screens. Raw-HTML
     parsing is possible but double-escaped and brittle. Google Forms → the `FB_PUBLIC_LOAD_DATA_`
     blob in the served HTML exposes every question and the intro terms
     (follower-count questions, KYC, country filters) — recipe in
     blocked-page-recovery section 4. Typeform → Jina reader returns ONLY the
     welcome screen; load the direct form URL in a browser and pull
     `JSON.stringify(window.rendererData.form.fields)` — that walks out every
     field (title, type, choices, `validations.required`, description) plus
     the track branching, i.e. the full question list per path, before
     anything is filled.
   - The program's own reply/thread often carries what the launch tweet lacks
     (apply link, payout tiers, campaign dates), pull it via
     `r.jina.ai/<post URL>`.
   - When the landing or application page gives NO reward figure, check the
     project's official X account before reporting "angka tak disebut":
     `r.jina.ai/https://x.com/<handle>` returns the pinned post and recent
     posts. Pool sizes and payout splits often live only there while the
     program page describes tasks and compliance. Attribute the figure to the
     official post and quote its date.
   - *Bug bounty programs: the platform page is the source, and the aggregator's
     reward range is routinely wrong.* Immunefi program pages are JS-heavy → the
     Jina reader (`r.jina.ai/https://immunefi.com/bug-bounty/<slug>/information/`)
     returns the tables cleanly; extract **Maximum Bounty**, **Live Since**, the
     per-severity reward table, the **payout asset** (a program "denominated in
     USD" can still pay in the project token), and **Total paid** when present.
     For Mantis use the JSON API, not the rendered page (see the Mantis bullet
     below); Sherlock pages carry the impacts/rewards table and the
     KYC-before-payout rule.     For an `audit-engine.sherlock.xyz` engagement, use
     the Audit Engine subsection of the same reference: invite-only entry, scope
     behind login, pool paid on Accepted findings, 2 Accepted issues plus a 20%
     Issues Ratio needed for payout. For an NDA question, use that reference's
     NDA-under-login subsection: the document is DocuSign-gated, so reconstruct
     obligations from public docs and the frontend bundle and leave login and
     signing to the operator. Intigriti publishes live status and exact tier
     tables in JSON, including for application-gated programs. Field-by-field
     recipe: `references/bounty-program-verification.md`.
   - *Self-hosted bounty paying a project token: also verify the operator.*
     Check domain age with RDAP, reconcile the legal entity across terms,
     whitepaper and investor deck, identify the founder, cross-check the PDFs'
     own numbers, verify the contract on Sourcify, date the PGP key, and check
     holder concentration. Recipe: `references/bounty-program-verification.md`
     → Operator / company legitimacy check. Report "real product" and "able
     to pay" as two separate verdicts.
   - *AI-agent / agentic-product bounties: mine the product's own security docs
     before recommending a hunt.* Fetch the public threat-model and defense-layer
     pages, the layer detail pages they link, and the program's
     scenario-to-severity examples. Two outputs: a concrete attack-surface map
     (which layer is a real boundary versus a tripwire, which env flags and
     policy exemptions can fail open) and an explicit "not a bug" exclusion
     list. The exclusions are the higher-value output, they stop the user
     burning time on patterns the program pre-rejects. Lead with scenarios
     whose tier is a fixed amount rather than "negotiated, up to $X".
     Recipe: `references/bounty-program-verification.md` → AI-agent bounty
     scoping.
   - A source-tree hash match (for example HEAD:contracts == audit commit:contracts) does NOT prove deployed bytecode matches the audited artifact. Deployment JSONs can be refreshed after a review even with zero source changes. Resolve diamond facets read-only from the authorized proxy, compute raw and metadata-normalized keccak256 of live code, and compare to both the audited-commit artifact and the post-audit HEAD artifact. Record which one matches. Drift that equals HEAD is a code-provenance or audit-coverage drift result, not by itself a vulnerability, and the facet addresses are usually not independently in scope.
  - An Immunefi program's "Audits" table can be stale and list fewer reports than the project's own audit index. Cross-check the project docs audit page before calling a target "unaudited" or scoring it as having no top-tier audit; the docs can add Certora/Cyfrin/Quantstamp reports absent from the Immunefi table. The program page's `knownIssues[]` array in the Next.js flight data is also more complete than the rendered, repeated tables: unescape `\"knownIssues\":[` and `raw_decode` it, and compare its last-updated date with the docs audit list before treating the blacklist as current.
  - Unknown fine print (prize currency, dates) → one targeted web_search on
     `<program name> rewards paid` / `creator program details`.
      - *Mantis bounties expose the full scope for free:* when given only the base `/bounties` page, fetch `https://mantis.inverse.finance/api/v1/bounties` first to enumerate `bounties[]` (each with `slug`, `status`, `rewards[]`, `assets[]`, `knownIssues[]`), then `.../api/v1/bounties/<slug>` for the full program terms (`inScopeRules`/`outOfScopeRules`). The slug is the last path segment of a bounty URL (`/bounties/<org>/<slug>`). Use the API instead of scraping the JS-rendered page, count only `assets` with `inScope: true` for the real scope size, and treat `status: "published"` as the accepting-reports signal when the UI sits on "Loading...". Classify `knownIssues[]` before quoting a bug count: they can be real disclosed bugs OR a blacklist of report patterns the program refuses to pay for. Taxonomy and API recipe in `references/bounty-program-verification.md`.
- *Listing/aggregator pages are stubs, not sources.* A shared listing link
     (e.g. hacklist.io) carries a title, one blurb, a deadline and an "Apply
     Now" — no real terms. Regex every `href=` out of the fetched HTML, keep
     the external ones, and fetch where they point: the organizer's own page
     (foundation site, devpost.com, application form). The blurb locates the
     program; it never settles eligibility.
   - *Rebuild a time-windowed aggregator digest from the platform's change
     feed, not from the post's headline counts.* `https://bugbounty.fyi/changes`
     and `/changes.rss` each cap at 100 events; walk `?page=2`, `?page=3` until
     timestamps pass the post's UTC window, dedupe overlapping rows, and regex
     `<li class="row-link...?</li>` for name, `datetime=`, pill class
     (`Launched`, `Back`, `Scope −`, `Raised`, `Closed`), platform and
     description. Check the post's counts against the feed and say plainly when
     "1 back open" or "1 big scope drop" maps to several rows. Why: the
     digest's counts are editorial while the feed holds multiple matching rows
     in the same window. Recipe in `references/bounty-program-verification.md`.
   - *DoraHacks-hosted programs: read the `/detail` route and the linked
     organizer rules thread, not only the base event URL.*
     `r.jina.ai/https://dorahacks.io/hackathon/<id>/detail` carries the rules,
     tiers and any dated update banner, such as a qualification-window
     extension. The base `/hackathon/<id>` redirects to `/build` and shows the
     event timeline, deadline and hacker/build counts, which double as a scale
     signal. Follow its "Official Program Rules and FAQ" link to the
     organizer's forum for payment rails, payout timing, anti-cheat and
     identity gates the event page omits. Attribute each date to the route
     that states it: an event submission deadline and a program qualification
     window can both be live and different.
   - *Discourse organizer forums: read the JSON endpoints, not the rendered
     topic.* `https://<host>/search.json?q=<term>` enumerates posts across the
     forum and `https://<host>/t/<id>.json` returns every reply with cooked
     HTML. A Jina or plain HTML read shows mostly the opening post, so staff
     answers to country, payout, KYC, eligibility and withdrawal questions
     hide in later replies. Batch a few targeted searches (`country`, `payout`,
     `withdraw`, `bank account`, `identity verification`) instead of guessing
     that no policy exists. When the only official answer routes the question
     to a private DM, keep the verdict as unconfirmed and hand the user a
     ready-to-send private message. Never turn silence or a private-channel
     referral into either "eligible" or "ineligible".
   - *Competitions: the rules page overrides the overview.* Devpost overviews
     summarize eligibility ("all countries, excluding standard exceptions")
     while `<host>/rules` carries the actual gates — org membership (e.g. the
     sponsor's partner network), named country exclusions, required submission
     fields, exact dates, credit expiry. Curl /rules directly; it is
     server-rendered. For "worth it for a newbie" odds on a recurring
     competition, the prior edition's funnel is the base rate (recipe in
     promo-deal-verification → references/competition-odds.md).
     *Client-side registration dialogs:* when a "Register" or "Apply" control
     is a `button` with `aria-haspopup="dialog"` / `data-slot="dialog-trigger"`
     and grepping the raw HTML finds no external href, do not report "no
     application link". Open the page in `browser_exec`, click the control,
     then read `document.querySelector('[role=dialog]').innerText` and map the
     fields with `[...d.querySelectorAll('input,textarea,select')].map(e =>
     ({name: e.name, type: e.type, placeholder: e.placeholder, required:
     e.required, label: e.labels?.[0]?.innerText}))`. The dialog's select option
     list is authoritative for target/category availability: compare
     "Fully Booked" markers in the landing cards with the dropdown before
     telling the operator a named target is still enterable. Consent checkboxes
     and identity gates (platform handles, country list) live only in the
     dialog, so include them in the verdict's hard gates.
     *Submission-portal reconnaissance*: the organizer's submit domain often
     publishes `/llms.txt` (deadline, gallery, rules routes in one file) and
     `/sitemap.xml` (per-entry detail URLs = an exact live field count);
     fetch both before quoting odds, and prefer the browser tool when those
     hosts sit behind Cloudflare/Vercel challenges. Recipe in
     promo-deal-verification → references/competition-odds.md.
   - *Item lists may live on another route.* A "Read All N" link on a grant
     page can be an `<a>` that navigates (check `location.href` after the
     click); read the destination as `main.innerText` slices when the text
     runs long (30K+ chars).
   - *Embedded CRM forms (GoHighLevel and similar):* a static landing page
     can hide the whole submission form behind an iframe. Grep the raw HTML
     for `<iframe data-src=` / `data-form-name` and for `<link rel=preconnect>`
     pointing at a CRM host, then curl the widget URL directly and strip
     `<script>`/`<style>` before extracting text. Every field label, input
     name, placeholder and required flag is in that server HTML: this is how
     to read what a report form collects (wallet address, handles, email,
     upload caps) without rendering or submitting anything. Note the host:
     data going to a third-party CRM rather than the project's own domain is
     a fact to state in the verdict.
4. **Rank on the three axes:**
   - **Newbie**: OK open (form / one piece of content) · GATE (KYC, follower
     count, country priority, platform score e.g. Sorsa) · NO KOL-only /
     2K+ followers.
   - **Payment**: USD/stablecoin from a credible payer (the platform itself,
     Superteam) beats project token / hashrate / points (mark *spekulatif*)
     beats no figure stated.
   - **Difficulty**: mudah = one action · sedang = routine content or product
     use · sulit = audience / referral / trading-volume performance.
5. **Group into S / A / B / C** from the axes — S = a real shot for a small
   account *and* credible pay. KOL-only entries go to C, never silently
   dropped. Sanity-check the unique count before presenting.
5b. **When the ask is whether the project is still alive, run the liveness
    audit** (recipe: `references/bounty-program-verification.md`): date the
    last human maintainer commit, merge and comment; separate those from bot
    pushes, scheduled CI and external hunter PRs; check the org's other repos
    and the project's site/social last-post dates; and verify deployment
    claims read-only on chain. Lead with the liveness verdict, then the
    evidence. An open bounty with no maintainer answering is not a payable
    opportunity.
    When asked to be notified when a bounty starts, read `status` and
    `timeframe.start` from the platform page or its list API FIRST and answer
    immediately if it is already live; install a monitor only for a genuinely
    pending program. Why: a standing reminder on an already-open program delays
    information the operator wanted now. Cantina's status payload field map is
    in `bugbounty-target-selection` → `references/program-recon-and-fork-tests.md`.
    When the operator asks to watch for a scope or reporting-channel change
    instead of a program start, a stale policy is a valid watch target: install
    a deterministic monitor rather than hand-checking. Keep the watch script
    under `~/AppData/Local/hermes/scripts/` and pass only its filename to
    `cronjob_manage` `monitor`, because an absolute path is rejected. Emit stable,
    timestamp-free lines so unchanged output suppresses the agent run, treat the
    first tick as baseline, and put the baseline facts in the job prompt so the
    diff has meaning. Why: the scheduler resolves script paths relative to its
    scripts directory and wakes the agent only when the monitored bytes change.
    For a fast pre-hunt screen before committing to the full audit, use the
    TVL and page-freshness recipe in
    `references/bounty-program-verification.md` → Target screening.
5c. **When asked to check or recheck your own earlier report, run a claim-diff,
    not a fresh audit.** Locate the artifact first: search conversation history
    for the topic, then search artifact filenames in Downloads, Telegram
    Desktop, Documents and `E:/audit` using near-spellings of the name the user
    gave, because a report label can live only in a filename or PDF body and
    message search then returns zero hits. Read the report, list each factual
    claim with its snapshot date, re-fetch every primary page it cites, and
    answer with the deltas plus a short "still valid" line.    Repeat the report's
    own disclaimer when it says it held ideas or verification rather than a
    proven bug. If two different near-miss labels both produce artifacts, do
    not commit to the first one: list both candidate targets and ask the
    operator which report they mean before writing the check. Close with
    numbered options for updating the document or starting the audit.
6. **Risk notes in every output**: for ambassador, creator and airdrop-style
   opportunities, anything requiring a deposit = walk away (legit programs say
   "no deposit"), but established bug-bounty platforms such as Cantina, Sherlock
   and Immunefi routinely charge a submission deposit, so read the platform's
   own rules before calling a deposit a red flag; token-denominated rewards
   flagged;
   card/KYC products often exclude Indonesia and don't publish country
   lists → "cek eligibility dulu"; for self-hosted programs the real country
   list often lives only in the main-site Terms of Use, never in the bounty
   policy page, so treat a post's list as partial until the ToS confirms it
   (recipe: `references/bounty-program-verification.md` → Self-hosted bounties:
   eligibility lives on the main site); a sub-campaign inside an aggregator entry
   may already be closed — grep the source page for deadline/status markers.
6b. **When a follow-up asks whether the operator already has qualifying work, audit local media before recommending creation from scratch.** Enumerate candidate files in likely directories with a date cut matching the rules' eligibility date, for example `find <dirs> -type f -newermt <YYYY-MM-DD> -printf ...`, filtering to the relevant media/project extensions. Run `ffprobe` on each for duration, codec and resolution. For visual qualification, extract ONE mid-point frame per file with ffmpeg and tile them into a single contact sheet (`xstack=inputs=N`), then run ONE `vision_analyze` on that sheet. This turns N image calls into one and makes "variations of one scene" versus "distinct story scenes" visible at a glance. Label mtime as generation/download date, not proof of completion date. A pile of short single-scene clips is material, not a complete work: state the editing still required for the track's complete-work rule instead of calling it eligible.

7. **Deliverable shape (user preferences):**
   - Chat: compact per-tier tables with columns
     `Program | Bayaran | Newbie | Sulit | Deadline (WIB)`; convert deadlines
     to WIB (PT is +15h in winter / +14h in summer); casual Indonesian
     register, program names/links stay as-is; minimal prose around them.
   - A one- or two-post "cek isinya" ask: a chat summary sectioned per program
     (what it pays, who can enter, deadline in WIB, hard gates) plus numbered
     next-step options; save the Documents markdown file for multi-program
     tier lists and for single-program deep dives that will span several
     follow-up turns, since the file is the durable evidence chain.
   - Urgent/soonest deadlines called out; close with numbered next-step
     options — the user answers with picks like "1", "1-3 berurutan".
   - When the user asks what to pick or for a plan: name the single program
     worth entering (a hard gate usually excludes the rest) and give a phased
     plan with the agent/user split per phase (read form → scope → build the
     required artifact → draft answers → user submits).
   - Save the full detail (all links, requirements, payout terms) as one
     markdown file in `C:\Users\TUF-GAMING\Documents` (durable; the scratch
     dir is pruned) and deliver it with a `MEDIA:` line. When a task produces
     several durable files, give each one its own `MEDIA:` line.
   - For a technical surface deep dive on a single asset (API or MCP endpoint),
     the durable file carries: the exact scope-export row with eligibility
     flags and `updated_at`, the read-only probe result, the auth boundary map,
     a tool table with impact hypotheses, a tripwire list, the program's
     do-not-report list, a validation bar, and a phased step split (agent does
     recon and drafts, operator does login and submission).
   - Tulis chat dan laporan tanpa em-dash; pakai koma atau titik dua. Berlaku
     juga untuk template resmi yang dikutip: tulis ulang dengan tanda hubung
     biasa dan arahkan pembaca ke sumber untuk tanda baca persisnya. Cek dengan
     `grep -n "—" <file>` sebelum mengirim laporan. Cek juga ideograf CJK yang
     terselip dari model (`grep -nP '[\x{4e00}-\x{9fff}]' <file>` atau regex
     Python `re.findall(r'[\u4e00-\u9fff]+', teks)`): frasa Mandarin bisa masuk
     ke tengah kalimat Indonesia saat menulis cepat, dan keduanya harus
     dibersihkan sebelum deliver.
8. **Account-side work stays with the user** (registration, KYC, login,
   public submission): produce step-by-step instructions for those parts, per
   the standing division of labor. The agent's share is drafts, verification,
   and evidence. When the operator reports an out-of-band step as done, verify
   the resulting artifact before starting dependent work (`ls -l` and `grep -c`
   for a config file, never open or print its contents): a reported "done" can mean only part of a
   command ran, and a missing secret silently blocks the next step. When the
   operator saved a secret through a GUI Save As, inspect the exact filename
   as well: typing the value into the filename field produces a file named
   `KEY=value.txt`, with the secret in the NAME and no secret in the CONTENT.
   Normalize by reading the value out of the filename into the canonical file
   without echoing it, then confirm with `grep -c` instead of reading the
   file into the conversation.

## Pitfalls

- Expand `lnkd.in/...` short links by fetching the response BODY and regexing
  `https?://...` out of it. A HEAD request returns 200 to the short URL with no
  redirect, so a status-only check wrongly concludes there is no destination.
  When an announcement's signup links all land on a login-gated dashboard,
  enumerate the plausible public `/apply`-style routes to make the negative
  auditable, then report the gate and tell the operator to check the account
  instead of guessing an application window.
- Don't state a reward the source doesn't state — "pool not listed" / "angka
  tak disebut" is the honest label. Inflated numbers poison the ranking.
- Announcing-account follower count + engagement (from the mirror JSON) is
  the fastest legitimacy signal for unknown projects, record it when
  judging, it catches obvious drive-by listings. For a bug-bounty post, also
  Jina-read the author's HackerOne/HackenProof profile: rank, reputation and
  **paid report count** show whether programs have actually paid them, a
  stronger signal than followers. It vouches for the announcement, never for
  the target's ability to pay.
- Check whether the target runs a paid KOL, referral or buy-to-earn program
  before treating a third-party bounty announcement as independent. A
  commission-per-referral page explains why accounts promote the project,
  including its bounty; state the incentive as context without claiming a
  specific announcer enrolled.
- Cross-check the operator's own social marketing claims (liquidity, holder
  counts, treasury sales) against live chain and DEX data and report them
  separately from the bounty terms. Decode X post dates from the snowflake ID
  when the mirror cannot load a status. For a time-windowed digest post, take
  `created_at` from the fxtwitter JSON as UTC; the timestamp rendered in an
  attached context or in the X UI is viewer-local and shifts the window. A figure that no longer matches the
  pools, or the operator discounting its own token for runway, is evidence
  about its cash position, not about scope or severity. A broad 30-day TVL decline across several blue-chip protocols is market-wide, not project-specific; compare peer protocols before treating it as a wind-down signal for one target.
- Check social channels directly instead of trusting a page load. `x.com/<handle>`
  returns a generic 200 shell even for a suspended account; the fxtwitter
  *user* endpoint returns the explicit `reason: "suspended"` and the account
  ID. Discord invite APIs need `?with_counts=true` to return member and online
  counts, and the Telegram `/s/<channel>` preview exposes subscriber count and
  message dates. Near-zero community activity is liveness evidence, not
  promotional noise. Recipes: `references/bounty-program-verification.md`.
- Verify a named founder is unique, not merely present. A common name with
  several unlinked profiles cannot anchor KYC, so keep "identified person"
  and "verified counterparty" as separate claims.
- Read the BODY of a linked long-form article before echoing the post's hook: a
  post hyping a huge repo stack linked an article whose own text said a small
  stack is enough and described a different business model. Report the
  contradiction side by side, each side labeled by source, instead of
  summarizing the hook.
- A project site can host sibling programs with different reward mechanics:
  an ambassador content pool, an affiliate sales commission, a token-denominated
  contributor program. Attribute every rate to its own page and never blend a
  sales commission into the ambassador figure. A footer or nav link to a
  sibling program is not the terms of the program being vetted.
- A form's gates are invisible from the tweet (follower minimums, KYC,
  country priority) — read the form before labeling anything newbie-friendly.
- For usage-threshold grants where pay depends on N monthly active users,
  price the threshold against the platform's own audience instead of the tier
  table. A large top tier is not an earning opportunity if the platform's
  following and participant counts are in the hundreds; say plainly that the
  hard part is acquiring qualified users on a small platform and that the
  entry tiers are micro-grants.
- Distinguish "not stated in the primary docs" from "does not exist". When a
  program page omits KYC, a country list, or an SLA, label it exactly that way
  and never upgrade it to "no KYC" or "no restrictions". Do not later suggest
  asking the operator about that same term as if a requirement had surfaced:
  it contradicts your own verdict and reads as a reversal to the user. If a
  follow-up question is worth asking, name the uncertainty plainly, for example
  whether payout processing adds an identity check that the policy never mentions.
- When a program's Terms omit the legal entity, check the Authenticode signature of the installer published on the vendor's own download page. The signer's subject is a primary-source entity claim and the signature date is freshness evidence; keep it separate from the product brand unless another source links them. A documented GitHub repo returning 404 does not end liveness: the official download page may still serve a freshly signed build.
- The overview summary is not the gate. An "open to all countries" contest can
  still require an org membership the user does not have (AWS Partner Network,
  MSP status) — read the rules before advising entry; when the gate excludes
  them, lead with "tidak eligible" instead of listing steps anyway.
- Two sources listing the same program may disagree (different reward
  figures, one cites a closed round) — prefer the primary announcement and
  note the discrepancy rather than averaging. Aggregator counts and totals
  are approximations too — report the primary page's own numbers. When the
  dispute is a deadline, check the primary page's own update or extension
  banner before telling the user the shared post is wrong: an aggregator
  detail page is a cached snapshot and can keep showing the old date after
  the organizer extends the window. An official platform announcement can also
  conflict with its own program page on the deadline. Record both dates with
  their sources, plan against the program page, and have the operator confirm
  the operative date in the account before spending time. Why: a launch post is
  written once and never corrected while the program page is what the
  submission portal uses.
- An aggregator can disagree with itself: its change feed may mark a program
  open again while its detail page still shows paused and zero assets until a
  second check lands. Settle status on the platform's live API and treat a
  submission timestamp after the reopen as proof that reports are accepted.
- A scope-add or reopening post is not permission to test. Open the platform's
  own engagement page and read its status banner, pause reason and resume date
  before recommending a hunt; a Bugcrowd engagement can list freshly added
  targets while displaying "This engagement has been paused". WHY: the
  aggregator's freshness field tracks the listing, not the triage state, and
  testing during a pause is a policy violation even when the targets are real.
- Aggregator bounty lists get the money wrong in both directions: ranges are
  understated against the platform's own maximum, and pool figures are
  invented or stale. Re-derive every figure from the platform page; never
  carry an aggregator's "up to" into the output table.
- A specific "up to $X for <severity>" figure in an aggregator post can come
  from a years-old announcement while the program's current policy pays case
  by case with no published table. Check whether the CURRENT program page
  states a numeric reward table; if it does not, label the figure as a
  historical ceiling and do not present it as guaranteed terms. WHY: repeating
  a press-release number as live policy overstates what a researcher can plan
  around.
- "Tier 1 / Tier 2" in a post is not automatically a severity or payout band.
  Read the program's scope export: on HackerOne, Tier 1/2/3 can be asset names
  with `asset_type: OTHER` while the post reads them as reward tiers. WHY: the
  wrong reading attaches a headline maximum to an asset the post never named.
- When a post quotes an endpoint exclusion ("X is excluded, Y stays in scope"),
  find which policy section it came from. If the named pattern sits under
  "known issues" or "ineligible issues", it is a pre-rejected report pattern,
  not a fresh opportunity: the technically accurate sentence still kills the
  obvious test. WHY: an aggregator can quote a blacklist accurately and still
  leave the reader thinking the surface is open.
- Treat the payout rail as a hard gate, not a footnote. Read the rules' verification and payment sections for tax-status, residency, identity and banking requirements before recommending entry: a bounty can pay only local self-employed or registered taxpayers through a domestic tax service, and a contest can require a W-8BEN plus a payment account that must be able to receive funds in the operator's country. "Open worldwide" on the landing page does not establish that a non-resident can actually be paid; when the rules defer non-resident instructions to a logged-in account, keep the verdict as unconfirmed and have the operator check it in their own account. WHY: recommending a program before checking how money leaves the platform sends the operator into KYC and account work for an unreachable payout.
- **Creator contests quote approximate retail value, not spendable cash.**
  Transcribe the official rules' prize table: separate the cash column from
  memberships, travel stipends, trophies and partner prizes, and label the
  headline "up to $X" as ARV when the cash maximum is lower. WHY: a post can
  advertise a $10,000 track award whose rules list $5,000 cash plus $2,200 of
  non-cash value, and repeating the headline overstates what a winner gets.
- For share-and-earn contest tracks, transcribe the full views-to-reward
  ladder, whether only the highest tier pays, the per-creator cap, the total
  pool and the exact views-count date. WHY: this ladder, not the grand prize,
  is the only path with a realistic expected value for an ordinary account;
  a finite pool or paid-boosted views can zero it out.
- An **audit competition** is not a per-bug bounty. One pool, whose size is
  set by the highest-severity valid finding, is split among all participating
  researchers by the platform's formula — so "bounty range" misstates both the
  amount and the odds. Check launch/end dates too: competitions are
  short-window, and a list can advertise one whose window is about to close.
  On bugbounty.fyi, the `Report on Cantina` line under At a glance is the
  detector for a contest pool rather than a per-bug bounty.
- Read the application form before scoping the work it demands: mandatory
  artifact fields set the build order (a required demo/repo link means the
  product must exist before submitting — build first, draft answers second),
  and the real funding options often live only in the form (a discrete $ tier
  ladder beats the aggregator's headline total as the honest "how much").
- When a submission requires naming a new project/product, verify the name
  first: `gh search repos <name>` for collisions and
  `curl -s -o /dev/null -w '%{http_code}' https://pypi.org/pypi/<name>/json`
  (404 = free on PyPI). A name an existing product or a popular repo already
  uses makes the entry read as a knockoff to reviewers.
- A tool/repo's marketing numbers (tool counts, benchmark percentages,
  "AI-powered") describe the product, not the interface you would actually
  integrate. Check the exposed surface separately before calling it usable.
- Before saying a program has no written scope, search the operator's scope
  store across roots, not just the notes folder. On this machine the per-program
  scopes are `E:/audit/<target>/scope*` and `Documents/*bounty*.md` are vetting
  notes. WHY: a note recording that the public scope is gated is evidence about
  the public page, not evidence that no local scope artifact exists, and a false
  negative sends the user back to account work for nothing.
- A repo-hosted bounty doc is a CLAIM, not the terms. Check when the doc was
  last committed and read the repo's security log before repeating phrases
  like "devnet, no funds at risk" — a doc that predates a logged mainnet launch
  is stale, and stale scope is ambiguous rather than settled.
- An X announcement can promote a self-hosted program whose own docs still say
  the programme has not opened and that the reporting address or PGP key will
  be published later. Read the doc's own status line and check for a live
  reporting channel before telling the user to hunt; lead with "belum open"
  and do not route vulnerability details through general support.
- Payout terms inside an OPEN pull request or an unanswered clarification
  issue are not program terms. Only merged docs count. State the ambiguity,
  advise asking the maintainer directly, and keep the written reply as the
  evidence a future session needs.
- When a program's own doc and its own security log disagree about deployment
  state, or one URL returns different terms via direct HTML vs Jina reader
  (payout asset, PGP fingerprint, SLA), treat the terms as unresolved. Resolve
  them with primary artifacts before stating them: verify the published PGP
  key's fingerprint with `gpg --show-keys --with-colons <file>`, check the
  search-engine snippet, and probe live endpoints or the contract. Report which
  version the artifacts corroborate, note the discrepancy, and never average
  the two or silently pick the flattering one.
- Read a same-name GitHub repo's README before treating it as the project's
  source. API Evangelist company profiles are automated third-party ratings
  whose README says "This is not our API"; calling one the company's repo
  invents a source-code claim. Conversely, its absence is not proof the
  project has no code.
- Verify a reported fund-loss incident read-only on-chain before repeating its
  amount or severity; report what RPC actually shows and label everything else
  as the reporter's claim. Recipe: `references/bounty-program-verification.md`.
- When a search surfaces a lawsuit or fraud headline about the project, read
  which side filed it and label allegations as allegations. A company suing a
  former executive over a node-sales scheme is the plaintiff, not the accused;
  reporting it as "project sued for fraud" invents a red flag.
- Before calling a site's price ticker or counter stale/fake, check the same
  figure against a primary price API in the same session. A BTC/ETH quote that
  looks years out of date can simply be the live feed value; call it wrong only
  when the API disagrees.
- A shared bounty post can be a retrospective payment announcement, not an open
  opportunity. Verify each claimed payout on its chain (explorer JSON API
  blocked? Jina-read the human transaction page, recipe in
  blocked-page-recovery section 4) and lead with the closed status before
  describing residual referral or integrator earnings, so the user does not
  start work on a program that no longer pays claims.
- AI red-team challenges can ban automated tooling outright while this user's
  normal workflow is agent-driven. Read the rules for a humans-only or
  manual-interaction gate and state it before suggesting an approach, since it
  decides whether their standard tooling is usable on the target at all.
- Bot pushes, scheduled CI runs and external hunter PRs are not maintainer
  activity. Date the last human maintainer commit, merge and comment and
  report that age against today: a repo full of fresh hunter PRs with a
  maintainer silent for weeks is a zombie, not a live program.
- A public explorer that labels itself "mainnet" can still read another
  cluster. Take one signature from its displayed activity and run
  `getTransaction` on both mainnet and devnet RPCs; a hit only on devnet means
  the label is wrong and every figure on that explorer is suspect.
- A burst of on-chain transactions whose timestamps fall inside a few minutes
  is not sustained usage. Read `blockTime` across the newest N signatures
  from `getSignaturesForAddress` before calling a program "active".
- A stored report is a snapshot, not the current terms. Re-fetch the primary
  pages before repeating its numbers: deposits, KYC gates, tier tables and
  submitted-findings counts are editable on live program pages, and a findings
  count can fall when reports are closed. WHY: a "check my report" answer that
  only paraphrases the old file presents stale terms as current fact.
- A name with zero conversation-history hits may be a near-miss of an agent or
  report label. Search artifact filenames with a near-spelling across Downloads,
  Telegram Desktop, Documents and `E:/audit` before concluding the report is
  absent. WHY: message search indexes dialogue text, while the label can exist
  only in a filename or PDF body.
- A self-hosted policy page with a "Last updated" age of a year or more,
  generic scope labels only (no addresses, repos or pinned commit), and payout
  handled directly by the team is not a plannable opportunity even when it
  prints a full reward table. Say plainly that the headline cannot be budgeted
  until scope and a reporting channel are published. WHY: a percentage-of-loss
  formula needs an asset base and a submission route the page does not supply.
- A post dated today can resurface a program whose rules repository has not
  moved in weeks. Date the last rules commit and compare it with the post
  before calling the program new. WHY: recency of the announcement is not
  recency of the terms or the code.
