# Audit-competition scope: acquisition and triage

A competition puts not-yet-deployed code in scope for a fixed window. The audit
work is the same as any bounty, but four things differ and cost real time if
unplanned.

## 1. Pin the scope commits

The competition page's Scope tab pins an exact commit per repo. Clone, check out
that commit, and verify:

    git clone <url> <dir> && git -C <dir> checkout <commit> \
      && git -C <dir> rev-parse --short HEAD

`--depth 1` will NOT contain a pinned commit that is not the branch tip; clone
enough history (or fetch the commit explicitly). Read the asset list and the
accepted PoC environment off the same tab (Immunefi:
`/audit-competition/<slug>/scope/`).

Confirm whether the mirror is really the upstream code before deciding what kind
of hunt this is. Competition repos under the platform's org are often exact
mirrors; a keyless tree-hash comparison settles it:

    git -C <dir> cat-file -p HEAD | head -2     # tree <sha>
    curl -sL https://api.github.com/repos/<upstream-org>/<repo>/commits/<sha> \
      -o <abs-path>/upstream_commit.json
    # read upstream_commit.json -> commit.tree.sha

Equal tree SHAs prove byte-identical content: the target is the genuine,
already-audited upstream code, so expect static scans to yield verified negatives
and spend the time on the fresh surface in section 4 instead of hunting for an
artificial defect. A MISMATCH means the mirror carries edits - diff the two trees
first and treat that delta as the highest-priority lead.

## 2. Hand-install Foundry deps when `forge install` does not populate `lib/`

A repo ships `lib/<dep>/...` imports with an empty (or absent) `lib/`. The repo's
`justfile` `deps:` target (or `foundry.toml` remappings) lists each dep and its
pinned commit. `forge install --no-git <dep>@<commit> ...` is the intended path;
when it fails to write `lib/` (seen on Windows as `Access is denied (os error
5)`), hand-install the same pins - identical result:

    mkdir -p lib
    # for each dep: repo-url, dir name, pinned commit
    git clone --filter=blob:none <repo-url> lib/<name>
    git -C lib/<name> checkout <pinned-commit>

Then `forge build` (expect a multi-solc run). Confirm each dep's checked-out
short hash equals the pin.

## 3. Triage slither on an already-audited codebase

Expect the High/Medium list to be dominated by false positives and by-design
patterns: multicall `controlled-delegatecall`/`arbitrary-send-eth`, proxy
`incorrect-return`, vendor libraries, OP-stack `write-after-write` on the
message-sender slot (set then reset), storage-spacer `constable-states`,
`divide-before-multiply` on intentional rounding. Do NOT grind the detector list.
Split findings by "is the file a recent commit / protocol-native module, or
inherited/vendor?" and read only the former. An `uninitialized-local` where every
path assigns-or-reverts is a false positive - confirm by reading the data flow,
not the flag.

## 4. The freshest surface is the scope window's own commits

In a repo audited many times, the new code is the delta: `git log --since=<window
start>` plus the files those commits touch. A mid-window security fix (e.g. a
`require(... not already X)` guard just added) is itself a lead: ask whether the
fix is COMPLETE and whether sibling paths/flows share the same flaw class. The
disclosed bug the fix closes is out of scope; its unfixed relatives are not. A
A pinned commit titled `fix(...)` is the freshest surface, not evidence that a bug
remains - read its diff and its tests before treating it as a finding.

Map every `Unreleased` changelog item back to the prior audit finding it closes before calling it new surface. When every item maps, the concept was already audited and only the post-audit implementation is fresh.

Do that mapping with two concrete reads. Extract an audit PDF with `pdftotext -layout <audit.pdf> <out.txt>` and grep the finding IDs plus `Fixed in PR`; PDF-only reports do not yield searchable text through a plain file read. Then compute the real post-audit delta with the compare API:

    curl -sL "https://api.github.com/repos/<org>/<repo>/compare/<audited_commit>...<pinned_commit>" -o compare.json
    # parse files[].filename / additions / deletions / patch

WHY: a changelog describes intent, while the compare payload shows exactly which source files and tests changed after the review, which is the surface worth fuzzing.

For a standard bounty whose README carries a "Changes since the last audit"
section, treat that section as a claim, not the delta: compute
`git diff -w <last-audit-tag> HEAD -- contracts` and drop comment-only lines
before choosing a surface. README summaries routinely understate the real code
delta and send you rereading audited core.

When the repo ships a frozen pre-refactor copy plus a parity/differential test,
run that suite before manually reviewing the refactor. It is the decisive
equivalence check: line-by-line diff reading cannot prove behavioural
equivalence, while the parity suite closes the surface in seconds.

## 5. Time-box before committing days

A competition on a major chain's own core protocol (node + contracts, hundreds of
researchers, tier-1 firms) is a long shot for a solo hunter. Do one focused pass
over the slice that matches your tooling, then park - the payoff does not justify
grinding an audited core.

## 6. Cross-checking prior audit work against an engagement bundle

Use this when handed a prior work product (hunt plan, scope checklist, PoC drafts,
generic mock harness) together with a source snapshot. Treat every inherited
hypothesis as UNVERIFIED until the bundle confirms it. A Sherlock-style bundle
ships `scope.json` (pinned commit + `in_scope_files`), `statements.json`
(engagement decisions tagged `known`, `scope`, `true_finding`), judging
guidelines, a protocol context file and a `query.py` helper. Work in this order:

1. Diff the supplied file list against `scope.json` `in_scope_files` as SETS after
   normalizing path prefixes. Report both directions and missing-on-disk files.
   An exact match proves only that the scope list is right, never that the
   findings are.
2. Enumerate every `.sol` under `src/` NOT in scope. Factory/clone/create2 code,
   oracle node graphs, `interfaces/` directories and vendored math libs are
   common carve-outs. Any hypothesis whose root cause lives there is dead for
   this engagement even when the mechanism is real in the abstract. Read the
   scope rule: a finding qualifies when its logic chain and the bulk of its
   impact land in the listed files.
3. Before writing any PoC, query the decisions file for each hypothesis keyword:
   `python context/query.py statements --dimension known --search <keyword>`.
   A decisive `known` statement closes that hypothesis; record its ID in the
   negative ledger. Trust-model statements close whole classes at once: "operator
   fully trusted" kills admin-misconfiguration paths, "no upgrade authority"
   kills proxy/reinitializer paths, "non-standard tokens unsupported" kills
   fee-on-transfer and ERC777 reentrancy paths.
4. Verify a mock harness is actually wired to the target. Grep the real source
   for each adapter entrypoint (`grep -rl "function <name>" src --include=*.sol`).
   Entrypoints that do not exist mean the suite exercises self-injected bug
   models, not the protocol. Negative controls prove the harness has teeth,
   NEVER that the target is vulnerable. A harness that passes 38 tests and a
   harness that found a bug are different claims.
5. Prefer the repo's own PoC base (`test/poc/PoCBase.t.sol` or equivalent) over
   an inherited hand-rolled adapter. A real deployment base with actual
   implementations beats a forwarding stub. Confirm it first with
   `forge build --skip test` and `forge test --match-path <PoC>`.
6. Deliver a per-hypothesis verdict table (hypothesis, verdict, evidence ID or
   `file:line`), a scope gap list, a harness section, and a short "what still
   makes sense" section drawn from requirement statements rather than from the
   mock's bug switches. Write it in Indonesian with no em-dashes.

Pitfall: an inherited harness may carry default `invariant.runs = 256` /
`depth = 64`, which can exceed a single tool timeout. Reproduce the suite with
`FOUNDRY_INVARIANT_RUNS=4 FOUNDRY_FUZZ_RUNS=4` first and scale only for a real
campaign; after a timeout, kill the leftover `forge` processes before rerunning
so the second run is not competing with the first.
