"use client";

import { useState } from "react";
import styles from "./HotelsPlanner.module.css";

export default function HotelsPlanner() {
  const [city, setCity] = useState("");
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");
  const [guests, setGuests] = useState(2);

  const onSearch = () => {
    // Placeholder for future integration with hotels API
    // Intentionally no-op for now
    console.log({ city, checkIn, checkOut, guests });
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
    </div>
  );
}

