# Contract: CLI Surface

The tool is invoked as a module; interaction is an interactive `rich` TUI, with a few flags
for non-interactive overrides.

## Entry point

```
python -m media_scraper [OPTIONS]
```

(Also installed as the console script `media-scraper` via `pyproject.toml`.)

## Options

| Flag | Type | Default | Effect |
|------|------|---------|--------|
| `--topic "<text>"` | str | (prompt) | Skip the topic prompt; run this topic directly. |
| `--config <path>` | path | `./config.toml` | Config file location. |
| `--output-dir <path>` | path | from config | Override report output directory. |
| `--model <name>` | str | from config | Override model for this run. |
| `--base-url <url>` | str | from config | Override LLM endpoint for this run. |
| `--headless` | flag | off | Run the browser headless (disables manual login — for open-source-only runs). |
| `--configure` | flag | — | Open the interactive configuration editor and exit. |
| `-h, --help` | flag | — | Show usage. |

Secret is **always** read from env `MEDIA_SCRAPER_API_KEY` — never a flag (avoids shell
history leakage).

## Interactive flow (no `--topic`)

1. Load config; if missing required fields, enter the configuration editor.
2. Prompt for the research topic (multi-line allowed).
3. Stream phase logs: `plan → gather → analyze → synthesize`.
4. On a login/captcha block, pause with a clear prompt; wait for the user to press Enter
   after signing in; re-check and continue (or skip the source).
5. On completion, print the path of the written Markdown report.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Report written successfully. |
| 1 | Fatal config/secret error (e.g. missing API key) — nothing run. |
| 2 | LLM backend unreachable or returned unusable output — no report written. |
| 3 | Plan produced no usable sources / no results found. |

## Guarantees

- A single failed source never changes the exit code from 0 (FR-013).
- No secret value appears in any printed output or log line (FR-011 / SC-005).
