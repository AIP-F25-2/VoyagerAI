# skyscanner_scraper.py
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import random
import re

def _parse_price(text):
    if not text:
        return None
    m = re.search(r'[\d,]+(?:\.\d+)?', text.replace(',', ''))
    if not m:
        return None
    return float(m.group(0))

def scrape_skyscanner(origin, destination, depart_date, return_date=None, max_results=5):
    """
    Scrape Skyscanner for flights between origin and destination.
    Example: scrape_skyscanner("lhr","jfk","2025-11-01")
    """

    url = f"https://www.skyscanner.ca/"
    if return_date:
        url += f"{return_date}/"

    print(f"Scraping URL: {url}")

    with sync_playwright() as p:
        # Launch visible browser (non-headless)
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--disable-http2"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}
        )

        # Stealth: hide webdriver flag
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()

        try:
            page.goto(url)
            print("Loading Skyscanner page...")
            time.sleep(10)  # Wait for dynamic content

            # Scroll to load all results
            for _ in range(5):
                page.mouse.wheel(0, 5000)
                time.sleep(2)

            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Try several common selectors
            flight_cards = soup.select("div.FlightCard, div.result, li.DayViewCard, div.Itinerary")
            print(f"Found {len(flight_cards)} possible flight cards.")

            flights = []
            for card in flight_cards[:max_results]:
                text = card.get_text(" ", strip=True)
                price = None
                airline = None
                depart_time = None
                arrive_time = None
                duration = None

                # Price
                price_el = card.select_one(".price, .Price_mainPrice, .Price_text, [data-testid='flight-card-price']")
                if price_el:
                    price = _parse_price(price_el.get_text())

                # Airline
                airline_el = card.select_one(".airline-name, .AirlineName, [data-testid='airline-name']")
                if airline_el:
                    airline = airline_el.get_text(strip=True)

                # Times
                times = card.select("time")
                if len(times) >= 2:
                    depart_time, arrive_time = times[0].get_text(strip=True), times[1].get_text(strip=True)

                # Duration
                dur_el = card.select_one(".duration, .Duration, [data-testid='journey-duration']")
                if dur_el:
                    duration = dur_el.get_text(strip=True)

                if price or airline:
                    flights.append({
                        "airline": airline,
                        "price": price,
                        "depart_time": depart_time,
                        "arrive_time": arrive_time,
                        "duration": duration
                    })

            print(f"Extracted {len(flights)} flights.")
            browser.close()
            return flights

        except Exception as e:
            print("Error during scraping:", e)
            browser.close()
            return []
