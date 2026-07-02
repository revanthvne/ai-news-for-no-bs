"""Assemble the 8 per-sector research files into ONE structured edition.

Input : pipeline/data/sectors/<date>/<Sector>.json  (one per sector)
Output: pipeline/data/edition_<date>.json            (the combined edition)

Adds: per-story images (og:image or gradient fallback), a credibility rating on
every story (the "no fake news" gate), the flattened all_news firehose, the lead
story, and the email subject.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

import config
import credibility
import images

# The order sectors appear in the edition (matches the channel's beats).
SECTOR_ORDER = [
    "AI", "Semiconductors", "Robotics", "eVTOL",
    "Drones", "Hardware", "Stocks", "Open Source",
]
SECTOR_FILE = {
    "AI": "AI.json", "Semiconductors": "Semiconductors.json", "Robotics": "Robotics.json",
    "eVTOL": "eVTOL.json", "Drones": "Drones.json", "Hardware": "Hardware.json",
    "Stocks": "Stocks.json", "Open Source": "OpenSource.json",
}


def slugify(x: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (x or "").lower()).strip("-")


def _finish_story(s: dict, sector: str, enrich: bool, budget: list) -> dict:
    s.setdefault("id", slugify(s.get("headline", "story"))[:60])
    if not s.get("source_name") and s.get("source_links"):
        s["source_name"] = credibility.source_label(s["source_links"][0])
    # Recompute credibility from the actual domains; keep the safer of the two.
    computed = credibility.rate_story(s.get("source_links", []))
    given = (s.get("credibility") or "").lower()
    order = {"high": 3, "medium": 2, "low": 1, "": 0}
    s["credibility"] = computed if order[computed] <= order.get(given, 0) else computed
    s["credible"] = credibility.is_publishable(s.get("source_links", []))
    # Image: only spend network budget on the ones missing an image.
    do_enrich = enrich and budget[0] > 0 and not s.get("image_url")
    s["image_url"] = images.resolve_image(s, sector, enrich=do_enrich)
    if do_enrich:
        budget[0] -= 1
    s["image_is_placeholder"] = s["image_url"].startswith("data:")
    return s


def assemble(date: str, enrich: bool = False, enrich_budget: int = 10) -> dict:
    src_dir = config.DATA_DIR / "sectors" / date
    if not src_dir.exists():
        raise SystemExit(f"No sector data at {src_dir}")

    budget = [enrich_budget]
    sectors, all_news = [], []
    for name in SECTOR_ORDER:
        f = src_dir / SECTOR_FILE[name]
        if not f.exists():
            continue
        data = json.loads(f.read_text())
        heroes = [_finish_story(s, name, enrich, budget) for s in data.get("heroes", [])]
        other = data.get("other_news", [])
        for o in other:
            o["credibility"] = credibility.rate_story(o.get("source_links", []))
            if not o.get("source_name") and o.get("source_links"):
                o["source_name"] = credibility.source_label(o["source_links"][0])
        sectors.append({"sector": name, "slug": slugify(name),
                        "heroes": heroes, "other_news": other})
        for h in heroes:
            all_news.append({"sector": name, "kind": "hero", "headline": h["headline"],
                             "one_liner": h.get("one_liner", ""), "source_name": h.get("source_name", ""),
                             "source_links": h.get("source_links", []), "credibility": h["credibility"],
                             "verdict": h.get("verdict", "")})
        for o in other:
            all_news.append({"sector": name, "kind": "other", "headline": o.get("headline", ""),
                             "one_liner": o.get("one_liner", ""), "source_name": o.get("source_name", ""),
                             "source_links": o.get("source_links", []), "credibility": o.get("credibility", "low")})

    lead = sectors[0]["heroes"][0] if sectors and sectors[0]["heroes"] else {"headline": "Daily AI Short"}
    all_stories = [h for s in sectors for h in s["heroes"]]
    edition = {
        "edition_date": date,
        "channel": config.CHANNEL_NAME,
        "generated_by": "seed-sectors",
        "sectors": sectors,
        "all_news": all_news,
        "lead": {"headline": lead["headline"], "sector": sectors[0]["sector"] if sectors else ""},
        "subject": f"APPROVAL REQUIRED: Daily AI Short - {lead['headline']}",
        "status": "pending_approval",
        "counts": {
            "sectors": len(sectors),
            "heroes": sum(len(s["heroes"]) for s in sectors),
            "other_news": sum(len(s["other_news"]) for s in sectors),
            "all_news": len(all_news),
        },
        "credibility_audit": credibility.audit(all_stories),
    }
    return edition


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="2026-07-01")
    ap.add_argument("--enrich", action="store_true", help="fetch og:images for stories missing one")
    ap.add_argument("--enrich-budget", type=int, default=10)
    args = ap.parse_args()
    edition = assemble(args.date, enrich=args.enrich, enrich_budget=args.enrich_budget)
    out = config.DATA_DIR / f"edition_{args.date}.json"
    out.write_text(json.dumps(edition, indent=2, ensure_ascii=False))
    c = edition["counts"]; a = edition["credibility_audit"]
    print(f"Assembled {out.name}: {c['sectors']} sectors · {c['heroes']} heroes · "
          f"{c['other_news']} other · {c['all_news']} all-news")
    print(f"Credibility: {a['high']} high · {a['medium']} medium · {a['low']} low")
    print(f"Lead: {edition['lead']['headline'][:70]}")


if __name__ == "__main__":
    main()
