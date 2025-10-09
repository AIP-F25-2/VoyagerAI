import argparse, json, os, random, re, time, webbrowser, socket
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import psycopg2
import pandas as pd
from playwright.sync_api import sync_playwright

# ------------------ CONFIG ------------------
BASE = "https://in.bookmyshow.com"
FIELDS = ["title", "date", "time", "venue", "place", "price", "url"]
# Encode @ in password as %40
SUPABASE_URL = "postgresql://postgres:Voyagerai_lcit@db.ykjgsjxbdmcuvenewkdk.supabase.co:5432/postgres"

UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]

# ------------------ HELPERS ------------------
def slug(s): return s.strip().lower().replace(" ", "-")
def home(city): return f"{BASE}/explore/home?city={slug(city)}"
def events(city): return f"{BASE}/explore/events-{slug(city)}"

def consent(page):
    for sel in ["#wzrk-confirm", "button:has-text('Accept')", "button:has-text('I Agree')", "button:has-text('Allow All')"]:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=700):
                loc.click()
                time.sleep(0.2)
                return
        except:
            pass

def scroll_until_stable(page, max_loops=18, pause=0.6):
    last = 0
    stable = 0
    for _ in range(max_loops):
        page.mouse.wheel(0, 2400)
        time.sleep(pause + random.uniform(0.05, 0.25))
        try:
            h = page.evaluate("document.body.scrollHeight")
        except:
            break
        if h == last:
            stable += 1
            if stable >= 3:
                break
        else:
            stable = 0
            last = h

def collect_links(page):
    links = set()
    for css in ["a[href*='/events/']", "a[href*='/activities/']", "a[href*='/buytickets/']"]:
        loc = page.locator(css)
        try:
            n = loc.count()
        except:
            n = 0
        for i in range(min(n, 4000)):
            try:
                href = loc.nth(i).get_attribute("href")
                if not href:
                    continue
                if href.startswith("/"):
                    href = BASE + href
                if "/movies/" in href:
                    continue
                links.add(href.split("?")[0])
            except:
                pass
    return sorted(links)

def first(v):
    if isinstance(v, list) and v:
        return v[0]
    if isinstance(v, str):
        return v
    return None

def parse_jsonld_event(obj):
    out = {"title": None, "date": None, "time": None, "venue": None, "place": None, "price": None}
    out["title"] = obj.get("name") or obj.get("headline")
    iso = first(obj.get("startDate"))
    if isinstance(iso, str):
        m = re.match(r"^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})", iso)
        if m:
            out["date"], out["time"] = m.group(1), m.group(2)
    loc = obj.get("location")
    if isinstance(loc, dict):
        out["venue"] = first(loc.get("name"))
        addr = loc.get("address")
        if isinstance(addr, dict):
            out["place"] = addr.get("addressLocality") or addr.get("addressRegion")
    offers = obj.get("offers")
    if isinstance(offers, dict):
        cur = offers.get("priceCurrency") or ""
        low, high, p = offers.get("lowPrice"), offers.get("highPrice"), offers.get("price")
        if low and high:
            out["price"] = f"{cur} {low}-{high}"
        elif low:
            out["price"] = f"{cur} {low}"
        elif p:
            out["price"] = f"{cur} {p}"
    elif isinstance(offers, list) and offers:
        cur = offers[0].get("priceCurrency") or ""
        p = offers[0].get("price")
        out["price"] = f"{cur} {p}" if p else None
    return out

def parse_event(page):
    row = {"title": None, "date": None, "time": None, "venue": None, "place": None, "price": None}
    scripts = page.locator("script[type='application/ld+json']")
    try:
        n = scripts.count()
    except:
        n = 0
    for i in range(n):
        try:
            data = scripts.nth(i).inner_text()
            if not data:
                continue
            data = json.loads(data)
        except:
            continue
        items = data if isinstance(data, list) else [data]
        for it in items:
            if isinstance(it, dict):
                t = it.get("@type")
                if t == "Event" or (isinstance(t, list) and "Event" in t):
                    got = parse_jsonld_event(it)
                    for k, v in got.items():
                        if v and not row[k]:
                            row[k] = v
        if row["title"]:
            break
    if not row["title"]:
        try:
            row["title"] = (page.title() or "").strip() or None
        except:
            pass
    return row

def retry_goto(page, url, attempts=3, wait="domcontentloaded", timeout=60000):
    last = None
    for i in range(attempts):
        try:
            page.goto(url, wait_until=wait, timeout=timeout)
            return True, None
        except Exception as e:
            last = e
            time.sleep(1.2 + i * 0.8 + random.uniform(0.2, 0.6))
    return False, last

# ------------------ SUPABASE ------------------
def insert_to_supabase(df):
    try:
        conn = psycopg2.connect(SUPABASE_URL)
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS events_bms (
                id SERIAL PRIMARY KEY,
                title TEXT,
                date TEXT,
                time TEXT,
                url TEXT UNIQUE
            );
        """)

        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO events_bms (title, date, time,url)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING;
            """, (
                row.get("title"),
                row.get("date"),
                row.get("time"),
                row.get("url"),
            ))

        conn.commit()
        cur.close()
        conn.close()
        print(f"[DB] Inserted {len(df)} rows into Supabase successfully.")
    except Exception as e:
        print("[DB ERROR]", e)

# ------------------ MAIN ------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="Chennai")
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--headless", type=int, default=1)
    ap.add_argument("--out", default="events_bms.csv")
    args = ap.parse_args()

    ua = random.choice(UAS)
    rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=bool(args.headless))
        ctx = browser.new_context(
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            user_agent=ua,
            viewport={"width": random.randint(1280, 1600), "height": random.randint(800, 1000)},
        )
        page = ctx.new_page()

        ok, err = retry_goto(page, home(args.city))
        consent(page)
        if not ok: print("[warn] home nav failed:", err)

        ok, err = retry_goto(page, events(args.city))
        consent(page)
        if not ok: print("[warn] events nav failed:", err)

        scroll_until_stable(page)
        links = collect_links(page)
        print(f"Found {len(links)} links")

        for i, url in enumerate(links[: args.limit], 1):
            print(f"[{i}/{min(len(links), args.limit)}] {url}")
            ok, err = retry_goto(page, url, attempts=3, wait="domcontentloaded", timeout=60000)
            consent(page)
            if not ok:
                print("  -> skip (nav failed):", err)
                continue
            data = parse_event(page)
            data["url"] = url
            rows.append(data)
            time.sleep(0.4)

        ctx.close()
        browser.close()

    df = pd.DataFrame(rows, columns=FIELDS)
    df.to_csv(args.out, index=False, encoding="utf-8-sig")
    print(f"[DONE] Saved {len(df)} events to {args.out}")

    insert_to_supabase(df)

if __name__ == "__main__":
    main()
