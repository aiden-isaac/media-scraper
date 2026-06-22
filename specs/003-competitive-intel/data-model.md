# Phase 1 Data Model: Competitive Intelligence Upgrade

Reuses the existing dataclasses in `src/media_scraper/models.py`. New fields are
**additive** (defaulted) so existing call sites and the stub test keep working.

## Config (extended)

Existing: `base_url, model, api_key, output_dir, user_data_dir, headless,
max_sources, max_chars_per_source`.

| New field | Type | Default | Notes |
|---|---|---|---|
| `brand` | `str` | `""` | Primary brand for the brief (e.g. "Pos Malaysia"). |
| `competitors` | `list[str]` | `[]` | Named competitors (e.g. J&T Express, GDEX, DHL, FedEx, City-Link Express). |
| `platforms` | `list[str]` | `[]` | Social/news platforms to cover (`x`, `reddit`, `youtube`, `facebook`, `linkedin`, `tiktok`, `news`). |
| `recency_days` | `int` | `0` | `0` = no date filter; else restrict to last N days. |

Loaded from `config.toml` (lists as TOML arrays); secret still env-only. CLI may
override `max_sources` and `recency_days` per run.

**Validation**: `recency_days >= 0`; `max_sources >= 1`; `platforms` entries
limited to the known set (unknown values ignored with a log line). `brand` may
be empty for ad-hoc `--topic` runs; `--brief` requires `brand` set.

## ResearchPlan

Unchanged shape (`topic, sub_questions, search_queries, rss_feeds,
target_sites`). The planner now *receives* brand/competitors/platforms/recency
in its prompt so the generated queries are comparative and time-scoped. No new
fields required — query expansion happens in `pipeline.gather_sources`.

## Source (unchanged shape)

`url, title, kind, text, status, error`. `kind` continues to use the existing
`SOURCE_KINDS = ("web", "news", "rss", "social")`. In-site search results are
recorded as `kind="social"`. No schema change.

## SourceAnalysis (extended)

| New field | Type | Default | Notes |
|---|---|---|---|
| `subject` | `str` | `""` | Which brand the source primarily concerns. Normalized to one of the brief's brands (case-insensitive match) or `"other"` when it matches none. |

`analyze()` returns `subject` from the LLM; the orchestrator normalizes it
against `[brand] + competitors`. Empty/unknown → `"other"`.

## Competitive Sentiment Summary (derived, not stored)

Computed in `report.py` from the analyzed sources — not a persisted entity.

Per brand in `[brand] + competitors`:
- `positive`, `neutral`, `negative` — counts of sources with that sentiment
  (`mixed` counted under neutral for the headline table; raw sentiment still
  shown per-source).
- `mentions` — total analyzed sources attributed to the brand.
- `avg_credibility` — mean credibility (1–5) of those sources, blank if none.

Brands with zero mentions still appear (as a row of zeros) so the table always
covers the full competitive set (SC-001).

## Seen-State (new, persisted)

File: `.state/<slug>.json` where `slug = report._slug(brand or topic)`.

```json
{ "seen": ["https://...", "https://..."], "updated": "2026-06-22T07:00:00Z" }
```

- **Read** at gather start: URLs in `seen` are skipped during gathering.
- **Write** after a successful run: union of prior `seen` and the run's reported
  URLs; `updated` set to run time.
- First run (file absent) → empty set → nothing suppressed.
- `ponytail:` flat JSON set; upgrade to SQLite only if brief count / URL volume
  ever makes load/save slow.

## State transitions

Run lifecycle (unchanged exit-code contract): `plan → gather → analyze →
synthesize → write report → update seen-state`. Seen-state is updated **only**
on a successfully written report, so a failed run does not suppress items from
the next attempt.
