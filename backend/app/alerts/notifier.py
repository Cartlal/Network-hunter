import asyncio
import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger("netmap.notifier")

SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
ALERT_EMAIL_TO = os.environ.get("ALERT_EMAIL_TO")


def _send_email_sync(subject: str, body: str) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = SMTP_USER
    message["To"] = ALERT_EMAIL_TO
    message.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=5) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(message)


async def notify(alerts: list) -> None:
    """In-app delivery (DB + WebSocket) always happens via the caller.
    Email is best-effort and only attempted if SMTP is configured via env
    vars - most users won't set this up, which is fine, the alerts still
    show up in the Alerts feed."""
    if not (SMTP_HOST and SMTP_USER and SMTP_PASSWORD and ALERT_EMAIL_TO):
        return

    critical = [a for a in alerts if getattr(a, "severity", None) == "critical"]
    if not critical:
        return

    subject = f"NetMap Live: {len(critical)} critical alert(s)"
    body = "\n".join(a.message for a in critical)
    try:
        await asyncio.to_thread(_send_email_sync, subject, body)
    except Exception:
        logger.exception("Failed to send alert email")
