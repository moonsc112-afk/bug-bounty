# Portable packaging for a hardened Electron app

Use when turning a working Electron fork into a distributable Windows folder without downloading a runtime at package time.

## Procedure

1. Confirm the local runtime exists at `node_modules/electron/dist/electron.exe`. If missing, install it with `npm rebuild electron`; do not make packaging depend on a network fetch when the binary is already local.
2. Create a `--dry-run` mode first. It should print the source `main`, the packaged `main`, target platform, excluded secret and vendor paths, and every required app file that would ship. Add a `node:test` case that asserts those lines before writing the real copy logic.
3. Build into a gitignored folder such as `export/<name>/`. Copy the Electron dist there, then copy first-party app files flattened into `resources/app/`. Copy root `node_modules/` into the same app root so runtime dependencies resolve.
4. Regenerate `resources/app/package.json` with `main` relative to the app root, for example `editor-main.js`. Do not copy the repository `package.json` unchanged when its `main` is `resources/app/editor-main.js`, because that would double-nest the app and move config resolution.
5. Exclude AI config files, `*.key`, vendor main and index files, bundled runtime directories, `node_modules` stored inside `resources/app`, tests, tools, source-only folders, export output, and git metadata.
6. Rename `electron.exe` to the product name, write a `sha256` sidecar, and add a short `START.txt` that states portability, license provenance, and which proprietary runtime is not included.
7. Smoke test the packaged executable with logging and a timeout, relying on an explicit `did-finish-load` ready log rather than treating a timeout kill message as a crash. For a bridge check, launch with `--remote-debugging-port`, connect with the global `WebSocket`, and evaluate `Runtime.evaluate` for `window.getApp()` and the exposed API object.

## Pitfalls

- Do not double-nest `resources/app/resources/app`; regenerate the app-root `package.json` with a root-relative `main`.
- Do not package `ai_config.json`, key files, or any vendor runtime, even if they are present locally during development.
- Do not use a downloader by default when the local Electron dist is already installed; it adds a network dependency to a step that should be deterministic.
- Do not claim a package works because the build exited zero; run the packaged exe and assert both the ready log and the renderer bridge.
- Do not let generated artifacts enter the commit; gitignore the output directory and test the dry-run plan instead.
