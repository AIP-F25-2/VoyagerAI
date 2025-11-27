#!/usr/bin/env python3
"""
berlin_scraper_robust_full.py
Robust, deeper Berlin events scraper for europaticket.com
"""

import requests
import time
import csv
import sys
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque

# --- CONFIG ---
BASE = "https://www.europaticket.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Referer": BASE + "/",
}
OUT_CSV = "berlin_events_large.csv"
TEMP_BACKUP_PREFIX = "berlin_events_temp_"
DELAY = 1.0                # base delay between requests (randomized)
MAX_EVENTS = 5000
MAX_WORKERS = 8            # thread pool size for parsing pages
REQUEST_RETRIES = 3
REQUEST_TIMEOUT = 25

# --- GLOBALS ---
seen_event_urls = set()
discovered_urls = set()
session = requests.Session()
session.headers.update(HEADERS)


def polite_sleep(base=DELAY):
    """Randomized polite sleep to reduce blocking."""
    time.sleep(random.uniform(base * 0.5, base * 1.5))


def fetch(url, retries=REQUEST_RETRIES, timeout=REQUEST_TIMEOUT):
    """Fetch a URL with retries and return BeautifulSoup or None."""
    for attempt in range(1, retries + 1):
        try:
            polite_sleep()
            resp = session.get(url, timeout=timeout)
            resp.raise_for_status()
            text = resp.text or ""
            # skip very short pages (likely blocked or captcha)
            if len(text) < 800:
                # allow one extra attempt
                if attempt == retries:
                    print(f"[WARN] Short response for {url} (len={len(text)})")
                    return BeautifulSoup(text, "html.parser")
                else:
                    print(f"[WARN] Received short response; retrying {url}")
                    time.sleep(attempt * 1.5)
                    continue
            return BeautifulSoup(text, "html.parser")
        except Exception as e:
            print(f"[ERROR] fetch {url} attempt {attempt}/{retries}: {e}")
            if attempt < retries:
                time.sleep(attempt * 1.5)
            else:
                return None
    return None


def normalize_url(href, base=BASE):
    if not href:
        return None
    # ignore javascript: and mailto:
    if href.startswith("javascript:") or href.startswith("mailto:"):
        return None
    try:
        return urljoin(base, href.split("#")[0])
    except:
        return None


def discover_seed_urls():
    """Build initial seed list: city pages, month pages, venue lists and search queries."""
    seeds = set()

    # Basic city pages
    city_variants = [
        f"{BASE}/en/city/berlin",
        f"{BASE}/en/city/berlin/",
        f"{BASE}/city/berlin",
        f"{BASE}/city/berlin/"
    ]
    seeds.update(city_variants)

    # Add month-based permutations (many sites have month anchors)
    months = [
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december"
    ]
    for m in months:
        seeds.add(f"{BASE}/en/city/berlin/{m}")
        seeds.add(f"{BASE}/city/berlin/{m}")

    # Known venue pages (seed list)
    venue_seeds = [
        f"{BASE}/en/venue/berliner-philharmonie",
        f"{BASE}/en/venue/deutsche-oper-berlin",
        f"{BASE}/en/venue/konzerthaus-berlin",
        f"{BASE}/en/venue/staatsoper-unter-den-linden",
        f"{BASE}/en/venue/mercedes-benz-arena-berlin",
        f"{BASE}/en/venue/waldbuhne-berlin",
        f"{BASE}/en/venue/friedrichstadt-palace-berlin"
    ]
    seeds.update(venue_seeds)

    # Expanded search queries
    search_queries = [
        "berlin", "berlin+concert", "berlin+opera", "berlin+festival",
        "berlin+theatre", "germany+berlin", "berlin+show", "berlin+music"
    ]
    for q in search_queries:
        seeds.add(f"{BASE}/en/search?q={q}")
        seeds.add(f"{BASE}/search?q={q}")

    # Add calendar page
    seeds.add(f"{BASE}/en/calendar")
    seeds.add(f"{BASE}/calendar")

    return list(seeds)


def auto_discover_urls_from_page(sp, current_url, queue):
    """Discover category pages, venue pages, pagination and event links from a page soup."""
    if not sp:
        return 0

    new_count = 0
    # 1) Find event links
    event_selectors = [
        'a[href*="/event/"]',
        'a[href*="/en/event/"]',
        'a[href*="event"]',
        'a[href*="concert"]',
        'a[href*="performance"]',
        '.event a', '.card a', '.item a', '.event-item a', '.event-card a'
    ]
    for sel in event_selectors:
        for a in sp.select(sel):
            href = a.get('href')
            full = normalize_url(href)
            if full and BASE in full and '/event/' in full and full not in seen_event_urls:
                seen_event_urls.add(full)
                new_count += 1

    # 2) Category & pagination & venue discovery
    category_keywords = ["opera", "concert", "ballet", "theatre", "music", "show", "festival", "venue", "city", "events", "calendar"]
    for a in sp.find_all('a', href=True):
        href = a['href'].lower()
        full = normalize_url(href)
        if not full or BASE not in full:
            continue

        # pagination links (look for page= or /page/)
        is_pag = ('page=' in href) or (re.search(r'/page/\d+', href) is not None) or ('next' in href)
        if is_pag and full not in discovered_urls:
            discovered_urls.add(full)
            queue.append(full)
            # don't count as event link
            continue

        # category pages / month pages / venue pages
        if any(k in href for k in category_keywords) and full not in discovered_urls:
            discovered_urls.add(full)
            queue.append(full)

    return new_count


def get_all_event_urls(max_urls=MAX_EVENTS):
    """Crawl seed pages and discover event URLs (breadth-first) until reaching max_urls."""
    seeds = discover_seed_urls()
    queue = deque(seeds)
    for s in seeds:
        discovered_urls.add(s)

    print(f"[INFO] Starting discovery with {len(seeds)} seed URLs.")
    processed = 0

    while queue and len(seen_event_urls) < max_urls:
        url = queue.popleft()
        processed += 1
        print(f"[DISCOVER {processed}] {url}  - found events so far: {len(seen_event_urls)}")
        sp = fetch(url)
        if not sp:
            continue

        # auto-discover category pages, pagination, venues and event links
        new_links = auto_discover_urls_from_page(sp, url, queue)
        print(f"  -> discovered {new_links} event links on this page; queue size {len(queue)}")
        # also attempt to auto-discover venue list pages (e.g. /en/venue)
        # find explicit venue lists
        for a in sp.find_all('a', href=True):
            href = a['href'].lower()
            if '/venue' in href and BASE in normalize_url(href) and normalize_url(href) not in discovered_urls:
                discovered_urls.add(normalize_url(href))
                queue.append(normalize_url(href))

    print(f"[DISCOVERY COMPLETE] Found {len(seen_event_urls)} unique event URLs")
    return list(seen_event_urls)[:max_urls]


# -------------------------
# Event parsing utilities
# -------------------------
def clean_text(text):
    if not text:
        return None
    text = re.sub(r'\s+', ' ', text.strip())
    # remove common junk
    junk_patterns = [r'Buy Official Tickets.*', r'CALL NOW:.*', r'MenuMenu']
    for p in junk_patterns:
        text = re.sub(p, '', text, flags=re.IGNORECASE)
    return text.strip() or None


def extract_price_from_description(text):
    if not text:
        return None
    patterns = [
        r'from\s*€\s*(\d+(?:[\.,]\d+)?)',
        r'€\s*(\d+(?:[\.,]\d+)?)',
        r'(\d+(?:[\.,]\d+)?)\s*€'
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val = m.group(1).replace(',', '.')
            return f"€{val}"
    return None


def extract_time_from_text(text):
    if not text:
        return None
    # common time patterns
    patterns = [r'\b\d{1,2}:\d{2}\b', r'\b\d{1,2}\s?[:]\s?\d{2}\s?(?:AM|PM|am|pm)?\b']
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(0)
    return None


def extract_meta_ld_json(sp):
    """Extract JSON-LD structured data if present and return dict (may be list)."""
    try:
        scripts = sp.find_all('script', type='application/ld+json')
        collected = []
        for s in scripts:
            if not s.string:
                continue
            try:
                obj = json.loads(s.string.strip())
                collected.append(obj)
            except Exception:
                # try to fix common trailing commas
                try:
                    cleaned = re.sub(r',\s*}', '}', s.string)
                    obj = json.loads(cleaned)
                    collected.append(obj)
                except Exception:
                    continue
        return collected
    except Exception:
        return []


def parse_event_page(url):
    """Parse event page and return a dict of fields."""
    sp = fetch(url)
    if not sp:
        return None

    result = {"url": url, "title": None, "date": None, "time": None,
              "price": None, "venue": None, "description": None, "category": None, "image": None, "organizer": None}

    # Title: prefer h1, then og:title, then title tag
    h1 = sp.select_one('h1')
    if h1 and h1.get_text(strip=True):
        result['title'] = clean_text(h1.get_text(strip=True))
    else:
        og = sp.select_one('meta[property="og:title"]')
        if og and og.get('content'):
            result['title'] = clean_text(og.get('content'))
        else:
            t = sp.select_one('title')
            if t:
                result['title'] = clean_text(t.get_text())

    # Description: meta description or main content paragraphs
    desc_meta = sp.select_one('meta[name="description"]')
    if desc_meta and desc_meta.get('content'):
        result['description'] = clean_text(desc_meta.get('content'))
    else:
        # prefer specific selectors added in your original code
        for sel in ('.description', '.event-description', '.summary', '.content p', '.event-content p'):
            el = sp.select_one(sel)
            if el and el.get_text(strip=True):
                result['description'] = clean_text(el.get_text())
                break

    # Structured JSON-LD
    ld = extract_meta_ld_json(sp)
    if ld:
        # find an object that looks like event
        for obj in ld:
            if isinstance(obj, dict):
                if obj.get('@type') and 'Event' in obj.get('@type'):
                    if obj.get('name') and not result['title']:
                        result['title'] = obj.get('name')
                    if obj.get('startDate'):
                        dt = obj.get('startDate')
                        if 'T' in dt:
                            date_part, time_part = dt.split('T', 1)
                            result['date'] = date_part
                            result['time'] = time_part.split('+')[0].split('-')[0]
                        else:
                            result['date'] = dt
                    if obj.get('location'):
                        if isinstance(obj['location'], dict):
                            result['venue'] = obj['location'].get('name') or result['venue']
                    if obj.get('offers'):
                        offers = obj.get('offers')
                        if isinstance(offers, dict):
                            price = offers.get('price') or offers.get('priceSpecification', {}).get('price')
                            if price:
                                result['price'] = f"€{price}" if not str(price).startswith("€") else str(price)
                    if obj.get('image') and not result.get('image'):
                        result['image'] = obj.get('image')

    # Venue: try heuristics if not from structured data
    if not result['venue']:
        # look for a link to /venue/ or /location/
        ven_link = sp.find('a', href=re.compile(r'/venue/|/location/'))
        if ven_link and ven_link.get_text(strip=True):
            result['venue'] = clean_text(ven_link.get_text(strip=True))
        else:
            for sel in ('.venue', '.location', '.place', '.theatre', '.hall', '.arena', '[class*="venue"]'):
                el = sp.select_one(sel)
                if el and el.get_text(strip=True):
                    result['venue'] = clean_text(el.get_text(strip=True))
                    break

    # Date and time: try time elements and fallback to regex
    time_elem = sp.find('time')
    if time_elem:
        dt = time_elem.get('datetime')
        if dt:
            if 'T' in dt:
                date_part, time_part = dt.split('T', 1)
                result['date'] = date_part
                result['time'] = time_part.split('+')[0].split('-')[0]
            else:
                result['date'] = dt
        else:
            ttxt = time_elem.get_text(strip=True)
            if ttxt:
                # may contain both date and time
                if re.search(r'\d{4}', ttxt):
                    result['date'] = clean_text(ttxt)
                else:
                    result['time'] = clean_text(ttxt)

    # search for common date patterns in page if still not found
    page_text = sp.get_text(separator=' ', strip=True)
    if not result['date']:
        date_patterns = [
            r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}',
            r'\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',
            r'\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
        ]
        for p in date_patterns:
            m = re.search(p, page_text, re.IGNORECASE)
            if m:
                result['date'] = clean_text(m.group(0))
                break

    if not result['time']:
        t = extract_time_from_text(page_text)
        if t:
            result['time'] = t

    # Price: try dedicated selectors then regex on page text
    if not result['price']:
        for sel in ('.price', '.ticket-price', '.cost', '[class*="price"]'):
            el = sp.select_one(sel)
            if el and el.get_text(strip=True):
                result['price'] = clean_text(el.get_text(strip=True))
                break
    if not result['price'] and result['description']:
        result['price'] = extract_price_from_description(result['description'])
    if not result['price']:
        m = re.search(r'€\s*\d+(?:[.,]\d+)?', page_text)
        if m:
            result['price'] = m.group(0)

    # Category/Type: try to detect
    if not result['category']:
        if 'opera' in page_text.lower():
            result['category'] = 'Opera'
        elif 'concert' in page_text.lower():
            result['category'] = 'Concert'
        elif 'theatre' in page_text.lower() or 'play' in page_text.lower():
            result['category'] = 'Theatre'

    # Organizer: attempt to parse
    org = sp.select_one('.organizer, .promoter')
    if org and org.get_text(strip=True):
        result['organizer'] = clean_text(org.get_text(strip=True))

    # Image: try og:image
    og_image = sp.select_one('meta[property="og:image"]')
    if og_image and og_image.get('content'):
        result['image'] = og_image.get('content')

    # final cleaning
    for k in result:
        if isinstance(result[k], str):
            result[k] = result[k].strip() or None

    return result


# -------------------------
# Runner and save
# -------------------------
def save_results(results, filename=OUT_CSV):
    if not results:
        return False
    df = pd.DataFrame(results)
    cols = ["title", "date", "time", "price", "venue", "category", "organizer", "image", "url", "description"]
    # ensure all columns present
    for c in cols:
        if c not in df.columns:
            df[c] = None
    df = df[cols]
    df.to_csv(filename, index=False, quoting=csv.QUOTE_NONNUMERIC, encoding='utf-8')
    return True


def run_scrape():
    print("[START] Discovering event URLs...")
    event_urls = get_all_event_urls(max_urls=MAX_EVENTS)
    if not event_urls:
        print("[ERROR] No event URLs discovered. Exiting.")
        return

    print(f"[INFO] Will attempt to parse {len(event_urls)} event pages (capped by discovery).")
    results = []
    failed = 0
    start = time.time()

    # use ThreadPoolExecutor for parallel parsing
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(parse_event_page, url): url for url in event_urls}
        completed = 0
        for fut in as_completed(futures):
            url = futures[fut]
            try:
                data = fut.result()
                completed += 1
                if data and data.get('title'):
                    results.append(data)
                    print(f"[PARSED {completed}/{len(event_urls)}] ✓ {data.get('title')[:80]} - {url}")
                else:
                    failed += 1
                    print(f"[PARSED {completed}/{len(event_urls)}] ✗ no title extracted - {url}")
            except Exception as e:
                failed += 1
                print(f"[ERROR] exception parsing {url}: {e}")

            # backup every 50 completed
            if completed % 50 == 0:
                temp_file = TEMP_BACKUP_PREFIX + str(completed) + ".csv"
                try:
                    save_results(results, temp_file)
                    print(f"[BACKUP] Saved {len(results)} parsed events to {temp_file}")
                except Exception as e:
                    print(f"[WARN] Failed to save backup: {e}")

    elapsed = time.time() - start
    print("=" * 80)
    print(f"[DONE] Parsed: {len(results)} successful, {failed} failed, elapsed {elapsed/60:.2f} min")

    # final save
    ok = save_results(results, OUT_CSV)
    if ok:
        print(f"[SUCCESS] Saved final {len(results)} events to {OUT_CSV}")
    else:
        print("[ERROR] Failed to save final CSV")


if __name__ == "__main__":
    try:
        run_scrape()
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] User aborted.")
