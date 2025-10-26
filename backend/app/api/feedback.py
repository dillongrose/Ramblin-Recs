from __future__ import annotations
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..models.feedback import Feedback
from ..models.user import User
from ..models.event import Event
import numpy as np

router = APIRouter(prefix="/feedback", tags=["feedback"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class FeedbackIn(BaseModel):
    user_id: str
    event_id: str
    clicked: bool | None = None
    saved: bool | None = None
    rsvp: bool | None = None
    dwell_seconds: int | None = None

def _normalize(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v if n == 0.0 else (v / n)

@router.post("")
def log_feedback(body: FeedbackIn, db: Session = Depends(get_db)):
    # write row
    rec = Feedback(
        user_id=body.user_id,
        event_id=body.event_id,
        clicked=bool(body.clicked or False),
        saved=bool(body.saved or False),
        rsvp=bool(body.rsvp or False),
        dwell_seconds=int(body.dwell_seconds or 0),
    )
    db.add(rec)

    # if positive signal, nudge user profile toward the event embedding
    positive = bool(body.clicked or body.saved or body.rsvp)
    if positive:
        u = db.query(User).filter(User.id == body.user_id).first()
        e = db.query(Event).filter(Event.id == body.event_id).first()
        if u and e and e.embed is not None:
            ev = np.array(e.embed, dtype=np.float32)
            if u.embed is None:
                newv = _normalize(ev)
            else:
                uv = np.array(u.embed, dtype=np.float32)
                # EMA update; tweak alpha if you want faster adaptation
                alpha = 0.9
                newv = _normalize(alpha * uv + (1.0 - alpha) * ev)
            u.embed = newv.tolist()

    db.commit()
    return {}
