from flask import Blueprint, jsonify, request
from .services.ticketmaster import fetch_events

bp = Blueprint("api", __name__)

@bp.route("/")
def home():
    """Test route to check backend is running"""
    return {"message": "Hello from Flask!"}

@bp.route("/events")
def get_events():
    """Fetch events from Ticketmaster"""
    query = request.args.get("q", "music")
    data = fetch_events(query)
    return jsonify(data)
