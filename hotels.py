import requests
import csv

# --- CONFIG ---
url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination"

querystring = {
    "checkout_date":"2025-10-20",
    "units":"metric",
    "dest_type":"city",
    "dest_id":"-1746441",  # Berlin city id
    "adults_number":"1",
    "checkin_date":"2025-10-16",
    "order_by":"popularity",
    "locale":"en-us",
    "filter_by_currency":"EUR",
    "page_number":"0",
    "include_adjacency":"true"
}

headers = {
    'x-rapidapi-key': "3d70da5d02mshe6f3e5b0ce2006cp14cf26jsn21e17c2df56d", # replace with your key
  'x-rapidapi-host': "booking-com15.p.rapidapi.com"
}

# --- MAKE REQUEST ---
response = requests.get(url, headers=headers, params=querystring)

if response.status_code == 200:
    data = response.json()
    hotels = data.get('result', [])

    if hotels:
        # --- CSV FILE SETUP ---
        csv_file = "berlin_hotels.csv"
        with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # write header
            writer.writerow(["Hotel Name", "Address", "Price (EUR)"])
            
            # write hotel data
            for hotel in hotels:
                name = hotel.get('hotel_name', 'N/A')
                address = hotel.get('address', 'N/A')
                price = hotel.get('price_breakdown', {}).get('all_inclusive_price', 'N/A')
                writer.writerow([name, address, price])

        print(f"Successfully saved {len(hotels)} hotels to {csv_file}")
    else:
        print("No hotels found.")
else:
    print(f"Error: {response.status_code}, {response.text}")
