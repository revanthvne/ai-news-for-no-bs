#!/usr/bin/env python3
"""NO BS — Daily AI Short: pipeline entry point (sector edition).

Usage:
  python run.py                 # auto: live fetch if keys exist, else today's seed
  python run.py --seed DATE     # build from researched sector files / edition_DATE.json
  python run.py --live          # force live fetch (5 per sector from free sources)
  python run.py --no-email
  python run.py --date 2026-07-01

Produces (per edition):
  output/edition-DATE.json           # structured sector edition (web/mobile read this)
  output/email-DATE.html             # APPROVAL REQUIRED email (sector layout)
  output/email-DATE.txt              # plain-text (exact spec sections)
  output/all-news-DATE.html          # the Deep Dive firehose page
  ../samples/daily-ai-short-DATE.html + all-news-DATE.html  (offline-clickable copies)
Sends email + upserts Supabase when configured.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
from pathlib import Path

import config
import email_render
import emailer
import store


def _load_seed(date: str) -> dict | None:
    combined = config.DATA_DIR / f"edition_{date}.json"
    if combined.exists():
        return json.loads(combined.read_text())
    # Assemble on the fly from per-sector research files if present.
    if (config.DATA_DIR / "sectors" / date).exists():
        import assemble
        return assemble.assemble(date, enrich=False)
    return None


SECTOR_MAP = {  # fetch categories -> the 8 edition sectors
    "AI": "AI", "Semiconductors": "Semiconductors", "Robotics": "Robotics",
    "eVTOL": "eVTOL", "Drones": "Drones", "Hardware": "Hardware",
    "Stocks": "Stocks", "Open Source": "Open Source",
}
SECTOR_ORDER = ["AI", "Semiconductors", "Robotics", "eVTOL", "Drones", "Hardware", "Stocks", "Open Source"]


def _build_live(date: str) -> dict:
    import sources, ranker, synthesize, credibility, images, assemble
    print("• Gathering candidates from free sources (RSS, HN, GitHub)...")
    cands = sources.gather_all()
    # No-fake-news gate: drop anything without a reputable source.
    cands = [c for c in cands if credibility.is_publishable([c.get("url")])]
    print(f"  {len(cands)} candidates after credibility filter")

    # group into sectors, top 5 each by rank score
    for c in cands:
        c["rank_score"] = ranker.score_story(c)
        c["sector"] = SECTOR_MAP.get(c.get("category", "AI"), "AI")
    sectors_out, all_news = [], []
    llm = config.has_llm()
    print(f"• Synthesizing deep-dives ({'LLM' if llm else 'template'} mode)...")
    for name in SECTOR_ORDER:
        group = sorted([c for c in cands if c["sector"] == name],
                       key=lambda x: x["rank_score"], reverse=True)
        heroes = []
        for c in group[:5]:
            s = synthesize.synthesize(dict(c))
            s["source_name"] = credibility.source_label(c["url"])
            s["credibility"] = credibility.rate_story([c["url"]])
            s["image_url"] = images.resolve_image(s, name, enrich=True)
            heroes.append(s)
        other = [{"headline": c["title"], "one_liner": c.get("summary", "")[:150],
                  "source_name": credibility.source_label(c["url"]),
                  "source_links": [c["url"]], "credibility": credibility.rate_story([c["url"]])}
                 for c in group[5:12]]
        if heroes:
            sectors_out.append({"sector": name, "slug": name.lower().replace(" ", "-"),
                                "heroes": heroes, "other_news": other})
            for h in heroes:
                all_news.append({"sector": name, "kind": "hero", "headline": h["headline"],
                                 "one_liner": h.get("one_liner", ""), "source_name": h.get("source_name", ""),
                                 "source_links": h.get("source_links", []), "credibility": h.get("credibility", "low"),
                                 "verdict": h.get("verdict", "")})
            for o in other:
                all_news.append({"sector": name, "kind": "other", **o})

    lead = sectors_out[0]["heroes"][0] if sectors_out else {"headline": "Daily AI Short"}
    all_stories = [h for s in sectors_out for h in s["heroes"]]
    return {
        "edition_date": date, "channel": config.CHANNEL_NAME, "generated_by": "live",
        "sectors": sectors_out, "all_news": all_news,
        "lead": {"headline": lead["headline"], "sector": sectors_out[0]["sector"] if sectors_out else ""},
        "counts": {"sectors": len(sectors_out),
                   "heroes": sum(len(s["heroes"]) for s in sectors_out),
                   "other_news": sum(len(s["other_news"]) for s in sectors_out),
                   "all_news": len(all_news)},
        "credibility_audit": credibility.audit(all_stories),
    }


def build_edition(date: str, mode: str) -> dict:
    edition = None
    if mode in ("auto", "seed"):
        edition = _load_seed(date)
        if edition:
            print(f"• Loaded sector edition for {date} "
                  f"({edition['counts']['heroes']} heroes / {edition['counts']['sectors']} sectors).")
    if edition is None:
        if mode == "seed":
            raise SystemExit(f"No seed/sector data for {date}")
        edition = _build_live(date)
    edition["edition_id"] = date
    edition["subject"] = email_render.subject(edition)
    edition["status"] = "pending_approval"
    return edition


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--seed", metavar="DATE")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--no-email", action="store_true")
    args = ap.parse_args()

    date = args.seed or args.date
    mode = "seed" if args.seed else ("live" if args.live else "auto")
    print(f"\n=== NO BS · Daily AI Short — {date} ({mode} mode) ===")
    edition = build_edition(date, mode)

    html_body = email_render.render_html(edition)
    text_body = email_render.render_text(edition)
    all_news_html = email_render.render_all_news_html(edition)
    subject = edition["subject"]
    print(f"• Subject: {subject[:80]}")
    print(f"• {edition['counts']['heroes']} heroes · {edition['counts']['all_news']} all-news · "
          f"credibility {edition['credibility_audit']}")

    # Save structured + rendered outputs
    store.save_local(edition)
    (config.OUTPUT_DIR / f"email-{date}.html").write_text(html_body)
    (config.OUTPUT_DIR / f"email-{date}.txt").write_text(text_body)
    (config.OUTPUT_DIR / f"all-news-{date}.html").write_text(all_news_html)

    samples = config.BASE_DIR.parent / "samples"; samples.mkdir(exist_ok=True)
    # Offline-clickable sample: All-News button points at the sibling file.
    sample_email = email_render.render_html(edition, all_news_link=f"all-news-{date}.html")
    (samples / f"daily-ai-short-{date}.html").write_text(sample_email)
    (samples / f"all-news-{date}.html").write_text(
        email_render.render_all_news_html(edition, back_link=f"daily-ai-short-{date}.html"))
    # web app static copy of the all-news page
    web_allnews = config.BASE_DIR.parent / "web" / "public" / "editions"
    web_allnews.mkdir(parents=True, exist_ok=True)
    (web_allnews / f"all-news-{date}.html").write_text(all_news_html)
    print("• Saved edition JSON + email + all-news page (output/, samples/, web/).")

    sb = store.push_supabase(edition)
    if not sb.get("skipped"):
        print(f"• Supabase: {sb}")

    if args.no_email:
        print("• Email skipped (--no-email).")
    else:
        res = emailer.send(subject, html_body, text_body)
        print("• Email:", "skipped (no provider) — open output/email-%s.html" % date
              if res.get("skipped") else res)
    print("=== done ===\n")
    return edition


if __name__ == "__main__":
    main()
