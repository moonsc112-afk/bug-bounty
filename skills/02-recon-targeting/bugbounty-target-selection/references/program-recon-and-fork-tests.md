# Program recon and deployed-contract fork tests

## HackenProof public program-list filters (no login)

When a `dashboard.hackenproof.com/user/programs?...` link redirects to login,
reproduce its gates on the public list:
`https://hackenproof.com/programs?kyc=false&reputation=<N>`. The Requirements
popup exposes KYC (Any/Yes/No), PoC, Reputation points required (Up to N) and
Submission fee (Up to N); the URL updates with the applied params. Do this for
read-only target recon instead of asking the operator to log in. Login and
submission remain the operator's own work.

Pitfall: the public result count includes FINISHED and PAUSED programs.
Classify every card by its status badge and shortlist only LIVE ones. A headline
count of 158 can mean 20 submittable bounties.

Pitfall: the Hidden Gems carousel above the results reuses the same card class
as the real list. Scope extraction to the results wrapper, not the whole page,
or the first ten cards are duplicates outside the filtered set.

Pitfall: the title link's `innerText` carries only the program name. Payout,
paid, submission count and updated date are sibling nodes inside the surrounding
`<article>`. Extract from the card root and read the `<dt>/<dd>` pairs, otherwise
every numeric field comes back empty.

Browser extraction pattern: results cards are `<article>` nodes inside the
results `<div class="_wrapper_...">`. Read name from `h3`, status from the badge
span, updated date and submissions from `<dt>/<dd>` pairs, up-to and paid from
the payout `<dl>`, tags from `ul[aria-label=Tags] li`. Paginate with
`button[aria-label="Page N"]` and poll until the card-slug set changes before
scraping each page. Append each page to a JSONL file and aggregate after the
last page so a timeout does not lose earlier pages.

Confirm each finalist's rep chip from raw HTML instead of trusting the filter:

```bash
curl -s -L -A 'Mozilla/5.0' "https://hackenproof.com/programs/<slug>" \
  | tr '\n' ' ' \
  | grep -oE '.{0,90}(points required|Reputation|KYC required|paid report).{0,90}' \
  | head -6
```

Pitfall: the filter cannot see free-text scope gates. Open the finalist page
and grep its rules for `KYC`, `paid report` and `access to the code` before
calling the program accessible.

## Immunefi explore-page JSON prefilter

`https://immunefi.com/bug-bounty/` embeds the whole program list as escaped JSON
in the HTML (`\"bounties\":[`). Extract with bracket matching, then unescape:

```python
key = '\\"bounties\\":['
i = h.find(key); start = i + len(key) - 1
# bracket-match from start, respecting quoted strings and escapes, to find end
s = h[start:end].replace('\\"', '"').replace('\\\\', '\\')
bounties = json.loads(s)
```

Per-program fields worth filtering on: `slug`, `project`, `launchDate`,
`updatedDate`, `kyc`, `maxBounty`, `proofOfConceptType`, `isPayToSubmit`,
`payToSubmitFeeUsdc`, `features`, `tags.language`, `tags.ecosystem`,
`performanceMetrics.totalPaidAmount`, `vaultBalance`, `pausedAt`,
`inviteOnly`. Use these to shortlist by code/program freshness, toolchain fit,
KYC, payout size and submission cost before opening individual information and
scope pages.

Pitfall: paginated third-party trackers show only a slice of programs and can
be a page behind. The explore-page JSON gives the full set in one fetch, so use
it first and reserve page-by-page reading for finalists.

Pitfall: `vaultBalance` and `totalPaidAmount` are often null. That means payout
history is not verifiable from this data; state that plainly instead of
implying a program pays just because it is listed on a strong platform.

## Fresh-program survey and escaped JSON snapshots

For a fast launched-recently survey, import the local `bugbounty_monitor.py` as a
module and call `parse_ssr_rows(fetch(SCAN_URL.format(plat[0], '')))` for every
platform. `PLATFORMS` entries are tuples, so use `plat[0]`; passing the tuple
to `.get` fails. Dedupe by slug before ranking.

Some platform pages, notably Sherlock bug-bounty pages, embed the full program
object in the HTML as escaped JSON. Find the blob around the escaped payout key
(`\\"payout\\":`), bracket-match it, then unescape `\\"` to `"`. The object
carries exact reward tiers, per-severity deposit amounts, update timestamps and
the complete scope address list with display names. Transcribe those addresses
into a scope-guard file instead of scraping the rendered table; the table may
be client-side and incomplete. Map network names such as `ETHEREUM` and
`ARBITRUM` to chain ids, put addresses only under In Scope, and keep reward and
policy prose under Special Rules.

Pitfall: a program's reward may be paid directly by the protocol in its own
token rather than from platform escrow. Name that counterparty and asset in the
vetting note; platform triage is not a payment guarantee.

## Cantina list API and streamed RSC payloads

Ranking a whole platform? Use its own list API rather than lazy-loaded cards.
The Cantina client calls `GET /api/v0/opportunities` on the same origin (empty
baseUrl):

```bash
curl -s 'https://cantina.xyz/api/v0/opportunities?status=live&limit=100'
```

That returns `groups` (currentBounties/currentCompetitions), aggregate stats and
`items[]`; `limit=100` returns all live programs, not the ten the UI first loads.
`kind` separates `public_bounty`, `private_bounty`, `public_contest`.

Discover the same endpoint on another Next.js app by extracting every
`<script src="/_next/static/chunks/...">` from the page, downloading the chunks
and grepping for the client method name (for example `listOpportunities`) to read
its `path:` and `method:`. Download with Python urllib, not a shell xargs loop:
App Router chunk paths contain parentheses from route groups and break `sh -c`.

A single bounty page carries the full program object in the streamed RSC payload:

```python
import re, json
chunks = re.findall(r'self\.__next_f\.push\(\[1,(".*?")\]\)', html, re.S)
blob = ''.join(json.loads(c) for c in chunks)
b = chr(92)
blob = blob.replace(b + '"', '"').replace(b + b, b)   # chunks can be double-escaped
```

Fields worth reading: `timeframe.start/end`, `status`, `totalFindings`,
`totalRewardPot`, `submissionFee`, `kycRequired`, `joined`, `createdAt`,
`assetGroups[].rewards[].maxReward` and `assetGroups[].outOfScope`.

Pitfall: rendered text alone can hide status. A page telling the researcher to
sign in can still be `status: live` with a start date years back. Read `status`
and `timeframe` from the payload or API before saying a bounty has not started.

Pitfall: when brace-matching an object out of an RSC blob, the nearest UUID
before the target key is often a nested object (company, asset group). Iterate
candidate starts backwards and keep the match whose text contains the key.

Pitfall: aggregate `maxReward` across in-scope asset groups and skip
`outOfScope: true`. Reading only `assetGroups[0]` reports empty tiers for
programs whose first group is the default out-of-scope group. Empty tiers in the
API mean unknown, not no payout; label them that way.

## Program rules in the streamed payload

The bounty object and its instruction text are separate stream chunks. Rules,
reward tables, out-of-scope lists and AI clauses arrive as plain-text chunks
marked `N:T<hex>,<text>` rather than as JSON strings, so the object-extraction
regex will not find them. Extract them from the unescaped blob with:

```python
parts = []
for m in re.finditer(r'\b(\d{1,4}):T[0-9a-f]+,', blob):
    start = m.end()
    nxt = re.search(r'\b\d{1,4}:[T\[]', blob[start:])
    end = start + (nxt.start() if nxt else len(blob) - start)
    parts.append(blob[start:end])
text = max(parts, key=len).replace(chr(92) + 'n', chr(10)).replace(chr(92) + '"', '"')
```

Pitfall: some programs expose no `assetGroups` or `rewards` in the API at all;
the only authoritative reward table is inside that instruction text. Search it
before calling a tier unknown or unpaid. Likewise the in-scope surface type comes
from asset group names/descriptions, not from the pot or the program title.

## Fork-test recipe for a deployed target

1. Pin a recent block and pick an archive-capable RPC. Verify with one
   `eth_getBalance` at the pinned block before writing any test. The public
   publicnode endpoint can refuse historical reads; a public archive endpoint
   such as `https://eth-mainnet.public.blastapi.io` answers without a key.
2. Pull verified source and ABI from Blockscout API v2
   (`https://eth.blockscout.com/api/v2/smart-contracts/<address>`). Read the
   exact function signatures, constants and epoch lengths from source. Never
   guess selectors or parameter order for the test interfaces.
3. Find funding sources from `https://eth.blockscout.com/api/v2/tokens/<addr>/holders`.
   Screen each candidate with `eth_getCode`: a top holder is often a contract
   with no plain `transfer`, so pranking it silently fails. Pick an EOA holding
   the token with a little native balance for gas.
4. Declare minimal Solidity interfaces in the test file and call the cheatcode
   interface at `0x7109709ECfa91a80626fF3989D68f67F5b1DD12D`. This avoids a
   forge-std install and keeps the harness self-contained.
5. Fund test users with `vm.prank(whale); token.transfer(user, amount)` followed
   by `approve` on the target. Do not patch storage slots when a whale transfer
   reproduces real balances.
6. Assert expected reverts with `try ... catch` on the pranked call. Custom-error
   selectors are easy to mistype on a first pass, and try/catch survives that.
7. For time-dependent logic, `vm.warp` to epoch boundaries computed from the
   contract's own epoch length, not arbitrary offsets. End-of-epoch accounting
   frequently needs one more deposit or checkpoint to advance `lastTokenTime`
   before the final epoch becomes claimable; warp past that boundary again.
8. Run `forge test -vv` after exporting the Foundry bin directory onto PATH,
   because the bare `forge` on this host is a different CLI. Keep the test
   project under the durable audit tree, not in a pruned scratch directory.
9. Write a TRACE file containing the RPC, pinned block, forge version, each
   test's purpose and result, and the exact remaining untested edges. Record a
   verified-negative with the test count so a later session does not repeat the
   same campaign.

Pitfall: keep optional `foundry.toml` keys minimal. Newer Foundry rejects a
string value for `cache` during config parsing, before any compilation starts.

Pitfall: a documented stale value in a contract is still a behaviour to verify,
not a dismissal. When source comments admit a limitation such as stale committed
balance or zero-supply epoch allocation, test whether an unprivileged actor can
turn it into a loss above the program's floor; if the failing fill or claim
reverts atomically, report it as a documented limitation rather than a payable
finding.

## Confirm a scope asset is Live before selecting it

An asset added to the scope page is not necessarily deployed. Check three
things: the scope entry's pinned repo (a private `*-dev` repository whose public
link 404s is a red flag), the protocol's own deployment manifests across every
listed network, and a deploy script that only *prepares* an address rather than
proving execution. Absence from every first-party manifest plus a private-repo
pin means the asset is "Latest audited": record it as not yet PoC-able and move
to the next finalist. A QA audit report for the file also does not establish
deployment. Third-party notes that call the change a scope delta with unknown
runtime identity are corroboration, not the primary source.

## Deployment-manifest addresses may be uninitialized implementations

Factory-based protocols publish implementation or template addresses in their
sdk deployment files. Before treating one as a fork target, read back a few
initializer-dependent getters (`name()`, `symbol()`, `owner()`, fee handler,
valuation handler, `asset()`, last request id). All-zero or empty returns mean
you are looking at an uninitialized implementation, not the stateful instance.
Why: the real per-fund proxy is created later by the factory and is the only
address that holds user funds. Find it from factory deployment events or the
protocol's fund registry, then repeat the state reads and the fork on that
proxy. Reading source from the implementation address stays valid; reading
state from it does not.
