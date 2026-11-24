#!/usr/bin/env python3
"""Chain-scope guard for EVM / Solana bug-bounty targets.

Adapts the markdown-program + scope-guard pattern from bugbounty-lab101 to
contract addresses and program IDs. Standard library only.

Target / scope entry format:
    evm:<chain-id-or-alias>:<0x-address>
    solana:<cluster>:<base58-pubkey>
Two-part entries (evm:1, solana:mainnet) mean "all identifiers on that chain"
and are only valid as SCOPE rules, never as a concrete target.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

INACTIVE_STATUSES = {
    "paused", "retired", "closed", "inactive", "archived", "ended",
    "draft", "unreviewed", "pending",
}
WILDCARD = "*"

EVM_CHAIN_ALIASES = {
    "ethereum": "1", "mainnet": "1", "eth": "1",
    "arbitrum": "42161", "arb": "42161",
    "base": "8453", "optimism": "10", "op": "10",
    "polygon": "137", "matic": "137",
    "bsc": "56", "binance": "56",
    "avalanche": "43114", "avax": "43114",
    "sonic": "146", "berachain": "80094",
}
SOLANA_CLUSTER_ALIASES = {
    "mainnet": "mainnet-beta", "mainnet-beta": "mainnet-beta",
    "devnet": "devnet", "testnet": "testnet", "localnet": "localnet",
}
EVM_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
BASE58_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
TABLE_ROW_RE = re.compile(r"^\|\s*\*{0,2}([^|*]+?)\*{0,2}\s*\|\s*(.*?)\s*\|\s*$")
B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


class ScopeError(ValueError):
    """Malformed target/scope entry, or an authorization denial."""


@dataclass(frozen=True)
class ChainTarget:
    raw: str
    ecosystem: str
    chain_ref: str
    identifier: str
    is_wildcard: bool = False

    @property
    def chain(self) -> str:
        return f"{self.ecosystem}:{self.chain_ref}"

    @property
    def canonical(self) -> str:
        return f"{self.chain}:{self.identifier}"


@dataclass
class ProgramPolicy:
    path: Path
    name: str
    platform: str = "HackenProof"
    handle: str = ""
    status: str = "Active"
    last_review: str | None = None
    in_scope: list[str] = field(default_factory=list)
    out_scope: list[str] = field(default_factory=list)
    in_rules: list[ChainTarget] = field(default_factory=list)
    out_rules: list[ChainTarget] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    active: bool = True
    stale_days: int | None = None
    parse_error: str | None = None


def b58decode(value: str) -> bytes:
    """Decode base58 without third-party deps; raise ValueError on bad chars."""
    number = 0
    for char in value:
        number = number * 58 + B58_ALPHABET.index(char)
    leading = len(value) - len(value.lstrip("1"))
    body = number.to_bytes((number.bit_length() + 7) // 8, "big") if number else b""
    return b"\x00" * leading + body


def _clean_token(value: str) -> str:
    cleaned = value.strip().strip("`<>")
    token = re.split(r"\s+", cleaned, maxsplit=1)[0]
    if not token:
        raise ScopeError("entry is empty")
    if any(ch.isspace() or ord(ch) < 32 for ch in token):
        raise ScopeError("entry contains whitespace or control characters")
    return token


def parse_target(value: str) -> ChainTarget:
    """Validate and normalize a concrete EVM/Solana target."""
    token = _clean_token(value)
    parts = token.split(":")
    if len(parts) != 3:
        raise ScopeError("expected <ecosystem>:<chain>:<identifier>")
    ecosystem, chain_raw, identifier = parts[0].lower(), parts[1].lower(), parts[2]
    if chain_raw in {"*", "all", "any"}:
        raise ScopeError("a concrete target cannot use a wildcard chain")
    if identifier == WILDCARD:
        raise ScopeError("a concrete target cannot be a wildcard")

    if ecosystem == "evm":
        chain = EVM_CHAIN_ALIASES.get(chain_raw, chain_raw)
        if not chain.isdigit() or not (1 <= len(chain) <= 20):
            raise ScopeError(f"invalid EVM chain id or alias: {chain_raw}")
        if not EVM_ADDRESS_RE.fullmatch(identifier):
            raise ScopeError("EVM identifier must be 0x followed by 40 hex characters")
        return ChainTarget(token, "evm", chain, identifier.lower())

    if ecosystem == "solana":
        chain = SOLANA_CLUSTER_ALIASES.get(chain_raw, "")
        if not chain:
            raise ScopeError(f"unknown Solana cluster: {chain_raw}")
        if not BASE58_RE.fullmatch(identifier):
            raise ScopeError("Solana identifier must be 32-44 base58 characters")
        try:
            decoded = b58decode(identifier)
        except ValueError as exc:
            raise ScopeError("Solana identifier contains invalid base58 characters") from exc
        if len(decoded) != 32:
            raise ScopeError(f"Solana pubkey must decode to 32 bytes (got {len(decoded)})")
        return ChainTarget(token, "solana", chain, identifier)

    raise ScopeError(f"unsupported ecosystem: {ecosystem} (use evm or solana)")


def parse_scope_rule(value: str) -> ChainTarget:
    """Parse a scope entry; wildcards and 2-part chain-wide entries are allowed."""
    token = _clean_token(value)
    parts = token.split(":")
    if len(parts) == 2:
        parts.append(WILDCARD)
    if len(parts) != 3:
        raise ScopeError("expected <ecosystem>:<chain>[:<identifier>]")
    ecosystem, chain_raw, identifier = parts[0].lower(), parts[1].lower(), parts[2]
    chain_wildcard = chain_raw in {"*", "all", "any"}

    if ecosystem == "evm":
        chain = WILDCARD if chain_wildcard else EVM_CHAIN_ALIASES.get(chain_raw, chain_raw)
        if chain != WILDCARD and (not chain.isdigit() or not (1 <= len(chain) <= 20)):
            raise ScopeError(f"invalid EVM chain id or alias: {chain_raw}")
        if identifier == WILDCARD:
            return ChainTarget(token, "evm", chain, WILDCARD, True)
        if not EVM_ADDRESS_RE.fullmatch(identifier):
            raise ScopeError("EVM identifier must be 0x followed by 40 hex characters")
        return ChainTarget(token, "evm", chain, identifier.lower())

    if ecosystem == "solana":
        chain = WILDCARD if chain_wildcard else SOLANA_CLUSTER_ALIASES.get(chain_raw, "")
        if not chain:
            raise ScopeError(f"unknown Solana cluster: {chain_raw}")
        if identifier == WILDCARD:
            return ChainTarget(token, "solana", chain, WILDCARD, True)
        if not BASE58_RE.fullmatch(identifier):
            raise ScopeError("Solana identifier must be 32-44 base58 characters")
        try:
            decoded = b58decode(identifier)
        except ValueError as exc:
            raise ScopeError("Solana identifier contains invalid base58 characters") from exc
        if len(decoded) != 32:
            raise ScopeError(f"Solana pubkey must decode to 32 bytes (got {len(decoded)})")
        return ChainTarget(token, "solana", chain, identifier)

    raise ScopeError(f"unsupported ecosystem: {ecosystem} (use evm or solana)")


def normalize_target(value: str) -> str:
    return parse_target(value).canonical


def rule_matches(target: ChainTarget, rule: ChainTarget) -> bool:
    if rule.chain_ref != WILDCARD and target.chain_ref != rule.chain_ref:
        return False
    return (
        target.ecosystem == rule.ecosystem
        and (rule.is_wildcard or target.identifier == rule.identifier)
    )


def _metadata(text: str, path: Path) -> tuple[str, str, str, str, str | None]:
    name = path.stem
    for line in text.splitlines():
        if line.strip().startswith("# "):
            heading = line.strip()[2:].strip()
            if heading and heading != "[Program Name]":
                name = heading
            break
    meta: dict[str, str] = {}
    for line in text.splitlines():
        match = TABLE_ROW_RE.match(line.strip())
        if match:
            meta[match.group(1).strip().lower()] = match.group(2).strip()
    platform = meta.get("platform", "HackenProof") or "HackenProof"
    handle = meta.get("handle") or meta.get("program handle") or ""
    status = meta.get("status", "Active") or "Active"
    review_raw = meta.get("last scope review", "")
    review = review_raw if re.fullmatch(r"\d{4}-\d{2}-\d{2}", review_raw) else None
    return name, platform, handle, status, review


def _stale_days(review: str | None) -> int | None:
    if not review:
        return None
    try:
        parsed = datetime.date.fromisoformat(review)
    except ValueError:
        return None
    elapsed = (datetime.datetime.now(datetime.timezone.utc).date() - parsed).days
    return max(0, elapsed)


def _is_active(status: str) -> bool:
    first = re.split(r"[\s(:;,/]+", status.strip().lower(), maxsplit=1)[0]
    return first not in INACTIVE_STATUSES


def read_program_policy(path: Path) -> ProgramPolicy:
    text = path.read_text(encoding="utf-8")
    name, platform, handle, status, review = _metadata(text, path)
    policy = ProgramPolicy(
        path=path, name=name, platform=platform, handle=handle,
        status=status, last_review=review, active=_is_active(status),
        stale_days=_stale_days(review),
    )
    current = ""
    for line_no, line in enumerate(text.splitlines(), start=1):
        heading = line.strip().lower()
        if heading == "## in scope":
            current = "in"
            continue
        if heading == "## out of scope":
            current = "out"
            continue
        if heading.startswith("## "):
            current = "note" if heading in {"## notes", "## special rules"} else ""
            continue
        bullet = re.match(r"^\s*[-*]\s+(.+?)\s*$", line)
        if current in {"in", "out"} and bullet:
            try:
                rule = parse_scope_rule(bullet.group(1))
            except ScopeError as exc:
                raise ScopeError(f"invalid scope entry at {path}:{line_no}: {exc}") from exc
            if current == "in":
                policy.in_scope.append(rule.canonical)
                policy.in_rules.append(rule)
            else:
                policy.out_scope.append(rule.canonical)
                policy.out_rules.append(rule)
        elif current == "note" and line.strip():
            policy.notes.append(line.strip())
    return policy


def load_program_policies(programs_dir: Path, lenient: bool = False) -> list[ProgramPolicy]:
    policies: list[ProgramPolicy] = []
    if not programs_dir.is_dir():
        return policies
    for path in sorted(programs_dir.glob("*.md")):
        if path.name in {"_template.md", "README.md"}:
            continue
        try:
            policies.append(read_program_policy(path))
        except (ScopeError, OSError) as exc:
            if not lenient:
                raise
            name, platform, handle, status, review = _metadata(
                path.read_text(encoding="utf-8", errors="replace"), path
            )
            policies.append(ProgramPolicy(
                path=path, name=name, platform=platform, handle=handle,
                status=status, last_review=review, active=_is_active(status),
                stale_days=_stale_days(review), parse_error=str(exc),
            ))
    return policies


def _max_age() -> int:
    try:
        return int(os.environ.get("CHAIN_SCOPE_MAX_AGE_DAYS", "30"))
    except ValueError:
        return 30


def _warn_stale(policy: ProgramPolicy) -> None:
    max_age = _max_age()
    if max_age > 0 and policy.stale_days is not None and policy.stale_days > max_age:
        print(
            f"Scope warning: {policy.path.name} last reviewed {policy.last_review} "
            f"({policy.stale_days}d ago > {max_age}d); re-verify the program page.",
            file=sys.stderr,
        )


def _evaluate(target: ChainTarget, policies: list[ProgramPolicy], programs_dir: Path) -> tuple[ProgramPolicy, ChainTarget]:
    for policy in policies:
        for rule in policy.out_rules:
            if rule_matches(target, rule):
                raise ScopeError(
                    f"{target.canonical} is explicitly OUT of scope in {policy.path.name} ({rule.canonical})"
                )
    for policy in policies:
        if policy.active:
            for rule in policy.in_rules:
                if rule_matches(target, rule):
                    return policy, rule
    for policy in policies:
        if not policy.active:
            for rule in policy.in_rules:
                if rule_matches(target, rule):
                    raise ScopeError(
                        f"{target.canonical} is only covered by inactive program "
                        f"{policy.path.name} (status: {policy.status})"
                    )
    raise ScopeError(f"{target.canonical} is not listed in scope under {programs_dir}")


def authorize(target: str, programs_dir: Path, warn_stale: bool = True) -> tuple[str, Path]:
    parsed = parse_target(target)
    policies = load_program_policies(programs_dir)
    policy, _ = _evaluate(parsed, policies, programs_dir)
    if warn_stale:
        _warn_stale(policy)
    return parsed.canonical, policy.path


def explain_target(target: str, programs_dir: Path) -> dict[str, object]:
    try:
        parsed = parse_target(target)
    except ScopeError as exc:
        return {"target": target, "authorized": False, "reason": str(exc), "program_file": None}
    try:
        policies = load_program_policies(programs_dir)
        policy, rule = _evaluate(parsed, policies, programs_dir)
    except ScopeError as exc:
        return {
            "target": target, "canonical": parsed.canonical, "authorized": False,
            "reason": str(exc), "program_file": None,
        }
    return {
        "target": target, "canonical": parsed.canonical, "authorized": True,
        "reason": f"Matched active in-scope rule '{rule.canonical}' in {policy.path.name}",
        "program_file": str(policy.path), "program_name": policy.name,
        "platform": policy.platform, "handle": policy.handle,
        "status": policy.status, "last_review": policy.last_review,
        "stale_days": policy.stale_days, "matched_rule": rule.canonical,
        "notes": policy.notes,
    }


def filter_file(input_path: Path, programs_dir: Path, authorized_out: Path,
                discarded_out: Path, candidates_out: Path | None = None) -> dict[str, int]:
    policies = load_program_policies(programs_dir)
    allowed: list[str] = []
    denied: list[str] = []
    if input_path.is_file():
        for line in input_path.read_text(encoding="utf-8", errors="replace").splitlines():
            candidate = line.strip()
            if not candidate or candidate.startswith("#"):
                continue
            try:
                _evaluate(parse_target(candidate), policies, programs_dir)
                allowed.append(candidate)
            except ScopeError:
                denied.append(candidate)
    _write_lf(authorized_out, "".join(f"{x}\n" for x in allowed))
    _write_lf(discarded_out, "".join(f"{x}\n" for x in denied))
    if candidates_out is not None and denied:
        existing = set()
        if candidates_out.is_file():
            existing = {
                line.strip() for line in
                candidates_out.read_text(encoding="utf-8", errors="replace").splitlines()
                if line.strip()
            }
        _write_lf(candidates_out, "".join(f"{x}\n" for x in sorted(existing | set(denied))))
    return {"authorized": len(allowed), "discarded": len(denied)}


def audit_programs(programs_dir: Path, max_age_days: int = 30) -> dict[str, object]:
    policies = load_program_policies(programs_dir, lenient=True)
    out_rules = [(p.path.name, r) for p in policies if not p.parse_error for r in p.out_rules]
    results: list[dict[str, object]] = []
    for policy in policies:
        stale = bool(max_age_days > 0 and policy.stale_days is not None and policy.stale_days > max_age_days)
        conflicts: list[str] = []
        if policy.active and policy.parse_error is None:
            for rule in policy.in_rules:
                for out_prog, out_rule in out_rules:
                    if rule_matches(rule, out_rule):
                        conflicts.append(
                            f"{rule.canonical} shadowed by out-of-scope '{out_rule.canonical}' in {out_prog}"
                        )
        results.append({
            "file": policy.path.name, "name": policy.name, "platform": policy.platform,
            "status": policy.status, "active": policy.active,
            "last_review": policy.last_review, "stale_days": policy.stale_days,
            "stale": stale, "missing_review": policy.last_review is None,
            "parse_error": policy.parse_error,
            "in_scope_total": len(policy.in_rules), "out_scope_total": len(policy.out_rules),
            "evm_rules": sum(1 for r in policy.in_rules if r.ecosystem == "evm"),
            "solana_rules": sum(1 for r in policy.in_rules if r.ecosystem == "solana"),
            "wildcard_rules": sum(1 for r in policy.in_rules if r.is_wildcard),
            "notes": len(policy.notes), "conflicts": conflicts,
        })
    return {
        "programs_dir": str(programs_dir), "total_programs": len(policies),
        "active_programs": sum(1 for p in policies if p.active),
        "parse_errors": sum(1 for p in policies if p.parse_error),
        "stale_or_missing_review": sum(
            1 for r in results if r["stale"] or r["missing_review"]
        ),
        "conflicts_found": sum(len(r["conflicts"]) for r in results),
        "programs": results,
    }


def _entries_from_file(path: Path) -> set[str]:
    entries: set[str] = set()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "|")):
            continue
        token = re.match(r"^\s*[-*]\s+(.+?)\s*$", stripped)
        value = token.group(1) if token else stripped
        try:
            entries.add(parse_scope_rule(value).canonical)
        except ScopeError:
            continue
    return entries


def diff_scope_sources(old: Path, new: Path) -> dict[str, list[str]]:
    before, after = _entries_from_file(old), _entries_from_file(new)
    return {"added": sorted(after - before), "removed": sorted(before - after)}


def _write_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


TEMPLATE = """# [Program Name]

| Field | Value |
|-------|-------|
| **Platform** | HackenProof |
| **Handle** |  |
| **Status** | Active |
| **Last Scope Review** | [YYYY-MM-DD] |
| **Researcher** | [RESEARCHER] |

## In Scope
- evm:1:0x0000000000000000000000000000000000000000
- solana:mainnet-beta:11111111111111111111111111111111

## Out of Scope
- evm:1:0x0000000000000000000000000000000000000001

## Special Rules
- Payout trigger: [loss of funds / other]
- Reward formula: [paste the exact clause]
- Known issues excluded: [link]
- Max RPC rate: [n] req/s
"""


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scope guard for EVM/Solana bug-bounty targets (markdown programs)."
    )
    parser.add_argument("target", nargs="?")
    parser.add_argument("--programs-dir", type=Path)
    parser.add_argument("--normalize", action="store_true", help="print normalized target and exit")
    parser.add_argument("--explain", action="store_true", help="print JSON verdict")
    parser.add_argument("--policy-json", action="store_true", help="print program policy JSON")
    parser.add_argument("--audit", action="store_true", help="audit all programs/*.md")
    parser.add_argument("--max-age-days", type=int)
    parser.add_argument("--json", action="store_true", help="pretty JSON output")
    parser.add_argument("--filter-file", type=Path)
    parser.add_argument("--authorized-out", type=Path)
    parser.add_argument("--discarded-out", type=Path)
    parser.add_argument("--candidates-out", type=Path)
    parser.add_argument("--diff", nargs=2, metavar=("OLD_FILE", "NEW_FILE"))
    parser.add_argument("--print-template", action="store_true")
    parser.add_argument("--new-program", metavar="NAME")
    parser.add_argument("--platform", default="HackenProof")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.print_template:
        print(TEMPLATE, end="")
        return 0

    programs_dir = args.programs_dir or Path(
        os.environ.get("CHAIN_SCOPE_DIR", "programs")
    )

    if args.new_program:
        name = args.new_program
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}", name):
            print("Program name may only contain letters, numbers, dots, underscores, hyphens.", file=sys.stderr)
            return 2
        dest = programs_dir / f"{name}.md"
        if dest.exists():
            print(f"Already exists: {dest}", file=sys.stderr)
            return 2
        researcher = os.environ.get("CHAIN_RESEARCHER", "researcher")
        today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
        content = (TEMPLATE
                   .replace("[Program Name]", name)
                   .replace("[YYYY-MM-DD]", today)
                   .replace("[RESEARCHER]", researcher)
                   .replace("| **Platform** | HackenProof |", f"| **Platform** | {args.platform} |"))
        _write_lf(dest, content)
        print(f"Created {dest}. Edit In Scope / Out of Scope before scanning.")
        return 0

    def dump(obj: object) -> None:
        print(json.dumps(obj, indent=2 if args.json else None, ensure_ascii=False))

    if args.audit:
        max_age = args.max_age_days if args.max_age_days is not None else _max_age()
        dump(audit_programs(programs_dir, max_age))
        return 0

    if args.diff:
        dump(diff_scope_sources(Path(args.diff[0]), Path(args.diff[1])))
        return 0

    if args.filter_file:
        if not args.authorized_out or not args.discarded_out:
            print("--filter-file requires --authorized-out and --discarded-out", file=sys.stderr)
            return 2
        counts = filter_file(args.filter_file, programs_dir, args.authorized_out,
                             args.discarded_out, args.candidates_out)
        dump(counts)
        return 0

    if not args.target:
        parser.error("a target is required unless --audit/--diff/--filter-file/--print-template/--new-program is used")

    if args.normalize:
        try:
            print(parse_target(args.target).canonical)
        except ScopeError as exc:
            print(f"[!] {exc}", file=sys.stderr)
            return 1
        return 0

    if args.explain:
        dump(explain_target(args.target, programs_dir))
        return 0

    try:
        canonical, program_path = authorize(args.target, programs_dir)
    except ScopeError as exc:
        print(f"[!] Scope denied: {exc}", file=sys.stderr)
        return 1

    if args.policy_json:
        policy = next(
            (p for p in load_program_policies(programs_dir) if p.path == program_path),
            None,
        )
        if policy:
            dump({
                "target": canonical, "program_file": str(policy.path),
                "program_name": policy.name, "platform": policy.platform,
                "handle": policy.handle, "status": policy.status,
                "last_review": policy.last_review, "stale_days": policy.stale_days,
                "in_scope": policy.in_scope, "out_scope": policy.out_scope,
                "notes": policy.notes,
            })
        return 0

    print(f"[✓] Scope OK - {canonical} covered by {program_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
