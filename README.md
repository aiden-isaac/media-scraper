# media-scraper

A single-user CLI that researches a free-text topic across the open web, news, RSS/Atom
feeds, and account-gated social media, then exports a Markdown report. A configurable
OpenAI-compatible LLM plans the research and analyzes sources (claims, sentiment,
credibility); you sign in / solve captchas yourself in a visible browser when a site
requires it, and sessions persist across runs.

See `specs/001-topic-research-scraper/` for the full spec, plan, and design.

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
