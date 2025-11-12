#!/usr/bin/env python3
"""
Script to load hotels from CSV files into the database.
Run this after setting up the database to populate it with hotel data.
"""

import os
import sys
import csv
import re
from datetime import datetime, timezone

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.models import db, Hotel

# Constants
CSV_COLUMN_HOTEL_NAME = 'Hotel Name'
CSV_COLUMN_LOCATION = 'Location'
CSV_COLUMN_RATING = 'Rating'
CSV_COLUMN_REVIEWS = 'Reviews'
CSV_COLUMN_PRICE = 'Price'
CSV_COLUMN_URL = 'URL'

def _extract_rating_from_text(rating_text):
    """Extract numeric rating from text."""
    if not rating_text:
        return None
    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
    if rating_match:
        return float(rating_match.group(1))
    return None

def _extract_review_count(reviews_text):
    """Extract review count from text."""
    if not reviews_text:
        return 0
    # Simplified regex to avoid DoS: match digits with optional commas, but limit backtracking
    # Pattern: one or more digits, optionally followed by comma and more digits (max 3 groups)
    review_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*reviews?', reviews_text)
    if review_match:
        return int(review_match.group(1).replace(',', ''))
    # Fallback for simple number without commas (bounded to prevent excessive backtracking)
    simple_match = re.search(r'(\d{1,10})\s*reviews?', reviews_text)
    if simple_match:
        return int(simple_match.group(1))
    return 0

def _extract_city_from_location(location):
    """Extract city from location string."""
    if not location:
        return "Unknown"
    
    # Simplified regex to avoid DoS: use non-greedy match with bounded length
    city_match = re.search(r',\s*([A-Za-z][A-Za-z\s]{0,50}?)(?:\s*\([^)]{0,50}\))?$', location)
    if city_match:
        return city_match.group(1).strip()
    
    # Fallback: look for common city patterns
    city_patterns = [
        r'\b(Toronto|Mumbai|Delhi|Bangalore|Chennai|Kolkata|Hyderabad|Pune|Ahmedabad|Jaipur|London|Paris|Berlin|Rome|Amsterdam|Madrid|Vienna|Prague|Barcelona|Munich|Zurich|Geneva|Brussels|Copenhagen|Stockholm|Oslo|Helsinki|Dublin|Edinburgh|Glasgow|Manchester|Birmingham|Liverpool|Leeds|Sheffield|Newcastle|Nottingham|Leicester|Coventry|Bradford|Cardiff|Belfast|Southampton|Portsmouth|Plymouth|Exeter|Bristol|Bath|Oxford|Cambridge|Canterbury|Norwich|Ipswich|Colchester|Chelmsford|Southend|Basildon|Maidstone|Gillingham|Chatham|Rochester|Dartford|Gravesend|Sevenoaks|Tunbridge Wells|Tonbridge|Ashford|Folkestone|Dover|Canterbury|Margate|Ramsgate|Broadstairs|Deal|Sandwich|Faversham|Whitstable|Herne Bay|Birchington|Westgate|Cliftonville|Manston|Ramsgate|Broadstairs|Margate|Cliftonville|Westgate|Birchington|Herne Bay|Whitstable|Faversham|Sandwich|Deal|Dover|Folkestone|Ashford|Tonbridge|Tunbridge Wells|Sevenoaks|Gravesend|Dartford|Rochester|Chatham|Gillingham|Maidstone|Basildon|Southend|Chelmsford|Colchester|Ipswich|Norwich|Canterbury|Cambridge|Oxford|Bath|Bristol|Exeter|Plymouth|Portsmouth|Southampton|Belfast|Cardiff|Bradford|Coventry|Leicester|Nottingham|Newcastle|Sheffield|Leeds|Liverpool|Birmingham|Manchester|Glasgow|Edinburgh|Dublin|Helsinki|Oslo|Stockholm|Copenhagen|Brussels|Geneva|Zurich|Munich|Barcelona|Prague|Vienna|Madrid|Amsterdam|Rome|Berlin|Paris|London|Jaipur|Ahmedabad|Pune|Hyderabad|Kolkata|Chennai|Bangalore|Delhi|Mumbai)\b'
    ]
    for pattern in city_patterns:
        city_match = re.search(pattern, location, re.IGNORECASE)
        if city_match:
            return city_match.group(1).strip()
    
    return "Unknown"

def parse_hotel_row(row):
    """Parse a single hotel row from CSV"""
    try:
        hotel_name = row.get(CSV_COLUMN_HOTEL_NAME, '').strip()
        if not hotel_name:
            return None
        
        location = row.get(CSV_COLUMN_LOCATION, '').strip()
        rating_text = row.get(CSV_COLUMN_RATING, '').strip()
        reviews_text = row.get(CSV_COLUMN_REVIEWS, '').strip()
        price_text = row.get(CSV_COLUMN_PRICE, '').strip()
        url = row.get(CSV_COLUMN_URL, '').strip()
        
        rating = _extract_rating_from_text(rating_text)
        review_count = _extract_review_count(reviews_text)
        city = _extract_city_from_location(location)
        
        return {
            "name": hotel_name,
            "city": city,
            "address": location,
            "location": location,
            "rating": rating,
            "review_count": review_count,
            "price_per_night": price_text if price_text else None,
            "url": url if url else None,
            "source": "csv"
        }
    except Exception as e:
        print(f"Error parsing hotel row: {e}")
        return None

def _extract_hotel_name_from_line(hotel_name_line):
    """Extract hotel name from line."""
    if hotel_name_line.startswith(CSV_COLUMN_HOTEL_NAME):
        return None  # Skip header
    hotel_name = hotel_name_line.split(',')[0].strip().strip('"')
    return hotel_name if hotel_name else None

def _scan_lines_for_data(lines, start_index, max_lines=10):
    """Scan lines for location, rating, reviews, and URL."""
    location = ""
    rating_text = ""
    reviews_text = ""
    url = ""
    
    for i in range(start_index, min(start_index + max_lines, len(lines))):
        line = lines[i].strip()
        
        if ',' in line and ('Toronto' in line or 'London' in line or 'Paris' in line or 'Berlin' in line):
            parts = line.split(',')
            if len(parts) >= 2:
                location = parts[1].strip().strip('"')
        
        if 'Scored' in line:
            rating_text = line
        
        if 'reviews' in line:
            reviews_text = line
        
        if 'https://www.booking.com' in line:
            url = line.strip().strip('"')
    
    return location, rating_text, reviews_text, url

def parse_multiline_hotel_entry(lines, start_index):
    """Parse a multiline hotel entry from CSV"""
    try:
        hotel_name_line = lines[start_index]
        hotel_name = _extract_hotel_name_from_line(hotel_name_line)
        if not hotel_name:
            return None
        
        location, rating_text, reviews_text, url = _scan_lines_for_data(lines, start_index)
        
        rating = _extract_rating_from_text(rating_text)
        review_count = _extract_review_count(reviews_text)
        city = _extract_city_from_location(location)
        
        return {
            "name": hotel_name,
            "city": city,
            "address": location,
            "location": location,
            "rating": rating,
            "review_count": review_count,
            "price_per_night": None,  # Not extracted in multiline format
            "url": url if url else None,
            "source": "csv"
        }
    except Exception as e:
        print(f"Error parsing multiline hotel entry: {e}")
        return None

def _clear_existing_hotels():
    """Clear existing hotels from database."""
    existing_count = Hotel.query.count()
    if existing_count > 0:
        print(f"Found {existing_count} existing hotels in database.")
        print("Clearing existing hotels and reloading with updated parsing...")
        Hotel.query.delete()
        db.session.commit()
        print("Cleared existing hotels.")

def _is_hotel_entry_start(line):
    """Check if line starts a hotel entry."""
    if not line:
        return False
    hotel_prefixes = ('Hotel Name', 'One King', 'Chelsea', 'Riu', 'Fairmont', 
                     'DoubleTree', 'Holiday', 'Radisson', 'Sheraton', 'Novotel', 
                     'Hotel X', 'Toronto Marriott', 'Hilton', 'Yorkville')
    return line.startswith(hotel_prefixes)

def _save_hotel_to_db(hotel_data):
    """Save or update hotel in database."""
    existing = Hotel.query.filter_by(
        name=hotel_data['name'],
        city=hotel_data['city']
    ).first()
    
    if existing:
        existing.address = hotel_data['address']
        existing.location = hotel_data['location']
        existing.rating = hotel_data['rating']
        existing.review_count = hotel_data['review_count']
        existing.price_per_night = hotel_data['price_per_night']
        existing.url = hotel_data['url']
        existing.updated_at = datetime.now(timezone.utc)
    else:
        hotel = Hotel(**hotel_data)
        db.session.add(hotel)

def _process_csv_file(csv_path, csv_file):
    """Process a single CSV file and return loaded count."""
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return 0
    
    print(f"Loading hotels from {csv_file}...")
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            content = file.read()
            lines = content.split('\n')
            
            i = 0
            loaded_count = 0
            
            while i < len(lines):
                line = lines[i].strip()
                if not _is_hotel_entry_start(line):
                    i += 1
                    continue
                
                hotel_data = parse_multiline_hotel_entry(lines, i)
                if hotel_data:
                    _save_hotel_to_db(hotel_data)
                    loaded_count += 1
                
                i += 1
            
            db.session.commit()
            print(f"Loaded {loaded_count} hotels from {csv_file}")
            return loaded_count
            
    except Exception as e:
        print(f"Error loading {csv_file}: {e}")
        db.session.rollback()
        return 0

def load_hotels_from_csv():
    """Load hotels from CSV files into database"""
    app = create_app()
    
    with app.app_context():
        _clear_existing_hotels()
        
        csv_files = ["booking_hotels.csv", "booking_hotels_full.csv"]
        total_loaded = 0
        
        for csv_file in csv_files:
            csv_path = os.path.join(os.path.dirname(__file__), csv_file)
            loaded_count = _process_csv_file(csv_path, csv_file)
            total_loaded += loaded_count
        
        print(f"\nTotal hotels loaded: {total_loaded}")
        print(f"Total hotels in database: {Hotel.query.count()}")

if __name__ == "__main__":
    load_hotels_from_csv()
