# Browser-driven auth and invite-gate reconstruction

Use when a web target's login is OAuth/OIDC with a hosted identity provider or a
Supabase-style auth service, the access gate is enforced after the provider
callback, and the browser is the practical way to drive consent.

## Multi-tab CDP control

- `browser_exec` `js()` / `page_info()` act on the active tab only. For another
  tab, enumerate `cdp("Target.getTargets")["targetInfos"]`, choose the target,
  then `sid = cdp("Target.attachToTarget", targetId=..., flatten=True)["sessionId"]`.
  Pass `session_id=sid` to `cdp("Runtime.evaluate", ...)`, `Page.captureScreenshot`,
  `Input.dispatchMouseEvent`, and `DOMStorage.getDOMStorageItems`. Why: the
  helper's default session is not necessarily the tab you inspected.
- Several tabs can share an origin and URL. Identify the owned tab by writing a
  unique input value and reading it back through each attached session, not by
  URL alone. Restore mutated inputs and cookies before finishing.
- To change a React-controlled input, call the native value setter on
  `HTMLInputElement.prototype` and dispatch `input`; assigning `element.value`
  alone leaves the form state on the old value.

## REA web tools on a browser already under CDP control

- Find the browser's CDP endpoint from the loopback port owned by the browser
  process (`netstat -ano` plus `/json/version`), then pass that `cdp_endpoint`
  and exact `allowed_origins` to REA `list_browser_targets`,
  `analyze_web_bundle`, and `inspect_web_page`. Why: REA does not discover the
  Hermes-managed browser on its own and rejects origins outside the allowlist.
- `analyze_web_bundle` requires `view: {kind: "web-bundle", collection: ...}`;
  a fresh call accepts `endpoints`, `summary`, or `inferences`. Client bundles
  show client routes and fetch literals only. An invite gate inside a server
  route handler leaves no client trace, so absence of `invite` in a bundle is
  not evidence that no gate exists.
- If `observe_web_session` or `inspect_web_page` reports `attach_limited` with
  an empty timeline or network list, stop retrying it and read
  `Page.getNavigationHistory` through your own attached CDP session. Why: a
  second attach to a target already driven by the browser helper starts after
  the events and cannot see them.

## Reconstructing the redirect and code chain

- Read the sign-in form action and method, then `curl -D headers -o body` the
  sign-in route WITHOUT `-L`. The 307 `Location` and `Set-Cookie` reveal the
  provider authorize URL, code challenge, scopes, and the verifier cookie. Why:
  following redirects hides the handoff and the cookie that binds the code.
- Treat the app callback as the gate. Calling it without a code gives a generic
  failure; the sign-in page's error codes (for example `denied`) map to the
  human-facing message. Save both as evidence, not as a finding.
- Hosted auth APIs commonly accept `authorize` without an apikey but require one
  on token/refresh endpoints. A user access JWT presented as `apikey` is
  rejected because verifiers distinguish anon/service keys from authenticated
  user tokens. Finding the project's publishable key is a separate prerequisite.
- When consent UI is stuck behind a scroll gate or a spinner, drive the
  provider's own web authorize API: read the user token with CDP
  `DOMStorage.getDOMStorageItems` (`securityOrigin` of the provider,
  `isLocalStorage: true`) when page `localStorage` is undefined, then POST the
  provider authorize endpoint with `client_id`, `scope`, `state`,
  `redirect_uri` and `authorize: true`. Use the returned `location` containing
  the one-time code. Why: this yields the same code without fighting UX.
- Follow the provider callback to the auth server callback, then open the
  resulting redirect URL in the browser so the app callback runs with its
  verifier cookie intact.
- Decode every JWT payload from cookies and URL fragments; record `iss`, `sub`,
  `email`, provider metadata, and expiry. A token from a different issuer or
  project is not accepted by this app even if cookie names look identical, and
  a fragment is client-only until code explicitly stores it.

## Localizing the gate with cookie surgery

- Delete the app session cookie, reload, and see whether it is recreated from
  remaining auth cookies. If it is, session creation is lazy and the gate sits
  at token issuance, not on every request.
- Keep the refresh credential and replace the access token with garbage, then
  reload. If a fresh access token appears, the refresh credential is primary.
  Setting only the access token reveals whether the pair is validated.
- Inspect denial responses with `curl -D` and no redirect following. If no
  session cookies are set on denial, there is no leaked session to race; do not
  claim a race without observing cookies on the failure response.
- A denial message that names both a staff email domain and an invite address
  states the gate's inputs directly. Record it as the intended model, then test
  whether the verifier checks claim fields such as `email_verified` or mailbox
  control before treating an unverified address as a bypass; an unverified-email
  hypothesis is not a finding until a second principal actually reaches a
  protected object.
- Edit non-httpOnly identity or analytics cookies only as a negative control:
  if changing the displayed email or role does not change the verdict, the gate
  reads the signed token instead. Restore original values afterward.

## Pitfalls

- Do not treat a client-side error message as proof of the check's input; replay
  the credential the server actually honors (token or cookie pair) and compare
  verdicts.
- Do not reuse an OAuth code or a solved captcha token across attempts; both are
  single-use and produce misleading retry states.
- A signup endpoint's `retry_after` is the authoritative backoff, and repeated
  attempts extend the window. Hand second-account creation back to the operator
  instead of grinding through registration CAPTCHAs.
