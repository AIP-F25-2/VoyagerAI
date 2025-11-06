#!/usr/bin/env python3
"""
Test script for hotel functionality
"""

import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app
from app.models import db, Hotel
from app.services.hotels import hotel_csv_loader

def test_hotel_csv_loading():
    """Test CSV loading functionality"""
    print("🧪 Testing hotel CSV loading...")
    
    # Test CSV loader
    hotels = hotel_csv_loader.get_all_hotels(limit=5)
    print(f"✅ Loaded {len(hotels)} hotels from CSV")
    
    if hotels:
        print("\n📋 Sample hotel data:")
        for i, hotel in enumerate(hotels[:3], 1):
            print(f"{i}. {hotel['name']} - {hotel['city']} (Rating: {hotel['rating']})")
    
    # Test search functionality
    toronto_hotels = hotel_csv_loader.get_hotels_by_city("Toronto", limit=3)
    print(f"\n🏙️ Found {len(toronto_hotels)} hotels in Toronto")
    
    if toronto_hotels:
        print("Sample Toronto hotels:")
        for hotel in toronto_hotels:
            print(f"  - {hotel['name']} ({hotel['rating']}/10)")

def test_database_operations():
    """Test database operations"""
    print("\n🧪 Testing database operations...")
    
    app = create_app()
    with app.app_context():
        # Check if hotels table exists
        try:
            hotel_count = Hotel.query.count()
            print(f"✅ Database has {hotel_count} hotels")
            
            if hotel_count > 0:
                # Get a sample hotel
                sample_hotel = Hotel.query.first()
                print(f"📋 Sample hotel from DB: {sample_hotel.name} - {sample_hotel.city}")
        except Exception as e:
            print(f"❌ Database error: {e}")

def test_api_endpoints():
    """Test API endpoints"""
    print("\n🧪 Testing API endpoints...")
    
    app = create_app()
    with app.test_client() as client:
        # Test hotels endpoint
        response = client.get('/api/hotels?limit=3')
        if response.status_code == 200:
            data = response.get_json()
            print(f"✅ GET /api/hotels - Found {len(data.get('hotels', []))} hotels")
        else:
            print(f"❌ GET /api/hotels - Status: {response.status_code}")
        
        # Test hotels search endpoint
        response = client.get('/api/hotels/search?city=Toronto&limit=3')
        if response.status_code == 200:
            data = response.get_json()
            print(f"✅ GET /api/hotels/search - Found {len(data.get('hotels', []))} hotels")
        else:
            print(f"❌ GET /api/hotels/search - Status: {response.status_code}")
        
        # Test cities endpoint
        response = client.get('/api/hotels/cities')
        if response.status_code == 200:
            data = response.get_json()
            cities = data.get('cities', [])
            print(f"✅ GET /api/hotels/cities - Found {len(cities)} cities")
            if cities:
                print(f"   Sample cities: {', '.join(cities[:5])}")
        else:
            print(f"❌ GET /api/hotels/cities - Status: {response.status_code}")

if __name__ == "__main__":
    print("🚀 Testing VoyagerAI Hotel Functionality\n")
    
    try:
        test_hotel_csv_loading()
        test_database_operations()
        test_api_endpoints()
        
        print("\n🎉 All tests completed!")
        print("\n📚 Available hotel endpoints:")
        print("  GET /api/hotels - Get all hotels with filtering")
        print("  GET /api/hotels/search - Search hotels by city")
        print("  GET /api/hotels/cities - Get available cities")
        print("  GET /api/hotels/popular - Get popular hotels")
        print("  GET /api/hotels/<id> - Get hotel details")
        print("  GET /api/hotels/db - Get hotels from database")
        print("  POST /api/hotels/db - Create hotel in database")
        print("  PUT /api/hotels/db/<id> - Update hotel")
        print("  DELETE /api/hotels/db/<id> - Delete hotel")
        
    except Exception as e:
        print(f"💥 Test failed: {e}")
        sys.exit(1)
