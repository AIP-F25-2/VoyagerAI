// app/api/airports/search/route.ts
import { NextResponse } from "next/server";
import { amadeusGet } from "@/lib/amadeus";

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const keyword = searchParams.get("keyword");

    if (!keyword) {
      return NextResponse.json({ error: "keyword is required" }, { status: 400 });
    }

    const data = await amadeusGet("/v1/reference-data/locations", {
      subType: "AIRPORT",
      keyword,
    });

    return NextResponse.json(data);
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
