from flask import Blueprint, jsonify, request
from .models import db, Event, Favorite, EventShare, EventReview, Subscription
from .__init__ import cache, limiter
from .services.notification_service import notification_service
from .services.recommendation_service import recommendation_service
from .services.hotels import search_hotels
from .services.flights import search_flights
from .services.scraper import (
    scrape_bookmyshow_events, 
    scrape_eventbrite_events, 
    scrape_europaticket_events,
    scrape_all_events
)
from .services.ticketmaster import fetch_events as fetch_ticketmaster
from .services.eventbrite import fetch_events as fetch_eventbrite
from .services.csv_loader import csv_loader
from .services.images import search_pixabay_image
from datetime import datetime, date, timedelta
from io import StringIO

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
        city = request.args.get("city", "").strip()
        query_param = request.args.get("q", "").strip()
        limit = int(request.args.get("limit", 50))
        # Enhanced filters
        provider = request.args.get("provider", "").strip().lower()  # ticketmaster|eventbrite|csv|all
        date_from = request.args.get("date_from", "").strip()
        date_to = request.args.get("date_to", "").strip()
        price_min = request.args.get("price_min", "").strip()
        price_max = request.args.get("price_max", "").strip()
        when = request.args.get("when", "").strip().lower()  # tonight|weekend|this_week|this_month
        category = request.args.get("category", "").strip().lower()  # music|sports|arts|food|tech|business
        venue = request.args.get("venue", "").strip()
        accessibility = request.args.get("accessibility", "").strip().lower()  # wheelchair|hearing|visual
        page = max(1, int(request.args.get("page", 1)))
        page_size = max(1, min(100, int(request.args.get("page_size", limit))))

        # Interpret shortcuts
        if when == "tonight":
            date_from = date.today().isoformat()
            date_to = date.today().isoformat()
        elif when == "weekend":
            today = date.today()
            # Next Friday to Sunday
            days_ahead = (4 - today.weekday()) % 7  # Friday index 4
            start = today + timedelta(days=days_ahead)
            end = start + timedelta(days=2)
            date_from = start.isoformat()
            date_to = end.isoformat()
        elif when == "this_week":
            today = date.today()
            start = today
            end = today + timedelta(days=7)
            date_from = start.isoformat()
            date_to = end.isoformat()
        elif when == "this_month":
            today = date.today()
            start = today
            end = today + timedelta(days=30)
            date_from = start.isoformat()
            date_to = end.isoformat()

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
            # Date filters
            try:
                if date_from:
                    df = datetime.strptime(date_from, "%Y-%m-%d").date()
                    db_query = db_query.filter(Event.date >= df)
                if date_to:
                    dt_ = datetime.strptime(date_to, "%Y-%m-%d").date()
                    db_query = db_query.filter(Event.date <= dt_)
            except Exception:
                pass

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

        # Enrich with a stored or fetched free image when missing
        def with_image(ev):
            if isinstance(ev.get("images"), list) and ev["images"]:
                return ev
            # Try Pixabay using event name
            q = ev.get("name") or ev.get("title") or ""
            img = search_pixabay_image(q) if q else None
            if img:
                ev["images"] = [{"url": img}]
            return ev

        def apply_date_filters(ev_list):
            if not (date_from or date_to):
                return ev_list
            filtered = []
            for ev in ev_list:
                d = (ev.get("dates") or {}).get("start", {}).get("localDate")
                try:
                    if not d:
                        continue
                    dval = datetime.strptime(d, "%Y-%m-%d").date()
                    if date_from:
                        df = datetime.strptime(date_from, "%Y-%m-%d").date()
                        if dval < df:
                            continue
                    if date_to:
                        dt_ = datetime.strptime(date_to, "%Y-%m-%d").date()
                        if dval > dt_:
                            continue
                    filtered.append(ev)
                except Exception:
                    continue
            return filtered

        ticketmaster_events = [with_image(e) for e in ticketmaster_events]
        eventbrite_events = [with_image(e) for e in eventbrite_events]
        csv_events = [with_image(e) for e in csv_events]

        # Apply provider filter
        if provider in {"ticketmaster", "tm"}:
            eventbrite_events, csv_events = [], []
        elif provider in {"eventbrite", "eb"}:
            ticketmaster_events, csv_events = [], []
        elif provider in {"csv"}:
            ticketmaster_events, eventbrite_events = [], []

        # Apply date filters to all lists
        ticketmaster_events = apply_date_filters(ticketmaster_events)
        eventbrite_events = apply_date_filters(eventbrite_events)
        csv_events = apply_date_filters(csv_events)

        # Pagination per merged result for client convenience
        merged = ticketmaster_events + eventbrite_events + csv_events
        total = len(merged)
        start = (page - 1) * page_size
        end = start + page_size
        merged_page = merged[start:end]

        return jsonify({
            "ticketmaster": ticketmaster_events,
            "eventbrite": eventbrite_events,
            "csv_events": csv_events,
            "merged": merged_page,
            "pagination": {"page": page, "page_size": page_size, "total": total}
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


@bp.route("/hotels/search")
def hotels_search():
    """Search hotels via provider stub (extendable with real API)."""
    try:
        city = request.args.get("city", "").strip()
        check_in = request.args.get("check_in", "").strip() or None
        check_out = request.args.get("check_out", "").strip() or None
        guests = int(request.args.get("guests", "2") or 2)
        limit = int(request.args.get("limit", "10") or 10)

        if not city:
            return jsonify({"success": False, "error": "city is required"}), 400

        items = search_hotels(city=city, check_in=check_in, check_out=check_out, guests=guests, limit=limit)
        return jsonify({"success": True, "hotels": items})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/flights/search")
def flights_search():
    """Search flights via provider stub (extendable with real API)."""
    try:
        origin = request.args.get("origin", "").upper().strip()
        destination = request.args.get("destination", "").upper().strip()
        departure_date = request.args.get("departure_date", "").strip()
        return_date = request.args.get("return_date", "").strip() or None
        adults = int(request.args.get("adults", "1") or 1)
        limit = int(request.args.get("limit", "10") or 10)

        if not origin or not destination or not departure_date:
            return jsonify({"success": False, "error": "origin, destination, and departure_date are required"}), 400

        items = search_flights(origin=origin, destination=destination, departure_date=departure_date, return_date=return_date, adults=adults, limit=limit)
        return jsonify({"success": True, "flights": items})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# Favorites
@bp.route("/favorites", methods=["GET"]) 
def list_favorites():
    email = request.args.get("email", "").strip() or None
    q = Favorite.query
    if email:
        q = q.filter(Favorite.user_email == email)
    items = [f.to_dict() for f in q.order_by(Favorite.created_at.desc()).limit(200).all()]
    return jsonify({"success": True, "favorites": items})


@bp.route("/favorites", methods=["POST"]) 
@limiter.limit("10/minute")
def add_favorite():
    try:
        data = request.get_json() or {}
        user_email = (data.get("email") or "").strip() or None
        title = data.get("title") or ""
        url = (data.get("url") or None)
        provider = data.get("provider")

        # Duplicate prevention: same user cannot add the same event twice
        existing_q = Favorite.query
        if user_email:
            existing_q = existing_q.filter(Favorite.user_email == user_email)

        # Prefer strong match by URL if available, otherwise fallback to title+date(+provider)
        if url:
            existing_q = existing_q.filter(Favorite.url == url)
        else:
            existing_q = existing_q.filter(Favorite.title == title)
            try:
                if data.get("date"):
                    date_val = datetime.fromisoformat(data["date"]).date()
                    existing_q = existing_q.filter(Favorite.date == date_val)
            except Exception:
                # If date can't be parsed, rely on title-only match
                pass
            if provider:
                existing_q = existing_q.filter(Favorite.provider == provider)

        existing = existing_q.first()
        if existing:
            return jsonify({"success": False, "error": "Favorite already exists for this user"}), 409

        fav = Favorite(
            user_email=user_email,
            title=title,
            venue=data.get("venue"),
            city=data.get("city"),
            url=url,
            image_url=data.get("image_url"),
            provider=provider,
        )
        # parse date/time if provided
        try:
            if data.get("date"):
                fav.date = datetime.fromisoformat(data["date"]).date()
        except Exception:
            pass
        try:
            if data.get("time"):
                fav.time = datetime.strptime(data["time"], "%H:%M").time()
        except Exception:
            pass

        db.session.add(fav)
        db.session.commit()
        return jsonify({"success": True, "favorite": fav.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/favorites/<int:fav_id>", methods=["DELETE"]) 
def delete_favorite(fav_id: int):
    try:
        fav = Favorite.query.get_or_404(fav_id)
        db.session.delete(fav)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


# ICS calendar export for a single event from DB
@bp.route("/events/<int:event_id>/ics")
def export_event_ics(event_id: int):
    try:
        event = Event.query.get_or_404(event_id)
        dt = event.date.isoformat() if event.date else ""
        tm = event.time.strftime("%H%M00") if event.time else "000000"
        uid = f"voyagerai-event-{event.id}"
        ics = "\r\n".join([
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//VoyagerAI//Events//EN",
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART:{dt.replace('-', '')}T{tm}",
            f"SUMMARY:{event.title}",
            f"LOCATION:{(event.venue or '')} {('' if not event.city else event.city)}",
            f"URL:{event.url or ''}",
            "END:VEVENT",
            "END:VCALENDAR",
        ])
        return (
            ics,
            200,
            {
                "Content-Type": "text/calendar; charset=utf-8",
                "Content-Disposition": f"attachment; filename=event-{event_id}.ics",
            },
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route("/events/filters")
def get_filter_options():
    """Get available filter options for events"""
    try:
        # Get unique cities from database
        cities = db.session.query(Event.city).filter(Event.city.isnot(None)).distinct().all()
        city_list = [city[0] for city in cities if city[0]]
        
        # Get unique venues from database
        venues = db.session.query(Event.venue).filter(Event.venue.isnot(None)).distinct().all()
        venue_list = [venue[0] for venue in venues if venue[0]]
        
        # Define categories based on common event types
        categories = [
            {"id": "music", "name": "Music & Concerts", "icon": "🎵"},
            {"id": "sports", "name": "Sports & Fitness", "icon": "⚽"},
            {"id": "arts", "name": "Arts & Culture", "icon": "🎨"},
            {"id": "food", "name": "Food & Drink", "icon": "🍕"},
            {"id": "tech", "name": "Technology", "icon": "💻"},
            {"id": "business", "name": "Business & Networking", "icon": "💼"},
            {"id": "education", "name": "Education & Learning", "icon": "📚"},
            {"id": "health", "name": "Health & Wellness", "icon": "🏥"},
            {"id": "family", "name": "Family & Kids", "icon": "👨‍👩‍👧‍👦"},
            {"id": "outdoor", "name": "Outdoor & Nature", "icon": "🌲"}
        ]
        
        # Define accessibility options
        accessibility_options = [
            {"id": "wheelchair", "name": "Wheelchair Accessible", "icon": "♿"},
            {"id": "hearing", "name": "Hearing Assistance", "icon": "👂"},
            {"id": "visual", "name": "Visual Assistance", "icon": "👁️"},
            {"id": "parking", "name": "Accessible Parking", "icon": "🅿️"}
        ]
        
        # Define time shortcuts
        time_shortcuts = [
            {"id": "tonight", "name": "Tonight", "icon": "🌙"},
            {"id": "weekend", "name": "This Weekend", "icon": "📅"},
            {"id": "this_week", "name": "This Week", "icon": "📆"},
            {"id": "this_month", "name": "This Month", "icon": "🗓️"}
        ]
        
        return jsonify({
            "success": True,
            "filters": {
                "cities": sorted(city_list),
                "venues": sorted(venue_list),
                "categories": categories,
                "accessibility": accessibility_options,
                "time_shortcuts": time_shortcuts,
                "providers": [
                    {"id": "all", "name": "All Sources", "icon": "🌐"},
                    {"id": "ticketmaster", "name": "Ticketmaster", "icon": "🎫"},
                    {"id": "eventbrite", "name": "Eventbrite", "icon": "📅"},
                    {"id": "csv", "name": "Local Events", "icon": "🏠"}
                ]
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Event Sharing endpoints
@bp.route("/events/share", methods=["POST"])
@limiter.limit("20/minute")
def share_event():
    """Share an event on social media or via other platforms"""
    try:
        data = request.get_json() or {}
        user_email = (data.get("email") or "").strip() or None
        event_title = data.get("title", "")
        event_url = data.get("url")
        event_venue = data.get("venue")
        event_city = data.get("city")
        event_date = data.get("date")
        platform = data.get("platform", "").lower()  # facebook, twitter, email, whatsapp, etc.
        
        if not event_title:
            return jsonify({"success": False, "error": "Event title is required"}), 400
        
        if not platform:
            return jsonify({"success": False, "error": "Platform is required"}), 400
        
        # Parse event date if provided
        parsed_date = None
        if event_date:
            try:
                parsed_date = datetime.fromisoformat(event_date).date()
            except Exception:
                pass
        
        # Create share record
        share = EventShare(
            user_email=user_email,
            event_title=event_title,
            event_url=event_url,
            event_venue=event_venue,
            event_city=event_city,
            event_date=parsed_date,
            share_platform=platform,
            share_url=None  # Will be set by frontend
        )
        
        db.session.add(share)
        db.session.commit()
        
        # Generate share URLs based on platform
        share_urls = {}
        base_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        
        if platform == "facebook":
            share_urls["facebook"] = f"https://www.facebook.com/sharer/sharer.php?u={event_url or base_url}"
        elif platform == "twitter":
            text = f"Check out this event: {event_title}"
            if event_venue:
                text += f" at {event_venue}"
            share_urls["twitter"] = f"https://twitter.com/intent/tweet?text={text}&url={event_url or base_url}"
        elif platform == "linkedin":
            share_urls["linkedin"] = f"https://www.linkedin.com/sharing/share-offsite/?url={event_url or base_url}"
        elif platform == "whatsapp":
            text = f"Check out this event: {event_title}"
            if event_venue:
                text += f" at {event_venue}"
            share_urls["whatsapp"] = f"https://wa.me/?text={text}%20{event_url or base_url}"
        elif platform == "email":
            subject = f"Event Recommendation: {event_title}"
            body = f"Hi! I thought you might be interested in this event:\n\n{event_title}"
            if event_venue:
                body += f"\nVenue: {event_venue}"
            if event_city:
                body += f"\nCity: {event_city}"
            if event_date:
                body += f"\nDate: {event_date}"
            if event_url:
                body += f"\nMore info: {event_url}"
            share_urls["email"] = f"mailto:?subject={subject}&body={body}"
        
        return jsonify({
            "success": True,
            "message": f"Event shared on {platform}",
            "share_id": share.id,
            "share_urls": share_urls
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# Event Reviews endpoints
@bp.route("/events/reviews", methods=["GET"])
def get_event_reviews():
    """Get reviews for a specific event"""
    try:
        event_title = request.args.get("event_title", "").strip()
        event_url = request.args.get("event_url", "").strip()
        limit = int(request.args.get("limit", 20))
        
        query = EventReview.query
        
        if event_title:
            query = query.filter(EventReview.event_title.ilike(f"%{event_title}%"))
        if event_url:
            query = query.filter(EventReview.event_url == event_url)
        
        reviews = query.order_by(EventReview.created_at.desc()).limit(limit).all()
        
        # Calculate average rating
        avg_rating = 0
        if reviews:
            total_rating = sum(review.rating for review in reviews)
            avg_rating = round(total_rating / len(reviews), 1)
        
        return jsonify({
            "success": True,
            "reviews": [review.to_dict() for review in reviews],
            "average_rating": avg_rating,
            "total_reviews": len(reviews)
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route("/events/reviews", methods=["POST"])
@limiter.limit("5/minute")
def add_event_review():
    """Add a review for an event"""
    try:
        data = request.get_json() or {}
        user_email = (data.get("email") or "").strip()
        event_title = data.get("title", "").strip()
        event_url = data.get("url")
        rating = data.get("rating")
        review_text = data.get("review_text", "").strip()
        event_date = data.get("event_date")
        
        if not user_email:
            return jsonify({"success": False, "error": "Email is required"}), 400
        
        if not event_title:
            return jsonify({"success": False, "error": "Event title is required"}), 400
        
        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({"success": False, "error": "Rating must be between 1 and 5"}), 400
        
        # Parse event date if provided
        parsed_date = None
        if event_date:
            try:
                parsed_date = datetime.fromisoformat(event_date).date()
            except Exception:
                pass
        
        # Check if user already reviewed this event
        existing_review = EventReview.query.filter_by(
            user_email=user_email,
            event_title=event_title,
            event_date=parsed_date
        ).first()
        
        if existing_review:
            # Update existing review
            existing_review.rating = rating
            existing_review.review_text = review_text
            existing_review.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Review updated successfully",
                "review": existing_review.to_dict()
            })
        else:
            # Create new review
            review = EventReview(
                user_email=user_email,
                event_title=event_title,
                event_url=event_url,
                rating=rating,
                review_text=review_text,
                event_date=parsed_date
            )
            
            db.session.add(review)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Review added successfully",
                "review": review.to_dict()
            })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# Recommendations endpoints
@bp.route("/events/recommendations")
def get_recommendations():
    """Get personalized event recommendations for a user"""
    try:
        user_email = request.args.get("email", "").strip()
        limit = int(request.args.get("limit", 10))
        
        if not user_email:
            return jsonify({"success": False, "error": "Email is required"}), 400
        
        recommendations = recommendation_service.get_personalized_recommendations(user_email, limit)
        
        return jsonify({
            "success": True,
            "recommendations": recommendations,
            "total": len(recommendations)
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route("/events/trending")
def get_trending_events():
    """Get trending events based on recent activity"""
    try:
        limit = int(request.args.get("limit", 10))
        
        trending = recommendation_service.get_trending_events(limit)
        
        return jsonify({
            "success": True,
            "trending": trending,
            "total": len(trending)
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Subscription endpoints
@bp.route("/subscription/plans")
def get_subscription_plans():
    """Get available subscription plans"""
    try:
        plans = [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "currency": "USD",
                "interval": "month",
                "features": [
                    "Up to 10 saved events",
                    "Basic event discovery",
                    "Community reviews",
                    "Email notifications"
                ],
                "limits": {
                    "max_favorites": 10,
                    "max_reviews": 5,
                    "ad_free": False,
                    "priority_support": False,
                    "early_access": False,
                    "advanced_filters": False
                }
            },
            {
                "id": "premium",
                "name": "Premium",
                "price": 9.99,
                "currency": "USD",
                "interval": "month",
                "features": [
                    "Up to 100 saved events",
                    "Ad-free experience",
                    "Advanced search filters",
                    "Priority customer support",
                    "Early access to events",
                    "Personalized recommendations"
                ],
                "limits": {
                    "max_favorites": 100,
                    "max_reviews": 50,
                    "ad_free": True,
                    "priority_support": True,
                    "early_access": True,
                    "advanced_filters": True
                }
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 19.99,
                "currency": "USD",
                "interval": "month",
                "features": [
                    "Unlimited saved events",
                    "Unlimited reviews",
                    "Ad-free experience",
                    "Advanced search filters",
                    "Priority customer support",
                    "Early access to events",
                    "Personalized recommendations",
                    "Event analytics"
                ],
                "limits": {
                    "max_favorites": -1,
                    "max_reviews": -1,
                    "ad_free": True,
                    "priority_support": True,
                    "early_access": True,
                    "advanced_filters": True
                }
            }
        ]
        
        return jsonify({
            "success": True,
            "plans": plans
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route("/subscription/status")
def get_subscription_status():
    """Get user's subscription status"""
    try:
        user_email = request.args.get("email", "").strip()
        
        if not user_email:
            return jsonify({"success": False, "error": "Email is required"}), 400
        
        # Get user's subscription
        subscription = Subscription.query.filter_by(user_email=user_email, status='active').first()
        
        if not subscription or not subscription.is_active():
            # Return free plan status
            return jsonify({
                "success": True,
                "subscription": {
                    "plan_type": "free",
                    "status": "active",
                    "limits": {
                        "max_favorites": 10,
                        "max_reviews": 5,
                        "ad_free": False,
                        "priority_support": False,
                        "early_access": False,
                        "advanced_filters": False
                    }
                }
            })
        
        return jsonify({
            "success": True,
            "subscription": {
                "plan_type": subscription.plan_type,
                "status": subscription.status,
                "end_date": subscription.end_date.isoformat() if subscription.end_date else None,
                "limits": subscription.get_plan_limits()
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route("/subscription/upgrade", methods=["POST"])
def upgrade_subscription():
    """Upgrade user subscription (mock implementation)"""
    try:
        data = request.get_json() or {}
        user_email = (data.get("email") or "").strip()
        plan_type = data.get("plan_type", "").strip().lower()
        
        if not user_email:
            return jsonify({"success": False, "error": "Email is required"}), 400
        
        if plan_type not in ["premium", "pro"]:
            return jsonify({"success": False, "error": "Invalid plan type"}), 400
        
        # Check if user already has an active subscription
        existing_sub = Subscription.query.filter_by(user_email=user_email, status='active').first()
        
        if existing_sub:
            # Update existing subscription
            existing_sub.plan_type = plan_type
            existing_sub.updated_at = datetime.utcnow()
            # Set end date to 1 month from now
            existing_sub.end_date = datetime.utcnow() + timedelta(days=30)
            db.session.commit()
        else:
            # Create new subscription
            subscription = Subscription(
                user_email=user_email,
                plan_type=plan_type,
                status='active',
                end_date=datetime.utcnow() + timedelta(days=30),
                payment_method='mock',  # In real implementation, this would be from payment processor
                payment_id=f"mock_{user_email}_{datetime.utcnow().timestamp()}"
            )
            db.session.add(subscription)
            db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Successfully upgraded to {plan_type} plan",
            "subscription": {
                "plan_type": plan_type,
                "status": "active",
                "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "limits": Subscription(plan_type=plan_type).get_plan_limits()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


# Admin endpoints
@bp.route("/admin/send-reminders", methods=["POST"])
def send_event_reminders():
    """Send event reminders (admin endpoint)"""
    try:
        sent_count = notification_service.send_event_reminders()
        return jsonify({
            "success": True,
            "message": f"Sent {sent_count} event reminders"
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route("/admin/send-digest", methods=["POST"])
def send_daily_digest():
    """Send daily digest (admin endpoint)"""
    try:
        notification_service.send_daily_digest()
        return jsonify({
            "success": True,
            "message": "Daily digest sent"
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500