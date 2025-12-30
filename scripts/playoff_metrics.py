#!/usr/bin/env python3
"""
playoff_metrics.py
Generate playoff_metrics.json from standings and matchups data.
Uses franchise owner mapping to normalize manager names.
"""

import json
import pandas as pd
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

# Franchise owner mapping (Yahoo nickname -> canonical owner)
# This maps various Yahoo display names to the consistent franchise owner
OWNER_MAP = {
    # winter's team
    "Kurt Russel": "winter",
    "kurt russel": "winter",
    # Add other mappings as needed
    "five1three": "altman",
    "Ian Lane": "ian",
    "John Condon": "johnny",
    "Goat": "slater",
    "Matt": "matty",  # Note: both matty and vern have "Matt" - need team context
    "michael": "ml",
    "Koroco": "sterbank",
    "peterO": "ott",
    "hags": "haigney",
    "Joshua": "kratz",
}

# Team name to owner mapping for disambiguation
TEAM_OWNER_MAP = {
    # winter
    "The RDCs": "winter",
    "Rancid Douche Cunts": "winter",
    "Rancid Dead Corpses": "winter",
    # vern
    "the stunods": "vern",
    "Los_ticos": "vern",
    "the_isotopes": "vern",
    # matty
    "Food Bag": "matty",
    "The Sound Machines": "matty",
    "SBU": "matty",
    "Team Snake Juice": "matty",
    "The Daniel Tigers": "matty",
    "Leave It Matty": "matty",
    "We Got Worms": "matty",
    # slater
    "Don't Rock The Goat": "slater",
    "Don\u2019t Rock The Goat": "slater",
    "Dont Rock The Goat": "slater",
    "Goat": "slater",
    # johnny
    "The Assbags": "johnny",
    "Assbags": "johnny",
    "Btch McFcky Pants": "johnny",
    # altman
    "Dick$hinersConnivers": "altman",
    "DickShinersConnivers": "altman",
    "The Connivers": "altman",
    "Connive Me Maybe": "altman",
    "ConnivingCamJammers": "altman",
    "2CockConnivers": "altman",
    "Conniving Crentists": "altman",
    "Khaleesi's Connivers": "altman",
    "Ten and Under": "altman",
    "The Regressing IdiOTTs.": "altman",
    # ott
    "Ottoman Empire": "ott",
    "#1Stunners": "ott",
    "99 Problems": "ott",
    "Cunning Stunts": "ott",
    "Kiss my cock": "ott",
    "Peter Gunz": "ott",
    "TKOSpikes": "ott",
    "Urban Ottfitters": "ott",
    "Yellow Fever": "ott",
    # haigney
    "The Horsemasters": "haigney",
    "Hags House of Whores": "haigney",
    "Hags of Hagglestick": "haigney",
    "KAAAAEEEDDINNGGGGGGG": "haigney",
    "The Glue Factory": "haigney",
    # ian
    "The Future Kings of Trash": "ian",
    "Grunting Grundles": "ian",
    "BonerLoaf Cunt Pasta": "ian",
    "BonerLoafCuntPasta": "ian",
    "ButtLordsOfCamillus": "ian",
    "DancinOnTheThielen": "ian",
    "LA BrucesOf Endicott": "ian",
    "StankinAssButtLords": "ian",
    "Stone Cold Steve Austin Ekeler": "ian",
    "TakeMeToTheHospital": "ian",
    "The Unclean Spleens": "ian",
    # sterbank
    "The Mustard Museum": "sterbank",
    "KoroCompany": "sterbank",
    "Slack Jaw`d Redman": "sterbank",
    "Slack-Jaw'd Redman": "sterbank",
    "Slack-Jaw\u2019d Redman": "sterbank",
    "This is fine": "sterbank",
    # kratz
    "howthewesTWOn": "kratz",
    "HowTheWestWillWin": "kratz",
    "HowTheWestWon": "kratz",
    # ml
    "I'll See You Later Walker": "ml",
    "I\u2019ll See You Later Walker": "ml",
    "Reginald (vel) Johnson Harvey": "ml",
    "Dollar Store Les Snead": "ml",
    "Banana Slamma!!": "ml",
    "King Henry MFers": "ml",
    "La Vida Locas": "ml",
    "MatsuisHouseofPorn": "ml",
    "Russellhustle&bustle": "ml",
    "The Non-Factors": "ml",
    "Trust the Process": "ml",
    # trendo
    "Dr. Dartmaster": "trendo",
    "Drinkin' in the Yard": "trendo",
    "Professor Keystone": "trendo",
    "The Dartmaster": "trendo",
    # z
    "Desparados": "z",
    "Desperados": "z",
    "Future Kings of Odds": "z",
    "I'veGotPO": "z",
    "Luck Is Mine": "z",
    "Once & Future Kings": "z",
    "Outlaws": "z",
    "Wizard of Odds": "z",
}


def normalize_owner(manager: str, team_name: str = None) -> str:
    """Normalize manager name to canonical franchise owner."""
    if pd.isna(manager):
        manager = ""
    manager = str(manager).strip()

    # First try team name mapping (most reliable)
    if team_name and team_name in TEAM_OWNER_MAP:
        return TEAM_OWNER_MAP[team_name]

    # Then try direct owner mapping
    if manager in OWNER_MAP:
        return OWNER_MAP[manager]

    # Otherwise return lowercase version
    return manager.lower() if manager else "unknown"


def get_championship_bracket_max_seed(num_teams: int) -> int:
    """Return max seed for championship bracket based on league size.

    - 10-team leagues (2004-2007): 4-team championship bracket (seeds 1-4)
    - 12-team leagues (2008+): 6-team championship bracket (seeds 1-6)
    """
    return 4 if num_teams <= 10 else 6


def get_playoff_weeks(season: int, num_teams: int) -> tuple:
    """Return (playoff_start_week, playoff_end_week) for a season.

    The NFL final week is excluded from fantasy playoffs:
    - Pre-2021: NFL week 17 is excluded, playoffs end week 16
    - 2021+: NFL week 18 is excluded, playoffs end week 17

    Playoff duration:
    - 4-team brackets (≤10 teams): 2 weeks
    - 6-team brackets (>10 teams): 3 weeks (except 2008 which used 2 weeks)
    """
    # Championship week (last week before NFL final week)
    playoff_end = 17 if season >= 2021 else 16

    # Number of playoff weeks
    if num_teams <= 10:
        num_playoff_weeks = 2  # 4-team bracket
    elif season == 2008:
        num_playoff_weeks = 2  # 2008 used 2-week playoffs despite 12 teams
    else:
        num_playoff_weeks = 3  # 6-team bracket

    playoff_start = playoff_end - num_playoff_weeks + 1
    return playoff_start, playoff_end


def main():
    standings = pd.read_csv(OUT_DIR / "standings_by_season.csv")
    matchups = pd.read_csv(OUT_DIR / "matchups.csv")

    # Add normalized owner to standings
    standings["franchise_owner"] = standings.apply(
        lambda r: normalize_owner(r.get("manager", ""), r.get("team_name", "")), axis=1
    )

    # Add normalized owner to matchups
    matchups["franchise_owner"] = matchups.apply(
        lambda r: normalize_owner("", r.get("team_name", "")), axis=1
    )

    # Build seed lookup: (season, team_name) -> playoff_seed
    seed_lookup = {}
    for _, r in standings.iterrows():
        if pd.notna(r["playoff_seed"]):
            seed_lookup[(r["season"], r["team_name"])] = int(r["playoff_seed"])

    # Add seeds to matchups
    matchups["my_seed"] = matchups.apply(
        lambda r: seed_lookup.get((r["season"], r["team_name"])), axis=1
    )
    matchups["opp_seed"] = matchups.apply(
        lambda r: seed_lookup.get((r["season"], r["opp_name"])), axis=1
    )

    # Filter to CHAMPIONSHIP BRACKET ONLY (exclude consolation bracket)
    # Championship bracket: seeds 1-4 for 10-team leagues, seeds 1-6 for 12-team leagues
    # Also filter to playoff weeks only (based on is_playoffs flag or inferred from week number)
    playoff_rows = []
    champions_by_season = {}

    for season in matchups["season"].unique():
        season_matchups = matchups[matchups["season"] == season]
        num_teams = len(standings[standings["season"] == season])
        max_champ_seed = get_championship_bracket_max_seed(num_teams)

        # Determine playoff weeks based on season and league size
        playoff_start, playoff_end = get_playoff_weeks(int(season), num_teams)

        # Championship bracket games: BOTH teams must be in the championship bracket
        # and within playoff weeks
        champ_bracket_games = season_matchups[
            (season_matchups["week"] >= playoff_start) &
            (season_matchups["week"] <= playoff_end) &
            (season_matchups["my_seed"].notna()) &
            (season_matchups["opp_seed"].notna()) &
            (season_matchups["my_seed"] <= max_champ_seed) &
            (season_matchups["opp_seed"] <= max_champ_seed)
        ].copy()

        if len(champ_bracket_games) == 0:
            continue

        playoff_rows.append(champ_bracket_games)

        # Find champion: the team that went UNDEFEATED in the championship bracket
        team_stats = {}
        for _, game in champ_bracket_games.iterrows():
            team = game["team_name"]
            if team not in team_stats:
                team_stats[team] = {"wins": 0, "losses": 0, "seed": game["my_seed"]}
            if game["pts_for"] > game["pts_against"]:
                team_stats[team]["wins"] += 1
            elif game["pts_for"] < game["pts_against"]:
                team_stats[team]["losses"] += 1

        # Champion is the undefeated team (with most wins if multiple)
        undefeated = [(t, s) for t, s in team_stats.items() if s["losses"] == 0 and s["wins"] > 0]
        if undefeated:
            # Sort by wins descending
            undefeated.sort(key=lambda x: -x[1]["wins"])
            champ_team, champ_stats = undefeated[0]
            owner = normalize_owner("", champ_team)

            # Get rank from standings
            season_standings = standings[standings["season"] == season]
            team_standing = season_standings[season_standings["team_name"] == champ_team]
            rank = int(team_standing["rank"].iloc[0]) if len(team_standing) > 0 and pd.notna(team_standing["rank"].iloc[0]) else None

            champions_by_season[str(season)] = {
                "franchise_owner": owner,
                "team_name": champ_team,
                "seed": int(champ_stats["seed"]),
                "rank": rank
            }

    if not playoff_rows:
        print("No playoff data found")
        return

    playoffs = pd.concat(playoff_rows, ignore_index=True)

    # Compute per-owner playoff stats
    per_owner = []
    for owner in playoffs["franchise_owner"].unique():
        if not owner or owner == "unknown":
            continue

        owner_games = playoffs[playoffs["franchise_owner"] == owner]
        wins = len(owner_games[owner_games["pts_for"] > owner_games["pts_against"]])
        losses = len(owner_games[owner_games["pts_for"] < owner_games["pts_against"]])
        ties = len(owner_games[owner_games["pts_for"] == owner_games["pts_against"]])

        titles = [str(s) for s, c in champions_by_season.items() if c["franchise_owner"] == owner]

        # Get playoff appearances - only count championship bracket appearances
        owner_standings = standings[standings["franchise_owner"] == owner]
        appearances = 0
        champ_bracket_seeds = []
        for _, row in owner_standings.iterrows():
            if pd.notna(row["playoff_seed"]):
                season = row["season"]
                num_teams = len(standings[standings["season"] == season])
                max_champ_seed = get_championship_bracket_max_seed(num_teams)
                if row["playoff_seed"] <= max_champ_seed:
                    appearances += 1
                    champ_bracket_seeds.append(row["playoff_seed"])

        best_seed = int(min(champ_bracket_seeds)) if champ_bracket_seeds else None
        worst_seed = int(max(champ_bracket_seeds)) if champ_bracket_seeds else None

        total_games = wins + losses + ties
        per_owner.append({
            "franchise_owner": owner,
            "titles": len(titles),
            "titles_by_year": titles,
            "playoff_appearances": appearances,
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "points_for": round(owner_games["pts_for"].sum(), 2),
            "points_against": round(owner_games["pts_against"].sum(), 2),
            "best_seed": best_seed,
            "worst_seed": worst_seed,
            "win_pct": round(wins / total_games, 3) if total_games > 0 else 0,
            "avg_points_for_per_playoff_game": round(owner_games["pts_for"].mean(), 2) if total_games > 0 else None,
            "avg_points_against_per_playoff_game": round(owner_games["pts_against"].mean(), 2) if total_games > 0 else None,
        })

    # Sort by titles desc, then win_pct
    per_owner.sort(key=lambda x: (-x["titles"], -x["win_pct"]))

    result = {
        "source": {
            "standings": str(OUT_DIR / "standings_by_season.csv"),
            "matchups": str(OUT_DIR / "matchups.csv")
        },
        "counts": {
            "finishes_rows": len(standings),
            "franchises": len(per_owner),
            "seasons": len(champions_by_season),
            "playoff_games": len(playoffs) // 2,  # Each game counted twice, championship bracket only
            "note": "All playoff stats are CHAMPIONSHIP BRACKET ONLY (excludes consolation bracket)"
        },
        "champions_by_season": champions_by_season,
        "per_owner": per_owner
    }

    out_path = OUT_DIR / "playoff_metrics.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"✅ Wrote {out_path}")
    print(f"   Champions: {len(champions_by_season)} seasons")
    print(f"   2025 champion: {champions_by_season.get('2025', {}).get('franchise_owner', 'N/A')}")


if __name__ == "__main__":
    main()
