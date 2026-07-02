"""Render a SECTOR-STRUCTURED edition into email + the All-News firehose page.

Edition shape (from assemble.py):
  { edition_date, subject, sectors:[{sector,slug,heroes:[...5...],other_news:[...]}],
    all_news:[...], lead:{headline,sector} }

Outputs:
  - subject(edition)            -> "APPROVAL REQUIRED: Daily AI Short - <lead>"
  - render_html(edition)        -> sector layout, images, per-story collapsible
                                   Deep Dive, credibility tags, + global All-News button
  - render_text(edition)        -> literal plain-text version (exact spec sections)
  - render_all_news_html(...)   -> the "Deep Dive — All News" firehose page
"""
from __future__ import annotations
import html
from typing import Dict, List

import config

SECTOR_EMOJI = {
    "AI": "🧠", "Semiconductors": "🔩", "Robotics": "🤖", "eVTOL": "🚁",
    "Drones": "🛸", "Hardware": "📱", "Stocks": "📈", "Open Source": "🐙",
}


def subject(edition: Dict) -> str:
    if edition.get("subject"):
        return edition["subject"]
    lead = edition.get("lead", {}).get("headline") or "Daily AI Short"
    return f"APPROVAL REQUIRED: Daily AI Short - {lead}"


def _esc(x: str) -> str:
    return html.escape(x or "")


def all_news_href(edition: Dict) -> str:
    return f"{config.APPROVE_BASE_URL}/all-news/{edition['edition_date']}"


# ─────────────────────────── PLAIN TEXT ───────────────────────────

def _text_hero(s: Dict, i: int) -> str:
    links = ", ".join(l for l in s.get("source_links", []) if l)
    return "\n".join([
        f"  ── Story {i}: {s['headline']}",
        f"     🎬 THE NEWS : {s.get('one_liner','')}",
        f"     SOURCE LINKS: {links}",
        f"     SOURCE / CREDIBILITY: {s.get('source_name','')} ({s.get('credibility','')})",
        f"     STORY: {s.get('story','')}",
        f"     THEIR FOUNDING STORY: {s.get('founding_story','')}",
        f"     WHO SHOULD USE THIS: {s.get('who_should_use','')}",
        f"     WHO SHOULD PURCHASE THIS: {s.get('who_should_buy','')}",
        f"     FREE TOOLS SIMILAR OR BETTER: {s.get('free_alternatives','')}",
        f"     VERDICT: {s.get('verdict','')}",
        "",
    ])


def render_text(edition: Dict) -> str:
    parts = [
        subject(edition), "",
        f"{config.CHANNEL_NAME} | Daily AI Short | {edition['edition_date']}",
        f"{edition['counts']['heroes']} deep-dives across {edition['counts']['sectors']} sectors "
        f"· {edition['counts']['all_news']} stories total.",
        f"DEEP DIVE — ALL NEWS: {all_news_href(edition)}",
        "Reply APPROVE to publish or REJECT to skip.", "",
    ]
    for sec in edition["sectors"]:
        parts.append("=" * 60)
        parts.append(f"{sec['sector'].upper()}  ({len(sec['heroes'])} deep-dives)")
        parts.append("=" * 60)
        for i, s in enumerate(sec["heroes"], 1):
            parts.append(_text_hero(s, i))
        if sec.get("other_news"):
            parts.append(f"  More in {sec['sector']}:")
            for o in sec["other_news"]:
                parts.append(f"    • {o.get('headline','')} ({o.get('source_name','')}) "
                             f"{(o.get('source_links') or [''])[0]}")
            parts.append("")
    return "\n".join(parts)


# ─────────────────────────── HTML EMAIL ───────────────────────────

def _cred_tag(s: Dict) -> str:
    c = (s.get("credibility") or "low").lower()
    color = {"high": "#22c55e", "medium": "#f59e0b", "low": "#ef4444"}.get(c, "#8a97a6")
    name = _esc(s.get("source_name", "source"))
    check = "✓ " if c == "high" else ""
    return (f'<span style="display:inline-block;padding:2px 9px;border-radius:999px;'
            f'background:{color}22;color:{color};font:700 11px Arial;">{check}{name} · {c}</span>')


def _verdict_pill(v: str) -> str:
    key = (v or "").split(" ")[0].split("—")[0].upper()
    color = {"BUY": "#22c55e", "USE": "#3b82f6", "WATCH": "#f59e0b", "SKIP": "#ef4444"}.get(key, "#00e0b8")
    return (f'<span style="display:inline-block;padding:3px 11px;border-radius:999px;'
            f'background:{color}22;color:{color};font:700 12px Arial;">{_esc(v)}</span>')


def _section(label: str, body: str) -> str:
    if not body:
        return ""
    return (f'<div style="margin-top:12px;"><div style="font:700 11px Arial;letter-spacing:.06em;'
            f'text-transform:uppercase;color:#00e0b8;">{_esc(label)}</div>'
            f'<div style="font:400 14px/1.6 Arial;color:#e8eef2;margin-top:3px;">{_esc(body)}</div></div>')


def _links(links: List[str]) -> str:
    return "<br>".join(f'<a href="{_esc(l)}" style="color:#00e0b8;word-break:break-all;">{_esc(l)}</a>'
                       for l in links if l) or "—"


def _hero_card(s: Dict, i: int) -> str:
    img = _esc(s.get("image_url", ""))
    deep = "".join([
        _section("Source links", _links(s.get("source_links", []))),
        _section("The story", s.get("story", "")),
        _section("Their founding story", s.get("founding_story", "")),
        _section("Who should USE this", s.get("who_should_use", "")),
        _section("Who should PURCHASE this", s.get("who_should_buy", "")),
        _section("Free / better alternatives", s.get("free_alternatives", "")),
    ])
    return f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       style="background:#12161c;border:1px solid #232a33;border-radius:14px;margin:0 0 14px;overflow:hidden;">
      <tr><td>
        <img src="{img}" width="100%" alt="" style="display:block;width:100%;max-height:190px;object-fit:cover;">
      </td></tr>
      <tr><td style="padding:14px 20px 18px;">
        <div style="margin-bottom:8px;">{_verdict_pill(s.get('verdict',''))} &nbsp; {_cred_tag(s)}</div>
        <div style="font:700 11px Arial;color:#8a97a6;">STORY {i}</div>
        <h3 style="margin:3px 0 6px;font:800 18px/1.3 Arial;color:#fff;">{_esc(s.get('headline',''))}</h3>
        <div style="font:800 11px Arial;letter-spacing:.06em;text-transform:uppercase;color:#00e0b8;">🎬 The News</div>
        <div style="font:400 14px/1.5 Arial;color:#cdd6df;margin-top:2px;">{_esc(s.get('one_liner',''))}</div>
        <details style="margin-top:10px;">
          <summary style="cursor:pointer;color:#00e0b8;font:700 13px Arial;list-style:none;">🔎 Deep Dive — full breakdown</summary>
          <div style="margin-top:6px;">{deep}</div>
        </details>
      </td></tr>
    </table>"""


def _sector_block(sec: Dict) -> str:
    heroes = "".join(_hero_card(s, i) for i, s in enumerate(sec["heroes"], 1))
    emoji = SECTOR_EMOJI.get(sec["sector"], "•")
    more = ""
    if sec.get("other_news"):
        items = "".join(
            f'<li style="margin:0 0 8px;color:#cdd6df;font:400 13px/1.5 Arial;">'
            f'{_esc(o.get("headline",""))} '
            f'<a href="{_esc((o.get("source_links") or [""])[0])}" style="color:#00e0b8;">↗ {_esc(o.get("source_name",""))}</a></li>'
            for o in sec["other_news"])
        more = (f'<div style="background:#0e1319;border:1px solid #232a33;border-radius:12px;padding:14px 18px;margin:2px 0 8px;">'
                f'<div style="font:800 13px Arial;color:#8a97a6;margin-bottom:8px;">More in {_esc(sec["sector"])}</div>'
                f'<ul style="margin:0;padding-left:16px;">{items}</ul></div>')
    return f"""
    <tr><td style="padding:18px 8px 4px;">
      <div style="font:900 20px Arial;color:#fff;border-bottom:2px solid #232a33;padding-bottom:8px;margin-bottom:14px;">
        {emoji} {_esc(sec['sector'])}
        <span style="font:700 12px Arial;color:#8a97a6;">· {len(sec['heroes'])} deep-dives</span></div>
      {heroes}
      {more}
    </td></tr>"""


def render_html(edition: Dict, all_news_link: str | None = None) -> str:
    date = _esc(edition["edition_date"])
    eid = _esc(str(edition.get("edition_id", edition["edition_date"])))
    approve = f"{config.APPROVE_BASE_URL}/approve?edition={eid}&action=approve"
    reject = f"{config.APPROVE_BASE_URL}/approve?edition={eid}&action=reject"
    allnews = _esc(all_news_link or all_news_href(edition))
    c = edition["counts"]
    sectors_html = "".join(_sector_block(s) for s in edition["sectors"])

    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;background:#0a0d11;">
 <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0a0d11;">
  <tr><td align="center" style="padding:22px 12px;">
   <table role="presentation" width="660" cellpadding="0" cellspacing="0" style="max-width:660px;width:100%;">

    <tr><td style="padding:8px 8px 16px;">
      <div style="font:900 26px Arial;color:#fff;">NO BS <span style="color:#00e0b8;">·</span>
        <span style="color:#8a97a6;font-size:16px;">Should You Buy This?</span></div>
      <div style="font:600 13px Arial;color:#8a97a6;margin-top:4px;">
        Daily AI Short · {date} · {c['heroes']} deep-dives across {c['sectors']} sectors · {c['all_news']} stories</div>
    </td></tr>

    <tr><td style="padding:0 8px 14px;">
      <table role="presentation" width="100%" style="background:#12161c;border:1px solid #2b3a2f;border-radius:12px;">
       <tr><td style="padding:16px 20px;">
        <div style="font:700 13px Arial;color:#f59e0b;margin-bottom:10px;">⚠️ APPROVAL REQUIRED — review, then publish or skip.</div>
        <a href="{approve}" style="display:inline-block;background:#22c55e;color:#04120a;font:800 14px Arial;
           text-decoration:none;padding:11px 22px;border-radius:9px;margin:0 6px 6px 0;">✓ Approve &amp; publish</a>
        <a href="{reject}" style="display:inline-block;background:#1b2027;color:#ef6b6b;font:800 14px Arial;
           text-decoration:none;padding:11px 22px;border-radius:9px;border:1px solid #3a2429;margin:0 6px 6px 0;">✕ Reject</a>
        <a href="{allnews}" style="display:inline-block;background:#12233a;color:#7cc4ff;font:800 14px Arial;
           text-decoration:none;padding:11px 22px;border-radius:9px;border:1px solid #234;margin:0 0 6px 0;">🔍 Deep Dive — All News ({c['all_news']})</a>
       </td></tr>
      </table>
    </td></tr>

    {sectors_html}

    <tr><td style="padding:20px 12px;text-align:center;">
      <a href="{allnews}" style="color:#7cc4ff;font:800 14px Arial;text-decoration:none;">🔍 Open the full All-News firehose ({c['all_news']} stories) →</a>
      <div style="font:400 12px/1.6 Arial;color:#5a6672;margin-top:14px;">
        Every fact links to a primary source · {edition['credibility_audit']['high']} high-credibility /
        {edition['credibility_audit']['medium']} medium / {edition['credibility_audit']['low']} low ·
        not financial advice.</div>
    </td></tr>

   </table>
  </td></tr>
 </table>
</body></html>"""


# ─────────────────────── ALL-NEWS FIREHOSE PAGE ───────────────────────

def render_all_news_html(edition: Dict, back_link: str = "/") -> str:
    date = _esc(edition["edition_date"])
    # group by sector, preserving edition order
    by_sector = {}
    for item in edition["all_news"]:
        by_sector.setdefault(item["sector"], []).append(item)

    blocks = []
    for sec in edition["sectors"]:
        name = sec["sector"]
        items = by_sector.get(name, [])
        rows = []
        for it in items:
            c = (it.get("credibility") or "low").lower()
            cc = {"high": "#22c55e", "medium": "#f59e0b", "low": "#ef4444"}.get(c, "#8a97a6")
            link = _esc((it.get("source_links") or [""])[0])
            kind = "★" if it.get("kind") == "hero" else "·"
            rows.append(
                f'<div style="padding:10px 0;border-bottom:1px solid #1c232b;">'
                f'<span style="color:#00e0b8;">{kind}</span> '
                f'<a href="{link}" style="color:#e8eef2;text-decoration:none;font-weight:600;">{_esc(it.get("headline",""))}</a> '
                f'<span style="display:inline-block;padding:1px 8px;border-radius:999px;background:{cc}22;color:{cc};font:700 10px Arial;">{_esc(it.get("source_name",""))}</span>'
                f'<div style="color:#8a97a6;font:400 13px/1.5 Arial;margin-top:2px;">{_esc(it.get("one_liner",""))}</div></div>')
        blocks.append(
            f'<h2 style="color:#fff;font:900 20px Arial;margin:26px 0 8px;">{SECTOR_EMOJI.get(name,"•")} {_esc(name)} '
            f'<span style="color:#8a97a6;font:700 13px Arial;">· {len(items)}</span></h2>{"".join(rows)}')

    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>All News · {date}</title></head>
<body style="margin:0;background:#0a0d11;font-family:Arial,sans-serif;">
 <div style="max-width:760px;margin:0 auto;padding:24px 16px 80px;">
  <a href="{_esc(back_link)}" style="color:#00e0b8;text-decoration:none;">← Back to the edition</a>
  <h1 style="color:#fff;font-size:24px;margin:14px 0 2px;">🔍 Deep Dive — All News</h1>
  <div style="color:#8a97a6;font-size:13px;">{date} · every story we gathered, grouped by sector · ★ = deep-dive hero</div>
  {"".join(blocks)}
  <div style="color:#5a6672;font-size:12px;margin-top:40px;text-align:center;">
    Sources shown on every item · not financial advice.</div>
 </div>
</body></html>"""
