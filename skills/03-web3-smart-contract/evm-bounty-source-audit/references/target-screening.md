# Screening many programs down to one target

Use when a fresh hunt starts and the choice is among several live programs (a platform
list, a "freshly launched" feed, a new-scope announcement). The expensive mistakes are
target-side: investing days in code eight firms already combed, or in a repo whose scope
pin no longer matches what is deployed. Order: list triage -> saturation grading ->
source availability -> fresh-surface check -> commit.

## 1. List triage (minutes)

- Enumerate the platform list with its cheap fields. Sherlock: `/bug-bounties` cards
  link `/bug-bounties/<id>`; each card shows payout + "Last Updated" (a scope refresh
  is the freshest pre-inspection signal).
- Open only the shortlist, and open the right tabs: `?tab=details` (reward tiers,
  severity floors, trusted-roles clauses, eligibility, PoC requirement) and
  `?tab=scope`. The contract list lives behind the query param, not a text tab.
- Read the SCOPE SHAPE before anything else:
  - ~10-file repo list -> coverable in days; the whole surface can be read.
  - 400+-address deployed fleet -> a sweep project; only worth it with fleet tooling.
  - deployed-address list -> names the chains you must fork (Ethereum-only is cheap;
    several chains means cross-chain wiring/config is part of the surface).
- Client-rendered scope: when the program page has no public scope API, curl the HTML and parse the Next.js RSC payload — stitch every `self.__next_f.push([1,"..."])` string, unicode-unescape, then regex the asset objects (`identifier`, `inScope`, `notes`). The `notes` field often carries the contract name, so the result is both the scope list and the name map; verify the count against the program's stated number. The live program homepage is authoritative for rules and known-issue exclusions — a project's docs site may still name the previous platform.
- Cantina list recon without login: the JS bundles expose a plain REST endpoint `https://cantina.xyz/api/v0/opportunities?status=live&limit=100`. Find it by downloading `/_next/static/chunks/*.js` and grepping for `listOpportunities` to reach `path:"/api/v0/opportunities"`. The JSON carries `totalRewardPot`, `totalFindings`, `timeframe.start`, `submissionFee`, `kycRequired`. Grade saturation with `totalFindings / days_live`, not pot size.
- On Cantina the API can omit `assetGroups` and `rewards` entirely; scope and payout form are in the streamed instructions. After stitching the `self.__next_f.push` chunks, instructions appear as plain text after a chunk marker `N:T<hex>,...`; split at the next digit-colon-`T` or `[` marker, unescape `\n` and `\"`, then read the markdown. Never conclude "no reward tiers" from an empty API `rewards` field.
- Read the IN-SCOPE ASSET GROUP, not the program title: a perp/trading protocol may list only its website, app and API as in scope with zero contracts. Reclassify before it enters an SC shortlist. The inverse also happens: all websites and APIs explicitly out of scope, plus a long list of named prior audit reports that are out of scope. That named-issue list is the checklist to clear before paying a submission fee.
- When the program enumerates in-scope CONTRACT KEYS (deployment JSON field names, diamond facet names), diff that list against the repo's own deployment records before filing. A facet present in a deployment file but absent from the program's list is out of scope even when it is reachable through an in-scope parent address. Why: a bug isolated to that extra facet gets rejected as "source file not listed" after the submission fee is paid.
- Check instructions for clauses addressed to AI agents or automated tools. Some programs require independent verification of every function and address, demand disclosure of AI assistance, and state that a report without human verification is ineligible; treat that as a submission gate for agent-driven work, not as boilerplate.
- Verify deployed addresses with `cast call` on a public RPC before trusting a repo deployment JSON (read `ROUTER()`, `PRICE_REGISTRY()`, `owner()` on the relevant contract). A deterministic deployment often shares ONE address across many chains, so a single read covers the fleet. Do not claim a deployed-address mismatch until this check is done.
- Aggregator shortcut: `bugbounty.fyi` lists programs by launch/scope-change recency
  ("Fresh to hunt" = scope added in the last 30 days); shortlist there, verify on the
  platform page. A platform whose listing lands on a marketing page (no public list
  without login) means the operator's account is the gate -- skip scraping it.
- Note payout FLOORS, not just caps: a Critical tier with a stated minimum makes
  mechanism-level findings fileable even when live monetization is bounded. Trusted-role
  clauses ("protocol admins are trusted") kill admin-trust classes up front.

## 2. Audit-saturation grading (before cloning)

- Count engagements from the project's audits page + a search ("<protocol> audit
  report"): Zellic/Certora/ToB PDFs, a Sherlock/C4 contest, an invariant-fuzz repo
  (Recon-Fuzz style) each count. Eight firms + a contest + public fuzzing = the classic
  surface is picked clean; deprioritize regardless of payout.
- Read the repo's branch list as a saturation signal:

      git ls-remote --heads origin

  Branches named `*-audit*`, `*-yaudit-N*`, `*-sherlock-*` show continuous review.
  Fetching one shows what the last review changed:

      git fetch --depth 1 origin <branch>
      git tag br-<slug> FETCH_HEAD
      git diff --stat main br-<slug>

- If a contest covered the same code, read its scope list AND its published outcome --
  a "zero valid M/H" contest result means the base layer is strong; the bounty surface
  is whatever the contest did NOT cover (see section 4).

## 3. Scope pin vs repo vs deployed

- Clone (depth 1), then pin-check the bounty's scope commit:

      git fetch --depth 1 origin <scope-sha>
      git tag pin-<sha> FETCH_HEAD
      git diff --stat pin-<sha> HEAD

  Empty diff = scope pin IS current main. Non-empty = read the delta FIRST: it is both
  the freshest code and a "already fixed?" vetting source for later findings.
- `pushed_at` from the GitHub API is NOT the default branch's last commit -- any branch
  push bumps it, so "pushed 3 days ago" can sit on a main branch untouched for months.
  Trust the default branch's own commit date.
- A private/404 scope repo is NOT a blocker: pull the deployed, verified source instead.
  Probe availability per address first (Blockscout v2):

      GET https://eth.blockscout.com/api/v2/smart-contracts/{addr}

  -> `name`, `is_verified`, `implementations`. A proxy's `implementations[0]` is the
  real code -- pull that too. Check a handful of addresses before committing.

## 4. The fresh-surface check (the actual edge)

- Cross-check the last audit/contest's scope file list against the live bounty scope.
  Whatever is NEW -- a circuit breaker, yield wrapper, strategy contract, a post-audit
  deployment batch -- is the uncovered code and the reason to pick this target.
- Community/partner forks and changelogs state it outright ("added post audit",
  "needs further validation") -- grep them; those sentences are free leads.
- Rank by money-path coverage: new component x money in/out x no audit marker beats
  old component x anything.

## Calibration example

A $1M program with 8 audit engagements (including a contest and invariant fuzzing) =
skip -- the classic surface is picked clean. A $1M program whose audit contest predates
its live deployment, and whose current scope includes a component its own community
fork calls "added post audit", = pick -- even when the brand attracts competitors, the
post-audit component is uncovered code. The saturation grade and the fresh-surface
check are what separate the two; payout size alone does not.
