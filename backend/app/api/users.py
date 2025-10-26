from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..models.user import User
from ..recs.embeddings import embed_text

router = APIRouter(prefix="/users", tags=["users"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CreateUser(BaseModel):
    email: str
    display_name: str | None = None

@router.post("")
def create_user(body: CreateUser, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="exists")
    u = User(email=body.email, display_name=body.display_name)
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"id": str(u.id), "email": u.email, "display_name": u.display_name}

class BootstrapIn(BaseModel):
    email: str
    display_name: str | None = None
    interests: list[str] = []

@router.post("/bootstrap")
def bootstrap_user(body: BootstrapIn, db: Session = Depends(get_db)):
    # upsert by email
    u = db.query(User).filter(User.email == body.email).first()
    if not u:
        u = User(email=body.email)
        db.add(u)
        db.flush()  # get id
    if body.display_name:
        u.display_name = body.display_name
    u.interests = body.interests
    # compute user embedding from interests
    txt = " ".join(body.interests) if body.interests else ""
    if txt:
        u.embed = embed_text(txt).tolist()
    db.commit()
    db.refresh(u)
    return {
        "id": str(u.id),
        "email": u.email,
        "display_name": u.display_name,
        "interests": u.interests or [],
    }


@router.get("/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "interests": user.interests or [],
    }
