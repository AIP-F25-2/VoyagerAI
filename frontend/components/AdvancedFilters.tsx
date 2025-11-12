"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/apiClient";

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
    date_from: "",
    date_to: ""
  });
  
  const [searchQuery, setSearchQuery] = useState("");
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    // Fetch filter options from backend
    apiClient.get<{ success: boolean; filters?: FilterOptions }>("/api/events/filters")
      .then(data => {
        if (data.success && data.filters) {
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
      date_from: "",
      date_to: ""
    };
    setFilters(clearedFilters);
    setSearchQuery("");
    onFiltersChange(clearedFilters);
    onSearch("");
  };

  // Get active filters count for badge
  const getActiveFiltersCount = () => {
    let count = 0;
    if (filters.city) count++;
    if (filters.category) count++;
    if (filters.date_from || filters.date_to) count++;
    return count;
  };

  // Get active filter labels for badges
  const getActiveFilters = () => {
    const active: Array<{ key: string; label: string; value: string }> = [];
    if (filters.city) {
      active.push({ key: "city", label: "City", value: filters.city });
    }
    if (filters.category) {
      const cat = filterOptions?.categories.find(c => c.id === filters.category);
      active.push({ key: "category", label: "Category", value: cat?.name || filters.category });
    }
    if (filters.date_from || filters.date_to) {
      const dateRange = `${filters.date_from || "..."} to ${filters.date_to || "..."}`;
      active.push({ key: "date_range", label: "Date Range", value: dateRange });
    }
    return active;
  };

  const removeFilter = (key: string) => {
    if (key === "date_range") {
      handleFilterChange("date_from", "");
      handleFilterChange("date_to", "");
    } else {
      handleFilterChange(key, "");
    }
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

      {/* Active Filters Badges */}
      {getActiveFiltersCount() > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {getActiveFilters().map((filter) => (
            <span
              key={filter.key}
              className="inline-flex items-center gap-2 px-3 py-1 bg-blue-600/30 border border-blue-500/50 rounded-full text-sm text-blue-200"
            >
              <span className="font-medium">{filter.label}:</span>
              <span>{filter.value}</span>
              <button
                onClick={() => removeFilter(filter.key)}
                className="ml-1 hover:text-red-400 transition-colors"
                title="Remove filter"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Toggle Advanced Filters */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="mb-4 text-blue-400 hover:text-blue-300 flex items-center gap-2 font-semibold"
      >
        {isExpanded ? "▼" : "▶"} Advanced Filters
        {getActiveFiltersCount() > 0 && (
          <span className="ml-2 px-2 py-0.5 bg-blue-600 rounded-full text-xs text-white">
            {getActiveFiltersCount()}
          </span>
        )}
      </button>

      {isExpanded && (
        <div className="space-y-6">
          {/* Essential Filters */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* City Filter */}
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-300">
                📍 City
              </label>
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
              <label className="block text-sm font-medium mb-2 text-gray-300">
                🎭 Category
              </label>
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
          </div>

          {/* Date Range Filter */}
          <div className="border-t border-gray-700 pt-4">
            <label className="block text-sm font-medium mb-3 text-gray-300">
              📅 Date Range
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-400 mb-1">From Date</label>
                <input
                  type="date"
                  value={filters.date_from}
                  onChange={(e) => handleFilterChange("date_from", e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 text-white"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-400 mb-1">To Date</label>
                <input
                  type="date"
                  value={filters.date_to}
                  min={filters.date_from || undefined}
                  onChange={(e) => handleFilterChange("date_to", e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500 text-white"
                />
              </div>
            </div>
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
