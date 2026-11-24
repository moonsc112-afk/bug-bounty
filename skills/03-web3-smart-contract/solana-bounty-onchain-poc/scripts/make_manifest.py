#!/usr/bin/env python3
"""Write, refresh or verify a sha256 manifest for a set of artifacts.

Why this exists: a submission bundle ships a manifest so a reviewer can verify every quoted artifact,
and the manifest has to be refreshed whenever a report file changes. This does both jobs without
needing sha256sum (absent on some hosts) and without reordering or dropping comment lines.

Usage:
    python make_manifest.py MANIFEST.sha256 PATH [PATH ...]   # add/refresh entries, keep order
    python make_manifest.py MANIFEST.sha256 --refresh         # rehash what is already listed
    python make_manifest.py MANIFEST.sha256 --check           # verify every entry, print a summary

Behaviour details that matter in practice:
  * entries are keyed by path; existing order and '#' comment lines are preserved
  * new paths are appended, missing files are reported but never silently dropped
  * written with LF endings, so the manifest stays portable between Windows and Linux checkouts
  * --check exits non-zero when anything is missing or mismatched
"""
import hashlib
import os
import sys

HEADER = [
    "# sha256 manifest",
    "# verify with: sha256sum -c MANIFEST.sha256  (or: python make_manifest.py MANIFEST.sha256 --check)",
    "# paths are relative to the manifest's directory unless they contain a separator already",
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    """Return (comment_lines, [(hash, filepath), ...]) preserving order."""
    comments, entries = [], []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8").read().splitlines():
            if line.startswith("#") or not line.strip():
                comments.append(line)
                continue
            if "  " in line:
                digest, f = line.split("  ", 1)
                entries.append((digest.strip(), f.strip()))
    return comments, entries


def write(path, comments, entries):
    body = comments if any(c.startswith("#") for c in comments) else list(HEADER)
    lines = [l for l in body if l is not None] + [""] + [f"{h}  {f}" for h, f in entries]
    open(path, "w", newline="\n").write("\n".join(lines) + "\n")


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    manifest = argv[1]
    args = argv[2:]
    comments, entries = load(manifest)
    order = [f for _, f in entries]
    known = dict(entries)

    if "--check" in args:
        ok = missing = bad = 0
        for digest, f in entries:
            if not os.path.exists(f):
                print(f"MISSING  {f}")
                missing += 1
            elif sha256(f) == digest:
                ok += 1
            else:
                print(f"CHANGED  {f}")
                bad += 1
        print(f"{ok}/{len(entries)} OK | {bad} changed | {missing} missing")
        return 0 if bad == 0 and missing == 0 else 1

    targets = [f for f in args if not f.startswith("--")]
    if "--refresh" in args or not targets:
        targets = order
    for f in order:
        if f not in targets:
            targets.append(f)

    for f in targets:
        if not os.path.exists(f):
            print(f"skip (not found): {f}")
            continue
        digest = sha256(f)
        if f in known and known[f] == digest:
            continue
        print(("refreshed" if f in known else "added") + f": {f}")
        if f not in known:
            order.append(f)
        known[f] = digest

    write(manifest, comments, [(known[f], f) for f in order if f in known])
    print(f"{manifest}: {sum(1 for f in order if f in known)} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
