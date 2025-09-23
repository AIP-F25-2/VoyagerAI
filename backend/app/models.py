from .db import db

class Event(db.Model):
    __tablename__ = "events"
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    date = db.Column(db.String)
    venue = db.Column(db.String)
