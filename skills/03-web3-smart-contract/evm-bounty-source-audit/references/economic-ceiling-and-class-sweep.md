# Submission economics + closing a bug class (lessons that changed a real audit)

## Check the deployment's ECONOMIC CEILING before investing

Read the live pool/liquidity (`poolAmounts` per token, `totalAssets`, TVL getters) and compare it against the program's payout mechanics. A program that caps Critical at **`10% of economic damage`** cannot pay more than ~10% of the funds the deployment actually holds.

Worked case (Fulcrom, Cronos zkEVM): the entire perp pool was ~$35–50k (10.07 vETH + 0.156 WBTC + 224 vUSD) — read from live `poolAmounts`. Consequences, all knowable in minutes:

- even a worst-case drain caps a Critical near **$5k** on that deployment;
- bounded-window defects (a revert band, a fee-sized accounting gap) can only ever buy **single-digit-dollar** damage on a small pool;
- it explains a program statistics line of 349 submissions / **$550 paid** — small pool, small budgets, high rejection rate.

Do this math BEFORE days of PoC work, say the number out loud to the operator, and only then decide how much effort the finding deserves. Corollary: before pivoting to "the next target", read ITS pool size too — the same math decides whether a finding there can ever be worth filing.

## A protocol match is not a target match

Programs are often umbrella programs covering many ecosystem projects: the Fulcrom deployment sits inside **"Cronos zkEVM Smart Contracts"**, not a 'Fulcrom' program (`hackenproof.com/programs/fulcrom` is a 404). Search the platform for the chain/program name first, then expand the scope table ('Show all targets') and confirm YOUR contract addresses literally appear — all seven Fulcrom addresses did.

## Close the bug class before submitting, and record the sweep

After finding one instance of a fork-side substitution (`msg.sender` where upstream passed a request field), sweep ALL protocol files for the pattern in fund/fee/account contexts and state the result in the submission:

- Fulcrom: 157 protocol files (excluding libs/interfaces/mocks) → 18 candidates, all legitimate except the two already found (`_collectFees(msg.sender, …)` in PositionRouter, and the referral guard comparing `affiliate == msg.sender`) → the class is closed, no third instance.
- Put one sentence in the draft: *"the class is closed; N candidates reviewed, all explained"*. Cheap credibility, and it stops the triager wondering whether you looked elsewhere.
- Keep the sweep script's scope honest: a glob limited to `contracts/core/*.sol` silently misses `contracts/referrals/ReferralManager.sol` — the very file with the second instance. Sweep the whole protocol tree per contract directory.

## Check the project is ALIVE before anything else (frontend + news, not just chain data)

Load the protocol's own frontend and do a news/search check BEFORE deep work on any deployment.

- Fulcrom Cronos zkEVM looked on-chain merely "quiet": pool ~$35–50k left, `feeReserves = 0` everywhere, ~5 increases per 100k blocks, an unverified OrderBook left unverified. The frontend said it plainly: **"Fulcrom is closing. You can no longer open positions, place orders, swap, buy FLP or stake. Please withdraw your funds."** — alongside an Aug–Sep 2026 incident and Cronos Labs sunsetting "all other projects".
- One page load would have reframed the whole audit's payout odds: the bounty page still says "active", the code stays deployed, the findings stay real — but a bounded-window defect at a closing protocol pays ~nothing (and its damage baseline keeps shrinking).
- Cheap signals to check, in this order: (1) homepage/status banner, (2) X/news search "<protocol> shutdown | incident | sunset", (3) feeReserves ≈ 0, tiny pool, near-zero recent activity, (4) an in-scope implementation left unverified for years.
- Say the conclusion out loud to the operator. "The chain data looks quiet" is not the same statement as "the project is closing", and the second one decides where effort goes.

## Falsify before you write up — and record the falsifications

Never let a suspicious pattern graduate to a claim without a minimal test that could kill it. Two shapes that paid for themselves:

- **Guard-bypass hypotheses.** `try target.check(...) returns (bool allowed, uint256 avail) { if (!allowed) revert RateLimitExceeded(); } catch {}` reads like a no-op guard. A 20-line semantics test (mock the checker, return `(false, 0)`, expect the caller to revert) shows a revert inside the try's SUCCESS block is NOT caught — the guard holds; only a *failing external call* is swallowed, so the catch merely makes an unregistered/reverting checker fail-open. Test both directions, log both outcomes, and state which hypothesis died and why.
- **Your own draft claims.** Re-run the draft's numbers through the harness and let the tests falsify whatever is wrong (a "the fee claim cannot be withdrawn" claim and an "exposure up to the position size" claim both died this way). Bounded claims that survived their own PoC — with the measurement that bounds them — are what make the rest of a submission believable; a falsified claim left in the draft is what makes a triager distrust the rest.

## Report the tally as found-vs-payable, and retire dead targets cleanly

When the operator asks how many bugs: give two numbers, not one — real findings (each with its PoC or draft artifact) and payable ones (after economics and target status) — plus a separate count of falsified hypotheses. Ground every count in artifacts (suite/test counts, the draft file list) rather than memory, and re-read them with a command before answering.

When the operator declares a target closed: remove or pause its monitor cron, drop it from the bug-hunt tally, keep the artifacts on disk as an archive (they remain the method and the evidence), and stop re-checking a closing protocol's verification or config — the payout is gone even though the findings were real. Say the retirement once, then move the effort to the live target.
