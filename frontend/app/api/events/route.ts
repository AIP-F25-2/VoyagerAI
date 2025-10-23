import { NextResponse } from "next/server";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const query = url.searchParams.get("q") || "Toronto";
  const city = url.searchParams.get("city") || "";
  const limit = url.searchParams.get("limit") || "1000";  // Increased from 50 to 1000

  // Proxy the request to Flask
  const params = new URLSearchParams({ q: query });
  if (city) params.set("city", city);
  if (limit) params.set("limit", limit);
  const res = await fetch(`http://127.0.0.1:5001/api/events?${params.toString()}`);
  const data = await res.json();

  return NextResponse.json(data);
}
