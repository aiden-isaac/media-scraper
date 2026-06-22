# Quickstart: Topic Research Scraper

## Prerequisites
- Python 3.11+
- A graphical desktop session (a visible browser window is needed for manual sign-in)
- Access to an OpenAI-compatible LLM endpoint (e.g. a LiteLLM/Qwen server)

## Install
```bash
pip install -e .            # installs deps from pyproject.toml
playwright install chromium # one-time browser download
```

## Configure
1. Set the secret (never committed):
   ```bash
   export MEDIA_SCRAPER_API_KEY="<your key>"
   ```
2. Edit `config.toml` (no secrets in here):
   ```toml
   base_url = "https://llm.example.com/v1"
   model = "qwen-moe-coder"
   output_dir = "reports"
   user_data_dir = ".browser-profile"
   headless = false
   max_sources = 12
   max_chars_per_source = 8000
   ```
   Or run the interactive editor: `python -m media_scraper --configure`.

## Run
```bash
python -m media_scraper
# enter a topic when prompted, e.g.:
#   "Public sentiment and credibility of coverage on <topic> over the last month,
#    across news, Reddit, and X."
```
- Watch the streaming log: `plan → gather → analyze → synthesize`.
- When a site needs login or shows a captcha, the browser window pauses — sign in / solve it
  yourself, then press Enter to continue. The login is saved for next time.
- On completion the path to the Markdown report is printed (under `output_dir`).

Non-interactive (open sources only, no login):
```bash
python -m media_scraper --topic "<topic>" --headless
```

## Verify it works
- Smoke-test the endpoint first (a tiny chat call to `base_url`) — see `tests/`.
- Run the pipeline test (no network/browser needed):
  ```bash
  python -m pytest tests/test_pipeline.py        # or: python tests/test_pipeline.py
  ```
- End-to-end: run a well-covered topic, confirm a report appears under `output_dir` with
  Summary, Key Findings, per-source sentiment + credibility, citations, and Steps Taken.

## Notes
- Never put the API key in `config.toml` or commit `.browser-profile/` or `reports/` — these
  are gitignored.
- If `ddgs` search starts returning nothing, the documented fallback is browser-driven search
  (see `research.md`).
