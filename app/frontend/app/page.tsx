// "use client";
// import { useEffect, useState } from "react";
// import SearchBar from "@/components/ui/SearchBar";
// import EventsSection from "@/components/ui/EventsSection";
// import { MusicalNoteIcon, TrophyIcon, TicketIcon, SparklesIcon } from "@heroicons/react/24/solid";

// export default function HomePage() {
//   const [ticketmasterEvents, setTicketmasterEvents] = useState<any[]>([]);
//   const [eventbriteEvents, setEventbriteEvents] = useState<any[]>([]);
//   const [loading, setLoading] = useState(false);
//   const [error, setError] = useState<string | null>(null);
//   const [query, setQuery] = useState("");

//   const loadEvents = async (search: string) => {
//     setLoading(true);
//     setError(null);
//     try {
//       const url = search ? `/api/events?q=${encodeURIComponent(search)}` : `/api/events`;
//       const res = await fetch(url);
//       if (!res.ok) throw new Error("Backend unavailable or API error");
//       const data = await res.json();
//       setTicketmasterEvents(data.ticketmaster || []);
//       setEventbriteEvents(data.eventbrite || []);
//     } catch (err: any) {
//       setError(err.message || "Failed to fetch events");
//       setTicketmasterEvents([]);
//       setEventbriteEvents([]);
//     } finally {
//       setLoading(false);
//     }
//   };

//   useEffect(() => {
//     loadEvents(query);
//   }, []);

//   const handleSearch = (e: React.FormEvent) => {
//     e.preventDefault();
//     loadEvents(query);
//   };

//   const categories = [
//     { label: "Concerts", icon: MusicalNoteIcon },
//     { label: "Sports", icon: TrophyIcon },
//     { label: "Theater", icon: TicketIcon },
//     { label: "Festivals", icon: SparklesIcon },
//   ];

//   return (
//     <main className="min-h-screen text-white select-none">
//       {/* Hero Section */}
//       <section className="relative w-full py-16 text-center rounded-4xl glass-dark shadow-glow mx-auto max-w-6xl mt-10">
//         <h1 className="text-5xl font-extrabold tracking-tight mb-4 drop-shadow-lg">
//           Discover Amazing Events
//         </h1>
//         <p className="max-w-2xl mx-auto text-lg text-gray-200 opacity-90">
//           Find concerts, sports, theater shows, and local events from Ticketmaster & Eventbrite.
//           Plus get hotel and travel recommendations all in one place.
//         </p>

//         {/* Search Bar */}
//         <div className="mt-8 max-w-3xl mx-auto glass-light p-4 rounded-2xl shadow-md border border-white/20">
//           <SearchBar query={query} setQuery={setQuery} onSearch={handleSearch} />
//         </div>

//         {/* Quick Categories */}
//         <div className="flex flex-wrap justify-center gap-4 mt-8">
//           {categories.map((cat) => (
//             <button
//               key={cat.label}
//               className="group flex items-center gap-2 px-6 py-2 rounded-xl glass-light
//               hover:bg-blue-600/40 hover:shadow-glow hover:cursor-pointer hover:scale-102
//               transition-all duration-300"
//               onClick={() => loadEvents(cat.label)}
//             >
//               <cat.icon className="h-5 w-5 text-neutral-300 group-hover:text-white transition" />
//               <span className="text-neutral-300 font-medium group-hover:text-white">{cat.label}</span>
//             </button>
//           ))}
//         </div>
//       </section>

//       {/* Results */}
//       <div className="mx-auto max-w-6xl px-4 py-10">
//         {loading && <p className="p-4 text-gray-300 text-lg font-medium">⏳ Loading events...</p>}
//         {error && <p className="p-4 text-red-500 font-medium">❌ {error}</p>}

//         {!loading && !error && (
//           <>
//             <EventsSection
//               title="Ticketmaster Events"
//               events={ticketmasterEvents}
//               provider="Ticketmaster"
//             />
//             <EventsSection
//               title="Eventbrite Events"
//               events={eventbriteEvents}
//               provider="Eventbrite"
//             />
//           </>
//         )}
//       </div>
//     </main>
//   );
// }


"use client";
import { useEffect, useState } from "react";
import SearchBar from "@/components/ui/SearchBar";
import EventsSection from "@/components/ui/EventsSection";
import AdvancedFilters from "@/components/AdvancedFilters";
// Removed Recommendations component
import FlightsPlanner from "@/components/FlightsPlanner";
import HotelsPlanner from "@/components/HotelsPlanner";
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

  const loadEvents = async (search: string, detectedCity = "", appliedFilters = {}, searchMode: "events" | "hotels" = "events") => {
    setLoading(true);
    setError(null);
    try {
      if (searchMode === "hotels") {
        // Search hotels
        const params = new URLSearchParams();
        if (search) params.append("city", search);
        else if (detectedCity) params.append("city", detectedCity);
        params.append("limit", "20");

        const res = await fetch(`/api/hotels/search?${params.toString()}`);
        if (!res.ok) throw new Error("Backend unavailable or API error");
        const data = await res.json();
        setHotels(data.hotels || []);
        // Clear events when searching hotels
        setTicketmasterEvents([]);
        setEventbriteEvents([]);
        setCsvEvents([]);
      } else {
        // Search events (existing logic)
        const params = new URLSearchParams();
        if (search) params.append("q", search);
        if (detectedCity) params.append("city", detectedCity);
        
        // Add filter parameters
        Object.entries(appliedFilters).forEach(([key, value]) => {
          if (value && value !== "") {
            params.append(key, value as string);
          }
        });

        const res = await fetch(`/api/events?${params.toString()}`);
        if (!res.ok) throw new Error("Backend unavailable or API error");
        const data = await res.json();
        setTicketmasterEvents(data.ticketmaster || []);
        setEventbriteEvents(data.eventbrite || []);
        setCsvEvents(data.csv_events || []);
        // Clear hotels when searching events
        setHotels([]);
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch data");
      setTicketmasterEvents([]);
      setEventbriteEvents([]);
      setCsvEvents([]);
      setHotels([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserCity();
  }, []);

  useEffect(() => {
    if (city) {
      loadEvents(query, city, filters, searchType);
    } else {
      loadEvents(query, "", filters, searchType); // fallback without location
    }
  }, [city, filters, searchType]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadEvents(query, city, filters, searchType);
  };

  const handleFiltersChange = (newFilters: any) => {
    setFilters(newFilters);
    loadEvents(query, city, newFilters, searchType);
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

      {/* Travel Planning Section */}
      <div className="mx-auto max-w-6xl px-4 py-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-gray-800/30 rounded-2xl p-6">
            <h2 className="text-2xl font-bold mb-4 text-center">✈️ Find Flights</h2>
            <FlightsPlanner />
          </div>
          <div className="bg-gray-800/30 rounded-2xl p-6">
            <h2 className="text-2xl font-bold mb-4 text-center">🏨 Book Hotels</h2>
            <HotelsPlanner />
          </div>
        </div>
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
                              price: hotel.price_per_night ? parseFloat(hotel.price_per_night.replace(/[^0-9.-]+/g, '')) : undefined,
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
