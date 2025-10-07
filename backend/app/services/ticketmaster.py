import os
import requests

TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")
BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

def fetch_events(query="", city="", start_date=None, size=12):
    """
    Fetch Ticketmaster events filtered by keyword, city, and date.
    """
    params = {
        "apikey": TICKETMASTER_API_KEY,
        "size": size,
        "sort": "date,asc",
        "countryCode": "CA",  # or remove if you want global
    }

    if query:
        params["keyword"] = query
    if city:
        params["city"] = city
    if start_date:
        params["startDateTime"] = start_date

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Ticketmaster API Error: {e}")
        return {}
