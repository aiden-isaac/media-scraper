# Implementation Plan: Topic Research Scraper

**Branch**: `001-topic-research-scraper` | **Date**: 2026-06-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-topic-research-scraper/spec.md`

## Summary

A single-user Python CLI that takes a free-text research topic, uses a configurable
OpenAI-compatible LLM to plan the research, gathers from open web/news, RSS/Atom, and
account-gated social media (with manual human sign-in in a headed Playwright browser),
analyzes each source (claims, sentiment, credibility), and synthesizes a Markdown report.
The orchestrator drives control flow by parsing structured JSON the LLM returns and calling
in-process Python functions — not the model's native tool-calling, not MCP, not skills.

## Technical Context

**Language/Version**: Python 3.11+ (stdlib `tomllib` for config)

**Primary Dependencies**: `playwright` (headed persistent-context browser), `openai`
(OpenAI-compatible client), `feedparser` (RSS/Atom), `ddgs` (keyless web/news search),
`rich` (TUI: streaming logs + prompts)

**Storage**: Local filesystem only — Playwright user-data dir (persisted sessions),
`config.toml` (no secrets), Markdown report files. No database.

**Testing**: Light. One runnable stub-LLM check covering the pipeline + report assembly
(`tests/test_pipeline.py`), `assert`-based, no heavy frameworks/fixtures.

**Target Platform**: Local desktop with a graphical environment (a visible browser window is
required for manual sign-in). Linux primary; cross-platform where Playwright supports it.

**Project Type**: Single-project CLI application.

**Performance Goals**: Not latency-critical. Bounded runs (per-run caps on source count and
per-source content length) so a topic completes in a reasonable interactive session.

**Constraints**: Secret (LLM API key) from env (`MEDIA_SCRAPER_API_KEY`), never logged or
committed. Playwright user-data dir, reports, and any secret-bearing config gitignored. Must
not store/enter credentials or solve captchas. Individual source failures must not abort a
run. LLM-unreachable / unusable-output must fail gracefully (no partial report).

**Scale/Scope**: One user, one machine, one run at a time. ~6 source modules, ~600–900 LOC.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Lazy & Minimal (YAGNI) | ✅ PASS | 5 justified deps; stdlib config; sync Playwright; no abstractions beyond the 6 cohesive modules; Markdown-only output; rich (no Textual). |
| II. Human-in-the-Loop Auth | ✅ PASS | Headed browser + manual sign-in/captcha pause; no credential storage; no captcha solver (FR-004, FR-006). |
| III. Provider-Agnostic, Orchestrator-Driven LLM | ✅ PASS | OpenAI-compatible base_url/model/key; secret from env; orchestrator parses JSON and calls functions (FR-002, FR-007, FR-011). |
| IV. Respectful Scraping & Local Sessions | ✅ PASS | Persistent user-data dir reuses logins; bounded request volume; user-data dir gitignored (FR-005). |
| V. Light, Runnable Testing | ✅ PASS | Single stub-LLM pipeline test; no framework sprawl. |
| VI. Simple Terminal Interface | ✅ PASS | `rich` logs + prompts only; no multi-panel TUI (FR-010, FR-012). |

**Initial gate: PASS.** No violations → Complexity Tracking left empty.
**Post-design re-check: PASS** (design below introduces no new dependencies or abstractions).

## Project Structure

### Documentation (this feature)

```text
specs/001-topic-research-scraper/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── cli.md           # CLI command surface
│   └── llm-json.md      # LLM request/response JSON contracts (plan, analysis)
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
pyproject.toml                 # project metadata, deps, `media-scraper` entry point
config.toml                    # base_url, model, output_dir, user_data_dir, headless, caps (NO secret)
.gitignore                     # secrets, user-data dir, reports, venv, caches
README.md                      # short usage note
src/media_scraper/
├── __init__.py
├── __main__.py                # `python -m media_scraper` → cli.main()
├── config.py                  # load/merge config.toml + env secret; defaults
├── cli.py                     # rich TUI: configure, topic prompt, run, login pauses, logs
├── llm.py                     # openai client wrapper: plan() / analyze() / synthesize(); JSON parse + repair retry
├── browser.py                 # Playwright persistent context; fetch_page/scrape; login+captcha detect & pause
├── sources.py                 # web_search (ddgs), fetch_rss (feedparser), dispatch by source type
├── pipeline.py                # orchestrate plan -> gather -> analyze -> synthesize
└── report.py                  # assemble Markdown -> output_dir/<slug>-<date>.md
tests/
└── test_pipeline.py           # stub-LLM check: plan parse + analysis + report assembly
```

**Structure Decision**: Single-project CLI (constitution Principle I — fewest files). Each
module is one cohesive responsibility; `pipeline.py` is the only orchestrator and the only
place the stages are wired together, which keeps the stub-LLM test simple.

## Complexity Tracking

> No constitution violations. Section intentionally empty.
