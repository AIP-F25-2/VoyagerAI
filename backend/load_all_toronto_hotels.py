#!/usr/bin/env python3
import re
import csv
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

def _scan_for_toronto_data(lines, start_index, max_lines=10):
    """Scan lines for Toronto hotel data."""
    location = ''
    rating_text = ''
    reviews_text = ''
    url = ''
    
    for j in range(start_index, min(start_index + max_lines, len(lines))):
        next_line = lines[j].strip()
        
        if 'Toronto' in next_line and ',' in next_line:
            parts = next_line.split(',')
            if len(parts) >= 2:
                location = parts[1].strip().strip('"')
        
        if 'Scored' in next_line:
            rating_text = next_line
        
        if 'reviews' in next_line:
            reviews_text = next_line
        
        if 'https://www.booking.com' in next_line:
            url = next_line.strip().strip('"')
    
    return location, rating_text, reviews_text, url

def _calculate_price_from_rating(rating):
    """Calculate price based on rating."""
    if not rating:
        return None
    if rating >= 9.0:
        return f'CAD {int(300 + (rating - 9.0) * 100)}'
    elif rating >= 8.0:
        return f'CAD {int(200 + (rating - 8.0) * 50)}'
    else:
        return f'CAD {int(150 + (rating - 7.0) * 25)}'

def _process_toronto_hotel(hotel_name, location, rating_text, reviews_text, url):
    """Process a Toronto hotel entry."""
    if 'Toronto' not in location:
        return None
    
    rating = _extract_rating_from_text(rating_text)
    review_count = _extract_review_count(reviews_text)
    price = _calculate_price_from_rating(rating)
    
    return {
        'name': hotel_name,
        'city': 'Toronto',
        'address': location,
        'location': location,
        'rating': rating,
        'review_count': review_count,
        'price_per_night': price,
        'url': url,
        'source': 'csv'
    }

def _parse_toronto_hotels_from_lines(lines):
    """Parse Toronto hotels from lines."""
    toronto_hotels = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        if not line or line.startswith(CSV_COLUMN_HOTEL_NAME):
            i += 1
            continue
        
        if ',' in line and not line.startswith('https://'):
            hotel_name = line.split(',')[0].strip().strip('"')
            location, rating_text, reviews_text, url = _scan_for_toronto_data(lines, i)
            
            hotel_data = _process_toronto_hotel(hotel_name, location, rating_text, reviews_text, url)
            if hotel_data:
                toronto_hotels.append(hotel_data)
                print(f'Found Toronto hotel: {hotel_name} - Rating: {hotel_data["rating"]}')
        
        i += 1
    
    return toronto_hotels

def _save_toronto_hotels_to_db(toronto_hotels):
    """Save Toronto hotels to database."""
    for hotel_data in toronto_hotels:
        hotel = Hotel(**hotel_data)
        db.session.add(hotel)
    
    db.session.commit()
    print(f'Added {len(toronto_hotels)} Toronto hotels to database')
    print(f'Total hotels in database: {Hotel.query.count()}')

def parse_toronto_hotels():
    app = create_app()
    with app.app_context():
        _clear_toronto_hotels()
        lines = _read_csv_lines('booking_hotels_full.csv')
        toronto_hotels = _parse_toronto_hotels_from_lines(lines)
        _save_toronto_hotels_to_db(toronto_hotels)

if __name__ == '__main__':
    parse_toronto_hotels()
