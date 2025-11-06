import { NextResponse } from "next/server";

async function fetchFromWikipedia(query: string): Promise<string | null> {
  try {
    const searchUrl = `https://en.wikipedia.org/w/rest.php/v1/search/title?q=${encodeURIComponent(query)}&limit=1`;
    const searchRes = await fetch(searchUrl, { headers: { "accept": "application/json" } });
    const search = await searchRes.json();
    const page = search?.pages?.[0];
    const title: string | undefined = page?.title;
    if (!title) return null;

    const summaryUrl = `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title)}`;
    const summaryRes = await fetch(summaryUrl, { headers: { "accept": "application/json" } });
    const summary = await summaryRes.json();
    const thumb: string | undefined = summary?.thumbnail?.source;
    return thumb || null;
  } catch {
    return null;
  }
}

export async function GET(req: Request) {
  const url = new URL(req.url);
  const q = (url.searchParams.get("q") || "").trim();
  if (!q) return NextResponse.json({ success: false, error: "q is required" }, { status: 400 });

  const image = await fetchFromWikipedia(q);
  if (!image) return NextResponse.json({ success: false, image: null });
  return NextResponse.json({ success: true, image });
}


