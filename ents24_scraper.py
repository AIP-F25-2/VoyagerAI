import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL of London events page
url = "https://www.ents24.com/whatson/london"

# Headers to avoid being blocked
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Ents24Scraper/1.0"
}

# Fetch the page
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Each event container
events = soup.select("li.event-listing")  # Updated selector

# Prepare a list to store data
event_list = []

for event in events:  # scrape all events on the page
    # Event Name
    title_el = event.select_one("h3 a")
    title = title_el.get_text(strip=True) if title_el else "N/A"
    event_url = title_el.get("href") if title_el else None
    if event_url and not event_url.startswith("http"):
        event_url = "https://www.ents24.com" + event_url

    # Event Date/Time
    date_el = event.select_one(".date")
    date_text = date_el.get_text(strip=True) if date_el else "N/A"

    # Venue
    venue_el = event.select_one(".venue")
    venue_text = venue_el.get_text(strip=True) if venue_el else "N/A"

    # Add to list
    event_list.append({
        "Title": title,
        "Date": date_text,
        "Venue": venue_text,
        "URL": event_url
    })

# Save to CSV
df = pd.DataFrame(event_list)
df.to_csv("london_events.csv", index=False)
print(f"Saved {len(event_list)} events to london_events.csv")
