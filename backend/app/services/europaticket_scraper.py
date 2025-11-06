#!/usr/bin/env python3
"""
europaticket_scraper.py

Scrapes europaticket.com events for given month ranges and writes a single CSV.

Fields saved:
- title, date, time, price, venue, city, url, description

Usage:
    python europaticket_scraper.py
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import datetime
from urllib.parse import urljoin, urlparse
import csv
import sys

BASE = "https://www.europaticket.com"
SEARCH_PATH = "/en/calendar"   # calendar/search endpoint
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
}

# months to collect (month numbers). The user requested Oct, Nov, Dec, Jan 2025.
TARGET_MONTHS = [
    (2025, 10),
    (2025, 11),
    (2025, 12),
    (2025, 1),   # Jan 2025
]

OUT_CSV = "europaticket_events_oct-nov-dec-jan_2025.csv"
REQUEST_DELAY = 1.0  # seconds between requests (be polite)


def month_date_range(year: int, month: int):
    """Return start and end date strings in dd-mm-yyyy format for the given month."""
    start = datetime.date(year, month, 1)
    # handle month wrap for January (month 1) and months near year boundaries
    if month == 12:
        end = datetime.date(year, 12, 31)
    else:
        # next month - 1 day
        next_month_first = datetime.date(year + (1 if month == 12 else 0),
                                         (month % 12) + 1, 1)
        end = next_month_first - datetime.timedelta(days=1)
    return start.strftime("%d-%m-%Y"), end.strftime("%d-%m-%Y")


def build_search_url(start_dd_mm_yyyy: str, end_dd_mm_yyyy: str, page: int = None):
    """
    Build a search URL that filters events by time range.
    Example: /en/calendar?artist=&city=&genre=&query=&time=01-02-2025-28-02-2025&venue=
    """
    q = f"{BASE}{SEARCH_PATH}?artist=&city=&genre=&query=&time={start_dd_mm_yyyy}-{end_dd_mm_yyyy}&venue="
    if page is not None and page > 1:
        # some sites use pagination param; try appending &page=N - works if site supports it
        q += f"&page={page}"
    return q


def get_soup(url):
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def extract_event_links_from_search_soup(soup):
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
            full = urljoin(BASE, href)
            links.add(full)
    return sorted(links)


def parse_event_page(event_url):
    """
    Visit event page and extract title, date, time, price, venue, city, description.
    Since HTML structure may change, try multiple heuristics.
    """
    try:
        soup = get_soup(event_url)
    except Exception as e:
        print(f"[WARN] Failed to fetch event page {event_url}: {e}", file=sys.stderr)
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


def scrape_month(year, month):
    start_str, end_str = month_date_range(year, month)
    print(f"[INFO] scraping {year}-{str(month).zfill(2)}: {start_str} -> {end_str}")
    page = 1
    all_event_urls = set()
    while True:
        url = build_search_url(start_str, end_str, page=page)
        try:
            soup = get_soup(url)
        except Exception as e:
            print(f"[ERROR] failed to fetch search page {url}: {e}", file=sys.stderr)
            break

        links = extract_event_links_from_search_soup(soup)
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
        time.sleep(REQUEST_DELAY)

        # Heuristic stop: if pagination isn't supported, we break after page 1.
        # If we detect a "next" link on the search results, continue; otherwise stop.
        next_btn = soup.find("a", string=lambda s: s and ("Next" in s or "next" in s or "›" in s))
        if not next_btn:
            break

    # Now visit each event page
    results = []
    for idx, event_url in enumerate(sorted(all_event_urls)):
        print(f"    [{idx+1}/{len(all_event_urls)}] parsing {event_url}")
        data = parse_event_page(event_url)
        if data:
            results.append(data)
        time.sleep(REQUEST_DELAY)

    return results


def scrape_europaticket_events(target_months=None, limit=50):
    """Scrape EuropaTicket events and return as list of dictionaries"""
    if target_months is None:
        target_months = TARGET_MONTHS
    
    all_results = []
    for year, month in target_months:
        res = scrape_month(year, month)
        all_results.extend(res)
        if len(all_results) >= limit:
            break

    return all_results[:limit]


def main():
    all_results = []
    for year, month in TARGET_MONTHS:
        res = scrape_month(year, month)
        all_results.extend(res)

    if not all_results:
        print("[WARN] No events found. Check selectors or site layout.")
        return

    # Normalize and write CSV
    df = pd.DataFrame(all_results)
    # reorder columns
    cols = ["title", "date", "time", "price", "venue", "city", "url", "description"]
    for c in cols:
        if c not in df.columns:
            df[c] = None
    df = df[cols]
    df.to_csv(OUT_CSV, index=False, quoting=csv.QUOTE_NONNUMERIC)
    print(f"[DONE] saved {len(df)} events to {OUT_CSV}")


if __name__ == "__main__":
    main()
