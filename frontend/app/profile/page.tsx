"use client";

import { useAuth } from "@/contexts/AuthContext";
import { useState, useEffect } from "react";
import SubscriptionStatus from "@/components/SubscriptionStatus";
import EventReviews from "@/components/EventReviews";

interface Favorite {
  id: number;
  title: string;
  date: string | null;
  time: string | null;
  venue: string | null;
  city: string | null;
  url: string | null;
  image_url: string | null;
  provider: string | null;
  created_at: string;
}

export default function ProfilePage() {
  const { user, isAuthenticated, logout } = useAuth();
  const [favorites, setFavorites] = useState<Favorite[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isAuthenticated && user?.email) {
      fetchFavorites();
    }
  }, [isAuthenticated, user]);

  const fetchFavorites = async () => {
    try {
      const response = await fetch(`/api/favorites?email=${encodeURIComponent(user?.email || "")}`);
      const data = await response.json();
      if (data.success) {
        setFavorites(data.favorites);
      }
    } catch (error) {
      console.error("Failed to fetch favorites:", error);
    } finally {
      setLoading(false);
    }
  };

  const deleteFavorite = async (id: number) => {
    try {
      const response = await fetch(`/api/favorites/${id}`, {
        method: "DELETE",
      });
      if (response.ok) {
        setFavorites(favorites.filter(fav => fav.id !== id));
      }
    } catch (error) {
      console.error("Failed to delete favorite:", error);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-black text-white p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold mb-8">Please sign in to view your profile</h1>
          <a href="/login" className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg">
            Sign In
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-black text-white p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">Welcome back, {user?.name}!</h1>
            <p className="text-gray-300 mt-2">{user?.email}</p>
            <p className="text-sm text-gray-400">Member since {new Date(user?.created_at || "").toLocaleDateString()}</p>
          </div>
          <button
            onClick={logout}
            className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg"
          >
            Logout
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gray-800/50 p-6 rounded-lg">
            <h3 className="text-xl font-semibold mb-2">📅 Saved Events</h3>
            <p className="text-3xl font-bold text-blue-400">{favorites.length}</p>
          </div>
          <div className="bg-gray-800/50 p-6 rounded-lg">
            <h3 className="text-xl font-semibold mb-2">🏆 Active</h3>
            <p className="text-3xl font-bold text-green-400">Yes</p>
          </div>
          <div className="bg-gray-800/50 p-6 rounded-lg">
            <h3 className="text-xl font-semibold mb-2">🎯 Account Type</h3>
            <p className="text-3xl font-bold text-purple-400">Free</p>
          </div>
        </div>

        {/* Subscription Status */}
        <SubscriptionStatus />

        {/* Your Reviews */}
        <div className="bg-gray-800/50 p-6 rounded-lg mb-8">
          <h2 className="text-2xl font-bold mb-6">Your Reviews</h2>
          <EventReviews
            eventTitle=""
            userEmail={user?.email}
          />
        </div>

        {/* Saved Events */}
        <div className="bg-gray-800/50 p-6 rounded-lg">
          <h2 className="text-2xl font-bold mb-6">Your Saved Events</h2>
          {loading ? (
            <p>Loading your favorites...</p>
          ) : favorites.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-400 text-lg mb-4">No saved events yet</p>
              <a href="/" className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg">
                Discover Events
              </a>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {favorites.map((favorite) => (
                <div key={favorite.id} className="bg-gray-700/50 p-4 rounded-lg">
                  <h3 className="font-semibold mb-2">{favorite.title}</h3>
                  {favorite.venue && <p className="text-sm text-gray-300 mb-1">📍 {favorite.venue}</p>}
                  {favorite.city && <p className="text-sm text-gray-300 mb-1">🏙️ {favorite.city}</p>}
                  {favorite.date && <p className="text-sm text-gray-300 mb-1">📅 {favorite.date}</p>}
                  {favorite.time && <p className="text-sm text-gray-300 mb-1">🕐 {favorite.time}</p>}
                  <div className="flex gap-2 mt-3">
                    {favorite.url && (
                      <a
                        href={favorite.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm"
                      >
                        View Event
                      </a>
                    )}
                    <button
                      onClick={() => deleteFavorite(favorite.id)}
                      className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
