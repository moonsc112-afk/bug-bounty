#!/usr/bin/env python3
"""Deterministic source-verification probe (safe as a Hermes cron `monitor` script).

Usage:
  python3 explorer_verification_probe.py \
      --explorer https://explorer.zkevm.cronos.org \
      --rpc https://mainnet.zkevm.cronos.org \
      --sourcify-chain 388 \
      0xADDR [0xADDR ...]

Per address it prints one STABLE line (no timestamps, no page-order dependence):
whether that exact address is verified on the explorer (address-prefixed file
keys found in __NEXT_DATA__; 0 == unverified), the implementation address the
explorer reports, the EIP-1967 slot (catches a proxy being repointed at a
verified impl) and the Sourcify match status. Identical output across runs can
gate a cron tick; changed output means the team published or upgraded something.

Why address-prefixed keys: the explorer keys each file as "<address>/path/File.sol",
so a nonzero count for an address means THAT address is verified. A verified
proxy says nothing about its implementation — always list both.
"""
import argparse
import json
import re
import urllib.request

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"
}
EIP1967 = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"


def get(url, timeout=45):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=timeout
    ).read().decode("utf-8", "ignore")


def rpc_get_storage(rpc, addr, slot):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_getStorageAt",
                       "params": [addr, slot, "latest"]}).encode()
    req = urllib.request.Request(rpc, data=body,
                                 headers={"Content-Type": "application/json", **UA})
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode()).get("result", "")


def sourcify_status(chain, addr):
    for kind in ("full_match", "partial_match"):
        try:
            req = urllib.request.Request(
                "https://repo.sourcify.dev/contracts/%s/%s/%s/metadata.json" % (kind, chain, addr),
                headers=UA)
            if urllib.request.urlopen(req, timeout=30).getcode() == 200:
                return kind
        except Exception:
            pass
    return "none"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--explorer", required=True,
                    help="explorer base URL, e.g. https://explorer.zkevm.cronos.org")
    ap.add_argument("--rpc", default="", help="RPC endpoint for the EIP-1967 slot read (optional)")
    ap.add_argument("--sourcify-chain", default="", help="Sourcify chain id (optional)")
    ap.add_argument("addresses", nargs="+")
    a = ap.parse_args()

    print("SOURCE-VERIFICATION STATUS")
    for addr in a.addresses:
        line = "addr=%s" % addr
        try:
            blob = get(a.explorer.rstrip("/") + "/address/" + addr)
            m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', blob, re.S)
            blob = m.group(1) if m else blob
            files = len(re.findall(r'"' + addr + r'/[^"]+\.sol"', blob))
            line += " explorer_verified=%s files=%d" % ("true" if files > 0 else "false", files)
            impl = re.search(r'"implementationContract"\s*:\s*"?(0x[a-fA-F0-9]{40})?"?', blob)
            if impl:
                line += " impl=%s" % impl.group(1)
        except Exception as e:
            line += " explorer=ERROR(%s)" % type(e).__name__
        if a.rpc:
            try:
                line += " slot1967=0x%s" % rpc_get_storage(a.rpc, addr, EIP1967)[-40:]
            except Exception as e:
                line += " slot1967=ERROR(%s)" % type(e).__name__
        if a.sourcify_chain:
            line += " sourcify=%s" % sourcify_status(a.sourcify_chain, addr)
        print(line)


if __name__ == "__main__":
    main()
