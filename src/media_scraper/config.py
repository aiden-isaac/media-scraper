"""Config loading/saving. Secret comes from the environment, never from config.toml."""

import os
import tomllib
from pathlib import Path

from .models import Config

ENV_KEY = "MEDIA_SCRAPER_API_KEY"

DEFAULTS: dict = {
    "base_url": "",
    "model": "",
    "output_dir": "reports",
    "user_data_dir": ".browser-profile",
    "headless": False,
    "max_sources": 12,
    "max_chars_per_source": 8000,
}


class ConfigError(Exception):
    """Raised for missing/invalid config or a missing secret (CLI exit code 1)."""


def load_config(path: str = "config.toml", overrides: dict | None = None) -> Config:
    data = dict(DEFAULTS)
    p = Path(path)
    if p.exists():
        with p.open("rb") as f:
            data.update(tomllib.load(f))
    if overrides:
        data.update({k: v for k, v in overrides.items() if v is not None})

    return Config(
        base_url=str(data["base_url"]),
        model=str(data["model"]),
        api_key=os.environ.get(ENV_KEY, ""),  # secret: env only
        output_dir=Path(data["output_dir"]),
        user_data_dir=Path(data["user_data_dir"]),
        headless=bool(data["headless"]),
        max_sources=int(data["max_sources"]),
        max_chars_per_source=int(data["max_chars_per_source"]),
    )


def validate_for_run(cfg: Config) -> None:
    missing = [name for name in ("base_url", "model") if not getattr(cfg, name)]
    if missing:
        raise ConfigError(
            f"Missing required config: {', '.join(missing)}. "
            f"Edit config.toml or run `--configure`."
        )
    if not cfg.api_key:
        raise ConfigError(f"No API key. Set the {ENV_KEY} environment variable.")


def ensure_dirs(cfg: Config) -> None:
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    cfg.user_data_dir.mkdir(parents=True, exist_ok=True)


def save_config(path: str, data: dict) -> None:
    """Write a minimal TOML file (tomllib is read-only). Never write secrets here."""
    lines = ["# media-scraper configuration. NO SECRETS HERE."]
    for key, value in data.items():
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        elif isinstance(value, (int, float)):
            rendered = str(value)
        else:
            rendered = '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'
        lines.append(f"{key} = {rendered}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
