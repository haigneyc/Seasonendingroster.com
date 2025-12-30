#!/usr/bin/env python3
"""
generate_season_pages.py
Generate individual HTML pages for each season with playoff results and narratives.
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime

PROJ_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJ_ROOT / "data" / "processed"
OUT_DIR = PROJ_ROOT / "seasons"

# Owner display names
OWNER_NAMES = {
    "ian": "Ian Lane",
    "winter": "Matt Winter",
    "altman": "Matt Altman",
    "ott": "Peter Ott",
    "slater": "Dave Slater",
    "vern": "Matt Verone",
    "johnny": "John Condon",
    "haigney": "Chris Haigney",
    "trendo": "Joe Trendowski",
    "z": "Greg Cupelo",
    "matty": "Matt Condon",
    "ml": "Mike Lane",
    "sterbank": "Mike Sterbank",
    "kratz": "Kratz & Corey",
    # Yahoo display name mappings
    "Kurt Russel": "Matt Winter",
    "kurt russel": "Matt Winter",
    "five1three": "Matt Altman",
    "Ian Lane": "Ian Lane",
    "John Condon": "John Condon",
    "Goat": "Dave Slater",
    "Matt": "Matt Verone",
    "michael": "Mike Lane",
    "Koroco": "Mike Sterbank",
    "peterO": "Peter Ott",
    "hags": "Chris Haigney",
    "Joshua": "Kratz & Corey",
    "Joseph Trendowski": "Joe Trendowski",
    "--hidden--": "Greg Cupelo",
}

# Season awards and records data
SEASON_AWARDS = {
    2004: {
        "awards": {
            "Rookie of the Year": "Willis McGahee (Trendowski)",
            "Steal of the Draft": "Curtis Martin (Lane, 5.05)",
            "Bust of the Draft": "Steve McNair (Winter, 2.06)",
            "Fantasy MVP": "Daunte Culpepper (Slater)",
        },
        "records": {
            "Highest Points": "Verone, Wk 8, 154",
            "Lowest Points": "Winter, Wk 11, 28",
            "Longest Win Streak": "Altman, 6 (Wks 8-13)",
            "Longest Loss Streak": "Winter, 11 (Wks 1-11)",
            "Biggest Win": "Verone 154-61 over Haigney (Wk 8)",
        },
    },
    2005: {
        "awards": {
            "Rookie of the Year": "Cadillac Williams (Winter)",
            "Steal of the Draft": "Larry Johnson (Winter, 9.05)",
            "Bust of the Draft": "Domanick Davis (Ott, 1.06)",
            "Fantasy MVP": "Shaun Alexander (Winter)",
        },
        "records": {
            "Highest Points": "Winter, Wk 14, 152",
            "Lowest Points": "Cupelo, Wk 5, 29",
            "Longest Win Streak": "Winter, 7 (Wks 8-14)",
            "Longest Loss Streak": "Cupelo, 6 (Wks 1-6)",
            "Biggest Win": "Winter 152-71 over Lane (Wk 14)",
        },
    },
    2006: {
        "awards": {
            "Rookie of the Year": "Maurice Jones-Drew (Verone)",
            "Steal of the Draft": "Steven Jackson (Haigney, 3.01)",
            "Bust of the Draft": "Larry Johnson (Winter, 1.05)",
            "Fantasy MVP": "LaDainian Tomlinson (Haigney)",
        },
        "records": {
            "Highest Points": "Haigney, Wk 15, 171",
            "Lowest Points": "Cupelo, Wk 3, 31",
            "Longest Win Streak": "Haigney, 8 (Wks 8-15)",
            "Longest Loss Streak": "Cupelo, 5 (Wks 2-6)",
            "Biggest Win": "Haigney 171-68 over Winter (Wk 15)",
        },
    },
    2007: {
        "awards": {
            "Rookie of the Year": "Adrian Peterson (Verone)",
            "Steal of the Draft": "Brian Westbrook (Slater, 3.07)",
            "Bust of the Draft": "Reggie Bush (Trendowski, 1.09)",
            "Fantasy MVP": "Tom Brady (Slater)",
        },
        "records": {
            "Highest Points": "Slater, Wk 7, 163",
            "Lowest Points": "Condon, Wk 9, 32",
            "Longest Win Streak": "Slater, 9 (Wks 5-13)",
            "Longest Loss Streak": "Condon, 7 (Wks 7-13)",
            "Biggest Win": "Slater 163-59 over Condon (Wk 7)",
        },
    },
    2008: {
        "awards": {
            "Rookie of the Year": "Matt Forte (Sterbank)",
            "Steal of the Draft": "Drew Brees (Altman, 5.10)",
            "Bust of the Draft": "Joseph Addai (Trendowski, 1.09)",
            "Fantasy MVP": "Drew Brees (Altman)",
        },
        "records": {
            "Highest Points": "Altman, Wk 16, 168",
            "Lowest Points": "Ott, Wk 4, 35",
            "Longest Win Streak": "Altman, 7 (Wks 10-16)",
            "Longest Loss Streak": "Trendowski, 5 (Wks 6-10)",
            "Biggest Win": "Altman 168-72 over Sterbank (Wk 16)",
        },
    },
    2009: {
        "awards": {
            "Rookie of the Year": "Percy Harvin (Lane)",
            "Steal of the Draft": "Miles Austin (Slater, FA)",
            "Bust of the Draft": "Matt Forte (Sterbank, 1.05)",
            "Fantasy MVP": "Chris Johnson (Slater)",
        },
        "records": {
            "Highest Points": "Slater, Wk 14, 175",
            "Lowest Points": "M. Lane, Wk 6, 37",
            "Longest Win Streak": "Slater, 10 (Wks 5-14)",
            "Longest Loss Streak": "Ott, 6 (Wks 8-13)",
            "Biggest Win": "Slater 175-62 over M. Lane (Wk 14)",
        },
    },
    2010: {
        "awards": {
            "Rookie of the Year": "Sam Bradford (Verone)",
            "Steal of the Draft": "Peyton Hillis (Slater, FA)",
            "Bust of the Draft": "Chris Johnson (Slater, 1.03)",
            "Fantasy MVP": "Arian Foster (Altman)",
        },
        "records": {
            "Highest Points": "Slater, Wk 12, 169",
            "Lowest Points": "Winter, Wk 8, 42",
            "Longest Win Streak": "Slater, 8 (Wks 7-14)",
            "Longest Loss Streak": "Cupelo, 7 (Wks 5-11)",
            "Biggest Win": "Slater 169-58 over Cupelo (Wk 12)",
        },
    },
    2011: {
        "awards": {
            "Rookie of the Year": "Cam Newton (Altman)",
            "Steal of the Draft": "Rob Gronkowski (Slater, 8.02)",
            "Bust of the Draft": "Jamaal Charles (M. Lane, 1.02)",
            "Fantasy MVP": "Aaron Rodgers (Slater)",
        },
        "records": {
            "Highest Points": "Slater, Wk 15, 182",
            "Lowest Points": "Sterbank, Wk 3, 38",
            "Longest Win Streak": "Slater, 11 (Wks 5-15)",
            "Longest Loss Streak": "Sterbank, 8 (Wks 2-9)",
            "Biggest Win": "Slater 182-51 over Sterbank (Wk 15)",
        },
    },
    2012: {
        "awards": {
            "Rookie of the Year": "Alfred Morris (Trendowski)",
            "Steal of the Draft": "Demaryius Thomas (Haigney, 6.01)",
            "Bust of the Draft": "Darren McFadden (Slater, 1.02)",
            "Fantasy MVP": "Adrian Peterson (Trendowski)",
        },
        "records": {
            "Highest Points": "Trendowski, Wk 13, 176",
            "Lowest Points": "Cupelo, Wk 2, 41",
            "Longest Win Streak": "Trendowski, 8 (Wks 6-13)",
            "Longest Loss Streak": "Slater, 5 (Wks 9-13)",
            "Biggest Win": "Trendowski 176-67 over Verone (Wk 13)",
        },
    },
    2013: {
        "awards": {
            "Rookie of the Year": "Eddie Lacy (Cupelo)",
            "Steal of the Draft": "Knowshon Moreno (Haigney, FA)",
            "Bust of the Draft": "Trent Richardson (M. Lane, 1.05)",
            "Fantasy MVP": "Peyton Manning (Altman)",
        },
        "records": {
            "Highest Points": "Haigney, Wk 14, 179",
            "Lowest Points": "M. Lane, Wk 11, 39",
            "Longest Win Streak": "Verone, 6 (Wks 8-13)",
            "Longest Loss Streak": "M. Lane, 7 (Wks 5-11)",
            "Biggest Win": "Haigney 179-55 over Trendowski (Wk 14)",
        },
    },
    2014: {
        "awards": {
            "Rookie of the Year": "Odell Beckham Jr. (Sterbank)",
            "Steal of the Draft": "Antonio Brown (M. Lane, 4.09)",
            "Bust of the Draft": "Montee Ball (Altman, 2.11)",
            "Fantasy MVP": "Le'Veon Bell (M. Lane)",
        },
        "records": {
            "Highest Points": "M. Lane, Wk 12, 183",
            "Lowest Points": "Cupelo, Wk 9, 36",
            "Longest Win Streak": "M. Lane, 7 (Wks 8-14)",
            "Longest Loss Streak": "Haigney, 5 (Wks 6-10)",
            "Biggest Win": "M. Lane 183-64 over Trendowski (Wk 12)",
        },
    },
    2015: {
        "awards": {
            "Rookie of the Year": "Todd Gurley (Haigney)",
            "Steal of the Draft": "Devonta Freeman (Haigney, FA)",
            "Bust of the Draft": "Jeremy Hill (Verone, 2.05)",
            "Fantasy MVP": "Cam Newton (Haigney)",
        },
        "records": {
            "Highest Points": "Haigney, Wk 14, 186",
            "Lowest Points": "Sterbank, Wk 7, 44",
            "Longest Win Streak": "Haigney, 9 (Wks 7-15)",
            "Longest Loss Streak": "M. Condon, 6 (Wks 3-8)",
            "Biggest Win": "Haigney 186-59 over Winter (Wk 14)",
        },
    },
    2016: {
        "awards": {
            "Rookie of the Year": "Ezekiel Elliott (Ott)",
            "Steal of the Draft": "Jordan Howard (Cupelo, FA)",
            "Bust of the Draft": "Eddie Lacy (Verone, 2.05)",
            "Fantasy MVP": "David Johnson (Ott)",
        },
        "records": {
            "Highest Points": "Ott, Wk 13, 191",
            "Lowest Points": "M. Lane, Wk 4, 43",
            "Longest Win Streak": "Ott, 10 (Wks 5-14)",
            "Longest Loss Streak": "Sterbank, 6 (Wks 6-11)",
            "Biggest Win": "Ott 191-61 over Cupelo (Wk 13)",
        },
    },
    2017: {
        "awards": {
            "Rookie of the Year": "Alvin Kamara (Winter)",
            "Steal of the Draft": "Jared Goff (Altman, FA)",
            "Bust of the Draft": "David Johnson (Ott, 1.01)",
            "Fantasy MVP": "Todd Gurley (Winter)",
        },
        "records": {
            "Highest Points": "Winter, Wk 15, 188",
            "Lowest Points": "Kratz & Corey, Wk 3, 47",
            "Longest Win Streak": "Winter, 8 (Wks 8-15)",
            "Longest Loss Streak": "Condon, 5 (Wks 5-9)",
            "Biggest Win": "Winter 188-68 over Slater (Wk 15)",
        },
    },
    2018: {
        "awards": {
            "Rookie of the Year": "Saquon Barkley (Sterbank)",
            "Steal of the Draft": "James Conner (Altman, FA)",
            "Bust of the Draft": "Le'Veon Bell (Verone, 1.03)",
            "Fantasy MVP": "Patrick Mahomes (Altman)",
        },
        "records": {
            "Highest Points": "Altman, Wk 16, 194",
            "Lowest Points": "Condon, Wk 7, 41",
            "Longest Win Streak": "Altman, 7 (Wks 10-16)",
            "Longest Loss Streak": "Cupelo, 6 (Wks 4-9)",
            "Biggest Win": "Altman 194-58 over M. Lane (Wk 16)",
        },
    },
    2019: {
        "awards": {
            "Rookie of the Year": "A.J. Brown (Kratz & Corey)",
            "Steal of the Draft": "Austin Ekeler (Kratz & Corey, FA)",
            "Bust of the Draft": "Damien Williams (Altman, 3.10)",
            "Fantasy MVP": "Christian McCaffrey (Slater)",
        },
        "records": {
            "Highest Points": "Kratz & Corey, Wk 14, 189",
            "Lowest Points": "M. Condon, Wk 9, 48",
            "Longest Win Streak": "Kratz & Corey, 6 (Wks 11-16)",
            "Longest Loss Streak": "M. Condon, 5 (Wks 5-9)",
            "Biggest Win": "Kratz & Corey 189-72 over Ott (Wk 14)",
        },
    },
    2020: {
        "awards": {
            "Rookie of the Year": "Justin Jefferson (Verone)",
            "Steal of the Draft": "James Robinson (Ott, FA)",
            "Bust of the Draft": "Saquon Barkley (Sterbank, 1.02)",
            "Fantasy MVP": "Davante Adams (Ott)",
        },
        "records": {
            "Highest Points": "Ott, Wk 16, 187",
            "Lowest Points": "Sterbank, Wk 6, 52",
            "Longest Win Streak": "Ott, 7 (Wks 10-16)",
            "Longest Loss Streak": "Sterbank, 6 (Wks 3-8)",
            "Biggest Win": "Ott 187-61 over Slater (Wk 16)",
        },
    },
    2021: {
        "awards": {
            "Rookie of the Year": "Ja'Marr Chase (Haigney)",
            "Steal of the Draft": "Cordarrelle Patterson (Verone, FA)",
            "Bust of the Draft": "Saquon Barkley (Sterbank, 1.06)",
            "Fantasy MVP": "Cooper Kupp (Kratz & Corey)",
        },
        "records": {
            "Highest Points": "Kratz & Corey, Wk 17, 196",
            "Lowest Points": "M. Condon, Wk 8, 49",
            "Longest Win Streak": "Kratz & Corey, 9 (Wks 9-17)",
            "Longest Loss Streak": "M. Condon, 7 (Wks 4-10)",
            "Biggest Win": "Kratz & Corey 196-64 over Winter (Wk 17)",
        },
    },
    2022: {
        "awards": {
            "Rookie of the Year": "Kenneth Walker III (Haigney)",
            "Steal of the Draft": "Josh Allen (Verone, 3.05)",
            "Bust of the Draft": "Jonathan Taylor (Slater, 1.01)",
            "Fantasy MVP": "Josh Allen (Verone)",
        },
        "records": {
            "Highest Points": "Verone, Wk 15, 198",
            "Lowest Points": "Sterbank, Wk 5, 54",
            "Longest Win Streak": "Verone, 8 (Wks 9-16)",
            "Longest Loss Streak": "M. Condon, 5 (Wks 7-11)",
            "Biggest Win": "Verone 198-67 over Sterbank (Wk 15)",
        },
    },
    2023: {
        "awards": {
            "Rookie of the Year": "Puka Nacua (M. Lane)",
            "Steal of the Draft": "De'Von Achane (Verone, FA)",
            "Bust of the Draft": "Austin Ekeler (Kratz & Corey, 1.08)",
            "Fantasy MVP": "CeeDee Lamb (Verone)",
        },
        "records": {
            "Highest Points": "Verone, Wk 16, 201",
            "Lowest Points": "Condon, Wk 10, 51",
            "Longest Win Streak": "Verone, 7 (Wks 10-16)",
            "Longest Loss Streak": "Condon, 6 (Wks 6-11)",
            "Biggest Win": "Verone 201-69 over Condon (Wk 16)",
        },
    },
    2024: {
        "awards": {
            "Rookie of the Year": "Jayden Daniels (Haigney)",
            "Steal of the Draft": "Jahmyr Gibbs (Verone, 2.05)",
            "Bust of the Draft": "Breece Hall (Ott, 1.05)",
            "Fantasy MVP": "Saquon Barkley (M. Lane)",
        },
        "records": {
            "Highest Points": "Verone, Wk 14, 205",
            "Lowest Points": "Sterbank, Wk 8, 56",
            "Longest Win Streak": "Verone, 6 (Wks 9-14)",
            "Longest Loss Streak": "Sterbank, 5 (Wks 5-9)",
            "Biggest Win": "Verone 205-71 over Sterbank (Wk 14)",
        },
    },
    2025: {
        "awards": {
            "Rookie of the Year": "TBD",
            "Steal of the Draft": "TBD",
            "Bust of the Draft": "TBD",
            "Fantasy MVP": "TBD",
        },
        "records": {
            "Highest Points": "TBD",
            "Lowest Points": "TBD",
            "Longest Win Streak": "TBD",
            "Longest Loss Streak": "TBD",
            "Biggest Win": "TBD",
        },
    },
}

# Known league events by year
LEAGUE_EVENTS = {
    2004: [
        "The League was founded by Commissioner Chris Haigney with 10 founding members.",
        "First ever draft held with snake format.",
        "Ian Lane wins the inaugural championship as a 3-seed, defeating 1-seed Matt Altman in the final.",
    ],
    2005: [
        "Matt Condon departs the league after the 2004 season.",
        "Greg Cupelo takes over Matt Condon's franchise.",
        "Matt Winter wins his first championship as the 1-seed.",
    ],
    2006: [
        "Chris Haigney wins his first championship as the 1-seed.",
        "The league continues with 10 teams.",
    ],
    2007: [
        "Dave Slater wins his first championship as a 3-seed.",
        "Final season with 10 teams before expansion.",
    ],
    2008: [
        "EXPANSION YEAR: League grows from 10 to 12 teams.",
        "Mike Lane and Mike Sterbank join as new franchise owners.",
        "Matt Altman wins his first championship as the 2-seed.",
        "First year with 6-team playoff bracket.",
    ],
    2009: [
        "Dave Slater begins his dynasty run, winning back-to-back titles.",
        "Slater wins as the 1-seed.",
    ],
    2010: [
        "Dave Slater three-peats, winning his third consecutive championship.",
        "Won as the 2-seed this year.",
    ],
    2011: [
        "Dave Slater completes an incredible FOUR-PEAT!",
        "Won as the 1-seed, cementing his dynasty.",
        "One of the most dominant runs in league history.",
    ],
    2012: [
        "Joe Trendowski ends Slater's dynasty, winning his first and only championship.",
        "Won as the 2-seed.",
    ],
    2013: [
        "Chris Haigney wins his second championship as a 5-seed underdog.",
        "Major upset in the playoffs.",
    ],
    2014: [
        "Mike Lane wins his first championship as a 5-seed.",
        "Another underdog victory in the finals.",
    ],
    2015: [
        "Joe Trendowski resigns from the league.",
        "Matt Condon returns to take over Trendowski's franchise.",
        "Chris Haigney wins his third championship as the 1-seed.",
    ],
    2016: [
        "Peter Ott wins his first championship as the 1-seed.",
        "Dominant regular season translates to playoff success.",
    ],
    2017: [
        "Greg Cupelo leaves the league.",
        "Kratz & Corey (Brian Kratz and Josh Corey) take over the franchise.",
        "Matt Winter wins his second championship as the 2-seed.",
        "The League History book (2017 Edition) is published.",
    ],
    2018: [
        "Matt Altman wins his second championship as a 3-seed.",
        "Strong playoff run from a lower seed.",
    ],
    2019: [
        "Kratz & Corey win their first championship as a 5-seed.",
        "Remarkable run for the new ownership group.",
    ],
    2020: [
        "COVID-19 pandemic affects the NFL season.",
        "Peter Ott wins his second championship as the 2-seed.",
    ],
    2021: [
        "NFL expands to 17-game regular season.",
        "Fantasy playoffs now run through Week 17.",
        "Kratz & Corey win their second championship as the 1-seed.",
    ],
    2022: [
        "Matt Verone wins his first championship as the 2-seed.",
        "Beginning of Vern's dynasty run.",
    ],
    2023: [
        "Matt Verone wins back-to-back championships as a 5-seed.",
        "Continues his dominant playoff performances.",
    ],
    2024: [
        "Matt Verone THREE-PEATS as champion!",
        "Won as the 2-seed, joining Slater as the only owners with 3+ consecutive titles.",
    ],
    2025: [
        "Matt Winter wins his third championship as a 5-seed.",
        "Ends Verone's three-peat bid.",
        "Current season completed.",
    ],
}


def get_playoff_weeks(season: int, num_teams: int) -> tuple:
    """Return (playoff_start_week, playoff_end_week) for a season."""
    playoff_end = 17 if season >= 2021 else 16
    if num_teams <= 10:
        num_playoff_weeks = 2
    elif season == 2008:
        num_playoff_weeks = 2
    else:
        num_playoff_weeks = 3
    playoff_start = playoff_end - num_playoff_weeks + 1
    return playoff_start, playoff_end


def get_championship_bracket_max_seed(num_teams: int) -> int:
    """Return max seed for championship bracket."""
    return 4 if num_teams <= 10 else 6


def generate_playoff_bracket(season: int, matchups: pd.DataFrame, standings: pd.DataFrame) -> str:
    """Generate HTML for playoff bracket results."""
    season_standings = standings[standings["season"] == season]
    season_matchups = matchups[matchups["season"] == season]
    num_teams = len(season_standings)
    max_seed = get_championship_bracket_max_seed(num_teams)
    playoff_start, playoff_end = get_playoff_weeks(season, num_teams)

    # Build seed lookup
    seed_lookup = {}
    manager_lookup = {}
    for _, r in season_standings.iterrows():
        if pd.notna(r["playoff_seed"]):
            seed_lookup[r["team_name"]] = int(r["playoff_seed"])
            manager_lookup[r["team_name"]] = r["manager"]

    # Get playoff games
    playoff_games = season_matchups[
        (season_matchups["week"] >= playoff_start) &
        (season_matchups["week"] <= playoff_end)
    ].copy()

    # Add seeds
    playoff_games["my_seed"] = playoff_games["team_name"].map(seed_lookup)
    playoff_games["opp_seed"] = playoff_games["opp_name"].map(seed_lookup)

    # Filter to championship bracket only
    champ_games = playoff_games[
        (playoff_games["my_seed"] <= max_seed) &
        (playoff_games["opp_seed"] <= max_seed)
    ]

    if len(champ_games) == 0:
        return "<p>No playoff data available for this season.</p>"

    # Group by week
    html = '<div class="playoff-bracket">'
    weeks = sorted(champ_games["week"].unique())

    round_names = {
        0: "Quarterfinals" if len(weeks) >= 3 else "Semifinals",
        1: "Semifinals" if len(weeks) >= 3 else "Championship",
        2: "Championship",
    }

    for i, week in enumerate(weeks):
        week_games = champ_games[champ_games["week"] == week]
        # Get unique matchups (each game appears twice)
        seen = set()
        unique_games = []
        for _, g in week_games.iterrows():
            key = tuple(sorted([g["team_name"], g["opp_name"]]))
            if key not in seen:
                seen.add(key)
                unique_games.append(g)

        round_name = round_names.get(i, f"Round {i+1}")
        html += f'<h4>{round_name} (Week {week})</h4>'
        html += '<div class="bracket-games">'

        for g in unique_games:
            winner = g["team_name"] if g["pts_for"] > g["pts_against"] else g["opp_name"]
            loser = g["opp_name"] if g["pts_for"] > g["pts_against"] else g["team_name"]
            w_score = g["pts_for"] if g["pts_for"] > g["pts_against"] else g["pts_against"]
            l_score = g["pts_against"] if g["pts_for"] > g["pts_against"] else g["pts_for"]
            w_seed = seed_lookup.get(winner, "?")
            l_seed = seed_lookup.get(loser, "?")
            w_mgr = OWNER_NAMES.get(manager_lookup.get(winner, ""), winner)
            l_mgr = OWNER_NAMES.get(manager_lookup.get(loser, ""), loser)

            html += f'''
            <div class="bracket-game">
                <div class="team winner">[{w_seed}] {w_mgr} <span class="score">{w_score:.1f}</span></div>
                <div class="team">[{l_seed}] {l_mgr} <span class="score">{l_score:.1f}</span></div>
            </div>'''

        html += '</div>'

    html += '</div>'
    return html


def generate_standings_table(season: int, standings: pd.DataFrame) -> str:
    """Generate HTML table for regular season standings."""
    season_standings = standings[standings["season"] == season].sort_values("rank")

    html = '''
    <table class="standings-table">
        <thead>
            <tr>
                <th>Rank</th>
                <th>Team</th>
                <th>Manager</th>
                <th>W</th>
                <th>L</th>
                <th>T</th>
                <th>PF</th>
                <th>PA</th>
                <th>Seed</th>
            </tr>
        </thead>
        <tbody>
    '''

    for _, r in season_standings.iterrows():
        manager_name = OWNER_NAMES.get(r["manager"], r["manager"])
        seed = int(r["playoff_seed"]) if pd.notna(r["playoff_seed"]) else "-"
        pf = f'{r["points_for"]:.1f}' if pd.notna(r["points_for"]) else "-"
        pa = f'{r["points_against"]:.1f}' if pd.notna(r["points_against"]) else "-"
        wins = int(r["wins"]) if pd.notna(r["wins"]) else 0
        losses = int(r["losses"]) if pd.notna(r["losses"]) else 0
        ties = int(r["ties"]) if pd.notna(r["ties"]) else 0

        html += f'''
            <tr>
                <td>{int(r["rank"])}</td>
                <td>{r["team_name"]}</td>
                <td>{manager_name}</td>
                <td>{wins}</td>
                <td>{losses}</td>
                <td>{ties}</td>
                <td>{pf}</td>
                <td>{pa}</td>
                <td>{seed}</td>
            </tr>
        '''

    html += '</tbody></table>'
    return html


def generate_season_narrative(season: int, champ_info: dict) -> str:
    """Generate narrative section for the season."""
    events = LEAGUE_EVENTS.get(season, [])
    champ_name = OWNER_NAMES.get(champ_info["franchise_owner"], champ_info["franchise_owner"])
    team_name = champ_info["team_name"]
    seed = champ_info["seed"]

    html = '<div class="season-narrative">'
    html += f'<p><strong>{champ_name}</strong> won the {season} championship with "<em>{team_name}</em>" as the #{seed} seed.</p>'

    if events:
        html += '<h4>Notable Events</h4><ul>'
        for event in events:
            html += f'<li>{event}</li>'
        html += '</ul>'

    html += '</div>'
    return html


def generate_awards_section(season: int) -> str:
    """Generate HTML for the awards and records section."""
    season_data = SEASON_AWARDS.get(season)
    if not season_data:
        return ""

    awards = season_data.get("awards", {})
    records = season_data.get("records", {})

    # Skip if all TBD
    if all(v == "TBD" for v in awards.values()) and all(v == "TBD" for v in records.values()):
        return ""

    html = '<div class="awards-section">'

    if awards and not all(v == "TBD" for v in awards.values()):
        html += '<h4>Season Awards</h4><ul class="awards-list">'
        for award, recipient in awards.items():
            if recipient != "TBD":
                html += f'<li><em>{award}:</em> {recipient}</li>'
        html += '</ul>'

    if records and not all(v == "TBD" for v in records.values()):
        html += '<h4>Season Records</h4><ul class="records-list">'
        for record, value in records.items():
            if value != "TBD":
                html += f'<li><em>{record}:</em> {value}</li>'
        html += '</ul>'

    html += '</div>'
    return html


def generate_season_page(season: int, matchups: pd.DataFrame, standings: pd.DataFrame, champions: dict) -> str:
    """Generate complete HTML page for a season."""
    champ_info = champions.get(str(season), {})
    champ_name = OWNER_NAMES.get(champ_info.get("franchise_owner", ""), "Unknown")
    team_name = champ_info.get("team_name", "Unknown")

    prev_season = season - 1 if season > 2004 else None
    next_season = season + 1 if season < 2025 else None

    nav_links = '<div class="season-nav">'
    if prev_season:
        nav_links += f'<a href="{prev_season}.html" class="btn">&larr; {prev_season}</a>'
    else:
        nav_links += '<span></span>'
    nav_links += f'<a href="../history.html" class="btn">All Seasons</a>'
    if next_season:
        nav_links += f'<a href="{next_season}.html" class="btn">{next_season} &rarr;</a>'
    else:
        nav_links += '<span></span>'
    nav_links += '</div>'

    playoff_html = generate_playoff_bracket(season, matchups, standings)
    standings_html = generate_standings_table(season, standings)
    narrative_html = generate_season_narrative(season, champ_info)
    awards_html = generate_awards_section(season)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{season} Season - Season Ending Roster</title>
    <link rel="stylesheet" href="../assets/styles.css" />
    <style>
        .season-wrap {{
            max-width: var(--max-width);
            margin: 0 auto;
            padding: 24px 20px;
        }}
        .season-header {{
            text-align: center;
            margin-bottom: 32px;
        }}
        .season-header h1 {{
            font-size: 2.5rem;
            margin-bottom: 8px;
        }}
        .champion-banner {{
            background: linear-gradient(135deg, var(--accent) 0%, #b8860b 100%);
            color: #000;
            padding: 20px 24px;
            border-radius: 8px;
            margin-bottom: 24px;
            text-align: center;
        }}
        .champion-banner h2 {{
            margin: 0 0 8px;
            font-size: 1.5rem;
        }}
        .champion-banner .team-name {{
            font-style: italic;
            opacity: 0.9;
        }}
        .section {{
            background: var(--card);
            border-radius: 8px;
            padding: 20px 24px;
            margin-bottom: 24px;
        }}
        .section h3 {{
            margin: 0 0 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--line);
        }}
        .season-nav {{
            display: flex;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 24px;
        }}
        .standings-table {{
            width: 100%;
            font-size: 0.9rem;
        }}
        .standings-table th {{
            position: static;
            background: var(--card);
        }}
        .playoff-bracket h4 {{
            margin: 16px 0 12px;
            color: var(--text-secondary);
        }}
        .bracket-games {{
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
        }}
        .bracket-game {{
            background: var(--bg);
            border: 1px solid var(--line);
            border-radius: 6px;
            padding: 12px 16px;
            min-width: 280px;
        }}
        .bracket-game .team {{
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
        }}
        .bracket-game .team.winner {{
            font-weight: 600;
            color: var(--accent);
        }}
        .bracket-game .score {{
            font-family: monospace;
        }}
        .season-narrative ul {{
            padding-left: 20px;
            line-height: 1.8;
        }}
        .season-narrative li {{
            margin-bottom: 8px;
        }}
        .awards-section h4 {{
            margin: 20px 0 12px;
            color: var(--text-secondary);
        }}
        .awards-section h4:first-child {{
            margin-top: 0;
        }}
        .awards-list, .records-list {{
            padding-left: 20px;
            line-height: 1.8;
        }}
        .awards-list li, .records-list li {{
            margin-bottom: 6px;
        }}
        .awards-list em, .records-list em {{
            color: var(--text-secondary);
        }}
    </style>
</head>
<body>
    <div class="sitebar">
        <div class="bar-inner">
            <div class="brand">Season Ending Roster</div>
            <nav class="tabs" aria-label="Primary">
                <a href="../index.html">Home</a>
                <a href="../franchises.html">Franchises</a>
                <a href="../playoffs.html">Playoffs</a>
                <a href="../brackets.html">Brackets</a>
                <a href="../h2h.html">H2H</a>
                <a href="../history.html">History</a>
            </nav>
        </div>
    </div>

    <div class="season-wrap">
        {nav_links}

        <div class="season-header">
            <h1>{season} Season</h1>
            <p class="hint">Complete results and standings</p>
        </div>

        <div class="champion-banner">
            <h2>&#x1F451; Champion: {champ_name}</h2>
            <div class="team-name">"{team_name}"</div>
        </div>

        <div class="section">
            <h3>Season Summary</h3>
            {narrative_html}
        </div>

        <div class="section">
            <h3>Playoff Bracket</h3>
            {playoff_html}
        </div>

        <div class="section">
            <h3>Regular Season Standings</h3>
            {standings_html}
        </div>

        {f'<div class="section"><h3>Awards & Records</h3>{awards_html}</div>' if awards_html else ''}

        {nav_links}
    </div>

    <footer class="site-footer">
        <div>&copy; 2004&ndash;<span id="year"></span> Season Ending Roster</div>
        <div class="foot-meta">Season {season}</div>
    </footer>

    <script>
        document.getElementById('year').textContent = new Date().getFullYear();
    </script>
</body>
</html>
'''
    return html


def main():
    # Load data
    standings = pd.read_csv(DATA_DIR / "standings_by_season.csv")
    matchups = pd.read_csv(DATA_DIR / "matchups.csv")

    with open(DATA_DIR / "playoff_metrics.json") as f:
        playoff_metrics = json.load(f)

    champions = playoff_metrics["champions_by_season"]

    # Create output directory
    OUT_DIR.mkdir(exist_ok=True)

    # Generate pages for all seasons in playoff_metrics (includes years without CSV data)
    seasons = sorted([int(s) for s in champions.keys()])

    for season in seasons:
        print(f"Generating {season} season page...")
        html = generate_season_page(season, matchups, standings, champions)
        out_path = OUT_DIR / f"{season}.html"
        out_path.write_text(html)

    print(f"\n✅ Generated {len(seasons)} season pages in {OUT_DIR}/")

    # Generate index page for seasons
    index_html = generate_seasons_index(seasons, champions)
    (OUT_DIR / "index.html").write_text(index_html)
    print(f"✅ Generated seasons index page")


def generate_seasons_index(seasons: list, champions: dict) -> str:
    """Generate index page listing all seasons."""
    rows = ""
    for season in sorted(seasons, reverse=True):
        champ = champions.get(str(season), {})
        owner = OWNER_NAMES.get(champ.get("franchise_owner", ""), "Unknown")
        team = champ.get("team_name", "Unknown")
        seed = champ.get("seed", "?")
        rows += f'''
            <tr>
                <td><a href="{season}.html">{season}</a></td>
                <td>{owner}</td>
                <td>{team}</td>
                <td>{seed}</td>
            </tr>
        '''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>All Seasons - Season Ending Roster</title>
    <link rel="stylesheet" href="../assets/styles.css" />
    <style>
        .seasons-wrap {{
            max-width: var(--max-width);
            margin: 0 auto;
            padding: 24px 20px;
        }}
        .seasons-table a {{
            color: var(--accent);
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="sitebar">
        <div class="bar-inner">
            <div class="brand">Season Ending Roster</div>
            <nav class="tabs" aria-label="Primary">
                <a href="../index.html">Home</a>
                <a href="../franchises.html">Franchises</a>
                <a href="../playoffs.html">Playoffs</a>
                <a href="../brackets.html">Brackets</a>
                <a href="../h2h.html">H2H</a>
                <a href="../history.html" aria-current="page">History</a>
            </nav>
        </div>
    </div>

    <div class="seasons-wrap">
        <div class="page-header">
            <h1>All Seasons</h1>
            <p class="hint">Click a season to view detailed results</p>
        </div>

        <div class="card">
            <table class="seasons-table">
                <thead>
                    <tr>
                        <th>Season</th>
                        <th>Champion</th>
                        <th>Team Name</th>
                        <th>Seed</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
    </div>

    <footer class="site-footer">
        <div>&copy; 2004&ndash;<span id="year"></span> Season Ending Roster</div>
    </footer>

    <script>
        document.getElementById('year').textContent = new Date().getFullYear();
    </script>
</body>
</html>
'''


if __name__ == "__main__":
    main()
