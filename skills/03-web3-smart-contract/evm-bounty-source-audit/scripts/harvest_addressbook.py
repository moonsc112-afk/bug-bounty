#!/usr/bin/env python3
"""Harvest verified deployed sources from a public address book (Blockscout v2, no key).

Generalized from a proven run (452-entry book, ~10 min). Fetches each address's
main source + additional_sources bundle, recurses into proxy implementations,
and writes a manifest.json while harvesting. Retry-safe: failed addresses are
logged and skipped.

Usage:
  python3 harvest_addressbook.py --root E:/audit/<target> --addressbook <path-or-url>
  # optional: --only-chain 1 --explorer eth.blockscout.com --sleep 0.4
"""
import argparse
import json
import os
import re
import time
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}


def load_book(src):
    if src.startswith("http"):
        req = urllib.request.Request(src, headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    return json.load(open(src, encoding="utf-8"))


def book_entries(d):
    found = []

    def walk(o, keys=()):
        if isinstance(o, dict):
            addr = None
            for k, v in o.items():
                if isinstance(v, str) and re.fullmatch(r"0x[0-9a-fA-F]{40}", v):
                    if k.lower() in ("address", "addr", "contract", "contractaddress", "proxy", "implementation"):
                        addr = v
            if addr:
                name = None
                for k in ("name", "label", "contract_name", "contractName", "title", "id"):
                    if isinstance(o.get(k), str):
                        name = o[k]
                        break
                chain = None
                for k in ("chain", "chainId", "chain_id", "network"):
                    if str(k) in o:
                        chain = str(o[k])
                        break
                found.append({"name": name or (keys[-1] if keys else "unnamed"), "chain": chain, "address": addr})
            for k, v in o.items():
                walk(v, keys + (str(k),))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, keys + (f"[{i}]",))

    walk(d)
    seen, out = set(), []
    for e in found:
        key = e["address"].lower()
        if key not in seen:
            seen.add(key)
            out.append(e)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="workdir for src_all/ + manifest.json")
    ap.add_argument("--addressbook", required=True, help="local path or https URL")
    ap.add_argument("--explorer", default="eth.blockscout.com")
    ap.add_argument("--only-chain", default=None, help="keep only entries whose chain matches (e.g. 1)")
    ap.add_argument("--sleep", type=float, default=0.4)
    a = ap.parse_args()

    api = f"https://{a.explorer}/api/v2/smart-contracts/{{addr}}"
    out_dir = os.path.join(a.root, "src_all")
    os.makedirs(out_dir, exist_ok=True)

    entries = book_entries(load_book(a.addressbook))
    if a.only_chain is not None:
        entries = [e for e in entries if e["chain"] in (a.only_chain, None)]
    print(f"address book entries: {len(entries)}", flush=True)

    manifest = []
    meta = {e["address"].lower(): e for e in entries}
    todo = [e["address"] for e in entries]
    seen = set()

    def fetch(addr):
        req = urllib.request.Request(api.format(addr=addr), headers=UA)
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)

    def sdir(e, addr):
        safe = re.sub(r"[^A-Za-z0-9_.\-]", "_", f"{e.get('chain') or 'na'}_{e.get('name') or 'unnamed'}_{addr}")[:80]
        return os.path.join(out_dir, safe)

    def save(d, target):
        os.makedirs(target, exist_ok=True)
        main_src = d.get("source_code") or ""
        if main_src:
            nm = re.sub(r"[^A-Za-z0-9_.\-]", "_", (d.get("name") or "contract")) + ".sol"
            open(os.path.join(target, nm), "w", encoding="utf-8").write(main_src)
        n = 0
        for item in (d.get("additional_sources") or []):
            fp = re.sub(r"[^A-Za-z0-9_.\-/]", "_", (item.get("file_path") or f"extra_{n}.sol")).lstrip("/")
            full = os.path.join(target, fp)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            open(full, "w", encoding="utf-8").write(item.get("source_code") or "")
            n += 1
        return n

    while todo:
        addr = todo.pop(0)
        if addr.lower() in seen:
            continue
        seen.add(addr.lower())
        e = meta.get(addr.lower(), {"name": "impl", "chain": "na"})
        try:
            d = fetch(addr)
        except Exception as ex:
            manifest.append({"name": e["name"], "address": addr, "ok": False, "err": str(ex)[:60]})
            print(f"FAIL {addr} {e['name']}: {ex}", flush=True)
            time.sleep(1.0)
            continue
        n = save(d, sdir(e, addr))
        impls = [im.get("address_hash") for im in (d.get("implementations") or []) if im.get("address_hash")]
        manifest.append({"name": e["name"], "address": addr, "contract": d.get("name"),
                         "verified": d.get("is_verified"), "files": n, "impls": impls})
        for im in impls:
            if im.lower() not in seen:
                meta[im.lower()] = {"name": (e["name"] or "proxy") + "_impl", "chain": e["chain"]}
                todo.append(im)
        print(f"ok {addr} {str(e['name'])[:28]:28s} files={n} impls={len(impls)}", flush=True)
        time.sleep(a.sleep)

    json.dump(manifest, open(os.path.join(a.root, "manifest.json"), "w", encoding="utf-8"), indent=1)
    ok = sum(1 for m in manifest if m.get("ok", True))
    print(f"DONE {ok}/{len(manifest)} fetched", flush=True)


if __name__ == "__main__":
    main()
