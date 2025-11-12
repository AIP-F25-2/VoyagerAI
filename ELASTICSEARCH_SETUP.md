# Elasticsearch Setup Guide

This guide explains how to set up and use Elasticsearch for advanced event search and filtering in VoyagerAI.

## Prerequisites

- Docker (recommended) or a local Elasticsearch installation
- Python 3.8+

## Quick Start with Docker

1. **Start Elasticsearch using Docker:**
   ```bash
   docker run -d \
     --name elasticsearch \
     -p 9200:9200 \
     -p 9300:9300 \
     -e "discovery.type=single-node" \
     -e "xpack.security.enabled=false" \
     elasticsearch:8.11.0
   ```

2. **Verify Elasticsearch is running:**
   ```bash
   curl http://localhost:9200
   ```
   You should see a JSON response with cluster information.

3. **Install Python dependencies:**
   ```bash
   cd VoyagerAI/backend
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Add to your `.env` file:
   ```env
   ELASTICSEARCH_URL=http://localhost:9200
   ELASTICSEARCH_INDEX=voyagerai_events
   ```

5. **Index existing events:**
   ```bash
   # Option 1: Use the script
   python scripts/index_events_to_elasticsearch.py
   
   # Option 2: Use the API endpoint
   curl -X POST http://localhost:5001/api/elasticsearch/index
   ```

## Features

### Automatic Indexing
- Events are automatically indexed when fetched from APIs
- New events are added to the index in real-time

### Advanced Search
- **Full-text search** across event names, descriptions, venues
- **City filtering** with exact and partial matching
- **Date range filtering** with proper date handling
- **Price range filtering** with min/max support
- **Category filtering** for event types
- **Source filtering** (Ticketmaster, Eventbrite, CSV)

### Fallback Behavior
- If Elasticsearch is unavailable, the system automatically falls back to the original filtering method
- No breaking changes - the API works with or without Elasticsearch

## API Endpoints

### Check Elasticsearch Status
```bash
GET /api/elasticsearch/status
```

### Index All Events
```bash
POST /api/elasticsearch/index
```

### Search Events (with Elasticsearch)
The `/api/events` endpoint automatically uses Elasticsearch when:
- Elasticsearch is available
- Filters or query parameters are provided

Example:
```bash
GET /api/events?city=Toronto&date_from=2025-11-01&date_to=2025-11-30
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ELASTICSEARCH_URL` | `http://localhost:9200` | Elasticsearch server URL |
| `ELASTICSEARCH_USERNAME` | (empty) | Username for authentication (optional) |
| `ELASTICSEARCH_PASSWORD` | (empty) | Password for authentication (optional) |
| `ELASTICSEARCH_INDEX` | `voyagerai_events` | Index name for events |

### Production Setup

For production, consider:
- Using Elasticsearch Cloud or managed service
- Enabling security (X-Pack)
- Setting up proper authentication
- Configuring cluster settings for performance

## Troubleshooting

### Elasticsearch not connecting
1. Check if Elasticsearch is running: `curl http://localhost:9200`
2. Verify `ELASTICSEARCH_URL` in `.env`
3. Check backend logs for connection errors

### No search results
1. Ensure events are indexed: `POST /api/elasticsearch/index`
2. Check index stats: `GET /api/elasticsearch/status`
3. Verify filters are correct

### Performance issues
- Increase Elasticsearch heap size: `-e "ES_JAVA_OPTS=-Xms1g -Xmx1g"`
- Consider using multiple nodes for production
- Monitor index size and optimize mappings if needed

## Benefits

✅ **Fast Search**: Sub-millisecond search even with thousands of events  
✅ **Scalable**: Handles millions of events efficiently  
✅ **Flexible**: Complex queries with multiple filters  
✅ **Fuzzy Matching**: Handles typos and partial matches  
✅ **Non-Breaking**: Falls back gracefully if unavailable  

## Next Steps

- Monitor Elasticsearch performance
- Tune index mappings for your use case
- Consider adding more advanced features (geo-search, aggregations, etc.)

