#!/usr/bin/env python3
"""Turn operator observations into structured evidence. Stdlib only.

No result is invented. Every field comes from a real run supplied by the operator.
Sample mode writes clearly labelled non-evidence files for checking the tool itself.
"""
import argparse
import datetime as dt
import hashlib
import json
import pathlib

FIELDS = [
    "case_id", "date_utc", "surface", "account_label", "tool_call_path",
    "artifact_paths", "observed_result", "amount_and_asset", "tx_hash",
    "card_shown", "notes",
]

SAMPLE = {
    "case_id": "SAMPLE_CASE",
    "date_utc": "SAMPLE_NOT_A_REAL_RUN",
    "surface": "SAMPLE",
    "account_label": "SAMPLE_TEST_ACCOUNT",
    "tool_call_path": "SAMPLE_PATH",
    "artifact_paths": "SAMPLE_PATH",
    "observed_result": "SAMPLE_UNKNOWN",
    "amount_and_asset": "SAMPLE_UNKNOWN",
    "tx_hash": "SAMPLE_UNKNOWN",
    "card_shown": "SAMPLE_UNKNOWN",
    "notes": "SAMPLE ONLY. Tool self-test, not evidence of a vulnerability.",
}


def write_manifest(outdir):
    out = pathlib.Path(outdir)
    if not out.is_dir():
        print(f"Not a directory: {out}")
        return
    rows = []
    for path in sorted(p for p in out.rglob("*") if p.is_file() and p.name != "SHA256SUMS"):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append(f"{digest}  {path.relative_to(out).as_posix()}")
    manifest = out / "SHA256SUMS"
    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {manifest.resolve()} with {len(rows)} entries")


def write_evidence(outdir, data, sample=False):
    out = pathlib.Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    status = "SAMPLE, NOT EVIDENCE" if sample else "OPERATOR SUPPLIED, VERIFY BEFORE SUBMISSION"
    md = [f"# {data['case_id']} evidence", "", f"Status: {status}", f"Recorded: {stamp}",
          "", "| Field | Value |", "| --- | --- |"]
    for key in FIELDS:
        value = str(data.get(key, "")).replace("|", "\\|").replace("\n", " ")
        md.append(f"| {key} | {value} |")
    md += ["", "## Capture discipline", "",
           "- Redact session cookies, Authorization headers, API keys and seed phrases before attaching.",
           "- Keep trace IDs, request IDs and test account labels visible for triage correlation.",
           "- Do not include another person's data or funds in any artifact.",
           "- Store unredacted originals locally only.", ""]
    base = out / (("SAMPLE_" if sample else "") + data["case_id"] + "_" + stamp)
    base.with_suffix(".md").write_text("\n".join(md), encoding="utf-8", newline="\n")
    base.with_suffix(".json").write_text(
        json.dumps({"sample": sample, "captured": stamp, **data}, indent=2) + "\n",
        encoding="utf-8", newline="\n")
    print(f"Wrote {base.name}.md and .json")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample", metavar="DIR", help="write labelled non-evidence files to DIR")
    ap.add_argument("--manifest", metavar="DIR", help="write LF-terminated SHA256SUMS for DIR")
    ap.add_argument("--show-fields", action="store_true")
    ap.add_argument("--case-id")
    for field in FIELDS:
        if field != "case_id":
            ap.add_argument("--" + field.replace("_", "-"), dest=field)
    args = ap.parse_args()

    if args.show_fields:
        print("Fields: " + ", ".join(FIELDS))
        return
    if args.manifest:
        write_manifest(args.manifest)
        return
    if args.sample:
        write_evidence(args.sample, SAMPLE, sample=True)
        write_manifest(args.sample)
        return
    data = {key: getattr(args, key, None) or "" for key in FIELDS}
    if not data["case_id"]:
        ap.error("--case-id is required for a real capture")
    write_evidence("evidence", data, sample=False)


if __name__ == "__main__":
    main()
