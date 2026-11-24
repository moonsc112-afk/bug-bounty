---
name: audit-competition-hunt
description: "Use when entering a smart-contract audit competition."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [BugBounty, AuditCompetition, SmartContract]
---

# Smart-Contract Audit Competition Hunt

## When to Use

Load for ANY smart-contract audit engagement: an Immunefi/Cantina/CodeHawks
competition OR an ongoing bounty (Immunefi, Sherlock, HackenProof). The
acquisition, build, security-notes, sibling-gap and invariant-campaign procedure
below is the same for both. Only the pool-sizing and fixed-window notes are
competition-specific.

Competitions deploy FRESH code for a fixed window, so the code is genuinely
less-audited (that is the point) - the trade-off is top-tier difficulty and a
tight deadline. An ongoing bounty can also be fresh: verify the CODE age, not the
listing age, and prefer the component released most recently.

Check `bounty-target-verdicts` first so a parked surface is not re-audited.

Domain checklist: `references/reward-accumulator-audit.md` - the index/checkpoint reward
accumulator pattern (staking, gauges, relay/vault share systems) and the exact places its
solvency and accrual invariants break.

## Find live competitions

- `bbradar.io/contests` - calendar across platforms (Immunefi, Cantina,
  CodeHawks, Huntr). Immunefi audit comps: `immunefi.com/audit-competitions`
  and the `/audit-competition/<slug>` pages. Cantina: `cantina.xyz/opportunities/competitions`.
- Code4rena SHUT DOWN (2026); Sherlock contests deprecated, but
  `audit-engine.sherlock.xyz` is a separate live product. Do not model it as a
  contest: entry is invite-only, scope sits behind login, the pool pays on
  Accepted findings, and payout needs 2 Accepted issues plus a 20% Issues
  Ratio. AI-assisted research is explicitly supported there. Recipe:
  the bounty-program-verification.md reference in the opportunity-vetting
  skill, Audit Engine section. Live SC comps are sparse - usually 1-2 at a time.

  While waiting on approval, recheck PUBLIC channels only: the platform status
  page measures website/API health, not application state, and the engagements
  URL always redirects to sign-in for a logged-out visitor. Public posts fix the
  window and the pool but never reveal whether an application was accepted.
  Report that distinction plainly and leave account and email checks to the operator.

## Read the scope properly (Immunefi comp)

- The competition page has Information / Scope / Resources tabs. `.../scope/`
  holds the categories (e.g. Blockchain/DLT + Smart Contract), **Assets in
  Scope** (repos @ pinned commits), and **Impacts in Scope**.
- Save ALL THREE tabs as local text before planning: `curl -sL -A 'Mozilla/5.0'
  <url> -o page.html`, strip script/style/tags, `html.unescape`, write `.txt`,
  then grep the saved files. On Immunefi the content is split by tab:
  `/scope/` carries impacts, PoC requirements and the full known-issues list;
  `/resources/` carries the deployed address tables, Production configuration
  and devnet recipe; `/information/` carries the date window and the
  severity-to-pool amounts. Reading only the Scope tab misses the address book
  and the config gates that decide PoC validity.
- Treat an operator-supplied recon dossier as leads, never as authority. Verify
  its dates, pool figures, commit pins and especially which CHAIN each address
  is on against the live tabs before acting: a transcribed table that moves L1
  contracts onto the L2 chain silently sends PoC work to the wrong network.
- The **PoC Requirements** section tells you WHERE the PoC runs - read it FIRST,
  it decides feasibility: a local devnet (`just devnet up <name>`), a Foundry
  test at a pinned commit for Solidity contracts, or component-level for proof
  programs. A PoC that mocks out a trusted component is invalid.
- Pool sizing: "highest valid severity sets the pool" (a Critical unlocks the
  full pool, shared among all researchers).
- Known issues: the repo's `audits/` directory (PDFs) + disclosed bugs are OUT
  of scope. A mid-contest fix PR means that bug is already claimed/remediated -
  look for VARIANTS or the part the fix missed, not a re-find.
- For ongoing bounties with deployed assets, transcribe the scope table and any
  address-book link into `chain-scope-guard` and validate each candidate address
  before RPC probing or PoC deployment. Competition scope is the pinned repo
  commit; the guard covers the deployed-asset side, not the commit pin.

## Acquire + set up

- Verify a competition mirror is byte-identical to the named upstream commit BEFORE deep reading: `curl -sL https://api.github.com/repos/<upstream>/commits/<sha> | jq -r .commit.tree.sha` versus `git -C <mirror> rev-parse HEAD^{tree}`. A match rules out injected or stale code and lets you trust upstream docs/tooling; a mismatch changes the entire hunt and must be resolved first.
- Clone each scope repo at its PINNED commit, not the default-branch tip:
  `git clone <url> && git -C <dir> checkout <sha>`.
- Solidity / Foundry scope: the repo's `justfile` `deps:` target lists pinned
  deps. `forge install --no-git` FAILS on Windows with "Access is denied. (os
  error 5)" - clone the deps MANUALLY into `lib/<name>` at the pinned commits
  instead (git-bash `git clone` + `checkout` works). Typical set: forge-std,
  openzeppelin-contracts, openzeppelin-contracts-upgradeable, solmate, solady,
  plus any in-repo dep (e.g. a nitro-validator). Then `forge build`.
- Solidity scope whose `foundry.toml` sets `libs = ['node_modules']` needs a JS
  install, not `forge install`. When `package.json` carries GitHub-URL deps
  (`github:owner/repo#tag`, a bare git URL, an `npm:` alias), npm on Windows can
  die with `spawn EPERM` / `errno -4048` from `@npmcli/git` and install NOTHING
  (`--ignore-scripts` does not help - the failure is the git spawn, not a
  lifecycle script). Working sequence: write a SEPARATE minimal `package.json`
  containing only the registry deps (keep the `npm:` aliases), `npm install
  --no-audit --no-fund --ignore-scripts` there, MOVE the resulting
  `node_modules` into the repo, then `git clone --depth 1 --branch <tag>` each
  git dep into its remapping path by hand. Verify against `remappings.txt`
  (which folder each import prefix expects) rather than guessing folder names.
- A PUBLIC SOURCE EXPORT may ship only `src/` - the `test/` tree the security
  notes reference can be absent. Check for it before planning to extend the
  target's own harness; if missing, budget for writing the deployment/setup
  from scratch and treat the notes' test names as behaviour specs, not runnable
  code.
- Static scan: `slither . --filter-paths "lib/|test/|scripts/" --exclude-informational --exclude-low`.
  TRIAGE before reporting: `msg-value-in-nonpayable` on a LIBRARY function is a false
  positive whenever a payable entrypoint reaches it by `delegatecall` - slither does not
  follow delegatecall reachability, and `msg.value` survives the delegatecall. Confirm by
  reading the entrypoint (`external payable` + the delegatecall site) instead of counting
  the finding; an entire scan of a delegatecall-heavy codebase can consist of nothing but
  this one detector. Same shape for internal/virtual override chains the reachability
  analysis misses.
- Rust / rollup scope: toolchain pinned in `mise.toml` / `rust-toolchain.toml`;
  the PoC needs the devnet (heavy full build).
- "Source lib/forge-std/src/Vm.sol not found" has TWO distinct causes; check for `.gitmodules` first. With submodules, a shallow clone leaves them empty: `git submodule update --init --recursive --depth 1` (deep recursion may fail on nested submodules - partial init is usually enough). With NO `.gitmodules` and a gitignored `lib/`, that command does nothing: run the repo's pinned `forge install --no-git ...` recipe from its `justfile`/README before `forge test`. `forge build` compiles only `src/` and can look green while the test tree still cannot import forge-std, so validate one small suite, not just the build.
- A repo containing a file named after a RESERVED WINDOWS DEVICE NAME (`aux.rs`,
  `con.rs`, `prn.*`, `nul.*`, `com1.*`, `lpt1.*`) CANNOT be checked out on Windows:
  git aborts with `error: invalid path '...aux.rs'` and leaves the ENTIRE working
  tree empty (the clone looks present, `git log` works, but no files). `core.longpaths`
  does not help - it is a Win32 name restriction, not a path-length one. Clone such
  repos inside WSL (ext4) instead; that is also where the Rust toolchain lives.
  Real case: `Near-One/omni-bridge` has `light-clients/utxo/btc-types/src/aux.rs`.
- The terminal tool strips shell VARIABLES (`$c`, `$A`, `$R`) from the command
  before the shell sees them, even inside single quotes, so a
  `for c in ...; do git show $c; done` loop silently runs with an empty value.
  Applies to plain commands and to `wsl -d <distro> -- bash -lc "..."` alike.
  Pass LITERAL values/paths, or write a script file and execute that. Loops over
  commits/paths are the usual victim.
- READ the target's own security notes FIRST: a `Known_issues` repo (audit PDFs +
  contest-known-issues) AND any in-repo `SECURITY.md`. Multi-leg monorepos ship one
  `SECURITY.md` PER LEG (`evm/`, `solana/`, ...), each with a "Design Decisions
  (Non-Issues)" list and a "Known Issues" list - everything named there is out of
  scope, and the non-issues list tells you which permissionless-looking functions
  are intentional (so you do not report them). Extract the PDFs and grep them for
  your hypothesis BEFORE spending time on it: an issue already named in a
  Zellic/Sherlock report is out of scope.
  Extract with pypdf and silence the fontTools noise:
  `warnings.filterwarnings("ignore")` + `import logging; logging.disable(logging.CRITICAL)`.

  Then MINE the accepted-behaviour list for invariants instead of only skipping it.
  A "reviewed and accepted / known and out of scope" document is the team's own
  statement of what they believe always holds, and each entry is a ready-made
  hypothesis: "the drain never reverts on one entry", "a holder can always queue
  their whole free position", "no funds move and no accounting changes", "a new
  holder can never reach rewards notified before its mint". Breaking a stated
  invariant is in scope even though the surrounding behaviour is accepted. Read
  for the explicit carve-outs ("the milder case ... is NOT accepted") - those are
  the team pre-committing to a severity boundary, so they are the cheapest valid
  findings to aim at. Also treat a stated premise as an attack surface: if the doc
  argues a path is safe BECAUSE some call cannot revert, find a cast/check in that
  call that can.

  GREP THE EXACT SYMBOL a note names before reasoning about it. Notes use loose names and
  interfaces carry declared-but-unused errors, so a mechanism the prose implies may not
  exist in code at all. The config struct's NatSpec is frequently the authoritative
  statement and can contradict the prose outright. Confirm presence/absence by symbol
  search, then quote the code comment that settles it.

  Before reporting a cast/check that CAN revert as a queue-freezing DoS, compute the
  trigger ratio with REALISTIC magnitudes (actual token total supplies, the configured
  dust floor). A `toUint128` needing `supply/backing > 2^128 / amount` is unreachable when
  `amount` is bounded by a real token supply. Write the arithmetic into the dismissal so
  the next pass does not re-open it, and check the other casts on the same path - a cast
  of a value that is ALREADY the narrow type cannot overflow.

  Generalize that: derive the protocol's accounting identity (for a lending market,
  `unlent + loans == deposits + feeOwed`) and prove the risky subtraction bounded by it
  BEFORE spending fuzz runs. A liquidation cap that binds only when the seized value is
  below `repaid * incentive`, or a write-off whose fee leg is bounded by
  `loans - deposits <= feeOwed`, are dismissals valid for every input. Keep the algebra in
  the trace alongside the campaign count — an algebraic proof and a fuzz campaign are
  complementary evidence, not alternatives.

## Hunt the FRESH surface, not the whole repo

Competitions re-use audited bases (OP-stack, upstream forks). The winning edge
is the CHANGE: `git log --since=<window>` plus the feature named in the title.
Base Everest = EIP-8430 Base Transactions + gas-limit billing, living in the NEW
crates/files - not the audited OP-stack. Prioritize files changed inside the
window and the new feature's crates; the audited base is a time sink.

## Work an audit report as a lead list, then scan for the sibling gap

A published audit is a map of where the code was weak. Extract the PDFs, list the
findings by severity, and for each HIGH: locate the named function, confirm whether
the fix landed, and read the fix itself for soundness. A fixed finding is not a dead
end - the same class of bug usually survives at a sibling call site.

Scan the WHOLE entry-point set for the missing guard instead of eyeballing only the
named functions. Two false-positive sources will otherwise dominate the result:
- Attributes sit ABOVE the `pub fn` line (`#[private]`, `#[init]`, Solidity
  modifiers). Look BACKWARD a few lines for them, not only forward into the body.
- Guards are often inline (`is_participant`, `is_self_call`, an `Authenticated*`
  constructor) rather than a named helper - include those patterns in the guard set.
What survives both corrections is usually the permissionless-by-design entry points;
read each one's doc comment before calling it a finding. A cleanup function that
looks dangerous is often safe because it exempts the in-use/active entries.

## Wire-format unit mismatches silently fake a PASS

Before asserting on a packed/binary wire format, read the decode path and write
its unit into the harness. A fork harness that fed SECONDS into a field the
contract reads as MILLISECONDS landed in 1970: the future-timestamp test
"passed" as a non-revert (`assertFalse(ok)`) and only the drift test caught it.
Encode units from the source (`toTimeMs`, shifts, masks) and add one deliberately
wrong-unit test so the mismatch can never pass silently. Build that control explicitly:
pack raw seconds into the millisecond field, decode it, and assert the value differs from
the correctly converted timestamp.

## Solana / Anchor targets

- `anchor build` in WSL can stall for a long time on **downloading platform-tools** (observed
  ~8 MB per 5 min). Do not block the audit on it: most account-lifecycle questions can be settled
  by reading the fetched Anchor sources in `~/.cargo/registry/src/*/anchor-lang-*/` and
  `anchor-syn-*/` instead.
- **`init_if_needed` front-running is closed by construction** (anchor-syn 0.32.1
  `codegen/accounts/constraints.rs`): the create path runs only when
  `!if_needed || actual_owner == system_program::ID`, so a program-owned initialized account is
  never re-created; afterwards it asserts `space == data_len`, `owner`, and rent-exemption.
  `AccountLoader::load_init` refuses a non-zero discriminator (`AccountDiscriminatorAlreadySet`)
  and never zeroes the data. Check these three before claiming a nonce/bitset reset bug.
- A scope entry naming a repo that 404s may be a **crate inside a monorepo** (e.g.
  `near/threshold-signatures` lives at `near/mpc/crates/threshold-signatures`). Check the org's
  repos / the monorepo's `crates/` before concluding the target is unavailable.

## Prove your negative is real (not vacuous)

- **Restrict invariant fuzzing to the harness.** Foundry's invariant fuzzer targets every external
  function of every contract the test deploys. A mock ERC20 with a public `mint` will be fuzzed
  directly and break supply invariants with a false positive. Call `targetContract(address(harness))`
  in `setUp()`. Two tell-tale signs that targeting is wrong: a shrunk sequence ending in a direct
  call to a mock's privileged function, OR an invariant "failure" whose reason is an ordinary revert
  from the target (`InsufficientUnlent()`) instead of an assertion message: with call count 1 and
  reverts 1. An expected revert in a fuzzed entrypoint is reported against the invariant; do not
  debug it as a broken invariant, fix the targeting.
- A hand-rolled ERC20 mock that implements IERC20 must NOT redeclare `Transfer`/`Approval` events —
  they are inherited, and redeclaring them fails compilation with "Event with same name and
  parameter types defined twice" (5883). Just emit them; bool-returning `approve`/`transfer` is
  enough for SafeERC20.
- When a library calls back into its host via `IRelayState(address(this))` (or any
  `address(this)` cast), the cast FAILS during the host's constructor because a contract under
  construction has no code. Move such initialization into an external `init()` called from
  `setUp()`; otherwise every fuzz run dies in setup with `EvmError: Revert` at gas 0.
- **Record invariant violations at execution time, not from final state.** A property like
  "an actor with debt must be whitelisted" goes false after a legitimate whitelist
  revocation, so checking final state reports a bug that never existed. Capture the
  precondition in the handler (`wasWhitelisted` before the call) and increment a ghost
  violation counter only when the action actually breached it; assert that counter is
  zero. Use final-state checks only for identities that must hold continuously, such as
  `unlent + loans == deposits + feeOwed`.
- **Make every negative control reachable and two-sided.** An earlier guard can mask the
  planted defect, so configure the parameters that let execution reach the guard under test
  (e.g. set close factor to 100% before testing a dust check). Assert the sound-mode
  behavior AND the bug-mode breach; a control that only asserts the bug behavior while the
  sound contract is deployed fails for the wrong reason.
- **`vm.prank` applies to one call only.** Two consecutive external calls after a single
  `prank` come from different senders, producing a ledger mismatch that is purely a harness
  artifact. Wrap multi-call setup in `startPrank`/`stopPrank`.
- **Guard view calls inside invariants.** If `price()` reverts on a stale feed, an
  invariant that calls it unconditionally fails with the target's revert reason instead of
  an assertion message. Check the freshness/decimals preconditions first, then call the view.
- Report the handler success counts from Foundry's call table alongside the run/call totals. A
  campaign with 200k calls but 0 successful `claim`/`notify` actions proves nothing; add a
  `test_sanityActionsExecute` that asserts ghost counters are nonzero.

An action harness that swallows reverts (a failed swap is still a valid state
transition) makes a GREEN invariant run indistinguishable from one where nothing
ever executed. Increment a ghost counter inside each action on SUCCESS, add a
`test_sanityActionsExecute` that drives every path once and asserts each counter
moved, and read the per-action call table at the end. Report the call count with
the verdict: "0 violations over N calls" is only meaningful once N is shown to be
exercise, not attempts.

Also read the target's OWN invariant tests first and name the dimension they miss
(one-swap-from-clean-state vs sequences/of-oracle-moves/with-fee-changes).
Extending the repo's base setup beats writing a parallel deployment, and the gap
statement is what makes the campaign worth worth running.

WIDEN THE GRID when the repo's own harness is narrow. If their invariant fuzzers run
a 2-bin pool, redeploy a wider one through their own `_deployPoolAndRegister` helper:
pack bins 5-per-uint256 (48 bits each), `_unpackBinStates` both arrays, pass
`lowestBin`/`highestBin` covering the whole grid, then REASSIGN the base test's `pool`
state variable so every inherited helper follows, and re-approve the users for the new
address. Add a crossing proof (`assertLt(curBinIdx, start)` after a deliberately large
swap) so the wide grid is demonstrably exercised rather than merely declared. A wide
grid reaches the multi-bin crossing loop and the int24 distance clamping that no
single-bin campaign touches.

## Build a pattern harness while scope is gated

Invite-only platforms keep the repo, commit and known-issues list behind login, so the
hunt cannot start on the real code yet. Do not idle: build a self-contained Foundry
model of the surfaces the public docs DO describe, with a defect switch per hypothesized
break and a negative control that proves each invariant catches it. When scope opens,
swap the model for a thin adapter over the real contracts and rerun the negative controls
before any long campaign. If an adapter cannot reproduce a planted defect, the function
mapping is wrong, not the target. Recipe and file layout:
`references/pattern-harness-before-scope.md`.

## Split a large target across disjoint reviewers

When the target spans several crates or components, dispatch parallel READ-ONLY reviewers with disjoint scopes and an explicit `NO_CLAIM` outcome plus `why_not_known_issue` on every claim. One reviewer across a monorepo gives shallow coverage; disjoint lanes make the negative ledger auditable and stop a reviewer from manufacturing a claim to satisfy the prompt. Feed every reviewer the already-saved known-issues text and forbid builds and edits so the reports stay comparable. Merge the lanes before deciding to park the target.

For non-Solidity components (Rust clients, precompiles), compile a std-only transliteration with `rustc -O` instead of building the whole workspace: copy every branch, bound and checkpoint effect, swap big integers and hashes for fixed primitives, and drive it with a deterministic seeded RNG. Run several campaigns at different clock rates (realistic, saturated, frozen) so boundary branches such as ring-full rejection are actually exercised; report accepted / rejected / violations counts. A single realistic-rate campaign that never touches a branch proves nothing about that branch. Keep a reverse index (hash -> slot count) for any per-iteration containment check: scanning the whole ring/map to assert an invariant turns a bounded campaign into an unbounded one and tempts you to shrink the sample instead of fixing the harness.

## Park decision (be honest)

A top-tier competition (a major protocol's core, 9+ audits, hundreds of
researchers) is a LONG SHOT for a solo hunter. Slither on an audited codebase
returns ~all false-positives (constable-states, by-design proxy/multicall).
After a time-boxed pass, if the fresh surface is (a) already fixed in-window and
(b) the rest is meticulously hardened (see the NatSpec edge-case reasoning),
PARK it - grinding has below-pivot expected value. Record the verified-negative
+ handoff, do not sink days.

When the operator insists on continuing a clean target, change the ANGLE rather than the sample
size: (1) derive the accounting identity algebraically and prove the risky subtractions bounded,
(2) test promises the repo makes to integrators in its docs (e.g. "helper returns the max accepted
value; +1 is refused") with a dedicated fuzz test, (3) fuzz a dimension the repo's own harness
misses with an independently written mock setup. If all three are clean, say so plainly and stop;
repeating the same campaign with more runs is not new evidence.

## Derive hypotheses from feature composition, and report in the operator's register

When public docs name several configurable features, enumerate candidate Critical scenarios at their INTERSECTIONS, not one per feature: multi-tenant shared liquidity against per-app debt, initializer or upgrade-role capture, oracle decimal/exponent mismatch, stale-price liquidation with configurable incentive, first-depositor donation inflation, and reentrancy through an arbitrary collateral token. For each, write the critical condition and the dismiss condition BEFORE reading code; this is what keeps a gated hunt from degrading into speculative reports. Checklist: `references/pattern-harness-before-scope.md`.

For this operator, write chat and reports in casual Indonesian, no em-dash, and end with a short numbered list of next-step options. Account, KYC, commit and public submission stay with the operator; the agent owns analysis, PoC and evidence drafts.

## Traps

- Reusable Foundry harnesses with handlers, ghost counters, negative controls and adapter stubs are covered by the `foundry-audit-harness` skill. Load it before writing a new invariant suite; it records verified pitfalls such as `expectRevert(string)` being unavailable in the local forge-std and `CHEATS.prank` being one-shot.
- A global binary named `forge` used to SHADOW Foundry's forge on PATH (the
  Atlassian Forge CLI installed via npm-global). **Fixed on this host:** `~/bin`
  now holds a host-aware `forge`/`cast`/`anvil`/`chisel` dispatcher, so bare
  `forge` is Foundry in git-bash and in WSL, and the Atlassian CLI moved to
  `forge-atl` (Windows only; it breaks in WSL on Node 18). If the symptom ever
  returns, diagnose with `which -a forge`: a `manifest.yml` line, a bare
  `15.1.0` version, or `Warning: Your version of Forge CLI is out of date` means
  the wrong forge ran, not that the repo is broken. Assert identity with
  `forge --version` -> `forge Version: 1.9.0` before any build, and check
  `cast sig 'transfer(address,uint256)'` returns a selector before trusting any
  PoC command in a fresh shell.
- **On a Windows host, `vm.ffi` test helpers spawn WSL bash, not git-bash.** A harness that runs `vm.ffi(["bash", "-c", "cast ..."])` then fails in `setUp()` with `cast: command not found`, because WSL's PATH never sees Foundry's Windows bin. Confirm from the `/mnt/c/...` path in the error, then create `~/bin/cast` as a dual-mode `#!/bin/sh` wrapper: `if [ -x /mnt/c/Users/<user>/.foundry/bin/cast.exe ]; then exec /mnt/c/.../cast.exe "$@"; fi; exec "C:/Users/<user>/.foundry/bin/cast.exe" "$@"`. The dual mode matters because `~/bin` precedes `~/.foundry/bin` in BOTH shells: a WSL-only wrapper makes `cast` die from git-bash with `No such file or directory`, which looks like a broken install. Do not edit the audited repo to work around a harness environment problem.
- `forge install --no-git` on Windows: "Access is denied. (os error 5)" -
  manual clone into `lib/` at pinned commits.
- A factory that clones an implementation and PRE-SEEDS the predicted address (sends the
  seed stake/tokens before the clone exists) must prove initialization actually ran: a
  codeless EIP-1167 clone returns success for EVERY call, so `initialize` can appear to
  succeed while stranding the seed. Look for a post-init assertion on a value only the real
  body writes (e.g. a satellite token address being nonzero). Conversely, do not report a
  clone-initialization front-run when create+initialize happen in one transaction and the
  salt is scoped to `msg.sender` - there is no window and no third-party salt occupation.
- Submission needs KYC (Immunefi) - start early; account/identity steps are the
  operator's own.
- Program rules forbid scanner / high-volume traffic on LIVE sites;
  competitions are local-fork or devnet only. Testing the public sequencer
  endpoint is prohibited.
