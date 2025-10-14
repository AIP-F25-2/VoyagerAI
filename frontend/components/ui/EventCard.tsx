"use client";
import Image from "next/image";
import { useMemo, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";

type EventCardProps = {
  event: any;
  provider: string;
};

export default function EventCard({ event, provider }: EventCardProps) {
  const { isAuthenticated, user } = useAuth();
  const venue = event._embedded?.venues?.[0];

  const fallback = useMemo(() => {
    const name: string = (event.name || "").toLowerCase();
    if (name.includes("opera") || name.includes("theatre") || name.includes("theater")) return "/window.svg";
    if (name.includes("concert") || name.includes("music") || name.includes("festival")) return "/vercel.svg";
    if (name.includes("museum") || name.includes("art") || name.includes("exhibition")) return "/file.svg";
    return "/globe.svg";
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
            await fetch("/api/favorites", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(body),
            });
            // naive UX: temporary text swap
            alert("Saved to Favorites");
          } catch (e) {
            alert("Failed to save");
          }
        }}
        className="mt-2 inline-block w-full text-center px-5 py-2 font-semibold rounded-lg text-white border glass-light border-neutral-800 bg-neutral-900/60 hover:bg-neutral-800/80 duration-300 transition"
      >
        ⭐ Save
      </button>
    </div>
  );
}
