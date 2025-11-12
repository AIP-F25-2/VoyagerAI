"use client";

import { useState, useEffect } from "react";
import styles from "./HotelsPlanner.module.css";
import HotelCard from "./HotelCard";
import { searchHotels, getHotelCities, getPopularHotels, Hotel, HotelSearchResponse } from "../lib/api";

export default function HotelsPlanner() {
  const [city, setCity] = useState("Toronto");
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");
  const [guests, setGuests] = useState(2);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Hotel[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [availableCities, setAvailableCities] = useState<string[]>([]);
  const [showPopular, setShowPopular] = useState(false);

  // Load available cities on component mount
  useEffect(() => {
    getHotelCities()
      .then((data) => {
        if (data.success) {
          setAvailableCities(data.cities);
        }
      })
      .catch((e) => console.error("Failed to load cities:", e));
  }, []);

  // Auto-load Toronto hotels on component mount
  useEffect(() => {
    if (city === "Toronto") {
      onSearch();
    }
  }, [city]);

  const onSearch = async () => {
    if (!city.trim()) {
      setError("Please enter a city");
      return;
    }

    setLoading(true);
    setError(null);
    setResults([]);
    setShowPopular(false);

    try {
      const data: HotelSearchResponse = await searchHotels(city, checkIn, checkOut, guests, 20);
      if (!data.success) {
        throw new Error("Failed to fetch hotels");
      }
      setResults(data.hotels || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const onShowPopular = async () => {
    setLoading(true);
    setError(null);
    setResults([]);
    setShowPopular(true);

    try {
      const data: HotelSearchResponse = await getPopularHotels(city || undefined, 20);
      if (!data.success) {
        throw new Error("Failed to fetch popular hotels");
      }
      setResults(data.hotels || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.card}>
      <h2 className={styles.title}>🏨 Find Your Perfect Hotel</h2>
      
      {/* Search Form */}
      <div className={styles.grid}>
        <label className={styles.group}>
          <span>City</span>
          <input 
            className={styles.input} 
            value={city} 
            onChange={(e) => setCity(e.target.value)} 
            placeholder="e.g., Toronto, Mumbai, Delhi"
            list="cities"
          />
          <datalist id="cities">
            {availableCities.slice(0, 10).map((cityName) => (
              <option key={cityName} value={cityName} />
            ))}
          </datalist>
        </label>
        <label className={styles.group}>
          <span>Check-in</span>
          <input className={styles.input} type="date" value={checkIn} onChange={(e) => setCheckIn(e.target.value)} />
        </label>
        <label className={styles.group}>
          <span>Check-out</span>
          <input className={styles.input} type="date" value={checkOut} onChange={(e) => setCheckOut(e.target.value)} />
        </label>
        <label className={styles.group}>
          <span>Guests</span>
          <input className={styles.input} type="number" min={1} max={10} value={guests} onChange={(e) => setGuests(Number.parseInt(e.target.value || "1"))} />
        </label>
      </div>
      
      {/* Action Buttons */}
      <div className={styles.actions}>
        <button className={styles.primaryBtn} onClick={onSearch} disabled={loading}>
          {loading ? "Searching..." : "🔍 Search Hotels"}
        </button>
        <button className={styles.secondaryBtn} onClick={onShowPopular} disabled={loading}>
          {loading ? "Loading..." : "⭐ Popular Hotels"}
        </button>
      </div>

      {/* Status Messages */}
      {loading && <div className={styles.loading}>🔍 Searching hotels...</div>}
      {error && <div className={styles.error}>❌ Error: {error}</div>}
      
      {/* Results */}
      {!loading && !error && results?.length > 0 && (
        <div className={styles.results}>
          <div className={styles.resultsHeader}>
            <h3>{showPopular ? "⭐ Popular Hotels" : "🏨 Search Results"}</h3>
            <span className={styles.resultsCount}>{results.length} hotels found</span>
          </div>
          
          <div className={styles.list}>
            {results.map((hotel) => (
              <HotelCard key={hotel.id} hotel={hotel} />
            ))}
          </div>
        </div>
      )}
      
      {/* No Results */}
      {!loading && !error && results?.length === 0 && city && (
        <div className={styles.noResults}>
          <p>😔 No hotels found for "{city}"</p>
          <p>Try searching for a different city or check our popular hotels!</p>
        </div>
      )}
      
      {/* Available Cities Info */}
      {availableCities.length > 0 && (
        <div className={styles.citiesInfo}>
          <small>💡 Available cities: {availableCities.slice(0, 5).join(", ")}{availableCities.length > 5 && ` and ${availableCities.length - 5} more`}</small>
        </div>
      )}
    </div>
  );
}

