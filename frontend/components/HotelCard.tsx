"use client";

import { Hotel } from "../lib/api";
import AddToItinerary from "./AddToItinerary";
import styles from "./HotelCard.module.css";

interface HotelCardProps {
  hotel: Hotel;
  showAddToItinerary?: boolean;
}

export default function HotelCard({ hotel, showAddToItinerary = true }: HotelCardProps) {
  const formatPrice = (price?: string) => {
    if (!price) return "";
    return price;
  };

  const formatRating = (rating?: number) => {
    if (!rating) return null;
    return `${rating.toFixed(1)}/10`;
  };

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <div className={styles.title}>{hotel.name}</div>
        {hotel.price_per_night && (
          <div className={styles.price}>{formatPrice(hotel.price_per_night)}</div>
        )}
      </div>
      
      <div className={styles.meta}>
        <div className={styles.location}>📍 {hotel.address}</div>
        <div className={styles.city}>🏙️ {hotel.city}</div>
        {hotel.rating && (
          <div className={styles.rating}>
            ⭐ {formatRating(hotel.rating)}
            {hotel.review_count && ` (${hotel.review_count} reviews)`}
          </div>
        )}
      </div>
      
      <div className={styles.actions}>
        {hotel.url && (
          <a className={styles.link} href={hotel.url} target="_blank" rel="noreferrer">
            🔗 View on Booking.com
          </a>
        )}
        {showAddToItinerary && (
          <AddToItinerary
            itemType="hotel"
            itemData={{
              title: hotel.name,
              description: `Hotel in ${hotel.city} - ${hotel.address}`,
              date: hotel.check_in,
              location: hotel.address,
              price: hotel.price_per_night ? parseFloat(hotel.price_per_night.replace(/[^0-9.-]+/g, '')) : undefined,
              url: hotel.url
            }}
          />
        )}
      </div>
    </div>
  );
}
