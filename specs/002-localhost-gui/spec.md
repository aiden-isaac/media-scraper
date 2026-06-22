# Feature Specification: Localhost GUI

**Feature Branch**: `002-local-gui`

**Created**: 2026-06-22

**Status**: Draft

**Input**: User description: "Create a FastAPI-based localhost GUI for the media-scraper project. The GUI should allow users to view and manage configuration settings through a web interface, run the existing scraper pipeline by entering a research topic, monitor scraper progress, and view results. Serve on localhost:8000 by default."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run a scraper from the web UI (Priority: P1)

A user opens their browser to `http://localhost:8000`, enters a research topic into a text field, clicks submit, and watches the scraper progress. Once complete, they can see the report was generated and download or view it. This is the primary value of the GUI — replacing the terminal workflow with a visual one.

**Why this priority**: This is the core value proposition. Without being able to run scrapers, the GUI has no purpose. Everything else supports this flow.

**Independent Test**: Start the FastAPI server, open the page in a browser, enter a topic, submit, and confirm the scraper runs and produces a report file.

**Acceptance Scenarios**:

1. **Given** the GUI is running, **When** the user enters a topic and submits, **Then** the scraper starts and the UI shows progress indicators for each phase.
2. **Given** a scraper is running, **When** the phase changes, **Then** the UI updates to show the current phase (planning, gathering, analyzing, synthesizing).
3. **Given** the scraper completes, **When** the report is written, **Then** the UI displays a success message with a link to view/download the report.
4. **Given** a scraper fails, **When** an error occurs, **Then** the UI shows an error message without crashing the server.

---

### User Story 2 - Manage configuration through the web UI (Priority: P2)

A user navigates to a settings page in the GUI where they can view and edit the scraper's configuration — LLM endpoint URL, model name, output directory, max sources, headless mode toggle. Changes are saved to the config file immediately. The API key remains read-only from environment variable only (never editable in the UI).

**Why this priority**: Configuration management is essential for first-time setup and ongoing use, but users who already have a working `config.toml` can still run scrapers without touching settings.

**Independent Test**: Open the settings page, modify a configuration value, save, and confirm the change persists to disk. Restart the server and verify the setting is applied.

**Acceptance Scenarios**:

1. **Given** the GUI is running, **When** the user opens the settings page, **Then** all configurable values are displayed from the current config file.
2. **Given** the settings page, **When** the user modifies a value and saves, **Then** the config file is updated and the UI confirms the save.
3. **Given** the settings page, **When** the user views the page, **Then** the API key is shown as masked (e.g., `sk-****`) and cannot be edited.
4. **Given** a config change, **When** the user restarts the server, **Then** the new config values are loaded and applied.

---

### User Story 3 - View past reports (Priority: P3)

A user can browse previously generated reports from the GUI. Reports are listed with their topic name, generation date, and a preview link. Clicking a report opens it in the browser.

**Why this priority**: Useful for reviewing historical research, but the tool works perfectly well without it — users can always find reports on disk.

**Independent Test**: Generate two reports via the GUI, navigate to the reports list, and confirm both appear with correct metadata. Click a report and confirm it renders.

**Acceptance Scenarios**:

1. **Given** reports exist in the output directory, **When** the user opens the reports page, **Then** all reports are listed sorted by most recent first.
2. **Given** a report in the list, **When** the user clicks it, **Then** the markdown report renders in the browser.
3. **Given** no reports exist, **When** the user opens the reports page, **Then** a friendly "no reports yet" message is displayed.

---

### Edge Cases

- **Scraper already running**: If the user tries to start a second scraper while one is in progress, the UI shows a clear "scraper already running" state and disables the submit button.
- **Server restart during scrape**: If the FastAPI server restarts while a scraper is running, the running scraper continues (or is terminated gracefully); the UI starts fresh without stale state.
- **Large topics / slow scraping**: The UI should handle long-running scrapes (minutes) without timing out or appearing frozen. Progress polling or SSE events keep the UI responsive.
- **Config file missing or malformed**: The UI shows a warning and falls back to defaults rather than crashing.
- **Browser not available**: If Playwright browsers aren't installed (`playwright install`), the GUI shows a helpful error message directing the user to install them.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST serve a web UI at `http://localhost:8000` accessible from any browser on the same machine.
- **FR-002**: Users MUST be able to enter a research topic and trigger the scraper pipeline from the web UI.
- **FR-003**: The UI MUST display real-time or near-real-time progress of the scraper through its phases (plan, gather, analyze, synthesize).
- **FR-004**: Users MUST be able to view and edit all non-secret configuration values (LLM endpoint, model name, output directory, max sources, headless mode) through the web UI.
- **FR-005**: The API key MUST NOT be exposed or editable through the web UI under any circumstances.
- **FR-006**: Configuration changes made through the UI MUST persist to the `config.toml` file immediately.
- **FR-007**: The UI MUST display a success or error message when a scraper run completes.
- **FR-008**: Users MUST be able to view previously generated reports through the web UI.
- **FR-009**: The system MUST prevent concurrent scraper runs — only one scraper may run at a time.
- **FR-010**: The system MUST handle scraper errors gracefully without crashing the web server.

### Key Entities

- **Scraper Run**: A single execution of the scraper pipeline, identified by topic, start time, status (running/success/error), and path to the generated report.
- **Configuration**: Key-value pairs representing scraper settings (endpoint, model, output directory, etc.), excluding secrets.
- **Report**: A generated Markdown research report, identified by topic slug, timestamp, file path, and source count.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can start the GUI server, open it in a browser, enter a topic, and obtain a complete report within one session — no terminal interaction required.
- **SC-002**: Configuration changes made through the UI are persisted to disk within 1 second and survive server restarts.
- **SC-003**: The API key never appears in any HTML response, API response body, or log output visible in the browser.
- **SC-004**: Users can browse and open previously generated reports from the UI without leaving the browser.
- **SC-005**: A failed scraper run does not crash or hang the GUI — the UI shows an error state and allows the user to try again.

## Assumptions

- The GUI is intended for single-user, local-only access; no authentication or multi-user support is needed.
- The FastAPI server runs on the same machine as the scraper; remote access is out of scope.
- Browser automation (Playwright) requires `playwright install` to be run once on the host machine.
- The GUI uses synchronous blocking for scraper execution (no background workers) since this is a single-user local tool.
- Report rendering in the browser uses basic markdown-to-HTML conversion without complex styling.
- The default listen address is `127.0.0.1:8000`; users can override via environment variable if needed.
