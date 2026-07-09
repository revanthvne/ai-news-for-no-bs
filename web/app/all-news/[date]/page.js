import { getEdition } from "../../../lib/data";

export const dynamic = "force-dynamic";

const EMOJI = {
  AI: "🧠", Semiconductors: "🔩", Robotics: "🤖", eVTOL: "🚁",
  Drones: "🛸", Hardware: "📱", Stocks: "📈", "Open Source": "🐙",
};

export default async function AllNews({ params }) {
  const edition = await getEdition(params.date);
  if (!edition) {
    return (
      <main>
        <div className="card">Edition {params.date} not found.</div>
        <a href="/">← Back</a>
      </main>
    );
  }
  // group all_news by sector, in edition sector order
  const order = (edition.sectors || []).map((s) => s.sector);
  const grouped = {};
  for (const it of edition.all_news || []) {
    (grouped[it.sector] = grouped[it.sector] || []).push(it);
  }

  return (
    <main>
      <p style={{ marginTop: 16 }}>
        <a href={`/edition/${edition.edition_date}`}>← Back to the edition</a>
      </p>
      <h1 style={{ fontSize: 24, marginBottom: 2 }}>🔍 Deep Dive — All News</h1>
      <div className="muted" style={{ marginBottom: 12 }}>
        {edition.edition_date} · {edition.all_news?.length} stories · ★ = deep-dive hero
      </div>

      {order.map((sector) => (
        <section key={sector}>
          <h2 className="sector-head">
            {EMOJI[sector] || "•"} {sector}
            <span className="sector-count">· {(grouped[sector] || []).length}</span>
          </h2>
          {(grouped[sector] || []).map((it, i) => (
            <div key={i} className="allnews-row">
              <a href={(it.source_links || [])[0]} target="_blank" rel="noreferrer" className="allnews-link">
                <span className="star">{it.kind === "hero" ? "★" : "·"}</span> {it.headline}
              </a>{" "}
              <span className={`cred cred-${(it.credibility || "low").toLowerCase()}`}>
                {it.source_name}
              </span>
              {it.one_liner ? <div className="allnews-sub">{it.one_liner}</div> : null}
            </div>
          ))}
        </section>
      ))}
    </main>
  );
}
