# Phase 0 Research: Competitive Intelligence Upgrade

No open `NEEDS CLARIFICATION` markers remained from the spec. The research below
records the key technical decisions and why the lazy/native option was chosen
over heavier alternatives.

## 1. Reaching social media without paid APIs

**Decision**: Three-tier, in priority order, per platform:
1. **Site search URL** — navigate the persistent browser to the platform's own
   search results page (e.g. `x.com/search?q=`, `reddit.com/search/?q=&sort=new`,
   `youtube.com/results?search_query=`, `facebook.com/search/posts?q=`,
   `linkedin.com/search/results/content/?keywords=`, `tiktok.com/search?q=`),
   extract result links + snippets.
2. **DOM search-box fallback** — if no results parse but a search input exists,
   fill it and submit, then re-extract.
3. **Keyless `site:` web search** — `ddgs` query `site:<domain> <terms>` returns
   individual public post permalinks, which are usually readable without login.
   This is the unattended/headless baseline.

**Rationale**: A site's own search URL is its native feature (ladder rung 3) —
far more robust than scraping a constantly-changing search-box DOM. The `site:`
fallback reuses code already in `sources.web_search` and needs no login, so cron
works on day one. Walled sites (X/FB/IG/LinkedIn) become deeply readable only
after the existing one-time manual sign-in seeds the persistent session.

**Alternatives rejected**: Official Reddit/X/YouTube APIs (keys, signup, cost,
ToS, new deps — violates Principle I and the "no paid APIs" non-goal); headless
scraping of logged-out social feeds (blocked by login walls); a third-party
social-listening service (cost + dependency).

## 2. Date / recency filtering

**Decision**: Add `recency_days`; map to `ddgs.text(..., timelimit=)` using
`d` (≤1), `w` (≤7), `m` (≤31), else `y`. Append freshness hints to social search
URLs where supported (`sort=new`, `f=live`). Inject "only the last N days" into
the LLM planning prompt.

**Rationale**: `timelimit` is a native `ddgs` parameter — zero new code or deps.
Per-item exact-date filtering isn't reliably available across all sources, so the
search-backend window + prompt steering is the pragmatic 80/20.

**Alternatives rejected**: Parsing and comparing per-article publish dates (no
uniform date field across web/social/RSS; high effort, brittle).

## 3. "Latest only" across recurring runs

**Decision**: A per-brief JSON file `.state/<slug>.json` holding the set of
source URLs already reported. Gather skips URLs present in the set; after a
successful run, newly reported URLs are merged in. `slug` reuses the existing
`report._slug` logic.

**Rationale**: Single stdlib-`json` file is the laziest durable state. The data
is a flat set of strings — a database is unjustified (Principle I).
`ponytail:` ceiling noted in code — swap for SQLite only if many briefs or huge
URL volumes ever make the flat file slow.

**Alternatives rejected**: SQLite/Postgres (non-goal, over-built for a string
set); content hashing/near-dup detection (URL identity is sufficient for "did we
already report this link").

## 4. Scheduling

**Decision**: OS cron / systemd timer triggers `media-scraper --brief
--headless`. Documented in `AGENTS.md`. No scheduler code in the app.

**Rationale**: The tool already runs non-interactively with exit codes; cron is
the native scheduler (ladder rung 3). An in-app daemon would be a service to keep
alive for zero benefit and contradicts the "no scheduler daemon" non-goal.

**Operational note**: Walled social platforms require **one** headed run to sign
in; the persistent `.browser-profile` session is then reused by headless cron
runs until it expires (after which that platform falls back to `site:` search).

## 5. Competitive structure (brand attribution + per-brand sentiment)

**Decision**: `analyze()` returns one extra key, `subject` (which brand the
source primarily concerns, constrained to the brief's brand list or "other").
`report.py` aggregates analyzed sources by `subject` into a Competitive
Sentiment table (positive/neutral/negative counts, average credibility, mention
count).

**Rationale**: One more JSON field on the existing orchestrator-driven analyze
call (Principle III) plus a tally loop in report assembly — minimal, testable,
no new model capability required.

**Alternatives rejected**: A separate NLP/NER dependency for entity attribution
(new dep; the LLM already reads the text and can attribute).

## 6. "Scrape farther" knob

**Decision**: Expose existing `Config.max_sources` as `--max-sources`; achieve
real breadth by expanding queries across brand × competitors × platforms so a
higher cap pulls genuinely more, distinct mentions.

**Rationale**: The cap already exists and is enforced in `gather_sources`; only
a CLI wire-up plus query expansion is needed. Recursive crawling is explicitly
rejected — unbounded, slow, ToS-risky, and unnecessary for breadth.

**Alternatives rejected**: Recursive link-following crawler (non-goal); a
separate crawl-depth parameter (implies the crawler we're not building).

## Outcome

All decisions use existing dependencies and stdlib only. No `NEEDS
CLARIFICATION` remains; Constitution Check passes. Ready for Phase 1 design.
