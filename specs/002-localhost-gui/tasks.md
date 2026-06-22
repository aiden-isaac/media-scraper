# Tasks: Localhost GUI

**Input**: Design documents from `/specs/002-localhost-gui/`
**Tests**: Included — pytest-based tests for endpoints and scraper integration

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Create `src/media_scraper/gui.py` as FastAPI app entry point
- [ ] [P] Create `src/media_scraper/templates/` directory with base template files
- [ ] [P] Create `src/media_scraper/static/style.css` for minimal styling
- [ ] [P] Add `fastapi`, `uvicorn[standard]`, `python-multipart`, `markdown` to `pyproject.toml` dependencies
- [ ] [P] Update `.gitignore` to exclude `__pycache__/`, `.venv/`, `*.egg-info/` if not already present

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] Implement `RunState` in-memory tracker in `src/media_scraper/gui.py` — thread-safe singleton holding current scraper run state (`topic`, `status`, `phase`, `report_path`, `error_message`, timestamps)
- [ ] T003 [P] Implement `_load_config()` helper in `gui.py` that reads existing `config.toml` via `media_scraper.config.load_config()` and returns non-secret values for the GUI
- [ ] T004 [P] Implement `_save_config()` helper in `gui.py` that writes config changes back to `config.toml` using existing `media_scraper.config.save_config()`, preserving API key from environment
- [ ] T005 [P] Implement `_list_reports(output_dir)` helper in `gui.py` that scans the output directory for `.md` files and returns sorted `ReportItem` metadata (filename, topic extracted from filename, path, timestamp)
- [ ] T006 [P] Create Jinja2 `base.html` template with nav bar, flash message area, and consistent layout structure
- [ ] T007 Configure FastAPI app with static file mounting at `/static`, template dir at `/templates`, and enable CORS disabled (localhost only)
- [ ] T008 Set up error handling middleware that catches exceptions, logs them, and returns friendly HTML error pages (not JSON) for page routes while returning JSON for `/api/` routes
- [ ] T009 Implement `_run_scraper_background(topic, cfg, llm)` function in `gui.py` that launches the existing `pipeline.run()` in a background thread, updates `RunState` through phases, and handles errors gracefully without crashing the server

**Checkpoint**: Foundation ready — config loading, report listing, background scraper runner, and base templates are all in place. User story implementation can now begin in parallel.

---

## Phase 3: User Story 1 — Run a Scraper from the Web UI (Priority: P1) 🎯 MVP

**Goal**: Users can enter a research topic, watch progress, and see results through the web interface.

**Independent Test**: Start the server, open the page, enter a topic, submit, and confirm the scraper runs end-to-end with visible progress updates.

### Implementation for User Story 1

- [ ] T010 [US1] Create `GET /` route handler that renders `index.html` with initial state (`status: "idle"`)
- [ ] [P] T011 [US1] Create `index.html` template with: (a) topic input form (text field + submit button), (b) progress display area that shows current phase, (c) result area that shows success/error messages and report link
- [ ] [P] T012 [US1] Implement `POST /api/run/start` endpoint — accepts `{ "topic": "..." }`, validates topic length (1–5000 chars), checks if a scraper is already running (returns 409 if so), starts background scraper thread, returns 201 with accepted status
- [ ] [P] T013 [US1] Implement `GET /api/run/status` endpoint — returns current `RunState` serialized as JSON (`topic`, `status`, `phase`, `report_path`, `error_message`, `started_at`, `completed_at`)
- [ ] [P] T014 [US1] Implement `POST /api/run/cancel` endpoint — stops the background scraper thread (best-effort via threading event), updates `RunState` to `"cancelled"` or `"error"`, returns 200 or 400 if idle
- [ ] T015 [US1] Add JavaScript polling logic in `index.html` — client polls `/api/run/status` every 2 seconds when status is `"running"`, updates progress indicator DOM elements, switches to success/error view on completion
- [ ] T016 [US1] Add client-side form validation (empty topic check, character count) and server-side validation (non-empty, max length) with proper error responses
- [ ] T017 [US1] Wire `_run_scraper_background()` to update `RunState.phase` through each pipeline stage: `"planning"` → `"gathering"` → `"analyzing"` → `"synthesizing"` → `"complete"` (or `"error"` on failure)

**Checkpoint**: At this point, User Story 1 should be fully functional — a user can enter a topic, watch progress, and receive a completed report.

---

## Phase 4: User Story 2 — Manage Configuration Through the Web UI (Priority: P2)

**Goal**: Users can view and edit all non-secret configuration values through the settings page.

**Independent Test**: Open the settings page, modify a value, save, confirm it persists to disk, restart server and verify the setting is applied.

### Implementation for User Story 2

- [ ] T018 [P] Create `GET /config` route handler that renders `config.html` with current config values loaded via `_load_config()`
- [ ] [P] T019 [US2] Create `config.html` template with: (a) form fields for `base_url`, `model`, `output_dir`, `headless` checkbox, `max_sources`, `max_chars_per_source`, (b) API key shown as masked (`sk-****`), (c) save button with confirmation toast, (d) validation error display area
- [ ] [P] T020 [US2] Implement `GET /api/config` endpoint — returns current configuration via `_load_config()` with `api_key_set: true/false` but never the actual key value
- [ ] [P] T021 [US2] Implement `PUT /api/config` endpoint — accepts partial config updates, validates types (bool for headless, int for max_sources/max_chars), rejects any request containing `api_key` (403 Forbidden), calls `_save_config()`, returns updated config
- [ ] T022 [US2] Add client-side form validation in `config.html` — numeric fields must be positive integers, URL fields must look like URLs, required fields checked before submit
- [ ] T023 [US2] Add JS save handler in `config.html` — serializes form data to JSON, sends PUT request, shows success/error toast, refreshes displayed values on success

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently — users can run scrapers and manage config through the GUI.

---

## Phase 5: User Story 3 — View Past Reports (Priority: P3)

**Goal**: Users can browse previously generated reports, click to view them, and see metadata.

**Independent Test**: Generate two reports via the GUI, navigate to the reports page, confirm both appear with correct metadata, click a report and confirm it renders.

### Implementation for User Story 3

- [ ] T024 [P] Create `GET /reports` route handler that renders `reports.html` with report list from `_list_reports()`
- [ ] [P] T025 [US3] Create `reports.html` template with: (a) header "Reports", (b) table/list of reports showing filename, topic, date, source count, (c) "no reports yet" message when empty, (d) clickable rows linking to `/report/<filename>`
- [ ] [P] T026 [US3] Create `GET /report/<filename>` route handler that reads the markdown file, converts to HTML using the `markdown` library, and renders `report.html` template with rendered content
- [ ] [P] T027 [US3] Create `report.html` template with: (a) title showing the report topic, (b) rendered markdown content area, (c) back-to-reports link, (d) safe HTML rendering (sanitize with bleach or use markdown's built-in safe mode)
- [ ] T028 [US3] Add path traversal protection on `/report/<filename>` — reject filenames containing `..`, leading `/`, or other traversal sequences; validate against allowed filenames from `_list_reports()` whitelist
- [ ] T029 [US3] Implement `GET /api/reports` endpoint — returns structured JSON report list for potential JS-driven features (mirrors what `/reports` page uses)
- [ ] T030 [US3] Implement `GET /api/reports/<filename>/content` endpoint — returns raw markdown content as JSON (`{ "filename": "...", "content": "..." }`)

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and ensure quality

- [ ] T031 [P] Write CSS in `static/style.css` — clean, readable layout with responsive design, color-coded phase indicators (blue=planning, green=success, red=error, yellow=running), card-style containers, form styling, mobile-friendly breakpoints
- [ ] T032 [P] Add startup banner in terminal — print `[INFO] Media Scraper GUI running at http://localhost:8000` and `[INFO] Open your browser to start researching` when server starts
- [ ] T033 [P] Add graceful shutdown handler — stop background scraper thread on server exit, log cleanup messages
- [ ] T034 [P] Update `__main__.py` or add CLI subcommand so `python -m media_scraper gui --port 8000` starts the GUI server (separate from existing CLI topic flow)
- [ ] T035 Update `pyproject.toml` — add `[project.optional-dependencies]` section with `gui = ["fastapi>=0.104", "uvicorn[standard]>=0.24", "python-multipart>=0.0.6", "markdown>=3.5"]` so users can install with `pip install -e ".[gui]"`
- [ ] T036 [P] Security audit — verify API key never appears in HTML responses, JSON responses, or log output; confirm no CSRF or session vulnerabilities; confirm localhost-only binding

---

## Phase 7: Tests

**Purpose**: Verify correctness of the GUI implementation

- [ ] T037 [P] Create `tests/test_gui/conftest.py` — fixtures for FastAPI test client, mock config loading, temporary output directory, stub LLM for scraper testing
- [ ] T038 [P] Create `tests/test_gui/test_endpoints.py` — unit tests for all `/api/` endpoints:
  - GET `/api/config` returns masked API key
  - PUT `/api/config` updates valid fields, rejects api_key field (403), validates types
  - POST `/api/run/start` starts scraper, rejects empty topic (422), rejects concurrent runs (409)
  - GET `/api/run/status` returns correct state transitions
  - POST `/api/run/cancel` cancels active run, rejects when idle (400)
  - GET `/api/reports` returns empty list when no reports exist
  - GET `/api/reports/<filename>/content` returns content, rejects path traversal (404)
- [ ] T039 [P] Create `tests/test_gui/test_scraping.py` — integration tests using StubLLM:
  - Full pipeline run via `/api/run/start` produces report file
  - Progress phases transition correctly: planning → gathering → analyzing → synthesizing → complete
  - Failed source doesn't crash the run; error state handled gracefully
  - Report file is written to the configured output directory
- [ ] T040 [P] Create `tests/test_gui/test_templates.py` — template rendering tests:
  - Base template renders without errors
  - Index page contains topic input form with expected form attributes
  - Config page displays all configurable fields
  - Reports page lists reports when they exist
  - Report viewer renders markdown content

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phases 3–5)**: All depend on Foundational phase completion
  - Can proceed sequentially (P1 → P2 → P3) or in parallel by different developers
- **Polish (Phase 6)**: Depends on all desired user stories being complete
- **Tests (Phase 7)**: Can be written alongside implementation; final integration tests depend on all phases

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational only. No dependencies on US2 or US3.
- **User Story 2 (P2)**: Depends on Foundational only. May integrate with US1's RunState for config validation during runs.
- **User Story 3 (P3)**: Depends on Foundational only. Uses shared `_list_reports()` from Foundational.

### Within Each User Story

- Models/helpers before services/endpoints
- Server-side implementation before client-side JS
- Core functionality before polish/validation
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- Once Foundational completes, US1, US2, US3 can start in parallel
- Template creation within each story can run in parallel with endpoint implementation
- Test files in Phase 7 can be written in parallel (different test files)

---

## Parallel Example: User Story 1

```bash
# Launch all independent tasks for US1 together:
Task: "T011 Create index.html template with topic form and progress display"
Task: "T012 Implement POST /api/run/start endpoint"
Task: "T013 Implement GET /api/run/status endpoint"
Task: "T014 Implement POST /api/run/cancel endpoint"

# After those complete:
Task: "T015 Add JavaScript polling logic to index.html"
Task: "T016 Add form validation"
Task: "T017 Wire background scraper phase tracking"
```

---

## Notes

- [P] tasks = different files, no dependencies between them
- Each user story is independently completable and testable
- The existing `pipeline.py`, `models.py`, `config.py` are reused as-is — no modifications needed to core modules
- `RunState` lives in `gui.py` as a module-level variable — simple for single-user, replaceable with DB later
- Tests use `pytest` and FastAPI's `TestClient` — no new test infrastructure needed
- Commit after each task or logical group of related changes
- Stop at any checkpoint to validate the story independently
- Avoid: vague task descriptions, same-file conflicts, cross-story dependencies that break independence
