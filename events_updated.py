#!/usr/bin/env python3
"""
europaticket_scraper.py

Scrapes europaticket.com events for Oct, Nov, Dec 2025 and Jan 2025,
and writes a single CSV.

Fields saved:
- title, date, time, price, venue, city, url, description

Usage:
    python europaticket_scraper.py
"""

import os
import re
import sys
import csv
import time
import datetime
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
import pandas as pd

# Optional: install psycopg2 if you plan to insert into Supabase
try:
    import psycopg2  # noqa: F401
    _HAVE_PG = True
except Exception:
    _HAVE_PG = False

BASE = "https://www.europaticket.com"
SEARCH_PATH = "/en/calendar"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    )
}

# Months to collect
TARGET_MONTHS = [
    (2025, 10),  # Oct 2025
]

OUT_CSV = "europaticket_events_oct-nov-dec-jan_2025.csv"
REQUEST_DELAY = 1.0  # seconds; be polite

# Heuristics
VENUE_HINTS = re.compile(
    r"(hall|theatre|theater|opera|palace|stadium|arena|church|auditorium|"
    r"konzerthaus|musikverein|philharm|basilica|house|teatro|palazzo)",
    re.I,
)
CITY_HINTS = re.compile(
    r"\b(Amsterdam|Athens|Barcelona|Berlin|Budapest|Copenhagen|Dresden|Florence|Lisbon|London|Madrid|Milan|Munich|Naples|Paris|Prague|Rome|Salzburg|Stockholm|Venice|Vienna|Zürich|Zurich)\b",
    re.I,
)


def month_date_range(year: int, month: int):
    """Return start and end date strings in dd-mm-yyyy for the given month."""
    start = datetime.date(year, month, 1)
    if month == 12:
        end = datetime.date(year, 12, 31)
    else:
        next_month_first = datetime.date(year, month + 1, 1)
        end = next_month_first - datetime.timedelta(days=1)
    return start.strftime("%d-%m-%Y"), end.strftime("%d-%m-%Y")


def build_search_url(start_dd_mm_yyyy: str, end_dd_mm_yyyy: str, page: int | None = None):
    """
    Example:
    /en/calendar?artist=&city=&genre=&query=&time=01-02-2025-28-02-2025&venue=
    """
    q = f"{BASE}{SEARCH_PATH}?artist=&city=&genre=&query=&time={start_dd_mm_yyyy}-{end_dd_mm_yyyy}&venue="
    if page and page > 1:
        q += f"&page={page}"
    return q


def get_soup(session: requests.Session, url: str) -> BeautifulSoup:
    r = session.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def extract_event_links_from_search_soup(soup: BeautifulSoup) -> list[str]:
    """
    Conservative approach: grab anchors that look like event pages.
    """
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/en/event/" in href or "/event/" in href:
            links.add(urljoin(BASE, href))
    return sorted(links)


def _url_date_fallback(event_url: str) -> str | None:
    """
    If the event link carries ?date=dd-mm-yyyy, normalize to yyyy-mm-dd.
    """
    try:
        q = parse_qs(urlparse(event_url).query)
        if "date" in q and q["date"]:
            ddmmyyyy = q["date"][0]
            d, m, y = ddmmyyyy.split("-")
            return f"{y}-{m}-{d}"
    except Exception:
        pass
    return None


def _nearby_text_time_guess(text: str) -> str | None:
    """
    Find times like 19:30, 8:00, etc.; prefer ones near 'start/begin/doors'.
    """
    times = list(re.finditer(r"\b([01]?\d|2[0-3]):[0-5]\d\b", text))
    if not times:
        return None
    key = re.compile(r"(start|begin|doors|performance|show|concert)\b", re.I)
    for m in times:
        window = text[max(0, m.start() - 60): m.end() + 60]
        if key.search(window):
            return m.group(0)
    return times[0].group(0)


def parse_event_page(session: requests.Session, event_url: str) -> dict:
    """
    Extract title, date, time, price, venue, city, description.
    Includes fallbacks for JS-loaded date/time.
    """
    try:
        soup = get_soup(session, event_url)
    except Exception as e:
        print(f"[WARN] Failed to fetch event page {event_url}: {e}", file=sys.stderr)
        return {}

    data = {
        "url": event_url,
        "title": None,
        "date": None,
        "time": None,
        "price": None,
        "venue": None,
        "city": None,
        "description": None,
    }

    # Title
    title_tag = soup.find("h1") or soup.find("h2")
    if title_tag:
        data["title"] = title_tag.get_text(strip=True)
    else:
        og = soup.find("meta", {"property": "og:title"})
        if og and og.get("content"):
            data["title"] = og["content"]

    # Description
    desc = None
    for cls in ("description", "event-description", "desc", "event__description"):
        el = soup.find(class_=lambda c: c and cls in c)
        if el:
            desc = el.get_text(" ", strip=True)
            break
    if not desc:
        meta_desc = soup.find("meta", {"name": "description"})
        if meta_desc and meta_desc.get("content"):
            desc = meta_desc["content"]
    data["description"] = desc

    # Venue (label-based, then heuristic)
    venue = None
    venue_label = soup.find(string=re.compile(r"\bVenue\b", re.I))
    if venue_label:
        parent = venue_label.find_parent() or soup
        h2 = parent.find_next("h2")
        if h2:
            venue = h2.get_text(" ", strip=True)
    if not venue:
        for h2 in soup.select("h2"):
            txt = h2.get_text(" ", strip=True)
            if VENUE_HINTS.search(txt):
                venue = txt
                break
        if not venue:
            for a in soup.find_all("a", href=True):
                if "/venue/" in a["href"]:
                    venue = a.get_text(" ", strip=True)
                    break
    data["venue"] = venue

    # City (near venue section, else regex from page)
    city = None
    if venue_label:
        block = venue_label.find_parent() or soup
        near_text = block.get_text(" ", strip=True)
        m = CITY_HINTS.search(near_text)
        if m:
            city = m.group(0)
    if not city:
        page_text_all = soup.get_text(" ", strip=True)
        m = CITY_HINTS.search((data["title"] or "") + " " + page_text_all)
        if m:
            city = m.group(0)
    data["city"] = city

    # Date
    date_val = None
    t = soup.find("time")
    if t and (t.get("datetime") or t.get_text(strip=True)):
        date_val = t.get("datetime") or t.get_text(" ", strip=True)
    if not date_val:
        for cls in ("date", "event-date", "event__date"):
            el = soup.find(class_=lambda c: c and cls in c)
            if el:
                date_val = el.get_text(" ", strip=True)
                break
    if not date_val:
        date_val = _url_date_fallback(event_url)
    data["date"] = date_val

    # Time
    page_text_all = soup.get_text(" ", strip=True)
    data["time"] = _nearby_text_time_guess(page_text_all)

    # Price
    price = None
    for cls in ("price", "event-price", "ticket-price"):
        el = soup.find(class_=lambda c: c and cls in c)
        if el:
            price = el.get_text(" ", strip=True)
            break
    if not price:
        for sym in ("€", "EUR", "£", "GBP", "$", "USD"):
            if sym in page_text_all:
                idx = page_text_all.find(sym)
                price = page_text_all[max(0, idx - 20): idx + 25].strip()
                break
    data["price"] = price

    return data


def scrape_month(session: requests.Session, year: int, month: int) -> list[dict]:
    start_str, end_str = month_date_range(year, month)
    print(f"[INFO] scraping {year}-{str(month).zfill(2)}: {start_str} -> {end_str}")
    page = 1
    all_event_urls = set()

    while True:
        url = build_search_url(start_str, end_str, page=page)
        try:
            soup = get_soup(session, url)
        except Exception as e:
            print(f"[ERROR] failed to fetch search page {url}: {e}", file=sys.stderr)
            break

        links = extract_event_links_from_search_soup(soup)
        if not links:
            break

        # dedupe
        new_links = 0
        for l in links:
            if l not in all_event_urls:
                all_event_urls.add(l)
                new_links += 1

        print(f"  page {page}: found {len(links)} links, {new_links} new")
        page += 1
        time.sleep(REQUEST_DELAY)

        # Heuristic pagination stop
        next_btn = soup.find("a", string=lambda s: s and ("Next" in s or "next" in s or "›" in s))
        if not next_btn:
            break

    # Visit each event page
    results = []
    urls_sorted = sorted(all_event_urls)
    for idx, event_url in enumerate(urls_sorted, 1):
        print(f"    [{idx}/{len(urls_sorted)}] parsing {event_url}")
        data = parse_event_page(session, event_url)
        if data:
            results.append(data)
        time.sleep(REQUEST_DELAY)

    return results


def insert_to_supabase(df):
    import psycopg2

    conn = psycopg2.connect(
        "postgresql://postgres:Voyagerai_lcit@db.ykjgsjxbdmcuvenewkdk.supabase.co:5432/postgres"
    )
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            title TEXT,
            date TEXT,
            time TEXT,
            price TEXT,
            venue TEXT,
            city TEXT,
            url TEXT UNIQUE,
            description TEXT
        );
    """)

    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO events (title, date, time, price, venue, city, url, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING;
        """, (
            row["title"], row["date"], row["time"], row["price"],
            row["venue"], row["city"], row["url"], row["description"]
        ))

    conn.commit()
    cur.close()
    conn.close()
    print(f"[DONE] inserted {len(df)} rows into Supabase DB")



def main():
    with requests.Session() as session:
        all_results = []
        for year, month in TARGET_MONTHS:
            all_results.extend(scrape_month(session, year, month))

    if not all_results:
        print("[WARN] No events found. Check selectors or site layout.")
        return

    # Normalize and write CSV
    df = pd.DataFrame(all_results)
    cols = ["title", "date", "time", "price", "venue", "city", "url", "description"]
    for c in cols:
        if c not in df.columns:
            df[c] = None
    df = df[cols]

    df.to_csv(OUT_CSV, index=False, quoting=csv.QUOTE_NONNUMERIC)
    print(f"[DONE] saved {len(df)} events to {OUT_CSV}")

    # Optional Supabase insert: uncomment if env vars set
    # insert_to_supabase(df)


if __name__ == "__main__":
    main()
