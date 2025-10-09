from flask import Blueprint, jsonify, request
from .models import db, Event
from .services.scraper import (
    scrape_bookmyshow_events, 
    scrape_eventbrite_events, 
    scrape_europaticket_events,
    scrape_all_events
)
from .services.ticketmaster import fetch_events as fetch_ticketmaster
from .services.eventbrite import fetch_events as fetch_eventbrite
from .services.csv_loader import csv_loader
from datetime import datetime

bp = Blueprint("api", __name__)


def _save_csv_events_to_db(csv_events):
    """Persist CSV-derived events into the SQL database if not already present."""
    saved_count = 0
    try:
        for ev in csv_events:
            title = ev.get("name") or ""
            url = ev.get("url") or None

            # Skip if we already have this event (match by URL if available, otherwise by title+date)
            existing = None
            if url:
                existing = Event.query.filter_by(url=url).first()
            if not existing and title:
                try:
                    date_str = ev.get("dates", {}).get("start", {}).get("localDate")
                    if date_str:
                        existing = (
                            Event.query
                            .filter(Event.title == title)
                            .filter(Event.date == datetime.strptime(date_str, "%Y-%m-%d").date())
                            .first()
                        )
                    else:
                        existing = Event.query.filter(Event.title == title).first()
                except Exception:
                    existing = None
            if existing:
                continue

            # Map fields
            local_date = (ev.get("dates", {}) or {}).get("start", {}).get("localDate")
            local_time = (ev.get("dates", {}) or {}).get("start", {}).get("localTime")
            venue = (ev.get("_embedded", {}) or {}).get("venues", [{}])[0].get("name")
            city = (ev.get("_embedded", {}) or {}).get("venues", [{}])[0].get("city", {}).get("name")

            parsed_date = None
            parsed_time = None
            try:
                if local_date:
                    parsed_date = datetime.strptime(local_date, "%Y-%m-%d").date()
            except Exception:
                parsed_date = None
            try:
                if local_time:
                    parsed_time = datetime.strptime(local_time, "%H:%M").time()
            except Exception:
                parsed_time = None

            price_text = None
            try:
                pr = ev.get("priceRanges")
                if isinstance(pr, list) and pr:
                    mn = pr[0].get("min")
                    mx = pr[0].get("max")
                    if mn is not None and mx is not None:
                        price_text = f"{mn}-{mx}"
            except Exception:
                price_text = None

            event_row = Event(
                title=title,
                date=parsed_date,
                time=parsed_time,
                venue=venue,
                place=city,
                price=price_text,
                url=url,
                city=city,
            )

            db.session.add(event_row)
            saved_count += 1

        if saved_count:
            db.session.commit()
        return saved_count
    except Exception:
        db.session.rollback()
        return 0

@bp.route("/")
def home():
    return {"message": "VoyagerAI Backend Running"}

@bp.route("/events")
def get_events():
    """Get events from real APIs and database, format for frontend."""
    try:
        city = request.args.get("city", "")
        query_param = request.args.get("q", "")
        limit = int(request.args.get("limit", 50))

        # Get real Ticketmaster events
        ticketmaster_events = []
        try:
            from .services.ticketmaster import fetch_events as fetch_ticketmaster
            from datetime import datetime
            
            # Use query_param or city for Ticketmaster search
            search_term = query_param or city or "Toronto"
            today = datetime.utcnow().strftime("%Y-%m-%dT00:00:00Z")
            
            ticketmaster_data = fetch_ticketmaster(
                query=search_term,
                city=city,
                start_date=today,
                size=min(limit, 20)
            )
            
            if ticketmaster_data and '_embedded' in ticketmaster_data:
                raw_events = ticketmaster_data['_embedded']['events']
                # Ensure each event has a unique ID
                for i, event in enumerate(raw_events):
                    if 'id' not in event or not event['id']:
                        event['id'] = f"tm_{i}_{hash(event.get('name', ''))}"
                ticketmaster_events = raw_events
                print(f"✅ Ticketmaster: Found {len(ticketmaster_events)} real events")
            else:
                print("⚠️ Ticketmaster: No events found")
        except Exception as e:
            print(f"❌ Ticketmaster API Error: {e}")

        # Get events from database for Eventbrite (since API is not working)
        eventbrite_events = []
        try:
            db_query = Event.query
            if city:
                db_query = db_query.filter(Event.city.ilike(f"%{city}%"))
            if query_param:
                db_query = db_query.filter(Event.title.ilike(f"%{query_param}%"))

            events = db_query.order_by(Event.created_at.desc()).limit(limit).all()
            
            for i, event in enumerate(events):
                # Convert our database event to Ticketmaster format (same as Ticketmaster for consistency)
                formatted_event = {
                    "id": f"eb_{event.id if hasattr(event, 'id') else i}_{hash(event.title)}",
                    "name": event.title,  # Simple string, not object
                    "url": event.url,
                    "dates": {
                        "start": {
                            "localDate": event.date.isoformat() if event.date else "2024-01-01",
                            "localTime": event.time.strftime("%H:%M") if event.time else "19:00"
                        }
                    },
                    "images": [{"url": "/placeholder.jpg"}],
                    "_embedded": {
                        "venues": [{
                            "name": event.venue or "TBA",
                            "city": {"name": event.city or "Unknown"}
                        }]
                    },
                    "priceRanges": [{"min": 0, "max": 100}] if event.price else None
                }
                eventbrite_events.append(formatted_event)
            
            print(f"✅ Eventbrite (DB): Found {len(eventbrite_events)} events")
        except Exception as e:
            print(f"❌ Eventbrite DB Error: {e}")

        # Get events from CSV files
        csv_events = []
        try:
            if query_param:
                # First try filtering by search term
                csv_events = csv_loader.get_events_by_query(query_param)
                # If nothing matches, try by city (if provided)
                if not csv_events and city:
                    csv_events = csv_loader.get_events_by_city(city)
                # As a final fallback, load all CSV events
                if not csv_events:
                    csv_events = csv_loader.load_all_csv_events()
            else:
                # No query provided; prefer city filter, else load all
                if city:
                    csv_events = csv_loader.get_events_by_city(city)
                if not csv_events:
                    csv_events = csv_loader.load_all_csv_events()
            
            # Limit CSV events to avoid overwhelming the response
            csv_events = csv_events[:limit]
            print(f"✅ CSV Events: Found {len(csv_events)} events")

            # Persist CSV events to DB for future queries
            saved = _save_csv_events_to_db(csv_events)
            if saved:
                print(f"💾 Saved {saved} CSV events to database")
        except Exception as e:
            print(f"❌ CSV Events Error: {e}")

        return jsonify({
            "ticketmaster": ticketmaster_events,
            "eventbrite": eventbrite_events,
            "csv_events": csv_events
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

@bp.route("/scrape/all", methods=["POST"])
def scrape_all_sources():
    """Scrape events from all sources (BookMyShow, Eventbrite, EuropaTicket) and save to database."""
    try:
        data = request.get_json() or {}
        city = data.get("city", "Mumbai")
        bms_limit = data.get("bms_limit", 10)
        eventbrite_limit = data.get("eventbrite_limit", 50)
        europaticket_limit = data.get("europaticket_limit", 50)

        # Scrape from all sources
        all_events = scrape_all_events(
            city=city,
            bms_limit=bms_limit,
            eventbrite_limit=eventbrite_limit,
            europaticket_limit=europaticket_limit
        )

        saved_count = 0
        for event_data in all_events:
            existing = Event.query.filter_by(url=event_data.get("url")).first()
            if existing:
                continue

            # Normalize event data for database
            event = Event(
                title=event_data.get("title", ""),
                venue=event_data.get("venue") or event_data.get("location"),
                place=event_data.get("place") or event_data.get("city"),
                price=event_data.get("price"),
                url=event_data.get("url"),
                city=event_data.get("city", city),
            )

            db.session.add(event)
            saved_count += 1

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Scraped {len(all_events)} events from all sources, saved {saved_count} new events",
            "scraped_count": len(all_events),
            "saved_count": saved_count,
            "sources": {
                "bookmyshow": len([e for e in all_events if e.get("source") == "bookmyshow"]),
                "eventbrite": len([e for e in all_events if e.get("source") == "eventbrite"]),
                "europaticket": len([e for e in all_events if e.get("source") == "europaticket"])
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route("/scrape/eventbrite", methods=["POST"])
def scrape_eventbrite_only():
    """Scrape events from Eventbrite only."""
    try:
        data = request.get_json() or {}
        months_ahead = data.get("months_ahead", 6)
        limit = data.get("limit", 50)

        scraped_events = scrape_eventbrite_events(months_ahead, limit)

        saved_count = 0
        for event_data in scraped_events:
            existing = Event.query.filter_by(url=event_data.get("url")).first()
            if existing:
                continue

            # Extract city from location
            city = "Unknown"
            if event_data.get("location"):
                city = event_data["location"].split(",")[-1].strip() if "," in event_data["location"] else "Unknown"

            event = Event(
                title=event_data.get("title", ""),
                venue=event_data.get("location"),
                place=city,
                price=event_data.get("price"),
                url=event_data.get("url"),
                city=city,
            )

            db.session.add(event)
            saved_count += 1

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Scraped {len(scraped_events)} Eventbrite events, saved {saved_count} new events",
            "scraped_count": len(scraped_events),
            "saved_count": saved_count,
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route("/scrape/europaticket", methods=["POST"])
def scrape_europaticket_only():
    """Scrape events from EuropaTicket only."""
    try:
        data = request.get_json() or {}
        limit = data.get("limit", 50)

        scraped_events = scrape_europaticket_events(limit=limit)

        saved_count = 0
        for event_data in scraped_events:
            existing = Event.query.filter_by(url=event_data.get("url")).first()
            if existing:
                continue

            event = Event(
                title=event_data.get("title", ""),
                venue=event_data.get("venue"),
                place=event_data.get("city"),
                price=event_data.get("price"),
                url=event_data.get("url"),
                city=event_data.get("city", "Unknown"),
            )

            db.session.add(event)
            saved_count += 1

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Scraped {len(scraped_events)} EuropaTicket events, saved {saved_count} new events",
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

# External providers - fetch without persisting, return combined
@bp.route("/events/fetch")
def fetch_provider_events():
    """Fetch events from external APIs (Ticketmaster & Eventbrite) without saving to database."""
    query = request.args.get("q", "").strip()
    city = request.args.get("city", "").strip()
    size = int(request.args.get("size", "12"))

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

    # CSV events fetch
    csv_events = []
    try:
        if city:
            csv_events = csv_loader.get_events_by_city(city)
        elif query:
            csv_events = csv_loader.get_events_by_query(query)
        else:
            csv_events = csv_loader.load_all_csv_events()
        
        csv_events = csv_events[:size]
    except Exception as e:
        print(f"❌ CSV Events Error: {e}")

    print(f"🎟 Ticketmaster -> {len(ticketmaster_data.get('_embedded', {}).get('events', []))} results")
    print(f"📅 Eventbrite -> {len(eventbrite_data.get('events', []))} results")
    print(f"📄 CSV Events -> {len(csv_events)} results")

    return jsonify({
        "ticketmaster": ticketmaster_data.get("_embedded", {}).get("events", []),
        "eventbrite": eventbrite_data.get("events", []),
        "csv_events": csv_events
    })