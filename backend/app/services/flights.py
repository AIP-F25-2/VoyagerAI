import os
from typing import List, Dict, Any


def search_flights(origin: str, destination: str, departure_date: str, return_date: str | None = None, adults: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
    """Stub provider for flights search.

    If FLIGHT_API_KEY is set, this function can be extended to call a real provider
    such as Amadeus/Skyscanner. Currently returns mocked results.
    """
    _ = os.getenv("FLIGHT_API_KEY")

    items: List[Dict[str, Any]] = []
    for i in range(max(1, min(limit, 10))):
        items.append({
            "id": f"mock_flight_{i}",
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "airline": "Sample Air",
            "flight_number": f"SA{i+101}",
            "price": "₹12,500",
            "url": "https://example.com/flight"
        })
    return items


