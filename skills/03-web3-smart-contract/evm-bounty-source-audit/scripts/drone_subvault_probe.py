#!/usr/bin/env python3
"""Drone / subvault probe for BoringVault-style fleets (Veda "Subaccount_N" pattern).

What it does:
  1) drone: extracts the controller (immutable boringVault) and gas floor from runtime
     bytecode, confirms the withdrawNativeFromDrone selector, lists token holdings.
  2) subvault cluster: reads authority of the subvault and every supplied member, probes
     isCapabilityPublic / canCall(0xbad) for the dangerous selectors, prints violations only.
  3) role graph: enumerates Blockscout-decoded role events on the authority, resolves
     selectors via 4byte.directory, classifies holders (EOA / EIP-7702 delegation /
     Safe N-of-M) so privileged-only trusts are separated from reachable bugs.

Usage:
  python3 drone_subvault_probe.py --rpc https://ethereum-rpc.publicnode.com \
      --drone 0x0877... --subvault 0xE23F... \
      --members hook=0x599d...,manager=0x5242...,solver=0x2689...,queue=0xB015...,accountant=0x9FEA...,pauser=0x3Dc2...
Optional: --blockscout https://eth.blockscout.com  (Ethereum default)
"""
import argparse
import json
import re
import subprocess
import time
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36"
BAD = "0x0000000000000000000000000000000000000bad"

DANGEROUS = [
    "enter(address,address,uint256,address,uint256)",
    "exit(address,address,uint256,address,uint256)",
    "manage(address,bytes,uint256)",
    "manage(address[],bytes[],uint256[])",
    "deposit(address,uint256,uint256,address)",
    "bulkDeposit(address,uint256,uint256,address)",
    "bulkWithdraw(address,uint256,uint256,address)",
    "refundDeposit(uint256,address,address,uint256,uint256,uint256,uint256)",
    "updateAssetData(address,bool,bool,uint16)",
    "solveOnChainWithdraws((uint96,address,address,uint128,uint128,uint40,uint24,uint24)[],bytes,address)",
    "updateExchangeRate(uint96)",
    "pauseAll()",
    "unpauseAll()",
    "setManageRoot(address,bytes32)",
    "setAuthority(address)",
    "setShareLockPeriod(uint64)",
]

_SIG_CACHE = {}


def sig(s):
    if s not in _SIG_CACHE:
        _SIG_CACHE[s] = subprocess.run(["cast", "sig", s], capture_output=True, text=True).stdout.strip()
    return _SIG_CACHE[s]


def pad(a):
    return a.lower().replace("0x", "").rjust(64, "0")


class Chain:
    def __init__(self, rpc):
        self.rpc = rpc

    def call(self, method, params, tries=3):
        for i in range(tries):
            try:
                req = urllib.request.Request(self.rpc,
                                             data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
                                             headers={"Content-Type": "application/json", "User-Agent": UA})
                with urllib.request.urlopen(req, timeout=35) as r:
                    j = json.loads(r.read().decode())
                    if "result" in j:
                        return j["result"]
            except Exception:
                time.sleep(0.8)
        return None

    def eth_call(self, to, data):
        return self.call("eth_call", [{"to": to, "data": data}, "latest"])

    def code(self, a):
        return self.call("eth_getCode", [a, "latest"]) or "0x"

    def code_size(self, a):
        # (len - 2) // 2, NOT len // 2: "0x" would otherwise read as a 1-byte contract
        # and an EOA/dead address would look like deployed code.
        c = self.code(a)
        return (len(c) - 2) // 2 if c.startswith("0x") else 0


def addr(r):
    return ("0x" + r[-40:]) if r and len(r) >= 42 else None


def uint(r):
    try:
        return int(r, 16) if r and r != "0x" else None
    except Exception:
        return None


def bs(base, path):
    req = urllib.request.Request(f"{base}/api/v2/{path}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode())


def classify_holder(chain, h):
    """EOA / EIP-7702 delegated EOA / Safe N-of-M / plain contract."""
    c = chain.code(h)
    size = (len(c) - 2) // 2 if c.startswith("0x") else 0
    if size == 0:
        return "EOA (privileged-role trust, out of scope)"
    if c.startswith("0xef0100") and len(c) >= 48:
        return f"EIP-7702 delegated EOA -> {('0x' + c[-40:])}"
    th = uint(chain.eth_call(h, sig("getThreshold()")))
    if th is not None:
        owners = chain.eth_call(h, sig("getOwners()"))
        n_owners = None
        if owners and owners != "0x":
            b = owners[2:]
            try:
                n_owners = int(b[64:128], 16)
            except Exception:
                n_owners = None
        return f"Safe {th}-of-{n_owners if n_owners else '?'} (code {size}B)"
    return f"contract ({size}B)"


def probe_drone(chain, drone, bsbase):
    print(f"\n### DRONE {drone}")
    code = chain.code(drone)
    body = code[2:]
    imm = []
    for m in re.finditer("7f", body):
        seg = body[m.start() + 2: m.start() + 66]
        if len(seg) == 64 and seg[:24] == "0" * 24 and seg[24:] != "0" * 40:
            imm.append("0x" + seg[24:])
        elif len(seg) == 64 and seg[:48] == "0" * 48 and seg[48:] != "0" * 16:
            imm.append(int(seg, 16))
    print(f"  codesize: {len(body) // 2} | immutables (controller vault, gas floor): {imm}")
    sel = sig("withdrawNativeFromDrone()")
    print("  withdrawNativeFromDrone selector present:", sel.replace("0x", "") in body)
    if bsbase:
        try:
            tb = bs(bsbase, f"addresses/{drone}/token-balances")
            print(f"  holdings ({len(tb)}) — custody if only the vault can call the fallback:")
            for it in tb:
                t = it.get("token") or {}
                dec = int(t.get("decimals") or 18)
                raw = int(it.get("value") or 0)
                print(f"    {str(t.get('symbol'))[:12]:12s} {raw / 10 ** dec:.6f} ({t.get('type')})")
        except Exception as e:
            print("  token-balances failed:", str(e)[:90])


def probe_caps(chain, label, target, authority):
    print(f"\n### {label} {target} authority={authority}")
    violations = 0
    for s in DANGEROUS:
        sel = sig(s)
        if sel == "0x00000000":
            continue
        p = chain.eth_call(authority, sig("isCapabilityPublic(address,bytes4)") + pad(target) + pad(sel))
        b = chain.eth_call(authority, sig("canCall(address,address,bytes4)") + pad(BAD) + pad(target) + pad(sel))
        if uint(p) or uint(b):
            violations += 1
            print(f"  !! {s} public={bool(uint(p))} attacker={bool(uint(b))}")
    if violations == 0:
        print("  clean: no public capability, attacker cannot call any probed selector")
    return violations


def f4(selector):
    """Resolve a 4-byte selector via 4byte.directory (cached)."""
    s = selector.lower()
    if s in _SIG_CACHE:
        return _SIG_CACHE[s]
    name = "?"
    try:
        j = bs_plain(f"https://www.4byte.directory/api/v1/signatures/?hex_signature={s}")
        res = j.get("results") or []
        name = res[0]["text_signature"] if res else "?"
    except Exception:
        name = "? (lookup failed)"
    time.sleep(0.25)
    _SIG_CACHE[s] = name
    return name


def bs_plain(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=35) as r:
        return json.loads(r.read().decode())


def role_graph(chain, bsbase, authority):
    print(f"\n### ROLE GRAPH authority={authority}")
    rows, params = [], None
    while True:
        url = f"addresses/{authority}/logs"
        q = ""
        if params:
            q = "?" + "&".join(f"{k}={v}" for k, v in params.items())
        j = bs(bsbase, url + q)
        for it in j.get("items") or []:
            d = it.get("decoded") or {}
            p = {}
            for par in d.get("parameters") or []:
                v = par.get("value")
                if isinstance(v, dict):
                    v = v.get("value")
                p[par.get("name")] = v
            rows.append((it.get("block_number"), d.get("method_call", ""), p))
        params = j.get("next_page_params")
        if not params:
            break
        time.sleep(0.35)

    users, caps = {}, []
    for blk, mc, p in rows:
        if "UserRoleUpdated" in mc and (p.get("enabled") is True or p.get("enabled") == "true"):
            users.setdefault(p.get("user"), []).append(int(p.get("role") or 0))
        elif "RoleCapabilityUpdated" in mc or "PublicCapabilityUpdated" in mc:
            caps.append((blk, mc, p))

    print(f"  events: {len(rows)} | holders: {len(users)}")
    for u, roles in sorted(users.items()):
        print(f"    {u} roles={sorted(roles)} | {classify_holder(chain, u)}")

    pubs = [c for c in caps if "PublicCapabilityUpdated" in c[1]
            and (c[2].get("enabled") is True or c[2].get("enabled") == "true")]
    print(f"  PUBLIC capabilities: {len(pubs)}")
    for blk, mc, p in pubs[:20]:
        sel = str(p.get("functionSig") or "")
        print(f"    {p.get('target')} {sel} {f4(sel) if sel else ''} (block {blk})")

    byrole = {}
    for blk, mc, p in caps:
        if "RoleCapabilityUpdated" in mc and (p.get("enabled") is True or p.get("enabled") == "true"):
            byrole.setdefault(int(p.get("role") or 0), []).append((p.get("target"), p.get("functionSig")))
    if byrole:
        print("  role -> caps (first 3 shown per role):")
        for role in sorted(byrole):
            holders = [u for u, rs in users.items() if role in rs]
            print(f"    role {role} holders={holders}")
            for tgt, sel in byrole[role][:3]:
                s = str(sel or "")
                print(f"       {tgt} {s} {f4(s) if s else ''}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rpc", required=True)
    ap.add_argument("--blockscout", default="https://eth.blockscout.com")
    ap.add_argument("--drone")
    ap.add_argument("--subvault")
    ap.add_argument("--authority")
    ap.add_argument("--members", default="", help="label=address,label=address")
    ap.add_argument("--skip-graph", action="store_true")
    a = ap.parse_args()

    chain = Chain(a.rpc)
    members = []
    for pair in a.members.split(","):
        if "=" in pair:
            k, v = pair.split("=", 1)
            members.append((k.strip(), v.strip()))

    if a.drone:
        probe_drone(chain, a.drone, a.blockscout)
    auth = a.authority
    if a.subvault and not auth:
        auth = addr(chain.eth_call(a.subvault, sig("authority()")))
    if a.subvault and auth:
        probe_caps(chain, "subvault", a.subvault, auth)
    for k, v in members:
        au = addr(chain.eth_call(v, sig("authority()"))) or auth
        probe_caps(chain, k, v, au)
    if auth and not a.skip_graph:
        role_graph(chain, a.blockscout, auth)


if __name__ == "__main__":
    main()
