---
name: installer-static-triage
description: "Use before running installers: hash, sign, NSIS extract."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Security, ReverseEngineering, BugBounty]
---

# Installer static triage

## When to Use

Use when a target ships a desktop installer and you need evidence before executing it, or when a bug-bounty target has no public source repo but a downloadable binary exists.

## Verify before running

- Download to a large drive, not C:. Recompute SHA256 and compare with the vendor header or published checksum.
- On Windows run `powershell.exe -NoProfile -Command "$s = Get-AuthenticodeSignature -FilePath 'PATH'; $s.Status; $s.SignerCertificate | Select-Object Subject,Issuer,NotBefore,NotAfter,Thumbprint"`.
- Treat a valid signature as proof of signer identity, not permission to trust the code.

## Extract without executing

- Identify the format with `file installer.exe`. Nullsoft Installer self-extracting archives are common.
- Inventory with `7zr l installer.exe > listing.txt`.
- Extract only what you need: `7zr x installer.exe "resources\app\dist\gateway\server.js" -o<dir> -y`.
- Bundled JS is often minified but keeps string constants. Grep for gate names, env vars, policy keys, and consent fields.

## Keep claims honest

- A documentation sentence is a hypothesis until the bundle or a live test confirms it.
- If code disproves the hypothesis, retract in the same pass: mark every draft, payload, and runbook that carried it as RETRACTED, and append the disproving observation to the findings file.
- Do not leave stale draft text that could be submitted by accident.

## Record

- Keep the exact command, hash, signer subject, cert dates, and file paths in a verification file.
- State explicitly that nothing was installed or executed.
