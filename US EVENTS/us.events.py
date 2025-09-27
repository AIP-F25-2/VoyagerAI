# eventbrite_event_pages_fixed.py
import time
import pandas as pd
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://www.eventbrite.ca/d/united-states/events/"
FIELDS = ["title", "date_time", "location", "price", "url"]

def get_event_details(page, url):
    """Open an event page and extract details"""
    try:
        page.goto(url, wait_until="networkidle", timeout=60000)
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
        print(f"⚠️ Failed to scrape {url}: {e}")
        return None

def main():
    all_rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f"Opening {URL} ...")
        page.goto(URL, wait_until="networkidle", timeout=60000)

        # Collect all unique event links
        cards = page.locator("a[href*='/e/']")
        n = cards.count()
        print(f"🔎 Found {n} event links")
        urls = set()
        for i in range(n):
            href = cards.nth(i).get_attribute("href")
            if href and "/e/" in href:   # ✅ FIXED
                if href.startswith("/"):
                    full_url = "https://www.eventbrite.ca" + href.split("?")[0]
                else:
                    full_url = href.split("?")[0]
                urls.add(full_url)

        print(f"✅ Unique event URLs: {len(urls)}")

        # Visit each event page
        for idx, url in enumerate(urls, 1):
            print(f"Scraping event {idx}/{len(urls)}: {url}")
            details = get_event_details(page, url)
            if details:
                all_rows.append(details)

        browser.close()

    if all_rows:
        out = Path("eventbrite_event_pages.csv")
        pd.DataFrame(all_rows, columns=FIELDS).to_csv(out, index=False, encoding="utf-8-sig")
        print(f"\n🎉 Done! Saved {len(all_rows)} events to:", out.resolve())
    else:
        print("No events scraped.")

if __name__ == "__main__":
    main()
