# Reading a hardened deployment: money-path loop, falsification ledger, park + watch, cross-chain bridge legs



Context: the repo is private / the scope is "all deployed contracts" and you already harvested the verified deployed sources (see harvesting-a-whole-deployment.md). Per-hypothesis PoCs cost hours and most hypotheses die on a close read. This loop front-loads reading so the few surviving hypotheses get the expensive treatment.



Maintenance rule: SKILL.md sits at the ~100K-char cap - every new lesson goes into references/, and SKILL.md only gets pointer lines.



## 1. Money-path read order (front-load where funds move)

1. Settlement engine: order struct + EIP-712 typehash + fill functions (open/close/borrow/repay/deposit/withdraw variants), flash callbacks (`onFlash`-style), fill arithmetic (preview/record), per-order fill ledger (`filledSellAmounts` style).

2. Position manager: deposit/withdraw/borrow/repay, flash flows (`*FlashAnd*For`), batch executor (`engineBatch`-style action arrays), hold/allowance primitives (`engineHeld`, `engineDebitAllowance`, tokenizer exceptions), liquidation entry (`liquidateFlash`-style).

3. Liquidation RFQ: pre/post HF gates, fairness cap (seize <= repay x (1+bonus)), repay cap corridor, residual dust rules, filler/protocol fee split.

4. Signature surfaces: EIP-712 meta modules (actions via user sig), session manager (session config, ordered-batch nonce bitmap, per-token allowance, executor binding), matched/batch modules that take raw order structs plus auth blobs.

5. Periphery (rarely pays - read last): marketplace offers/listings, merkle ACL gates, oracle router + capped/NAV feeds, yield wrapper, token/NFT.



## 2. Gate-chain notation - record it per money function

- callers: modifiers/allowlists (`onlyX`, engine/liquidation-module sets). Admin-gated = informational under the usual grading clause; say so in the ledger.

- signature binding: which digest; are ALL order-critical fields committed; is any caller-supplied parameter trusted where it should be signed (e.g. an `expectedHash` argument - check how far the signed minimums bound it).

- amount measurement: balance delta (before/after, excludes pre-existing) vs caller-declared amount; leftover handling (refund vs keep).

- rounding: Ceil/Floor per leg and who it favors; cumulative-delta pro-rata (Ceil of [0,new] minus Ceil of [0,prev]) vs naive per-fill multiply.

- post-conditions: HF invariant sweeps, solvency caps (`credited >= min`), nonce/bitmap consumption (`nonce >> 8`, `1 << uint8(nonce)`), permit2 requestedAmount caps.



## 3. Copy-diff (delegatecall modules on one side, version bundles on the other)

- A module executed by `delegatecall` usually carries COPIES of engine helpers. Extract matching functions from both sources, normalize whitespace + type prefixes, diff: a semantic divergence (missing check, different rounding) is the candidate.

- Diff v1-vs-active impl bundles of the same contract: `diff -rq` then unified diff of differing `.sol` files. The v1->v2 delta names the team's recent focus AND its new features (batch/matched-order settlement) = the least-audited surface; hunt those first, then look for fix-missed siblings of anything they changed.



## 4. Deadly-pattern grep sweep (whole harvested tree)

- `catch {}` / `catch { continue }` around circuit-breaker / oracle / strategy calls = fail-open limit; ask who can force the revert that skips it.

- `delegatecall` to a settable module = admin-set code in the engine's storage context; compare module vs engine storage layouts.

- Every dangerous admin-gated power: grep for CALLERS. Zero callers on the live deploy = dormant (observation, never a finding) - e.g. bypass/lock functions reserved for future engines.

- Callback entrypoints (`onFlash`-style): must be reachable only from the trusted caller (`msg.sender` check) - and check what the callback can do with caller-supplied `abi.decode` data.

- EIP-712 digests: never a bare `keccak256` of fields - must be `toTypedDataHash(domainSeparator, structHash)`; mismatched field order between typehash string and encode() is a real bug class (verify by hand once per struct).



## 5. Falsification ledger (the discipline that makes zero-findings defensible)

- One file per target: Findings (each with reachability + honest severity) / Verified negatives (each with the KILL REASON - the exact line or mechanism that makes it safe) / Remaining surfaces / Key addresses (proxy AND impl for each contract).

- When a measurement or close read falsifies your own claim, rewrite every artifact that carried it and name the retracted claim. A killed hypothesis moves to the negatives list with its kill reason; it must not be re-litigated next session.

- Tag every entry attacker-reachable vs privileged-role-reachable: grading clauses usually make the latter informational, and that is the difference between a $0 observation and a submission.



## 6. Park + watch

- Park when: the program's grading clauses pre-kill your candidate classes AND the style is uniformly guarded (checks at every seam, conservative rounding, per-order limits, post-action invariants) after the money-surface sweep. Close out with the ledger + a watch; do not grind remaining seams.

- Watch (scripts/upgrade_watch.py): snapshot file storing (a) EIP-1967 impl slot per watched proxy - `cast storage <proxy> 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc` - and (b) sha256 of the public address-book JSON. Output must be deterministic (no timestamps) so it can run as a cron's monitor: unchanged output suppresses the agent run; a change injects the diff and wakes it.

- On a watch hit: fetch the changed contract's source from the explorer, diff against the ledger notes, re-read the money paths that changed first.

- Proxy vs impl trap: address books list the impl for some contracts and the proxy for others. Query the PROXY for state (getters on an impl return 0x0/empty); verify proxyness by the impl slot being nonzero.

- RPC hygiene: public explorer RPCs throttle (429). For `cast` calls fall back to general public RPCs (e.g. `ethereum-rpc.publicnode.com`, `eth.llamarpc.com`); keep the explorer API for source harvest. Write scratch files into the workdir, never bare `/tmp`, on Windows/MSYS hosts (native tools resolve `/tmp` differently than git-bash).



## 7. Cross-chain bridge legs (EVM + Solana + NEAR/UTXO light clients)

A bridge monorepo has one leg per chain plus a shared message/codec layer. Clear each leg against the same five seams, then compare legs to each other - a check present in one leg and missing in its sibling is the finding. Read each leg's own `SECURITY.md` first (see the known-issues rule in audit-competition-hunt).

1. **Signature binding.** Diff the serializer that builds the signed digest FIELD BY FIELD against the payload struct: every mutable field (destination nonce, origin chain, origin nonce, token, amount, recipient, fee recipient, message) plus the DESTINATION chain id must be committed. The strongest form binds the ACTUAL on-chain account keys passed to the instruction (Solana `serialize_for_near((mint.key(), recipient.key()))`), not merely payload fields - that closes account substitution. Also require an explicit low-s malleability guard (`!sig.s.is_high()`) and a comparison of the recovered signer against the stored derived bridge key.

2. **Conservation.** Per-transfer checks are not enough: find the GLOBAL finalize/invariant step that nets deposits against withdrawals per token and fails the WHOLE batch on any unmatched delta. Verify the matcher preserves per-account totals exactly (a greedy two-pointer over descending-sorted lists does) and that each (sender, receiver, token) pair is emitted once - that uniqueness is what justifies an `unreachable!()` on transfer overflow.

3. **Replay.** Nonce consumption must be an atomic check-and-set (bitset `!slot.replace(true)`, or a mapping write). Marking the nonce BEFORE signature verification is safe only because any later failure reverts the whole tx - confirm no path keeps the mark while skipping the effect. For bitset/PDA accounts created with `init_if_needed`, the residual lead is front-running: pre-funding the PDA, or an account with an unset discriminator so `load_init` zeroes existing bits instead of falling back to `load_mut`.

4. **Privileged bypass paths.** A finalize-without-proof / DAO-recovery / trusted-relayer path is safe only if it is role-gated AND reuses the SAME callback and accounting as the proven path. Read the role macro, then diff its body against the normal path for checks it skips.

5. **Accounting state machines.** When a fix adds an "entry missing" branch, enumerate EVERY state the key can be in (bound / deployed-but-unbound / not-yet-registered) and check each branch - a fix in one callback often leaves the sibling callback (deploy vs bind) on the old behaviour. Distinguish lock/release tokens from mint/burn tokens: skipping the locked-counter is correct for one model and a bug for the other.

**Two-step commit/submit designs** (used when a chain's system-tx logs are invisible to the attestation layer, so a message published inline is never attested): the commitment hash must use `abi.encode`, never `encodePacked`, when adjacent fields are dynamic strings ("ab"+"c" collides with "a"+"bc"); the submit step must re-derive and compare the commitment, delete it BEFORE the effect, and re-check fee/pause there if the commit step deliberately accepts everything to avoid stranding funds.

**Deprecated verification APIs:** before reporting a weak/deprecated verifier (e.g. an SPV inclusion proof with no coinbase-length check), grep the CALLERS for the version they actually invoke. A deprecated public method no in-scope caller uses is a third-party-integrator footgun, not a submittable loss-of-funds - record it as a verified negative with that kill reason.

**Role-gated arithmetic is still worth reading, but grade it honestly:** a real wrap/overflow bug behind a trusted-relayer or DAO gate is informational under the usual grading clause. Say so in the ledger instead of writing it up as a Critical.

## 8. Match local source to the deployed implementation before claiming anything

- Never report a finding from a local source tree against a deployed chain until the deployed runtime bytecode has been compared with a local build artifact. A source bundle verified on another chain, or harvested from a different explorer, is not evidence for this chain.
- Procedure: for each proxy read the EIP-1967 slot `0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc` with `eth_getStorageAt(proxy, slot, "latest")`; the last 40 hex chars are the implementation. Fetch its runtime code with `eth_getCode`. Compare lowercase hex with `out/<Contract>.sol/<Contract>.json` field `deployedBytecode.object`. Identical implementation addresses across several proxies mean one comparison covers all of them.
- On mismatch inspect metadata before blaming optimizer settings: read the last two bytes of both bytecodes as the CBOR length, slice the metadata blobs, and compare them. Equal metadata length and equal solc version but a different source hash inside the metadata means a DIFFERENT SOURCE TREE, not a compiler-flag difference. A dispatcher divergence at byte ~11 plus different runtime lengths confirms it.
- Record the verdict in the falsification ledger as a blocking verified negative: every static read and fuzz campaign run against that tree is unverified for the deployed chain, and no submission is eligible until verified source for that chain is obtained. WHY: a clean PoC against the wrong bytecode produces a confident false report.

### 8b. Recover verified source for the correct chain, then re-run the campaigns

When the local tree fails section 8, do not park the target permanently: fetch verified source for the DEPLOYED chain and rebuild.

- Query Sourcify first: `GET https://sourcify.dev/server/v2/contract/<chainId>/<impl>`; require `runtimeMatch: exact_match` and `creationMatch: exact_match`. `?fields=all` returns `sources` (path -> content) plus `metadata` with the compiler settings. Basescan's V1 `getsourcecode` route is deprecated and a Blockscout API can 403 from the host, so Sourcify is the reliable first stop. Fetch large JSON with `curl`/`urllib` into a file, not `web_extract`, which returns a head+tail mangled render of large API responses.
- Reconstruct a Foundry tree from `sources`, preserving the exact source paths, and remap each top-level prefix (`@openzeppelin/contracts/`, `@layerzerolabs/oft-evm/`, `contracts/`, ...) to `src/<prefix>`. Files shared by several contracts must be byte-identical; dedupe by content hash and resolve any conflict before building.
- Recompile with the solc version and settings from `metadata.settings` (optimizer runs, evmVersion, viaIR). Compare the rebuilt `deployedBytecode.object` with Sourcify's `recompiledBytecode` and with `eth_getCode`. Solc appends a CBOR metadata blob whose source hash depends on the verifier's source naming, so read its length from the final two bytes and strip that blob before comparing: executable code must be byte-identical even when the metadata hash differs. Equal runtime length plus equality after stripping is the green light.
- Re-run every static read and fuzz campaign against the reconstructed tree before making any claim. Keep the old tree's verdict in the ledger as a chain-wrong result, not as a finding. WHY: correct source converts the earlier blocking negative into usable evidence, but only after the bytecode equivalence check passes.

