#!/usr/bin/env python3
"""Template for a two-principal authorization matrix. Edit CASES per target.

Runs in the OPERATOR's shell. Reads credentials from environment variables,
refuses to run when any required variable is missing, sends one request per
cell sequentially, redacts secrets from every artifact, and writes a status
table plus a JSON body for the agent to read.

Required env by default: BASE_URL, AUTH_MODE, TOKEN_A, TOKEN_B, OBJECT_A, OBJECT_B
AUTH_MODE is bearer, cookie or none. Never ask the operator to paste secrets
into chat.
"""
import datetime as dt
import json
import os
import pathlib
import re
import urllib.error
import urllib.request

REQUIRED = ["BASE_URL", "AUTH_MODE", "TOKEN_A", "TOKEN_B", "OBJECT_A", "OBJECT_B"]

# Replace this list with the object class and verbs under test.
# Each case: (id, principal, method, path_template, body_or_None, note)
CASES = [
    ("T1", "none", "GET", "/v1/objects", None, "no-auth control"),
    ("T2", "A", "GET", "/v1/objects", None, "owner positive control"),
    ("T3", "B", "GET", "/v1/objects/{OBJECT_A}", None, "cross-principal read"),
]


def redact(text, secrets):
    for secret in secrets:
        if secret and len(secret) >= 4:
            text = text.replace(secret, "[REDACTED]")
    text = re.sub(r'(?i)(authorization\s*:\s*)bearer\s+\S+', r'\1Bearer [REDACTED]', text)
    text = re.sub(r'(?i)(cookie\s*:\s*)[^\r\n]+', r'\1[REDACTED]', text)
    return text


def send(base, mode, token, method, path, body=None):
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    if token and mode != "none":
        headers["Authorization" if mode == "bearer" else "Cookie"] = (
            "Bearer " + token if mode == "bearer" else token
        )
    req = urllib.request.Request(base.rstrip("/") + path, data=data, headers=headers, method=method)
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            status, raw = resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as exc:
        status, raw = exc.code, exc.read().decode("utf-8", "ignore")
    except Exception as exc:
        status, raw = 0, f"{type(exc).__name__}: {exc}"
    return {"utc": started, "method": method, "path": path, "status": status, "body": raw}


def main():
    missing = [k for k in REQUIRED if not os.environ.get(k)]
    if missing:
        print("Missing env vars: " + ", " .join(missing))
        return 2
    mode = os.environ["AUTH_MODE"].lower()
    if mode not in ("bearer", "cookie", "none"):
        print("AUTH_MODE must be bearer, cookie or none")
        return 2
    base = os.environ["BASE_URL"]
    tokens = {"A": os.environ["TOKEN_A"], "B": os.environ["TOKEN_B"], "none": ""}
    objects = {"OBJECT_A": os.environ["OBJECT_A"], "OBJECT_B": os.environ["OBJECT_B"]}
    secrets = list(tokens.values()) + list(objects.values())

    rows = []
    for case_id, principal, method, template, body, note in CASES:
        path = template
        for key, value in objects.items():
            path = path.replace("{" + key + "}", value)
        row = send(base, mode, tokens[principal], method, path, body)
        row.update({"case": case_id, "principal": principal, "note": note})
        rows.append(row)
        print(f"{case_id}: HTTP {row['status']} ({note})")
        if case_id == "T2" and row["status"] != 200:
            print("Owner positive control failed. Stop and fix request shape.")
            break

    out = pathlib.Path("results")
    out.mkdir(exist_ok=True)
    clean = []
    for row in rows:
        item = dict(row)
        item["body"] = redact(row["body"], secrets)
        clean.append(item)
    (out / "matrix.json").write_text(json.dumps(clean, indent=2) + "\n", encoding="utf-8", newline="\n")
    lines = ["# Authorization matrix", "", "| Case | Principal | Verb | HTTP | Note |", "| --- | --- | --- | --- | --- |"]
    for row in clean:
        lines.append(f"| {row['case']} | {row['principal']} | {row['method']} | {row['status']} | {row['note']} |")
    (out / "matrix.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {out.resolve()}/matrix.json and matrix.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
