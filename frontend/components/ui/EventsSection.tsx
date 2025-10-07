"use client";
import { useState } from "react";
import EventCard from "./EventCard";

type EventsSectionProps = {
  title: string;
  events: any[];
  provider: string;
};

export default function EventsSection({ title, events, provider }: EventsSectionProps) {
  // Pagination settings
  const itemsPerPage = 6;
  const [currentPage, setCurrentPage] = useState(1);

  const totalPages = Math.ceil(events.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const visibleEvents = events.slice(startIndex, startIndex + itemsPerPage);

  const handlePrev = () => {
    if (currentPage > 1) setCurrentPage((prev) => prev - 1);
  };

  const handleNext = () => {
    if (currentPage < totalPages) setCurrentPage((prev) => prev + 1);
  };

  return (
    <section className="my-10">
      <h2 className="text-2xl font-bold mb-4 text-white/90">{title}</h2>

      {/* No events */}
      {events.length === 0 ? (
        <p className="text-gray-400 text-sm">No {provider} events found.</p>
      ) : (
        <>
          {/* Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {visibleEvents.map((event) => (
              <EventCard key={event.id} event={event} provider={provider} />
            ))}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-4 my-16">
              <button
                onClick={handlePrev}
                disabled={currentPage === 1}
                className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                  currentPage === 1
                    ? "bg-gray-500/30 text-gray-400 cursor-not-allowed"
                    : "bg-blue-950/70 hover:bg-blue-950 text-white"
                }`}
              >
                ◄  &nbsp; Previous
              </button>

              <span className="text-gray-300 text-sm">
                Page {currentPage} of {totalPages}
              </span>

              <button
                onClick={handleNext}
                disabled={currentPage === totalPages}
                className={`px-4 py-2 rounded-lg font-semibold transition-all hover:cursor-pointer ${
                  currentPage === totalPages
                    ? "bg-gray-500/30 text-gray-400 cursor-not-allowed"
                    : "bg-blue-950/70 hover:bg-blue-950 text-white"
                }`}
              >
                Next &nbsp; ►
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}
