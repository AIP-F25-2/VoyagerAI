#!/usr/bin/env python3
"""
FAST fetch of nearby tourist places for hotels using OpenStreetMap (city-level batching + caching).

Inputs (same folder):
  - booking_hotels.csv
  - booking_hotels1.csv
  - Final.csv

Columns used if present: City, Hotel Name, Location, URL

Environment variables (optional):
  NOMINATIM_USER_AGENT = "YourApp/1.0 (your@email)"   # REQUIRED by Nominatim policy
  SEARCH_RADIUS_M      = meters radius around city/hotel (default 3000)
  MAX_POIS_PER_CITY    = max POIs per city (default 250)
  MAX_POIS_PER_HOTEL   = max POIs kept per hotel after distance sort (default 80)
  GEOCODE_DELAY_SEC    = delay between geocoding calls (default 0.4)
  OVERPASS_DELAY_SEC   = delay between Overpass calls (default 0.5)
  HOTEL_GEOCODE        = "1" to geocode hotels (slower, more accurate distances). "0" default = skip.
  CACHE_TTL_DAYS       = days before city Overpass cache expires (default 14)

Output:
  nearby_tourist_places.csv
  geocode_cache.json
  overpass_city_cache.json
"""
import os
import time
import math
import csv
import sys
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional

import requests
import pandas as pd
from requests.adapters import HTTPAdapter, Retry

# -----------------------
# Config
# -----------------------
USER_AGENT = os.environ.get("NOMINATIM_USER_AGENT", "VoyagerAttractionsFetcher/1.0 (replace_with_your_email@example.com)")
SEARCH_RADIUS_M = int(os.environ.get("SEARCH_RADIUS_M", "3000"))
MAX_POIS_PER_CITY = int(os.environ.get("MAX_POIS_PER_CITY", "250"))
MAX_POIS_PER_HOTEL = int(os.environ.get("MAX_POIS_PER_HOTEL", "80"))
GEOCODE_DELAY_SEC = float(os.environ.get("GEOCODE_DELAY_SEC", "0.4"))
OVERPASS_DELAY_SEC = float(os.environ.get("OVERPASS_DELAY_SEC", "0.5"))
HOTEL_GEOCODE = os.environ.get("HOTEL_GEOCODE", "0") == "1"
CACHE_TTL_DAYS = int(os.environ.get("CACHE_TTL_DAYS", "14"))

INPUT_FILES = ["booking_hotels.csv", "booking_hotels1.csv", "Final.csv"]
OUTPUT_FILE = "nearby_tourist_places.csv"
GEOCODE_CACHE_FILE = "geocode_cache.json"
OVERPASS_CITY_CACHE_FILE = "overpass_city_cache.json"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Overpass categories (touristy + cultural + nature)
OVERPASS_TEMPLATE = r"""
[out:json][timeout:60];
(
  node[tourism~"^(attraction|museum|gallery|viewpoint|information)$"](around:{radius},{lat},{lon});
  way[tourism~"^(attraction|museum|gallery|viewpoint|information)$"](around:{radius},{lat},{lon});
  relation[tourism~"^(attraction|museum|gallery|viewpoint|information)$"](around:{radius},{lat},{lon});

  node[historic](around:{radius},{lat},{lon});
  way[historic](around:{radius},{lat},{lon});
  relation[historic](around:{radius},{lat},{lon});

  node[leisure~"^(park|garden)$"](around:{radius},{lat},{lon});
  way[leisure~"^(park|garden)$"](around:{radius},{lat},{lon});
  relation[leisure~"^(park|garden)$"](around:{radius},{lat},{lon});

  node[amenity~"^(theatre|fountain|place_of_worship|arts_centre)$"](around:{radius},{lat},{lon});
  way[amenity~"^(theatre|fountain|place_of_worship|arts_centre)$"](around:{radius},{lat},{lon});
  relation[amenity~"^(theatre|fountain|place_of_worship|arts_centre)$"](around:{radius},{lat},{lon});

  node[natural~"^(peak|wood|beach|cliff|spring|water)$"](around:{radius},{lat},{lon});
  way[natural~"^(peak|wood|beach|cliff|spring|water)$"](around:{radius},{lat},{lon});
  relation[natural~"^(peak|wood|beach|cliff|spring|water)$"](around:{radius},{lat},{lon});
);
out center {limit};
"""

# -----------------------
# HTTP session with retries
# -----------------------
session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})
retries = Retry(
    total=3,
    backoff_factor=0.8,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=frozenset(["GET", "POST"]),
)
session.mount("https://", HTTPAdapter(max_retries=retries))
session.mount("http://", HTTPAdapter(max_retries=retries))

# -----------------------
# Utils
# -----------------------
def haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

# -----------------------
# Caches
# -----------------------
def load_json(path: str, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default

def save_json(path: str, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)

geocode_cache: Dict[str, Any] = load_json(GEOCODE_CACHE_FILE, {})
overpass_city_cache: Dict[str, Any] = load_json(OVERPASS_CITY_CACHE_FILE, {})

def cache_key_city(city: str, radius: int) -> str:
    return hashlib.sha1(f"{city}|{radius}".encode("utf-8")).hexdigest()

def cache_fresh(ts_iso: str, ttl_days: int) -> bool:
    try:
        ts = datetime.fromisoformat(ts_iso.replace("Z", ""))
        return datetime.utcnow() - ts < timedelta(days=ttl_days)
    except Exception:
        return False

# -----------------------
# IO
# -----------------------
def read_inputs(files: List[str]) -> pd.DataFrame:
    frames = []
    for f in files:
        if not os.path.exists(f):
            continue
        try:
            df = pd.read_csv(f)
        except Exception:
            try:
                df = pd.read_excel(f)
            except Exception:
                continue
        df["__source_file"] = os.path.basename(f)
        frames.append(df)
    if not frames:
        raise FileNotFoundError("No input CSV/Excel files found among: " + ", ".join(files))
    merged = pd.concat(frames, ignore_index=True)

    for col in ["City", "Hotel Name", "Location", "URL"]:
        if col not in merged.columns:
            merged[col] = None

    keep_cols = ["__source_file", "City", "Hotel Name", "Location", "URL"]
    merged = merged[keep_cols].drop_duplicates().reset_index(drop=True)

    # keep rows with at least one location hint
    merged = merged[merged[["Location", "City", "Hotel Name"]].notnull().any(axis=1)]
    return merged

# -----------------------
# Geocoding
# -----------------------
def geocode(query: str) -> Optional[Tuple[float, float, str]]:
    q = query.strip()
    if not q:
        return None
    if q in geocode_cache and isinstance(geocode_cache[q], dict):
        entry = geocode_cache[q]
        return float(entry["lat"]), float(entry["lon"]), entry.get("display_name", "")
    params = {"q": q, "format": "json", "limit": 1}
    try:
        resp = session.get(NOMINATIM_URL, params=params, timeout=20)
        if resp.status_code == 429:
            time.sleep(2.0)
            resp = session.get(NOMINATIM_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None
        lat, lon = float(data[0]["lat"]), float(data[0]["lon"])
        disp = data[0].get("display_name", "")
        geocode_cache[q] = {"lat": lat, "lon": lon, "display_name": disp, "ts": now_iso()}
        save_json(GEOCODE_CACHE_FILE, geocode_cache)
        return lat, lon, disp
    except Exception:
        return None
    finally:
        time.sleep(GEOCODE_DELAY_SEC)

# -----------------------
# Overpass
# -----------------------
def fetch_overpass_city(lat: float, lon: float, radius_m: int, city_name: str) -> List[Dict[str, Any]]:
    key = cache_key_city(city_name.lower(), radius_m)
    cached = overpass_city_cache.get(key)
    if cached and isinstance(cached, dict) and cache_fresh(cached.get("ts", ""), CACHE_TTL_DAYS):
        return cached.get("elements", [])

    q = OVERPASS_TEMPLATE.format(radius=radius_m, lat=lat, lon=lon, limit=MAX_POIS_PER_CITY)
    try:
        resp = session.post(OVERPASS_URL, data=q.encode("utf-8"), timeout=60)
        if resp.status_code == 429:
            time.sleep(3.0)
            resp = session.post(OVERPASS_URL, data=q.encode("utf-8"), timeout=60)
        resp.raise_for_status()
        js = resp.json()
        elems = js.get("elements", [])
        overpass_city_cache[key] = {"ts": now_iso(), "elements": elems, "city": city_name, "lat": lat, "lon": lon, "radius": radius_m}
        save_json(OVERPASS_CITY_CACHE_FILE, overpass_city_cache)
        return elems
    except Exception:
        return []
    finally:
        time.sleep(OVERPASS_DELAY_SEC)

def normalize_poi(elem: Dict[str, Any]) -> Dict[str, Any]:
    tags = elem.get("tags", {}) or {}
    name = tags.get("name") or tags.get("alt_name") or ""
    poi_type = (
        tags.get("tourism") or
        tags.get("historic") or
        tags.get("leisure") or
        tags.get("amenity") or
        tags.get("natural") or
        ""
    )
    lat = elem.get("lat")
    lon = elem.get("lon")
    if lat is None or lon is None:
        c = elem.get("center") or {}
        lat = c.get("lat")
        lon = c.get("lon")
    return {
        "poi_name": name,
        "poi_type": poi_type,
        "poi_lat": lat,
        "poi_lon": lon,
        "osm_id": elem.get("id"),
        "osm_element_type": elem.get("type"),
        "raw_tags": tags
    }

# -----------------------
# Main
# -----------------------
def best_query_row(row: pd.Series) -> str:
    parts = []
    if pd.notna(row.get("Hotel Name")) and str(row["Hotel Name"]).strip():
        parts.append(str(row["Hotel Name"]).strip())
    if pd.notna(row.get("Location")) and str(row["Location"]).strip():
        parts.append(str(row["Location"]).strip())
    if pd.notna(row.get("City")) and str(row["City"]).strip():
        parts.append(str(row["City"]).strip())
    if not parts and pd.notna(row.get("URL")):
        parts.append(str(row["URL"]))
    return ", ".join(parts)

def main():
    # run from script folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    hotels = read_inputs(INPUT_FILES)

    # Optional per-hotel geocoding (off by default for speed)
    hotel_coords: Dict[int, Tuple[Optional[float], Optional[float], str]] = {}

    # 1) City-level batching
    out_rows = []
    grouped = hotels.groupby("City", dropna=True)

    for city, group in grouped:
        city_str = str(city).strip()
        if not city_str or city_str.lower() == "nan":
            continue

        # Geocode city once
        g = geocode(city_str)
        if not g:
            # Try a more specific query from a row
            sample_q = best_query_row(group.iloc[0])
            g = geocode(sample_q)
        if not g:
            # Skip this city
            continue
        city_lat, city_lon, city_disp = g

        # Fetch POIs once for the city
        elements = fetch_overpass_city(city_lat, city_lon, SEARCH_RADIUS_M, city_str)
        pois = [normalize_poi(e) for e in elements if (e.get("lat") or e.get("center")) and (e.get("lon") or e.get("center"))]

        # For speed, only geocode hotels if HOTEL_GEOCODE=1
        if HOTEL_GEOCODE:
            for idx, row in group.iterrows():
                q = best_query_row(row)
                h = geocode(q) or geocode(str(row.get("Location") or "")) or geocode(city_str)
                if h:
                    hotel_coords[idx] = (float(h[0]), float(h[1]), h[2])
                else:
                    hotel_coords[idx] = (None, None, "")
        else:
            # store None, we will compute distance from city center as proxy
            for idx, _ in group.iterrows():
                hotel_coords[idx] = (None, None, "")

        # Emit rows: compute distance per hotel either from hotel coord (accurate) or city center (fast)
        for idx, row in group.iterrows():
            hlat, hlon, hdisp = hotel_coords[idx]
            base_lat = hlat if hlat is not None else city_lat
            base_lon = hlon if hlon is not None else city_lon
            base_label = hdisp if hdisp else city_disp

            # sort per-hotel by distance and trim
            enriched = []
            for p in pois:
                plat, plon = p["poi_lat"], p["poi_lon"]
                if plat is None or plon is None:
                    continue
                d = haversine(float(base_lat), float(base_lon), float(plat), float(plon))
                enriched.append((d, p))
            enriched.sort(key=lambda x: x[0])
            if MAX_POIS_PER_HOTEL > 0:
                enriched = enriched[:MAX_POIS_PER_HOTEL]

            for dist_m, p in enriched:
                out_rows.append({
                    "source_file": row["__source_file"],
                    "city": city_str,
                    "hotel_name": row.get("Hotel Name"),
                    "location_text": row.get("Location"),
                    "url": row.get("URL"),
                    "hotel_lat": hlat,
                    "hotel_lon": hlon,
                    "hotel_geocoded_display_name": base_label if HOTEL_GEOCODE else "",
                    "city_lat": city_lat,
                    "city_lon": city_lon,
                    "city_geocoded_display_name": city_disp,
                    "poi_name": p["poi_name"],
                    "poi_type": p["poi_type"],
                    "poi_lat": p["poi_lat"],
                    "poi_lon": p["poi_lon"],
                    "distance_m": round(dist_m, 1),
                    "osm_id": p["osm_id"],
                    "osm_element_type": p["osm_element_type"],
                    "raw_tags": p["raw_tags"],
                })

    # 2) Handle rows with missing/blank City (fallback: try hotel/location text)
    no_city = hotels[hotels["City"].isna() | (hotels["City"].astype(str).str.strip() == "")]
    for idx, row in no_city.iterrows():
        q = best_query_row(row)
        g = geocode(q)
        if not g:
            continue
        lat, lon, disp = g
        elements = fetch_overpass_city(lat, lon, SEARCH_RADIUS_M, q)
        pois = [normalize_poi(e) for e in elements if (e.get("lat") or e.get("center")) and (e.get("lon") or e.get("center"))]
        enriched = []
        for p in pois:
            plat, plon = p["poi_lat"], p["poi_lon"]
            if plat is None or plon is None:
                continue
            d = haversine(lat, lon, float(plat), float(plon))
            enriched.append((d, p))
        enriched.sort(key=lambda x: x[0])
        if MAX_POIS_PER_HOTEL > 0:
            enriched = enriched[:MAX_POIS_PER_HOTEL]
        for dist_m, p in enriched:
            out_rows.append({
                "source_file": row["__source_file"],
                "city": row.get("City"),
                "hotel_name": row.get("Hotel Name"),
                "location_text": row.get("Location"),
                "url": row.get("URL"),
                "hotel_lat": lat if HOTEL_GEOCODE else None,
                "hotel_lon": lon if HOTEL_GEOCODE else None,
                "hotel_geocoded_display_name": disp if HOTEL_GEOCODE else "",
                "city_lat": lat,
                "city_lon": lon,
                "city_geocoded_display_name": disp,
                "poi_name": p["poi_name"],
                "poi_type": p["poi_type"],
                "poi_lat": p["poi_lat"],
                "poi_lon": p["poi_lon"],
                "distance_m": round(dist_m, 1),
                "osm_id": p["osm_id"],
                "osm_element_type": p["osm_element_type"],
                "raw_tags": p["raw_tags"],
            })

    # Write output
    out_df = pd.DataFrame(out_rows)
    cols = [
        "source_file","city","hotel_name","location_text","url",
        "hotel_lat","hotel_lon","hotel_geocoded_display_name",
        "city_lat","city_lon","city_geocoded_display_name",
        "poi_name","poi_type","poi_lat","poi_lon","distance_m",
        "osm_id","osm_element_type","raw_tags"
    ]
    for c in cols:
        if c not in out_df.columns:
            out_df[c] = None
    out_df = out_df[cols]
    out_df.to_csv(OUTPUT_FILE, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"Wrote {len(out_df)} rows to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
