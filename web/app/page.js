import { getLatestEdition, listEditions } from "../lib/data";
import { SectorFeed, TopProducts } from "./components";
import Subscribe from "./subscribe";

// Refresh the homepage cache every 30 min so a fresh 6-hourly edition shows up
// quickly (a redeploy on each commit also regenerates it).
// Render fresh from the DB on every request — new editions appear instantly.
export const dynamic = "force-dynamic";

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
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
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
