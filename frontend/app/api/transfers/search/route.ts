// app/api/transfers/search/route.ts
import { NextResponse } from "next/server";
import { amadeusGet } from "@/lib/amadeus";

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);

    const startLatitude = searchParams.get("startLatitude");
    const startLongitude = searchParams.get("startLongitude");
    const endLatitude = searchParams.get("endLatitude");
    const endLongitude = searchParams.get("endLongitude");
    const departureDateTime = searchParams.get("departureDateTime"); // ISO, e.g. 2025-11-05T10:00:00

    if (!startLatitude || !startLongitude || !endLatitude || !endLongitude || !departureDateTime) {
      return NextResponse.json(
        { error: "startLatitude, startLongitude, endLatitude, endLongitude, departureDateTime are required" },
        { status: 400 }
      );
    }

    const params: Record<string, string> = {
      startLatitude,
      startLongitude,
      endLatitude,
      endLongitude,
      departureDateTime,
      passengers: searchParams.get("passengers") || "1",
      currencyCode: searchParams.get("currencyCode") || process.env.NEXT_PUBLIC_DEFAULT_CURRENCY || "CAD",
    };

    const data = await amadeusGet("/v1/shopping/transfer-offers", params);
    return NextResponse.json(data);
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
