# database.py (mock demo database)

# Fake in-memory "tables" with preloaded data
places_db = [
    {"id": 1, "name": "Eiffel Tower", "location": "Paris, France", "description": "Iconic landmark"},
    {"id": 2, "name": "Statue of Liberty", "location": "New York, USA", "description": "Historic monument"},
    {"id": 3, "name": "Taj Mahal", "location": "Agra, India", "description": "Famous marble mausoleum"}
]

hotels_db = [
    {
        "id": 1,
        "name": "Hilton Midtown",
        "address": "123 Main Street",
        "city": "New York",
        "country": "USA",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "rating": 4.3,
        "price_range": "200-300 USD/night",
        "source": "Demo"
    },
    {
        "id": 2,
        "name": "Marriott Champs Elysees",
        "address": "Avenue des Champs Elysees",
        "city": "Paris",
        "country": "France",
        "latitude": 48.8566,
        "longitude": 2.3522,
        "rating": 4.5,
        "price_range": "250-400 EUR/night",
        "source": "Demo"
    },
    {
        "id": 3,
        "name": "Oberoi Amarvilas",
        "address": "Near Taj Mahal",
        "city": "Agra",
        "country": "India",
        "latitude": 27.1751,
        "longitude": 78.0421,
        "rating": 4.8,
        "price_range": "350-600 USD/night",
        "source": "Demo"
    }
]

def get_places_db():
    return places_db

def get_hotels_db():
    return hotels_db
