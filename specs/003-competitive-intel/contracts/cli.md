# CLI & Brief Contract: Competitive Intelligence Upgrade

Extends the existing CLI (`media_scraper.cli:main`). All existing flags and exit
codes are preserved.

## New / changed flags

| Flag | Type | Effect |
|---|---|---|
| `--max-sources N` | int | Override `Config.max_sources` for this run (the "scrape farther" reach knob). |
| `--days N` | int | Recency window: gather only items from the last N days. Maps to the search backend's date filter and the planner prompt. Mutually exclusive with `--since`. |
| `--since YYYY-MM-DD` | date | Recency window expressed as a start date; converted to a day count from today. Mutually exclusive with `--days`. |
| `--brief` | flag | Non-interactive run built from config (`brand` + `competitors` + `platforms` + `recency_days`). No topic prompt. Intended for cron. |

Existing flags retained: `--topic`, `--config`, `--output-dir`, `--model`,
`--base-url`, `--headless`, `--configure`.

## Config keys (config.toml)

```toml
brand = "Pos Malaysia"
competitors = ["J&T Express", "GDEX", "DHL", "FedEx", "City-Link Express"]
platforms = ["x", "reddit", "youtube", "facebook", "linkedin", "news"]
recency_days = 7
max_sources = 30
# existing: base_url, model, output_dir, user_data_dir, headless, max_chars_per_source
```

Secret remains env-only (`MEDIA_SCRAPER_API_KEY`); never written to config.

## Behavior contract

- **`--brief`** requires `brand` to be set in config; otherwise exit `1` (config
  error) with a message naming the missing key.
- **`--brief --headless`** runs fully unattended: no prompts, no manual-login
  pauses. Walled platforms with no reusable session fall back to keyless `site:`
  search; if still unreadable they are recorded as `login_skipped` in the report
  appendix (run is **not** aborted).
- **Recency**: `--days`/`--since` override `recency_days` for the run. `0`/absent
  = no date filter.
- **Dedup**: each run reads/writes `.state/<slug>.json`; sources already reported
  for this brief are skipped. Seen-state is updated only after a report is
  written.
- **Reach**: `--max-sources` raises/lowers the total gathered cap; breadth comes
  from query expansion across brand × competitors × platforms.

## Exit codes (unchanged)

| Code | Meaning |
|---|---|
| 0 | Report written successfully. |
| 1 | Config/secret error (missing API key, missing `brand` for `--brief`, invalid config). |
| 2 | LLM backend unreachable or returned unusable output. |
| 3 | Plan produced no usable sources. |

## Cron contract

A scheduled run is a single non-interactive command. Example weekly (Mon 07:00):

```cron
0 7 * * 1 cd /home/aiden/Projects/media-scraper && \
  MEDIA_SCRAPER_API_KEY=… .venv/bin/media-scraper --brief --headless >> reports/cron.log 2>&1
```

**Pre-req for walled social platforms**: run once headed
(`media-scraper --brief`) and sign in at the pause; the persistent session is
then reused by headless cron runs.

## Report additions

The generated Markdown gains a **Competitive Sentiment** section (per-brand
positive/neutral/negative counts, average credibility, mention count) and a note
stating the run reported only mentions new since the last run for this brief.
All existing sections (Summary, Key Findings, Per-Source Analysis, Sources,
Steps Taken, Appendix) are preserved.
