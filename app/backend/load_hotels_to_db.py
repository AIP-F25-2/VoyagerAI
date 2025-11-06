#!/usr/bin/env python3
"""
Script to load hotels from CSV files into the database.
Run this after setting up the database to populate it with hotel data.
"""

import os
import sys
import csv
import re
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.models import db, Hotel

def parse_hotel_row(row):
    """Parse a single hotel row from CSV"""
    try:
        hotel_name = row.get('Hotel Name', '').strip()
        if not hotel_name:
            return None
        
        location = row.get('Location', '').strip()
        rating_text = row.get('Rating', '').strip()
        reviews_text = row.get('Reviews', '').strip()
        price_text = row.get('Price', '').strip()
        url = row.get('URL', '').strip()
        
        # Extract rating from text like "Scored 8.8\n8.8\nExcellent\n7,713 reviews"
        rating = None
        if rating_text:
            # Look for numeric rating in the text
            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
            if rating_match:
                rating = float(rating_match.group(1))
        
        # Extract review count
        review_count = 0
        if reviews_text:
            review_match = re.search(r'(\d+(?:,\d+)*)\s*reviews?', reviews_text)
            if review_match:
                review_count = int(review_match.group(1).replace(',', ''))
        
        # Extract city from location
        city = "Unknown"
        if location:
            # Try to extract city from location string
            # Pattern: "District, City (District)" or "City" or "District, City"
            city_match = re.search(r',\s*([A-Za-z\s]+?)(?:\s*\([^)]+\))?$', location)
            if city_match:
                city = city_match.group(1).strip()
            else:
                # Fallback: look for common city patterns
                city_patterns = [
                    r'\b(Toronto|Mumbai|Delhi|Bangalore|Chennai|Kolkata|Hyderabad|Pune|Ahmedabad|Jaipur|London|Paris|Berlin|Rome|Amsterdam|Madrid|Vienna|Prague|Barcelona|Munich|Zurich|Geneva|Brussels|Copenhagen|Stockholm|Oslo|Helsinki|Dublin|Edinburgh|Glasgow|Manchester|Birmingham|Liverpool|Leeds|Sheffield|Newcastle|Nottingham|Leicester|Coventry|Bradford|Cardiff|Belfast|Southampton|Portsmouth|Plymouth|Exeter|Bristol|Bath|Oxford|Cambridge|Canterbury|Norwich|Ipswich|Colchester|Chelmsford|Southend|Basildon|Maidstone|Gillingham|Chatham|Rochester|Dartford|Gravesend|Sevenoaks|Tunbridge Wells|Tonbridge|Ashford|Folkestone|Dover|Canterbury|Margate|Ramsgate|Broadstairs|Deal|Sandwich|Faversham|Whitstable|Herne Bay|Birchington|Westgate|Cliftonville|Manston|Ramsgate|Broadstairs|Margate|Cliftonville|Westgate|Birchington|Herne Bay|Whitstable|Faversham|Sandwich|Deal|Dover|Folkestone|Ashford|Tonbridge|Tunbridge Wells|Sevenoaks|Gravesend|Dartford|Rochester|Chatham|Gillingham|Maidstone|Basildon|Southend|Chelmsford|Colchester|Ipswich|Norwich|Canterbury|Cambridge|Oxford|Bath|Bristol|Exeter|Plymouth|Portsmouth|Southampton|Belfast|Cardiff|Bradford|Coventry|Leicester|Nottingham|Newcastle|Sheffield|Leeds|Liverpool|Birmingham|Manchester|Glasgow|Edinburgh|Dublin|Helsinki|Oslo|Stockholm|Copenhagen|Brussels|Geneva|Zurich|Munich|Barcelona|Prague|Vienna|Madrid|Amsterdam|Rome|Berlin|Paris|London|Jaipur|Ahmedabad|Pune|Hyderabad|Kolkata|Chennai|Bangalore|Delhi|Mumbai)\b'
                ]
                for pattern in city_patterns:
                    city_match = re.search(pattern, location, re.IGNORECASE)
                    if city_match:
                        city = city_match.group(1).strip()
                        break
        
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

def parse_multiline_hotel_entry(lines, start_index):
    """Parse a multiline hotel entry from CSV"""
    try:
        # Find the hotel name line
        hotel_name_line = lines[start_index]
        if hotel_name_line.startswith('Hotel Name'):
            return None  # Skip header
        
        # Extract hotel name (first part before comma)
        hotel_name = hotel_name_line.split(',')[0].strip().strip('"')
        if not hotel_name:
            return None
        
        # Find the location (look for pattern like "District, City (District)")
        location = ""
        rating_text = ""
        reviews_text = ""
        price_text = ""
        url = ""
        
        # Look through the next few lines to find all data
        for i in range(start_index, min(start_index + 10, len(lines))):
            line = lines[i].strip()
            
            # Look for location pattern
            if ',' in line and ('Toronto' in line or 'London' in line or 'Paris' in line or 'Berlin' in line):
                parts = line.split(',')
                if len(parts) >= 2:
                    location = parts[1].strip().strip('"')
            
            # Look for rating pattern
            if 'Scored' in line:
                rating_text = line
            
            # Look for reviews pattern
            if 'reviews' in line:
                reviews_text = line
            
            # Look for URL pattern
            if 'https://www.booking.com' in line:
                url = line.strip().strip('"')
        
        # Extract rating
        rating = None
        if rating_text:
            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
            if rating_match:
                rating = float(rating_match.group(1))
        
        # Extract review count
        review_count = 0
        if reviews_text:
            review_match = re.search(r'(\d+(?:,\d+)*)\s*reviews?', reviews_text)
            if review_match:
                review_count = int(review_match.group(1).replace(',', ''))
        
        # Extract city from location
        city = "Unknown"
        if location:
            # Try to extract city from location string
            city_match = re.search(r',\s*([A-Za-z\s]+?)(?:\s*\([^)]+\))?$', location)
            if city_match:
                city = city_match.group(1).strip()
            else:
                # Fallback: look for common city patterns
                city_patterns = [
                    r'\b(Toronto|Mumbai|Delhi|Bangalore|Chennai|Kolkata|Hyderabad|Pune|Ahmedabad|Jaipur|London|Paris|Berlin|Rome|Amsterdam|Madrid|Vienna|Prague|Barcelona|Munich|Zurich|Geneva|Brussels|Copenhagen|Stockholm|Oslo|Helsinki|Dublin|Edinburgh|Glasgow|Manchester|Birmingham|Liverpool|Leeds|Sheffield|Newcastle|Nottingham|Leicester|Coventry|Bradford|Cardiff|Belfast|Southampton|Portsmouth|Plymouth|Exeter|Bristol|Bath|Oxford|Cambridge|Canterbury|Norwich|Ipswich|Colchester|Chelmsford|Southend|Basildon|Maidstone|Gillingham|Chatham|Rochester|Dartford|Gravesend|Sevenoaks|Tunbridge Wells|Tonbridge|Ashford|Folkestone|Dover|Canterbury|Margate|Ramsgate|Broadstairs|Deal|Sandwich|Faversham|Whitstable|Herne Bay|Birchington|Westgate|Cliftonville|Manston|Ramsgate|Broadstairs|Margate|Cliftonville|Westgate|Birchington|Herne Bay|Whitstable|Faversham|Sandwich|Deal|Dover|Folkestone|Ashford|Tonbridge|Tunbridge Wells|Sevenoaks|Gravesend|Dartford|Rochester|Chatham|Gillingham|Maidstone|Basildon|Southend|Chelmsford|Colchester|Ipswich|Norwich|Canterbury|Cambridge|Oxford|Bath|Bristol|Exeter|Plymouth|Portsmouth|Southampton|Belfast|Cardiff|Bradford|Coventry|Leicester|Nottingham|Newcastle|Sheffield|Leeds|Liverpool|Birmingham|Manchester|Glasgow|Edinburgh|Dublin|Helsinki|Oslo|Stockholm|Copenhagen|Brussels|Geneva|Zurich|Munich|Barcelona|Prague|Vienna|Madrid|Amsterdam|Rome|Berlin|Paris|London|Jaipur|Ahmedabad|Pune|Hyderabad|Kolkata|Chennai|Bangalore|Delhi|Mumbai)\b'
                ]
                for pattern in city_patterns:
                    city_match = re.search(pattern, location, re.IGNORECASE)
                    if city_match:
                        city = city_match.group(1).strip()
                        break
        
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
        print(f"Error parsing multiline hotel entry: {e}")
        return None

def load_hotels_from_csv():
    """Load hotels from CSV files into database"""
    app = create_app()
    
    with app.app_context():
        # Check if hotels already exist
        existing_count = Hotel.query.count()
        if existing_count > 0:
            print(f"Found {existing_count} existing hotels in database.")
            print("Clearing existing hotels and reloading with updated parsing...")
            Hotel.query.delete()
            db.session.commit()
            print("Cleared existing hotels.")
        
        csv_files = [
            "booking_hotels.csv",
            "booking_hotels_full.csv"
        ]
        
        total_loaded = 0
        
        for csv_file in csv_files:
            csv_path = os.path.join(os.path.dirname(__file__), csv_file)
            
            if not os.path.exists(csv_path):
                print(f"CSV file not found: {csv_path}")
                continue
            
            print(f"Loading hotels from {csv_file}...")
            
            try:
                with open(csv_path, 'r', encoding='utf-8') as file:
                    # Handle multiline CSV entries
                    content = file.read()
                    lines = content.split('\n')
                    
                    # Process each potential hotel entry
                    i = 0
                    loaded_count = 0
                    
                    while i < len(lines):
                        line = lines[i].strip()
                        if not line or not line.startswith(('Hotel Name', 'One King', 'Chelsea', 'Riu', 'Fairmont', 'DoubleTree', 'Holiday', 'Radisson', 'Sheraton', 'Novotel', 'Hotel X', 'Toronto Marriott', 'Hilton', 'Yorkville')):
                            i += 1
                            continue
                        
                        # Parse the hotel entry (might span multiple lines)
                        hotel_data = parse_multiline_hotel_entry(lines, i)
                        if hotel_data:
                            loaded_count += 1
                            # Add to database
                            existing = Hotel.query.filter_by(
                                name=hotel_data['name'],
                                city=hotel_data['city']
                            ).first()
                            
                            if not existing:
                                hotel = Hotel(
                                    name=hotel_data['name'],
                                    city=hotel_data['city'],
                                    address=hotel_data['address'],
                                    location=hotel_data['location'],
                                    rating=hotel_data['rating'],
                                    review_count=hotel_data['review_count'],
                                    price_per_night=hotel_data['price_per_night'],
                                    url=hotel_data['url'],
                                    source=hotel_data['source']
                                )
                                db.session.add(hotel)
                        
                        i += 1
                        
                        # Check if hotel already exists (by name and city)
                        existing = Hotel.query.filter_by(
                            name=hotel_data['name'],
                            city=hotel_data['city']
                        ).first()
                        
                        if existing:
                            # Update existing hotel
                            existing.address = hotel_data['address']
                            existing.location = hotel_data['location']
                            existing.rating = hotel_data['rating']
                            existing.review_count = hotel_data['review_count']
                            existing.price_per_night = hotel_data['price_per_night']
                            existing.url = hotel_data['url']
                            existing.updated_at = datetime.utcnow()
                        else:
                            # Create new hotel
                            hotel = Hotel(**hotel_data)
                            db.session.add(hotel)
                        
                        loaded_count += 1
                    
                    db.session.commit()
                    print(f"Loaded {loaded_count} hotels from {csv_file}")
                    total_loaded += loaded_count
                    
            except Exception as e:
                print(f"Error loading {csv_file}: {e}")
                db.session.rollback()
        
        print(f"\nTotal hotels loaded: {total_loaded}")
        print(f"Total hotels in database: {Hotel.query.count()}")

if __name__ == "__main__":
    load_hotels_from_csv()
