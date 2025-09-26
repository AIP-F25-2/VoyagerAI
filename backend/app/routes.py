from flask import Blueprint, jsonify, request
from .services.ticketmaster import fetch_events as fetch_ticketmaster
from .services.eventbrite import fetch_events as fetch_eventbrite

# Register Blueprint
bp = Blueprint("api", __name__)

@bp.route("/")
def home():
    return {"message": "VoyagerAI Backend Running"}

@bp.route("/events")
def get_events():
    """Fetch events from both Ticketmaster & Eventbrite"""
    query = request.args.get("q", "music")
    size = int(request.args.get("size", "10"))
    location = request.args.get("city", query)  # fallback: use query as city

    # Fetch data from both APIs
    ticketmaster_data = fetch_ticketmaster(query)
    eventbrite_data = fetch_eventbrite(query, location, size)

    # Debug logs
    print("Ticketmaster:", ticketmaster_data.keys() if isinstance(ticketmaster_data, dict) else ticketmaster_data)
    print("Eventbrite:", eventbrite_data.keys() if isinstance(eventbrite_data, dict) else eventbrite_data)

    return jsonify({
        "ticketmaster": ticketmaster_data.get("_embedded", {}).get("events", []),
        "eventbrite": eventbrite_data.get("events", [])
    })
