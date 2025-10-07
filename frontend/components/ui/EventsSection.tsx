"use client";
import EventCard from "./EventCard";

type EventsSectionProps = {
  title: string;
  events: any[];
  provider: string;
};

export default function EventsSection({ title, events, provider }: EventsSectionProps) {
  return (
    <section className="my-10">
      <h2 className="text-3xl font-bold mb-4 text-white/90">{title}</h2>
      {events.length === 0 ? (
        <p className="text-gray-400">No {provider} events found.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {events.map((event) => (
            <EventCard key={event.id} event={event} provider={provider} />
          ))}
        </div>
      )}
    </section>
  );
}
