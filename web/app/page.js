import { getLatestEdition, listEditions } from "../lib/data";
import { SectorFeed, TopProducts } from "./components";
import Subscribe from "./subscribe";

// Render fresh from the DB on every request — new editions appear instantly.
export const dynamic = "force-dynamic";

// Freshness signal: catches a frozen site at a glance. If the pipeline's quality
// gate blocks a run (or the job fails), the live edition_date stops advancing —
// this turns amber, then red, so a stale state is obvious.
function freshness(dateStr) {
  const ed = new Date(`${dateStr}T00:00:00Z`);
  const now = new Date();
  const today = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
  const days = Math.round((today - ed) / 86400000);
  if (Number.isNaN(days)) return { color: "#64748b", dot: "⚪", label: "updated —" };
  if (days <= 0) return { color: "#16a34a", dot: "🟢", label: "Live · updated today" };
  if (days === 1) return { color: "#d97706", dot: "🟡", label: "Updated yesterday" };
  return { color: "#dc2626", dot: "🔴", label: `Stale · last updated ${days} days ago` };
}

export default async function Home() {
  const edition = await getLatestEdition();
  const editions = await listEditions();

  if (!edition) {
    return (
      <main>
        <div className="card">
          <p>No editions yet. Run <code>python pipeline/run.py</code>.</p>
        </div>
      </main>
    );
  }

  const c = edition.counts || {};
  const fresh = freshness(edition.edition_date);
  return (
    <main>
      <div className="topbar">
        <div>
          <span className={`badge ${edition.status === "approved" ? "approved" : "pending"}`}>
            {edition.status === "approved" ? "Published" : "Latest"}
          </span>{" "}
          <strong>{edition.edition_date}</strong>
          <span className="muted">
            {" "}· {c.heroes} deep-dives · {c.sectors} sectors
          </span>
          <span
            title="Editions refresh every 6 hours. If this shows amber or red, the latest run didn't publish (blocked by the quality gate or a failed job) and you're seeing the last good edition."
            style={{
              display: "inline-flex", alignItems: "center", gap: 6, marginLeft: 10,
              padding: "2px 10px", borderRadius: 999, fontSize: 12, fontWeight: 600,
              color: fresh.color, border: `1px solid ${fresh.color}33`,
              background: `${fresh.color}14`, whiteSpace: "nowrap",
            }}
          >
            <span aria-hidden>{fresh.dot}</span>
            {fresh.label}
          </span>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <a className="allnews-btn" href="/creator">📈 Creator trends</a>
          <a className="allnews-btn" href="/editions">🗂 View all editions</a>
          <a className="allnews-btn" href={`/all-news/${edition.edition_date}`}>
            🔍 Deep Dive — All News ({c.all_news})
          </a>
        </div>
      </div>

      <TopProducts products={edition.top_products} />

      <SectorFeed sectors={edition.sectors} />

      <Subscribe />

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Past editions</h3>
        <div className="editions-list">
          {editions.map((e) => (
            <a key={e.edition_date} href={`/edition/${e.edition_date}`}>
              <strong>{e.edition_date}</strong> — {e.subject?.replace("APPROVAL REQUIRED: ", "")}
            </a>
          ))}
        </div>
      </div>
    </main>
  );
}
