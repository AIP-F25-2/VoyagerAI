import os
import io
import json
import time
import pandas as pd
import streamlit as st
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

APP_TITLE = "Smart Trip Planner (LLM-powered)"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🧭",
    layout="wide",
)

# -------------------------------
# Helpers
# -------------------------------
def norm(s: Optional[str]) -> str:
    return (s or "").strip()

def lower(s: Optional[str]) -> str:
    return (s or "").strip().lower()

def currency(n: Any, symbol: str = "$") -> str:
    try:
        v = float(str(n).replace(",", "").replace(symbol, ""))
        return f"{symbol}{v:,.2f}"
    except Exception:
        return str(n)

def load_csv_upload(label: str, example_link: Optional[str] = None) -> Optional[pd.DataFrame]:
    f = st.file_uploader(label, type=["csv"])
    if f:
        try:
            return pd.read_csv(f)
        except Exception as e:
            st.error(f"Failed to read CSV: {e}")
            return None
    if example_link:
        st.link_button("Download sample", example_link)
    return None

def normalize_events(df: pd.DataFrame) -> pd.DataFrame:
    cols = {c.lower(): c for c in df.columns}
    def get(row, klist):
        for k in klist:
            c = cols.get(k)
            if c is not None:
                v = row.get(c, "")
                if pd.notna(v) and str(v).strip():
                    return v
        return ""
    out = []
    for _, r in df.iterrows():
        out.append({
            "title": get(r, ["title", "event", "name"]),
            "date": get(r, ["date"]),
            "time": get(r, ["time"]),
            "price": get(r, ["price"]),
            "url": get(r, ["url"]),
            "city": get(r, ["city"]),
        })
    out = pd.DataFrame(out)
    out = out[out["title"].astype(str).str.strip() != ""]
    return out

def normalize_hotels(df: pd.DataFrame) -> pd.DataFrame:
    cols = {c.lower(): c for c in df.columns}
    def pickcol(*names):
        for n in names:
            if n in cols:
                return cols[n]
        return None
    out = pd.DataFrame({
        "city": df.get(pickcol("city", "place", "location", "town"), ""),
        "name": df.get(pickcol("hotel name", "name", "title"), ""),
        "address": df.get(pickcol("address", "location", "loc"), ""),
        "price_per_night": df.get(pickcol("price_per_night", "price", "rate"), ""),
        "rating": df.get(pickcol("rating", "stars", "score"), ""),
        "url": df.get(pickcol("url", "link"), ""),
    })
    out = out[out["name"].astype(str).str.strip() != ""]
    return out

def normalize_pois(df: pd.DataFrame) -> pd.DataFrame:
    cols = {c.lower(): c for c in df.columns}
    def col(name, fallback=None):
        return df.get(cols.get(name, ""), fallback)
    out = pd.DataFrame({
        "city": df.get(cols.get("city", ""), ""),
        "hotel_name": df.get(cols.get("hotel_name", ""), ""),
        "poi_name": df.get(cols.get("poi_name", "") or cols.get("name", ""), ""),
        "poi_type": df.get(cols.get("poi_type", "") or cols.get("type", ""), ""),
        "distance_m": df.get(cols.get("distance_m", "") or cols.get("distance", ""), ""),
    })
    out = out[out["poi_name"].astype(str).str.strip() != ""]
    return out

def hotels_subset_for_prompt(hotels_df: Optional[pd.DataFrame], city: str, selected_names: List[str], max_per_city: int = 3):
    if hotels_df is None:
        return []
    df = hotels_df.copy()
    if city:
        df = df[ df["city"].astype(str).str.strip().str.lower() == city.strip().lower() ]
    if selected_names:
        df = df[ df["name"].isin(selected_names) ]
    # If nothing selected, take top few from city as hints
    if df.empty and city:
        df = hotels_df[ hotels_df["city"].astype(str).str.strip().str.lower() == city.strip().lower() ].head(max_per_city)
    out = []
    for _, r in df.iterrows():
        out.append({
            "place": r.get("city", ""),
            "name": r.get("name", ""),
            "address": r.get("address", ""),
            "price_per_night": r.get("price_per_night", ""),
            "rating": r.get("rating", ""),
            "url": r.get("url", ""),
        })
    return out

def build_prompt(
    trip_name: str,
    start_date: date,
    num_days: int,
    pace: str,
    budget_level: str,
    interests: List[str],
    city: str,
    party_size: int,
    selected_events: List[Dict[str, Any]],
    selected_hotels: List[str],
    selected_pois: List[str],
    hotels_df: Optional[pd.DataFrame],
    pois_df: Optional[pd.DataFrame],
) -> str:
    hotels_snippets = hotels_subset_for_prompt(hotels_df, city, selected_hotels, max_per_city=3)

    if pois_df is not None:
        pois_in_city = pois_df[ pois_df["city"].astype(str).str.strip().str.lower() == city.strip().lower() ]
        pois_in_prompt = pois_in_city[ pois_in_city["poi_name"].isin(selected_pois) ] if selected_pois else pois_in_city.head(12)
    else:
        pois_in_prompt = pd.DataFrame(columns=["poi_name", "poi_type", "distance_m"])

    ev_brief = [
        {k: v for k, v in e.items() if k in ["title", "date", "time", "price", "url"]}
        for e in selected_events
    ]
    poi_brief = [
        {
            "poi_name": r["poi_name"],
            "poi_type": r.get("poi_type", ""),
            "distance_m": r.get("distance_m", ""),
        }
        for _, r in pois_in_prompt.iterrows()
    ]

    template = (
        "You are a meticulous travel planner. Build a realistic, efficient, local-savvy itinerary.\n"
        f"Trip name: {trip_name}\n"
        f"Start date: {start_date.isoformat()}\n"
        f"Total days: {num_days}\n"
        f"Pace: {pace}\n"
        f"Budget level: {budget_level}\n"
        f"Party size: {party_size}\n"
        f"City: {city or 'unspecified'}\n"
        f"Interests: {', '.join(interests) if interests else 'General sightseeing'}\n"
        f"Must-include events: {json.dumps(ev_brief, ensure_ascii=False)}\n"
        f"Hotel options: {json.dumps(hotels_snippets, ensure_ascii=False)}\n"
        f"Candidate tourist places: {json.dumps(poi_brief, ensure_ascii=False)}\n\n"
        "Rules:\n"
        "- Return a clean Markdown document with a Summary, then Day 1..N sections.\n"
        "- Each day: morning / afternoon / evening blocks, with timing windows.\n"
        "- Minimize backtracking; cluster nearby attractions. Mention transit time.\n"
        "- Assign hotels sensibly; if options provided, pick the best and include the URL.\n"
        "- Add local food suggestions near planned spots.\n"
        "- Add a per-day budget table and a total (local currency).\n"
        "- Include rain/closure backup ideas per day.\n"
        "- Avoid closed attractions (note typical closure days if relevant).\n"
        "- Output only Markdown."
    )
    return template

def call_openai_chat(prompt: str, model: str, temperature: float, api_key: str) -> str:
    if OpenAI is None:
        raise RuntimeError("openai package not available. Install `openai>=1.0.0`.")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY.")
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": "You are a helpful, detail-oriented travel planner."},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content or ""

# -------------------------------
# Sidebar: global inputs
# -------------------------------
st.title("🧭 Smart Trip Planner")
st.caption("First pick events. Then fill the survey and choose hotels and places. Finally, generate an AI itinerary.")

with st.sidebar:
    st.header("Trip settings")
    trip_name = st.text_input("Trip name", "City Break")
    start_date = st.date_input("Start date", value=date.today() + timedelta(days=30))
    num_days = st.number_input("Number of days", min_value=1, max_value=60, value=5)
    party_size = st.number_input("People", min_value=1, max_value=10, value=2)
    pace = st.selectbox("Pace", ["Relaxed", "Balanced", "Intense"], index=1)
    budget_level = st.selectbox("Budget level", ["Budget", "Mid-range", "Premium"], index=1)
    interests = st.multiselect(
        "Interests",
        ["Food", "Culture", "History", "Nature", "Shopping", "Nightlife", "Beaches", "Adventure"],
        default=["Food", "Culture"],
    )

    st.divider()
    st.subheader("Model")
    api_key = st.text_input("OPENAI_API_KEY", type="password", placeholder="sk-...")
    model = st.text_input("Model name", value="gpt-4o-mini")
    temperature = st.slider("Creativity", 0.0, 1.0, 0.4, 0.05)

# -------------------------------
# Tabs
# -------------------------------
tab1, tab2, tab3 = st.tabs(["1) Events", "2) Survey", "3) AI Itinerary"])

# Session state for selections
if "selected_event_rows" not in st.session_state:
    st.session_state.selected_event_rows = []
if "selected_hotel_names" not in st.session_state:
    st.session_state.selected_hotel_names = []
if "selected_poi_names" not in st.session_state:
    st.session_state.selected_poi_names = []
if "preferred_city" not in st.session_state:
    st.session_state.preferred_city = ""

# --------------------------------
# Tab 1: Events page
# --------------------------------
with tab1:
    st.subheader("Events")
    st.caption("Upload your events CSV (e.g., Final.csv). Expected columns (flexible): title, date, time, price, url, city.")

    events_df_upload = load_csv_upload("Upload events CSV")
    # If you want default paths, uncomment:
    # if events_df_upload is None and os.path.exists("Final.csv"):
    #     events_df_upload = pd.read_csv("Final.csv")

    if events_df_upload is not None:
        events_df = normalize_events(events_df_upload)
        left, right = st.columns([3, 2])
        with left:
            city_filter = st.selectbox(
                "Filter by city",
                ["All"] + sorted([c for c in events_df["city"].dropna().astype(str).str.strip().unique() if c]),
                index=0
            )
            query = st.text_input("Search title/date/time")
        with right:
            st.write("")

        filtered = events_df.copy()
        if city_filter != "All":
            filtered = filtered[filtered["city"].astype(str).str.strip().str.lower() == city_filter.strip().lower()]
        if query:
            q = query.lower()
            mask = (
                filtered["title"].astype(str).str.lower().str.contains(q) |
                filtered.get("date", pd.Series([""]*len(filtered))).astype(str).str.lower().str.contains(q) |
                filtered.get("time", pd.Series([""]*len(filtered))).astype(str).str.lower().str.contains(q)
            )
            filtered = filtered[mask]

        st.dataframe(filtered.reset_index(drop=True), use_container_width=True, height=380)

        st.markdown("**Select events to include**")
        selected = st.multiselect(
            "Pick events",
            options=[f"{r.title} | {r.date or ''} | {r.city or ''}" for r in filtered.itertuples()],
        )
        # Map back to rows
        chosen_rows = []
        for s in selected:
            title = s.split(" | ")[0].strip()
            row = filtered[ filtered["title"] == title ].head(1)
            if not row.empty:
                chosen_rows.append(row.iloc[0].to_dict())
        st.session_state.selected_event_rows = chosen_rows

        st.success(f"Selected {len(chosen_rows)} event(s). Move to the Survey tab.")
    else:
        st.info("Upload an events CSV to proceed.")

# --------------------------------
# Tab 2: Survey page
# --------------------------------
with tab2:
    st.subheader("Survey")
    st.caption("Pick city, upload hotels and tourist places, and select options.")

    colA, colB = st.columns(2)
    with colA:
        preferred_city = st.text_input("City for itinerary", st.session_state.preferred_city or "")
        st.session_state.preferred_city = preferred_city

        st.markdown("**Upload hotels CSV**  \nColumns (flexible): city/place, name, address, price_per_night, rating, url")
        hotels_df_upload = load_csv_upload("Hotels CSV", example_link=None)
        if hotels_df_upload is not None:
            hotels_df = normalize_hotels(hotels_df_upload)
        else:
            hotels_df = None

        st.markdown("**Upload tourist places CSV**  \nColumns (flexible): city, poi_name/name, poi_type/type, distance_m")
        pois_df_upload = load_csv_upload("Tourist places CSV", example_link=None)
        if pois_df_upload is not None:
            pois_df = normalize_pois(pois_df_upload)
        else:
            pois_df = None

        if hotels_df is not None and preferred_city:
            city_hotels = hotels_df[ hotels_df["city"].astype(str).str.strip().str.lower() == preferred_city.strip().lower() ]
            st.write("Hotels in city:", len(city_hotels))
            st.dataframe(city_hotels.reset_index(drop=True).head(20), use_container_width=True, height=250)
            st.session_state.selected_hotel_names = st.multiselect(
                "Select hotels",
                options=list(city_hotels["name"].unique()),
                default=st.session_state.selected_hotel_names,
            )
        else:
            st.info("Upload hotels and set a city to select hotels.")

    with colB:
        if pois_df is not None and preferred_city:
            city_pois = pois_df[ pois_df["city"].astype(str).str.strip().str.lower() == preferred_city.strip().lower() ]
            st.write("Tourist places in city:", len(city_pois))
            st.dataframe(city_pois.reset_index(drop=True).head(40), use_container_width=True, height=350)
            st.session_state.selected_poi_names = st.multiselect(
                "Select tourist places",
                options=list(city_pois["poi_name"].unique()),
                default=st.session_state.selected_poi_names,
            )
        else:
            st.info("Upload tourist places and set a city to select POIs.")

    st.success("Survey ready. Go to the AI Itinerary tab to generate.")

# --------------------------------
# Tab 3: AI Itinerary
# --------------------------------
with tab3:
    st.subheader("AI Itinerary")
    st.caption("Paste your OpenAI key to call the API, or just copy the prompt.")

    # Build prompt preview
    events_selected = st.session_state.selected_event_rows or []
    hotels_selected = st.session_state.selected_hotel_names or []
    pois_selected = st.session_state.selected_poi_names or []
    preferred_city = st.session_state.preferred_city or ""

    # For prompt: we need the normalized frames from Survey tab again (if any)
    hotels_df = None
    pois_df = None
    # Re-ask upload quickly (won't lose state if they already did, but needed in this tab to reference)
    with st.expander("Optional: Re-upload hotels/POIs here if not in memory", expanded=False):
        hotels_df_upload2 = load_csv_upload("Hotels CSV (optional)")
        pois_df_upload2 = load_csv_upload("Tourist places CSV (optional)")
        if hotels_df_upload2 is not None:
            hotels_df = normalize_hotels(hotels_df_upload2)
        if pois_df_upload2 is not None:
            pois_df = normalize_pois(pois_df_upload2)

    user_prompt = build_prompt(
        trip_name=trip_name,
        start_date=start_date,
        num_days=int(num_days),
        pace=pace,
        budget_level=budget_level,
        interests=interests,
        city=preferred_city,
        party_size=int(party_size),
        selected_events=events_selected,
        selected_hotels=hotels_selected,
        selected_pois=pois_selected,
        hotels_df=hotels_df,
        pois_df=pois_df,
    )

    st.markdown("**Prompt preview**")
    st.code(user_prompt, language="markdown")

    col1, col2, col3 = st.columns([1.2, 1, 1])
    with col1:
        copied = st.button("Copy prompt")
        if copied:
            st.session_state["_copied"] = True
            st.toast("Prompt copied.")
    with col2:
        dl = st.download_button(
            "Download prompt",
            data=user_prompt.encode("utf-8"),
            file_name="itinerary_prompt.md",
            mime="text/markdown",
        )
    with col3:
        call = st.button("✨ Generate with OpenAI")

    if call:
        try:
            if not api_key:
                st.error("Add OPENAI_API_KEY in the sidebar.")
            else:
                with st.spinner("Generating itinerary..."):
                    content = call_openai_chat(user_prompt, model=model, temperature=temperature, api_key=api_key)
                st.markdown(content)
                st.download_button("Download Markdown", data=content.encode("utf-8"),
                                   file_name="itinerary.md", mime="text/markdown", key="dl-itin")
        except Exception as e:
            st.error(f"Failed to generate: {e}")
