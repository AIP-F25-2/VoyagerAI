"use client";
import { useState } from "react";

export default function SearchBar({
  query,
  setQuery,
  onSearch,
}: {
  query: string;
  setQuery: (q: string) => void;
  onSearch: (e: React.FormEvent) => void;
}) {
  return (
    <form
      onSubmit={onSearch}
      className="flex flex-col sm:flex-row items-center gap-3 glass-light p-3 rounded-2xl border border-white/10 shadow-lg"
    >
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search by city, artist, or event..."
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
        Search
      </button>
    </form>
  );
}
