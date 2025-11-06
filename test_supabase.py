#!/usr/bin/env python3
"""
Fetch Berlin hotel data from Booking.com API and store results in Supabase
"""

import requests
import csv
import psycopg2

# --- CONFIG ---

# RapidAPI Booking.com settings
BOOKING_URL = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"
BOOKING_HEADERS = {
    "x-rapidapi-key": "3d70da5d02mshe6f3e5b0ce2006cp14cf26jsn21e17c2df56d",  # Replace with your valid key
    "x-rapidapi-host": "booking-com15.p.rapidapi.com"
}
BOOKING_QUERY = {
    "checkout_date": "2025-10-20",
    "units": "metric",
    "dest_type": "city",
    "dest_id": "-1746441",  # Berlin city ID
    "adults_number": "1",
    "checkin_date": "2025-10-16",
    "order_by": "popularity",
    "locale": "en-us",
    "filter_by_currency": "EUR",
    "page_number": "0",
    "include_adjacency": "true"
}

# Supabase PostgreSQL credentials
SUPABASE_CONN = {
    "host": "db.firxksjrdatingseueuw.supabase.co",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "Voyagerai@lcit"
}

# --- FUNCTIONS ---

def test_supabase_connection():
    """Test Supabase PostgreSQL connection"""
    print("Testing Supabase connection...")
    try:
        conn = psycopg2.connect(**SUPABASE_CONN)
        print("✅ Supabase connection successful!")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False


def fetch_hotels():
    """Fetch hotels from Booking.com API"""
    print("\nFetching hotel data from Booking.com...")
    response = requests.get(BOOKING_URL, headers=BOOKING_HEADERS, params=BOOKING_QUERY)
    if response.status_code == 200:
        data = response.json()
        hotels = data.get("data", [])
        if not hotels:
            print("⚠️ No hotels found in the response.")
        return hotels
    else:
        print(f"❌ API Error {response.status_code}: {response.text}")
        return []


def save_to_csv(hotels):
    """Save hotels to a CSV file"""
    csv_file = "berlin_hotels.csv"
    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Hotel Name", "Address", "Price (EUR)", "Rating"])
        for hotel in hotels:
            name = hotel.get("property", {}).get("name", "N/A")
            address = hotel.get("property", {}).get("address", {}).get("address", "N/A")
            price = hotel.get("property", {}).get("priceBreakdown", {}).get("grossPrice", {}).get("value", "N/A")
            rating = hotel.get("property", {}).get("reviewScore", "N/A")
            writer.writerow([name, address, price, rating])
    print(f"✅ Saved {len(hotels)} hotels to {csv_file}")


def save_to_supabase(hotels):
    """Insert hotel data into Supabase table"""
    try:
        conn = psycopg2.connect(**SUPABASE_CONN)
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS berlin_hotels (
                id SERIAL PRIMARY KEY,
                name TEXT,
                address TEXT,
                price_eur FLOAT,
                rating FLOAT
            );
        """)
        conn.commit()

        # Insert hotel data
        for hotel in hotels:
            name = hotel.get("property", {}).get("name", "N/A")
            address = hotel.get("property", {}).get("address", {}).get("address", "N/A")
            price = hotel.get("property", {}).get("priceBreakdown", {}).get("grossPrice", {}).get("value", None)
            rating = hotel.get("property", {}).get("reviewScore", None)
            cursor.execute(
                "INSERT INTO berlin_hotels (name, address, price_eur, rating) VALUES (%s, %s, %s, %s)",
                (name, address, price, rating)
            )

        conn.commit()
        print(f"✅ Inserted {len(hotels)} hotels into Supabase database.")
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Failed to insert into Supabase: {e}")


# --- MAIN EXECUTION ---

if __name__ == "__main__":
    if test_supabase_connection():
        hotels = fetch_hotels()
        if hotels:
            save_to_csv(hotels)
            save_to_supabase(hotels)
    else:
        print("⚠️ Skipping data insertion because Supabase connection failed.")
