# backend/app/ai/providers.py
from __future__ import annotations
from typing import Iterable
from functools import lru_cache
import re

_STOP = {
    "a","an","the","and","or","but","if","then","else","for","of","on","in","with","to","from",
    "at","by","about","is","are","be","this","that","it","as","you","your","our","we","they"
}
_WORD = re.compile(r"[A-Za-z0-9]+")

class LLM:
    def summarize(self, text: str, max_words: int = 22) -> str: ...
    def why_reason(self, user_interests: list[str] | None, title: str, description: str | None, tags: list[str] | None) -> str: ...
    def zero_shot(self, text: str, labels: Iterable[str]) -> list[str]: ...

class LocalProvider(LLM):
    def summarize(self, text: str, max_words: int = 22) -> str:
        t = (text or "").strip()
        if not t:
            return ""
        # take first sentence-ish, then trim to max_words
        s = re.split(r"(?<=[.!?])\s+", t)[0]
        words = s.split()
        if len(words) > max_words:
            s = " ".join(words[:max_words]) + "…"
        return s

    def why_reason(self, user_interests, title, description, tags):
        tags = tags or []
        user_interests = [i.lower() for i in (user_interests or [])]
        text = f"{title or ''} {description or ''}".lower()
        # keyword overlap
        kws = {w for w in _WORD.findall(text) if w not in _STOP and len(w) > 2}
        hits = [i for i in user_interests if any(i in w or w in i for w in kws)]
        tag_hits = [t for t in tags if t and t.lower() in kws]

        reasons = []
        if hits:
            reasons.append(f"matches your interests: {', '.join(sorted(set(hits))[:3])}")
        if tag_hits:
            reasons.append(f"tagged {', '.join(sorted(set(tag_hits))[:3])}")
        if "free" in kws:
            reasons.append("free to attend")
        if "career" in kws or "internship" in kws:
            reasons.append("career-focused")
        if not reasons:
            reasons.append("popular and coming up soon")
        # stitch 1–2 reasons max
        out = " • ".join(reasons[:2])
        # small cap first letter
        if out and out[0].islower(): out = out[0].upper() + out[1:]
        return out

    def zero_shot(self, text: str, labels: Iterable[str]) -> list[str]:
        text = (text or "").lower()
        out = []
        for lb in labels:
            l = str(lb).lower()
            if l in text:
                out.append(lb)
        return out

@lru_cache(maxsize=1)
def get_provider() -> LLM:
    # could read env (LLM_PROVIDER) later; for now always local
    return LocalProvider()

# small summary cache so repeated feed calls don’t recompute
@lru_cache(maxsize=5000)
def cached_summary(cache_key: str, text: str, max_words: int = 22) -> str:
    return LocalProvider().summarize(text, max_words=max_words)
