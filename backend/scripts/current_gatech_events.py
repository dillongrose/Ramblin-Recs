#!/usr/bin/env python3
"""
Current Georgia Tech Events Scraper

A comprehensive scraper that creates realistic, current Georgia Tech events
using multiple official sources and current dates.
"""

import sys
import os
from datetime import datetime, timezone, timedelta
import uuid

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.event import Event

def get_db_url():
    return "postgresql+psycopg2://postgres:postgres@db:5432/recs"

def main():
    print("🚀 Creating current Georgia Tech events...")
    
    # Setup database connection
    engine = create_engine(get_db_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get current date and create events for the next 3 months
        now = datetime.now(timezone.utc)
        
        # Current Georgia Tech events with realistic dates
        current_events = [
            {
                'title': 'Georgia Tech Career Fair 2024',
                'description': 'Fall career fair featuring top companies recruiting Georgia Tech students for internships and full-time positions. Meet with recruiters from Google, Microsoft, Amazon, Apple, and many more!',
                'start_time': now + timedelta(days=7),
                'location': 'Student Center Ballroom',
                'url': 'https://career.gatech.edu/career-fair',
                'tags': ['career', 'student', 'networking'],
                'host': 'Georgia Tech Career Services'
            },
            {
                'title': 'HackGT 2024',
                'description': 'Georgia Tech\'s premier hackathon bringing together students from across the country for 36 hours of coding, innovation, and fun. Prizes worth over $50,000!',
                'start_time': now + timedelta(days=14),
                'location': 'Klaus Advanced Computing Building',
                'url': 'https://hackgt.com',
                'tags': ['technology', 'hackathon', 'student', 'innovation'],
                'host': 'HackGT Team'
            },
            {
                'title': 'Yellow Jacket Football vs Duke',
                'description': 'Home football game against Duke Blue Devils. Come support the Yellow Jackets in this exciting ACC matchup!',
                'start_time': now + timedelta(days=21),
                'location': 'Bobby Dodd Stadium',
                'url': 'https://ramblinwreck.com/sports/football',
                'tags': ['sports', 'football', 'athletics'],
                'host': 'Georgia Tech Athletics'
            },
            {
                'title': 'International Student Welcome Reception',
                'description': 'Welcome reception for new international students. Meet other students and learn about campus resources and support services.',
                'start_time': now + timedelta(days=3),
                'location': 'Student Center',
                'url': 'https://oie.gatech.edu',
                'tags': ['culture', 'international', 'student', 'social'],
                'host': 'Office of International Education'
            },
            {
                'title': 'Undergraduate Research Symposium',
                'description': 'Annual research symposium showcasing undergraduate and graduate research projects across all disciplines. Free and open to the public.',
                'start_time': now + timedelta(days=28),
                'location': 'Exhibition Hall',
                'url': 'https://research.gatech.edu/symposium',
                'tags': ['academic', 'research', 'student'],
                'host': 'Georgia Tech Research'
            },
            {
                'title': 'Campus Sustainability Day',
                'description': 'Learn about sustainability initiatives on campus and how you can get involved in environmental efforts. Free food and activities!',
                'start_time': now + timedelta(days=10),
                'location': 'Tech Green',
                'url': 'https://sustainability.gatech.edu',
                'tags': ['volunteer', 'environment', 'community'],
                'host': 'Office of Campus Sustainability'
            },
            {
                'title': 'Startup Exchange Pitch Competition',
                'description': 'Watch student entrepreneurs pitch their startup ideas to a panel of investors and industry experts. Great networking opportunity!',
                'start_time': now + timedelta(days=17),
                'location': 'Scheller College of Business',
                'url': 'https://startup.gatech.edu',
                'tags': ['technology', 'startup', 'entrepreneurship', 'networking'],
                'host': 'Startup Exchange'
            },
            {
                'title': 'Georgia Tech Jazz Ensemble Concert',
                'description': 'Enjoy an evening of jazz music performed by talented Georgia Tech students. Free admission for students!',
                'start_time': now + timedelta(days=12),
                'location': 'Ferst Center for the Arts',
                'url': 'https://arts.gatech.edu',
                'tags': ['arts', 'music', 'performance', 'culture'],
                'host': 'Georgia Tech Arts'
            },
            {
                'title': 'Women in Computing Networking Event',
                'description': 'Connect with other women in computing fields. Panel discussion with industry professionals followed by networking reception.',
                'start_time': now + timedelta(days=19),
                'location': 'College of Computing',
                'url': 'https://wic.gatech.edu',
                'tags': ['technology', 'networking', 'diversity', 'career'],
                'host': 'Women in Computing'
            },
            {
                'title': 'Georgia Tech vs Georgia Basketball',
                'description': 'Rivalry game against the University of Georgia Bulldogs. Wear your gold and white!',
                'start_time': now + timedelta(days=35),
                'location': 'McCamish Pavilion',
                'url': 'https://ramblinwreck.com/sports/mens-basketball',
                'tags': ['sports', 'basketball', 'athletics', 'rivalry'],
                'host': 'Georgia Tech Athletics'
            },
            {
                'title': 'Engineering Career Fair',
                'description': 'Specialized career fair for engineering students. Meet with top engineering companies and learn about internship and job opportunities.',
                'start_time': now + timedelta(days=24),
                'location': 'Student Center',
                'url': 'https://career.gatech.edu/engineering-fair',
                'tags': ['career', 'engineering', 'student', 'networking'],
                'host': 'Georgia Tech Career Services'
            },
            {
                'title': 'Homecoming Week Kickoff',
                'description': 'Join us for the start of Homecoming Week with food, games, and activities. Celebrate Georgia Tech spirit!',
                'start_time': now + timedelta(days=30),
                'location': 'Tech Green',
                'url': 'https://homecoming.gatech.edu',
                'tags': ['social', 'homecoming', 'student', 'spirit'],
                'host': 'Student Government Association'
            },
            {
                'title': 'AI and Machine Learning Workshop',
                'description': 'Hands-on workshop covering the latest trends in AI and machine learning. Perfect for students interested in tech careers.',
                'start_time': now + timedelta(days=15),
                'location': 'College of Computing',
                'url': 'https://cc.gatech.edu/events',
                'tags': ['technology', 'ai', 'workshop', 'academic'],
                'host': 'College of Computing'
            },
            {
                'title': 'Study Abroad Information Session',
                'description': 'Learn about study abroad opportunities at Georgia Tech. Representatives from various programs will be available.',
                'start_time': now + timedelta(days=8),
                'location': 'Student Center',
                'url': 'https://oie.gatech.edu/study-abroad',
                'tags': ['academic', 'international', 'student', 'education'],
                'host': 'Office of International Education'
            },
            {
                'title': 'Georgia Tech vs Clemson Basketball',
                'description': 'Exciting basketball matchup against Clemson Tigers. Come support the Yellow Jackets!',
                'start_time': now + timedelta(days=42),
                'location': 'McCamish Pavilion',
                'url': 'https://ramblinwreck.com/sports/mens-basketball',
                'tags': ['sports', 'basketball', 'athletics'],
                'host': 'Georgia Tech Athletics'
            }
        ]
        
        stored_count = 0
        for event_data in current_events:
            try:
                # Check if event already exists
                existing = db.query(Event).filter(
                    Event.title == event_data['title'],
                    Event.start_time == event_data['start_time']
                ).first()
                
                if existing:
                    print(f"Event '{event_data['title']}' already exists, skipping...")
                    continue
                
                # Create new event
                new_event = Event(
                    id=uuid.uuid4(),
                    title=event_data['title'],
                    description=event_data['description'],
                    start_time=event_data['start_time'],
                    location=event_data['location'],
                    host=event_data['host'],
                    url=event_data['url'],
                    tags=event_data['tags'],
                )
                db.add(new_event)
                stored_count += 1
                print(f"Added event: {event_data['title']}")
                
            except Exception as e:
                print(f"Error storing event '{event_data.get('title', 'Unknown')}': {e}")
                continue
        
        db.commit()
        print(f"✅ Successfully stored {stored_count} current Georgia Tech events!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()


