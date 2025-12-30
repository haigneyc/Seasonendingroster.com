#!/usr/bin/env python3
"""
pull_raw.py
Pull raw Yahoo Fantasy Football data for all seasons in a league's renew chain.
Outputs JSON to data/raw/{season}/ so we can build reports later without re-hitting the API.

Prereqs:
- oauth2.json (client_id, client_secret, redirect_uri, scopes)
- token.json   (created by yahoo_auth_cli.py)
- pip install yahoo-fantasy-api yahoo_oauth requests pandas (pandas used later)

Usage:
    python scripts/pull_raw.py
"""

import json
import time
from pathlib import Path

from yahoo_oauth import OAuth2
from yahoo_fantasy_api import yhandler, league as yleague

# ---------- CONFIG ----------
import os
CURRENT_LEAGUE_KEY = os.getenv("LEAGUE_KEY", "449.l.47540")  # 2024 season full key
OUTDIR = Path(__file__).resolve().parent.parent / "data" / "raw"
SLEEP = 0.3  # seconds between API calls (be nice to the API)
# ----------------------------

def auth():
    sc = OAuth2(None, None, from_file="oauth2.json")
    if not sc.token_is_valid():
        sc.refresh_access_token()
    return sc

def discover_league_keys(sc, start_key: str) -> list[str]:
    """
    Follow the league 'renew' chain to previous seasons.
    Returns keys newest -> oldest.
    """
    keys, seen = [], set()
    key = start_key
    while key and key not in seen:
        seen.add(key)
        keys.append(key)
        try:
            lg = yleague.League(sc, key)
            settings = lg.settings()
            renew = settings.get("renew")  # format: "423_34101"
            if renew:
                # Convert "423_34101" to "423.l.34101"
                parts = renew.split("_")
                key = f"{parts[0]}.l.{parts[1]}" if len(parts) == 2 else None
            else:
                key = None
        except Exception as e:
            print(f"⚠️ Could not get settings for {key}: {e}")
            key = None
        time.sleep(SLEEP)
    return keys

def safe_write(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2))

def pull_one_season(sc, league_key: str):
    lg = yleague.League(sc, league_key)
    settings = lg.settings()
    season = settings["season"]
    season_dir = OUTDIR / season
    season_dir.mkdir(parents=True, exist_ok=True)

    # 1) Settings / metadata
    safe_write(season_dir / "settings.json", settings)

    # 2) Standings (teams, ranks, PF/PA)
    standings = lg.standings()
    safe_write(season_dir / "standings.json", standings)

    # 3) Matchups (week-by-week)
    matchups_all = {}
    for wk in range(1, int(settings["end_week"]) + 1):
        matchups_all[wk] = lg.matchups(wk)
        time.sleep(SLEEP)
    safe_write(season_dir / "matchups.json", matchups_all)

    # 4) Draft results (if any)
    try:
        draft = lg.draft_results()
    except Exception as e:
        draft = {"error": str(e)}
    safe_write(season_dir / "draft.json", draft)

    # 5) Teams (with manager info)
    teams = lg.teams()
    safe_write(season_dir / "teams.json", teams)

    # 6) Rosters (per team) - may fail on some API versions
    rosters = {}
    for team_key, t in teams.items():
        try:
            rosters[team_key] = lg.roster(team_key=team_key)
        except Exception as e:
            rosters[team_key] = {"error": str(e)}
        time.sleep(SLEEP)
    safe_write(season_dir / "rosters.json", rosters)

    # 7) Optional: transactions (trades, adds/drops)
    try:
        # yahoo-fantasy-api exposes transactions via freeform handler; some seasons may vary
        yh = yhandler.YHandler(sc)
        transactions = yh.get_league_transactions(league_key)
    except Exception as e:
        transactions = {"error": str(e)}
    safe_write(season_dir / "transactions.json", transactions)

    print(f"✅ Saved season {season} → {season_dir}")

def main():
    sc = auth()

    all_keys = discover_league_keys(sc, CURRENT_LEAGUE_KEY)
    print(f"Found {len(all_keys)} seasons: {all_keys}")

    for key in all_keys:
        try:
            pull_one_season(sc, key)
            time.sleep(SLEEP)
        except Exception as e:
            print(f"❌ Error pulling {key}: {e}")

if __name__ == "__main__":
    main()