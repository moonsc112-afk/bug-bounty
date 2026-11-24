# Deployed-source provenance and bytecode equivalence

Use when a local source tree does not byte-match the deployed implementation, or before claiming any static result or PoC against a deployed address. A finding built from the wrong tree is not a finding.

## Procedure

1. Resolve the implementation behind a proxy with `eth_getStorageAt(proxy, 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc, 'latest')` and take the low 20 bytes. Then `eth_getCode(impl, 'latest')` for the live runtime bytecode.
2. Ask Sourcify for verified source: `https://sourcify.dev/server/v2/contract/<chainId>/<address>?fields=all`. The `fields=all` suffix is required; without it the response only carries match metadata. Accept only `runtimeMatch` and `creationMatch` equal to `exact_match`; a bare `match` means runtime bytes agree but metadata differs, so record it but do not call it exact verification. A 400 for a scope address can mean a proxy without its own verification entry, or simply a contract Sourcify never indexed: check the EIP-1967 slot and query the implementation first, then try Blockscout `https://eth.blockscout.com/api/v2/smart-contracts/<address>` before declaring the source unavailable. Invoke that call with `curl` (a plain `curl` in a subprocess succeeds where a Python HTTP client is rejected on User-Agent) and read `name`, `file_path`, `is_verified` and the ABI function list to identify the contract. When `is_verified` is true, the same response's `source_code` field carries the complete verified source; save it verbatim rather than reconstructing it from the ABI.
3. Fetch the response with `curl`/`urllib`, not a page-extraction tool: the payload is megabytes of source and an extractor will truncate it into malformed JSON. Save each response verbatim.
4. Rebuild a source tree by merging the `sources` map of every contract under test: key by source path, dedupe identical content, and stop if the same path has two different hashes. If a shared file such as `BoringVault.sol` has two different hashes, do not merge at all: keep one source tree per verified contract so each harness compiles against the version that was actually deployed. Write files with the original paths so imports resolve.
5. Recompile with the exact settings in the response `metadata` (`compiler.version`, `optimizer`, `evmVersion`), not the host project's defaults.
6. Compare compiled `deployedBytecode.object` to `runtimeBytecode.onchainBytecode` after stripping the final 43 bytes (CBOR metadata tail). Equal means executable code is identical and the fuzz results can be claimed against the deployment.
7. A first difference exactly at `len - 43` is only the metadata hash. A difference earlier, or a different code length, means the source really differs.

## Audited-commit identity (cheap precheck before reading audit PDFs)

When the local repo is shallow/grafted, fetch full history first (`git fetch --unshallow`). Then compare the source BLOB, not just the commit message: `git rev-parse <last-audited-commit>:src/<File>.sol` against `git rev-parse HEAD:src/<File>.sol`. Equal hashes prove the deployed source reviewed locally is the exact code the auditors saw. List `git log --oneline <audited>..HEAD` and `git diff --stat <audited> HEAD` and confirm every post-audit commit touched only `script/`, config or `test/`; if `src/` changed, the audit no longer covers the deployed code and must be re-dated.

This settles the "are the four PDFs even about this code?" question in two commands. Check it before spending time diffing audit editions: duplicate reports that differ only in date and commit hash are TWO documents, not four independent reviews. Extract each PDF with `pdftotext -layout` first and diff the text to find unique reports, then read the summary and scope-exclusions sections of each unique one.

## Explorer quirks and diamond staleness

- Etherscan V2 `getsourcecode` returns `SourceCode` as standard-json wrapped in one extra brace pair. Strip one leading and one trailing brace before `json.loads`; a parse failure here does not mean the contract is unverified.
- Explorer verification can lag a diamond's live facet set. Enumerate `facetAddresses()` and call a getter that exists only in the new feature; a non-zero result proves the feature is live even when the verified `System.sol` still lacks the new fields. Do not conclude the feature is undeployed from stale verified source alone.
- When live facet bytecode does not match local `deployedBytecode`, report that as a provenance caveat rather than a bug: compiler settings, library linking and dependency versions can all differ. Use on-chain behavior getters for liveness and reserve byte equality for claims that need exact source equivalence.

## Reading constructor config with no public getter

Upgradeable contracts often expose no getter for `endpoint`, `accountingReceiver`, or role addresses. Read the ERC-7201 namespace slot constant from the source, then `eth_getStorageAt(proxy, slot + fieldOffset, 'latest')` walking the struct field order. Remember Solidity packs a trailing `uint32` into the same slot as a preceding `address`: parse both out of one 32-byte word. Verify the result against a known on-chain value before trusting it.

## Fork test for a cross-chain compose handler

- Build the LayerZero compose message in the codec's order: `nonce(8) || srcEid(4) || amountLD(32) || composeFrom(32) || composeMsg`, where `composeMsg = abi.encode(SendParam, minMsgValue)`.
- Fund the composer through its real roles rather than guessing storage slots: have the accounting receiver mint to the vault, then prank the vault to transfer the OFT to the composer.
- For `lzReceive` tests on an OApp, call `setPeer(srcEid, sender)` on the receiver first. `_getPeerOrRevert` otherwise reverts `NoPeer`, which reads as a broken message path rather than a missing setup step.
- `vm.prank(endpoint)` and call `lzCompose` with the real endpoint address read from storage. This exercises the composer's `msg.sender == endpoint` guard; it does not exercise the endpoint's own validation. Say that limit in the report.
- Assert the downstream effect, such as shares credited to the intended recipient, and add a negative test that a non-endpoint caller reverts.

## Fork test for a backend-signed quote flow

When an entrypoint verifies an EIP-712 signature from an off-chain signer whose key you do not have, do not skip the flow or stub the verifier. On the fork, `vm.prank(owner)` the admin setter that rotates the signer to `vm.addr(TEST_PK)`, then build the digest exactly as the contract does (its type hashes, its `hashQuote` getter, and a live-computed domain separator), sign with `vm.sign(TEST_PK, digest)` and pass `abi.encodePacked(r, s, v)`. Change only the signer key so the test still exercises the real role configuration, and state that substitution in the report.

Public RPCs commonly reject historical-state requests with an archive-token error. For a state-dependent fork test that does not need a particular block, call `vm.createSelectFork(url)` with no block number instead of pinning one; this avoids the archive requirement while still running against live state. Record the block Forge reports in the test output so the result remains reproducible.

For a settlement path, capture token balances before the submit, not before the fill: the submit already moves the offer asset, so measuring afterwards silently drops the deposit leg. Simulate any per-call allowance the privileged manager normally grants with `vm.prank(sourceAddress)` on the token's `approve`, and set it to the exact fill total. An allowance larger than the filled amount tripping a residual-approval guard is confirmation of the invariant, not a bug.

## Pitfalls

- Same solc version with a different metadata hash is a different source, not an optimizer setting. Do not explain it away and proceed.
- `web_extract` silently truncates large JSON responses into a head/tail string that cannot be parsed; use a direct HTTP client for source and bytecode payloads.
- A verified source for one chain does not transfer to another chain's deployment of the same protocol. Repeat the bytecode check per chain even when the labels and addresses look familiar.
- A Sourcify `sources` map is the compilation closure of the target, not a full repository. Proxy bases such as `Proxy.sol` or `ERC1967Proxy.sol` are commonly absent, so a harness cannot import them: write a minimal inline EIP-1967 proxy (ERC1967Utils slot plus a delegatecall fallback) instead. The same rule applies to hand-written mocks: an ERC4626 mock must also pass the ERC20 name/symbol constructor args, or the build fails on an indirect base rather than on the code under test. Copy stub signatures exactly from the interface file: a Solidity enum ABI-encodes as `uint8`, so substituting `bytes32` changes the selector and makes handlers revert before reaching the code under test. Confirm non-zero handler call counts after every campaign.
- State plainly which paths the fork test covers and which it does not; a pranked endpoint is not end-to-end cross-chain delivery.
