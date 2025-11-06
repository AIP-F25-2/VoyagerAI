import csv
import os
from datetime import datetime
from typing import List, Dict, Any
import re

class CSVEventLoader:
    """Load and parse CSV event data from the backend directory."""
    
    def __init__(self):
        self.backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.csv_files = [
            'berlin_events_large.csv',
            'europaticket_events_oct-nov-dec-jan_2025.csv'
        ]
    
    def load_all_csv_events(self) -> List[Dict[str, Any]]:
        """Load events from all CSV files and return formatted data."""
        all_events = []
        
        for csv_file in self.csv_files:
            file_path = os.path.join(self.backend_dir, csv_file)
            if os.path.exists(file_path):
                events = self._load_csv_file(file_path, csv_file)
                all_events.extend(events)
        
        return all_events
    
    def _load_csv_file(self, file_path: str, filename: str) -> List[Dict[str, Any]]:
        """Load and parse a single CSV file."""
        events = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # Detect delimiter
                sample = file.read(1024)
                file.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(file, delimiter=delimiter)
                
                for i, row in enumerate(reader):
                    # Clean and format the row data
                    event = self._format_event_data(row, filename, i)
                    if event:
                        events.append(event)
                        
        except Exception as e:
            print(f"Error loading CSV file {filename}: {e}")
        
        return events
    
    def _format_event_data(self, row: Dict[str, str], filename: str, index: int) -> Dict[str, Any]:
        """Format CSV row data into standardized event format."""
        try:
            # Extract title
            title = row.get('title', '').strip().strip('"')
            if not title:
                return None
            
            # Extract URL
            url = row.get('url', '').strip().strip('"')
            
            # Extract description
            description = row.get('description', '').strip().strip('"')
            
            # Extract date and time (if available)
            date_str = row.get('date', '').strip().strip('"')
            time_str = row.get('time', '').strip().strip('"')
            
            # Parse date
            event_date = None
            if date_str:
                event_date = self._parse_date(date_str)
            
            # Extract venue
            venue = row.get('venue', '').strip().strip('"')
            
            # Extract price
            price = row.get('price', '').strip().strip('"')
            
            # Extract city from venue or description
            city = self._extract_city(venue, description, title)
            
            # Create unique ID
            event_id = f"csv_{filename}_{index}_{hash(title)}"
            
            # Format for frontend (matching Ticketmaster format)
            formatted_event = {
                "id": event_id,
                "name": title,
                "url": url,
                "dates": {
                    "start": {
                        "localDate": event_date.strftime("%Y-%m-%d") if event_date else "2025-01-01",
                        "localTime": time_str if time_str else "19:00"
                    }
                },
                "images": [{"url": "/placeholder.jpg"}],
                "_embedded": {
                    "venues": [{
                        "name": venue or "TBA",
                        "city": {"name": city or "Unknown"}
                    }]
                },
                "priceRanges": [{"min": 0, "max": 100}] if price else None,
                "description": description,
                "source": "csv",
                "csv_file": filename
            }
            
            return formatted_event
            
        except Exception as e:
            print(f"Error formatting event data: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse various date formats from CSV."""
        try:
            # Common date formats in the CSV
            date_formats = [
                "%d %b %Y",  # "08 Oct 2025"
                "%d/%m/%Y",  # "08/10/2025"
                "%Y-%m-%d",  # "2025-10-08"
                "%d-%m-%Y",  # "08-10-2025"
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # If no format matches, return a default date
            return datetime(2025, 1, 1)
            
        except Exception:
            return datetime(2025, 1, 1)
    
    def _extract_city(self, venue: str, description: str, title: str) -> str:
        """Extract city name from venue, description, or title."""
        # Common European cities in the data
        cities = [
            "Berlin", "Vienna", "Budapest", "Barcelona", "Madrid", "Rome", 
            "Florence", "Naples", "Hamburg", "Munich", "Prague", "Bratislava",
            "Seville", "Milan", "Paris", "London", "Amsterdam", "Brussels"
        ]
        
        text_to_search = f"{venue} {description} {title}".lower()
        
        for city in cities:
            if city.lower() in text_to_search:
                return city
        
        # Try to extract from venue if it contains city info
        if venue and "," in venue:
            parts = venue.split(",")
            for part in parts:
                part = part.strip()
                if any(city.lower() in part.lower() for city in cities):
                    return part
        
        return "Unknown"
    
    def get_events_by_city(self, city: str) -> List[Dict[str, Any]]:
        """Get events filtered by city."""
        all_events = self.load_all_csv_events()
        if not city:
            return all_events
        
        city_lower = city.lower()
        return [
            event for event in all_events
            if city_lower in event["_embedded"]["venues"][0]["city"]["name"].lower()
        ]
    
    def get_events_by_query(self, query: str) -> List[Dict[str, Any]]:
        """Get events filtered by search query."""
        all_events = self.load_all_csv_events()
        if not query:
            return all_events
        
        query_lower = query.lower()
        return [
            event for event in all_events
            if (query_lower in event["name"].lower() or 
                query_lower in event.get("description", "").lower())
        ]

# Global instance
csv_loader = CSVEventLoader()
