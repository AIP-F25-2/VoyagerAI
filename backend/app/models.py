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
    is_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(255), nullable=True)
    password_reset_token = db.Column(db.String(255), nullable=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)

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

    def generate_verification_token(self):
        """Generate email verification token"""
        payload = {
            'user_id': self.id,
            'email': self.email,
            'type': 'email_verification',
            'exp': datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry
        }
        secret_key = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        self.email_verification_token = token
        return token

    def generate_password_reset_token(self):
        """Generate password reset token"""
        payload = {
            'user_id': self.id,
            'email': self.email,
            'type': 'password_reset',
            'exp': datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
        }
        secret_key = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        self.password_reset_token = token
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        return token

    @staticmethod
    def verify_token(token, token_type='email_verification'):
        """Verify JWT token and return user"""
        try:
            secret_key = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            
            if payload.get('type') != token_type:
                return None
                
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
            "is_active": self.is_active,
            "is_verified": self.is_verified
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

    # Enforce uniqueness at the DB level to prevent duplicates
    __table_args__ = (
        db.UniqueConstraint('user_email', 'url', name='uq_favorite_user_url'),
        db.UniqueConstraint('user_email', 'title', 'date', 'provider', name='uq_favorite_user_title_date_provider'),
    )

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


class Itinerary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    destination = db.Column(db.String(200), nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    budget = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), default='draft')  # draft, active, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with user
    user = db.relationship('User', backref=db.backref('itineraries', lazy=True))
    
    # Relationship with itinerary items
    items = db.relationship('ItineraryItem', backref='itinerary', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "destination": self.destination,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "budget": self.budget,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "items": [item.to_dict() for item in self.items] if self.items else []
        }


class ItineraryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    itinerary_id = db.Column(db.Integer, db.ForeignKey('itinerary.id'), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)  # event, hotel, flight, activity, note
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=True)
    time = db.Column(db.Time, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    price = db.Column(db.Float, nullable=True)
    url = db.Column(db.String(1000), nullable=True)
    image_url = db.Column(db.String(1000), nullable=True)
    status = db.Column(db.String(50), default='planned')  # planned, confirmed, completed, cancelled
    order_index = db.Column(db.Integer, default=0)  # For ordering items within itinerary
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "itinerary_id": self.itinerary_id,
            "item_type": self.item_type,
            "title": self.title,
            "description": self.description,
            "date": self.date.isoformat() if self.date else None,
            "time": self.time.strftime("%H:%M") if self.time else None,
            "location": self.location,
            "price": self.price,
            "url": self.url,
            "image_url": self.image_url,
            "status": self.status,
            "order_index": self.order_index,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class EventShare(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(200), nullable=True)
    event_title = db.Column(db.String(500), nullable=False)
    event_url = db.Column(db.String(1000), nullable=True)
    event_venue = db.Column(db.String(200), nullable=True)
    event_city = db.Column(db.String(100), nullable=True)
    event_date = db.Column(db.Date, nullable=True)
    share_platform = db.Column(db.String(50), nullable=False)  # facebook, twitter, email, whatsapp, etc.
    share_url = db.Column(db.String(1000), nullable=True)  # The actual shared URL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_email": self.user_email,
            "event_title": self.event_title,
            "event_url": self.event_url,
            "event_venue": self.event_venue,
            "event_city": self.event_city,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "share_platform": self.share_platform,
            "share_url": self.share_url,
            "created_at": self.created_at.isoformat()
        }


class EventReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(200), nullable=False)
    event_title = db.Column(db.String(500), nullable=False)
    event_url = db.Column(db.String(1000), nullable=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    review_text = db.Column(db.Text, nullable=True)
    event_date = db.Column(db.Date, nullable=True)  # When they attended
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Enforce one review per user per event
    __table_args__ = (
        db.UniqueConstraint('user_email', 'event_title', 'event_date', name='uq_review_user_event_date'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_email": self.user_email,
            "event_title": self.event_title,
            "event_url": self.event_url,
            "rating": self.rating,
            "review_text": self.review_text,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(200), nullable=False)
    plan_type = db.Column(db.String(50), nullable=False)  # free, premium, pro
    status = db.Column(db.String(20), nullable=False, default='active')  # active, cancelled, expired
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    auto_renew = db.Column(db.Boolean, default=True)
    payment_method = db.Column(db.String(100), nullable=True)  # stripe, paypal, etc.
    payment_id = db.Column(db.String(200), nullable=True)  # External payment ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Enforce one active subscription per user
    __table_args__ = (
        db.UniqueConstraint('user_email', 'status', name='uq_user_active_subscription'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_email": self.user_email,
            "plan_type": self.plan_type,
            "status": self.status,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "auto_renew": self.auto_renew,
            "payment_method": self.payment_method,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def is_active(self):
        """Check if subscription is currently active"""
        if self.status != 'active':
            return False
        if self.end_date and self.end_date < datetime.utcnow():
            return False
        return True
    
    def get_plan_limits(self):
        """Get plan limits based on subscription type"""
        limits = {
            'free': {
                'max_favorites': 10,
                'max_reviews': 5,
                'ad_free': False,
                'priority_support': False,
                'early_access': False,
                'advanced_filters': False
            },
            'premium': {
                'max_favorites': 100,
                'max_reviews': 50,
                'ad_free': True,
                'priority_support': True,
                'early_access': True,
                'advanced_filters': True
            },
            'pro': {
                'max_favorites': -1,  # Unlimited
                'max_reviews': -1,    # Unlimited
                'ad_free': True,
                'priority_support': True,
                'early_access': True,
                'advanced_filters': True
            }
        }
        return limits.get(self.plan_type, limits['free'])

