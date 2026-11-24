import json
import os
import sys
import urllib.request

ENV = os.path.join(os.path.expanduser("~"), "AppData", "Local", "hermes", ".env")
URL = "https://mantis.inverse.finance/mcp"


def token():
    with open(ENV, encoding="utf-8") as f:
        for line in f:
            if line.startswith("MCP_MANTIS_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("MCP_MANTIS_API_KEY missing")


def call(method, params=None, rid=1):
    body = json.dumps({"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}}).encode()
    req = urllib.request.Request(
        URL, data=body, headers={
            "Authorization": "Bearer " + token(),
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }, method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8", "replace")
    for line in raw.splitlines():
        if line.startswith("data:"):
            line = line[5:].strip()
        if line.startswith("{"):
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if "result" in obj or "error" in obj:
                return obj
    return {"raw": raw[:2000]}


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "list"
    if mode == "list":
        tools = call("tools/list").get("result", {}).get("tools", [])
        for t in tools:
            print(t.get("name"), "|", (t.get("description") or "")[:160].replace("\n", " "))
        print("COUNT", len(tools))
    elif mode == "tool":
        name = sys.argv[2]
        args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        print(json.dumps(call("tools/call", {"name": name, "arguments": args}), indent=2)[:12000])
