# Email-based program submissions (age-encrypted, Merkl-style)

For programs that receive submissions by email and want sensitive findings encrypted (Merkl: `security@merkl.xyz`, recipient key `github.com/leomerkl.keys`). The encryption + fingerprint-verification recipe is in SKILL.md § Reporting & submission gates; this file covers getting the mail delivered.

## Program-side rules to satisfy (re-verify per program)
- Unencrypted attachments and links are NOT opened → never attach `report.txt`; the full report travels only as `report.age`.
- "Findings only in a file are not reviewed" → put a one-line summary of every finding in the body (id, mechanism, assessed severity, live-ness), plus the "no production system was attacked; local unit tests + read-only fork sims" line and the payout address (EVM EOA line).
- First-reporter rule → send as soon as the bundle verifies; don't sit on a PoC. After sending: no more testing against production, no public disclosure before the fix is confirmed.

## Delivery path 1 (default): operator sends from their own client
Hand over a copy-paste kit:
- exact Subject line;
- paste-ready plain-text body (no markdown);
- attachment location — copy `report.age` to the Desktop and sha256-verify it through the new path, so the attach dialog is one click;
- warning: Windows hides the `.txt` extension (the folder shows "report" and "report.age" side by side — attach the `.age` one only; "report" is the plaintext);
- the payload must survive byte-identical inside the kit — keep translated glosses OUTSIDE the copied block; a program-mandated placeholder line (e.g. a gate tx-hash first line) that got glossed or translated is exactly what the verbatim line check catches, so run it before handing the kit over.

## Delivery path 2 (agent sends, only when asked): Python smtplib
- Operator fills a local ini (schema in `scripts/send_report_email.py` docstring; example: `merkl_mail_cred.ini` in the user's home). Never paste a password into chat; the script must never echo it. Gmail app passwords require 2FA enabled; strip spaces before login.
- Pre-flight egress before asking the operator for anything: socket banner test to the SMTP host on 587 and 465 (no auth needed) — proves the network path.
- Use `scripts/send_report_email.py`: dry-run first (validates config + attachment sha256 against the recorded final hash), then send, print refused recipients, then IMAP-search the Sent folder for the subject as delivery evidence. Gmail auto-saves SMTP-sent mail to Sent; some providers do not — 0 hits there means "cannot verify via IMAP", not necessarily failure (report the raw SMTP result in that case).

## Status bookkeeping (both paths)
- Flip the workspace's `SUBMISSION_README.md` to SUBMITTED (date + subject + attachment) immediately — future sessions must not resend.
- Advise the operator: watch Spam for the reply; if silence for ~1–2 weeks, a short status-ping follow-up is reasonable; keep PoCs + numbers in the workspace for whatever triage asks next.
