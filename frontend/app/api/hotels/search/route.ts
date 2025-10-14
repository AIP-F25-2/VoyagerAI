import { NextResponse } from "next/server";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const city = url.searchParams.get("city") || "";
  const check_in = url.searchParams.get("check_in") || "";
  const check_out = url.searchParams.get("check_out") || "";
  const guests = url.searchParams.get("guests") || "2";
  const limit = url.searchParams.get("limit") || "10";

  const params = new URLSearchParams();
  if (city) params.set("city", city);
  if (check_in) params.set("check_in", check_in);
  if (check_out) params.set("check_out", check_out);
  if (guests) params.set("guests", guests);
  if (limit) params.set("limit", limit);

  const res = await fetch(`http://127.0.0.1:5000/api/hotels/search?${params.toString()}`);
  const data = await res.json();
  return NextResponse.json(data);
}


