# Severity evidence and proof quality

Use when a finding is real but its rating, novelty, or profitability is contested. The goal is to convert a judgment call into evidence the judge can check.

## Developer intent as novelty and severity evidence
Grep the vulnerable module AND its git history for comments or docstrings that name the safety property the code was meant to enforce. When a comment explicitly identifies the risk ("avoid ... being used to drain depositors") or the intended ordering ("liquidations should happen before bad debt repayment") and the implementation does neither, the "this is intended design" rebuttal collapses: the team wrote down the property and failed to enforce it. Quote the comment verbatim with `file:line` and the commit it came from, then show which specific guard fails to cover the reproduced case. Re-check that the comment is still present in the deployed version, not just in an old commit.

## Prove net profit, not just victim loss
A PoC that only shows "the victim pool paid X" invites the rebuttal that the attacker gained nothing. Snapshot the attacker's liquid balance, collateral balance, escrow balance, and debt immediately before the exploit call. After the call assert each is unchanged except the intended one, and assert `netWorthGain == payout` where net worth is `liquid assets + collateral at true price - debt`. Asserting unchanged balances is what proves the attacker kept the collateral. Label the log line so the output reads as a direct statement of the claim.

## Precondition-frequency claims must match the PoC's configuration
When arguing that a precondition is routine rather than an "extensive constraint", compute it at least two ways, for example a multi-day swing on close prices and a rolling low compared with close. Counts differ by methodology; report the range and keep the headline number tied to the exact collateral and configuration the PoC uses. Never present one methodology's count as universal, and never inflate a swing-based count into a claim about the oracle's own low-based window. State the methodology next to the number.

## Threshold math must come from the PoC market
For a dampened 2-day-low oracle with collateral factor `cf` in basis points, `viewPrice < spot` requires the recorded low to fall below `spot * cf / 10000`, i.e. a dip greater than `(1 - cf_bps/10000)`. CF 8500 needs >15%, CF 9200 needs >8%. Compute this from the actual market in the PoC before quoting a percentage; a number borrowed from a different market is a factual error even when the direction is right. A lower theoretical threshold on a market whose collateral is a stable LP with a virtual-price feed does not widen real exploitability: confirm the feed can actually be pushed down before claiming a second attack surface.

## Negative results belong in the record
If a live survey shows no market currently satisfies the precondition, say so explicitly and keep it in the report. It does not lower severity: programs reward the existence of the vulnerability and its conditions, not a single instant of exploitability. Hiding the negative invites a credibility hit if the judge checks it themselves. A negative from a reproduction attempt only counts after its setup is proven correct; an unmet cap, reversed queue ordering, cached metric or exhausted gas budget is a setup failure, not evidence against the finding. When a later corrected run reverses an earlier retraction, rewrite every draft, appendix and report that carried the old claim and regenerate the checksum manifest in the same pass.

## When the data is challenged
Keep the number that matches the PoC's actual parameters and explain the methodology rather than sending a stream of corrections. A correction that changes the headline number without changing the conclusion usually muddies the report more than it helps.

## Preventive control bypass is a valid severity argument
Do not insist on a measured cash shortfall before reporting a real bug. When the program scope says an in-scope vulnerability "causes or worsens the impact", a permissionless bypass of the only guard against a documented loss scenario is reportable on expected risk. Build the case as a chain: the platform or project acknowledges the loss, names the control that prevents it, and the PoC shows that control failing. Keep the absence of realized loss in the honest bounds instead of using it to suppress the finding. The operator corrected an over-conservative evidence standard on Flex: preventive framing matters, but never inflate severity beyond what the chain proves.
