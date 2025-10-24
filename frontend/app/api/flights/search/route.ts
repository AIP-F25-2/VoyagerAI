// app/api/flights/search/route.ts
import { NextResponse } from "next/server";
import { amadeusGet } from "@/lib/amadeus";

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const origin = searchParams.get("origin");
    const destination = searchParams.get("destination");
    const departureDate = searchParams.get("departureDate");
    const returnDate = searchParams.get("returnDate");
    const adults = searchParams.get("adults") || "1";
    const currencyCode = searchParams.get("currencyCode") || process.env.NEXT_PUBLIC_DEFAULT_CURRENCY || "CAD";
    const max = searchParams.get("max") || "20";

    if (!origin || !destination || !departureDate) {
      return NextResponse.json({ error: "origin, destination, departureDate are required" }, { status: 400 });
    }

    const params: Record<string, string> = {
      originLocationCode: origin,
      destinationLocationCode: destination,
      departureDate,
      adults,
      currencyCode,
      max,
    };
    if (returnDate) params.returnDate = returnDate;

    const data = await amadeusGet("/v2/shopping/flight-offers", params);
    return NextResponse.json(data);
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
