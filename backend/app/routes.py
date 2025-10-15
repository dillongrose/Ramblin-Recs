from fastapi import APIRouter
from .api import events, ingestion, admin

router = APIRouter()
router.include_router(events.router)
router.include_router(ingestion.router)
router.include_router(admin.router, prefix="/admin", tags=["admin"])
