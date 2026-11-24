#!/usr/bin/env python3
"""Multichain fleet enumeration for Merkl-style wrapper (burn-on-transfer) protocols.

Stages (resumable):
    python3 multichain_fleet_scan.py --netdir <dir> --probe    # reachability probe only
    python3 multichain_fleet_scan.py --netdir <dir>            # full scan

Inputs
    --netdir DIR    directory of per-chain deployment JSONs. Each file:
                    {"chainId": ..., "transactions": [{"to": <DC proxy>}, {"to": <Distributor proxy>}, ...]}
                    (Gnosis-Safe upgrade batches straight from the protocol repo's
                    deployments/ directory; chain name parsed from "<id> - <Name> ...").
    --chains FILE   alternative: JSON list [{"chainId","name","dc","dst"}, ...]
    --dc ADDR       fallback DC proxy address (deterministic deploys reuse one address
                    on every chain, so a single address probes the whole fleet)
    --out DIR       output directory (default ./fleet_out)

What it does per reachable chain
    1. eth_getCode(dc) != 0x  -> chain hosts the fleet.
    2. Enumerate rewardTokens(i) in batches of 20 until the first empty slot.
    3. holder() probe per token -> wrapper set.
    4. Detail probes (4 wrappers x ~15 calls per batch, missing ids retried singly):
       name/token/holder/totalSupply/decimals/pool/vault/claimFeeRate/unlockTimestamp/
       debtToken/distributor/isTokenWrapper/amountToTransfer + isAllowed(DC) + isAllowed(dst).
    5. DC-level feeRecipient() for the F-02-class collision checks.

Resumability: <out>/<chainId>.json written per chain; a file WITHOUT "skipped" is done
and skipped next run; files marked "skipped" are retried (dead RPC today may live later).

Pitfalls baked in (learned the hard way)
    * A JSON-RPC batch can return HTTP 200 with only SOME ids -- never trust a list
      response as complete; missing ids are retried individually (a missing id parsed
      as None is indistinguishable from a revert and silently fakes results).
    * Selector-only calls to getters that take ARGUMENTS (amountToTransfer(address))
      revert even when the function exists -- pad an argument.
    * isAllowed() must be decoded as an int; hex-string decoding silently breaks
      `!= 1` comparisons.
    * A dead RPC under thread-pool load is not a dead chain: sequential retry with
      alternate endpoints before declaring unreachable.
    * Send a browser User-Agent; some hosts 403 the default UA.

Variant classification AFTER the scan (no ABI needed)
    getters first: claimFeeRate -> ClaimFee, unlockTimestamp -> TGE, debtToken -> AaveDebt,
    vault -> Vault, pool -> Withdraw; else compare runtime code length vs compiled
    artifact deployedBytecode lengths (+/-2 bytes metadata tolerance; <400 bytes =
    proxied old-gen instance).

Requires `cast` on PATH (selector computation); everything else is stdlib.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

# RPC candidates per chain id; the probe takes the FIRST that answers.
# Verified working on this host (add alternates as hosts rate-limit or die).
RPCS = {
    "1": ["https://ethereum-rpc.publicnode.com", "https://eth.drpc.org"],
    "10": ["https://mainnet.optimism.io", "https://optimism-rpc.publicnode.com"],
    "30": ["https://public-node.rsk.co"],
    "50": ["https://erpc.xinfin.network", "https://rpc.xdcrpc.com"],
    "56": ["https://bsc-dataseed.binance.org", "https://bsc-rpc.publicnode.com"],
    "100": ["https://rpc.gnosischain.com", "https://gnosis-rpc.publicnode.com"],
    "122": ["https://rpc.fuse.io"],
    "130": ["https://mainnet.unichain.org"],
    "137": ["https://polygon-rpc.com", "https://polygon-bor-rpc.publicnode.com"],
    "143": ["https://rpc.monad.xyz"],
    "146": ["https://rpc.soniclabs.com"],
    "151": ["https://governors.mainnet.redbelly.network"],
    "169": ["https://pacific-rpc.manta.network/http"],
    "196": ["https://rpc.xlayer.tech", "https://xlayerrpc.okx.com"],
    "239": ["https://rpc.tac.build"],
    "252": ["https://rpc.frax.com"],
    "324": ["https://mainnet.era.zksync.io"],
    "480": ["https://worldchain-mainnet.g.alchemy.com/public"],
    "592": ["https://1rpc.io/astr", "https://astar-rpc.dwellir.com", "https://astar.api.onfinality.io/public"],
    "988": ["https://rpc.stable.xyz"],
    "999": ["https://rpc.hyperliquid.xyz/evm"],
    "1135": ["https://lisk.drpc.org", "https://rpc.lisk.com"],
    "1284": ["https://moonbeam.api.onfinality.io/public", "https://moonbeam.drpc.org"],
    "1329": ["https://evm-rpc.sei-apis.com"],
    "1868": ["https://rpc.soneium.org"],
    "1923": ["https://rpc.ankr.com/swell", "https://swell-mainnet.alt.technology"],
    "2020": ["https://api.roninchain.com/rpc"],
    "4114": ["https://rpc.mainnet.citrea.xyz", "https://rpc.citrea.xyz"],
    "4326": ["https://rpc.megaeth.com"],
    "5000": ["https://rpc.mantle.xyz"],
    "8453": ["https://base-rpc.publicnode.com", "https://mainnet.base.org"],
    "9745": ["https://rpc.plasma.to"],
    "16661": ["https://0g-rpc.publicnode.com", "https://evm-rpc.0g.ai"],
    "31612": ["https://evm-rpc.mezo.org", "https://rpc.mezo.network"],
    "33139": ["https://rpc.apechain.com/http"],
    "34443": ["https://mainnet.mode.network"],
    "42161": ["https://arb1.arbitrum.io/rpc", "https://arbitrum-one-rpc.publicnode.com"],
    "42220": ["https://forno.celo.org"],
    "42793": ["https://rpc.etherlink.com", "https://node.mainnet.etherlink.com"],
    "43111": ["https://rpc.hemi.network/rpc"],
    "43114": ["https://api.avax.network/ext/bc/C/rpc"],
    "48900": ["https://mainnet.zircuit.com"],
    "5064014": ["https://rpc.ethereal.fi", "https://rpc.ethereal.trade"],
    "534352": ["https://rpc.scroll.io"],
    "57073": ["https://rpc-gel.inkonchain.com"],
    "59144": ["https://rpc.linea.build"],
    "60808": ["https://rpc.gobob.xyz"],
    "6900": ["https://evm-rpc.nibiru.fi", "https://rpc.nibiru.fi"],
    "747": ["https://mainnet.evm.nodes.onflow.org"],
    "747474": ["https://rpc.katana.network"],
    "80094": ["https://rpc.berachain.com"],
    "81457": ["https://blast-rpc.publicnode.com", "https://rpc.ankr.com/blast"],
    "98866": ["https://rpc.plume.org"],
    "13371": ["https://rpc.immutable.com"],
    "167000": ["https://rpc.taiko.xyz"],
    "21000000": ["https://rpc.corn.xyz", "https://corn-rpc.publicnode.com"],
    "2046399126": ["https://mainnet.skalenodes.com/v1/elated-tan-skat"],
}

DETAIL_SIGS = ["name()", "token()", "holder()", "totalSupply()", "decimals()", "pool()",
               "vault()", "claimFeeRate()", "unlockTimestamp()", "debtToken()",
               "distributor()", "isTokenWrapper()", "amountToTransfer(address)"]


def sig(s):
    return subprocess.run(["cast", "sig", s], capture_output=True, text=True).stdout.strip()


SEL = {s: sig(s) for s in ["rewardTokens(uint256)", "feeRecipient()", "isAllowed(address)"] + DETAIL_SIGS}


def post(url, payload, timeout=25, retries=3):
    data = json.dumps(payload).encode()
    for a in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers={
                "Content-Type": "application/json", "User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except Exception:
            time.sleep(0.8 * (a + 1))
    return None


def call_batch(url, calls, retries=3):
    """Aligned results; a partial batch response is NOT trusted -- missing ids retried singly."""
    out = [None] * len(calls)
    payload = [{"jsonrpc": "2.0", "id": i, "method": "eth_call", "params": [c, "latest"]}
               for i, c in enumerate(calls)]
    res = post(url, payload, retries=retries)
    if isinstance(res, list):
        for item in res:
            if isinstance(item, dict) and isinstance(item.get("id"), int) and item["id"] < len(calls):
                if item.get("result") is not None:
                    out[item["id"]] = item["result"]
    for i, v in enumerate(out):
        if v is None:
            rr = post(url, {"jsonrpc": "2.0", "id": 0, "method": "eth_call",
                            "params": [calls[i], "latest"]}, retries=2)
            if isinstance(rr, dict) and rr.get("result") is not None:
                out[i] = rr["result"]
    return out


def dec_addr(h):
    return None if not h or h == "0x" else "0x" + h[-40:]


def dec_int(h):
    try:
        return int(h, 16)
    except Exception:
        return None


def dec_str(r):
    try:
        hx = r[2:]
        off = int(hx[0:64], 16) * 2
        ln = int(hx[off:off + 64], 16)
        return bytes.fromhex(hx[off + 64:off + 64 + ln * 2]).decode("utf-8", "replace")
    except Exception:
        return None


def chains_from_netdir(d):
    out = []
    for f in sorted(glob.glob(os.path.join(d, "*.json"))):
        try:
            j = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        cid = j.get("chainId")
        if cid is None:
            continue
        m = re.match(r"^\d+ - (.*?) Upgrade", os.path.basename(f))
        name = m.group(1) if m else os.path.basename(f)
        txs = j.get("transactions", [])
        dc = txs[0]["to"] if txs else None
        dst = txs[1]["to"] if len(txs) > 1 else None
        out.append({"chainId": str(cid), "name": name, "dc": dc, "dst": dst})
    return out


def probe_one(ch):
    for url in RPCS.get(ch["chainId"], []):
        res = post(url, [{"jsonrpc": "2.0", "id": 0, "method": "eth_blockNumber"},
                         {"jsonrpc": "2.0", "id": 1, "method": "eth_getCode",
                          "params": [ch["dc"], "latest"]}])
        if isinstance(res, list):
            by = {i["id"]: i.get("result") for i in res if isinstance(i, dict)}
            if by.get(0):
                return {**ch, "rpc": url, "block": int(by[0], 16),
                        "dc_code_len": (len(by.get(1) or "0x") - 2) // 2}
    return {**ch, "rpc": None, "block": None, "dc_code_len": 0}


def scan_chain(url, dc, dst):
    out = {"dc": dc, "dst": dst, "tokens": [], "wrappers": {}, "err": None}
    try:
        tokens = []
        i = 0
        while i < 400:
            calls = [{"to": dc, "data": SEL["rewardTokens(uint256)"] + hex(k)[2:].rjust(64, "0")}
                     for k in range(i, i + 20)]
            res = call_batch(url, calls)
            stop = False
            for k in range(i, min(i + 20, 400)):
                r = res[k - i]
                if not r or len(r) < 42:
                    stop = True
                    break
                tokens.append("0x" + r[-40:])
            if stop:
                break
            i += 20
        out["token_count"] = len(tokens)
        out["tokens"] = tokens

        res = call_batch(url, [{"to": dc, "data": SEL["feeRecipient()"]},
                               {"to": dc, "data": SEL["distributor()"]}
                               if "distributor()" in SEL else {"to": dc, "data": "0x"}])
        out["dc_feeRecipient"] = dec_addr(res[0]) if res and res[0] else None

        wrappers = []
        for i in range(0, len(tokens), 20):
            batch = tokens[i:i + 20]
            res = call_batch(url, [{"to": t, "data": SEL["holder()"]} for t in batch])
            for j, t in enumerate(batch):
                r = res[j] if j < len(res) else None
                if r and len(r) >= 42 and r != "0x":
                    wrappers.append(t)
        out["wrapper_count"] = len(wrappers)

        for i in range(0, len(wrappers), 4):
            batch = wrappers[i:i + 4]
            calls, keys = [], []
            for w in batch:
                for s in DETAIL_SIGS:
                    data = SEL[s]
                    if s == "amountToTransfer(address)":
                        data += "0" * 63 + "1"  # padded argument: selector-only reverts
                    calls.append({"to": w, "data": data})
                    keys.append((w, s))
                calls.append({"to": w, "data": SEL["isAllowed(address)"] + "0" * 24 + dc[2:]})
                keys.append((w, "isAllowed_DC"))
                if dst:
                    calls.append({"to": w, "data": SEL["isAllowed(address)"] + "0" * 24 + dst[2:]})
                    keys.append((w, "isAllowed_DST"))
            res = call_batch(url, calls)
            for j, (w, s) in enumerate(keys):
                r = res[j]
                info = out["wrappers"].setdefault(w, {})
                if r is None or r == "0x":
                    info[s] = None
                elif s == "name()":
                    info[s] = dec_str(r)
                elif s == "isTokenWrapper()":
                    info[s] = (dec_int(r) == 1)
                elif s in ("isAllowed_DC", "isAllowed_DST"):
                    info[s] = dec_int(r)
                elif s in ("totalSupply()", "decimals()", "claimFeeRate()", "unlockTimestamp()",
                           "amountToTransfer(address)"):
                    info[s] = dec_int(r)
                else:
                    info[s] = dec_addr(r)
            time.sleep(0.1)
        out["ok"] = True
    except Exception as e:
        out["err"] = f"{type(e).__name__}: {e}"
        out.setdefault("ok", False)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--netdir")
    ap.add_argument("--chains")
    ap.add_argument("--dc", default="0x8BB4C975Ff3c250e0ceEA271728547f3802B36Fd")
    ap.add_argument("--out", default="fleet_out")
    ap.add_argument("--probe", action="store_true")
    a = ap.parse_args()

    if a.netdir:
        chs = chains_from_netdir(a.netdir)
    elif a.chains:
        chs = json.load(open(a.chains, encoding="utf-8"))
        chs = [{"chainId": str(c["chainId"]), "name": c.get("name", c["chainId"]),
                "dc": c.get("dc", a.dc), "dst": c.get("dst")} for c in chs]
    else:
        print("need --netdir or --chains")
        return 2
    for c in chs:
        if not c.get("dc"):
            c["dc"] = a.dc
    os.makedirs(a.out, exist_ok=True)
    print(f"chains: {len(chs)}", flush=True)

    probe = {}
    with ThreadPoolExecutor(max_workers=12) as ex:
        futs = {ex.submit(probe_one, c): c for c in chs}
        for fu in as_completed(futs):
            r = fu.result()
            probe[r["chainId"]] = r
    json.dump(probe, open(os.path.join(a.out, "mc_probe.json"), "w"), indent=1)
    live = [r for r in probe.values() if r["rpc"]]
    print(f"LIVE: {len(live)}/{len(chs)}", flush=True)
    for r in sorted(probe.values(), key=lambda x: int(x["chainId"])):
        print(f"  {r['name'][:20]:20s} {r['chainId']:>10s} dc_code_len={r['dc_code_len']} "
              f"{'LIVE ' + str(r['rpc']) if r['rpc'] else 'DEAD'}", flush=True)
    if a.probe:
        return 0

    for c in chs:
        rj = os.path.join(a.out, f"{c['chainId']}.json")
        if os.path.exists(rj):
            prev = json.load(open(rj, encoding="utf-8"))
            if "skipped" not in prev:
                continue  # done; resumes across runs
        pr = probe.get(c["chainId"], {})
        url = pr.get("rpc")
        if not url:
            # sequential retry: transient thread-load failures look like dead chains
            for cand in RPCS.get(c["chainId"], []):
                rr = post(cand, [{"jsonrpc": "2.0", "id": 0, "method": "eth_blockNumber"}],
                          timeout=12, retries=1)
                if isinstance(rr, list) and rr and rr[0].get("result"):
                    url = cand
                    break
        if not url:
            json.dump({"skipped": "no_rpc", **c}, open(rj, "w"))
            continue
        if pr.get("dc_code_len") == 0:
            json.dump({"skipped": "no_dc_code", **c}, open(rj, "w"))
            continue
        res = scan_chain(url, c["dc"], c["dst"])
        res.update({"chainId": c["chainId"], "name": c["name"]})
        json.dump(res, open(rj, "w"), indent=1)
        print(f"{c['name']}: tokens={res.get('token_count')} wrappers={res.get('wrapper_count')} "
              f"{'OK' if res.get('ok') else 'ERR ' + str(res.get('err'))}", flush=True)
    print("DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
