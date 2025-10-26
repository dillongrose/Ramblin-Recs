from fastapi import APIRouter
from .api import events, ingestion, admin, users, feedback

router = APIRouter()
router.include_router(events.router)
router.include_router(ingestion.router)
router.include_router(admin.router, prefix="/admin", tags=["admin"])
router.include_router(users.router)
router.include_router(feedback.router)
