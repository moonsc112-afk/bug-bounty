#!/usr/bin/env python3
"""Probe an external agent-readable file and its landing page.

Usage:
    python audit_agent_file.py <llms.txt URL> [landing page URL]

Stdlib + curl only. Prints: every extracted URL with HTTP status/effective URL,
hidden-instruction pattern hits, invisible/Bidi characters, HTML comments,
hidden CSS blocks, inline script sizes and network-call flags.
Read-only: never executes page content.
"""

import os
import re
import sys
import subprocess
import unicodedata
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0"
SUSPICIOUS = [
    "ignore previous", "ignore all", "disregard", "system prompt",
    "developer mode", "jailbreak", "exfiltrat", "curl ", "wget ",
    "eval(", "base64", "do not tell", "secret", "password",
    "api key", "token", "send to", "upload",
]
INVISIBLE = {0x200b, 0x200c, 0x200d, 0x2060, 0x202e, 0x202a, 0xfeff, 0x00ad}


def fetch(url):
    p = subprocess.run(
        ["curl", "-sSL", "--max-time", "25", "-A", UA, url],
        capture_output=True, text=True, errors="replace",
    )
    return p.stdout


def check(url):
    p = subprocess.run(
        ["curl", "-sSL", "-o", os.devnull, "-w",
         "%{http_code} %{url_effective} %{num_redirects}",
         "--max-time", "25", "-A", UA, url],
        capture_output=True, text=True, errors="replace",
    )
    return url, p.stdout.strip()


def scan_instructions(text, label):
    print(f"\n=== hidden-instruction scan: {label} ===")
    hits = 0
    for n, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        for pat in SUSPICIOUS:
            if pat in low:
                hits += 1
                print(f"L{n} [{pat}] {line.strip()[:180]}")
    weird = [
        (n, hex(ord(c)), unicodedata.name(c, "?"))
        for n, line in enumerate(text.splitlines(), 1)
        for c in line if ord(c) in INVISIBLE
    ]
    print("invisible/Bidi chars:", weird[:20] if weird else "none")
    print("pattern hits:", hits)


def scan_html(html):
    print("\n=== landing page scan ===")
    comments = [c.strip()[:200] for c in re.findall(r"<!--(.*?)-->", html, re.S) if c.strip()]
    print("HTML comments:", comments[:15] or "none")
    hidden = re.findall(
        r"<[^>]+(?:display\s*:\s*none|visibility\s*:\s*hidden)[^>]*>(.{0,300})",
        html, re.S | re.I,
    )
    print("hidden-style blocks:",
          [re.sub(r"<[^>]+>", "", h).strip()[:200] for h in hidden][:15] or "none")
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S | re.I)
    print("inline scripts:", len(scripts), "js bytes:", sum(len(s) for s in scripts))
    for pat in ["fetch(", "XMLHttpRequest", "navigator.sendBeacon", "WebSocket("]:
        flagged = [i for i, s in enumerate(scripts, 1) if pat in s]
        if flagged:
            print(f"  network call [{pat}] in scripts: {flagged}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    file_url = sys.argv[1]
    page_url = sys.argv[2] if len(sys.argv) > 2 else file_url.rsplit("/", 1)[0] + "/"

    text = fetch(file_url)
    print(f"fetched {len(text)} bytes from {file_url}")
    urls = sorted({u.rstrip(".,;") for u in re.findall(r"https?://[^\s)\]>\"']+", text)})
    print(f"\n=== link check ({len(urls)} unique URLs) ===")
    with ThreadPoolExecutor(max_workers=8) as pool:
        for url, status in pool.map(check, urls):
            code = status.split()[0] if status else "ERR"
            flag = "OK" if code.startswith(("2", "3")) else "DEAD"
            print(f"{flag:4} {status}" if code.startswith(("2", "3")) else f"{flag:4} {code:4} {url}")

    scan_instructions(text, "agent-readable file")
    scan_html(fetch(page_url))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
