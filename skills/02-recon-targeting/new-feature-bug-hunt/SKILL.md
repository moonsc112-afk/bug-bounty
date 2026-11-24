---
name: new-feature-bug-hunt
description: "Use when hunting bugs in newly released features."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [BugBounty, Recon, NewFeature, Solana, EVM]
---

# Bug Hunting in New Features

Fresh features are where the bugs are: least review, most rushing, deadlines that
skip edge cases. The old app has been picked over by hundreds of hunters for
years; a feature released last week has been touched by almost nobody.

## When to Use

Load this when starting a hunt on a target that just shipped something — a new
program/deployment, an upgrade, a passed governance proposal, a new web feature,
or a newly added scope asset. Also use it whenever a program's changelog,
release notes, blog, JS bundle, or scope page changes.

**Surface routing:** the concrete workflow below (blockscout age check, fork PoC,
keccak signature diffs) is CHAIN-specific. For a web / REST API / OAuth / hosted
MCP target, the consistency question here still drives the hunt, but the recon
probe matrix, account handoff, and PoC harness live in **web-api-bounty-hunt** —
load that instead of applying the chain mechanics to a web surface.

## The one question that drives everything

For every new action that moves money or changes state, ask:

> Does the new feature follow the same rules as the old ones?

Same permissions, same checks, same ownership, same accounting, same pause,
same event shape. Usually somebody forgot exactly one. Find it.

## Workflow

1. **Discovery** — find what is new. Changelog, release notes, blog/announcement,
   scope page, JS bundle diff (web); new program ID / proxy impl / passed
   proposal / new deployment (chain).
   For web3 contests, read each platform's own live-competition page (Immunefi,
   Cantina, Sherlock, ...). A generic bounty aggregator RSS feed is dominated by
   web2 scope changes and will miss web3 launches — use it only as a secondary signal.
   **Verify the real age before investing — a platform's "launched <30d" / "New" /
   "New scope" badge dates the LISTING, not the CODE.** Two checks decide it, and
   one cost line decides whether it pays at all:
   - source-code scope: the GitHub API on the PINNED commits (`git log`,
     `api.github.com/repos/<org>/<repo>/commits/<sha>`) — a brand-new listing can
     pin a codebase years old and long since audited. Faster first pass: the repo
     object's `created_at`/`pushed_at`, plus any in-repo release manifest
     (`VERSIONS`, RELEASES.md) mapping version -> commit -> first-distribution
     date; that dates the code without needing the pinned sha. When the code IS
     fresh, enter through the component named in the newest release-prep commit —
     it is the least-audited part of an otherwise heavily audited protocol.
   - release commits named "deploy X" or "setup X market" usually touch only
     deployment JSONs, OpenZeppelin manifests and config, not `.sol` sources.
     List the files each commit actually changed before scoring a target as fresh
     code; the file-list commands and the rule live in `bugbounty-target-selection`,
     section "Commit messages are not proof of new code surface".
   - on-chain scope: `https://<chain>.blockscout.com/api/v2/addresses/<addr>` ->
     `creation_transaction_hash` -> that tx's `timestamp` = the real deployment
     date; a fresh listing can point at year-old contracts.
   - **Confirm the feature is live on an in-scope address before staking.** A
     release commit can add a feature to repo HEAD while every target in scope
     still runs an older version. Batch `eth_call` to the version getter on every
     scope address (`apiVersion()` for Yearn-style vaults, selector `0x25829410`)
     and to a getter that exists only in the new version. Include addresses the
     program folds in via an "all contracts listed on <site>" clause, not just
     the visible asset table. If none report the new version, park the idea: a
     bug in undeployed code cannot reach the assets the bounty covers.
     For a diamond/proxy, explorer verification can lag the live facet set. Enumerate
     `facetAddresses()` and call a feature-only getter on the diamond; a non-zero
     answer proves the upgrade is live even when the explorer's verified `System.sol`
     still lacks the new fields. Do not park the target from stale verified source
     alone.
   - **A component can be explicitly full scope and still be Testnet only while the
     reward is tied to Mainnet code.** Before committing a day to the least-audited
     module, read the program's deployment clause and inventory the same release's
     Mainnet commits by changed-file list. Rank by payable surface, not by code
     freshness. A clean verdict on a Testnet-only component is not closure of the
     release; the unswept Mainnet modules are the carry-over that must be named.
   - On Solana, source presence is NOT dispatch presence. A handler file, its
     snake_case name in the ELF string pool, and one of its log phrases can all exist
     while the instruction is absent from the deployed dispatcher. Before investing in
     a PoC, check the CamelCase `<Name>Instruction` dispatch string, the official SDK
     IDL's `instructions[]`, and finally call it with `sha256("global:<snake_case>")[:8]`;
     `Custom(101) InstructionFallbackNotFound` means the discriminator missed, NOT that
     the handler is absent. Derive the exact snake_case name from the `pub fn` in `lib.rs`
     and from the SDK IDL's camelCase name before killing a lead. Real case: a handler
     file named `handler_repay_and_withdraw_redeem.rs` dispatches as
     `repay_and_withdraw_and_redeem` (IDL `repayAndWithdrawAndRedeem`); a PoC using
     `global:repay_and_withdraw_redeem` returned 101 for both arms and was wrongly
     recorded as source-only until the correct discriminator dispatched it on deployed
     bytecode. Only after both names agree does a 101 justify a kill in the coverage
     ledger. Why: source-only code cannot move bounty assets, but a wrong discriminator
     can fake that conclusion.
   - After the discriminator matches, verify the account list against a REAL successful
     transaction for that instruction before trusting any ProgramTest constraint error.
     Enumerate recent signatures for the program, fetch candidates with JSON encoding,
     decode instruction data as base58 (not base64), keep a tx whose first eight bytes equal
     the discriminator, and compare its account count and order with the SDK IDL's flattened
     account list. A cached meta file with a different discriminator or fewer accounts is a
     different instruction; its `InvalidProgramId` or `AccountNotEnoughKeys` result is harness
     debt, not protocol behaviour. Why: a wrong account list reproduces the program's own
     constraint failures faithfully and manufactures a false verdict.
   - cost: platforms charge per-report deposits (Sherlock USDC 250, Cantina 50,
     HackenProof 5). Cantina refunds for valid AND legitimately invalid reports;
     only spam, low-effort/AI content or inflated severity slashes the deposit,
     per its deposits doc. Factor that into expected value and never book a
     refundable deposit as a sunk fee.
   - contest reality check: before investing in a contest found via search,
     confirm the page is a PRODUCTION listing, not a demo/preview. Demo pages say
     so explicitly and carry contradictory dates; a preview subdomain plus
     inconsistent start/end dates is a hard stop. Confirm a named judge and an
     actual funding guarantee. A contest advertised as POST-AUDIT with a
     Critical-only, large-loss threshold is not an unaudited fresh surface,
     however new the listing looks.
   - payout reality check: the reward must be liquid money with a stated amount
     and conversion. Points / airdrop credits with an unspecified conversion are
     not a payable target, however fresh and unaudited the code is.
   If every fresh-looking listing is old code, the fresh SURFACE is the DIFF
   between the pinned commits (see the signature-refactor rule under step 3), or
   the next audit competition — pre-launch code is the only reliably fresh scope.
2. **Recon** — map every new entry point, its caller permission, the state it
   touches, the events it emits, and its integrations (token, oracle, bridge,
   admin, fee, pause).
3. **Consistency** — the core pass. For each action: ownership, permission,
   accounting, rounding/precision, idempotency/replay, reentrancy, slippage,
   rate limit, pause, admin, storage layout, error handling, event completeness.
   **Signature-layer refactors are a forgery seam:** when a release moves or
   rewrites the code that verifies signed payloads, extract every
   `keccak256(abi.encodePacked(...))` argument list from the old and the new
   source and diff them field by field — any field the new hash dropped is now
   attacker-controllable (forgery). Identical field lists clear the whole
   refactor in minutes. Read the OLD file raw at
   `raw.githubusercontent.com/<org>/<repo>/<sha>/<path>` and the per-file
   patches at `api.github.com/repos/<org>/<repo>/compare/<shaA>...<shaB>`
   (unauthenticated) — no need to clone both trees.
4. **Impact filter** — keep only candidates that mean loss of funds: double
   claim, withdraw over balance, mint without backing, wrong interest/fee,
   stale/manipulated oracle, stuck funds, privilege escalation.
5. **PoC** — reproduce on testnet/fork; show state before -> action -> state
   after; prove value moved or got locked; check the program's grading clauses
   and that it is not a duplicate.
   - When a hand-written minimal interface call reverts with empty `0x` data,
     diff that function's signature against the source before treating it as
     on-chain behaviour: multi-argument view functions are commonly encoded as
     single-argument ones. Why: the wrong selector hits no function and reverts
     with empty data, which reads like a protocol failure and starts a false lead.
   - Confirm the function selector is actually installed on the mock diamond before trusting negative tests. If the harness deploys only a subset of facets, every invalid-input case can pass with `Diamond: Function does not exist` while the real validation is never exercised. Add the missing facet with the protocol's own diamond-cut helper, then rerun.
   - Seed arbitrary state with the protocol's mock facets instead of forcing the production deposit path when the mock invariant blocks setup. Record the happy path as unverified if the mock still reverts; do not claim a valid flow from negative tests alone. Why: a harness that only proves reverts cannot establish that the feature works.
   - Before rebuilding a stateful setup in Foundry, check whether the repo ships a Hardhat suite that already configures it (recapitalization, governance, oracle, Barn Raise). Run that suite first and add the new split to it. Why: a Foundry mock harness can hit harness-only invariant or zero-denominator failures even when the protocol path is sound; the native suite's fixture proves both the baseline and the new case.
   - When enumerating holders from event logs on a public RPC, chunk the block
     range to the provider cap (publicnode Base rejects ranges over 50k blocks)
     and dedupe addresses across chunks. Why: one wide range errors and looks
     like "no holders", which can kill a live lead.
6. **Report** — title with feature + impact, numbered repro, tx hash + PoC,
   quantified impact, fix recommendation, severity per the program's rubric.

## Speed

The window is short: aim to report within 1-7 days of release. A 15-minute
pass per release (find the new surface -> ask the consistency question -> test
one seam on a fork) is enough to decide whether to invest.

## Checklist

The full checklist, including the 15-minute version and the consistency
questions, is in [references/checklist.md](references/checklist.md).

For Solana PoCs rebuilt from live transactions, the harness reconstruction
recipe is in [references/solana-poc-from-live-tx.md](references/solana-poc-from-live-tx.md).
