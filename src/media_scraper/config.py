"""Config loading/saving. Secret comes from the environment, never from config.toml."""

import os
import tomllib
from pathlib import Path

from .models import PLATFORMS, Config

ENV_KEY = "MEDIA_SCRAPER_API_KEY"

DEFAULTS: dict = {
    "base_url": "",
    "model": "",
    "output_dir": "reports",
    "user_data_dir": ".browser-profile",
    "headless": False,
    "max_sources": 12,
    "max_chars_per_source": 8000,
    "brand": "",
    "competitors": [],
    "platforms": [],
    "recency_days": 0,
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

    max_sources = int(data["max_sources"])
    recency_days = int(data["recency_days"])
    if recency_days < 0:
        raise ConfigError("recency_days must be >= 0.")
    if max_sources < 1:
        raise ConfigError("max_sources must be >= 1.")

    # Unknown platforms are dropped (ponytail: no logger here; typos surface as missing coverage).
    platforms = [p for p in (str(x).lower() for x in data["platforms"]) if p in PLATFORMS]

    return Config(
        base_url=str(data["base_url"]),
        model=str(data["model"]),
        api_key=os.environ.get(ENV_KEY, ""),  # secret: env only
        output_dir=Path(data["output_dir"]),
        user_data_dir=Path(data["user_data_dir"]),
        headless=bool(data["headless"]),
        max_sources=max_sources,
        max_chars_per_source=int(data["max_chars_per_source"]),
        brand=str(data["brand"]),
        competitors=[str(x) for x in data["competitors"]],
        platforms=platforms,
        recency_days=recency_days,
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
    def _str(v) -> str:
        return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'

    lines = ["# media-scraper configuration. NO SECRETS HERE."]
    for key, value in data.items():
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        elif isinstance(value, (int, float)):
            rendered = str(value)
        elif isinstance(value, (list, tuple)):
            rendered = "[" + ", ".join(_str(v) for v in value) + "]"
        else:
            rendered = _str(value)
        lines.append(f"{key} = {rendered}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
