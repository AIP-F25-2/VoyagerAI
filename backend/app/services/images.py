import os
import requests
from typing import Optional


PIXABAY_ENDPOINT = "https://pixabay.com/api/"


def search_pixabay_image(query: str) -> Optional[str]:
    """Return a copyright-free image URL from Pixabay for the query.

    Requires PIXABAY_API_KEY. Returns a largeImageURL or webformatURL if found.
    """
    api_key = os.getenv("PIXABAY_API_KEY")
    if not api_key:
        return None
    try:
        params = {
            "key": api_key,
            "q": query,
            "image_type": "photo",
            "safesearch": "true",
            "per_page": 5,
            "orientation": "horizontal",
        }
        res = requests.get(PIXABAY_ENDPOINT, params=params, timeout=8)
        res.raise_for_status()
        data = res.json()
        hits = data.get("hits") or []
        if not hits:
            return None
        first = hits[0]
        return first.get("largeImageURL") or first.get("webformatURL") or None
    except Exception:
        return None


