# goibibo_hotels_scraper.py
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import re
import random

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def _parse_price(text):
    if not text:
        return None
    m = re.search(r'[\d,]+(?:\.\d+)?', text.replace('\xa0',''))
    if not m:
        return None
    return float(m.group(0).replace(',', ''))

def scrape_goibibo_hotels(city, checkin, checkout, budget_per_night=None, min_stars=None, max_results=20, headless=True, timeout=30):
    """
    city: city name or city slug (e.g. 'mumbai')
    checkin, checkout: 'YYYY-MM-DD' (used for URL param construction)
    Returns list of dicts: {name, price, stars, location, raw}
    """
    # Build a search URL. Goibibo's site uses dynamic routes; this is a heuristic URL.
    # Example: https://www.goibibo.com/hotels/{city}-hotels/
    city_slug = city.replace(" ", "-").lower()
    url = f"https://www.goibibo.com/hotels/{city_slug}-hotels/?checkin={checkin}&checkout={checkout}"

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    viewport={"width":1280,"height":900},
    java_script_enabled=True
)

        page = context.new_page()
        page.set_default_timeout(timeout * 1000)
        try:
            page.goto(url)
            time.sleep(4 + random.random()*2)
            # accept cookie if present
            try:
                page.locator("button:has-text('Accept'), button:has-text('OK')").first.click(timeout=2000)
            except:
                pass

            # scroll to load more hotels
            for _ in range(8):
                page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                time.sleep(0.6 + random.random()*0.5)

            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            # selectors to find hotel cards
            cards = soup.select(".HotelCard, .hotelCard, .HotelCard__container, .listingCard") 
            if not cards:
                # alternative: look for items with hotel name class
                cards = soup.select("div")
            seen = 0
            for c in cards:
                if seen >= max_results:
                    break
                name_el = c.select_one(".HotelCard__hotelName, .hotelName, .hotel_name, .HotelName, .hotel-name")
                price_el = c.select_one(".OfferPrice, .price, .finalPrice, .actual-price, .priceAmt")
                stars_el = c.select_one(".starRating, .stars, .HotelCard__stars")

                name = name_el.get_text(strip=True) if name_el else None
                price = _parse_price(price_el.get_text()) if price_el else None
                stars = None
                if stars_el:
                    # parse numeric stars out of text
                    m = re.search(r'(\d)', stars_el.get_text())
                    if m:
                        stars = int(m.group(1))
                location = None
                loc_el = c.select_one(".HotelCard__locality, .locality, .hotel_location")
                if loc_el:
                    location = loc_el.get_text(strip=True)

                # filter out when no name or price
                if not name or price is None:
                    continue

                ok = True
                if budget_per_night and price:
                    try:
                        if price > float(budget_per_night):
                            ok = False
                    except:
                        pass
                if min_stars and stars:
                    try:
                        if stars < int(min_stars):
                            ok = False
                    except:
                        pass

                if ok:
                    results.append({
                        "name": name,
                        "price": price,
                        "stars": stars,
                        "location": location,
                        "raw": str(c)[:1000]
                    })
                    seen += 1

        finally:
            try:
                context.close()
                browser.close()
            except:
                pass

    # sort by price
    results = sorted(results, key=lambda x: (x["price"] if x["price"] is not None else 1e12))
    return results[:max_results]


if __name__ == "__main__":
    out = scrape_goibibo_hotels("mumbai", "2025-11-10", "2025-11-12", budget_per_night=8000, min_stars=3, max_results=10)
    for h in out:
        print(h)
