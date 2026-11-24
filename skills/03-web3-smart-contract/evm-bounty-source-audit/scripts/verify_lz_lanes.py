#!/usr/bin/env python3
"""Verify LayerZero lane configuration across a fleet of tellers (BoringVault-style protocols).

Distilled from a session-verified probe: reads `peers(eid)` + `idToChains(eid)` per teller using
eids from the AUTHORITATIVE LayerZero metadata API (never guess eids), then verifies the peer side
on the remote chain (vault coherence + reciprocity + allow flags) and compares each teller's
`endpoint()` against the canonical EndpointV2 for its chain.

Usage:
  python verify_lz_lanes.py lanes.json [--out result.json]
  python verify_lz_lanes.py --suggest        # print a chains block built from the metadata API

lanes.json:
{
  "chains": {
    "Ethereum":  {"rpc": "https://ethereum-rpc.publicnode.com", "eid": 30101},
    "Berachain": {"rpc": "https://berachain-rpc.publicnode.com", "eid": 30362}
  },
  "tellers": [
    {"chain": "Ethereum", "address": "0x..", "vault": "0x..", "name": "optional"}
  ]
}

Include every chain you want lanes verified against in "chains" (a peer chain left out is skipped).
Fill eids from --suggest, not from docs tables: several differ from the older published lists
(Scroll=30214, BOB=30279, Plasma=30383, Tempo=30410 at last check — the metadata entries are
keyed inconsistently too, e.g. bera-mainnet / hyperliquid-mainnet).
Requires `cast` on PATH (Foundry); stdlib otherwise.
"""
import json, os, shutil, subprocess, sys, time, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
META = "https://metadata.layerzero-api.com/v1/metadata/deployments"
ALIASES = {"ethereum": "Ethereum", "bsc": "BNB", "bnb": "BNB", "arbitrum": "Arbitrum",
           "optimism": "Optimism", "base": "Base", "scroll": "Scroll", "ink": "Ink",
           "bera": "Berachain", "hyperliquid": "HyperEVM", "hyperevm": "HyperEVM", "bob": "BOB",
           "monad": "Monad", "plasma": "Plasma", "tempo": "Tempo"}


def cast_bin():
    c = shutil.which("cast")
    if c:
        return c
    for p in (os.path.expanduser("~/.foundry/bin/cast"), os.path.expanduser("~/.foundry/bin/cast.exe")):
        if os.path.exists(p):
            return p
    raise SystemExit("cast not found on PATH")


def sel(sig):
    return subprocess.run([cast_bin(), "sig", sig], capture_output=True, text=True).stdout.strip()


def pad64(x):
    """Exactly 64 hex chars. NEVER slice this result afterwards (stripping leading chars shifts
    the ABI argument left and every read silently returns zero)."""
    h = x if isinstance(x, str) else hex(x)
    return h.lower().replace("0x", "").rjust(64, "0")


def call(url, to, data, retries=3):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                       "params": [{"to": to, "data": data}, "latest"]}).encode()
    for a in range(retries):
        try:
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as r:
                res = json.loads(r.read().decode())
            return res.get("result") if isinstance(res, dict) else None
        except Exception:
            if a == retries - 1:
                return None
            time.sleep(1.2 * (a + 1))


def word(r, i):
    if not r or len(r) < 2 + (i + 1) * 64:
        return None
    return int(r[2 + i * 64: 2 + (i + 1) * 64], 16)


def addr(r):
    return ("0x" + r[-40:]).lower() if r and len(r) >= 42 else None


def metadata():
    req = urllib.request.Request(META, headers={"User-Agent": UA})
    J = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
    out = {}
    for key, val in J.items():
        if "-mainnet" not in key:
            continue
        for d in (val.get("deployments") or []):
            if str(d.get("stage")) == "mainnet" and int(d.get("version", 0) or 0) == 2:
                ep = (d.get("endpointV2") or {}).get("address")
                if ep:
                    out[key] = {"eid": int(d["eid"]), "endpoint": ep.lower()}
    return out


def suggest():
    md = metadata()
    for key in sorted(md):
        canon = next((v for k, v in ALIASES.items() if key.split("-")[0] == k), None)
        if not canon:
            continue
        print('  "%s": {"rpc": "https://<rpc for %s>", "eid": %d},   // %s endpoint %s'
              % (canon, canon, md[key]["eid"], key, md[key]["endpoint"]))


def main():
    if "--suggest" in sys.argv:
        return suggest()
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    chains = cfg["chains"]
    md = metadata()
    canon = {}
    for name, c in chains.items():
        hit = next((v for k, v in md.items() if v["eid"] == int(c["eid"])), None)
        canon[name] = (hit or {}).get("endpoint")

    S = {"peers": sel("peers(uint32)"), "idToChains": sel("idToChains(uint32)"),
         "endpoint": sel("endpoint()"), "vault": sel("vault()")}

    lanes, issues = [], []
    for t in cfg["tellers"]:
        chain, taddr = t["chain"], t["address"]
        url = chains[chain]["rpc"]
        local_eid = int(chains[chain]["eid"])
        ep = addr(call(url, taddr, S["endpoint"]))
        if canon.get(chain) and ep != canon[chain]:
            issues.append({"kind": "ENDPOINT", "chain": chain, "teller": taddr, "got": ep, "canonical": canon[chain]})
        for remote, c2 in chains.items():
            eid = int(c2["eid"])
            if eid == local_eid:
                continue
            peer = addr(call(url, taddr, S["peers"] + pad64(eid)))
            if not peer or peer == "0x" + "0" * 40:
                continue
            flags = call(url, taddr, S["idToChains"] + pad64(eid))
            lane = {"local": chain, "teller": taddr, "remote": remote, "eid": eid, "peer": peer,
                    "vault": t.get("vault"), "allowFrom": bool(word(flags, 0)), "allowTo": bool(word(flags, 1))}
            rurl = c2["rpc"]
            lane["peerVault"] = addr(call(rurl, peer, S["vault"]))
            lane["peerBackPeer"] = addr(call(rurl, peer, S["peers"] + pad64(local_eid)))
            rflags = call(rurl, peer, S["idToChains"] + pad64(local_eid))
            lane["peerAllowFrom"] = bool(word(rflags, 0))
            lane["peerAllowTo"] = bool(word(rflags, 1))
            if lane["vault"] and lane["peerVault"] and lane["peerVault"] != lane["vault"].lower():
                issues.append({"kind": "VAULT-MISMATCH", **lane})
            if lane["peerBackPeer"] and lane["peerBackPeer"] != taddr.lower():
                issues.append({"kind": "NOT-RECIPROCAL", **lane})
            if not lane["peerAllowFrom"]:
                issues.append({"kind": "REMOTE-NOT-ALLOWING-FROM-US", **lane})
            if not lane["peerAllowTo"]:
                issues.append({"kind": "REMOTE-NOT-ALLOWING-TO-US", **lane})
            lanes.append(lane)
            print("lane %s -> %s (eid %d) peer=%s vaultOK=%s back=%s from=%s to=%s"
                  % (chain, remote, eid, peer, lane["peerVault"] == (t.get("vault") or "").lower(),
                     lane["peerBackPeer"], lane["peerAllowFrom"], lane["peerAllowTo"]))

    print("\n%d configured lanes, %d issues" % (len(lanes), len(issues)))
    for i in issues:
        print("  ISSUE %s %s -> %s %s" % (i.get("kind"), i.get("local"), i.get("remote"), i.get("teller")))
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
        json.dump({"lanes": lanes, "issues": issues}, open(out, "w"), indent=1)
        print("written", out)


if __name__ == "__main__":
    main()
