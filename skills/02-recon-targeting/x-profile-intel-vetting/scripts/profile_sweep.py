#!/usr/bin/env python3
"""Fetch X statuses through the fxtwitter mirror and verify returned ids.

Usage:
  python profile_sweep.py --out DIR ID [ID ...]
  python profile_sweep.py --out DIR --handles HANDLE [HANDLE ...]

Writes one <id>.json per status plus index.json. Never guesses credentials
and never touches x.com directly; it only reads the public mirror.
"""

import argparse
import json
import os
import re
import time
import urllib.parse
import urllib.request

MIRROR = "https://api.fxtwitter.com/status/{}"
PROFILE = "https://r.jina.ai/https://nitter.gq/{}"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"


def get(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def fetch_status(status_id, out_dir):
    path = os.path.join(out_dir, "{}.json".format(status_id))
    raw = get(MIRROR.format(status_id))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(raw)
    data = json.loads(raw)
    tweet = data.get("tweet") or {}
    returned = str(tweet.get("id") or "")
    text = tweet.get("text") or ""
    return {
        "requested": status_id,
        "returned": returned,
        "id_match": returned == status_id,
        "author": (tweet.get("author") or {}).get("screen_name"),
        "followers": (tweet.get("author") or {}).get("followers"),
        "text": text,
        "file": path,
    }


def fetch_profile(handle, out_dir):
    safe = re.sub(r"[^A-Za-z0-9_]", "_", handle)
    path = os.path.join(out_dir, "profile_{}.md".format(safe))
    raw = get(PROFILE.format(urllib.parse.quote(handle, safe="")))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(raw)
    reward_posts = len(re.findall(r"Just got a reward", raw, re.I))
    hunters = sorted(set(re.findall(r"yeswehack\.com/hunters/([A-Za-z0-9_-]+)", raw, re.I)))
    return {
        "handle": handle,
        "reward_posts_observed": reward_posts,
        "hunter_links": hunters,
        "status_ids": sorted(set(re.findall(r"/status/(\d+)", raw))),
        "file": path,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--handles", nargs="+", help="profile handles to sweep")
    ap.add_argument("--ids", nargs="+", help="status ids to fetch")
    ap.add_argument("--sleep", type=float, default=0.6)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    index = {"statuses": [], "profiles": []}
    for sid in args.ids or []:
        try:
            index["statuses"].append(fetch_status(sid, args.out))
        except Exception as exc:
            index["statuses"].append({"requested": sid, "error": str(exc)})
        time.sleep(args.sleep)
    for handle in args.handles or []:
        try:
            index["profiles"].append(fetch_profile(handle, args.out))
        except Exception as exc:
            index["profiles"].append({"handle": handle, "error": str(exc)})
        time.sleep(args.sleep)
    index_path = os.path.join(args.out, "index.json")
    with open(index_path, "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=2)
    assert len(index["statuses"]) + len(index["profiles"]) == len(args.ids or []) + len(args.handles or [])
    print(json.dumps(index, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
