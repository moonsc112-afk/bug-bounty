# ERC-4626 lending audit recipes

Topical depth for harness work on lending pools, debt tokens and liquidation engines. Rules here are verified against real implementations; keep each proof step in the test file so the report can quote exact numbers.

## Rounding residue bound

For share price `r = (totalAssets + V) / (totalSupply + V)`, a collateral position of `S` shares is read as `A = floor(S*r)` and a seizure needs `S2 = ceil(A/r)`. The residue `k = S - S2` satisfies `k <= floor(frac(S*r)/r)` with `frac < 1`, therefore `k*r < 1` unit. A statement claiming a residue "worth at least one unit" cannot be produced by this composition. Derive the bound before brute-forcing sizes, and record the claim as algebraically dismissed once the bound holds.

## Organic supply cap

To drive share price below one and grow supply without storage shims: supply assets, restore a healthy collateral price, deposit collateral, borrow all idle liquidity, crash the collateral price, then liquidate with a minimal repayment so bad debt is written off. Each cycle lowers price; later deposits mint more shares. A handful of cycles can reach `type(uint128).max`. Close the final room with a real ERC-4626 `mint(maxMint)`, never an internal mint. Record cycle count, final supply and `maxMint`/`maxDeposit` in the README.

## Accrual overflow

Configure a real IRM clone at an extreme fixed rate and warp decades. Overflow then panics in `pendingInterest`, `repay`, `liquidate` and `writeOffDebt`, blocking every debt-clearing path. Quote the exact warp needed and distinguish borrow-index overflow from pool-debt overflow; do not claim both unless both were tested.

For truncation checks, compare accrued debt against the on-chain integer formula, not continuous `e^(rate*time)`. When high-precision continuous values are needed for a comparison, precompute them outside Solidity and pin the constant with a comment stating its derivation.

## Donation and flash-loan boundaries

Direct token transfers and direct mints into a pool are excluded from idle liquidity, `totalAssets` and share price, and cannot be borrowed. `maxFlashLoan` typically reads the raw token balance, so donations increase the flash-loanable amount; prove this with a real ERC-3156 borrower implemented inside the test file. Shares transferred directly to the pool lack a matching collateral token and are unredeemable through the collateral path.

## Full-close liquidation engines

An engine that always closes the whole loan still validates request bounds: collateral requests are minimums, borrow requests are maximums that must cover the full debt. A partial repayment request reverts. Swap engines explicitly when a harness needs full-position closure, and keep the partial engine for bad-debt recipes that need a residual loan. Swapping the engine back mid-test is normal when different steps need different semantics.

## Report discipline

Treat each documented behavior as verified negative only when the exact mechanism was exercised. If an adjacent condition was tested instead, mark the original as open. Quote the forge counts, the exact numbers observed, the limitations, and every shim used. Keep drafts under the engagement NDA; the operator alone handles account, KYC and submission steps.
