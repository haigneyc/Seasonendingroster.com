#!/usr/bin/env python3
"""
metrics.py
Consumes processed CSVs (from transform.py) and produces:
- site_data/champions.json
- site_data/runnerups.json
- site_data/all_time.json
- site_data/records.json
Also writes CSV mirrors in reports/csv/ for sanity checking.

Run after transform.py:
    python scripts/metrics.py
"""

from pathlib import Path
import json
import pandas as pd
import math

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
SITE_DATA = ROOT / "site_data"
REPORTS_CSV = ROOT / "reports" / "csv"

SITE_DATA.mkdir(parents=True, exist_ok=True)
REPORTS_CSV.mkdir(parents=True, exist_ok=True)

def write_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2))

def write_csv(path: Path, df: pd.DataFrame):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)

def load_processed():
    st = pd.read_csv(PROCESSED / "standings_by_season.csv")
    # Optional: these may not exist for very old pulls
    mu = None
    p_matchups = PROCESSED / "matchups.csv"
    if p_matchups.exists():
        mu = pd.read_csv(p_matchups)
    return st, mu

def compute_champions_and_runnerups(standings: pd.DataFrame):
    champs = (
        standings[standings["rank"] == 1]
        .sort_values(["season", "team_name"])
        [["season","team_name","manager"]]
        .reset_index(drop=True)
    )
    runnerups = (
        standings[standings["rank"] == 2]
        .sort_values(["season", "team_name"])
        [["season","team_name","manager"]]
        .reset_index(drop=True)
    )
    return champs, runnerups

def compute_all_time(standings: pd.DataFrame):
    # Aggregate per team across seasons
    agg = (
        standings.groupby(["team_name","manager"], dropna=False)
        .agg(
            seasons=("season","nunique"),
            wins=("wins","sum"),
            losses=("losses","sum"),
            ties=("ties","sum"),
            pf=("points_for","sum"),
            pa=("points_against","sum"),
            titles=("rank", lambda s: int((s == 1).sum()))
        )
        .reset_index()
    )
    agg["games"] = agg["wins"] + agg["losses"] + agg["ties"]
    agg["win_pct"] = agg.apply(
        lambda r: (r["wins"] + 0.5*r["ties"]) / r["games"] if r["games"] > 0 else 0.0,
        axis=1
    )
    # Round a bit for pretty JSON/CSV
    agg["pf"] = agg["pf"].round(2)
    agg["pa"] = agg["pa"].round(2)
    agg["win_pct"] = (agg["win_pct"]*100).round(2)
    # Sort: titles desc, win% desc, pf desc
    agg = agg.sort_values(["titles","win_pct","pf"], ascending=[False, False, False]).reset_index(drop=True)
    return agg

def compute_records(matchups: pd.DataFrame | None):
    if matchups is None or matchups.empty:
        return {
            "single_week_high": None,
            "single_week_margin": None,
            "longest_win_streak": None
        }
    # Highest single-week points
    m = matchups.sort_values("pts_for", ascending=False).iloc[0]
    single_week_high = {
        "season": int(m["season"]),
        "week": int(m["week"]),
        "team_name": str(m["team_name"]),
        "points": float(m["pts_for"])
    }

    # Largest margin (pts_for - pts_against), per row is already team perspective
    matchups = matchups.copy()
    matchups["margin"] = matchups["pts_for"] - matchups["pts_against"]
    mm = matchups.sort_values("margin", ascending=False).iloc[0]
    single_week_margin = {
        "season": int(mm["season"]),
        "week": int(mm["week"]),
        "team_name": str(mm["team_name"]),
        "opp_name": str(mm["opp_name"]),
        "margin": float(mm["margin"]),
        "pts_for": float(mm["pts_for"]),
        "pts_against": float(mm["pts_against"]),
    }

    # Longest win streak per team (quick pass: compute W/L per row then scan)
    def result_row(row):
        if math.isclose(row["pts_for"], row["pts_against"]):
            return "T"
        return "W" if row["pts_for"] > row["pts_against"] else "L"

    matchups["result"] = matchups.apply(result_row, axis=1)
    streak_rows = []
    for team, df in matchups.sort_values(["season","week"]).groupby("team_name"):
        current = best = 0
        best_season_week = None
        for _, r in df.iterrows():
            if r["result"] == "W":
                current += 1
                if current > best:
                    best = current
                    best_season_week = (int(r["season"]), int(r["week"]))
            else:
                current = 0
        streak_rows.append({"team_name": team, "longest_win_streak": best,
                            "season": best_season_week[0] if best_season_week else None,
                            "week": best_season_week[1] if best_season_week else None})
    streaks = pd.DataFrame(streak_rows).sort_values(["longest_win_streak","team_name"], ascending=[False, True])
    longest = None if streaks.empty else streaks.iloc[0].to_dict()

    return {
        "single_week_high": single_week_high,
        "single_week_margin": single_week_margin,
        "longest_win_streak": longest
    }

def main():
    standings, matchups = load_processed()

    champs_df, runners_df = compute_champions_and_runnerups(standings)
    all_time_df = compute_all_time(standings)
    records_obj = compute_records(matchups)

    # Write JSON for the website
    write_json(SITE_DATA / "champions.json", champs_df.to_dict(orient="records"))
    write_json(SITE_DATA / "runnerups.json", runners_df.to_dict(orient="records"))
    write_json(SITE_DATA / "all_time.json", all_time_df.to_dict(orient="records"))
    write_json(SITE_DATA / "records.json", records_obj)

    # CSV mirrors (handy for debugging)
    write_csv(REPORTS_CSV / "champions.csv", champs_df)
    write_csv(REPORTS_CSV / "runnerups.csv", runners_df)
    write_csv(REPORTS_CSV / "all_time.csv", all_time_df)

    print("✅ Wrote site_data/*.json and reports/csv/*.csv")

if __name__ == "__main__":
    main()