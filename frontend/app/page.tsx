"use client";
import { useEffect, useState } from "react";

export default function HomePage() {
  const [ticketmasterEvents, setTicketmasterEvents] = useState<any[]>([]);
  const [eventbriteEvents, setEventbriteEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("Toronto");

  const loadEvents = async (search: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/events?q=${encodeURIComponent(search)}`);
      if (!res.ok) throw new Error("Backend unavailable or API error");
      const data = await res.json();

      setTicketmasterEvents(data.ticketmaster || []);
      setEventbriteEvents(data.eventbrite || []);

      if (data.errors?.ticketmaster) {
        console.error("Ticketmaster Error:", data.errors.ticketmaster);
      }
      if (data.errors?.eventbrite) {
        console.error("Eventbrite Error:", data.errors.eventbrite);
      }

    } catch (err: any) {
      setError(err.message || "Failed to fetch events");
      setTicketmasterEvents([]);
      setEventbriteEvents([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents(query);
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) loadEvents(query);
  };

  const renderCard = (event: any, provider: string) => {
    const venue = event.venue || event._embedded?.venues?.[0];
    const image =
      event.logo?.url || event.images?.[0]?.url || "/placeholder.jpg";

    return (
      <div
        key={event.id}
        className="p-4 border rounded-xl shadow bg-gray-800 hover:shadow-lg transition flex flex-col"
      >
        <img
          src={image}
          alt={event.name.text || event.name}
          className="w-full h-48 object-cover rounded-md mb-3"
        />
        <h2 className="font-bold text-lg mb-2 text-white">
          {event.name.text || event.name}
        </h2>
        <p className="text-gray-300 mb-1">
          {event.start?.local || event.dates?.start?.localDate}
        </p>
        {venue && (
          <p className="text-gray-400 mb-3">
            📍 {venue.name}, {venue.city?.name || venue.address?.localized_address_display}
          </p>
        )}
        <a
          href={event.url}
          target="_blank"
          rel="noreferrer"
          className="mt-auto inline-block px-5 py-2 bg-gray-300 text-gray-700 font-medium rounded-md hover:bg-blue-900 hover:text-white transition"
        >
          🎟 Buy Tickets ({provider})
        </a>
      </div>
    );
  };

  return (
    <main className="min-h-screen bg-gray-900 p-6">
      <div className="mx-auto max-w-6xl">
        <form
          onSubmit={handleSearch}
          className="mb-8 flex flex-col sm:flex-row gap-3"
        >
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search events..."
            className="flex-1 p-2 border rounded-lg shadow-sm bg-white text-gray-900 focus:outline-none focus:ring-1 focus:ring-blue-900"
          />
          <button
            type="submit"
            className="px-5 py-2 font-bold bg-blue-900 text-white rounded-lg hover:bg-white hover:text-neutral-900 cursor-pointer transition"
          >
            Search
          </button>
        </form>

        {loading && <p className="p-4 text-gray-300">⏳ Loading events...</p>}
        {error && <p className="p-4 text-red-400">❌ {error}</p>}

        {!loading && !error && (
          <>
            {/* Ticketmaster */}
            <h2 className="text-xl font-bold mb-4 text-pink-400">🎟 Ticketmaster Events</h2>
            {ticketmasterEvents.length === 0 ? (
              <p className="text-gray-500 mb-6">No Ticketmaster events found.</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                {ticketmasterEvents.map((event) => renderCard(event, "Ticketmaster"))}
              </div>
            )}

            {/* Eventbrite */}
            <h2 className="text-xl font-bold mb-4 text-purple-400">📅 Eventbrite Events</h2>
            {eventbriteEvents.length === 0 ? (
              <p className="text-gray-500">No Eventbrite events found.</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {eventbriteEvents.map((event) => renderCard(event, "Eventbrite"))}
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
}
