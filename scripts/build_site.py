#!/usr/bin/env python3
"""
build_site.py
Reads site_data/*.json (from metrics.py) and builds simple static HTML pages in reports/.
- reports/index.html (links to other pages)
- reports/champions.html
- reports/all_time.html
- reports/records.html

Run after metrics.py:
    python scripts/build_site.py
"""

from pathlib import Path
import json
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
SITE_DATA = ROOT / "site_data"
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

STYLE = """
<style>
  :root { --bg:#0f0f10; --card:#1b1b1d; --muted:#a0a0a0; --text:#fff; --line:#2a2a2e; }
  * { box-sizing: border-box; }
  body { margin: 0; font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
         background: var(--bg); color: var(--text); padding: 24px; }
  a { color: #9ecbff; text-decoration: none; }
  header { max-width: 1000px; margin: 0 auto 12px; }
  main { max-width: 1000px; margin: 0 auto; }
  h1 { margin: 0 0 12px; font-size: 28px; }
  .muted { color: var(--muted); }
  .card { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 16px; margin: 16px 0; }
  table { width: 100%; border-collapse: collapse; }
  th, td { padding: 10px; border-bottom: 1px solid var(--line); text-align: left; }
  th { position: sticky; top: 0; background: var(--card); }
  .num { text-align: right; }
  nav a { margin-right: 12px; }
  .chip { display:inline-block; padding:4px 8px; border-radius:999px; background:#222; border:1px solid var(--line); }
  footer { margin: 40px auto; max-width: 1000px; color: var(--muted); font-size: 13px; }
</style>
"""

def wrap_page(title: str, body_html: str) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!doctype html>
<html lang="en"><head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  {STYLE}
</head>
<body>
<header>
  <h1>{title}</h1>
  <nav>
    <a href="/reports/index.html">Reports Home</a>
    <a href="/reports/champions.html">Champions</a>
    <a href="/reports/all_time.html">All-time</a>
    <a href="/reports/records.html">Records</a>
  </nav>
</header>
<main>
{body_html}
</main>
<footer>Generated {now}</footer>
</body>
</html>"""

def load_json(name: str):
    p = SITE_DATA / name
    return json.loads(p.read_text()) if p.exists() else None

def build_index():
    body = """
<div class="card">
  <p>Welcome! Explore long-term league stats:</p>
  <ul>
    <li><a href="/reports/champions.html">Champions by season</a></li>
    <li><a href="/reports/all_time.html">All-time standings (aggregated)</a></li>
    <li><a href="/reports/records.html">Fun records (high week, biggest blowout, streaks)</a></li>
  </ul>
  <p class="muted">Tip: add other pages as you build more metrics.</p>
</div>
"""
    (REPORTS / "index.html").write_text(wrap_page("League Reports", body))

def build_champions():
    champs = load_json("champions.json") or []
    runners = load_json("runnerups.json") or []

    rows = "\n".join(
        f"<tr><td>{c['season']}</td><td>{c['team_name']}</td><td>{c.get('manager','')}</td></tr>"
        for c in champs
    )
    rows2 = "\n".join(
        f"<tr><td>{c['season']}</td><td>{c['team_name']}</td><td>{c.get('manager','')}</td></tr>"
        for c in runners
    )

    body = f"""
<div class="card">
  <h2>Champions</h2>
  <table>
    <thead><tr><th>Season</th><th>Team</th><th>Manager</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>

<div class="card">
  <h2>Runner-ups</h2>
  <table>
    <thead><tr><th>Season</th><th>Team</th><th>Manager</th></tr></thead>
    <tbody>{rows2}</tbody>
  </table>
</div>
"""
    (REPORTS / "champions.html").write_text(wrap_page("Champions & Runner-ups", body))

def build_all_time():
    data = load_json("all_time.json") or []
    rows = "\n".join(
        f"<tr>"
        f"<td>{i+1}</td>"
        f"<td>{d['team_name']}</td>"
        f"<td>{d.get('manager','')}</td>"
        f"<td class='num'>{d['seasons']}</td>"
        f"<td class='num'>{d['titles']}</td>"
        f"<td class='num'>{d['wins']}-{d['losses']}-{d['ties']}</td>"
        f"<td class='num'>{d['win_pct']:.2f}%</td>"
        f"<td class='num'>{d['pf']:.2f}</td>"
        f"<td class='num'>{d['pa']:.2f}</td>"
        f"</tr>"
        for i, d in enumerate(data)
    )
    body = f"""
<div class="card">
  <h2>All-time standings</h2>
  <p class="muted">Sorted by titles, then win%, then points for.</p>
  <table>
    <thead>
      <tr>
        <th>#</th><th>Team</th><th>Manager</th>
        <th class="num">Seasons</th>
        <th class="num">Titles</th>
        <th class="num">W-L-T</th>
        <th class="num">Win %</th>
        <th class="num">PF</th>
        <th class="num">PA</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
</div>
"""
    (REPORTS / "all_time.html").write_text(wrap_page("All-time Standings", body))

def build_records():
    rec = load_json("records.json") or {}
    high = rec.get("single_week_high")
    blow = rec.get("single_week_margin")
    streak = rec.get("longest_win_streak")

    item = lambda label, val: f"<div><span class='chip'>{label}</span> {val}</div>"

    parts = []
    if high:
        parts.append(item(
            "Highest single-week points",
            f"{high['team_name']} — {high['points']:.2f} (Week {high['week']}, {high['season']})"
        ))
    if blow:
        parts.append(item(
            "Biggest blowout",
            f"{blow['team_name']} over {blow['opp_name']} by {blow['margin']:.2f} " +
            f"({blow['pts_for']:.2f}–{blow['pts_against']:.2f}) — Week {blow['week']}, {blow['season']}"
        ))
    if streak and streak.get("longest_win_streak", 0) > 0:
        parts.append(item(
            "Longest win streak",
            f"{streak['team_name']} — {streak['longest_win_streak']} (through Week {streak.get('week')} {streak.get('season')})"
        ))

    body = f"""
<div class="card">
  <h2>Records</h2>
  {"".join(parts) if parts else "<p class='muted'>No matchup data available.</p>"}
</div>
"""
    (REPORTS / "records.html").write_text(wrap_page("Fun Records", body))

def main():
    build_index()
    build_champions()
    build_all_time()
    build_records()
    print("✅ Wrote reports/*.html")

if __name__ == "__main__":
    main()