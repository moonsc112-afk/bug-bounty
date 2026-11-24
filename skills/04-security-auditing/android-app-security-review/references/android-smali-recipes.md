# Android smali verification recipes

Use these checks when a lead survives manifest triage. Each recipe ends with what would actually confirm a bug.

## WebView navigation and URL policy

- Find the client subclass: search_files pattern `shouldOverrideUrlLoading|shouldInterceptRequest`, file_glob `*.smali`, scoped to the decompile directory.
- A policy is only as strong as its coverage: `onPageStarted` must reject and call `stopLoading`; `shouldOverrideUrlLoading` must return true to block; `shouldInterceptRequest` must return a 403 for screened schemes. SSL errors must be cancelled, never proceeded.
- For a URL policy, read early returns first (for example the `about:blank` branch before host validation), then rejection of backslash, control characters, userinfo, opaque URIs, host/port checks and `toASCIIString` normalization. java.net.URI accepts host forms Chromium rejects; a parser differential is a bypass only if the validated string is the one the engine actually loads.

## Exported platform services

- `exported=true` with no permission tag is insufficient evidence. Base classes may enforce the permission: AOSP `RecognitionService.java` checks RECORD_AUDIO with a PermissionChecker preflight plus `checkPermissionAndStartDataDelivery` before `onStartListening`.
- For forwarding services, trace both sides: a client API creates a session under the app UID, while the base class checks the original caller. A bug exists only if the caller's missing permission is never checked on either side.

## Caller checks that swallow exceptions

- Read the try/catch around signature checks to the return value. If the check throws SecurityException and the catch returns null, unauthorized callers get no data. If the catch falls through to the data-producing branch, it is a leak.
- Verify each helper's semantics from its own smali; obfuscated names do not indicate what the helper does.

## Sensitive-site blocklists

- Check normalization on both sides: canonicalization of the server-provided host list and runtime lowering, suffix/prefix stripping and parent-domain walk of the visited host. A mismatch between the two is the bypass candidate.
- A domain-only blocklist is weak against IP-literal access by design; only report it if the code claims IP coverage or an IP path reaches the protected content in practice.

## JS bridges

- `addJavascriptInterface` persists across navigations of that WebView. Check whether the bridged WebView can navigate at all (WebViewClient, window.location callers, URL parameters in the local HTML) and whether generation or host guards exist on every annotated bridge method.
- A bridge on a pinned local asset with no navigation path and narrow forwarding methods is not exposure.

## Efficient tooling

- `search_files` with `path: E:\audit\<t>\apktool` and `file_glob: '*.smali'` beats `grep -r` on large decompilations.
- The apktool output `AndroidManifest.xml` is already plain XML; use the rea `inspect_android_package` `summary` detail for a quick component projection.

## OAuth callbacks and ActivityResult reachability

- A callback activity that puts a URI in `setResult` only delivers it to the activity that launched it. Trace the launcher contract and every launch call site before claiming an externally supplied callback URI reaches a second activity's `onActivityResult`; an external explicit intent returns the result to the external app, not to the app's own consumer.
- Read the callback validator's expected-parameter list: presence checks accept arbitrary values. If a consumer feeds a callback query parameter such as `destination_url` straight into `WebView.loadUrl`, keep it in UNRESOLVED until the launcher path is proven reachable.
- Look for one-time state consumption (removing a pending state from a map) as the CSRF control before calling a connector callback state-less.

## Approval receivers and PendingIntents

- Check the manifest `exported` attribute first. A receiver with `exported=false` and no intent filter is not reachable by a third-party broadcast, regardless of what its action strings suggest.
- PendingIntent flags `0xc000000` mean FLAG_UPDATE_CURRENT | FLAG_IMMUTABLE. A helper that clears FLAG_MUTABLE and ORs FLAG_IMMUTABLE closes the extras-tampering path.
- Verify the receiver base class's caller-scope check (signature or trusted-caller verification) before treating a forged decision broadcast as a HITL approval bypass.
