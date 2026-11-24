---
name: web-api-authz-matrix
description: "Use for IDOR/BOLA/BFLA: build the object-role matrix."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [BugBounty, WebAPI, IDOR, BOLA, BFLA, Authz]
    related_skills: [web-api-bounty-hunt, race-condition-web-api, finding-validation-gate, evidence-hygiene]
---

# Web/API authorization matrix (IDOR, BOLA, BFLA)

Authorization bugs are the cheapest payable class in web2 work: no memory tricks, only a disciplined second-account matrix. This skill owns that matrix. `web-api-bounty-hunt` owns recon and reachability.

## When to Use

- The target exposes per-object resources (records, invoices, wallets, files, exports) or roles (member, admin, owner, support).
- A numeric or UUID identifier appears in a path, query, body or GraphQL argument.
- A mutating endpoint is reachable by a lower role and the UI hides it, but the API does not.
- The target exposes an approval or consent-grant store as CRUD routes. Treat every grant as an owned object, not as a harmless UI preference.
- Not for state-competition bugs (`race-condition-web-api`) or scope questions (`chain-scope-guard`).

## Before the matrix: locate the gate

- Decode the auth token (JWT payload, or the opaque-session equivalent) and list its claims before recruiting a second account. If no role/tenant/entitlement claim exists, authorization is enforced server-side, so the interesting question becomes which principal can obtain any accepted token at all.
- Replay an authenticated-only GET with each session cookie alone and with none. The credential that returns 200 is what the API honors; swap that one in the matrix, not whichever cookie the UI happens to set.
- Verify the login in the exact automation surface you will replay from. GUI desktop control and CDP-managed browser control keep separate cookie jars, so a successful login in one does not authenticate the other. WHY: building a matrix on a session you cannot read produces 401s that look like routing or authz results and stalls the whole test.
- Distinguish a login-time gate (invite list, signup allowlist, SSO restriction) from an object-level gap. A rejected login is not an IDOR/BOLA/BFLA cell; report it as broken access control only with a token the API accepts plus evidence of the protected object it reaches. Map the exact identity claim the gate reads by comparing two accounts across every login provider: a signed IdP token outranks JS-writable mirror cookies, so editing those cookies changes the display but not the decision. Run the gate-mapping sequence in `references/login-gate-recon.md` before treating an invite wall as a finding; decode each provider's JWT issuer, exercise each auth route with a rejected identity, and test cookie rehydration and tampering separately. WHY: providers can point at different identity projects, and a server-minted session pair can be rebuilt without rechecking the gate.
- For a local-first app, read the gateway admission check before filling the matrix. If a coarse gateway token is configured, every non-exempt route requires the same token and there is no per-user object boundary; if no token is configured, the Host/Origin gate decides remote reachability and a wildcard CORS list may still be restricted to loopback origins. Record which principal can actually reach the route before calling absent owner checks a finding.
- Find the real gateway port from the listening sockets owned by the app process, then probe `/healthz`. Desktop apps often bind an ephemeral loopback port instead of a documented fixed port. WHY: a failed probe on 8080 is not an unreachable gateway, and treating it as one aborts a valid matrix before it starts.
- Hand matrix commands in the operator's shell syntax. In Windows PowerShell use `$env:VAR='...'` and `curl.exe`; `export` and the `curl` alias are Git Bash and `Invoke-WebRequest` respectively. WHY: syntax from a different shell produces argument errors that look like target failures.

## Two accounts, one marker

Create account A and account B from the same program alias, with distinct markers (`markerA`, `markerB`) in the fields you will compare. A same-tenant pair is enough for horizontal bugs; a higher-role account is needed for vertical ones. Record both login emails and object ids before testing.

## Matrix shape

Fill per object class, not per endpoint. One row per `(principal, object, verb)`: 

```
Object: invoice
Verb | Owner (A) | Other user (B) | Lower role | Higher role | Unauth
READ | 200 | ??? | | | 
UPDATE | 200 | ??? | | |
DELETE | 204 | ??? | | |
LIST/export | 200 | ??? | | |
```

`???` is the only interesting cell. Every other cell is baseline confirmation.

## Procedure

0. Probe reachability before any credentials. Send a health or unauthenticated GET to the base URL first; a local-first app may have no gateway listener even though its docs describe routes. Stop when the route is unreachable instead of interpreting a connection failure as an authz result.

1. Inventory object classes and their id formats from the JS bundle, OpenAPI or GraphQL schema. For consent or approval grants, read the lookup predicate before filling cells: if it matches only on scope id and tool name while ignoring the supplied `user_id`, a grant created by principal A can authorize principal B's session, and the constraints are the real permission boundary.
2. Capture an owner request for each verb, verbatim, with cookies from account A.
3. Replay with account B's cookie and A's object id. Swap headers too: `Authorization`, tenant, and org headers.
4. Then vary the id, not the cookie: adjacent integers, zero-padded, UUID from B, id from a deleted record.
5. Then change the verb or path shape: PUT for PATCH, `/export` for `/list`, GraphQL node id in a different root.
6. Then lower the privilege: strip the role claim, call the admin route as member, call the owner-only route as invited guest.
7. Negative control at every step: the same request with the correct cookie must still succeed, otherwise you proved a routing accident, not an authz gap.

## The differential moment

A finding exists when B's cookie returns A's data with a 200 and a body that matches A's marker, or when a lower role completes a higher-role mutation and the state visibly changed. The mutation must be read back with the higher-role account to prove persistence.

Anything weaker is a lead:

- 200 with an empty envelope, or a zeroed `data: []`, is not access. Check the field, not the status.
- A token that carries `sub` and an id in the URL can pass by accident: the server may prefer the token. Change the id in the body too, and try without the token.
- GraphQL returns 200 for errors; read `errors[].extensions.code` before declaring success.
- A `user_id` overwritten in the body is mass assignment, a different class: keep it separate.

## Credential handling when the matrix needs API keys

When the agent's own terminal has no keys, never ask the operator to paste API
keys or session cookies into chat. Hand them a stdlib runner script executed in
their own shell instead: read the keys from environment variables, refuse to
run when any variable is missing, send at most one request per matrix cell in
sequence, redact the `Authorization` header and every known secret value from
all output, and write redacted JSON plus a status table for the agent to read.
WHY: pasted credentials become durable chat and tool-log exposure, while a
locally run script keeps the secret inside the operator's environment and still
produces analyzable evidence.

- Mask only secret values. Never mask a syntactic value or cmdlet fragment such as `AUTH_MODE=bearer` or `Get-Content` with `***`: the operator copies the placeholder literally and gets parser errors that look like a target failure. State the literal word to type when the masked form would be copied.
- A and B must be distinct credentials before any cross-cell is interpreted. If the operator set `AUTH_B` from `AUTH_A`, every cross-scope write, read and revoke is self-access, and principal labels in a redacted matrix can still show A for both roles. Verify from the runner output that the two credentials differ, or close the cross-principal claim as unproven. WHY: a same-token positive control proves routing and auth shape, not an object-level authorization gap.

Per confirmed cell: raw request with B's cookie, the response containing A's marker, the read-back as A, and the same request with B's own id as the negative control. Redact per `evidence-hygiene`; keep the marker visible, it is the proof. Request and response timestamps must be within the same minute.

## Severity notes

No P1 without a real object class: a leaked draft title is P4, a leaked invoice with amount and address is P3/P2, a cross-tenant file download or account takeover is P1/P2. State the object class and the field exposed, not just "IDOR".

## Pitfalls

- Make each matrix case vary exactly the condition its label claims. A case named "larger notional" that resends the same body as the cross-wallet case adds no coverage, and the table looks complete while one dimension was never tested. Diff the case bodies before interpreting the cells. WHY: a mislabeled duplicate silently removes a test dimension from the matrix.
- Do not test on a second account created in a different workspace; the tenant guard will mask a true horizontal bug.
- Do not mass-modify data on the wrong partner with a scripted sweep; one id, read first.
- A missing `403` where the UI hides the button is not a finding until the mutation lands.
- CORS and cookies differ per host: a sibling `api.` host may accept a session the `www` host issued without any authz change.
- Replays inside one second on a mutating verb can reproduce a race, not an authz bug: separate the two with a sequential run first.
- Do not claim a service-wide login gate as IDOR: without a second principal that reaches a concrete object, there is no object-role matrix to fill.
- A missing per-object owner check is not automatically cross-tenant. Map the coarse gateway token and the Host/Origin admission gate first; a local single-owner control plane can intentionally let any caller with gateway access edit any object id while still rejecting foreign origins. WHY: the object-role cell only exists for a principal the API actually accepts.
- When an audited surface has no object classes, roles or authenticated sessions, record the matrix as N/A in the coverage ledger with the evidence that proves it (no object ids in the route map, no login routes, no role claims). Marking it N/A with evidence is a completed class, not a skipped one.

## Support files

- `references/login-gate-recon.md` - ordered sequence for mapping an invite/allowlist gate: auth-route inventory, JWT issuer comparison, four cookie tests, failed-callback cookie check, CDP frame disambiguation, and operator handoff for a second account.
- `scripts/authz_matrix_runner.py` - stdlib two-principal matrix template. Copy it, edit `CASES`, and hand it to the operator to run in their own shell so credentials stay out of chat and results are redacted before the agent reads them.
- A body-supplied object identifier such as `walletAddress` is not automatically an owned resource. A generated transaction payload for another address is not impact by itself: require a state change on that other principal's object, non-public data, or a side effect on the other account before calling it a finding. WHY: many APIs intentionally build calldata for arbitrary addresses, and the owner's signature remains a real gate.
- Prove the endpoint honours the swapped credential before building the whole matrix. Send a no-auth control and an owner-positive control first; if the positive control fails, stop and fix the request shape instead of reading cross-principal results from a routing accident.
- Do not treat an approval grant with only a broad chain or network plus an upper amount cap as a narrowly scoped permission. It is blanket approval for every matching call below the cap. Require an exact argument hash or a typed recipient, and read the grant back from the other principal before calling the write cross-principal. WHY: a constraint that looks like a safety limit still authorizes the whole matching class of actions.
- Do not use a fund-moving grant during the matrix just because the target tool is fund-moving. Create the grant with the smallest valid cap and never execute the granted tool; an unexecuted grant is an authorization artifact, not loss of funds.
