# Quickstart: Competitive Intelligence Upgrade

## Prerequisites

- Existing setup from feature 001 (venv, `playwright install chromium`,
  `MEDIA_SCRAPER_API_KEY` env var, working `config.toml`).
- No new dependencies to install.

## 1. Define the brief in config.toml

```toml
brand = "Pos Malaysia"
competitors = ["J&T Express", "GDEX", "DHL", "FedEx", "City-Link Express"]
platforms = ["x", "reddit", "youtube", "facebook", "linkedin", "news"]
recency_days = 7
max_sources = 30
```

## 2. One-time sign-in for walled social platforms (headed)

```bash
media-scraper --brief        # headed; sign in to X / Facebook / LinkedIn at the pause
```

The session is saved in `.browser-profile/` and reused by later headless runs.

## 3. Run unattended (what cron will run)

```bash
media-scraper --brief --headless --days 7
```

Produces `reports/pos-malaysia-<timestamp>.md` containing a **Competitive
Sentiment** table for Pos Malaysia + the five competitors, plus social/news
sources from the last 7 days, excluding anything already reported.

## 4. Schedule weekly via cron

```cron
0 7 * * 1 cd /home/aiden/Projects/media-scraper && \
  MEDIA_SCRAPER_API_KEY=… .venv/bin/media-scraper --brief --headless >> reports/cron.log 2>&1
```

## Verification

1. **Stub test** (no network/browser):
   ```bash
   python -m pytest tests/test_pipeline.py
   ```
   New asserts confirm an already-seen URL is skipped and the per-brand tally is
   computed.

2. **Competitive coverage (SC-001)**: run once; confirm the report's Competitive
   Sentiment table lists all six brands.

3. **Social coverage (SC-002)**: confirm at least one X/Reddit/YouTube permalink
   appears in Sources.

4. **Latest-only (SC-003)**: run `--brief` twice within the window; the second
   report's Sources contain no URL from the first (check `.state/<slug>.json`
   grew).

5. **Recency (SC-005)**: confirm the search backend is called with a date limit
   and social URLs carry `sort=new`/`f=live` (run with logging).

6. **Unattended (SC-004)**: run `--brief --headless`; no prompts, exit code `0`,
   timestamped report present.

7. **Reach (SC-006)**: run with `--max-sources 10` then `--max-sources 30`;
   confirm more mentions gathered at the higher cap.
