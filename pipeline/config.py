"""Central configuration. Reads from environment (.env) with safe defaults
so the pipeline always runs — even with no keys at all."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except Exception:
    pass  # dotenv optional

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CHANNEL_NAME = "NO BS — Should You Buy This?"
BRAND_TAGLINE = "The hype, the reality, and whether your money is worth it."

# The categories the channel covers, used to steer live fetching + ranking.
CATEGORIES = [
    "AI", "Semiconductors", "Robotics", "eVTOL", "Drones",
    "Hardware", "Stocks", "Open Source",
]

# --- LLM ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "none").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# --- Email ---
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "none").lower()
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "NO BS Daily <daily@example.com>")
APPROVER_EMAIL = os.getenv("APPROVER_EMAIL", "")  # set in .env — no address hardcoded
# "compact" keeps the daily email small (scannable cards + links) so Gmail
# (which clips messages over ~102 KB) shows it in full. "full" inlines every
# deep-dive (large — good for Apple Mail, will be clipped in Gmail).
EMAIL_MODE = os.getenv("EMAIL_MODE", "compact")  # compact | full

# When true, scheduled editions publish straight to the live site (no approval
# gate). Set AUTO_PUBLISH=false to require the email Approve button first.
AUTO_PUBLISH = os.getenv("AUTO_PUBLISH", "true").lower() == "true"
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

# --- Optional enrichment ---
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# --- Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

APPROVE_BASE_URL = os.getenv("APPROVE_BASE_URL", "http://localhost:3000")

# How many hero (deep-dive) stories per edition.
HERO_COUNT = 5

def has_llm() -> bool:
    return LLM_PROVIDER in {"groq", "openai", "anthropic"} and bool(
        {"groq": GROQ_API_KEY, "openai": OPENAI_API_KEY, "anthropic": ANTHROPIC_API_KEY}.get(LLM_PROVIDER)
    )

def has_email() -> bool:
    if EMAIL_PROVIDER == "resend":
        return bool(RESEND_API_KEY)
    if EMAIL_PROVIDER == "smtp":
        return bool(SMTP_HOST and SMTP_USER and SMTP_PASS)
    return False
