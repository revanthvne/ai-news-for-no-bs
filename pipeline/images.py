"""Story images.

Order of preference:
  1) An image_url already supplied by research/LLM.
  2) The article's Open Graph image (og:image / twitter:image), fetched at
     build time from the primary source URL (best-effort, short timeout).
  3) A deterministic per-sector gradient placeholder (no network, always works)
     so every card looks intentional even when no photo is available.
"""
from __future__ import annotations
import re
from urllib.parse import urljoin

import requests

UA = {"User-Agent": "Mozilla/5.0 (compatible; NO-BS-Daily/1.0)"}

# Per-sector gradient palettes for the placeholder (hex pairs).
SECTOR_GRADIENTS = {
    "AI": ("#00e0b8", "#0891b2"),
    "Semiconductors": ("#f59e0b", "#b45309"),
    "Robotics": ("#a78bfa", "#6d28d9"),
    "eVTOL": ("#38bdf8", "#0369a1"),
    "Drones": ("#34d399", "#047857"),
    "Hardware": ("#f472b6", "#be185d"),
    "Stocks": ("#4ade80", "#15803d"),
    "Open Source": ("#fb923c", "#c2410c"),
}

_OG_RE = re.compile(
    r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)(?::url)?["\'][^>]+content=["\']([^"\']+)["\']',
    re.I,
)
_OG_RE2 = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\'](?:og:image|twitter:image)(?::url)?["\']',
    re.I,
)


def fetch_og_image(url: str, timeout: int = 5) -> str | None:
    try:
        r = requests.get(url, headers=UA, timeout=timeout)
        if r.status_code != 200 or "text/html" not in r.headers.get("content-type", ""):
            return None
        html = r.text[:200_000]
        m = _OG_RE.search(html) or _OG_RE2.search(html)
        if m:
            img = m.group(1).strip()
            if img.startswith("//"):
                img = "https:" + img
            elif img.startswith("/"):
                img = urljoin(url, img)
            if img.startswith("http"):
                return img
    except Exception:
        return None
    return None


def gradient_svg_data_uri(sector: str, label: str = "") -> str:
    """A self-contained SVG placeholder (works offline, in email and apps)."""
    c1, c2 = SECTOR_GRADIENTS.get(sector, ("#334155", "#0f172a"))
    txt = (label or sector).upper()[:22]
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='640' height='300'>"
        f"<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>"
        f"<stop offset='0' stop-color='{c1}'/><stop offset='1' stop-color='{c2}'/>"
        f"</linearGradient></defs>"
        f"<rect width='640' height='300' fill='url(#g)'/>"
        f"<text x='32' y='268' font-family='Arial' font-size='22' font-weight='bold' "
        f"fill='#0a0d11' opacity='0.85'>{txt}</text></svg>"
    )
    import base64
    b64 = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"


def resolve_image(story: dict, sector: str, enrich: bool = True) -> str:
    """Return the best available image URL/URI for a story (never empty)."""
    if story.get("image_url"):
        return story["image_url"]
    if enrich:
        for link in story.get("source_links", [])[:2]:
            og = fetch_og_image(link)
            if og:
                story["image_url"] = og
                return og
    return gradient_svg_data_uri(sector, story.get("source_name", ""))
