#!/usr/bin/env python3
"""Send a bounty-submission email (e.g. age-encrypted report.age) via SMTP.

The operator fills a local ini file; this script never prints the password.

Cred ini schema (operator fills; keep out of chats/repos):
    [mail]
    email = you@example.com        ; sender (also used for IMAP verify)
    smtp_host = smtp.gmail.com
    smtp_port = 587
    encryption = starttls          ; or ssl (usually port 465)
    imap_host = imap.gmail.com     ; optional; enables Sent-folder verification
    password = <provider app password>

Usage:
    python send_report_email.py --cred CRED.ini --to security@example.xyz \\
        --subject "Security report (age-encrypted) - N verified findings" \\
        --body-file body.txt --attach report.age \\
        [--expected-sha256 <hex of first attachment>] [--dry-run]

Always dry-run first. Exit codes: 0 ok, 1 send/verify failure, 2 config/input error.
"""
import argparse
import configparser
import hashlib
import imaplib
import pathlib
import smtplib
import ssl
import sys
from email.message import EmailMessage


def _fail(msg: str) -> int:
    print(f"ERROR: {msg}")
    return 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cred", required=True, help="path to the operator-filled ini")
    ap.add_argument("--to", required=True)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--body-file", required=True)
    ap.add_argument("--attach", action="append", default=[], help="repeatable")
    ap.add_argument("--expected-sha256", default=None,
                    help="sha256 of the FIRST attachment; refuse to send on mismatch")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cred_path = pathlib.Path(args.cred)
    if not cred_path.exists():
        return _fail(f"cred file not found: {cred_path}")
    cp = configparser.ConfigParser()
    cp.read(cred_path, encoding="utf-8")
    if "mail" not in cp:
        return _fail("section [mail] missing in cred file")
    m = cp["mail"]
    email_addr = (m.get("email") or "").strip()
    password = (m.get("password") or "").strip().replace(" ", "")
    host = (m.get("smtp_host") or "smtp.gmail.com").strip()
    port = int((m.get("smtp_port") or "587").strip())
    enc = (m.get("encryption") or "starttls").strip().lower()
    imap_host = (m.get("imap_host") or "").strip()
    if not email_addr or "@" not in email_addr:
        return _fail("field 'email' not filled / invalid")
    if not password:
        return _fail("field 'password' (app password) not filled")

    body = pathlib.Path(args.body_file).read_text(encoding="utf-8")
    payloads = []
    for a in args.attach:
        p = pathlib.Path(a)
        if not p.exists():
            return _fail(f"attachment not found: {p}")
        data = p.read_bytes()
        payloads.append((p.name, data))
        print(f"attach : {p} ({len(data)} bytes) sha256 {hashlib.sha256(data).hexdigest()}")
    if args.expected_sha256 and payloads:
        got = hashlib.sha256(payloads[0][1]).hexdigest()
        if got != args.expected_sha256:
            return _fail("attachment sha256 != --expected-sha256 — verify the artifact before sending")

    msg = EmailMessage()
    msg["From"] = email_addr
    msg["To"] = args.to
    msg["Subject"] = args.subject
    msg.set_content(body)
    for name, data in payloads:
        msg.add_attachment(data, maintype="application", subtype="octet-stream",
                           filename=name)
    print(f"to      : {args.to}\nsubject : {args.subject}\nsmtp    : {host}:{port} [{enc}]")

    if args.dry_run:
        print("DRY RUN - not sending. Configuration looks OK.")
        return 0

    ctx = ssl.create_default_context()
    try:
        if enc == "ssl":
            server = smtplib.SMTP_SSL(host, port, timeout=60, context=ctx)
        else:
            server = smtplib.SMTP(host, port, timeout=60)
            server.ehlo()
            server.starttls(context=ctx)
            server.ehlo()
        server.login(email_addr, password)
        refused = server.send_message(msg)
        server.quit()
    except Exception as e:  # noqa: BLE001 - surface provider errors verbatim
        print(f"SMTP ERROR: {type(e).__name__}: {e}")
        return 1
    if refused:
        print(f"PARTIAL: refused recipients: {refused}")
        return 1
    print("SENT OK (server accepted; no refused recipients)")

    if imap_host:
        try:
            M = imaplib.IMAP4_SSL(imap_host, 993)
            M.login(email_addr, password)
            folder = '"[Gmail]/Sent Mail"' if "gmail" in imap_host else "Sent"
            typ, _ = M.select(folder)
            if typ == "OK":
                q = args.subject.replace('"', "")
                typ, dat = M.search(None, f'(SUBJECT "{q}")')
                ids = dat[0].split() if typ == "OK" and dat and dat[0] else []
                print(f"IMAP verify: {len(ids)} message(s) matching subject in Sent "
                      f"(0 = provider may not copy SMTP-sent mail to Sent)")
            else:
                print(f"IMAP verify: cannot open Sent folder ({typ})")
            M.logout()
        except Exception as e:  # noqa: BLE001
            print(f"IMAP verify skipped: {type(e).__name__}: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
