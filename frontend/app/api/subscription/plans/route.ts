import { NextResponse } from "next/server";
import { API_BASE_URL } from "@/lib/apiConfig";

export async function GET() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/subscription/plans`);
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : "Failed to fetch subscription plans";
    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500 }
    );
  }
}
