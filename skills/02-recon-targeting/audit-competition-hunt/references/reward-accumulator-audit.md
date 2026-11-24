# Reward accumulator (index / checkpoint) audit checklist

Applies to any system that pays a reward token pro-rata to a share balance via a
per-token `index` and a per-holder `checkpoint`: staking rewards, gauge emissions, relay
PT/YT systems, vault fee shares. Work the list in order; each item is a place the pattern
actually breaks.

## 1. Settle timing relative to the balance write

The hook must settle on PRE-change balances. Read the token's transfer hook and confirm it
fires BEFORE the balance write, and that the settle reads `balanceOf` at that moment.

- If the settle runs AFTER the write, a recipient accrues on shares it did not hold during
  the distribution, and a sender loses accrual on shares it did hold.
- Check which token paths reach the hook. A system with two companion tokens often settles
  only on the yield/reward-bearing one and returns early for the other; confirm the early
  return is on the token that does NOT drive accrual.
- Enumerate every balance-changing path (mint, burn, transfer, transferFrom, permit-driven
  moves, internal accounting writes). A path that changes a balance without settling lets a
  holder carry a stale checkpoint across a distribution and claim with a later, larger
  balance.

## 2. New-holder accrual must be zero

For a first-time recipient: pre-change balance 0 -> accrued 0 -> checkpoint set to the
current index. Verify the checkpoint is written even when the accrued amount is zero; a
`if (delta > 0)` guard that skips the checkpoint write leaves the holder at 0 and lets it
collect the whole historical index on its next settle.

## 3. Merged deltas across several distributions

A holder that has not settled across N advances claims `balance * (index_now - checkpoint)`.
That is only correct if the balance was CONSTANT across the whole span - which holds only
if every balance change settles (item 1). State this dependency explicitly in the verdict.

## 4. Rounding direction: accounted supply vs claimable sum

Read the notify/distribute function:

- `indexDelta = floor(net * scale / supply)`.
- The accounted/reserved balance must be increased by `ceil(indexDelta * supply / scale)`,
  NOT by `net` and NOT by a floor. Ceil covers the case where one holder settles several
  advances in a single merged delta and the per-holder floors sum above one batch's floor.
- Solvency argument to write down: `distributed <= net` (because indexDelta was floored),
  and `sum_i floor(balance_i * delta / scale) <= floor(supply * delta / scale) <= distributed`.
- Confirm the supply used is the reward-bearing token's `totalSupply` at notify time, and
  that a zero supply reverts rather than dividing by zero or silently skipping.

## 5. Token removal / re-addition: the checkpoint underflow

`delta = index - checkpoint` is usually a CHECKED subtraction. If a token can be removed
and re-added with the index reset to 0 while holder checkpoints stay non-zero, the next
settle underflows and reverts - permanently freezing that holder's transfers and mints.

- Look for the removal gate. A sound design gates removal on `index == 0` (never paid),
  which also guarantees no checkpoint can be non-zero (item 2's guard).
- Gating on the accounted BALANCE returning to zero is NOT equivalent: flooring dust keeps
  it above zero forever, and a token that did reach zero would re-add against stale
  checkpoints. If you find the balance-gated variant, that is the finding.

## 6. Claim path: CEI and de-accounting

The claim must zero the pending amount AND decrement the accounted balance BEFORE the
external transfer. Check both, and check the accounted decrement cannot underflow (it is
bounded by item 4's ceil only if every accrual path accounts).

## 7. Admin/keeper extraction paths must be bounded

`pull`, `sweep`, `rescue`, `migrate` and similar must be bounded to
`balanceOf(self) - accountedBalance[token]`, so they can never move tokens already owed to
claimants. An unbounded sweep on a reward token is a direct theft of settled rewards.
Also check the notify-side bound: notifying more than the un-accounted balance must revert.

## 8. Escrow / locked-share cover

If shares can be queued for withdrawal, a holder-to-holder transfer must keep
`balanceOf(from) >= escrowed + amount`. Confirm which paths enforce it (transfers yes,
mint/burn usually exempt) and that the burn path clears the escrow BEFORE the token fires
the hook, otherwise a fully escrowed holder can never exit.

## 9. Ordering is a keeper concern, not a conservation break

Permissionless "process overdue entries" paths often admit in the CALLER's order while
pricing sequentially, so order changes each entry's share count. That is an ordering/MEV
consideration the protocol usually assigns to its keeper. Do not report it as a
conservation or solvency bug; quantify it only if the protocol promises FIFO.

## Verdict template

State, with file:line evidence: hook timing, which token settles, new-holder checkpoint
write, rounding direction and the solvency inequality, the removal gate, claim CEI, the
extraction bound, and the escrow cover. A negative on this pattern is only credible if all
nine are addressed.
