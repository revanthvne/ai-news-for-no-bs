import { getProduct } from "../../../lib/data";
import { Verdict } from "../../components";

export const dynamic = "force-dynamic";

function Sec({ label, children }) {
  if (!children) return null;
  return (
    <div style={{ marginTop: 18 }}>
      <div className="section-label">{label}</div>
      <div className="section-body">{children}</div>
    </div>
  );
}

export default async function ProductPage({ params }) {
  const res = await getProduct(params.slug);
  if (!res) {
    return (
      <main>
        <p style={{ marginTop: 16 }}>
          <a href="/">← Latest</a>
        </p>
        <div className="card" style={{ padding: "16px 20px" }}>
          This product review isn’t available (it may have rotated out of recent editions).
        </div>
      </main>
    );
  }
  const { product: p, edition_date } = res;
  return (
    <main>
      <p style={{ marginTop: 16 }}>
        <a href="/">← Latest</a> · <a href={`/edition/${edition_date}`}>{edition_date} edition</a>
      </p>

      <div className="card" style={{ padding: "20px 22px" }}>
        <span className="tp-cat">{p.category}</span>
        <h1 style={{ fontSize: 26, margin: "6px 0 4px", color: "#fff" }}>{p.name}</h1>
        {p.tagline ? <p className="muted" style={{ margin: 0 }}>{p.tagline}</p> : null}
        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap", marginTop: 12 }}>
          {p.rating ? <span className="prod-rating">{p.rating}/10</span> : null}
          {p.verdict ? <Verdict verdict={p.verdict} /> : null}
          <a className="tp-link" href={p.url} target="_blank" rel="noreferrer" style={{ marginTop: 0 }}>
            Visit {p.name} ↗
          </a>
        </div>
        {p.hot_take ? <p className="prod-hot">“{p.hot_take}”</p> : null}
      </div>

      <Sec label="End-to-end review">{p.deep_review}</Sec>
      <Sec label="Who should use it">{p.who_should_use}</Sec>
      <Sec label="Why it's good">{p.the_good}</Sec>
      <Sec label="Why it's bad">{p.the_bad}</Sec>
      <Sec label="What it lacks">{p.what_it_lacks}</Sec>
      <Sec label="Can AI models do it better?">{p.ai_leverage}</Sec>

      {p.experiments && p.experiments.length ? (
        <div style={{ marginTop: 18 }}>
          <div className="section-label">Experiments — what I'd build with it</div>
          <ul className="tp-exp" style={{ marginTop: 8 }}>
            {p.experiments.map((e, i) => (
              <li key={i} style={{ marginBottom: 8 }}>{e}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="footer">Reviewed by the NO BS pipeline · not financial advice.</div>
    </main>
  );
}
