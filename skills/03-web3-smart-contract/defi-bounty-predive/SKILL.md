---
name: defi-bounty-predive
description: "Use before DeFi audits: target go/no-go and bug patterns."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [bug-bounty, defi, target-selection, audit, solana]
    related_skills: [bounty-target-verdicts, evm-bounty-source-audit, bugbounty-target-selection, new-feature-bug-hunt]
---

# DeFi bounty pre-dive and pattern hit-list

> **Spoke of `evm-bounty-source-audit`, go/no-go stage only.** Run it before the audit to settle economics and pick a hit list, then continue in `evm-bounty-source-audit`. Do not hunt, harness or report from this file.

## When to Use

Load this before opening a DeFi/EVM or Solana token target's code: when
shortlisting a new bounty, when an existing verdict register has no entry for
the protocol, or when starting a fresh audit pass and needing an attack-order
shortlist. Do not use it to re-open a target already parked with evidence in
`bounty-target-verdicts` unless new code shipped.

Two decisions in one place: **is this target worth a session**, and **which
class to attack first once it is**. Consult `bounty-target-verdicts` first to
avoid a protocol already parked with evidence. Then apply this skill before
`evm-bounty-source-audit` (acquisition -> static -> fuzz campaign).

Concepts adapted from the `web3-audit` skill in `elementalsouls/Claude-BugHunter`
(skill text CC BY 4.0); rewritten and trimmed for this workspace.

## 1. Pre-dive economics: kill before you read

A session spent on a low-payout, heavily audited protocol is a lost session,
even if you find a real bug. Compute these numbers first.

**Hard kills**

- `max_realistic_payout = min(0.10 * TVL, program_cap)`. If under $10K, skip
  unless the target is a stepping stone for a named client.
- TVL below $500K with no high floor: the severity matrix pegs payout to a
  percentage of TVL, so even a valid Critical pays little.
- Two or more top-tier audits (Halborn, Trail of Bits, Cyfrin, OpenZeppelin)
  on a small, simple protocol: the cheap bugs are gone.
- Fewer than 500 LOC and a single A -> B -> C flow: attack surface too small.
- Pays only points / airdrop units with no published conversion: not a payout.
  Do not treat it as equivalent to a cash bounty.
- Finding requires the team or admin to act maliciously: most programs list
  centralization risk as out of scope or downgrade it. Check the brief.

**Soft kill**: current version audited by a top firm AND codebase over 500K
LOC. Expect tens of hours for maybe one finding; proceed only with a floor
over $50K and protocol-specific expertise.

**Scorecard (go at 6 or more of 10)**

| Signal | Points |
|---|---|
| TVL over $10M | +2 |
| Critical bounty at or above $50K | +2 |
| No top-tier audit of the current version | +2 |
| Deployed under 30 days ago (check code age, not listing age) | +1 |
| Protocol already hunted before | +1 |
| Source available with NatSpec comments | +1 |
| Upgradeable proxies (new surface, but check admin path) | +1 |

- Turn the headline cap into a real number before ranking. Pull DefiLlama
  `currentChainTvls` for chain-level TVL, then measure funds actually held by
  the in-scope contracts: take the collateral token addresses from the repo's
  deploy config JSONs and batch `eth_call` with selector `0x70a08231`
  (`balanceOf(address)`) for each token against every in-scope contract on that
  chain. Price the balances with
  `https://coins.llama.fi/prices/current/<llama-chain>:<address>`. Sum per
  contract and per chain; that is the `funds directly affected` base for a
  percentage reward formula. A program floor still pays when the percentage
  comes out below it, so report both the computed percentage and the floor.
  Why: repeating the advertised maximum overstates a target whose TVL and
  per-contract holdings are an order of magnitude smaller.

Read an existing audit's **scope-exclusion** section first. What the auditor
explicitly did not cover (oracles, governance, off-chain, frontend, admin) is
the highest-yield place to look.

- Build a **DO-NOT-REPORT list** from every acknowledged audit finding plus
  every impact the program policy excludes. Acknowledged residuals (timing,
  MEV, frozen-account edges) stay non-eligible even when reproducible.
  Re-reporting one burns the only submission that counts as first.
- Dedupe audit PDFs by extracted text and scope section, not by filename:
  versioned reports often repeat the same findings with a new date and final
  commit. Treat them as one report with several reviewed commits.
- Verify the deployed source against the LAST audited commit before calling a
  surface new. `git rev-parse <commit>:src/X.sol` versus
  `git rev-parse HEAD:src/X.sol` proves blob identity without a text diff. If
  the blobs match and every post-audit commit touched only tests, scripts or
  config, the shipped code is exactly the audited code and a code-level hunt
  is a dead end.
- An audit of a deployer or assembler that explicitly excludes the underlying
  stack is not evidence that the stack is clean. The exclusion sentence names
  the real unaudited contracts.
- Diff the cloned repo against the audit's file list and its final reviewed
  commit. Files in the repo but absent from that list, and commits after that
  hash, are the first places to look for genuinely new surface. Confirm a
  deployment record before treating an unaudited file as live.
- Establish a build/test baseline before calling anything a bug: compile with
  the pinned toolchain, then trace each failing fuzz test to its revert site.
  A failure caused by harness setup (oracle or mock never wired) is harness
  debt, not a contract finding. Say so explicitly and move on. For a Foundry
  repo that dies on duplicate `deployCode` definitions, work in a scratch copy:
  delete nested `lib/*/lib/forge-std` dirs and write an explicit `remappings.txt`
  listing every top-level lib prefix, because auto-detected remappings after
  the deletion can still omit the main dependency prefix.

## 2. The one rule

Read **every sibling function** of the one you are reviewing. If `vote()` has
a modifier, check `poke()`, `reset()`, `harvest()`. A missing modifier on a
sibling is a recurring Critical pattern. Same for a fast path: if one branch
returns early, check which state updates it skipped.

**An off-chain-only view that overstates health is not a payable finding by
itself.** Trace the server-authorised call to its on-chain state change and
attempt the unbacked borrow or withdrawal on a fork before investing. If the
state-changing path still reaches the real guard (for example a card-collection
entrypoint forwarding the account as borrower into `checkBorrow` ->
`InsufficientAccountLiquidity`), the observable impact stops at a failed user
transaction, which most programs exclude as griefing. Why: a view no
state-changing path trusts cannot move value, and an audit's out-of-scope
observation built on that view will be rejected as known. Also check the view's
control cases: if it passes for an account with no position at all, it is a
weak authorisation signal rather than a collateral bug.

## 3. Ten-class hit-list

A chain appearing in an Immunefi address list does not mean the core protocol is deployed there. Enumerate the actual asset descriptions per chain: a sidechain may list only `USDp`, `TokenP`, bridge, flashloan, and access-manager modules with no protocol diamond. Live core getters such as collateral lists, fee curves, oracle hyperparameters, caps, and surplus buffer cannot be read through an authorized target in that case. The absence of a repo config file is a scope-composition fact, not a recoverable local gap. For bridge tokens, read the in-scope `BridgeableTokenP` or `lz-USDp` getters directly: principal, fee rate, daily and global limits, isolate mode, balances, and recipient. A live zero fee rate on many chains is a published DoS precondition, not a loss-of-funds candidate.

Work down this list in order; the first four historically produce the most
Critical findings. Full variants and grep probes in
`references/pattern-catalog.md`.

1. **Accounting state desync** (rank 1): two variables meant to stay in sync;
   one path updates A but not B; a later read of both invents value.
2. **Access control**: missing modifier on a sibling, existence check where
   ownership was meant, `if` instead of `require`, uninitialized proxy.
3. **Incomplete code path**: a fast path or early return skips a refund,
   leaves a partial fill stuck, or bypasses a check the sibling enforces.
4. **Off-by-one / boundary**: check every `<` vs `<=`, `>` vs `>=`, rounding
   direction, and zero/empty/max cases.
5. **Oracle / price**: missing staleness check, no Pyth confidence interval,
   TWAP too short for the pool depth, single source, stale failover path.
6. **ERC-4626 vault**: near-empty vault share-price manipulation, share
   transfer that moves shares but not the linked stake/lock record.
7. **Reentrancy**: cross-function and read-only reentrancy through view
   functions called mid-state-change, plus ERC-777/hook callbacks.
8. **Flash loan**: the primitive is unchanged (borrow, distort price, drain,
   repay); look for composability assumptions that break under imbalance.
9. **Signature replay**: missing nonce, missing chain id, cross-delegation
   reuse.
10. **Proxy / upgrade**: storage collision, uninitialized implementation,
    `delegatecall` to user-controlled address.

## 4. Newer vectors to add to the pass

- **EIP-1153 transient storage**: `tload`/`tstore` values cached within a
  transaction can desync from persistent storage after an external call.
- **EIP-7702 / Pectra**: an EOA that delegated once can be re-delegated; audit
  signature reuse across delegations.
- **ERC-4337**: paymaster sponsorship without a strict sender allowlist drains
  on first call; bundler griefing.
- **LST/LRT depeg**: code that assumes a 1:1 peg while the oracle or market
  reflects a depeg breaks liquidation math.
- **Bridge legs**: proof replay across rollups, sequencer forced-inclusion
  edges. Simulate both endpoints, never one side.

## 5. Reporting discipline that affects payout

- A PoC must be a single command that proves impact, with an explicit assert
  on the drained balance, minted amount, or corrupted state. Multi-step manual
  setup invites a downgrade.
- Use the program's own severity matrix verbatim. Do not invent severities;
  most matrices gate on economic loss as a fraction of TVL.
- Before submitting, run `finding-validation-gate`-style gates: exploitable now,
  listed impact, in-scope asset, no privileged assumption, not already known,
  impact beyond "technically possible".

## Related skills

`bounty-target-verdicts` (already parked targets), `evm-bounty-source-audit`
(acquisition, trust-boundary audit, invariant campaigns),
`new-feature-bug-hunt` (code-age verification), `bugbounty-target-selection`
(rep and KYC gates), `solana-vulnerability-scanner` for the Solana leg.
