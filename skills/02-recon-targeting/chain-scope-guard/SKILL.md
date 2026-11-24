---
name: chain-scope-guard
description: "Use before testing EVM/Solana bounty targets: enforce scope."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [BugBounty, SmartContract, EVM, Solana, Scope]
---

# Chain Scope Guard

Markdown-program scope validator for EVM contract addresses and Solana program
IDs. Adapted from the `programs/*.md` + `scope_guard.py` pattern in
`DevCop95/bugbounty-lab101`, rebuilt for chain targets with no third-party
dependencies. This is a guard, not a scanner: it only answers "may I touch this
asset for this program?".

## When to use

Load this BEFORE any on-chain interaction for a bounty: RPC probing, fork setup,
PoC deployment, or writing a report against a deployed address. Use it again
whenever a target list grows (address book, docs deployment table, new chain).
Pair with `bugbounty-target-selection` (rep gate, payout clauses) and
`audit-competition-hunt` (pinned commits, known issues): scope is only one gate.

## Files

- `scripts/chain_scope_guard.py` : the validator and CLI.
- `scripts/scope_extract.py` : extracts a DRAFT program from a program page.
- `scripts/scope.sh` : bash wrapper that fixes MSYS path handling on Windows.
  Keep it LF-only; CRLF breaks `set -o pipefail` when it runs under WSL.
- `templates/program_template.md` : program scope file template.

## Extract a draft from a program page

```bash
python scripts/scope_extract.py --url <program-scope-url> \
    --output programs/<slug>.md --report reports/<slug>.json
# Offline / saved page:
python scripts/scope_extract.py --input-file page.html --output programs/<slug>.md
```

It fetches with a browser UA and falls back to the keyless Jina reader, strips
HTML, then collects EVM addresses and 32-byte Solana base58 pubkeys. Chain is
read from the address's OWN line, then the preceding heading, never from a wide
window (neighbouring addresses would leak their chain). Out of Scope headings
and Known Issues sections route addresses to the exclusion list. Repos, pinned
commit candidates, docs/address-book links and per-address context excerpts go
to `## Special Rules` as provenance. `Status` is always `Draft`, which the guard
REFUSES to authorize until you verify and flip it to Active.

The extractor is a candidate generator, not an authority. It cannot read
conditional carve-outs ("except tokenId 1001"), KYC gates, or payout clauses,
and a docs address-book link it finds is a FOLLOW-UP, not extracted scope.
Verified live run on the Immunefi 0x resources page produced 7 chain-agnostic
addresses, the repo link and the docs follow-up; the tokenId carve-out still
needed a human read.

## Set up a program file

```bash
# Create programs/<name>.md from the template, then EDIT the scope sections.
./scripts/scope.sh --new-program <program-slug> --platform HackenProof
# Or just print the template and save it yourself.
./scripts/scope.sh --print-template
```

Copy the In Scope / Out of Scope entries VERBATIM from the live program page or
competition Scope tab, including any "Additional Scope" address-book clause.
Set `Last Scope Review` to the date you read the page. When transcribing from a
saved page or an aggregator mirror, the page prints its own count (for example
"In Scope (54)"). Compare your parsed rule count against it and treat an unexpected lower
count as a parsing failure, not a smaller scope: mirror layouts often put the
asset name BEFORE the explorer link, so a URL-only regex silently drops rows or
attaches the wrong name. A lower count is legitimate only when the page's own
list contains non-address assets (for example a web app URL) or duplicate
(chain, address) pairs: dedupe by canonical target, put the non-address entries
in Special Rules, and record the stated total plus the difference. Why: a web
URL and a duplicated deployment make a correct extraction look short, and a
blind "count is low, parsing failed" conclusion discards accurate scope. Parse the name, URL and description as a triple and
derive the chain from the explorer host (`optimistic.etherscan.io` to `evm:10`,
`basescan.org` to `evm:8453`). Entries in the markdown
file, not the guard, are authoritative: re-verify the page when in doubt.
Keep those two sections to target-format lines only. A prose bullet under
In Scope or Out of Scope is a parse_error that silently drops every rule in the
file, so source-only URLs, carve-outs and pinned revisions belong in Special Rules.

When a reader renders fewer assets than the page's own total (for example 12
visible of 386), first fetch the raw HTML and look for a serialized `assets[]`
array before accepting the rendered subset. Next.js program pages embed the
authoritative list in escaped JSON flight data (`\"assets\":[{...}]`); locate
the opening bracket, replace backslash-quote with quote, and hand the tail to
`json.JSONDecoder().raw_decode()` so trailing flight-data after the array is
ignored. Derive each chain from that entry's OWN explorer URL host
(`etherscan.io` 1, `gnosisscan.io` and `blockscout.com/xdai` 100,
`arbiscan.io` 42161, `basescan.org` 8453, `optimistic.etherscan.io` and
`explorer.optimism.io` 10, `uniscan.xyz` 130, `oklink.com/xlayer` 196,
`worldscan.org` 480, `snowtrace.io` 43114); record
the host-to-chain map in Special Rules and leave an unknown host UNRESOLVED.
Omit entries whose URL has no well-formed address, including concatenated
addresses in malformed explorer paths, and never repair them. Explorer hosts
are not self-describing: `snowscan.xyz` is Avalanche C-Chain (43114), not
Sonic, while `sonicscan.org` is Sonic (146), `hyperevmscan.io` is Hyperliquid
EVM (999), and `www.oklink.com/fr/x-layer` / `/fr/fantom` encode the chain in
the path (196 / 250). Verify a sample address with read-only `eth_getCode` on
the candidate RPC and `eth_chainId` before writing the rule, and record the
verified host-to-chain map in Special Rules. For entries omitted from a
rendered subset, record the stated total plus the missing count in Special
Rules. Let
deny-by-default cover the rest. Do not infer the unrendered addresses, and do
not assign a chain from a neighbouring row when the same address appears under
several chains: an address with two chain assignments is UNRESOLVED. A partial
active file is an honest working set, not a claim of full scope coverage; say
which addresses were omitted and why before any report cites a target.

## Target and rule format

```
evm:<chain-id-or-alias>:<0x-address>
solana:<cluster>:<base58-pubkey>
```

Chain aliases: `ethereum`/`mainnet`/`eth` -> 1, `arbitrum`/`arb` -> 42161,
`base` -> 8453, `optimism`/`op` -> 10, `polygon`/`matic` -> 137,
`bsc`/`binance` -> 56, `avalanche`/`avax` -> 43114, `sonic` -> 146.
Solana clusters: `mainnet`/`mainnet-beta`, `devnet`, `testnet`, `localnet`.

A two-part rule (`evm:42161`, `solana:devnet`) or an explicit `*` means every
identifier on that chain. A wildcard CHAIN (`evm:*:0x...`) means that identifier
on every chain; use it only when the program says scope is not chain-limited.
Wildcards are valid in SCOPE RULES only; a concrete target can never be a
wildcard. EVM addresses are normalized to lowercase; Solana base58 identifiers
are case-sensitive and decoded to 32 bytes.

## Commands

```bash
SCOPE="./scripts/scope.sh --programs-dir programs"
$SCOPE evm:1:0xabc...                 # exit 0 = authorized, 1 = denied
$SCOPE --explain solana:mainnet-beta:<pubkey>   # structured JSON verdict
$SCOPE --normalize EVM:Ethereum:0xABC...        # print canonical target
$SCOPE --audit                         # stale, parse errors, scope conflicts
$SCOPE --diff old-scope.md new-scope.md # added / removed canonical entries
$SCOPE --filter-file candidates.txt --authorized-out ok.txt \
       --discarded-out no.txt --candidates-out pending.txt
```

Set `CHAIN_SCOPE_DIR` to avoid passing `--programs-dir` every time;
`CHAIN_SCOPE_MAX_AGE_DAYS` (default 30) controls the stale warning and audit;
`CHAIN_RESEARCHER` fills the template handle.

## Decision rules (mirroring the web scope guard)

1. An Out of Scope rule in ANY program file wins, including inactive programs.
2. Only ACTIVE programs can authorize a target.
3. Coverage by an inactive/paused program alone is a denial.
4. No matching rule is a denial. There is no `FORCE` or env override.
5. A review older than the max age prints a stderr warning; `--audit` counts it.
6. `--audit` also flags an in-scope rule shadowed by an out-of-scope rule.
7. `Draft`, `Unreviewed` and `Pending` count as inactive, so an auto-extracted
   draft can never authorize a target until you set `Status` to `Active`.
8. A program whose published scope names only web URLs, accounts, or product
   families (with a docs address book that says it is lookup, not scope) has ZERO
   authorized chain targets. Create its file with an empty In Scope and record
   the URLs in Special Rules, then prove with `--explain` that the precompile,
   core-contract and token addresses you found in public docs are denied.
   Static review of a published SDK artifact does not touch the target and stays
   allowed; RPC reads, fork setup, PoC deployment, and any report naming a
   deployed address do not. Ask the program for an explicit address-book clause
   before touching chain state, rather than inferring scope from documentation.
   When the program's own prose conflicts with the generated guard (repo-only
   scope plus 'include chain and contract address where applicable' implies
   deployed instances are covered), surface the conflict to the operator and
   do not silently pick either side. Label read-only `eth_call` as intelligence
   and keep deployed addresses out of any report until the conflict is resolved.
   Re-fetch both authoritative pages before treating a recorded conflict as
   still open; project docs are often rewritten to match the platform. If they
   now agree, patch the local program file, record the re-check date and the
   resolution in Special Rules, and re-run `--audit` instead of escalating to
   the operator. Why: a stale local conflict note blocks a live program just as
   effectively as a wrong scope rule.
9. An authorized address may be an UNINITIALIZED shared implementation while the
   stateful live instance is an EIP-1167 clone of it. The guard denies the clone
   unless its own address is listed. Verify the delegate target with read-only
   `eth_getCode`, report the denial openly, and add the clone to In Scope only
   when the operator explicitly approves that scope edit: compile-match and PoC
   evidence about the implementation do not by themselves authorize the clone.

## Class-based scopes (contract names or source paths, no address list)

Some program pages define scope by contract NAME or repo path, for example 'the deployed token wrappers (`contracts/partners/tokenWrappers/`)', with carve-outs such as 'deprecated wrappers excluded', instead of by address. Unlike rule 8's URLs-only scope, this IS a chain scope: transcribe each cited instance as a concrete `evm:<chain>:<address>` rule using the official address book plus on-chain evidence, record the derivation and the carve-out in Special Rules, set Status Active only after reading the authoritative page, then run `--audit` and `--explain` on every cited address. State in the deliverable that the address list is derived rather than quoted verbatim, so a later dispute can be settled against the page.

When the operator authorizes adding derived addresses to the guard, back the program file up before editing and write one `## Special Rules` line that names the authorization, the source rows used for the derivation, and the review date. Mark the addition explicitly as an OPERATOR-AUTHORIZED LOCAL ADDITION, not official platform scope, then re-run `--audit` and `--explain` on every new target and keep the `authorized: true` output as the working list. Why: without the label and backup a later session treats a locally expanded In Scope section as platform-backed and loses the pre-addition state needed to settle a scope dispute.

Never invent the missing middle of a truncated address to fill a rule. Omit it and let deny-by-default cover it, or re-fetch the full value from a primary source. Why: a plausible-looking fabricated hex string silently authorizes or excludes the wrong contract and defeats the guard's purpose.

## Integration rule

Before creating a program file, search the whole audit tree for an existing
guard file for the same program (`programs/`, `scope-programs/`, and any prior
`<slug>.md`); reuse and re-audit it instead of writing a second one, because a
prior session may already contain operator-authorized scope edits that a fresh
file would silently discard. Before hunting, transcribe the scope into a
program file, run `--audit`, then run `--explain` on every candidate address
from the address book and keep the authorized output as your working target
list. When a regenerated program adds addresses that a DIFFERENT program file
lists as out of scope, `--audit` reports a conflict and `--explain` denies them;
surface each conflict to the operator instead of treating the local addition as
official scope. After the operator authorizes a resolution, if the conflict comes from the other program's third-party-protocol carve-out, delete those addresses from the OTHER program's Out of Scope list rather than dropping them from the target program: with no matching in-scope rule they stay denied for that other program, while the target program's authoritative page keeps them authorized. When the conflicting rule is a wildcard chain rule (`evm:1`, `evm:1:*`) in a source-only program, you cannot delete individual addresses from it: back the file up, remove the wildcard, and add a Special Rules line saying that program stays source-only and its empty In Scope section still denies every deployed target. Prove the resolution with a combined-directory `--explain` on both sets of targets. Why: rule 1 makes another program's wildcard deny global across the directory, so leaving it in place silently blocks an authoritative in-scope list from a different program.
Record that rationale in the other file's Special Rules, back the file up before editing, and re-run `--audit` and `--explain` on both. When merging program files from several roots into one directory for a cross-program audit, name copies by the full relative parent path plus filename. Using only the immediate parent name collides for sibling directories with the same basename (for example `programs/` and `scope-programs/` under one target), so later copies silently overwrite earlier ones and the audit undercounts programs. Re-run after any scope change or
proxy implementation upgrade, and again before filing a finding against every
address the report cites. Before any report, re-fetch the platform's authoritative
scope (revision, `assets[]` with `inScope` flags, and rules text) and diff the
addresses against the local program file. An operator-authorized local addition
such as an EIP-1167 clone is NOT official scope until the program confirms it,
and a locally skipped ambiguous-chain asset is an acknowledged gap: state the
deviation explicitly instead of treating `authorized: true` from a locally
edited guard as program-backed. The guard does NOT fetch the program page,
verify payouts, or check KYC/reputation gates.

When the scope was machine-extracted (e.g. an API JSON with per-address
`inScope` flags), generate the program .md from that JSON: one
`evm:<chain>:<address>` rule per in-scope entry, the excluded ADDRESSES under
Out of Scope, `Status: Active` and the date the page was read. Put non-address
entries (URLs, product names, prose carve-outs) in Special Rules, never in the
two scope sections, because a prose line there is a parse_error that silently
drops every rule. Parse the chain from each entry's OWN notes field: chain
words inside a contract name (`ChainlinkBasePriceFeed`, `MainnetDolaFlashMinter`)
are not chain assignments. An address with two chain assignments is UNRESOLVED:
leave it out of In Scope and let it deny by default instead of guessing a chain.
If the notes name both chains and read-only checks confirm a verified contract at that address on each, resolve it by adding one rule per chain with provenance in Special Rules, with explicit operator approval and a backup of the guard file first.
Write generated program files to a durable audit path, not the Hermes scratch
dir (scratch is pruned), and re-run `--audit` after the copy. An `--audit` that
reports `total_programs: 0` is a PATH failure, not an empty scope: on this host
native Python receives MSYS paths as `\e\audit\...`, so pass a native
`E:/...` path to `--programs-dir` and re-check the reported rule counts.

## Verify the tool itself

```bash
python -m pytest -q scripts/test_chain_scope_guard.py scripts/test_scope_extract.py
```
