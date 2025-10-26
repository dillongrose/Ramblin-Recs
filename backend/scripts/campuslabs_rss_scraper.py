#!/usr/bin/env python3
"""
Georgia Tech CampusLabs RSS Events Scraper

This script scrapes real events from the CampusLabs RSS feed:
https://gatech.campuslabs.com/engage/events.rss
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import uuid
import re

import aiohttp
import feedparser
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db import get_db_url
from app.models.event import Event

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class CampusLabsRSSScraper:
    def __init__(self):
        self.session = None
        self.db_session = None
        self.rss_url = "https://gatech.campuslabs.com/engage/events.rss"
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        
        # Setup database connection
        engine = create_engine(get_db_url())
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db_session = SessionLocal()
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.db_session:
            self.db_session.close()

    async def scrape_rss_events(self) -> List[Dict[str, Any]]:
        """Scrape events from CampusLabs RSS feed"""
        events = []
        
        try:
            logger.info(f"Scraping RSS feed: {self.rss_url}")
            
            async with self.session.get(self.rss_url) as response:
                if response.status == 200:
                    content = await response.text()
                    feed = feedparser.parse(content)
                    
                    logger.info(f"Found {len(feed.entries)} events in RSS feed")
                    
                    for i, entry in enumerate(feed.entries):
                        event_data = self._parse_rss_entry(entry)
                        if event_data:
                            if self._is_valid_event(event_data):
                                events.append(event_data)
                            else:
                                logger.debug(f"Event {i+1} '{event_data.get('title', 'Unknown')}' filtered out (invalid)")
                        else:
                            logger.debug(f"Event {i+1} '{entry.get('title', 'Unknown')}' could not be parsed")
                    
                else:
                    logger.warning(f"Failed to fetch RSS feed: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error scraping RSS feed: {e}")
            
        return events

    def _parse_rss_entry(self, entry) -> Optional[Dict[str, Any]]:
        """Parse a single RSS entry into event data"""
        event_data = {
            'title': entry.get('title', '').strip(),
            'description': '',
            'start_time': None,
            'end_time': None,
            'location': '',
            'url': entry.get('link', ''),
            'tags': [],
            'host': '',
            'status': 'confirmed'
        }
        
        # Extract description
        if hasattr(entry, 'description'):
            event_data['description'] = entry.description.strip()
        elif hasattr(entry, 'summary'):
            event_data['description'] = entry.summary.strip()
        
        # Try to extract more detailed date/time from description first
        date_info = self._extract_datetime_from_description(event_data['description'])
        if date_info:
            event_data.update(date_info)
        else:
            # Fall back to published date if no specific event time found
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                event_data['start_time'] = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        
        # Extract location from description
        location = self._extract_location_from_description(event_data['description'])
        if location:
            event_data['location'] = location
        
        # Extract host organization
        host = self._extract_host_from_description(event_data['description'])
        if host:
            event_data['host'] = host
        
        # Generate tags based on content
        event_data['tags'] = self._generate_tags(event_data)
        
        # Check if event is cancelled
        if 'cancelled' in event_data['description'].lower() or 'cancelled' in event_data['title'].lower():
            event_data['status'] = 'cancelled'
        
        return event_data

    def _extract_datetime_from_description(self, description: str) -> Optional[Dict[str, Any]]:
        """Extract date and time information from event description"""
        if not description:
            return None
        
        # First try to extract from HTML datetime attributes
        datetime_match = re.search(r'datetime="([^"]+)"', description)
        if datetime_match:
            try:
                from dateutil import parser as date_parser
                dt_str = datetime_match.group(1)
                parsed_dt = date_parser.parse(dt_str)
                if parsed_dt.tzinfo is None:
                    parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                return {'start_time': parsed_dt}
            except Exception as e:
                logger.warning(f"Error parsing HTML datetime: {e}")
        
        # Look for patterns like "From Friday, October 24, 2025 6:00 PM to 8:00 PM EDT"
        datetime_patterns = [
            r'From\s+(\w+),\s+(\w+)\s+(\d+),\s+(\d+)\s+(\d+):(\d+)\s+(AM|PM)\s+to\s+(\d+):(\d+)\s+(AM|PM)\s+(\w+)',
            r'(\w+),\s+(\w+)\s+(\d+),\s+(\d+)\s+(\d+):(\d+)\s+(AM|PM)\s+to\s+(\d+):(\d+)\s+(AM|PM)',
            r'(\w+)\s+(\d+),\s+(\d+)\s+(\d+):(\d+)\s+(AM|PM)\s+to\s+(\d+):(\d+)\s+(AM|PM)'
        ]
        
        for pattern in datetime_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                try:
                    # Parse the date components
                    groups = match.groups()
                    if len(groups) >= 6:
                        # Extract start time
                        start_time = self._parse_datetime_from_groups(groups)
                        if start_time:
                            result = {'start_time': start_time}
                            
                            # Try to extract end time if available
                            if len(groups) >= 10:
                                end_time = self._parse_endtime_from_groups(groups)
                                if end_time:
                                    result['end_time'] = end_time
                            
                            return result
                except Exception as e:
                    logger.warning(f"Error parsing datetime: {e}")
                    continue
        
        return None

    def _parse_datetime_from_groups(self, groups) -> Optional[datetime]:
        """Parse datetime from regex groups"""
        try:
            # Handle different group patterns
            if len(groups) >= 6:
                # Pattern: From Friday, October 24, 2025 6:00 PM to 8:00 PM EDT
                month_name = groups[1]
                day = int(groups[2])
                year = int(groups[3])
                hour = int(groups[4])
                minute = int(groups[5])
                ampm = groups[6]
                
                # Convert to 24-hour format
                if ampm.upper() == 'PM' and hour != 12:
                    hour += 12
                elif ampm.upper() == 'AM' and hour == 12:
                    hour = 0
                
                # Convert month name to number
                month_map = {
                    'january': 1, 'february': 2, 'march': 3, 'april': 4,
                    'may': 5, 'june': 6, 'july': 7, 'august': 8,
                    'september': 9, 'october': 10, 'november': 11, 'december': 12
                }
                month = month_map.get(month_name.lower(), 1)
                
                return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
        except Exception as e:
            logger.warning(f"Error parsing datetime groups: {e}")
        
        return None

    def _parse_endtime_from_groups(self, groups) -> Optional[datetime]:
        """Parse end time from regex groups"""
        try:
            if len(groups) >= 10:
                # Extract end time components
                month_name = groups[1]
                day = int(groups[2])
                year = int(groups[3])
                end_hour = int(groups[7])
                end_minute = int(groups[8])
                end_ampm = groups[9]
                
                # Convert to 24-hour format
                if end_ampm.upper() == 'PM' and end_hour != 12:
                    end_hour += 12
                elif end_ampm.upper() == 'AM' and end_hour == 12:
                    end_hour = 0
                
                # Convert month name to number
                month_map = {
                    'january': 1, 'february': 2, 'march': 3, 'april': 4,
                    'may': 5, 'june': 6, 'july': 7, 'august': 8,
                    'september': 9, 'october': 10, 'november': 11, 'december': 12
                }
                month = month_map.get(month_name.lower(), 1)
                
                return datetime(year, month, day, end_hour, end_minute, tzinfo=timezone.utc)
        except Exception as e:
            logger.warning(f"Error parsing end time: {e}")
        
        return None

    def _extract_location_from_description(self, description: str) -> Optional[str]:
        """Extract location from event description"""
        if not description:
            return None
        
        # Look for "at [location]" pattern
        location_patterns = [
            r'at\s+([^.]+?)(?:\.|$)',
            r'Location:\s*([^.]+?)(?:\.|$)',
            r'Where:\s*([^.]+?)(?:\.|$)',
            r'Venue:\s*([^.]+?)(?:\.|$)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                if location and len(location) < 100:  # Reasonable location length
                    return location
        
        return None

    def _extract_host_from_description(self, description: str) -> Optional[str]:
        """Extract host organization from event description"""
        if not description:
            return None
        
        # Look for organization names in parentheses or email addresses
        host_patterns = [
            r'\(([^)]+)\)',
            r'([a-zA-Z\s]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'Hosted by\s+([^.]+?)(?:\.|$)',
            r'Presented by\s+([^.]+?)(?:\.|$)'
        ]
        
        for pattern in host_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                host = match.group(1).strip()
                if host and len(host) < 100:
                    return host
        
        return None

    def _generate_tags(self, event_data: Dict[str, Any]) -> List[str]:
        """Generate tags based on event content"""
        tags = set()
        
        text = f"{event_data.get('title', '')} {event_data.get('description', '')}".lower()
        
        # Category keywords
        category_keywords = {
            'academic': ['lecture', 'seminar', 'workshop', 'conference', 'research', 'academic', 'class', 'symposium', 'study'],
            'social': ['social', 'party', 'mixer', 'networking', 'meetup', 'gathering', 'reception', 'trivia', 'game'],
            'sports': ['sports', 'athletics', 'game', 'match', 'tournament', 'fitness', 'gym', 'football', 'basketball', 'volleyball'],
            'arts': ['art', 'music', 'theater', 'performance', 'exhibition', 'concert', 'dance', 'jazz', 'drama', 'improv'],
            'career': ['career', 'job', 'internship', 'recruiting', 'interview', 'resume', 'fair', 'networking'],
            'technology': ['tech', 'coding', 'programming', 'hackathon', 'startup', 'innovation', 'ai', 'machine learning'],
            'culture': ['culture', 'diversity', 'international', 'heritage', 'celebration', 'festival', 'cultural'],
            'volunteer': ['volunteer', 'service', 'community', 'outreach', 'charity', 'fundraiser', 'community service'],
            'student': ['student', 'club', 'organization', 'sga', 'fraternity', 'sorority', 'greek'],
            'religious': ['religious', 'christian', 'muslim', 'jewish', 'hindu', 'buddhist', 'spiritual', 'faith', 'worship', 'fellowship'],
            'wellness': ['wellness', 'health', 'mental health', 'support', 'awareness', 'cancer', 'breast cancer']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                tags.add(category)
        
        # Add specific tags based on content
        if 'cancelled' in text:
            tags.add('cancelled')
        if 'free' in text:
            tags.add('free')
        if 'food' in text:
            tags.add('food')
        if 'first year' in text or 'fywe' in text:
            tags.add('first-year')
        if 'grad' in text:
            tags.add('graduate-student')
        
        return list(tags)

    def _is_valid_event(self, event_data: Dict[str, Any]) -> bool:
        """Check if event data is valid and worth storing"""
        # Must have a title
        if not event_data.get('title') or len(event_data['title']) < 3:
            return False
            
        # Must have a start time
        if not event_data.get('start_time'):
            return False
            
        # For RSS feeds, be more lenient with dates since they might be published dates
        # Allow events from the past week to future events
        one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        one_year_future = datetime.now(timezone.utc) + timedelta(days=365)
        
        if event_data['start_time'] < one_week_ago:
            return False
            
        if event_data['start_time'] > one_year_future:
            return False
            
        return True

    async def scrape_and_store_events(self) -> int:
        """Main method to scrape events and store them in the database"""
        logger.info("Starting CampusLabs RSS events scraping...")
        
        # Scrape events from RSS feed
        events = await self.scrape_rss_events()
        
        logger.info(f"Total events scraped: {len(events)}")
        
        # Store events in database
        stored_count = 0
        for event_data in events:
            try:
                if await self._store_event(event_data):
                    stored_count += 1
            except Exception as e:
                logger.error(f"Error storing event '{event_data.get('title', 'Unknown')}': {e}")
                
        logger.info(f"Successfully stored {stored_count} RSS events")
        return stored_count

    async def _store_event(self, event_data: Dict[str, Any]) -> bool:
        """Store a single event in the database"""
        try:
            # Check if event already exists (by URL or title + start_time)
            existing = None
            if event_data.get('url'):
                existing = self.db_session.query(Event).filter(
                    Event.url == event_data['url']
                ).first()
            
            if not existing and event_data.get('title') and event_data.get('start_time'):
                existing = self.db_session.query(Event).filter(
                    Event.title == event_data['title'],
                    Event.start_time == event_data['start_time']
                ).first()
            
            if existing:
                # Update existing event
                existing.description = event_data.get('description') or existing.description
                existing.location = event_data.get('location') or existing.location
                existing.host = event_data.get('host') or existing.host
                existing.tags = event_data.get('tags') or existing.tags
                existing.url = event_data.get('url') or existing.url
                if event_data.get('end_time'):
                    existing.end_time = event_data['end_time']
                self.db_session.commit()
                return True
            else:
                # Create new event
                new_event = Event(
                    id=uuid.uuid4(),
                    title=event_data['title'],
                    description=event_data.get('description', ''),
                    start_time=event_data['start_time'],
                    end_time=event_data.get('end_time'),
                    location=event_data.get('location', ''),
                    host=event_data.get('host', ''),
                    url=event_data.get('url', ''),
                    tags=event_data.get('tags', []),
                )
                self.db_session.add(new_event)
                self.db_session.commit()
                return True
                
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Database error storing event: {e}")
            return False

async def main():
    """Main function to run the RSS scraper"""
    async with CampusLabsRSSScraper() as scraper:
        try:
            stored_count = await scraper.scrape_and_store_events()
            print(f"✅ Successfully scraped and stored {stored_count} real Georgia Tech events from RSS!")
        except Exception as e:
            logger.error(f"RSS scraping failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
