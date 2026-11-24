# Normalising a large multi-chain scope

Use when a program lists dozens or hundreds of in-scope addresses across several
chains. The goal is a ranked list of live, funded instances, not a raw address
dump.

## 1. Capture the authoritative scope

- Open the platform's own Scope tab, not just an aggregator. The aggregator may
  show only a truncated list behind a `Show all N` button.
- Click the button, extract the rendered text, and parse address/label/chain
  triplets. Expect more chain-deployment entries than unique addresses: the same
  CREATE3 address is often redeployed on many chains, so dedupe by address while
  keeping every chain entry.
- Save the raw text and the parsed JSON to the audit workspace. Note the program
  rules that say which components count: some bounties list only fund-holding
  contracts but let the root cause live in any helper, decoder, manager or
  config.

## 2. Classify addresses with batched view calls

For EVM chains, compute selectors with `Crypto.Hash.keccak(digest_bits=256)` and
batch `eth_call` through a public RPC per chain. Start with `name()`,
`symbol()`, `totalSupply()`, `decimals()`, `authority()`, `hook()`.
Addresses that answer with a name and supply are the vault/token contracts;
those that do not are queues, drones or helpers. Record which chain each
answer came from.

## 3. Rank by funds held

For vault architectures that expose an accountant rate, compute
`assets = totalSupply() * getRate() / 10 ** vaultDecimals()` on each chain.
Fetch token decimals from the base asset and USD prices from
`https://coins.llama.fi/prices/current/<chain>:<address>` (DefiLlama chain
slugs, not the platform's chain labels). Cross-check the sum against the
protocol's DefiLlama `chainTvls` to see how much of the protocol is missing from
public deployment files; large gaps usually mean private deployments.

## 4. Overlay audit gaps

If the repo stores per-deployment metadata (`auditGap`, `auditUrl`,
`deploymentCommit`), aggregate it across all deployments and join it to the
funded-instance table by chain and address. Rank components by
`unaudited` > `state,selectors,auth` > `state` > `none`. Verify that the gap is
for the deployed commit, not a stale note: a source file header saying
"last audited" can disagree with the deployment metadata, so compare the audit
URL and commit where possible.

## 5. Read the known-issues list before choosing a surface

Scrape the full program page text, not just the summary. Mark which of your
candidate components are explicitly excluded. A component that is both funded,
flagged unaudited, and absent from known issues is the first place to spend
PoC time.

## 6. Confirm the gate is crossable

Before deep work on a role-gated component, call the live authority with the
zero address and a few random EOAs for the target selector. If all are denied,
a pure logic bug in that component cannot pay under a trusted-role clause;
require a path that gives an unprivileged address the capability of a trusted
role. Avoid environment-specific RPC failures by testing one `eth_chainId` per
chain before batching calls, and record which chain RPCs actually served the
addresses.

## 7. Product-family scope with a lookup-only address book

Some programs define scope by NAMED PRODUCT FAMILIES (liquid lockers, vaults,
Votemarket) and publish a docs address book that explicitly says it is a lookup,
not scope, because it also lists retired products. Do not turn that table into
authorized targets.

- Parse the docs table from raw HTML, not a text extractor: readers often repeat
  the first rows once per filtered section. On Vocs-style pages each row is a
  `<tr>` with a `<code title="0x...">` plus classed cells such as
  `vocs-addresses-chain`, `-protocol`, `-contract-name`, `-category`; extract by
  class and dedupe on the full tuple.
- Record the book's own "Data updated / Snapshot" date and count rows by
  protocol, chain and category. A 700-row book with 200 rows from the target
  protocol is normal; the rest are third-party dependencies.
- Narrow to fund-holding candidates with batched `eth_call` on `balanceOf`
  (selector `0x70a08231`, address left-padded to 32 bytes) over the protocol's
  own addresses and the few tokens the product actually uses. Batch in chunks
  of about 40 calls per JSON-RPC POST. Also read native `eth_getBalance`: when
  every native balance is dust, value sits in ERC20 or vote-escrow positions and
  a token scan alone understates the product's size.
- Date "live" by recent transactions, not by the registry listing:
  `https://<chain>.blockscout.com/api/v2/addresses/<addr>/transactions` returns
  timestamps and decoded method names. Pair it with
  `/api/v2/smart-contracts/<addr>` for the ABI, `is_proxy` and `implementations`,
  then filter function names for withdraw/claim/rescue/set roles to map the
  money flow. Cross-check protocol size with `https://api.llama.fi/protocol/<slug>`.
- A large balance in a third-party base protocol, oracle or DEX pool is NOT the
  target when the terms exclude third-party-only defects: only the operator's
  own integration code can qualify. Say this explicitly so the largest number
  in the table is not mistaken for the best target.
- Treat every read-only call as INTELLIGENCE. Write the scope file with an empty
  In Scope, the explicitly excluded addresses under Out of Scope, and the
  product families plus this caveat in Special Rules. Prove with `--explain`
  that candidates deny, then ask the program for the deployed addresses before
  any PoC or report.

## 8. Blockscout v2 on custom chains: access and event forensics

- Call Blockscout v2 with `curl -A 'Mozilla/5.0' -H 'Accept: application/json'
  -H 'Referer: https://<explorer>/'`. A urllib/requests call without those headers
  can get 403 on the same host where curl succeeds, so do not declare the explorer
  unavailable until curl has been tried.
- Per-address logs live at `/api/v2/addresses/<address>/logs?topic=<topic0>`.
  The global `/api/v2/logs` route is not implemented on every Blockscout instance.
- The `topic=` filter matches a topic in ANY position, not only topic0. To find
  beacon-style proxy upgrades, filter with the beacon address left-padded to 32
  bytes (topic1 of `UpgradeBeacon`) and read the matching event record.
- A proxy's `implementation()` getter on a beacon proxy returns the beacon's
  implementation, which is a DIFFERENT address from the proxy's actual delegate
  target. Do not report that difference as a misconfiguration; identify the
  beacon pattern from the upgrade events first.
- Date a deployment from the event record's own block/timestamp, then verify code
  at that block with an archived at-block RPC call. A current-state call can be
  silently upgraded later and misdates the finding.
