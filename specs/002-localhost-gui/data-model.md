# Data Model: Localhost GUI

**Date**: 2026-06-22

## RunState

Tracks the state of a currently running scraper pipeline.

| Field | Type | Description |
|-------|------|-------------|
| `topic` | `str` | The research topic submitted by the user |
| `status` | `str` | One of: `running`, `success`, `error`, `idle` |
| `phase` | `str` | Current phase: `planning`, `gathering`, `analyzing`, `synthesizing`, `complete` |
| `report_path` | `Optional[str]` | Path to the generated report (set on success) |
| `error_message` | `Optional[str]` | Error description (set on error) |
| `started_at` | `datetime` | When the scraper run started |
| `completed_at` | `Optional[datetime]` | When the run finished |

**Constraints**: Only one `RunState` exists at a time. Setting a new run replaces the previous state. On server restart, state resets to `idle`.

## RunResponse (API response model)

Serialized representation of `RunState` for API responses.

| Field | Type | Description |
|-------|------|-------------|
| `topic` | `str` | Research topic |
| `status` | `str` | Current status |
| `phase` | `str` | Current phase |
| `report_path` | `Optional[str]` | Report file path (null if not complete) |
| `error_message` | `Optional[str]` | Error message (null if no error) |
| `started_at` | `str` | ISO 8601 timestamp |
| `completed_at` | `Optional[str]` | ISO 8601 timestamp (null if not finished) |

## ConfigUpdateRequest (API request model)

User-submitted configuration changes.

| Field | Type | Description |
|-------|------|-------------|
| `base_url` | `str` | LLM endpoint URL |
| `model` | `str` | Model name |
| `output_dir` | `str` | Output directory path |
| `headless` | `bool` | Whether to run browser headlessly |
| `max_sources` | `int` | Maximum number of sources to gather |
| `max_chars_per_source` | `int` | Character limit per source text |

**Constraints**: All fields are optional — only changed fields need to be included in PUT requests. Missing fields are left unchanged.

## ConfigResponse (API response model)

Current configuration as seen by the GUI.

| Field | Type | Description |
|-------|------|-------------|
| `base_url` | `str` | LLM endpoint URL |
| `model` | `str` | Model name |
| `output_dir` | `str` | Output directory path |
| `headless` | `bool` | Headless mode flag |
| `max_sources` | `int` | Max sources cap |
| `max_chars_per_source` | `int` | Max chars per source |
| `api_key_set` | `bool` | True if API key is configured (value never exposed) |

## ReportItem

Metadata for a single generated report.

| Field | Type | Description |
|-------|------|-------------|
| `filename` | `str` | Filename (e.g., `climate-change-20260622-143000.md`) |
| `topic` | `str` | The research topic this report covers |
| `path` | `str` | Full filesystem path to the report |
| `created_at` | `str` | ISO 8601 timestamp from filename |
| `source_count` | `int` | Number of sources analyzed (read from report content or metadata) |

## ReportsListResponse

Collection of past reports.

| Field | Type | Description |
|-------|------|-------------|
| `reports` | `list[ReportItem]` | Sorted list (newest first) |
| `total` | `int` | Total count of reports |

## Relationships

```
RunState ──► (one-to-one) Scraper Pipeline Execution
ConfigResponse ◄── (reads from) config.toml
ReportsListResponse ◄── (scans from) output_dir/
RunState.report_path ──► ReportItem (after successful completion)
```

No database is used. All state is either in-memory (`RunState`), file-based (`config.toml`), or filesystem-scanned (`reports/`).
