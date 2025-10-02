from .db import db

# Ticketmaster collection
ticketmaster_col = db.ticketmaster
# Eventbrite collection
eventbrite_col = db.eventbrite

def save_ticketmaster_events(events: list):
    """Insert or update Ticketmaster events"""
    for ev in events:
        ev["_source"] = "ticketmaster"
        ticketmaster_col.update_one({"id": ev["id"]}, {"$set": ev}, upsert=True)

def save_eventbrite_events(events: list):
    """Insert or update Eventbrite events"""
    for ev in events:
        ev["_source"] = "eventbrite"
        eventbrite_col.update_one({"id": ev["id"]}, {"$set": ev}, upsert=True)

def get_all_ticketmaster():
    """Get all Ticketmaster events from DB"""
    return list(ticketmaster_col.find({}, {"_id": 0}))

def get_all_eventbrite():
    """Get all Eventbrite events from DB"""
    return list(eventbrite_col.find({}, {"_id": 0}))

def get_all_events():
    """Get all events from both collections"""
    return get_all_ticketmaster() + get_all_eventbrite()
