"use client";

import React, { useState, useEffect } from "react";
import { getFavorites } from "@/lib/api";

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

// Wrapper component that handles auth context
function RecommendationsContent({ onEventClick }: RecommendationsProps) {
  const [recommendations, setRecommendations] = useState<RecommendedEvent[]>([]);
  const [trending, setTrending] = useState<RecommendedEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'personalized' | 'trending'>('personalized');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [authLoading, setAuthLoading] = useState(true);

  // Check authentication status directly
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('voyagerai_token');
        if (token) {
          const response = await fetch('http://127.0.0.1:5000/api/auth/verify-token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token })
          });
          const data = await response.json();
          
          if (data.success && data.user) {
            setIsAuthenticated(true);
            setUser(data.user);
          } else {
            localStorage.removeItem('voyagerai_token');
            setIsAuthenticated(false);
            setUser(null);
          }
        } else {
          setIsAuthenticated(false);
          setUser(null);
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        setIsAuthenticated(false);
        setUser(null);
      } finally {
        setAuthLoading(false);
      }
    };

    checkAuth();
  }, []);

  // Debug: Log auth state
  useEffect(() => {
    console.log('Recommendations - Auth state:', {
      user: user,
      isAuthenticated: isAuthenticated,
      authLoading: authLoading
    });
  }, [isAuthenticated, user, authLoading]);

  useEffect(() => {
    if (!authLoading) {
      loadRecommendations();
      loadTrending();
    }
  }, [user, isAuthenticated, authLoading]);

  const loadRecommendations = async () => {
    try {
      console.log('Recommendations: Loading saved events...');
      console.log('Recommendations: User object:', user);
      
      // Only load saved events if user is authenticated
      if (!isAuthenticated) {
        console.log('Recommendations: No authentication, skipping saved events');
        setRecommendations([]);
        return;
      }
      
      let userEmail = null;
      
      if (user?.email) {
        console.log('Recommendations: Using user email:', user.email);
        userEmail = user.email;
      } else {
        console.log('Recommendations: No user email, trying to get from token...');
        try {
          const token = localStorage.getItem('voyagerai_token');
          console.log('Recommendations: Token found:', token ? 'Yes' : 'No');
          
          if (token) {
            const response = await fetch('http://127.0.0.1:5000/api/auth/profile', {
              headers: { 'Authorization': `Bearer ${token}` }
            });
            console.log('Recommendations: Profile response status:', response.status);
            
            if (response.ok) {
              const userData = await response.json();
              console.log('Recommendations: Profile data:', userData);
              if (userData.user?.email) {
                console.log('Recommendations: Using profile email:', userData.user.email);
                userEmail = userData.user.email;
              }
            } else {
              console.log('Recommendations: Token expired, clearing localStorage');
              localStorage.removeItem('voyagerai_token');
            }
          }
        } catch (e) {
          console.log('Recommendations: Could not get user email from token:', e);
        }
        
        if (!userEmail) {
          console.log('Recommendations: Using fallback email for token error:', userEmail);
          userEmail = 'fallback@example.com'; // Fallback for testing
        }
      }
      
      if (!userEmail) {
        console.log('Recommendations: No user email found, skipping saved events');
        setRecommendations([]);
        return;
      }

      console.log('Recommendations: Loading saved events for email:', userEmail);
      const data = await getFavorites(userEmail);
      console.log('Recommendations: Saved events response:', data);
      
      // Convert favorites to recommended events format
      const savedEvents = data.map((fav: any) => ({
        id: fav.id,
        title: fav.title,
        venue: fav.venue,
        city: fav.city,
        date: fav.date,
        price: fav.price,
        url: fav.url,
        provider: fav.provider || 'saved',
        recommendation_score: 0.9, // High score for saved events
        recommendation_reason: 'You saved this event'
      }));
      
      setRecommendations(savedEvents);
      console.log('Recommendations: Set recommendations:', savedEvents.length);
    } catch (error) {
      console.error("Recommendations: Failed to load saved events:", error);
      setRecommendations([]);
    }
  };

  const loadTrending = async () => {
    try {
      console.log('Recommendations: Loading trending events...');
      const response = await fetch('http://127.0.0.1:5000/api/events/trending');
      const data = await response.json();
      
      if (data.success && data.trending) {
        const trendingEvents = data.trending.map((event: any) => ({
          id: event.id || Math.random(),
          title: event.title || event.name,
          venue: event.venue,
          city: event.city,
          date: event.date,
          price: event.price,
          url: event.url,
          provider: event.provider || 'trending',
          recommendation_score: event.score || 0.8,
          recommendation_reason: 'Trending in your area'
        }));
        
        setTrending(trendingEvents);
        console.log('Recommendations: Set trending:', trendingEvents.length);
      }
    } catch (error) {
      console.error("Recommendations: Failed to load trending events:", error);
      setTrending([]);
    }
  };

  if (authLoading) {
    return (
      <div className="text-center py-8 text-gray-400">
        Loading recommendations...
      </div>
    );
  }

  return (
    <div className="bg-gray-800/30 rounded-2xl p-6">
      <h2 className="text-2xl font-bold mb-6 text-center">🎯 Discover Events</h2>
      
      {/* Tab Navigation */}
      <div className="flex justify-center mb-6">
        <div className="flex bg-gray-700/50 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('personalized')}
            className={`px-4 py-2 rounded-md transition ${
              activeTab === 'personalized'
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:text-white'
            }`}
          >
            For You
          </button>
          <button
            onClick={() => setActiveTab('trending')}
            className={`px-4 py-2 rounded-md transition ${
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
          {!isAuthenticated && recommendations.length === 0 ? (
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
                recommendations.map((event) => (
                  <div
                    key={event.id}
                    className="bg-gray-700/50 rounded-lg p-4 hover:bg-gray-700/70 transition cursor-pointer"
                    onClick={() => onEventClick?.(event)}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h3 className="font-semibold text-white mb-2">{event.title}</h3>
                        {event.venue && (
                          <p className="text-sm text-gray-300 mb-1">📍 {event.venue}</p>
                        )}
                        {event.city && (
                          <p className="text-sm text-gray-300 mb-1">🏙️ {event.city}</p>
                        )}
                        {event.date && (
                          <p className="text-sm text-gray-300 mb-1">📅 {event.date}</p>
                        )}
                        {event.price && (
                          <p className="text-sm text-gray-300 mb-1">💰 {event.price}</p>
                        )}
                        {event.recommendation_reason && (
                          <p className="text-xs text-blue-400 mt-2">
                            {event.recommendation_reason}
                          </p>
                        )}
                      </div>
                      <div className="ml-4">
                        <div className="bg-blue-600/20 text-blue-400 px-2 py-1 rounded text-xs">
                          {Math.round((event.recommendation_score || 0) * 100)}% match
                        </div>
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
              Loading trending events...
            </div>
          ) : (
            trending.map((event) => (
              <div
                key={event.id}
                className="bg-gray-700/50 rounded-lg p-4 hover:bg-gray-700/70 transition cursor-pointer"
                onClick={() => onEventClick?.(event)}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="font-semibold text-white mb-2">{event.title}</h3>
                    {event.venue && (
                      <p className="text-sm text-gray-300 mb-1">📍 {event.venue}</p>
                    )}
                    {event.city && (
                      <p className="text-sm text-gray-300 mb-1">🏙️ {event.city}</p>
                    )}
                    {event.date && (
                      <p className="text-sm text-gray-300 mb-1">📅 {event.date}</p>
                    )}
                    {event.price && (
                      <p className="text-sm text-gray-300 mb-1">💰 {event.price}</p>
                    )}
                    {event.recommendation_reason && (
                      <p className="text-xs text-green-400 mt-2">
                        {event.recommendation_reason}
                      </p>
                    )}
                  </div>
                  <div className="ml-4">
                    <div className="bg-green-600/20 text-green-400 px-2 py-1 rounded text-xs">
                      Trending
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

// Main component with error boundary
export default function Recommendations({ onEventClick }: RecommendationsProps) {
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    const handleError = () => setHasError(true);
    window.addEventListener('error', handleError);
    return () => window.removeEventListener('error', handleError);
  }, []);

  if (hasError) {
    return (
      <div className="bg-gray-800/30 rounded-2xl p-6">
        <h2 className="text-2xl font-bold mb-6 text-center">🎯 Discover Events</h2>
        <div className="text-center text-gray-400 py-8">
          Unable to load recommendations. Please try refreshing the page.
        </div>
      </div>
    );
  }

  return <RecommendationsContent onEventClick={onEventClick} />;
}