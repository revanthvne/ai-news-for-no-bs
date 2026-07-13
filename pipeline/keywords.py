"""Creator trends — keyword VOLUME & RANKING derived from every platform the
pipeline already aggregates (RSS across all 8 sectors + Hacker News + Product
Hunt + GitHub).

Design notes
------------
* "Volume" here is a *cross-platform interest score*, not paid search volume.
  It weights each mention by the platform it came from and the source's
  credibility, so a topic trending on Hacker News + a major outlet outranks one
  that only shows up in a single low-signal feed.
* "Ranking" is the position by volume (1 = hottest).
* Momentum compares this edition's volume to the previous edition's, so you can
  see what's heating up vs cooling down.
* PROVIDER SEAM: pass `volume_provider=fn` to override the derived volume with a
  real search-volume API (Google Trends / Ahrefs / SimilarWeb) later — no caller
  changes needed. `fn(keyword) -> int | None`.
"""
from __future__ import annotations
import re
from collections import defaultdict
from urllib.parse import urlparse

# Words that never make good trend keywords.
STOP = set((
    "the a an and or but for nor so yet of to in on at by with from as is are was "
    "were be been being this that these those it its it's you your we our they their "
    "he she his her them who whom what which when where why how all any both each few "
    "more most other some such no not only own same than too very can will just don "
    "should now new news says say said report reports launch launches launched update "
    "updates first best top get gets getting make makes making use uses using into out "
    "up down over after before about via amid could would may might has have had do does "
    "day today week year years million billion company companies startup ai's inc corp "
    "here there back off per vs also one two three big small early late next last "
    # calendar + GitHub/Product-Hunt scaffolding noise (not real trend topics)
    "january february march april june july august september october november december "
    "jan feb mar apr jun jul aug sep sept oct nov dec mon tue wed thu fri sat sun "
    "star stars repo repos repository github commit commits pull request issue issues "
    "app apps tool tools platform api release releases version versions beta alpha demo "
    "free paid open source based build built launch launches feature features project "
    "list awesome guide template library framework code codebase readme docs doc "
    "under shipped ship ships production available announced announcing introducing "
    # generic English fillers that have huge baseline search volume but zero trend value
    "online offline live real really way ways post posts while people world worlds "
    "power thing things stuff part parts lot lots bit high higher low lower long longer "
    "good great full want wants need needs like look looks looking going goes went come "
    "comes came take takes took give gives given work works working help helps used "
    "week weeks month months hour hours set sets run runs show shows place places case "
    "cases point points side sides fact facts kind sort type types time times still "
    "much many well left right thing does done getting making being having "
    "against concerns concern sparking spark sparks sparked raising raises raise toward "
    "towards despite according amid amongst among within without unless whether"
).split())

PLATFORM_BASE = {"Hacker News": 1.4, "Product Hunt": 1.25, "GitHub": 1.2, "RSS / Web": 1.0}
CRED_MULT = {"high": 1.3, "medium": 1.0, "low": 0.7}


def _platform(url: str, source_name: str = "") -> str:
    host = (urlparse(url or "").netloc or source_name or "").lower()
    if "ycombinator" in host or "hacker news" in host:
        return "Hacker News"
    if "producthunt" in host or "product hunt" in host:
        return "Product Hunt"
    if "github" in host:
        return "GitHub"
    return "RSS / Web"


_TOKEN = re.compile(r"[a-z0-9][a-z0-9\+\.\-]{1,}")


def _phrases(text: str):
    """Yield candidate keywords: meaningful unigrams + adjacent bigrams."""
    toks = [t for t in _TOKEN.findall((text or "").lower())]
    kept = [t for t in toks if t not in STOP and len(t) >= 3 and not t.isdigit()]
    seen = set()
    for t in kept:
        if t not in seen:
            seen.add(t)
            yield t
    # bigrams from the original (stop-aware) token stream to keep real phrases
    for i in range(len(toks) - 1):
        a, b = toks[i], toks[i + 1]
        if a in STOP or b in STOP or len(a) < 3 or len(b) < 3 or a.isdigit() or b.isdigit():
            continue
        bg = f"{a} {b}"
        if bg not in seen:
            seen.add(bg)
            yield bg


def _story_units(edition: dict):
    """Every content item across platforms, normalized to (text, url, source, cred, sector, kind)."""
    units = []
    for item in edition.get("all_news", []):
        links = item.get("source_links") or []
        units.append((
            f"{item.get('headline','')} {item.get('one_liner','')}",
            (links[0] if links else ""),
            item.get("source_name", ""),
            (item.get("credibility") or "low").lower(),
            item.get("sector", ""),
            item.get("kind", "news"),
        ))
    for p in edition.get("top_products", []):
        units.append((
            f"{p.get('name','')} {p.get('tagline','')} {p.get('category','')}",
            p.get("url", ""),
            "Product Hunt",
            "medium",
            p.get("category", "Product"),
            "product",
        ))
    return units


def extract_keywords(edition: dict, prev_volumes: dict | None = None,
                     volume_provider=None, top: int = 60, min_mentions: int = 2):
    agg = defaultdict(lambda: {
        "weight": 0.0, "mentions": 0, "sectors": set(), "platforms": set(), "samples": []})
    for text, url, source, cred, sector, kind in _story_units(edition):
        platform = _platform(url, source)
        w = PLATFORM_BASE.get(platform, 1.0) * CRED_MULT.get(cred, 0.8)
        headline = text.strip()
        for kw in _phrases(text):
            e = agg[kw]
            e["weight"] += w
            e["mentions"] += 1
            if sector:
                e["sectors"].add(sector)
            e["platforms"].add(platform)
            if len(e["samples"]) < 3 and headline:
                e["samples"].append({"headline": headline[:120], "url": url, "source": source})

    items = []
    for kw, e in agg.items():
        # 'volume' = derived cross-platform news-relevance (keeps the default
        # ranking niche-relevant). A provider (Google Trends) adds real
        # 'search_volume' as a separate, sortable property — it never hijacks the
        # default ranking with broad high-search words.
        vol = int(round(e["weight"] * 10))
        sv = None
        if volume_provider:
            try:
                pv = volume_provider(kw)
                if pv is not None:
                    sv = round(float(pv), 1)
            except Exception:
                pass
        items.append({
            "keyword": kw, "volume": vol, "search_volume": sv, "mentions": e["mentions"],
            "sectors": sorted(e["sectors"]), "platforms": sorted(e["platforms"]),
            "samples": e["samples"],
        })

    # Prefer cross-source trends; relax if that leaves too few.
    strong = [i for i in items if i["mentions"] >= min_mentions]
    if len(strong) < 15:
        strong = items
    strong.sort(key=lambda i: (i["volume"], i["mentions"]), reverse=True)
    strong = strong[:top]

    prev = prev_volumes or {}
    for rank, i in enumerate(strong, 1):
        i["rank"] = rank
        p = prev.get(i["keyword"])
        if not p:
            i["trend"] = "new"
            i["delta_pct"] = None
        else:
            d = round((i["volume"] - p) / p * 100)
            i["delta_pct"] = d
            i["trend"] = "▲ rising" if d >= 15 else "▼ cooling" if d <= -15 else "steady"
    return strong


def topic_ideas(keywords: list, n: int = 8):
    """Turn the hottest keywords into NO BS video-topic angles (deterministic, $0)."""
    ideas = []
    for kw in keywords[:n]:
        k = kw["keyword"]
        sector = (kw["sectors"] or ["tech"])[0]
        sample = (kw["samples"] or [{}])[0]
        ideas.append({
            "title": f"{k.title()} — hype or worth it? (NO BS)",
            "angle": (f"'{k}' is trending across {', '.join(kw['platforms'])} "
                      f"({kw['mentions']} stories, volume {kw['volume']}). Do a NO BS breakdown: "
                      f"what it actually is, who should care, and the free/better alternative."),
            "sector": sector,
            "volume": kw["volume"],
            "trend": kw.get("trend", "new"),
            "hook_source": sample,
        })
    return ideas


def build_trends(edition: dict, prev_volumes: dict | None = None, volume_provider=None):
    kws = extract_keywords(edition, prev_volumes=prev_volumes, volume_provider=volume_provider)
    has_search = bool(volume_provider) and any(k.get("search_volume") is not None for k in kws)
    if has_search:
        source = "RSS (8 sectors) + Hacker News + Product Hunt + GitHub · Search volume from Google Trends"
        note = ("Volume = cross-platform news relevance in the niche (the default ranking). "
                "Search volume = Google Trends relative search interest (0-100+, anchor-normalized) "
                "— sort by it to see raw search demand. Momentum compares to the previous edition.")
    else:
        source = "RSS (8 sectors) + Hacker News + Product Hunt + GitHub"
        note = ("Volume = cross-platform interest score (mentions weighted by platform + source "
                "credibility). Enable GOOGLE_TRENDS=true to add real Google search volume.")
    return {
        "generated_by": "google-trends" if has_search else "pipeline-derived",
        "has_search": has_search,
        "source": source,
        "note": note,
        "keywords": kws,
        "topics": topic_ideas(kws),
    }
