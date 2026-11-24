# Host fuzz harness recipes

Techniques for running dynamic checks cheaply on this host without a full project build.

## Foundry `vm.ffi` that shells out to `cast`

Some repo test setups (`CommonTest` / deploy scripts) call `vm.ffi` with `["bash", "-c", "cast abi-encode ..."]`. On this host forge spawns WSL bash, whose PATH cannot see the Windows Foundry binaries, so the command dies with `cast: command not found` and every suite fails in `setUp()` for reasons unrelated to the code under test.

Fix once per host:

```bash
mkdir -p "$HOME/bin"   # git-bash home
# $HOME/bin/cast:
# #!/bin/sh
# exec "/mnt/c/Users/<user>/.foundry/bin/cast.exe" "$@"
chmod +x "$HOME/bin/cast"
wsl -d Ubuntu-24.04 -- bash -lc '/mnt/c/Users/<user>/bin/cast --version'  # verify

export PATH="$HOME/.foundry/bin:$HOME/bin:$PATH"
forge test --match-path 'test/<area>/<File>.t.sol'
```

Keep the wrapper for the session; it is a test-harness repair, not a change to audited code.

## rustc-only invariant harness for pure algorithms

For a state machine implemented in Rust that has no external-type dependence in the logic under test (circular buffers, replay rings, bit trackers, epoch math), do not build the workspace or add cargo dependencies:

1. Copy the target function's control flow verbatim into a standalone `.rs` file; simplify only framework types (`B256` -> `[u8; 32]`, `U256` expiry -> `u64`).
2. Add a seeded xorshift RNG (no crates) and an invariant checker after every successful operation.
3. Compile and run under WSL: `rustc -O harness.rs -o /tmp/h && /tmp/h`. Millions of iterations finish in seconds.
4. State plainly in the verdict which types were simplified: this is a differential/logic model, not a byte-exact reproduction of production code.

### Harness pitfalls

- Maintain reverse indexes incrementally. An O(n) per-iteration scan of the whole map (counting duplicate ring entries, for example) turns a 2M-iteration run into minutes and masks real findings behind timeouts. Keep a `HashMap<Key, count>` updated on insert/clear and assert on that.
- Stage campaigns to exercise rare branches on purpose: realistic cadence first, then saturated input (frozen clock, minimal gas, maximum throughput) so cap/full/overflow counters are nonzero. Report hit counts per pass; a branch with zero hits is untested, not sound.
- Bound retained history in the harness (`pending.retain(...)` plus a cap) or memory growth dominates long runs.
