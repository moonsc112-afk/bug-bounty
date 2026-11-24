#!/usr/bin/env python3
"""Validate an operator-supplied Solana RPC endpoint without ever printing its key.

Usage:
    python check_rpc_endpoint.py [--file rpc_url.txt] [--program <pubkey>] [--slice 64]
    python check_rpc_endpoint.py --url 'https://...'          # explicit endpoint

What it probes, cheapest first:
  1. getBlockHeight - a standard, 1-credit call. If this is refused, the KEY is the
     problem: wrong or rotated key, a project id pasted where a key belongs (some
     providers issue both as UUIDs), or a project that is not active yet.
  2. getProgramAccounts on --program with a small data slice - the shape heavy
     enumerations need. Refused while probe 1 passes means the plan or the method is
     restricted, not the key.

Accepted file contents: a full RPC URL, or a bare key on its own (the default
provider URL is then built around it). A URL on a commented-out line still counts;
placeholder text (`xxxx`, PASTE, YOUR_KEY) does not. Exit code is 0 only when every
probe that was asked for succeeded.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

UUID_RE = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
PLACEHOLDERS = ("xxxx", "paste", "your", "example", "here")
DEFAULT_KEYED_HOST = "https://mainnet.helius-rpc.com/?api-key="


def endpoint_from_file(path):
    """Return (url, note) from a file holding either a full URL or a bare key."""
    text = open(path, encoding="utf-8-sig").read()
    urls = [u for u in re.findall(r"https?://[^\s#'\"]+", text)
            if not any(p in u.lower() for p in PLACEHOLDERS)]
    if urls:
        return urls[0], "url from file"
    keys = [k for k in re.findall(UUID_RE, text)
            if not any(p in k.lower() for p in PLACEHOLDERS)]
    if keys:
        return DEFAULT_KEYED_HOST + keys[0], "bare key from file - provider URL built"
    return None, "no URL or key found (comments and placeholders only)"


def call(url, method, params, timeout=90):
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          "User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode()), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code} {e.reason} | server body: {e.read().decode(errors='replace')[:300]}"
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:200]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=None, help="file holding the URL or the bare key")
    ap.add_argument("--url", default=None, help="explicit endpoint URL")
    ap.add_argument("--program", default=None, help="pubkey for the getProgramAccounts probe")
    ap.add_argument("--slice", type=int, default=64, help="dataSlice length for that probe")
    args = ap.parse_args()

    if args.url:
        url, note = args.url, "explicit --url"
    else:
        path = args.file or os.path.join(os.getcwd(), "rpc_url.txt")
        if not os.path.exists(path):
            print(f"no endpoint file at {path}")
            return 2
        url, note = endpoint_from_file(path)
    if not url:
        print(f"cannot use {args.file or 'rpc_url.txt'}: {note}")
        return 2

    host = url.split("?")[0]
    key = url.split("api-key=")[1] if "api-key=" in url else ""
    print(f"endpoint : {host}   ({note})")
    if key:
        shaped = bool(re.fullmatch(UUID_RE, key))
        print(f"key      : {len(key)} chars, UUID shape = {shaped}")
    else:
        print("key      : none in the URL (path-token providers keep theirs in the path)")
    print()

    failures = 0
    data, err = call(url, "getBlockHeight", [])
    if err:
        failures += 1
        print(f"probe 1 getBlockHeight: FAILED {err}")
    else:
        print(f"probe 1 getBlockHeight: OK - block height {data.get('result')}")

    if args.program:
        data, err = call(url, "getProgramAccounts",
                         [args.program, {"encoding": "base64",
                                         "dataSlice": {"offset": 0, "length": args.slice}}])
        if err:
            failures += 1
            print(f"probe 2 getProgramAccounts({args.program[:8]}...): FAILED {err}")
        else:
            res = data.get("result")
            n = len(res) if isinstance(res, list) else "unexpected shape"
            print(f"probe 2 getProgramAccounts({args.program[:8]}...): OK - {n} accounts")
            if res == []:
                print("         empty array: fine for a small program, a red flag for a large one")
    print()
    print("verdict: " + ("endpoint works" if not failures else "endpoint refused a call - see above"))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
