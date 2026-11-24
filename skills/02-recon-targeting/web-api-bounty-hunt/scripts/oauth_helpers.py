#!/usr/bin/env python3
"""OAuth helpers for an MCP / authorization-code + PKCE flow (shim over a core issuer).

Hosts via env (no hardcoded target):
  NC_AUTHORIZE  shim/core authorize URL   (e.g. https://auth.host/application/o/authorize/)
  NC_TOKEN      token endpoint            (e.g. https://auth.host/application/o/token/)
  NC_TOKEN_ALT  alternate token endpoint to try on redeem (e.g. core /oauth2/token)
  NC_DEVICE     device authorization endpoint
  NC_REDIRECT   loopback callback         (default http://127.0.0.1:33418/callback)
  NC_CLIENT     client_id                 (e.g. the public MCP client)
  NC_SCOPE     scope                      (default 'openid email profile groups offline_access')

Subcommands:
  pkce                     -> {verifier, challenge(S256), method}; SAVE the verifier
  url <verifier> [aud]     -> authorize URL; aud optional = audience-override test
  redeem <code> <verifier> -> POST token endpoint(s), print token JSON
  refresh <refresh_token>  -> refresh access token
  device                   -> initiate device code, print JSON
  devicepoll <device_code> -> poll token endpoint once

Browser steps (sign-in + consent) are driven separately via browser_exec; the
loopback redirect fails to load but location.href carries ?code=... -> redeem here.
"""
import sys, os, json, secrets, hashlib, base64, urllib.request, urllib.parse, urllib.error

AUTHORIZE = os.environ.get("NC_AUTHORIZE", "")
TOKEN = os.environ.get("NC_TOKEN", "")
TOKEN_ALT = os.environ.get("NC_TOKEN_ALT", "")
DEVICE = os.environ.get("NC_DEVICE", "")
REDIRECT = os.environ.get("NC_REDIRECT", "http://127.0.0.1:33418/callback")
CLIENT = os.environ.get("NC_CLIENT", "")
SCOPE = os.environ.get("NC_SCOPE", "openid email profile groups offline_access")
DEVICE_GRANT = "urn:ietf:params:oauth:grant-type:device_code"

def b64url(b):
    return base64.urlsafe_b64encode(b).decode().rstrip("=")

def challenge(v):
    return b64url(hashlib.sha256(v.encode()).digest())

def post(url, fields):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(fields).encode(), method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "pkce"
    if cmd == "pkce":
        v = secrets.token_urlsafe(48)[:64]
        print(json.dumps({"verifier": v, "challenge": challenge(v), "method": "S256"}))
    elif cmd == "url":
        v = sys.argv[2]
        q = {"response_type": "code", "client_id": CLIENT, "redirect_uri": REDIRECT,
             "scope": SCOPE, "state": secrets.token_urlsafe(12),
             "code_challenge": challenge(v), "code_challenge_method": "S256"}
        if len(sys.argv) > 3:
            q["audience"] = sys.argv[3]
        print(AUTHORIZE + "?" + urllib.parse.urlencode(q))
    elif cmd == "redeem":
        code, v = sys.argv[2], sys.argv[3]
        for ep in [e for e in (TOKEN, TOKEN_ALT) if e]:
            s, raw = post(ep, {"grant_type": "authorization_code", "code": code,
                               "client_id": CLIENT, "redirect_uri": REDIRECT, "code_verifier": v})
            print("endpoint:", ep, "HTTP", s); print(raw)
            if s == 200:
                break
    elif cmd == "refresh":
        s, raw = post(TOKEN, {"grant_type": "refresh_token", "refresh_token": sys.argv[2], "client_id": CLIENT})
        print("HTTP", s); print(raw)
    elif cmd == "device":
        s, raw = post(DEVICE, {"client_id": CLIENT, "scope": SCOPE})
        print("HTTP", s); print(raw)
    elif cmd == "devicepoll":
        s, raw = post(TOKEN_ALT or TOKEN, {"grant_type": DEVICE_GRANT, "device_code": sys.argv[2], "client_id": CLIENT})
        print("HTTP", s); print(raw)
    else:
        raise SystemExit("unknown cmd")

if __name__ == "__main__":
    main()
