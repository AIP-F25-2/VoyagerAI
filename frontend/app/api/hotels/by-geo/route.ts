// app/api/hotels/by-geo/route.ts
import { NextResponse } from "next/server";
import { amadeusGet } from "@/lib/amadeus";

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const lat = searchParams.get("lat") || searchParams.get("latitude");
    const lon = searchParams.get("lon") || searchParams.get("longitude");
    const radius = searchParams.get("radius") || "5"; // KM

    if (!lat || !lon) {
      return NextResponse.json({ error: "lat and lon are required" }, { status: 400 });
    }

    const data = await amadeusGet("/v1/reference-data/locations/hotels/by-geocode", {
      latitude: String(lat),
      longitude: String(lon),
      radius: String(radius),
      radiusUnit: "KM",
    });

    return NextResponse.json(data);
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
