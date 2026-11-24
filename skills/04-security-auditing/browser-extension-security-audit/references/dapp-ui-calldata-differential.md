# dApp UI versus wallet calldata differential

Use for a bounty surface where the website has no published source and the accepted
impact is "the interface shows one trade and asks the wallet to sign another".
Run it with a fake injected wallet. No operator key, account or real funds are
needed, and nothing is broadcast.

## Setup

Use a scripted Playwright browser rather than an interactive browser session for
the whole flow. Point `PLAYWRIGHT_BROWSERS_PATH` at the installed browser tree and,
if the repo's Playwright expects a different Chromium revision than the one on
disk, launch with an explicit `executablePath`.

## Procedure

1. Inject an EIP-1193 provider with `context.addInitScript`. It records every
   `request()` call, returns a deterministic fake account and chain id, forwards
   read-only methods (`eth_call`, `eth_getBalance`, `eth_blockNumber`, ...) to a
   public RPC, and captures `eth_sendTransaction` and signing requests instead of
   broadcasting them.
2. Announce the same provider over EIP-6963: listen for
   `eip6963:requestProvider` and dispatch `eip6963:announceProvider` with an
   `info` object plus the provider. Do this before navigation. A CONNECT button
   that ignores `window.ethereum` is usually using provider discovery, and the
   shim will otherwise look absent.
3. Drive the UI with locators: skip any intro overlay, click CONNECT, fill the
   amount input through the native value setter plus an `input` event, pick the
   slippage preset, and wait for the quote to settle. Read the whole `body.innerText`
   and keep the EXPECTED OUT and MIN RECEIVED lines captured immediately before
   the signing click; quotes can re-price between DOM capture and click.
4. Advance past the approval step. A wallet-provider shim alone is not enough if
   the site polls its own RPC: add `page.route` for JSON-RPC POSTs and answer
   `eth_call` to the allowance selector (`0xdd62ed3e`) with max uint, and
   `eth_getTransactionReceipt` for the captured fake hash with `status: 0x1`.
   Without this the interface stays on its "APPROVE TX" state and never exposes
   the swap calldata.
5. Capture every `eth_sendTransaction`. Expect one ERC-20 `approve` and one swap.
   Record the `to`, `data`, gas fields and the UI text at that moment.
6. Identify the swap selector before decoding. Fetch the program's published ABI
   (`/api/abi`, or the repo ABI), build canonical signatures including tuple
   components, run `cast sig` over that list, and match the selector. Then use
   `cast calldata-decode "<signature>" "<data>"` to read `amountIn`, `userMinOut`,
   `recipient`, `deadline` and permit fields.
7. Compare each security-relevant field with the UI: input token and amount,
   output token, recipient, minimum received, slippage and deadline. Classify any
   difference by cause before calling it a finding: deliberate caller choice,
   reprice/rounding between capture and click, or a real field substitution.

## Verdict discipline

- An unlimited approval to the canonical Permit2 behind a terse "Approve" label is
  a disclosure concern, not an accepted signing mismatch. It becomes a finding only
  if the calldata encodes a different recipient, token, amount or minimum than the
  interface led the caller to sign, or if the quote diverges from execution.
- A minimum in calldata a few ten-thousandths above the displayed value is stricter
  than shown and usually a reprice. Record the exact numbers and do not escalate it
  without evidence of a worse-than-displayed fill.
- Keep raw request logs and the decoded field table as evidence; never turn a
  display-only observation into a submission draft.
