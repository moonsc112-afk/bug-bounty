#!/usr/bin/env python3
"""Scope-gated baseline/variant differential probe for one in-scope origin.

Plan file is JSON: [{"name": "baseline", "path": "/api/admin"}, ...].
The first entry is the baseline. No request is sent unless --scope-confirm
IN_SCOPE is passed. A variant is flagged only when the baseline is a denial
(401/403/404) and the variant returns 200/206 with a different body hash.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import http.server
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

SCOPE = "IN_SCOPE"
DENIALS = (401, 403, 404)
ALLOWED = (200, 206)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch(url, timeout, ua):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "*/*"})
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=timeout) as r:
            status, hdrs, body = r.getcode(), dict(r.headers.items()), r.read(262144)
    except urllib.error.HTTPError as e:
        status = e.code
        hdrs = dict(e.headers.items()) if e.headers else {}
        body = e.read(262144)
    except Exception as e:
        return {"status": 0, "error": f"{type(e).__name__}: {e}"[:200],
                "hash": "", "len": 0, "preview": ""}
    return {
        "status": status,
        "content_type": hdrs.get("Content-Type", ""),
        "hash": hashlib.sha256(body).hexdigest(),
        "len": len(body),
        "preview": body[:200].decode("utf-8", "replace"),
    }


def run(base, plan, out, scope, delay=0.3, timeout=10.0, ua="scope-diff/1.0"):
    if scope != SCOPE:
        raise ValueError("scope not confirmed: pass --scope-confirm IN_SCOPE")
    p = urllib.parse.urlsplit(base)
    if p.scheme not in ("http", "https") or not p.netloc:
        raise ValueError("base must be an absolute http(s) origin")
    if not plan or "path" not in plan[0]:
        raise ValueError("plan must be a non-empty JSON list of {name, path}")
    os.makedirs(out, exist_ok=True)
    rows = []
    for item in plan:
        path = item["path"]
        if not path.startswith("/"):
            path = "/" + path
        url = urllib.parse.urlunsplit((p.scheme, p.netloc, path, "", ""))
        rows.append({"name": item["name"], "path": path,
                     **fetch(url, timeout, ua)})
        if delay:
            time.sleep(delay)
    base_row = rows[0]
    usable = base_row["status"] in DENIALS
    for r in rows[1:]:
        if not usable or 0 in (base_row["status"], r["status"]):
            r["verdict"] = "INCONCLUSIVE_BASELINE"
        elif (r["status"] in ALLOWED
              and r["status"] != base_row["status"]
              and r["hash"] != base_row["hash"]):
            r["verdict"] = "DELTA_CANDIDATE"
        else:
            r["verdict"] = "NO_DELTA"
    report = {
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "base": base, "baseline_status": base_row["status"],
        "baseline_usable": usable, "rows": rows,
        "note": "DELTA_CANDIDATE needs review; save full request/response pairs",
    }
    with open(os.path.join(out, "results.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    lines = ["# Scope-gated differential", "",
             f"Base: `{base}`, baseline: **{base_row['status']}** (usable: {usable})",
             "", "| Case | Path | Status | Body hash | Verdict |",
             "|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['name']} | `{r['path']}` | {r['status']} | "
                     f"{r.get('hash', '')[:12] or '-'} | {r.get('verdict', 'BASELINE')} |")
    with open(os.path.join(out, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return report


class _Mock(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def do_GET(self):
        path = self.path
        if any(t in path for t in (";anything", "%3B", "%3b")):
            body, status = b"SECRET-MARKER", 200
        else:
            body, status = b"FORBIDDEN", 403
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def self_test():
    srv = http.server.HTTPServer(("127.0.0.1", 0), _Mock)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"
    tmp = os.path.join(os.environ.get("TMPDIR", os.path.expanduser("~")),
                       "scope-diff-selftest")
    os.makedirs(tmp, exist_ok=True)
    plan = [
        {"name": "baseline", "path": "/api/admin"},
        {"name": "literal_semicolon", "path": "/api/admin;anything"},
        {"name": "encoded_semicolon", "path": "/api/admin%3Bbypass=true"},
        {"name": "negative_null", "path": "/api/admin%00/data"},
    ]
    try:
        r = run(base, plan, tmp, SCOPE, delay=0, timeout=5)
        v = {x["name"]: x.get("verdict") for x in r["rows"]}
        assert r["baseline_status"] == 403, v
        assert v["literal_semicolon"] == "DELTA_CANDIDATE", v
        assert v["encoded_semicolon"] == "DELTA_CANDIDATE", v
        assert v["negative_null"] == "NO_DELTA", v
        try:
            run(base, plan, tmp, "", delay=0, timeout=5)
        except ValueError:
            pass
        else:
            raise AssertionError("scope guard did not refuse")
        print("SELFTEST PASS", v)
    finally:
        srv.shutdown()
        srv.server_close()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-url", default="")
    ap.add_argument("--plan", default="",
                    help="JSON file: [{'name','path'}, ...]; first is baseline")
    ap.add_argument("--out", default="")
    ap.add_argument("--scope-confirm", default="", choices=["", SCOPE])
    ap.add_argument("--delay", type=float, default=0.3)
    ap.add_argument("--timeout", type=float, default=10.0)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        self_test()
        return 0
    if not (a.base_url and a.plan and a.out):
        ap.error("--base-url, --plan and --out are required unless --self-test")
    with open(a.plan, encoding="utf-8") as f:
        plan = json.load(f)
    try:
        r = run(a.base_url, plan, a.out, a.scope_confirm, a.delay, a.timeout)
    except ValueError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    hits = [x for x in r["rows"] if x.get("verdict") == "DELTA_CANDIDATE"]
    print(f"baseline={r['baseline_status']} delta_candidates={len(hits)} out={a.out}")
    for h in hits:
        print(f"  HIT {h['name']} {h['path']} -> {h['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
