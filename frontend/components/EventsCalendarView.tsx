"use client";

import { useMemo, useState } from "react";
import { Calendar, momentLocalizer, View, Event as CalendarEvent } from "react-big-calendar";
import moment from "moment";
import "react-big-calendar/lib/css/react-big-calendar.css";
import AddToItinerary from "./AddToItinerary";

// Set moment locale to English (default, but explicit)
moment.locale("en");

const localizer = momentLocalizer(moment);

interface Event {
  id?: string;
  name?: string;
  title?: string;
  venue?: string;
  city?: string;
  place?: string;
  url?: string;
  price?: string;
  date?: string;
  time?: string;
  dates?: {
    start?: {
      localDate?: string;
      localTime?: string;
    };
  };
  _embedded?: {
    venues?: Array<{
      name?: string;
      city?: {
        name?: string;
      };
    }>;
  };
}

interface EventsCalendarViewProps {
  events: Event[];
  loading?: boolean;
}

interface CalendarEventWithData extends CalendarEvent {
  eventData?: Event;
}

export default function EventsCalendarView({ events, loading }: EventsCalendarViewProps) {
  const [currentView, setCurrentView] = useState<View>("month");
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);

  // Convert events to calendar format
  const calendarEvents: CalendarEventWithData[] = useMemo(() => {
    return events
      .map((event) => {
        // Extract date from various formats
        let eventDate: Date | null = null;
        let eventTime: string | null = null;

        if (event.date) {
          eventDate = new Date(event.date);
        } else if (event.dates?.start?.localDate) {
          const dateStr = event.dates.start.localDate;
          const timeStr = event.dates.start.localTime || event.time || "12:00";
          eventDate = new Date(`${dateStr}T${timeStr}`);
          eventTime = timeStr;
        }

        if (!eventDate || isNaN(eventDate.getTime())) {
          return null;
        }

        const title = event.name || event.title || "Untitled Event";
        const venue = event.venue || event._embedded?.venues?.[0]?.name || "";
        const city = event.city || event.place || event._embedded?.venues?.[0]?.city?.name || "";

        // Create end time (default to 2 hours after start)
        const endDate = new Date(eventDate);
        endDate.setHours(endDate.getHours() + 2);

        return {
          title: `${title}${venue ? ` - ${venue}` : ""}`,
          start: eventDate,
          end: endDate,
          allDay: !eventTime,
          eventData: event,
        } as CalendarEventWithData;
      })
      .filter((event): event is CalendarEventWithData => event !== null);
  }, [events]);

  const handleSelectEvent = (event: CalendarEventWithData) => {
    setSelectedEvent(event.eventData || null);
  };

  const handleNavigate = (newDate: Date) => {
    setCurrentDate(newDate);
  };

  const handleViewChange = (view: View) => {
    setCurrentView(view);
  };

  if (loading) {
    return (
      <div className="w-full rounded-lg border border-gray-700 bg-gray-800/50" style={{ height: "600px" }}>
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-400">Loading calendar...</p>
          </div>
        </div>
      </div>
    );
  }

  if (calendarEvents.length === 0) {
    return (
      <div className="w-full rounded-lg border border-gray-700 bg-gray-800/50" style={{ height: "600px" }}>
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <p className="text-4xl mb-4">📅</p>
            <p className="text-gray-400 text-lg">No events to display on calendar</p>
            <p className="text-gray-500 text-sm mt-2">Try adjusting your search or filters</p>
          </div>
        </div>
      </div>
    );
  }

  // Custom event style
  const eventStyleGetter = (event: CalendarEventWithData) => {
    const isEvent = event.eventData?.dates || event.eventData?.date;
    return {
      style: {
        backgroundColor: isEvent ? "#3b82f6" : "#10b981",
        borderColor: isEvent ? "#2563eb" : "#059669",
        color: "white",
        borderRadius: "4px",
        border: "none",
        padding: "2px 4px",
        fontSize: "12px",
      },
    };
  };

  return (
    <div className="w-full">
      {/* Calendar */}
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-4 mb-4">
        <Calendar
          localizer={localizer}
          events={calendarEvents}
          startAccessor="start"
          endAccessor="end"
          style={{ height: 600 }}
          view={currentView}
          date={currentDate}
          onNavigate={handleNavigate}
          onView={handleViewChange}
          onSelectEvent={handleSelectEvent}
          eventPropGetter={eventStyleGetter}
          popup
          className="text-white"
          formats={{
            dayFormat: "ddd D",
            weekdayFormat: "ddd",
            monthHeaderFormat: "MMMM YYYY",
            dayHeaderFormat: "dddd, MMMM D",
            dayRangeHeaderFormat: ({ start, end }) =>
              `${moment(start).format("MMM D")} - ${moment(end).format("MMM D, YYYY")}`,
          }}
        />
      </div>

      {/* Event Details Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-lg shadow-xl w-full max-w-md border border-gray-700">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-2xl font-bold text-white">
                  {selectedEvent.name || selectedEvent.title || "Event Details"}
                </h2>
                <button
                  onClick={() => setSelectedEvent(null)}
                  className="text-gray-400 hover:text-white text-2xl"
                >
                  ×
                </button>
              </div>

              <div className="space-y-3 text-gray-300">
                {selectedEvent.venue && (
                  <p>
                    <span className="font-semibold">📍 Venue:</span> {selectedEvent.venue}
                  </p>
                )}
                {selectedEvent.city && (
                  <p>
                    <span className="font-semibold">🏙️ City:</span> {selectedEvent.city}
                  </p>
                )}
                {selectedEvent.date && (
                  <p>
                    <span className="font-semibold">📅 Date:</span>{" "}
                    {new Date(selectedEvent.date).toLocaleDateString()}
                  </p>
                )}
                {selectedEvent.time && (
                  <p>
                    <span className="font-semibold">⏰ Time:</span> {selectedEvent.time}
                  </p>
                )}
                {selectedEvent.price && (
                  <p>
                    <span className="font-semibold">💰 Price:</span> {selectedEvent.price}
                  </p>
                )}
              </div>

              <div className="flex gap-3 mt-6">
                {selectedEvent.url && (
                  <a
                    href={selectedEvent.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-center transition"
                  >
                    View Event →
                  </a>
                )}
                <AddToItinerary
                  itemType="event"
                  itemData={{
                    title: selectedEvent.name || selectedEvent.title || "Event",
                    description: `${selectedEvent.venue || ""} ${selectedEvent.city || ""}`.trim(),
                    date: selectedEvent.date || selectedEvent.dates?.start?.localDate,
                    time: selectedEvent.time || selectedEvent.dates?.start?.localTime,
                    location: selectedEvent.venue || selectedEvent.city,
                    price: selectedEvent.price
                      ? Number.parseFloat(selectedEvent.price.replace(/[^0-9.-]+/g, ""))
                      : undefined,
                    url: selectedEvent.url,
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

