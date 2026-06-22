"""Terminal UI: configuration, topic prompt, streaming logs, and manual-login pauses."""

import argparse

from rich.console import Console
from rich.prompt import Prompt

from . import config as config_mod
from . import pipeline
from .config import ConfigError

console = Console()


def _parse_args(argv):
    p = argparse.ArgumentParser(prog="media-scraper", description="Topic research scraper.")
    p.add_argument("--topic", help="Research topic (skips the prompt).")
    p.add_argument("--config", default="config.toml", help="Path to config.toml.")
    p.add_argument("--output-dir", help="Override report output directory.")
    p.add_argument("--model", help="Override LLM model for this run.")
    p.add_argument("--base-url", help="Override LLM endpoint for this run.")
    p.add_argument("--headless", action="store_true", help="Run the browser headless (no manual login).")
    p.add_argument("--configure", action="store_true", help="Edit config.toml interactively and exit.")
    p.add_argument("--max-sources", type=int, help="Override the max sources gathered this run (reach knob).")
    p.add_argument("--brief", action="store_true", help="Non-interactive run built from config (requires brand). For cron.")
    recency = p.add_mutually_exclusive_group()
    recency.add_argument("--days", type=int, help="Recency window: gather only items from the last N days.")
    recency.add_argument("--since", help="Recency window start date (YYYY-MM-DD); converted to a day count.")
    return p.parse_args(argv)


def _configure(path: str) -> None:
    """Interactive config editor. Never writes the secret (that stays in the env)."""
    try:
        current = config_mod.load_config(path)
    except Exception:
        current = config_mod.load_config("/nonexistent")  # defaults only

    console.print("[bold]Configure media-scraper[/] (the API key stays in $MEDIA_SCRAPER_API_KEY)")
    data = {
        "base_url": Prompt.ask("LLM base URL", default=current.base_url or "https://llm.frizzt.com/v1"),
        "model": Prompt.ask("Model", default=current.model or "qwen-moe-coder"),
        "output_dir": Prompt.ask("Output directory", default=str(current.output_dir)),
        "user_data_dir": Prompt.ask("Browser profile directory", default=str(current.user_data_dir)),
        "headless": Prompt.ask("Headless browser? (true/false)", default=str(current.headless).lower()) == "true",
        "max_sources": int(Prompt.ask("Max sources per run", default=str(current.max_sources))),
        "max_chars_per_source": int(Prompt.ask("Max chars per source", default=str(current.max_chars_per_source))),
        "brand": Prompt.ask("Brand for competitive briefs (blank for none)", default=current.brand),
        "recency_days": int(Prompt.ask("Recency window in days (0 = no filter)", default=str(current.recency_days))),
        # Lists are carried through as-is — edit them directly in config.toml.
        "competitors": current.competitors,
        "platforms": current.platforms,
    }
    config_mod.save_config(path, data)
    console.print(f"[green]Saved[/] {path}")


def main(argv=None) -> int:
    args = _parse_args(argv)

    if args.configure:
        _configure(args.config)
        return 0

    recency_days = args.days
    if args.since:
        from datetime import date
        try:
            recency_days = max(0, (date.today() - date.fromisoformat(args.since)).days)
        except ValueError:
            console.print(f"[red]Invalid --since date (expected YYYY-MM-DD):[/] {args.since}")
            return 1

    try:
        cfg = config_mod.load_config(
            args.config,
            overrides={
                "output_dir": args.output_dir,
                "model": args.model,
                "base_url": args.base_url,
                "headless": True if args.headless else None,
                "max_sources": args.max_sources,
                "recency_days": recency_days,
            },
        )
        config_mod.validate_for_run(cfg)
    except ConfigError as exc:
        console.print(f"[red]{exc}[/]")
        return 1
    except Exception as exc:
        console.print(f"[red]Config error:[/] {exc}")
        return 1

    if args.brief and not cfg.brand:
        console.print("[red]--brief requires 'brand' to be set in config.toml.[/]")
        return 1

    config_mod.ensure_dirs(cfg)

    if args.brief:
        topic = (
            f"{cfg.brand} vs {', '.join(cfg.competitors)}: brand perception and competitive intelligence"
            if cfg.competitors
            else f"{cfg.brand}: brand perception"
        )
    else:
        topic = args.topic or Prompt.ask("Research topic")
        if not topic.strip():
            console.print("[red]No topic provided.[/]")
            return 1

    def log(phase: str, msg: str = "") -> None:
        console.print(f"[bold cyan]{phase:>10}[/] {msg}")

    def pause(prompt: str) -> None:
        console.print(f"\n[bold yellow]⏸  {prompt}[/]")
        Prompt.ask("[yellow]Press Enter when you've finished[/]", default="")

    # Lazy imports so config/--configure errors don't require playwright/openai installed.
    from .browser import Browser
    from .llm import LLM, LLMError

    try:
        llm = LLM(cfg)
        with Browser(cfg, log=log, pause=pause) as browser:
            path = pipeline.run(
                topic,
                cfg,
                llm,
                gather=lambda plan, seen: pipeline.gather_sources(plan, cfg, browser, log, seen=seen),
                log=log,
                brand=cfg.brand if args.brief else "",
            )
    except pipeline.NoSourcesError as exc:
        console.print(f"[red]{exc}[/]")
        return 3
    except LLMError as exc:
        console.print(f"[red]LLM error:[/] {exc}")
        return 2

    console.print(f"\n[bold green]Report written:[/] {path}")
    return 0
