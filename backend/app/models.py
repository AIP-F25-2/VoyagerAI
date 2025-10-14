from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import os
from datetime import datetime, timedelta

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


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return check_password_hash(self.password_hash, password)

    def generate_token(self):
        """Generate JWT token for the user"""
        payload = {
            'user_id': self.id,
            'email': self.email,
            'exp': datetime.utcnow() + timedelta(days=7)  # Token expires in 7 days
        }
        secret_key = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
        return jwt.encode(payload, secret_key, algorithm='HS256')

    @staticmethod
    def verify_token(token):
        """Verify JWT token and return user"""
        try:
            secret_key = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            user_id = payload['user_id']
            return User.query.get(user_id)
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def to_dict(self):
        """Convert user to dictionary (without password)"""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active
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


class Hotel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    city = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(500), nullable=True)
    rating = db.Column(db.Float, nullable=True)
    price_per_night = db.Column(db.String(50), nullable=True)
    url = db.Column(db.String(1000), nullable=True)
    check_in = db.Column(db.Date, nullable=True)
    check_out = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "city": self.city,
            "address": self.address,
            "rating": self.rating,
            "price_per_night": self.price_per_night,
            "url": self.url,
            "check_in": self.check_in.isoformat() if self.check_in else None,
            "check_out": self.check_out.isoformat() if self.check_out else None,
        }


class Flight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    origin = db.Column(db.String(10), nullable=False)
    destination = db.Column(db.String(10), nullable=False)
    departure_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=True)
    airline = db.Column(db.String(120), nullable=True)
    flight_number = db.Column(db.String(50), nullable=True)
    price = db.Column(db.String(50), nullable=True)
    url = db.Column(db.String(1000), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "origin": self.origin,
            "destination": self.destination,
            "departure_date": self.departure_date.isoformat() if self.departure_date else None,
            "return_date": self.return_date.isoformat() if self.return_date else None,
            "airline": self.airline,
            "flight_number": self.flight_number,
            "price": self.price,
            "url": self.url,
        }


class EventImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    url = db.Column(db.String(1000), nullable=False)
    source = db.Column(db.String(50), nullable=True)  # e.g., 'pixabay'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # If not authenticated, allow storing by email or anonymous token later
    user_email = db.Column(db.String(200), nullable=True)
    # Store minimal event snapshot for external events also
    title = db.Column(db.String(500), nullable=False)
    date = db.Column(db.Date, nullable=True)
    time = db.Column(db.Time, nullable=True)
    venue = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    url = db.Column(db.String(1000), nullable=True)
    image_url = db.Column(db.String(1000), nullable=True)
    provider = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_email": self.user_email,
            "title": self.title,
            "date": self.date.isoformat() if self.date else None,
            "time": self.time.strftime("%H:%M") if self.time else None,
            "venue": self.venue,
            "city": self.city,
            "url": self.url,
            "image_url": self.image_url,
            "provider": self.provider,
            "created_at": self.created_at.isoformat()
        }

