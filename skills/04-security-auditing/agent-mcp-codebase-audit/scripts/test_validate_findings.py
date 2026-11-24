#!/usr/bin/env python3
"""Self-test for validate_findings.py. Uses only stdlib and a scratch directory."""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
VALIDATOR = HERE / "validate_findings.py"

BASE = {
    "schema_version": "1.0.0",
    "target": "test-agent-tooling",
    "generated_at": "2026-11-24T00:00:00Z",
    "coverage_ledger": [{
        "unit_id": "U1", "boundary": "service response to local artifact",
        "entry_point": "HTTP response body", "sink": "results/consent_matrix.json",
        "state": "covered",
    }],
    "checked_not_a_problem": ["control case redacts plaintext"],
    "not_covered": ["live service not exercised"],
}

CONFIRMED = {
    "verdict": "confirmed",
    "fingerprint": "redact/unescape-order",
    "title": "Encoded credential survives redaction",
    "owasp": "LLM02:2025",
    "source": "service response body with HTML entity encoded token",
    "sink": "results/consent_matrix.json",
    "attack": "service reflects an encoded token after redaction runs",
    "impact": "credential written plaintext to local artifact",
    "fix": "unescape before redacting and remove the later unescape",
    "locations": ["run_consent_matrix.py:20"],
    "trace": [
        {"kind": "entry", "value": "HTTP response body"},
        {"kind": "transform", "value": "html.unescape after secret replace"},
        {"kind": "sink", "value": "write_text to results/consent_matrix.json"},
    ],
    "verifier": {
        "id": "isolated-ast-redact-check",
        "checks": ["extracted redact(), crafted encoded secret, leak True"],
        "result": "confirmed",
    },
    "severity": "medium",
    "evidence": ["crafted input produced plaintext secret in output"],
}


def run(doc, name):
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / name
        p.write_text(json.dumps(doc), encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(VALIDATOR), str(p)],
            capture_output=True, text=True,
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()


def main():
    cases = []

    good = dict(BASE)
    good["findings"] = [CONFIRMED]
    cases.append(("valid confirmed", good, 0))

    nv = dict(BASE)
    nv["findings"] = [{
        "verdict": "needs_validation", "fingerprint": "nv/one",
        "title": "needs runtime proof", "blockers": ["no live gateway"],
        "validation_plan": "operator runs local harness", "severity": "low",
    }]
    cases.append(("needs_validation with severity", nv, 1))

    nov = json.loads(json.dumps(CONFIRMED))
    del nov["verifier"]
    bad = dict(BASE)
    bad["findings"] = [nov]
    cases.append(("confirmed without verifier", bad, 1))

    sec = json.loads(json.dumps(CONFIRMED))
    sec["notes"] = "token sk-abcdefghijklmnopqrstuvwxyz1234"
    bad2 = dict(BASE)
    bad2["findings"] = [sec]
    cases.append(("secret value in text", bad2, 1))

    dup = dict(BASE)
    dup["findings"] = [CONFIRMED, dict(CONFIRMED)]
    cases.append(("duplicate fingerprint", dup, 1))

    bad3 = dict(BASE)
    bad3["coverage_ledger"] = [dict(BASE["coverage_ledger"][0], state="done")]
    bad3["findings"] = []
    cases.append(("invalid ledger state", bad3, 1))

    failed = 0
    for name, doc, expect in cases:
        code, out, err = run(doc, name.replace(" ", "_") + ".json")
        ok = code == expect
        print(f"{'PASS' if ok else 'FAIL'} {name}: exit {code}, expected {expect}, {out.splitlines()[0] if out else err}")
        if not ok:
            failed += 1
    print(f"\n{len(cases) - failed}/{len(cases)} cases passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
