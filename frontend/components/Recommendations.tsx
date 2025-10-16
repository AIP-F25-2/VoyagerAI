"use client";

import { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";

interface RecommendedEvent {
  id: number;
  title: string;
  venue?: string;
  city?: string;
  date?: string;
  price?: string;
  url?: string;
  provider?: string;
  recommendation_score?: number;
  recommendation_reason?: string;
}

interface RecommendationsProps {
  onEventClick?: (event: RecommendedEvent) => void;
}

export default function Recommendations({ onEventClick }: RecommendationsProps) {
  const [isClient, setIsClient] = useState(false);
  const [recommendations, setRecommendations] = useState<RecommendedEvent[]>([]);
  const [trending, setTrending] = useState<RecommendedEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'personalized' | 'trending'>('personalized');
  
  // Get auth context only on client side
  let authContext = null;
  let user = null;
  try {
    authContext = useAuth();
    user = authContext?.user;
  } catch (error) {
    // Auth context not available (server-side rendering)
    authContext = null;
    user = null;
  }

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Debug: Log auth state
  useEffect(() => {
    if (isClient) {
      console.log('Recommendations - Auth state:', {
        user: user,
        authContext: authContext,
        isAuthenticated: authContext?.isAuthenticated,
        isLoading: authContext?.isLoading,
        hasToken: typeof window !== 'undefined' ? !!localStorage.getItem('voyagerai_token') : false
      });
    }
  }, [isClient, authContext, user]);

  useEffect(() => {
    if (isClient) {
      loadRecommendations();
      loadTrending();
    }
  }, [user, isClient]);

  const loadRecommendations = async () => {
    try {
      const params = new URLSearchParams();
      if (user?.email) {
        params.append('email', user.email);
      } else if (hasToken) {
        // If we have a token but no user object, try to get user email from token
        try {
          const token = localStorage.getItem('voyagerai_token');
          const response = await fetch('http://localhost:5000/api/auth/profile', {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (response.ok) {
            const userData = await response.json();
            if (userData.success && userData.user?.email) {
              params.append('email', userData.user.email);
            }
          }
        } catch (e) {
          console.log('Could not get user email from token');
        }
      }

      const response = await fetch(`http://localhost:5000/api/events/recommendations?${params}`);
      const data = await response.json();
      
      if (data.success) {
        setRecommendations(data.recommendations || []);
      }
    } catch (error) {
      console.error("Failed to load recommendations:", error);
    }
  };

  const loadTrending = async () => {
    try {
      const response = await fetch("http://localhost:5000/api/events/trending");
      const data = await response.json();
      
      if (data.success) {
        setTrending(data.trending || []);
      }
    } catch (error) {
      console.error("Failed to load trending events:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const getScoreColor = (score?: number) => {
    if (!score) return "text-gray-400";
    if (score >= 0.8) return "text-green-400";
    if (score >= 0.6) return "text-yellow-400";
    return "text-orange-400";
  };

  const getScoreText = (score?: number) => {
    if (!score) return "N/A";
    if (score >= 0.8) return "Perfect Match";
    if (score >= 0.6) return "Great Match";
    if (score >= 0.4) return "Good Match";
    return "Fair Match";
  };

  // Don't render on server side
  if (!isClient) {
    return (
      <div className="bg-gray-800/50 p-6 rounded-lg">
        <div className="text-center text-gray-400">Loading recommendations...</div>
      </div>
    );
  }

  // Wait for auth context to load or check if we have a token
  const hasToken = typeof window !== 'undefined' && localStorage.getItem('voyagerai_token');
  
  // Only show loading if auth context is actually loading
  if (authContext?.isLoading) {
    return (
      <div className="bg-gray-800/50 p-6 rounded-lg">
        <div className="text-center text-gray-400">Loading user data...</div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="bg-gray-800/50 p-6 rounded-lg">
        <div className="text-center text-gray-400">Loading recommendations...</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800/50 p-6 rounded-lg">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">Discover Events</h2>
        <div className="flex bg-gray-700 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('personalized')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'personalized'
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:text-white'
            }`}
          >
            For You
          </button>
          <button
            onClick={() => setActiveTab('trending')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'trending'
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:text-white'
            }`}
          >
            Trending
          </button>
        </div>
      </div>

      {activeTab === 'personalized' ? (
        <div>
          {!user && !hasToken ? (
            <div className="text-center py-8">
              <div className="text-gray-400 mb-4">
                Sign in to get personalized recommendations based on your preferences!
              </div>
              <button
                onClick={() => window.location.href = '/login'}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white"
              >
                Sign In
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {recommendations.length === 0 ? (
                <div className="text-center text-gray-400 py-8">
                  Save some events to get personalized recommendations!
                </div>
              ) : (
                recommendations.map(event => (
                  <div
                    key={event.id}
                    className="p-4 bg-gray-700/30 rounded-lg hover:bg-gray-700/50 transition-colors cursor-pointer"
                    onClick={() => onEventClick?.(event)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-white mb-1">
                          {event.title}
                        </h3>
                        <div className="text-sm text-gray-300 space-y-1">
                          {event.venue && <div>📍 {event.venue}</div>}
                          {event.city && <div>🏙️ {event.city}</div>}
                          {event.date && <div>📅 {new Date(event.date).toLocaleDateString()}</div>}
                          {event.price && <div>💰 {event.price}</div>}
                        </div>
                        {event.recommendation_reason && (
                          <div className="mt-2 text-xs text-blue-300">
                            💡 {event.recommendation_reason}
                          </div>
                        )}
                      </div>
                      {event.recommendation_score && (
                        <div className="ml-4 text-right">
                          <div className={`text-sm font-semibold ${getScoreColor(event.recommendation_score)}`}>
                            {getScoreText(event.recommendation_score)}
                          </div>
                          <div className="text-xs text-gray-400">
                            {Math.round(event.recommendation_score * 100)}% match
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {trending.length === 0 ? (
            <div className="text-center text-gray-400 py-8">
              No trending events at the moment.
            </div>
          ) : (
            trending.map((event, index) => (
              <div
                key={event.id}
                className="p-4 bg-gray-700/30 rounded-lg hover:bg-gray-700/50 transition-colors cursor-pointer"
                onClick={() => onEventClick?.(event)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-lg">🔥</span>
                      <span className="text-sm text-orange-400 font-semibold">
                        #{index + 1} Trending
                      </span>
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-1">
                      {event.title}
                    </h3>
                    <div className="text-sm text-gray-300 space-y-1">
                      {event.venue && <div>📍 {event.venue}</div>}
                      {event.city && <div>🏙️ {event.city}</div>}
                      {event.date && <div>📅 {new Date(event.date).toLocaleDateString()}</div>}
                      {event.price && <div>💰 {event.price}</div>}
                    </div>
                  </div>
                  <div className="ml-4 text-right">
                    <div className="text-sm text-orange-400 font-semibold">
                      Hot Right Now
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
