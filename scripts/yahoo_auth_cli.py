#!/usr/bin/env python3
"""
yahoo_auth_cli.py
Manual, copy-paste Yahoo OAuth2 flow.
- Prints login URL
- You log in, approve, get redirected to your registered redirect_uri
- Copy the full redirect URL back here
- Script parses the code, exchanges for tokens, saves token.json
"""

import base64
import json
import sys
import urllib.parse
from pathlib import Path

import requests

AUTH_URL = "https://api.login.yahoo.com/oauth2/request_auth"
TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"

# Load config
cfg_path = Path("oauth2.json")
if not cfg_path.exists():
    sys.exit("❌ Missing oauth2.json. Copy oauth2.example.json and fill in your keys.")

cfg = json.loads(cfg_path.read_text())
CLIENT_ID = cfg["client_id"]
CLIENT_SECRET = cfg["client_secret"]
REDIRECT_URI = cfg["redirect_uri"]
SCOPES = cfg.get("scopes", "fspt-r")

def b64_basic_auth(client_id, client_secret):
    raw = f"{client_id}:{client_secret}".encode()
    return base64.b64encode(raw).decode()

def build_auth_url():
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "state": "ser_csrf"  # simple CSRF check value
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

def exchange_code_for_tokens(code: str):
    headers = {
        "Authorization": f"Basic {b64_basic_auth(CLIENT_ID, CLIENT_SECRET)}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code,
    }
    r = requests.post(TOKEN_URL, headers=headers, data=data, timeout=30)
    r.raise_for_status()
    return r.json()

def save_tokens(tokens: dict):
    Path("token.json").write_text(json.dumps(tokens, indent=2))
    print("✅ Saved tokens to token.json")

def main():
    # Step 1: Direct user to login URL
    print("\n1) Open this URL in your browser, sign in, and approve access:\n")
    print(build_auth_url(), "\n")
    print("2) After Yahoo redirects you to your domain, COPY the full URL")
    print("   (e.g., https://seasonendingroster.com/oauth2callback?code=...&state=...)")

    # Step 2: Paste redirect URL
    pasted = input("\nPaste the FULL redirect URL here and press Enter:\n").strip()
    parsed = urllib.parse.urlparse(pasted)
    qs = urllib.parse.parse_qs(parsed.query)
    code = (qs.get("code") or [None])[0]
    state = (qs.get("state") or [None])[0]

    if not code:
        sys.exit("❌ Couldn't find ?code=... in the URL you pasted.")

    if state and state != "ser_csrf":
        print("⚠️  State mismatch; expected ser_csrf, got", state)

    # Step 3: Exchange code for tokens
    tokens = exchange_code_for_tokens(code)
    save_tokens(tokens)

    print("\nAccess token (short-lived):", tokens.get("access_token", "")[:12], "…")
    print("Refresh token:", "present" if "refresh_token" in tokens else "missing")
    print("\n✅ You can now run scripts that use token.json to call the Yahoo Fantasy API.")

if __name__ == "__main__":
    main()