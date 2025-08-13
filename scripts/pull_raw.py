#!/usr/bin/env python3
"""
pull_raw.py
Pulls raw Yahoo Fantasy Football league data for all seasons in the league's renew chain.
Requires: token.json (from yahoo_auth_cli.py), oauth2.json (for client_id/secret/redirect_uri)
"""

import json
import time
from pathlib import Path
from yahoo_oauth import OAuth2
from yahoo_fantasy_api import yhandler, league as yleague

# ---------- CONFIG ----------
CURRENT_LEAGUE_KEY = "nfl.l.12345"  # <-- replace with your current league key
OUTDIR = Path(__file__).resolve().parent.parent / "data" / "raw"
SLEEP = 0.3  # seconds between API calls to avoid rate limits
# ----------------------------

def load_oauth():
    """Load OAuth2 credentials & return an authenticated session."""
    sc = OAuth2(None, None, from_file="oauth2.json", access_token=None)
    if not sc.token_is_valid():
        sc.refresh_access_token()
    return sc

def discover_all_league_keys(yh, start_key):
    """Follow the renew chain backward to get all seasons for the league."""
    keys = []
    key = start_key
    seen = set()
    while key and key not in seen:
        seen.add(key)
        meta = yh.get_league_metadata(key)
        keys.append(key)
        key = meta.get("renew")  # older season
    return keys

def pull_league_data(sc, league_key):
    """Pull standings, matchups, and draft results for a single season."""
    lg = yleague.League(sc, league_key)
    settings = lg.settings()
    season = settings["season"]

    season_dir = OUTDIR / season
    season_dir.mkdir(parents=True, exist_ok=True)

    # Save settings/metadata
    (season_dir / "settings.json").write_text(json.dumps(settings, indent=2))

    # Standings
    standings = lg.standings()
    (season_dir / "standings.json").write_text(json.dumps(standings, indent=2))

    # Matchups (weeks 1..final)
    matchups_all = {}
    for week in range(1, settings["end_week"] + 1):
        matchups_all[week] = lg.matchups(week)
        time.sleep(SLEEP)
    (season_dir / "matchups.json").write_text(json.dumps(matchups_all, indent=2))

    # Draft results (may be empty for no-draft years)
    try:
        draft = lg.draft_results()
    except Exception as e:
        draft = {"error": str(e)}
    (season_dir / "draft.json").write_text(json.dumps(draft, indent=2))

    print(f"✅ Saved season {season} to {season_dir}")

def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)

    sc = load_oauth()
    yh = yhandler.YHandler(sc)

    all_keys = discover_all_league_keys(yh, CURRENT_LEAGUE_KEY)
    print(f"Found {len(all_keys)} seasons: {all_keys}")

    for key in all_keys:
        try:
            pull_league_data(sc, key)
            time.sleep(SLEEP)
        except Exception as e:
            print(f"❌ Error pulling {key}: {e}")

if __name__ == "__main__":
    main()