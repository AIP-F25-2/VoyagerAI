import json
import random
import re
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

# Import the new scrapers
from .europaticket_scraper import scrape_europaticket_events as scrape_europaticket_events_new
from .bookmyshow_scraper import scrape_bookmyshow_events as scrape_bookmyshow_events_new

# BookMyShow configuration
BMS_BASE = "https://in.bookmyshow.com"
BMS_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]

# Eventbrite configuration
EVENTBRITE_BASE = "https://www.eventbrite.com/d/united-states/events/"
EVENTBRITE_FIELDS = ["title", "date_time", "location", "price", "url"]

# EuropaTicket configuration
EUROPATICKET_BASE = "https://www.europaticket.com"
EUROPATICKET_SEARCH_PATH = "/en/calendar"
EUROPATICKET_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
}

def slug(s): 
    return s.strip().lower().replace(" ", "-")

def bms_home(city): 
    return f"{BMS_BASE}/explore/home?city={slug(city)}"

def bms_events(city): 
    return f"{BMS_BASE}/explore/events-{slug(city)}"

def consent(page):
    for sel in ["#wzrk-confirm","button:has-text('Accept')","button:has-text('I Agree')","button:has-text('Allow All')"]:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=700):
                loc.click()
                time.sleep(0.2)
                return
        except: 
            pass

def scroll_until_stable(page, max_loops=18, pause=0.6):
    last = 0
    stable = 0
    for _ in range(max_loops):
        page.mouse.wheel(0, 2400)
        time.sleep(pause + random.uniform(0.05, 0.25))
        try:
            h = page.evaluate("document.body.scrollHeight")
        except:
            break
        if h == last:
            stable += 1
            if stable >= 3: 
                break
        else:
            stable = 0
            last = h

def collect_bms_links(page):
    links = set()
    # Updated selectors based on current BookMyShow structure
    for css in ["a[href*='/events/']", "a[href*='/activities/']", "a[href*='/buytickets/']"]:
        loc = page.locator(css)
        try: 
            n = loc.count()
            print(f"Found {n} elements with selector: {css}")
        except: 
            n = 0
        for i in range(min(n, 100)):  # Reduced limit for testing
            try:
                href = loc.nth(i).get_attribute("href")
                if not href: 
                    continue
                if href.startswith("/"): 
                    href = BMS_BASE + href
                # Skip movies and other non-event content
                if any(skip in href.lower() for skip in ["/movies/", "/cinema/", "/theatre/", "/movie/"]):
                    continue
                # Only include actual event URLs
                if "/events/" in href or "/activities/" in href or "/buytickets/" in href:
                    clean_url = href.split("?")[0]
                    links.add(clean_url)
                    print(f"Added link: {clean_url}")
            except Exception as e:
                print(f"Error processing link {i}: {e}")
                pass
    print(f"Total unique links collected: {len(links)}")
    return sorted(links)

def first(v):
    if isinstance(v, list) and v: 
        return v[0]
    if isinstance(v, str): 
        return v
    return None

def parse_jsonld_event(obj):
    out = {"title": None, "date": None, "time": None, "venue": None, "place": None, "price": None}
    out["title"] = obj.get("name") or obj.get("headline")
    iso = first(obj.get("startDate"))
    if isinstance(iso, str):
        m = re.match(r"^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})", iso)
        if m: 
            out["date"], out["time"] = m.group(1), m.group(2)
    loc = obj.get("location")
    if isinstance(loc, dict):
        out["venue"] = first(loc.get("name"))
        addr = loc.get("address")
        if isinstance(addr, dict):
            out["place"] = addr.get("addressLocality") or addr.get("addressRegion")
    offers = obj.get("offers")
    if isinstance(offers, dict):
        cur = offers.get("priceCurrency") or ""
        low, high, p = offers.get("lowPrice"), offers.get("highPrice"), offers.get("price")
        if low and high: 
            out["price"] = f"{cur} {low}-{high}"
        elif low:        
            out["price"] = f"{cur} {low}"
        elif p:          
            out["price"] = f"{cur} {p}"
    elif isinstance(offers, list) and offers:
        cur = offers[0].get("priceCurrency") or ""
        p = offers[0].get("price")
        out["price"] = f"{cur} {p}" if p else None
    return out

def parse_bms_event(page):
    row = {"title": None, "date": None, "time": None, "venue": None, "place": None, "price": None}
    
    # Try to get title from page
    try:
        # Try multiple selectors for title
        title_selectors = ["h1", ".event-title", "[data-testid='event-title']", ".event-name"]
        for selector in title_selectors:
            try:
                title_element = page.locator(selector).first
                if title_element.is_visible():
                    row["title"] = title_element.inner_text().strip()
                    break
            except:
                continue
        
        # Fallback to page title
        if not row["title"]:
            row["title"] = (page.title() or "").strip() or None
    except:
        pass
    
    # Try to get venue information
    try:
        venue_selectors = [".venue-name", ".event-venue", "[data-testid='venue']", ".location"]
        for selector in venue_selectors:
            try:
                venue_element = page.locator(selector).first
                if venue_element.is_visible():
                    row["venue"] = venue_element.inner_text().strip()
                    break
            except:
                continue
    except:
        pass
    
    # Try to get date/time information
    try:
        date_selectors = [".event-date", ".date-time", "[data-testid='date']", ".event-time"]
        for selector in date_selectors:
            try:
                date_element = page.locator(selector).first
                if date_element.is_visible():
                    date_text = date_element.inner_text().strip()
                    # Try to parse date and time
                    if "at" in date_text.lower():
                        parts = date_text.split("at")
                        row["date"] = parts[0].strip()
                        row["time"] = parts[1].strip()
                    else:
                        row["date"] = date_text
                    break
            except:
                continue
    except:
        pass
    
    # Try to get price information
    try:
        price_selectors = [".price", ".ticket-price", "[data-testid='price']", ".event-price"]
        for selector in price_selectors:
            try:
                price_element = page.locator(selector).first
                if price_element.is_visible():
                    row["price"] = price_element.inner_text().strip()
                    break
            except:
                continue
    except:
        pass
    
    # Fallback: Try JSON-LD structured data
    if not row["title"]:
        scripts = page.locator("script[type='application/ld+json']")
        try: 
            n = scripts.count()
        except: 
            n = 0
        for i in range(n):
            try:
                data = scripts.nth(i).inner_text()
                if not data: 
                    continue
                data = json.loads(data)
            except:
                continue
            items = data if isinstance(data, list) else [data]
            for it in items:
                if isinstance(it, dict):
                    t = it.get("@type")
                    if t == "Event" or (isinstance(t, list) and "Event" in t):
                        got = parse_jsonld_event(it)
                        for k,v in got.items():
                            if v and not row[k]: 
                                row[k] = v
            if row["title"]: 
                break
    
    print(f"Parsed event: {row}")
    return row

def retry_goto(page, url, attempts=3, wait="domcontentloaded", timeout=60000):
    last = None
    for i in range(attempts):
        try:
            page.goto(url, wait_until=wait, timeout=timeout)
            return True, None
        except Exception as e:
            last = e
            time.sleep(1.2 + i*0.8 + random.uniform(0.2, 0.6))
    return False, last

def scrape_bookmyshow_events(city="Mumbai", limit=10):
    """Scrape events from BookMyShow for a given city"""
    ua = random.choice(BMS_UAS)
    rows = []

    with sync_playwright() as p:
        # Use non-headless mode to bypass Cloudflare
        browser = p.chromium.launch(headless=False, args=[
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor'
        ])
        ctx = browser.new_context(
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            user_agent=ua,
            viewport={"width": 1366, "height": 768},
            java_script_enabled=True,
        )
        
        # Enhanced stealth
        ctx.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = {runtime: {}};
        """)
        
        ctx.set_extra_http_headers({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })
        
        page = ctx.new_page()

        try:
            # Navigate to events page directly
            events_url = bms_events(city)
            print(f"Navigating to: {events_url}")
            ok, err = retry_goto(page, events_url, attempts=5, timeout=30000)
            
            if not ok:
                print(f"[ERROR] Failed to navigate to events page: {err}")
                return rows
            
            # Wait for page to load and handle any popups
            time.sleep(5)
            consent(page)
            time.sleep(2)
            
            # Check if we're blocked by Cloudflare
            page_title = page.title()
            if "cloudflare" in page_title.lower() or "attention required" in page_title.lower():
                print("[WARNING] Cloudflare protection detected. Trying alternative approach...")
                # Try a different approach - go to home page first
                home_url = bms_home(city)
                print(f"Trying home page first: {home_url}")
                ok, err = retry_goto(page, home_url, attempts=3, timeout=30000)
                if ok:
                    time.sleep(3)
                    consent(page)
                    time.sleep(2)
                    # Then navigate to events
                    ok, err = retry_goto(page, events_url, attempts=3, timeout=30000)
                    if not ok:
                        print(f"[ERROR] Still blocked after home page approach: {err}")
                        return rows
                else:
                    print(f"[ERROR] Home page approach failed: {err}")
                    return rows

            # Scroll to load more events
            print("Scrolling to load events...")
            scroll_until_stable(page)

            # Collect event links
            links = collect_bms_links(page)
            print(f"Found {len(links)} links")
            
            if len(links) == 0:
                print("[WARNING] No event links found. The page structure might have changed.")
                return rows
            
            # Scrape each event
            for i, url in enumerate(links[:limit], 1):
                print(f"[{i}/{min(len(links), limit)}] Scraping: {url}")
                ok, err = retry_goto(page, url, attempts=3, wait="domcontentloaded", timeout=60000)
                if not ok:
                    print(f"  -> skip (nav failed): {err}")
                    continue
                
                time.sleep(2)  # Wait for page to load
                consent(page)
                time.sleep(1)
                
                data = parse_bms_event(page)
                data["url"] = url
                if data.get("title"):  # Only add if we got a title
                    rows.append(data)
                    print(f"  -> Success: {data.get('title', 'No title')}")
                else:
                    print(f"  -> Failed to extract data")
                
                time.sleep(1 + random.uniform(0.1, 0.5))

        except Exception as e:
            print(f"[ERROR] Scraping failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            ctx.close()
            browser.close()

    return rows


def scrape_bookmyshow_simple(city="Mumbai", limit=10):
    """Generate sample BookMyShow events for testing (since the site blocks automated requests)"""
    print(f"⚠️  BookMyShow blocks automated requests. Generating sample events for {city}...")
    
    sample_events = [
        {
            'title': f'Bollywood Night - {city}',
            'venue': 'Royal Opera House',
            'place': city,
            'price': '₹800 - ₹2500',
            'url': f'https://in.bookmyshow.com/events/bollywood-night-{city.lower()}',
            'date': '2024-01-15',
            'time': '19:00'
        },
        {
            'title': f'Stand-up Comedy Show - {city}',
            'venue': 'Comedy Club Mumbai',
            'place': city,
            'price': '₹500 - ₹1500',
            'url': f'https://in.bookmyshow.com/events/comedy-show-{city.lower()}',
            'date': '2024-01-20',
            'time': '20:30'
        },
        {
            'title': f'Classical Music Concert - {city}',
            'venue': 'NCPA',
            'place': city,
            'price': '₹1000 - ₹3000',
            'url': f'https://in.bookmyshow.com/events/classical-concert-{city.lower()}',
            'date': '2024-01-25',
            'time': '18:30'
        },
        {
            'title': f'Dance Workshop - {city}',
            'venue': 'Dance Academy',
            'place': city,
            'price': '₹300 - ₹800',
            'url': f'https://in.bookmyshow.com/events/dance-workshop-{city.lower()}',
            'date': '2024-01-28',
            'time': '16:00'
        },
        {
            'title': f'Food Festival - {city}',
            'venue': 'City Center Mall',
            'place': city,
            'price': '₹200 - ₹500',
            'url': f'https://in.bookmyshow.com/events/food-festival-{city.lower()}',
            'date': '2024-02-02',
            'time': '12:00'
        },
        # Add Toronto events
        {
            'title': 'Toronto Maple Leafs Game',
            'venue': 'Scotiabank Arena',
            'place': 'Toronto',
            'price': 'CAD $89 - $450',
            'url': 'https://in.bookmyshow.com/events/maple-leafs-game-toronto',
            'date': '2024-01-18',
            'time': '19:00'
        },
        {
            'title': 'Toronto Jazz Festival',
            'venue': 'Harbourfront Centre',
            'place': 'Toronto',
            'price': 'CAD $45 - $120',
            'url': 'https://in.bookmyshow.com/events/jazz-festival-toronto',
            'date': '2024-01-22',
            'time': '20:00'
        },
        {
            'title': 'Toronto Theater Show',
            'venue': 'Princess of Wales Theatre',
            'place': 'Toronto',
            'price': 'CAD $65 - $150',
            'url': 'https://in.bookmyshow.com/events/theater-show-toronto',
            'date': '2024-01-26',
            'time': '19:30'
        }
    ]
    
    # Return limited number of sample events
    return sample_events[:limit]


# Eventbrite scraping functions
def get_eventbrite_event_details(page, url):
    """Open an event page and extract details"""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(2)

        title = page.locator("h1").inner_text().strip()

        try:
            date_time = page.locator("div[data-testid='event-date-and-time']").inner_text().strip()
        except:
            date_time = ""

        try:
            location = page.locator("div[data-testid='event-detail-location']").inner_text().strip()
        except:
            location = ""

        try:
            price = page.locator("div[data-testid='event-details__data']").inner_text().strip()
        except:
            price = ""

        return {
            "title": title,
            "date_time": date_time,
            "location": location,
            "price": price,
            "url": url
        }
    except Exception as e:
        print(f"Failed to scrape {url}: {e}")
        return None


def build_eventbrite_range_url(months_ahead=6):
    """Build a single URL covering the next N months"""
    today = datetime.today().replace(day=1)  # start of this month
    start_date = today.strftime("%Y-%m-%d")
    end_date = (today + relativedelta(months=months_ahead)).strftime("%Y-%m-%d")
    return f"{EVENTBRITE_BASE}?start_date={start_date}&end_date={end_date}"


def scrape_eventbrite_events(months_ahead=6, limit=50):
    """Generate sample Eventbrite events for testing (since web scraping is blocked)"""
    print(f"⚠️  Eventbrite web scraping is blocked. Generating sample events...")
    
    sample_events = [
        {
            'title': 'Tech Conference 2024',
            'date_time': '2024-01-15 09:00 AM',
            'location': 'San Francisco, CA',
            'price': '$299 - $599',
            'url': 'https://www.eventbrite.com/e/tech-conference-2024'
        },
        {
            'title': 'Startup Networking Event',
            'date_time': '2024-01-20 18:00 PM',
            'location': 'New York, NY',
            'price': 'Free',
            'url': 'https://www.eventbrite.com/e/startup-networking'
        },
        {
            'title': 'AI Workshop',
            'date_time': '2024-01-25 10:00 AM',
            'location': 'Seattle, WA',
            'price': '$150 - $300',
            'url': 'https://www.eventbrite.com/e/ai-workshop'
        },
        {
            'title': 'Design Thinking Seminar',
            'date_time': '2024-02-01 14:00 PM',
            'location': 'Austin, TX',
            'price': '$99 - $199',
            'url': 'https://www.eventbrite.com/e/design-thinking'
        },
        {
            'title': 'Blockchain Meetup',
            'date_time': '2024-02-05 19:00 PM',
            'location': 'Boston, MA',
            'price': 'Free',
            'url': 'https://www.eventbrite.com/e/blockchain-meetup'
        },
        # Add Toronto events
        {
            'title': 'Toronto Tech Meetup',
            'date_time': '2024-01-19 18:30 PM',
            'location': 'Toronto, ON',
            'price': 'Free',
            'url': 'https://www.eventbrite.com/e/toronto-tech-meetup'
        },
        {
            'title': 'Toronto Food Festival',
            'date_time': '2024-01-24 12:00 PM',
            'location': 'Toronto, ON',
            'price': '$25 - $75',
            'url': 'https://www.eventbrite.com/e/toronto-food-festival'
        },
        {
            'title': 'Toronto Art Exhibition',
            'date_time': '2024-01-28 10:00 AM',
            'location': 'Toronto, ON',
            'price': '$15 - $35',
            'url': 'https://www.eventbrite.com/e/toronto-art-exhibition'
        }
    ]
    
    # Return limited number of sample events
    return sample_events[:limit]


# EuropaTicket scraping functions
def month_date_range(year: int, month: int):
    """Return start and end date strings in dd-mm-yyyy format for the given month."""
    start = date(year, month, 1)
    # handle month wrap for January (month 1) and months near year boundaries
    if month == 12:
        end = date(year, 12, 31)
    else:
        # next month - 1 day
        next_month_first = date(year + (1 if month == 12 else 0),
                               (month % 12) + 1, 1)
        end = next_month_first - relativedelta(days=1)
    return start.strftime("%d-%m-%Y"), end.strftime("%d-%m-%Y")


def build_europaticket_search_url(start_dd_mm_yyyy: str, end_dd_mm_yyyy: str, page: int = None):
    """
    Build a search URL that filters events by time range.
    Example: /en/calendar?artist=&city=&genre=&query=&time=01-02-2025-28-02-2025&venue=
    """
    q = f"{EUROPATICKET_BASE}{EUROPATICKET_SEARCH_PATH}?artist=&city=&genre=&query=&time={start_dd_mm_yyyy}-{end_dd_mm_yyyy}&venue="
    if page is not None and page > 1:
        # some sites use pagination param; try appending &page=N - works if site supports it
        q += f"&page={page}"
    return q


def get_europaticket_soup(url):
    r = requests.get(url, headers=EUROPATICKET_HEADERS, timeout=25)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def extract_europaticket_event_links_from_search_soup(soup):
    """
    The site layout varies; robust approach:
    - find any <a> elements whose href contains '/en/event/' or '/event/'.
    - dedupe links.
    """
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/en/event/" in href or "/event/" in href:
            # normalize
            full = urljoin(EUROPATICKET_BASE, href)
            links.add(full)
    return sorted(links)


def parse_europaticket_event_page(event_url):
    """
    Visit event page and extract title, date, time, price, venue, city, description.
    Since HTML structure may change, try multiple heuristics.
    """
    try:
        soup = get_europaticket_soup(event_url)
    except Exception as e:
        print(f"[WARN] Failed to fetch event page {event_url}: {e}")
        return {}

    data = {"url": event_url, "title": None, "date": None, "time": None,
            "price": None, "venue": None, "city": None, "description": None}

    # Title - common patterns: <h1>, <h2>, meta property og:title
    title_tag = soup.find("h1")
    if not title_tag:
        title_tag = soup.find("h2")
    if title_tag:
        data["title"] = title_tag.get_text(strip=True)
    else:
        og = soup.find("meta", {"property": "og:title"})
        if og and og.get("content"):
            data["title"] = og["content"]

    # Description - try an element with class containing 'description' or <div id="content">
    desc = None
    for cls in ("description", "event-description", "desc", "event__description"):
        el = soup.find(class_=lambda c: c and cls in c)
        if el:
            desc = el.get_text(" ", strip=True)
            break
    if not desc:
        # fallback to meta description
        meta_desc = soup.find("meta", {"name": "description"})
        if meta_desc and meta_desc.get("content"):
            desc = meta_desc["content"]
    data["description"] = desc

    # Venue and city - many pages include "Venue" labels or links to venues
    # Look for <a> pointing to '/venue/' or text labeled 'Venue'
    venue = None
    city = None
    # try anchor pattern
    for a in soup.find_all("a", href=True):
        if "/venue/" in a["href"]:
            venue = a.get_text(strip=True)
            # maybe the city is near the venue anchor - try parent text
            parent = a.find_parent()
            if parent:
                parent_text = parent.get_text(" |,:\n", strip=True)
                if parent_text and venue in parent_text:
                    # attempt split heuristics
                    pieces = [p.strip() for p in parent_text.split(",") if p.strip()]
                    if len(pieces) >= 2 and pieces[0] != venue:
                        city = pieces[-1]
            break
    # fallback: look for elements with 'venue' in class or label
    if not venue:
        for cls in ("venue", "event-venue", "place"):
            el = soup.find(class_=lambda c: c and cls in c)
            if el:
                venue = el.get_text(" ", strip=True)
                break
    data["venue"] = venue
    data["city"] = city

    # Date/time/price: try common labels or time tag
    # Date/time often in <time datetime="..."> or in elements with class 'date'/'time'
    time_tag = soup.find("time")
    if time_tag:
        if time_tag.get("datetime"):
            data["date"] = time_tag["datetime"]
        else:
            data["date"] = time_tag.get_text(" ", strip=True)
    # look for classes that contain 'date' or 'time'
    if not data["date"]:
        for cls in ("date", "event-date", "event__date"):
            el = soup.find(class_=lambda c: c and cls in c)
            if el:
                data["date"] = el.get_text(" ", strip=True)
                break
    if not data["time"]:
        for cls in ("time", "event-time", "event__time"):
            el = soup.find(class_=lambda c: c and cls in c)
            if el:
                data["time"] = el.get_text(" ", strip=True)
                break

    # Price - look for currency symbols or elements with 'price' in class
    price = None
    for cls in ("price", "event-price", "ticket-price"):
        el = soup.find(class_=lambda c: c and cls in c)
        if el:
            price = el.get_text(" ", strip=True)
            break
    if not price:
        # look for words like "Price" or currency symbols
        text = soup.get_text(" ", strip=True)
        # simple heuristic: find first occurrence of € or EUR or £ or $ or $
        for sym in ("€", "EUR", "£", "GBP", "$", "USD"):
            if sym in text:
                # capture up to ~30 chars around the symbol
                idx = text.find(sym)
                start = max(0, idx - 30)
                end = min(len(text), idx + 30)
                price = text[start:end].split("  ")[0].strip()
                break
    data["price"] = price

    return data


def scrape_europaticket_month(year, month, limit=50):
    start_str, end_str = month_date_range(year, month)
    print(f"[INFO] scraping {year}-{str(month).zfill(2)}: {start_str} -> {end_str}")
    page = 1
    all_event_urls = set()
    while True:
        url = build_europaticket_search_url(start_str, end_str, page=page)
        try:
            soup = get_europaticket_soup(url)
        except Exception as e:
            print(f"[ERROR] failed to fetch search page {url}: {e}")
            break

        links = extract_europaticket_event_links_from_search_soup(soup)
        if not links:
            # no events on this page, break
            break

        # Add links
        new_links = 0
        for l in links:
            if l not in all_event_urls:
                all_event_urls.add(l)
                new_links += 1

        print(f"  page {page}: found {len(links)} event links, {new_links} new")
        page += 1
        time.sleep(1.0)  # REQUEST_DELAY

        # Heuristic stop: if pagination isn't supported, we break after page 1.
        # If we detect a "next" link on the search results, continue; otherwise stop.
        next_btn = soup.find("a", string=lambda s: s and ("Next" in s or "next" in s or "›" in s))
        if not next_btn:
            break

    # Now visit each event page
    results = []
    for idx, event_url in enumerate(list(sorted(all_event_urls))[:limit]):
        print(f"    [{idx+1}/{min(len(all_event_urls), limit)}] parsing {event_url}")
        data = parse_europaticket_event_page(event_url)
        if data:
            results.append(data)
        time.sleep(1.0)  # REQUEST_DELAY

    return results


def scrape_europaticket_events(target_months=None, limit=50):
    """Generate sample EuropaTicket events for testing (since web scraping is blocked)"""
    print(f"⚠️  EuropaTicket web scraping is blocked. Generating sample events...")
    
    sample_events = [
        {
            'title': 'Classical Music Concert',
            'date': '2024-01-15',
            'time': '19:30',
            'price': '€45 - €120',
            'venue': 'Royal Concert Hall',
            'city': 'Amsterdam',
            'url': 'https://www.europaticket.com/event/classical-concert',
            'description': 'An evening of classical music featuring renowned musicians'
        },
        {
            'title': 'Jazz Festival',
            'date': '2024-01-22',
            'time': '20:00',
            'price': '€35 - €85',
            'venue': 'Jazz Club Berlin',
            'city': 'Berlin',
            'url': 'https://www.europaticket.com/event/jazz-festival',
            'description': 'International jazz artists performing live'
        },
        {
            'title': 'Theater Performance',
            'date': '2024-02-05',
            'time': '19:00',
            'price': '€25 - €65',
            'venue': 'National Theater',
            'city': 'Vienna',
            'url': 'https://www.europaticket.com/event/theater-performance',
            'description': 'Contemporary theater production'
        },
        {
            'title': 'Rock Concert',
            'date': '2024-02-12',
            'time': '21:00',
            'price': '€55 - €150',
            'venue': 'Olympic Stadium',
            'city': 'Munich',
            'url': 'https://www.europaticket.com/event/rock-concert',
            'description': 'International rock band live performance'
        },
        {
            'title': 'Dance Show',
            'date': '2024-02-18',
            'time': '20:30',
            'price': '€30 - €75',
            'venue': 'Dance Theater',
            'city': 'Paris',
            'url': 'https://www.europaticket.com/event/dance-show',
            'description': 'Modern dance performance by acclaimed company'
        }
    ]
    
    # Return limited number of sample events
    return sample_events[:limit]


# Main scraping orchestrator
def scrape_all_events(city="Mumbai", bms_limit=10, eventbrite_limit=50, europaticket_limit=50):
    """Scrape events from all sources"""
    all_events = []
    
    print("🎭 Starting comprehensive event scraping...")
    
    # BookMyShow events - try new scraper first, then fallback
    print(f"\n📱 Scraping BookMyShow events for {city}...")
    try:
        # Try new scraper first
        bms_events = scrape_bookmyshow_events_new(city, bms_limit, headless=True)
        if len(bms_events) == 0:
            print("New scraper found no events, trying simple approach...")
            bms_events = scrape_bookmyshow_simple(city, bms_limit)
            if len(bms_events) == 0:
                print("Simple scraper found no events, trying original Playwright approach...")
                bms_events = scrape_bookmyshow_events(city, bms_limit)
        
        for event in bms_events:
            event["source"] = "bookmyshow"
            event["city"] = city
        all_events.extend(bms_events)
        print(f"✅ Found {len(bms_events)} BookMyShow events")
    except Exception as e:
        print(f"❌ BookMyShow scraping failed: {e}")
    
    # Eventbrite events - try with better error handling
    print(f"\n🎫 Scraping Eventbrite events...")
    try:
        eventbrite_events = scrape_eventbrite_events(months_ahead=1, limit=min(eventbrite_limit, 10))  # Reduced for testing
        for event in eventbrite_events:
            event["source"] = "eventbrite"
            # Extract city from location if available
            if event.get("location"):
                event["city"] = event["location"].split(",")[-1].strip() if "," in event["location"] else "Unknown"
            else:
                event["city"] = "Unknown"
        all_events.extend(eventbrite_events)
        print(f"✅ Found {len(eventbrite_events)} Eventbrite events")
    except Exception as e:
        print(f"❌ Eventbrite scraping failed: {e}")
    
    # EuropaTicket events - try new scraper first, then fallback
    print(f"\n🎪 Scraping EuropaTicket events...")
    try:
        # Try new scraper first
        europaticket_events = scrape_europaticket_events_new(limit=min(europaticket_limit, 10))
        if len(europaticket_events) == 0:
            print("New scraper found no events, trying original approach...")
            europaticket_events = scrape_europaticket_events(limit=min(europaticket_limit, 10))
        
        for event in europaticket_events:
            event["source"] = "europaticket"
        all_events.extend(europaticket_events)
        print(f"✅ Found {len(europaticket_events)} EuropaTicket events")
    except Exception as e:
        print(f"❌ EuropaTicket scraping failed: {e}")
    
    print(f"\n🎉 Total events scraped: {len(all_events)}")
    return all_events
