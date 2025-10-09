#!/usr/bin/env python3
"""
london_scraper_final.py - Robust scraper for London events with multiple fallback strategies
"""

import requests, time, csv, sys
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import json
import random

# --- CONFIG ---
BASE = "https://www.europaticket.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://www.europaticket.com/",
    "Cache-Control": "no-cache",
}
OUT_CSV = "london_events_large.csv"
DELAY = 1.5
MAX_EVENTS = 5000

def soup(url, retries=3):
    """Fetch URL and parse with BeautifulSoup with retry logic."""
    for attempt in range(retries):
        try:
            # Add random delay to avoid being blocked
            time.sleep(random.uniform(0.5, 1.5))
            
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()

            
            
            # Check if we got a valid response
            if response.status_code == 200 and len(response.text) > 1000:
                return BeautifulSoup(response.text, "html.parser")
            else:
                print(f"[WARNING] Received short response for {url}")
                
        except Exception as e:
            if attempt < retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"[RETRY {attempt + 1}/{retries}] Failed to fetch {url}: {e}")
                print(f"[WAIT] Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"[ERROR] Failed to fetch {url} after {retries} attempts: {e}")
                return None
    return None

def get_london_events_robust():
    """Get London events using multiple strategies."""
    event_links = set()
    
    # Strategy 1: Main London city page
    london_urls = [
        f"{BASE}/en/city/london",
        f"{BASE}/en/city/london/",
        f"{BASE}/city/london",
        f"{BASE}/city/london/"
    ]
    
    # Strategy 2: London venue pages
    venue_urls = [
        f"{BASE}/en/venue/royal-opera-house",
        f"{BASE}/en/venue/royal-albert-hall",
        f"{BASE}/en/venue/barbican-centre",
        f"{BASE}/en/venue/southbank-centre",
        f"{BASE}/en/venue/royal-festival-hall",
        f"{BASE}/en/venue/wembley-stadium",
        f"{BASE}/en/venue/olympia-london",
        f"{BASE}/en/venue/albert-hall",
        f"{BASE}/en/venue/covent-garden",
        f"{BASE}/en/venue/west-end",
        f"{BASE}/en/venue/globe-theatre",
        f"{BASE}/en/venue/old-vic",
        f"{BASE}/en/venue/national-theatre",
        f"{BASE}/en/venue/lyceum-theatre",
        f"{BASE}/en/venue/palladium"
    ]
    
    # Strategy 3: Search URLs for London events
    search_urls = [
        f"{BASE}/en/search?city=london",
        f"{BASE}/en/calendar?city=london",
        f"{BASE}/search?q=london",
        f"{BASE}/en/events?city=london",
        f"{BASE}/en/search?q=west+end",
        f"{BASE}/en/search?q=royal+opera+house",
        f"{BASE}/en/search?q=royal+albert+hall"
    ]
    
    all_urls = london_urls + venue_urls + search_urls
    
    print(f"[INFO] Checking {len(all_urls)} URLs for London events...")
    
    for i, url in enumerate(all_urls, 1):
        print(f"[{i}/{len(all_urls)}] Checking: {url}")
        
        sp = soup(url)
        if not sp:
            continue
            
        # Debug: Check what we actually got
        page_text = sp.get_text().lower()
        print(f"  Page length: {len(page_text)} characters")
        print(f"  Contains 'london': {'london' in page_text}")
        print(f"  Contains 'event': {'event' in page_text}")
        
        # Multiple selectors to find event links
        selectors = [
            'a[href*="/event/"]',
            'a[href*="/en/event/"]', 
            '.event a',
            '.card a',
            '.item a',
            '.event-item a',
            '.event-card a',
            '.performance a',
            '.show a',
            '.concert a',
            'a[href*="event"]',
            'a[href*="concert"]',
            'a[href*="performance"]'
        ]
        
        found_links = 0
        for selector in selectors:
            links = sp.select(selector)
            for link in links:
                href = link.get('href')
                if href and ('/event/' in href or 'event' in href.lower()):
                    clean_href = href.split('#')[0]
                    full_url = urljoin(BASE, clean_href)
                    
                    # Check if it's a valid event URL
                    if full_url not in event_links and 'europaticket.com' in full_url:
                        event_links.add(full_url)
                        found_links += 1
        
        print(f"  Found {found_links} new event links on this page")
        
        # Also look for any links that might lead to more events
        all_links = sp.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text().lower()
            
            # Look for London-related links
            if any(keyword in href.lower() or keyword in text for keyword in ['london', 'event', 'concert', 'performance', 'west end', 'royal opera', 'royal albert']):
                clean_href = href.split('#')[0]
                full_url = urljoin(BASE, clean_href)
                
                if ('/event/' in full_url or 'event' in full_url.lower()) and full_url not in event_links:
                    event_links.add(full_url)
                    found_links += 1
        
        print(f"  Total new links found: {found_links}")
        
        # If we found many links, we might want to check pagination
        if found_links > 10:
            print(f"  [INFO] Found many links, checking for pagination...")
            pagination_selectors = [
                'a[href*="page="]',
                '.pagination a',
                '.page-numbers a', 
                '.pager a',
                'a[href*="next"]',
                'a[href*="more"]'
            ]
            
            for pag_selector in pagination_selectors:
                pag_links = sp.select(pag_selector)
                for pag_link in pag_links[:2]:  # Only check first 2 pagination links
                    pag_href = pag_link.get('href')
                    if pag_href:
                        pag_url = urljoin(BASE, pag_href)
                        if pag_url not in all_urls and 'page=' in pag_url:
                            all_urls.append(pag_url)
    
    event_list = list(event_links)
    print(f"\n[SUCCESS] Found {len(event_list)} unique London event URLs")
    
    # If we still don't have enough, try a different approach
    if len(event_list) < 50:
        print("[INFO] Low event count, trying alternative approach...")
        return get_london_events_alternative()
    
    return event_list[:MAX_EVENTS]

def get_london_events_alternative():
    """Alternative method to find London events."""
    event_links = set()
    
    print("[INFO] Trying alternative event discovery...")
    
    # Try to find events through search or API endpoints
    search_terms = ['london', 'west end london', 'royal opera house london', 'royal albert hall london', 'barbican london', 'southbank london']
    
    for term in search_terms:
        search_url = f"{BASE}/en/search?q={term}"
        print(f"[INFO] Searching for: {term}")
        
        sp = soup(search_url)
        if sp:
            links = sp.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if '/event/' in href:
                    full_url = urljoin(BASE, href.split('#')[0])
                    event_links.add(full_url)
    
    # Try calendar view
    calendar_url = f"{BASE}/en/calendar"
    print(f"[INFO] Checking calendar: {calendar_url}")
    
    sp = soup(calendar_url)
    if sp:
        links = sp.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            text = link.get_text().lower()
            if '/event/' in href and 'london' in text:
                full_url = urljoin(BASE, href.split('#')[0])
                event_links.add(full_url)
    
    event_list = list(event_links)
    print(f"[INFO] Alternative method found {len(event_list)} events")
    
    return event_list[:MAX_EVENTS]

def clean_text(text):
    """Clean extracted text."""
    if not text:
        return None
    
    text = re.sub(r'\s+', ' ', text.strip())
    unwanted_patterns = [
        r'ENDEITFRESRUJPRO.*?CALL NOW:.*?\d+',
        r'Shop now.*?tickets:.*?£',
        r'PHONE.*?WHATSAPP.*?CALL NOW:.*?\d+',
        r'MenuMenu',
        r'CALL NOW:.*?\d+',
        r'Buy Official Tickets.*?Visit our website.*?',
        r'For more information.*?contact us by phone.*?',
    ]
    
    for pattern in unwanted_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    return text.strip() if text.strip() else None

def extract_venue_from_description(description):
    """Extract venue from description text."""
    if not description:
        return None
    
    london_venues = [
        'Royal Opera House', 'Royal Albert Hall', 'Barbican Centre', 'Southbank Centre',
        'Royal Festival Hall', 'Wembley Stadium', 'Olympia London', 'Covent Garden',
        'Globe Theatre', 'Old Vic', 'National Theatre', 'Lyceum Theatre', 'Palladium',
        'West End', 'Her Majesty\'s Theatre', 'Prince of Wales Theatre', 'Adelphi Theatre',
        'Apollo Theatre', 'Cambridge Theatre', 'Dominion Theatre', 'Fortune Theatre',
        'Garrick Theatre', 'Gielgud Theatre', 'Haymarket Theatre', 'Novello Theatre',
        'Phoenix Theatre', 'Piccadilly Theatre', 'Playhouse Theatre', 'Savoy Theatre',
        'Shaftesbury Theatre', 'St. Martin\'s Theatre', 'Theatre Royal Drury Lane',
        'Vaudeville Theatre', 'Wyndham\'s Theatre', 'Saddler\'s Wells', 'Regent\'s Park Open Air Theatre'
    ]
    
    for venue in london_venues:
        if venue.lower() in description.lower():
            return venue
    
    at_patterns = [
        r'at\s+([^,\.]+?)(?:\s*,|\s*\.|\s*in\s+London|\s*London)',
        r'at\s+([^,\.]+?)(?:\s*\.|\s*,|\s*London)',
        r'at\s+([A-Z][^,\.]+?)(?:\s*,|\s*\.)',
    ]
    
    for pattern in at_patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            venue = match.group(1).strip()
            venue = re.sub(r'\s+', ' ', venue)
            if len(venue) > 3 and not venue.lower().startswith('the ') and venue != 'Venue':
                return venue
    
    return None

def extract_price_from_description(description):
    """Extract price from description text."""
    if not description:
        return None
    
    price_patterns = [
        r'from\s*£\s*(\d+(?:\.\d{2})?)',
        r'£\s*(\d+(?:\.\d{2})?)',
        r'(\d+(?:\.\d{2})?)\s*£',
        r'starting\s*from\s*£\s*(\d+(?:\.\d{2})?)',
        r'prices?\s*from\s*£\s*(\d+(?:\.\d{2})?)',
        r'£(\d+)',
        r'(\d+)\s*£',
        r'from\s*€\s*(\d+(?:\.\d{2})?)',
        r'€\s*(\d+(?:\.\d{2})?)',
        r'(\d+(?:\.\d{2})?)\s*€',
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            price = match.group(1)
            if '£' in pattern:
                return f"£{price}"
            else:
                return f"€{price}"
    
    return None

def extract_time_from_page(sp):
    """Extract time information from page."""
    time_patterns = [
        r'\b(\d{1,2}:\d{2})\b',
        r'\b(\d{1,2}:\d{2}\s*[AP]M)\b',
        r'\b(\d{1,2}:\d{2}\s*[ap]m)\b',
    ]
    
    time_elem = sp.find('time')
    if time_elem:
        time_attr = time_elem.get('datetime')
        if time_attr and 'T' in time_attr:
            time_part = time_attr.split('T')[1].split('+')[0].split('-')[0]
            if len(time_part) >= 5:
                return time_part
    
    page_text = sp.get_text()
    for pattern in time_patterns:
        match = re.search(pattern, page_text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def parse_event(url):
    """Extract event details with improved parsing."""
    sp = soup(url)
    if not sp:
        return {}
    
    result = {"url": url}
    
    # Title
    title = None
    title_selectors = [
        'h1',
        '.event-title',
        '.title',
        'meta[property="og:title"]',
        'title'
    ]
    
    for selector in title_selectors:
        if selector.startswith('meta'):
            elem = sp.select_one(selector)
            if elem and elem.get('content'):
                title = elem.get('content')
                break
        else:
            elem = sp.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                break
    
    result["title"] = clean_text(title)
    
    # Description
    desc = None
    desc_selectors = [
        '.description',
        '.event-description',
        '.summary',
        'meta[name="description"]',
        '.content p',
        '.event-content p'
    ]
    
    for selector in desc_selectors:
        if selector.startswith('meta'):
            elem = sp.select_one(selector)
            if elem and elem.get('content'):
                desc = elem.get('content')
                break
        else:
            elem = sp.select_one(selector)
            if elem:
                desc = elem.get_text(strip=True)
                break
    
    result["description"] = clean_text(desc)
    
    # Venue
    venue = extract_venue_from_description(desc)
    
    if not venue:
        venue_link = sp.find('a', href=re.compile(r'/venue/|/location/'))
        if venue_link:
            venue = venue_link.get_text(strip=True)
        
        if not venue:
            venue_selectors = [
                '.venue',
                '.location',
                '.place',
                '.theatre',
                '.opera',
                '.hall',
                '.arena',
                '.stadium',
                '[class*="venue"]',
                '[class*="location"]'
            ]
            
            for selector in venue_selectors:
                elem = sp.select_one(selector)
                if elem:
                    venue = elem.get_text(strip=True)
                    break
    
    result["venue"] = clean_text(venue)
    
    # Date and Time
    date = None
    time_val = None
    
    # Try structured data
    json_scripts = sp.find_all('script', type='application/ld+json')
    for script in json_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                if 'startDate' in data:
                    start_date = data['startDate']
                    if 'T' in start_date:
                        date_part, time_part = start_date.split('T')
                        date = date_part
                        time_val = time_part.split('+')[0].split('-')[0]
                    else:
                        date = start_date
                elif 'datePublished' in data:
                    date = data['datePublished']
        except:
            continue
    
    # Try time elements
    if not date:
        time_elem = sp.find('time')
        if time_elem:
            datetime_attr = time_elem.get('datetime')
            if datetime_attr:
                if 'T' in datetime_attr:
                    date_part, time_part = datetime_attr.split('T')
                    date = date_part
                    if not time_val:
                        time_val = time_part.split('+')[0].split('-')[0]
                else:
                    date = datetime_attr
            else:
                date = time_elem.get_text(strip=True)
    
    # Try date-related selectors
    if not date:
        date_selectors = [
            '.date',
            '.event-date',
            '.performance-date',
            '.show-date',
            '[class*="date"]'
        ]
        
        for selector in date_selectors:
            elem = sp.select_one(selector)
            if elem:
                date = elem.get_text(strip=True)
                break
    
    # Look for date patterns in text
    if not date:
        page_text = sp.get_text()
        date_patterns = [
            r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}',
            r'\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}',
            r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*\s+\d{1,2}[a-z]*\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',
            r'\d{1,2}\.\d{1,2}\.\d{4}',
            r'\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                date = match.group(0)
                break
    
    # Extract time if not already found
    if not time_val:
        time_val = extract_time_from_page(sp)
    
    result["date"] = clean_text(date)
    result["time"] = clean_text(time_val)
    
    # Price
    price = extract_price_from_description(desc)
    
    if not price:
        price_selectors = [
            '.price',
            '.ticket-price',
            '.cost',
            '[class*="price"]'
        ]
        
        for selector in price_selectors:
            elem = sp.select_one(selector)
            if elem:
                price = elem.get_text(strip=True)
                break
        
        if not price:
            page_text = sp.get_text()
            price_patterns = [
                r'£\s*\d+(?:\.\d{2})?',
                r'\d+(?:\.\d{2})?\s*£',
                r'from\s*£\s*\d+',
                r'starting\s*from\s*£\s*\d+',
                r'€\s*\d+(?:\.\d{2})?',
                r'\d+(?:\.\d{2})?\s*€',
                r'from\s*€\s*\d+',
                r'\$\s*\d+(?:\.\d{2})?',
                r'\d+(?:\.\d{2})?\s*\$'
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    price = match.group(0)
                    break
    
    result["price"] = clean_text(price)
    
    return result

def save_results(results, filename):
    """Save results to CSV file."""
    if not results:
        return False
    
    df = pd.DataFrame(results)
    cols = ["title", "date", "time", "price", "venue", "url", "description"]
    df = df.reindex(columns=cols)
    
    try:
        df.to_csv(filename, index=False, quoting=csv.QUOTE_NONNUMERIC, encoding='utf-8')
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save CSV: {e}")
        return False

def main():
    print(f"[INFO] Starting ROBUST large-scale London events scraping")
    print(f"[INFO] Target: Up to {MAX_EVENTS} events")
    print(f"[INFO] Delay between requests: {DELAY}s")
    print("="*80)
    
    # Get event URLs using robust method
    print("[INFO] Discovering London events using multiple strategies...")
    event_urls = get_london_events_robust()
    
    if not event_urls:
        print("[ERROR] No events found using any method!")
        return
    
    print(f"[INFO] Found {len(event_urls)} unique London event URLs")
    
    results = []
    failed_count = 0
    start_time = time.time()
    
    for i, url in enumerate(event_urls, 1):
        try:
            print(f"\n[{i}/{len(event_urls)}] Processing: {url}")
            event_data = parse_event(url)
            
            if event_data and event_data.get('title'):
                results.append(event_data)
                print(f"  ✓ Title: {event_data.get('title')}")
                print(f"  ✓ Venue: {event_data.get('venue') or 'N/A'}")
                print(f"  ✓ Date: {event_data.get('date') or 'N/A'}")
                print(f"  ✓ Time: {event_data.get('time') or 'N/A'}")
                print(f"  ✓ Price: {event_data.get('price') or 'N/A'}")
                
                # Show progress every 25 events
                if i % 25 == 0:
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    print(f"\n[PROGRESS] Processed {i}/{len(event_urls)} events ({len(results)} successful, {failed_count} failed)")
                    print(f"[RATE] {rate:.1f} events/second")
                    if rate > 0:
                        print(f"[ETA] {(len(event_urls) - i) / rate / 60:.1f} minutes remaining")
                    
                    # Save intermediate results
                    temp_filename = f"london_events_temp_{i}.csv"
                    if save_results(results, temp_filename):
                        print(f"[BACKUP] Saved {len(results)} events to {temp_filename}")
            else:
                failed_count += 1
                print(f"  ✗ Failed to extract data")
                
        except KeyboardInterrupt:
            print(f"\n[INTERRUPTED] Scraping stopped by user at event {i}")
            break
        except Exception as e:
            failed_count += 1
            print(f"  ✗ Error processing event: {e}")
        
        time.sleep(DELAY)
    
    # Final save
    print("\n" + "="*80)
    print("[INFO] SCRAPING COMPLETED")
    print("="*80)
    
    if results:
        if save_results(results, OUT_CSV):
            print(f"[SUCCESS] {len(results)} London events saved to {OUT_CSV}")
            
            # Print summary statistics
            elapsed_total = time.time() - start_time
            print(f"\n[STATISTICS]")
            print(f"Total events processed: {len(event_urls)}")
            print(f"Successfully scraped: {len(results)}")
            print(f"Failed extractions: {failed_count}")
            print(f"Success rate: {len(results)/len(event_urls)*100:.1f}%")
            print(f"Total time: {elapsed_total/60:.1f} minutes")
            if elapsed_total > 0:
                print(f"Average rate: {len(event_urls)/elapsed_total:.1f} events/second")
            
            # Show sample of results
            print(f"\n[SAMPLE RESULTS - First 5 events]")
            for i, row in enumerate(pd.DataFrame(results).head().iterrows(), 1):
                _, data = row
                print(f"{i}. {data['title'] or 'N/A'}")
                print(f"   Venue: {data['venue'] or 'N/A'}")
                print(f"   Date: {data['date'] or 'N/A'}")
                print(f"   Time: {data['time'] or 'N/A'}")
                print(f"   Price: {data['price'] or 'N/A'}")
                print()
        else:
            print(f"[ERROR] Failed to save final results to {OUT_CSV}")
    else:
        print("[WARNING] No valid event data extracted")

if __name__ == "__main__":
    main()
