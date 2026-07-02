"""Fetch candidate stories from FREE sources only.

Sources used (all free, no paid API required):
  - Curated RSS feeds across AI / chips / robotics / eVTOL / drones / stocks
  - Hacker News (Algolia API) for what developers are actually upvoting
  - GitHub Search API for trending / highest-rated new releases

Each source returns a list of normalized dicts:
  {title, url, source, category, published, score, extra}
"""
from __future__ import annotations
import datetime as dt
import time
from typing import List, Dict

import requests

try:
    import feedparser
except Exception:
    feedparser = None

import config

UA = {"User-Agent": "NO-BS-DailyAIShort/1.0 (+https://github.com/)"}
TIMEOUT = 20

# Curated, free RSS feeds mapped to the channel's beats.
RSS_FEEDS = {
    "AI": [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "https://venturebeat.com/category/ai/feed/",
    ],
    "Semiconductors": [
        "https://www.tomshardware.com/feeds/all",
        "https://semiengineering.com/feed/",
    ],
    "Robotics": [
        "https://spectrum.ieee.org/feeds/topic/robotics.rss",
        "https://www.therobotreport.com/feed/",
    ],
    "eVTOL": [
        "https://evtol.com/feed/",
    ],
    "Drones": [
        "https://dronedj.com/feed/",
    ],
    "Stocks": [
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",  # Technology
    ],
}


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def fetch_rss(max_per_feed: int = 8) -> List[Dict]:
    out: List[Dict] = []
    if feedparser is None:
        return out
    for category, feeds in RSS_FEEDS.items():
        for url in feeds:
            try:
                parsed = feedparser.parse(url, request_headers=UA)
            except Exception:
                continue
            for entry in parsed.entries[:max_per_feed]:
                published = None
                if getattr(entry, "published_parsed", None):
                    published = dt.datetime.fromtimestamp(
                        time.mktime(entry.published_parsed), dt.timezone.utc
                    )
                out.append({
                    "title": getattr(entry, "title", "").strip(),
                    "url": getattr(entry, "link", ""),
                    "source": parsed.feed.get("title", url) if parsed.feed else url,
                    "category": category,
                    "published": published.isoformat() if published else None,
                    "score": 0.0,
                    "summary": getattr(entry, "summary", "")[:600],
                })
    return out


def fetch_hackernews(min_points: int = 150) -> List[Dict]:
    """Top stories from HN in the last 3 days above a points threshold."""
    out: List[Dict] = []
    cutoff = int((_now() - dt.timedelta(days=3)).timestamp())
    query = (
        "https://hn.algolia.com/api/v1/search_by_date"
        f"?tags=story&numericFilters=created_at_i>{cutoff},points>{min_points}&hitsPerPage=40"
    )
    try:
        r = requests.get(query, headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
        for hit in r.json().get("hits", []):
            title = (hit.get("title") or "").strip()
            if not title:
                continue
            out.append({
                "title": title,
                "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                "source": "Hacker News",
                "category": _guess_category(title),
                "published": hit.get("created_at"),
                "score": float(hit.get("points", 0)) / 10.0,
                "summary": "",
            })
    except Exception:
        pass
    return out


def fetch_github_releases(days: int = 10) -> List[Dict]:
    """Highest-rated recently-created repos — proxy for hot new releases/tools."""
    out: List[Dict] = []
    since = (_now() - dt.timedelta(days=days)).strftime("%Y-%m-%d")
    headers = dict(UA)
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
    q = f"created:>{since}+stars:>200"
    url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page=15"
    try:
        r = requests.get(url, headers=headers, timeout=TIMEOUT)
        r.raise_for_status()
        for repo in r.json().get("items", []):
            out.append({
                "title": f"{repo['full_name']} — {repo.get('description') or 'new open-source release'}",
                "url": repo["html_url"],
                "source": "GitHub",
                "category": "Open Source",
                "published": repo.get("created_at"),
                "score": float(repo.get("stargazers_count", 0)) / 100.0,
                "summary": (repo.get("description") or "")[:300],
                "extra": {"stars": repo.get("stargazers_count"), "language": repo.get("language")},
            })
    except Exception:
        pass
    return out


_CATEGORY_HINTS = {
    "Semiconductors": ["chip", "semiconductor", "nvidia", "tsmc", "amd", "wafer", "hbm", "nm ", "gpu"],
    "Robotics": ["robot", "humanoid", "atlas", "figure", "cobot"],
    "eVTOL": ["evtol", "air taxi", "joby", "archer", "vertiport"],
    "Drones": ["drone", "uav", "quadcopter", "dji"],
    "Stocks": ["stock", "shares", "earnings", "ipo", "market cap", "selloff"],
    "AI": ["ai", "model", "llm", "gpt", "gemini", "agent", "openai", "anthropic"],
}


def _guess_category(title: str) -> str:
    t = title.lower()
    for cat, hints in _CATEGORY_HINTS.items():
        if any(h in t for h in hints):
            return cat
    return "AI"


def gather_all() -> List[Dict]:
    """Pull from every free source and return a combined candidate list."""
    stories: List[Dict] = []
    stories += fetch_rss()
    stories += fetch_hackernews()
    stories += fetch_github_releases()
    # de-dup by URL
    seen, deduped = set(), []
    for s in stories:
        key = s["url"].split("?")[0]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(s)
    return deduped


if __name__ == "__main__":
    got = gather_all()
    print(f"Fetched {len(got)} candidate stories")
    for s in got[:10]:
        print(f"  [{s['category']}] {s['title'][:80]}  <{s['source']}>")
