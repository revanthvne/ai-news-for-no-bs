"""Turn a ranked story into the NO BS deep-dive.

Two modes:
  1) LLM mode (if an API key is set): asks the model for the exact sections the
     channel needs — story, founding story, who should use, who should buy,
     free/better alternatives, and a verdict.
  2) Offline/template mode: builds a solid structured deep-dive from the fetched
     metadata so the pipeline ALWAYS produces a usable edition with zero keys.

The output schema matches the seed JSON in data/, so downstream rendering,
storage and the web/mobile apps treat live and seed content identically.
"""
from __future__ import annotations
import json
from typing import Dict

import requests
import config

SYSTEM_PROMPT = (
    "You are the lead researcher for 'NO BS — Should You Buy This?', a channel that cuts hype and "
    "gives brutally honest buy/skip advice on AI, chips, robotics, eVTOL, drones and hardware.\n"
    "Return STRICT JSON (no markdown, and NO HTML tags in any value) with these keys:\n"
    "- one_liner: one punchy plain-English sentence on what this is.\n"
    "- story: 3-4 sentences of clean prose — what happened and why it matters. Never include HTML or 'Discussion | Link' text.\n"
    "- founding_story: the REAL origin — who built the company/product, what year, why they started, notable "
    "funding/backers or milestones. If you are unsure of a fact, say so plainly instead of inventing it.\n"
    "- who_should_use: specific personas and concrete use cases — name the job, the workflow, the pain it removes. "
    "Not vague ('people interested in AI').\n"
    "- who_should_buy: who should actually PAY and whether it's worth it. Say what genuinely makes it special "
    "(or admit nothing does), the pricing reality, and who should NOT buy it.\n"
    "- free_alternatives: name specific free / open-source / cheaper tools that do the same job, and say honestly "
    "whether any is as good or better.\n"
    "- verdict: start with exactly one of BUY, USE, WATCH, SKIP, then ' — ' and one honest sentence.\n"
    "Be skeptical, specific, and useful. Never fabricate."
)


_DEFAULT_MODELS = {
    "groq": "llama-3.3-70b-versatile",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-20241022",
}


def _model_for(provider: str) -> str:
    """Use the configured model, but auto-correct an obvious provider mismatch
    (e.g. provider=anthropic but LLM_MODEL still the Groq default)."""
    m = config.LLM_MODEL or ""
    if provider == "anthropic" and not m.startswith("claude"):
        return _DEFAULT_MODELS["anthropic"]
    if provider == "openai" and ("llama" in m or "claude" in m or not m):
        return _DEFAULT_MODELS["openai"]
    if provider == "groq" and ("gpt" in m or "claude" in m or not m):
        return _DEFAULT_MODELS["groq"]
    return m


def _llm_call(prompt: str, system: str = SYSTEM_PROMPT) -> str | None:
    provider = config.LLM_PROVIDER
    model = _model_for(provider)
    try:
        if provider == "groq":
            return _openai_compatible(
                "https://api.groq.com/openai/v1/chat/completions",
                config.GROQ_API_KEY, model, prompt, system)
        if provider == "openai":
            return _openai_compatible(
                "https://api.openai.com/v1/chat/completions",
                config.OPENAI_API_KEY, model, prompt, system)
        if provider == "anthropic":
            return _anthropic(config.ANTHROPIC_API_KEY, model, prompt, system)
    except Exception as e:
        print(f"  ! LLM call failed ({e}); falling back to template.")
    return None


def _openai_compatible(url: str, key: str, model: str, prompt: str, system: str = SYSTEM_PROMPT) -> str:
    r = requests.post(url, timeout=60, headers={"Authorization": f"Bearer {key}"}, json={
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
    })
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _anthropic(key: str, model: str, prompt: str, system: str = SYSTEM_PROMPT) -> str:
    r = requests.post("https://api.anthropic.com/v1/messages", timeout=60, headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json",
    }, json={
        "model": model, "max_tokens": 1200, "system": system,
        "messages": [{"role": "user", "content": prompt + "\nReturn ONLY JSON."}],
    })
    r.raise_for_status()
    return r.json()["content"][0]["text"]


def synthesize(story: Dict) -> Dict:
    """Return the story enriched with deep-dive fields."""
    if config.has_llm():
        prompt = (
            f"NEWS ITEM\nTitle: {story.get('title')}\nCategory: {story.get('category')}\n"
            f"Source: {story.get('source')}\nURL: {story.get('url')}\n"
            f"Summary: {story.get('summary','')}\n"
        )
        raw = _llm_call(prompt)
        if raw:
            try:
                data = json.loads(raw)
                story.update({k: data.get(k, "") for k in (
                    "one_liner", "story", "founding_story",
                    "who_should_use", "who_should_buy", "free_alternatives", "verdict")})
                story["headline"] = story.get("title")
                story["source_links"] = [story.get("url")]
                return story
            except Exception:
                pass
    return _template(story)


def _template(story: Dict) -> Dict:
    """Deterministic, honest fallback so we never ship an empty section."""
    from sources import clean_html
    cat = story.get("category", "AI")
    title = clean_html(story.get("title", "This release"))
    summary = clean_html(story.get("summary", ""))
    stars = (story.get("extra") or {}).get("stars")
    story.setdefault("headline", title)
    story.setdefault("source_links", [story.get("url")])
    story["one_liner"] = summary[:180] or f"A notable new {cat} development worth a look."
    story["story"] = (
        summary
        or f"{title}. Flagged by {story.get('source')} as a significant {cat} development. "
           "See the source link for primary details."
    )
    story["founding_story"] = (
        "Company/project background to be verified against primary sources before publishing. "
        "(Auto-mode fills this from the source; enable an LLM key or add a seed entry for a full origin story.)"
    )
    story["who_should_use"] = f"People actively working in or evaluating {cat.lower()} tools and products."
    story["who_should_buy"] = (
        "Buy only if it solves a problem you have today; otherwise wait for reviews and price drops. "
        "NO BS default: don't buy v1 on hype."
    )
    story["free_alternatives"] = (
        "Check for open-source or free-tier equivalents before paying — there is usually one. "
        + (f"This itself is open source ({stars:,}★)." if stars else "")
    )
    story["verdict"] = "WATCH — verify details before making a purchase call."
    return story


PRODUCT_SYSTEM = (
    "You review new tech/AI products for 'NO BS — Should You Buy This?'. For the given product, return STRICT "
    "JSON (no HTML) with two keys: "
    "'deep_review' — 4-6 honest sentences: what it actually does, standout strengths, real weaknesses/limits, "
    "who it's genuinely for, and whether it's worth paying for. Be specific and skeptical; if unsure, say so. "
    "'experiments' — an array of 3 to 5 concrete, specific things someone could build or try with this product "
    "to see what it can do (each a short, actionable idea). Never fabricate features."
)


def synthesize_product(product: dict) -> dict:
    """Enrich a top-product entry with a deep_review + 3-5 hands-on experiments."""
    name = product.get("name", "This product")
    if config.has_llm():
        prompt = (f"PRODUCT\nName: {name}\nTagline: {product.get('tagline','')}\n"
                  f"Category: {product.get('category','')}\nURL: {product.get('url','')}")
        raw = _llm_call(prompt, system=PRODUCT_SYSTEM)
        if raw:
            try:
                data = json.loads(raw)
                dr, ex = data.get("deep_review"), data.get("experiments")
                if dr and isinstance(ex, list) and ex:
                    product["deep_review"] = dr
                    product["experiments"] = [str(x) for x in ex][:5]
                    return product
            except Exception:
                pass
    cat = product.get("category", "tool")
    product["deep_review"] = (
        f"{name} — {product.get('tagline','')}. A new {cat} product; try its free tier before paying and "
        "look for open-source equivalents first. Deeper review pending AI analysis.")
    product["experiments"] = [
        f"Run {name} on one real task from your workflow and compare it to your current tool.",
        f"Push {name}'s free tier to its limits before you consider paying.",
        "See whether an open-source or free alternative does the same job.",
    ]
    return product
