"""
LLM service for VoyagerAI
Provides AI-powered travel recommendations, chat assistance, and personalized suggestions
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..models import db, Favorite, Event, Hotel, Itinerary

# Ensure dotenv is loaded
try:
    from dotenv import load_dotenv
    # Try loading from backend directory first, then root
    import pathlib
    backend_dir = pathlib.Path(__file__).parent.parent.parent
    env_path = backend_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Try root directory
        root_dir = backend_dir.parent
        env_path = root_dir / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            # Fallback to default dotenv behavior
            load_dotenv()
except ImportError:
    pass  # dotenv not available, rely on system env vars

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not installed. LLM features will be limited.")


class LLMService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        self.client = None
        
        # Log initialization status
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI library not installed. Install with: pip install openai")
        elif not self.api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables. LLM features will be disabled.")
        else:
            logger.info(f"OpenAI API key found (length: {len(self.api_key)}), model: {self.model}")
        
        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                # Test the connection with a simple validation
                logger.info("LLM Service initialized successfully with OpenAI")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            if OPENAI_AVAILABLE:
                logger.warning("LLM Service initialized without OpenAI client (API key missing)")
            else:
                logger.warning("LLM Service initialized without OpenAI (library not installed)")
    
    def is_available(self) -> bool:
        """Check if LLM service is available"""
        return self.client is not None
    
    def get_user_context(self, user_email: str) -> Dict[str, Any]:
        """Get user context for personalized recommendations"""
        context = {
            "favorites": [],
            "recent_events": [],
            "preferences": {}
        }
        
        try:
            # Get user's favorites
            favorites = Favorite.query.filter_by(user_email=user_email).limit(10).all()
            context["favorites"] = [
                {
                    "title": fav.title,
                    "city": fav.city,
                    "venue": fav.venue,
                    "date": fav.date.isoformat() if fav.date else None,
                    "provider": fav.provider
                }
                for fav in favorites
            ]
            
            # Get recent events
            recent_events = Event.query.order_by(Event.date.desc()).limit(5).all()
            context["recent_events"] = [
                {
                    "title": event.title,
                    "city": event.city,
                    "venue": event.venue,
                    "date": event.date.isoformat() if event.date else None
                }
                for event in recent_events
            ]
            
            # Infer preferences from favorites
            cities = [f["city"] for f in context["favorites"] if f["city"]]
            venues = [f["venue"] for f in context["favorites"] if f["venue"]]
            
            context["preferences"] = {
                "preferred_cities": list(set(cities)),
                "preferred_venues": list(set(venues))
            }
            
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
        
        return context
    
    def get_enhanced_recommendations(
        self, 
        user_email: str, 
        events: List[Dict[str, Any]], 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get AI-enhanced recommendations with explanations"""
        if not self.is_available():
            return events[:limit]
        
        try:
            user_context = self.get_user_context(user_email)
            
            # Prepare events summary
            events_summary = []
            for event in events[:20]:  # Limit to top 20 for context
                events_summary.append({
                    "title": event.get("title", event.get("name", "")),
                    "city": event.get("city", ""),
                    "venue": event.get("venue", ""),
                    "date": event.get("date", event.get("dates", {}).get("start", {}).get("localDate", "")),
                    "description": event.get("description", "")[:200]  # Truncate
                })
            
            prompt = f"""You are a travel and event recommendation assistant for VoyagerAI.

User's saved favorites:
{json.dumps(user_context["favorites"], indent=2)}

Available events:
{json.dumps(events_summary, indent=2)}

Based on the user's preferences and saved events, recommend the top {limit} events that would be most interesting to them.
For each recommendation, provide:
1. Why this event matches their interests
2. What makes it special
3. A brief, engaging description

Return a JSON array with this structure:
[
  {{
    "index": 0,
    "title": "Event Title",
    "reason": "Why this matches their interests",
    "highlight": "What makes it special",
    "description": "Brief engaging description"
  }}
]

Only return the JSON array, no other text."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful travel and event recommendation assistant. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            recommendations = json.loads(content)
            
            # Merge AI insights with original event data
            enhanced_events = []
            for rec in recommendations:
                idx = rec.get("index", 0)
                if idx < len(events):
                    event = events[idx].copy()
                    event["ai_reason"] = rec.get("reason", "")
                    event["ai_highlight"] = rec.get("highlight", "")
                    event["ai_description"] = rec.get("description", "")
                    enhanced_events.append(event)
            
            return enhanced_events[:limit]
            
        except Exception as e:
            logger.error(f"Error getting enhanced recommendations: {e}")
            return events[:limit]
    
    def _extract_city_from_message(self, message: str) -> Optional[str]:
        """Extract city name from message if mentioned."""
        message_lower = message.lower()
        common_cities = [
            "toronto", "berlin", "vienna", "budapest", "barcelona", "madrid",
            "rome", "paris", "london", "amsterdam", "mumbai", "delhi", "bangalore"
        ]
        for city in common_cities:
            if city in message_lower:
                return city
        return None

    def _is_event_query(self, message: str) -> bool:
        """Check if message is asking about events."""
        message_lower = message.lower()
        event_keywords = [
            "event", "concert", "show", "weekend", "this week", "tonight",
            "today", "tomorrow", "sports", "theater", "festival", "music"
        ]
        return any(keyword in message_lower for keyword in event_keywords)

    def _determine_date_range(self, message: str) -> tuple:
        """Determine date range from message query."""
        from datetime import datetime, timedelta
        today = datetime.now().date()
        message_lower = message.lower()
        
        if "weekend" in message_lower or "this weekend" in message_lower:
            days_until_saturday = (5 - today.weekday()) % 7
            if days_until_saturday == 0 and today.weekday() < 5:
                days_until_saturday = 7
            saturday = today + timedelta(days=days_until_saturday)
            sunday = saturday + timedelta(days=1)
            return saturday, sunday
        elif "this week" in message_lower:
            return today, today + timedelta(days=7)
        elif "tonight" in message_lower or "today" in message_lower:
            return today, today
        elif "tomorrow" in message_lower:
            tomorrow = today + timedelta(days=1)
            return tomorrow, tomorrow
        else:
            return today, today + timedelta(days=30)

    def _fetch_events_for_chat(self, date_from, date_to, city_mentioned: Optional[str]) -> List[Dict]:
        """Fetch events from database for chat query."""
        try:
            from app.models import Event
            db_query = Event.query.filter(Event.date >= date_from)
            if date_to:
                db_query = db_query.filter(Event.date <= date_to)
            if city_mentioned:
                db_query = db_query.filter(Event.city.ilike(f"%{city_mentioned}%"))
            
            events = db_query.order_by(Event.date).limit(20).all()
            
            events_data = []
            for event in events:
                events_data.append({
                    "title": event.title,
                    "date": event.date.isoformat() if event.date else None,
                    "time": event.time.strftime("%H:%M") if event.time else None,
                    "venue": event.venue or "TBA",
                    "city": event.city or "Unknown",
                    "url": event.url
                })
            
            logger.info(f"Found {len(events_data)} events for chat query")
            return events_data
        except Exception as e:
            logger.error(f"Error fetching events for chat: {e}")
            return []

    def _build_chat_messages(self, system_prompt: str, user_context: Optional[Dict],
                            events_data: List[Dict], conversation_history: Optional[List[Dict]],
                            message: str) -> List[Dict]:
        """Build messages list for LLM chat."""
        messages = [{"role": "system", "content": system_prompt}]
        
        if user_context and user_context.get("favorites"):
            context_msg = f"User's saved favorites: {json.dumps(user_context['favorites'][:5], indent=2)}"
            messages.append({"role": "system", "content": context_msg})
        
        if events_data:
            events_context = f"""Here are real events from our database that match the user's query:

{json.dumps(events_data[:15], indent=2)}

Use this information to give specific, helpful recommendations. Mention event names, dates, venues, and cities when relevant."""
            messages.append({"role": "system", "content": events_context})
        
        if conversation_history:
            for msg in conversation_history[-10:]:
                messages.append(msg)
        
        messages.append({"role": "user", "content": message})
        return messages

    def chat(
        self, 
        message: str, 
        user_email: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Chat with the AI assistant about travel and events"""
        if not self.is_available():
            return {
                "success": False,
                "error": "LLM service is not available. Please configure OPENAI_API_KEY."
            }
        
        try:
            # Get user context if available
            user_context = None
            if user_email:
                user_context = self.get_user_context(user_email)
            
            # Detect if user is asking about events and fetch real data
            events_data = []
            city_mentioned = self._extract_city_from_message(message)
            
            if self._is_event_query(message):
                date_from, date_to = self._determine_date_range(message)
                events_data = self._fetch_events_for_chat(date_from, date_to, city_mentioned)
            
            # Build system prompt
            system_prompt = """You are VoyagerAI, a helpful travel and event planning assistant. 
You help users discover events, plan trips, find hotels, and create itineraries.

You can:
- Recommend events based on user preferences
- Suggest hotels and accommodations
- Help plan travel itineraries
- Answer questions about events, venues, and cities
- Provide travel tips and suggestions

Be friendly, concise, and helpful. When you have real event data, use it to give specific recommendations."""

            # Build messages and get response
            messages = self._build_chat_messages(
                system_prompt, user_context, events_data, conversation_history, message
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )
            
            assistant_message = response.choices[0].message.content.strip()
            
            return {
                "success": True,
                "message": assistant_message,
                "model": self.model,
                "events_found": len(events_data) if events_data else 0
            }
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_itinerary_suggestions(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        events: List[Dict[str, Any]],
        hotels: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate AI-powered itinerary suggestions"""
        if not self.is_available():
            return {
                "success": False,
                "error": "LLM service is not available"
            }
        
        try:
            from datetime import datetime, timedelta
            
            # Calculate number of days
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            num_days = (end - start).days + 1
            
            # Group events by date
            events_by_date = {}
            for event in events:
                event_date = event.get("date", "")
                if event_date:
                    if event_date not in events_by_date:
                        events_by_date[event_date] = []
                    events_by_date[event_date].append(event)
            
            # Format events for prompt (limit to most relevant)
            formatted_events = []
            for event in events[:30]:  # Top 30 events
                formatted_events.append({
                    "title": event.get("title", "Unknown"),
                    "date": event.get("date", ""),
                    "time": event.get("time", ""),
                    "venue": event.get("venue", "TBA"),
                    "city": event.get("city", destination)
                })
            
            # Format hotels for prompt
            formatted_hotels = []
            for hotel in hotels[:15]:  # Top 15 hotels
                formatted_hotels.append({
                    "name": hotel.get("name", "Unknown Hotel"),
                    "city": hotel.get("city", destination),
                    "address": hotel.get("address", ""),
                    "rating": hotel.get("rating", ""),
                    "price_per_night": hotel.get("price_per_night", "")
                })
            
            budget_info = ""
            if preferences and preferences.get("budget"):
                budget_info = f"\nBudget: ${preferences['budget']:,.2f}"
            
            # Add user hints/instructions if provided
            hints_section = ""
            if preferences and preferences.get("hints"):
                hints_section = f"\n\nUSER PREFERENCES AND HINTS:\n{preferences['hints']}\n\nPlease incorporate these preferences into the itinerary."
            
            description_section = ""
            if preferences and preferences.get("description"):
                description_section = f"\n\nTrip Description: {preferences['description']}"
            
            prompt = f"""You are an expert travel planner. Create a detailed {num_days}-day itinerary for {destination} from {start_date} to {end_date}.{budget_info}{description_section}{hints_section}

Available Events ({len(formatted_events)} events):
{json.dumps(formatted_events, indent=2)}

Available Hotels ({len(formatted_hotels)} hotels):
{json.dumps(formatted_hotels, indent=2)}

Create a day-by-day itinerary with:
1. Specific events from the list above (use actual event titles and dates)
2. Hotel recommendations from the list above
3. Practical tips for each day
4. A balanced mix of activities and rest time

IMPORTANT:
- Use REAL event titles and dates from the events list
- Use REAL hotel names from the hotels list
- Match events to their actual dates
- Distribute events across all days
- Include 1-2 events per day maximum
- Suggest 1 hotel for the entire stay (or different hotels if multi-city)

Return ONLY valid JSON in this exact format:
{{
  "itinerary": [
    {{
      "day": 1,
      "date": "{start_date}",
      "events": ["Exact Event Title from list"],
      "hotel": "Exact Hotel Name from list",
      "tips": "Practical tips for this day"
    }}
  ],
  "summary": "Brief 2-3 sentence trip overview",
  "tips": ["General tip 1", "General tip 2", "General tip 3"]
}}

Return ONLY the JSON object, no markdown, no code blocks, no explanations."""

            # Try with response_format (for newer OpenAI API versions)
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a travel planning expert. You MUST respond with valid JSON only. No markdown, no code blocks, just pure JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                    response_format={"type": "json_object"}
                )
            except TypeError:
                # Fallback for older API versions that don't support response_format
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a travel planning expert. You MUST respond with valid JSON only. No markdown, no code blocks, just pure JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up response
            if content.startswith("```"):
                parts = content.split("```")
                if len(parts) > 1:
                    content = parts[1]
                    if content.startswith("json"):
                        content = content[4:]
                content = content.strip()
            
            # Remove any leading/trailing whitespace or newlines
            content = content.strip()
            
            itinerary = json.loads(content)
            
            # Validate and enhance itinerary
            if "itinerary" not in itinerary:
                raise ValueError("Invalid response: missing 'itinerary' field")
            
            # Ensure dates are correct
            current_date = start
            for day_plan in itinerary.get("itinerary", []):
                if "date" not in day_plan or not day_plan["date"]:
                    day_plan["date"] = current_date.isoformat()
                current_date += timedelta(days=1)
            
            return {
                "success": True,
                "itinerary": itinerary
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in itinerary generation: {e}")
            logger.error(f"Response content: {content[:500] if 'content' in locals() else 'N/A'}")
            return {
                "success": False,
                "error": f"Failed to parse AI response as JSON: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error generating itinerary: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }


# Global LLM service instance
llm_service = LLMService()

