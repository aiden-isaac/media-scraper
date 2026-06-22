# Phase 0 Research: Topic Research Scraper

All Technical Context items are resolved (no NEEDS CLARIFICATION remain). Decisions below.

## LLM connection: native tool-calling vs MCP vs orchestrator-driven JSON

- **Decision**: Orchestrator-driven structured JSON. The LLM returns JSON (a research plan,
  then per-source analyses) that the Python orchestrator parses and acts on by calling
  in-process functions. Reached via the `openai` SDK against a configurable OpenAI-compatible
  `base_url`.
- **Rationale**: The default backend is a local LiteLLM→Qwen whose native tool-calling is
  unreliable (the user's own model config patches XML-tag tool formatting). Orchestrator-
  driven JSON is deterministic, portable across providers, and needs no protocol layer. MCP
  is for exposing tools to *external* hosts or reaching *remote* MCP servers — irrelevant for
  a self-contained app. Skills are an authoring concept, not runtime wiring.
- **Alternatives considered**: (a) Native function/tool calling — rejected: flaky on the
  target local model. (b) MCP server/client — rejected: protocol + process overhead for zero
  benefit in-process. (c) Anthropic SDK — rejected: backend is OpenAI-compatible, not Claude.
- **Robustness**: strict "JSON only" prompting + one JSON-repair retry (re-ask the model to
  return valid JSON) before failing the stage.

## Browser automation & persistent manual login

- **Decision**: Playwright **sync** API, `launch_persistent_context(user_data_dir=…,
  headless=False)`. Cookies/localStorage persist in the user-data dir across runs.
- **Rationale**: Persistent context is the native mechanism for session reuse — no custom
  cookie handling. Headed mode lets the human sign in / solve captchas in the real window.
  Sync API keeps the whole app synchronous (no asyncio mixing) — lazier and simpler.
- **Login/captcha detection**: heuristic — after navigation, check for login/captcha signals
  (URL redirect to a login path, known login/consent selectors, very thin page text). On
  detection, surface a `rich` prompt ("sign in / solve the challenge in the browser, then
  press Enter") and re-check after the user confirms; skip the source if still blocked.
- **Alternatives considered**: async Playwright (rejected: needs an event loop around the
  whole pipeline for no gain); storage_state JSON export/import (rejected: persistent context
  is simpler and also persists service-worker/IndexedDB state).

## Web/news search without an API key

- **Decision**: `ddgs` (DuckDuckGo search) for general web + news result URLs.
- **Rationale**: Keyless, purpose-built, returns titles + URLs to feed the fetch stage.
- **Alternatives considered**: paid search APIs (rejected: extra config/cost/keys); scraping
  a search-engine results page via Playwright (kept as the documented **fallback** if `ddgs`
  becomes unreliable — reuses the browser we already have, but more fragile/anti-bot-prone).

## RSS/Atom ingestion

- **Decision**: `feedparser`. Topic-relevant feed URLs come from the LLM plan and/or
  discovered links; entries provide title, link, summary.
- **Rationale**: De-facto standard, handles RSS + Atom + malformed feeds. One small dep.
- **Alternatives considered**: hand-rolled XML parsing (rejected: feed quirks are exactly
  what feedparser already solves — Principle I says use the existing dependency).

## Page text extraction

- **Decision**: Playwright `page.inner_text("body")` + light whitespace/boilerplate cleanup,
  truncated to a per-source character cap before analysis.
- **Rationale**: Zero extra dependency; good enough for the LLM to analyze. Truncation keeps
  prompts bounded.
- **Alternatives considered**: `trafilatura`/readability (better article isolation) — deferred
  as an optional upgrade only if analysis quality is poor (Principle I: don't add the dep
  until measured need).

## Terminal UI

- **Decision**: `rich` — `Console` for streaming phase logs; `rich.prompt` for configuration
  and the manual-login pauses.
- **Rationale**: Matches "simple TUI for now"; one dep covers logs + prompts.
- **Alternatives considered**: `Textual` multi-panel app (rejected: out of scope/over-built);
  bare `print()` + `input()` (rejected: poorer log readability for little savings).

## Configuration & secrets

- **Decision**: `config.toml` (stdlib `tomllib`) for `base_url`, `model`, `output_dir`,
  `user_data_dir`, `headless`, and per-run caps; the LLM API key from env
  (`MEDIA_SCRAPER_API_KEY`). `.gitignore` excludes secrets, the user-data dir, and reports.
- **Rationale**: `tomllib` is stdlib (no dep). Env-only secret keeps keys out of git/logs
  (Principle III, FR-011).
- **Alternatives considered**: `.env` + `python-dotenv` (rejected: extra dep; env var is
  enough); a key field in `config.toml` (rejected: invites committing secrets).

## Pipeline shape

- **Decision**: Fixed `plan → gather → analyze → synthesize` orchestrated in `pipeline.py`;
  LLM reasons at plan/analyze/synthesize, code performs gather. Per-source failures are caught
  and recorded; the run continues.
- **Rationale**: A fixed pipeline is more reliable with a weak local model than a free-form
  agentic loop, and it makes the single stub-LLM test straightforward. Upgradeable to a true
  tool-call loop later with no structural change.
- **Alternatives considered**: fully autonomous tool-call loop (rejected for v1: depends on
  reliable tool-calling the target model lacks).

## Testing approach

- **Decision**: One `tests/test_pipeline.py` driving the pipeline with a stub LLM (canned
  plan + analyses) and a stub gather, asserting a report file with all required sections is
  produced and that a single failed source doesn't abort.
- **Rationale**: Principle V — smallest check that fails if the orchestration/report logic
  breaks, no network or browser needed.
