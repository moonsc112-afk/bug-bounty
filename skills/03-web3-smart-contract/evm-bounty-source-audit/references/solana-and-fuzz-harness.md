# Solana bounty acquisition + standalone invariant-fuzz harness

## Repo acquisition + reading/build split
- List org repos: `curl https://api.github.com/orgs/{org}/repos?per_page=100&sort=pushed` -> name/language/pushed_at/size. Freshest pushed_at = best odds.
- Clone shallow into WSL-native home (inside the E: VHDX): `git clone --depth 1 https://github.com/{org}/{repo}.git`. Unshallow for history: `git fetch --unshallow`; `git log --name-only --pretty=format:'@@ %h %ad %s' --date=short -12` -> recently-changed src files.
- Reading copy for Windows tools: `cp -r repo /mnt/e/audit/{protocol}/` (read_file/search_files work on E:\audit\...). Build copy stays WSL-native (~/audit/...) — cargo/anchor on /mnt/e (9p) is slow.
- WSL command pitfalls (full rules in wsl-secondary-drive-install skill): inline `wsl -- bash -c '...$var...'` through git-bash eats $vars/quotes -> ALWAYS run a script file `wsl -- bash /mnt/e/.../script.sh`. Non-login scripts must `. "$HOME/.cargo/env"` explicitly. Set CARGO_TARGET_DIR to a native path for /mnt/e source builds.
- Toolchain: repo rust-toolchain.toml pins the Rust version (rustup auto-installs). Older anchor/solana crates may not build on a very new stable — use the pinned toolchain for the real program; a standalone math harness can use current stable.

## Standalone fuzz harness (avoid the heavy framework build)
Pattern: the bug-prone code is usually PURE math (share/amount conversion, rounding, reward accrual) depending only on a small math crate. Copy those functions VERBATIM into a minimal crate; replicate the state machine that calls them; fuzz invariants. This tests the real math without compiling anchor-lang/solana-sdk (15-30 min) or deploying a fork.

Cargo.toml deps match the source's math crate exactly:
- Decimal-style (kfarms): `decimal-wad = "0.1.9"`, `uint = "0.9.5"`, `rand = "0.8"`.
- Fraction-style (klend/kvault): `fixed = "1"` (Fraction = fixed::types::U68F60, 60 frac bits), uint, rand.
- `[profile.release] overflow-checks = true` (mirror the program; underflow/overflow panics so catch_unwind catches it).

Steps:
1. Copy the exact conversion functions verbatim (e.g. convert_amount_to_stake / convert_stake_to_amount / full_decimal_mul_div / u64_mul_div; or Fraction full_mul_int_ratio[_ceil] + BigFraction mul/div + CollateralExchangeRate conversions). Verbatim = no transcription drift.
2. Replicate the state machine on plain structs (Farm/User with the same fields) using those functions — same arithmetic, same rounding direction, same update/drop order.
3. Seeded RNG (StdRng::seed_from_u64) drives random op sequences: deposit/stake/activate/unstake/withdraw/donate(increase_total_amount)/fractional-unstake, multiple users.
4. Assert invariants after EVERY op:
   - stake conservation: sum(user active) == farm total_active_stake; sum(pending) == total_pending_stake.
   - solvency: sum(convert_stake_to_amount(user stake)) <= pool amount (active and pending).
   - no rounding profit: total withdrawn <= total deposited + donations.
   - rounding-error paths: disinvest >= actual_send (no underflow); actual_send <= send.
5. Wrap each sequence in catch_unwind(AssertUnwindSafe(...)); count violations; print seed + op sequence on failure.
6. Build release with CARGO_TARGET_DIR native; run e.g. 20000 sequences x 60 ops (stake) or 2_000_000 iterations (rounding). 0 violations = strong soundness evidence.

## EVM minimal Foundry invariant harness (isolate the core, skip the full program)
When the bug-prone logic is a self-contained contract cluster (e.g. a PT/YT dual-token vault), build a MINIMAL Foundry project around just that cluster instead of the whole protocol (which pulls morpho-blue/bridge deps and a heavy deploy).

Setup:
1. Copy only the needed src subtrees preserving relative import paths (e.g. `request/abstract/` + the concrete `Vault.sol` + `libs/request/` + `libs/common/` + `libs/Constants.sol` + `interfaces/request/` + `interfaces/integrations/`). DROP the top-level concrete contract that wires in heavy deps (e.g. Request.sol with OfferReceiver/EIP712/morpho) and any standalone interface that imports a dropped lib (grep the copied tree for `lib/morpho`/external imports and delete self-referential offenders).
2. Install the math/util libs at the EXACT versions in the repo's `foundry.lock` (read it for tag+rev): `git clone --depth 1 --branch <tag> https://github.com/vectorized/solady.git` (and forge-std) into `lib/`. Source imports like `lib/solady/src/...` resolve from project root.
3. `foundry.toml`: pin `solc_version` to the repo's (e.g. `0.8.34`), `auto_detect_solc = false`, `ignored_error_codes = [2424, 8429]` for dep warnings; `[invariant] runs/depth`, `fail_on_revert = false`.
4. Write a CONCRETE controller extending the abstract base: implement the abstract internal hooks (`_asset`/`_canWithdraw`/`_syncWithdrawalStatus`/`_ptToken`/`_ytToken`) + interface metadata (`name`/`symbol`/`decimals`) + test helpers (`mintShares`, `setWithdrawEnabled`). Read the interface (ITokenController/IVaultController) first to implement every required function.
5. **Pitfall — `_disableInitializers()` in a constructor blocks direct initialization.** Deploy the implementation, then `LibClone.clone(address(impl))` (solady) and call `initialize(...)` on the fresh-storage proxy. Immutables (e.g. an `_IS_YT` flag) live in bytecode so clones share them correctly. Wiring order: asset -> impls -> clones -> controller(asset, ptClone, ytClone) -> initialize clones with controller -> fund + mint + enable withdrawals.

### Foundry fuzz-harness compile traps

- Importing a test CONTRACT does not import that file's file-level constants. Reuse the builders by extending the test contract, but use literals (or explicit constant imports) for module-level constants.
- Do not call `fail()` inside a `try` block to assert a revert: `catch` swallows its revert and the test passes falsely. Use `vm.expectRevert("reason")` in a non-`view` test instead.
- Mutating `bytes` needs an explicit `bytes1(uint8Value)` cast. Calling a library extension method needs `using LibName for Type;` in the harness contract.
- Add a positive control for every negative fuzz: assert the unmutated fixture is accepted before running mutations. WHY: a harness whose cache, hints or fixture setup silently fails will revert on every case and report zero failures, which looks like soundness evidence but proves nothing.

WHY: each of these compiles or runs cleanly enough to look like coverage while the intended assertion never executes.

Handler + invariants:
- Handler `is Test` (gives `vm`/`bound`). Ghost accounting: `initialBalance`, `totalDonated`, `totalRedeemed` — measure redeemed as the controller's asset-balance delta around each redeem/withdraw call (update ghost AFTER the call so a revert rolls it back).
- `vm.prank(user)` before `vault.redeem(shares, user, user)` so caller==owner (no allowance path); bound amounts to the user's balance; guard zero-balance users with an early return.
- Ops: redeemPT/redeemYT/withdrawPT/withdrawYT + donate (mint asset to controller = yield/repayment) + mintShares (dilution / under-collateralization cases).
- Invariants: **conservation** (`balance == initial + donated - redeemed`) is the strongest catch-all for wrong transfer amounts; **solvency** (`redeemed <= initial + donated`); protocol split rule (e.g. PT priority `pAssets == min(balance, ptSupply)`); **supply conservation** (`totalSupply == sum user balances`); **no-overclaim** (`convertToAssets(allShares) <= balance`).
- Exercise BOTH signs of any accounting report the contract exposes. A mint-only or yield-up harness never reaches the burn branch, so a NAV drop or loss report stays untested. Give the strategy a controllable exchange rate, seed the burn sink with enough balance, and assert the recorded position and the token balance both move in the expected direction, then restore the rate and assert the reverse. WHY: the negative branch often carries the more severe accounting mistake, and a positive-only invariant suite passes without touching it.
- Run `FOUNDRY_INVARIANT_RUNS=1024 FOUNDRY_INVARIANT_DEPTH=80 forge test --match-path test/<file>` (~80k calls, ~30s). Reverts are expected edge cases (fail_on_revert=false). All-pass = verified soundness.

## Interpreting results
- These protocols are heavily audited (Certora/OtterSec/Offside/Sec3/ChainSecurity). Expect invariants to HOLD. A passing fuzz is a verified negative, not a failure — report it and move to the next-best-odds target.
- Theoretical edge cases (e.g. Ord mis-ordering only when exponent diff exceeds the producer's bounded range) are often UNREACHABLE — check input bounds before claiming exploitability.
- Trusted-role functions (Signer + has_one delegate/admin) are not external vulnerabilities even with unchecked arithmetic.
