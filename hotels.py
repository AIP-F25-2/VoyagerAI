import requests

url = "https://booking-com.p.rapidapi.com/v1/hotels/search"

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
    "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
    "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

if response.status_code == 200:
    data = response.json()
    hotels = data.get('result', [])
    for hotel in hotels:
        print(f"Name: {hotel.get('hotel_name')}, Address: {hotel.get('address')}, Price: {hotel.get('price_breakdown', {}).get('all_inclusive_price')}")
else:
    print(f"Error: {response.status_code}")
