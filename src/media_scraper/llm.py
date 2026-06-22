"""OpenAI-compatible LLM wrapper.

The orchestrator drives control flow by parsing structured JSON the model returns — it does
NOT use native tool-calling (the default backend is a local model whose tool-calling is
unreliable). See specs .../contracts/llm-json.md.
"""

import json
import re

from .models import Config, ResearchPlan, Source, SourceAnalysis

_JSON_ONLY = "\nRespond with ONLY a valid JSON object. No prose, no markdown, no code fences."


class LLMError(Exception):
    """Backend unreachable or returned unusable output (CLI exit code 2)."""


def _normalize_subject(value: str, brands: list[str]) -> str:
    """Map the model's free-text subject to one of `brands` (case-insensitive) or "other"."""
    if not brands:
        return ""
    v = value.strip().lower()
    for b in brands:
        if v == b.lower():
            return b
    return "other"


def _extract_json(text: str) -> dict | None:
    if not text:
        return None
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n?", "", t)
        t = re.sub(r"\n?```$", "", t).strip()
    try:
        obj = json.loads(t)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    i, j = t.find("{"), t.rfind("}")
    if 0 <= i < j:
        try:
            obj = json.loads(t[i : j + 1])
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None
    return None


class LLM:
    def __init__(self, cfg: Config):
        from openai import OpenAI  # lazy import

        self.cfg = cfg
        self.model = cfg.model
        # OpenAI-compatible endpoint; key from env via Config. Fallback placeholder for
        # local servers that require a non-empty key but don't validate it.
        self.client = OpenAI(base_url=cfg.base_url, api_key=cfg.api_key or "sk-none")

    def _chat(self, system: str, user: str) -> str:
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except Exception as exc:  # network / auth / server error
            raise LLMError(f"LLM request failed: {exc}") from exc
        if not resp.choices:
            raise LLMError("LLM returned no choices.")
        return resp.choices[0].message.content or ""

    def _chat_json(self, system: str, user: str) -> dict:
        raw = self._chat(system + _JSON_ONLY, user)
        obj = _extract_json(raw)
        if obj is None:  # one repair retry
            raw = self._chat(
                system + _JSON_ONLY,
                user + "\n\nYour previous reply was not valid JSON. Return ONLY the JSON object.",
            )
            obj = _extract_json(raw)
        if obj is None:
            raise LLMError("The model did not return valid JSON after a repair attempt.")
        return obj

    def plan(self, topic: str) -> ResearchPlan:
        system = (
            "You are a research planner. Given a topic, produce a JSON research plan with "
            'keys: "sub_questions" (string[]), "search_queries" (string[]), '
            '"rss_feeds" (string[] of feed URLs, may be empty), and "target_sites" '
            "(string[] of specific sites/social handles worth checking, may be empty)."
        )
        user = f"Topic:\n{topic}"
        if self.cfg.brand:
            user += (
                f"\n\nThis is a competitive brand-perception brief. Primary brand: "
                f"{self.cfg.brand}. Competitors: {', '.join(self.cfg.competitors) or 'none'}. "
                "Make search_queries comparative — cover the brand AND each competitor "
                "(reputation, complaints, service, news)."
            )
        if self.cfg.recency_days:
            user += f"\nFocus on the last {self.cfg.recency_days} days only."
        data = self._chat_json(system, user)
        return ResearchPlan(
            topic=topic,
            sub_questions=[str(x) for x in (data.get("sub_questions") or [])],
            search_queries=[str(x) for x in (data.get("search_queries") or [])],
            rss_feeds=[str(x) for x in (data.get("rss_feeds") or [])],
            target_sites=[str(x) for x in (data.get("target_sites") or [])],
        )

    def analyze(self, source: Source) -> SourceAnalysis:
        brands = self.cfg.brands
        subject_hint = (
            f' "subject" (which of these brands the source primarily concerns — one of '
            f"{brands + ['other']}; use \"other\" if none), and"
            if brands
            else ""
        )
        system = (
            "You are a source analyst. Given a source, return JSON with keys: "
            '"claims" (string[] of key claims), "sentiment" (one of '
            '"positive","neutral","negative","mixed"), "credibility" (integer 1-5, '
            f"5 = highly credible),{subject_hint} "
            '"credibility_rationale" (one or two sentences).'
        )
        user = f"URL: {source.url}\nTitle: {source.title}\n\nContent:\n{source.text}"
        try:
            data = self._chat_json(system, user)
        except LLMError:
            # Analysis of one source must not abort the run; fall back to neutral defaults.
            return SourceAnalysis(
                url=source.url,
                sentiment="neutral",
                credibility=3,
                credibility_rationale="Analysis unavailable (model returned unusable output).",
                subject=_normalize_subject("", brands),
            )

        sentiment = str(data.get("sentiment", "neutral")).lower()
        if sentiment not in ("positive", "neutral", "negative", "mixed"):
            sentiment = "neutral"
        try:
            cred = int(data.get("credibility", 3))
        except (TypeError, ValueError):
            cred = 3
        cred = min(5, max(1, cred))
        return SourceAnalysis(
            url=source.url,
            claims=[str(x) for x in (data.get("claims") or [])],
            sentiment=sentiment,
            credibility=cred,
            credibility_rationale=str(data.get("credibility_rationale", "")),
            subject=_normalize_subject(str(data.get("subject", "")), brands),
        )

    def synthesize(self, topic: str, plan: ResearchPlan, analyzed: list[tuple[Source, SourceAnalysis]]) -> str:
        system = (
            "Write a concise Markdown research report body. Start with a '## Summary' section, "
            "then a '## Key Findings' section with bullet points. Base it ONLY on the provided "
            "per-source analyses and cite source URLs inline. Do not invent sources."
        )
        parts = [f"Topic: {topic}", f"Sub-questions: {', '.join(plan.sub_questions) or 'none'}", "", "Analyzed sources:"]
        for s, a in analyzed:
            claims = "; ".join(a.claims[:5]) if a.claims else "(no claims extracted)"
            parts.append(
                f"- {s.title or s.url} ({s.url}) — sentiment={a.sentiment}, "
                f"credibility={a.credibility}/5. Claims: {claims}"
            )
        if not analyzed:
            parts.append("- (no sources were successfully gathered)")
        return self._chat(system, "\n".join(parts))
