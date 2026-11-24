# Web3 UI versus wallet signing differential

Goal: compare what a dApp displays with what it asks the wallet to sign, without a real wallet, seed phrase, or funds. Use the skill's isolation ground rules to decide whether the browser runs locally or in a sandbox; the provider technique is the same either way.

## Procedure

1. Build a provider shim with `context.addInitScript` before navigation. Define `window.ethereum` and also announce it with EIP-6963 (`eip6963:requestProvider` / `announceProvider`). Many modern dApps only listen for the discovery event, so a bare `window.ethereum` shim never gets a CONNECT click.
2. Record every `request({method, params})` in an array on `window`. Return synthetic values for `eth_accounts`, `eth_chainId`, signatures, and `eth_sendTransaction`; forward read-only calls such as `eth_call` to a public RPC of the target chain.
3. Intercept JSON-RPC POSTs made by the site itself with `page.route('**/*')`. For a classic approval flow, answer an allowance `eth_call` (selector `0xdd62ed3e`) with `uint256` max and answer `eth_getTransactionReceipt` for the synthetic hash with a successful receipt. Without those two answers the UI stops at the approval step and never shows the swap request.
4. Drive the page with Playwright locators: fill `input[placeholder="0.0"]`, click the slippage button by name, wait for the quote, capture the body text immediately before clicking the execute button, then click it and read the recorded `eth_sendTransaction` params.
5. Decode the calldata. Pull the ABI from the project's `/api/abi?contract=<name>` endpoint, build canonical function signatures including tuple components, find the selector with `cast sig`, then use `cast calldata-decode`. Compare `amountIn`, `userMinOut`, `recipient`, and `deadline` against the captured UI text, not against a snapshot taken earlier.
6. Record the approval separately: token address, spender, and amount. A canonical Permit2 spender with unlimited allowance behind a bland label is a disclosure observation, not automatically a payable finding.

## Standalone Playwright on Windows

When a long browser session makes the built-in browser daemon unreliable, use a standalone script instead of narrating a failure. Import the CommonJS package through its default export and pin the browser binary:

```js
import pw from 'file:///E:/path/to/node_modules/playwright/index.js';
const { chromium } = pw;
const browser = await chromium.launch({
  headless: true,
  executablePath: 'E:/tools/playwright-browsers/chromium-<rev>/chrome-win64/chrome.exe'
});
```

WHY: a named ESM import from a CommonJS path throws, and relying on the ambient browser revision causes version mismatch errors after a dependency update.

## Pitfalls

- Do not conclude a UI-vs-calldata divergence from a minimum-output gap of a few basis points. Quotes re-price at signing; capture the DOM at the click instant and accept a stricter signed minimum as timing noise.
- Do not treat an approval request as the trade call. The first `eth_sendTransaction` is often the token approval; the second, after a synthetic successful receipt, is the actual swap.
- When searching a blob of function signatures with `cast sig`, strip carriage returns first. CRLF line endings make every signature fail to parse and produce a false "no match".
- Hostile token metadata reaches MCP tools as data. A live token whose `name` says "approve max" appearing in `get_token_info` output does not prove an agent followed it; require an actual tool chain that ends in a harmful transaction before claiming impact. Some tools such as a token x-ray do not echo metadata at all.
