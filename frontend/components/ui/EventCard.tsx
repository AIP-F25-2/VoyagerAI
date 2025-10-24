"use client";
import Image from "next/image";

export type EventCardEvent = {
  id: string;
  name: string;
  url?: string;
  images?: { url: string }[];
  dates?: { start?: { localDate?: string; localTime?: string } };
  _embedded?: { venues?: Array<{ name?: string; city?: { name?: string }; location?: { latitude?: string; longitude?: string } }> };
};

export default function EventCard({
  event,
  provider,
  onPlan,
}: {
  event: EventCardEvent;
  provider: string;
  onPlan: (e: EventCardEvent) => void;
}) {
  const venue = event._embedded?.venues?.[0];
  const image = event.images?.[0]?.url || "/placeholder.jpg";
  const lat = venue?.location?.latitude ? Number(venue.location.latitude) : undefined;
  const lon = venue?.location?.longitude ? Number(venue.location.longitude) : undefined;

  return (
    <div className="p-4 rounded-2xl bg-gradient-to-b from-neutral-900 via-blue-950 to-black text-white border-2 border-neutral-900 hover:scale-[1.01] transition">
      <Image src={image} alt={event.name} width={500} height={300} className="w-full h-56 object-cover rounded-lg mb-3" />
      <h2 className="font-bold text-lg mb-1">{event.name}</h2>
      <p className="text-gray-300 mb-1">
        {event.dates?.start?.localDate || "TBA"} {event.dates?.start?.localTime && `at ${event.dates.start.localTime}`}
      </p>
      {venue && (
        <p className="text-gray-400 text-sm mb-3">📍 {venue.name}{venue.city?.name ? `, ${venue.city.name}` : ""}</p>
      )}

      <div className="grid grid-cols-2 gap-2">
        <a
          href={event.url}
          target="_blank"
          rel="noreferrer"
          className="inline-block text-center px-4 py-2 font-semibold rounded-lg glass-light border border-blue-950"
        >
          🎟 Buy ({provider})
        </a>

        <button
          onClick={() =>
            onPlan({
              ...event,
              _embedded: {
                venues: [
                  {
                    ...venue,
                    location: { latitude: lat?.toString(), longitude: lon?.toString() },
                  },
                ],
              },
            })
          }
          className="inline-block text-center px-4 py-2 font-semibold rounded-lg bg-blue-600/80 hover:bg-blue-600 transition"
        >
          ✈️ Plan Trip
        </button>
      </div>
    </div>
  );
}
