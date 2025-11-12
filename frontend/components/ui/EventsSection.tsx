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
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-white/90">{title}</h2>
        {events.length > 0 && (
          <span className="px-3 py-1 bg-blue-600/30 border border-blue-500/50 rounded-full text-sm text-blue-200">
            {events.length} {events.length === 1 ? 'event' : 'events'}
          </span>
        )}
      </div>

      {/* No events */}
      {events.length === 0 ? (
        <div className="text-center py-12 px-6 bg-gradient-to-br from-gray-800/40 to-gray-900/40 rounded-xl border border-gray-700/50 backdrop-blur-sm">
          <div className="max-w-md mx-auto">
            <div className="mb-4">
              <svg className="w-16 h-16 mx-auto text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-300 mb-2">
              No {provider} Events Available
            </h3>
            <p className="text-sm text-gray-400 mb-6">
              We couldn't find any events matching your current search criteria.
            </p>
            
            {provider === "Eventbrite" && (
              <div className="mt-6 p-5 bg-gradient-to-br from-blue-950/30 to-blue-900/20 border border-blue-800/40 rounded-xl backdrop-blur-sm">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-blue-600/20 flex items-center justify-center">
                    <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <h4 className="text-sm font-semibold text-blue-200 mb-1.5">About Eventbrite Events</h4>
                    <p className="text-xs text-blue-300/70 leading-relaxed">
                      Eventbrite events are sourced from our database. To populate events, use the backend scraping API endpoint.
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {provider === "CSV" && (
              <div className="mt-6 p-5 bg-gradient-to-br from-green-950/30 to-green-900/20 border border-green-800/40 rounded-xl backdrop-blur-sm">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-green-600/20 flex items-center justify-center">
                    <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <h4 className="text-sm font-semibold text-green-200 mb-1.5">European Events Coverage</h4>
                    <p className="text-xs text-green-300/70 leading-relaxed mb-2">
                      Our European events database includes major cities such as Berlin, Barcelona, Paris, Rome, Madrid, Prague, Budapest, Vienna, and more.
                    </p>
                    <p className="text-xs text-gray-400 mt-3 pt-3 border-t border-green-800/30">
                      <strong className="text-green-300">Suggestions:</strong> Try adjusting your city filter or browse without location restrictions to discover available events.
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {provider === "Ticketmaster" && (
              <div className="mt-6 p-5 bg-gradient-to-br from-purple-950/30 to-purple-900/20 border border-purple-800/40 rounded-xl backdrop-blur-sm">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-purple-600/20 flex items-center justify-center">
                    <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4v-3a2 2 0 00-2-2H5z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <h4 className="text-sm font-semibold text-purple-200 mb-1.5">Ticketmaster Integration</h4>
                    <p className="text-xs text-purple-300/70 leading-relaxed">
                      Events are fetched in real-time from the Ticketmaster API. Try selecting a different location or adjusting your search parameters to find available events.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
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
                    ? "border border-neutral-950 bg-gradient-to-bl from-neutral-950 via-blue-950 to-neutral-950 text-gray-600 cursor-not-allowed"
                    : "border border-blue-950 bg-gradient-to-r from-neutral-950 via-black-950 to-blue-950 text-white hover:shadow-[0_0_20px_rgba(59,130,246,0.4)] transition-all duration-300 ease-in-out cursor-pointer"
                }`}
              >
                ⮜ &nbsp; Previous
              </button>

              <span className="text-gray-300 text-sm">
                Page {currentPage} of {totalPages}
              </span>

              <button
                onClick={handleNext}
                disabled={currentPage === totalPages}
                className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                  currentPage === totalPages
                    ? "border border-neutral-950 bg-gradient-to-br from-neutral-950 via-blue-950 to-neutral-950 text-gray-600 cursor-not-allowed"
                    : "border border-blue-950 bg-gradient-to-r from-blue-950 via-black-950 to-neutral-950 text-white hover:shadow-[0_0_20px_rgba(59,130,246,0.4)] transition-all duration-300 ease-in-out cursor-pointer"

                }`}
              >
                Next &nbsp; ⮞
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}
