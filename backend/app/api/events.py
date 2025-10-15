from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Sequence

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

# DB session dep (supports either module name)
try:
    from ..db import get_db  # type: ignore
except Exception:  # pragma: no cover
    from ..database import get_db  # type: ignore

# Lightweight “AI” helpers you already added
from ..ai.providers import get_provider, cached_summary

router = APIRouter(prefix="/events", tags=["events"])


# --------------------------- helpers ---------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _kwset(s: str) -> set[str]:
    import re
    stop = {
        "a","an","the","and","or","but","if","then","else","for","of","on","in","with",
        "to","from","at","by","about","is","are","be","this","that","it","as","you",
        "your","our","we","they","will","their","there","here"
    }
    words = set(w.lower() for w in re.findall(r"[A-Za-z0-9]+", s or ""))
    return {w for w in words if len(w) > 2 and w not in stop}

def _interest_score(user_interests: List[str], title: str, desc: str, tags: List[str]) -> float:
    if not user_interests:
        return 0.0
    text_kws = _kwset(f"{title} {desc}")
    score = 0.0
    for i in user_interests:
        i2 = i.lower().strip()
        if not i2:
            continue
        if i2 in text_kws:
            score += 1.0
        if any(i2 in (t or "").lower() for t in tags or []):
            score += 0.75
    return min(score, 3.0)

def _recency_boost(start_time: datetime) -> float:
    # Sooner = higher. 0–2 range.
    import math
    dt_days = (start_time - _now()).total_seconds() / 86400.0
    # events far in future get little boost; this week gets most
    return max(0.0, 2.0 * math.exp(-max(dt_days, 0.0) / 7.0))

def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    if inter == 0:
        return 0.0
    return inter / float(len(a | b))

def _row_to_event_dict(r: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(r["id"]),
        "title": r.get("title") or "",
        "start_time": r["start_time"].isoformat() if isinstance(r.get("start_time"), datetime) else r.get("start_time"),
        "location": r.get("location"),
        "tags": r.get("tags") or [],
        "url": r.get("url"),
    }


def _load_user_interests(db: Session, user_id: str | None) -> List[str]:
    if not user_id:
        return []
    row = db.execute(text("SELECT interests FROM users WHERE id=:id"), {"id": user_id}).first()
    interests = list(row[0]) if row and isinstance(row[0], list) else []
    return [str(x) for x in interests]


def _fetch_upcoming(db: Session, limit: int = 200) -> List[Dict[str, Any]]:
    bind = db.get_bind()
    with bind.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT id, title, description, start_time, location, tags, url
                FROM events
                WHERE start_time > NOW()
                ORDER BY start_time ASC
                LIMIT :lim
            """),
            {"lim": limit},
        ).mappings().all()
        return [dict(r) for r in rows]


# --------------------------- endpoints ---------------------------

@router.get("/feed")
def feed(
    user_id: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Personalized feed (simple interest + recency scoring)."""
    prov = get_provider()
    interests = _load_user_interests(db, user_id)
    rows = _fetch_upcoming(db, limit=400)

    scored: List[Dict[str, Any]] = []
    for r in rows:
        title = r.get("title") or ""
        desc = r.get("description") or ""
        tags = r.get("tags") or []
        start_time = r.get("start_time")
        if not isinstance(start_time, datetime):
            continue

        s_interest = _interest_score(interests, title, desc, tags)
        s_when = _recency_boost(start_time)
        score = s_interest + s_when

        ck = f'{r["id"]}:{len(desc)}'
        item = _row_to_event_dict(r)
        item.update({
            "score": round(score, 6),
            "summary": cached_summary(ck, f"{title}. {desc}", max_words=22),
            "why": prov.why_reason(interests, title, desc, tags),
        })
        scored.append(item)

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]


@router.get("/search")
def search(
    q: str,
    limit: int = Query(20, ge=1, le=100),
    user_id: str | None = None,
    db: Session = Depends(get_db),
):
    """Keyword search (title/description ILIKE) with summaries/why."""
    prov = get_provider()
    interests = _load_user_interests(db, user_id)

    bind = db.get_bind()
    with bind.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT id, title, description, start_time, location, tags, url
                FROM events
                WHERE start_time > NOW()
                  AND (title ILIKE :p OR description ILIKE :p)
                ORDER BY start_time ASC
                LIMIT :lim
            """),
            {"p": f"%{q}%", "lim": limit},
        ).mappings().all()

    out: List[Dict[str, Any]] = []
    for r in rows:
        title = r.get("title") or ""
        desc = r.get("description") or ""
        tags = r.get("tags") or []
        ck = f'{r["id"]}:{len(desc)}'

        item = _row_to_event_dict(r)
        item.update({
            "score": 0.0,
            "summary": cached_summary(ck, f"{title}. {desc}", max_words=22),
            "why": prov.why_reason(interests, title, desc, tags),
        })
        out.append(item)
    return out


@router.get("/{event_id}")
def get_event(event_id: str, db: Session = Depends(get_db)):
    bind = db.get_bind()
    with bind.connect() as conn:
        r = conn.execute(
            text("""
                SELECT id, title, description, start_time, location, tags, url
                FROM events WHERE id = :id
            """),
            {"id": event_id},
        ).mappings().first()

    if not r:
        raise HTTPException(status_code=404, detail="not found")

    return {
        "id": str(r["id"]),
        "title": r.get("title"),
        "description": r.get("description"),
        "start_time": r.get("start_time").isoformat() if isinstance(r.get("start_time"), datetime) else r.get("start_time"),
        "location": r.get("location"),
        "tags": r.get("tags") or [],
        "url": r.get("url"),
    }


@router.get("/{event_id}/similar")
def similar(
    event_id: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Similar events (semantic-lite):
      - start from the target event
      - compute token overlap + tag overlap
      - return top-N upcoming
    If you later wire real vector similarity, swap the scoring block.
    """
    bind = db.get_bind()
    with bind.connect() as conn:
        base = conn.execute(
            text("SELECT id, title, description, start_time, location, tags, url FROM events WHERE id=:id"),
            {"id": event_id},
        ).mappings().first()
        if not base:
            raise HTTPException(404, "not found")

        # candidate pool: upcoming events (exclude self), grab a decent window
        rows = conn.execute(
            text("""
                SELECT id, title, description, start_time, location, tags, url
                FROM events
                WHERE start_time > NOW() AND id <> :id
                ORDER BY start_time ASC
                LIMIT 400
            """),
            {"id": event_id},
        ).mappings().all()

    base_kw = _kwset(f"{base.get('title') or ''} {base.get('description') or ''}")
    base_tags = set((base.get("tags") or []))

    prov = get_provider()
    out: List[Dict[str, Any]] = []
    for r in rows:
        title = r.get("title") or ""
        desc = r.get("description") or ""
        tags = r.get("tags") or []
        kw = _kwset(f"{title} {desc}")
        tag_overlap = _jaccard(base_tags, set(tags))
        text_overlap = _jaccard(base_kw, kw)
        score = 0.6 * text_overlap + 0.4 * tag_overlap

        ck = f'{r["id"]}:{len(desc)}'
        item = _row_to_event_dict(r)
        item.update({
            "score": round(score, 6),
            "summary": cached_summary(ck, f"{title}. {desc}", max_words=22),
            "why": prov.why_reason(list(base_tags), title, desc, tags),
        })
        out.append(item)

    out.sort(key=lambda x: x["score"], reverse=True)
    return out[:limit]
