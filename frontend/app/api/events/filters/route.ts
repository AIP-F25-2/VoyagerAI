import { NextResponse } from "next/server";
import { API_BASE_URL } from "@/lib/apiConfig";

export async function GET(req: Request) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/events/filters`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching filter options:", error);
    return NextResponse.json({ success: false, error: "Failed to fetch filter options" }, { status: 500 });
  }
}
