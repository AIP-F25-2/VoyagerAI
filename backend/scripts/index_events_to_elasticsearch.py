#!/usr/bin/env python3
"""
Script to index all existing events into Elasticsearch.
Run this after setting up Elasticsearch to populate the index.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, Event
from app.services.csv_loader import csv_loader
from app.services.elasticsearch_service import es_service

def main():
    """Index all events into Elasticsearch."""
    app = create_app()
    
    with app.app_context():
        # Check if Elasticsearch is available
        if not es_service.is_available():
            print("❌ Elasticsearch is not available!")
            print("   Make sure Elasticsearch is running and ELASTICSEARCH_URL is set correctly.")
            return 1
        
        # Create index if it doesn't exist
        print("📋 Creating Elasticsearch index...")
        if not es_service.create_index():
            print("❌ Failed to create index")
            return 1
        
        print("✅ Index created/verified")
        
        # Get all events from database
        print("\n📊 Fetching events from database...")
        db_events = Event.query.all()
        print(f"   Found {len(db_events)} events in database")
        
        # Format and index database events
        indexed_db = 0
        for event in db_events:
            formatted_event = {
                "id": f"eb_{event.id}",
                "name": event.title,
                "url": event.url,
                "dates": {
                    "start": {
                        "localDate": event.date.isoformat() if event.date else "2024-01-01",
                        "localTime": event.time.strftime("%H:%M") if event.time else "19:00"
                    }
                },
                "images": [{"url": "/placeholder.jpg"}],
                "_embedded": {
                    "venues": [{
                        "name": event.venue or "TBA",
                        "city": {"name": event.city or "Unknown"}
                    }]
                },
                "priceRanges": [{"min": 0, "max": 100}] if event.price else None,
                "source": "eventbrite"
            }
            if es_service.index_event(formatted_event):
                indexed_db += 1
        
        print(f"✅ Indexed {indexed_db} database events")
        
        # Get CSV events
        print("\n📄 Loading CSV events...")
        csv_events = csv_loader.load_all_csv_events()
        print(f"   Found {len(csv_events)} CSV events")
        
        csv_indexed = es_service.bulk_index_events(csv_events)
        print(f"✅ Indexed {csv_indexed} CSV events")
        
        total_indexed = indexed_db + csv_indexed
        print(f"\n🎉 Successfully indexed {total_indexed} total events!")
        
        # Show stats
        stats = es_service.get_index_stats()
        print(f"\n📊 Index Statistics:")
        print(f"   Total events in index: {stats.get('total_events', 0)}")
        
        return 0

if __name__ == "__main__":
    sys.exit(main())

