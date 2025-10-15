#!/usr/bin/env python3
"""
Simple Georgia Tech Events Scraper

A lightweight scraper that focuses on specific, reliable Georgia Tech event sources.
This version is designed to be run regularly and is more conservative in its scraping.
"""

import asyncio
import logging
import re
import sys
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
import uuid

import aiohttp
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path to import app modules
sys.path.append('/Users/dillongrose/Documents/ramblin-recs/backend')
from app.db import get_db_url
from app.models.event import Event

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleGatechScraper:
    def __init__(self):
        self.base_url = "https://calendar.gatech.edu"
        self.session = None
        self.db_session = None
        
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

    async def scrape_calendar_events(self) -> List[Dict[str, Any]]:
        """Scrape events from the main Georgia Tech calendar"""
        events = []
        
        # Try to get events from the main calendar page
        try:
            url = f"{self.base_url}/event-search"
            logger.info(f"Scraping calendar events from: {url}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    events = self._parse_calendar_html(html)
                    logger.info(f"Found {len(events)} events from calendar")
                else:
                    logger.warning(f"Failed to fetch calendar: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error scraping calendar: {e}")
            
        return events

    def _parse_calendar_html(self, html: str) -> List[Dict[str, Any]]:
        """Parse events from the calendar HTML"""
        soup = BeautifulSoup(html, 'lxml')
        events = []
        
        # Look for event containers - these selectors are based on common calendar layouts
        event_containers = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'event|calendar', re.I))
        
        # If no specific event containers, look for links that might be events
        if not event_containers:
            event_containers = soup.find_all('a', href=re.compile(r'/event/|/events/'))
        
        for container in event_containers:
            try:
                event_data = self._extract_event_from_container(container)
                if event_data and self._is_valid_event(event_data):
                    events.append(event_data)
            except Exception as e:
                logger.warning(f"Error parsing event container: {e}")
                continue
                
        return events

    def _extract_event_from_container(self, container) -> Optional[Dict[str, Any]]:
        """Extract event data from a container element"""
        event_data = {
            'title': '',
            'description': '',
            'start_time': None,
            'location': '',
            'url': '',
            'tags': [],
            'host': 'Georgia Tech'
        }
        
        # Extract title - look for headings or links
        title_elem = container.find(['h1', 'h2', 'h3', 'h4']) or container.find('a')
        if title_elem:
            event_data['title'] = title_elem.get_text(strip=True)
            
            # If it's a link, get the URL
            if title_elem.name == 'a' and title_elem.get('href'):
                event_data['url'] = urljoin(self.base_url, title_elem.get('href'))
        
        # Extract description
        desc_elem = container.find(['p', 'div'], class_=re.compile(r'desc|summary|content', re.I))
        if desc_elem:
            event_data['description'] = desc_elem.get_text(strip=True)
        
        # Extract date/time
        date_elem = container.find(['span', 'div', 'time'], class_=re.compile(r'date|time', re.I))
        if date_elem:
            date_text = date_elem.get_text(strip=True)
            parsed_date = self._parse_date(date_text)
            if parsed_date:
                event_data['start_time'] = parsed_date
        
        # Extract location
        location_elem = container.find(['span', 'div'], class_=re.compile(r'location|venue|place', re.I))
        if location_elem:
            event_data['location'] = location_elem.get_text(strip=True)
        
        # Generate tags based on content
        event_data['tags'] = self._generate_tags(event_data)
        
        return event_data

    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse date string into datetime object"""
        if not date_text:
            return None
            
        try:
            # Clean up the date text
            date_text = re.sub(r'\s+', ' ', date_text.strip())
            
            # Try dateutil parser
            parsed = date_parser.parse(date_text, fuzzy=True)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
            
        except Exception as e:
            logger.warning(f"Could not parse date '{date_text}': {e}")
            return None

    def _generate_tags(self, event_data: Dict[str, Any]) -> List[str]:
        """Generate tags based on event content"""
        tags = set()
        
        # Extract tags from title and description
        text = f"{event_data.get('title', '')} {event_data.get('description', '')}".lower()
        
        # Common Georgia Tech event categories
        category_keywords = {
            'academic': ['lecture', 'seminar', 'workshop', 'conference', 'research', 'academic', 'class'],
            'social': ['social', 'party', 'mixer', 'networking', 'meetup', 'gathering'],
            'sports': ['sports', 'athletics', 'game', 'match', 'tournament', 'fitness', 'gym'],
            'arts': ['art', 'music', 'theater', 'performance', 'exhibition', 'concert', 'dance'],
            'career': ['career', 'job', 'internship', 'recruiting', 'interview', 'resume', 'fair'],
            'technology': ['tech', 'coding', 'programming', 'hackathon', 'startup', 'innovation', 'ai'],
            'culture': ['culture', 'diversity', 'international', 'heritage', 'celebration', 'festival'],
            'volunteer': ['volunteer', 'service', 'community', 'outreach', 'charity', 'fundraiser'],
            'student': ['student', 'club', 'organization', 'sga', 'fraternity', 'sorority', 'greek'],
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                tags.add(category)
        
        # Add location-based tags
        location = event_data.get('location', '').lower()
        if 'library' in location:
            tags.add('library')
        if 'student center' in location:
            tags.add('student-center')
        if 'stadium' in location or 'arena' in location:
            tags.add('sports-venue')
        if 'tech' in location.lower():
            tags.add('gatech-venue')
        
        return list(tags)

    def _is_valid_event(self, event_data: Dict[str, Any]) -> bool:
        """Check if event data is valid and worth storing"""
        # Must have a title
        if not event_data.get('title') or len(event_data['title']) < 3:
            return False
            
        # Must have a start time
        if not event_data.get('start_time'):
            return False
            
        # Must be in the future
        if event_data['start_time'] < datetime.now(timezone.utc):
            return False
            
        # Must be within reasonable timeframe (next 3 months)
        three_months = datetime.now(timezone.utc) + timedelta(days=90)
        if event_data['start_time'] > three_months:
            return False
            
        return True

    async def create_sample_events(self) -> int:
        """Create some sample Georgia Tech events for testing"""
        sample_events = [
            {
                'title': 'Georgia Tech Career Fair',
                'description': 'Annual career fair featuring top companies recruiting Georgia Tech students for internships and full-time positions.',
                'start_time': datetime.now(timezone.utc) + timedelta(days=7),
                'location': 'Student Center Ballroom',
                'url': 'https://career.gatech.edu/career-fair',
                'tags': ['career', 'student', 'networking'],
                'host': 'Georgia Tech Career Services'
            },
            {
                'title': 'HackGT 2024',
                'description': 'Georgia Tech\'s premier hackathon bringing together students from across the country for 36 hours of coding, innovation, and fun.',
                'start_time': datetime.now(timezone.utc) + timedelta(days=14),
                'location': 'Klaus Advanced Computing Building',
                'url': 'https://hackgt.com',
                'tags': ['technology', 'hackathon', 'student', 'innovation'],
                'host': 'HackGT Team'
            },
            {
                'title': 'Yellow Jacket Football vs Clemson',
                'description': 'Home football game against Clemson Tigers. Come support the Yellow Jackets!',
                'start_time': datetime.now(timezone.utc) + timedelta(days=21),
                'location': 'Bobby Dodd Stadium',
                'url': 'https://ramblinwreck.com/sports/football',
                'tags': ['sports', 'football', 'athletics'],
                'host': 'Georgia Tech Athletics'
            },
            {
                'title': 'International Student Welcome Reception',
                'description': 'Welcome reception for new international students. Meet other students and learn about campus resources.',
                'start_time': datetime.now(timezone.utc) + timedelta(days=3),
                'location': 'Student Center',
                'url': 'https://oie.gatech.edu',
                'tags': ['culture', 'international', 'student', 'social'],
                'host': 'Office of International Education'
            },
            {
                'title': 'Research Symposium',
                'description': 'Annual research symposium showcasing undergraduate and graduate research projects across all disciplines.',
                'start_time': datetime.now(timezone.utc) + timedelta(days=28),
                'location': 'Exhibition Hall',
                'url': 'https://research.gatech.edu/symposium',
                'tags': ['academic', 'research', 'student'],
                'host': 'Georgia Tech Research'
            },
            {
                'title': 'Campus Sustainability Day',
                'description': 'Learn about sustainability initiatives on campus and how you can get involved in environmental efforts.',
                'start_time': datetime.now(timezone.utc) + timedelta(days=10),
                'location': 'Tech Green',
                'url': 'https://sustainability.gatech.edu',
                'tags': ['volunteer', 'environment', 'community'],
                'host': 'Office of Campus Sustainability'
            }
        ]
        
        stored_count = 0
        for event_data in sample_events:
            try:
                if await self._store_event(event_data):
                    stored_count += 1
            except Exception as e:
                logger.error(f"Error storing sample event '{event_data.get('title', 'Unknown')}': {e}")
                
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
    """Main function to run the scraper"""
    async with SimpleGatechScraper() as scraper:
        try:
            # First, create some sample events for testing
            logger.info("Creating sample Georgia Tech events...")
            sample_count = await scraper.create_sample_events()
            logger.info(f"Created {sample_count} sample events")
            
            # Then try to scrape real events
            logger.info("Scraping real Georgia Tech events...")
            real_events = await scraper.scrape_calendar_events()
            
            # Store real events
            stored_count = 0
            for event_data in real_events:
                try:
                    if await scraper._store_event(event_data):
                        stored_count += 1
                except Exception as e:
                    logger.error(f"Error storing real event: {e}")
            
            total_events = sample_count + stored_count
            print(f"✅ Successfully processed {total_events} Georgia Tech events!")
            print(f"   - {sample_count} sample events")
            print(f"   - {stored_count} scraped events")
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

