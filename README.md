# media-scraper

A single-user CLI that researches a free-text topic across the open web, news, RSS/Atom
feeds, and account-gated social media, then exports a Markdown report. A configurable
OpenAI-compatible LLM plans the research and analyzes sources (claims, sentiment,
credibility); you sign in / solve captchas yourself in a visible browser when a site
requires it, and sessions persist across runs.

It also runs recurring **brand-vs-competitor briefs**: a scheduled, non-interactive
run that produces a per-brand competitive sentiment report, searches social platforms
in-site, narrows to a recency window, and reports only mentions new since the last run.

See `specs/001-topic-research-scraper/` and `specs/003-competitive-intel/` for the full
specs, plans, and design.

## Install

```bash
pip install -e .
# Or, to include the web GUI:
pip install -e ".[gui]"

playwright install chromium    # one-time browser download
```

## Configure

```bash
export MEDIA_SCRAPER_API_KEY="<your key>"   # secret — never goes in config.toml
```

Edit `config.toml` (endpoint, model, output dir, caps) or run the interactive editor:

```bash
python -m media_scraper --configure
```

## Run CLI

```bash
python -m media_scraper                       # prompts for a topic
python -m media_scraper --topic "<topic>"     # non-interactive topic
python -m media_scraper --topic "<topic>" --headless   # open sources only, no manual login
```

Watch the streaming log (`plan → gather → analyze → synthesize`). When a site needs login or
shows a captcha, the browser window pauses — sign in / solve it, then press Enter. The login
is reused next time. On completion the report path is printed (under `output_dir`).

## Competitive briefs

Define a brief in `config.toml` (`brand`, `competitors`, `platforms`, `recency_days`,
`max_sources`), then:

```bash
python -m media_scraper --brief                       # headed: sign in to walled platforms once
python -m media_scraper --brief --headless --days 7   # unattended (what cron runs)
python -m media_scraper --brief --max-sources 30      # widen reach
python -m media_scraper --since 2026-06-01            # recency by start date (vs --days N)
```

`--brief` requires `brand` set. The report leads with a **Competitive Sentiment** table
covering the brand and every competitor. Each brief tracks reported URLs in
`.state/<slug>.json` (gitignored), so re-runs report only new items. Walled platforms
(X / Facebook / LinkedIn) need one headed sign-in; the persistent session is reused by
headless runs, falling back to keyless `site:` search when unavailable. Schedule with OS
cron — see `AGENTS.md` for the cron line.

## Run Web GUI

If you installed the `[gui]` optional dependencies, you can run a local web server to manage settings, launch research tasks, and view reports from your browser:

```bash
python -m media_scraper gui --port 8000
```
Then open `http://localhost:8000` in your web browser.

## Test

```bash
python tests/test_pipeline.py      # stub-LLM check, no network/browser needed
# or: python -m pytest tests/
```

## Notes

- Never commit the API key, `.browser-profile/`, or `reports/` (all gitignored).
- If web search (`ddgs`) stops returning results, the documented fallback is browser-driven
  search — see `specs/001-topic-research-scraper/research.md`.
- The tool never stores credentials and includes no captcha solver: logins are manual.
