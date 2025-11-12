"""
Elasticsearch service for event search and filtering.
Provides fast, scalable search capabilities for events.
"""
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ElasticsearchService:
    """Service for managing Elasticsearch operations for events."""
    
    def __init__(self):
        """Initialize Elasticsearch client."""
        self.es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self.index_name = os.getenv("ELASTICSEARCH_INDEX", "voyagerai_events")
        
        # Initialize client
        # For Elasticsearch 8.x/9.x, pass URL directly or use connection parameters
        try:
            # Try direct URL first (works for Elasticsearch 8.x/9.x)
            es_username = os.getenv("ELASTICSEARCH_USERNAME")
            es_password = os.getenv("ELASTICSEARCH_PASSWORD")
            
            if es_username and es_password:
                # With authentication
                from urllib.parse import urlparse
                parsed = urlparse(self.es_url)
                self.client = Elasticsearch(
                    hosts=[f"{parsed.scheme}://{parsed.netloc}"],
                    basic_auth=(es_username, es_password),
                    verify_certs=False,
                    ssl_show_warn=False
                )
            else:
                # Without authentication - pass URL directly
                self.client = Elasticsearch(
                    [self.es_url],
                    verify_certs=False,
                    ssl_show_warn=False
                )
            
            # Test connection with a timeout
            if not self.client.ping(request_timeout=5):
                raise ConnectionError("Cannot connect to Elasticsearch")
            print(f"✅ Connected to Elasticsearch at {self.es_url}")
        except Exception as e:
            print(f"⚠️  Elasticsearch connection failed: {e}")
            print("   Events will still work, but search may be slower")
            import traceback
            traceback.print_exc()
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Elasticsearch is available."""
        if not self.client:
            return False
        try:
            return self.client.ping()
        except (ConnectionError, TimeoutError, AttributeError):
            return False
    
    def create_index(self) -> bool:
        """Create the events index with proper mappings."""
        if not self.is_available():
            return False
        
        # Define index mapping
        mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "description": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "url": {"type": "keyword"},
                    "source": {"type": "keyword"},  # ticketmaster, eventbrite, csv
                    "date": {
                        "type": "date",
                        "format": "yyyy-MM-dd"
                    },
                    "time": {"type": "keyword"},
                    "city": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "venue": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "category": {
                        "type": "keyword"
                    },
                    "price_min": {"type": "float"},
                    "price_max": {"type": "float"},
                    "image_url": {"type": "keyword"},
                    "created_at": {"type": "date"}
                }
            }
        }
        
        try:
            # Check if index exists
            if self.client.indices.exists(index=self.index_name):
                print(f"📋 Index '{self.index_name}' already exists")
                return True
            
            # Create index (use mappings parameter for newer Elasticsearch versions)
            try:
                self.client.indices.create(index=self.index_name, mappings=mapping["mappings"])
            except TypeError:
                # Fallback for older versions
                self.client.indices.create(index=self.index_name, body=mapping)
            print(f"✅ Created Elasticsearch index '{self.index_name}'")
            return True
        except Exception as e:
            print(f"❌ Failed to create index: {e}")
            return False
    
    def _extract_event_date(self, event: Dict[str, Any]) -> Optional[str]:
        """Extract and format event date."""
        if not event.get("dates") or not event["dates"].get("start"):
            return None
        date_str = event["dates"]["start"].get("localDate")
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date().isoformat()
        except (ValueError, TypeError):
            return None

    def _extract_price_range(self, event: Dict[str, Any]) -> tuple:
        """Extract price min and max from event."""
        price_min = None
        price_max = None
        if event.get("priceRanges") and isinstance(event["priceRanges"], list) and len(event["priceRanges"]) > 0:
            pr = event["priceRanges"][0]
            if isinstance(pr, dict):
                price_min = pr.get("min")
                price_max = pr.get("max")
        return price_min, price_max

    def _extract_venue_info(self, event: Dict[str, Any]) -> tuple:
        """Extract venue and city from event."""
        city = None
        venue = None
        if event.get("_embedded") and event["_embedded"].get("venues"):
            venues = event["_embedded"]["venues"]
            if venues and len(venues) > 0:
                city = venues[0].get("city", {}).get("name")
                venue = venues[0].get("name")
        return venue, city

    def _extract_image_url(self, event: Dict[str, Any]) -> Optional[str]:
        """Extract image URL from event."""
        if event.get("images") and isinstance(event["images"], list) and len(event["images"]) > 0:
            return event["images"][0].get("url")
        return None

    def _build_event_document(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Build Elasticsearch document from event data."""
        event_date = self._extract_event_date(event)
        price_min, price_max = self._extract_price_range(event)
        venue, city = self._extract_venue_info(event)
        image_url = self._extract_image_url(event)
        
        return {
            "id": event.get("id"),
            "name": event.get("name", ""),
            "description": event.get("description", ""),
            "url": event.get("url"),
            "source": event.get("source", "unknown"),
            "date": event_date,
            "time": event.get("dates", {}).get("start", {}).get("localTime") if event.get("dates") else None,
            "city": city,
            "venue": venue,
            "category": event.get("category", {}).get("name") if isinstance(event.get("category"), dict) else None,
            "price_min": price_min,
            "price_max": price_max,
            "image_url": image_url,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    def index_event(self, event: Dict[str, Any]) -> bool:
        """Index a single event."""
        if not self.is_available():
            return False
        
        try:
            doc = self._build_event_document(event)
            self.client.index(
                index=self.index_name,
                id=event.get("id"),
                document=doc
            )
            return True
        except Exception as e:
            print(f"❌ Failed to index event {event.get('id')}: {e}")
            return False
    
    def bulk_index_events(self, events: List[Dict[str, Any]]) -> int:
        """Bulk index multiple events."""
        if not self.is_available():
            return 0
        
        indexed = 0
        for event in events:
            if self.index_event(event):
                indexed += 1
        return indexed
    
    def _build_text_search_clause(self, query: str) -> Dict[str, Any]:
        """Build text search clause for Elasticsearch query."""
        return {
            "multi_match": {
                "query": query,
                "fields": ["name^3", "description^2", "venue", "city"],
                "type": "best_fields",
                "fuzziness": "AUTO"
            }
        }

    def _build_city_filter(self, city: str) -> Dict[str, Any]:
        """Build city filter clause for Elasticsearch query."""
        return {
            "bool": {
                "should": [
                    {"match": {"city.keyword": city}},
                    {"match": {"city": city}},
                    {"wildcard": {"city": f"*{city.lower()}*"}}
                ],
                "minimum_should_match": 1
            }
        }

    def _build_date_range_filter(self, date_from: Optional[str], date_to: Optional[str]) -> Dict[str, Any]:
        """Build date range filter clause."""
        date_range = {}
        if date_from:
            date_range["gte"] = date_from
        if date_to:
            date_range["lte"] = date_to
        return {"range": {"date": date_range}}

    def _build_price_range_filter(self, price_min: Optional[float], price_max: Optional[float]) -> Dict[str, Any]:
        """Build price range filter clause."""
        price_range = {}
        if price_min is not None:
            price_range["gte"] = price_min
        if price_max is not None:
            price_range["lte"] = price_max
        return {
            "bool": {
                "should": [
                    {"range": {"price_min": price_range}},
                    {"range": {"price_max": price_range}}
                ],
                "minimum_should_match": 1
            }
        }

    def _build_es_query(self, must_clauses: List[Dict], filter_clauses: List[Dict]) -> Dict[str, Any]:
        """Build final Elasticsearch query."""
        if not must_clauses and not filter_clauses:
            return {"match_all": {}}
        
        es_query = {"bool": {}}
        if must_clauses:
            es_query["bool"]["must"] = must_clauses
        if filter_clauses:
            es_query["bool"]["filter"] = filter_clauses
        return es_query

    def _build_sort_clause(self, sort: str) -> List[Dict[str, Any]]:
        """Build sort clause for Elasticsearch query."""
        sort_clause = []
        if sort == "date_asc":
            sort_clause.append({"date": {"order": "asc"}})
        elif sort == "date_desc":
            sort_clause.append({"date": {"order": "desc"}})
        elif sort == "price_asc":
            sort_clause.append({"price_min": {"order": "asc", "missing": "_last"}})
        elif sort == "price_desc":
            sort_clause.append({"price_max": {"order": "desc", "missing": "_last"}})
        else:
            sort_clause.append({"date": {"order": "asc"}})
        return sort_clause

    def search_events(
        self,
        query: Optional[str] = None,
        city: Optional[str] = None,
        category: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        source: Optional[str] = None,
        sort: str = "date_asc",
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Search events using Elasticsearch.
        
        Returns:
            {
                "events": [...],
                "total": count,
                "page": page,
                "page_size": page_size
            }
        """
        if not self.is_available():
            return {"events": [], "total": 0, "page": page, "page_size": page_size}
        
        try:
            # Build query clauses
            must_clauses = []
            filter_clauses = []
            
            if query:
                must_clauses.append(self._build_text_search_clause(query))
            
            if city:
                filter_clauses.append(self._build_city_filter(city))
            
            if category:
                filter_clauses.append({"term": {"category": category.lower()}})
            
            if date_from or date_to:
                filter_clauses.append(self._build_date_range_filter(date_from, date_to))
            
            if price_min is not None or price_max is not None:
                filter_clauses.append(self._build_price_range_filter(price_min, price_max))
            
            if source:
                filter_clauses.append({"term": {"source": source.lower()}})
            
            # Build final query and sort
            es_query = self._build_es_query(must_clauses, filter_clauses)
            sort_clause = self._build_sort_clause(sort)
            
            # Execute search
            from_index = (page - 1) * page_size
            response = self.client.search(
                index=self.index_name,
                query=es_query,
                sort=sort_clause,
                from_=from_index,
                size=page_size
            )
            
            # Extract results
            total = response["hits"]["total"]["value"]
            events = []
            
            for hit in response["hits"]["hits"]:
                source_data = hit["_source"]
                # Get source from Elasticsearch document, default to "unknown" if not set
                event_source = source_data.get("source", "unknown")
                
                # Convert back to frontend format
                event = {
                    "id": source_data.get("id"),
                    "name": source_data.get("name"),
                    "url": source_data.get("url"),
                    "dates": {
                        "start": {
                            "localDate": source_data.get("date"),
                            "localTime": source_data.get("time")
                        }
                    },
                    "images": [{"url": source_data.get("image_url")}] if source_data.get("image_url") else [],
                    "_embedded": {
                        "venues": [{
                            "name": source_data.get("venue", "TBA"),
                            "city": {"name": source_data.get("city", "Unknown")}
                        }]
                    },
                    "priceRanges": [{
                        "min": source_data.get("price_min"),
                        "max": source_data.get("price_max")
                    }] if source_data.get("price_min") or source_data.get("price_max") else None,
                    "description": source_data.get("description"),
                    "source": event_source  # Ensure source is always set
                }
                events.append(event)
            
            return {
                "events": events,
                "total": total,
                "page": page,
                "page_size": page_size
            }
        except Exception as e:
            print(f"❌ Elasticsearch search error: {e}")
            import traceback
            traceback.print_exc()
            return {"events": [], "total": 0, "page": page, "page_size": page_size}
    
    def delete_event(self, event_id: str) -> bool:
        """Delete an event from the index."""
        if not self.is_available():
            return False
        
        try:
            self.client.delete(index=self.index_name, id=event_id)
            return True
        except NotFoundError:
            return True  # Already deleted
        except Exception as e:
            print(f"❌ Failed to delete event {event_id}: {e}")
            return False
    
    def delete_index(self) -> bool:
        """Delete the entire index (use with caution!)."""
        if not self.is_available():
            return False
        
        try:
            self.client.indices.delete(index=self.index_name)
            print(f"✅ Deleted index '{self.index_name}'")
            return True
        except Exception as e:
            print(f"❌ Failed to delete index: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the index."""
        if not self.is_available():
            return {"available": False}
        
        try:
            stats = self.client.count(index=self.index_name)
            return {
                "available": True,
                "total_events": stats["count"],
                "index_name": self.index_name
            }
        except Exception as e:
            return {"available": False, "error": str(e)}


# Global instance
es_service = ElasticsearchService()

