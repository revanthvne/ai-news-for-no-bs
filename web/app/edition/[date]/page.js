import { getEdition } from "../../../lib/data";
import { SectorFeed, TopProducts } from "../../components";

export const dynamic = "force-dynamic";

export default async function EditionPage({ params }) {
  const edition = await getEdition(params.date);
  if (!edition) {
    return (
      <main>
        <div className="card">Edition {params.date} not found.</div>
        <a href="/">← Back</a>
      </main>
    );
  }
  const c = edition.counts || {};
  return (
    <main>
      <div className="topbar">
        <a href="/">← Latest</a>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <a className="allnews-btn" href="/editions">🗂 View all editions</a>
          <a className="allnews-btn" href={`/all-news/${edition.edition_date}`}>
            🔍 All News ({c.all_news})
          </a>
        </div>
      </div>
      <h1 style={{ fontSize: 22 }}>Daily AI Short — {edition.edition_date}</h1>
      <TopProducts products={edition.top_products} />
      <SectorFeed sectors={edition.sectors} />
    </main>
  );
}
