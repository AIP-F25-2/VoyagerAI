from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
            'id': self.id,
            'title': self.title,
            'date': self.date.isoformat() if self.date else None,
            'time': self.time.strftime('%H:%M') if self.time else None,
            'venue': self.venue,
            'place': self.place,
            'price': self.price,
            'url': self.url,
            'city': self.city,
            'created_at': self.created_at.isoformat()
        }
