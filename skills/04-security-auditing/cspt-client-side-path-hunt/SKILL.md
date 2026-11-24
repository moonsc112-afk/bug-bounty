---
name: cspt-client-side-path-hunt
description: "Use when hunting CSPT/CSRFg: URL-controlled path sinks."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [BugBounty, WebAPI, CSPT, CSRFg, ClientSide]
    related_skills: [web-api-bounty-hunt, writeup-intel-digest, blocked-page-recovery]
---

# CSPT / client-side request forgery hunt

Owns one hypothesis: a value the attacker puts in the URL is read by client JavaScript and used to build the path of a request the browser sends. The request is same-origin, so cookies ride along and origin-based CSRF checks often do not apply. What is broken is path control, not a CSRF token. This skill takes that hypothesis from bundle evidence to a one-click chain or a documented kill. `web-api-bounty-hunt` owns recon and reachability; `writeup-intel-digest` turns source writeups into checklist bullets.

## When to Use

- An invitation, share, preview, or deep link triggers a request automatically when opened.
- A URL query value appears to be interpolated into a fetch or XHR path.
- A writeup describes CSPT, CSRFg, or one-click state change and you want to test it on a live target.
- Not for ordinary IDOR (use `web-api-authz-matrix`) and not for classic cross-origin CSRF with a missing token (covered in the Web/API checklist section 5b).

## Procedure

### 1. Static source to sink scan

On the downloaded JS bundles, search these source patterns: `URLSearchParams`, `useSearchParams`, `searchParams.get`, `location.search`, `router.query`. Search these sinks near them: `fetch(`, `axios`, `instrumentedFetch`, template literals with `${}` that contain `/api/` or `/uc/`.

A candidate window is a source and a sink within roughly 700 characters before and 900 after, with an interpolated template literal. Save every window to a file; do not judge from counts alone.

Filter known noise before reading: Privy OAuth internals (`privy_oauth_state`, `privy_oauth_code`), Next.js RSC internals (`NEXT_RSC_UNION_QUERY`), Sentry DSN envelope building, Next image `?dpl=` cache busting. Treat first-party analytics and deep-link parameters as state inputs until a sink is proven; do not attribute vendor SDK code to the target.

### 2. Read-only browser differential

Inject a recorder BEFORE the first reload, then navigate twice with different parameter values.

```python
rec = """window.__cap=[];
const of=window.fetch;
window.fetch=function(...a){try{window.__cap.push({k:'fetch',u:String((a[0]&&a[0].url)||a[0]),m:String((a[1]&&a[1].method)||'GET')})}catch(e){}return of.apply(this,a)};
const oo=XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open=function(m,u,...r){try{window.__cap.push({k:'xhr',u:String(u),m:String(m)})}catch(e){}return oo.call(this,m,u,...r)};"""
cdp('Page.addScriptToEvaluateOnNewDocument', source=rec)
```

For each value: `goto_url`, `wait_for_load`, wait about four seconds, then read `JSON.stringify(window.__cap)`. Normalize volatile ids to `<ID>`, split each URL on `?`, and diff the two sets of `(method, path)`. Also check whether the parameter value itself appears in any recorded URL and whether any recorded request is non-GET/HEAD.

A negative result means: no source-to-sink link on that page in that session state. Compare the set of normalized paths, not the count of requests, and check that the parameter value never appears in a recorded URL. That kills the hypothesis for the signed-out surface only, because bundles loaded after login are still unseen.

### 3. Find a sink whose default state is permissive

Only after step 2 shows a real source-to-sink link, inventory state-changing PUT/POST endpoints. The exploitable shape from the reference writeup was: edit folder permissions with the permission object in the request body; removing the body returned `200 OK` with `{"permissions": null}` and reset the folder to Open Access, letting every user edit files.

- [ ] Try empty body, `null`, and a wrong data type, then read the object state back
- [ ] Prefer endpoints with two named states where one is permissive: view only versus open, private versus public, member versus owner
- [ ] Confirm the request is built client-side from the URL value, not from a server-held record

### 4. Chain and prove one click

1. Two accounts you own, attacker A and victim B, with a marker on B's disposable object.
2. Put the full target path into the controllable parameter with URL-encoded traversal (`%2f` for `/`). Example shape: `..%2f..%2fsettings%2fworkspaces%2f<id>%2ffolders%2f<uuid>%2fpermissions`.
3. Open the crafted link in B's session and record the request the browser generates.
4. Read B's object before and after. A change with no other interaction is the proof.
5. Stop at proof. No widening to other accounts.

## Evidence

Keep the crafted URL, both differential request lists, the generated state-changing request with path, method, body and relevant headers, the before and after object state with the marker, and the fact that the victim only opened a link. State severity as a claim until the program rates it. The reference writeup's author himself estimated only medium severity.

## Pitfalls

- A static match is a lead, not a finding. Confirm with the recorder differential before spending account-phase probes.
- A negative signed-out differential is not proof that authenticated pages are clean. Rerun steps 1 and 2 after the operator hands over a session.
- Do not send state-changing requests during discovery. Steps 1 and 2 are read-only.
- Do not confuse CSPT with classic CSRF. If the value is not in the request path, this skill does not own the case.
- Install the CDP recorder in its own call and confirm it returns an identifier before navigating. Do not batch CDP injection together with tab creation, navigation, and reads in one block; if the setup fails silently the page loads unrecorded and the differential looks like a clean negative.
- Account creation, login, and session handoff belong to the operator. Give numbered steps, never type his credentials.
