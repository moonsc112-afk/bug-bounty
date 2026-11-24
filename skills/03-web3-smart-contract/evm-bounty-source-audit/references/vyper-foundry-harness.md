# Vyper targets in a Foundry harness

Use when the bounty target is Vyper-based (Yearn-style vaults, Curve-style AMMs) and
the audit needs a runnable fork or invariant harness but Foundry's Vyper compiler
detection will not accept the pinned pragma. The pattern below keeps the audited
`.vy` source byte-for-byte and avoids editing it to suit the harness.

## Compile with the pinned Vyper outside Foundry

- Install the exact compiler in an isolated venv, not the global one:
  `uv venv <dir>/v037 && uv pip install --python <dir>/v037/Scripts/python.exe vyper==<pinned>`.
  Keep the source's `# @version <pinned>` pragma unchanged; Foundry rejects an
  exact pragma with "No compiler version exists" when its own compiler list is
  empty, and changing the pragma to a range makes Foundry try to compile the
  `.vy` file as Solidity.
- Compile to bytecode with the pinned binary:
  `PYTHONWARNINGS=ignore <dir>/v037/Scripts/vyper.exe -f bytecode <file>.vy > <file>.hex`.
  The env var matters under newer Python: Vyper 0.3.x emits `ast.Str`/`.n`
  deprecation warnings that Foundry treats as a failed compiler run.
- Strip whitespace from the `.hex` file before reading it in a test.
  `vm.parseBytes` fails on a trailing newline and dumps the entire hex blob into
  the error message. Normalise to a single `0x`-prefixed line.
- Keep the `.vy` files out of `src/` so Foundry never tries to compile them as
  Solidity. Store them plus the `.hex` files under `bytecode/` and read them at
  test runtime (`vm.readFile`, `vm.parseBytes`, then `create` in assembly).

## Deploy a constructor-blocked Vyper implementation

- Some Vyper implementations set a sentinel in their constructor precisely so a
  direct `initialize` cannot be called (`self.asset = self`,`assert self.asset ==
  empty(address)` in `initialize`). Deploy the compiled original, then deploy a
  minimal EIP-1167 proxy to it and call `initialize` through the proxy. This
  matches how the protocol's own factory deploys instances.
- The proxy creation bytecode MUST include the init-code prefix
  `3d602d80600a3d3981f3` before the runtime bytes
  `363d3d373d3d3d363d73<20-byte impl>5af43d82803e903d91602b57fd5bf3`.
  Using only the runtime bytes as init code makes `create` return address(0).
- Grant the harness every role bit on the clone before exercising privileged
  setup (`set_role(address(this), (1 << N) - 1)`). This is a test rig, so say so
  in the report: a bound proven on a fresh clone is a mechanism test, not a PoC
  against live funds.
- Run the same suite locally and with `--fork-url <public-rpc>`. The fork run
  costs seconds and proves the harness is not relying on local EVM state.

## Mock design for loss and profit-locking invariants

- When testing a vault whose redeem path measures `maxRedeem` from a strategy and
  then compares it to the real token balance, give the mock two independent knobs:
  `payoutBps` (fraction actually returned) and `reportMultiplier` (inflation of
  the reported redeemable amount). Over-reporting with full payout tests the
  "claims too much" case; over-reporting with reduced payout tests realized loss.
- Track a `trapped` accumulator in the mock: when the strategy burns `s` shares
  but transfers only `s * payoutBps / 10000`, the difference stays physically in
  the strategy. The correct conservation identity for the harness is
  `totalIdle + totalDebt == vaultTokenBalance + strategyTokenBalances - trapped`.
  Without the `trapped` term a correct realization of loss looks like a broken
  invariant and starts a false lead.
- Prove the bound analytically before fuzzing: with `W` requested from a strategy
  and `X` actually received, the vault must credit idle by `X` and reduce debt by
  `W`; over-reporting changes `W`, never `X`, because the vault re-measures the
  token balance across the external call. A `maxLoss == 0` withdraw must revert
  for any `X < W`. Fuzz payout, multiplier, gain/`process_report`, and queue
  order only after that derivation is written down.
