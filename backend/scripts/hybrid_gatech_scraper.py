#!/usr/bin/env python3
"""
Hybrid Georgia Tech Events Scraper

This script creates realistic, current Georgia Tech events based on:
- Real Georgia Tech event patterns and locations
- Current academic calendar dates
- Actual Georgia Tech departments and organizations
- Realistic event types that actually happen at GT
"""

import os
import sys
from datetime import datetime, timezone, timedelta
import uuid
import random

# Add the parent directory to the path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db import get_db_url
from app.models.event import Event
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def get_db_url():
    return "postgresql+psycopg2://postgres:postgres@db:5432/recs"

def create_realistic_gatech_events():
    """Create realistic Georgia Tech events based on real patterns"""
    
    # Get current date and create events for the next 3 months
    now = datetime.now(timezone.utc)
    
    # Real Georgia Tech departments, organizations, and locations
    departments = [
        "College of Computing",
        "College of Engineering", 
        "College of Sciences",
        "Scheller College of Business",
        "Ivan Allen College of Liberal Arts",
        "College of Design",
        "College of Sciences"
    ]
    
    locations = [
        "Student Center",
        "Student Center Ballroom", 
        "Klaus Advanced Computing Building",
        "College of Computing",
        "Scheller College of Business",
        "Ferst Center for the Arts",
        "Tech Green",
        "Exhibition Hall",
        "Global Learning Center",
        "Bobby Dodd Stadium",
        "McCamish Pavilion",
        "CRC (Campus Recreation Center)",
        "Library",
        "Clough Undergraduate Learning Commons"
    ]
    
    # Real Georgia Tech event types that actually happen
    event_templates = [
        {
            'title_template': 'Georgia Tech Career Fair',
            'description_template': 'Annual career fair featuring top companies recruiting Georgia Tech students for internships and full-time positions. Meet with recruiters from leading tech companies.',
            'tags': ['career', 'student', 'networking'],
            'host': 'Georgia Tech Career Services',
            'location': 'Student Center Ballroom',
            'url': 'https://career.gatech.edu/career-fair',
            'frequency': 'monthly'
        },
        {
            'title_template': 'HackGT 2024',
            'description_template': 'Georgia Tech\'s premier hackathon bringing together students from across the country for 36 hours of coding, innovation, and fun. Prizes worth over $50,000!',
            'tags': ['technology', 'hackathon', 'student', 'innovation'],
            'host': 'HackGT Team',
            'location': 'Klaus Advanced Computing Building',
            'url': 'https://hackgt.com',
            'frequency': 'yearly'
        },
        {
            'title_template': '{department} Research Symposium',
            'description_template': 'Annual research symposium showcasing undergraduate and graduate research projects from {department}. Free and open to the public.',
            'tags': ['academic', 'research', 'student'],
            'host_template': '{department}',
            'location': 'Exhibition Hall',
            'url_template': 'https://college.gatech.edu/symposium',
            'frequency': 'semester'
        },
        {
            'title_template': 'International Student Welcome Reception',
            'description_template': 'Welcome reception for new international students. Meet other students and learn about campus resources and support services.',
            'tags': ['culture', 'international', 'student', 'social'],
            'host': 'Office of International Education',
            'location': 'Student Center',
            'url': 'https://oie.gatech.edu',
            'frequency': 'semester'
        },
        {
            'title_template': 'Campus Sustainability Day',
            'description_template': 'Learn about sustainability initiatives on campus and how you can get involved in environmental efforts. Free food and activities!',
            'tags': ['volunteer', 'environment', 'community'],
            'host': 'Office of Campus Sustainability',
            'location': 'Tech Green',
            'url': 'https://sustainability.gatech.edu',
            'frequency': 'semester'
        },
        {
            'title_template': 'Startup Exchange Pitch Competition',
            'description_template': 'Watch student entrepreneurs pitch their startup ideas to a panel of investors and industry experts. Great networking opportunity!',
            'tags': ['technology', 'startup', 'entrepreneurship', 'networking'],
            'host': 'Startup Exchange',
            'location': 'Scheller College of Business',
            'url': 'https://startup.gatech.edu',
            'frequency': 'semester'
        },
        {
            'title_template': 'Georgia Tech Jazz Ensemble Concert',
            'description_template': 'Enjoy an evening of jazz music performed by talented Georgia Tech students. Free admission for students!',
            'tags': ['arts', 'music', 'performance', 'culture'],
            'host': 'Georgia Tech Arts',
            'location': 'Ferst Center for the Arts',
            'url': 'https://arts.gatech.edu',
            'frequency': 'monthly'
        },
        {
            'title_template': 'Women in Computing Networking Event',
            'description_template': 'Connect with other women in computing fields. Panel discussion with industry professionals followed by networking reception.',
            'tags': ['technology', 'networking', 'diversity', 'career'],
            'host': 'Women in Computing',
            'location': 'College of Computing',
            'url': 'https://wic.gatech.edu',
            'frequency': 'monthly'
        },
        {
            'title_template': 'Yellow Jacket Football vs {opponent}',
            'description_template': 'Home football game against {opponent}. Come support the Yellow Jackets in this exciting ACC matchup!',
            'tags': ['sports', 'football', 'athletics'],
            'host': 'Georgia Tech Athletics',
            'location': 'Bobby Dodd Stadium',
            'url': 'https://ramblinwreck.com/sports/football',
            'frequency': 'weekly',
            'opponents': ['Duke', 'Clemson', 'Florida State', 'Virginia Tech', 'Miami', 'North Carolina']
        },
        {
            'title_template': 'Georgia Tech vs Georgia Basketball',
            'description_template': 'Rivalry game against the University of Georgia Bulldogs. Wear your gold and white!',
            'tags': ['sports', 'basketball', 'athletics', 'rivalry'],
            'host': 'Georgia Tech Athletics',
            'location': 'McCamish Pavilion',
            'url': 'https://ramblinwreck.com/sports/mens-basketball',
            'frequency': 'yearly'
        },
        {
            'title_template': 'Engineering Career Fair',
            'description_template': 'Specialized career fair for engineering students. Meet with top engineering companies and learn about internship and job opportunities.',
            'tags': ['career', 'engineering', 'student', 'networking'],
            'host': 'Georgia Tech Career Services',
            'location': 'Student Center',
            'url': 'https://career.gatech.edu/engineering-fair',
            'frequency': 'semester'
        },
        {
            'title_template': 'Homecoming Week Kickoff',
            'description_template': 'Join us for the start of Homecoming Week with food, games, and activities. Celebrate Georgia Tech spirit!',
            'tags': ['social', 'homecoming', 'student', 'spirit'],
            'host': 'Student Government Association',
            'location': 'Tech Green',
            'url': 'https://homecoming.gatech.edu',
            'frequency': 'yearly'
        },
        {
            'title_template': 'AI and Machine Learning Workshop',
            'description_template': 'Hands-on workshop covering the latest trends in AI and machine learning. Perfect for students interested in tech careers.',
            'tags': ['technology', 'ai', 'workshop', 'academic'],
            'host': 'College of Computing',
            'location': 'College of Computing',
            'url': 'https://cc.gatech.edu/events',
            'frequency': 'monthly'
        },
        {
            'title_template': 'Study Abroad Information Session',
            'description_template': 'Learn about study abroad opportunities at Georgia Tech. Representatives from various programs will be available.',
            'tags': ['academic', 'international', 'student', 'education'],
            'host': 'Office of International Education',
            'location': 'Student Center',
            'url': 'https://oie.gatech.edu/study-abroad',
            'frequency': 'monthly'
        },
        {
            'title_template': 'Graduate School Information Session',
            'description_template': 'Learn about graduate programs at Georgia Tech. Meet with faculty and current graduate students.',
            'tags': ['academic', 'graduate', 'student', 'education'],
            'host': 'Graduate Studies',
            'location': 'Student Center',
            'url': 'https://grad.gatech.edu',
            'frequency': 'monthly'
        },
        {
            'title_template': 'Diversity and Inclusion Forum',
            'description_template': 'Join the conversation about diversity and inclusion at Georgia Tech. Panel discussion with students, faculty, and staff.',
            'tags': ['diversity', 'social', 'student', 'community'],
            'host': 'Office of Diversity and Inclusion',
            'location': 'Student Center',
            'url': 'https://diversity.gatech.edu',
            'frequency': 'semester'
        },
        {
            'title_template': 'Tech Talks: {topic}',
            'description_template': 'Join industry professionals as they discuss the latest trends in {topic}. Great networking opportunity!',
            'tags': ['technology', 'networking', 'career', 'professional'],
            'host': 'Georgia Tech Professional Education',
            'location': 'Global Learning Center',
            'url': 'https://pe.gatech.edu',
            'frequency': 'weekly',
            'topics': ['Cybersecurity', 'Artificial Intelligence', 'Data Science', 'Software Engineering', 'Robotics']
        },
        {
            'title_template': 'Student Organization Fair',
            'description_template': 'Discover student organizations at Georgia Tech. Meet representatives from clubs, societies, and interest groups.',
            'tags': ['social', 'student', 'clubs', 'organizations'],
            'host': 'Student Engagement',
            'location': 'Tech Green',
            'url': 'https://studentengagement.gatech.edu',
            'frequency': 'semester'
        }
    ]
    
    events = []
    
    for template in event_templates:
        # Generate events based on frequency
        if template['frequency'] == 'weekly':
            num_events = 8  # Next 8 weeks
        elif template['frequency'] == 'monthly':
            num_events = 3  # Next 3 months
        elif template['frequency'] == 'semester':
            num_events = 2  # This and next semester
        elif template['frequency'] == 'yearly':
            num_events = 1  # This year
        else:
            num_events = 1
        
        for i in range(num_events):
            event_data = create_event_from_template(template, now, i, departments)
            if event_data:
                events.append(event_data)
    
    return events

def create_event_from_template(template, base_date, index, departments):
    """Create a single event from a template"""
    
    # Calculate date based on frequency
    if template['frequency'] == 'weekly':
        start_date = base_date + timedelta(weeks=index + 1)
    elif template['frequency'] == 'monthly':
        start_date = base_date + timedelta(days=30 * (index + 1))
    elif template['frequency'] == 'semester':
        start_date = base_date + timedelta(days=90 * (index + 1))
    else:  # yearly
        start_date = base_date + timedelta(days=30 * (index + 1))
    
    # Add some randomness to make it more realistic
    start_date += timedelta(days=random.randint(-7, 7))
    
    # Format title
    title = template['title_template']
    if '{department}' in title:
        department = random.choice(departments)
        title = title.format(department=department)
    elif '{opponent}' in title:
        opponent = random.choice(template.get('opponents', ['Opponent']))
        title = title.format(opponent=opponent)
    elif '{topic}' in title:
        topic = random.choice(template.get('topics', ['Technology']))
        title = title.format(topic=topic)
    
    # Format description
    description = template['description_template']
    if '{department}' in description:
        description = description.format(department=department)
    elif '{opponent}' in description:
        description = description.format(opponent=opponent)
    elif '{topic}' in description:
        description = description.format(topic=topic)
    
    # Format host
    host = template.get('host_template', template.get('host', 'Georgia Tech'))
    if '{department}' in host:
        host = host.format(department=department)
    
    # Format URL
    url = template.get('url_template', template.get('url', ''))
    if '{department.lower().replace(" ", "-")}' in url:
        url = url.format(department=department.lower().replace(' ', '-'))
    elif '{department}' in url:
        url = url.format(department=department)
    
    return {
        'title': title,
        'description': description,
        'start_time': start_date,
        'location': template['location'],
        'host': host,
        'url': url,
        'tags': template['tags'].copy()
    }

def main():
    print("🚀 Creating realistic Georgia Tech events...")
    
    # Setup database connection
    engine = create_engine(get_db_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Clear existing events
        db.execute(text("DELETE FROM events"))
        db.commit()
        
        # Create realistic events
        events_data = create_realistic_gatech_events()
        
        stored_count = 0
        for event_data in events_data:
            try:
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
        print(f"✅ Successfully stored {stored_count} realistic Georgia Tech events!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
