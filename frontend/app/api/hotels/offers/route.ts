// app/api/hotels/offers/route.ts
import { NextResponse } from "next/server";
import { amadeusGet } from "@/lib/amadeus";

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const hotelIds = searchParams.get("hotelIds");           // comma-separated
    const checkInDate = searchParams.get("checkInDate");     // YYYY-MM-DD
    const checkOutDate = searchParams.get("checkOutDate");   // YYYY-MM-DD
    const adults = searchParams.get("adults") || "1";
    const currency = searchParams.get("currency") || process.env.NEXT_PUBLIC_DEFAULT_CURRENCY || "CAD";

    if (!hotelIds || !checkInDate || !checkOutDate) {
      return NextResponse.json({ error: "hotelIds, checkInDate, checkOutDate are required" }, { status: 400 });
    }

    const data = await amadeusGet("/v3/shopping/hotel-offers", {
      hotelIds,
      checkInDate,
      checkOutDate,
      adults,
      currency,
      bestRateOnly: "true",
    });

    return NextResponse.json(data);
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
