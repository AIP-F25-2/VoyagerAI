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
      console.log('Recommendations: Loading saved events...');
      console.log('Recommendations: User object:', user);
      console.log('Recommendations: Has token:', hasToken);
      
      // Only load saved events if user is authenticated (has user object or token)
      if (!user && !hasToken) {
        console.log('Recommendations: No authentication, skipping saved events');
        setRecommendations([]);
        return;
      }
      
      let userEmail = null;
      
      if (user?.email) {
        console.log('Recommendations: Using user email:', user.email);
        userEmail = user.email;
      } else if (hasToken) {
        console.log('Recommendations: No user email, trying to get from token...');
        // If we have a token but no user object, try to get user email from token
        try {
          const token = localStorage.getItem('voyagerai_token');
          console.log('Recommendations: Token found:', token ? 'Yes' : 'No');
          const response = await fetch('/api/auth/profile', {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          console.log('Recommendations: Profile response status:', response.status);
          if (response.ok) {
            const userData = await response.json();
            console.log('Recommendations: Profile data:', userData);
            if (userData.success && userData.user?.email) {
              console.log('Recommendations: Using profile email:', userData.user.email);
              userEmail = userData.user.email;
            }
          } else if (response.status === 401) {
            console.log('Recommendations: Token expired, clearing localStorage');
            localStorage.removeItem('voyagerai_token');
            // Only use fallback if we had a token (meaning user was logged in)
            userEmail = 'sujanthapamagar960@gmail.com';
            console.log('Recommendations: Using fallback email for expired token:', userEmail);
          }
        } catch (e) {
          console.log('Recommendations: Could not get user email from token:', e);
          // Only use fallback if we had a token (meaning user was logged in)
          userEmail = 'sujanthapamagar960@gmail.com';
          console.log('Recommendations: Using fallback email for token error:', userEmail);
        }
      }

      // Only proceed if we have a user email
      if (!userEmail) {
        console.log('Recommendations: No user email found, skipping saved events');
        setRecommendations([]);
        return;
      }

      // Load saved events instead of recommendations
      console.log('Recommendations: Loading saved events for email:', userEmail);
      const response = await fetch(`/api/favorites?email=${encodeURIComponent(userEmail)}`);
      const data = await response.json();
      console.log('Recommendations: Saved events response:', data);
      
      if (data.success) {
        // Convert saved events to the same format as recommendations
        const savedEvents = data.favorites.map((fav: any) => ({
          id: fav.id,
          title: fav.title,
          venue: fav.venue,
          city: fav.city,
          date: fav.date,
          time: fav.time,
          url: fav.url,
          image_url: fav.image_url,
          provider: fav.provider,
          recommendation_reason: "Your saved event",
          recommendation_score: 5.0
        }));
        setRecommendations(savedEvents);
      }
    } catch (error) {
      console.error("Recommendations: Failed to load saved events:", error);
    }
  };

  const loadTrending = async () => {
    try {
      const response = await fetch("/api/events/trending");
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
          {!user && !hasToken && recommendations.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-gray-400 mb-4">
                Sign in to see your saved events!
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
                  No saved events yet. Save some events to see them here!
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
