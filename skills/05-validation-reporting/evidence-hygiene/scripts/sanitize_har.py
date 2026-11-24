#!/usr/bin/env python3
"""Sanitize a HAR file with the Python standard library, no jq required.

Redacts the headers and cookies that evidence-hygiene requires, and optionally
scrubs named strings from response bodies. Writes a .sanitized.har copy and
verifies the result before exiting.

Usage:
  python3 sanitize_har.py exported.har
  python3 sanitize_har.py exported.har -o clean.har
  python3 sanitize_har.py exported.har --redact-text 'alice@example.com'
  python3 sanitize_har.py clean.har --verify-only
"""
import argparse
import json
import re
import sys

REDACTED = "<REDACTED>"
REQUEST_HEADERS = {"cookie", "authorization", "x-csrf-token"}
RESPONSE_HEADERS = {"set-cookie"}


def redact_headers(headers, names):
    for header in headers or []:
        if isinstance(header, dict) and str(header.get("name", "")).lower() in names:
            header["value"] = REDACTED
    return headers


def redact_cookies(cookies):
    for cookie in cookies or []:
        if isinstance(cookie, dict):
            cookie["value"] = REDACTED
    return cookies


def redact_body(text, patterns):
    if not isinstance(text, str):
        return text
    for pattern in patterns:
        try:
            text = re.sub(pattern, REDACTED, text)
        except re.error as exc:
            raise SystemExit("invalid --redact-text regex: %s" % exc)
    return text


def sanitize(data, patterns):
    entries = data.get("log", {}).get("entries", [])
    if not isinstance(entries, list):
        raise SystemExit("unexpected HAR shape: log.entries is not a list")
    for entry in entries:
        request = entry.get("request", {})
        response = entry.get("response", {})
        redact_headers(request.get("headers", []), REQUEST_HEADERS)
        redact_headers(response.get("headers", []), RESPONSE_HEADERS)
        redact_cookies(request.get("cookies", []))
        redact_cookies(response.get("cookies", []))
        content = response.get("content", {})
        if isinstance(content, dict):
            content["text"] = redact_body(content.get("text"), patterns)
    return data


def leaks(data):
    found = []
    for index, entry in enumerate(data.get("log", {}).get("entries", [])):
        for side, names in (("request", REQUEST_HEADERS), ("response", RESPONSE_HEADERS)):
            for header in entry.get(side, {}).get("headers", []) or []:
                if not isinstance(header, dict):
                    continue
                if str(header.get("name", "")).lower() in names and header.get("value") != REDACTED:
                    found.append("entry %d %s header %s" % (index, side, header.get("name")))
        for side in ("request", "response"):
            for cookie in entry.get(side, {}).get("cookies", []) or []:
                if isinstance(cookie, dict) and cookie.get("value") != REDACTED:
                    found.append("entry %d %s cookie %s" % (index, side, cookie.get("name")))
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="HAR file to sanitize or verify")
    parser.add_argument("-o", "--output", help="output path, default <input>.sanitized.har")
    parser.add_argument("--redact-text", action="append", default=[],
                        help="regex to scrub from response bodies, repeatable")
    parser.add_argument("--verify-only", action="store_true",
                        help="only check an existing file for leaks")
    args = parser.parse_args()

    try:
        with open(args.input, encoding="utf-8", errors="replace") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        raise SystemExit("cannot read HAR: %s" % exc)

    if not args.verify_only:
        data = sanitize(data, args.redact_text)
        if args.output:
            output = args.output
        elif args.input.lower().endswith(".har"):
            output = args.input[:-4] + ".sanitized.har"
        else:
            output = args.input + ".sanitized.har"
        try:
            with open(output, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, ensure_ascii=False)
        except OSError as exc:
            raise SystemExit("cannot write output: %s" % exc)
        print("Sanitized: %s" % output)
        check_path = output
    else:
        check_path = args.input

    bad = leaks(data)
    if bad:
        print("LEAKS STILL PRESENT:", file=sys.stderr)
        for item in bad:
            print("  " + item, file=sys.stderr)
        raise SystemExit(2)
    print("Verified: no sensitive headers or cookies left unredacted in %s" % check_path)


if __name__ == "__main__":
    main()
