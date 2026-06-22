# Contract: LLM JSON I/O

The orchestrator calls the OpenAI-compatible chat endpoint and parses **JSON only** from the
response. Each call uses a system message demanding strict JSON; on parse failure the
orchestrator issues one repair retry ("return ONLY valid JSON matching this shape") before
failing the stage (exit code 2). No native tool-calling is used.

## 1. plan(topic) → ResearchPlan

Request: system = JSON-only instruction + the schema; user = the topic text.

Expected response JSON:

```json
{
  "sub_questions": ["...", "..."],
  "search_queries": ["...", "..."],
  "rss_feeds": ["https://...", "..."],
  "target_sites": ["reddit.com/r/...", "x.com/..."]
}
```

Rules: arrays may be empty but the object must contain all four keys; at least one of
`search_queries` / `rss_feeds` / `target_sites` must be non-empty (else exit code 3).

## 2. analyze(source) → SourceAnalysis

Request: system = JSON-only instruction + schema; user = source title, url, and truncated
text (≤ `max_chars_per_source`).

Expected response JSON:

```json
{
  "claims": ["...", "..."],
  "sentiment": "positive | neutral | negative | mixed",
  "credibility": 1,
  "credibility_rationale": "one or two sentences"
}
```

Rules: `sentiment` must be one of the four enum values; `credibility` is an integer 1–5.
Out-of-range/invalid values trigger the repair retry; persistent invalidity → record the
source as analyzed-with-defaults (`neutral`, credibility 3, rationale noting parse failure)
rather than aborting.

## 3. synthesize(topic, plan, analyses) → Markdown body

Request: system = "write a Markdown research report with these sections"; user = topic,
plan, and the list of per-source analyses + citations.

Response: Markdown text (not JSON) for the report body. `report.py` wraps it with the title,
metadata header, Steps-Taken section, and the skipped/failed-source appendix so required
sections (FR-008) are guaranteed present even if the model omits one.

## Token / size discipline

- Source text is truncated to `max_chars_per_source` before being sent to `analyze`.
- Number of analyzed sources is capped by `max_sources`.
- The synthesize call receives compact per-source analyses, not full source texts.
