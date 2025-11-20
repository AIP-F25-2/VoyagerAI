import googlemaps
from datetime import datetime

# Initialize the Google Maps client with your API key
gmaps = googlemaps.Client(key='AIzaSyChVA38WwvepIGTSjiVHzEmD_S7seYq9jk')

# Function to get the distance using the Routes API
def get_distance(start_location, end_location):
    # Request the route between the two locations using the Google Maps Routes API
    route = gmaps.directions(start_location, end_location, mode="driving", departure_time=datetime.now())

    if route:
        # Extract distance and duration from the response
        distance = route[0]['legs'][0]['distance']['text']
        duration = route[0]['legs'][0]['duration']['text']
        return distance, duration
    else:
        return None, None

# Example usage
start_location = "Toronto, Canada"  # User's current location (can be a city name or lat/lng)
end_location = "Mumbai, India"      # Destination location (can be a city name or lat/lng)

distance, duration = get_distance(start_location, end_location)

if distance and duration:
    print(f"The distance from {start_location} to {end_location} is {distance} and it will take approximately {duration}.")
else:
    print("Sorry, we couldn't calculate the distance at this time.")
