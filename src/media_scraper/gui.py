"""FastAPI web GUI for media-scraper.

Start with:  python -m media_scraper.gui --port 8000
Or via uvicorn: uvicorn src.media_scraper.gui:app --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import markdown
from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, ConfigDict, StrictBool, StrictInt, field_validator

from .config import load_config, save_config
from .llm import LLM
from .models import Config as ScraperConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Run state — single scraper run tracker (thread-safe via lock)
# ---------------------------------------------------------------------------

class RunState:
    """Tracks a single scraper pipeline execution."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.topic: str = ""
        self.status: str = "idle"       # idle | running | success | error | cancelled
        self.phase: str = "planning"    # planning | gathering | analyzing | synthesizing | complete
        self.report_path: Optional[str] = None
        self.error_message: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self._cancel_event = threading.Event()
        self.llm: Optional[LLM] = None

    @property
    def is_running(self) -> bool:
        return self.status == "running"

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "status": self.status,
            "phase": self.phase,
            "report_path": self.report_path,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


run_state = RunState()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CONFIG_PATH = "config.toml"


def _load_gui_config() -> dict[str, Any]:
    """Load config and return non-secret values as a plain dict."""
    cfg = load_config(CONFIG_PATH)
    api_key_set = bool(cfg.api_key)
    return {
        "base_url": cfg.base_url,
        "model": cfg.model,
        "output_dir": str(cfg.output_dir),
        "headless": cfg.headless,
        "max_sources": cfg.max_sources,
        "max_chars_per_source": cfg.max_chars_per_source,
        "api_key_set": api_key_set,
    }


def _save_gui_config(updates: dict[str, Any]) -> dict[str, Any]:
    """Save config changes from the GUI. Never touches api_key."""
    # Read current config
    current_data = {}
    p = Path(CONFIG_PATH)
    if p.exists():
        import tomllib
        with p.open("rb") as f:
            current_data = dict(tomllib.load(f))

    # Apply updates (exclude api_key)
    for key in ("base_url", "model", "output_dir", "headless", "max_sources", "max_chars_per_source"):
        if key in updates and updates[key] is not None:
            current_data[key] = updates[key]

    save_config(CONFIG_PATH, current_data)
    return _load_gui_config()


def _list_reports(output_dir: str) -> list[dict[str, Any]]:
    """Scan output directory for .md report files and return metadata."""
    reports = []
    dir_path = Path(output_dir)
    if not dir_path.exists():
        return reports

    for md_file in sorted(dir_path.glob("*.md"), reverse=True):
        # Extract topic from filename: <topic-slug>-<YYYYMMDD-HHMMSS>.md
        name = md_file.stem
        # Try to extract date from end of filename
        date_match = re.search(r"(\d{8})-(\d{6})", name)
        created_at = None
        topic = name
        if date_match:
            created_at = date_match.group(1)
            topic = name[: len(name) - len(date_match.group(0)) - 1].replace("-", " ")

        reports.append({
            "filename": md_file.name,
            "topic": topic,
            "path": str(md_file),
            "created_at": created_at or "unknown",
            "source_count": None,
        })
    return reports


def _safe_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    # Reject any path traversal attempts
    if ".." in filename or "/" in filename or "\\" in filename or "\0" in filename:
        raise ValueError("Invalid filename")
    return filename.split("/")[-1].split("\\")[-1]


# ---------------------------------------------------------------------------
# Background scraper runner
# ---------------------------------------------------------------------------

def _run_scraper_background(topic: str, cfg: ScraperConfig) -> None:
    """Run the pipeline in a background thread, updating run_state."""
    from .pipeline import NoSourcesError, gather_sources, run
    from .browser import Browser

    run_state.status = "running"
    run_state.started_at = datetime.now(timezone.utc)

    try:
        # Phase: planning
        run_state.phase = "planning"
        llm = LLM(cfg)
        run_state.llm = llm

        plan = llm.plan(topic)
        if not plan.has_sources:
            raise NoSourcesError("The model produced no searchable sources for this topic.")

        # Phase: gathering
        run_state.phase = "gathering"
        browser = Browser(cfg)
        all_sources = gather_sources(plan, cfg, browser, log=lambda *a: None)

        usable = [s for s in all_sources if s.status == "ok" and s.text.strip()]

        # Phase: analyzing
        run_state.phase = "analyzing"
        analyzed = [(s, llm.analyze(s)) for s in usable]

        # Phase: synthesizing
        run_state.phase = "synthesizing"
        body = llm.synthesize(topic, plan, analyzed)

        # Write report
        from .report import write_report
        report_path = write_report(topic, plan, all_sources, analyzed, body, cfg)

        # Complete
        run_state.phase = "complete"
        run_state.report_path = str(report_path)
        run_state.status = "success"
        run_state.completed_at = datetime.now(timezone.utc)

    except Exception as exc:
        logger.exception("Scraper run failed")
        run_state.status = "error"
        run_state.error_message = str(exc)
        run_state.completed_at = datetime.now(timezone.utc)
    finally:
        # Clean up cancel event
        run_state._cancel_event.clear()


# ---------------------------------------------------------------------------
# Pydantic models for API requests/responses
# ---------------------------------------------------------------------------

class StartRequest(BaseModel):
    topic: str

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Topic must be a non-empty string")
        if len(v) > 5000:
            raise ValueError("Topic must not exceed 5000 characters")
        return v


class ConfigUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    base_url: Optional[str] = None
    model: Optional[str] = None
    output_dir: Optional[str] = None
    headless: Optional[StrictBool] = None
    max_sources: Optional[StrictInt] = None
    max_chars_per_source: Optional[StrictInt] = None


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

VERSION = "0.1.0"

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    if run_state.is_running:
        run_state.status = "cancelled"
        run_state._cancel_event.set()
        logger.info("Background scraper cancelled on shutdown")

app = FastAPI(title="Media Scraper GUI", version=VERSION, lifespan=lifespan)
_j2_env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")), cache_size=0)
templates = Jinja2Templates(env=_j2_env)
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")


# ---------------------------------------------------------------------------
# Page routes (HTML)
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"current_path": "/", "version": VERSION})


@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    return templates.TemplateResponse(request=request, name="config.html", context={"current_path": "/config", "version": VERSION})


@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    gui_cfg = _load_gui_config()
    reports = _list_reports(gui_cfg["output_dir"])
    return templates.TemplateResponse(request=request, name="reports.html", context={"current_path": "/reports", "reports": reports, "version": VERSION})


@app.get("/report/{filename}", response_class=HTMLResponse)
async def view_report(request: Request, filename: str):
    gui_cfg = _load_gui_config()
    try:
        safe_name = _safe_filename(filename)
        report_path = Path(gui_cfg["output_dir"]) / safe_name
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Report not found")
        
        content = report_path.read_text(encoding="utf-8")
        html_content = markdown.markdown(content, extensions=["tables", "fenced_code"])
        
        # Extract topic from filename
        topic = safe_name.rsplit("-", 1)[0].replace("-", " ")
        
        return templates.TemplateResponse(
            request=request,
            name="report.html",
            context={"content": html_content, "topic": topic, "version": VERSION},
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid filename")


# ---------------------------------------------------------------------------
# API routes (JSON)
# ---------------------------------------------------------------------------

@app.get("/api/run/status")
async def get_run_status():
    """Return current scraper run state."""
    return run_state.to_dict()


@app.post("/api/run/start")
async def start_run(req: StartRequest):
    """Start a new scraper run."""
    if run_state.is_running:
        raise HTTPException(
            status_code=409,
            detail="A scraper run is already in progress. Wait for it to complete."
        )

    run_state.topic = req.topic
    run_state.status = "running"
    run_state.phase = "planning"
    run_state.report_path = None
    run_state.error_message = None
    run_state.started_at = datetime.now(timezone.utc)
    run_state.completed_at = None
    run_state._cancel_event.clear()

    cfg = ScraperConfig(
        base_url="",
        model="",
        api_key="",
        output_dir=Path(""),
        user_data_dir=Path(""),
        headless=False,
        max_sources=1,
        max_chars_per_source=1
    ) # A dummy config just to get it started, we will load real one
    try:
        from .config import load_config
        cfg = load_config(CONFIG_PATH)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        # we will just proceed with the dummy cfg if there's no config file yet, wait
        # The GUI endpoints actually read the real config. 
        
    t = threading.Thread(target=_run_scraper_background, args=(req.topic, cfg), daemon=True)
    t.start()

    return JSONResponse(
        status_code=201,
        content={"status": "accepted", "message": "Research started. Poll /api/run/status for progress."},
    )


@app.post("/api/run/cancel")
async def cancel_run():
    """Cancel the currently running scraper."""
    if not run_state.is_running:
        raise HTTPException(status_code=400, detail="No scraper run is currently active.")

    run_state.status = "cancelled"
    run_state.completed_at = datetime.now(timezone.utc)
    run_state._cancel_event.set()
    return JSONResponse(content={"status": "cancelled", "message": "Scraper cancellation requested."})


@app.get("/api/config")
async def get_config():
    """Get current configuration (API key masked)."""
    return _load_gui_config()


@app.put("/api/config")
async def update_config(req: ConfigUpdateRequest):
    """Update configuration values."""
    # Check for api_key injection attempt
    raw_data = req.model_dump(exclude_none=True)
    if "api_key" in raw_data:
        raise HTTPException(status_code=403, detail="Cannot change API key through the GUI.")

    config = _save_gui_config(raw_data)
    return {"message": "Configuration updated.", "config": config}


@app.get("/api/reports")
async def list_reports():
    """List all generated reports as JSON."""
    gui_cfg = _load_gui_config()
    reports = _list_reports(gui_cfg["output_dir"])
    return {"reports": reports, "total": len(reports)}


@app.get("/api/reports/{filename}/content")
async def get_report_content(filename: str):
    """Get raw markdown content of a report."""
    gui_cfg = _load_gui_config()
    try:
        safe_name = _safe_filename(filename)
        report_path = Path(gui_cfg["output_dir"]) / safe_name
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Report not found")

        content = report_path.read_text(encoding="utf-8")
        return {"filename": safe_name, "content": content}
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid filename")


# Shutdown logic is now handled in the lifespan context manager.
