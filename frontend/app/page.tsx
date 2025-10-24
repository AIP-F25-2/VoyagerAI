"use client";

import { useEffect, useState } from "react";
import EventsSection from "@/components/ui/EventsSection";

export default function Home() {
  const [query, setQuery] = useState("");
  const [city, setCity] = useState("Toronto");
  const [category, setCategory] = useState<"concerts"|"sports"|"theatre"|"festivals"|"">("");
  const [loading, setLoading] = useState(false);
  const [events, setEvents] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function search() {
    setLoading(true);
    setError(null);
    setEvents([]);
    try {
      // category just influences the keyword
      const kw = category === "concerts" ? "music"
                : category === "sports" ? "sports"
                : category === "theatre" ? "theatre"
                : category === "festivals" ? "festival"
                : query || "music";

      const url = `/api/events?keyword=${encodeURIComponent(kw)}&city=${encodeURIComponent(city)}&countryCode=CA&size=12`;
      const res = await fetch(url, { cache: "no-store" });
      const data = await res.json();
      if (!res.ok) {
        setError(data?.error || "API error");
        console.error("Events API details:", data?.details);
      } else {
        setEvents(data.ticketmaster || []);
      }
    } catch (e: any) {
      setError(String(e?.message || e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { search(); }, []); // first load

  return (
    <main className="mx-auto max-w-6xl p-4 md:p-8">
      <header className="text-center mb-6">
        <h1 className="text-3xl md:text-4xl font-extrabold">Discover Events Around You</h1>
        <p className="text-sm text-gray-400">Find concerts, sports, theater shows, and more near your area.</p>
      </header>

      {/* Search bar */}
      <div className="mx-auto max-w-3xl mb-4 flex gap-2">
        <input
          className="flex-1 border rounded-lg px-4 py-3 bg-neutral-800 text-white placeholder-gray-400"
          placeholder="Search by city, artist, or event…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <input
          className="w-48 border rounded-lg px-3 py-3 bg-neutral-800 text-white placeholder-gray-400"
          placeholder="City (e.g., Toronto)"
          value={city}
          onChange={(e) => setCity(e.target.value)}
        />
        <button
          onClick={search}
          className="px-5 py-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold"
        >
          Search
        </button>
      </div>

      {/* Quick categories */}
      <div className="mx-auto max-w-3xl mb-6 flex gap-2 justify-center">
        {[
          ["concerts","🎵 Concerts"],
          ["sports","🏆 Sports"],
          ["theatre","🎭 Theater"],
          ["festivals","🎉 Festivals"]
        ].map(([val,label]) => (
          <button
            key={val}
            onClick={() => setCategory(val as any)}
            className={`px-4 py-2 rounded-lg border ${category===val ? "bg-blue-600 text-white border-blue-600" : "border-neutral-700 text-gray-300"}`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Error / loading */}
      {error && <p className="text-center text-red-400 mb-4">Backend error: {error}</p>}
      {loading && <p className="text-center text-gray-400 mb-4">Loading…</p>}

      {/* Results */}
      <EventsSection title="Results" events={events} provider="Ticketmaster" />
    </main>
  );
}
