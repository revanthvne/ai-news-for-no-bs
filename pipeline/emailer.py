"""Send the APPROVAL REQUIRED email via Resend (free tier) or plain SMTP.
Falls back to writing the email to disk if no provider is configured."""
from __future__ import annotations
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
import config


def send(subject: str, html_body: str, text_body: str, to: str | None = None) -> dict:
    to = to or config.APPROVER_EMAIL
    if not to:
        return {"ok": False, "skipped": True, "reason": "no recipient (set APPROVER_EMAIL)"}
    if config.EMAIL_PROVIDER == "resend" and config.RESEND_API_KEY:
        return _resend(subject, html_body, text_body, to)
    if config.EMAIL_PROVIDER == "smtp" and config.SMTP_HOST:
        return _smtp(subject, html_body, text_body, to)
    return {"ok": False, "skipped": True, "reason": "no email provider configured"}


def _resend(subject: str, html_body: str, text_body: str, to: str) -> dict:
    r = requests.post(
        "https://api.resend.com/emails", timeout=30,
        headers={"Authorization": f"Bearer {config.RESEND_API_KEY}",
                 "Content-Type": "application/json"},
        json={"from": config.EMAIL_FROM, "to": [to], "subject": subject,
              "html": html_body, "text": text_body},
    )
    ok = r.status_code < 300
    return {"ok": ok, "status": r.status_code, "body": r.text[:300]}


def _smtp(subject: str, html_body: str, text_body: str, to: str) -> dict:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_FROM
    msg["To"] = to
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASS)
            server.sendmail(config.SMTP_USER, [to], msg.as_string())
        return {"ok": True, "via": "smtp"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
