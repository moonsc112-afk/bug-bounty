# Unauthenticated OAuth / MCP / API recon probe matrix

Read-only, low-volume (sleep ~0.4-0.5s between probes; stay under the program's
per-host rate cap). Save raw headers AND body for every probe (`curl -D h -o b
-w '%{http_code}'`) — they are the evidence and the elimination record. Set hosts
as shell vars; nothing here is target-specific.

## 1. Metadata chain (map the flow before probing it)

- `GET <resource>/.well-known/oauth-protected-resource/<path>` (RFC 9728) ->
  `authorization_servers[]`, `scopes_supported`, `bearer_methods_supported`.
- `GET <as>/.well-known/openid-configuration` -> authorization/token/device/
  userinfo/revocation/introspection endpoints, `registration_endpoint` (DCR),
  `grant_types_supported`, `response_types_supported`,
  `code_challenge_methods_supported`, `token_endpoint_auth_methods_supported`.
- Also fetch the ROOT issuer's `/.well-known/openid-configuration` and
  `/.well-known/jwks.json` if the AS is a per-client shim over a core issuer.
- **Compare JWKS across issuers/clients**: identical `kid` + `n` = one shared
  signing key. That is a token-confusion CANDIDATE (a verifier that checks only
  signature, not iss/aud), not a finding by itself — key sharing is often by
  design. Test acceptance with real tokens in the authenticated phase.
- Note the server stack from headers/body artifacts (e.g. `server: uvicorn` shim
  over Ory Hydra `/oauth2/*`; a leaked Go struct field like `"Header": null` in a
  device response fingerprints Hydra). A version banner alone is ineligible;
  you need a working deviation.

## 2. MCP wire (hosted MCP server)

- `POST <mcp>` initialize, no auth -> expect `401` + `WWW-Authenticate: Bearer
  resource_metadata="..."`. Confirms the RFC 9728 challenge.
- `GET`/`DELETE <mcp>` -> expect `405` (stateless Streamable HTTP, POST only).
- Batch JSON-RPC -> refused; `notifications/*` -> `202`. Methods: initialize,
  ping, tools/list, tools/call. Result clipping (e.g. 40k chars) is documented.
- `POST <registration_endpoint>` (DCR) with your own `redirect_uris` -> note the
  returned `client_id`. A shim returns a SHARED client_id and echoes your
  metadata; real provisioning may instead happen per-redirect at authorize time
  (each distinct redirect_uri yields a distinct `client_id`, reused for the same
  redirect). Neither is a bug alone.

## 3. Authorize endpoint (compute a real S256 PKCE challenge first)

`challenge = base64url(sha256(verifier))` no padding; `state` must be >= 8 chars
(Hydra rejects short state with `invalid_state` — do not mistake that for an
audience/redirect rejection). Probe:

- no `code_challenge`, and `code_challenge_method=plain` -> expect `403` at the
  edge AND at the core authorize (test both layers).
- `response_type=token` / `code token` (implicit) -> expect refusal.
- **redirect_uri allowlist bypass matrix** (each its own probe):
  - external host (`https://evil.example.com/cb`)
  - suffix trick (`http://127.0.0.1.evil.example.com`, `https://allowed.host.evil.com`)
  - userinfo (`http://127.0.0.1@evil.example.com`)
  - fragment (`http://evil.example.com#@127.0.0.1`)
  - decimal/hex/octal loopback (`http://2130706433`, `http://0x7f000001`)
  - IPv6 loopback (`http://[::1]:PORT/cb`)
  - LAN (`http://192.168.0.1`) and link-local metadata (`http://169.254.169.254`)
  - allowed-host path scope: exact callback path vs other paths vs prefix vs
    trailing-slash/traversal; other plausible allowed hosts (apex, workspace,
    other OAuth clients' hosts).
  - Loopback (127.0.0.1/localhost/[::1], any port/path) + an exact third-party
    callback path are commonly allowed BY DESIGN for MCP clients. A shared
    third-party callback allowed for ALL clients is a mix-up candidate (see
    authenticated-test-plan.md), not an open redirect.
- **audience / resource override**: pass `audience=<value>` (and separately
  `resource=<value>`, RFC 8707) to the shim authorize. Observe whether the shim
  forwards it. THEN hit the CORE authorize directly with a provisioned client_id
  + the same audience. The core commonly validates against a per-client whitelist:
  `invalid_request: Requested audience 'X' has not been whitelisted by the OAuth
  2.0 Client` = DEFENDED. Only `audience = the client's own id` (the shim default)
  is accepted. If the core accepts an arbitrary audience, that is a live
  token-confusion vector — carry it to the authenticated phase.
- redirect_uri mismatch against a provisioned client's registered URI -> expect
  `invalid_request` (redirect does not match pre-registered).

## 4. Token endpoint grant probes (use a NONEXISTENT user for password tests)

- `grant_type=client_credentials` with a public client -> expect refusal
  ("public client not allowed").
- `grant_type=password` (ROPC) -> expect refusal for an interactive client. Use a
  nonexistent username so you never lock a real account; differing error shapes
  for unknown-user vs wrong-password = an enumeration oracle (identity exposure).
- `grant_type=authorization_code` with a fabricated code, and
  `grant_type=refresh_token` with a fabricated token -> note error shapes.
- `grant_type=urn:ietf:params:oauth:grant-type:device_code` with a client_id that
  lacks the device grant -> `unauthorized_client` (per-client grant enforcement).

## 5. Device flow

- `POST <device_endpoint>` client_id=<client> -> `device_code`, `user_code`,
  `verification_uri[_complete]`, `expires_in`. Note the user_code alphabet/length
  for brute-force feasibility (8 chars from a ~20-char alphabet is infeasible;
  measure against the program's rate cap, never volume-test).
- Poll the token endpoint with the device_code -> `authorization_pending` until a
  user approves. Cross-client_id poll tests device_code<->client binding (the
  grant-type check fires at poll; issuance binding needs the authenticated phase).

## 6. Retired / legacy IdP paths (a path that still signs in = finding)

Probe the old identity software's paths on the auth host; expect redirect-to-new
or 404. Authentik: `/if/flow/`, `/api/v3/`, `/admin/`, `/static/`. Keycloak:
`/auth/realms/`. Ory admin: `/oauth2/introspect`, `/oauth2/admin/clients` (should
not be public). The program's "known and accepted" usually documents these as
retired — confirm, don't report the documented redirect/404.

## 7. Public surfaces that feed the authenticated phase

- Onboarding/setup scripts (e.g. `access.<host>/setup.sh`) reveal public
  descriptor endpoints (`/api/onboard/<ref>?email=`) that may return cluster
  name, SSH host/port/user (often email-derived), OIDC issuer, kubeconfig URL
  WITHOUT a token. Test the existence-oracle shape (uniform 404 vs distinguishable)
  and whether the email param resolves arbitrary accounts. A kubeconfig that is
  just a public PKCE client + CA (no secrets) is by design; access is enforced at
  device sign-in + RBAC.
- OpenAPI contracts (`/api/*/openapi.json`), `/llms.txt`, `/AGENTS.md`,
  `llms-full.txt` -> build a route map (method, path, auth scheme). Flag routes
  with org/tenant-id PATH params (IDOR candidates) and console-session-only
  destructive actions.
- Public feeds (checkpoint/public feed, signed-out console anonymous feed) are
  public by design — reading them is not a finding, but harvest identifiers
  (cluster ids, org display names) for descriptor/IDOR tests.
- JS bundles: the entry HTML lists chunks; login/auth chunks reveal the sign-in
  API endpoints (`/u/login/email`, `/u/login/password`, passkey options, etc.).
  Small loader chunks import the real logic — follow the imports.
