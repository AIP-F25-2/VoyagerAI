# VoyagerAI - Event Discovery App

This is a web app I built to find events from different sources like BookMyShow. It has a Python backend and React frontend.

## What I used

- Backend: Flask (Python)
- Frontend: Next.js with React
- Database: SQLite (works out of the box)
- Web scraping: Playwright to get events from websites

## How to run it

You need:
- Python 3.8 or newer
- Node.js 18 or newer
- Git

The easiest way is to just run:
```bash
./start_all.sh
```

This starts both the backend and frontend for you.

If you want to do it manually:

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python init_db.py
python wsgi.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Where to find it

- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

## What it does

### Backend
- Scrapes events from BookMyShow and other sites
- Stores events in a database
- Has an API to get events
- Handles errors properly

### Frontend
- Shows events in a nice UI
- You can search and filter events
- Click to scrape new events
- Links to buy tickets

## API stuff

- `GET /api/events` - Get all events
- `GET /api/events/{id}` - Get one event
- `DELETE /api/events/{id}` - Delete an event
- `POST /api/scrape` - Scrape new events

To scrape events, send a POST request like:
```json
{
  "city": "Mumbai",
  "limit": 10
}
```

## Database

The events table looks like this:
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

## Development

### Backend
```bash
cd backend
source venv/bin/activate
python wsgi.py
```

### Frontend
```bash
cd frontend
npm run dev
```

### Reset database if needed
```bash
cd backend
rm -f voyagerai.db && python init_db.py
```

## Project structure

```
VoyagerAI/
├── backend/          # Python Flask backend
├── frontend/         # React Next.js frontend
├── start_all.sh      # Script to start everything
└── README.md
```

## If something goes wrong

1. **Playwright issues**
   ```bash
   cd backend
   playwright install chromium
   ```

2. **Port already in use**
   ```bash
   lsof -ti:3000 | xargs kill -9
   lsof -ti:5000 | xargs kill -9
   ```

3. **Database issues**
   ```bash
   cd backend
   rm -f voyagerai.db && python init_db.py
   ```

That's it! The app should work with the default settings.