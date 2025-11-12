#!/usr/bin/env python3
import csv
import re
from app import create_app
from app.models import db, Hotel

def parse_toronto_hotels():
    app = create_app()
    with app.app_context():
        # Clear existing Toronto hotels
        Hotel.query.filter(Hotel.city == 'Toronto').delete()
        db.session.commit()
        print('Cleared existing Toronto hotels')
        
        # Read the CSV file with proper handling of multiline entries
        hotels = []
        
        with open('booking_hotels_full.csv', 'r', encoding='utf-8') as file:
            content = file.read()
            lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip header
            if line.startswith('Hotel Name,Location'):
                i += 1
                continue
            
            if not line:
                i += 1
                continue
            
            # Try to parse as standard CSV row
            try:
                parts = line.split(',', 1)  # Split only on first comma
                if len(parts) >= 2:
                    hotel_name = parts[0].strip().strip('"')
                    remaining = parts[1]
                    
                    # Check if it's a Toronto hotel
                    if 'Toronto' in remaining:
                        # Now we need to extract all fields
                        # Read more lines to get complete entry
                        entry_lines = [line]
                        j = i + 1
                        rating_text = ''
                        reviews_text = ''
                        url = ''
                        
                        # Look ahead for additional data
                        while j < len(lines) and j < i + 10:
                            next_line = lines[j].strip()
                            if not next_line:
                                j += 1
                                continue
                            
                            if next_line.startswith('https://'):
                                url = next_line.strip().strip('"')
                            elif 'Scored' in next_line:
                                rating_text = next_line
                            elif 'reviews' in next_line:
                                reviews_text = next_line
                            
                            j += 1
                        
                        # Extract location - split properly and get location field
                        location_parts = remaining.split('",')
                        location = location_parts[0].strip().strip('"') if len(location_parts) > 0 else remaining[:100]
                        
                        # Clean up address - extract just the neighborhood/district
                        address = location.split(',')[0] if ',' in location else location
                        
                        # Extract rating
                        rating = None
                        if rating_text:
                            match = re.search(r'Scored\s+(\d+\.?\d*)', rating_text)
                            if match:
                                rating = float(match.group(1))
                        
                        # Extract review count
                        review_count = 0
                        if reviews_text:
                            match = re.search(r'(\d+(?:,\d+)*)\s*reviews?', reviews_text)
                            if match:
                                review_count = int(match.group(1).replace(',', ''))
                        
                        # Add to hotels list
                        if hotel_name and 'Toronto' in location:
                            hotels.append({
                                'name': hotel_name,
                                'city': 'Toronto',
                                'address': location,
                                'location': location,
                                'rating': rating,
                                'review_count': review_count,
                                'price_per_night': None,
                                'url': url if url else None,
                                'source': 'csv'
                            })
                            print(f'Found Toronto hotel: {hotel_name} - Rating: {rating}')
            
            except Exception as e:
                pass
            
            i += 1
        
        # Add all Toronto hotels to database
        for hotel_data in hotels:
            hotel = Hotel(**hotel_data)
            db.session.add(hotel)
        
        db.session.commit()
        print(f'\nAdded {len(hotels)} Toronto hotels to database')
        print(f'Total hotels in database: {Hotel.query.count()}')

if __name__ == '__main__':
    parse_toronto_hotels()
