"use client";
import { useState } from "react";
import EventCard, { EventCardEvent } from "./EventCard";
import ItineraryPanel from "./ItineraryPanel";

export default function EventsSection({
  title,
  events,
  provider,
}: {
  title: string;
  events: any[];
  provider: string;
}) {
  // pagination (unchanged)
  const itemsPerPage = 6;
  const [currentPage, setCurrentPage] = useState(1);
  const totalPages = Math.ceil(events.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const visible = events.slice(startIndex, startIndex + itemsPerPage);

  // itinerary
  const [selected, setSelected] = useState<EventCardEvent | null>(null);

  return (
    <section className="my-10">
      <h2 className="text-2xl font-bold mb-4 text-white/90">{title}</h2>

      {events.length === 0 ? (
        <p className="text-gray-400 text-sm">No {provider} events found.</p>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {visible.map((ev) => (
              <EventCard key={ev.id} event={ev} provider={provider} onPlan={(e) => setSelected(e)} />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-4 my-16">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className={`px-4 py-2 rounded-lg font-semibold ${
                  currentPage === 1
                    ? "border border-neutral-900 text-gray-600 cursor-not-allowed"
                    : "border border-blue-900 text-white hover:shadow-[0_0_20px_rgba(59,130,246,0.4)]"
                }`}
              >
                ⮜ Previous
              </button>

              <span className="text-gray-300 text-sm">Page {currentPage} of {totalPages}</span>

              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className={`px-4 py-2 rounded-lg font-semibold ${
                  currentPage === totalPages
                    ? "border border-neutral-900 text-gray-600 cursor-not-allowed"
                    : "border border-blue-900 text-white hover:shadow-[0_0_20px_rgba(59,130,246,0.4)]"
                }`}
              >
                Next ⮞
              </button>
            </div>
          )}
        </>
      )}

      {selected && (
        <ItineraryPanel
          event={{
            id: selected.id,
            name: selected.name,
            city: selected._embedded?.venues?.[0]?.city?.name,
            lat: selected._embedded?.venues?.[0]?.location?.latitude
              ? Number(selected._embedded.venues[0].location.latitude)
              : undefined,
            lon: selected._embedded?.venues?.[0]?.location?.longitude
              ? Number(selected._embedded.venues[0].location.longitude)
              : undefined,
            startDate: selected.dates?.start?.localDate,
          }}
          onClose={() => setSelected(null)}
        />
      )}
    </section>
  );
}
