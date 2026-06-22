# media-scraper — agent instructions

## Setup & environment
- Python >=3.11, managed via `.venv/` (gitignored). Install deps with: `pip install -e .`
- LLM key via env var `MEDIA_SCRAPER_API_KEY` — never commit `.env`.
- Browser profile lives in `.browser-profile/` (Playwright persistent context, gitignored).

## Running
- Entry point: `python -m media_scraper` or `media-scraper` CLI script.
- Config: `config.toml` (override per-run; see `src/media_scraper/config.py`).
- Reports written to `reports/` (gitignored).

## Tests
```
python tests/test_pipeline.py       # standalone stub-LLM test
python -m pytest tests/test_pipeline.py  # via pytest
```
No network or browser required for the test suite — it uses a `StubLLM` and fake sources.

## Architecture at a glance
| Module | Responsibility |
|---|---|
| `cli.py` | CLI entry, arg parsing |
| `config.py` | Load `config.toml`, merge env vars |
| `llm.py` | OpenAI-compatible API client (`plan`, `analyze`, `synthesize`) |
| `pipeline.py` | Orchestrates plan → gather → analyze → synthesize → report |
| `sources.py` | Web scraping via Playwright, RSS/feedparser, DDGS, social sources |
| `report.py` | Markdown report generation |
| `models.py` | Pydantic data models (`Config`, `ResearchPlan`, `Source`, `SourceAnalysis`) |
| `browser.py` | Playwright persistent-browser helper |

## Constraints & conventions
- All reports must include sections: `Summary & Key Findings`, `Per-Source Analysis`, `Sources`, `Steps Taken`, and `Appendix: Skipped or Failed Sources`.
- Failed sources are not dropped — they appear in the appendix.
- The stub-LLM test (`tests/test_pipeline.py`) is the canonical verification that these invariants hold. Run it after any pipeline change.
- No lint/typecheck/formatter config exists — keep code style consistent with existing files.

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->
