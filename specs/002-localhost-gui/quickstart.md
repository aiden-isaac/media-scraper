# Quickstart: Localhost GUI

**Date**: 2026-06-22

## Prerequisites

1. Python >=3.11 installed
2. `.venv` activated (`source .venv/bin/activate`)
3. Dependencies installed: `pip install -e ".[gui]"` (or add gui deps manually)
4. Playwright browsers installed: `playwright install chromium`
5. `MEDIA_SCRAPER_API_KEY` environment variable set

## Install GUI Dependencies

```bash
pip install fastapi uvicorn[standard] python-multipart markdown
```

These are the only new dependencies beyond what the CLI already requires.

## Start the GUI Server

```bash
python -m media_scraper.gui --port 8000
```

Or with custom host/port:

```bash
python -m media_scraper.gui --host 127.0.0.1 --port 8000
```

The server starts at `http://localhost:8000`.

## First Run

1. Open `http://localhost:8000` in your browser
2. Go to Settings and verify configuration (endpoint, model, output dir)
3. On the Home page, enter a research topic (e.g., "impact of AI on journalism")
4. Click "Start Research"
5. Watch progress update every ~2 seconds as phases complete
6. When done, click the report link to view the generated Markdown

## API Key Setup

The API key is read from the `MEDIA_SCRAPER_API_KEY` environment variable only. It cannot be set through the GUI. To configure it:

```bash
export MEDIA_SCRAPER_API_KEY="sk-your-key-here"
python -m media_scraper.gui
```

The GUI shows `api_key_set: true/false` but never displays the actual key value.

## Stopping the Server

Press `Ctrl+C` in the terminal to gracefully shut down the server.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Port already in use | Use `--port` flag with a different port number |
| "No module named media_scraper.gui" | Run `pip install -e .` to install the package in editable mode |
| Reports don't appear | Check that `output_dir` in config points to a writable directory |
| Scraper fails immediately | Verify `MEDIA_SCRAPER_API_KEY` is set and the LLM endpoint is reachable |
| Browser errors | Run `playwright install chromium` to install browser binaries |
