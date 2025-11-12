import { NextResponse } from "next/server";
import { API_BASE_URL } from "@/lib/apiConfig";

export async function PUT(req: Request, { params }: { params: { id: string; itemId: string } }) {
  try {
    const body = await req.json();
    const res = await fetch(`${API_BASE_URL}/api/itineraries/${params.id}/items/${params.itemId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ success: false, error: "Failed to update itinerary item" }, { status: 500 });
  }
}

export async function DELETE(req: Request, { params }: { params: { id: string; itemId: string } }) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/itineraries/${params.id}/items/${params.itemId}`, {
      method: 'DELETE',
    });
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ success: false, error: "Failed to delete itinerary item" }, { status: 500 });
  }
}
