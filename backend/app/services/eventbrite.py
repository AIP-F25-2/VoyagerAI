import os
import requests

EVENTBRITE_TOKEN = os.getenv("EVENTBRITE_PRIVATE_TOKEN")
BASE_URL = "https://www.eventbriteapi.com/v3/events/search/"

def fetch_events(query="", location="", size=12):
    """
    Fetch Eventbrite events filtered by keyword and location.
    """
    headers = {"Authorization": f"Bearer {EVENTBRITE_TOKEN}"}
    params = {
        "expand": "venue",
        "sort_by": "date",
        "page_size": size,
    }

    if query:
        params["q"] = query
    if location:
        params["location.address"] = location

    try:
        response = requests.get(BASE_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Eventbrite API Error: {e}")
        return {}
