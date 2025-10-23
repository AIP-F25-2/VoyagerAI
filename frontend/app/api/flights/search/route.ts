// app/api/flights/search/route.ts
import { NextResponse } from "next/server";
import { amadeusGet } from "@/lib/amadeus";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const origin = searchParams.get("origin");
  const destination = searchParams.get("destination");
  const departureDate = searchParams.get("departureDate");
  const returnDate = searchParams.get("returnDate");

  if (!origin || !destination || !departureDate)
    return NextResponse.json({ error: "origin, destination, departureDate required" }, { status: 400 });

  const params: Record<string, string> = {
    originLocationCode: origin,
    destinationLocationCode: destination,
    departureDate,
    adults: "1",
    currencyCode: process.env.NEXT_PUBLIC_DEFAULT_CURRENCY || "CAD",
    max: "20",
  };
  if (returnDate) params.returnDate = returnDate;

  const data = await amadeusGet("/v2/shopping/flight-offers", params);
  return NextResponse.json(data);
}
