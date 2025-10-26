"""
Event Ingestion API endpoints

Provides endpoints for ingesting events from external sources like Georgia Tech calendars.
"""

import asyncio
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session

# DB session dep
try:
    from ..db import get_db  # type: ignore
except Exception:  # pragma: no cover
    from ..database import get_db  # type: ignore

router = APIRouter(prefix="/ingestion", tags=["ingestion"])
logger = logging.getLogger(__name__)

async def _run_gatech_scraper():
    """Run the Georgia Tech RSS event scraper"""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
        
        from campuslabs_rss_scraper import CampusLabsRSSScraper
        
        # Run the RSS scraper
        async with CampusLabsRSSScraper() as scraper:
            stored_count = await scraper.scrape_and_store_events()
        
        return {
            "sample_events": 0,
            "scraped_events": stored_count,
            "total_events": stored_count
        }
            
    except Exception as e:
        logger.error(f"Error running Georgia Tech RSS scraper: {e}")
        raise

@router.post("/gatech-events")
async def ingest_gatech_events(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Trigger ingestion of Georgia Tech events.
    
    This endpoint will:
    1. Create sample Georgia Tech events for testing
    2. Attempt to scrape real events from Georgia Tech calendars
    3. Store all events in the database
    """
    try:
        # Run the scraper in the background
        result = await _run_gatech_scraper()
        
        return {
            "success": True,
            "message": "Georgia Tech events ingestion completed",
            "results": result
        }
        
    except Exception as e:
        logger.error(f"Failed to ingest Georgia Tech events: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to ingest events: {str(e)}"
        )

@router.get("/status")
async def get_ingestion_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get the current status of event ingestion"""
    try:
        # Count total events in database
        from sqlalchemy import text
        result = db.execute(text("SELECT COUNT(*) FROM events")).scalar()
        total_events = result or 0
        
        # Count events with Georgia Tech URLs
        gatech_result = db.execute(
            text("SELECT COUNT(*) FROM events WHERE url LIKE '%gatech.edu%' OR host LIKE '%Georgia Tech%'")
        ).scalar()
        gatech_events = gatech_result or 0
        
        # Count upcoming events
        upcoming_result = db.execute(
            text("SELECT COUNT(*) FROM events WHERE start_time > NOW()")
        ).scalar()
        upcoming_events = upcoming_result or 0
        
        return {
            "total_events": total_events,
            "gatech_events": gatech_events,
            "upcoming_events": upcoming_events,
            "status": "healthy"
        }
        
    except Exception as e:
        logger.error(f"Error getting ingestion status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )
