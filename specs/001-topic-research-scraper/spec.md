# Feature Specification: Topic Research Scraper

**Feature Branch**: `001-topic-research-scraper`

**Created**: 2026-06-22

**Status**: Draft

**Input**: User description: "Build a Python CLI tool that researches a user-provided topic across the open web, news, RSS/Atom feeds, and account-gated social media, and exports a Markdown report. A configurable language-model backend plans the research and analyzes the gathered sources (sentiment, credibility); the user signs in / solves captchas manually in a visible browser when a site requires it; sessions persist across runs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Research a topic and get a report (Priority: P1)

A user opens the tool, types a research topic (a paragraph or a few sentences), and the
tool investigates the topic across openly accessible sources (the open web, news sites, and
RSS/Atom feeds), analyzes what it finds, and writes an exportable report file. The user can
read the report to understand the topic, the key findings, how each source leans
(sentiment), how trustworthy each source appears (credibility), and where the information
came from.

**Why this priority**: This is the core value of the tool and a viable product on its own —
even with no account-gated sources, a user gets a researched, analyzed report from a single
prompt. Everything else builds on this loop.

**Independent Test**: Run the tool with a topic that has ample open coverage, let it gather
from open sources only, and confirm a report file is produced containing a summary,
findings, per-source sentiment and credibility, and source links.

**Acceptance Scenarios**:

1. **Given** a configured tool and a topic, **When** the user starts a run, **Then** the
   tool produces a research plan (sub-questions and what it will look for) before gathering.
2. **Given** a research plan, **When** gathering completes, **Then** each gathered source is
   analyzed for key claims, sentiment, and credibility.
3. **Given** completed analysis, **When** the run finishes, **Then** a Markdown report file
   is written to the configured output location containing a summary, key findings,
   per-source sentiment and credibility, source links/citations, and the steps taken.
4. **Given** a source that cannot be retrieved, **When** gathering continues, **Then** the
   run does not abort — the failure is noted and other sources are still processed.

---

### User Story 2 - Reach account-gated and protected sources via manual sign-in (Priority: P2)

While researching, the tool encounters sources that require an account (e.g. X, Reddit,
Instagram) or present a captcha. It opens a visible browser, pauses, and asks the user to
sign in or solve the challenge themselves; once the user confirms, the run continues and
uses the now-accessible content. The signed-in state is remembered so later runs do not
require signing in again.

**Why this priority**: Account-gated sources materially expand coverage, but the tool is
already useful without them (P1). This adds reach on top of the core loop.

**Independent Test**: Point the tool at a topic that requires a login-gated source; confirm
the tool pauses with a clear prompt, lets the user sign in in the visible browser, resumes
after confirmation, and — on a second run — reuses the session without prompting again.

**Acceptance Scenarios**:

1. **Given** a source that requires sign-in, **When** the tool reaches it, **Then** it shows
   a visible browser and pauses with an instruction to sign in or solve the challenge.
2. **Given** the user has signed in and confirmed, **When** the run resumes, **Then** the
   tool retrieves the gated content and includes it in analysis.
3. **Given** a prior successful sign-in, **When** the user starts a later run, **Then** the
   tool reuses the saved session and does not prompt for that site again (until the session
   expires).
4. **Given** the tool is gathering, **When** any credential is involved, **Then** the tool
   never stores, transmits, or auto-enters credentials and never attempts to solve captchas
   itself.

---

### User Story 3 - Configure the backend and follow progress (Priority: P3)

Before or during use, the user configures the tool — which language-model service to use
(endpoint, model) and where reports are written — through a simple terminal interface, and
watches a running log of what the tool is doing (planning, searching, fetching, analyzing,
synthesizing) so the process is transparent and the manual-login pauses are obvious.

**Why this priority**: Configuration and visibility are necessary for real use but support
the core loop rather than delivering value alone.

**Independent Test**: Launch the tool, set a model endpoint/model and an output directory
through the terminal UI, run a short topic, and confirm the log shows each phase and that
settings are applied (report lands in the chosen directory; the chosen model is used).

**Acceptance Scenarios**:

1. **Given** a first launch, **When** the user opens configuration, **Then** they can set
   the language-model endpoint, model name, and output directory.
2. **Given** a run in progress, **When** the tool moves between phases, **Then** the
   terminal shows readable, streaming log messages for each phase.
3. **Given** a secret (API key) is required, **When** the tool reads it, **Then** the secret
   is taken from the environment and never written to configuration files, logs, or reports.

---

### Edge Cases

- **No results found**: the topic yields no usable sources — the tool reports that clearly
  rather than producing an empty or misleading report.
- **Model unavailable / malformed model output**: the language-model service is unreachable
  or returns output that cannot be used — the tool surfaces the error and fails gracefully
  without a half-written report.
- **User declines/abandons a sign-in pause**: the user closes the browser or skips the
  login — the tool continues with the sources it can reach and notes the skipped source.
- **Captcha or anti-bot block on an open page**: treated like a sign-in pause (manual
  resolution) or skipped if unresolved.
- **Very large source**: overly long page content is handled (truncated/condensed for
  analysis) rather than failing the run.
- **Expired session**: a previously saved login no longer works — the tool prompts the user
  to sign in again.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The tool MUST accept a free-text research topic of at least a paragraph from
  the user.
- **FR-002**: The tool MUST use a configurable language-model backend to produce a research
  plan (sub-questions, search queries, and target source types) from the topic before
  gathering.
- **FR-003**: The tool MUST gather information from open sources: general web/news search,
  RSS/Atom feeds, and directly fetched web pages.
- **FR-004**: The tool MUST be able to gather from account-gated sources by opening a
  visible browser and pausing for the user to sign in or solve a captcha manually, then
  resuming.
- **FR-005**: The tool MUST persist browser sessions locally so that successful sign-ins are
  reused across runs, and MUST exclude that session data from version control.
- **FR-006**: The tool MUST NOT store, transmit, or programmatically enter user credentials,
  and MUST NOT include any captcha-solving service.
- **FR-007**: The tool MUST analyze each gathered source for key claims, sentiment, and a
  source-credibility assessment with rationale.
- **FR-008**: The tool MUST synthesize a Markdown report containing: an overall summary, key
  findings, per-source sentiment and credibility, source links/citations, and a record of
  the steps taken.
- **FR-009**: The tool MUST write the report to a user-configurable output location as an
  exportable file.
- **FR-010**: The tool MUST let the user configure the language-model endpoint, model name,
  and output directory through a simple terminal interface.
- **FR-011**: The tool MUST read secrets (e.g. the model API key) from the environment and
  MUST NOT write them to configuration files, logs, or reports.
- **FR-012**: The tool MUST stream readable progress messages for each phase (plan, gather,
  analyze, synthesize) and make manual-login pauses unambiguous.
- **FR-013**: The tool MUST continue a run when an individual source fails to load or be
  retrieved, noting the failure rather than aborting.
- **FR-014**: The tool MUST fail gracefully (clear error, no partial/misleading report) when
  the language-model backend is unreachable or returns unusable output.

### Key Entities *(include if feature involves data)*

- **Research Topic**: the user's free-text prompt that drives a run.
- **Research Plan**: the model-produced breakdown of the topic into sub-questions, search
  queries, and target source types.
- **Source**: a single gathered item (web page, news article, feed entry, or gated post),
  with its origin URL, retrieved content, and retrieval status.
- **Source Analysis**: per-source extracted claims, sentiment, and credibility assessment
  with rationale.
- **Report**: the synthesized Markdown deliverable for a run (summary, findings, per-source
  analysis, citations, steps taken).
- **Session State**: locally persisted browser login state, reused across runs, scoped to a
  user-data location and excluded from version control.
- **Configuration**: language-model endpoint, model name, and output directory (secrets
  excluded, sourced from the environment).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: From entering a topic, a user obtains a complete report file for an
  open-coverage topic in a single run without manual intervention.
- **SC-002**: The report always includes all required sections — summary, key findings,
  per-source sentiment, per-source credibility, source links, and steps taken — for every
  successful run.
- **SC-003**: For an account-gated source, the user can sign in manually and the run
  resumes; a subsequent run on the same machine reuses that sign-in without prompting again
  (until the session expires).
- **SC-004**: A single failed or unreachable source never aborts a run — the report is still
  produced from the remaining sources.
- **SC-005**: No credential or secret value ever appears in any committed file, log line, or
  report.
- **SC-006**: At every stage of a run, the user can see from the terminal what phase the
  tool is in and whether it is waiting on a manual sign-in.

## Assumptions

- The tool is a single-user, local command-line utility; no multi-user or server deployment
  is in scope.
- The user supplies their own access to a language-model service reachable over a
  standard chat-completions interface, configured via endpoint/model/key.
- "Social media / account-gated" coverage is best-effort across common sites; the tool does
  not guarantee any specific site works, and behavior depends on the user being able to sign
  in manually.
- Reasonable per-run caps on the number of sources and amount of content are applied to keep
  runs bounded; exact limits are an implementation detail.
- Credibility is expressed on a simple, consistent scale with a short rationale; the exact
  scale is an implementation detail.
- The host machine has a graphical environment capable of showing a browser window for the
  manual sign-in flow.
- Out of scope for v1: automated credential entry, captcha solving, a full multi-panel
  terminal UI, scheduled/automated runs, and export formats other than Markdown.
