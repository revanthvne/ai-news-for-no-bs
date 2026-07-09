import { NextResponse } from "next/server";
import { SUPABASE_URL, SUPABASE_ANON as ANON } from "../../../lib/supabase-config";

export async function POST(req) {
  let email;
  try {
    ({ email } = await req.json());
  } catch {
    return NextResponse.json({ ok: false }, { status: 400 });
  }
  if (!email || !/^[^@]+@[^@]+\.[^@]+$/.test(email)) {
    return NextResponse.json({ ok: false, error: "invalid email" }, { status: 400 });
  }

  // If Supabase is configured, store it. Otherwise accept and no-op
  // (so the form works in local/demo mode).
  if (SUPABASE_URL && ANON) {
    try {
      const r = await fetch(`${SUPABASE_URL}/rest/v1/subscribers`, {
        method: "POST",
        headers: {
          apikey: ANON,
          Authorization: `Bearer ${ANON}`,
          "Content-Type": "application/json",
          Prefer: "resolution=ignore-duplicates",
        },
        body: JSON.stringify({ email }),
      });
      if (!r.ok && r.status !== 409) {
        return NextResponse.json({ ok: false }, { status: 500 });
      }
    } catch {
      return NextResponse.json({ ok: false }, { status: 500 });
    }
  }
  return NextResponse.json({ ok: true });
}
