import { getLatestEdition } from "../../lib/data";
import { CreatorTrends } from "../components";

export const dynamic = "force-dynamic";

export default async function Creator() {
  const edition = await getLatestEdition();
  const trends = edition?.trends;

  return (
    <main>
      <p style={{ marginTop: 16 }}>
        <a href="/">← Latest edition</a>
        {edition ? <span className="muted"> · trends from {edition.edition_date}</span> : null}
      </p>
      <div className="topbar">
        <div>
          <span className="badge approved">Creator</span>{" "}
          <strong>Trends & keyword research</strong>
          <span className="muted"> · find what to make next</span>
        </div>
      </div>
      <CreatorTrends trends={trends} />
    </main>
  );
}
