# VoyagerAI - Complete Travel Planning Platform

**A comprehensive event discovery and travel planning application with hotel booking, itinerary management, and real-time event data integration.**

## 🚀 Project Overview

VoyagerAI is a full-stack travel planning platform that combines event discovery, hotel booking, and itinerary management into a seamless user experience. Built with modern technologies and real-time data integration.

### 🎯 Key Features

- **🎫 Event Discovery**: Real-time events from Ticketmaster, Eventbrite, and local sources
- **🏨 Hotel Booking**: Toronto hotels with real ratings, prices, and booking links
- **📋 Travel Planning**: Create and manage complete travel itineraries
- **🔍 Advanced Search**: Smart filtering by city, category, venue, price, and accessibility
- **👤 User Management**: Authentication, profiles, and personalized experiences
- **📱 Responsive Design**: Works perfectly on desktop and mobile devices

## 🏗️ Architecture

### Backend (Python Flask)
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL with SQLite fallback
- **Authentication**: JWT-based user authentication
- **APIs**: RESTful API with comprehensive endpoints
- **Data Sources**: Ticketmaster API, Eventbrite, CSV files, web scraping

### Frontend (Next.js React)
- **Framework**: Next.js 15 with React 18
- **Styling**: Tailwind CSS with custom components
- **State Management**: React Context API
- **Authentication**: JWT token management
- **UI Components**: Custom reusable components

## 📊 Database Schema

### Core Tables
```sql
-- Users and Authentication
users (id, email, name, password_hash, created_at)

-- Events
events (id, title, description, date, time, venue, city, price, url, source, created_at)

-- Hotels
hotels (id, name, city, address, rating, review_count, price_per_night, url, source, created_at)

-- Travel Planning
itineraries (id, user_id, title, destination, start_date, end_date, budget, status, created_at)
itinerary_items (id, itinerary_id, item_type, title, description, date, time, location, price, url, order_index)

-- User Features
favorites (id, user_email, title, venue, city, url, image_url, provider, date, created_at)
event_reviews (id, event_id, user_email, rating, comment, created_at)
```

## 🔧 Technology Stack

### Backend Technologies
- **Python 3.9+**: Core language
- **Flask 3.0**: Web framework
- **SQLAlchemy 2.0**: Database ORM
- **PostgreSQL**: Primary database
- **SQLite**: Development fallback
- **Playwright**: Web scraping
- **Pandas**: Data processing
- **JWT**: Authentication
- **Flask-CORS**: Cross-origin requests
- **Flask-Limiter**: Rate limiting

### Frontend Technologies
- **Next.js 15**: React framework
- **React 18**: UI library
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **React Context**: State management
- **Fetch API**: HTTP requests

### External APIs
- **Ticketmaster API**: Real-time event data
- **Eventbrite API**: Additional event sources
- **Booking.com**: Hotel data integration
- **Pixabay API**: Event images

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL (optional, SQLite works)
- Git

### One-Command Setup
```bash
git clone <repository>
cd VoyagerAI
./start_all.sh
```

### Manual Setup

#### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python init_db.py
python load_hotels_to_db.py  # Load hotel data
python wsgi.py
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5001
- **API Documentation**: http://localhost:5001/api

## 📡 API Endpoints

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/profile` - Get user profile
- `POST /api/auth/verify-token` - Verify JWT token

### Events
- `GET /api/events` - Get events with filtering
- `GET /api/events/{id}` - Get specific event
- `POST /api/scrape` - Scrape new events
- `GET /api/events/filters` - Get filter options
- `POST /api/events/reviews` - Add event review
- `GET /api/events/recommendations` - Get recommendations

### Hotels
- `GET /api/hotels` - Get hotels with filtering
- `GET /api/hotels/search` - Search hotels by city
- `GET /api/hotels/cities` - Get available cities
- `GET /api/hotels/popular` - Get popular hotels
- `GET /api/hotels/{id}` - Get hotel details

### Travel Planning
- `GET /api/travel-plans` - Get user itineraries
- `POST /api/travel-plans` - Create new itinerary
- `GET /api/travel-plans/{id}` - Get specific itinerary
- `PUT /api/travel-plans/{id}` - Update itinerary
- `DELETE /api/travel-plans/{id}` - Delete itinerary
- `POST /api/travel-plans/{id}/items` - Add item to itinerary
- `PUT /api/travel-plans/{id}/items/{itemId}` - Update itinerary item
- `DELETE /api/travel-plans/{id}/items/{itemId}` - Delete itinerary item

### User Features
- `GET /api/favorites` - Get user favorites
- `POST /api/favorites` - Add to favorites
- `DELETE /api/favorites/{id}` - Remove from favorites

## 🎨 Frontend Components

### Core Components
- **Header**: Navigation with authentication
- **SearchBar**: Event and hotel search
- **AdvancedFilters**: Multi-criteria filtering
- **EventCard**: Event display with actions
- **HotelCard**: Hotel display with booking
- **HotelsPlanner**: Hotel search interface
- **FlightsPlanner**: Flight search interface
- **AddToItinerary**: Add items to travel plans

### Pages
- **Home (`/`)**: Main dashboard with search and planning tools
- **Hotels (`/hotels`)**: Dedicated hotel search and booking
- **Travel Plans (`/travel-plans`)**: Itinerary management
- **Travel Plan Detail (`/travel-plans/[id]`)**: Individual itinerary view
- **Authentication**: Login, signup, profile management

## 🏨 Hotel Integration

### Data Sources
- **CSV Files**: `booking_hotels.csv`, `booking_hotels_full.csv`
- **Real Data**: 22+ Toronto hotels with actual ratings and prices
- **Booking Links**: Direct links to Booking.com

### Features
- **City Search**: Search hotels by city (Toronto, Mumbai, Delhi, etc.)
- **Rating Filter**: Filter by hotel ratings
- **Price Display**: Real pricing information
- **Review Counts**: Actual review numbers
- **Itinerary Integration**: Add hotels to travel plans

## 📋 Travel Planning Features

### Itinerary Management
- **Mixed Content**: Events and hotels in same itinerary
- **Drag & Drop**: Reorder items
- **Date Management**: Set dates and times
- **Budget Tracking**: Track expenses
- **Status Management**: Draft, active, completed

### Item Types
- **Events**: Concerts, sports, theater, festivals
- **Hotels**: Accommodations with booking links
- **Flights**: Flight information (planned)
- **Activities**: Custom activities
- **Notes**: Personal notes

## 🔍 Search & Filtering

### Event Filters
- **Text Search**: Full-text search across names and descriptions
- **City Filter**: Filter by specific cities
- **Category Filter**: Music, sports, arts, food, tech, business
- **Venue Filter**: Filter by specific venues
- **Time Filter**: Today, this week, this month
- **Price Range**: Min/max price filtering
- **Provider Filter**: Ticketmaster, Eventbrite, local sources

### Hotel Filters
- **City Search**: Search hotels by city
- **Rating Filter**: Filter by hotel ratings
- **Price Range**: Filter by price per night
- **Popular Hotels**: Highest rated hotels

## 👤 User Management

### Authentication
- **JWT Tokens**: Secure authentication
- **Password Hashing**: Secure password storage
- **Session Management**: Persistent login sessions
- **Profile Management**: User profile updates

### User Features
- **Favorites**: Save events and hotels
- **Reviews**: Rate and review events
- **Travel Plans**: Create and manage itineraries
- **Personalization**: Customized recommendations

## 📊 Data Management

### Event Data Sources
1. **Ticketmaster API**: Real-time events from major cities
2. **Database Events**: User-added and scraped events
3. **CSV Files**: Local event data
4. **Web Scraping**: Additional event sources

### Hotel Data Sources
1. **CSV Files**: Curated hotel data
2. **Database Storage**: Persistent hotel information
3. **Real-time Integration**: Booking.com links

## 🚀 Deployment Ready

### Production Considerations
- **Environment Variables**: Configurable settings
- **Database Migration**: Schema management
- **Error Handling**: Comprehensive error management
- **Rate Limiting**: API protection
- **CORS Configuration**: Cross-origin support
- **Logging**: Application monitoring

### Scalability Features
- **Database Optimization**: Efficient queries
- **Caching**: Flask-Caching integration
- **API Rate Limiting**: Request throttling
- **Modular Architecture**: Easy to extend

## 🧪 Testing & Quality

### Backend Testing
- **API Testing**: Comprehensive endpoint testing
- **Database Testing**: Data integrity validation
- **Error Handling**: Graceful error management
- **Performance Testing**: Response time optimization

### Frontend Testing
- **Component Testing**: UI component validation
- **Integration Testing**: API integration testing
- **User Experience**: Responsive design validation

## 📈 Performance Metrics

### Current Capabilities
- **Events**: 1000+ events from multiple sources
- **Hotels**: 22+ Toronto hotels with real data
- **Response Time**: Sub-second API responses
- **Concurrent Users**: Supports multiple simultaneous users
- **Database**: Optimized queries with proper indexing

## 🔮 Future Enhancements

### Planned Features
- **Elasticsearch Integration**: Advanced search capabilities
- **Real-time Notifications**: Event updates and alerts
- **Social Features**: Share itineraries and reviews
- **Mobile App**: Native mobile application
- **AI Recommendations**: Machine learning suggestions
- **Payment Integration**: Direct booking and payments

## 🛠️ Development Commands

### Backend Development
```bash
cd backend
source venv/bin/activate
python wsgi.py                    # Start development server
python init_db.py                 # Initialize database
python load_hotels_to_db.py       # Load hotel data
python test_hotels.py             # Test hotel functionality
```

### Frontend Development
```bash
cd frontend
npm run dev                       # Start development server
npm run build                     # Build for production
npm run lint                      # Run linting
```

### Database Management
```bash
cd backend
python setup_database.py          # Setup PostgreSQL
python init_db.py                 # Create tables
python migrate_db.py              # Run migrations
```

## 📚 Documentation

### API Documentation
- **Swagger/OpenAPI**: Available at `/api/docs`
- **Postman Collection**: Available in `/docs` folder
- **Example Requests**: Included in API endpoints

### Code Documentation
- **Inline Comments**: Comprehensive code documentation
- **Type Hints**: Python type annotations
- **TypeScript**: Full type safety in frontend

## 🎯 Presentation Highlights

### Technical Achievements
1. **Full-Stack Development**: Complete backend and frontend
2. **Real-time Data Integration**: Multiple API sources
3. **Database Design**: Optimized schema with relationships
4. **User Authentication**: Secure JWT implementation
5. **Responsive Design**: Mobile-first approach
6. **API Architecture**: RESTful design with proper error handling

### Business Value
1. **User Experience**: Intuitive travel planning interface
2. **Data Integration**: Real events and hotel data
3. **Scalability**: Built for growth and expansion
4. **Performance**: Fast, responsive application
5. **Extensibility**: Easy to add new features

### Innovation Points
1. **Mixed Itineraries**: Events and hotels in same plan
2. **Real-time Search**: Live event and hotel data
3. **Advanced Filtering**: Multi-criteria search
4. **Booking Integration**: Direct links to booking sites
5. **User Personalization**: Customized recommendations

## 🏆 Project Status

**✅ COMPLETE AND READY FOR PRESENTATION**

- **Backend**: Fully functional with all APIs
- **Frontend**: Complete UI with all features
- **Database**: Populated with real data
- **Authentication**: Working user management
- **Hotel Integration**: Real Toronto hotel data
- **Travel Planning**: Complete itinerary management
- **Testing**: Validated functionality

**Ready to demonstrate all features live!** 🚀