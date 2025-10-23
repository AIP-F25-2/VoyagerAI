import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time

# -----------------------
# Configuration
# -----------------------
CITIES = ["mumbai", "delhi", "ahmedabad"]
MONTHS = ["2025-11", "2025-12", "2026-01"]  # Nov, Dec, Jan
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# Ask user for stay duration
try:
    STAY_DURATION = int(input("Enter number of nights to stay: ").strip())
    if STAY_DURATION <= 0:
        raise ValueError
except ValueError:
    print("Invalid input. Defaulting to 2 nights.")
    STAY_DURATION = 2

# -----------------------
# Helper: generate date ranges
# -----------------------
def generate_dates(month):
    start_date = datetime.strptime(month + "-01", "%Y-%m-%d")
    next_month = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
    days_in_month = (next_month - start_date).days
    return [start_date + timedelta(days=i) for i in range(0, days_in_month, 5)]  # every 5 days

# -----------------------
# Scrape function
# -----------------------
def scrape_booking(city, checkin, checkout):
    url = (
        f"https://www.booking.com/searchresults.html"
        f"?ss={city}&checkin_year={checkin.year}&checkin_month={checkin.month}&checkin_monthday={checkin.day}"
        f"&checkout_year={checkout.year}&checkout_month={checkout.month}&checkout_monthday={checkout.day}"
        f"&rows=25"
    )
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    hotels = []
    listings = soup.select("div[data-testid='property-card']")
    for item in listings:
        name = item.select_one("div[data-testid='title']")
        name = name.get_text(strip=True) if name else None
        price = item.select_one("span[data-testid='price-and-discounted-price']")
        price = price.get_text(strip=True) if price else None
        rating = item.select_one("div[data-testid='review-score']")
        rating = rating.get_text(strip=True).split("\n")[0] if rating else None
        location = item.select_one("span[data-testid='address']")
        location = location.get_text(strip=True) if location else None
        link = item.select_one("a[data-testid='title-link']")
        link = "https://www.booking.com" + link['href'] if link else None

        hotels.append({
            "City": city.capitalize(),
            "Check-in": checkin.strftime("%Y-%m-%d"),
            "Check-out": checkout.strftime("%Y-%m-%d"),
            "Hotel Name": name,
            "Location": location,
            "Rating": rating,
            "Price": price,
            "URL": link
        })
    return hotels

# -----------------------
# Main logic
# -----------------------
all_data = []
for city in CITIES:
    for month in MONTHS:
        for checkin in generate_dates(month):
            checkout = checkin + timedelta(days=STAY_DURATION)
            print(f"Scraping {city.title()} from {checkin.date()} to {checkout.date()}...")
            try:
                hotels = scrape_booking(city, checkin, checkout)
                all_data.extend(hotels)
                time.sleep(2)  # avoid blocking
            except Exception as e:
                print(f"Error scraping {city} {checkin.date()}: {e}")
                continue

# -----------------------
# Save results
# -----------------------
df = pd.DataFrame(all_data)
df.to_csv("booking_hotels1.csv", index=False, encoding='utf-8-sig')
print(f"\n✅ Data saved to booking_hotels.csv ({len(df)} rows)")
