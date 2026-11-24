# Bounding oracle-manipulation findings

Use when a candidate finding depends on pushing a feed price far enough to harm depositors. Prove the bound before writing a report.

## Procedure

1. **Read the WHOLE update function, including state-write order, before deriving a one-block bound.** `alpha = exp(-delta_t / ma_exp_time)` is the weight applied when an EMA is next WRITTEN, not proof that the current read jumps. Curve-style `save_p_from_price(last_price)` packs `self._ma_price()` into the stored EMA BEFORE advancing `ma_last_time`, and `price_oracle()` returns that stored EMA while `ma_last_time == block.timestamp`. A large spot move in one transaction can leave the read unchanged however long the pool was idle; the gap bleeds in only on a LATER swap after time advances. Read the writer and the reader as a pair, fork-test the exact same-timestamp sequence, and state the measured same-block delta before writing any one-block claim.
2. **Find the real gate between feed and valuation.** Oracles often store daily lows or rounded snapshots in mappings. Clear those storage slots with `vm.store` and confirm with `vm.load` first, then rerun the same pressure test. If the manipulated price only propagates after the slots are cleared, the dampening layer was the blocker, not the feed. Compute a nested mapping slot as `keccak256(abi.encode(key2, keccak256(abi.encode(key1, slotBase))))` from the contract's storage layout.
3. **Measure direction and cost on a fork, not by hand.** Run one swap in each direction to learn which way lowers the read; then loop with `vm.warp(+60)` and a fixed swap size. Log the read at intervals, the token spent, the token received, and the counter-token balance after each step.
4. **Compute net cost correctly.** `net_cost = tokens_spent * initial_rate - tokens_received`, then convert with the project's own Chainlink feed and its `decimals()`. Gas and arbitrage against the trade are extra, not included.
5. **Check counter-token liquidity.** A sustained attack dies when the pool's counter side is drained. If a 30-minute campaign consumes most of that balance, a longer or deeper attack is not demonstrated by the test.
6. **Quantify the actual harm threshold.** Collateral value must cross debt (liquidation) or the module's cap (slash) before any funds move. Convert that requirement into a required percentage drop and compare it to the measured drop. A 30% price move on a 2.8x-collateralized position is not a finding.
7. **Check whether the mechanism was already judged.** If the program rejected the downstream payout path as intended behaviour, a bigger price move does not make a new report.

## Pitfalls

- Do not value seized collateral at the pre-manipulation price when the collateral's own price source is the pool you manipulated. With `reward = debt / price_p * (1 + incentive)` and resale value `= collateral * price_p`, gain above the standard liquidation bonus is identically zero at ANY false price; manipulation slippage then drives net PnL negative. Sweep small manipulations too: an apparent 'profit at true price' is the designed liquidation bonus minus cost, not a protocol loss.
- Before relying on that resale assumption, trace the collateral's redemption path and measure secondary-venue depth. A vault share may redeem at an internal `pricePerShare` free of the manipulated EMA, yet the underlying may be permanently non-redeemable and nearly all liquidity may sit in the one manipulated pool; the economic conclusion still holds, but the stated reason must match the measured path.
- Do not turn a missing freshness check into a finding without a loss chain. An oracle that ignores `updatedAt`/`roundId`/`answeredInRound` is an informational observation until a stale round is shown to flow into a transfer, mint, or seizure.
- Do not present a large spot move as a large valuation move. Report the value that the consuming contract actually reads.
- Do not ignore read-only storage helpers such as `pausable()` or `expiration()`: grep their consumers first. If no contract reads them, only the boolean view matters.
- Keep a token-level `paused()` bitmask separate from a chain-level `SystemConfig.paused()`. They are different mechanisms and must not be mixed in one PoC.
- A failed full `forge build` does not invalidate a passing targeted suite; see simular-box-offload for the cloud-box fallback.
