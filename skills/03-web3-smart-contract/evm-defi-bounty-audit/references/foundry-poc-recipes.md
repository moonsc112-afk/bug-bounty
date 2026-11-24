# Foundry fork PoC recipes

Reusable patterns from building mainnet-fork PoCs against deployed contracts. Pair with `references/toolchain-windows.md` for setup.

## Reentrancy PoC with real signed orders
1. Fork with `vm.createSelectFork(vm.envString("RPC_URL"))` and call the **deployed** contract when it is already initialized and configured. A fresh deployment skips EIP-712 domain and fee setup.
2. Fund actors with `deal(token, actor, amount)` and approve the spender with `vm.prank(actor)`. A helper contract used as the caller must approve from its own function.
3. Sign with `vm.sign(pk, router.hashOrder(order))` when `hashOrder()` already returns the typed digest. Signature is `abi.encodePacked(r, s, v)`.
4. Put the nested call in a callback helper: store the nested calldata, and in `limitRouterCallback` call the router with `(bool ok, ) = address(router).call(nested)`. Record balances before and after to prove ordering.
5. Confirm the negative controls: replaying the same signed order after status mutation should be a no-op, and a second fill must still collect payment. If both hold, reentrancy alone is not a finding.
6. Check `payer == order.receiver` style skips before claiming free assets. If the skip requires the maker or integrator to choose that receiver, the program's out-of-scope rules likely cover it.

## Arbitrary external-call sink PoC
- Trace who funds the intermediate contract immediately before the call (`_transferIn` into the swap helper). Reproduce that transfer, then set the attacker-controlled external router and calldata.
- Assert three things: attacker received the tokens, intermediary balance is zero, and any approval granted during the call persists. Report the precondition (who supplies the calldata) in the same breath as the impact.

## Compiler and literal traps
- Run `forge test --match-contract <Name> -vv` and read the final `Suite result` line, not the compiler warnings or a piped tail's exit code.
- Use `cast --to-checksum-address` on every address literal that fails Solidity's checksum check; do not hand-edit letter case.
- Cast a non-payable address to `address payable` when the target contract has a payable fallback.
