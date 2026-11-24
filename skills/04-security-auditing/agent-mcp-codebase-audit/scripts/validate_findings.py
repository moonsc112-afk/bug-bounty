#!/usr/bin/env python3
"""Validate an agent-mcp-codebase-audit findings document.

Usage: python validate_findings.py <path-to-findings.json>

Adapted from cloudflare/security-audit-skill report-schema.json and its
zero-dependency validator. This is stdlib only. It checks the subset of JSON
Schema used by references/findings-schema.json plus the rules that are clearer
in code: verdict specific fields, severity placement, verifier presence and
consistency, unique fingerprints and a basic secret-value guard.
"""
import json
import pathlib
import re
import sys

MAX_BYTES = 5 * 1024 * 1024
MAX_ITEMS = 1000
MAX_ERRORS = 100

VERDICTS = {"confirmed", "needs_validation", "rejected"}
SEVERITIES = {"critical", "high", "medium", "low"}
STATES = {"planned", "candidate", "covered", "needs_validation", "blocked"}
TRACE_KINDS = {"entry", "transform", "guard", "sink"}

FP_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+-]*$")
UNIT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
SECRET_RE = re.compile(
    r"(?i)(?:sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|"
    r"bearer\s+(?!\[REDACTED\])[A-Za-z0-9._-]{12,}|"
    r"(?:api[_-]?key|password|secret)\s*[:=]\s*[A-Za-z0-9._-]{12,})"
)

CONFIRMED_REQUIRED = (
    "fingerprint", "title", "source", "sink", "attack", "impact",
    "fix", "locations", "trace", "verifier", "severity",
)
NEEDS_REQUIRED = ("fingerprint", "title", "blockers", "validation_plan")
REJECTED_REQUIRED = ("fingerprint", "title", "refutation")
TOP_REQUIRED = (
    "schema_version", "target", "generated_at", "coverage_ledger",
    "findings", "checked_not_a_problem", "not_covered",
)


class Checker:
    def __init__(self):
        self.errors = []

    def err(self, path, msg):
        if len(self.errors) < MAX_ERRORS:
            self.errors.append(f"{path}: {msg}")

    def nonblank(self, obj, key, path):
        value = obj.get(key)
        if not isinstance(value, str) or not value.strip():
            self.err(f"{path}.{key}", "must be a non-empty string")

    def string_list(self, obj, key, path, required=False, min_items=0):
        value = obj.get(key)
        if value is None and not required:
            return
        if not isinstance(value, list):
            self.err(f"{path}.{key}", "must be an array")
            return
        if len(value) > MAX_ITEMS:
            self.err(f"{path}.{key}", f"too many items (max {MAX_ITEMS})")
        if len(value) < min_items:
            self.err(f"{path}.{key}", f"needs at least {min_items} item(s)")
        for i, item in enumerate(value):
            if not isinstance(item, str) or not item.strip():
                self.err(f"{path}.{key}[{i}]", "must be a non-empty string")


def check_secret_strings(node, checker, path="$"):
    if isinstance(node, str):
        if SECRET_RE.search(node):
            checker.err(path, "possible credential value in document text")
    elif isinstance(node, dict):
        for k, v in node.items():
            check_secret_strings(v, checker, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            check_secret_strings(v, checker, f"{path}[{i}]")


def check_verifier(verifier, checker, path):
    if not isinstance(verifier, dict):
        checker.err(path, "must be an object")
        return
    checker.nonblank(verifier, "id", path)
    checker.string_list(verifier, "checks", path, required=True, min_items=1)
    if verifier.get("result") not in VERDICTS:
        checker.err(f"{path}.result", f"must be one of {sorted(VERDICTS)}")


def check_trace(trace, checker, path):
    if not isinstance(trace, list):
        checker.err(path, "must be an array")
        return
    if len(trace) < 1:
        checker.err(path, "needs at least one step")
    for i, step in enumerate(trace[:MAX_ITEMS]):
        sp = f"{path}[{i}]"
        if not isinstance(step, dict):
            checker.err(sp, "must be an object")
            continue
        if step.get("kind") not in TRACE_KINDS:
            checker.err(f"{sp}.kind", f"must be one of {sorted(TRACE_KINDS)}")
        checker.nonblank(step, "value", sp)


def check_finding(finding, checker, path):
    if not isinstance(finding, dict):
        checker.err(path, "must be an object")
        return
    verdict = finding.get("verdict")
    if verdict not in VERDICTS:
        checker.err(f"{path}.verdict", f"must be one of {sorted(VERDICTS)}")
        return
    fp = finding.get("fingerprint")
    if not isinstance(fp, str) or not FP_RE.match(fp):
        checker.err(f"{path}.fingerprint", "invalid fingerprint format")
    checker.nonblank(finding, "title", path)
    checker.string_list(finding, "locations", path)

    if verdict == "confirmed":
        for key in CONFIRMED_REQUIRED:
            if key not in finding:
                checker.err(path, f"confirmed finding missing {key}")
        for key in ("source", "sink", "attack", "impact", "fix"):
            checker.nonblank(finding, key, path)
        checker.string_list(finding, "locations", path, required=True, min_items=1)
        check_trace(finding.get("trace"), checker, f"{path}.trace")
        check_verifier(finding.get("verifier"), checker, f"{path}.verifier")
        if finding.get("severity") not in SEVERITIES:
            checker.err(f"{path}.severity", f"must be one of {sorted(SEVERITIES)}")
        verifier = finding.get("verifier")
        if isinstance(verifier, dict) and verifier.get("result") != "confirmed":
            checker.err(f"{path}.verifier.result", "confirmed finding needs a confirming verifier")
    elif verdict == "needs_validation":
        for key in NEEDS_REQUIRED:
            if key not in finding:
                checker.err(path, f"needs_validation finding missing {key}")
        checker.string_list(finding, "blockers", path, required=True, min_items=1)
        checker.nonblank(finding, "validation_plan", path)
        if "severity" in finding and finding["severity"] is not None:
            checker.err(f"{path}.severity", "needs_validation must not carry a severity")
    else:
        for key in REJECTED_REQUIRED:
            if key not in finding:
                checker.err(path, f"rejected finding missing {key}")
        checker.nonblank(finding, "refutation", path)
        if "severity" in finding and finding["severity"] is not None:
            checker.err(f"{path}.severity", "rejected must not carry a severity")


def check_document(doc):
    checker = Checker()
    if not isinstance(doc, dict):
        checker.err("$", "document must be an object")
        return checker.errors
    for key in TOP_REQUIRED:
        if key not in doc:
            checker.err("$", f"missing top-level {key}")
    if doc.get("schema_version") != "1.0.0":
        checker.err("$.schema_version", "must be 1.0.0")
    checker.nonblank(doc, "target", "$")
    checker.nonblank(doc, "generated_at", "$")

    ledger = doc.get("coverage_ledger")
    if not isinstance(ledger, list):
        checker.err("$.coverage_ledger", "must be an array")
    else:
        if len(ledger) > MAX_ITEMS:
            checker.err("$.coverage_ledger", f"too many units (max {MAX_ITEMS})")
        for i, unit in enumerate(ledger[:MAX_ITEMS]):
            up = f"$.coverage_ledger[{i}]"
            if not isinstance(unit, dict):
                checker.err(up, "must be an object")
                continue
            for key in ("unit_id", "boundary", "entry_point", "sink"):
                checker.nonblank(unit, key, up)
            uid = unit.get("unit_id")
            if isinstance(uid, str) and not UNIT_RE.match(uid):
                checker.err(f"{up}.unit_id", "invalid unit id")
            if unit.get("state") not in STATES:
                checker.err(f"{up}.state", f"must be one of {sorted(STATES)}")

    findings = doc.get("findings")
    if not isinstance(findings, list):
        checker.err("$.findings", "must be an array")
    else:
        if len(findings) > MAX_ITEMS:
            checker.err("$.findings", f"too many findings (max {MAX_ITEMS})")
        seen = set()
        for i, finding in enumerate(findings[:MAX_ITEMS]):
            check_finding(finding, checker, f"$.findings[{i}]")
            if isinstance(finding, dict):
                fp = finding.get("fingerprint")
                if isinstance(fp, str):
                    if fp in seen:
                        checker.err(f"$.findings[{i}].fingerprint", "duplicate fingerprint")
                    seen.add(fp)

    checker.string_list(doc, "checked_not_a_problem", "$")
    checker.string_list(doc, "not_covered", "$")
    check_secret_strings(doc, checker)
    return checker.errors


def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_findings.py <path-to-findings.json>", file=sys.stderr)
        return 2
    path = pathlib.Path(sys.argv[1])
    try:
        if path.stat().st_size > MAX_BYTES:
            print(f"File too large (max {MAX_BYTES} bytes)", file=sys.stderr)
            return 2
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"Cannot read JSON: {exc}", file=sys.stderr)
        return 2
    errors = check_document(doc)
    if errors:
        print("INVALID")
        for err in errors[:MAX_ERRORS]:
            print(" -", err)
        return 1
    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
