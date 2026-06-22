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

    def search_site(self, platform: str, query: str, limit: int = 5, fresh: bool = False) -> list[Source]:
        """Tier 1+2 in-site search: navigate the platform's search URL, extract result
        links/snippets as social Sources; DOM search-box fill+submit as fallback.

        Returns [] when the platform is walled and the session can't resolve it — the caller
        then falls back to keyless `site:` web search.
        ponytail: result extraction is an anchor-href heuristic, not per-platform parsers;
        add a parser only if a platform's links stop coming through.
        """
        from . import sources

        page = self._page
        try:
            page.goto(sources.search_url(platform, query, fresh=fresh), wait_until="domcontentloaded", timeout=30000)
        except Exception as exc:
            self.log("gather", f"search_site {platform} failed: {str(exc)[:120]}")
            return []

        if self._looks_blocked(page):
            if self.pause is not None and not self.cfg.headless:
                self.pause(f"Sign in to {platform} in the browser window to search it.")
                try:
                    page.reload(wait_until="domcontentloaded", timeout=30000)
                except Exception:
                    pass
            if self._looks_blocked(page):
                return []  # walled & unresolved — caller uses the site: fallback

        results = self._extract_result_links(page, platform, limit)
        if not results and self._dom_search(page, query):
            results = self._extract_result_links(page, platform, limit)
        return results

    def _extract_result_links(self, page, platform: str, limit: int) -> list[Source]:
        from . import sources

        domain = sources.SITE_DOMAINS.get(platform, platform)
        try:
            anchors = page.eval_on_selector_all(
                "a[href]", "els => els.map(e => [e.href, (e.innerText||'').trim()])"
            )
        except Exception:
            return []
        out: list[Source] = []
        seen: set[str] = set()
        chrome = ("/search", "/login", "/signup", "/help", "/about", "/policies", "/settings")
        for href, text in anchors:
            low = (href or "").lower()
            if not href or domain not in low or href in seen or any(x in low for x in chrome):
                continue
            seen.add(href)
            out.append(
                Source(
                    url=href,
                    title=(text or href)[:120],
                    kind="social",
                    text=(text or "")[: self.cfg.max_chars_per_source],
                    status="ok",
                )
            )
            if len(out) >= limit:
                break
        return out

    def _dom_search(self, page, query: str) -> bool:
        for sel in (
            "input[type=search]",
            "input[name=q]",
            "input[aria-label*=Search i]",
            "input[placeholder*=Search i]",
        ):
            try:
                box = page.query_selector(sel)
                if box:
                    box.fill(query)
                    box.press("Enter")
                    page.wait_for_load_state("domcontentloaded", timeout=15000)
                    return True
            except Exception:
                continue
        return False

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
