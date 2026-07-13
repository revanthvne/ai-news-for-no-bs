"""Open-source trending for the Creator tab — what's hot on GitHub & Hugging Face.

Both use free, keyless public APIs (a GitHub token just raises rate limits).
Everything is defensive: any failure returns [] so the Creator tab still renders.
Results cache per day to avoid re-hitting the APIs on 6-hourly re-runs.
"""
from __future__ import annotations
import datetime as dt
import json

import requests
import config

UA = {"User-Agent": "NO-BS-DailyAIShort/1.0 (+https://github.com/)"}
TIMEOUT = 20


def github_trending(days: int = 14, limit: int = 12) -> list[dict]:
    """Repos created in the last `days`, ranked by stars — a free 'trending' proxy."""
    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    headers = dict(UA)
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
    url = ("https://api.github.com/search/repositories"
           f"?q=created:>{since}+stars:>50&sort=stars&order=desc&per_page={limit}")
    out = []
    try:
        r = requests.get(url, headers=headers, timeout=TIMEOUT)
        r.raise_for_status()
        for repo in r.json().get("items", []):
            out.append({
                "name": repo["full_name"],
                "url": repo["html_url"],
                "stars": repo.get("stargazers_count", 0),
                "language": repo.get("language") or "",
                "description": (repo.get("description") or "")[:160],
                "source": "GitHub",
            })
    except Exception:
        pass
    return out


def _hf(kind: str, limit: int) -> list[dict]:
    # kind = "models" | "datasets"
    url = (f"https://huggingface.co/api/{kind}"
           f"?sort=trendingScore&direction=-1&limit={limit}&full=false")
    base = "https://huggingface.co/" + ("datasets/" if kind == "datasets" else "")
    out = []
    try:
        r = requests.get(url, headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
        for m in r.json():
            ident = m.get("id") or m.get("modelId") or m.get("datasetId") or ""
            if not ident:
                continue
            out.append({
                "name": ident,
                "url": base + ident,
                "likes": m.get("likes", 0),
                "downloads": m.get("downloads", 0),
                "task": m.get("pipeline_tag") or "",
                "kind": "model" if kind == "models" else "dataset",
                "source": "Hugging Face",
            })
    except Exception:
        pass
    return out


def trending(github_limit: int = 12, hf_models: int = 12, hf_datasets: int = 8) -> dict:
    cache = config.OUTPUT_DIR / f"opensource-{dt.date.today().isoformat()}.json"
    try:
        cached = json.loads(cache.read_text())
        if cached.get("github") or cached.get("hf_models"):
            return cached
    except Exception:
        pass
    data = {
        "github": github_trending(limit=github_limit),
        "hf_models": _hf("models", hf_models),
        "hf_datasets": _hf("datasets", hf_datasets),
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    try:
        cache.write_text(json.dumps(data, ensure_ascii=False))
    except Exception:
        pass
    return data
