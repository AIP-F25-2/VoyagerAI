import os
from datetime import datetime
from typing import List, Dict, Any


def search_hotels(city: str, check_in: str | None = None, check_out: str | None = None, guests: int | None = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Stub provider for hotels search.

    If HOTEL_API_KEY is set, this function can be extended to call a real provider.
    Currently returns mocked results shaped for basic UI display.
    """
    _ = os.getenv("HOTEL_API_KEY")

    items: List[Dict[str, Any]] = []
    for i in range(max(1, min(limit, 10))):
        items.append({
            "id": f"mock_hotel_{i}",
            "name": f"Sample Hotel {i+1}",
            "city": city,
            "address": f"{i+1} Main Street, {city}",
            "rating": 4.2,
            "price_per_night": "₹4,200",
            "url": "https://example.com/hotel",
            "check_in": check_in,
            "check_out": check_out,
        })
    return items


