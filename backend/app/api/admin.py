from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..models.event import Event
from ..models.user import User
from ..recs.embeddings import embed_text
from sqlalchemy import text
from datetime import datetime, timezone

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/reindex")
def reindex(db: Session = Depends(get_db)):
    updated_events = 0
    updated_users = 0

    evs = db.query(Event).filter(Event.embed == None).limit(5000).all()  # noqa: E711
    for e in evs:
        txt = f"{e.title or ''} {e.description or ''}".strip()
        e.embed = embed_text(txt).tolist()
        updated_events += 1

    us = db.query(User).filter(User.embed == None).limit(5000).all()  # noqa: E711
    for u in us:
        ints = u.interests or []
        txt = " ".join(ints) if isinstance(ints, list) else str(ints)
        u.embed = embed_text(txt).tolist()
        updated_users += 1

    db.commit()
    return {"events": updated_events, "users": updated_users}
    
@router.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    bind = db.get_bind()
    with bind.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT
                  SUM(CASE WHEN clicked THEN 1 ELSE 0 END) AS clicks,
                  SUM(CASE WHEN saved THEN 1 ELSE 0 END)   AS saves,
                  SUM(CASE WHEN rsvp THEN 1 ELSE 0 END)    AS rsvps
                FROM feedback
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """)
        ).first()
        clicks = int(rows.clicks or 0)
        saves  = int(rows.saves or 0)
        rsvps  = int(rows.rsvps or 0)
    return {"window": "last_24h", "clicks": clicks, "saves": saves, "rsvps": rsvps,
            "interactions": clicks + saves + rsvps}