# 🚀 VoyagerAI - Event Discovery Platform

A full-stack web application for discovering and managing events from BookMyShow, built with Flask (Python) backend and Next.js (React) frontend, using SQLite by default for data storage (PostgreSQL optional).

## 🏗️ Architecture

- **Backend**: Flask with SQLAlchemy ORM
- **Frontend**: Next.js with TypeScript and Tailwind CSS
- **Database**: PostgreSQL
- **Web Scraping**: Playwright for BookMyShow events
- **API**: RESTful API with CORS support

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+
- SQLite (default) or PostgreSQL
- Git

### 1. Database Setup

SQLite is enabled by default; no installation is required.

### 2. Start Everything (Recommended)

```bash
# This will start both backend and frontend
./start_all.sh
```

### 3. Manual Setup (Alternative)

#### Backend Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Initialize database (creates voyagerai.db)
python init_db.py

# Start backend server
python wsgi.py
```

#### Frontend Setup
```bash
# Navigate to frontend (in a new terminal)
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 🌐 Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Documentation**: http://localhost:5000/api/

## 📊 Features

### Backend Features
- **Event Scraping**: Automated scraping of BookMyShow events
- **Database Storage**: PostgreSQL integration with SQLAlchemy
- **RESTful API**: Complete CRUD operations for events
- **CORS Support**: Cross-origin requests from frontend
- **Error Handling**: Comprehensive error handling and logging

### Frontend Features
- **Modern UI**: Clean, responsive design with Tailwind CSS
- **Event Management**: View, filter, and manage events
- **Real-time Scraping**: Trigger event scraping from the UI
- **Event Details**: Comprehensive event information display
- **External Links**: Direct links to BookMyShow event pages

## 🔧 API Endpoints

### Events
- `GET /api/events` - Get all events (with optional city filter)
- `GET /api/events/{id}` - Get specific event
- `DELETE /api/events/{id}` - Delete event
- `POST /api/scrape` - Scrape new events

### Scraping
- `POST /api/scrape` - Trigger event scraping
  ```json
  {
    "city": "Mumbai",
    "limit": 10
  }
  ```

## 🗄️ Database Schema

### Events Table
```sql
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    date DATE,
    time TIME,
    venue VARCHAR(200),
    place VARCHAR(200),
    price VARCHAR(100),
    url VARCHAR(1000),
    city VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🛠️ Development

### Backend Development
```bash
cd backend
source venv/bin/activate

# Run server
python wsgi.py

# Or via CLI
python cli.py runserver

# Init DB
python init_db.py
# Or
python cli.py init-db

# Scrape via CLI (saves to DB)
python cli.py scrape --city Mumbai --limit 10
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Database Management
```bash
# Initialize database
cd backend
python init_db.py

# Reset database (if needed)
rm -f voyagerai.db && python init_db.py
```

## 🚀 Deployment

### Production Backend
```bash
cd backend
source venv/bin/activate
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

### Production Frontend
```bash
cd frontend
npm run build
npm start
```

## 📁 Project Structure

```
VoyagerAI/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── routes.py
│   │   └── services/
│   │       └── scraper.py
│   ├── scripts/
│   │   ├── README.md
│   │   └── events_standalone.py
│   ├── cli.py
│   ├── init_db.py
│   ├── wsgi.py
│   ├── requirements.txt
│   └── config.py
├── frontend/
│   ├── src/
│   │   └── app/
│   │       ├── page.tsx
│   │       ├── layout.tsx
│   │       └── globals.css
│   ├── package.json
│   └── next.config.ts
├── setup_database.sh
├── start_backend.sh
├── start_frontend.sh
├── start_all.sh
└── README.md
```

## 🔍 Troubleshooting

### Common Issues

1. **Switching to PostgreSQL (optional)**
   ```bash
   # Install Postgres (macOS)
   brew install postgresql

   # Set DATABASE_URL in backend/.env and restart backend
   ```

2. **Playwright Browser Issues**
   ```bash
   cd backend
   playwright install chromium
   ```

3. **Port Already in Use**
   ```bash
   # Kill processes on ports 3000 and 5000
   lsof -ti:3000 | xargs kill -9
   lsof -ti:5000 | xargs kill -9
   ```

4. **Database Permission Issues**
   ```bash
   # Create database manually
   createdb voyagerai
   ```

## 📝 Environment Variables

Create a `.env` file in the backend directory (optional, only needed to override defaults):

```env
DATABASE_URL=sqlite:///voyagerai.db
FLASK_ENV=development
FLASK_DEBUG=True
SCRAPING_TIMEOUT=60
MAX_EVENTS_PER_CITY=100
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Check the console logs for errors
4. Ensure all dependencies are installed correctly