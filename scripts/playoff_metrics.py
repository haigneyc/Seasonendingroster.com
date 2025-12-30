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


def get_playoff_weeks(season: int) -> tuple:
    """Return playoff start week and championship week for a season."""
    # Standard: playoffs weeks 14-16, championship week 16
    # Some years may vary
    if season >= 2021:
        return 15, 17  # 17-game season era
    return 14, 16


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

    # Identify playoff games
    playoff_rows = []
    for season in matchups["season"].unique():
        playoff_start, champ_week = get_playoff_weeks(int(season))
        season_playoffs = matchups[
            (matchups["season"] == season) &
            (matchups["week"] >= playoff_start)
        ].copy()
        season_playoffs["is_championship"] = season_playoffs["week"] == champ_week
        playoff_rows.append(season_playoffs)

    if not playoff_rows:
        print("No playoff data found")
        return

    playoffs = pd.concat(playoff_rows, ignore_index=True)

    # Determine champions by tracking the playoff bracket
    # We need to identify the actual championship game, not just highest score
    champions_by_season = {}
    for season in playoffs["season"].unique():
        playoff_start, champ_week = get_playoff_weeks(int(season))

        # Get semi-final winners (week before championship)
        semi_week = champ_week - 1
        semi_winners = set()
        semi_games = playoffs[
            (playoffs["season"] == season) &
            (playoffs["week"] == semi_week) &
            (playoffs["pts_for"] > playoffs["pts_against"])
        ]
        for _, game in semi_games.iterrows():
            semi_winners.add(game["team_key"])

        # Championship game is between semi-final winners in championship week
        champ_week_games = playoffs[
            (playoffs["season"] == season) &
            (playoffs["week"] == champ_week) &
            (playoffs["pts_for"] > playoffs["pts_against"])
        ]

        # Find the game where winner was a semi-final winner playing another semi-final winner
        champ_game = None
        for _, game in champ_week_games.iterrows():
            if game["team_key"] in semi_winners and game["opp_key"] in semi_winners:
                champ_game = game
                break

        # Fallback: if no semi-final tracking works, use the winner who was also in semis
        if champ_game is None:
            for _, game in champ_week_games.iterrows():
                if game["team_key"] in semi_winners:
                    champ_game = game
                    break

        # Last fallback: highest scoring winner
        if champ_game is None and len(champ_week_games) > 0:
            champ_game = champ_week_games.loc[champ_week_games["pts_for"].idxmax()]

        if champ_game is not None:
            owner = normalize_owner("", champ_game["team_name"])

            # Get seed from standings
            season_standings = standings[standings["season"] == season]
            team_standing = season_standings[
                season_standings["team_name"] == champ_game["team_name"]
            ]
            seed = int(team_standing["playoff_seed"].iloc[0]) if len(team_standing) > 0 and pd.notna(team_standing["playoff_seed"].iloc[0]) else None
            rank = int(team_standing["rank"].iloc[0]) if len(team_standing) > 0 and pd.notna(team_standing["rank"].iloc[0]) else None

            champions_by_season[str(season)] = {
                "franchise_owner": owner,
                "team_name": champ_game["team_name"],
                "seed": seed,
                "rank": rank
            }

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

        # Get playoff appearances from standings (has playoff_seed)
        owner_standings = standings[standings["franchise_owner"] == owner]
        appearances = len(owner_standings[owner_standings["playoff_seed"].notna()])

        seeds = owner_standings[owner_standings["playoff_seed"].notna()]["playoff_seed"].dropna()
        best_seed = int(seeds.min()) if len(seeds) > 0 else None
        worst_seed = int(seeds.max()) if len(seeds) > 0 else None

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
            "playoff_games": len(playoffs) // 2  # Each game counted twice
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
