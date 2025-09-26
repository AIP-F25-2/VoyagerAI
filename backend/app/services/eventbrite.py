import os
import requests

API_BASE = "https://www.eventbriteapi.com/v3"

def fetch_events(keyword="music", location=None, size=10):
    """Fetch events from Eventbrite with fallback if location fails."""
    token = os.getenv("EVENTBRITE_PRIVATE_TOKEN")
    if not token:
        return {"error": "Missing Eventbrite private token"}

    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": keyword, "expand": "venue", "page_size": size}

    if location:  # only add location if provided
        params["location.address"] = location

    try:
        resp = requests.get(f"{API_BASE}/events/search/", headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        # If no events found, retry without location filter
        if not data.get("events"):
            print("!!! No events found with location, retrying without it…")
            params.pop("location.address", None)
            resp = requests.get(f"{API_BASE}/events/search/", headers=headers, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

        print("Eventbrite RAW:", data)
        return data

    except Exception as e:
        return {"error": str(e)}
