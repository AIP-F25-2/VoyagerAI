"use client";
import { useState } from "react";

export default function SearchBar({
  query,
  setQuery,
  onSearch,
  searchType,
  onSearchTypeChange,
}: {
  query: string;
  setQuery: (q: string) => void;
  onSearch: (e: React.FormEvent) => void;
  searchType?: "events" | "hotels";
  onSearchTypeChange?: (type: "events" | "hotels") => void;
}) {
  const [internalSearchType, setInternalSearchType] = useState<"events" | "hotels">("events");
  
  const currentSearchType = searchType || internalSearchType;
  const handleSearchTypeChange = onSearchTypeChange || setInternalSearchType;

  return (
    <div className="w-full">
      {/* Search Type Toggle */}
      <div className="flex justify-center mb-4">
        <div className="glass-light p-1 rounded-xl border border-white/10">
          <button
            type="button"
            onClick={() => handleSearchTypeChange("events")}
            className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
              currentSearchType === "events"
                ? "bg-blue-500 text-white shadow-lg"
                : "text-gray-300 hover:text-white"
            }`}
          >
            🎟️ Events
          </button>
          <button
            type="button"
            onClick={() => handleSearchTypeChange("hotels")}
            className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
              currentSearchType === "hotels"
                ? "bg-blue-500 text-white shadow-lg"
                : "text-gray-300 hover:text-white"
            }`}
          >
            🏨 Hotels
          </button>
        </div>
      </div>

      {/* Search Form */}
      <form
        onSubmit={onSearch}
        className="flex flex-col sm:flex-row items-center gap-3 glass-light p-3 rounded-2xl border border-white/10 shadow-lg"
      >
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={
            currentSearchType === "events"
              ? "Search events by city, artist, or event..."
              : "Search hotels by city (e.g., Mumbai, Delhi, Bangalore)..."
          }
          className="flex-1 px-4 py-3 rounded-xl bg-white/10 text-white placeholder-gray-300
          focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
        <button
          type="submit"
          className="px-6 py-3 text-white rounded-xl font-bold hover:cursor-pointer transition"
          style={{
            background: 'linear-gradient(135deg, #0088ff, #6a5cff)',
            boxShadow: '0 8px 22px rgba(0,136,255,0.25)'
          }}
        >
          {currentSearchType === "events" ? "🔍 Search Events" : "🏨 Search Hotels"}
        </button>
      </form>

      {/* Quick Hotel Cities */}
      {currentSearchType === "hotels" && (
        <div className="mt-4 text-center">
          <p className="text-gray-300 text-sm mb-2">Popular destinations:</p>
          <div className="flex flex-wrap justify-center gap-2">
            {["Toronto", "London", "Paris", "Berlin", "Mumbai"].map((city) => (
              <button
                key={city}
                type="button"
                onClick={() => {
                  setQuery(city);
                  onSearch(new Event('submit') as any);
                }}
                className="px-3 py-1 text-xs bg-white/10 text-gray-300 rounded-full hover:bg-blue-500/30 hover:text-white transition-all duration-200"
              >
                {city}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
