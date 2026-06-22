---
description: "Task list for Topic Research Scraper"
---

# Tasks: Topic Research Scraper

> **Status (2026-06-22)**: T001–T024 and T026 complete and committed (`f01c33f`); stub test
> passes, CLI/config verified. **Open**: T025 (end-to-end quickstart run) and T027 (manual
> gated-login check) — both require your live LLM endpoint + a desktop browser, so run them
> on your machine per `quickstart.md`.

**Input**: Design documents from `/specs/001-topic-research-scraper/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Light per constitution Principle V — exactly one runnable stub-LLM pipeline check
(no framework sprawl, no per-module suites).

**Organization**: Tasks grouped by user story (US1 P1 = MVP, US2 P2, US3 P3).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 / US2 / US3 (setup, foundational, polish have no story label)

## Path Conventions

Single project: package at `src/media_scraper/`, tests at `tests/`, config/manifest at repo root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project skeleton and dependencies.

- [ ] T001 Create the project tree: `src/media_scraper/` and `tests/` directories
- [ ] T002 Create `pyproject.toml` (Python ≥3.11; deps: `playwright`, `openai`, `feedparser`, `ddgs`, `rich`; `media-scraper` console entry point → `media_scraper.cli:main`)
- [ ] T003 [P] Create `.gitignore` excluding secrets, the Playwright user-data dir (`.browser-profile/`), `reports/`, `__pycache__/`, `.venv/`, `*.egg-info/`
- [ ] T004 [P] Create `config.toml` template at repo root (`base_url`, `model`, `output_dir`, `user_data_dir`, `headless`, `max_sources`, `max_chars_per_source`) — NO secret field
- [ ] T005 [P] Create `README.md` with install + quickstart (from `specs/001-topic-research-scraper/quickstart.md`)
- [ ] T006 [P] Create `src/media_scraper/__init__.py` and `src/media_scraper/__main__.py` (calls `cli.main()`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared types, config, and the LLM client that every story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T007 [P] Define dataclasses `Config`, `ResearchPlan`, `Source`, `SourceAnalysis` in `src/media_scraper/models.py` per `data-model.md` (incl. `Source.status` and `SourceAnalysis` enums)
- [ ] T008 Implement `src/media_scraper/config.py`: load `config.toml` via stdlib `tomllib`, read secret from env `MEDIA_SCRAPER_API_KEY`, apply defaults, create `output_dir`/`user_data_dir`; never log/persist the secret
- [ ] T009 Implement `src/media_scraper/llm.py` client base: build the `openai` client from `Config` (base_url/model/key); `_chat_json()` (strict JSON-only prompt + one JSON-repair retry) and `_chat_text()`; raise a clear error when the backend is unreachable or returns unusable output (maps to exit code 2)

**Checkpoint**: Types + config + LLM transport ready — user stories can begin.

---

## Phase 3: User Story 1 - Research a topic and get a report (Priority: P1) 🎯 MVP

**Goal**: Topic → researched, analyzed Markdown report from open sources (web/news/RSS +
direct page fetch). Viable product on its own.

**Independent Test**: Run an open-coverage topic with `--headless`; confirm a report file is
written containing summary, key findings, per-source sentiment + credibility, citations, and
steps taken — with no manual sign-in.

### Implementation for User Story 1

- [ ] T010 [P] [US1] Implement `web_search(query)` (ddgs) and `fetch_rss(feed_url)` (feedparser) plus a `gather(plan, ...)` dispatch in `src/media_scraper/sources.py`
- [ ] T011 [P] [US1] Implement basic page fetch in `src/media_scraper/browser.py`: Playwright navigate + `inner_text("body")` + whitespace cleanup + truncate to `max_chars_per_source` (headless-capable; no login handling yet)
- [ ] T012 [US1] Implement `plan()`, `analyze()`, `synthesize()` in `src/media_scraper/llm.py` per `contracts/llm-json.md` (validate enums/ranges; default-on-invalid for analysis)
- [ ] T013 [US1] Implement `src/media_scraper/report.py`: assemble Markdown with all required sections, guarantee sections even if the model omits one, write to `output_dir/<topic-slug>-<YYYYMMDD-HHMMSS>.md`
- [ ] T014 [US1] Implement `src/media_scraper/pipeline.py`: orchestrate `plan → gather → analyze → synthesize`; catch per-source failures (record `fetch_error`, continue); accept a `log` callback; enforce `max_sources`
- [ ] T015 [US1] Implement minimal run path in `src/media_scraper/cli.py`: parse flags (`--topic`, `--config`, `--headless`, etc.), load config, prompt topic if absent, run pipeline, print report path, return exit codes (0/1/2/3 per `contracts/cli.md`)
- [ ] T016 [US1] Add `tests/test_pipeline.py`: stub LLM (canned plan + analyses) + stub gather; assert the report file contains every required section and that one failing source does not abort the run

**Checkpoint**: MVP — open-source topic research produces a complete report.

---

## Phase 4: User Story 2 - Account-gated sources via manual sign-in (Priority: P2)

**Goal**: Reach login-gated / captcha-protected sources by pausing for the human to sign in
in a visible browser, with sessions persisted across runs.

**Independent Test**: Run a topic needing a login-gated source; confirm the tool shows a
browser and pauses, resumes after manual sign-in, includes the gated content, and on a second
run reuses the session without prompting.

### Implementation for User Story 2

- [ ] T017 [US2] Extend `src/media_scraper/browser.py` to launch a **persistent** context (`launch_persistent_context(user_data_dir, headless=False)`) so logins persist across runs
- [ ] T018 [US2] Add login/captcha detection + manual pause/resume in `src/media_scraper/browser.py` (heuristic: login redirect / known selectors / thin page text; prompt via the `log`/pause hook; re-check; mark `login_skipped` if still blocked)
- [ ] T019 [US2] Implement gated/social page scraping through the persistent context in `src/media_scraper/browser.py`
- [ ] T020 [US2] Route `plan.target_sites` (and social URLs) through the browser gated path in `src/media_scraper/sources.py` / `pipeline.py`, tagging results `kind="social"`

**Checkpoint**: US1 + US2 — open and account-gated sources both work; sessions reused.

---

## Phase 5: User Story 3 - Configure the backend and follow progress (Priority: P3)

**Goal**: Configure LLM endpoint/model/output via a simple terminal UI and see streaming
phase logs and unambiguous login pauses.

**Independent Test**: Launch with no/partial config; set endpoint, model, and output dir via
the editor; run a short topic and confirm each phase logs and settings are applied.

### Implementation for User Story 3

- [ ] T021 [US3] Implement the interactive config editor (`--configure`) in `src/media_scraper/cli.py` using `rich.prompt` (write `config.toml` without any secret)
- [ ] T022 [US3] Wire streaming phase logs throughout the run: pass a `rich.Console`-backed `log` callback into `pipeline.py`; redact any secret-looking values from log output
- [ ] T023 [US3] Surface manual-login pauses prominently in the TUI and add the startup secret check (clear message + exit 1 when `MEDIA_SCRAPER_API_KEY` is missing)

**Checkpoint**: All three stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T024 [P] Update `README.md`/quickstart notes: `playwright install chromium`, the ddgs→browser-search fallback, and the manual-login UX
- [ ] T025 Run `specs/001-topic-research-scraper/quickstart.md` end-to-end on an open-coverage topic and confirm all report sections (SC-001, SC-002)
- [ ] T026 [P] Verify no secret leaks: grep committed files, a sample report, and captured logs for the key value (SC-005)
- [ ] T027 Manual check: a gated source login → resume → reuse on a second run (SC-003)

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (P1)**: no dependencies.
- **Foundational (P2)**: after Setup; **blocks all user stories**.
- **User Stories**: all depend on Foundational. US1 first (MVP). US2 and US3 build on US1's
  browser/cli/pipeline but are independently testable.
- **Polish**: after the desired stories are complete.

### User Story Dependencies
- **US1 (P1)**: after Foundational. No dependency on other stories.
- **US2 (P2)**: extends `browser.py` and source dispatch from US1; testable on its own.
- **US3 (P3)**: extends `cli.py`/logging from US1; testable on its own.

### Within a story
- models → config/llm → sources/browser/report → pipeline → cli.
- The single pipeline test (T016) lands at the end of US1.

### Parallel Opportunities
- Setup: T003, T004, T005, T006 in parallel.
- Foundational: T007 parallel with the start of T008/T009 (different files).
- US1: T010 and T011 in parallel (different files) before T012–T015.
- Polish: T024 and T026 in parallel.

---

## Parallel Example: User Story 1

```bash
# Different files, no inter-dependencies — can run together:
Task: "Implement sources.py (web_search via ddgs, fetch_rss via feedparser)"
Task: "Implement browser.py basic page fetch (navigate + inner_text + truncate)"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)
1. Phase 1 Setup → 2. Phase 2 Foundational → 3. Phase 3 US1 → **STOP & validate** the report
on an open-coverage topic (`--headless`). This is a usable tool.

### Incremental Delivery
US1 (MVP) → add US2 (gated sources) → add US3 (config + progress polish) → Polish. Each step
adds value without breaking the previous.

---

## Notes
- [P] = different files, no dependencies.
- Tests kept to one stub-LLM pipeline check (constitution Principle V) — do not add per-module
  suites unless asked.
- Never commit secrets, `.browser-profile/`, or `reports/` (T003).
- Total: 27 tasks — Setup 6, Foundational 3, US1 7, US2 4, US3 3, Polish 4.
