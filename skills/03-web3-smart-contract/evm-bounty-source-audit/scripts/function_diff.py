#!/usr/bin/env python3
"""Compare two Solidity files function-by-function.

Comments and whitespace are normalized, function bodies are extracted by brace
matching, and each identically named function is reported as SAME or DIFF.
Use it for fork-vs-upstream audits: the DIFF rows are the fork's own edits,
which is where behavioural deviations live.
"""

import argparse
import re


def load(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        source = handle.read()
    source = re.sub(r"//.*", "", source)
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
    return source


def function_bodies(source):
    found = {}
    for match in re.finditer(r"function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", source):
        start = match.start()
        brace = source.find("{", start)
        if brace < 0:
            continue
        depth = 0
        in_string = False
        escaped = False
        index = brace
        while index < len(source):
            char = source[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
            else:
                if char == '"':
                    in_string = True
                elif char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        body = source[start:index + 1]
                        found.setdefault(match.group(1), re.sub(r"\s+", " ", body).strip())
                        break
            index += 1
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("upstream")
    parser.add_argument("fork")
    parser.add_argument("--output", help="optional path for the full comparison table")
    args = parser.parse_args()

    upstream = function_bodies(load(args.upstream))
    fork = function_bodies(load(args.fork))
    rows = []
    for name in sorted(set(upstream) | set(fork)):
        left = upstream.get(name, "<absent>")
        right = fork.get(name, "<absent>")
        verdict = "SAME" if left == right else "DIFF"
        rows.append(f"=== {name} ===\nUPSTREAM: {left}\nFORK    : {right}\n{verdict}\n")
        print(name, verdict)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write("\n".join(rows))
        print("wrote", args.output)


if __name__ == "__main__":
    main()
