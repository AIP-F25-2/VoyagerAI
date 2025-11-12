"use client";
import { useEffect, useState } from "react";
import SearchBar from "@/components/ui/SearchBar";
import EventsSection from "@/components/ui/EventsSection";
import AdvancedFilters from "@/components/AdvancedFilters";
// Removed Recommendations component
import AddToItinerary from "@/components/AddToItinerary";
import AIChat from "@/components/AIChat";
import Link from "next/link";
import { MusicalNoteIcon, TrophyIcon, TicketIcon, SparklesIcon } from "@heroicons/react/24/solid";

export default function HomePage() {
  const [ticketmasterEvents, setTicketmasterEvents] = useState<any[]>([]);
  const [eventbriteEvents, setEventbriteEvents] = useState<any[]>([]);
  const [csvEvents, setCsvEvents] = useState<any[]>([]);
  const [hotels, setHotels] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [city, setCity] = useState("");
  const [filters, setFilters] = useState<any>({});
  const [searchType, setSearchType] = useState<"events" | "hotels">("events");
  const [showAIChat, setShowAIChat] = useState(false);
  // Removed showRecommendations state

  // Get user's location using Geolocation + reverse geocoding
  const fetchUserCity = async () => {
    if (!navigator.geolocation) return;

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        try {
          const geoRes = await fetch(
            `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${latitude}&longitude=${longitude}&localityLanguage=en`
          );
          const geoData = await geoRes.json();
          if (geoData.city) setCity(geoData.city);
          else if (geoData.locality) setCity(geoData.locality);
        } catch (err) {
          console.warn("Geolocation lookup failed:", err);
        }
      },
      () => console.warn("User denied location access.")
    );
  };

  // Helper functions for loadEvents
  const buildHotelsParams = (search: string, detectedCity: string): URLSearchParams => {
    const params = new URLSearchParams();
    if (search) params.append("city", search);
    else if (detectedCity) params.append("city", detectedCity);
    params.append("limit", "20");
    return params;
  };

  const buildEventsParams = (search: string, detectedCity: string, appliedFilters: any): URLSearchParams => {
    const params = new URLSearchParams();
    if (search) params.append("q", search);
    if (detectedCity) params.append("city", detectedCity);
    
    Object.entries(appliedFilters).forEach(([key, value]) => {
      if (value && value !== "" && value !== "all") {
        params.append(key, value as string);
      }
    });
    
    if (!params.has("limit")) {
      params.append("limit", "50");
    }
    return params;
  };

  const handleHotelsResponse = async (params: URLSearchParams) => {
    const res = await fetch(`/api/hotels/search?${params.toString()}`);
    if (!res.ok) throw new Error("Backend unavailable or API error");
    const data = await res.json();
    setHotels(data.hotels || []);
    setTicketmasterEvents([]);
    setEventbriteEvents([]);
    setCsvEvents([]);
  };

  const extractIndividualArrays = (data: any) => {
    const tmEvents = Array.isArray(data.ticketmaster) ? data.ticketmaster : [];
    const ebEvents = Array.isArray(data.eventbrite) ? data.eventbrite : [];
    const csvEvts = Array.isArray(data.csv_events) ? data.csv_events : [];
    
    console.log('📦 Received data from API:', {
      ticketmaster: tmEvents.length,
      eventbrite: ebEvents.length,
      csv: csvEvts.length,
      firstTMName: tmEvents.length > 0 ? tmEvents[0]?.name : 'none',
      firstEBName: ebEvents.length > 0 ? ebEvents[0]?.name : 'none',
      firstCSVName: csvEvts.length > 0 ? csvEvts[0]?.name : 'none'
    });
    
    setTicketmasterEvents(tmEvents);
    setEventbriteEvents(ebEvents);
    setCsvEvents(csvEvts);
    
    console.log('✅ Setting events state:', {
      ticketmaster: tmEvents.length,
      eventbrite: ebEvents.length,
      csv: csvEvts.length
    });
  };

  const handleMergedArray = (data: any) => {
    const merged = data.merged || [];
    setTicketmasterEvents(merged.filter((e: any) => 
      !e.source || e.source === "ticketmaster" || e.source === "unknown"
    ));
    setEventbriteEvents(merged.filter((e: any) => e.source === "eventbrite"));
    setCsvEvents(merged.filter((e: any) => e.source === "csv"));
  };

  const clearAllEvents = () => {
    setTicketmasterEvents([]);
    setEventbriteEvents([]);
    setCsvEvents([]);
  };

  const handleEventsResponse = async (params: URLSearchParams, data: any) => {
    const hasIndividualArrays = data.ticketmaster !== undefined || 
                                 data.eventbrite !== undefined || 
                                 data.csv_events !== undefined;
    
    if (hasIndividualArrays) {
      extractIndividualArrays(data);
    } else if (data.merged && Array.isArray(data.merged) && data.merged.length > 0) {
      handleMergedArray(data);
    } else {
      clearAllEvents();
    }
    
    console.log('📊 Events loaded from API:', {
      ticketmaster: Array.isArray(data.ticketmaster) ? data.ticketmaster.length : 0,
      eventbrite: Array.isArray(data.eventbrite) ? data.eventbrite.length : 0,
      csv: Array.isArray(data.csv_events) ? data.csv_events.length : 0,
      merged: Array.isArray(data.merged) ? data.merged.length : 0,
      source: data.source,
      hasTicketmasterKey: 'ticketmaster' in data,
      ticketmasterType: typeof data.ticketmaster,
      firstTMName: Array.isArray(data.ticketmaster) && data.ticketmaster.length > 0 ? data.ticketmaster[0]?.name : 'none'
    });
    setHotels([]);
  };

  const loadEvents = async (search: string, detectedCity = "", appliedFilters = {}, searchMode: "events" | "hotels" = "events") => {
    setLoading(true);
    setError(null);
    console.log('🔄 Loading events with:', { search, detectedCity, appliedFilters, searchMode });
    console.log('🔄 Current state before load:', { 
      ticketmasterCount: ticketmasterEvents.length, 
      eventbriteCount: eventbriteEvents.length, 
      csvCount: csvEvents.length 
    });
    try {
      if (searchMode === "hotels") {
        const params = buildHotelsParams(search, detectedCity);
        await handleHotelsResponse(params);
      } else {
        const params = buildEventsParams(search, detectedCity, appliedFilters);
        const res = await fetch(`/api/events?${params.toString()}`);
        if (!res.ok) throw new Error("Backend unavailable or API error");
        const data = await res.json();
        await handleEventsResponse(params, data);
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch data");
      clearAllEvents();
      setHotels([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserCity();
  }, []);

  // Initial load on mount - load events immediately
  useEffect(() => {
    console.log('🔄 Initial mount - loading events');
    loadEvents("", "", {}, "events");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load events when city, searchType, or query changes
  useEffect(() => {
    // Skip initial mount (handled by the effect above)
    const cityToUse = filters?.city || city || "";
    console.log('🔄 useEffect triggered (city/query/searchType):', { city, filters, searchType, query, cityToUse });
    loadEvents(query, cityToUse, filters || {}, searchType);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [city, searchType, query]);
  
  // Separate effect for filter changes to avoid dependency issues
  useEffect(() => {
    // Skip if filters is empty object (initial state) - initial load is handled separately
    if (filters && Object.keys(filters).length > 0) {
      const cityToUse = filters?.city || city || "";
      console.log('🔄 Filter change detected, reloading events:', { filters, cityToUse });
      loadEvents(query, cityToUse, filters, searchType);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(filters)]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadEvents(query, city, filters, searchType);
  };

  const handleFiltersChange = (newFilters: any) => {
    console.log('🔧 Filters changed:', newFilters);
    setFilters(newFilters);
    // Use city from filters if available, otherwise use detected city
    const cityToUse = newFilters.city || city || "";
    loadEvents(query, cityToUse, newFilters, searchType);
  };

  const handleSearchTypeChange = (type: "events" | "hotels") => {
    setSearchType(type);
    setQuery(""); // Clear query when switching search types
  };

  const categories = [
    { label: "Concerts", icon: MusicalNoteIcon },
    { label: "Sports", icon: TrophyIcon },
    { label: "Theater", icon: TicketIcon },
    { label: "Festivals", icon: SparklesIcon },
  ];

  return (
    <main className="min-h-screen text-white select-none">
      {/* AI Chat Floating Button */}
      {!showAIChat && (
        <button
          onClick={() => setShowAIChat(true)}
          className="fixed bottom-6 right-6 z-50 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white px-6 py-4 rounded-full shadow-2xl flex items-center gap-3 font-semibold transition-all duration-300 hover:scale-105"
          style={{ boxShadow: '0 8px 32px rgba(139, 92, 246, 0.5)' }}
        >
          <span className="text-2xl">🤖</span>
          <span>AI Assistant</span>
        </button>
      )}

      {/* AI Chat Modal */}
      {showAIChat && (
        <div className="fixed bottom-6 right-6 z-50 w-96 max-w-[calc(100vw-3rem)]">
          <AIChat onClose={() => setShowAIChat(false)} />
        </div>
      )}

      {/* AI Itinerary Banner */}
      <div className="mx-auto max-w-6xl px-4 mt-4 mb-4">
        <div className="bg-gradient-to-r from-purple-600/20 to-blue-600/20 border border-purple-500/30 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">✨</span>
            <div>
              <h3 className="font-bold text-lg">AI-Powered Itinerary Generation</h3>
              <p className="text-sm text-gray-300">Let AI create a complete travel plan for you!</p>
            </div>
          </div>
          <Link
            href="/travel-plans"
            className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 px-6 py-2 rounded-lg font-semibold transition-all duration-300 hover:scale-105"
          >
            Try It Now →
          </Link>
        </div>
      </div>

      {/* Hero Section */}
      <section className="relative w-full py-16 text-center mx-auto max-w-6xl mt-6">
        <div className="rounded-3xl glass-dark shadow-glow px-4 sm:px-8 py-10">
          <h1 className="text-5xl font-extrabold tracking-tight mb-3">
            Discover Events Around You
          </h1>
          <p className="max-w-2xl mx-auto text-lg text-gray-200 opacity-90 mb-6">
            Find concerts, sports, theater shows, and more near{' '}
            <span className="text-blue-400 font-semibold">{city || 'your area'}</span>.
          </p>

          {/* SearchBar */}
          <div className="max-w-3xl mx-auto mb-6">
            <SearchBar 
              query={query} 
              setQuery={setQuery} 
              onSearch={handleSearch}
              searchType={searchType}
              onSearchTypeChange={handleSearchTypeChange}
            />
          </div>

          {/* Category Buttons */}
          <div className="flex flex-wrap justify-center gap-4">
            {categories.map((cat) => (
              <button
                key={cat.label}
                className="group flex items-center gap-2 px-6 py-2 rounded-xl glass-light hover:bg-blue-600/40 hover:shadow-glow hover:cursor-pointer hover:scale-105 transition-all duration-300"
                onClick={() => loadEvents(cat.label, city, filters)}
              >
                <cat.icon className="h-5 w-5 text-neutral-300 group-hover:text-white transition" />
                <span className="text-neutral-300 font-medium group-hover:text-white">{cat.label}</span>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Advanced Filters */}
      <div className="mx-auto max-w-6xl px-4">
        <AdvancedFilters
          onFiltersChange={handleFiltersChange}
          onSearch={handleSearch}
        />
      </div>

      {/* Recommendations section removed */}

      {/* Results */}
      <div className="mx-auto max-w-6xl px-4 py-10">
        {loading && (
          <p className="text-gray-400 text-lg text-center">
            ⏳ Loading {searchType === "hotels" ? "hotels" : "events"} near you...
          </p>
        )}
        {error && <p className="text-red-400 text-center">{error}</p>}
        {!loading && !error && (
          <>
            {/* Hotel Results */}
            {searchType === "hotels" && (
              <div className="mb-8">
                <h2 className="text-2xl font-bold text-white mb-6 text-center">
                  🏨 Hotels in {query || city || "your area"}
                </h2>
                {hotels.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {hotels.slice(0, 12).map((hotel) => (
                      <div key={hotel.id} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                        <div className="flex justify-between items-start mb-2">
                          <h3 className="text-lg font-semibold text-white">{hotel.name}</h3>
                          {hotel.price_per_night && (
                            <span className="text-green-400 font-bold">{hotel.price_per_night}</span>
                          )}
                        </div>
                        <p className="text-gray-300 text-sm mb-2">📍 {hotel.address}</p>
                        <p className="text-gray-300 text-sm mb-2">🏙️ {hotel.city}</p>
                        {hotel.rating && (
                          <p className="text-yellow-400 text-sm mb-3">
                            ⭐ {hotel.rating.toFixed(1)}/10
                            {hotel.review_count && ` (${hotel.review_count} reviews)`}
                          </p>
                        )}
                        <div className="flex gap-2">
                          {hotel.url && (
                            <a
                              href={hotel.url}
                              target="_blank"
                              rel="noreferrer"
                              className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition"
                            >
                              🔗 Book Now
                            </a>
                          )}
                          <AddToItinerary
                            itemType="hotel"
                            itemData={{
                              title: hotel.name,
                              description: `Hotel in ${hotel.city} - ${hotel.address}`,
                              date: hotel.check_in,
                              location: hotel.address,
                              price: hotel.price_per_night ? Number.parseFloat(hotel.price_per_night.replace(/[^0-9.-]+/g, '')) : undefined,
                              url: hotel.url
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : !loading && (
                  <div className="text-center py-12 bg-gray-800/30 rounded-lg border border-gray-700">
                    <p className="text-gray-400 text-lg mb-2">😔 No hotels found</p>
                    <p className="text-gray-500 text-sm">Try searching for a different city or check our hotels page</p>
                    <a href="/hotels" className="inline-block mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition">
                      🌐 Browse All Hotels
                    </a>
                  </div>
                )}
              </div>
            )}

            {/* Filter Summary */}
            {searchType === "events" && Object.keys(filters).some(key => {
              const value = filters[key];
              return value && value !== "" && value !== "all" && value !== "date_asc";
            }) && (
              <div className="mb-6 p-4 bg-blue-600/20 border border-blue-500/30 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">🔍</span>
                  <span className="font-semibold text-blue-200">Filters Applied</span>
                </div>
                <p className="text-sm text-gray-300">
                  Showing {ticketmasterEvents.length + eventbriteEvents.length + csvEvents.length} total events
                  {filters.city && ` in ${filters.city}`}
                  {filters.category && ` • Category: ${filters.category}`}
                  {filters.date_from && ` • From: ${filters.date_from}`}
                  {filters.date_to && ` to ${filters.date_to}`}
                  {filters.price_min && ` • Price: $${filters.price_min}`}
                  {filters.price_max && ` - $${filters.price_max}`}
                </p>
                {filters.city && ticketmasterEvents.length === 0 && eventbriteEvents.length === 0 && csvEvents.length === 0 && (
                  <div className="mt-3 p-3 bg-yellow-600/20 border border-yellow-500/30 rounded">
                    <p className="text-sm text-yellow-200">
                      ⚠️ No events found for <strong>{filters.city}</strong>. Try:
                    </p>
                    <ul className="mt-2 ml-4 text-xs text-yellow-300 list-disc">
                      <li>Check if the city name is spelled correctly</li>
                      <li>Try a different city or remove the city filter</li>
                      <li>Check the backend console logs for filtering details</li>
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Event Results */}
            {searchType === "events" && (
              <>
                <EventsSection
                  title="🎟 Ticketmaster Events"
                  events={ticketmasterEvents}
                  provider="Ticketmaster"
                />
                <EventsSection
                  title="📅 Eventbrite Events"
                  events={eventbriteEvents}
                  provider="Eventbrite"
                />
                <EventsSection
                  title="📄 European Events"
                  events={csvEvents}
                  provider="CSV"
                />
              </>
            )}
          </>
        )}
      </div>
    </main>
  );
}
