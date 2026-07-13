#!/usr/bin/env python3
"""Automated tests for the NO BS pipeline.

Runs with pytest:      python -m pytest pipeline/test_pipeline.py -v
or standalone (no dep): python pipeline/test_pipeline.py

All tests are offline — they build the deterministic seed edition (2026-07-01)
that ships in the repo, so they pass with zero API keys and catch regressions
in the data model, credibility gate, and email rendering on every run.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import assemble
import email_render
import credibility
import run

SEED_DATE = "2026-07-01"
GMAIL_CLIP_BYTES = 102 * 1024
REQUIRED = ["headline", "one_liner", "source_links", "story", "founding_story",
            "who_should_use", "who_should_buy", "free_alternatives", "verdict",
            "image_url", "credibility"]
SECTORS = ["AI", "Semiconductors", "Robotics", "eVTOL",
           "Drones", "Hardware", "Stocks", "Open Source"]


def _edition():
    return assemble.assemble(SEED_DATE, enrich=False)


def test_eight_sectors_five_heroes():
    e = _edition()
    assert e["counts"]["sectors"] == 8, e["counts"]
    got = [s["sector"] for s in e["sectors"]]
    for name in SECTORS:
        assert name in got, f"missing sector {name}"
    for s in e["sectors"]:
        assert len(s["heroes"]) == 5, f"{s['sector']} has {len(s['heroes'])} heroes"


def test_every_hero_has_all_fields():
    e = _edition()
    for s in e["sectors"]:
        for i, h in enumerate(s["heroes"], 1):
            missing = [k for k in REQUIRED if not h.get(k)]
            assert not missing, f"{s['sector']} hero {i} missing {missing}"
            assert h["source_links"], f"{s['sector']} hero {i} has no source links"


def test_no_low_credibility_sources():
    e = _edition()
    stories = [h for s in e["sectors"] for h in s["heroes"]]
    audit = credibility.audit(stories)
    assert audit["low"] == 0, f"low-credibility stories present: {audit}"


def test_verdicts_start_with_valid_keyword():
    e = _edition()
    for s in e["sectors"]:
        for h in s["heroes"]:
            first = h["verdict"].split(" ")[0].split("—")[0].upper()
            assert first in {"BUY", "USE", "WATCH", "SKIP"}, h["verdict"]


def test_subject_format():
    e = _edition()
    e["subject"] = email_render.subject(e)
    assert e["subject"].startswith("APPROVAL REQUIRED: Daily AI Short - "), e["subject"]


def test_all_news_covers_everything():
    e = _edition()
    assert len(e["all_news"]) >= 40, len(e["all_news"])
    heroes = sum(len(s["heroes"]) for s in e["sectors"])
    other = sum(len(s["other_news"]) for s in e["sectors"])
    assert len(e["all_news"]) == heroes + other


def test_compact_email_under_gmail_limit():
    e = _edition()
    e["subject"] = email_render.subject(e)
    html = email_render.render_html(e, mode="compact")
    size = len(html.encode("utf-8"))
    assert size < GMAIL_CLIP_BYTES, f"compact email is {size} bytes (>{GMAIL_CLIP_BYTES})"
    for name in SECTORS:  # every sector visible in the email
        assert name in html, f"sector {name} not in compact email"


def test_plaintext_has_exact_spec_labels():
    e = _edition()
    e["subject"] = email_render.subject(e)
    txt = email_render.render_text(e)
    for label in ["🎬 THE NEWS :", "SOURCE LINKS:", "THEIR FOUNDING STORY:",
                  "WHO SHOULD USE THIS:", "WHO SHOULD PURCHASE THIS:",
                  "FREE TOOLS SIMILAR OR BETTER:"]:
        assert txt.count(label) >= 40, f"'{label}' appears {txt.count(label)} times (expected >=40)"


def test_all_news_page_renders():
    e = _edition()
    html = email_render.render_all_news_html(e)
    assert "Deep Dive" in html and "All News" in html
    for name in SECTORS:
        assert name in html


def test_quality_gate_passes_real_edition():
    # The researched seed edition is genuine AI/expert content — it must pass.
    e = _edition()
    ok, reason = run.edition_quality_ok(e)
    assert ok, f"real edition wrongly blocked: {reason}"


def test_quality_gate_blocks_template_placeholders():
    # An edition made entirely of fallback template text must be blocked so it
    # can never overwrite a good edition on the live site.
    templated = {
        "sectors": [{"sector": "AI", "heroes": [
            {"headline": f"H{i}", "founding_story": "To be verified on the next run."}
            for i in range(5)]}],
        "top_products": [
            {"name": f"P{i}", "deep_review": "Written automatically by the AI on each cloud run."}
            for i in range(3)],
    }
    ok, reason = run.edition_quality_ok(templated)
    assert not ok, f"template edition wrongly published: {reason}"


def test_trends_have_volume_and_ranking():
    import keywords
    e = _edition()
    t = keywords.build_trends(e)
    ks = t["keywords"]
    assert len(ks) >= 15, f"only {len(ks)} keywords"
    # every keyword carries the requested properties
    for k in ks:
        assert isinstance(k["volume"], int) and k["volume"] > 0
        assert k["keyword"] and k["mentions"] >= 1 and k["platforms"]
    # ranking is contiguous and volume-ordered
    assert [k["rank"] for k in ks] == list(range(1, len(ks) + 1))
    assert all(ks[i]["volume"] >= ks[i + 1]["volume"] for i in range(len(ks) - 1))
    assert len(t["topics"]) >= 1


def test_trends_momentum_vs_previous():
    import keywords
    e = _edition()
    prev = {k["keyword"]: 1 for k in keywords.extract_keywords(e)}  # tiny prev volumes
    ks = keywords.extract_keywords(e, prev_volumes=prev)
    assert any(k["trend"] == "▲ rising" for k in ks), "expected rising vs low prev volumes"


def test_trends_provider_adds_search_volume_without_hijacking_ranking():
    import keywords
    e = _edition()
    base = keywords.extract_keywords(e)
    ks = keywords.extract_keywords(e, volume_provider=lambda kw: 777)
    # search_volume is populated from the provider ...
    assert ks and all(k["search_volume"] == 777.0 for k in ks)
    # ... but the default 'volume' ranking is unchanged (news-relevance stays).
    assert [k["keyword"] for k in ks] == [k["keyword"] for k in base]
    assert all(k["search_volume"] is None for k in base)


def test_gtrends_anchor_normalization_is_comparable():
    # Offline unit test of the cross-batch normalization math (no network).
    import gtrends
    batches = [
        {"chatgpt": 50, "humanoid robot": 25, "chip": 100},   # anchor=50
        {"chatgpt": 80, "evtol": 40, "drone swarm": 20},       # anchor=80
    ]
    out = gtrends._normalize(batches, "chatgpt")
    assert out["humanoid robot"] == 50.0   # 25/50*100
    assert out["chip"] == 200.0            # 100/50*100
    assert out["evtol"] == 50.0            # 40/80*100
    assert "chatgpt" not in out            # anchor itself excluded


def test_gtrends_volume_map_safe_without_network():
    # Must degrade to a dict (never raise) when Trends/pytrends is unavailable.
    import gtrends
    assert isinstance(gtrends.volume_map([]), dict)


def test_quality_gate_blocks_empty_edition():
    ok, reason = run.edition_quality_ok({"sectors": [], "top_products": []})
    assert not ok and "empty" in reason


def test_quality_gate_tolerates_a_few_fallbacks():
    # Mostly-real edition with one templated product should still publish.
    e = _edition()
    e = dict(e)
    e["top_products"] = [{"name": "X", "deep_review": "written automatically on each cloud run."}]
    ok, reason = run.edition_quality_ok(e)
    assert ok, f"mostly-real edition wrongly blocked: {reason}"


# ---- standalone runner (no pytest needed) ----
if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {t.__name__}: {e}")
            failed += 1
        except Exception as e:  # noqa
            print(f"  ✗ {t.__name__}: ERROR {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
