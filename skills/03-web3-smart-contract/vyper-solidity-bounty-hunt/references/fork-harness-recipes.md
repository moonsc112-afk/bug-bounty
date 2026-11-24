# Fork harness recipes for scope-compliant bug-bounty PoCs

Use these when a program's scope excludes unendorsed markets, retired deployments, or code not deployed on mainnet. The goal is a PoC whose affected contracts are the live ones, not lookalikes deployed by the test.

## Live-contract fork setup
1. Fetch the authoritative scope through the platform MCP (`get_bounty` on Mantis) before writing the PoC. The rendered page can omit exclusions such as non-deployed code and unendorsed markets. Take the live addresses from the repo's deployment scripts (`script/Base.s.sol` or equivalent), not from memory.
2. Call `eth_getCode` at the intended fork block for every live address. A harness often caches a block that predates the deployment; if any address has no code, override the harness `setUp` with a later fixed block instead of relying on the cached one.
3. Repoint BOTH the test's router variable and its factory variable at the live addresses. A locally deployed factory bakes the local router into each strategy constructor's immutable, so calls fail with `!exitRouter` even after the test variable is repointed. Constructing through the live factory fixes the immutable.
4. Pick an endorsed market from the registry on-chain: read `get_all_markets()`, map each TroveManager to its Lender, and use one of those Lenders. Do not reuse the harness default if it points at a retired market.
5. Prove the PoC on the endorsed market and keep the earlier local-market PoC only as an illustrative mock. Report the live addresses, fork block, commit and observed command output.

## Reachability evidence for peripheral primitives
A code-level defect in a peripheral helper is only a finding if a live consumer can reach it. Read the consumer's config getters on the deployed instance, confirm the vulnerable selector is present in that implementation's code, and check whether the required whitelist has ever been activated (absence of setup events is decisive). If the whitelist is empty, record the primitive as hardening and do not report it.

## Bounded stress tests
Before creating thousands of on-chain positions, ask what a single cheap differential test proves. A mock differential that shows only a control bypass does NOT settle cross-user loss; if the claim depends on a cap being exceeded, say so and design the stress run to actually cross the cap. Expect gas in the billions and runtime in the tens of minutes; run it as a tracked background process and record gas, runtime and the exact measured assertion.

Fixture rules for capped-redemption or sorted-list stress tests:
- Make the liquidity-draining position the HIGHEST-rate trove, not the lowest. Redemption walks from the lowest rate; a large low-rate drain trove satisfies the whole exit immediately and the cap is never reached, producing a false negative.
- Size the redemption above the debt covered by the cap (number of cap troves times minimum debt), not merely above a single trove. Otherwise the walk stops before the cap.
- Use O(1) insertion hints by appending in monotonic rate order. Open troves with descending rates and pass the previous tail as `prev_id` with `next_id = 0`; ascending or zero hints turn a thousand-trove setup into an O(n^2) search.
- Raise the fork test gas budget explicitly with `FOUNDRY_GAS_LIMIT=<large>` in the command environment. Foundry's default 2^30 is exhausted by roughly two thousand stateful positions; the run then dies with a bare `OutOfGas` that looks like a logic revert. The `vm.txGasLimit` cheatcode may not exist in older forge-std versions, so prefer the environment setting over a code change.
- Measure underlying value, not a cached share-price view. `convertToAssets`/`totalAssets` on tokenized vaults only refresh on report and stay flat within the transaction. Compute `balance + total_debt - unclaimed_fees` times the victim's share of total supply, or force a report before comparing.
- If a third party's claim rises by exactly the exiting party's shortfall, that is positive proof of loss rather than a contradiction. The shortfall was socialised away from the caller; name the correct injured party before downgrading severity.

An unchanged victim balance from a correctly designed run falsifies the escalation and must be written back into every draft that claimed it.
