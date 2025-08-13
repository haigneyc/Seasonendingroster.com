# REFRESH.md — How to refresh Yahoo OAuth tokens & update the site

This guide is for a junior dev who’s never done OAuth before. Follow it step-by-step and you’ll be fine. 🙂

---

## What you’re refreshing (plain English)

- **Access token**: short-lived key used to call Yahoo’s API (expires ~1 hour).
- **Refresh token**: long-lived key used to *get a new access token* without logging in again.

You’ll refresh the **access token** using the **refresh token**, then run our data pull to rebuild reports and push them to the website.

---

## Folder layout (Option A)

```
repo/
├─ index.html            # live site landing/gallery (served by GitHub Pages)
├─ reports/              # generated static report pages (served)
├─ site_data/            # generated JSON for charts/tables (served)
├─ scripts/              # local scripts (NOT served by Pages)
│  ├─ yahoo_auth_cli.py  # one-time login to create token.json
│  ├─ refresh_token.py   # refresh access token without login
│  ├─ pull_raw.py        # download raw data by season → data/raw/...
│  ├─ transform.py       # (optional) convert raw → CSV
│  ├─ metrics.py         # (optional) compute summary stats → site_data/
│  └─ build_site.py      # (optional) render HTML pages → reports/
├─ data/                 # local working data (NOT committed)
│  ├─ raw/
│  └─ processed/
├─ oauth2.example.json   # template (safe to commit)
├─ .gitignore            # prevents secrets/data from being committed
└─ README.md
```

**Important:** `oauth2.json` and `token.json` live **locally** next to the scripts and are **ignored by git**.

---

## One-time setup (only once per machine)

1. **Copy the OAuth template**  
   ```bash
   cd repo
   cp oauth2.example.json oauth2.json
   ```
   Edit `oauth2.json` with the real values (ask the maintainer if you don’t have them):
   ```json
   {
     "client_id":    "YOUR_YAHOO_APP_CLIENT_ID",
     "client_secret":"YOUR_YAHOO_APP_CLIENT_SECRET",
     "redirect_uri": "https://seasonendingroster.com/oauth2callback",
     "scopes":       "fspt-r profile email"
   }
   ```

2. **Install Python deps**  
   ```bash
   pip install requests yahoo-fantasy-api yahoo_oauth pandas
   ```

3. **Do the first login (creates token.json)**  
   ```bash
   python scripts/yahoo_auth_cli.py
   ```
   - It prints a login URL → open it → sign in → approve.
   - You’ll be redirected to our domain with `?code=...`.
   - **Copy the entire redirect URL** from your browser and paste it into the script.
   - On success, you’ll see `✅ Saved tokens to token.json`.

You won’t need to log in again unless you revoke access or delete `token.json`.

---

## Everyday use: refresh + pull + rebuild

### 1) Refresh the token (fast, no login)
```bash
python scripts/refresh_token.py
```
- Output says “✅ Token refreshed …”.
- This updates `token.json` with a fresh `access_token`.

> Tip: Many scripts can auto-refresh; running this manually first is the simplest workflow.

### 2) Pull data
Edit `scripts/pull_raw.py` and set your current league key:
```python
CURRENT_LEAGUE_KEY = "nfl.l.123456"
```
Then:
```bash
python scripts/pull_raw.py
```
You should see season folders appear under `data/raw/20XX/`.

### 3) (Optional) Transform + metrics + build site
If the repo includes these helpers:
```bash
python scripts/transform.py
python scripts/metrics.py
python scripts/build_site.py
```
This writes JSON into `site_data/` and HTML pages into `reports/`.

### 4) Publish to the website
Commit only the **site files** (and any code changes), **not** secrets or `data/`:

```bash
git add reports/ site_data/ .
git commit -m "Refresh reports"
git push
```

GitHub Pages will update automatically within ~30–90 seconds (sometimes a couple minutes).

---

## Do **NOT** commit these files

Make sure `.gitignore` contains:

```
# secrets & local data
oauth2.json
token.json
data/
__pycache__/
*.pyc
```

If you accidentally committed secrets, **rotate** them (see “Common fixes” below).

---

## Quick “it’s broken” checklist

1. **Site didn’t update**
   - Wait 1–2 minutes, then hard refresh (or use a private/incognito window).
   - Check that you committed **reports/** and **site_data/** files.

2. **API calls failing with 401/expired token**
   - Run `python scripts/refresh_token.py` again.
   - Re-run your command.

3. **`refresh_token.py` says “No refresh_token found”**
   - Your `token.json` may be incomplete or old.  
     Re-run the one-time login:
     ```bash
     python scripts/yahoo_auth_cli.py
     ```

4. **Error: `invalid_client`**
   - `client_id/client_secret` in `oauth2.json` are wrong or rotated.  
     Ask maintainer for updated values.

5. **Error: `redirect_uri_mismatch`**
   - The `redirect_uri` in `oauth2.json` must match *exactly* what’s registered in Yahoo’s developer console (including https and path).  
   - Update your local `oauth2.json` to the correct URI.

6. **`invalid_grant` during token exchange**
   - The authorization `code` might be used/expired.  
     Run `yahoo_auth_cli.py` again and paste a fresh redirect URL.

7. **Rate limits / intermittent 429s**
   - The scripts already sleep between calls. If it persists, wait a minute and retry.

---

## Common maintenance tasks

### Rotate secrets (if compromised)
1. In Yahoo dev console, **revoke** old client secret and create a new one.
2. Update local `oauth2.json`.
3. Re-run `yahoo_auth_cli.py` to create a fresh `token.json`.

### Move to a new laptop
- Copy `oauth2.json` and `token.json` securely to the new machine **or** just run `yahoo_auth_cli.py` again on the new machine.
- Install Python deps and go.

### Verify what you’re publishing
- `reports/` and `site_data/` are public.  
- `data/`, `oauth2.json`, `token.json` are private (local only).

---

## FAQ

**Q: How often should I refresh?**  
A: Anytime you run a script and get 401/expired token errors. It’s quick and safe to run before each pull.

**Q: Do I ever need to log in again?**  
A: Only if `token.json` is deleted/invalidated or you revoke the app in Yahoo. Otherwise, `refresh_token.py` is enough.

**Q: How long until changes are live?**  
A: Usually under 2 minutes for GitHub Pages. Hard refresh if you don’t see updates.

**Q: Where do I change which seasons we pull?**  
A: `scripts/pull_raw.py` follows Yahoo’s **renew chain** automatically. To limit, add logic there (e.g., only recent years).

---

## TL;DR quick commands

```bash
# 0) one-time (first machine only)
python scripts/yahoo_auth_cli.py

# 1) every time you want fresh data
python scripts/refresh_token.py
python scripts/pull_raw.py
python scripts/transform.py
python scripts/metrics.py
python scripts/build_site.py

# 2) publish
git add reports/ site_data/
git commit -m "Refresh reports"
git push
```

You’re done. If anything’s confusing, ping the maintainer with the exact error message you see in the terminal.