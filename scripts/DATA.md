# DATA.md — League data pipeline (pull → transform → metrics → site)

This doc explains **what data we store**, **where it lives**, **how it flows**, and **how to run the steps**. It’s written for a junior developer.

---

## TL;DR workflow

```bash
# 0) One-time: make sure oauth2.json + token.json exist (see REFRESH.md)
python scripts/yahoo_auth_cli.py   # only once per machine

# 1) Refresh token (safe to run anytime)
python scripts/refresh_token.py

# 2) Pull raw data from Yahoo (JSON snapshots per season)
python scripts/pull_raw.py

# 3) Convert raw → CSV (tidy tables for analysis)
python scripts/transform.py

# 4) Compute metrics + build static report pages
python scripts/metrics.py
python scripts/build_site.py

# 5) Publish only /reports and /site_data (never commit /data or secrets)
git add reports/ site_data/
git commit -m "Update reports"
git push
```

---

## Repository layout (Option A)

```
repo/
├─ index.html
├─ images/
├─ reports/            # PUBLIC: static HTML pages (generated)
│  └─ csv/             # PUBLIC: CSV mirrors (ok to commit)
├─ site_data/          # PUBLIC: JSON used by report pages (generated)
├─ scripts/            # LOCAL: code only, not served by Pages
│  ├─ yahoo_auth_cli.py
│  ├─ refresh_token.py
│  ├─ pull_raw.py
│  ├─ transform.py
│  ├─ metrics.py
│  └─ build_site.py
├─ data/               # LOCAL: raw + processed working data (do not commit)
│  ├─ raw/
│  └─ processed/
├─ oauth2.example.json
├─ .gitignore
└─ README.md
```

**Public** = served by GitHub Pages. **Local** = stays on your machine, never committed.

---

## Data flow (overview)

1) **Raw pull**  
   - Source: Yahoo Fantasy Sports API (authorized by your Yahoo account)  
   - Output: `data/raw/{season}/` with multiple JSON files  
   - Purpose: immutable snapshots (we can rebuild reports later without re-pulling)

2) **Transform**  
   - Input: `data/raw/**`  
   - Output: `data/processed/*.csv` (normalized tables)  
   - Purpose: stable schemas for downstream metrics

3) **Metrics**  
   - Input: `data/processed/*.csv`  
   - Output: `site_data/*.json` (public-friendly structures) + `reports/csv/*.csv`  
   - Purpose: precomputed aggregates

4) **Site build**  
   - Input: `site_data/*.json`  
   - Output: `reports/*.html` (static pages)  
   - Purpose: publishable artifacts for GitHub Pages

---

## Raw data (JSON) — what we keep

Each season has its own folder:

```
data/raw/2024/
  settings.json
  standings.json
  matchups.json
  draft.json
  rosters.json
  transactions.json
```

### Files

- **settings.json**  
  League configuration for that season:
  ```json
  {
    "season": "2024",
    "name": "My League",
    "end_week": 17,
    "num_teams": 12,
    "scoring_type": "head"
  }
  ```

- **standings.json**  
  Array of teams with ranks and totals:
  ```json
  [
    {
      "team_key": "nfl.l.123456.t.1",
      "name": "Team A",
      "managers": [{"nickname":"Chris"}],
      "standings": { "rank": 1,
        "outcome_totals": {"wins":11,"losses":3,"ties":0}
      },
      "team_points": {"total": "1562.40"},
      "team_points_against": {"total": "1401.10"}
    }
  ]
  ```

- **matchups.json**  
  Map of week → list of games. For each game we store both team perspectives later in CSV.
  ```json
  {
    "1": [
      {
        "teams": [
          {"team_key":"...t.1","name":"Team A","team_points":{"total":"110.2"}},
          {"team_key":"...t.2","name":"Team B","team_points":{"total":"98.7"}}
        ]
      }
    ],
    "2": [ ... ]
  }
  ```

- **draft.json**  
  Draft picks for the season (if available). May be empty/absent for some formats.

- **rosters.json**  
  Map of `team_key` → roster list (used for deeper analysis later).

- **transactions.json**  
  Adds/drops/trades. Structure can vary by season; treat as optional.

> **Note:** Raw JSON schemas can vary slightly by year/league type. That’s why we keep snapshots and normalize in the transform step.

---

## Processed data (CSV) — stable schemas

Produced by `scripts/transform.py` into `data/processed/`:

### 1) `standings_by_season.csv`

| column        | type    | description                                  |
|---------------|---------|----------------------------------------------|
| season        | int     | e.g., 2024                                   |
| league_key    | string  | Yahoo league key (if present in raw)         |
| team_key      | string  | Yahoo team key                               |
| team_name     | string  | Team name                                    |
| manager       | string  | First manager nickname (if available)        |
| wins          | int     |                                              |
| losses        | int     |                                              |
| ties          | int     |                                              |
| rank          | int     | Final season rank                            |
| points_for    | float   | Total season points                          |
| points_against| float   | Total points against                         |

### 2) `matchups.csv`

Each game is represented twice (once per team perspective).

| column      | type   | description                         |
|-------------|--------|-------------------------------------|
| season      | int    |                                     |
| week        | int    | 1..end_week                         |
| team_key    | string | team’s key                          |
| team_name   | string | team’s name                         |
| opp_key     | string | opponent’s key                      |
| opp_name    | string | opponent’s name                     |
| pts_for     | float  | team’s points that week             |
| pts_against | float  | opponent’s points that week         |
| is_home     | bool?  | if available in raw, may be null    |

> These two CSVs are enough to compute **Champions**, **All-time standings**, and fun **Records**. You can add more transforms later for drafts, rosters, or transactions.

---

## Metrics outputs (public JSON)

Produced by `scripts/metrics.py` into `site_data/`:

- `champions.json` — `[{"season":2024,"team_name":"...","manager":"..."}]`
- `runnerups.json` — same shape (rank 2)
- `all_time.json` — aggregated per team:
  ```json
  [{
    "team_name":"Team A","manager":"Chris","seasons":10,
    "wins":85,"losses":55,"ties":0,
    "pf": 14876.22, "pa": 14220.01,
    "titles":2, "games":140, "win_pct":60.71
  }]
  ```
- `records.json` — quick facts:
  ```json
  {
    "single_week_high": {"season":2021,"week":7,"team_name":"Team A","points":184.3},
    "single_week_margin": {"season":2022,"week":3,"team_name":"Team B","opp_name":"Team C",
                           "margin":72.1,"pts_for":180.0,"pts_against":107.9},
    "longest_win_streak": {"team_name":"Team D","longest_win_streak":8,"season":2020,"week":12}
  }
  ```

CSV mirrors for debugging go to `reports/csv/`:
- `champions.csv`, `runnerups.csv`, `all_time.csv`

---

## Site outputs (public HTML)

Produced by `scripts/build_site.py` into `reports/`:

- `reports/index.html` — links to other pages
- `reports/champions.html`
- `reports/all_time.html`
- `reports/records.html`

These pages **read from `site_data/*.json`** and are safe to publish.

---

## Config you may need to edit

- `scripts/pull_raw.py` → `CURRENT_LEAGUE_KEY = "nfl.l.123456"`  
  (Ask the maintainer how to find your Yahoo league key; it’s also visible in the Yahoo league URL and via the API.)

- Sleep between API calls: `SLEEP = 0.3` seconds (be kind to the API/rate limits).

---

## Privacy & Git hygiene

**Never commit:**
- `oauth2.json` (client_id + client_secret)
- `token.json` (refresh/access tokens)
- `data/` (raw & processed)

**Your `.gitignore` must include:**
```
oauth2.json
token.json
data/
__pycache__/
*.pyc
```

Public, safe to commit:
- `/reports/**` (HTML + CSV mirrors)
- `/site_data/**` (derived JSON without secrets)
- `/scripts/**` (code only, no secrets)

---

## Common “why is this different” notes

- **Old seasons** may have slightly different raw schemas (Yahoo has evolved). Our `transform.py` is defensive—if something’s missing, it skips bad rows rather than crash. You can improve normalization over time.
- **Team names/managers** can change across years; `all_time.json` groups on `(team_name, manager)` by default. If you want a *manager-id* based grouping, add a normalization step.
- **Matchups**: Some weeks (bye weeks/playoffs) can look different; we already guard against odd rows.

---

## Error checklist

- `401 Unauthorized` when pulling:  
  Run `python scripts/refresh_token.py`, then try again.

- `redirect_uri_mismatch` during first login:  
  Make sure your `oauth2.json` `redirect_uri` **exactly** matches what’s registered in Yahoo (including `https` and path).

- `No refresh_token found`:  
  Re-run `yahoo_auth_cli.py` to generate a new `token.json`.

- Site didn’t update after push:  
  Wait ~1–2 minutes, then hard refresh/Incognito. Ensure you committed `reports/` and `site_data/`.

---

## Extending the pipeline (ideas)

- Add **draft analysis** (value over ADP/slot, keeper impact).
- Add **trades network** graph (who trades with whom).
- Add **Elo-like ratings** over seasons.
- Add **manager profiles** pages using `site_data` slices.

Keep the same pattern: raw → transform → metrics → site.

---

## Handy commands (copy/paste)

```bash
# Run full refresh (safe daily/weekly)
python scripts/refresh_token.py
python scripts/pull_raw.py
python scripts/transform.py
python scripts/metrics.py
python scripts/build_site.py
git add reports/ site_data/
git commit -m "Refresh league reports"
git push
```

> If anything breaks, copy the exact error and ask the maintainer. Most issues boil down to tokens, redirect URIs, or a weird raw JSON edge case we can patch in `transform.py`.