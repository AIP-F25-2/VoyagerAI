#!/usr/bin/env python3
import re
import csv
from app import create_app
from app.models import db, Hotel
# Import helper functions from load_hotels_to_db
from load_hotels_to_db import (
    CSV_COLUMN_HOTEL_NAME, CSV_COLUMN_LOCATION, CSV_COLUMN_RATING,
    CSV_COLUMN_REVIEWS, CSV_COLUMN_PRICE, CSV_COLUMN_URL,
    _extract_rating_from_text, _extract_review_count, _extract_city_from_location
)

def load_all_hotels():
    app = create_app()
    with app.app_context():
        # Clear ALL existing hotels
        Hotel.query.delete()
        db.session.commit()
        print('Cleared all existing hotels')
        
        # Load from both CSV files
        csv_files = ['booking_hotels.csv', 'booking_hotels_full.csv']
        total_loaded = 0
        
        for csv_file in csv_files:
            print(f'Loading from {csv_file}...')
            
            try:
                with open(csv_file, 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    loaded_count = 0
                    
                    for row in reader:
                        hotel_data = parse_hotel_row(row)
                        if hotel_data:
                            hotel = Hotel(**hotel_data)
                            db.session.add(hotel)
                            loaded_count += 1
                            
                            if loaded_count % 100 == 0:
                                print(f'Loaded {loaded_count} hotels from {csv_file}...')
                
                db.session.commit()
                print(f'Loaded {loaded_count} hotels from {csv_file}')
                total_loaded += loaded_count
                
            except Exception as e:
                print(f'Error loading {csv_file}: {e}')
        
        print(f'Total hotels loaded: {total_loaded}')
        print(f'Total hotels in database: {Hotel.query.count()}')
        
        # Show cities summary
        cities = db.session.query(Hotel.city).filter(Hotel.city.isnot(None)).distinct().all()
        print(f'Cities available: {len(cities)}')
        for (city,) in cities[:10]:  # Show first 10 cities
            count = Hotel.query.filter(Hotel.city == city).count()
            print(f'  {city}: {count} hotels')

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

if __name__ == '__main__':
    load_all_hotels()
