# VoyagerAI Enhanced Scraping System

This document describes the comprehensive event scraping system integrated into VoyagerAI backend.

## 🎯 Overview

The enhanced scraping system supports multiple event sources:
- **BookMyShow** - Indian events and activities
- **Eventbrite** - Global events and conferences  
- **EuropaTicket** - European events and concerts

## 🚀 Features

### Multi-Source Scraping
- Scrape from all sources simultaneously
- Individual source scraping
- Configurable limits per source
- Automatic data normalization

### Data Sources
1. **BookMyShow** (`bookmyshow.com`)
   - Indian events, concerts, activities
   - Uses Playwright for dynamic content
   - Supports multiple cities

2. **Eventbrite** (`eventbrite.com`)
   - Global events and conferences
   - 6-month range scraping
   - US-focused events

3. **EuropaTicket** (`europaticket.com`)
   - European events and concerts
   - Multi-month scraping
   - Comprehensive event details

## 📡 API Endpoints

### Scraping Endpoints

#### `/scrape` (POST)
Scrape BookMyShow events only
```json
{
  "city": "Mumbai",
  "limit": 10
}
```

#### `/scrape/all` (POST)
Scrape from all sources
```json
{
  "city": "Mumbai",
  "bms_limit": 10,
  "eventbrite_limit": 50,
  "europaticket_limit": 50
}
```

#### `/scrape/eventbrite` (POST)
Scrape Eventbrite events only
```json
{
  "months_ahead": 6,
  "limit": 50
}
```

#### `/scrape/europaticket` (POST)
Scrape EuropaTicket events only
```json
{
  "limit": 50
}
```

### Data Retrieval Endpoints

#### `/events` (GET)
Get events from database
- `city` - Filter by city
- `limit` - Number of events to return

#### `/events/fetch` (GET)
Fetch from external APIs (Ticketmaster & Eventbrite)
- `q` - Search query
- `city` - City filter
- `size` - Number of results

## 🛠️ Installation & Setup

### Dependencies
```bash
pip install -r requirements.txt
```

### Required Packages
- `playwright` - Web scraping
- `beautifulsoup4` - HTML parsing
- `pandas` - Data processing
- `requests` - HTTP requests
- `python-dateutil` - Date handling

### Playwright Setup
```bash
playwright install chromium
```

## 🔧 Usage Examples

### Python API Usage

```python
from app.services.scraper import scrape_all_events

# Scrape from all sources
events = scrape_all_events(
    city="Mumbai",
    bms_limit=10,
    eventbrite_limit=50,
    europaticket_limit=50
)

print(f"Found {len(events)} events")
```

### Individual Source Scraping

```python
from app.services.scraper import (
    scrape_bookmyshow_events,
    scrape_eventbrite_events,
    scrape_europaticket_events
)

# BookMyShow
bms_events = scrape_bookmyshow_events("Mumbai", limit=10)

# Eventbrite
eventbrite_events = scrape_eventbrite_events(months_ahead=6, limit=50)

# EuropaTicket
europaticket_events = scrape_europaticket_events(limit=50)
```

## 📊 Data Structure

### Event Object
```json
{
  "title": "Event Title",
  "date": "2024-01-15",
  "time": "19:00",
  "venue": "Venue Name",
  "place": "City, Country",
  "price": "₹500-₹2000",
  "url": "https://example.com/event",
  "city": "Mumbai",
  "source": "bookmyshow"
}
```

## 🧪 Testing

Run the test script to verify functionality:
```bash
cd backend
source venv/bin/activate
python test_scraping.py
```

## ⚙️ Configuration

### Environment Variables
- `DATABASE_URL` - Database connection string
- `MONGODB_URI` - MongoDB connection (optional)

### Scraping Limits
- BookMyShow: Default 10 events
- Eventbrite: Default 50 events, 6 months
- EuropaTicket: Default 50 events

## 🚨 Error Handling

The system includes comprehensive error handling:
- Network timeouts and retries
- Rate limiting compliance
- Graceful degradation on source failures
- Detailed error logging

## 🔒 Rate Limiting

Each scraper implements respectful rate limiting:
- BookMyShow: 0.25-0.6s delays
- Eventbrite: 2s delays
- EuropaTicket: 1s delays

## 📈 Performance

### Optimization Features
- Parallel processing where possible
- Efficient data structures
- Memory-conscious scraping
- Database deduplication

### Monitoring
- Progress logging
- Source-specific counters
- Error tracking
- Performance metrics

## 🛡️ Best Practices

1. **Respectful Scraping**
   - Implement delays between requests
   - Use appropriate user agents
   - Follow robots.txt guidelines

2. **Data Quality**
   - Validate scraped data
   - Handle missing fields gracefully
   - Normalize data formats

3. **Error Recovery**
   - Retry failed requests
   - Skip problematic events
   - Continue processing on errors

## 🔄 Maintenance

### Regular Updates
- Monitor site structure changes
- Update selectors as needed
- Test scraping functionality
- Update dependencies

### Monitoring
- Check scraping success rates
- Monitor data quality
- Track performance metrics
- Review error logs

## 📝 Notes

- The system is designed to be extensible for additional sources
- All scrapers include comprehensive error handling
- Data is automatically normalized for database storage
- The system supports both individual and batch scraping operations

## 🤝 Contributing

When adding new scrapers:
1. Follow the existing pattern in `scraper.py`
2. Add appropriate error handling
3. Include rate limiting
4. Update this documentation
5. Add tests for new functionality
