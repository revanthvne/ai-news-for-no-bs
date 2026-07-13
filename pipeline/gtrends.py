"""Google Trends provider for the Creator tab.

Turns a list of keywords into comparable *search-volume* scores using Google
Trends (via the unofficial `pytrends` library). This plugs into the
`volume_provider` seam in keywords.py.

Why this is non-trivial: Google Trends returns interest that is normalized 0-100
*within each request* of up to 5 terms. To compare terms across many requests we
include a fixed ANCHOR term in every batch and rescale each batch so the anchor
is a common reference — giving one globally-comparable 0-100+ scale.

Everything here is defensive: if pytrends is missing, Trends is rate-limited, or
the network is unavailable, `volume_map` returns {} and callers fall back to the
derived cross-platform score. Results are cached per day to avoid re-hitting
Google on re-runs.
"""
from __future__ import annotations
import json
import time
from pathlib import Path

import config

ANCHOR = "chatgpt"  # common, high-volume reference present in every batch


def _normalize(batch_means: list[dict], anchor: str) -> dict:
    """Rescale each batch by its anchor value so scores are cross-comparable.

    batch_means: list of {term: mean_interest} dicts, one per batch (each
    containing the anchor). Pure function — unit-tested offline.
    """
    out: dict[str, float] = {}
    for means in batch_means:
        a = means.get(anchor, 0) or 0
        if a <= 0:
            continue  # anchor flat in this batch — can't normalize, skip
        for term, val in means.items():
            if term == anchor:
                continue
            out[term] = round((val / a) * 100, 1)
    return out


def _chunk(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def volume_map(keywords: list[str]) -> dict:
    """Return {keyword: google_trends_score}. {} on any failure (safe fallback)."""
    if not keywords:
        return {}
    kws = [k for k in keywords if k and k != ANCHOR][: config.GOOGLE_TRENDS_MAX]

    cache = config.OUTPUT_DIR / f"gtrends-{_today()}.json"
    cached = _read_cache(cache)
    missing = [k for k in kws if k not in cached]
    if not missing:
        return {k: cached[k] for k in kws if k in cached}

    try:
        from pytrends.request import TrendReq
    except Exception:
        return cached  # library not installed — use whatever we cached, else {}

    try:
        pt = TrendReq(hl="en-US", tz=0, timeout=(10, 25))
        batch_means = []
        for group in _chunk(missing, 4):  # 4 + anchor = 5 (Trends max per request)
            terms = [ANCHOR] + group
            try:
                pt.build_payload(terms, timeframe=config.GOOGLE_TRENDS_TIMEFRAME,
                                 geo=config.GOOGLE_TRENDS_GEO)
                df = pt.interest_over_time()
                if df is None or df.empty:
                    continue
                cols = [c for c in df.columns if c != "isPartial"]
                batch_means.append({c: float(df[c].mean()) for c in cols})
            except Exception:
                continue
            time.sleep(1.2)  # be polite; avoid 429s
        fresh = _normalize(batch_means, ANCHOR)
    except Exception:
        return cached

    merged = {**cached, **fresh}
    _write_cache(cache, merged)
    return {k: merged[k] for k in kws if k in merged}


def _today():
    import datetime as dt
    return dt.date.today().isoformat()


def _read_cache(p: Path) -> dict:
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def _write_cache(p: Path, data: dict):
    try:
        p.write_text(json.dumps(data, ensure_ascii=False))
    except Exception:
        pass
