"use client";

import { useState, useEffect } from "react";

interface FilterOptions {
  cities: string[];
  venues: string[];
  categories: Array<{ id: string; name: string; icon: string }>;
  accessibility: Array<{ id: string; name: string; icon: string }>;
  time_shortcuts: Array<{ id: string; name: string; icon: string }>;
  providers: Array<{ id: string; name: string; icon: string }>;
}

interface AdvancedFiltersProps {
  onFiltersChange: (filters: any) => void;
  onSearch: (query: string) => void;
}

export default function AdvancedFilters({ onFiltersChange, onSearch }: AdvancedFiltersProps) {
  const [filters, setFilters] = useState({
    city: "",
    category: "",
    venue: "",
    when: "",
    provider: "all",
    accessibility: ""
  });
  
  const [searchQuery, setSearchQuery] = useState("");
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    // Fetch filter options from backend
    fetch("/api/events/filters")
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setFilterOptions(data.filters);
        }
      })
      .catch(err => console.error("Failed to load filters:", err));
  }, []);

  const handleFilterChange = (key: string, value: string) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const handleSearch = () => {
    onSearch(searchQuery);
  };

  const clearFilters = () => {
    const clearedFilters = {
      city: "",
      category: "",
      venue: "",
      when: "",
      provider: "all",
      accessibility: ""
    };
    setFilters(clearedFilters);
    setSearchQuery("");
    onFiltersChange(clearedFilters);
    onSearch("");
  };

  if (!filterOptions) {
    return <div className="p-4 text-center">Loading filters...</div>;
  }

  return (
    <div className="bg-gray-800/50 p-6 rounded-lg mb-6">
      {/* Search Bar */}
      <div className="mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Search by city, artist, or event..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 text-white"
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button
            onClick={handleSearch}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-semibold"
          >
            Search
          </button>
        </div>
      </div>

      {/* Toggle Advanced Filters */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="mb-4 text-blue-400 hover:text-blue-300 flex items-center gap-2"
      >
        {isExpanded ? "▼" : "▶"} Advanced Filters
      </button>

      {isExpanded && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* City Filter */}
          <div>
            <label className="block text-sm font-medium mb-2 text-gray-300">City</label>
            <select
              value={filters.city}
              onChange={(e) => handleFilterChange("city", e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 text-white"
            >
              <option value="">All Cities</option>
              {filterOptions.cities.map(city => (
                <option key={city} value={city}>{city}</option>
              ))}
            </select>
          </div>

          {/* Category Filter */}
          <div>
            <label className="block text-sm font-medium mb-2 text-gray-300">Category</label>
            <select
              value={filters.category}
              onChange={(e) => handleFilterChange("category", e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 text-white"
            >
              <option value="">All Categories</option>
              {filterOptions.categories.map(category => (
                <option key={category.id} value={category.id}>
                  {category.icon} {category.name}
                </option>
              ))}
            </select>
          </div>

          {/* Time Shortcuts */}
          <div>
            <label className="block text-sm font-medium mb-2 text-gray-300">When</label>
            <select
              value={filters.when}
              onChange={(e) => handleFilterChange("when", e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 text-white"
            >
              <option value="">Any Time</option>
              {filterOptions.time_shortcuts.map(shortcut => (
                <option key={shortcut.id} value={shortcut.id}>
                  {shortcut.icon} {shortcut.name}
                </option>
              ))}
            </select>
          </div>

          {/* Venue Filter */}
          <div>
            <label className="block text-sm font-medium mb-2 text-gray-300">Venue</label>
            <select
              value={filters.venue}
              onChange={(e) => handleFilterChange("venue", e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 text-white"
            >
              <option value="">All Venues</option>
              {filterOptions.venues.slice(0, 20).map(venue => (
                <option key={venue} value={venue}>{venue}</option>
              ))}
            </select>
          </div>

          {/* Provider Filter */}
          <div>
            <label className="block text-sm font-medium mb-2 text-gray-300">Source</label>
            <select
              value={filters.provider}
              onChange={(e) => handleFilterChange("provider", e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 text-white"
            >
              {filterOptions.providers.map(provider => (
                <option key={provider.id} value={provider.id}>
                  {provider.icon} {provider.name}
                </option>
              ))}
            </select>
          </div>

          {/* Accessibility Filter */}
          <div>
            <label className="block text-sm font-medium mb-2 text-gray-300">Accessibility</label>
            <select
              value={filters.accessibility}
              onChange={(e) => handleFilterChange("accessibility", e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 text-white"
            >
              <option value="">Any</option>
              {filterOptions.accessibility.map(access => (
                <option key={access.id} value={access.id}>
                  {access.icon} {access.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Clear Filters Button */}
      <div className="mt-4 flex justify-end">
        <button
          onClick={clearFilters}
          className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg text-white"
        >
          Clear All Filters
        </button>
      </div>
    </div>
  );
}
