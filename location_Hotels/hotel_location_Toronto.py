from playwright.sync_api import sync_playwright
import pandas as pd
import time, os

#  Choose your search city here
DESTINATION = "Toronto"

#  Choose your save path
OUTPUT_FILE = r"C:\Users\aniru\Desktop\datascraping US events\Trip\booking_hotels_full.csv"


def scrape_booking_hotels():
    all_hotels = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        page = browser.new_page()
        page.goto("https://www.booking.com/", wait_until="domcontentloaded", timeout=60000)
        print(" Opened Booking.com")

        # Close cookies popup if present
        try:
            page.locator('button:has-text("Accept")').first.click(timeout=4000)
            print(" Accepted cookies.")
        except:
            pass

        # Fill in destination
        search_box = page.locator('input[name="ss"]')
        search_box.fill(DESTINATION)
        page.keyboard.press("Enter")

        print(f"🔍 Searching hotels in {DESTINATION}...")
        page.wait_for_load_state("networkidle")
        time.sleep(5)

        page.wait_for_selector('[data-testid="property-card"]', timeout=40000)

        page_num = 1
        while True:
            print(f"\n Scraping page {page_num}...")
            page.wait_for_selector('[data-testid="property-card"]', timeout=40000)

            hotels = page.locator('[data-testid="property-card"]')
            count = hotels.count()
            print(f"  ➜ Found {count} hotels on this page")

            for i in range(count):
                try:
                    hotel = hotels.nth(i)
                    name = hotel.locator('[data-testid="title"]').inner_text().strip()
                    try:
                        rating = hotel.locator('[data-testid="review-score"]').inner_text().strip()
                    except:
                        rating = None

                    try:
                        reviews = hotel.locator('[data-testid="review-score"] + div').inner_text().strip()
                    except:
                        reviews = None

                    try:
                        price = hotel.locator('[data-testid="price-and-discounted-price"]').inner_text().strip()
                    except:
                        price = None

                    try:
                        location = hotel.locator('[data-testid="address"]').inner_text().strip()
                    except:
                        location = None

                    try:
                        url = hotel.locator('a').first.get_attribute('href')
                        if url and not url.startswith("http"):
                            url = "https://www.booking.com" + url
                    except:
                        url = None

                    all_hotels.append({
                        "Hotel Name": name,
                        "Location": location,
                        "Rating": rating,
                        "Reviews": reviews,
                        "Price": price,
                        "URL": url
                    })
                except Exception as e:
                    print(" Error reading hotel:", e)

            # Try to click the "Next page" button
            try:
                next_button = page.locator('button[aria-label="Next page"]').first
                if next_button.is_visible() and next_button.is_enabled():
                    print(" Moving to next page...")
                    next_button.click()
                    page.wait_for_load_state("networkidle")
                    time.sleep(4)
                    page_num += 1
                else:
                    print(" No more pages available.")
                    break
            except:
                print(" Reached last page.")
                break

        browser.close()

    # ✅ Save results
    df = pd.DataFrame(all_hotels)
    df.drop_duplicates(subset=["Hotel Name", "URL"], inplace=True)

    if len(df) > 0:
        df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
        abs_path = os.path.abspath(OUTPUT_FILE)
        print(f"\n Saved {len(df)} hotels to {abs_path}")
    else:
        print(" No data scraped; CSV not saved.")


if __name__ == "__main__":
    scrape_booking_hotels()
