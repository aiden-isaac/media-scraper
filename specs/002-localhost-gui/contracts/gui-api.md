# API Contract: Localhost GUI

**Date**: 2026-06-22

## Base URL

```
http://localhost:8000
```

All endpoints below are relative to this base. No authentication is required.

---

## Pages (HTML Routes)

### GET `/` — Home Page

Renders the main page with a topic input form and scraper progress display.

**Response**: `text/html` (200)

---

### GET `/config` — Configuration Page

Renders the settings management page showing all configurable values.

**Response**: `text/html` (200)

---

### GET `/reports` — Reports List

Renders a page listing all generated reports, sorted newest first.

**Response**: `text/html` (200)

---

### GET `/report/<filename>` — Report Viewer

Renders a single report as HTML. The `<filename>` path segment is the `.md` filename from the output directory.

**Response**: `text/html` (200)

**Error**: `404 Not Found` if the file doesn't exist or the filename contains path traversal characters (`..`, `/`).

---

## API Endpoints (JSON Routes under `/api/`)

### GET `/api/run/status` — Scraper Run Status

Returns the current state of any running scraper.

**Response** `200 OK`:

```json
{
  "topic": "AI in journalism",
  "status": "running",
  "phase": "gathering",
  "report_path": null,
  "error_message": null,
  "started_at": "2026-06-22T14:30:00",
  "completed_at": null
}
```

**Possible `status` values**: `"idle"`, `"running"`, `"success"`, `"error"`

**Possible `phase` values**: `"planning"`, `"gathering"`, `"analyzing"`, `"synthesizing"`, `"complete"`

---

### POST `/api/run/start` — Start Scraper

Submits a research topic and starts the pipeline.

**Request Body** (`application/json`):

```json
{
  "topic": "impact of remote work on productivity"
}
```

**Validation**:
- `topic` is required and must be a non-empty string (min 1 char, max 5000 chars)
- Returns `422 Unprocessable Entity` if validation fails

**Response** `201 Created`:

```json
{
  "status": "accepted",
  "message": "Research started. Poll /api/run/status for progress."
}
```

**Conflict**: If a scraper is already running, returns `409 Conflict`:

```json
{
  "detail": "A scraper run is already in progress. Wait for it to complete."
}
```

---

### POST `/api/run/cancel` — Cancel Running Scraper

Stops the currently running scraper (best-effort).

**Response** `200 OK`:

```json
{
  "status": "cancelled",
  "message": "Scraper cancellation requested."
}
```

**Idle**: If no scraper is running, returns `400 Bad Request`:

```json
{
  "detail": "No scraper run is currently active."
}
```

---

### GET `/api/config` — Get Configuration

Returns current configuration (with masked API key).

**Response** `200 OK`:

```json
{
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o",
  "output_dir": "/home/user/media-scraper/reports",
  "headless": true,
  "max_sources": 12,
  "max_chars_per_source": 8000,
  "api_key_set": true
}
```

---

### PUT `/api/config` — Update Configuration

Updates one or more configuration values. Only provided fields are changed.

**Request Body** (`application/json`):

```json
{
  "model": "gpt-4o-mini",
  "max_sources": 10
}
```

**Constraints**:
- `api_key` is never accepted in requests (returns `403 Forbidden` if included)
- All fields are optional; omitted fields remain unchanged
- `headless` must be boolean; `max_sources` and `max_chars_per_source` must be positive integers

**Response** `200 OK`:

```json
{
  "message": "Configuration updated.",
  "config": { /* full updated config as returned by GET /api/config */ }
}
```

**Error** `422 Unprocessable Entity`: Invalid field types or values.

**Error** `403 Forbidden`: Request includes `api_key` field.

---

### GET `/api/reports` — List Reports

Returns all generated reports in the output directory.

**Query Parameters**: None required.

**Response** `200 OK`:

```json
{
  "reports": [
    {
      "filename": "remote-work-20260622-143000.md",
      "topic": "impact of remote work on productivity",
      "path": "/home/user/media-scraper/reports/remote-work-20260622-143000.md",
      "created_at": "2026-06-22T14:30:00",
      "source_count": 8
    },
    {
      "filename": "ai-journalism-20260621-090000.md",
      "topic": "AI tools in modern journalism",
      "path": "/home/user/media-scraper/reports/ai-journalism-20260621-090000.md",
      "created_at": "2026-06-21T09:00:00",
      "source_count": 5
    }
  ],
  "total": 2
}
```

Sorted by `created_at` descending (newest first). Empty list if no reports exist.

---

### GET `/api/reports/<filename>/content` — Get Report Content

Returns the raw markdown content of a report.

**Path Parameter**: `<filename>` — the `.md` filename from the output directory.

**Response** `200 OK`:

```json
{
  "filename": "remote-work-20260622-143000.md",
  "content": "# impact of remote work...\n\n## Summary & Key Findings..."
}
```

**Error** `404 Not Found`: File doesn't exist or contains path traversal.

---

## Error Response Format

All error responses follow FastAPI's default format:

```json
{
  "detail": "Human-readable error message"
}
```

Common status codes:
- `400` — Bad request (e.g., cancel when idle)
- `403` — Forbidden (e.g., trying to set API key via UI)
- `404` — Not found (e.g., missing report file)
- `409` — Conflict (scraper already running)
- `422` — Validation error (invalid input)
- `500` — Internal server error (unexpected failure)

## Security Notes

- **API key never appears in any response body**, even on successful requests.
- **Report filenames are sanitized**: path traversal sequences (`..`, leading `/`) are rejected.
- **No CSRF protection** is implemented since this is a localhost-only single-user tool.
- **No CORS headers** are configured — cross-origin access is not supported.
