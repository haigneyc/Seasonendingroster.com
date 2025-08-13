#!/usr/bin/env python3
"""
refresh_token.py
Refresh Yahoo OAuth2 access token using the refresh_token from token.json.
"""

import base64
import json
import sys
from pathlib import Path
import requests

TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"

cfg_path = Path("oauth2.json")
tok_path = Path("token.json")

if not cfg_path.exists():
    sys.exit("❌ Missing oauth2.json")
if not tok_path.exists():
    sys.exit("❌ Missing token.json – run yahoo_auth_cli.py first.")

cfg = json.loads(cfg_path.read_text())
tok = json.loads(tok_path.read_text())

CLIENT_ID = cfg["client_id"]
CLIENT_SECRET = cfg["client_secret"]
REDIRECT_URI = cfg["redirect_uri"]

if "refresh_token" not in tok:
    sys.exit("❌ No refresh_token found in token.json. Run yahoo_auth_cli.py again.")

def b64_basic_auth(client_id, client_secret):
    raw = f"{client_id}:{client_secret}".encode()
    return base64.b64encode(raw).decode()

headers = {
    "Authorization": f"Basic {b64_basic_auth(CLIENT_ID, CLIENT_SECRET)}",
    "Content-Type": "application/x-www-form-urlencoded",
}

data = {
    "grant_type": "refresh_token",
    "redirect_uri": REDIRECT_URI,
    "refresh_token": tok["refresh_token"],
}

print("🔄 Refreshing token...")
r = requests.post(TOKEN_URL, headers=headers, data=data, timeout=30)
r.raise_for_status()

new_tok = r.json()
# Merge new access token info into existing token.json
tok.update(new_tok)

tok_path.write_text(json.dumps(tok, indent=2))
print("✅ Token refreshed and saved to token.json")
print("New access token (truncated):", tok.get("access_token", "")[:12], "…")