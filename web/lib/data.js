// Data access layer.
// Priority: Supabase (if configured) -> local static JSON in public/editions/.
// This means the site renders real content with ZERO backend setup.
import fs from "node:fs";
import path from "node:path";
import { SUPABASE_URL, SUPABASE_ANON } from "./supabase-config";

function editionsDir() {
  return path.join(process.cwd(), "public", "editions");
}

function readLocal(file) {
  try {
    const p = path.join(editionsDir(), file);
    return JSON.parse(fs.readFileSync(p, "utf8"));
  } catch {
    return null;
  }
}

async function supabaseGet(query) {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/${query}`, {
    headers: { apikey: SUPABASE_ANON, Authorization: `Bearer ${SUPABASE_ANON}` },
    // Always read the DB fresh — new editions must appear immediately.
    cache: "no-store",
  });
  if (!res.ok) return null;
  return res.json();
}

export async function getLatestEdition() {
  if (SUPABASE_URL && SUPABASE_ANON) {
    const rows = await supabaseGet(
      "editions?status=in.(approved,published)&order=edition_date.desc&limit=1"
    );
    if (rows && rows[0]) return rows[0].payload;
  }
  return readLocal("latest.json");
}

// Build-time list of edition dates (used by generateStaticParams).
export function listEditionDates() {
  try {
    return fs
      .readdirSync(editionsDir())
      .filter((f) => /^\d{4}-\d{2}-\d{2}\.json$/.test(f))
      .map((f) => f.replace(".json", ""));
  } catch {
    return [];
  }
}

export async function getEdition(date) {
  if (SUPABASE_URL && SUPABASE_ANON) {
    const rows = await supabaseGet(`editions?edition_date=eq.${date}&limit=1`);
    if (rows && rows[0]) return rows[0].payload;
  }
  return readLocal(`${date}.json`);
}

export async function listEditions() {
  if (SUPABASE_URL && SUPABASE_ANON) {
    const rows = await supabaseGet(
      "editions?status=in.(approved,published)&order=edition_date.desc&select=edition_date,subject,status"
    );
    if (rows) return rows;
  }
  // Local fallback: list JSON files in public/editions/
  try {
    return fs
      .readdirSync(editionsDir())
      .filter((f) => /^\d{4}-\d{2}-\d{2}\.json$/.test(f))
      .sort()
      .reverse()
      .map((f) => {
        const e = readLocal(f);
        return {
          edition_date: f.replace(".json", ""),
          subject: e?.subject || "",
          status: e?.status || "pending_approval",
        };
      });
  } catch {
    return [];
  }
}
