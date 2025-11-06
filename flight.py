# ✅ Updated Booking.com Flight Scraper – Vancouver → Toronto (6 months)
# pip install playwright pandas tqdm
# playwright install

import time
import pandas as pd
from datetime import datetime, timedelta
from tqdm import tqdm
from playwright.sync_api import sync_playwright

def scrape_booking(origin_code="YVR", dest_code="YYZ", months=6):
    base_url = "https://www.booking.com/flights/searchresults.html"
    start_date = datetime.today()
    all_flights = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        page = browser.new_page()
        page.set_default_timeout(120000)

        total_days = months * 30
        print(f"🛫 Collecting {total_days} days of flights ({months} months)...")

        for i in tqdm(range(total_days)):
            date_str = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            url = f"{base_url}?origin={origin_code}&destination={dest_code}&depart={date_str}&adults=1"
            print(f"\n📅 {date_str} – loading results...")

            try:
                page.goto(url, timeout=90000)
                # wait until at least one flight card or error banner appears
                page.wait_for_selector("body", timeout=30000)
                page.wait_for_timeout(5000)

                # first: wait for main result cards (sometimes 'FlightCard' or 'itinerary-card')
                selectors = [
                    '[data-testid="itinerary-card"]',
                    '[data-testid="flight-card"]',
                    '.FlightCard__outer', 
                    '[data-testid*="flight-result-card"]'
                ]
                flight_elements = []
                for sel in selectors:
                    try:
                        page.wait_for_selector(sel, timeout=15000)
                        flight_elements = page.query_selector_all(sel)
                        if flight_elements:
                            break
                    except:
                        continue

                if not flight_elements:
                    print(f"⚠️ No flights found for {date_str}.")
                    continue

                print(f"✈️ Found {len(flight_elements)} flights.")

                for f in flight_elements:
                    try:
                        airline = f.query_selector('[data-testid="airline-name"]')
                        airline = airline.inner_text().strip() if airline else "N/A"

                        depart = f.query_selector('[data-testid*="leg-departure-time"]')
                        arrive = f.query_selector('[data-testid*="leg-arrival-time"]')
                        depart = depart.inner_text().strip() if depart else "N/A"
                        arrive = arrive.inner_text().strip() if arrive else "N/A"

                        duration = f.query_selector('[data-testid="leg-duration"]')
                        duration = duration.inner_text().strip() if duration else "N/A"

                        stops = f.query_selector('[data-testid="stops-text"]')
                        stops = stops.inner_text().strip() if stops else "N/A"

                        price = f.query_selector('[data-testid="itinerary-price-label"]')
                        price = price.inner_text().replace("$", "").replace(",", "").strip() if price else "N/A"

                        all_flights.append({
                            "date": date_str,
                            "origin": origin_code,
                            "destination": dest_code,
                            "airline": airline,
                            "depart_time": depart,
                            "arrive_time": arrive,
                            "duration": duration,
                            "stops": stops,
                            "price_cad": price
                        })
                    except Exception as e:
                        print("⚠️ Parse error:", e)
                        continue

                time.sleep(3)

            except Exception as e:
                print(f"⚠️ Error on {date_str}: {e}")
                continue

        browser.close()

    if all_flights:
        df = pd.DataFrame(all_flights)
        csv_name = f"booking_flights_{origin_code}_{dest_code}_next{months}months.csv"
        df.to_csv(csv_name, index=False)
        print(f"\n✅ Saved {len(df)} flight records to {csv_name}")
    else:
        print("\n❌ No flight data captured.")

if __name__ == "__main__":
    scrape_booking("YVR", "YYZ", 6)
