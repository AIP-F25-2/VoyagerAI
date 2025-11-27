import requests
import csv
import time

# --- CONFIG ---
url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination"

headers = {
    "x-rapidapi-key": "3d70da5d02mshe6f3e5b0ce2006cp14cf26jsn21e17c2df56d",
    "x-rapidapi-host": "booking-com15.p.rapidapi.com"
}

base_query = {
    "checkout_date": "2025-10-20",
    "units": "metric",
    "dest_type": "city",
    "dest_id": "-1746441",   # Berlin
    "adults_number": "1",
    "checkin_date": "2025-10-16",
    "order_by": "popularity",
    "locale": "en-us",
    "filter_by_currency": "EUR",
    "include_adjacency": "true"
}

# CSV SETUP
csv_file = "berlin_hotels_full.csv"
with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow([
        "Hotel Name", "Address", "Price (EUR)", "Review Score", 
        "Review Count", "Star Rating", "Latitude", "Longitude"
    ])

# FETCH MULTIPLE PAGES
page = 0
total_saved = 0

while True:
    print(f"Fetching page {page}...")

    query = base_query.copy()
    query["page_number"] = str(page)

    response = requests.get(url, headers=headers, params=query)

    if response.status_code != 200:
        print(f"Error: {response.status_code} -> {response.text}")
        break

    data = response.json()
    hotels = data.get("result", [])

    if not hotels:
        print("No more hotels found. Stopping.")
        break

    # Append hotels to CSV
    with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        for h in hotels:
            writer.writerow([
                h.get("hotel_name", "N/A"),
                h.get("address", "N/A"),
                h.get("price_breakdown", {}).get("all_inclusive_price", "N/A"),
                h.get("review_score", "N/A"),
                h.get("review_nr", "N/A"),
                h.get("class", "N/A"),  # star rating
                h.get("location", {}).get("latitude", "N/A"),
                h.get("location", {}).get("longitude", "N/A")
            ])
            total_saved += 1

    page += 1
    time.sleep(1)  # avoid rate limits

print(f"\n✅ Completed! Saved total {total_saved} hotel records to {csv_file}")
