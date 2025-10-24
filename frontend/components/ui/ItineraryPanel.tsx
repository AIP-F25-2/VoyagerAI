"use client";

import { useEffect, useMemo, useRef, useState } from "react";

// -------------------------------
// helpers
// -------------------------------
const fmtMoney = (n?: string | number, c = "CAD") =>
  n ? new Intl.NumberFormat(undefined, { style: "currency", currency: c }).format(Number(n)) : "—";

const ymd = (d: Date | string) =>
  (typeof d === "string" ? new Date(d) : d).toISOString().slice(0, 10);

const addDays = (iso: string, n: number) => {
  const d = new Date(iso);
  d.setDate(d.getDate() + n);
  return ymd(d);
};

function gfDeepLink(origin: string, dest: string, depart: string, ret?: string) {
  // Google Flights hash format works reliably with ORG.DST.DATE* back leg
  const back = ret ? `*${dest}.${origin}.${ret}` : "";
  return `https://www.google.com/travel/flights?hl=en#flt=${origin}.${dest}.${depart}${back}`;
}

function ghDeepLinkByCoords(lat: number, lon: number, checkIn: string, checkOut: string) {
  return `https://www.google.com/travel/hotels?hl=en&checkin=${checkIn}&checkout=${checkOut}&latlng=${lat},${lon}`;
}

function ghDeepLinkByName(name: string, checkIn: string, checkOut: string, city?: string) {
  const q = encodeURIComponent(`${name}${city ? " " + city : ""}`);
  return `https://www.google.com/travel/hotels?q=${q}&checkin=${checkIn}&checkout=${checkOut}&hl=en`;
}

type Evt = { id: string; name: string; city?: string; lat?: number; lon?: number; startDate?: string };

// -------------------------------
// main component
// -------------------------------
export default function ItineraryPanel({ event, onClose }: { event: Evt; onClose: () => void }) {
  // base fields
  const [origin, setOrigin] = useState("YYZ");
  const [destCity, setDestCity] = useState(event.city || "");
  const [destIata, setDestIata] = useState("");
  const [stayNights, setStayNights] = useState(2);
  const [checkIn, setCheckIn] = useState<string>("");
  const [checkOut, setCheckOut] = useState<string>("");
  const [adults, setAdults] = useState(1);

  // data
  const [meta, setMeta] = useState<any>(null);
  const [flightsData, setFlightsData] = useState<any>(null);
  const [hotelsNearby, setHotelsNearby] = useState<any>(null);
  const [hotelOffers, setHotelOffers] = useState<any>(null);

  // ui
  const [tab, setTab] = useState<"summary" | "flights" | "hotels">("summary");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  // filters
  const [flightMax, setFlightMax] = useState<number | "">("");
  const [nonStopOnly, setNonStopOnly] = useState(false);
  const [hotelMax, setHotelMax] = useState<number | "">("");

  // initial dates (arrive day -1, depart day +stay)
  useEffect(() => {
    if (event.startDate) {
      const arrive = addDays(event.startDate, -1);
      const leave = addDays(event.startDate, stayNights);
      setCheckIn(arrive);
      setCheckOut(leave);
    }
  }, [event.startDate, stayNights]);

  // blur + esc + click-outside
  useEffect(() => {
    const html = document.documentElement;
    html.classList.add("overflow-hidden");
    const esc = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", esc);
    return () => {
      html.classList.remove("overflow-hidden");
      window.removeEventListener("keydown", esc);
    };
  }, [onClose]);

  function onBackdropClick(e: React.MouseEvent<HTMLDivElement>) {
    if (cardRef.current && !cardRef.current.contains(e.target as Node)) onClose();
  }

  // destination resolve
  async function resolveAirportFromCity() {
    if (!destCity) return;
    const r = await fetch(`/api/airports/search?keyword=${encodeURIComponent(destCity)}&subType=AIRPORT,CITY`);
    const j = await r.json();
    const code =
      j?.data?.find((x: any) => x.iataCode && (x.subType === "CITY" || x.subType === "AIRPORT"))?.iataCode || "";
    setDestIata(code);
  }

  // build itinerary (flights + hotels)
  async function build() {
    try {
      setLoading(true);
      setErr(null);
      setMeta(null);
      setFlightsData(null);
      setHotelsNearby(null);
      setHotelOffers(null);

      // must have: iata + coords + dates
      if (!destIata || !checkIn || !checkOut || !event.lat || !event.lon) {
        setErr("Missing destination/venue/dates. Make sure you set destination and the event has a venue.");
        return;
      }

      const qs = new URLSearchParams({
        userOrigin: origin,
        destination: destIata,
        venueLat: String(event.lat),
        venueLon: String(event.lon),
        eventDate: event.startDate || checkIn,
        stayNights: String(stayNights),
        adults: String(adults),
      });

      const data = await fetch(`/api/itinerary/build?${qs}`, { cache: "no-store" }).then((r) => r.json());
      if (data?.error) {
        setErr(data.error);
      }
      setMeta({
        ...data?.meta,
        checkIn,
        checkOut,
        origin,
        destIata,
      });
      setFlightsData(data?.flights);
      setHotelsNearby(data?.hotelsNearby);
      setHotelOffers(data?.hotelOffers);
      setTab("flights");
    } finally {
      setLoading(false);
    }
  }

  // reactive re-search for flights/hotels when filters change (optional lightweight)
  const filteredFlightOffers = useMemo(() => {
    const items: any[] = flightsData?.data || [];
    let out = items.slice();
    if (nonStopOnly) {
      out = out.filter((o) =>
        (o.itineraries || []).every((it: any) => (it.segments || []).length === 1)
      );
    }
    if (flightMax !== "" && !Number.isNaN(Number(flightMax))) {
      out = out.filter((o) => Number(o.price?.total) <= Number(flightMax));
    }
    out.sort((a, b) => Number(a.price?.total || 1e9) - Number(b.price?.total || 1e9));
    return out;
  }, [flightsData, flightMax, nonStopOnly]);

  const hotelCards = useMemo(() => {
    const hotels = Array.isArray(hotelsNearby?.data) ? hotelsNearby.data : [];
    const offers = Array.isArray(hotelOffers?.data) ? hotelOffers.data : [];
    // map id => best offer
    const byId: Record<string, any> = {};
    for (const o of offers) {
      const id = o.hotel?.hotelId;
      if (!id) continue;
      const first = o.offers?.[0];
      if (!byId[id] || Number(first?.price?.total) < Number(byId[id]?.price?.total || Infinity)) {
        byId[id] = first;
      }
    }

    let rows = hotels.map((h: any) => {
      const offer = byId[h.hotelId];
      return {
        id: h.hotelId,
        name: h.name || `Hotel ${h.hotelId}`,
        lat: h.geoCode?.latitude,
        lon: h.geoCode?.longitude,
        address: [ ...(h.address?.lines || []), h.address?.cityName ].filter(Boolean).join(", "),
        offer,
      };
    });

    if (hotelMax !== "" && !Number.isNaN(Number(hotelMax))) {
      rows = rows.filter((r) => !r.offer || Number(r.offer?.price?.total) <= Number(hotelMax));
    }

    rows.sort((a, b) => Number(a.offer?.price?.total || 1e9) - Number(b.offer?.price?.total || 1e9));
    return rows;
  }, [hotelsNearby, hotelOffers, hotelMax]);

  // init: guess dest IATA once
  useEffect(() => { if (!destIata && destCity) void resolveAirportFromCity(); }, []);

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 md:p-6"
      onMouseDown={onBackdropClick}
    >
      <div
        ref={cardRef}
        onMouseDown={(e) => e.stopPropagation()}
        className="w-full max-w-6xl max-h-[100vh] overflow-hidden rounded-2xl border border-white/10 bg-neutral-900 text-neutral-100 shadow-2xl
                   transition-all duration-200 ease-out animate-in fade-in zoom-in-95"
      >
        {/* header */}
        <div className="sticky top-0 z-10 flex items-center gap-3 border-b border-white/10 bg-neutral-900/80 backdrop-blur px-4 py-3">
          <h2 className="font-semibold text-base md:text-lg">
            Plan trip — <span className="text-gray-300">{event.name}</span>
          </h2>
          <button onClick={onClose} className="ml-auto rounded-lg border border-white/15 bg-white/5 px-3 py-1.5 text-sm hover:bg-white/10">
            Close
          </button>
        </div>

        {/* search bar */}
        <div className="px-4 pt-4 grid gap-2 md:grid-cols-[1fr_1fr_auto_auto_auto]">
          <input
            className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500/50"
            value={origin}
            onChange={(e) => setOrigin(e.target.value.toUpperCase())}
            placeholder="Origin IATA (e.g., YYZ)"
          />
          <div className="grid grid-cols-[1fr_auto] gap-2">
            <input
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500/50"
              value={destCity}
              onChange={(e) => setDestCity(e.target.value)}
              placeholder="Destination city (e.g., Vancouver)"
            />
            <button
              onClick={resolveAirportFromCity}
              className="rounded-lg border border-white/15 bg-white/10 px-3 py-2 text-sm hover:bg-white/20"
              title="Resolve IATA from city"
            >
              Find IATA
            </button>
          </div>
          <input
            className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500/50"
            value={destIata}
            onChange={(e) => setDestIata(e.target.value.toUpperCase())}
            placeholder="IATA (auto-filled)"
          />
          <input
            type="date"
            className="rounded-lg border border-white/10 bg-white/5 px-3 py-2"
            value={checkIn || ""}
            onChange={(e) => setCheckIn(e.target.value)}
            title="Check-in / departure date"
          />
          <input
            type="date"
            className="rounded-lg border border-white/10 bg-white/5 px-3 py-2"
            value={checkOut || ""}
            onChange={(e) => setCheckOut(e.target.value)}
            title="Check-out / return date"
          />
        </div>

        {/* build action + adults/nights */}
        <div className="px-4 pt-2 pb-1 flex items-center gap-2">
          <div className="flex items-center gap-2">
            <input
              type="number"
              min={1}
              className="w-24 rounded-lg border border-white/10 bg-white/5 px-3 py-2"
              value={adults}
              onChange={(e) => setAdults(parseInt(e.target.value || "1"))}
              placeholder="Adults"
              title="Adults"
            />
            <input
              type="number"
              min={1}
              className="w-28 rounded-lg border border-white/10 bg-white/5 px-3 py-2"
              value={stayNights}
              onChange={(e) => setStayNights(parseInt(e.target.value || "2"))}
              placeholder="Nights"
              title="Stay nights"
            />
          </div>

          <button
            className="ml-auto rounded-lg bg-blue-600 hover:bg-blue-500 px-4 py-2 font-medium disabled:opacity-50"
            onClick={build}
            disabled={!origin || !destIata || !checkIn || !checkOut || loading}
          >
            {loading ? "Building…" : "Build"}
          </button>
        </div>

        {/* tabs */}
        <div className="px-4 py-3">
          <div className="inline-flex gap-2 rounded-xl bg-white/5 p-1">
            <Tab label="Summary" active={tab === "summary"} onClick={() => setTab("summary")} />
            <Tab label="Flights" active={tab === "flights"} onClick={() => setTab("flights")} />
            <Tab label="Hotels" active={tab === "hotels"} onClick={() => setTab("hotels")} />
          </div>
        </div>

        {/* content */}
        <div className="px-4 pb-5 overflow-y-auto max-h-[65vh]">
          {err && <p className="mb-3 text-sm text-red-400">{err}</p>}

          {tab === "summary" && (
            <Summary meta={meta} />
          )}

          {tab === "flights" && (
            <>
              {/* flight filters */}
              <div className="mb-3 flex flex-wrap items-center gap-3">
                <div className="text-sm text-gray-300">Filters:</div>
                <label className="text-sm flex items-center gap-2">
                  <span className="text-gray-400">Max price</span>
                  <input
                    type="number"
                    className="w-28 rounded-lg border border-white/10 bg-white/5 px-2 py-1"
                    value={flightMax}
                    onChange={(e) => setFlightMax((e.target.value as any) || "")}
                    placeholder="e.g., 500"
                  />
                </label>
                <label className="text-sm flex items-center gap-2">
                  <input type="checkbox" checked={nonStopOnly} onChange={(e) => setNonStopOnly(e.target.checked)} />
                  Non-stop only
                </label>
                {meta?.origin && meta?.destIata && meta?.arrive && (
                  <a
                    className="ml-auto text-sm underline text-blue-400"
                    target="_blank"
                    rel="noreferrer"
                    href={gfDeepLink(meta.origin, meta.destIata, meta.arrive, meta.depart)}
                  >
                    Open on Google Flights ↗
                  </a>
                )}
              </div>

              <FlightsList offers={filteredFlightOffers} currency={meta?.currency || "CAD"} />
            </>
          )}

          {tab === "hotels" && (
            <>
              <div className="mb-3 flex flex-wrap items-center gap-3">
                <div className="text-sm text-gray-300">Filters:</div>
                <label className="text-sm flex items-center gap-2">
                  <span className="text-gray-400">Max nightly total</span>
                  <input
                    type="number"
                    className="w-32 rounded-lg border border-white/10 bg-white/5 px-2 py-1"
                    value={hotelMax}
                    onChange={(e) => setHotelMax((e.target.value as any) || "")}
                    placeholder="e.g., 200"
                  />
                </label>
                {event.lat && event.lon && checkIn && checkOut && (
                  <a
                    className="ml-auto text-sm underline text-blue-400"
                    target="_blank"
                    rel="noreferrer"
                    href={ghDeepLinkByCoords(event.lat, event.lon, checkIn, checkOut)}
                  >
                    Open area on Google Hotels ↗
                  </a>
                )}
              </div>

              <HotelsList
                rows={hotelCards}
                checkIn={checkIn}
                checkOut={checkOut}
                eventCity={event.city}
              />
            </>
          )}

          {!meta && !loading && !err && (
            <p className="text-sm text-gray-400">Fill fields and click <b>Build</b> to get live recommendations.</p>
          )}
        </div>
      </div>
    </div>
  );
}

function Tab({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} className={`px-3 py-1.5 rounded-lg text-sm transition ${active ? "bg-blue-600 text-white" : "text-gray-300 hover:bg-white/10"}`}>
      {label}
    </button>
  );
}

function Summary({ meta }: { meta: any }) {
  if (!meta) return null;
  return (
    <div className="grid gap-3">
      <div className="rounded-xl border border-white/10 bg-white/5 p-3">
        <h3 className="font-semibold mb-1">Trip window</h3>
        <p className="text-sm text-gray-300">
          Origin: <b>{meta.origin}</b> • Destination: <b>{meta.destIata}</b> • Arrive: <b>{meta.arrive}</b> •
          Depart: <b>{meta.depart}</b>
        </p>
      </div>
      <p className="text-xs text-gray-400">
        Use the tabs to view flight options and hotel offers. Click <b>Book</b> to open the provider in a new tab.
      </p>
    </div>
  );
}

function FlightsList({ offers, currency }: { offers: any[]; currency: string }) {
  if (!offers || offers.length === 0) return <p className="text-sm text-gray-400">No flight offers found.</p>;
  return (
    <div className="grid gap-3">
      {offers.slice(0, 30).map((offer, i) => {
        const price = fmtMoney(offer.price?.total, offer.price?.currency || currency);
        const itins = offer.itineraries || [];
        const out = itins[0];
        const ret = itins[1];
        const seg0 = out?.segments?.[0];
        const segLast = out?.segments?.slice(-1)[0];
        const oDep = seg0?.departure?.iataCode;
        const oArr = segLast?.arrival?.iataCode;
        const dDate = seg0?.departure?.at?.slice(0, 10);
        const rDate = ret?.segments?.[0]?.departure?.at?.slice(0, 10);
        const link = oDep && oArr && dDate ? gfDeepLink(oDep, oArr, dDate, rDate) : undefined;

        return (
          <div key={i} className="rounded-xl border border-white/10 bg-white/5 p-3">
            <div className="flex items-center gap-2">
              <div className="font-semibold text-sm">Option {i + 1}</div>
              <div className="ml-auto text-sm">{price}</div>
            </div>
            <p className="text-xs text-gray-300 mt-1">
              {oDep} → {oArr} {ret ? " (round trip)" : ""} • {offer.numberOfBookableSeats || "?"} seats
              {offer.validatingAirlineCodes?.length ? ` • ${offer.validatingAirlineCodes.join(", ")}` : ""}
              {out?.segments?.length ? ` • ${out.segments.length - 1} stops` : ""}
            </p>
            {link && (
              <a
                target="_blank"
                rel="noreferrer"
                href={link}
                className="inline-block mt-2 text-sm underline text-blue-400"
              >
                Book on Google Flights ↗
              </a>
            )}
          </div>
        );
      })}
    </div>
  );
}

function HotelsList({
  rows,
  checkIn,
  checkOut,
  eventCity,
}: {
  rows: Array<{ id: string; name: string; lat?: number; lon?: number; address?: string; offer?: any }>;
  checkIn: string;
  checkOut: string;
  eventCity?: string;
}) {
  if (!rows || rows.length === 0) return <p className="text-sm text-gray-400">No hotel offers found.</p>;

  return (
    <div className="grid gap-3">
      {rows.slice(0, 30).map((h) => {
        const total = h.offer?.price?.total;
        const cur = h.offer?.price?.currency || "CAD";
        const link =
          h.lat && h.lon
            ? ghDeepLinkByCoords(h.lat, h.lon, checkIn, checkOut)
            : ghDeepLinkByName(h.name, checkIn, checkOut, eventCity);

        return (
          <div key={h.id} className="rounded-xl border border-white/10 bg-white/5 p-3">
            <div className="flex items-start gap-2">
              <div className="font-semibold text-sm">{h.name}</div>
              <div className="ml-auto text-sm">{fmtMoney(total, cur)}</div>
            </div>
            {h.address && <p className="text-xs text-gray-300 mt-1">{h.address}</p>}
            <a
              target="_blank"
              rel="noreferrer"
              href={link}
              className="inline-block mt-2 text-sm underline text-blue-400"
            >
              Book on Google Hotels ↗
            </a>
          </div>
        );
      })}
    </div>
  );
}
