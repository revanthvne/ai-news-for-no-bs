import { NextResponse } from "next/server";
import { SUPABASE_URL, SUPABASE_ANON as ANON } from "../../../lib/supabase-config";

// Mobile app posts its Expo push token here so the pipeline can notify it.
export async function POST(req) {
  let token, platform;
  try {
    ({ token, platform } = await req.json());
  } catch {
    return NextResponse.json({ ok: false }, { status: 400 });
  }
  if (!token) return NextResponse.json({ ok: false }, { status: 400 });

  if (SUPABASE_URL && ANON) {
    try {
      await fetch(`${SUPABASE_URL}/rest/v1/push_tokens`, {
        method: "POST",
        headers: {
          apikey: ANON,
          Authorization: `Bearer ${ANON}`,
          "Content-Type": "application/json",
          Prefer: "resolution=ignore-duplicates",
        },
        body: JSON.stringify({ token, platform: platform || "web" }),
      });
    } catch {
      return NextResponse.json({ ok: false }, { status: 500 });
    }
  }
  return NextResponse.json({ ok: true });
}
