---
name: bugbounty-target-selection
description: "Use when picking a bug-bounty target: verify rep gate."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [BugBounty, TargetSelection, Recon]
---

# Bug-Bounty Target Selection

Choosing WHERE to hunt matters more than hunting harder. A third-party list or
PDF draws you to a target; verify it on the platform BEFORE investing days.

## When to Use

Load this before starting work on any bug-bounty target, and whenever you are
tempted to invest in a program drawn from a list, PDF, or aggregator. Use it to
check the reputation gate, scope accessibility, and audit depth FIRST, so you
don't sink days into a target you cannot submit to or that is already audited.

## Start from the workspace's own work ledger

Check `references/campaign-ledger.md` first for targets already driven to a
verified negative, then confirm the on-disk artifacts still exist. Before
cloning or scouting any target, list `<audit-root>/<target>/` for a
`VERDICT*` or `*TRACE*.md` note, prior repo checkouts and PoC/harness files. A
parked verdict backed by invariant traces is a completed engagement: report it
instead of re-cloning or repeating the same campaign, and clean up any duplicate
checkout you created. If resuming that work, re-read the current program page
before relying on the old verdict — gates such as KYC can change after it was
written.

When asked which targets from a list have NOT been worked on, never answer from
recollection. Scan the Hermes session DB read-only, then corroborate with the
audit tree:

```python
import sqlite3
c = sqlite3.connect('file:C:/Users/<user>/AppData/Local/hermes/state.db?mode=ro', uri=True)
rows = c.execute('select m.session_id, m.role, m.content from messages m').fetchall()
# per target: case-insensitive aliases -> hit count, distinct sessions, sample user turns
```

Exclude the current session id from the DB scan before counting hits. The user's own list or question injects every target name into this session, so including it inflates every target to a recent hit and hides the real history. Identify the current session from the conversation's own messages, then group the remaining hits by session and role before corroborating with artifacts.

Follow with an inventory of the audit workspace (`E:/audit` on this host): a
cloned repo plus a PoC, harness or verdict note means the target was really
worked; one or two mentions inside a research PDF or an aggregator post mean
it was only scouted. Report the two buckets separately and name the artifact
that justifies each classification.

Use program-specific phrases when scanning, not bare brand words. Short or
common names generate substring false positives (`raac` inside an unrelated
Android class name, `exactly` as ordinary English), so corroborate every hit
with an artifact path before calling a target worked on.

## Query public report corpora before choosing a target

A disclosed-report corpus such as POJIA (https://cve.pojia.ai) is a fast
pre-filter for which bug classes and weaknesses have actually paid in a
program. Query it for discovery paths before scouting code, then apply the
gates below. The REST/MCP recipe, verification caveats and the live-stats
check live in `references/public-report-corpora.md`.

Treat the corpus as a lead source, not evidence. Annotations can be
model-generated and most corpora serve excerpts plus links, so open the
original report and carry the pattern forward only as a hypothesis. Verify the
corpus's own live stats endpoint instead of repeating counts from the post that
advertised it.

## Compare a long list on toolchain fit

When the ask is a comparison rather than a single pick, rank on four columns:
fit with the tools actually installed, gate and fee to submit, freshness versus
competition, and whether the payout mechanic pays the impact the operator cares
about. Put the per-row caveat beside the score: audit depth, KYC at payout,
submission fee, known-issues exclusions, mainnet-testing bans. Deliver the
matrix in chat plus one durable markdown file, then numbered next-step options.
When the operator answers that menu with several numbers or letters, execute every
selected item to completion in the same turn before replying, in the order given.
Write the deliverable in casual Indonesian without em-dash. Before delivering ANY
Indonesian artifact (comparison matrix, verdict, ledger note or result file),
grep the file for non-Latin characters, doubled words and leaked template or
placeholder syntax: generated Indonesian reports can leak stray CJK/Japanese
glyphs, duplicated tokens and leftover `${...}` fragments, and a broken
character in a reward figure or path makes the report look unreliable.

When the platform exposes its own list API, rank from that data instead of the
rendered cards. Derive `findings / days live` as a competition-saturation proxy,
then combine with freshness, pot size and the severity tiers that actually pay;
aggregate reward tiers over all in-scope asset groups. Present the score with the
caveat that a low finding rate can mean a hard or non-paying scope, not an open
field. Cantina's endpoint and the streamed-payload field map are in
`references/program-recon-and-fork-tests.md`.

## Read the in-scope surface type and AI clauses before ranking

Open the in-scope asset groups, not just the pot: a top-paying program can list
only website / web-app / API assets, which disqualifies a Solidity-only operator
regardless of reward size. Read each asset group's `outOfScope` flag and its
asset names/descriptions, then match the surface to the operator's toolchain
before scoring. Why: a large pot on a web-only scope wastes the whole deep-dive
budget.

Check the program rules for AI/automation eligibility clauses. Some programs
state that unverified AI-forwarded reports are spam, that the fee is forfeited
for them, that AI assistance must be disclosed, and that a finding without human
review is ineligible. Treat that as a fee-risk gate: keep PoCs local, verify every
function, address, code path and exploit step against deployed code, and require
human review before any submission. Why: the fee is non-refundable on those
programs, so an agent-drafted report can cost money and pay nothing.

Use an aggregator's one-line program metadata (rep requirement, PoC flag,
submission fee, submission count, total rewards) as a FAST PRE-FILTER across a
long list, then open the official program pages for the finalists. Aggregator
metadata is a bucket, never the last word: some slugs 404 or omit the gate, so
an absent field means unknown, not zero. On Immunefi the program JSON `features`
can expose `Pay to Submit` and `Pay to Mediate - No Free Mediations` even when the
public page shows no fee: quote exact aggregator amounts as caveats, not facts,
and treat no-free-mediation as an extra dispute cost. The same JSON carries an
`audits` array and `pocPerTypeAndSeverity`; use their counts as a fast
audit-depth and PoC-burden prefilter before opening every finalist page.
For the full Immunefi program list in one fetch, the HackenProof public
program-list filter recipe, escaped JSON snapshots on other platform pages, and
the deployed-contract fork-test recipe, see
`references/program-recon-and-fork-tests.md`.

## Verify the reputation gate on the PROGRAM PAGE, not a list

Third-party lists and PDFs publish stale/optimistic reputation requirements.
Always open the program page and read the real "Reputation N points required".
Verified example (Nov 2026, HackenProof) vs what the list claimed:

| Program | Real rep | List claimed |
|---|---|---|
| RedStone | 150 | ">50" |
| GMGN, Starknet Web&SC/Staking, XT, Gate US, Turbos, NAVI | 100 | ">50" |
| Rhea, Arcadia, WhiteBIT | 50 | "11-50" |

Your rep must be >= the requirement to submit. A missed gate = zero payout for
the whole engagement. Factor rep INTO target choice, not after.

Read the gate from raw HTML when the reader drops it: a Jina-rendered program
page can carry the full policy yet omit the sidebar requirement chips
(Reputation, identity, paid-report rules). Fetch the page directly and grep the
`<dt>...</dt><dd>...</dd>` pairs, for example the `<dt>Reputation</dt>` chip
followed by `50 points required`. Why: a gate absent from rendered text means
unknown, not "no gate", and it decides eligibility before any code work.

On HackenProof the same raw HTML carries a devalue-encoded Nuxt payload whose
fields are integer indices into a flat array; decode it to recover
`minReputation`, `kycRequired`, `pocRequired`, `submissionFee`, `maxReward`,
`startDate`, `endDate` and `repoLink` when the reader drops those chips. Recipe: in the opportunity-vetting skill's bounty-program-verification.md,
section "HackenProof program pages".

Treat a platform's KYC filter as a fast prefilter only, never as proof the
scope is open. A program can pass `kyc=false` while its Program Rules require
KYC plus at least one paid Medium-or-higher report to unlock the code. Grep the
finalist page text for `KYC`, `paid report`, `access to the code` and
`permission` before ranking it. Why: structured filter chips encode metadata,
while scope-access conditions live in free-text rules and can block every
submission until satisfied.

## Find the right program, and read what the reward mechanic rewards

- Program slugs follow the *program*, not the protocol: `<platform>/programs/<protocol>` is often a 404 because the deployment sits inside an umbrella program named after the chain or ecosystem. Search by chain/ecosystem name, then expand the scope table ("Show all targets") and read any **Additional Scope** clause — it frequently extends coverage to the docs' address-book link listing ALL production deployments, so the visible core list is only a subset.
- A retired paid bounty remains in aggregator lists and X roundups long after
  it stops paying. Read the program's own doc for "ended / no longer pays" and
  the platform changelog for paused or removed status before ranking an entry
  as available. A closed program with a referral tail is not a bounty.
- A reopen announcement is a lead, not a green light. Verify live status on the
  platform and confirm with a submission timestamp after the reopen; if the
  scope is hidden behind an application, park the target until approved rather
  than scouting blind.
- Read the reward mechanic as a hunting hint. A program defining the damage baseline in a specific way — e.g. "maximum reward = 10% of funds directly affected, calculated from the circuit breaker's maximum withdrawal limit; if the bug BYPASSES the circuit breaker, funds affected equals the TVL" — is telling you which bug class pays: anything that moves value out while skipping the rate limiter. Definitions like "significant freezing of funds for >1 year" also pay; read them as target classes, not fine print.
- Read the known-issues list before hunting (usually an `<org>/security` repo, e.g. `KNOWN_ISSUES.md`): your intended surface being absent from it is a reason to invest, and the *neighbourhood* of a disclosed issue is where variants live. The list often lives ON the platform page itself (e.g. Sherlock's "Previous Audits" section), scrape it there even if the linked repo 404s (private). When the program links audit PDFs as known issues, also read each report's conclusion and its paragraph about issues noticed outside audit scope: acknowledged residuals and out-of-scope observations are rejection-prone, so a report built on one must add a runnable, unprivileged exploit with quantified loss, not restate the auditor's note.
- Read the program's GRADING CLAUSES before deep work and pre-classify your candidate finding classes against them. The trusted-roles clause ("privileged roles are fully trusted... if any privileged role can harm the protocol or the users in any way, it's considered informational") zeroes out entire classes: admin-set oracles/NAV feeds, dormant admin-gated powers (bypass/lock functions), trusted-forwarder bypasses. Check each candidate: can a NON-privileged actor trigger it? If not, it is informational — do not invest or stake on it. For a live role-gated entry point, read the on-chain authority before deep work (Solmate-style `canCall(address(0), target, selector)` plus a couple of random EOAs). If every EOA is denied, a bug inside an admin/decoder component cannot pay by itself: the report must show that an unprivileged address GAINS that capability. Do not spend a stake on a component whose only gate cannot be crossed.
- When the platform program page and the project's own docs disagree on reward
  tiers or submission channel, treat the platform page (the escrow holder) as
  authoritative for submission and do not switch to the project's email until
  the discrepancy is resolved: an email route bypasses the escrow that made the
  target worth selecting in the first place. Record both versions with their
  modification dates and ask for written confirmation.
- Treat the program's own address book as a LOOKUP, not as scope, when the terms say so: a registry page can list retired, shut-down and migrated products beside live ones. Select contracts from the named live-product scope and confirm each candidate's production status before mapping its money flow.
- Fork-only evidence clauses pre-kill whole report classes. When the terms demand a fork of the deployed implementation at a recent block, a PoC on mocks, a local redeploy, or storage patched over a production address is invalid. Check also for a named on-chain victim, a control run without the bug, and a ban on impersonating governance or keepers to manufacture the condition, then price the extra fork work before committing.
- A minimum demonstrated-loss floor plus a percentage-of-loss cap (payouts only above a stated USD amount, capped at a fraction of loss, with no Medium/Low tiers) means the reward formula decides eligibility, not the severity label. Compute the funds at risk needed to clear the floor before choosing a bug class.
- Separate the platform from the payer. A platform-hosted program can still pay directly from the protocol in its own token while the platform only triages and mediates; escrow protection and payout liquidity are then different from a platform-paid bounty. Quote the token, chain and payer before ranking. Why: a large USD maximum in a volatile project token is not the same exposure as a stablecoin escrow.
- Price the submission against the plausible payout: Sherlock stake (~$250/report, refunded if valid), Cantina deposits that are refunded for valid AND legitimately invalid reports (slashed only for spam, low-effort/AI content or inflated severity, see `docs.cantina.security/researchers/participation/deposits`), against floors like the platforms' own minimum for a valid Critical. Look for "Deposit required" on the bounty page and never record a refundable deposit as a sunk fee.
- Compare the percentage-of-funds mechanic and the funds-at-risk needed to hit the cap, not only the advertised maximum: a 20% mechanic halves the required damage versus 10%, which changes which bug classes justify deep work.
- Economics + life-signs pre-check (deployment TVL vs payout mechanic; frontend banner/news) before any deep work — worked numbers and the full method live in the **evm-bounty-source-audit** skill's economics reference.

## Immunefi scope pages hide most in-scope instances

The visible asset table is only the core list. Click the `Show all` button and
extract every `a[href*="etherscan.io/address/"]`, dedupe by address, and walk up
to the card containing `Name` and `Added on`. The `Added on` dates reveal which
contracts came from the latest release. Then open the protocol's own
address-registry repo (`maple-labs/address-registry`, `address-registry.json` is
a good pattern): the program's \"all instances deployed from all factories\"
clause makes those live proxy instances in-scope even when absent from the 40-row
table. Verify new entries with `eth_getCode` on a public RPC
(`https://ethereum-rpc.publicnode.com` works when hosted RPCs return 403).

For EVM view calls without web3, compute selectors with
`Crypto.Hash.keccak(digest_bits=256)` and batch `eth_call` on publicnode. The
correct `totalAssets()` selector is `0x01e1d114`; do not rely on memorised
selectors. Comparing pool `totalAssets()` and strategy `assetsUnderManagement()`
separates funded instances from bootstrap-only (1 unit) deployments before
choosing where to hunt. For scopes with dozens of addresses across many chains,
use `references/multichain-scope-recon.md` to normalise the list and rank by TVL.

When a view returns a struct, ABI encoding gives EVERY field its own 32-byte word
regardless of how the struct is packed in storage. Read the field order from the
repo's deployment artifact (`deployments/<chain>/<Name>.json` in Hardhat/Foundry
projects) and decode one word per field, in order. Applying storage-packing
arithmetic to the returned hex produces plausible but wrong values, for example
a boolean flag read as false when it is true. Prefer those deployment artifacts
over explorer verified-source APIs when the explorer is gated: they carry the
proxy address, implementation address, constructor args and the full ABI.

## Fuzzing a funded instance: harness pattern that works here

Medusa accepts property functions WITH arguments; Echidna property mode does
not (`Test "..." has arguments, aborting`). Build two harnesses over the same
setup: a Medusa harness with `echidna_*()` entry points that take random args
and wrap risky calls in low-level `call`/`try` so expected reverts are not
counted as property failures, and an Echidna harness in `--test-mode assertion`
whose `fuzz*()` entry points end with `assert(invariant)`. Put privileged
entry points behind a small actor contract registered through the protocol's
own Globals/registry so no VM prank cheatcode is needed.

crytic-compile (used by both Medusa and Echidna) spawns `forge` from PATH. The
`~/bin` shim makes bare `forge` Foundry here; still assert `forge --version`
starts with `forge Version:` before a fuzz run, because a `manifest.yml` line
means the Atlassian CLI answered and compilation will fail.

## Commit messages are not proof of new code surface

A release message like "deploy X", "setup X market" or "upgrade auditor" usually
means deployment JSONs, OpenZeppelin manifest entries and config changes, not a
new `.sol` implementation. Before scoring a target as fresh code, list the files
each recent commit touched and check the source file's own history:

```bash
gh api --jq '.files[] | [.filename, .status] | @tsv' \
  "repos/<org>/<repo>/commits/<sha>"
gh api --jq '.[0] | [.commit.author.date, .sha[0:10], .commit.message] | @tsv' \
  "repos/<org>/<repo>/commits?path=contracts/<File>.sol&per_page=1"
```

Why: deploying existing code changes deployment artifacts on every release, so a
message-only freshness check turns a plain new listing into a false "unaudited
new code" claim. Newly deployed instances can still be a real edge, but classify
them as deployed-config surface, not unaudited source.

## Before claiming an area is unaudited, match hashes

Audit PDFs usually list a repo commit and per-file SHA256. Recompute those
hashes with `git show <commit>:<path> | sha256sum` before assuming coverage.
Then diff the audited file against the verified deployed source: a handful of
cosmetic lines (interface removed, public→external) still counts as direct
coverage. Also check the live authority: `getRolesWithCapability(target, selector)`
and `isCapabilityPublic(target, selector)` can show a whole component is
decommissioned (all capabilities revoked), which ends the hunt faster than
source review alone.

## Verify deployed source before trusting repo HEAD

Blockscout's API v2 (`https://<chain>.blockscout.com/api/v2/smart-contracts/<address>`)
returns verified `source_code`, `additional_sources`, compiler version, EVM
version, and `is_changed_bytecode` without an API key. On Etherscan-only chains
use `api.<domain>/api?module=contract&action=getsourcecode&address=...`.
Etherscan V2 uses the unified endpoint with `chainid` and `apikey` instead. Multi-file `SourceCode` arrives as a JSON string wrapped in one extra brace pair: strip the first and last character before `json.loads`, then read `sources`. Compare main contract files by basename; dependency files under `node_modules` show as missing if the local index excluded them, so a raw missing-file count is not evidence of a source mismatch.
Compare each returned file against repo HEAD after stripping comments and
whitespace. A repo can be far ahead of what is live: a Veda vault's decoder had
0/27 matching files (deployed version rejected compose messages and SVM CCIP;
HEAD supported both). Auditing HEAD then gives false confidence. `is_changed_bytecode=false`
only means bytecode was not changed after verification, not that repo HEAD is
the deployed version. When many files differ, compare the economic formulas
rather than the file count: a rename plus helper extraction can be a large diff
with identical fee math. For sanitizer/decoder code, a scan for unused `address`
parameters is not sufficient; separately scan address-typed fields inside
struct/bytes arguments and confirm each reaches the packed output.

If live bytecode differs in size from the locally compiled artifact, do not
report a source mismatch yet: read distinctive view functions and immutable
constants (`name()`, `symbol()`, `cap()`, fixed fee bps, role and lock getters)
with `eth_call` and compare them with the pinned source. Why: optimizer and
via-IR settings change deployed bytecode while leaving public state and logic
identical, so selector-level agreement is the cheaper provenance check.

## Bytes32 address halves in sanitizer outputs are left-aligned

When a decoder splits a `bytes32` recipient into two `address` halves via
`address(bytes20(bytes16(x)))` and `address(bytes20(bytes16(x << 128)))`,
the resulting address contains the 16 source bytes as its HIGH bytes with four
zero bytes appended. A test that constructs the `bytes32` by right-aligning an
`address` (`bytes32(uint256(uint160(a)))`) puts the value in the low bytes and
will see zeros in the first half. Left-align with `bytes32(uint256(uint160(a)) << 96)`
or assert against `address(bytes20(bytes16(original)))` instead of the raw
address.

## Mainnet-fork invariant suites need an archive RPC

Stateful invariant tests pinned to an old block fail on publicnode with
"Archive requests require a personal token". `https://eth-mainnet.public.blastapi.io`
answered archive `eth_getBalance` at block 25,523,119 without a key and ran the
suite to completion. Budget time: a 2-pool modular-strategy invariant run took
~400 seconds. Verify archive access with a single `eth_getBalance` at the pinned
block before launching the full campaign.

Event-log recon has per-RPC range caps that vary wildly: `https://arb1.arbitrum.io/rpc`
accepted a 2,000,000-block `eth_getLogs` window, while blastapi caps it at 10 blocks,
dRPC at 100, and Tenderly at 1,000; publicnode demands an archive token. Parallelise
wide scans with a thread pool and chunk to each provider's real cap. Etherscan V1
`module=logs` endpoints now return a deprecation notice; use V2.

For explorer logs, Blockscout v2 exposes
`/api/v2/addresses/<address>/logs?topic=<topic0>` with pagination via
`next_page_params` (`block_number`, `index`, `items_count`). Direct `urllib` fetches
can get 403 while the explorer HTML loads; retry with `curl -A 'Mozilla/5.0'
-H 'Referer: <explorer origin>'` or extract the address page through a text reader.
`base.blockscout.com` may 403 while `explorer.base.org` serves HTML, not the v2 API.
When a factory event names a proxy, read state from the proxy: SDK manifest
addresses are frequently uninitialized implementations returning zeros.

When a test helper creates a new pool it may overwrite an inherited
`poolManager` state variable (Maple's `_createPoolSharingStrategy` does). Cache
the original pool manager address before creating the second pool, or the
"other pool" assertions silently test the same pool twice.

## Before trusting an audit report, diff its final commit against HEAD

Published audit PDFs pin an audited commit and a final commit. Clone the repo
and run `git diff -w <audit-final> HEAD -- contracts`: formatting-only diffs
mean the report still applies; semantic diffs are fixes that landed after the
review (often the audit's own recommendations) or unaudited new logic. Name
exactly which findings were fixed before calling a surface "still open".

For Foundry repos on this host, bare `forge` is Foundry through the `~/bin`
shim; if it ever prints `15.1.0` or writes `manifest.yml`, the Atlassian CLI
answered: call `C:/Users/TUF-GAMING/.foundry/bin/forge.exe` directly. For repos
that omit `foundry.toml` and vendor libraries, clone the exact tagged
dependencies named in the repo or audit into `lib/` with git
(`git clone --depth 1 --branch <tag> <repo> lib/<dir>`) and write remappings for
`forge-std/` and `@openzeppelin/contracts/`. Set `via_ir = true` with the
optimizer when legacy tests hit stack-too-deep. Run `forge test --match-path
<file>` for the PoC after a baseline run: missing docs/config fixtures can fail
unrelated tests for filesystem reasons, which is not a finding. Maple-style repos use `modules/`
with git@github.com submodules: init with
`git -c url."https://github.com/".insteadOf=git@github.com: submodule update --init --recursive`
or compilation fails on missing imports. Run `forge test -q` as a baseline
before any PoC work. If `forge build` fails inside `script/` on stale helper
signatures, do not treat it as a blocker: `forge test --match-path <file>`
compiles src + test but not scripts and usually still runs. For an oversized
submodule, shallow clone with `--filter=blob:none --sparse` then
`git sparse-checkout set` only the directories the imports need.

## Verify audit depth from the repo before investing

Some repos ship per-deployment component-level audit gaps (for example
`deployments/addresses/<chain>/*.json` with `contractMetadata[*].auditGap`).
Aggregate the gap values across deployments and cross-reference components
marked `unaudited` or `state,selectors,auth` against the INSTANCES THAT HOLD
FUNDS. This is how fresh surfaces are found inside a codebase that looks
uniformly well-audited at the top level.

"Well-audited" = the repo ships audit PDFs or the protocol names established
firms (OtterSec, MoveBit, Veridise, Asymptotic, Trail of Bits, Sherlock, Hacken,
Zellic, CertiK, BlockSec) or has formal verification. Well-audited ~= verified
negatives. Check `find -iname '*audit*.pdf'`, an `/audits` docs page, a Security
section. Also read the program page's own audit statement: it may say the base
contracts are audited while the actual in-scope deployments are not. Treat
that as a claim, not a finding: pull the deployed source (Etherscan HTML
`data-csource`, Blockscout v2, or Sourcify) and byte-diff it against the repo
commit named in the audit PDF after stripping whitespace. A byte-match means
the code IS covered and kills the fresh-listing thesis; only a genuine diff
opens the hunt. Sui/Move protocols are
routinely audited (MoveBit/OtterSec/Veridise) - assume audited unless the repo
is fresh. Prefer fresh/less-audited: recently deployed V2s, new protocols, small
TVL, code the audits did not cover.

## Self-hosted / non-platform bounty programs

When a program uses its own landing page and form instead of Immunefi /
HackerOne / Sherlock / Cantina, there is no platform escrow, no published
payout history and no platform-enforced severity contract. Vet before deep
work:

- A severity guide saying "Critical = loss or theft of funds" is a
  CLASSIFICATION, not a payout promise. Search the launch thread, landing
  page, poster images and the form for an actual reward table or payout
  terms. If none exists anywhere, label it "no reward published" and do not
  imply it pays. Matching the user's loss-of-funds-only criterion is not
  enough when the payment commitment itself is missing.
- Verify the operating entity, not just the brand: WHOIS the old and new
  domains separately (a young product domain on a decades-old brand domain
  is normal, not proof of legitimacy), the parent's own press releases,
  company registries, and the site's Terms for regulator disclaimers. A
  public-company parent confirmed in a press release is a real signal. A
  "scam / withdrawal issues" write-up is not evidence until its BODY is read:
  such pages often just list transparency gaps (no SEC/FinCEN record,
  address mismatch, low traffic).
- Check what the report form costs the hunter: fields demanding a wallet
  address, handles and email mean personal data goes to whoever hosts that
  form, which may be a third-party CRM.

## Platform landscape (rep gates are HackenProof-specific)

- **HackenProof**: rep gates 50/100/150; curated (well-audited); scopes often
  KYC- or paid-report-gated (`hackenproof-public/*`).
- **Immunefi**: ~150 programs, NO reputation gate; KYC per program, PoC
  required, loss-of-funds focus. Breaks the rep deadlock.
- **Intigriti**: no reputation gate, but many programs are application gated:
  scope and policy stay hidden until approval, and the public programs API's
  `status`/`confidentialityLevel` is the live signal. ID verification is now
  required at submission creation for reward-eligible programs, not just at
  payout. Verify both before scouting code; recipe in the opportunity-vetting
  skill's bounty-program-verification reference.
- **Mantis**: no reputation gate, platform escrow, and orgs are marked
  `verified` by Mantis staff. Its published set can be very small, so enumerate
  every published/verified bounty instead of trusting aggregator lists; newer
  programs often carry precise loss-floor and fork-PoC grading clauses. Full
  API and field-name recipe lives in the opportunity-vetting skill, in its
  bounty-program-verification reference file.
- **Cantina**: ~47 programs, optional per-program deposit (commonly $50, refundable except spam/AI/inflated severity), KYC at join or at payout depending on the program. **Sherlock**: ~38,
  $250 stake. **Code4rena shut down (2026)**. Check Sherlock's `/contests` and
  `/bug-bounties` separately: contests can be empty while staked bug bounties
  are still live.
- Rep-gated out of good HackenProof targets -> pivot to a no-gate platform
  instead of grinding low-rep web2 for rep points.

## Reality check: "less audited" rarely coexists with "SC + high reward"

High-reward SC programs ARE the well-audited ones. In the rep<=100 band the
genuinely less-audited targets are web2/apps or small/zero-payout. If a target
seems to be all of {less-audited, SC, high-reward, accessible}, re-check - one
of those is usually false.

## Fresh code when every program is audited: hunt a competition

Competitions put NOT-yet-deployed code in scope for a fixed window - the only
target class that is genuinely less-audited, and a level playing field (first
valid finder wins; no reputation gate).

Discovery: `bbradar.io/contests` (calendar across platforms - check "live now"
first), `cantina.xyz/opportunities/competitions`, the Immunefi site's
audit-competition section, `codehawks.cyfrin.io`.

Mechanics to read off the competition page before investing:
- The pool is set by the highest valid severity and shared among all valid
  finders (e.g. Critical->$250k, High->$125k, Medium->$70k, Low->$30k), not
  paid per finder.
- A runnable PoC is required for EVERY report (no PoC = closed); KYC is
  required for payout; mid-contest fixes are often allowed.
- Read the PoC environment clause: if it demands a local devnet / real binaries,
  the slice matching your tooling (e.g. a Foundry test for the Solidity
  contracts) is the tractable part; the rest is heavy node/firmware work.
- Read the scope off the competition page's own Scope tab (Immunefi:
  `/audit-competition/<slug>/scope/`) - it pins the exact commit per repo and
  names the accepted PoC environments per component.
- Weigh difficulty BEFORE investing: a competition on a major chain's own core
  protocol draws hundreds of researchers plus tier-1 firms and the code is
  already audited many times over - a long shot for a solo hunter. Time-box one
  focused pass over the slice matching your tooling, then park it; smaller/newer
  protocols are where the field is thinner.

## Target vetting checklist (run before deep work)

1. Rep requirement on the program page <= my rep?
2. Scope accessible (not application-gated with hidden scope, KYC, or
   >=1-paid-report gated)?
3. Audit depth (repo PDFs / named firms)?
4. Payout history ($ paid > 0; $0 = unproven)?
5. Submission count and its delta between snapshots (a count climbing several reports per day means the easy surface is already picked over)?
6. Language matches my tooling? Verify from the program page's language tags AND the repo's file extension (.sol / .rs / .clar / .move / .cairo) - a protocol's name or an aggregator label can mislead (a "Solana LST" from the list was actually Clarity/Stacks). Run `gh api repos/<o>/<r>/languages` as well: a nominally Solidity repo can hide a large Vyper core that needs a separate compiler. Confirm the compiler and test runner before ranking the target: Cairo needs `scarb` plus a Starknet test runner, Substrate runtime work needs the `wasm32-unknown-unknown` rustup target, and Clarity needs its own toolchain. When one is absent, park with the named install and source-unlock conditions instead of reading source you cannot turn into a PoC.
7. Known issues / disclosed hacks excluded from scope? Read the list itself (a `security` repo, `KNOWN_ISSUES.md`), not just the fact that one exists.
8. Submission cost (stake/fee) priced against the plausible payout?

9. Grading clauses (trusted roles / severity formula / known-issues content) extracted and applied to your candidate classes?
10. For an on-chain target, every deployed address validated with `chain-scope-guard` against a transcribed program scope file, including the Additional Scope address book?
11. Public report corpus checked for the candidate class/program, discovery paths read, and annotations verified against the original report?
12. Every finalist scope asset confirmed DEPLOYED, not merely audited? An asset
    pinned to a private dev repo and absent from the first-party deployment
    manifests is a "Latest audited" item and cannot carry a fork PoC yet.
13. In-scope asset types match my toolchain (SC vs web/API), and the rules checked
    for AI/automation clauses, disclosure duties and fee-forfeiture terms?

Skip the target if (1) or (2) fails, or if (3) says well-audited AND (4) says $0.

## Verified-negative is a real outcome

Well-audited targets yield verified negatives (observed: 5 surfaces on one EVM
lending core, an LST, all clean). Record the negative, note the remaining
untested edge, and move on - do not keep grinding a target whose audits already
cover the code. The edge, if any, is the fresh / deployed-config surface, not
the audited library.

For an audit contest with a public prior audit report, transcribe its finding
table and map each candidate PoC to an accepted finding or a privileged-role
path before submitting. A runnable PoC that only reproduces an accepted finding
is a verified negative, not a payable report. Why: contest rules exclude known
issues and rogue privileged roles, so the technically correct exploit is ground
the program refuses to pay.

Time-box the DEEP phase: extract the grading clauses + map the money surface
FIRST (a few hours); if the clauses pre-kill your candidate classes and the
style is uniformly guarded (constructor/argument checks, Ceil/Floor rounding
conservatism, per-order limits, post-action HF sweeps), park after the
surface-map sweep instead of line-reading every seam. 30+ deep reads to zero
payable is a signal to stop, not to push harder; leave a findings ledger +
an upgrade watch (proxy impl-slot + public address-book hash on a cron) so new
deployments re-open the hunt cheaply.

## Post-hack rebuilds: the known hack is OUT of scope

A program launched after a hack targets the REBUILT code; the disclosed exploit
is excluded. The value is whether the fix is complete / has variants and whether
other logic is sound - not re-finding the public bug. The rebuilt repo is often
KYC-gated; the public upstream mirror is the pre-hack version.
