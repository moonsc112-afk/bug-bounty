# Vyper fork harness when Foundry will not compile the target source

Use this when a Vyper target's own toolchain is heavy but the deployed logic must
exercise in a fork. Validated with Vyper 0.3.7 and Foundry 1.9 on Windows.

## Deploy Vyper code without Foundry's Vyper plugin

- Confirm the deployed source first: pull verified source from Etherscan HTML
  (`data-cname`/`data-csource`), Blockscout v2 or Sourcify, then byte-diff it
  against the repo commit named in the audit PDF after stripping whitespace.
  A byte-match means the code is already covered; do not build a harness on a
  version that is not live.
- If Foundry rejects the Vyper pragma with `No compiler version exists that
  matches the version requirement`, do not edit the pragma to a range: Foundry
  then falls back to compiling the `.vy` file as Solidity. Compile with the
  exact Vyper CLI instead and deploy the resulting creation bytecode:

```bash
PYTHONWARNINGS=ignore <vyper-bin> -f bytecode <Contract>.vy > bytecode/<Contract>.hex
```

`PYTHONWARNINGS=ignore` matters on Python 3.14 hosts: older Vyper emits
`ast.Str`/`Attribute n` DeprecationWarnings on stderr and Foundry treats that
noise as a compiler failure.

- In the Foundry test, read the hex, strip trailing newlines, parse with
  `vm.parseBytes`, and deploy with inline assembly `create(0, add(b,0x20),
  mload(b))`. Run the constructor this way; `vm.etch` only sets runtime code.
- To get an initialisable instance, deploy a minimal EIP-1167 clone over the
  compiled original. Use the FULL creation bytecode, not just the runtime
  prefix: `0x3d602d80600a3d3981f3363d3d373d3d3d363d73<address>5af43d82803e903d91602b57fd5bf3`.
  Deploying only `363d3d...` returns address zero with no error detail.
- Call the clone's `initialize` (or equivalent) directly, grant harness roles,
  then wire mocks through the protocol's own role setters rather than storage
  patches.

## Mock accounting: reconcile the identity before calling a bug

- A conservation invariant over a strategy harness is
  `accounted = real_assets - value_trapped_in_mocks - surplus_unaccounted`.
  Under-delivering strategy mocks trap value; over-returning mocks create
  surplus that the target contract may not credit to idle. Track both in the
  mock and assert them explicitly.
- When the identity fails, first check for trapped or surplus value in the
  mock. Only after those reconcile should a residual be treated as a target
  bug. Assert `accounted <= real_assets - trapped` as the safe direction and
  assert the exact surplus in the specific scenario test.
- Model oracle-dependent `convertToAssets`/`previewWithdraw`/`maxRedeem` as
  settable mock values and fuzz a wide price band plus queue order. A bound
  that holds here is evidence the target caps payouts by measuring the real
  token balance, not by trusting the reported redeemable amount.

## Before building on a function named in an old audit

Confirm every entrypoint your exploit path depends on still exists in the
deployed version's ABI. Audit reports are pinned to an older commit; a function
they criticised can be removed in a later release. Enumerate the compiled ABI
(`vyper -f abi`, or the explorer ABI) and issue a direct call to its selector.
A revert with no fallback means the premise is invalid, not that the call was
malformed.

## Run both modes

Run the suite locally first, then repeat with `--fork-url <public-rpc>` so the
result is defensible as fork evidence. Keep the harness in its own directory
with a short result note recording the exact commands and pass counts.
