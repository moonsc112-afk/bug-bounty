#!/usr/bin/env python3
"""Extract candidate smart-contract scope from a bounty program page.

Produces a DRAFT program markdown file for chain-scope-guard. Nothing written
here is authoritative: the draft has Status=Draft, which the guard refuses to
authorize until a human verifies entries against the live program page.
Standard library only.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chain_scope_guard import (  # noqa: E402
    EVM_CHAIN_ALIASES, SOLANA_CLUSTER_ALIASES, b58decode, parse_scope_rule,
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"
)
EVM_RE = re.compile(r"0x[a-fA-F0-9]{40}")
B58_RE = re.compile(r"(?<![A-Za-z0-9])([1-9A-HJ-NP-Za-km-z]{32,44})(?![A-Za-z0-9])")
OUT_HEADING_RE = re.compile(
    r"(?im)^\s*(?:#{1,6}\s*)?(?:out of scope|out-of-scope|not in scope|"
    r"not eligible|exclusions|known issues)\b[^\n]*$"
)
NEXT_HEADING_RE = re.compile(r"(?m)^\s*#{1,4}\s+\S")
GITHUB_RE = re.compile(r"github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
SHA_RE = re.compile(r"(?<![\w])[a-fA-F0-9]{40}(?![\w])")
URL_RE = re.compile(r"https?://[^\s<>\"')]+")
CHAIN_AGNOSTIC_RE = re.compile(
    r"not limited to (?:any|a specific|one) chain|any chain|all chains|"
    r"deployed to many|supported mainnet chains", re.I
)
SOLANA_CONTEXT_RE = re.compile(r"solana|program id|mint address|token mint", re.I)
DEVNET_RE = re.compile(r"devnet|testnet|localnet", re.I)

# Order matters: specific chains before generic "mainnet"/"ethereum".
CHAIN_PATTERNS = [
    (re.compile(r"\barbitrum\b|\barb(?:itrum)?\b", re.I), "42161"),
    (re.compile(r"\bavalanche\b|\bavax\b", re.I), "43114"),
    (re.compile(r"\boptimism\b|\bop\b", re.I), "10"),
    (re.compile(r"\bpolygon\b|\bmatic\b", re.I), "137"),
    (re.compile(r"\bbase\b", re.I), "8453"),
    (re.compile(r"\bbinance\b|\bbnb chain\b|\bbsc\b", re.I), "56"),
    (re.compile(r"\bsonic\b", re.I), "146"),
    (re.compile(r"\bberachain\b", re.I), "80094"),
    (re.compile(r"\blinea\b", re.I), "59144"),
    (re.compile(r"\bscroll\b", re.I), "534352"),
    (re.compile(r"\bethereum\b|\beth\b", re.I), "1"),
]


class _TextExtractor(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg"}
    BLOCK = {"p", "div", "li", "br", "h1", "h2", "h3", "h4", "tr", "td", "section"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skipping = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skipping += 1
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skipping:
            self.skipping -= 1
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skipping:
            self.parts.append(data)


def html_to_text(raw: str) -> str:
    parser = _TextExtractor()
    parser.feed(raw)
    text = "".join(parser.parts)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fetch_page(url: str, timeout: int = 30) -> tuple[str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8", "replace")
    method = "direct"
    if len(raw.strip()) < 400 or "Just a moment" in raw or "Enable JavaScript" in raw:
        jina_url = "https://r.jina.ai/" + url
        jina_request = urllib.request.Request(jina_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(jina_request, timeout=60) as response:
            raw = response.read().decode("utf-8", "replace")
        method = "jina"
    if re.search(r"<!doctype html|<html[\s>]", raw[:2000], re.I):
        return html_to_text(raw), method
    return raw.strip(), method


def out_of_scope_text(text: str) -> str:
    matches = list(OUT_HEADING_RE.finditer(text))
    if not matches:
        return ""
    start = matches[0].start()
    following = NEXT_HEADING_RE.search(text, matches[0].end())
    end = following.start() if following else min(len(text), start + 20000)
    return text[start:end]


def nearest_chain(context: str, center: int) -> str | None:
    best: tuple[int, str] | None = None
    for pattern, chain in CHAIN_PATTERNS:
        for match in pattern.finditer(context):
            distance = abs(match.start() - center)
            if best is None or distance < best[0]:
                best = (distance, chain)
    return best[1] if best else None


def chain_for_position(text: str, position: int, agnostic: bool) -> str | None:
    """Read the chain from the address's own line, then its preceding heading.

    A wide character window leaks chain names from neighbouring addresses and
    mislabels unlabelled deployments, so the line is the unit of context.
    """
    if agnostic:
        return "*"
    line_start = text.rfind("\n", 0, position) + 1
    line_end = text.find("\n", position)
    if line_end < 0:
        line_end = len(text)
    line = text[line_start:line_end]
    chain = nearest_chain(line, position - line_start)
    if chain:
        return chain
    previous_start = text.rfind("\n", 0, line_start - 1) + 1
    previous = text[previous_start:line_start - 1].strip()
    return nearest_chain(previous, len(previous) // 2) if previous else None


def guess_platform(url: str) -> str:
    host = re.sub(r"^https?://", "", url).split("/")[0].lower()
    for needle, platform in (
        ("immunefi", "Immunefi"), ("hackenproof", "HackerOne/HackenProof"),
        ("cantina", "Cantina"), ("sherlock", "Sherlock"),
        ("codehawks", "CodeHawks"), ("code4rena", "Code4rena"),
    ):
        if needle in host:
            return platform
    return "Unknown"


def slug_from_url(url: str) -> str:
    parts = [p for p in re.sub(r"^https?://", "", url).split("/") if p]
    slug = parts[-2] if len(parts) >= 2 and parts[-1] in {
        "scope", "resources", "information", "scope/", ""
    } else (parts[-1] if parts else "program")
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", slug).strip("-").lower()
    return slug or "program"


def _canonical_evm(address: str, chain: str) -> str:
    return parse_scope_rule(f"evm:{chain}:{address}").canonical.lower()


def _canonical_solana(pubkey: str, cluster: str) -> str:
    return parse_scope_rule(f"solana:{cluster}:{pubkey}").canonical


def extract(text: str, source: str, method: str, name: str, platform: str,
            fetched_at: str) -> dict[str, object]:
    out_slice = out_of_scope_text(text)
    agnostic = bool(CHAIN_AGNOSTIC_RE.search(text))
    in_entries: list[str] = []
    out_entries: list[str] = []
    needs_chain: list[str] = []
    solana_seen: set[str] = set()

    for match in EVM_RE.finditer(text):
        address = match.group(0)
        canonical_addr = address.lower()
        chain = chain_for_position(text, match.start(), agnostic)
        destination = out_entries if canonical_addr in out_slice.lower() else in_entries
        if chain is None:
            if canonical_addr not in needs_chain:
                needs_chain.append(canonical_addr)
            continue
        entry = _canonical_evm(address, chain)
        if entry not in destination:
            destination.append(entry)

    for match in B58_RE.finditer(text):
        pubkey = match.group(1)
        if pubkey in solana_seen:
            continue
        try:
            if len(b58decode(pubkey)) != 32:
                continue
        except ValueError:
            continue
        context = text[max(0, match.start() - 220): match.end() + 220]
        if not SOLANA_CONTEXT_RE.search(context):
            continue
        cluster = "devnet" if DEVNET_RE.search(context) else "mainnet-beta"
        entry = _canonical_solana(pubkey, cluster)
        solana_seen.add(pubkey)
        destination = out_entries if pubkey.lower() in out_slice.lower() else in_entries
        if entry not in destination:
            destination.append(entry)

    notes: list[str] = []
    if agnostic:
        notes.append("Scope text says the address list is not chain-limited: entries use evm:*:<address>. Confirm the exact chain list on the program page.")
    for address in needs_chain:
        notes.append(f"Needs manual chain assignment: {address}")
    for repo in sorted(set(GITHUB_RE.findall(text))):
        notes.append(f"Repo: https://{repo}")
    for commit in sorted(set(SHA_RE.findall(text))):
        notes.append(f"Pinned commit candidate: {commit}")
    for link in sorted(set(URL_RE.findall(text))):
        if re.search(r"docs|address|deploy|known-issue|audit", link, re.I):
            notes.append(f"Follow-up link: {link}")
    for entry in in_entries[:12]:
        position = text.lower().find(entry.split(":")[-1])
        if position >= 0:
            snippet = re.sub(r"\s+", " ", text[max(0, position - 120): position + 160]).strip()
            notes.append(f"Context for {entry}: {snippet[:260]}")

    return {
        "source": source, "method": method, "fetched_at": fetched_at,
        "platform": platform, "name": name,
        "chain_agnostic": agnostic,
        "in_scope": in_entries, "out_scope": out_entries,
        "needs_chain": needs_chain, "notes": notes,
        "counts": {
            "in_scope": len(in_entries), "out_scope": len(out_entries),
            "needs_chain": len(needs_chain), "notes": len(notes),
        },
        "warning": "AUTO-EXTRACTED DRAFT: verify every entry against the live page before setting Status to Active.",
    }


def render_markdown(report: dict[str, object]) -> str:
    def cell(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = [
        f"# {report['name']}", "", "| Field | Value |", "|-------|-------|",
        f"| **Platform** | {cell(report['platform'])} |",
        "| **Handle** |  |", "| **Status** | Draft |",
        f"| **Last Scope Review** | {str(report['fetched_at'])[:10]} |",
        f"| **Source URL** | {cell(report['source'])} |",
        f"| **Fetched At** | {cell(report['fetched_at'])} |",
        f"| **Extraction Method** | {cell(report['method'])} |",
        "| **Researcher** |  |", "", "## In Scope",
    ]
    in_scope = report["in_scope"]  # type: ignore[index]
    out_scope = report["out_scope"]  # type: ignore[index]
    lines += [f"- {entry}" for entry in in_scope] or [
        "<!-- none extracted, review the source page -->"
    ]
    lines += ["", "## Out of Scope"]
    lines += [f"- {entry}" for entry in out_scope] or [
        "<!-- none extracted, check the source page manually -->"
    ]
    lines += ["", "## Special Rules", f"- {report['warning']}",
              f"- Source: {report['source']}", f"- Fetched: {report['fetched_at']}",
              f"- Extraction: {report['method']}"]
    lines += [f"- {note}" for note in report["notes"]]  # type: ignore[union-attr]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract a DRAFT chain-scope program from a bounty page.")
    parser.add_argument("--url")
    parser.add_argument("--input-file", type=Path, help="local HTML/markdown file instead of fetching")
    parser.add_argument("--output", type=Path, help="write draft markdown here; JSON report goes to stdout")
    parser.add_argument("--report", type=Path, help="also write the JSON report here")
    parser.add_argument("--name")
    parser.add_argument("--platform")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args(argv)

    if bool(args.url) == bool(args.input_file):
        parser.error("provide exactly one of --url or --input-file")

    source = args.url or str(args.input_file)
    fetched_at = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    if args.url:
        text, method = fetch_page(args.url, args.timeout)
        name = args.name or slug_from_url(args.url)
        platform = args.platform or guess_platform(args.url)
    else:
        raw = args.input_file.read_text(encoding="utf-8", errors="replace")
        text = html_to_text(raw) if re.search(r"<!doctype html|<html[\s>]", raw[:2000], re.I) else raw
        method = "file"
        name = args.name or args.input_file.stem
        platform = args.platform or "Unknown"

    report = extract(text, source, method, name, platform, fetched_at)
    markdown = render_markdown(report)
    report_json = json.dumps(report, indent=2, ensure_ascii=False)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
        print(report_json)
    else:
        print(markdown)
        print(report_json, file=sys.stderr)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report_json + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
