// "use client";
// import { useEffect, useState } from "react";
// import SearchBar from "@/components/ui/SearchBar";
// import EventsSection from "@/components/ui/EventsSection";
// import { MusicalNoteIcon, TrophyIcon, TicketIcon, SparklesIcon } from "@heroicons/react/24/solid";

// export default function HomePage() {
//   const [ticketmasterEvents, setTicketmasterEvents] = useState<any[]>([]);
//   const [eventbriteEvents, setEventbriteEvents] = useState<any[]>([]);
//   const [loading, setLoading] = useState(false);
//   const [error, setError] = useState<string | null>(null);
//   const [query, setQuery] = useState("");

//   const loadEvents = async (search: string) => {
//     setLoading(true);
//     setError(null);
//     try {
//       const url = search ? `/api/events?q=${encodeURIComponent(search)}` : `/api/events`;
//       const res = await fetch(url);
//       if (!res.ok) throw new Error("Backend unavailable or API error");
//       const data = await res.json();
//       setTicketmasterEvents(data.ticketmaster || []);
//       setEventbriteEvents(data.eventbrite || []);
//     } catch (err: any) {
//       setError(err.message || "Failed to fetch events");
//       setTicketmasterEvents([]);
//       setEventbriteEvents([]);
//     } finally {
//       setLoading(false);
//     }
//   };

//   useEffect(() => {
//     loadEvents(query);
//   }, []);

//   const handleSearch = (e: React.FormEvent) => {
//     e.preventDefault();
//     loadEvents(query);
//   };

//   const categories = [
//     { label: "Concerts", icon: MusicalNoteIcon },
//     { label: "Sports", icon: TrophyIcon },
//     { label: "Theater", icon: TicketIcon },
//     { label: "Festivals", icon: SparklesIcon },
//   ];

//   return (
//     <main className="min-h-screen text-white select-none">
//       {/* Hero Section */}
//       <section className="relative w-full py-16 text-center rounded-4xl glass-dark shadow-glow mx-auto max-w-6xl mt-10">
//         <h1 className="text-5xl font-extrabold tracking-tight mb-4 drop-shadow-lg">
//           Discover Amazing Events
//         </h1>
//         <p className="max-w-2xl mx-auto text-lg text-gray-200 opacity-90">
//           Find concerts, sports, theater shows, and local events from Ticketmaster & Eventbrite.
//           Plus get hotel and travel recommendations all in one place.
//         </p>

//         {/* Search Bar */}
//         <div className="mt-8 max-w-3xl mx-auto glass-light p-4 rounded-2xl shadow-md border border-white/20">
//           <SearchBar query={query} setQuery={setQuery} onSearch={handleSearch} />
//         </div>

//         {/* Quick Categories */}
//         <div className="flex flex-wrap justify-center gap-4 mt-8">
//           {categories.map((cat) => (
//             <button
//               key={cat.label}
//               className="group flex items-center gap-2 px-6 py-2 rounded-xl glass-light
//               hover:bg-blue-600/40 hover:shadow-glow hover:cursor-pointer hover:scale-102
//               transition-all duration-300"
//               onClick={() => loadEvents(cat.label)}
//             >
//               <cat.icon className="h-5 w-5 text-neutral-300 group-hover:text-white transition" />
//               <span className="text-neutral-300 font-medium group-hover:text-white">{cat.label}</span>
//             </button>
//           ))}
//         </div>
//       </section>

//       {/* Results */}
//       <div className="mx-auto max-w-6xl px-4 py-10">
//         {loading && <p className="p-4 text-gray-300 text-lg font-medium">⏳ Loading events...</p>}
//         {error && <p className="p-4 text-red-500 font-medium">❌ {error}</p>}

//         {!loading && !error && (
//           <>
//             <EventsSection
//               title="Ticketmaster Events"
//               events={ticketmasterEvents}
//               provider="Ticketmaster"
//             />
//             <EventsSection
//               title="Eventbrite Events"
//               events={eventbriteEvents}
//               provider="Eventbrite"
//             />
//           </>
//         )}
//       </div>
//     </main>
//   );
// }


"use client";
import { useEffect, useState } from "react";
import SearchBar from "@/components/ui/SearchBar";
import EventsSection from "@/components/ui/EventsSection";
import { MusicalNoteIcon, TrophyIcon, TicketIcon, SparklesIcon } from "@heroicons/react/24/solid";

export default function HomePage() {
  const [ticketmasterEvents, setTicketmasterEvents] = useState<any[]>([]);
  const [eventbriteEvents, setEventbriteEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [city, setCity] = useState("");

  // Get user's location using Geolocation + reverse geocoding
  const fetchUserCity = async () => {
    if (!navigator.geolocation) return;

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;
        try {
          const geoRes = await fetch(
            `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${latitude}&longitude=${longitude}&localityLanguage=en`
          );
          const geoData = await geoRes.json();
          if (geoData.city) setCity(geoData.city);
          else if (geoData.locality) setCity(geoData.locality);
        } catch (err) {
          console.warn("Geolocation lookup failed:", err);
        }
      },
      () => console.warn("User denied location access.")
    );
  };

  const loadEvents = async (search: string, detectedCity = "") => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (search) params.append("q", search);
      if (detectedCity) params.append("city", detectedCity);

      const res = await fetch(`/api/events?${params.toString()}`);
      if (!res.ok) throw new Error("Backend unavailable or API error");
      const data = await res.json();
      setTicketmasterEvents(data.ticketmaster || []);
      setEventbriteEvents(data.eventbrite || []);
    } catch (err: any) {
      setError(err.message || "Failed to fetch events");
      setTicketmasterEvents([]);
      setEventbriteEvents([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserCity();
  }, []);

  useEffect(() => {
    if (city) {
      loadEvents(query, city);
    } else {
      loadEvents(query); // fallback without location
    }
  }, [city]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadEvents(query, city);
  };

  const categories = [
    { label: "Concerts", icon: MusicalNoteIcon },
    { label: "Sports", icon: TrophyIcon },
    { label: "Theater", icon: TicketIcon },
    { label: "Festivals", icon: SparklesIcon },
  ];

  return (
    <main className="min-h-screen text-white">
      {/* Hero Section */}
      <section className="w-full py-16 text-center">
        <h1 className="text-4xl font-extrabold mb-4">
          Discover Events Around You
        </h1>
        <p className="text-gray-300 mb-6">
          Find concerts, sports, theater shows, and more near{" "}
          <span className="text-blue-400 font-semibold">{city || "your area"}</span>.
        </p>

        {/* SearchBar */}
        <div className="max-w-3xl mx-auto mb-6">
          <SearchBar query={query} setQuery={setQuery} onSearch={handleSearch} />
        </div>

        {/* Category Buttons */}
        <div className="flex flex-wrap justify-center gap-4">
          {categories.map((cat) => (
            <button
              key={cat.label}
              className="group flex items-center gap-2 px-6 py-2 bg-white/20 backdrop-blur-md rounded-lg text-white hover:bg-blue-600/40 transition-all duration-300 hover:cursor-pointer"
              onClick={() => loadEvents(cat.label, city)}
            >
              <cat.icon className="h-5 w-5 text-white group-hover:text-white" />
              <span>{cat.label}</span>
            </button>
          ))}
        </div>
      </section>

      {/* Results */}
      <div className="mx-auto max-w-6xl px-4 py-10">
        {loading && (
          <p className="text-gray-400 text-lg text-center">⏳ Loading events near you...</p>
        )}
        {error && <p className="text-red-400 text-center">{error}</p>}
        {!loading && !error && (
          <>
            <EventsSection
              title="🎟 Ticketmaster Events"
              events={ticketmasterEvents}
              provider="Ticketmaster"
            />
            <EventsSection
              title="📅 Eventbrite Events"
              events={eventbriteEvents}
              provider="Eventbrite"
            />
          </>
        )}
      </div>
    </main>
  );
}
