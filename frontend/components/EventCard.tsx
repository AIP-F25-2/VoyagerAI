import { EventItem } from "@/lib/api";
import styles from "./EventCard.module.css";
import AddToItinerary from "./AddToItinerary";

interface Props {
  event: EventItem;
}

export default function EventCard({ event }: Props) {
  return (
    <div className={styles.card}>
      <div className={styles.title}>{event.title}</div>

      <div className={styles.metaChips}>
        {event.date && (
          <span className={styles.chip}>
            <span className={styles.chipLabel}>Date</span>
            {event.date}
          </span>
        )}
        {event.time && (
          <span className={styles.chip}>
            <span className={styles.chipLabel}>Time</span>
            {event.time}
          </span>
        )}
        {event.price && (
          <span className={styles.chip}>
            <span className={styles.chipLabel}>Price</span>
            {event.price}
          </span>
        )}
        {event.city && (
          <span className={styles.chip}>
            <span className={styles.chipLabel}>City</span>
            {event.city}
          </span>
        )}
      </div>

      <div className={styles.detailsGrid}>
        {event.venue && (
          <div className={styles.detailRow}>
            <span className={styles.detailKey}>Venue</span>
            <span className={styles.detailVal}>{event.venue}</span>
          </div>
        )}
        {event.place && (
          <div className={styles.detailRow}>
            <span className={styles.detailKey}>Place</span>
            <span className={styles.detailVal}>{event.place}</span>
          </div>
        )}
      </div>

      <div className={styles.actions}>
        {event.url && (
          <a href={event.url} target="_blank" rel="noopener noreferrer" className={styles.viewBtn}>
            View
          </a>
        )}
        <AddToItinerary
          itemType="event"
          itemData={{
            title: event.title,
            description: `${event.venue ? `Venue: ${event.venue}` : ''}${event.place ? `, Place: ${event.place}` : ''}`,
            date: event.date,
            time: event.time,
            location: event.venue || event.place,
            price: event.price ? parseFloat(event.price.replace(/[^0-9.-]+/g, '')) : undefined,
            url: event.url
          }}
        />
      </div>
    </div>
  );
}

