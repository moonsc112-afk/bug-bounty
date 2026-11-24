# Unverified bytecode: units and collateral checks

When an unverified wrapper or partner contract exposes a counter that looks impossible against a token's total supply (for example `totalLocked()` > `totalSupply()`), do not flag it as an anomaly or a bug until the units and the collateral side are checked.

## Procedure
1. Read both counters in raw wei with `eth_call`.
2. Identify what each is denominated in: the program's receipt/claim token versus the underlying asset. Names like `totalLocked`, `totalReleased`, `totalStaked` are not proof of the same denomination.
3. Call `balanceOf(wrapper)` on the UNDERLYING token, not on the wrapper. If the liability counter equals that balance to the wei, the contract is fully collateralized and the ratio is just two different units (collateral in, receipts out).
4. Check vesting/time gates before reading zero counters as breakage: read `tgeTimestamp()`, cliff/vesting duration and `totalReleased()`. A zero released total inside a cliff is expected.
5. Check who can move funds and whether the source is verified/in-repo. If it is a partner contract with gated admin, scope-check before spending time on deep RE.

## Rule
Never write an "impossible" accounting ratio into a report as evidence before step 3. Record the exact equality (or the shortfall) instead: equality closes the lead, a shortfall is the actual finding.

## Why
The two numbers live on opposite sides of the contract. A locked/collateral counter can legitimately exceed the issued receipt supply when the bucket is pre-funded or denominated in the underlying. Only a balance comparison settles the unit mismatch.
