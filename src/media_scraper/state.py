"""Per-brief seen-URL store for cross-run "latest only" dedup.

A flat JSON set under `.state/<slug>.json`.
ponytail: flat JSON set is the laziest durable state; swap for SQLite only if brief
count / URL volume ever makes load/save slow.
"""

import json
from datetime import datetime, timezone
from pathlib import Path


def _path(slug: str, state_dir: str) -> Path:
    return Path(state_dir) / f"{slug}.json"


def load_seen(slug: str, state_dir: str = ".state") -> set[str]:
    """Return the set of URLs already reported for this brief (empty if no state yet)."""
    p = _path(slug, state_dir)
    if not p.exists():
        return set()
    try:
        return set(json.loads(p.read_text(encoding="utf-8")).get("seen", []))
    except Exception:
        return set()  # corrupt/unreadable state must not abort a run


def save_seen(slug: str, urls: set[str], state_dir: str = ".state") -> None:
    """Persist the union of seen URLs. Called only after a report is written."""
    p = _path(slug, state_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "seen": sorted(urls),
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    p.write_text(json.dumps(payload), encoding="utf-8")
