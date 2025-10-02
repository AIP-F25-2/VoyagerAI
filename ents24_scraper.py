#!/usr/bin/env python3
"""
ents24_scraper.py - Scrapes events for the selected months.
"""

import requests, time, datetime, csv, sys
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- CONFIG ---
BASE = "https://www.europaticket.com"
SEARCH = "/en/calendar"
HEADERS = {"User-Agent": "Mozilla/5.0"}
TARGET_MONTHS = [(2025, 10)]  # Only October 2025 for initial testing
OUT_CSV = "europaticket_events.csv"
DELAY = 0.5  # Delay between requests
MAX_EVENTS = 5  # Limit to 5 events for testing; increase for full scrape

# --- HELPERS ---
def month_range(y, m):
    """Return start and end date strings for the given month in dd-mm-yyyy format."""
    start = datetime.date(y, m, 1)
    end = (datetime.date(y+1, 1, 1) - datetime.timedelta(days=1)) if m == 12 else (
        datetime.date(y, m+1, 1) - datetime.timedelta(days=1)
    )
    return start.strftime("%d-%m-%Y"), end.strftime("%d-%m-%Y")

def soup(url): 
    """Fetch the URL and parse it with BeautifulSoup."""
    return BeautifulSoup(requests.get(url, headers=HEADERS, timeout=20).text,"html.parser")

def search_urls(y, m):
    """Get event URLs for a given month, limited by MAX_EVENTS."""
    s, e = month_range(y, m)
    urls, page = set(), 1
    url = f"{BASE}{SEARCH}?time={s}-{e}&page={page}"  # first page only
    try: 
        sp = soup(url)
    except Exception as err: 
        print("[ERR]", err, url, file=sys.stderr)
        return urls
    links = {urljoin(BASE, a["href"]) for a in sp.find_all("a", href=True) if "/event/" in a["href"]}
    return set(list(links)[:MAX_EVENTS])  # limit to MAX_EVENTS

def parse_event(url):
    """Extract event details: title, description, venue, date, time, price."""
    try:
        sp = soup(url)
    except Exception as err:
        print("[WARN]", err, url, file=sys.stderr)
        return {}

    def gettxt(*cls):
        el = sp.find(class_=lambda c: c and any(k in c for k in cls))
        return el.get_text(" ", strip=True) if el else None

    # Title
    title = None
    if sp.find("h1"):
        title = sp.find("h1").get_text(strip=True)
    elif sp.find("h2"):
        title = sp.find("h2").get_text(strip=True)
    else:
        meta = sp.find("meta", {"property": "og:title"})
        if meta and meta.get("content"):
            title = meta["content"]

    # Description
    desc = None
    desc_tag = sp.find(class_="description")
    if desc_tag:
        desc = desc_tag.get_text(" ", strip=True)
    else:
        meta_desc = sp.find("meta", {"name": "description"})
        if meta_desc and meta_desc.get("content"):
            desc = meta_desc["content"]

    # Venue
    venue = next((a.get_text(strip=True) for a in sp.find_all("a", href=True) if "/venue/" in a["href"]), None)

    # Date, Time, Price
    time_tag = sp.find("time")
    date = time_tag.get("datetime") if time_tag and time_tag.get("datetime") else gettxt("date")
    time_val = gettxt("time")
    price = gettxt("price")

    return {
        "url": url,
        "title": title,
        "description": desc,
        "venue": venue,
        "date": date,
        "time": time_val,
        "price": price
    }

# --- MAIN ---
def main():
    results = []
    for y, m in TARGET_MONTHS:
        for i, u in enumerate(search_urls(y, m), 1):
            print(f"[{y}-{m:02d}] {i}: {u}")
            ev = parse_event(u)
            if ev: results.append(ev)
            time.sleep(DELAY)

    if results:
        df = pd.DataFrame(results)
        cols = ["title","date","time","price","venue","url","description"]
        df = df.reindex(columns=cols)
        df.to_csv(OUT_CSV, index=False, quoting=csv.QUOTE_NONNUMERIC)
        print(f"[DONE] {len(df)} events -> {OUT_CSV}")
    else:
        print("[WARN] No events found.")

if __name__ == "__main__":
    main()

