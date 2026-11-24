# Cantina bounty triage (data extraction and ranking)

Use before choosing a Cantina target or paying a submission fee. Never trust the rendered page alone for status, rewards, or scope.

## Live inventory
- `GET https://cantina.xyz/api/v0/opportunities?status=live&limit=100` returns all live programs (bounties plus contests) in one response. Fields include `id`, `kind`, `timeframe.start/end`, `status`, `totalRewardPot`, `totalFindings`, `submissionFee`, `kycRequired`, `joined`, and `item.assetGroups`.
- The page advertises counts in `groups` (`currentBounties`, `currentCompetitions`). Reconcile the returned `items` count against those numbers before ranking.
- A bounty announced as upcoming can already be `live`. Check `timeframe.start` and `status` before setting any reminder or monitor.
- Rank by numeric signals, not by pot alone: `findings per day = totalFindings / days live`, pot size, program age, submission fee, and which severity tiers actually pay. Low findings/day plus a large pot is the strongest signal of an under-reported surface.
- Treat low findings/day as a prioritization hint, not evidence of an easy bug. A narrow scope, hard code, or unpaid severities produce the same signal.

## Instructions and rewards
- The HTML is Next.js streamed data. Join `self.__next_f.push([1,"..."])` chunks and JSON-decode each outer string. Long instruction text appears as a raw `NN:T<hex>,...` chunk, not a JSON-quoted string; extract from the chunk marker to the next chunk marker and unescape `\n` and `\"`.
- Some programs have no `assetGroups` or `rewards` in the API. Read the reward table from the instructions text before concluding a program does not pay. Cross-market and repeatable-attack caps also live only in the instructions.
- Build a known-issues checklist from the instructions before paying a fee. Audit reports named there are out of scope. Audit files present in the repo but absent from that list are reference-only until confirmed.
- Check `kycRequired` and `joined` before planning work; `restricted` means sign-in as a researcher is required.

## On-chain cross-check
- Use the public market API for candidate asset addresses, paginate with `limit=100&skip=N`; `limit=1000` is rejected. Batch `eth_call` for getters such as `tokenPrice(address)` and `isRateLimited(address)` across all candidates, then report the exact counts.
- A zero hit for a configured price or flag is a live-state result, not a code-level vulnerability. Label it as a design observation unless an attacker-controlled loss path is demonstrated.
- When `debug_traceTransaction` is unavailable on public RPCs, replay the transaction with `cast run <tx> --rpc-url <archive-capable-rpc> --quick` and grep the trace for the internal call's decoded arguments. Blockscout v2 internal-transactions prove a call happened but their items omit `input`, so they cannot decode calldata. If neither path works, read the SDK or frontend that builds the data instead of claiming the calldata is absent or harmless. WHY: the parent transaction's calldata only shows the outer router call, so a contract-level conclusion needs the internal arguments from a replay or from the authoritative builder.
