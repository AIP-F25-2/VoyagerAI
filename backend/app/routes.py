from flask import Blueprint, jsonify, request
from .models import db, Event
from .services.scraper import scrape_bookmyshow_events
from datetime import datetime, date, time

bp = Blueprint("api", __name__)

@bp.route("/")
def home():
    """Test route to check backend is running"""
    return {"message": "Hello from Flask!"}

@bp.route("/events")
def get_events():
    """Get events from database"""
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
            "events": [event.to_dict() for event in events]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route("/scrape", methods=["POST"])
def scrape_events():
    """Scrape events from BookMyShow and save to database"""
    try:
        data = request.get_json() or {}
        city = data.get("city", "Mumbai")
        limit = data.get("limit", 10)
        
        # Scrape events
        scraped_events = scrape_bookmyshow_events(city, limit)
        
        # Save to database
        saved_count = 0
        for event_data in scraped_events:
            # Check if event already exists
            existing = Event.query.filter_by(url=event_data.get("url")).first()
            if existing:
                continue
                
            # Parse date and time
            event_date = None
            event_time = None
            if event_data.get("date"):
                try:
                    event_date = datetime.strptime(event_data["date"], "%Y-%m-%d").date()
                except:
                    pass
            if event_data.get("time"):
                try:
                    event_time = datetime.strptime(event_data["time"], "%H:%M").time()
                except:
                    pass
            
            event = Event(
                title=event_data.get("title", ""),
                date=event_date,
                time=event_time,
                venue=event_data.get("venue"),
                place=event_data.get("place"),
                price=event_data.get("price"),
                url=event_data.get("url"),
                city=city
            )
            
            db.session.add(event)
            saved_count += 1
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Scraped {len(scraped_events)} events, saved {saved_count} new events",
            "scraped_count": len(scraped_events),
            "saved_count": saved_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route("/events/<int:event_id>")
def get_event(event_id):
    """Get a specific event by ID"""
    try:
        event = Event.query.get_or_404(event_id)
        return jsonify({"success": True, "event": event.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route("/events/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    """Delete a specific event"""
    try:
        event = Event.query.get_or_404(event_id)
        db.session.delete(event)
        db.session.commit()
        return jsonify({"success": True, "message": "Event deleted"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
