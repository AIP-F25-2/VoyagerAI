// app/api/activities/search/route.ts
import { NextResponse } from "next/server";
import { amadeusGet } from "@/lib/amadeus";

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);

    // Required: latitude & longitude
    const latitude = searchParams.get("latitude");
    const longitude = searchParams.get("longitude");
    if (!latitude || !longitude) {
      return NextResponse.json(
        { error: "latitude and longitude are required" },
        { status: 400 }
      );
    }

    // Pass through optional params (radius, startDate, endDate, page[limit], category, etc.)
    const params: Record<string, string> = { latitude, longitude };
    for (const [k, v] of searchParams.entries()) {
      if (k in params) continue;
      params[k] = v;
    }

    const data = await amadeusGet("/v1/shopping/activities", params);
    return NextResponse.json(data);
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
