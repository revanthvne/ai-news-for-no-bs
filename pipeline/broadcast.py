#!/usr/bin/env python3
"""Broadcast an APPROVED edition to subscribers (email) + mobile (Expo push).

Run this AFTER you approve an edition (manually, or from a second GitHub Action
triggered when status flips to 'approved'):

    python broadcast.py --date 2026-07-01

- Email: pulls active subscribers from Supabase and sends the edition via your
  configured email provider.
- Push:  pulls push tokens from Supabase and sends an Expo push notification.
Both steps no-op cleanly if Supabase / providers aren't configured.
"""
from __future__ import annotations
import argparse
import json

import requests
import config
import email_render
import emailer


def _sb_get(path: str):
    if not (config.SUPABASE_URL and config.SUPABASE_SERVICE_KEY):
        return []
    r = requests.get(
        f"{config.SUPABASE_URL.rstrip('/')}/rest/v1/{path}",
        headers={"apikey": config.SUPABASE_SERVICE_KEY,
                 "Authorization": f"Bearer {config.SUPABASE_SERVICE_KEY}"},
        timeout=30)
    return r.json() if r.ok else []


def _load_edition(date: str) -> dict:
    f = config.OUTPUT_DIR / f"edition-{date}.json"
    if not f.exists():
        raise SystemExit(f"No built edition at {f}. Run run.py first.")
    return json.loads(f.read_text())


def email_subscribers(edition: dict) -> int:
    subs = _sb_get("subscribers?active=eq.true&select=email")
    if not subs:
        print("• No subscribers (or Supabase not configured).")
        return 0
    html_body = email_render.render_html(edition)
    text_body = email_render.render_text(edition)
    subject = edition.get("subject") or email_render.subject(edition)
    subject = subject.replace("APPROVAL REQUIRED: ", "")  # subscribers get the clean subject
    sent = 0
    for row in subs:
        res = emailer.send(subject, html_body, text_body, to=row["email"])
        sent += 1 if res.get("ok") else 0
    print(f"• Emailed {sent}/{len(subs)} subscribers.")
    return sent


def push_mobile(edition: dict) -> int:
    tokens = _sb_get("push_tokens?select=token")
    if not tokens:
        print("• No push tokens (or Supabase not configured).")
        return 0
    hero = edition["heroes"][0]
    messages = [{
        "to": t["token"],
        "title": "NO BS · Daily AI Short",
        "body": hero["headline"][:120],
        "data": {"date": edition["edition_date"]},
    } for t in tokens]
    try:
        r = requests.post("https://exp.host/--/api/v2/push/send",
                          json=messages, timeout=30,
                          headers={"Content-Type": "application/json"})
        print(f"• Expo push: {r.status_code}")
        return len(messages) if r.ok else 0
    except Exception as e:
        print(f"• Push failed: {e}")
        return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    args = ap.parse_args()
    edition = _load_edition(args.date)
    print(f"Broadcasting edition {args.date}...")
    email_subscribers(edition)
    push_mobile(edition)
    print("Done.")


if __name__ == "__main__":
    main()
