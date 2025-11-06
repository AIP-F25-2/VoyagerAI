# VoyagerAI Hotel Features

This document describes the hotel functionality added to VoyagerAI backend, which allows users to search, view, and manage hotel information from CSV data sources.

## Features Added

### 1. Hotel Data Model
- **Hotel Model**: Enhanced SQLAlchemy model with fields for name, city, address, location, rating, review count, price, URL, and metadata
- **Database Integration**: Full CRUD operations for hotel management
- **CSV Integration**: Automatic loading and parsing of hotel data from CSV files

### 2. Hotel Service Layer
- **CSV Loader**: `HotelCSVLoader` class that parses and loads hotel data from CSV files
- **Search Functions**: Multiple search methods for finding hotels by city, query, or rating
- **Data Parsing**: Intelligent parsing of rating and review information from CSV text

### 3. API Endpoints

#### CSV-based Endpoints (Real-time from CSV files)
- `GET /api/hotels` - Get hotels with filtering (city, query, min_rating, pagination)
- `GET /api/hotels/search` - Search hotels by city with check-in/check-out dates
- `GET /api/hotels/cities` - Get list of cities with available hotels
- `GET /api/hotels/popular` - Get popular hotels (highest rated)
- `GET /api/hotels/<hotel_id>` - Get detailed information about a specific hotel

#### Database CRUD Endpoints
- `GET /api/hotels/db` - Get hotels from database with filtering
- `GET /api/hotels/db/<hotel_id>` - Get specific hotel from database
- `POST /api/hotels/db` - Create new hotel in database
- `PUT /api/hotels/db/<hotel_id>` - Update hotel in database
- `DELETE /api/hotels/db/<hotel_id>` - Delete hotel from database

## Setup Instructions

### 1. Initialize Database
```bash
cd /Users/sujanvg/sujan/aip/VoyagerAI/backend
python init_db.py
```

### 2. Load Hotels from CSV
```bash
python load_hotels_to_db.py
```

### 3. Test Functionality
```bash
python test_hotels.py
```

### 4. Start Server
```bash
python wsgi.py
```

## CSV Data Structure

The hotel CSV files should have the following columns:
- **Hotel Name**: Name of the hotel
- **Location**: Full location string (e.g., "Financial District, Toronto (Financial District)")
- **Rating**: Rating text (e.g., "Scored 8.8\n8.8\nExcellent\n7,713 reviews")
- **Reviews**: Review count text
- **Price**: Price per night (optional)
- **URL**: Booking URL (optional)

## API Usage Examples

### Search Hotels by City
```bash
curl "http://localhost:5000/api/hotels/search?city=Toronto&limit=5"
```

### Get Hotels with Filtering
```bash
curl "http://localhost:5000/api/hotels?city=Toronto&min_rating=8.0&limit=10"
```

### Get Popular Hotels
```bash
curl "http://localhost:5000/api/hotels/popular?city=Toronto&limit=5"
```

### Get Available Cities
```bash
curl "http://localhost:5000/api/hotels/cities"
```

### Create Hotel in Database
```bash
curl -X POST "http://localhost:5000/api/hotels/db" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Hotel",
    "city": "Toronto",
    "address": "123 Test Street",
    "rating": 8.5,
    "review_count": 100,
    "price_per_night": "$150"
  }'
```

## Data Flow

1. **CSV Loading**: Hotel data is loaded from CSV files into memory using `HotelCSVLoader`
2. **Real-time Search**: API endpoints search the in-memory CSV data for fast responses
3. **Database Storage**: Optional database storage for persistent hotel management
4. **Hybrid Approach**: Both CSV (for bulk data) and database (for user-added hotels) are supported

## File Structure

```
backend/
├── app/
│   ├── models.py          # Hotel model definition
│   ├── routes.py          # Hotel API endpoints
│   └── services/
│       └── hotels.py      # Hotel service functions
├── booking_hotels.csv     # Hotel data source
├── booking_hotels_full.csv # Additional hotel data
├── load_hotels_to_db.py   # Database loading script
├── test_hotels.py         # Test script
└── init_db.py            # Database initialization
```

## Features

- **Fast CSV Search**: In-memory search for quick responses
- **Database Integration**: Full CRUD operations for hotel management
- **Intelligent Parsing**: Automatic extraction of ratings and review counts
- **City Extraction**: Smart city name extraction from location strings
- **Pagination**: Support for paginated results
- **Filtering**: Multiple filter options (city, rating, query)
- **Error Handling**: Comprehensive error handling and validation

## Future Enhancements

- **External API Integration**: Connect to real hotel booking APIs
- **Image Support**: Add hotel image URLs
- **Amenities**: Track hotel amenities and features
- **Price Comparison**: Compare prices across different sources
- **User Reviews**: Allow users to add reviews and ratings
- **Recommendations**: Personalized hotel recommendations based on user preferences
