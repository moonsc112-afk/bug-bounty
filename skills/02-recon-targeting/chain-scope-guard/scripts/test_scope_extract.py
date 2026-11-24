import json
import subprocess
import sys
from pathlib import Path

import pytest

import chain_scope_guard as csg
import scope_extract as se

A = "0x" + "a" * 40
B = "0x" + "b" * 40
C = "0x" + "c" * 40
D = "0x" + "d" * 40
COMMIT = "1234567890abcdef1234567890abcdef12345678"
SOL = "So11111111111111111111111111111111111111112"

HTML = f"""<!doctype html><html><body>
<h1>Demo Program</h1>
<h2>Assets in Scope</h2>
<p>Arbitrum endpoint: {A}</p>
<p>Ethereum vault: {B}</p>
<p>Solana program ID: {SOL}</p>
<p>Unlabelled deployment: {D}</p>
<h2>Out of scope</h2>
<p>Ethereum test contract: {C}</p>
<p>Repo: github.com/demo/protocol at commit {COMMIT}</p>
</body></html>
"""


def make_report(text=HTML):
    prepared = se.html_to_text(text) if "<html" in text[:2000].lower() else text
    return se.extract(prepared, "https://example.test/program", "file",
                      "demo", "Immunefi", "2026-11-21T00:00:00+00:00")


def test_extracts_chain_addresses_and_out_of_scope():
    report = make_report()
    assert f"evm:42161:{A}" in report["in_scope"]
    assert f"evm:1:{B}" in report["in_scope"]
    assert f"solana:mainnet-beta:{SOL}" in report["in_scope"]
    assert f"evm:1:{C}" in report["out_scope"]
    assert D in report["needs_chain"]
    assert any("Repo: https://github.com/demo/protocol" in n for n in report["notes"])
    assert any(COMMIT in n for n in report["notes"])
    assert report["counts"]["in_scope"] == 3


def test_chain_agnostic_scope():
    text = f"<p>The scope is limited to these addresses, not limited to any chain: {A}</p>"
    report = make_report(text)
    assert f"evm:*:{A}" in report["in_scope"]
    rule = csg.parse_scope_rule(f"evm:*:{A}")
    assert csg.rule_matches(csg.parse_target(f"evm:8453:{A}"), rule)


def test_draft_markdown_cannot_authorize(tmp_path):
    report = make_report()
    markdown = se.render_markdown(report)
    assert "| **Status** | Draft |" in markdown
    programs = tmp_path / "programs"
    programs.mkdir()
    (programs / "demo.md").write_text(markdown, encoding="utf-8")
    with pytest.raises(csg.ScopeError, match="inactive program"):
        csg.authorize(f"evm:42161:{A}", programs)


def test_cli_from_input_file(tmp_path):
    source = tmp_path / "program.html"
    source.write_text(HTML, encoding="utf-8")
    output = tmp_path / "draft.md"
    script = Path(se.__file__).resolve()
    result = subprocess.run(
        [sys.executable, str(script), "--input-file", str(source),
         "--output", str(output), "--name", "demo"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["method"] == "file"
    assert f"evm:42161:{A}" in report["in_scope"]
    assert "| **Status** | Draft |" in output.read_text(encoding="utf-8")
