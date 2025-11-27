"use client";

import { useState, useEffect } from "react";
import HotelsPlanner from "../../components/HotelsPlanner";
import HotelCard from "../../components/HotelCard";
import { getHotels, getPopularHotels, getHotelCities, Hotel, HotelSearchResponse } from "../../lib/api";

export default function HotelsPage() {
  const [popularHotels, setPopularHotels] = useState<Hotel[]>([]);
  const [allHotels, setAllHotels] = useState<Hotel[]>([]);
  const [cities, setCities] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        
        // Load popular hotels - focus on Toronto first
        const popularData: HotelSearchResponse = await getPopularHotels("Toronto", 6);
        if (popularData.success) {
          setPopularHotels(popularData.hotels);
        }

        // Load all hotels
        const hotelsData = await getHotels(undefined, undefined, undefined, 12);
        if (hotelsData.success) {
          setAllHotels(hotelsData.hotels);
        }

        // Load cities
        const citiesData = await getHotelCities();
        if (citiesData.success) {
          setCities(citiesData.cities);
        }

      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Loading hotels...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center">
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              <strong>Error:</strong> {error}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            🏨 Find Your Perfect Hotel
          </h1>
                <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
                  Discover amazing hotels across {cities.length} cities including Toronto, Mumbai, Delhi, and more with real-time pricing and ratings from our comprehensive database.
                </p>
        </div>

        {/* Hotel Search Planner */}
        <HotelsPlanner />

        {/* Popular Hotels Section */}
            {popularHotels.length > 0 && (
              <section className="mt-12">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                    ⭐ Popular Hotels
                  </h2>
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    Highest rated hotels
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {popularHotels.map((hotel) => (
                    <HotelCard key={hotel.id} hotel={hotel} />
                  ))}
                </div>
              </section>
            )}

            {/* All Hotels Section */}
            {allHotels.length > 0 && (
              <section className="mt-12">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                    🏨 All Hotels
                  </h2>
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {allHotels.length} hotels available
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {allHotels.map((hotel) => (
                    <HotelCard key={hotel.id} hotel={hotel} />
                  ))}
                </div>
              </section>
            )}

        {/* Cities Section */}
        {cities.length > 0 && (
          <section className="mt-12">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
              🌍 Available Cities
            </h2>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                {cities.map((city) => (
                  <span
                    key={city}
                    className="px-3 py-2 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-sm font-medium text-center"
                  >
                    {city}
                  </span>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* Features Section */}
        <section className="mt-12">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
            ✨ Hotel Features
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
              <div className="text-3xl mb-3">🔍</div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Smart Search
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Search hotels by city, rating, and availability with real-time results.
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
              <div className="text-3xl mb-3">⭐</div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Verified Ratings
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                All hotels come with verified ratings and review counts from trusted sources.
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
              <div className="text-3xl mb-3">💰</div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Real Pricing
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Get real-time pricing information directly from booking platforms.
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
              <div className="text-3xl mb-3">📅</div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Itinerary Integration
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Add hotels directly to your travel itineraries for seamless planning.
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
              <div className="text-3xl mb-3">🌍</div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Wide Coverage
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Hotels available in {cities.length} cities across multiple countries.
              </p>
            </div>
            {/* Direct Booking card removed per request */}
          </div>
        </section>
      </div>
    </div>
  );
}
