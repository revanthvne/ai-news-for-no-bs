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
    "You are the researcher for a YouTube channel called 'NO BS — Should You Buy This?'. "
    "You cut hype and give honest purchase advice about AI, chips, robotics, eVTOL, drones and hardware. "
    "For the given news item, return STRICT JSON with these keys: "
    "one_liner, story, founding_story, who_should_use, who_should_buy, free_alternatives, verdict. "
    "'verdict' must start with one of: BUY, USE, WATCH, SKIP. Be specific, skeptical, and useful. "
    "Never invent facts you can't reasonably infer; if unknown, say so plainly."
)


def _llm_call(prompt: str) -> str | None:
    provider = config.LLM_PROVIDER
    try:
        if provider == "groq":
            return _openai_compatible(
                "https://api.groq.com/openai/v1/chat/completions",
                config.GROQ_API_KEY, config.LLM_MODEL, prompt)
        if provider == "openai":
            return _openai_compatible(
                "https://api.openai.com/v1/chat/completions",
                config.OPENAI_API_KEY, config.LLM_MODEL, prompt)
        if provider == "anthropic":
            return _anthropic(config.ANTHROPIC_API_KEY, config.LLM_MODEL, prompt)
    except Exception as e:
        print(f"  ! LLM call failed ({e}); falling back to template.")
    return None


def _openai_compatible(url: str, key: str, model: str, prompt: str) -> str:
    r = requests.post(url, timeout=60, headers={"Authorization": f"Bearer {key}"}, json={
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
    })
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _anthropic(key: str, model: str, prompt: str) -> str:
    r = requests.post("https://api.anthropic.com/v1/messages", timeout=60, headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json",
    }, json={
        "model": model, "max_tokens": 1200, "system": SYSTEM_PROMPT,
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
    cat = story.get("category", "AI")
    title = story.get("title", "This release")
    stars = (story.get("extra") or {}).get("stars")
    story.setdefault("headline", title)
    story.setdefault("source_links", [story.get("url")])
    story["one_liner"] = story.get("summary") or f"A notable new {cat} development worth a look."
    story["story"] = (
        story.get("summary")
        or f"{title}. Flagged by {story.get('source')} as a significant {cat} development. "
           "Full deep-dive pending — see the source link for primary details."
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
