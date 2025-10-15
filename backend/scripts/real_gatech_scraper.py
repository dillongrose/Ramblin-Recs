#!/usr/bin/env python3
"""
Real Georgia Tech Events Scraper

This script scrapes real events from official Georgia Tech sources including:
- Campus Calendar RSS feeds
- College-specific event pages
- Student organization events
- Athletics events
"""

import asyncio
import logging
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import uuid

import aiohttp
import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db import get_db_url
from app.models.event import Event

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealGatechScraper:
    def __init__(self):
        self.base_url = "https://calendar.gatech.edu"
        self.session = None
        self.db_session = None
        
        # Real Georgia Tech event sources
        self.rss_feeds = [
            "https://calendar.gatech.edu/rss-feeds",
            "https://calendar.gatech.edu/rss-feeds/all-events",
            "https://calendar.gatech.edu/rss-feeds/student-events",
            "https://calendar.gatech.edu/rss-feeds/academic-events",
        ]
        
        self.event_pages = [
            "https://calendar.gatech.edu/event-search",
            "https://arts.gatech.edu/events",
            "https://cos.gatech.edu/events",
            "https://research.gatech.edu/events",
            "https://career.gatech.edu/events",
        ]
        
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

    async def scrape_rss_feeds(self) -> List[Dict[str, Any]]:
        """Scrape events from Georgia Tech RSS feeds"""
        events = []
        
        for feed_url in self.rss_feeds:
            try:
                logger.info(f"Scraping RSS feed: {feed_url}")
                
                async with self.session.get(feed_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        for entry in feed.entries:
                            event_data = self._parse_rss_entry(entry)
                            if event_data and self._is_valid_event(event_data):
                                events.append(event_data)
                        
                        logger.info(f"Found {len(feed.entries)} entries in {feed_url}")
                    else:
                        logger.warning(f"Failed to fetch RSS feed {feed_url}: {response.status}")
                        
            except Exception as e:
                logger.error(f"Error scraping RSS feed {feed_url}: {e}")
                
        return events

    def _parse_rss_entry(self, entry) -> Optional[Dict[str, Any]]:
        """Parse a single RSS entry into event data"""
        event_data = {
            'title': entry.get('title', '').strip(),
            'description': entry.get('description', '').strip(),
            'start_time': None,
            'location': '',
            'url': entry.get('link', ''),
            'tags': [],
            'host': 'Georgia Tech'
        }
        
        # Clean up description (remove HTML tags)
        if event_data['description']:
            soup = BeautifulSoup(event_data['description'], 'html.parser')
            event_data['description'] = soup.get_text().strip()
        
        # Parse date from entry
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            event_data['start_time'] = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            event_data['start_time'] = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
        
        # Try to extract date from title or description
        if not event_data['start_time']:
            date_match = re.search(r'(\w{3,9}\s+\d{1,2},?\s+\d{4})', event_data['title'] + ' ' + event_data['description'])
            if date_match:
                try:
                    parsed_date = date_parser.parse(date_match.group(1))
                    if parsed_date.tzinfo is None:
                        parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                    event_data['start_time'] = parsed_date
                except:
                    pass
        
        # Extract location from description
        location_patterns = [
            r'Location:\s*([^\.\n]+)',
            r'Where:\s*([^\.\n]+)',
            r'Venue:\s*([^\.\n]+)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, event_data['description'], re.IGNORECASE)
            if match:
                event_data['location'] = match.group(1).strip()
                break
        
        # Generate tags based on content
        event_data['tags'] = self._generate_tags(event_data)
        
        return event_data

    async def scrape_event_pages(self) -> List[Dict[str, Any]]:
        """Scrape events from Georgia Tech event pages"""
        events = []
        
        for page_url in self.event_pages:
            try:
                logger.info(f"Scraping event page: {page_url}")
                
                async with self.session.get(page_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        page_events = self._parse_event_page(html, page_url)
                        events.extend(page_events)
                        logger.info(f"Found {len(page_events)} events from {page_url}")
                    else:
                        logger.warning(f"Failed to fetch page {page_url}: {response.status}")
                        
            except Exception as e:
                logger.error(f"Error scraping page {page_url}: {e}")
                
        return events

    def _parse_event_page(self, html: str, source_url: str) -> List[Dict[str, Any]]:
        """Parse events from an HTML page"""
        soup = BeautifulSoup(html, 'lxml')
        events = []
        
        # Look for common event container patterns
        event_selectors = [
            '.event-item',
            '.event',
            '.calendar-event',
            '.event-card',
            '[class*="event"]',
            '.event-list-item',
            '.event-summary',
            '.event-details'
        ]
        
        event_elements = []
        for selector in event_selectors:
            elements = soup.select(selector)
            if elements:
                event_elements.extend(elements)
                break
        
        # If no specific event containers found, look for general patterns
        if not event_elements:
            # Look for links that might be events
            event_elements = soup.find_all('a', href=re.compile(r'/event/|/events/'))
        
        for element in event_elements:
            try:
                event_data = self._extract_event_from_element(element, source_url)
                if event_data and self._is_valid_event(event_data):
                    events.append(event_data)
            except Exception as e:
                logger.warning(f"Error parsing event element: {e}")
                continue
                
        return events

    def _extract_event_from_element(self, element, source_url: str) -> Optional[Dict[str, Any]]:
        """Extract event data from a DOM element"""
        event_data = {
            'title': '',
            'description': '',
            'start_time': None,
            'location': '',
            'url': '',
            'tags': [],
            'host': 'Georgia Tech'
        }
        
        # Extract title
        title_selectors = ['h1', 'h2', 'h3', '.title', '.event-title', 'a']
        for selector in title_selectors:
            title_elem = element.find(selector) if hasattr(element, 'find') else None
            if title_elem and title_elem.get_text(strip=True):
                event_data['title'] = title_elem.get_text(strip=True)
                break
        
        # If no title found, try to get text content
        if not event_data['title'] and hasattr(element, 'get_text'):
            text = element.get_text(strip=True)
            if text and len(text) < 200:  # Reasonable title length
                event_data['title'] = text
        
        # Extract URL
        if hasattr(element, 'get') and element.get('href'):
            event_data['url'] = urljoin(source_url, element.get('href'))
        elif element.find('a'):
            link = element.find('a')
            if link and link.get('href'):
                event_data['url'] = urljoin(source_url, link.get('href'))
        
        # Extract description
        desc_selectors = ['.description', '.summary', '.content', 'p']
        for selector in desc_selectors:
            desc_elem = element.find(selector) if hasattr(element, 'find') else None
            if desc_elem:
                desc_text = desc_elem.get_text(strip=True)
                if desc_text and len(desc_text) > 10:
                    event_data['description'] = desc_text
                    break
        
        # Extract date/time information
        date_selectors = ['.date', '.time', '.datetime', '.event-date', '.event-time']
        for selector in date_selectors:
            date_elem = element.find(selector) if hasattr(element, 'find') else None
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                parsed_date = self._parse_date(date_text)
                if parsed_date:
                    event_data['start_time'] = parsed_date
                    break
        
        # Extract location
        location_selectors = ['.location', '.venue', '.place', '.where']
        for selector in location_selectors:
            loc_elem = element.find(selector) if hasattr(element, 'find') else None
            if loc_elem:
                event_data['location'] = loc_elem.get_text(strip=True)
                break
        
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
            'academic': ['lecture', 'seminar', 'workshop', 'conference', 'research', 'academic', 'class', 'symposium'],
            'social': ['social', 'party', 'mixer', 'networking', 'meetup', 'gathering', 'reception'],
            'sports': ['sports', 'athletics', 'game', 'match', 'tournament', 'fitness', 'gym', 'football', 'basketball'],
            'arts': ['art', 'music', 'theater', 'performance', 'exhibition', 'concert', 'dance', 'jazz'],
            'career': ['career', 'job', 'internship', 'recruiting', 'interview', 'resume', 'fair'],
            'technology': ['tech', 'coding', 'programming', 'hackathon', 'startup', 'innovation', 'ai', 'machine learning'],
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
            
        # Must be within reasonable timeframe (next 6 months)
        six_months = datetime.now(timezone.utc) + timedelta(days=180)
        if event_data['start_time'] > six_months:
            return False
            
        return True

    async def scrape_and_store_events(self) -> int:
        """Main method to scrape events and store them in the database"""
        logger.info("Starting real Georgia Tech events scraping...")
        
        # Scrape events from multiple sources
        all_events = []
        
        # Get events from RSS feeds
        rss_events = await self.scrape_rss_feeds()
        all_events.extend(rss_events)
        
        # Get events from event pages
        page_events = await self.scrape_event_pages()
        all_events.extend(page_events)
        
        logger.info(f"Total events scraped: {len(all_events)}")
        
        # Store events in database
        stored_count = 0
        for event_data in all_events:
            try:
                if await self._store_event(event_data):
                    stored_count += 1
            except Exception as e:
                logger.error(f"Error storing event '{event_data.get('title', 'Unknown')}': {e}")
                
        logger.info(f"Successfully stored {stored_count} real events")
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
    async with RealGatechScraper() as scraper:
        try:
            stored_count = await scraper.scrape_and_store_events()
            print(f"✅ Successfully scraped and stored {stored_count} real Georgia Tech events!")
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
