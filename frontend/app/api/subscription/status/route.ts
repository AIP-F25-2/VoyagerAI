import { NextResponse } from "next/server";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const email = url.searchParams.get("email") || "";

  try {
    const res = await fetch(`http://127.0.0.1:5001/api/subscription/status?email=${encodeURIComponent(email)}`);
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: "Failed to fetch subscription status" },
      { status: 500 }
    );
  }
}
