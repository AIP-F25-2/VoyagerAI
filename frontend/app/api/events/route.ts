// app/api/events/route.ts
import { NextResponse } from "next/server";
export const dynamic = "force-dynamic";

function normalizeTMEvent(raw: any) {
  const v = raw?._embedded?.venues?.[0];
  const img =
    raw?.images?.find((i: any) => i.width >= 1000)?.url ||
    raw?.images?.[0]?.url;
  const pr = raw?.priceRanges?.[0];
  const cl = raw?.classifications?.[0];
  return {
    id: raw?.id,
    name: raw?.name,
    url: raw?.url,
    images: raw?.images,
    image: img,
    dates: raw?.dates,
    _embedded: raw?._embedded,
    startDate: raw?.dates?.start?.localDate,
    startTime: raw?.dates?.start?.localTime,
    venueName: v?.name,
    city: v?.city?.name,
    country: v?.country?.countryCode,
    lat: v?.location?.latitude ? Number(v.location.latitude) : undefined,
    lon: v?.location?.longitude ? Number(v.location.longitude) : undefined,
    priceMin: pr?.min,
    priceMax: pr?.max,
    currency: pr?.currency,
    segment: cl?.segment?.name,
    genre: cl?.genre?.name,
  };
}

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const keyword = searchParams.get("q") || searchParams.get("keyword") || "music";
    const city = searchParams.get("city") || "";
    const countryCode =
      searchParams.get("countryCode") ||
      process.env.NEXT_PUBLIC_DEFAULT_COUNTRY ||
      "CA";
    const size = searchParams.get("size") || "24";

    const apiKey = process.env.TICKETMASTER_API_KEY;
    if (!apiKey) {
      return NextResponse.json(
        { error: "Missing TICKETMASTER_API_KEY in frontend/.env.local" },
        { status: 500 }
      );
    }

    const tmParams = new URLSearchParams({
      apikey: apiKey,
      keyword,
      countryCode,
      size,
      sort: "date,asc",
    });
    if (city) tmParams.set("city", city);

    const url = `https://app.ticketmaster.com/discovery/v2/events.json?${tmParams.toString()}`;
    const r = await fetch(url, { cache: "no-store", headers: { Accept: "application/json" } });

    if (!r.ok) {
      const txt = await r.text();
      return NextResponse.json(
        { error: `Ticketmaster ${r.status}`, details: txt.slice(0, 600) },
        { status: 502 }
      );
    }

    const j = await r.json();
    const eventsRaw = j?._embedded?.events ?? [];
    const ticketmaster = eventsRaw.map(normalizeTMEvent);

    // Keep this shape to match your existing UI
    return NextResponse.json({ ticketmaster, eventbrite: [] });
  } catch (e: any) {
    return NextResponse.json(
      { error: "Server error", details: String(e?.message || e) },
      { status: 500 }
    );
  }
}
