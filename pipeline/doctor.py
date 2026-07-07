"""Config doctor — surfaces anything still unset so nothing is a silent landmine.

Run directly:            python doctor.py
Called at pipeline start: prints WARN lines for placeholders/missing config,
but never blocks the run (the pipeline still works in offline/seed mode).
"""
from __future__ import annotations
import config

PLACEHOLDERS = ("example.com", "localhost", "YOUR-WEB-APP", "yourdomain.com")


def _is_placeholder(v: str) -> bool:
    return (not v) or any(p in v for p in PLACEHOLDERS)


def check() -> list[str]:
    warns: list[str] = []

    # LLM
    if not config.has_llm():
        warns.append("LLM not configured → deep-dives use template mode. "
                     "Set LLM_PROVIDER + a key (Groq is free) for real synthesis.")

    # Email
    if not config.has_email():
        warns.append("EMAIL not configured → the approval email is written to disk, not sent. "
                     "Set EMAIL_PROVIDER + key (Resend free tier) to send.")
    if _is_placeholder(config.APPROVER_EMAIL):
        warns.append("APPROVER_EMAIL is unset → no recipient for the APPROVAL email. Set it in .env.")
    if _is_placeholder(config.EMAIL_FROM):
        warns.append("EMAIL_FROM is a placeholder → set a verified sender (e.g. daily@yourdomain).")

    # Public URL for approve/deep-dive links
    if _is_placeholder(config.APPROVE_BASE_URL):
        warns.append("APPROVE_BASE_URL is localhost → email Approve/Deep-Dive links won't work "
                     "for a remote reader. Set it to your deployed Vercel URL.")

    # Supabase (optional but needed for web/mobile persistence)
    if not (config.SUPABASE_URL and config.SUPABASE_SERVICE_KEY):
        warns.append("SUPABASE not configured → web/mobile read static JSON only; "
                     "approvals/subscribers/push won't persist. (Optional.)")

    return warns


def print_report(prefix: str = "  ⚠ ") -> None:
    warns = check()
    if not warns:
        print("  ✓ config doctor: everything configured.")
        return
    print(f"  config doctor: {len(warns)} thing(s) to set (non-blocking):")
    for w in warns:
        print(prefix + w)


if __name__ == "__main__":
    print("NO BS · config doctor")
    print_report()
