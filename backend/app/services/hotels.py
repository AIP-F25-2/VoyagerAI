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
    
    def _extract_rating(self, rating_text: str) -> Optional[float]:
        """Extract numeric rating from text."""
        if not rating_text:
            return None
        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
        if rating_match:
            return float(rating_match.group(1))
        return None

    def _extract_review_count(self, reviews_text: str) -> int:
        """Extract review count from text."""
        if not reviews_text:
            return 0
        review_match = re.search(r'(\d+(?:,\d+)*)\s*reviews?', reviews_text)
        if review_match:
            return int(review_match.group(1).replace(',', ''))
        return 0

    def _extract_city_from_location(self, location: str) -> str:
        """Extract city name from location string."""
        if not location:
            return "Unknown"
        
        # Try to extract city from location string
        # Pattern: "District, City (District)" or "City" or "District, City"
        city_match = re.search(r',\s*([A-Za-z\s]+?)(?:\s*\([^)]+\))?$', location)
        if city_match:
            return city_match.group(1).strip()
        
        # Fallback: look for common city patterns
        common_cities = [
            "Toronto", "Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata",
            "Hyderabad", "Pune", "Ahmedabad", "Jaipur", "London", "Paris",
            "Berlin", "Rome", "Amsterdam", "Madrid", "Vienna", "Prague",
            "Barcelona", "Munich", "Zurich", "Geneva", "Brussels", "Copenhagen",
            "Stockholm", "Oslo", "Helsinki", "Dublin", "Edinburgh", "Glasgow"
        ]
        
        location_lower = location.lower()
        for city in common_cities:
            if city.lower() in location_lower:
                return city
        
        return "Unknown"

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
            
            rating = self._extract_rating(rating_text)
            review_count = self._extract_review_count(reviews_text)
            city = self._extract_city_from_location(location)
            
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


