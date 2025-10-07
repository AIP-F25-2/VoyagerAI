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
      className="flex flex-col sm:flex-row items-center gap-3 glass-light p-3 rounded-xl border border-white/10"
    >
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search by city, artist, or event..."
        className="flex-1 px-4 py-2 rounded-lg bg-white/10 text-white placeholder-gray-300
        focus:outline-none focus:ring-2 focus:ring-blue-400"
      />
      <button
        type="submit"
        className="px-6 py-2 bg-blue-900 text-white rounded-lg font-semibold
        hover:bg-blue-950 hover:cursor-pointer transition"
      >
        Search
      </button>
    </form>
  );
}
