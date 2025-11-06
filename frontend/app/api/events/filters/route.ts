import { NextResponse } from "next/server";

export async function GET(req: Request) {
  try {
    const res = await fetch(`http://127.0.0.1:5001/api/events/filters`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching filter options:", error);
    return NextResponse.json({ success: false, error: "Failed to fetch filter options" }, { status: 500 });
  }
}
