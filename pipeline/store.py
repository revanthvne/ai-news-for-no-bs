"""Persist an edition to Supabase (free tier) so the web + mobile apps can read it.

Uses Supabase's REST endpoint directly (no SDK dependency required). If Supabase
isn't configured, editions are still written to pipeline/output/ as JSON, which
the web app can also read as a local fallback.
"""
from __future__ import annotations
import json
from pathlib import Path

import requests
import config


def save_local(edition: dict) -> Path:
    out = config.OUTPUT_DIR / f"edition-{edition['edition_date']}.json"
    out.write_text(json.dumps(edition, indent=2, ensure_ascii=False))
    # Also drop a copy the web app can serve statically.
    web_dir = config.BASE_DIR.parent / "web" / "public" / "editions"
    try:
        web_dir.mkdir(parents=True, exist_ok=True)
        (web_dir / f"{edition['edition_date']}.json").write_text(
            json.dumps(edition, indent=2, ensure_ascii=False))
        (web_dir / "latest.json").write_text(
            json.dumps(edition, indent=2, ensure_ascii=False))
    except Exception:
        pass
    return out


def push_supabase(edition: dict) -> dict:
    if not (config.SUPABASE_URL and config.SUPABASE_SERVICE_KEY):
        return {"ok": False, "skipped": True, "reason": "supabase not configured"}
    base = config.SUPABASE_URL.rstrip("/")
    headers = {
        "apikey": config.SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {config.SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation",
    }
    # Upsert the edition row.
    ed_row = {
        "edition_date": edition["edition_date"],
        "status": edition.get("status", "pending_approval"),
        "subject": edition.get("subject", ""),
        "payload": edition,
    }
    try:
        # upsert on the edition_date unique key so re-runs on the same day update
        # the row instead of failing with a 409 conflict.
        r = requests.post(f"{base}/rest/v1/editions?on_conflict=edition_date",
                          headers=headers, json=ed_row, timeout=30)
        ok = r.status_code < 300
        return {"ok": ok, "status": r.status_code, "body": r.text[:300]}
    except Exception as e:
        return {"ok": False, "error": str(e)}
