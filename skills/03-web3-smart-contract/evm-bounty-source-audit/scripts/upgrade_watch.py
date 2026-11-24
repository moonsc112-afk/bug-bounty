#!/usr/bin/env python3
"""Deployment upgrade watch (generic template).

Checks (a) EIP-1967 impl slots of watched proxies and (b) the sha256 of a
public address-book JSON. Output is deterministic (no timestamps) so it can
gate a cron via monitor mode: unchanged output = the agent never runs.

Config: TARGETS + ADDRBOOK below. Run: python3 upgrade_watch.py
"""
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(HERE, "upgrade_watch_snapshot.json")
CAST = os.path.expanduser("~/.foundry/bin/cast.exe")
RPCS = ["https://ethereum-rpc.publicnode.com", "https://eth.llamarpc.com"]
EIP1967_IMPL = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"

# --- config: proxies of the watched deployment (impl addresses do NOT belong here) ---
TARGETS = {
    # example (a perp-DEX deployment) - replace with the target's proxies:
    # "PositionsManager": "0x...",
    # "RfqEngine": "0x...",
}
ADDRBOOK = ""  # e.g. "https://<site>/address-book/<name>.json"; "" = skip
# ----------------------------------------------------------------------------------


def _cast(args):
    return subprocess.run([CAST] + args, capture_output=True, text=True, timeout=60)


def rpc_call(args):
    last = ""
    for r in RPCS:
        p = _cast(args + ["--rpc-url", r])
        if p.returncode == 0 and p.stdout.strip():
            return p.stdout.strip()
        last = (p.stderr or "").strip()[:120]
    return f"ERR:{last}"


def load(path, default):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return default


def addrbook_sha(url):
    if not url:
        return None
    p = subprocess.run(
        ["curl", "-s", "--max-time", "60", url], capture_output=True, text=True, timeout=90
    )
    body = (p.stdout or "").strip()
    if not body or body[0] not in "[{":
        return None
    return hashlib.sha256(body.encode()).hexdigest()


def main():
    snap = load(SNAP, {"impls": {}, "addrbook_sha256": None})
    changes = []

    impls = {}
    for name, addr in TARGETS.items():
        v = rpc_call(["storage", addr, EIP1967_IMPL])
        impl = "0x" + v[-40:] if v.startswith("0x") and len(v) >= 42 else v
        impls[name] = impl
        old = snap.get("impls", {}).get(name)
        if old is not None and old != impl:
            changes.append(f"IMPL CHANGED {name}: {old} -> {impl}")

    sha = addrbook_sha(ADDRBOOK)
    old_sha = snap.get("addrbook_sha256")
    if ADDRBOOK and sha is None:
        changes.append("ADDRBOOK: fetch failed (check manually)")
    elif sha and old_sha and sha != old_sha:
        changes.append(f"ADDRBOOK CHANGED: {old_sha[:12]} -> {sha[:12]}")

    snap["impls"] = impls
    if sha:
        snap["addrbook_sha256"] = sha
    with open(SNAP, "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=2)

    if changes:
        print("WATCH: CHANGE DETECTED")
        for c in changes:
            print(" -", c)
        print("Next: fetch the changed contract's source (explorer API), diff vs ledger, read money paths first.")
        sys.exit(0)
    print("WATCH: NO CHANGE")
    for n, i in impls.items():
        print(f"   {n}: {i}")


if __name__ == "__main__":
    main()
