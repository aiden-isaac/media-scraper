---

description: "Task list for Recurring Brand-Perception & Competitive Intelligence"
---

# Tasks: Recurring Brand-Perception & Competitive Intelligence

**Input**: Design documents from `/specs/003-competitive-intel/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md

**Tests**: Included per constitution Principle V (extend the single stub-LLM
`tests/test_pipeline.py`; no new framework). No other test scaffolding added.

**Organization**: Grouped by user story (US1 P1, US2 P2, US3 P3) for independent
implementation and testing. All paths are under the existing
`src/media_scraper/` package — this is a lean in-place extension, no new deps.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete dependencies)
- **[Story]**: US1 / US2 / US3 (setup, foundational, polish carry no story label)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Wiring with no logic; safe to do first.

- [X] T001 [P] Add `.state/` to `.gitignore`
- [X] T002 [P] Add brief keys (`brand`, `competitors`, `platforms`, `recency_days`, `max_sources`) for the Pos Malaysia brief to `config.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared data-model/config changes every story depends on.

**⚠️ CRITICAL**: No user story work begins until this phase is complete.

- [X] T003 Extend `Config` dataclass with `brand: str`, `competitors: list[str]`, `platforms: list[str]`, `recency_days: int` in `src/media_scraper/models.py`
- [X] T004 Extend `SourceAnalysis` dataclass with `subject: str = ""` in `src/media_scraper/models.py`
- [X] T005 Update `DEFAULTS` and `load_config` to read the new fields (TOML arrays → lists, ints), keep secret env-only, and validate (`recency_days >= 0`, `max_sources >= 1`) in `src/media_scraper/config.py`

**Checkpoint**: Models/config carry the brief; stories can begin.

---

## Phase 3: User Story 1 - Comparative brand-perception report (Priority: P1) 🎯 MVP

**Goal**: Produce a report whose centerpiece is a per-brand competitive
sentiment table, attributing each source to the brand it concerns. Works on
web/news sources alone (before social).

**Independent Test**: Run with a brand + competitors; confirm the report's
Competitive Sentiment table covers all named brands and each source is
attributed to a brand.

- [X] T006 [P] [US1] Add `subject` to the `analyze()` JSON prompt and normalize the returned value against `[brand] + competitors` (case-insensitive; unknown → `"other"`) in `src/media_scraper/llm.py`
- [X] T007 [US1] Inject brand + competitors (+ recency hint) into the `plan()` prompt so generated queries are comparative in `src/media_scraper/llm.py`
- [X] T008 [US1] Aggregate analyzed sources by `subject` and render a **Competitive Sentiment** section (per-brand positive/neutral/negative counts, avg credibility, mention count; zero-rows for brands with no mentions) plus a "new since last run" note in `src/media_scraper/report.py`
- [X] T009 [US1] Extend `tests/test_pipeline.py` with a self-check that the stub-LLM subjects are tallied per brand and the Competitive Sentiment table renders for all brands

**Checkpoint**: US1 delivers the competitive report independently.

---

## Phase 4: User Story 2 - Social-media coverage via in-site search (Priority: P2)

**Goal**: Gather social posts by searching *within* each platform (search-URL,
DOM-fill fallback) and a keyless `site:` fallback; reuse the persistent login for
walled sites. Fix the malformed-handle bug.

**Independent Test**: Configure social platforms, run, confirm
platform-originated posts/links appear among gathered sources.

- [X] T010 [P] [US2] Add the per-platform search-URL map and helpers (`search_url(platform, query)`, `site_query(platform, terms)`) in `src/media_scraper/sources.py`
- [X] T011 [US2] Add `Browser.search_site(platform, query, limit)` — navigate the search URL, extract result links/snippets as `Source`s, DOM search-box fill + submit as fallback — in `src/media_scraper/browser.py`
- [X] T012 [US2] Fix bare-`@handle`/bare-domain normalization so it never yields `https://@handle` in `src/media_scraper/pipeline.py`
- [X] T013 [US2] Expand `gather_sources` to run in-site search per platform × brand/competitor, falling back to keyless `site:` `web_search` when blocked/headless, recording results as `kind="social"` in `src/media_scraper/pipeline.py`
- [X] T014 [US2] Confirm walled-but-unresolved social sources remain `login_skipped` in the appendix via the new path (extend the stub-LLM check in `tests/test_pipeline.py` if a gather branch is now non-trivial)

**Checkpoint**: US1 + US2 work; reports now include social sentiment.

---

## Phase 5: User Story 3 - Recurring "latest-only" runs (Priority: P3)

**Goal**: Recency window, cross-run dedup, the reach knob, and a non-interactive
`--brief` mode for OS-cron scheduling.

**Independent Test**: Run `--brief` twice within the window; second report's
sources contain only new items; an unattended run produces a timestamped report
with no prompts.

- [X] T015 [P] [US3] Create `src/media_scraper/state.py` with `load_seen(slug)` / `save_seen(slug, urls)` over `.state/<slug>.json` (stdlib `json`; `ponytail:` flat-set ceiling note)
- [X] T016 [US3] Add a `timelimit` parameter to `web_search()` and map `recency_days` → `d`/`w`/`m`/`y`; append `sort=new`/`f=live` to social search URLs where supported in `src/media_scraper/sources.py`
- [X] T017 [US3] Apply recency to gathering + planner, skip already-seen URLs during gather, and write seen-state only after a report is successfully written; add the `ponytail:` no-recursive-crawl note in `src/media_scraper/pipeline.py`
- [X] T018 [US3] Add CLI flags `--max-sources`, `--days`/`--since` (mutually exclusive), and `--brief` (builds the run from config; requires `brand`, else exit 1) and wire overrides in `src/media_scraper/cli.py`
- [X] T019 [US3] Extend `tests/test_pipeline.py` with a dedup self-check (a URL present in seen-state is skipped on the next run)

**Checkpoint**: All three stories independently functional; cron-ready.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T020 [P] Document `--brief`, `--days`/`--since`, `--max-sources`, the cron line, and the one-time-headed-login note in `AGENTS.md`
- [X] T021 Run `python -m pytest tests/test_pipeline.py` and execute the quickstart validations (SC-001 … SC-006) from `specs/003-competitive-intel/quickstart.md`
- [X] T022 Constitution re-check: confirm `pyproject.toml` gained no new runtime dependency and the diff stays minimal

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup; **blocks all user stories**.
- **US1 (Phase 3)**: after Foundational. MVP.
- **US2 (Phase 4)**: after Foundational. Independent of US1, but its social
  sources flow into US1's competitive table when both are present.
- **US3 (Phase 5)**: after Foundational. Recency/dedup/`--brief` wrap the gather
  loop US2 extends; deliver after US2 for the full cron experience, but the
  dedup/recency/CLI pieces are testable on web/news alone.
- **Polish (Phase 6)**: after the desired stories.

### Within Each User Story

- Models/config (Phase 2) before any story logic.
- For US2: `sources.py` helpers (T010) before the browser method (T011) before
  the gather wiring (T013).
- For US3: `state.py` (T015) and `sources` recency (T016) before the pipeline
  wiring (T017) and CLI (T018).

### Parallel Opportunities

- T001, T002 (Setup) in parallel.
- T006 (llm prompt) ∥ early US2 helper T010 once Foundational is done.
- T015 (`state.py`) ∥ T016 (`sources` recency) — different files.
- T020, T022 (docs / dep check) in parallel during Polish.

---

## Parallel Example: Foundational → US1 start

```bash
# After T003–T005 land:
Task: "Add subject to analyze() prompt + normalization in src/media_scraper/llm.py"   # T006
Task: "Add per-platform search-URL map/helpers in src/media_scraper/sources.py"        # T010 (US2 prep)
Task: "Create src/media_scraper/state.py seen-URL store"                               # T015 (US3 prep)
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1 Setup → Phase 2 Foundational.
2. Phase 3 US1 → **stop and validate**: report shows the competitive sentiment
   table for Pos Malaysia + the five competitors from web/news (SC-001).
3. Demo.

### Incremental Delivery

1. Foundational ready.
2. + US1 → competitive report (MVP). 3. + US2 → social coverage. 4. + US3 →
   recency + dedup + `--brief` cron. Each adds value without breaking the prior.

---

## Notes

- [P] = different files, no incomplete dependency.
- No new runtime dependency is introduced (constitution Principle I); recency
  uses `ddgs` `timelimit`, state uses stdlib `json`, scheduling uses OS cron.
- Tests stay within the single stub-LLM `tests/test_pipeline.py`.
- Walled social sites require a one-time headed login; document, do not automate.
