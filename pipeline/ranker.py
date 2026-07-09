"""Rank candidate stories so the top HERO_COUNT get the deep-dive treatment.

Scoring blends:
  - source signal (HN points, GitHub stars) already partly in `score`
  - freshness (last 72h heavily favored)
  - category balance (don't let one beat dominate)
  - "buy decision" relevance — the channel is about purchase advice, so
    stories about concrete products/tools/launches outrank pure commentary.
"""
from __future__ import annotations
import datetime as dt
from typing import List, Dict

BUY_SIGNAL_WORDS = [
    "launch", "launches", "released", "release", "unveil", "announces", "announced",
    "available", "pre-order", "preorder", "ships", "shipping", "price", "$", "ipo",
    "review", "vs", "alternative", "open source", "open-source", "free",
]

CATEGORY_WEIGHT = {
    "AI": 1.15, "Robotics": 1.15, "Semiconductors": 1.1, "Open Source": 1.1,
    "eVTOL": 1.05, "Drones": 1.05, "Stocks": 1.0, "Hardware": 1.05,
}


def _freshness(published: str | None) -> float:
    if not published:
        return 0.3
    try:
        ts = dt.datetime.fromisoformat(published.replace("Z", "+00:00"))
    except Exception:
        return 0.3
    age_h = (dt.datetime.now(dt.timezone.utc) - ts).total_seconds() / 3600.0
    if age_h <= 24:
        return 1.0
    if age_h <= 72:
        return 0.7
    if age_h <= 168:
        return 0.4
    return 0.15


def _buy_relevance(title: str, summary: str) -> float:
    text = (title + " " + (summary or "")).lower()
    hits = sum(1 for w in BUY_SIGNAL_WORDS if w in text)
    return min(1.0, 0.2 + 0.15 * hits)


def score_story(s: Dict) -> float:
    import credibility
    base = float(s.get("score", 0.0))
    fresh = _freshness(s.get("published"))
    buy = _buy_relevance(s.get("title", ""), s.get("summary", ""))
    cat = CATEGORY_WEIGHT.get(s.get("category", "AI"), 1.0)
    # Source authority: major/high-credibility outlets lead; low-trust sinks.
    links = s.get("source_links") or ([s["url"]] if s.get("url") else [])
    cred_mult = {"high": 1.35, "medium": 1.0, "low": 0.6}[credibility.rate_story(links)]
    # normalize base (HN/GitHub) into ~0..3 range then blend
    return round((min(base, 3.0) * 1.4 + fresh * 2.2 + buy * 1.6) * cat * cred_mult, 3)


def rank(stories: List[Dict], hero_count: int = 5, max_per_category: int = 2) -> Dict:
    for s in stories:
        s["rank_score"] = score_story(s)
    ordered = sorted(stories, key=lambda x: x["rank_score"], reverse=True)

    heroes, per_cat = [], {}
    # First pass: enforce category diversity (max_per_category each).
    for s in ordered:
        c = s.get("category", "AI")
        if per_cat.get(c, 0) >= max_per_category:
            continue
        heroes.append(s)
        per_cat[c] = per_cat.get(c, 0) + 1
        if len(heroes) >= hero_count:
            break

    # Backfill: on low-diversity days the cap can leave us short — top up with
    # the next-highest-scoring stories so we always return hero_count heroes.
    if len(heroes) < hero_count:
        chosen = {h["url"] for h in heroes}
        for s in ordered:
            if s["url"] in chosen:
                continue
            heroes.append(s)
            chosen.add(s["url"])
            if len(heroes) >= hero_count:
                break

    hero_urls = {h["url"] for h in heroes}
    roundup = [s for s in ordered if s["url"] not in hero_urls][:10]
    return {"heroes": heroes, "roundup": roundup}
