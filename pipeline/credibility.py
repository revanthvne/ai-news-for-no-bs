"""Source-legitimacy gate — the "no fake news" layer.

We keep an allowlist of reputable outlets + official newsrooms. Every story is
tagged high / medium / low based on its source domain. In LIVE mode, low-trust
or unknown domains are filtered OUT before a story can become a hero, so junk
and content-farm 'news' never reaches an edition.
"""
from __future__ import annotations
from urllib.parse import urlparse

# Tier 1 — major wire services, national press, top tech desks: "high"
HIGH = {
    "reuters.com", "bloomberg.com", "cnbc.com", "apnews.com", "wsj.com", "ft.com",
    "nytimes.com", "washingtonpost.com", "theguardian.com", "economist.com",
    "theverge.com", "techcrunch.com", "arstechnica.com", "wired.com",
    "engadget.com", "theinformation.com", "axios.com", "forbes.com",
    "nikkei.com", "asia.nikkei.com", "koreaherald.com", "cnn.com", "bbc.com",
    "ieee.org", "spectrum.ieee.org", "tomshardware.com", "anandtech.com",
    "marketwatch.com", "fool.com", "barrons.com", "businessinsider.com",
    "defensenews.com", "breakingdefense.com", "navalnews.com", "flightglobal.com",
    "aviationweek.com", "euronews.com", "venturebeat.com", "siliconangle.com",
    "gulfnews.com", "pcworld.com", "androidpolice.com", "androidcentral.com",
    "phonearena.com", "gamespot.com", "techradar.com", "restofworld.org",
    "kyivpost.com", "fedscoop.com", "insidedefense.com",
    "electrek.co", "qz.com", "macrumors.com", "macworld.com", "huggingface.co",
    "9to5mac.com", "9to5google.com", "electrifynews.com", "theregister.com",
}

# Tier 2 — specialist trade press, respected blogs, PR wires, official-ish: "medium"
MEDIUM = {
    "semiengineering.com", "eetimes.com", "trendforce.com", "digitimes.com",
    "therobotreport.com", "dronedj.com", "dronexl.co", "evtol.com", "flying-mag.com",
    "flyingmag.com", "aerotime.aero", "interestingengineering.com", "neowin.net",
    "technode.com", "kedglobal.com", "sof.news", "cio.com", "coindesk.com",
    "lowaltitudeeconomy.aero", "airdatanews.com", "ossinsight.io", "crunchbase.com",
    "24-7 wallst.com", "247wallst.com", "tomsguide.com", "pitchbook.com",
    "news.ycombinator.com", "producthunt.com",  # user-requested discovery sources
    "the-decoder.com", "techtimes.com", "techspot.com", "thenewstack.io",
    "morganlewis.com", "pillsburylaw.com", "dronedeploy.com", "tipranks.com",
    "focustaiwan.tw", "sammobile.com", "anysilicon.com", "dcd.com",
}

# Official company / primary domains are always trusted.
OFFICIAL_SUFFIXES = (
    "openai.com", "google.com", "blog.google", "anthropic.com", "microsoft.com",
    "nvidia.com", "amd.com", "tsmc.com", "samsung.com", "intel.com", "qualcomm.com",
    "meta.com", "apple.com", "valvesoftware.com", "steampowered.com",
    "jobyaviation.com", "archer.com", "beta.team", "verticalaerospace.com",
    "toyota.com", "bostondynamics.com", "figure.ai", "agilityrobotics.com",
    "ubtrobot.com", "dji.com", "skydio.com", "insta360.com", "anduril.com",
    "ondas.com", "github.com", "githubusercontent.com", "ollama.com",
    "businesswire.com", "prnewswire.com", "globenewswire.com",
)


def _domain(url: str) -> str:
    try:
        d = urlparse(url).netloc.lower()
        return d[4:] if d.startswith("www.") else d
    except Exception:
        return ""


def rate_domain(url: str) -> str:
    d = _domain(url)
    if not d:
        return "low"
    if d.endswith(".gov") or d.endswith(".gov.uk") or d.endswith(".mil"):
        return "high"  # primary government/official source
    if any(d == s or d.endswith("." + s) for s in OFFICIAL_SUFFIXES):
        return "high"
    if d in HIGH:
        return "high"
    if d in MEDIUM:
        return "medium"
    # subdomains of known outlets
    if any(d.endswith("." + h) for h in HIGH):
        return "high"
    if any(d.endswith("." + m) for m in MEDIUM):
        return "medium"
    return "low"


def rate_story(source_links) -> str:
    """Best (highest) rating across a story's links."""
    order = {"high": 3, "medium": 2, "low": 1}
    best = "low"
    for l in source_links or []:
        r = rate_domain(l)
        if order[r] > order[best]:
            best = r
    return best


def source_label(url: str) -> str:
    d = _domain(url)
    return d or "source"


def is_publishable(source_links) -> bool:
    """A story may run only if it has at least one medium+ source."""
    return rate_story(source_links) in {"high", "medium"}


def audit(stories) -> dict:
    """Summarize the credibility of an edition's stories."""
    counts = {"high": 0, "medium": 0, "low": 0}
    for s in stories:
        counts[rate_story(s.get("source_links", []))] += 1
    return counts
