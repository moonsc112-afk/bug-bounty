# Inverse Finance (Mantis): compact case facts

Program: Mantis, 89 in-scope Ethereum mainnet addresses; DebtConverter explicitly out of scope. Bridge legs are not in scope. Payout requires demonstrable loss of funds plus PoC and KYC.

## Terminal platform ruling
JD-01 (permissionless slash overpay using dampened collateral value) was rejected as intended behaviour: jrDOLA absorbs post-drop bad debt by design, pessimistic valuation is intended, and the scenario depends on a market move the borrower cannot cause. Do not re-litigate this root cause.

## Code facts that survived verification
- `Oracle.getPrice` is permissionless and writes `dailyLows`; `viewPrice` applies a two-day low. `getFeedPrice` checks only `price > 0`, ignoring `updatedAt`, `roundId`, and `answeredInRound`. This is informational without a loss chain.
- `Market.liquidate` uses the same `getPrice` for the health check and the liquidator reward, then pays collateral from escrow. `forceReplenish` requires collateral value above the new debt and pays a reward from market DOLA.
- Curve EMA: the save path packs the pre-update EMA, so `price_oracle()` does not move within one timestamp. A 10% pool swap moved `last_price` 6958 bps but the feed 0 bps. Sustained 30-minute manipulation moved the feed 3473 bps; collateral value at the manipulated price gave exactly the designed 12% bonus, zero excess, and a large negative net PnL after slippage.
- `forceReplenish` upward path: donation raised the feed enough to pass the collateral check, but cost 16119 times the reward and was unrecoverable.
- ALE v5 is byte-identical to the local patched source; it only wraps Market deposit/borrow/repay/withdraw and receives no seized collateral. Leverage plus a false low again produced zero excess over the 12% bonus.
- st-yCRV is a Yearn Vault v2 (not ERC4626) redeeming to yCRV via `pricePerShare`. yCRV cannot be redeemed to CRV. The manipulated pool holds 97.37% of yCRV liquidity; secondary venues are 2.63% and follow the main pool. No cross-market path exists.
- DOLA and DBR minting is limited to the Timelock and registered minters; Fed/PSMFed/FlashMinter/DolaSavings are gated by a 2-of-6 chair Safe, payments, or borrower debt. VaultFed was already removed as a minter.

## Outcome
Slither triage, invariant harnesses, fork PoCs, and secondary-venue survey produced no submittable finding. All negatives and corrections are recorded in `E:/audit/inverse/findings/inverse-coverage.md`.
