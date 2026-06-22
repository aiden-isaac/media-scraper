# Research: Localhost GUI

**Date**: 2026-06-22

## Decisions Made

### 1. Framework Choice: FastAPI over alternatives

**Options considered**: Streamlit, Gradio, Flask, FastAPI

**Decision**: FastAPI

**Rationale**:
- Already chosen by user — aligns with project preferences
- Native async support for future extensibility (though we start synchronous)
- Built-in request/response validation with Pydantic (matches existing `models.py`)
- Automatic OpenAPI docs at `/docs` for debugging
- Lightweight — no heavy frontend framework required
- Well-documented with strong community support

### 2. Template Engine: Jinja2 over static HTML/JS frameworks

**Decision**: Jinja2 templates served directly by FastAPI

**Rationale**:
- Zero JavaScript build step — fits "simple but functional" requirement
- Python-side templating keeps everything in one package
- Easy to add dynamic elements (progress updates, conditional rendering)
- No npm, no bundler, no frontend toolchain needed
- Can always migrate to a JS framework later if needed

### 3. Progress Updates: Polling over WebSockets/SSE

**Decision**: Simple HTTP polling (client polls `/api/run/status` every 2 seconds)

**Rationale**:
- Simpler to implement and debug than WebSocket or SSE connections
- Adequate for scraper phases that change every 10–60 seconds
- No connection management overhead
- Works reliably across all browsers without fallback
- Could upgrade to SSE/WebSocket in a future iteration if needed

### 4. Scraper Execution: Blocking thread over background task queue

**Decision**: Run scraper in a background `threading.Thread`, store state in module-level variable

**Rationale**:
- Single-user local tool — no need for Celery/RQ/Redis
- Module-level `current_run: Optional[RunState]` is sufficient for concurrency tracking
- Simple restart/recovery semantics: server restart clears run state
- Background thread blocks only within the scraper; FastAPI main thread stays responsive
- For a more complex deployment, this could be replaced with a proper task queue later

### 5. Report Rendering: Server-side markdown-to-HTML over client-side

**Decision**: Server renders markdown to HTML using the `markdown` Python library; serves pre-rendered HTML to browser

**Rationale**:
- No JavaScript markdown parser needed
- Consistent rendering across browsers
- Easier to style with CSS since HTML structure is known
- Security: server controls what gets rendered (no client-side XSS from raw markdown)

### 6. Configuration Storage: Direct TOML read/write over database

**Decision**: Read/write `config.toml` directly using the existing config system

**Rationale**:
- Existing `config.py` already handles TOML parsing, env var merging, and secret isolation
- No new dependency (no SQLite, no ORM)
- File-based config is human-editable and version-control-friendly
- Atomic writes (write to temp file then rename) prevent corruption during concurrent access

### 7. Static Assets: Plain CSS over Tailwind/Bulma/bootstrap

**Decision**: Minimal custom CSS in a single `static/style.css` file

**Rationale**:
- Keeps dependencies minimal
- The UI is simple enough that a full CSS framework adds more weight than value
- Custom CSS is easier to maintain long-term for small projects
- Can always add a CSS framework later if the UI grows

### 8. Authentication: None

**Decision**: No authentication, no session management

**Rationale**:
- Local-only tool, bound to 127.0.0.1
- Single-user environment assumed
- Adding auth would require storing credentials somewhere, which conflicts with security-first approach
- If remote access is needed later, reverse proxy with basic auth or JWT can be added
