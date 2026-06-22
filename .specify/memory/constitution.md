<!--
Sync Impact Report
==================
Version change: (uninitialized template) → 1.0.0
Rationale: Initial ratification of the project constitution (MAJOR baseline).

Principles defined (all new):
  I.   Lazy & Minimal (YAGNI)
  II.  Human-in-the-Loop Authentication
  III. Provider-Agnostic, Orchestrator-Driven LLM
  IV.  Respectful Scraping & Local Session Persistence
  V.   Light, Runnable Testing
  VI.  Simple Terminal Interface

Sections defined:
  - Technology & Security Constraints
  - Development Workflow

Templates reviewed for alignment:
  ✅ .specify/templates/plan-template.md  (Constitution Check gate is generic; compatible)
  ✅ .specify/templates/spec-template.md  (no mandatory-section changes required)
  ✅ .specify/templates/tasks-template.md (testing discipline = "one runnable check per
     non-trivial module"; lighter than TDD but compatible with the phase structure)

Deferred TODOs: none
-->

# media-scraper Constitution

## Core Principles

### I. Lazy & Minimal (YAGNI)

Build the shortest thing that works. Code MUST climb the laziness ladder and stop at the
first rung that holds: does it need to exist at all → stdlib → native platform feature →
already-installed dependency → one line → minimum custom code. New third-party
dependencies MUST be justified against what a few lines of stdlib could do; speculative
abstractions (interfaces with one implementation, factories for one product, config for a
value that never changes) are prohibited. Deletion is preferred over addition; the
shortest working diff wins.

Rationale: This tool is a personal research utility, not a platform. Every unneeded layer
is future maintenance and a 3am debugging session that did not have to happen.

### II. Human-in-the-Loop Authentication

The tool MUST NOT store, transmit, or programmatically enter user credentials, and MUST
NOT include any captcha-solving service or evasion tooling. When a site requires login or
presents a captcha, the tool MUST run a headed browser, pause, and let the human sign in
or solve it manually, then continue. Authenticated state is the user's responsibility to
establish interactively.

Rationale: Manual sign-in keeps the tool on the right side of site terms and out of the
credential-storage business; it is also simpler than any automated alternative.

### III. Provider-Agnostic, Orchestrator-Driven LLM

The LLM backend MUST be reached through an OpenAI-compatible API with `base_url`, model,
and key all configurable. Secrets MUST come from the environment and MUST NOT be committed
to the repository. The orchestrator MUST drive control flow by parsing structured JSON the
model returns and calling in-process functions itself; it MUST NOT depend on the model's
native tool-calling for correctness (a strong tool-calling model is an optional upgrade,
not a requirement).

Rationale: The default backend is a local model whose native tool-calling is unreliable;
orchestrator-driven JSON keeps the pipeline deterministic and portable across providers.

### IV. Respectful Scraping & Local Session Persistence

The tool SHOULD respect site terms of service and robots directives within reason and
SHOULD avoid aggressive request patterns. Browser sessions MUST persist locally (in a
gitignored user-data directory) so manual logins are reused across runs rather than
repeated.

Rationale: Reusing sessions reduces friction and request volume; restraint keeps the tool
sustainable and low-risk.

### V. Light, Runnable Testing

Every non-trivial module (a branch, loop, parser, or report-assembly path) MUST leave
behind one runnable check — the smallest thing that fails if the logic breaks. Tests MUST
NOT introduce heavy frameworks, fixtures, or per-function suites unless explicitly
requested; a stub-driven `test_*.py` or an `assert`-based self-check is sufficient.
Trivial one-liners need no test.

Rationale: Lazy code without a check is unfinished; heavy test scaffolding violates
Principle I.

### VI. Simple Terminal Interface

User interaction MUST happen through a simple terminal UI (`rich`) for configuration,
streaming logs, and the manual-login pauses. A full multi-panel TUI is out of scope unless
explicitly requested later.

Rationale: "Simple TUI for now" — configuration and visible logs are the only UI needs;
anything heavier is premature.

## Technology & Security Constraints

- **Language/runtime:** Python.
- **Core dependencies:** `playwright` (browser + persistent login), `openai`
  (OpenAI-compatible client), `feedparser` (RSS), a keyless web-search source, and `rich`
  (TUI). Additions beyond these MUST be justified per Principle I.
- **Secrets:** API keys and tokens MUST be read from environment variables and excluded
  via `.gitignore`. They MUST NOT appear in committed config, logs, or reports.
- **Output:** Reports are exported as Markdown files; other formats are later add-ons.
- **Persistence:** the Playwright user-data directory and generated reports MUST be
  gitignored.

## Development Workflow

- Features follow the SpecKit flow: constitution → specify → plan → tasks →
  (optionally) taskstoissues → implement.
- Each change MUST be reviewed against these principles before merging; any deviation MUST
  be justified in the plan's Complexity Tracking section.
- Prefer the fewest files and the shortest working diff. Mark deliberate simplifications
  with a short comment naming the shortcut and its upgrade path.

## Governance

This constitution supersedes other practices for this project. Amendments MUST be recorded
in this file with a version bump and an updated Sync Impact Report, following semantic
versioning: MAJOR for incompatible principle removals/redefinitions, MINOR for new or
materially expanded principles/sections, PATCH for clarifications. All reviews MUST verify
compliance; unjustified complexity is grounds to reject a change.

**Version**: 1.0.0 | **Ratified**: 2026-06-22 | **Last Amended**: 2026-06-22
