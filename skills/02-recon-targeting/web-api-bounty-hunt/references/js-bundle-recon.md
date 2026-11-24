# JS bundle endpoint recon for SPA consoles

Use when a target's OpenAPI docs cover only part of its surface and the console
is a React/rolldown/Vite SPA. Produces an endpoint map plus a short statement of
which documented families the bundles add.

## Steps

1. Fetch the signed-out shell once with a browser user agent. Save the raw HTML
   and headers. Read the `nc-release` (or equivalent build) meta so the map can
   be tied to a build version. Next.js shells may expose the build only as
   `window.__BUILD_NUMBER__` and a Sentry `meta name="baggage"` value with
   `sentry-release=...`; record both when present.
2. Extract **every** quoted `.js` URL from the raw HTML. Do not rely on
   `<script src>`: modern shells list chunks as `<link rel="modulepreload"
   href="...">` and reference others only in inline imports. A regex over
   `["'][^"']+\.js["']` catches both forms.
3. Fetch each bundle with a one-second gap, respecting the program's per-host
   rate cap. Save to a native `C:/...` scratch path and print byte counts so an
   empty or challenge body is visible immediately.
4. Regex string literals beginning `/api/`, `/public/`, `/mcp`, `/oauth2/`,
   and similar route prefixes. Keep template segments such as `/api/orgs/${e}/`
   intact; they reveal the route family even without a concrete value. Run a
   SECOND broader pass over all quoted strings containing `api/` anywhere, not
   just strings starting with `/`: minified bundles store most routes as
   `${baseUrl}/api/...` or `https://host/api/...`, and the prefix-only regex
   misses whole families (one SPA second pass yielded 61 additional routes).
   Search
   for an embedded client-side API registry first: entries shaped
   `api_name:"...",route_name:"..."` often carry `method:"POST"` and a regex
   path in the preceding few hundred characters. Walking backwards from each
   `route_name` to the last `method` yields first-party routes WITH their HTTP
   method, far higher signal than the raw literal list.
5. Diff the literal paths against the OpenAPI route map. A family the docs do
   not mention is candidate surface, not a finding. Group by family and record
   the source bundle for each path. When no OpenAPI or Swagger document is
   published, say so once and stop guessing doc URLs; the bundle registry
   becomes the route map. Also grep `wss?://` in the bundles for WebSocket
   channels, which a REST path list will not show.
5b. Harvest first-party hosts (any `*.domain` string) from the bundles and
    add passive sources before probing. CertSpotter
    (`https://api.certspotter.com/v1/issuances?domain=<domain>&include_subdomains=true&expand=dns_names`)
    and Wayback CDX
    (`https://web.archive.org/cdx/search/cdx?url=*.<domain>/*&output=json&collapse=urlkey&fl=original&limit=500`)
    both return JSON that is easy to union with bundle-derived hosts; CT search
    sites are another input. An absent subdomain is not proof it does not exist.
6. Confirm the live call shape for any candidate in a browser session before
   probing. Resource timing returns URLs only, and bundle literals are
   incomplete. Inject a recorder before the page loads, then reload and read
   the log:

   ```
   cdp('Page.addScriptToEvaluateOnNewDocument', source=`
   window.__calls = [];
   const of = window.fetch;
   window.fetch = function (input, init) {
     const url = typeof input === 'string' ? input : (input && input.url) || String(input);
     const method = (init && init.method) || (input && input.method) || 'GET';
     const headers = {};
     new Headers((init && init.headers) || {}).forEach((v,k)=>headers[k]=v);
     window.__calls.push({kind:'fetch', method, url, headers, body: String((init && init.body) || '').slice(0,400)});
     return of.apply(this, arguments);
   };
   const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send,
         oh = XMLHttpRequest.prototype.setRequestHeader;
   XMLHttpRequest.prototype.open = function (method, url) {
     this.__rec = {kind:'xhr', method, url, headers:{}, body:null};
     window.__calls.push(this.__rec);
     return oo.apply(this, arguments);
   };
   XMLHttpRequest.prototype.setRequestHeader = function (k,v) {
     if (this.__rec) this.__rec.headers[k] = String(v);
     return oh.apply(this, arguments);
   };
   XMLHttpRequest.prototype.send = function (b) {
     if (this.__rec) this.__rec.body = b ? String(b).slice(0,400) : null;
     return os.apply(this, arguments);
   };
   `)
   js('location.reload()'); wait_for_load(); js('window.__calls')
   ```

   XHR coverage is the reliable part because modules may have captured the
   original `fetch` before the patch; supplement with resource timing for
   fetch-only calls. Visit two page types (a listing and a detail page), since
   endpoint families differ by route. Pace navigation: a tight `goto_url` loop
   over several routes lands on `chrome-error://chromewebdata/` because the
   page has not committed; sleep roughly 2-3 s after each navigation before
   reading the log. The injected recorder can vanish after a run of
   navigations, so check `Array.isArray(window.__calls)` before each page and
   re-inject when needed. For URL-level mapping only,
   `performance.getEntriesByType('resource').map(e => e.name)` needs no
   injection and survives those navigations; it loses method, headers and
   bodies, so treat it as the fallback, not the primary recorder.
7. Deliver a stable markdown report plus a JSON map of path -> source bundles
   in the home directory, with `MEDIA:` links. Include the build version, the
   request count, and the rate used.

## Pitfalls

- Regex the raw file with `open()` in `execute_code`, not `read_file` output:
  `read_file` inserts line numbers and truncates long lines, which breaks
  literal extraction from minified single-line bundles.
- Vendor chunks are large and mostly noise, but still scan them; a helper that
  builds auth headers can live there. Do not attribute their route literals to
  the target: an embedded auth SDK emits dozens of `/api/v1/*` paths (SIWE,
  passkeys, passwordless, OAuth, MFA, onramp) against its own base such as
  `https://auth.privy.io`. Read the base URL and the SDK app ID out of the
  bundle and classify those paths as vendor before writing the map, or the
  report claims a large false attack surface. Resolve the base constant for
  EVERY endpoint family, not only vendor-looking SDK paths: on-ramp and payment
  helpers emit ordinary-looking `/api/account`, `/api/bridge/*`, `/api/meld/*`
  and `/api/request-fund` routes whose base resolves to a third-party host.
  Probing those wastes scope and rate budget and can breach the engagement.
- If no `Authorization`, `Basic `, or `WWW-Authenticate` string appears in any
  bundle, a Basic-auth-bypass pattern from a writeup is likely inapplicable.
  Kill it with a six to seven request read-only differential (with and without
  the trigger header on two representative endpoints), record the status and
  challenge header, and stop, instead of carrying the pattern into the account
  phase.
- Bundle route literals are candidate surface, not the live call map. A SPA
  can call POST endpoints and whole families (navigation flyout, price history,
  comments feed) whose paths never appear as string literals. Report both what
  the bundle declares and what the browser actually called, and mark which
  endpoints are reachable signed-out versus account-gated.
- UUID or template paths need real values from an owned account; never guess a
  value and never probe another party's data to get one.
- Record the API base URL and the allowed-domain list from the bundle before
  probing. A web target's frontend host often is not its API host; a relative
  `/api/...` path can 404 on `www` while the same path on `api.<domain>` works.
  Missing this makes public endpoints look absent.
