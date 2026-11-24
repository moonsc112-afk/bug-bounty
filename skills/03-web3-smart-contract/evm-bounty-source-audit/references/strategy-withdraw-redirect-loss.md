# Redirected withdrawal proceeds and synthetic loss in ERC4626 strategies

Use when a yield strategy or withdraw router forwards redemption proceeds directly to an external receiver instead of back to the strategy.

- **Trace the whole accounting chain before calling the redirect benign.** A router that arms a transient `proceedsReceiver`, a strategy whose `_freeFunds` passes that receiver into the underlying vault redeem, and a vault that re-reads its own idle balance after `freeFunds` will book the redirected amount as a loss. In Yearn `TokenizedStrategy._withdraw`, `loss = assets - idle` is then checked against `assets * maxLoss / 10_000`, so any `maxLoss < MAX_BPS` reverts with `too much loss`.
- **Prove it with a differential PoC, not a happy-path test.** One call with a conventional loss bound (for example 100 bps) must revert; the identical call with `MAX_BPS` must succeed and burn the shares. Assert the observable side effect (auction kicked, receiver set) so the control is not vacuous.
- **Do not treat a passing test suite as evidence.** Suites that always pass `MAX_BPS` hide this class entirely. Grep the test tree for the loss-bound argument before concluding the path is sound.
- **State severity bounds explicitly.** A 100% workaround means no permanent fund lock, so the honest grade is Medium unless an independent underfill or accounting path demonstrates direct loss. Do not fold an already-registered underfill issue into this root cause; keep the drafts separate.
- **Check audit scope, not just audit age.** Bundled audit reports often cover only the core contracts repo. A freshly pushed allocator or periphery repo can be novel even when the core is saturation-audited.
