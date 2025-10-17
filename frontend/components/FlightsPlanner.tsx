"use client";

import { useState } from "react";
import styles from "./HotelsPlanner.module.css"; // Reusing styles for consistency
import AddToItinerary from "./AddToItinerary";

export default function FlightsPlanner() {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [departureDate, setDepartureDate] = useState("");
  const [returnDate, setReturnDate] = useState("");
  const [adults, setAdults] = useState(1);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  const onSearch = () => {
    setLoading(true);
    setError(null);
    setResults([]);
    const params = new URLSearchParams();
    if (origin) params.set("origin", origin);
    if (destination) params.set("destination", destination);
    if (departureDate) params.set("departure_date", departureDate);
    if (returnDate) params.set("return_date", returnDate);
    if (adults) params.set("adults", String(adults));

    fetch(`/api/flights/search?${params.toString()}`)
      .then((r) => r.json())
      .then((data) => {
        if (!data.success) throw new Error(data.error || "Failed to fetch flights");
        setResults(data.flights || []);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  return (
    <div className={styles.card}>
      <h2 className={styles.title}>Find your flights</h2>
      <div className={styles.grid}>
        <label className={styles.group}>
          <span>From</span>
          <input 
            className={styles.input} 
            value={origin} 
            onChange={(e) => setOrigin(e.target.value.toUpperCase())} 
            placeholder="e.g., NYC" 
            maxLength={3}
          />
        </label>
        <label className={styles.group}>
          <span>To</span>
          <input 
            className={styles.input} 
            value={destination} 
            onChange={(e) => setDestination(e.target.value.toUpperCase())} 
            placeholder="e.g., LAX" 
            maxLength={3}
          />
        </label>
        <label className={styles.group}>
          <span>Departure</span>
          <input 
            className={styles.input} 
            type="date" 
            value={departureDate} 
            onChange={(e) => setDepartureDate(e.target.value)} 
          />
        </label>
        <label className={styles.group}>
          <span>Return (Optional)</span>
          <input 
            className={styles.input} 
            type="date" 
            value={returnDate} 
            onChange={(e) => setReturnDate(e.target.value)} 
          />
        </label>
        <label className={styles.group}>
          <span>Passengers</span>
          <input 
            className={styles.input} 
            type="number" 
            min={1} 
            max={9} 
            value={adults} 
            onChange={(e) => setAdults(parseInt(e.target.value || "1"))} 
          />
        </label>
      </div>
      <div className={styles.actions}>
        <button className={styles.primaryBtn} onClick={onSearch}>Search Flights</button>
      </div>
      {loading && <div className={styles.loading}>Searching flights…</div>}
      {error && <div className={styles.error}>Error: {error}</div>}
      {!loading && !error && results?.length > 0 && (
        <div className={styles.list}>
          {results.map((flight) => (
            <div key={flight.id} className={styles.item}>
              <div className={styles.itemHeader}>
                <div className={styles.itemTitle}>
                  {flight.origin} → {flight.destination}
                </div>
                <div className={styles.itemPrice}>{flight.price}</div>
              </div>
              <div className={styles.itemMeta}>
                {flight.airline && `Airline: ${flight.airline}`}
                {flight.flight_number && ` | Flight: ${flight.flight_number}`}
              </div>
              <div className={styles.itemMeta}>
                Departure: {flight.departure_date}
                {flight.return_date && ` | Return: ${flight.return_date}`}
              </div>
              <div className={styles.itemActions}>
                {flight.url && (
                  <a className={styles.itemLink} href={flight.url} target="_blank" rel="noreferrer">Book</a>
                )}
                <AddToItinerary
                  itemType="flight"
                  itemData={{
                    title: `${flight.origin} → ${flight.destination}`,
                    description: `${flight.airline ? `Airline: ${flight.airline}` : ''}${flight.flight_number ? `, Flight: ${flight.flight_number}` : ''}`,
                    date: flight.departure_date,
                    location: `${flight.origin} to ${flight.destination}`,
                    price: flight.price ? parseFloat(flight.price.replace(/[^0-9.-]+/g, '')) : undefined,
                    url: flight.url
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
