import json
import subprocess
import sys
from pathlib import Path

import pytest

import chain_scope_guard as csg

A = "0x" + "a" * 40
B = "0x" + "b" * 40
C = "0x" + "c" * 40
D = "0x" + "d" * 40
SOL = "So11111111111111111111111111111111111111112"
SYS = "11111111111111111111111111111111"

ALPHA = f"""# Alpha Program

| Field | Value |
|-------|-------|
| **Platform** | HackenProof |
| **Handle** | alpha |
| **Status** | Active |
| **Last Scope Review** | 2099-01-01 |

## In Scope
- evm:1:{A}
- evm:1:{B}
- solana:mainnet-beta:{SOL}

## Out of Scope
- evm:1:{B}

## Special Rules
- Payout trigger: loss of funds
"""

BETA = f"""# Beta Program

| Field | Value |
|-------|-------|
| **Platform** | Immunefi |
| **Status** | Paused |
| **Last Scope Review** | 2020-01-01 |

## In Scope
- evm:42161:{C}
"""

GAMMA = """# Gamma Program

| Field | Value |
|-------|-------|
| **Platform** | Cantina |
| **Status** | Active |
| **Last Scope Review** | 2099-01-01 |

## In Scope
- solana:devnet:*

## Out of Scope
- solana:mainnet-beta:11111111111111111111111111111111
"""


@pytest.fixture()
def programs(tmp_path):
    directory = tmp_path / "programs"
    directory.mkdir()
    (directory / "alpha.md").write_text(ALPHA, encoding="utf-8")
    (directory / "beta.md").write_text(BETA, encoding="utf-8")
    (directory / "gamma.md").write_text(GAMMA, encoding="utf-8")
    return directory


def test_normalize_evm_case_and_chain_alias():
    target = csg.parse_target(f"EVM:Ethereum:0x{'A' * 40}")
    assert target.canonical == f"evm:1:{A}"
    assert csg.parse_target(f"evm:arbitrum:{C}").chain_ref == "42161"
    with pytest.raises(csg.ScopeError):
        csg.normalize_target(f"arb:{C}")


def test_reject_malformed_evm():
    for bad in ("evm:1:0x123", "evm:notachain:" + A, "evm:1:" + A + "00", "btc:1:" + A):
        with pytest.raises(csg.ScopeError):
            csg.parse_target(bad)


def test_solana_pubkey_validation():
    assert csg.parse_target(f"solana:mainnet:{SYS}").canonical == f"solana:mainnet-beta:{SYS}"
    assert csg.parse_target(f"solana:mainnet-beta:{SOL}").identifier == SOL
    for bad in (f"solana:mainnet:{'z' * 32}", "solana:mainnet:0OIl" + "1" * 28,
                "solana:nowhere:" + SYS):
        with pytest.raises(csg.ScopeError):
            csg.parse_target(bad)


def test_wildcard_rules_only():
    wildcard = csg.parse_scope_rule("solana:devnet")
    assert wildcard.is_wildcard and wildcard.canonical == "solana:devnet:*"
    assert csg.rule_matches(csg.parse_target(f"solana:devnet:{SYS}"), wildcard)
    with pytest.raises(csg.ScopeError):
        csg.parse_target("solana:devnet:*")


def test_chain_wildcard_rule():
    rule = csg.parse_scope_rule(f"evm:any:{A}")
    assert rule.canonical == f"evm:*:{A}"
    assert csg.rule_matches(csg.parse_target(f"evm:1:{A}"), rule)
    assert csg.rule_matches(csg.parse_target(f"evm:8453:{A}"), rule)
    assert not csg.rule_matches(csg.parse_target(f"evm:8453:{C}"), rule)
    with pytest.raises(csg.ScopeError):
        csg.parse_target(f"evm:*:{A}")


def test_draft_program_cannot_authorize(tmp_path):
    directory = tmp_path / "programs"
    directory.mkdir()
    (directory / "draft.md").write_text(
        f"| **Status** | Draft |\n\n## In Scope\n- evm:1:{A}\n", encoding="utf-8"
    )
    with pytest.raises(csg.ScopeError, match="inactive program"):
        csg.authorize(f"evm:1:{A}", directory)


def test_authorize_active_and_deny_paths(programs):
    assert csg.authorize(f"evm:1:{A}", programs)[1].name == "alpha.md"
    assert csg.authorize(f"solana:mainnet-beta:{SOL}", programs)[1].name == "alpha.md"
    assert csg.authorize(f"solana:devnet:{SYS}", programs)[1].name == "gamma.md"

    with pytest.raises(csg.ScopeError, match="explicitly OUT"):
        csg.authorize(f"evm:ethereum:{B}", programs)
    with pytest.raises(csg.ScopeError, match="inactive program"):
        csg.authorize(f"evm:42161:{C}", programs)
    with pytest.raises(csg.ScopeError, match="not listed"):
        csg.authorize(f"evm:1:{D}", programs)


def test_explain_is_structured(programs):
    ok = csg.explain_target(f"evm:1:{A}", programs)
    assert ok["authorized"] is True and ok["matched_rule"] == f"evm:1:{A}"
    bad = csg.explain_target(f"evm:1:{D}", programs)
    assert bad["authorized"] is False and bad["program_file"] is None
    malformed = csg.explain_target("nonsense", programs)
    assert malformed["authorized"] is False


def test_filter_file(tmp_path, programs):
    candidates = tmp_path / "candidates.txt"
    candidates.write_text(
        f"evm:1:{A}\nevm:1:{B}\nevm:1:{D}\n# comment\n\n", encoding="utf-8"
    )
    allowed, denied, pending = (tmp_path / n for n in ("ok.txt", "no.txt", "pending.txt"))
    counts = csg.filter_file(candidates, programs, allowed, denied, pending)
    assert counts == {"authorized": 1, "discarded": 2}
    assert allowed.read_text(encoding="utf-8").strip() == f"evm:1:{A}"
    assert set(denied.read_text(encoding="utf-8").split()) == {f"evm:1:{B}", f"evm:1:{D}"}
    assert set(pending.read_text(encoding="utf-8").split()) == {f"evm:1:{B}", f"evm:1:{D}"}


def test_audit_flags_stale_and_conflicts(tmp_path):
    directory = tmp_path / "programs"
    directory.mkdir()
    (directory / "one.md").write_text(
        f"| **Status** | Active |\n| **Last Scope Review** | 2099-01-01 |\n\n"
        f"## In Scope\n- evm:1:{A}\n\n## Out of Scope\n- evm:1:{B}\n",
        encoding="utf-8",
    )
    (directory / "two.md").write_text(
        f"| **Status** | Active |\n| **Last Scope Review** | 2020-01-01 |\n\n"
        f"## In Scope\n- evm:1:{B}\n",
        encoding="utf-8",
    )
    report = csg.audit_programs(directory, 30)
    assert report["conflicts_found"] == 1
    assert report["stale_or_missing_review"] == 1
    assert report["programs"][0]["evm_rules"] == 1


def test_diff_scope_sources(tmp_path):
    old = tmp_path / "old.md"
    new = tmp_path / "new.md"
    old.write_text(f"## In Scope\n- evm:1:{A}\n- evm:1:{B}\n", encoding="utf-8")
    new.write_text(f"## In Scope\n- evm:1:{A}\n- evm:1:{D}\n", encoding="utf-8")
    result = csg.diff_scope_sources(old, new)
    assert result["added"] == [f"evm:1:{D}"]
    assert result["removed"] == [f"evm:1:{B}"]


def test_cli_exit_codes_and_explain(tmp_path, programs):
    script = Path(csg.__file__).resolve()
    base = [sys.executable, str(script), "--programs-dir", str(programs)]
    ok = subprocess.run(base + [f"evm:1:{A}"], capture_output=True, text=True)
    assert ok.returncode == 0 and "Scope OK" in ok.stdout
    denied = subprocess.run(base + [f"evm:1:{B}"], capture_output=True, text=True)
    assert denied.returncode == 1 and "OUT of scope" in denied.stderr
    explained = subprocess.run(base + ["--explain", f"evm:1:{D}"], capture_output=True, text=True)
    payload = json.loads(explained.stdout)
    assert payload["authorized"] is False
    normalized = subprocess.run(base + ["--normalize", f"EVM:Ethereum:0x{'A' * 40}"], capture_output=True, text=True)
    assert normalized.stdout.strip() == f"evm:1:{A}"


def test_cli_new_program(tmp_path):
    script = Path(csg.__file__).resolve()
    target_dir = tmp_path / "fresh"
    result = subprocess.run(
        [sys.executable, str(script), "--programs-dir", str(target_dir),
         "--new-program", "hacken-alpha", "--platform", "HackenProof"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    content = (target_dir / "hacken-alpha.md").read_text(encoding="utf-8")
    assert "hacken-alpha" in content and "## In Scope" in content
    assert "## Out of Scope" in content
