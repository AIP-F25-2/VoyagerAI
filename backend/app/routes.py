from flask import Blueprint, jsonify, request
from .models import db, Event
from .services.scraper import scrape_bookmyshow_events
from .services.ticketmaster import fetch_events as fetch_ticketmaster
from .services.eventbrite import fetch_events as fetch_eventbrite
from datetime import datetime

bp = Blueprint("api", __name__)

@bp.route("/")
def home():
    return {"message": "VoyagerAI Backend Running"}

@bp.route("/events")
def get_events():
    """Get events from SQL database (sujan branch)."""
    try:
        city = request.args.get("city", "")
        limit = int(request.args.get("limit", 50))

        query = Event.query
        if city:
            query = query.filter(Event.city.ilike(f"%{city}%"))

        events = query.order_by(Event.created_at.desc()).limit(limit).all()

        return jsonify({
            "success": True,
            "count": len(events),
            "events": [event.to_dict() for event in events],
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route("/scrape", methods=["POST"])
def scrape_events():
    """Scrape events from BookMyShow and save to SQL database."""
    try:
        data = request.get_json() or {}
        city = data.get("city", "Mumbai")
        limit = data.get("limit", 10)

        scraped_events = scrape_bookmyshow_events(city, limit)

        saved_count = 0
        for event_data in scraped_events:
            existing = Event.query.filter_by(url=event_data.get("url")).first()
            if existing:
                continue

            event = Event(
                title=event_data.get("title", ""),
                venue=event_data.get("venue"),
                place=event_data.get("place"),
                price=event_data.get("price"),
                url=event_data.get("url"),
                city=city,
            )

            db.session.add(event)
            saved_count += 1

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Scraped {len(scraped_events)} events, saved {saved_count} new events",
            "scraped_count": len(scraped_events),
            "saved_count": saved_count,
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route("/events/<int:event_id>")
def get_event(event_id):
    try:
        event = Event.query.get_or_404(event_id)
        return jsonify({"success": True, "event": event.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route("/events/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    try:
        event = Event.query.get_or_404(event_id)
        db.session.delete(event)
        db.session.commit()
        return jsonify({"success": True, "message": "Event deleted"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


# External providers (nischal branch) - fetch without persisting, return combined
@bp.route("/events/fetch")
def fetch_provider_events():
    query = request.args.get("q", "").strip()
    city = request.args.get("city", "").strip()
    size = int(request.args.get("size", "12"))

    today = datetime.utcnow().strftime("%Y-%m-%dT00:00:00Z")

    ticketmaster_data = fetch_ticketmaster(query=query, city=city, start_date=today, size=size)
    eventbrite_data = fetch_eventbrite(query=query, location=city, size=size)

    return jsonify({
        "ticketmaster": ticketmaster_data.get("_embedded", {}).get("events", []),
        "eventbrite": eventbrite_data.get("events", []),
    })
=======
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
>>>>>>> origin/nischal
