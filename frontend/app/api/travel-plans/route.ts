import { NextResponse } from "next/server";
import { API_BASE_URL } from "@/lib/apiConfig";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const user_id = url.searchParams.get("user_id");

  if (!user_id) {
    return NextResponse.json({ success: false, error: "User ID is required" }, { status: 400 });
  }

  try {
    const res = await fetch(`${API_BASE_URL}/api/itineraries?user_id=${user_id}`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : "Failed to fetch travel plans";
    return NextResponse.json({ success: false, error: errorMessage }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const res = await fetch(`${API_BASE_URL}/api/itineraries`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : "Failed to create travel plan";
    return NextResponse.json({ success: false, error: errorMessage }, { status: 500 });
  }
}
