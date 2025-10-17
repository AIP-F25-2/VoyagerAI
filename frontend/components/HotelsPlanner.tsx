"use client";

import { useState } from "react";
import styles from "./HotelsPlanner.module.css";
import AddToItinerary from "./AddToItinerary";

export default function HotelsPlanner() {
  const [city, setCity] = useState("");
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");
  const [guests, setGuests] = useState(2);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  const onSearch = () => {
    setLoading(true);
    setError(null);
    setResults([]);
    const params = new URLSearchParams();
    if (city) params.set("city", city);
    if (checkIn) params.set("check_in", checkIn);
    if (checkOut) params.set("check_out", checkOut);
    if (guests) params.set("guests", String(guests));

    fetch(`/api/hotels/search?${params.toString()}`)
      .then((r) => r.json())
      .then((data) => {
        if (!data.success) throw new Error(data.error || "Failed to fetch hotels");
        setResults(data.hotels || []);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  return (
    <div className={styles.card}>
      <h2 className={styles.title}>Plan your stay</h2>
      <div className={styles.grid}>
        <label className={styles.group}>
          <span>City</span>
          <input className={styles.input} value={city} onChange={(e) => setCity(e.target.value)} placeholder="e.g., Mumbai" />
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
          <input className={styles.input} type="number" min={1} max={10} value={guests} onChange={(e) => setGuests(parseInt(e.target.value || "1"))} />
        </label>
      </div>
      <div className={styles.actions}>
        <button className={styles.primaryBtn} onClick={onSearch}>Search Hotels</button>
      </div>
      {loading && <div className={styles.loading}>Searching…</div>}
      {error && <div className={styles.error}>Error: {error}</div>}
      {!loading && !error && results?.length > 0 && (
        <div className={styles.list}>
          {results.map((h) => (
            <div key={h.id} className={styles.item}>
              <div className={styles.itemHeader}>
                <div className={styles.itemTitle}>{h.name}</div>
                <div className={styles.itemPrice}>{h.price_per_night}</div>
              </div>
              <div className={styles.itemMeta}>{h.address}</div>
              <div className={styles.itemMeta}>Rating: {h.rating ?? "-"}</div>
              <div className={styles.itemActions}>
                {h.url && (
                  <a className={styles.itemLink} href={h.url} target="_blank" rel="noreferrer">View</a>
                )}
                <AddToItinerary
                  itemType="hotel"
                  itemData={{
                    title: h.name,
                    description: `Address: ${h.address}, Rating: ${h.rating ?? "N/A"}`,
                    date: h.check_in,
                    location: h.address,
                    price: h.price_per_night ? parseFloat(h.price_per_night.replace(/[^0-9.-]+/g, '')) : undefined,
                    url: h.url
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

