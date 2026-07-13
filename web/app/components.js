"use client";
import { useState, useMemo } from "react";

const SECTOR_EMOJI = {
  AI: "🧠", Semiconductors: "🔩", Robotics: "🤖", eVTOL: "🚁",
  Drones: "🛸", Hardware: "📱", Stocks: "📈", "Open Source": "🐙",
};

export function Verdict({ verdict }) {
  if (!verdict) return null;
  const key = (verdict.split(/\s|—|-/)[0] || "").toUpperCase();
  const cls = ["BUY", "USE", "WATCH", "SKIP"].includes(key) ? `v-${key}` : "v-WATCH";
  return <span className={`verdict ${cls}`}>{verdict}</span>;
}

export function CredTag({ s }) {
  const c = (s.credibility || "low").toLowerCase();
  return (
    <span className={`cred cred-${c}`}>
      {c === "high" ? "✓ " : ""}
      {s.source_name || "source"} · {c}
    </span>
  );
}

function Section({ label, children }) {
  if (!children) return null;
  return (
    <>
      <div className="section-label">{label}</div>
      <div className="section-body">{children}</div>
    </>
  );
}

function HeroCard({ s, idx }) {
  const [open, setOpen] = useState(false);
  return (
    <article className="card story">
      {s.image_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img className="story-img" src={s.image_url} alt="" />
      ) : null}
      <div className="story-body">
        <div className="pill-row">
          <Verdict verdict={s.verdict} />
          <CredTag s={s} />
        </div>
        <div className="eyebrow">Story {idx}</div>
        <h3 className="headline">{s.headline}</h3>
        <p className="oneliner">🎬 {s.one_liner}</p>
        <button className="deepdive-btn" onClick={() => setOpen((o) => !o)}>
          {open ? "▲ Hide deep dive" : "🔎 Deep Dive — full breakdown"}
        </button>
        {open && (
          <div className="deepdive">
            <div className="section-label">Source links</div>
            <div className="sources">
              {(s.source_links || []).map((l) => (
                <a key={l} href={l} target="_blank" rel="noreferrer">{l}</a>
              ))}
            </div>
            <Section label="The story">{s.story}</Section>
            <Section label="Their founding story">{s.founding_story}</Section>
            <Section label="Who should USE this">{s.who_should_use}</Section>
            <Section label="Who should PURCHASE this">{s.who_should_buy}</Section>
            <Section label="Free / better alternatives">{s.free_alternatives}</Section>
          </div>
        )}
      </div>
    </article>
  );
}

function OtherNews({ items, sector }) {
  if (!items || !items.length) return null;
  return (
    <div className="card other">
      <div className="other-title">More in {sector}</div>
      <ul>
        {items.map((o, i) => (
          <li key={i}>
            {o.headline}{" "}
            <a href={(o.source_links || [])[0]} target="_blank" rel="noreferrer">
              ↗ {o.source_name}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Sector({ sec }) {
  const [open, setOpen] = useState(true);
  return (
    <section className="sector">
      <h2 className="sector-head" onClick={() => setOpen((o) => !o)}>
        <span>
          {SECTOR_EMOJI[sec.sector] || "•"} {sec.sector}
          <span className="sector-count"> · {sec.heroes.length} deep-dives</span>
        </span>
        <span className="sector-toggle" aria-label={open ? "collapse" : "expand"}>
          {open ? "▲" : "▼"}
        </span>
      </h2>
      {open && (
        <div>
          {sec.heroes.map((s, i) => (
            <HeroCard key={s.id || i} s={s} idx={i + 1} />
          ))}
          <OtherNews items={sec.other_news} sector={sec.sector} />
        </div>
      )}
    </section>
  );
}

export function SectorFeed({ sectors }) {
  return (
    <>
      {(sectors || []).map((sec) => (
        <Sector key={sec.sector} sec={sec} />
      ))}
    </>
  );
}

function ProductCard({ p }) {
  return (
    <a className="tp-item" href={`/product/${p.slug}`}>
      <div className="tp-name">{p.name}</div>
      {p.tagline ? <div className="tp-tagline">{p.tagline}</div> : null}
      <div className="tp-meta-row">
        <span className="tp-cat">{p.category}</span>
        {p.rating ? <span className="tp-rating">{p.rating}/10</span> : null}
        {p.verdict ? <span className="tp-verdict">{p.verdict.split(/\s|—/)[0]}</span> : null}
      </div>
      {p.hot_take ? <div className="tp-hot">{p.hot_take}</div> : null}
      <div className="tp-readmore">Read expert assessment →</div>
    </a>
  );
}

export function TopProducts({ products }) {
  if (!products || !products.length) return null;
  return (
    <div className="card topproducts">
      <h3 style={{ marginTop: 0 }}>🚀 Top products launching today</h3>
      <div className="tp-grid">
        {products.map((p, i) => (
          <ProductCard key={i} p={p} />
        ))}
      </div>
    </div>
  );
}

const TREND_COLOR = { "▲ rising": "#16a34a", "▼ cooling": "#dc2626", steady: "#64748b", new: "#7c3aed" };

export function CreatorTrends({ trends }) {
  const all = (trends && trends.keywords) || [];
  const topics = (trends && trends.topics) || [];
  const [q, setQ] = useState("");
  const [sector, setSector] = useState("All");
  const [sort, setSort] = useState("volume");

  const sectors = useMemo(() => {
    const s = new Set();
    all.forEach((k) => (k.sectors || []).forEach((x) => s.add(x)));
    return ["All", ...Array.from(s).sort()];
  }, [all]);

  const rows = useMemo(() => {
    let r = all.filter((k) => k.keyword.toLowerCase().includes(q.toLowerCase()));
    if (sector !== "All") r = r.filter((k) => (k.sectors || []).includes(sector));
    const key =
      sort === "mentions" ? (k) => k.mentions
      : sort === "momentum" ? (k) => (k.delta_pct ?? -999)
      : (k) => k.volume;
    return [...r].sort((a, b) => key(b) - key(a));
  }, [all, q, sector, sort]);

  if (!all.length) {
    return (
      <div className="card">
        <h3 style={{ marginTop: 0 }}>📈 Creator trends</h3>
        <p className="muted">
          Keyword volume & ranking generate on the next pipeline run. Trigger one, then refresh.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="card">
        <h3 style={{ marginTop: 0 }}>🎯 What to make next</h3>
        <p className="muted" style={{ marginTop: 0, fontSize: 13 }}>
          Hottest keywords across {trends.source}, turned into NO BS video angles.
        </p>
        <div className="tp-grid">
          {topics.map((t, i) => (
            <div key={i} className="tp-item" style={{ cursor: "default" }}>
              <div className="tp-name">{t.title}</div>
              <div className="tp-meta-row">
                <span className="tp-cat">{t.sector}</span>
                <span className="tp-rating">vol {t.volume}</span>
                <span style={{ color: TREND_COLOR[t.trend] || "#64748b", fontSize: 12, fontWeight: 700 }}>
                  {t.trend}
                </span>
              </div>
              <div className="tp-tagline" style={{ marginTop: 6 }}>{t.angle}</div>
              {t.hook_source && t.hook_source.url ? (
                <a className="tp-readmore" href={t.hook_source.url} target="_blank" rel="noreferrer">
                  source: {t.hook_source.source || "link"} →
                </a>
              ) : null}
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>📊 Keyword volume & ranking</h3>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", margin: "8px 0 14px" }}>
          <input
            className="kw-input" placeholder="Filter keywords…" value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <select className="kw-input" value={sector} onChange={(e) => setSector(e.target.value)}>
            {sectors.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <select className="kw-input" value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="volume">Sort: Volume</option>
            <option value="mentions">Sort: Mentions</option>
            <option value="momentum">Sort: Momentum</option>
          </select>
        </div>
        <div className="kw-table-wrap">
          <table className="kw-table">
            <thead>
              <tr>
                <th>#</th><th>Keyword</th><th>Volume</th><th>Mentions</th>
                <th>Trend</th><th>Sectors</th><th>Platforms</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((k) => (
                <tr key={k.keyword}>
                  <td className="muted">{k.rank}</td>
                  <td>
                    {k.samples && k.samples[0] && k.samples[0].url ? (
                      <a href={k.samples[0].url} target="_blank" rel="noreferrer">{k.keyword}</a>
                    ) : k.keyword}
                  </td>
                  <td><strong>{k.volume}</strong></td>
                  <td>{k.mentions}</td>
                  <td style={{ color: TREND_COLOR[k.trend] || "#64748b", fontWeight: 600 }}>
                    {k.trend}{k.delta_pct != null ? ` ${k.delta_pct > 0 ? "+" : ""}${k.delta_pct}%` : ""}
                  </td>
                  <td className="muted">{(k.sectors || []).join(", ")}</td>
                  <td className="muted">{(k.platforms || []).join(", ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="muted" style={{ fontSize: 11, marginTop: 12 }}>{trends.note}</p>
      </div>
    </>
  );
}
