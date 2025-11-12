import { NextResponse } from "next/server";
import { API_BASE_URL } from "@/lib/apiConfig";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const email = url.searchParams.get("email") || "";

  try {
    const res = await fetch(`${API_BASE_URL}/api/subscription/status?email=${encodeURIComponent(email)}`);
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Failed to fetch subscription status" },
      { status: 500 }
    );
  }
}
