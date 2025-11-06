"use client";
import Image from "next/image";
import { useMemo, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import EventSharing from "../EventSharing";

type EventCardProps = {
  event: any;
  provider: string;
};

export default function EventCard({ event, provider }: EventCardProps) {
  const { isAuthenticated, user } = useAuth();
  const venue = event._embedded?.venues?.[0];

  const fallback = useMemo(() => {
    const name: string = (event.name || "").toLowerCase();
    
    // Use Unsplash for better dummy images based on event type
    if (name.includes("opera") || name.includes("theatre") || name.includes("theater")) {
      return "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=500&h=300&fit=crop&crop=center";
    }
    if (name.includes("concert") || name.includes("music") || name.includes("festival")) {
      return "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=500&h=300&fit=crop&crop=center";
    }
    if (name.includes("museum") || name.includes("art") || name.includes("exhibition")) {
      return "https://images.unsplash.com/photo-1541961017774-22349e4a1262?w=500&h=300&fit=crop&crop=center";
    }
    if (name.includes("sports") || name.includes("game") || name.includes("match")) {
      return "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=300&fit=crop&crop=center";
    }
    if (name.includes("food") || name.includes("dinner") || name.includes("restaurant")) {
      return "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=500&h=300&fit=crop&crop=center";
    }
    if (name.includes("comedy") || name.includes("standup") || name.includes("joke")) {
      return "https://images.unsplash.com/photo-1511795409834-ef04bbd61622?w=500&h=300&fit=crop&crop=center";
    }
    
    // Default to a nice event/entertainment image
    return "https://images.unsplash.com/photo-1501281668745-f7f57925c3b4?w=500&h=300&fit=crop&crop=center";
  }, [event?.name]);

  const preferred = event.images?.[0]?.url as string | undefined;
  const [imgSrc, setImgSrc] = useState<string>(preferred || fallback);
  const title = (event?.name || "").toString();
  const providerLabel = provider;
  const imageUrlForSave = imgSrc;

  async function tryFetchRealtime() {
    try {
      if (!title) return;
      const res = await fetch(`/api/images/search?q=${encodeURIComponent(title)}`);
      const data = await res.json();
      if (data?.success && data?.image) {
        setImgSrc(data.image);
      } else {
        setImgSrc(fallback);
      }
    } catch {
      setImgSrc(fallback);
    }
  }

  return (
    <div
      className="p-4 rounded-2xl
      bg-gradient-to-b from-neutral-900 via-blue-950 to-black text-white border-2 border-neutral-900
      hover:bg-gradient-to-b hover:from-black hover:via-black hover:to-blue-950 hover:text-white hover:scale-102 hover:glass-light hover:border-blue-950
      duration-300 transition"
    >
      <Image
        src={imgSrc}
        alt={event.name}
        width={500}
        height={300}
        className="w-full h-56 object-cover rounded-lg mb-3"
        onError={() => {
          if (imgSrc !== fallback) {
            // First failure: try live fetch
            tryFetchRealtime();
          } else {
            // Already tried: stick to fallback
            setImgSrc(fallback);
          }
        }}
      />

      <h2 className="font-bold text-lg mb-1">{event.name}</h2>
      <p className="text-gray-300 mb-1">
        {event.dates?.start?.localDate || "TBA"}{" "}
        {event.dates?.start?.localTime && `at ${event.dates.start.localTime}`}
      </p>
      {venue && (
        <p className="text-gray-400 text-sm mb-3">
          📍 {venue.name}, {venue.city?.name}
        </p>
      )}

      <a
        href={event.url}
        target="_blank"
        rel="noreferrer"
        className="m-auto inline-block w-full text-center px-5 py-2
        font-semibold rounded-lg text-white border glass-light
        border-blue-950 bg-gradient-to-br from-neutral-900 via-blue-950 to-neutral-900
        hover:from-blue-950 hover:via-black hover:to-blue-950 hover:border-black
        duration-300 transition"
      >
        🎟 Buy Tickets ({provider})
      </a>
      <button
        onClick={() => {
          try {
            const d = event?.dates?.start?.localDate?.replaceAll('-', '') || ''
            const t = (event?.dates?.start?.localTime ? event.dates.start.localTime.replace(':','') + '00' : '000000')
            const ics = [
              'BEGIN:VCALENDAR',
              'VERSION:2.0',
              'PRODID:-//VoyagerAI//Events//EN',
              'BEGIN:VEVENT',
              `UID:client-${(event?.id || Math.random()).toString()}`,
              `DTSTAMP:${new Date().toISOString().replace(/[-:]/g, '').split('.')[0]}Z`,
              `DTSTART:${d}T${t}`,
              `SUMMARY:${event?.name || title}`,
              `LOCATION:${venue?.name || ''} ${venue?.city?.name || ''}`,
              `URL:${event?.url || ''}`,
              'END:VEVENT',
              'END:VCALENDAR'
            ].join('\r\n')
            const blob = new Blob([ics], { type: 'text/calendar;charset=utf-8;' })
            const url = URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = url
            link.download = `event-${event?.id || 'voyagerai'}.ics`
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            URL.revokeObjectURL(url)
          } catch {}
        }}
        className="mt-2 inline-block w-full text-center px-5 py-2 font-semibold rounded-lg text-white border glass-light border-neutral-800 bg-neutral-900/60 hover:bg-neutral-800/80 duration-300 transition"
      >
        📆 Add to Calendar
      </button>
      <div className="mt-2 flex gap-2">
        <button
          onClick={async () => {
            try {
              if (!isAuthenticated) {
                alert("Please sign in to save favorites.");
                window.location.href = "/login";
                return;
              }
              const body = {
                email: user?.email || null,
                title,
                date: event?.dates?.start?.localDate || null,
                time: event?.dates?.start?.localTime || null,
                venue: venue?.name || null,
                city: venue?.city?.name || null,
                url: event?.url || null,
                image_url: imageUrlForSave || null,
                provider: providerLabel,
              };
              const resp = await fetch("http://127.0.0.1:5001/api/favorites", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
              });
              if (resp.status === 409) {
                alert("Already saved to Favorites");
                return;
              }
              if (!resp.ok) {
                throw new Error("Failed to save");
              }
              alert("Saved to Favorites");
            } catch (e) {
              alert("Failed to save");
            }
          }}
          className="flex-1 text-center px-3 py-2 font-semibold rounded-lg text-white border glass-light border-neutral-800 bg-neutral-900/60 hover:bg-neutral-800/80 duration-300 transition"
        >
          ⭐ Save
        </button>
        
        <EventSharing
          event={{
            title,
            venue: venue?.name,
            city: venue?.city?.name,
            date: event?.dates?.start?.localDate,
            url: event?.url
          }}
          userEmail={user?.email}
        />
      </div>
    </div>
  );
}
