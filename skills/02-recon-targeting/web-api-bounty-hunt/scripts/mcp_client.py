#!/usr/bin/env python3
"""MCP JSON-RPC client (Streamable HTTP, stateless, protocol 2025-06-18).

Endpoint via env NC_MCP_URL (e.g. https://host/mcp, or org-pinned https://host/mcp/o/<org>).
Token = OAuth access token from the MCP sign-in, NOT an org API token.

  NC_MCP_URL=https://host/mcp python mcp_client.py <token> initialize
  NC_MCP_URL=https://host/mcp python mcp_client.py <token> tools/list
  NC_MCP_URL=https://host/mcp python mcp_client.py <token> call <tool> '<json_args>'
  NC_MCP_URL=https://host/mcp python mcp_client.py <token> ping

Env NC_MCP_TOKEN overrides the argv token. A 401 on a fake token confirms the
harness reaches the live endpoint (smoke test before you hold a real token).
"""
import sys, os, json, urllib.request, urllib.error

URL = os.environ.get("NC_MCP_URL", "")
PROTO = os.environ.get("NC_MCP_PROTO", "2025-06-18")

def rpc(token, method, params=None, rid=1, url=None):
    url = url or URL
    if not url:
        raise SystemExit("set NC_MCP_URL")
    body = {"jsonrpc": "2.0", "id": rid, "method": method}
    if params is not None:
        body["params"] = params
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, dict(r.headers), r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode()

def pretty(raw):
    try:
        return json.dumps(json.loads(raw), indent=2, ensure_ascii=False)
    except Exception:
        return raw

def main():
    args = sys.argv[1:]
    token = os.environ.get("NC_MCP_TOKEN") or (args[0] if args else "")
    if not token:
        raise SystemExit("need token (argv[0] or NC_MCP_TOKEN)")
    rest = args[1:] if args else []
    cmd = rest[0] if rest else "initialize"
    if cmd == "initialize":
        s, h, raw = rpc(token, "initialize", {"protocolVersion": PROTO, "capabilities": {},
                        "clientInfo": {"name": "hermes-poc", "version": "0.1"}})
    elif cmd == "ping":
        s, h, raw = rpc(token, "ping", {})
    elif cmd == "tools/list":
        s, h, raw = rpc(token, "tools/list", {})
    elif cmd == "call":
        arguments = json.loads(rest[2]) if len(rest) > 2 else {}
        s, h, raw = rpc(token, "tools/call", {"name": rest[1], "arguments": arguments})
    else:
        raise SystemExit("unknown cmd: " + cmd)
    print("HTTP", s)
    print(pretty(raw))

if __name__ == "__main__":
    main()
