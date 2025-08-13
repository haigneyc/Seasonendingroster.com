#!/usr/bin/env python3
"""
transform.py
Converts raw JSON (data/raw/{season}/...) into tidy CSVs in data/processed/.
- standings_by_season.csv
- matchups.csv

Run after pull_raw.py:
    python scripts/transform.py
"""

import json
from pathlib import Path
import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

def load_json(p: Path):
    return json.loads(p.read_text())

def transform_standings():
    rows = []
    for season_dir in sorted(RAW_DIR.iterdir()):
        if not season_dir.is_dir():
            continue
        settings_p = season_dir / "settings.json"
        standings_p = season_dir / "standings.json"
        if not (settings_p.exists() and standings_p.exists()):
            continue

        season = load_json(settings_p)["season"]
        teams = load_json(standings_p)
        for t in teams:
            rows.append({
                "season": season,
                "league_key": t.get("league_key", ""),  # may not be present
                "team_key": t["team_key"],
                "team_name": t["name"],
                "manager": (t.get("managers") or [{}])[0].get("nickname", ""),
                "wins": int(t["standings"]["outcome_totals"]["wins"]),
                "losses": int(t["standings"]["outcome_totals"]["losses"]),
                "ties": int(t["standings"]["outcome_totals"].get("ties", 0)),
                "rank": int(t["standings"]["rank"]),
                "points_for": float(t["team_points"]["total"]),
                "points_against": float(t["team_points_against"]["total"]),
            })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows).sort_values(["season", "rank"])
    df.to_csv(OUT_DIR / "standings_by_season.csv", index=False)
    print(f"✅ Wrote {OUT_DIR / 'standings_by_season.csv'} ({len(df)} rows)")

def transform_matchups():
    rows = []
    for season_dir in sorted(RAW_DIR.iterdir()):
        if not season_dir.is_dir():
            continue
        settings_p = season_dir / "settings.json"
        matchups_p = season_dir / "matchups.json"
        if not (settings_p.exists() and matchups_p.exists()):
            continue

        season = load_json(settings_p)["season"]
        wk_to_games = load_json(matchups_p)  # {week: [matchups]}
        for wk_str, games in wk_to_games.items():
            week = int(wk_str)
            # Each 'game' typically contains two teams and their points
            for g in games:
                try:
                    t1, t2 = g["teams"]
                    rows.append({
                        "season": season,
                        "week": week,
                        "team_key": t1["team_key"],
                        "team_name": t1["name"],
                        "opp_key": t2["team_key"],
                        "opp_name": t2["name"],
                        "pts_for": float(t1["team_points"]["total"]),
                        "pts_against": float(t2["team_points"]["total"]),
                        "is_home": t1.get("is_home", None),
                    })
                    rows.append({
                        "season": season,
                        "week": week,
                        "team_key": t2["team_key"],
                        "team_name": t2["name"],
                        "opp_key": t1["team_key"],
                        "opp_name": t1["name"],
                        "pts_for": float(t2["team_points"]["total"]),
                        "pts_against": float(t1["team_points"]["total"]),
                        "is_home": t2.get("is_home", None),
                    })
                except Exception:
                    # Some weeks or formats may differ; skip bad rows rather than crash
                    continue

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows).sort_values(["season", "week", "team_name"])
    df.to_csv(OUT_DIR / "matchups.csv", index=False)
    print(f"✅ Wrote {OUT_DIR / 'matchups.csv'} ({len(df)} rows)")

def main():
    transform_standings()
    transform_matchups()

if __name__ == "__main__":
    main()