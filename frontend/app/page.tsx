"use client";
import { useEffect, useState } from "react";

export default function HomePage() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("Toronto");

  // Fetch events
  const loadEvents = async (search: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/events?q=${encodeURIComponent(search)}&size=10`);
      if (!res.ok) throw new Error("Backend unavailable or API error");
      const data = await res.json();
      setEvents(data._embedded?.events || []);
    } catch (err: any) {
      setError(err.message || "Failed to fetch events");
      setEvents([]);
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    loadEvents(query);
  }, []);

  // Handle search
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) loadEvents(query);
  };

  return (
    <main className="min-h-screen bg-gray-900 p-6">
      <div className="mx-auto max-w-6xl">

        {/* Search */}
        <form
          onSubmit={handleSearch}
          className="mb-8 flex flex-col sm:flex-row gap-3"
        >
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by city, artist, or event..."
            className="flex-1 p-2 border rounded-lg shadow-sm bg-white text-gray-900 focus:outline-none focus:ring-1 focus:ring-blue-600"
          />
          <button
            type="submit"
            className="px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Search
          </button>
        </form>

        {/* Loading / Error */}
        {loading && <p className="p-4 text-gray-300">⏳ Loading events...</p>}
        {error && <p className="p-4 text-red-500">❌ {error}</p>}

        {/* Results */}
        {!loading && !error && (
          <>
            {events.length === 0 ? (
              <p className="text-gray-400">No events found.</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {events.map((event) => {
                  const venue = event._embedded?.venues?.[0];
                  const image = event.images?.[0]?.url || "/placeholder.jpg"; // fallback if missing
                  return (
                    <div
                      key={event.id}
                      className="p-4 border rounded-xl shadow bg-gray-800 hover:shadow-lg transition flex flex-col"
                    >
                      {/* Event image */}
                      <img
                        src={image}
                        alt={event.name}
                        className="w-full h-48 object-cover rounded-md mb-3"
                      />

                      {/* Event title */}
                      <h2 className="font-bold text-lg mb-2 text-white">{event.name}</h2>

                      {/* Date & Time */}
                      <p className="text-gray-300 mb-1">
                        {event.dates.start.localDate}{" "}
                        {event.dates.start.localTime && `at ${event.dates.start.localTime}`}
                      </p>

                      {/* Venue */}
                      {venue && (
                        <p className="text-gray-400 mb-3">
                          📍 {venue.name}, {venue.city?.name}
                        </p>
                      )}

                      {/* CTA */}
                      <a
                        href={event.url}
                        target="_blank"
                        rel="noreferrer"
                        className="mt-auto inline-block px-5 py-2 bg-gray-300 text-gray-700 font-medium rounded-md hover:bg-blue-700 hover:text-white transition"
                      >
                        🎟 Buy Tickets
                      </a>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
}
