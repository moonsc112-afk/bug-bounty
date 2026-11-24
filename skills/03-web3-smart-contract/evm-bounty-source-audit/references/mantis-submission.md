# Mantis submission workflow

Use when a finding is ready to post to a Mantis-hosted bounty. Pair with `hermes-mcp-mantis-login` for auth.

## Read the live program first
- `get_bounty` takes `bountyIdOrSlug` (the URL slug works), not `id`; the response wraps the record under `bounty`.
- The live page description is the source of truth. Docs markdown may still describe a legacy platform. Read known issues, exclusions, severity tiers and the PoC requirement from the live record. Prefer the MCP `get_bounty` record over the rendered page: `inScopeRules` and `outOfScopeRules` there are often stricter (for example excluding code that is not deployed on mainnet and markets that are not endorsed), and a finding that only reproduces on an undeployed or unendorsed market is ineligible.
- Sweep published audit PDFs and in-repo review directories for prior art before claiming a finding is new. An unfixed published finding is ineligible. Download the linked PDFs and grep the BODY for mechanism keywords (function names, valuation words like pessimistic/dampened, `without seizing`), not just finding titles: the same mechanism is often reported under an unrelated heading.

## Resolve asset IDs
- `bounty.assets[].identifier` holds the address; post with `assetId`, the separate record ID. Look each affected address up in the live asset list, never paste the address into the `assets` field.
- Confirm every address is `inScope` before submitting.

## Build the payload
- `submit_report` requires `title`, `description`, `severity`, `assets` (an array of `{assetId, description}`) and `bountyId`.
- Compose description and pocText from the approved paste-ready draft, not from chat: H1 goes in `title`, body from the Summary onward in `description`, Reproduction in `pocText`.
- Map severity to the live reward table and keep the agreed rating; do not inflate it at submit time. `submit_report` accepts only severities present in `bounty.rewards`, even though its inputSchema enum also lists medium/low/informational; a non-reward rating returns `invalid_severity`. When the honest rating is not payable, tell the operator and ask for a decision instead of silently escalating. Quote the exact tier language in the report's severity rationale, and check known-issue clauses that cap severity (for example a clause capping a class at Medium): showing why the higher tiers do NOT apply is what makes the rating credible.
- Show the operator the complete draft and wait for explicit approval before calling `submit_report`.

## Call and verify
- If MCP tools are not loaded in the current session, invoke the tool through the MCP endpoint with the token read from `.env` inside the shell (see `hermes-mcp-mantis-login`). Build the JSON-RPC envelope from a payload file so the token never appears in command text.
- Argument names are not guessable (`get_bounty` uses `bountyIdOrSlug`, `add_submission_followup` uses `submissionId`). Call JSON-RPC `tools/list` first and read `inputSchema` for the exact tool before composing any payload.
- Verify with `get_submission` using the returned submissionId; record the ID, severity and status.

## Follow-ups after filing
- There is no edit tool for a filed report. When a stronger proof or a missing assertion appears after submission, post it with `add_submission_followup`: `submissionId`, `body` (GFM Markdown, max 16000 chars), `acting_as: "hunter"`. Treat it as an additive evidence note, not a replacement for the original text.
- Verify the returned message's `submissionId` and `authorSide` match the original filing and record the follow-up message ID. The same auth and JSON-RPC envelope rules apply.
