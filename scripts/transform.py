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

def normalize_team_map(data):
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        return {
            t.get("team_key"): t
            for t in data
            if isinstance(t, dict) and t.get("team_key")
        }
    return {}


def get_manager_nickname(t: dict) -> str:
    """Extract manager nickname from team data (handles both old and new formats)."""
    managers = t.get("managers", [])
    if not managers:
        return ""
    mgr = managers[0]
    # New format: {"manager": {...}}
    if isinstance(mgr, dict) and "manager" in mgr:
        return mgr["manager"].get("nickname", "")
    # Old format: direct dict
    return mgr.get("nickname", "")


def transform_standings():
    rows = []
    for season_dir in sorted(RAW_DIR.iterdir()):
        if not season_dir.is_dir():
            continue
        settings_p = season_dir / "settings.json"
        standings_p = season_dir / "standings.json"
        teams_p = season_dir / "teams.json"
        if not (settings_p.exists() and standings_p.exists()):
            continue

        season = load_json(settings_p)["season"]
        standings_list = load_json(standings_p)

        # Handle both list and dict formats
        if isinstance(standings_list, dict):
            standings_list = [
                v for v in standings_list.values() if isinstance(v, dict)
            ]

        # Load team manager info from teams.json if available
        team_managers = {}
        if teams_p.exists():
            teams_data = normalize_team_map(load_json(teams_p))
            for team_key, team_info in teams_data.items():
                team_managers[team_key] = get_manager_nickname(team_info)

        for t in standings_list:
            try:
                # New format: outcome_totals at top level
                if "outcome_totals" in t:
                    ot = t["outcome_totals"]
                    team_key = t["team_key"]
                    rows.append({
                        "season": season,
                        "team_key": team_key,
                        "team_name": t["name"],
                        "manager": team_managers.get(team_key, get_manager_nickname(t)),
                        "rank": int(t.get("rank", 0)) if t.get("rank") else None,
                        "playoff_seed": t.get("playoff_seed"),
                        "wins": int(ot.get("wins", 0)),
                        "losses": int(ot.get("losses", 0)),
                        "ties": int(ot.get("ties", 0)),
                        "pct": float(ot.get("percentage", 0)),
                        "streak_type": t.get("streak", {}).get("type"),
                        "streak_value": t.get("streak", {}).get("value"),
                        "points_for": float(t.get("points_for", 0)),
                        "points_against": float(t.get("points_against", 0)),
                    })
                # Old format: nested standings
                elif "standings" in t:
                    st = t["standings"]
                    ot = st["outcome_totals"]
                    rows.append({
                        "season": season,
                        "team_key": t["team_key"],
                        "team_name": t["name"],
                        "manager": get_manager_nickname(t),
                        "rank": int(st.get("rank", 0)),
                        "playoff_seed": t.get("playoff_seed"),
                        "wins": int(ot.get("wins", 0)),
                        "losses": int(ot.get("losses", 0)),
                        "ties": int(ot.get("ties", 0)),
                        "pct": float(ot.get("percentage", 0)),
                        "streak_type": st.get("streak", {}).get("type"),
                        "streak_value": st.get("streak", {}).get("value"),
                        "points_for": float(t.get("team_points", {}).get("total", 0)),
                        "points_against": float(t.get("team_points_against", {}).get("total", 0)),
                    })
            except Exception as e:
                print(f"⚠️ Skipping team in {season}: {e}")
                continue

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows).sort_values(["season", "rank"])
    df.to_csv(OUT_DIR / "standings_by_season.csv", index=False)
    print(f"✅ Wrote {OUT_DIR / 'standings_by_season.csv'} ({len(df)} rows)")


def parse_team_from_nested(team_data: list) -> dict:
    """Parse team data from nested list-of-dicts format to flat dict."""
    result = {}
    for item in team_data:
        if isinstance(item, dict):
            result.update(item)
        elif isinstance(item, list):
            for subitem in item:
                if isinstance(subitem, dict):
                    result.update(subitem)
    return result


def get_scoreboard(league):
    if isinstance(league, dict):
        return league.get("scoreboard")
    if isinstance(league, list):
        for item in league:
            if isinstance(item, dict) and "scoreboard" in item:
                return item["scoreboard"]
    return None


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
        wk_data = load_json(matchups_p)

        for wk_str, week_content in wk_data.items():
            week = int(wk_str)

            # Navigate the nested API structure
            try:
                if isinstance(week_content, dict) and "fantasy_content" in week_content:
                    fc = week_content["fantasy_content"]
                    league = fc["league"]
                    scoreboard = get_scoreboard(league)
                    if not scoreboard:
                        continue

                    # Iterate through matchups (keys are "0", "1", etc.)
                    matchup_idx = 0
                    while str(matchup_idx) in scoreboard:
                        matchups_container = scoreboard[str(matchup_idx)].get("matchups", {})

                        # Iterate through each matchup
                        m_idx = 0
                        while str(m_idx) in matchups_container:
                            matchup = matchups_container[str(m_idx)].get("matchup", {})

                            # Get teams from matchup
                            teams_container = matchup.get("teams")
                            if teams_container is None:
                                teams_container = matchup.get("0", {}).get("teams", {})
                            team_list = []
                            t_idx = 0
                            while str(t_idx) in teams_container:
                                team_raw = teams_container[str(t_idx)].get("team", [])
                                team_data = parse_team_from_nested(team_raw)
                                # Get points
                                team_points = team_data.get("team_points", {})
                                pts = float(team_points.get("total", 0)) if team_points else 0
                                team_list.append({
                                    "team_key": team_data.get("team_key", ""),
                                    "name": team_data.get("name", ""),
                                    "points": pts,
                                })
                                t_idx += 1

                            if len(team_list) == 2:
                                t1, t2 = team_list
                                rows.append({
                                    "season": season,
                                    "week": week,
                                    "team_key": t1["team_key"],
                                    "team_name": t1["name"],
                                    "opp_key": t2["team_key"],
                                    "opp_name": t2["name"],
                                    "pts_for": t1["points"],
                                    "pts_against": t2["points"],
                                })
                                rows.append({
                                    "season": season,
                                    "week": week,
                                    "team_key": t2["team_key"],
                                    "team_name": t2["name"],
                                    "opp_key": t1["team_key"],
                                    "opp_name": t1["name"],
                                    "pts_for": t2["points"],
                                    "pts_against": t1["points"],
                                })
                            m_idx += 1
                        matchup_idx += 1

                # Old format: list of matchups
                elif isinstance(week_content, list):
                    for g in week_content:
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
                            })
                        except Exception:
                            continue
            except Exception as e:
                print(f"⚠️ Error processing week {week} in {season}: {e}")
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
