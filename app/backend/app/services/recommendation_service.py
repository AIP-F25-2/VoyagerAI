"""
Recommendation service for VoyagerAI
Provides personalized event recommendations based on user behavior
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from ..models import db, Favorite, EventReview, Event
import logging

logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(self):
        self.min_events_for_recommendation = 3
        
    def get_personalized_recommendations(self, user_email: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get personalized event recommendations for a user"""
        try:
            # Get user's favorites to understand preferences
            user_favorites = Favorite.query.filter_by(user_email=user_email).all()
            
            if len(user_favorites) < self.min_events_for_recommendation:
                # Not enough data for personalization, return popular events
                return self._get_popular_events(limit)
            
            # Analyze user preferences
            preferences = self._analyze_user_preferences(user_favorites)
            
            # Get recommendations based on preferences
            recommendations = self._get_recommendations_by_preferences(preferences, limit)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations for {user_email}: {e}")
            return self._get_popular_events(limit)
    
    def _analyze_user_preferences(self, favorites: List[Favorite]) -> Dict[str, Any]:
        """Analyze user's favorite events to understand preferences"""
        preferences = {
            "preferred_cities": {},
            "preferred_venues": {},
            "preferred_categories": {},
            "preferred_times": {},
            "preferred_days": {}
        }
        
        for fav in favorites:
            # City preferences
            if fav.city:
                preferences["preferred_cities"][fav.city] = preferences["preferred_cities"].get(fav.city, 0) + 1
            
            # Venue preferences
            if fav.venue:
                preferences["preferred_venues"][fav.venue] = preferences["preferred_venues"].get(fav.venue, 0) + 1
            
            # Time preferences (if time is available)
            if fav.time:
                hour = fav.time.hour
                if 6 <= hour < 12:
                    time_slot = "morning"
                elif 12 <= hour < 17:
                    time_slot = "afternoon"
                elif 17 <= hour < 21:
                    time_slot = "evening"
                else:
                    time_slot = "night"
                preferences["preferred_times"][time_slot] = preferences["preferred_times"].get(time_slot, 0) + 1
            
            # Day preferences
            if fav.date:
                day_of_week = fav.date.strftime("%A").lower()
                preferences["preferred_days"][day_of_week] = preferences["preferred_days"].get(day_of_week, 0) + 1
            
            # Category preferences (infer from title keywords)
            category = self._infer_category_from_title(fav.title)
            if category:
                preferences["preferred_categories"][category] = preferences["preferred_categories"].get(category, 0) + 1
        
        return preferences
    
    def _infer_category_from_title(self, title: str) -> str:
        """Infer event category from title using keyword matching"""
        title_lower = title.lower()
        
        category_keywords = {
            "music": ["concert", "music", "band", "singer", "dj", "festival", "live", "acoustic", "jazz", "rock", "pop", "classical"],
            "sports": ["sports", "game", "match", "tournament", "fitness", "gym", "yoga", "running", "football", "basketball", "soccer"],
            "arts": ["art", "gallery", "museum", "exhibition", "painting", "sculpture", "theater", "drama", "play", "show"],
            "food": ["food", "restaurant", "cooking", "wine", "beer", "tasting", "dinner", "lunch", "brunch", "chef"],
            "tech": ["tech", "technology", "coding", "programming", "startup", "innovation", "ai", "machine learning", "data"],
            "business": ["business", "networking", "conference", "seminar", "workshop", "meeting", "entrepreneur", "startup"],
            "education": ["learning", "course", "class", "workshop", "training", "education", "tutorial", "lecture", "study"],
            "health": ["health", "wellness", "medical", "fitness", "yoga", "meditation", "therapy", "mental health"],
            "family": ["family", "kids", "children", "baby", "toddler", "parent", "family-friendly", "playground"],
            "outdoor": ["outdoor", "nature", "hiking", "camping", "park", "garden", "beach", "mountain", "trail"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        
        return None
    
    def _get_recommendations_by_preferences(self, preferences: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Get event recommendations based on user preferences"""
        try:
            # Get upcoming events
            today = datetime.now().date()
            upcoming_events = Event.query.filter(Event.date >= today).order_by(Event.date).limit(limit * 3).all()
            
            # Score events based on preferences
            scored_events = []
            for event in upcoming_events:
                score = self._calculate_event_score(event, preferences)
                if score > 0:
                    scored_events.append((event, score))
            
            # Sort by score and return top events
            scored_events.sort(key=lambda x: x[1], reverse=True)
            recommendations = []
            
            for event, score in scored_events[:limit]:
                event_dict = event.to_dict()
                event_dict["recommendation_score"] = score
                event_dict["recommendation_reason"] = self._get_recommendation_reason(event, preferences)
                recommendations.append(event_dict)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations by preferences: {e}")
            return self._get_popular_events(limit)
    
    def _calculate_event_score(self, event: Event, preferences: Dict[str, Any]) -> float:
        """Calculate recommendation score for an event based on user preferences"""
        score = 0.0
        
        # City preference score
        if event.city and event.city in preferences["preferred_cities"]:
            score += preferences["preferred_cities"][event.city] * 2.0
        
        # Venue preference score
        if event.venue and event.venue in preferences["preferred_venues"]:
            score += preferences["preferred_venues"][event.venue] * 1.5
        
        # Category preference score
        category = self._infer_category_from_title(event.title)
        if category and category in preferences["preferred_categories"]:
            score += preferences["preferred_categories"][category] * 3.0
        
        # Time preference score
        if event.time:
            hour = event.time.hour
            if 6 <= hour < 12:
                time_slot = "morning"
            elif 12 <= hour < 17:
                time_slot = "afternoon"
            elif 17 <= hour < 21:
                time_slot = "evening"
            else:
                time_slot = "night"
            
            if time_slot in preferences["preferred_times"]:
                score += preferences["preferred_times"][time_slot] * 1.0
        
        # Day preference score
        if event.date:
            day_of_week = event.date.strftime("%A").lower()
            if day_of_week in preferences["preferred_days"]:
                score += preferences["preferred_days"][day_of_week] * 1.0
        
        return score
    
    def _get_recommendation_reason(self, event: Event, preferences: Dict[str, Any]) -> str:
        """Get human-readable reason for recommendation"""
        reasons = []
        
        if event.city and event.city in preferences["preferred_cities"]:
            reasons.append(f"in {event.city} (you've saved events here before)")
        
        category = self._infer_category_from_title(event.title)
        if category and category in preferences["preferred_categories"]:
            reasons.append(f"similar to your {category} interests")
        
        if event.venue and event.venue in preferences["preferred_venues"]:
            reasons.append(f"at {event.venue} (a venue you like)")
        
        if reasons:
            return f"Recommended because it's {' and '.join(reasons)}"
        else:
            return "Recommended based on your preferences"
    
    def _get_popular_events(self, limit: int) -> List[Dict[str, Any]]:
        """Get popular events when personalization isn't possible"""
        try:
            # Get events with most favorites
            popular_events = db.session.query(Event, db.func.count(Favorite.id).label('favorite_count'))\
                .outerjoin(Favorite, Event.title == Favorite.title)\
                .group_by(Event.id)\
                .order_by(db.desc('favorite_count'), Event.date)\
                .limit(limit)\
                .all()
            
            recommendations = []
            for event, favorite_count in popular_events:
                event_dict = event.to_dict()
                event_dict["recommendation_score"] = favorite_count
                event_dict["recommendation_reason"] = f"Popular event ({favorite_count} saves)"
                recommendations.append(event_dict)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting popular events: {e}")
            return []
    
    def get_trending_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending events based on recent activity"""
        try:
            # Get events that have been favorited recently
            recent_date = datetime.now() - timedelta(days=7)
            trending_events = db.session.query(Event, db.func.count(Favorite.id).label('recent_favorites'))\
                .outerjoin(Favorite, db.and_(Event.title == Favorite.title, Favorite.created_at >= recent_date))\
                .group_by(Event.id)\
                .order_by(db.desc('recent_favorites'), Event.date)\
                .limit(limit)\
                .all()
            
            trending = []
            for event, recent_favorites in trending_events:
                event_dict = event.to_dict()
                event_dict["trending_score"] = recent_favorites
                event_dict["trending_reason"] = f"Trending ({recent_favorites} recent saves)"
                trending.append(event_dict)
            
            return trending
            
        except Exception as e:
            logger.error(f"Error getting trending events: {e}")
            return []

# Global recommendation service instance
recommendation_service = RecommendationService()
