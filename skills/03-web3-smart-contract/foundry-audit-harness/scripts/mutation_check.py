#!/usr/bin/env python3
"""Mutation-check Foundry harnesses against real source and restore the tree.

Usage:
    python mutation_check.py --repo <repo-root> --spec <spec.json> [--timeout 300]

The spec is a JSON array. Each entry names one harness and one exact source
mutation:

    [
      {
        "test": "test/poc/MyHarness.t.sol",
        "source": "src/pool/lib/ShareMath.sol",
        "old": "assets.mulDiv(..., rounding)",
        "new": "assets.mulDiv(..., Math.Rounding.Ceil)"
      }
    ]

For each entry the script requires exactly one occurrence of `old`, backs up
the source, applies `new`, runs `forge test --match-path <test>`, then restores
the byte-identical file, verifies its SHA-256, and touches it so Foundry
recompiles instead of serving a cached mutated artifact.

Exit status is 1 when a mutation fails to break its harness (no teeth) or when
a restore/occurrence check fails. A green exit means every mutation was caught.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess


def sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="Foundry project root")
    parser.add_argument("--spec", required=True, help="JSON mutation spec")
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()

    with open(args.spec, encoding="utf-8") as handle:
        spec = json.load(handle)

    broken = 0
    for index, item in enumerate(spec, 1):
        test = item["test"]
        source = os.path.join(args.repo, item["source"])
        backup = source + ".mutation-bak"
        original = open(source, encoding="utf-8").read()
        original_hash = sha256(source)
        occurrences = original.count(item["old"])

        if occurrences != 1:
            print(f"[{index}] SKIP {test}: expected 1 occurrence of source snippet, found {occurrences}")
            broken += 1
            continue

        shutil.copy2(source, backup)
        try:
            open(source, "w", encoding="utf-8", newline="").write(
                original.replace(item["old"], item["new"])
            )
            proc = subprocess.run(
                ["forge", "test", "--match-path", test],
                cwd=args.repo,
                capture_output=True,
                text=True,
                timeout=args.timeout,
            )
            output = proc.stdout + proc.stderr
            fails = [line.strip() for line in output.splitlines() if "[FAIL" in line]
            summary = next(
                (line.strip() for line in reversed(output.splitlines()) if "Suite result:" in line),
                "no suite summary",
            )
            if fails:
                print(f"[{index}] TEETH OK {test}: {summary}")
                for line in fails[:4]:
                    print("    " + line[:240])
            else:
                print(f"[{index}] NO TEETH {test}: mutation did not break the harness - {summary}")
                broken += 1
        finally:
            shutil.copy2(backup, source)
            os.remove(backup)
            restored_hash = sha256(source)
            if restored_hash != original_hash:
                print(f"[{index}] RESTORE FAILED {source}: hash mismatch")
                broken += 1
            os.utime(source, None)

    print(f"mutation check: {len(spec)} entries, {broken} problem(s)")
    return 1 if broken else 0


if __name__ == "__main__":
    raise SystemExit(main())
