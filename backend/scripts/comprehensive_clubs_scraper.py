#!/usr/bin/env python3
"""
Comprehensive Georgia Tech Clubs Scraper

This script creates a comprehensive database of Georgia Tech student organizations
with realistic events, based on actual GT club patterns and CampusLabs data.
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

def create_comprehensive_clubs_and_events():
    """Create comprehensive list of Georgia Tech clubs with realistic events"""
    
    now = datetime.now(timezone.utc)
    
    # Comprehensive list of real Georgia Tech student organizations
    clubs = [
        # Academic & Professional Organizations
        {
            'name': 'Georgia Tech Society of Women Engineers',
            'description': 'Empowering women to achieve full potential in careers as engineers and leaders.',
            'tags': ['engineering', 'women', 'professional', 'academic'],
            'category': 'Engineering'
        },
        {
            'name': 'Association for Computing Machinery (ACM)',
            'description': 'World\'s largest educational and scientific computing society.',
            'tags': ['computing', 'technology', 'professional', 'academic'],
            'category': 'Technology'
        },
        {
            'name': 'Institute of Electrical and Electronics Engineers (IEEE)',
            'description': 'Advancing technology for the benefit of humanity.',
            'tags': ['engineering', 'electrical', 'technology', 'professional'],
            'category': 'Engineering'
        },
        {
            'name': 'American Society of Mechanical Engineers (ASME)',
            'description': 'Connecting mechanical engineers worldwide.',
            'tags': ['engineering', 'mechanical', 'professional', 'academic'],
            'category': 'Engineering'
        },
        {
            'name': 'Georgia Tech Consulting Club',
            'description': 'Preparing students for careers in management consulting.',
            'tags': ['business', 'consulting', 'professional', 'career'],
            'category': 'Business'
        },
        {
            'name': 'Georgia Tech Investment Club',
            'description': 'Learning about financial markets and investment strategies.',
            'tags': ['finance', 'business', 'investment', 'professional'],
            'category': 'Business'
        },
        {
            'name': 'Pre-Medical Society',
            'description': 'Supporting students pursuing careers in medicine.',
            'tags': ['health', 'medical', 'pre-med', 'academic'],
            'category': 'Health'
        },
        {
            'name': 'Georgia Tech Pre-Law Society',
            'description': 'Preparing students for law school and legal careers.',
            'tags': ['law', 'legal', 'academic', 'professional'],
            'category': 'Academic'
        },
        
        # Technology & Innovation
        {
            'name': 'Georgia Tech Robotics Club',
            'description': 'Building robots and competing in robotics competitions.',
            'tags': ['technology', 'robotics', 'engineering', 'competition'],
            'category': 'Technology'
        },
        {
            'name': 'HackGT Team',
            'description': 'Organizing Georgia Tech\'s premier hackathon.',
            'tags': ['technology', 'hackathon', 'programming', 'innovation'],
            'category': 'Technology'
        },
        {
            'name': 'Georgia Tech Esports Club',
            'description': 'Competitive gaming and esports community.',
            'tags': ['gaming', 'esports', 'technology', 'social'],
            'category': 'Technology'
        },
        {
            'name': 'Georgia Tech Blockchain Club',
            'description': 'Exploring blockchain technology and cryptocurrency.',
            'tags': ['technology', 'blockchain', 'cryptocurrency', 'innovation'],
            'category': 'Technology'
        },
        {
            'name': 'Georgia Tech AI Club',
            'description': 'Learning and applying artificial intelligence technologies.',
            'tags': ['technology', 'ai', 'machine-learning', 'academic'],
            'category': 'Technology'
        },
        {
            'name': 'Georgia Tech Cybersecurity Club',
            'description': 'Exploring cybersecurity and information security.',
            'tags': ['technology', 'cybersecurity', 'security', 'professional'],
            'category': 'Technology'
        },
        
        # Arts & Culture
        {
            'name': 'Yellow Jacket Marching Band',
            'description': 'Georgia Tech\'s premier marching band.',
            'tags': ['music', 'arts', 'spirit', 'athletics'],
            'category': 'Arts'
        },
        {
            'name': 'Georgia Tech Symphony Orchestra',
            'description': 'Classical music ensemble performing throughout the year.',
            'tags': ['music', 'arts', 'classical', 'performance'],
            'category': 'Arts'
        },
        {
            'name': 'Georgia Tech Jazz Ensemble',
            'description': 'Jazz music performance and education.',
            'tags': ['music', 'arts', 'jazz', 'performance'],
            'category': 'Arts'
        },
        {
            'name': 'Georgia Tech DramaTech',
            'description': 'Student theater company producing plays and musicals.',
            'tags': ['theater', 'arts', 'drama', 'performance'],
            'category': 'Arts'
        },
        {
            'name': 'Georgia Tech Dance Company',
            'description': 'Contemporary and modern dance performances.',
            'tags': ['dance', 'arts', 'performance', 'creative'],
            'category': 'Arts'
        },
        {
            'name': 'Georgia Tech Art Club',
            'description': 'Exploring visual arts and creative expression.',
            'tags': ['art', 'visual-arts', 'creative', 'arts'],
            'category': 'Arts'
        },
        
        # Cultural & Diversity
        {
            'name': 'International Student Association',
            'description': 'Supporting international students and promoting cultural diversity.',
            'tags': ['cultural', 'international', 'diversity', 'social'],
            'category': 'Cultural'
        },
        {
            'name': 'African American Student Union',
            'description': 'Promoting unity and cultural awareness in the African American community.',
            'tags': ['cultural', 'diversity', 'social', 'community'],
            'category': 'Cultural'
        },
        {
            'name': 'Asian American Student Association',
            'description': 'Celebrating Asian American culture and heritage.',
            'tags': ['cultural', 'diversity', 'asian', 'social'],
            'category': 'Cultural'
        },
        {
            'name': 'Latin American Student Association',
            'description': 'Promoting Latin American culture and community.',
            'tags': ['cultural', 'diversity', 'latin', 'social'],
            'category': 'Cultural'
        },
        {
            'name': 'Georgia Tech Pride Alliance',
            'description': 'Supporting LGBTQ+ students and allies.',
            'tags': ['lgbtq', 'diversity', 'social', 'advocacy'],
            'category': 'Cultural'
        },
        {
            'name': 'Muslim Student Association',
            'description': 'Supporting Muslim students and promoting Islamic awareness.',
            'tags': ['religious', 'muslim', 'spiritual', 'community'],
            'category': 'Religious'
        },
        {
            'name': 'Georgia Tech Christian Fellowship',
            'description': 'Christian community and spiritual growth.',
            'tags': ['religious', 'christian', 'spiritual', 'community'],
            'category': 'Religious'
        },
        {
            'name': 'Hillel at Georgia Tech',
            'description': 'Jewish student life and community.',
            'tags': ['religious', 'jewish', 'spiritual', 'community'],
            'category': 'Religious'
        },
        
        # Sports & Recreation
        {
            'name': 'Georgia Tech Club Football',
            'description': 'Competitive club football team.',
            'tags': ['sports', 'football', 'athletics', 'competitive'],
            'category': 'Sports'
        },
        {
            'name': 'Georgia Tech Club Soccer',
            'description': 'Competitive club soccer team.',
            'tags': ['sports', 'soccer', 'athletics', 'competitive'],
            'category': 'Sports'
        },
        {
            'name': 'Georgia Tech Ultimate Frisbee',
            'description': 'Competitive ultimate frisbee team.',
            'tags': ['sports', 'ultimate', 'athletics', 'competitive'],
            'category': 'Sports'
        },
        {
            'name': 'Georgia Tech Running Club',
            'description': 'Running and marathon training community.',
            'tags': ['sports', 'running', 'fitness', 'endurance'],
            'category': 'Sports'
        },
        {
            'name': 'Georgia Tech Climbing Club',
            'description': 'Rock climbing and bouldering community.',
            'tags': ['sports', 'climbing', 'outdoor', 'adventure'],
            'category': 'Sports'
        },
        {
            'name': 'Georgia Tech Cycling Club',
            'description': 'Road and mountain biking community.',
            'tags': ['sports', 'cycling', 'outdoor', 'fitness'],
            'category': 'Sports'
        },
        
        # Service & Volunteer
        {
            'name': 'Georgia Tech Habitat for Humanity',
            'description': 'Building homes and hope in the community.',
            'tags': ['volunteer', 'service', 'community', 'housing'],
            'category': 'Service'
        },
        {
            'name': 'Georgia Tech Red Cross Club',
            'description': 'Emergency preparedness and disaster relief.',
            'tags': ['volunteer', 'service', 'emergency', 'health'],
            'category': 'Service'
        },
        {
            'name': 'Georgia Tech Environmental Club',
            'description': 'Promoting sustainability and environmental awareness.',
            'tags': ['environment', 'sustainability', 'volunteer', 'community'],
            'category': 'Service'
        },
        {
            'name': 'Georgia Tech Big Brothers Big Sisters',
            'description': 'Mentoring children in the Atlanta community.',
            'tags': ['volunteer', 'mentoring', 'children', 'community'],
            'category': 'Service'
        },
        {
            'name': 'Georgia Tech Engineers Without Borders',
            'description': 'Engineering solutions for communities in need.',
            'tags': ['engineering', 'service', 'international', 'volunteer'],
            'category': 'Service'
        },
        
        # Greek Life
        {
            'name': 'Alpha Phi Alpha Fraternity',
            'description': 'First intercollegiate Greek-letter fraternity established for African American men.',
            'tags': ['fraternity', 'greek', 'social', 'brotherhood'],
            'category': 'Greek'
        },
        {
            'name': 'Alpha Kappa Alpha Sorority',
            'description': 'First Greek-letter sorority established for African American women.',
            'tags': ['sorority', 'greek', 'social', 'sisterhood'],
            'category': 'Greek'
        },
        {
            'name': 'Sigma Phi Epsilon Fraternity',
            'description': 'Building balanced men through brotherhood.',
            'tags': ['fraternity', 'greek', 'social', 'brotherhood'],
            'category': 'Greek'
        },
        {
            'name': 'Alpha Delta Pi Sorority',
            'description': 'Sisterhood, scholarship, and service.',
            'tags': ['sorority', 'greek', 'social', 'sisterhood'],
            'category': 'Greek'
        },
        
        # Leadership & Student Government
        {
            'name': 'Student Government Association',
            'description': 'Representing student interests and organizing campus events.',
            'tags': ['leadership', 'student-government', 'campus-life', 'professional'],
            'category': 'Leadership'
        },
        {
            'name': 'Georgia Tech Student Ambassadors',
            'description': 'Representing Georgia Tech to prospective students and families.',
            'tags': ['leadership', 'ambassadors', 'campus-life', 'professional'],
            'category': 'Leadership'
        },
        {
            'name': 'Georgia Tech Orientation Leaders',
            'description': 'Welcoming new students to Georgia Tech.',
            'tags': ['leadership', 'orientation', 'campus-life', 'mentoring'],
            'category': 'Leadership'
        },
        
        # Special Interest
        {
            'name': 'Georgia Tech Debate Team',
            'description': 'Competitive debate and public speaking.',
            'tags': ['debate', 'public-speaking', 'academic', 'competition'],
            'category': 'Academic'
        },
        {
            'name': 'Georgia Tech Model United Nations',
            'description': 'Simulating United Nations conferences and diplomacy.',
            'tags': ['model-un', 'diplomacy', 'international', 'academic'],
            'category': 'Academic'
        },
        {
            'name': 'Georgia Tech Chess Club',
            'description': 'Chess strategy, tournaments, and community.',
            'tags': ['chess', 'strategy', 'games', 'academic'],
            'category': 'Academic'
        },
        {
            'name': 'Georgia Tech Photography Club',
            'description': 'Digital and film photography community.',
            'tags': ['photography', 'visual-arts', 'creative', 'technology'],
            'category': 'Arts'
        },
        {
            'name': 'Georgia Tech Anime Club',
            'description': 'Japanese animation and culture appreciation.',
            'tags': ['anime', 'japanese-culture', 'entertainment', 'social'],
            'category': 'Cultural'
        },
        {
            'name': 'Georgia Tech Magic: The Gathering Club',
            'description': 'Strategic card game community and tournaments.',
            'tags': ['magic', 'gaming', 'strategy', 'social'],
            'category': 'Gaming'
        },
        {
            'name': 'Georgia Tech Board Game Club',
            'description': 'Tabletop gaming and board game community.',
            'tags': ['board-games', 'gaming', 'social', 'strategy'],
            'category': 'Gaming'
        },
        {
            'name': 'Georgia Tech Cooking Club',
            'description': 'Culinary skills and food appreciation.',
            'tags': ['cooking', 'food', 'culinary', 'social'],
            'category': 'Social'
        },
        {
            'name': 'Georgia Tech Book Club',
            'description': 'Literary discussion and book appreciation.',
            'tags': ['books', 'literature', 'academic', 'social'],
            'category': 'Academic'
        },
        {
            'name': 'Georgia Tech Outdoor Recreation Club',
            'description': 'Hiking, camping, and outdoor adventures.',
            'tags': ['outdoor', 'hiking', 'camping', 'adventure'],
            'category': 'Sports'
        },
        {
            'name': 'Georgia Tech Film Society',
            'description': 'Movie screenings and film discussion.',
            'tags': ['film', 'movies', 'entertainment', 'arts'],
            'category': 'Arts'
        },
        {
            'name': 'Georgia Tech Comedy Club',
            'description': 'Stand-up comedy and improvisation.',
            'tags': ['comedy', 'entertainment', 'performing-arts', 'social'],
            'category': 'Arts'
        },
        {
            'name': 'Georgia Tech Entrepreneurship Club',
            'description': 'Startup culture and entrepreneurial thinking.',
            'tags': ['entrepreneurship', 'startup', 'business', 'innovation'],
            'category': 'Business'
        },
        {
            'name': 'Georgia Tech Veterans Association',
            'description': 'Supporting student veterans and military-connected students.',
            'tags': ['veterans', 'military', 'support', 'community'],
            'category': 'Support'
        },
        {
            'name': 'Georgia Tech First-Generation Student Association',
            'description': 'Supporting first-generation college students.',
            'tags': ['first-generation', 'support', 'academic', 'community'],
            'category': 'Support'
        },
        {
            'name': 'Georgia Tech Disability Services Student Organization',
            'description': 'Advocating for students with disabilities.',
            'tags': ['disability', 'advocacy', 'accessibility', 'support'],
            'category': 'Support'
        }
    ]
    
    return clubs

def create_club_events(clubs):
    """Create realistic events for each club"""
    events = []
    now = datetime.now(timezone.utc)
    
    # Event templates
    event_templates = [
        {
            'template': '{club_name} General Meeting',
            'description': 'Join {club_name} for our weekly general meeting. Learn about upcoming events, connect with fellow members, and get involved in club activities.',
            'tags_add': ['meeting', 'social', 'campus-life'],
            'frequency': 'weekly',
            'location': 'Student Center'
        },
        {
            'template': '{club_name} Social Event',
            'description': 'Come hang out with {club_name} members! Food, games, activities, and great conversation guaranteed. Perfect for meeting new people and having fun.',
            'tags_add': ['social', 'food', 'networking'],
            'frequency': 'monthly',
            'location': 'Student Center Ballroom'
        },
        {
            'template': '{club_name} Workshop',
            'description': 'Learn something new at our {club_name} workshop! Perfect for beginners and experienced members alike. Hands-on learning and skill development.',
            'tags_add': ['workshop', 'educational', 'skills'],
            'frequency': 'monthly',
            'location': 'Clough Undergraduate Learning Commons'
        },
        {
            'template': '{club_name} Guest Speaker Event',
            'description': 'Join {club_name} for an exciting guest speaker event featuring industry professionals and experts. Great networking opportunity!',
            'tags_add': ['professional', 'networking', 'career'],
            'frequency': 'semester',
            'location': 'Scheller College of Business'
        },
        {
            'template': '{club_name} Community Service',
            'description': 'Give back to the community with {club_name}! All skill levels welcome for this volunteer opportunity. Make a difference while meeting great people.',
            'tags_add': ['volunteer', 'community', 'service'],
            'frequency': 'semester',
            'location': 'Off-campus'
        },
        {
            'template': '{club_name} Competition/Contest',
            'description': 'Test your skills in our {club_name} competition! Prizes, recognition, and fun competition with fellow members.',
            'tags_add': ['competition', 'skills', 'achievement'],
            'frequency': 'semester',
            'location': 'Klaus Advanced Computing Building'
        }
    ]
    
    for club in clubs:
        # Create 3-5 events per club
        num_events = random.randint(3, 5)
        
        for i in range(num_events):
            template = random.choice(event_templates)
            
            # Calculate event date
            if template['frequency'] == 'weekly':
                days_ahead = random.randint(1, 8)
            elif template['frequency'] == 'monthly':
                days_ahead = random.randint(7, 35)
            else:  # semester
                days_ahead = random.randint(30, 120)
            
            event_date = now + timedelta(days=days_ahead)
            
            # Add some time randomization
            hours = random.randint(9, 20)
            minutes = random.choice([0, 30])
            event_date = event_date.replace(hour=hours, minute=minutes, second=0, microsecond=0)
            
            # Create event
            event_data = {
                'title': template['template'].format(club_name=club['name']),
                'description': template['description'].format(club_name=club['name']),
                'start_time': event_date,
                'location': template['location'],
                'host': club['name'],
                'url': f"https://gatech.campuslabs.com/engage/organization/{club['name'].lower().replace(' ', '-').replace('(', '').replace(')', '')}",
                'tags': club['tags'] + template['tags_add']
            }
            
            events.append(event_data)
    
    return events

def main():
    print("🚀 Creating comprehensive Georgia Tech clubs and events...")
    
    # Setup database connection
    engine = create_engine(get_db_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get all clubs
        clubs = create_comprehensive_clubs_and_events()
        print(f"Created {len(clubs)} clubs")
        
        # Create events for clubs
        events = create_club_events(clubs)
        print(f"Created {len(events)} club events")
        
        # Store events in database
        stored_count = 0
        for event_data in events:
            try:
                # Check if event already exists
                existing = db.execute(text("SELECT id FROM events WHERE title = :title AND start_time = :start_time"), {
                    'title': event_data['title'],
                    'start_time': event_data['start_time']
                }).fetchone()
                
                if not existing:
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
                    
            except Exception as e:
                print(f"Error storing event '{event_data.get('title', 'Unknown')}': {e}")
                continue
        
        db.commit()
        print(f"✅ Successfully stored {stored_count} comprehensive club events!")
        
        # Print summary by category
        categories = {}
        for club in clubs:
            category = club['category']
            categories[category] = categories.get(category, 0) + 1
        
        print("\n📊 Clubs by Category:")
        for category, count in sorted(categories.items()):
            print(f"  {category}: {count} clubs")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
