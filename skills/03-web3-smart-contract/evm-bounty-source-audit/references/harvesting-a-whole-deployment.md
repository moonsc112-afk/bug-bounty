# Harvesting a whole deployment when the repo is private (audit what is DEPLOYED)

A bounty's repo link can be private (a clone dies with `could not read Username`) or the scope can be "all deployed contracts". Then the verified deployed sources ARE the truth and usually sufficient — no repo access required.

## Steps

1. **Enumerate.** Collect every published address list: the bounty's Scope tab (often only the core subset), the project's docs "Contract addresses" page, and the security repo README. Docs pages frequently offer ONE json for everything (`https://<site>/address-book/<name>.json`) — prefer it: a 452-entry address book beats a 17-address scope table.
2. **Harvest per address** from a free explorer API (Blockscout v2, no key): `GET https://eth.blockscout.com/api/v2/smart-contracts/<addr>` returns `source_code` (main file), `additional_sources[]` (often the whole monorepo bundle, OZ/LayerZero/Lib deps included), `is_verified`, `name`, and `implementations[]` for proxies.
3. **Recurse into `implementations`.** A proxy's own bundle is only the OZ proxy files; the logic lives at the impl address, so queue it and fetch it separately (dedupe by address).
4. **Write a manifest while harvesting** (name, address, contract, verified, files, impls) and pace ~0.4 s per request: 130+ addresses finish in ~10 minutes, and a re-run is retry-safe.
5. **Assemble a compilable tree** from the bundles. Harvested paths line up with the usual remappings (`@openzeppelin/…`, `lib/…`, `@layerzerolabs/…` map straight into the tree), so `forge build` works once the missing dev dependency (`forge-std`) is cloned in. Normalize test imports to root-relative paths before any transfer to another machine.

## Read the scope clause before trusting (or distrusting) a list

Scope tabs are often a subset: look for an **Additional Scope** clause, which may extend coverage to the docs' address book ("all contracts deployed for purposes of this bounty… all production deployments"). When the security-repo README and the scope tab disagree, the README typically says the platform's rules govern — quote the governing sentence in your notes. Record the chains in scope too: a deployment can span five chains while the API you harvest covers only one.

Next step once sourced: **reading-a-hardened-deployment.md** — money-path read order, per-function gate-chain ledger, copy-diff of module/engine duplicates, park + watch. Run the harvest with `scripts/harvest_addressbook.py` (args: `--root`, `--addressbook`, optional `--only-chain`).
