#!/usr/bin/env python3
"""
discover_league_keys.py
Given a bare LEAGUE_ID (e.g., "123456"), find all seasons and build full LEAGUE_KEY values.

Usage:
    export LEAGUE_ID="123456"
    python scripts/discover_league_keys.py
"""

import json
import os
import sys
from pathlib import Path
from yahoo_oauth import OAuth2
from yahoo_fantasy_api import yhandler

OUTFILE = Path(__file__).resolve().parent.parent / "data" / "raw" / "league_keys.json"

def auth():
    sc = OAuth2(None, None, from_file="oauth2.json")
    if not sc.token_is_valid():
        sc.refresh_access_token()
    return sc

def main():
    league_id = os.getenv("LEAGUE_ID", "").strip()
    if not league_id.isdigit():
        sys.exit("❌ LEAGUE_ID must be set to a numeric value in the environment.")

    sc = auth()
    yh = yhandler.YHandler(sc)

    # Find the most recent league key from the game list
    games = yh.get_user_games("nfl")
    current_league_key = None
    for g in games:
        if g.get("league_id") == league_id:
            current_league_key = g["league_key"]
            break

    if not current_league_key:
        sys.exit(f"❌ Could not find league {league_id} in your Yahoo account.")

    # Walk the renew chain
    all_keys = []
    key = current_league_key
    while key:
        if key in all_keys:
            break
        all_keys.append(key)
        meta = yh.get_league_metadata(key)
        key = meta.get("renew")  # may be None if oldest season

    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    OUTFILE.write_text(json.dumps({"league_id": league_id, "league_keys": all_keys}, indent=2))

    print(f"✅ Found {len(all_keys)} seasons. Saved to {OUTFILE}")
    for k in all_keys:
        print(" -", k)

if __name__ == "__main__":
    main()