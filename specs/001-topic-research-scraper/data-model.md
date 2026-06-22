# Phase 1 Data Model: Topic Research Scraper

In-memory dataclasses passed between pipeline stages (no database). Persistence is limited to
the Playwright user-data dir (sessions) and the Markdown report file.

## Config
Loaded from `config.toml` + env. Secret never persisted to disk by the app.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| base_url | str | config.toml | OpenAI-compatible endpoint |
| model | str | config.toml | model name |
| api_key | str | env `MEDIA_SCRAPER_API_KEY` | never written to config/logs/report |
| output_dir | str/Path | config.toml | report destination |
| user_data_dir | str/Path | config.toml | Playwright persistent context dir (gitignored) |
| headless | bool | config.toml | default False (manual login needs a visible window) |
| max_sources | int | config.toml | per-run cap on gathered sources |
| max_chars_per_source | int | config.toml | per-source content truncation cap |

Validation: `base_url` and `model` required; `api_key` required at run start (clear error if
missing); `output_dir`/`user_data_dir` created if absent.

## ResearchPlan
Produced by `llm.plan(topic)` from JSON. See `contracts/llm-json.md`.

| Field | Type | Notes |
|-------|------|-------|
| topic | str | original user topic |
| sub_questions | list[str] | what to answer |
| search_queries | list[str] | web/news queries |
| rss_feeds | list[str] | candidate feed URLs (may be empty) |
| target_sites | list[str] | named sites/social to attempt (may require login) |

Validation: at least one of `search_queries`/`rss_feeds`/`target_sites` non-empty, else the
run reports "could not form a plan".

## Source
One gathered item, created during the gather stage.

| Field | Type | Notes |
|-------|------|-------|
| url | str | origin |
| title | str | best-effort title |
| kind | enum: web \| news \| rss \| social | how it was reached |
| text | str | extracted content (truncated to max_chars_per_source) |
| status | enum: ok \| login_skipped \| fetch_error | retrieval outcome |
| error | str \| None | message when status != ok |

Rule (FR-013): a Source with status != ok is retained and reported, never aborts the run.

## SourceAnalysis
Produced by `llm.analyze(source)` from JSON. See `contracts/llm-json.md`.

| Field | Type | Notes |
|-------|------|-------|
| url | str | back-reference to Source |
| claims | list[str] | key extracted claims |
| sentiment | enum: positive \| neutral \| negative \| mixed | overall lean |
| credibility | int 1–5 | 1=low, 5=high |
| credibility_rationale | str | short justification |

Only sources with status == ok are analyzed; skipped/errored sources are listed in the
report's appendix without analysis.

## Report
Assembled by `report.py`, written to `output_dir/<topic-slug>-<YYYYMMDD-HHMMSS>.md`.

Sections (FR-008): Title + topic; Summary; Key Findings; Per-Source Analysis (sentiment +
credibility + rationale + link); Sources/Citations; Steps Taken (the plan + what ran);
Appendix of skipped/failed sources.

## SessionState (external)
Not a Python object — the Playwright `user_data_dir` on disk. Reused across runs; gitignored;
holds cookies/localStorage from manual sign-ins. Expiry is handled by re-prompting on the
next blocked navigation.
