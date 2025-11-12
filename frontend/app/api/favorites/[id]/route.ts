import { NextResponse } from "next/server";
import { API_BASE_URL } from "@/lib/apiConfig";

export async function DELETE(
  req: Request,
  { params }: { params: { id: string } }
) {
  const { id } = params;
  const res = await fetch(`${API_BASE_URL}/api/favorites/${id}`, {
    method: "DELETE",
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
