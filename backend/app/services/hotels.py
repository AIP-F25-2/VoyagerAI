import os
import csv
import re
from datetime import datetime
from typing import List, Dict, Any, Union, Optional


class HotelCSVLoader:
    """Load and search hotels from CSV files"""
    
    def __init__(self):
        self.hotels_data = []
        self.load_hotels_from_csv()
    
    def load_hotels_from_csv(self):
        """Load hotels from CSV files"""
        csv_files = [
            "/Users/sujanvg/sujan/aip/VoyagerAI/backend/booking_hotels.csv",
            "/Users/sujanvg/sujan/aip/VoyagerAI/backend/booking_hotels_full.csv"
        ]
        
        for csv_file in csv_files:
            if os.path.exists(csv_file):
                try:
                    with open(csv_file, 'r', encoding='utf-8') as file:
                        reader = csv.DictReader(file)
                        for row in reader:
                            # Clean and parse the data
                            hotel_data = self._parse_hotel_row(row)
                            if hotel_data:
                                self.hotels_data.append(hotel_data)
                except Exception as e:
                    print(f"Error loading {csv_file}: {e}")
    
    def _parse_hotel_row(self, row: Dict[str, str]) -> Optional[Dict[str, Any]]:
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
                "id": f"hotel_{len(self.hotels_data)}",
                "name": hotel_name,
                "city": city,
                "address": location,
                "rating": rating,
                "review_count": review_count,
                "price_per_night": price_text if price_text else None,
                "url": url if url else None,
                "source": "csv"
            }
        except Exception as e:
            print(f"Error parsing hotel row: {e}")
            return None
    
    def search_hotels(self, city: str = None, query: str = None, min_rating: float = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Search hotels by city, query, or rating"""
        results = self.hotels_data.copy()
        
        # Filter by city
        if city:
            city_lower = city.lower()
            results = [h for h in results if city_lower in h.get('city', '').lower()]
        
        # Filter by query (search in name, city, address)
        if query:
            query_lower = query.lower()
            results = [h for h in results if (
                query_lower in h.get('name', '').lower() or
                query_lower in h.get('city', '').lower() or
                query_lower in h.get('address', '').lower()
            )]
        
        # Filter by minimum rating
        if min_rating:
            results = [h for h in results if h.get('rating', 0) >= min_rating]
        
        # Sort by rating (highest first), handle None values
        results.sort(key=lambda x: x.get('rating') or 0, reverse=True)
        
        return results[:limit]
    
    def get_hotels_by_city(self, city: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get hotels for a specific city"""
        return self.search_hotels(city=city, limit=limit)
    
    def get_all_hotels(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all hotels"""
        return self.hotels_data[:limit]


# Global instance
hotel_csv_loader = HotelCSVLoader()


def search_hotels(city: str, check_in: Optional[str] = None, check_out: Optional[str] = None, guests: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Search hotels from CSV data and database.
    
    Args:
        city: City to search in
        check_in: Check-in date (optional)
        check_out: Check-out date (optional)
        guests: Number of guests (optional)
        limit: Maximum number of results
    
    Returns:
        List of hotel dictionaries
    """
    # First try to get hotels from CSV data
    csv_hotels = hotel_csv_loader.search_hotels(city=city, limit=limit)
    
    # Add check-in/check-out dates to results
    for hotel in csv_hotels:
        hotel["check_in"] = check_in
        hotel["check_out"] = check_out
        hotel["guests"] = guests

    # If we have CSV results, return them
    if csv_hotels:
        return csv_hotels

    # If no CSV results, try database
    try:
        from app import create_app
        from app.models import db, Hotel
        
        app = create_app()
        with app.app_context():
            db_hotels = Hotel.query.filter(Hotel.city.ilike(f"%{city}%")).limit(limit).all()
            
            if db_hotels:
                result = []
                for hotel in db_hotels:
                    hotel_dict = hotel.to_dict()
                    hotel_dict["check_in"] = check_in
                    hotel_dict["check_out"] = check_out
                    hotel_dict["guests"] = guests
                    result.append(hotel_dict)
                return result
    except Exception as e:
        print(f"Error searching database: {e}")

    # If no results found, return empty list
    return []


def get_hotels_by_city(city: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Get hotels for a specific city"""
    return hotel_csv_loader.get_hotels_by_city(city, limit)


def get_all_hotels(limit: int = 100) -> List[Dict[str, Any]]:
    """Get all available hotels"""
    return hotel_csv_loader.get_all_hotels(limit)


def search_hotels_by_query(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Search hotels by query string"""
    return hotel_csv_loader.search_hotels(query=query, limit=limit)


