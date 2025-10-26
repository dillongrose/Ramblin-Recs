from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

# DB session dep (supports either module name)
try:
    from ..db import get_db  # type: ignore
except Exception:  # pragma: no cover
    from ..database import get_db  # type: ignore

router = APIRouter(prefix="/user", tags=["user"])


class SaveEventRequest(BaseModel):
    user_id: str
    event_id: str


def _row_to_event_dict(r) -> Dict[str, Any]:
    """Convert a database row to event dictionary."""
    return {
        "id": str(r["id"]),
        "title": r.get("title"),
        "description": r.get("description"),
        "start_time": r.get("start_time").isoformat() if r.get("start_time") else None,
        "end_time": r.get("end_time").isoformat() if r.get("end_time") else None,
        "timezone": r.get("timezone"),
        "location": r.get("location"),
        "host": r.get("host"),
        "price_cents": r.get("price_cents"),
        "url": r.get("url"),
        "tags": r.get("tags") or [],
        "raw_s3_uri": r.get("raw_s3_uri"),
        "popularity": float(r.get("popularity") or 0),
        "created_at": r.get("created_at").isoformat() if r.get("created_at") else None,
    }


@router.get("/saved-events")
def get_saved_events(
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Get all saved events for a user, sorted chronologically."""
    # Get saved events for the user
    rows = db.execute(
        text("""
            SELECT e.* FROM events e
            INNER JOIN user_saved_events use ON e.id = use.event_id
            WHERE use.user_id = :user_id
            ORDER BY e.start_time ASC
        """),
        {"user_id": user_id}
    ).fetchall()
    
    return [_row_to_event_dict(r) for r in rows]


@router.post("/save-event")
def save_event(
    request: SaveEventRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Save an event for a user."""
    # Check if event exists
    event_exists = db.execute(
        text("SELECT id FROM events WHERE id = :event_id"),
        {"event_id": request.event_id}
    ).fetchone()
    
    if not event_exists:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if already saved
    already_saved = db.execute(
        text("""
            SELECT id FROM user_saved_events 
            WHERE user_id = :user_id AND event_id = :event_id
        """),
        {"user_id": request.user_id, "event_id": request.event_id}
    ).fetchone()
    
    if already_saved:
        return {"message": "Event already saved", "saved": True}
    
    # Save the event
    db.execute(
        text("""
            INSERT INTO user_saved_events (user_id, event_id, saved_at)
            VALUES (:user_id, :event_id, NOW())
        """),
        {"user_id": request.user_id, "event_id": request.event_id}
    )
    db.commit()
    
    return {"message": "Event saved successfully", "saved": True}


@router.delete("/unsave-event")
def unsave_event(
    user_id: str,
    event_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Remove a saved event for a user."""
    result = db.execute(
        text("""
            DELETE FROM user_saved_events 
            WHERE user_id = :user_id AND event_id = :event_id
        """),
        {"user_id": user_id, "event_id": event_id}
    )
    db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Saved event not found")
    
    return {"message": "Event removed from saved list", "saved": False}
