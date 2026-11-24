---
name: bounty-hunt-pipeline
description: "Use to route a bounty engagement P0-P6 end to end."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [BugBounty, Pipeline, Orchestration, Workflow]
    related_skills: [bugbounty-target-selection, chain-scope-guard, evm-bounty-source-audit, web-api-bounty-hunt, finding-validation-gate, report-writing]
---

# Bounty hunt pipeline (P0 to P6)

One router for a full engagement. It does not duplicate any phase skill: it names the phase, the skill that owns it, the artifact that must exist before the next phase, and the condition that sends you back.

## When to Use

- Starting a new target, or resuming one after a gap, and the next step is unclear.
- Deciding whether a candidate is worth a phase transition.
- Not for a single-finding question (that is `finding-validation-gate`) and not for readiness of the arsenal (`skill-library-audit`).

## Phases

| Phase | Owner skill | Artifact to produce | Gate forward |
|---|---|---|---|
| P0 Target | `bugbounty-target-selection`, `bounty-target-verdicts` | Gate sheet: rep, KYC, PoC rule, payout band, prior verdicts, freshness | All five recorded, and not already parked at HEAD |
| P1 Scope | `chain-scope-guard` (contracts) or the live brief transcript (web2) | `scope.json` with every in-scope id and rule | `--audit` passes; a three-line quote of the accepted-impact clause |
| P2 Recon | `new-feature-bug-hunt`, `web-api-bounty-hunt` | Asset and entry-point inventory, code age, deployment map, local-vs-deployed delta when a deployment exists | One inventory row per scope entry; every instruction or route present in only one of repo/deployment recorded |
| P3 Hunt | `evm-bounty-source-audit` or `web-api-bounty-hunt`, spokes only as routed | Test matrix plus coverage ledger (`redteam-mindset`) | All sweep classes recorded |
| P4 Validate | `finding-validation-gate` | Gate sheet per candidate, microscope on the strongest | Every survivor has a PoC or a named park condition |
| P5 Evidence | `evidence-hygiene` | Redacted screenshots, sanitized HAR or tx bundle, SHA256 manifest | Manifest verifies, secret scan clean |
| P6 Deliver | `report-writing`, plus `bugcrowd-reporting` on Bugcrowd | Paste-ready draft plus an audited send kit shown to the operator | Every kit item matches current status; operator approves; submission ID recorded |

## Routing fork

- Contracts (static source, fork, fuzz): P3 is `evm-bounty-source-audit`. Add `defi-bounty-predive` for go/no-go and `meme-coin-audit` only on token scopes. Never both checklists at once.
- Web or API (live HTTP): P3 is `web-api-bounty-hunt`, with `web-api-authz-matrix` for object and role boundaries, `race-condition-web-api` for one-use flows, and `cspt-client-side-path-hunt` when a URL value reaches a client-built request path.
- Mobile or binary: `android-app-security-review` or `rea-static-analysis` at P3, with the same P1 and P5 rules.
- Substrate/Rust node source with pallet-based scope (for example a self-hosted node bounty): P3 is read-only static review of the pallet named in the newest release-prep commit, entered through a tag-to-tag diff so only the fresh lines are hunted. P1 is the program's own brief transcript, not a chain-address guard, when the program takes reports by email. Do not install the wasm32/Substrate build stack before an in-scope candidate exists; when the operator authorizes a runtime build, offload it to Colab or Kaggle rather than compiling locally. WHY: the runtime build is the expensive step and the fresh pallet diff is where the least-reviewed code sits.

## Send-backs

- P4 kills the only candidate: return to P3, next sweep class, not to P0.
- P1 loses an asset the finding depends on: the finding becomes a chain at P4, or dies.
- A new commit lands on an in-scope surface after P5: restart P2 for that surface only, then P4.

## Non-negotiables

- Every phase writes a file under `E:/audit/<target>/`. Chat is not storage.
- On any "how many bugs / what is new / what is left" question, reconcile first:
  search prior sessions for the target, inventory every findings directory
  including any final audit report and coverage ledger, and rank the newest
  verified artifact above older drafts. Report confirmed, retracted and
  submittable counts separately. WHY: a parallel session can retract a finding
  or add one after the current context was written, and an outdated count sends
  the operator to submit a dead finding.
- At P6, audit the send kit itself. Every panduan, paste file, bundle README
  and checksum manifest must agree with current finding status; remove
  retracted and disqualified items and regenerate the manifest. WHY: the
  operator copies the kit, not the chat conclusion, so a stale bundle is an
  active submission hazard.
- No phase starts with its artifact from the previous phase still empty. A skipped artifact is the usual cause of a wrong report.
- When a phase is blocked on an operator-side dependency (account, session, deposit, KYC), still write that phase's artifact with an explicit blocked status and the named unblocking condition, then write each downstream artifact as an empty placeholder with `[TOFILL]` and no invented finding. WHY: a missing artifact invites the next session to jump the gate and manufacture a report to fill the hole.
- Do not append a verdict to `bounty-target-verdicts` for a target that is still active with no finding. Reserve that register for submitted findings and closed negative verdicts with evidence paths. WHY: a parked label on a live target stops a future session from resuming it.
- Account steps (signup, KYC, deposit, public submit) belong to the operator; hand them a numbered list, never a paragraph.
- A program rule requiring the operator to personally validate the finding and run the PoC is a P6 gate, not a P3 blocker: continue the read-only hunt, build PoCs and drafts, and mark P6 blocked with the operator's own validation as the named unblock. Never submit from the agent side.
- A parked verdict in `bounty-target-verdicts` reopens only on new code touching the parked surface, checked by commit date.
- Do not skip P0 to save time on a listing badge: listing age is not code age.
- Never park an in-scope program as unauditable for lack of source before searching the local audit corpus and the SDK IDL. A private repository still leaves public audit PDFs, and those name the functions, file paths, patch identifiers and acknowledged-versus-resolved status; that is enough to rank a live hunt without the source tree. WHY: "no public repo" is a statement about git access, not about the amount of specification available, and a parked lane with an unread audit is a coverage hole that survives into later sessions.
- When the operator asks what changed or what was under-dug, run a freshness pass before answering: remote HEADs of every cloned repo, the protocol's own config API listing, the program page's last-updated field, and the local audit directory. Report the deltas with evidence, then act on the highest-value gap in the same turn rather than delivering an inventory alone.
- When the target is a live deployment with a public repo, diff the deployed instruction/route set against the repo's list before P3. A handler present only in the deployment is unaudited by every published review; a handler present only in the repo does not exist on chain and a PoC built on it reverts. Also re-read offsets out of the deployment (an SDK IDL, the program's own error text), never out of a repo struct — a drifting layout gives reads that look plausible and are wrong.

## Close-out

Coverage ledger, verdict per lane, carry-overs, monitor jobs if freshness matters, and the verdict appended to `bounty-target-verdicts`. Then stop; no padding.

If the engagement is blocked before a verdict exists, close with the carry-over list and the named unblocking step instead. A status file that names each phase, its owner skill, its artifact, and its gate is the router's own output; keep it beside the phase artifacts so a resumed session starts from the gate, not from chat history.
