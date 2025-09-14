from fastapi import APIRouter
from .api import users, events, feedback, admin

router = APIRouter()
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(events.router, prefix="/events", tags=["events"])
router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])
