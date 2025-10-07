from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# SQLAlchemy (sujan branch)
db = SQLAlchemy()


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    date = db.Column(db.Date, nullable=True)
    time = db.Column(db.Time, nullable=True)
    venue = db.Column(db.String(200), nullable=True)
    place = db.Column(db.String(200), nullable=True)
    price = db.Column(db.String(100), nullable=True)
    url = db.Column(db.String(1000), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "date": self.date.isoformat() if self.date else None,
            "time": self.time.strftime("%H:%M") if self.time else None,
            "venue": self.venue,
            "place": self.place,
            "price": self.price,
            "url": self.url,
            "city": self.city,
            "created_at": self.created_at.isoformat(),
        }


# Mongo helpers (nischal branch)
try:
    from .db import db as mongo_db  # type: ignore

    ticketmaster_col = mongo_db.ticketmaster
    eventbrite_col = mongo_db.eventbrite

    def save_ticketmaster_events(events: list):
        for ev in events:
            ev["_source"] = "ticketmaster"
            ticketmaster_col.update_one({"id": ev.get("id")}, {"$set": ev}, upsert=True)

    def save_eventbrite_events(events: list):
        for ev in events:
            ev["_source"] = "eventbrite"
            eventbrite_col.update_one({"id": ev.get("id")}, {"$set": ev}, upsert=True)

    def get_all_ticketmaster():
        return list(ticketmaster_col.find({}, {"_id": 0}))

    def get_all_eventbrite():
        return list(eventbrite_col.find({}, {"_id": 0}))

    def get_all_events():
        return get_all_ticketmaster() + get_all_eventbrite()
except Exception:
    # Mongo not configured; leave SQLAlchemy-only functionality
    pass
