#!/usr/bin/env python3
import re
import csv
from app import create_app
from app.models import db, Hotel

def parse_toronto_hotels():
    app = create_app()
    with app.app_context():
        # Clear existing Toronto hotels
        Hotel.query.filter(Hotel.city == 'Toronto').delete()
        db.session.commit()
        print('Cleared existing Toronto hotels')
        
        # Read the CSV file
        with open('booking_hotels_full.csv', 'r', encoding='utf-8') as file:
            content = file.read()
            lines = content.split('\n')
        
        toronto_hotels = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip header and empty lines
            if not line or line.startswith('Hotel Name'):
                i += 1
                continue
            
            # Check if this line contains a hotel name
            if ',' in line and not line.startswith('https://'):
                hotel_name = line.split(',')[0].strip().strip('"')
                
                # Look for Toronto in the next few lines
                location = ''
                rating_text = ''
                reviews_text = ''
                url = ''
                
                # Search through next 10 lines for hotel data
                for j in range(i, min(i + 10, len(lines))):
                    next_line = lines[j].strip()
                    
                    # Look for location with Toronto
                    if 'Toronto' in next_line and ',' in next_line:
                        parts = next_line.split(',')
                        if len(parts) >= 2:
                            location = parts[1].strip().strip('"')
                    
                    # Look for rating
                    if 'Scored' in next_line:
                        rating_text = next_line
                    
                    # Look for reviews
                    if 'reviews' in next_line:
                        reviews_text = next_line
                    
                    # Look for URL
                    if 'https://www.booking.com' in next_line:
                        url = next_line.strip().strip('"')
                
                # Only process if we found Toronto location
                if 'Toronto' in location:
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
                    
                    # Generate price based on rating
                    price = None
                    if rating:
                        if rating >= 9.0:
                            price = f'CAD {int(300 + (rating - 9.0) * 100)}'
                        elif rating >= 8.0:
                            price = f'CAD {int(200 + (rating - 8.0) * 50)}'
                        else:
                            price = f'CAD {int(150 + (rating - 7.0) * 25)}'
                    
                    hotel_data = {
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
                    
                    toronto_hotels.append(hotel_data)
                    print(f'Found Toronto hotel: {hotel_name} - Rating: {rating}')
            
            i += 1
        
        # Add all Toronto hotels to database
        for hotel_data in toronto_hotels:
            hotel = Hotel(**hotel_data)
            db.session.add(hotel)
        
        db.session.commit()
        print(f'Added {len(toronto_hotels)} Toronto hotels to database')
        print(f'Total hotels in database: {Hotel.query.count()}')

if __name__ == '__main__':
    parse_toronto_hotels()
