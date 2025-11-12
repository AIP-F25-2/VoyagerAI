import { NextResponse } from "next/server";
import { API_BASE_URL } from "@/lib/apiConfig";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const eventTitle = url.searchParams.get("event_title") || "";
  const eventDate = url.searchParams.get("event_date") || "";
  const limit = url.searchParams.get("limit") || "20";

  // Build query parameters
  const params = new URLSearchParams();
  if (eventTitle) params.set("event_title", eventTitle);
  if (eventDate) params.set("event_date", eventDate);
  if (limit) params.set("limit", limit);

  try {
    const res = await fetch(`${API_BASE_URL}/api/events/reviews?${params.toString()}`);
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : "Failed to fetch reviews";
    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500 }
    );
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    
    const res = await fetch(`${API_BASE_URL}/api/events/reviews`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : "Failed to submit review";
    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500 }
    );
  }
}
