from flask import Blueprint, jsonify, request
from .services.ticketmaster import fetch_events as fetch_ticketmaster
from .services.eventbrite import fetch_events as fetch_eventbrite
from datetime import datetime

bp = Blueprint("api", __name__)

@bp.route("/")
def home():
    return {"message": "VoyagerAI Backend Running"}

@bp.route("/events")
def get_events():
    """
    Fetch events from both Ticketmaster & Eventbrite.
    If 'q' or 'city' are provided, they are used to narrow results.
    Otherwise, fetches all events from the user's location or country.
    """
    query = request.args.get("q", "").strip()
    city = request.args.get("city", "").strip()
    size = int(request.args.get("size", "12"))

    # Get current date
    today = datetime.utcnow().strftime("%Y-%m-%dT00:00:00Z")

    # Ticketmaster API fetch
    ticketmaster_data = fetch_ticketmaster(
        query=query,
        city=city,
        start_date=today,
        size=size
    )

    # Eventbrite API fetch
    eventbrite_data = fetch_eventbrite(
        query=query,
        location=city,
        size=size
    )

    print(f"🎟 Ticketmaster -> {len(ticketmaster_data.get('_embedded', {}).get('events', []))} results")
    print(f"📅 Eventbrite -> {len(eventbrite_data.get('events', []))} results")

    return jsonify({
        "ticketmaster": ticketmaster_data.get("_embedded", {}).get("events", []),
        "eventbrite": eventbrite_data.get("events", [])
    })
