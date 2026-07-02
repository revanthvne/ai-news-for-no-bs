import { getEdition, listEditionDates } from "../../../lib/data";
import { SectorFeed } from "../../components";

export const revalidate = 3600;

export function generateStaticParams() {
  return listEditionDates().map((date) => ({ date }));
}

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
        <a href="/">← All editions</a>
        <a className="allnews-btn" href={`/all-news/${edition.edition_date}`}>
          🔍 All News ({c.all_news})
        </a>
      </div>
      <h1 style={{ fontSize: 22 }}>Daily AI Short — {edition.edition_date}</h1>
      <SectorFeed sectors={edition.sectors} />
    </main>
  );
}
