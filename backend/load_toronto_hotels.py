#!/usr/bin/env python3
import csv
import re
from app import create_app
from app.models import db, Hotel
from load_hotels_to_db import (
    CSV_COLUMN_HOTEL_NAME, _extract_rating_from_text, _extract_review_count
)

def _clear_toronto_hotels():
    """Clear existing Toronto hotels."""
    Hotel.query.filter(Hotel.city == 'Toronto').delete()
    db.session.commit()
    print('Cleared existing Toronto hotels')

def _read_csv_lines(filename):
    """Read CSV file and return lines."""
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()
        return content.split('\n')

def _should_skip_line(line):
    """Check if line should be skipped."""
    if not line:
        return True
    if line.startswith('Hotel Name,Location'):
        return True
    return False

def _scan_ahead_for_data(lines, start_index, max_lines=10):
    """Scan ahead for rating, reviews, and URL."""
    rating_text = ''
    reviews_text = ''
    url = ''
    
    for j in range(start_index + 1, min(start_index + max_lines, len(lines))):
        next_line = lines[j].strip()
        if not next_line:
            continue
        
        if next_line.startswith('https://'):
            url = next_line.strip().strip('"')
        elif 'Scored' in next_line:
            rating_text = next_line
        elif 'reviews' in next_line:
            reviews_text = next_line
    
    return rating_text, reviews_text, url

def _extract_location_from_remaining(remaining):
    """Extract location from remaining CSV data."""
    location_parts = remaining.split('",')
    if len(location_parts) > 0:
        return location_parts[0].strip().strip('"')
    return remaining[:100]

def _extract_address_from_location(location):
    """Extract address from location."""
    if ',' in location:
        return location.split(',')[0]
    return location

def _extract_rating_from_scored_text(rating_text):
    """Extract rating from 'Scored X.X' text."""
    if not rating_text:
        return None
    match = re.search(r'Scored\s+(\d+\.?\d*)', rating_text)
    if match:
        return float(match.group(1))
    return None

def _parse_toronto_hotel_entry(line, remaining, lines, i):
    """Parse a single Toronto hotel entry."""
    if 'Toronto' not in remaining:
        return None
    
    hotel_name = line.split(',', 1)[0].strip().strip('"')
    if not hotel_name:
        return None
    
    rating_text, reviews_text, url = _scan_ahead_for_data(lines, i)
    location = _extract_location_from_remaining(remaining)
    address = _extract_address_from_location(location)
    
    rating = _extract_rating_from_scored_text(rating_text)
    review_count = _extract_review_count(reviews_text)
    
    if 'Toronto' not in location:
        return None
    
    return {
        'name': hotel_name,
        'city': 'Toronto',
        'address': location,
        'location': location,
        'rating': rating,
        'review_count': review_count,
        'price_per_night': None,
        'url': url if url else None,
        'source': 'csv'
    }

def _parse_toronto_hotels_from_lines(lines):
    """Parse Toronto hotels from lines."""
    hotels = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        if _should_skip_line(line):
            i += 1
            continue
        
        try:
            parts = line.split(',', 1)
            if len(parts) >= 2:
                remaining = parts[1]
                hotel_data = _parse_toronto_hotel_entry(line, remaining, lines, i)
                if hotel_data:
                    hotels.append(hotel_data)
                    print(f'Found Toronto hotel: {hotel_data["name"]} - Rating: {hotel_data["rating"]}')
        except Exception:
            pass
        
        i += 1
    
    return hotels

def _save_toronto_hotels_to_db(hotels):
    """Save Toronto hotels to database."""
    for hotel_data in hotels:
        hotel = Hotel(**hotel_data)
        db.session.add(hotel)
    
    db.session.commit()
    print(f'\nAdded {len(hotels)} Toronto hotels to database')
    print(f'Total hotels in database: {Hotel.query.count()}')

def parse_toronto_hotels():
    app = create_app()
    with app.app_context():
        _clear_toronto_hotels()
        lines = _read_csv_lines('booking_hotels_full.csv')
        hotels = _parse_toronto_hotels_from_lines(lines)
        _save_toronto_hotels_to_db(hotels)

if __name__ == '__main__':
    parse_toronto_hotels()
