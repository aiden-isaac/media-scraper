"""Playwright persistent-context browser with manual login/captcha pauses.

Persistent context (user_data_dir) reuses manual logins across runs. Headed by default so the
user can sign in / solve captchas themselves — the tool never enters credentials or solves
captchas. Playwright is imported lazily so other modules import without it.
"""

import re

from .models import Config, Source

_LOGIN_URL_HINTS = ("login", "signin", "sign-in", "/auth", "captcha", "challenge", "consent")
_BLOCK_TEXT_HINTS = ("log in", "sign in", "captcha", "verify you are human", "are you a robot")


def _noop(*_args, **_kwargs) -> None:
    pass


class Browser:
    """Context manager wrapping a single persistent browser page."""

    def __init__(self, cfg: Config, log=_noop, pause=None):
        self.cfg = cfg
        self.log = log
        self.pause = pause  # callable(prompt) used to block for manual sign-in
        self._pw = None
        self._ctx = None
        self._page = None

    def __enter__(self) -> "Browser":
        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        self._ctx = self._pw.chromium.launch_persistent_context(
            user_data_dir=str(self.cfg.user_data_dir),
            headless=self.cfg.headless,
        )
        self._page = self._ctx.new_page()
        return self

    def __exit__(self, *_exc) -> None:
        try:
            if self._ctx is not None:
                self._ctx.close()
        finally:
            if self._pw is not None:
                self._pw.stop()

    def fetch_page(self, url: str, kind: str = "web", title: str = "") -> Source:
        page = self._page
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as exc:
            return Source(url=url, title=title, kind=kind, status="fetch_error", error=str(exc)[:200])

        if self._looks_blocked(page):
            if self.pause is not None and not self.cfg.headless:
                self.pause(f"'{url}' needs sign-in or a captcha. Solve it in the browser window.")
                try:
                    page.reload(wait_until="domcontentloaded", timeout=30000)
                except Exception:
                    pass
            if self._looks_blocked(page):
                return Source(
                    url=url,
                    title=title or self._safe_title(page) or url,
                    kind=kind,
                    status="login_skipped",
                    error="login/captcha not resolved",
                )

        return Source(
            url=url,
            title=title or self._safe_title(page) or url,
            kind=kind,
            text=self._extract(page),
            status="ok",
        )

    def _looks_blocked(self, page) -> bool:
        try:
            if page.query_selector("input[type=password]"):
                return True
        except Exception:
            pass
        url = (getattr(page, "url", "") or "").lower()
        if any(hint in url for hint in _LOGIN_URL_HINTS):
            return True
        try:
            text = page.inner_text("body")[:2000].lower()
        except Exception:
            text = ""
        if len(text.strip()) < 80 and any(hint in text for hint in _BLOCK_TEXT_HINTS):
            return True
        return False

    def _extract(self, page) -> str:
        try:
            raw = page.inner_text("body")
        except Exception:
            raw = ""
        text = re.sub(r"\n{3,}", "\n\n", raw)
        text = re.sub(r"[ \t]+", " ", text).strip()
        return text[: self.cfg.max_chars_per_source]

    @staticmethod
    def _safe_title(page) -> str:
        try:
            return page.title() or ""
        except Exception:
            return ""
