"use client";
import { useState } from "react";

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
