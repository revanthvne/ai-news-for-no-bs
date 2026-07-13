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
import sys
from pathlib import Path

import config
import email_render
import emailer
import store


def edition_quality_ok(edition: dict):
    """True only if the edition is genuinely AI-written (not template placeholders).
    Prevents ever overwriting a good edition with identical fallback text."""
    heroes = [h for s in edition.get("sectors", []) for h in s.get("heroes", [])]
    prods = edition.get("top_products", [])

    def h_tmpl(h):
        fs = (h.get("founding_story") or "").lower()
        return ("to be verified" in fs) or ("auto-mode" in fs) or (not fs)

    def p_tmpl(p):
        dr = (p.get("deep_review") or "").lower()
        return ("written automatically" in dr) or ("cloud run" in dr) or (not dr)

    total = len(heroes) + len(prods)
    if total == 0:
        return False, "empty edition"
    bad = sum(1 for h in heroes if h_tmpl(h)) + sum(1 for p in prods if p_tmpl(p))
    real_pct = round((1 - bad / total) * 100)
    return (bad / total) <= 0.35, f"{total - bad}/{total} sections real ({real_pct}%)"


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
            s["verdict"] = email_render.normalize_verdict(s.get("verdict", ""))
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

    all_stories = [h for s in sectors_out for h in s["heroes"]]
    # Lead with the single highest-scored story across all sectors (major news wins).
    lead = max(all_stories, key=lambda h: h.get("rank_score", 0)) if all_stories \
        else {"headline": "Daily AI Short", "category": ""}
    try:
        tp = sources.top_products()
    except Exception:
        tp = []
    return {
        "edition_date": date, "channel": config.CHANNEL_NAME, "generated_by": "live",
        "sectors": sectors_out, "all_news": all_news, "top_products": tp,
        "lead": {"headline": lead["headline"], "sector": lead.get("category", "")},
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
    # Give each top product a deep review + 3-5 hands-on experiments.
    import synthesize
    for p in (edition.get("top_products") or []):
        try:
            synthesize.synthesize_product(p)
        except Exception:
            pass
    # Creator trends: keyword volume & ranking across every platform we pull.
    try:
        import keywords
        edition["trends"] = keywords.build_trends(edition, prev_volumes=_prev_keyword_volumes(date))
    except Exception as e:
        print(f"  (trends skipped: {e})")
    # Auto-publish (default) makes scheduled editions go live immediately.
    edition["status"] = "approved" if config.AUTO_PUBLISH else "pending_approval"
    return edition


def _prev_keyword_volumes(date: str) -> dict:
    """Load the most recent prior edition's keyword volumes for momentum."""
    try:
        prior = sorted(p for p in config.OUTPUT_DIR.glob("edition-*.json")
                       if p.stem.replace("edition-", "") < date and "BLOCKED" not in p.stem)
        if not prior:
            return {}
        payload = json.loads(prior[-1].read_text())
        return {k["keyword"]: k["volume"] for k in payload.get("trends", {}).get("keywords", [])}
    except Exception:
        return {}


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
    import doctor
    doctor.print_report()
    edition = build_edition(date, mode)

    # QUALITY GATE — never publish template placeholders over a good edition.
    ok, reason = edition_quality_ok(edition)
    if not ok:
        print(f"\n✗ QUALITY GATE FAILED — {reason}.")
        print("  The AI did not run (missing/invalid LLM key, or every LLM call failed), so this")
        print("  edition is template placeholder text. NOT publishing — the live site keeps its last")
        print("  good edition. Fix the LLM key (GROQ_API_KEY / OPENROUTER_API_KEY) and re-run.")
        (config.OUTPUT_DIR / f"edition-{date}-BLOCKED.json").write_text(
            json.dumps(edition, ensure_ascii=False, indent=2))
        sys.exit(2)
    print(f"• Quality gate OK — {reason}.")

    html_body = email_render.render_html(edition)                 # config EMAIL_MODE (compact default)
    full_html = email_render.render_html(edition, mode="full")     # full-depth reference copy
    text_body = email_render.render_text(edition)
    all_news_html = email_render.render_all_news_html(edition)
    subject = edition["subject"]
    print(f"• Subject: {subject[:80]}")
    print(f"• Email mode: {config.EMAIL_MODE} · size {len(html_body)//1024} KB "
          f"(Gmail clips >~102 KB) · full copy {len(full_html)//1024} KB")
    print(f"• {edition['counts']['heroes']} heroes · {edition['counts']['all_news']} all-news · "
          f"credibility {edition['credibility_audit']}")

    # Save structured + rendered outputs
    store.save_local(edition)
    (config.OUTPUT_DIR / f"email-{date}.html").write_text(html_body)
    (config.OUTPUT_DIR / f"email-{date}-full.html").write_text(full_html)
    (config.OUTPUT_DIR / f"email-{date}.txt").write_text(text_body)
    (config.OUTPUT_DIR / f"all-news-{date}.html").write_text(all_news_html)

    samples = config.BASE_DIR.parent / "samples"; samples.mkdir(exist_ok=True)
    # Offline-clickable samples: All-News button points at the sibling file.
    sample_email = email_render.render_html(edition, all_news_link=f"all-news-{date}.html")
    (samples / f"daily-ai-short-{date}.html").write_text(sample_email)
    (samples / f"daily-ai-short-{date}-full.html").write_text(
        email_render.render_html(edition, all_news_link=f"all-news-{date}.html", mode="full"))
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
