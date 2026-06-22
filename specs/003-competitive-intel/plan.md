# Implementation Plan: Recurring Brand-Perception & Competitive Intelligence

**Branch**: `003-competitive-intel` | **Date**: 2026-06-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-competitive-intel/spec.md`

## Summary

Extend the existing topic-research-scraper into a recurring brand-vs-competitor
intelligence tool. The four-stage pipeline (plan → gather → analyze →
synthesize) is preserved; the feature adds: (1) **in-site social search** —
drive the browser to each platform's own search and reuse a one-time login,
with a keyless `site:` web-search fallback that works unattended; (2) a
**recency window** mapped to the search backend's native date filter; (3) a
**reach** knob (`--max-sources`) plus query expansion across brand × competitors
× platforms; (4) **per-brand competitive sentiment** in the report; (5) a small
JSON **seen-state** file for "latest only" dedup across runs; (6) a
non-interactive **`--brief`** mode driven from config, scheduled with OS cron.
No new dependencies — `ddgs` already supports `timelimit`, stdlib `json` covers
state, Playwright already drives the browser, OS cron does scheduling.

## Technical Context

**Language/Version**: Python 3.11+ (existing requirement)

**Primary Dependencies**: existing only — `playwright`, `openai`, `feedparser`,
`ddgs`, `rich`. **No additions.** (`ddgs.text(timelimit=...)` and stdlib `json`
cover the new needs.)

**Storage**: Files only. Markdown reports in `output_dir/` (existing); new
per-brief seen-state JSON under a gitignored `.state/<slug>.json`. No database.

**Testing**: stub-LLM `tests/test_pipeline.py` extended with self-checks for
dedup and the competitive tally (Principle V — one runnable check per non-trivial
path, no new framework).

**Target Platform**: Local CLI on Linux/macOS; headed browser for one-time
logins, headless for cron.

**Project Type**: Single-project CLI (existing `src/media_scraper/` package).

**Performance Goals**: Not latency-critical; runs are bounded by `max_sources`.
Cron runs complete unattended within minutes.

**Constraints**: No new runtime dependency; no DB; no in-app scheduler; secrets
stay env-only; human-in-the-loop auth (no credential storage / captcha solving);
walled-site reads only via reused manual sessions.

**Scale/Scope**: Single user, single brief at a time. Typical run gathers up to
`max_sources` (default 12, now CLI-tunable) across web/news/RSS/social.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Lazy & Minimal (YAGNI) | ✅ PASS | Zero new deps; reuse `ddgs` date filter, stdlib `json`, OS cron, existing browser. Recursive crawler explicitly rejected. New code is additive to existing modules + one ~20-line `state.py`. |
| II. Human-in-the-Loop Auth | ✅ PASS | Walled social sites read only via the existing manual-login/persistent-session path. No credential storage, no captcha solving. Keyless `site:` fallback needs no login. |
| III. Provider-Agnostic, Orchestrator-Driven LLM | ✅ PASS | New `subject` (brand attribution) is one more JSON key in the existing orchestrator-parsed `analyze()`; no native tool-calling introduced. |
| IV. Respectful Scraping & Local Sessions | ✅ PASS | In-site search uses each site's own search (not aggressive crawling); `max_sources` caps volume; recency narrows queries; sessions persist in the gitignored profile dir. `.state/` added to `.gitignore`. |
| V. Light, Runnable Testing | ✅ PASS | Extend the single stub-LLM test with dedup + tally asserts; no new framework/fixtures. |
| VI. Simple Terminal Interface | ✅ PASS | New flags (`--brief`, `--days`/`--since`, `--max-sources`) use the existing `argparse`/`rich` surface; no new UI. |

**Result**: PASS — no violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/003-competitive-intel/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cli.md           # CLI flags + brief config + cron contract
├── checklists/
│   └── requirements.md  # Spec quality checklist (from /speckit-specify)
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
src/media_scraper/
├── models.py        # +Config.competitors/platforms/recency_days; +SourceAnalysis.subject
├── config.py        # load/save the new fields; defaults; .state dir helper
├── cli.py           # +--max-sources, --days/--since, --brief; wire overrides
├── sources.py       # web_search(timelimit=); per-platform search-URL map; site: expansion
├── browser.py       # +search_site(); DOM search-box fallback; fix @handle normalization
├── pipeline.py      # query expansion (brand×competitors×platforms); in-site search;
│                    #   apply recency + dedup; ponytail note: no recursive crawl
├── llm.py           # plan() prompt takes competitors/platforms/recency; analyze() -> subject
├── report.py        # +Competitive Sentiment table; "new since last run" note
└── state.py         # NEW ~20 lines: load_seen(slug)/save_seen(slug, urls) JSON

tests/
└── test_pipeline.py # extend: dedup skip + per-brand tally asserts

config.toml          # add competitors, platforms, recency_days for the Pos Malaysia brief
AGENTS.md            # document --brief, recency flags, cron line, one-time-login note
.gitignore           # add .state/
```

**Structure Decision**: Single-project CLI; all changes land in the existing
`src/media_scraper/` package plus one new small module (`state.py`). No new
top-level directories, services, or test trees — consistent with the existing
layout and Principle I.

## Complexity Tracking

> No constitution violations. Section intentionally empty.
