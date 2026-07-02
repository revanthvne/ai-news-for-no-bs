"use client";
import { useState } from "react";

export default function Subscribe() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState("");

  async function submit(e) {
    e.preventDefault();
    setStatus("...");
    try {
      const r = await fetch("/api/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      setStatus(r.ok ? "Subscribed ✓" : "Something went wrong");
      if (r.ok) setEmail("");
    } catch {
      setStatus("Something went wrong");
    }
  }

  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>Get the daily NO BS short in your inbox</h3>
      <form onSubmit={submit} style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <input
          type="email"
          required
          placeholder="you@email.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <button className="sub-btn" type="submit">Subscribe</button>
        <span style={{ color: "var(--muted)" }}>{status}</span>
      </form>
    </div>
  );
}
