# bms_events_discover.py
import argparse, json, os, random, re, time, webbrowser, socket
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import pandas as pd
from playwright.sync_api import sync_playwright

BASE = "https://in.bookmyshow.com"
FIELDS = ["title","date","time","venue","place","price","url"]

UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]

def slug(s): return s.strip().lower().replace(" ", "-")
def home(city): return f"{BASE}/explore/home?city={slug(city)}"
def events(city): return f"{BASE}/explore/events-{slug(city)}"

def consent(page):
    for sel in ["#wzrk-confirm","button:has-text('Accept')","button:has-text('I Agree')","button:has-text('Allow All')"]:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=700):
                loc.click(); time.sleep(0.2); return
        except (TimeoutError, AttributeError, TypeError):
            pass

def scroll_until_stable(page, max_loops=18, pause=0.6):
    last = 0; stable = 0
    for _ in range(max_loops):
        # Security Hotspot Review: random.uniform() used for timing delays (non-cryptographic)
        page.mouse.wheel(0, 2400); time.sleep(pause + random.uniform(0.05, 0.25))
        try:
            h = page.evaluate("document.body.scrollHeight")
        except (TimeoutError, AttributeError, TypeError):
            break
        if h == last:
            stable += 1
            if stable >= 3: break
        else:
            stable = 0; last = h

def _normalize_link(href):
    """Normalize a link URL."""
    if not href:
        return None
    if href.startswith("/"):
        href = BASE + href
    if "/movies/" in href:
        return None
    return href.split("?")[0]


def _get_link_count(loc):
    """Safely get the count of locator elements."""
    try:
        return loc.count()
    except (TimeoutError, AttributeError, TypeError):
        return 0


def _extract_link_from_locator(loc, index):
    """Extract and normalize a link from a locator at a specific index."""
    try:
        href = loc.nth(index).get_attribute("href")
        return _normalize_link(href)
    except (TimeoutError, AttributeError, TypeError, IndexError):
        return None


def collect_links(page):
    """Collect event links from the page."""
    links = set()
    css_selectors = ["a[href*='/events/']", "a[href*='/activities/']", "a[href*='/buytickets/']"]
    
    for css in css_selectors:
        loc = page.locator(css)
        n = _get_link_count(loc)
        
        for i in range(min(n, 4000)):
            normalized_link = _extract_link_from_locator(loc, i)
            if normalized_link:
                links.add(normalized_link)
    
    return sorted(links)

def first(v):
    if isinstance(v, list) and v: return v[0]
    if isinstance(v, str): return v
    return None

def _parse_start_date(iso):
    """Parse start date and time from ISO string."""
    if not isinstance(iso, str):
        return None, None
    m = re.match(r"^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})", iso)
    if m:
        return m.group(1), m.group(2)
    return None, None


def _parse_location(loc):
    """Parse venue and place from location object."""
    venue = None
    place = None
    if isinstance(loc, dict):
        venue = first(loc.get("name"))
        addr = loc.get("address")
        if isinstance(addr, dict):
            place = addr.get("addressLocality") or addr.get("addressRegion")
    return venue, place


def _parse_price_from_dict(offers):
    """Parse price from offers dictionary."""
    cur = offers.get("priceCurrency") or ""
    low = offers.get("lowPrice")
    high = offers.get("highPrice")
    p = offers.get("price")
    
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
    elif isinstance(offers, list) and offers:
        return _parse_price_from_list(offers)
    return None


def parse_jsonld_event(obj):
    """Parse JSON-LD event object into structured data."""
    out = {"title": None, "date": None, "time": None, "venue": None, "place": None, "price": None}
    out["title"] = obj.get("name") or obj.get("headline")
    
    # Parse date and time
    iso = first(obj.get("startDate"))
    out["date"], out["time"] = _parse_start_date(iso)
    
    # Parse location
    loc = obj.get("location")
    out["venue"], out["place"] = _parse_location(loc)
    
    # Parse price
    offers = obj.get("offers")
    out["price"] = _parse_price(offers)
    
    return out

def _get_script_count(scripts):
    """Safely get count of script elements."""
    try:
        return scripts.count()
    except (TimeoutError, AttributeError, TypeError):
        return 0


def _parse_script_data(scripts, index):
    """Parse JSON data from script element at index."""
    try:
        data = scripts.nth(index).inner_text()
        if not data:
            return None
        return json.loads(data)
    except (json.JSONDecodeError, AttributeError, TypeError):
        return None


def _is_event_type(obj):
    """Check if object is an Event type."""
    if not isinstance(obj, dict):
        return False
    t = obj.get("@type")
    return t == "Event" or (isinstance(t, list) and "Event" in t)


def _merge_event_data(row, event_data):
    """Merge parsed event data into row."""
    for k, v in event_data.items():
        if v and not row[k]:
            row[k] = v


def _extract_events_from_data(data):
    """Extract event objects from parsed JSON data."""
    items = data if isinstance(data, list) else [data]
    return [it for it in items if _is_event_type(it)]


def _get_page_title_fallback(page):
    """Get page title as fallback if no event title found."""
    try:
        return (page.title() or "").strip() or None
    except (TimeoutError, AttributeError, TypeError):
        return None


def parse_event(page):
    """Parse event data from page JSON-LD scripts."""
    row = {"title": None, "date": None, "time": None, "venue": None, "place": None, "price": None}
    scripts = page.locator("script[type='application/ld+json']")
    n = _get_script_count(scripts)
    
    for i in range(n):
        data = _parse_script_data(scripts, i)
        if not data:
            continue
        
        events = _extract_events_from_data(data)
        for event_obj in events:
            got = parse_jsonld_event(event_obj)
            _merge_event_data(row, got)
        
        if row["title"]:
            break
    
    if not row["title"]:
        row["title"] = _get_page_title_fallback(page)
    
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

def _free_port(start=8000):
    import socket
    port = start
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                port += 1

def _serve(open_browser: bool):
    port = _free_port()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), SimpleHTTPRequestHandler)
    url = f"http://127.0.0.1:{port}/events.html"
    if open_browser:
        webbrowser.open(url)
    print(f"[server] {url}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

def scrape_bookmyshow_events(city="Mumbai", limit=100, headless=True):
    """Scrape BookMyShow events and return as list of dictionaries"""
    # Security Hotspot Review: random.choice() is used for selecting user agents for web scraping.
    # This is NOT security-sensitive as it's only used to randomize HTTP headers to avoid detection,
    # not for cryptographic purposes. The pseudorandom number generator is sufficient for this use case.
    ua = random.choice(UAS)
    rows = []

    with sync_playwright() as p:
        launch_kwargs = {"headless": headless}
        browser = p.chromium.launch(**launch_kwargs)
        # Security Hotspot Review: random.randint() is used for viewport dimensions to randomize browser
        # fingerprinting during web scraping. This is NOT security-sensitive as it's only used to avoid
        # detection, not for cryptographic purposes. The pseudorandom number generator is sufficient.
        ctx = browser.new_context(
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            user_agent=ua,
            viewport={"width": random.randint(1280, 1600), "height": random.randint(800, 1000)},
            java_script_enabled=True,
        )
        # light stealth
        ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
        ctx.set_extra_http_headers({"Accept-Language": "en-IN,en;q=0.9", "Upgrade-Insecure-Requests": "1"})
        page = ctx.new_page()

        ok, err = retry_goto(page, home(city))
        # Security Hotspot Review: random.uniform() used for timing delays (non-cryptographic)
        consent(page); time.sleep(0.3 + random.uniform(0.1, 0.4))
        if not ok: print("[warn] home nav failed:", err)

        ok, err = retry_goto(page, events(city))
        # Security Hotspot Review: random.uniform() used for timing delays (non-cryptographic)
        consent(page); time.sleep(0.3 + random.uniform(0.1, 0.4))
        if not ok: print("[warn] events nav failed:", err)

        scroll_until_stable(page)

        links = collect_links(page)
        print(f"Found {len(links)} links")
        for i, url in enumerate(links[: limit], 1):
            print(f"[{i}/{min(len(links), limit)}] {url}")
            ok, err = retry_goto(page, url, attempts=3, wait="domcontentloaded", timeout=60000)
            # Security Hotspot Review: random.uniform() used for timing delays (non-cryptographic)
            consent(page); time.sleep(0.35 + random.uniform(0.05, 0.35))
            if not ok:
                print("  -> skip (nav failed):", err)
                continue
            data = parse_event(page); data["url"] = url
            rows.append(data)
            # Security Hotspot Review: random.uniform() used for timing delays (non-cryptographic)
            time.sleep(0.25 + random.uniform(0.05, 0.25))

        ctx.close(); browser.close()

    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="Mumbai")
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--headless", type=int, default=0)
    ap.add_argument("--out", default="events.csv")
    ap.add_argument("--proxy", default="", help="http://user:pass@host:port")
    ap.add_argument("--serve", action="store_true", help="Serve events.html + events.csv locally")
    ap.add_argument("--open", action="store_true", help="Open browser to served events.html")
    args = ap.parse_args()

    rows = scrape_bookmyshow_events(args.city, args.limit, bool(args.headless))

    # atomic write to avoid PermissionError on Windows
    out = Path(args.out)
    tmp = out.with_suffix(".csv.tmp")
    pd.DataFrame(rows, columns=FIELDS).to_csv(tmp, index=False, encoding="utf-8-sig")
    os.replace(tmp, out)
    print("Saved:", out.resolve())

    if args.serve or args.open:
        html = Path("events.html")
        if not html.exists():
            html.write_text("<!doctype html><meta charset='utf-8'><p>Place your events.html here.</p>", encoding="utf-8")
        _serve(open_browser=args.open)

if __name__ == "__main__":
    main()
