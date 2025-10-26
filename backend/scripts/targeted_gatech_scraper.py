#!/usr/bin/env python3
"""
Targeted Georgia Tech Events Scraper

This script scrapes real events from specific working Georgia Tech sources:
- Georgia Tech Athletics (sports events)
- Georgia Tech Arts (performances)
- College of Computing events
- Career Services events
"""

import asyncio
import logging
import os
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
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db import get_db_url
from app.models.event import Event

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TargetedGatechScraper:
    def __init__(self):
        self.session = None
        self.db_session = None
        
        # Working Georgia Tech event sources
        self.target_urls = [
            {
                'url': 'https://ramblinwreck.com/sports/football/schedule/',
                'type': 'sports',
                'sport': 'football'
            },
            {
                'url': 'https://ramblinwreck.com/sports/mens-basketball/schedule/',
                'type': 'sports',
                'sport': 'basketball'
            },
            {
                'url': 'https://arts.gatech.edu/events',
                'type': 'arts'
            },
            {
                'url': 'https://www.cc.gatech.edu/events',
                'type': 'academic',
                'department': 'computing'
            },
            {
                'url': 'https://career.gatech.edu/events',
                'type': 'career'
            }
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

    async def scrape_all_sources(self) -> List[Dict[str, Any]]:
        """Scrape events from all targeted sources"""
        all_events = []
        
        for source in self.target_urls:
            try:
                logger.info(f"Scraping {source['type']} events from: {source['url']}")
                
                async with self.session.get(source['url']) as response:
                    if response.status == 200:
                        html = await response.text()
                        events = self._parse_source(html, source)
                        all_events.extend(events)
                        logger.info(f"Found {len(events)} events from {source['url']}")
                    else:
                        logger.warning(f"Failed to fetch {source['url']}: {response.status}")
                        
            except Exception as e:
                logger.error(f"Error scraping {source['url']}: {e}")
                
        return all_events

    def _parse_source(self, html: str, source: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse events from a specific source based on type"""
        soup = BeautifulSoup(html, 'lxml')
        events = []
        
        if source['type'] == 'sports':
            events = self._parse_sports_events(soup, source)
        elif source['type'] == 'arts':
            events = self._parse_arts_events(soup, source)
        elif source['type'] == 'academic':
            events = self._parse_academic_events(soup, source)
        elif source['type'] == 'career':
            events = self._parse_career_events(soup, source)
            
        return events

    def _parse_sports_events(self, soup: BeautifulSoup, source: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse sports events from athletics pages"""
        events = []
        
        # Look for game/event rows in schedules
        game_rows = soup.find_all(['tr', 'div'], class_=re.compile(r'game|event|match', re.I))
        
        for row in game_rows:
            try:
                event_data = {
                    'title': '',
                    'description': '',
                    'start_time': None,
                    'location': '',
                    'url': source['url'],
                    'tags': ['sports', source.get('sport', 'athletics')],
                    'host': 'Georgia Tech Athletics'
                }
                
                # Extract opponent/team name
                opponent_elem = row.find(['span', 'div', 'td'], class_=re.compile(r'opponent|team|school', re.I))
                if opponent_elem:
                    opponent = opponent_elem.get_text(strip=True)
                    event_data['title'] = f"Georgia Tech vs {opponent}"
                
                # Extract date/time
                date_elem = row.find(['span', 'div', 'td'], class_=re.compile(r'date|time', re.I))
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    parsed_date = self._parse_date(date_text)
                    if parsed_date:
                        event_data['start_time'] = parsed_date
                
                # Extract location
                location_elem = row.find(['span', 'div', 'td'], class_=re.compile(r'location|venue', re.I))
                if location_elem:
                    event_data['location'] = location_elem.get_text(strip=True)
                
                # Set default location if none found
                if not event_data['location']:
                    event_data['location'] = 'Bobby Dodd Stadium' if source.get('sport') == 'football' else 'McCamish Pavilion'
                
                if event_data['title'] and event_data['start_time']:
                    events.append(event_data)
                    
            except Exception as e:
                logger.warning(f"Error parsing sports event: {e}")
                continue
                
        return events

    def _parse_arts_events(self, soup: BeautifulSoup, source: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse arts events"""
        events = []
        
        # Look for event containers
        event_containers = soup.find_all(['div', 'article'], class_=re.compile(r'event|performance', re.I))
        
        for container in event_containers:
            try:
                event_data = {
                    'title': '',
                    'description': '',
                    'start_time': None,
                    'location': 'Ferst Center for the Arts',
                    'url': source['url'],
                    'tags': ['arts', 'performance', 'culture'],
                    'host': 'Georgia Tech Arts'
                }
                
                # Extract title
                title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
                if title_elem:
                    event_data['title'] = title_elem.get_text(strip=True)
                
                # Extract description
                desc_elem = container.find('p')
                if desc_elem:
                    event_data['description'] = desc_elem.get_text(strip=True)
                
                # Extract date
                date_elem = container.find(['span', 'div'], class_=re.compile(r'date|time', re.I))
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    parsed_date = self._parse_date(date_text)
                    if parsed_date:
                        event_data['start_time'] = parsed_date
                
                if event_data['title'] and event_data['start_time']:
                    events.append(event_data)
                    
            except Exception as e:
                logger.warning(f"Error parsing arts event: {e}")
                continue
                
        return events

    def _parse_academic_events(self, soup: BeautifulSoup, source: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse academic events"""
        events = []
        
        # Look for event containers
        event_containers = soup.find_all(['div', 'article'], class_=re.compile(r'event|seminar|workshop', re.I))
        
        for container in event_containers:
            try:
                event_data = {
                    'title': '',
                    'description': '',
                    'start_time': None,
                    'location': 'College of Computing',
                    'url': source['url'],
                    'tags': ['academic', 'technology', 'computing'],
                    'host': 'College of Computing'
                }
                
                # Extract title
                title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
                if title_elem:
                    event_data['title'] = title_elem.get_text(strip=True)
                
                # Extract description
                desc_elem = container.find('p')
                if desc_elem:
                    event_data['description'] = desc_elem.get_text(strip=True)
                
                # Extract date
                date_elem = container.find(['span', 'div'], class_=re.compile(r'date|time', re.I))
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    parsed_date = self._parse_date(date_text)
                    if parsed_date:
                        event_data['start_time'] = parsed_date
                
                if event_data['title'] and event_data['start_time']:
                    events.append(event_data)
                    
            except Exception as e:
                logger.warning(f"Error parsing academic event: {e}")
                continue
                
        return events

    def _parse_career_events(self, soup: BeautifulSoup, source: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse career events"""
        events = []
        
        # Look for event containers
        event_containers = soup.find_all(['div', 'article'], class_=re.compile(r'event|career|fair', re.I))
        
        for container in event_containers:
            try:
                event_data = {
                    'title': '',
                    'description': '',
                    'start_time': None,
                    'location': 'Student Center',
                    'url': source['url'],
                    'tags': ['career', 'networking', 'student'],
                    'host': 'Georgia Tech Career Services'
                }
                
                # Extract title
                title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
                if title_elem:
                    event_data['title'] = title_elem.get_text(strip=True)
                
                # Extract description
                desc_elem = container.find('p')
                if desc_elem:
                    event_data['description'] = desc_elem.get_text(strip=True)
                
                # Extract date
                date_elem = container.find(['span', 'div'], class_=re.compile(r'date|time', re.I))
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    parsed_date = self._parse_date(date_text)
                    if parsed_date:
                        event_data['start_time'] = parsed_date
                
                if event_data['title'] and event_data['start_time']:
                    events.append(event_data)
                    
            except Exception as e:
                logger.warning(f"Error parsing career event: {e}")
                continue
                
        return events

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
            
            # Make sure it's in the future
            if parsed < datetime.now(timezone.utc):
                return None
                
            return parsed
            
        except Exception as e:
            logger.warning(f"Could not parse date '{date_text}': {e}")
            return None

    async def scrape_and_store_events(self) -> int:
        """Main method to scrape events and store them in the database"""
        logger.info("Starting targeted Georgia Tech events scraping...")
        
        # Scrape events from all sources
        all_events = await self.scrape_all_sources()
        
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
    async with TargetedGatechScraper() as scraper:
        try:
            stored_count = await scraper.scrape_and_store_events()
            print(f"✅ Successfully scraped and stored {stored_count} real Georgia Tech events!")
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

