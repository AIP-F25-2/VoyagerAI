import { NextResponse } from "next/server";

export async function DELETE(
  req: Request,
  { params }: { params: { id: string } }
) {
  const { id } = params;
  const res = await fetch(`http://127.0.0.1:5001/api/favorites/${id}`, {
    method: "DELETE",
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
