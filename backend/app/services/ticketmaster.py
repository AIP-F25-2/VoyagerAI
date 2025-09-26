import requests
import os

def fetch_events(keyword="music", country="CA"):
    """Fetch events from Ticketmaster Discovery API"""
    apikey = os.getenv("TICKETMASTER_API_KEY")
    if not apikey:
        return {"error": "Missing Ticketmaster API Key"}

    url = (
        f"https://app.ticketmaster.com/discovery/v2/events.json"
        f"?apikey={apikey}&keyword={keyword}&countryCode={country}&size=5"
    )

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # Debug log
        print("Ticketmaster Raw API Response:", data)

        return data
    except Exception as e:
        return {"error": str(e)}
