# Share-token / LST audit checklist

For liquid-staking tokens, ERC4626 vaults, lending-pool tranches and any
protocol that mints a *share* against pooled assets. Work these in order; each
is a real loss-of-funds class.

## 1. Share/asset rounding direction
- assets->shares on deposit and shares->assets on withdraw must round DOWN
  (the user gets fewer), never up. Compute in wide integer math (U256) then
  cast down; a down-cast after mulDiv is a silent truncation bug.
- Round-trip fuzz both directions: `convertToAssets(convertToShares(x)) <= x`
  and `convertToShares(convertToAssets(y)) <= y`.
- Round-UP variants legitimately exist for internal accounting (e.g. a debt
  index); confirm which path uses which, do not assume all round the same way.

## 2. First-depositor / donation inflation
- Mitigation is a nonzero initial share supply (mint an INIT amount to the
  contract at init) OR a virtual assets/shares offset (VAS).
- If neither is present, test: donate -> tiny first deposit -> the next
  depositor's shares round to 0 -> their deposit is captured.

## 3. Cross-contract callback ACL (the classic critical)
- Every callback an external counterparty invokes (staking-pool balance,
  unstake result, token receiver) must authenticate the caller: `#[private]`
  in near-sdk, a msg.sender / predecessor check in Solidity, a signer check on
  Solana. A missing check = forged balances or state from an attacker contract.
- Internal share mint/burn helpers must NOT be reachable as external endpoints.

## 4. Reward / fee distribution conservation
- Total minted == total allocated; the last recipient absorbs rounding dust.
- Any bps/weight table must be capped (sum <= 100%) AND its setter access-
  controlled; an uncapped table lets a privileged caller over-mint and dilute
  holders.

## 5. External accounting sync (slashing / loss) - the dead-edge check
- When a remote balance can DECREASE (slashing, loss), the sync path must
  either mirror the decrease first or safe-revert. Confirm the decrease is
  REACHABLE on the target chain before treating it as a finding: "reverts on
  slashing" is a non-issue on a chain with no active slashing, and safe-revert
  is not fund loss.
- Mirror stake/unstake success AND failure callbacks symmetrically, and keep a
  guard flag that blocks overlapping actions per position.

## 6. Reentrancy
- Share mint/burn around external calls: check for a reentrancy guard and that
  the share price is not read after an external call.

Verdict note: a standard, well-constructed LST that passes 1-6 is a legitimate
verified-negative - record it and move on.
