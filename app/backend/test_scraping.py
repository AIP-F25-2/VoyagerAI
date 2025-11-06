#!/usr/bin/env python3
"""
Test script for the integrated scraping functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.scraper import (
    scrape_bookmyshow_events,
    scrape_eventbrite_events, 
    scrape_europaticket_events,
    scrape_all_events
)

def test_bookmyshow():
    """Test BookMyShow scraping"""
    print("🧪 Testing BookMyShow scraping...")
    try:
        events = scrape_bookmyshow_events("Mumbai", limit=2)
        print(f"✅ BookMyShow: Found {len(events)} events")
        if events:
            print(f"   Sample: {events[0].get('title', 'No title')}")
        return True
    except Exception as e:
        print(f"❌ BookMyShow failed: {e}")
        return False

def test_eventbrite():
    """Test Eventbrite scraping"""
    print("🧪 Testing Eventbrite scraping...")
    try:
        events = scrape_eventbrite_events(months_ahead=1, limit=2)
        print(f"✅ Eventbrite: Found {len(events)} events")
        if events:
            print(f"   Sample: {events[0].get('title', 'No title')}")
        return True
    except Exception as e:
        print(f"❌ Eventbrite failed: {e}")
        return False

def test_europaticket():
    """Test EuropaTicket scraping"""
    print("🧪 Testing EuropaTicket scraping...")
    try:
        events = scrape_europaticket_events(limit=2)
        print(f"✅ EuropaTicket: Found {len(events)} events")
        if events:
            print(f"   Sample: {events[0].get('title', 'No title')}")
        return True
    except Exception as e:
        print(f"❌ EuropaTicket failed: {e}")
        return False

def test_all_sources():
    """Test scraping from all sources"""
    print("🧪 Testing all sources scraping...")
    try:
        events = scrape_all_events("Mumbai", bms_limit=1, eventbrite_limit=1, europaticket_limit=1)
        print(f"✅ All sources: Found {len(events)} total events")
        
        sources = {}
        for event in events:
            source = event.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        print(f"   Sources: {sources}")
        return True
    except Exception as e:
        print(f"❌ All sources failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting scraping integration tests...")
    print("=" * 50)
    
    tests = [
        test_bookmyshow,
        test_eventbrite, 
        test_europaticket,
        test_all_sources
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Integration successful!")
        return True
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
