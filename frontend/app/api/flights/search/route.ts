import { NextResponse } from "next/server";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const origin = url.searchParams.get("origin") || "";
  const destination = url.searchParams.get("destination") || "";
  const departure_date = url.searchParams.get("departure_date") || "";
  const return_date = url.searchParams.get("return_date") || "";
  const adults = url.searchParams.get("adults") || "1";
  const limit = url.searchParams.get("limit") || "10";

  const params = new URLSearchParams();
  if (origin) params.set("origin", origin);
  if (destination) params.set("destination", destination);
  if (departure_date) params.set("departure_date", departure_date);
  if (return_date) params.set("return_date", return_date);
  if (adults) params.set("adults", adults);
  if (limit) params.set("limit", limit);

  const res = await fetch(`http://127.0.0.1:5000/api/flights/search?${params.toString()}`);
  const data = await res.json();
  return NextResponse.json(data);
}


