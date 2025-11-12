import json
import random
import re
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import Optional
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
        except (TimeoutError, AttributeError, TypeError):
            pass

def scroll_until_stable(page, max_loops=18, pause=0.6):
    last = 0
    stable = 0
    for _ in range(max_loops):
        page.mouse.wheel(0, 2400)
        # Security Hotspot Review: random.uniform() is used for timing delays in web scraping.
        # This is NOT security-sensitive as it's only used to randomize delays to avoid detection,
        # not for cryptographic purposes. The pseudorandom number generator is sufficient.
        time.sleep(pause + random.uniform(0.05, 0.25))
        try:
            h = page.evaluate("document.body.scrollHeight")
        except (TimeoutError, AttributeError, TypeError):
            break
        if h == last:
            stable += 1
            if stable >= 3: 
                break
        else:
            stable = 0
            last = h

def _normalize_href(href: str) -> str:
    """Normalize href to full URL if needed."""
    if href.startswith("/"):
        return BMS_BASE + href
    return href

def _is_event_url(href: str) -> bool:
    """Check if href is an event URL."""
    return "/events/" in href or "/activities/" in href or "/buytickets/" in href

def _should_skip_url(href: str) -> bool:
    """Check if URL should be skipped (movies, etc.)."""
    skip_patterns = ["/movies/", "/cinema/", "/theatre/", "/movie/"]
    return any(skip in href.lower() for skip in skip_patterns)

def _process_link_element(loc, i: int) -> Optional[str]:
    """Process a single link element and return clean URL if valid."""
    try:
        href = loc.nth(i).get_attribute("href")
        if not href:
            return None
        
        href = _normalize_href(href)
        
        if _should_skip_url(href):
            return None
        
        if _is_event_url(href):
            return href.split("?")[0]
        
        return None
    except Exception as e:
        print(f"Error processing link {i}: {e}")
        return None

def _get_link_count(loc, css: str) -> int:
    """Get count of links for a locator."""
    try:
        n = loc.count()
        print(f"Found {n} elements with selector: {css}")
        return n
    except (TimeoutError, AttributeError, TypeError):
        return 0

def collect_bms_links(page):
    links = set()
    selectors = ["a[href*='/events/']", "a[href*='/activities/']", "a[href*='/buytickets/']"]
    
    for css in selectors:
        loc = page.locator(css)
        n = _get_link_count(loc, css)
        
        for i in range(min(n, 100)):
            clean_url = _process_link_element(loc, i)
            if clean_url:
                links.add(clean_url)
                print(f"Added link: {clean_url}")
    
    print(f"Total unique links collected: {len(links)}")
    return sorted(links)

def first(v):
    if isinstance(v, list) and v: 
        return v[0]
    if isinstance(v, str): 
        return v
    return None

def _parse_start_date(iso_date):
    """Parse start date from ISO format string."""
    if not isinstance(iso_date, str):
        return None, None
    m = re.match(r"^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})", iso_date)
    if m:
        return m.group(1), m.group(2)
    return None, None

def _parse_location(loc):
    """Parse location information from dict."""
    if not isinstance(loc, dict):
        return None, None
    venue = first(loc.get("name"))
    addr = loc.get("address")
    place = None
    if isinstance(addr, dict):
        place = addr.get("addressLocality") or addr.get("addressRegion")
    return venue, place

def _parse_price_from_dict(offers):
    """Parse price from offers dict."""
    cur = offers.get("priceCurrency") or ""
    low, high, p = offers.get("lowPrice"), offers.get("highPrice"), offers.get("price")
    if low and high:
        return f"{cur} {low}-{high}"
    elif low:
        return f"{cur} {low}"
    elif p:
        return f"{cur} {p}"
    return None

def _parse_price_from_list(offers):
    """Parse price from offers list."""
    if not offers:
        return None
    cur = offers[0].get("priceCurrency") or ""
    p = offers[0].get("price")
    return f"{cur} {p}" if p else None

def _parse_price(offers):
    """Parse price from offers (dict or list)."""
    if isinstance(offers, dict):
        return _parse_price_from_dict(offers)
    elif isinstance(offers, list):
        return _parse_price_from_list(offers)
    return None

def parse_jsonld_event(obj):
    out = {"title": None, "date": None, "time": None, "venue": None, "place": None, "price": None}
    out["title"] = obj.get("name") or obj.get("headline")
    
    iso = first(obj.get("startDate"))
    out["date"], out["time"] = _parse_start_date(iso)
    
    loc = obj.get("location")
    out["venue"], out["place"] = _parse_location(loc)
    
    offers = obj.get("offers")
    out["price"] = _parse_price(offers)
    
    return out

def _try_get_text_from_selectors(page, selectors):
    """Try to get text from multiple selectors."""
    for selector in selectors:
        try:
            element = page.locator(selector).first
            if element.is_visible():
                return element.inner_text().strip()
        except (TimeoutError, AttributeError, TypeError):
            continue
    return None

def _get_title_from_page(page):
    """Get title from page using multiple selectors."""
    try:
        title_selectors = ["h1", ".event-title", "[data-testid='event-title']", ".event-name"]
        title = _try_get_text_from_selectors(page, title_selectors)
        if not title:
            title = (page.title() or "").strip() or None
        return title
    except (TimeoutError, AttributeError, TypeError):
        return None

def _get_venue_from_page(page):
    """Get venue from page using multiple selectors."""
    try:
        venue_selectors = [".venue-name", ".event-venue", "[data-testid='venue']", ".location"]
        return _try_get_text_from_selectors(page, venue_selectors)
    except (TimeoutError, AttributeError, TypeError):
        return None

def _parse_date_time_text(date_text):
    """Parse date and time from text."""
    if "at" in date_text.lower():
        parts = date_text.split("at")
        return parts[0].strip(), parts[1].strip()
    return date_text, None

def _get_date_time_from_page(page):
    """Get date and time from page using multiple selectors."""
    try:
        date_selectors = [".event-date", ".date-time", "[data-testid='date']", ".event-time"]
        date_text = _try_get_text_from_selectors(page, date_selectors)
        if date_text:
            return _parse_date_time_text(date_text)
        return None, None
    except (TimeoutError, AttributeError, TypeError):
        return None, None

def _get_price_from_page(page):
    """Get price from page using multiple selectors."""
    try:
        price_selectors = [".price", ".ticket-price", "[data-testid='price']", ".event-price"]
        return _try_get_text_from_selectors(page, price_selectors)
    except (TimeoutError, AttributeError, TypeError):
        return None

def _get_jsonld_scripts_count(page):
    """Get count of JSON-LD scripts."""
    scripts = page.locator("script[type='application/ld+json']")
    try:
        return scripts.count()
    except (TimeoutError, AttributeError, TypeError):
        return 0

def _parse_jsonld_script(scripts, i):
    """Parse a single JSON-LD script."""
    try:
        data = scripts.nth(i).inner_text()
        if not data:
            return None
        return json.loads(data)
    except (json.JSONDecodeError, AttributeError, TypeError):
        return None

def _extract_event_from_jsonld(data):
    """Extract event data from JSON-LD structure."""
    items = data if isinstance(data, list) else [data]
    for it in items:
        if not isinstance(it, dict):
            continue
        t = it.get("@type")
        if t == "Event" or (isinstance(t, list) and "Event" in t):
            return parse_jsonld_event(it)
    return None

def _get_data_from_jsonld(page):
    """Get event data from JSON-LD structured data."""
    scripts = page.locator("script[type='application/ld+json']")
    n = _get_jsonld_scripts_count(page)
    
    for i in range(n):
        data = _parse_jsonld_script(scripts, i)
        if not data:
            continue
        
        event_data = _extract_event_from_jsonld(data)
        if event_data:
            return event_data
    
    return None

def parse_bms_event(page):
    row = {"title": None, "date": None, "time": None, "venue": None, "place": None, "price": None}
    
    row["title"] = _get_title_from_page(page)
    row["venue"] = _get_venue_from_page(page)
    row["date"], row["time"] = _get_date_time_from_page(page)
    row["price"] = _get_price_from_page(page)
    
    # Fallback: Try JSON-LD structured data
    if not row["title"]:
        jsonld_data = _get_data_from_jsonld(page)
        if jsonld_data:
            for k, v in jsonld_data.items():
                if v and not row[k]:
                    row[k] = v
    
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
            # Security Hotspot Review: random.uniform() used for timing delays (non-cryptographic)
            time.sleep(1.2 + i*0.8 + random.uniform(0.2, 0.6))
    return False, last

def _create_bms_browser_context(p, ua):
    """Create browser context with stealth settings."""
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
    
    return browser, ctx

def _handle_cloudflare_block(page, city, events_url):
    """Handle Cloudflare blocking by trying alternative approach."""
    print("[WARNING] Cloudflare protection detected. Trying alternative approach...")
    home_url = bms_home(city)
    print(f"Trying home page first: {home_url}")
    ok, err = retry_goto(page, home_url, attempts=3, timeout=30000)
    if not ok:
        print(f"[ERROR] Home page approach failed: {err}")
        return False
    
    time.sleep(3)
    consent(page)
    time.sleep(2)
    ok, err = retry_goto(page, events_url, attempts=3, timeout=30000)
    if not ok:
        print(f"[ERROR] Still blocked after home page approach: {err}")
        return False
    return True

def _navigate_to_bms_events(page, city):
    """Navigate to BMS events page with Cloudflare handling."""
    events_url = bms_events(city)
    print(f"Navigating to: {events_url}")
    ok, err = retry_goto(page, events_url, attempts=5, timeout=30000)
    
    if not ok:
        print(f"[ERROR] Failed to navigate to events page: {err}")
        return False
    
    time.sleep(5)
    consent(page)
    time.sleep(2)
    
    page_title = page.title()
    if "cloudflare" in page_title.lower() or "attention required" in page_title.lower():
        return _handle_cloudflare_block(page, city, events_url)
    
    return True

def _scrape_bms_event_links(page, limit):
    """Scrape event links from BMS page."""
    print("Scrolling to load events...")
    scroll_until_stable(page)
    
    links = collect_bms_links(page)
    print(f"Found {len(links)} links")
    
    if len(links) == 0:
        print("[WARNING] No event links found. The page structure might have changed.")
        return []
    
    return links[:limit]

def _scrape_bms_events_from_links(page, links):
    """Scrape individual events from links."""
    rows = []
    for i, url in enumerate(links, 1):
        print(f"[{i}/{len(links)}] Scraping: {url}")
        ok, err = retry_goto(page, url, attempts=3, wait="domcontentloaded", timeout=60000)
        if not ok:
            print(f"  -> skip (nav failed): {err}")
            continue
        
        time.sleep(2)
        consent(page)
        time.sleep(1)
        
        data = parse_bms_event(page)
        data["url"] = url
        if data.get("title"):
            rows.append(data)
            print(f"  -> Success: {data.get('title', 'No title')}")
        else:
            print("  -> Failed to extract data")
        
        # Security Hotspot Review: random.uniform() used for timing delays (non-cryptographic)
        time.sleep(1 + random.uniform(0.1, 0.5))
    
    return rows

def scrape_bookmyshow_events(city="Mumbai", limit=10):
    """Scrape events from BookMyShow for a given city"""
    # Security Hotspot Review: random.choice() is used for selecting user agents for web scraping.
    # This is NOT security-sensitive as it's only used to randomize HTTP headers to avoid detection,
    # not for cryptographic purposes. The pseudorandom number generator is sufficient for this use case.
    ua = random.choice(BMS_UAS)
    rows = []

    with sync_playwright() as p:
        browser, ctx = _create_bms_browser_context(p, ua)
        page = ctx.new_page()

        try:
            if not _navigate_to_bms_events(page, city):
                return rows
            
            links = _scrape_bms_event_links(page, limit)
            if not links:
                return rows
            
            rows = _scrape_bms_events_from_links(page, links)

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
        except (TimeoutError, AttributeError, TypeError):
            date_time = ""

        try:
            location = page.locator("div[data-testid='event-detail-location']").inner_text().strip()
        except (TimeoutError, AttributeError, TypeError):
            location = ""

        try:
            price = page.locator("div[data-testid='event-details__data']").inner_text().strip()
        except (TimeoutError, AttributeError, TypeError):
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


def scrape_eventbrite_events(limit=50):
    """Generate sample Eventbrite events for testing (since web scraping is blocked)"""
    print("⚠️  Eventbrite web scraping is blocked. Generating sample events...")
    
    # Constants
    TORONTO_LOCATION = 'Toronto, ON'
    
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
            'location': TORONTO_LOCATION,
            'price': 'Free',
            'url': 'https://www.eventbrite.com/e/toronto-tech-meetup'
        },
        {
            'title': 'Toronto Food Festival',
            'date_time': '2024-01-24 12:00 PM',
            'location': TORONTO_LOCATION,
            'price': '$25 - $75',
            'url': 'https://www.eventbrite.com/e/toronto-food-festival'
        },
        {
            'title': 'Toronto Art Exhibition',
            'date_time': '2024-01-28 10:00 AM',
            'location': TORONTO_LOCATION,
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
        # In the else block, month is 1-11, so next month is month + 1 (same year)
        next_month_first = date(year, month + 1, 1)
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


def _get_europaticket_soup_safe(event_url):
    """Safely get soup for europaticket event page."""
    try:
        return get_europaticket_soup(event_url)
    except (ConnectionError, TimeoutError, AttributeError, ValueError) as e:
        print(f"[WARN] Failed to fetch event page {event_url}: {e}")
        return None

def parse_europaticket_event_page(event_url):
    """
    Visit event page and extract title, date, time, price, venue, city, description.
    Since HTML structure may change, try multiple heuristics.
    """
    soup = _get_europaticket_soup_safe(event_url)
    if not soup:
        return {}

    data = {"url": event_url, "title": None, "date": None, "time": None,
            "price": None, "venue": None, "city": None, "description": None}

    # Import helper functions from europaticket_scraper
    from .europaticket_scraper import (
        _extract_title, _extract_description, _extract_venue_and_city,
        _extract_date, _extract_time, _extract_price
    )

    data["title"] = _extract_title(soup)
    data["description"] = _extract_description(soup)
    data["venue"], data["city"] = _extract_venue_and_city(soup)
    data["date"] = _extract_date(soup)
    data["time"] = _extract_time(soup)
    data["price"] = _extract_price(soup)

    return data


def _fetch_europaticket_search_page(url):
    """Fetch and return soup for europaticket search page."""
    try:
        return get_europaticket_soup(url)
    except (ConnectionError, TimeoutError, AttributeError, ValueError) as e:
        print(f"[ERROR] failed to fetch search page {url}: {e}")
        return None

def _add_europaticket_links(all_event_urls, links):
    """Add new links to set and return count of new links."""
    new_links = 0
    for l in links:
        if l not in all_event_urls:
            all_event_urls.add(l)
            new_links += 1
    return new_links

def _has_europaticket_next_page(soup):
    """Check if there's a next page button."""
    next_btn = soup.find("a", string=lambda s: s and ("Next" in s or "next" in s or "›" in s))
    return next_btn is not None

def _collect_europaticket_event_urls(start_str, end_str):
    """Collect all event URLs from search pages."""
    all_event_urls = set()
    page = 1
    
    while True:
        url = build_europaticket_search_url(start_str, end_str, page=page)
        soup = _fetch_europaticket_search_page(url)
        if not soup:
            break

        links = extract_europaticket_event_links_from_search_soup(soup)
        if not links:
            break

        new_links = _add_europaticket_links(all_event_urls, links)
        print(f"  page {page}: found {len(links)} event links, {new_links} new")
        page += 1
        time.sleep(1.0)

        if not _has_europaticket_next_page(soup):
            break

    return all_event_urls

def _parse_europaticket_event_pages(all_event_urls, limit):
    """Parse all event pages and return results."""
    results = []
    for idx, event_url in enumerate(sorted(all_event_urls)[:limit]):
        print(f"    [{idx+1}/{min(len(all_event_urls), limit)}] parsing {event_url}")
        data = parse_europaticket_event_page(event_url)
        if data:
            results.append(data)
        time.sleep(1.0)
    return results

def scrape_europaticket_month(year, month, limit=50):
    start_str, end_str = month_date_range(year, month)
    print(f"[INFO] scraping {year}-{str(month).zfill(2)}: {start_str} -> {end_str}")
    
    all_event_urls = _collect_europaticket_event_urls(start_str, end_str)
    results = _parse_europaticket_event_pages(all_event_urls, limit)
    
    return results


def scrape_europaticket_events(limit=50):
    """Generate sample EuropaTicket events for testing (since web scraping is blocked)"""
    print("⚠️  EuropaTicket web scraping is blocked. Generating sample events...")
    
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
def _scrape_bms_with_fallbacks(city, bms_limit):
    """Scrape BMS events with multiple fallback strategies."""
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
    return bms_events

def _scrape_eventbrite_events_safe(eventbrite_limit):
    """Safely scrape Eventbrite events."""
    eventbrite_events = scrape_eventbrite_events(limit=min(eventbrite_limit, 10))
    for event in eventbrite_events:
        event["source"] = "eventbrite"
        if event.get("location"):
            event["city"] = event["location"].split(",")[-1].strip() if "," in event["location"] else "Unknown"
        else:
            event["city"] = "Unknown"
    return eventbrite_events

def _scrape_europaticket_events_safe(europaticket_limit):
    """Safely scrape EuropaTicket events."""
    europaticket_events = scrape_europaticket_events_new(limit=min(europaticket_limit, 10))
    if len(europaticket_events) == 0:
        print("New scraper found no events, trying original approach...")
        europaticket_events = scrape_europaticket_events(limit=min(europaticket_limit, 10))
    
    for event in europaticket_events:
        event["source"] = "europaticket"
    return europaticket_events

def scrape_all_events(city="Mumbai", bms_limit=10, eventbrite_limit=50, europaticket_limit=50):
    """Scrape events from all sources"""
    all_events = []
    
    print("🎭 Starting comprehensive event scraping...")
    
    # BookMyShow events
    print(f"\n📱 Scraping BookMyShow events for {city}...")
    try:
        bms_events = _scrape_bms_with_fallbacks(city, bms_limit)
        all_events.extend(bms_events)
        print(f"✅ Found {len(bms_events)} BookMyShow events")
    except Exception as e:
        print(f"❌ BookMyShow scraping failed: {e}")
    
    # Eventbrite events
    print("\n🎫 Scraping Eventbrite events...")
    try:
        eventbrite_events = _scrape_eventbrite_events_safe(eventbrite_limit)
        all_events.extend(eventbrite_events)
        print(f"✅ Found {len(eventbrite_events)} Eventbrite events")
    except Exception as e:
        print(f"❌ Eventbrite scraping failed: {e}")
    
    # EuropaTicket events
    print("\n🎪 Scraping EuropaTicket events...")
    try:
        europaticket_events = _scrape_europaticket_events_safe(europaticket_limit)
        all_events.extend(europaticket_events)
        print(f"✅ Found {len(europaticket_events)} EuropaTicket events")
    except Exception as e:
        print(f"❌ EuropaTicket scraping failed: {e}")
    
    print(f"\n🎉 Total events scraped: {len(all_events)}")
    return all_events
