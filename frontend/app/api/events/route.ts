import { NextResponse } from "next/server";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const query = url.searchParams.get("q") || "Toronto";

  // Proxy the request to Flask
  const res = await fetch(`http://127.0.0.1:5000/api/events?q=${query}`);
  const data = await res.json();

  return NextResponse.json(data);
}
