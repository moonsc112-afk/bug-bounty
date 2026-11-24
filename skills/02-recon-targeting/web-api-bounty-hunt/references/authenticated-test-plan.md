# Account handoff + authenticated candidate checklist

Everything below the handoff is a HYPOTHESIS checklist, not validated findings.
Confirm impact against the program rubric before claiming a tier. Stop at proof.

## Account handoff (division of labor)

The program rarely provides bounty accounts; the user creates them on the sign-in
page. Common paths: institutional email (.edu/.mil/.gov) -> instant account + own
org + welcome credits; Google -> account, org when a waitlist spot opens; ordinary
email -> waitlist; a separate CTF/red-team program -> reviewed account + free
capacity (but that account is for the CTF only, not general bounty testing).
Ideal: TWO accounts in TWO separate orgs (cross-org IDOR + join-rule tests).

### Provisioning gates — check feasibility before recommending a path

- **Match the user's REAL email domain to the program's literal TLD list.** A
  `.edu/.mil/.gov` gate is US-centric; country-code equivalents (`.ac.id`, `.go.id`,
  `.mil.id`, `.edu.au`, `.ac.uk`) do NOT match. Confirm the user holds a qualifying
  address before recommending the "instant institutional" path, or you send them
  down a dead end.
- **Acquiring a .edu without one (international):** US community-college NONCREDIT /
  extended-learning applications are the open path — tuition-free, often "no
  SSN/residency/citizenship restrictions", processed in ~1-2 days, issues a .edu
  student email (a `student.<college>.edu` subdomain qualifies like any .edu). But
  California CCCApply requires identity verification BEFORE the application is
  delivered: international applicants verify via ID.me with a NON-US PASSPORT +
  proof of address; "Verify Later" defers, it does not bypass. No passport -> only
  local staff verification (impractical remotely) -> pivot to CTF/waitlist/Google.
  Re-check the current rule on the college's admissions page + CCCApply public docs
  (the policy tightens). Never fake SSN/identity or use ".edu generator" sites —
  payout KYC (PayPal + tax form) needs the same real identity, so fabrication fails
  late and wastes the effort.
- **CTF / red-team application (sanctioned research-account path):** draft it for
  the user; submission stays theirs. Write motivation/experience from the user's
  REAL profile and method; leave name/email as placeholders (the agreement needs a
  legal name, 18+); leave honeypot fields EMPTY. Restate the challenges-only
  restriction and that live challenges pay (prize vs bounty, whichever higher).
- **Check credibility links BEFORE citing them.** `gh api user` +
  `gh api users/<login>/repos` shows what a reviewer sees: an empty profile or an
  off-topic fork adds nothing. Lead with verifiable platform reputation (e.g. a
  HackenProof profile with real rep) over an empty GitHub. Never fabricate portfolio
  content, and never publish ongoing/embargoed hunt artifacts (PoC scripts,
  writeups) as portfolio — coordinated disclosure forbids it.

### Chain-backed targets: testnet account provisioning

When a web/API target settles writes on a chain, the authenticated phase starts
with a chain account, not a sign-in page. Give the user these steps in order and
never take their keys:

1. Create a BURNER wallet in a separate profile; never the payout wallet. Record
   both address encodings the chain uses (EVM `0x...`, Cosmos `addr1...`) — they
   are often the same 20 bytes in two formats.
2. Add the network from the chain's official docs (RPC URL, chain ID, symbol,
   explorer). Do not guess chain IDs from token names.
3. Claim from the official faucet, then compare what it pays with the one-time
   trading-account opening fee. If the faucet payout is orders of magnitude below
   the fee, that is a real provisioning gate: ask the program team for a funded
   test account instead of telling the user to farm faucet claims. Say so early,
   before the user spends time on wallet setup.
4. Many chains require a separate on-chain trading account before any order.
   Read the module's `params`/`allowed_fees` endpoint for the accepted token and
   amount rather than assuming a symbol; check the open status with the chain's
   `is_opened` query.
5. Bridged assets usually land on the EVM side while trading settles on the
   Core/native side, so an EVM-to-Core transfer is a separate step. Respect the
   per-layer decimals; Core often fixes 18 while an EVM ERC20 has its own.
6. Have the user hand back only the address, the open status and the read-only
   balance. The agent then runs the authenticated candidate tests; account
   creation, fee payment and wallet signing stay with the user.

Hand the agent a credential ONE of two ways:
- **Sign-in link** from the email -> user pastes it to chat -> agent opens it in
  the browser it drives, clicks Continue, gets the auth session cookie. The link
  signs in whoever opens it (often documented/accepted), so it is sensitive — but
  it is the user's own test account; revoke sessions afterward. A 6-digit code is
  usually browser-bound to the requester, so the LINK is the clean handoff.
- **Org API token** -> user mints it on the console's API Keys page, saves the
  secret to a file (chmod 600, never chat/shell history), gives the agent the
  path. The token acts for the org on every API.

### Sanitized capture handoff (user keeps the session)

When the user declines to sign in through the agent-driven browser and also
declines to share a session link or token, stop asking for a login. Hand him a
DevTools capture checklist instead: F12 > Network > Fetch/XHR with Preserve log,
visit each named page, and for each target endpoint copy Method, URL, status,
request payload and response body. Put the redaction rules in the SAME message:
strip `Authorization`, `Cookie`, `Set-Cookie`, `Bearer ...` and every
`token`/`refresh_token`/`access_token` value; replace email, phone, wallet
address and KYC data with `[mine]`; keep paths, query params, `fp-request-id`,
`traceparent`, status codes and JSON shapes. Include a paste template per
endpoint. Reconstruct the call shape, build the object/role matrix and draft
the PoC from the sanitized data. This keeps account-side work with the user and
still unblocks the authenticated phase without the agent ever holding a secret.

## Driving the MCP OAuth flow in a driven browser (no listener needed)

1. `oauth_helpers.py pkce` -> save the verifier.
2. `oauth_helpers.py url <verifier> [audience]` -> authorize URL with a LOOPBACK
   redirect (`http://127.0.0.1:<port>/callback`).
3. Open it in the signed-in driven browser -> consent page -> click Continue.
   Screenshot the consent page (what host/scopes it names — relevant to mix-up).
4. The browser redirects to the loopback URL, which FAILS to load (nothing
   listening) but `location.href` carries `?code=...&state=...`. Read it via
   `js('location.href')` / page_info. Works with cloud OR local browser — the
   code is in the URL, no localhost listener required.
5. `oauth_helpers.py redeem <code> <verifier>` from the agent host -> access +
   refresh token. Then `mcp_client.py <token> initialize|tools/list|call ...`.
6. Bootstrap reads: `grid_whoami` (MCP) + `GET /api/whoami` (org token) +
   `tools/list` -> map org/cluster/region and every tool's argument schema before
   testing.

## Candidate checklist (the consistency question per surface)

- **IDOR on org/tenant-id path params** — token A + org B's uuid in the path
  (`/api/.../orgs/{org_uuid}/...`, wake, ssh-keys, volume delete). Expect 404 for
  another org; any 200 = cross-org access (Critical). Check sibling routes too.
- **Proxy/allowlist bypass (grid_api-style)** — a fixed GET allowlist with
  URL-decoded templated keys + query-string merge. Seams: double-encoding,
  traversal (`/../`), case, trailing slash/dot, `{id}` value injection, params vs
  query precedence. An unlisted path served = finding, rated by what it reaches.
- **Two-phase confirm_token TOCTOU** — "same call with identical arguments +
  single-use token executes." Canonicalization seams: JSON key order, whitespace,
  type coercion (1 vs "1" vs 1.0), null vs absent, unicode normalization. Preview
  cheap, execute canonically-different -> does the cost/destroy change apply?
  Billing integrity = Critical.
- **Free-form query scoping (metrics_query / PromQL / SQL)** — "scoped to your
  org." If enforced by an injected matcher on a SHARED store, a direct label
  matcher or injection may reach other orgs' series. Enumerate visible
  names/labels first, then try cross-tenant matchers.
- **service_call / port-forward SSRF** — one HTTP request to an internal Service.
  Is there a host/port allowlist? Can it reach pod/node IPs, other namespaces,
  cloud metadata, the control plane? Response carrying creds/private data ->
  Critical; otherwise SSRF = High. Needs a cluster (own tenancy).
- **Join-rule / domain matching at signup** — account creation joins the org whose
  rule admits the email. Suffix vs label-boundary bug (`evil-lab.x.edu` matching a
  `lab.x.edu` rule) -> account lands in an EXISTING org = Critical. Needs two
  accounts + an org with a join rule on a domain you control.
- **OAuth mix-up via a shared callback host** — an exact third-party callback
  (e.g. a hosted-agent connector callback) allowed for ALL dynamically provisioned
  clients. Attacker initiates their own connector flow -> authorize URL with
  attacker state + that callback -> victim opens, signs in, approves (consent
  names only the legit host) -> code binds victim identity to ATTACKER's client =
  account takeover WITH interaction (High). Verify the consent wording and whether
  the callback host binds the code to the initiating session.
- **Token-type confusion** — present each token type (MCP OAuth, org API,
  member/workspace, kubectl/device, cluster ServiceAccount) to each verifier (MCP,
  REST, console API, Grafana, cluster API, SSH CA). Cross-acceptance of a wrong
  issuer / another client's audience / expired-or-tampered token = finding. The
  shared-signing-key topology (recon §1) makes this the highest-value matrix.
- **Onboarding descriptor identity oracle** — cluster-id -> name / ssh_user
  (email-derived) / endpoints without token; arbitrary `email` param -> account
  existence oracle (Medium). Needs a valid cluster id (own, from whoami).
- **Sign-in link/code entropy** — analyze the token format from the user's emails
  (redacted). Predict/forge = Critical; brute-force feasibility is bounded by the
  mail-rate cap (e.g. 20/day) and per-code try limit — usually infeasible.
- **Device cross-client binding** — device_code requested by client X redeemed
  with client Y at issuance (only device-capable clients).

## Generic Web/API patterns distilled from public writeups

Use these when the target is an ordinary web app or REST API rather than the
platform-specific surfaces above. All are hypotheses until confirmed.

- **Derived views of a private object** — primary endpoints return 403, but
  `/{id}/preview`, `/{id}/export`, `/{id}/diagram`, `/{id}/summary`,
  `/{id}/versions`, `/{id}/permissions`, `/{id}/history` return 200 and serialize
  the protected content. Enumerate every representation of an object, not just
  the one the UI uses. A UUID exposed by a legitimate share feed is an identifier,
  not an authorization; the finding is the missing object-level check on the
  derived route.
- **Mass assignment** — send a profile/username/password update and inspect the
  response for fields the request did not contain. Replay them in the request and
  check persistence. If the response is only `status: OK`, fuzz parameter names
  with a wordlist and check `/swagger`, `/swagger-ui`, `/api-docs`,
  `/openapi.json` for the object schema. Field classes worth testing: `role`,
  `is_admin`, `verified`, `approved`, `status`, `credit`, `use_limit`, `quota`,
  `plan`, `price`, `owner_id`, `user_id`. A field rejected on one endpoint is
  often accepted on another, so carry the list across endpoints. Impact can be a
  business-logic flaw (reset quota, free credits) rather than privilege escalation.
- **Parser confusion in confirmation flows** — a value stored verbatim but
  rendered differently (null byte, zero-width space, bidi override, trailing
  whitespace) breaks name-based delete/rename confirmations. Ask whether any
  input is reused as the key of a later request. Chain against an object cap for
  an unrecoverable feature-level DoS.
- **IDOR beyond GET and beyond primary routes** — swap the victim's ID in
  PUT/PATCH/DELETE/POST, in JSON bodies, headers (`X-User-Id`) and GraphQL
  `node(id:)`; cover share/export/resend/print/webhook endpoints where the check
  was not copied. Try method change, form-vs-JSON, `id[]=<victim>`, and parameter
  pollution `?id=<own>&id=<victim>`. Confirm blind cases by side effect in the
  victim account, not by the response body.
- **Honest impact scoping** — state exactly which objects and operations were
  proven and whether the boundary was same-org or cross-tenant. Session ID
  substitution is hijacking, not automatically session fixation. Do not claim
  account takeover or cross-tenant access without evidence; the report is rated
  on the proof actually shown.

## Reporting

One root cause per report; a chain rated once by its end state. Include surface +
endpoint, UTC test time, named test accounts/orgs, repro steps with requests +
responses, claimed tier by the page's definitions, and for non-owned data the
identifier + count (never contents). Draft for the user to submit; payment often
requires the user's tax paperwork and a post-fix retest confirmation.
