import { NextResponse } from "next/server";

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
    const res = await fetch(`http://127.0.0.1:5001/api/events/reviews?${params.toString()}`);
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Failed to fetch reviews" },
      { status: 500 }
    );
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    
    const res = await fetch("http://127.0.0.1:5001/api/events/reviews", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Failed to submit review" },
      { status: 500 }
    );
  }
}
