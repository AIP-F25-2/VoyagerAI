import { NextResponse } from "next/server";
import { API_BASE_URL } from "@/lib/apiConfig";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const query = url.searchParams.get("q") || "";  // Don't default to "Toronto" - let backend handle it
  const city = url.searchParams.get("city") || "";
  const limit = url.searchParams.get("limit") || "1000";  // Increased from 50 to 1000

  // Proxy the request to Flask
  const params = new URLSearchParams();
  if (query) params.set("q", query);  // Only add query if provided
  if (city) params.set("city", city);
  if (limit) params.set("limit", limit);
  
  const res = await fetch(`${API_BASE_URL}/api/events?${params.toString()}`);
  const data = await res.json();

  return NextResponse.json(data);
}
