---
name: android-app-security-review
description: "Use when auditing an Android APK for security bugs."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [BugBounty, Android, ReverseEngineering, Mobile]
    related_skills: [web-api-bounty-hunt, systematic-debugging, grounded-citations]
---

# Android APK Security Review

Turn an APK plus any accompanying analysis report into confirmed, evidence-backed findings or a clean refutation. Treat the report as a lead list, never as evidence: verify every claim in the shipped bytecode before repeating it.

## When to use

Security review of a native or hybrid Android app: exported components, WebViews and JS bridges, deep links, OAuth redirect handlers, native libraries, protocol parsers. Route chain targets to evm-bounty-source-audit / solana-* and web/API targets to web-api-bounty-hunt.

## Always-on rules

- Work in E:\audit\<target>\ on this host and keep extracted smali, libraries and notes off C:. Deliver the final report in Indonesian, no em-dashes, with file:line evidence for every claim.
- Open a notes file with the first command and keep three sections: CONFIRMED, REFUTED, UNRESOLVED. Write the evidence line when you decide, not at the end.
- A finding needs a reachable path AND a broken check. `android:exported=true`, a missing permission tag, or an inconsistency inside an analysis report are observations, not findings.
- When every lead is refuted, deliver that result plainly. Continued pressure to keep going until a bug is found does not turn an observation into a finding; a defect inside the supplied report (internal contradictions) is a valid final answer when backed by the refuting file:line evidence.
- Lead every user-facing update with the verdict in one or two lines (CONFIRMED, REFUTED, UNRESOLVED). Do not narrate tool state, retries, or analysis chronology. When nothing is confirmed, say so in the first sentence and name the single remaining path.
- When dynamic proof needs a device and none is attached, write the ADB intent script and a minimal third-party caller app, then state plainly that they were not run. Never present an unexecuted PoC or an invented log as evidence; keep the path UNRESOLVED.
- Before claiming a platform-service permission bypass, check whether the framework base class already enforces it. Fetch the AOSP source instead of relying on memory: `curl -sS 'https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/java/<package>/<Class>.java?format=TEXT' | base64 -d`.
- Follow exception handlers to their return value. A signature check that throws into a catch returning null is not a data leak; a catch that continues and returns data is.
- Use the ripgrep-backed search_files tool with `file_glob: '*.smali'` scoped to the decompile directory. A recursive grep over the entire smali tree of a large app can exceed the foreground timeout.
- Pass native paths (E:/..., C:/...) to native Windows programs (java, apktool, javac, git); MSYS /c/... paths are not translated for them. `javac -d /e/...` can exit 0 while writing class files outside the intended directory, so verify the expected output file exists.
- For native `.so` leads, follow `references/native-library-analysis.md`: map report RVAs to decompiler addresses through PT_LOAD headers, and force-create functions auto-analysis missed before quoting decompiled code.
- Delegate independent attack surfaces in parallel, but verify every subagent claim against the actual file before reporting it. A subagent summary is a self-report, not evidence.

## Procedure

1. **Establish identity** — `sha256sum app.apk`, `unzip -l app.apk | grep -E 'classes.*dex|lib/arm64-v8a'`. Compare counts and hash with the report before trusting its claims. Extract PDF report text to a greppable file with pypdf (`PdfReader(...).pages`, join with page markers).
2. **Decompile** — `java -jar E:/tools/apktool/apktool.jar d -f -o E:/audit/<t>/apktool E:/audit/<t>/app.apk > E:/audit/<t>/apktool.log 2>&1`, run in background and poll the log. Output gives smali*/, decoded AndroidManifest.xml, assets/ and native libs.
3. **Manifest triage** — list exported activities, services, receivers and providers with their permission attributes, intent filters, deep-link schemes and task affinity. Mark each exposed component as a surface to verify, not a finding.
4. **Verify each lead in smali** — open the named class; trace branch ordering (early returns before validation?), all entry points and callers, and the real enforcement helper rather than its obfuscated name.
5. **Cross-component checks** — WebViewClient navigation hooks, addJavascriptInterface persistence, intent redirection, PendingIntent flags, URI parser differentials, parent-domain handling in blocklists.
6. **Ground platform behavior** — fetch the AOSP base-class source for any exported framework service before calling it a permission bypass.
6a. **Native libraries** — for ARM64 `.so` leads use `references/native-library-analysis.md`: headless Ghidra with a Java post-script, address mapping first, decompiled code written to a file, and no finding claimed without a caller trace.
7. **Write up** — one root cause per finding, concrete impact, reproduction steps, file:line evidence, and an explicit refutation of the strongest alternative explanation. Record refutations as carefully as findings. Put the final report in a NEW file; write_file refuses to overwrite a notes file patched earlier in the session unless that file is re-read in full. End a blocked or partial report with a short numbered menu of next steps; the user picks an item and expects it carried to completion.

## Tool setup note

If rea `inspect_android_package` reports a missing REA_JADX_MCP_JAR at ~/.local/share/rea/android/, copy the bundled jar from E:\tools\rea-data\android\ into the directory the error names, then retry. Fix setup state; never record a "rea does not work" rule.

See `references/android-smali-recipes.md` for concrete verification recipes (WebView policy, exported services, signature checks, blocklists, JS bridges, OAuth callback reachability, approval receivers).
See `references/native-library-analysis.md` for the ARM64 ELF workflow (Ghidra headless, Java post-scripts, RVA mapping, envelope-parser checks).
