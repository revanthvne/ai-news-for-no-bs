// Approve / reject an edition straight from the email buttons.
// GET /approve?edition=2026-07-01&action=approve[&secret=...]
import { NextResponse } from "next/server";
import { SUPABASE_URL, SUPABASE_SERVICE as SERVICE_KEY } from "../../lib/supabase-config";

const APPROVE_SECRET = process.env.APPROVE_SECRET;

function page(title, body, color) {
  return new NextResponse(
    `<!doctype html><meta charset="utf-8">
     <body style="background:#0a0d11;color:#e8eef2;font-family:-apple-system,Arial,sans-serif;
                  display:flex;min-height:100vh;align-items:center;justify-content:center;text-align:center;">
       <div><div style="font-size:44px">${color}</div>
       <h1>${title}</h1><p style="color:#8a97a6">${body}</p>
       <a href="/" style="color:#00e0b8">← Back to NO BS</a></div>
     </body>`,
    { headers: { "content-type": "text/html; charset=utf-8" } }
  );
}

export async function GET(req) {
  const { searchParams } = new URL(req.url);
  const edition = searchParams.get("edition");
  const action = searchParams.get("action");
  const secret = searchParams.get("secret");

  if (!edition || !["approve", "reject"].includes(action)) {
    return page("Invalid request", "Missing edition or action.", "⚠️");
  }
  if (APPROVE_SECRET && secret !== APPROVE_SECRET) {
    return page("Not authorized", "Bad or missing secret.", "🔒");
  }

  const status = action === "approve" ? "approved" : "rejected";

  if (SUPABASE_URL && SERVICE_KEY) {
    try {
      const r = await fetch(
        `${SUPABASE_URL}/rest/v1/editions?edition_date=eq.${edition}`,
        {
          method: "PATCH",
          headers: {
            apikey: SERVICE_KEY,
            Authorization: `Bearer ${SERVICE_KEY}`,
            "Content-Type": "application/json",
            Prefer: "return=representation",
          },
          body: JSON.stringify({ status }),
        }
      );
      if (!r.ok) return page("Update failed", await r.text(), "⚠️");
      // Log the approval action too.
      await fetch(`${SUPABASE_URL}/rest/v1/approvals`, {
        method: "POST",
        headers: {
          apikey: SERVICE_KEY,
          Authorization: `Bearer ${SERVICE_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ action, actor: "email", edition_date: edition }),
      }).catch(() => {});
    } catch (e) {
      return page("Server error", String(e), "⚠️");
    }
  }

  return action === "approve"
    ? page(`Edition ${edition} approved`, "It’s now live on the site and will be sent to subscribers.", "✅")
    : page(`Edition ${edition} rejected`, "It won’t be published.", "🚫");
}
