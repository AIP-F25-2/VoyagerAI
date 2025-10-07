"use client";
import Image from "next/image";
import { useState } from "react";

type EventCardProps = {
  event: any;
  provider: string;
};

export default function EventCard({ event, provider }: EventCardProps) {
  const venue = event._embedded?.venues?.[0];
  const image = event.images?.[0]?.url || "/placeholder.jpg";

  return (
    <div
      className="p-4 rounded-2xl
      bg-gradient-to-b from-neutral-900 via-blue-950 to-black text-white border-2 border-neutral-900
      hover:bg-gradient-to-b hover:from-black hover:via-black hover:to-blue-950 hover:text-white hover:scale-102 hover:glass-light hover:border-blue-950
      duration-300 transition"
    >
      <Image
        src={image}
        alt={event.name}
        width={500}
        height={300}
        className="w-full h-56 object-cover rounded-lg mb-3"
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
    </div>
  );
}
