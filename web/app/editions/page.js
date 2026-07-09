import { listEditions } from "../../lib/data";

export const dynamic = "force-dynamic";

export default async function AllEditions() {
  const editions = await listEditions();
  return (
    <main>
      <div className="topbar">
        <a href="/">← Latest</a>
      </div>
      <h1 style={{ fontSize: 24, marginBottom: 2 }}>All editions</h1>
      <div className="muted" style={{ marginBottom: 14 }}>
        {editions.length} edition{editions.length === 1 ? "" : "s"} · newest first
      </div>

      {editions.length === 0 ? (
        <div className="card" style={{ padding: "16px 20px" }}>No editions yet.</div>
      ) : (
        <div className="editions-list">
          {editions.map((e) => (
            <a key={e.edition_date} href={`/edition/${e.edition_date}`}>
              <span className={`badge ${e.status === "approved" || e.status === "published" ? "approved" : "pending"}`}>
                {e.edition_date}
              </span>{" "}
              {e.subject?.replace("APPROVAL REQUIRED: Daily AI Short - ", "") || "Daily AI Short"}
            </a>
          ))}
        </div>
      )}
    </main>
  );
}
