# Feature Specification: Recurring Brand-Perception & Competitive Intelligence

**Feature Branch**: `003-competitive-intel`

**Created**: 2026-06-22

**Status**: Draft

**Input**: User description: "Upgrade the topic-research-scraper into a recurring brand-perception and competitive-landscape intelligence tool. Primary use case: a daily/weekly report on Pos Malaysia's brand perception versus key logistics competitors (J&T Express, GDEX, DHL, FedEx, City-Link Express), with sentiment across social media and news, pulling only the latest mentions since the last run. Lean extension, no new dependencies. Adds in-site social search, configurable recency window, a reach/breadth knob, per-brand competitive sentiment, latest-only dedup, and OS-cron scheduling."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Comparative brand-perception report (Priority: P1)

A marketing analyst defines a brief — a primary brand (Pos Malaysia) plus named
competitors (J&T Express, GDEX, DHL, FedEx, City-Link Express) — and runs the
tool. They receive a Markdown report whose centerpiece is a competitive
sentiment breakdown: for each brand, how many recent public mentions were
positive, neutral, or negative, an average credibility, and the mention count,
alongside the existing summary, key findings, and cited sources.

**Why this priority**: This is the core deliverable the whole upgrade exists for
— turning a single-topic researcher into a brand-vs-competitor perception
report. It is valuable on web + news sources alone, even before social coverage
is added.

**Independent Test**: Run the tool with a brand and one or more competitors;
confirm the report contains a competitive sentiment table covering the brand and
every named competitor, with each cited source attributed to the brand it
concerns.

**Acceptance Scenarios**:

1. **Given** a brief naming a brand and five competitors, **When** the analyst
   runs the tool, **Then** the report includes a per-brand sentiment table
   listing all six entities with positive/neutral/negative counts and a mention
   count.
2. **Given** sources that mention different brands, **When** they are analyzed,
   **Then** each source is attributed to the brand it primarily concerns and
   tallied under that brand.
3. **Given** a source that fails to load, **When** the run completes, **Then**
   the report still finishes and the failed source is listed in the appendix
   (existing invariant preserved).

---

### User Story 2 - Social-media coverage via in-site search (Priority: P2)

The analyst wants mentions from social platforms (X/Twitter, Reddit, YouTube,
Facebook, LinkedIn, TikTok), not just news sites. The tool searches *within*
each configured platform for the brand/competitor terms — using the platform's
own search rather than landing on a profile page — and includes the resulting
posts as analyzed sources. For platforms that require sign-in, the analyst signs
in once in a visible browser window; that session is reused on later runs.
Without any sign-in, the tool still surfaces individual public post links via a
keyless site-scoped web search.

**Why this priority**: Social sentiment is half the original objective, and the
current tool silently skips it. This story adds the missing dimension but builds
on US1's reporting, so it ships second.

**Independent Test**: Configure one or more social platforms, run the tool, and
confirm that posts/links originating from those platforms appear among the
gathered sources and feed into the per-brand sentiment.

**Acceptance Scenarios**:

1. **Given** a configured social platform, **When** the tool gathers sources,
   **Then** it queries that platform's own search for the brand terms and
   includes returned posts as sources.
2. **Given** a sign-in-walled platform and a previously established session,
   **When** an unattended run executes, **Then** the tool reads the platform
   without prompting, reusing the saved session.
3. **Given** a sign-in-walled platform with no usable session in an unattended
   run, **Then** the tool falls back to a keyless site-scoped web search for
   public post links and continues without failing the run.
4. **Given** a brand expressed as a bare handle (e.g. `@PosMalaysia`), **When**
   it is used to build a destination, **Then** it resolves to a valid address
   (no malformed URL).

---

### User Story 3 - Recurring "latest-only" runs (Priority: P3)

The analyst schedules the tool to run unattended daily or weekly so marketing
gets a fresh digest automatically. Each run is limited to a configurable recency
window (e.g. the last 7 days) and reports only mentions not seen in prior runs,
so consecutive digests do not repeat the same items. The analyst can also tune
how far the scan reaches (how many sources to gather).

**Why this priority**: Automation and freshness make the tool a standing
marketing input rather than a manual one-off. It depends on US1/US2 producing
the content, so it is last.

**Independent Test**: Run the brief twice within the recency window; confirm the
second report's sources contain only items absent from the first, and that an
unattended (no-prompt) invocation produces a timestamped report.

**Acceptance Scenarios**:

1. **Given** a configured recency window of N days, **When** the tool gathers
   from date-filterable sources, **Then** results older than N days are
   excluded.
2. **Given** a prior run recorded its gathered links, **When** the brief runs
   again, **Then** links already reported are skipped and only new mentions
   appear.
3. **Given** an unattended invocation, **When** it runs, **Then** it completes
   with no interactive prompts and returns a success exit code with a
   timestamped report.
4. **Given** a larger configured reach, **When** the tool runs, **Then** it
   gathers proportionally more mentions (up to the configured limit).

---

### Edge Cases

- **No new mentions since last run**: the report states clearly that nothing new
  was found rather than appearing broken or empty without explanation.
- **A platform changes its search layout** so no results parse: the tool falls
  back to the keyless site-scoped web search and the run still completes.
- **A bare handle or non-URL brand reference**: normalized to a valid address;
  never produces a malformed destination.
- **Session expired on a walled platform during an unattended run**: the
  platform is skipped (recorded in the appendix) and the run continues via the
  keyless fallback; it does not hang waiting for a login.
- **First-ever run (no prior state)**: every gathered item is treated as new; no
  dedup suppression.
- **Recency window wider than available history**: all available recent items
  are included without error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The tool MUST let the user define a brief consisting of a primary
  brand, a list of competitors, a list of social/news platforms to cover, a
  recency window, and a reach limit.
- **FR-002**: The tool MUST search *within* each configured social platform for
  the brand/competitor terms using that platform's own search, rather than only
  visiting a profile or home page.
- **FR-003**: When a platform requires sign-in, the tool MUST allow a one-time
  manual sign-in in a visible browser and reuse that saved session on later
  runs. It MUST NOT store, transmit, or auto-enter credentials, and MUST NOT
  solve captchas (constitution Principle II).
- **FR-004**: For unattended runs and sign-in-walled platforms without a usable
  session, the tool MUST fall back to a keyless site-scoped web search that
  surfaces individual public post links, and continue without failing the run.
- **FR-005**: The tool MUST normalize brand references such as bare handles or
  bare domains into valid destinations (no malformed addresses).
- **FR-006**: The tool MUST support a configurable recency window and restrict
  date-filterable sources to items within that window, and convey the window to
  the research-planning step.
- **FR-007**: The tool MUST expose a configurable reach/breadth limit
  controlling how many sources are gathered per run, settable both
  per-invocation and in persistent configuration.
- **FR-008**: For each analyzed source, the tool MUST determine which brand the
  source primarily concerns, in addition to its sentiment and credibility.
- **FR-009**: The report MUST include a competitive sentiment summary that, for
  each brand in the brief, shows positive/neutral/negative mention counts,
  average credibility, and total mention count.
- **FR-010**: Across recurring runs of the same brief, the tool MUST record
  which source links have already been reported and skip them on subsequent
  runs so each digest contains only new mentions.
- **FR-011**: The tool MUST support a fully non-interactive invocation that
  builds the run from the saved brief and completes without prompts, preserving
  the existing exit-code contract (success / config error / backend error / no
  sources).
- **FR-012**: Recurring scheduling MUST be achievable through the operating
  system's scheduler (cron / systemd timer) with documented setup; the tool
  itself MUST NOT include a long-running scheduler process.
- **FR-013**: Failed or skipped sources (including login-skipped social
  platforms) MUST be recorded in the report appendix and MUST NOT abort the run
  (existing invariant preserved).
- **FR-014**: The upgrade MUST remain a lean extension: no new runtime
  dependencies, no database, and compliance with the project constitution's
  minimalism principle.

### Key Entities *(include if feature involves data)*

- **Brief**: the recurring research definition — primary brand, competitors,
  platforms to cover, recency window, reach limit. Drives planning, gathering,
  and the report's competitive structure.
- **Source**: a gathered item (web/news/social/RSS) — now also attributed to the
  brand it primarily concerns, in addition to its existing sentiment,
  credibility, status, and origin.
- **Competitive Sentiment Summary**: per-brand aggregation of analyzed sources —
  sentiment counts, average credibility, mention count.
- **Seen-State**: a record, per brief, of source links already reported, used to
  suppress duplicates across recurring runs.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A single run on a brief with a brand and five competitors produces
  a report whose competitive sentiment summary covers all six brands.
- **SC-002**: When public social mentions of the brand exist within the recency
  window, at least one social-platform-originated mention appears among the
  report's sources.
- **SC-003**: Running the same brief twice within the recency window yields a
  second report whose sources contain zero items already present in the first
  report.
- **SC-004**: A scheduled/unattended invocation completes with no interactive
  prompts and writes a timestamped report, returning a success exit code.
- **SC-005**: No item older than the configured recency window appears among
  date-filterable sources in the report.
- **SC-006**: Increasing the configured reach limit results in more mentions
  gathered (up to the limit), demonstrating the "scrape farther" control.

## Assumptions

- The existing pipeline (LLM planning, per-source sentiment/credibility, Markdown
  report, persistent headed-browser login) is reused; this feature extends it
  rather than replacing it.
- "Scrape farther" means broader coverage via more targeted queries across brand
  × competitors × platforms and a higher source cap — **not** recursive link
  crawling, which is explicitly out of scope.
- Walled social platforms are made readable in unattended runs only after a
  one-time manual sign-in establishes a reusable session; otherwise the keyless
  site-scoped fallback provides best-effort public coverage.
- Sentiment, credibility, and brand attribution are produced by the configured
  LLM (no separate NLP dependency is added).
- Scheduling, secrets, and output remain as today: OS-level scheduler, API key
  from the environment, Markdown reports in the output directory.

### Non-Goals

- Recursive web crawling / following links beyond the gathered result pages.
- Any database or persistent store beyond small local files (state is a simple
  per-brief record).
- Any in-app scheduler daemon, job queue, or background-worker service.
- Paid or key-gated social-platform APIs.
- Multi-user operation, remote access, or a hosted dashboard.
