#!/usr/bin/env python3
import re
import csv
from app import create_app
from app.models import db, Hotel

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
            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
            if rating_match:
                rating = float(rating_match.group(1))
        
        # Extract review count
        review_count = 0
        if reviews_text:
            review_match = re.search(r'(\d+(?:,\d+)*)\s*reviews?', reviews_text)
            if review_match:
                review_count = int(review_match.group(1).replace(',', ''))
        
        # Extract city from location - improved parsing
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

if __name__ == '__main__':
    load_all_hotels()
