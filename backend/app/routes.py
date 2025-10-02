from flask import Blueprint, jsonify, request
from .services.ticketmaster import fetch_events as fetch_ticketmaster
from .services.eventbrite import fetch_events as fetch_eventbrite
from .models import (
    save_ticketmaster_events,
    save_eventbrite_events,
    get_all_ticketmaster,
    get_all_eventbrite,
    get_all_events,
)

bp = Blueprint("api", __name__)

@bp.route("/")
def home():
    return {"message": "VoyagerAI Backend Running"}

@bp.route("/events")
def get_events():
    """Fetch from APIs and save into MongoDB"""
    query = request.args.get("q", "music")
    size = int(request.args.get("size", "10"))
    location = request.args.get("city", query)

    # Fetch Ticketmaster + Eventbrite
    ticketmaster_data = fetch_ticketmaster(query)
    eventbrite_data = fetch_eventbrite(query, location, size)

    tm_events = ticketmaster_data.get("_embedded", {}).get("events", [])
    eb_events = eventbrite_data.get("events", [])

    # Save to Mongo
    if tm_events:
        save_ticketmaster_events(tm_events)
    if eb_events:
        save_eventbrite_events(eb_events)

    return jsonify({
        "ticketmaster": tm_events,
        "eventbrite": eb_events
    })

@bp.route("/events/db")
def get_events_from_db():
    """Return cached events from MongoDB"""
    return jsonify({
        "ticketmaster": get_all_ticketmaster(),
        "eventbrite": get_all_eventbrite(),
        "all": get_all_events()
    })
