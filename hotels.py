import requests
import csv

# --- CONFIG ---
url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"   # Correct endpoint

querystring = {
    "dest_id": "-1746441",  # Berlin city id
    "search_type": "CITY",
    "arrival_date": "2025-10-16",
    "departure_date": "2025-10-20",
    "adults": "1",
    "children_age": "",
    "room_qty": "1",
    "page_number": "1",
    "units": "metric",
    "locale": "en-us",
    "currency_code": "EUR",
    "sort_by": "popularity"
}

headers = {
    "x-rapidapi-key": "3d70da5d02mshe6f3e5b0ce2006cp14cf26jsn21e17c2df56d",
    "x-rapidapi-host": "booking-com15.p.rapidapi.com"
}

# --- MAKE REQUEST ---
response = requests.get(url, headers=headers, params=querystring)

if response.status_code == 200:
    data = response.json()

    hotels = data.get("data", {}).get("hotels", [])  # Correct path

    if hotels:
        csv_file = "berlin_hotels.csv"

        with open(csv_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            # Header
            writer.writerow(["Hotel Name", "Address", "Price (EUR)", "Review Score"])

            # Extract data
            for hotel in hotels:
                name = hotel.get("hotel_name", "N/A")
                address = hotel.get("address", "N/A")

                price_info = hotel.get("price_breakdown", {})
                price = price_info.get("all_inclusive_price", "N/A")

                review = hotel.get("review_score", "N/A")

                writer.writerow([name, address, price, review])

        print(f"Successfully saved {len(hotels)} hotels to {csv_file}")

    else:
        print("No hotels found or response changed.")
else:
    print(f"Error: {response.status_code}, {response.text}")
