# Pattern catalog (quick probe reference)

Condensed from the `web3-audit` skill in `elementalsouls/Claude-BugHunter`
(skill text CC BY 4.0). Use as a prompt for what to inspect, not as a scanner
to run blindly. Adapt paths to the repo under review.

## 1. Accounting state desync

Two state variables intended to stay equal diverge after one code path.
`real_value = A - B`; if A moves without B, value appears out of nowhere.

Variants worth testing:

- **Phantom yield**: supply is decremented before the backing transfer, so
  `backing.balanceOf(this) - totalSupply` yields a fake surplus. Check the
  order of supply changes versus external balance reads.
- **Fast path early return**: the cheap branch transfers and returns before
  updating cumulative debt, weights, or totals; only the slow branch updates
  everything. Diff the two branches field by field.
- **Wrong order**: a share price is computed before assets are added, then
  assets are updated; the new depositor gets the old rate.

Probe:

```bash
grep -rn "totalSupply\|totalShares\|totalAssets\|totalDebt\|rewardPerShare\|cumulative" contracts/
grep -rn "\breturn\b" contracts/ -B4 | grep -B4 "if\s*("
```

For each early return, list which state writes appear only after it. Turn each
missing write into an invariant: `sum(balances) == accounting_total`.

## 2. Access control

- Missing modifier on a sibling mutator (the dominant form).
- `exists(id)` used where `ownerOf(id) == msg.sender` was intended.
- `if (cond) _;` silently swallowing a failure where `require(cond)` was meant.
- Implementation contract never initialized, so `initialize()` is open.

Probe: enumerate every `external`/`public` mutator and record its modifiers;
the outlier in an otherwise uniform family is the lead.

## 3. Incomplete code path

Compare the full function family, not one function. Update functions that
forget a refund; partial fills leaving tokens stuck; `mint()` bypassing a cap
that `deposit()` enforces. Any branch that exits before a cleanup step is a
candidate.

## 4. Off-by-one and boundaries

Test `<` against `<=`, `>` against `>=`, division rounding direction, zero,
one, max uint, empty arrays, and the exact threshold where a state change
flips. Ignore "impossible" magnitudes only after computing the required ratio.

## 5. Oracle and price

- No `updatedAt`/staleness check, or a fallback that never expires.
- Pyth-style feeds consumed without the confidence interval.
- TWAP window shorter than the time an attacker can hold a flash-loaned
  imbalance in a shallow pool.
- A single source where the primary is sound but the secondary (internal
  oracle, thin LP, fallback) is not. Audit the failover chain.

## 6. ERC-4626

Near-empty vault: first depositor inflates share price so later depositors
round down to zero shares. Check virtual-share/decimals offsets and minimum
liquidity locks. Check that a share `transfer` also moves whatever stake,
lock, or reward record the shares represent.

## 7. Reentrancy

Checks-Effects-Interactions is necessary, not sufficient. Look for a view
function that reads a balance mid-state-change (read-only reentrancy), and for
cross-function paths where two functions share an accounting variable.
Hooks and ERC-777 callbacks reintroduce entry points.

## 8. Flash loan

Borrow, distort a price source, extract value, repay. The vulnerability is
usually in the price or the share math, not the loan itself. Check whether a
protocol assumes pool balances reflect "real" liquidity.

## 9. Signature replay

Nonce present and consumed atomically? Chain id and verifying contract bound
into the digest? Under EIP-7702, can the same signature authorize a different
delegation target?

## 10. Proxy and upgrade

Compare storage layouts across versions for collisions; confirm the
implementation is initialized; verify `delegatecall` targets cannot be
attacker-supplied. Check the admin path separately, but remember that most
programs exclude admin-malice findings.
