from __future__ import annotations
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
import numpy as np
from ..db import SessionLocal
from ..models.event import Event
from ..models.user import User
from ..recs.service import user_feed, similar_events, DIM
from ..ai.providers import get_provider, cached_summary
from sqlalchemy import text
from ..ai.providers import get_provider, cached_summary


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _to_vec(v) -> np.ndarray:
    if v is None:
        return np.zeros(DIM, dtype=np.float32)
    arr = np.array(v, dtype=np.float32)
    n = np.linalg.norm(arr)
    return arr if n == 0 else arr / n

@router.get("/feed")
def feed(user_id: str | None = None, limit: int = 20, db: Session = Depends(get_db)):
    bind = db.get_bind()
    with bind.connect() as conn:
        uvec = np.zeros(DIM, dtype=np.float32)
        user_interests: list[str] = []
        if user_id:
            u = db.query(User).filter(User.id == user_id).first()
            if u:
                if u.embed is not None:
                    uvec = _to_vec(u.embed)
                if isinstance(u.interests, list):
                    user_interests = u.interests

        rows = user_feed(conn, uvec, limit=limit)
        prov = get_provider()
        out = []
        for r in rows:
            desc = r.get("description") or ""
            title = r.get("title") or ""
            tags = r.get("tags") or []
            # cache key can be event id + short hash of text length
            ck = f'{r["id"]}:{len(desc)}'
            summary = cached_summary(ck, f"{title}. {desc}", max_words=22)
            why = prov.why_reason(user_interests, title, desc, tags)

            out.append({
                "id": str(r["id"]),
                "title": title,
                "start_time": r["start_time"].isoformat(),
                "location": r.get("location"),
                "tags": tags,
                "score": float(r.get("score", 0.0)),
                "summary": summary,
                "why": why,
            })
        return out

@router.get("/{event_id}/similar")
def similar(event_id: str, limit: int = 8, db: Session = Depends(get_db)):
    e = db.query(Event).filter(Event.id == event_id).first()
    if not e or e.embed is None:
        raise HTTPException(404, "event or embedding not found")
    bind = db.get_bind()
    with bind.connect() as conn:
        rows = similar_events(conn, _to_vec(e.embed), limit=limit)
        prov = get_provider()
        out = []
        for r in rows:
            desc = r.get("description") or ""
            title = r.get("title") or ""
            tags = r.get("tags") or []
            ck = f'{r["id"]}:{len(desc)}'
            summary = cached_summary(ck, f"{title}. {desc}", max_words=22)
            why = prov.why_reason([], title, desc, tags)
            out.append({
                "id": str(r["id"]),
                "title": title,
                "start_time": r["start_time"].isoformat(),
                "location": r.get("location"),
                "tags": tags,
                "score": float(r.get("score", 0.0)),
                "summary": summary,
                "why": why,
            })
        return out

@router.get("/search")
def search(q: str, limit: int = 20, user_id: str | None = None, db: Session = Depends(get_db)):
    bind = db.get_bind()
    with bind.connect() as conn:
        user_interests: list[str] = []
        if user_id:
            u = db.query(User).filter(User.id == user_id).first()
            if isinstance(u and u.interests, list):
                user_interests = u.interests

        rows = conn.execute(
            text("""
                SELECT id, title, description, start_time, location, tags, 0.0 AS score
                FROM events
                WHERE start_time > NOW()
                  AND (title ILIKE :p OR description ILIKE :p)
                ORDER BY start_time ASC
                LIMIT :lim
            """),
            {"p": f"%{q}%", "lim": limit},
        ).mappings().all()

        prov = get_provider()
        out = []
        for r in rows:
            desc = r.get("description") or ""
            title = r.get("title") or ""
            tags = r.get("tags") or []
            ck = f'{r["id"]}:{len(desc)}'
            out.append({
                "id": str(r["id"]),
                "title": title,
                "start_time": r["start_time"].isoformat(),
                "location": r.get("location"),
                "tags": tags,
                "score": 0.0,
                "summary": cached_summary(ck, f"{title}. {desc}", max_words=22),
                "why": prov.why_reason(user_interests, title, desc, tags),
            })
        return out

@router.get("/{event_id}")
def get_event(event_id: str, db: Session = Depends(get_db)):
    e = db.query(Event).filter(Event.id == event_id).first()
    if not e:
        raise HTTPException(404, "not found")
    return {
        "id": str(e.id),
        "title": e.title,
        "description": e.description,
        "start_time": e.start_time.isoformat(),
        "location": e.location,
        "tags": e.tags or [],
        "url": e.url,
    }