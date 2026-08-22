"""Email helpers — log invite links when mail is not configured."""

from __future__ import annotations

import logging

from flask import current_app
from flask_mail import Message

from app.extensions import mail

logger = logging.getLogger(__name__)


def mail_is_configured() -> bool:
    server = current_app.config.get("MAIL_SERVER") or ""
    return bool(server.strip())


def build_invite_link(token: str) -> str:
    base = current_app.config.get("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    return f"{base}/accept-invite?token={token}"


def send_invite_email(to_email: str, token: str, role: str = "admin") -> str:
    """
    Send an invite email, or log the link when MAIL_SERVER is unset.

    Returns the invite URL (useful for tests / local development).
    """
    invite_url = build_invite_link(token)
    subject = f"MyDuka {role.title()} Invitation"
    body = (
        f"You have been invited to join MyDuka as a {role}.\n\n"
        f"Open this link to accept (it expires):\n{invite_url}\n"
    )

    if not mail_is_configured():
        logger.info(
            "MAIL not configured — invite link for %s (%s): %s",
            to_email,
            role,
            invite_url,
        )
        print(f"[MyDuka invite] {to_email} ({role}): {invite_url}")
        return invite_url

    msg = Message(
        subject=subject,
        recipients=[to_email],
        body=body,
        sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
    )
    mail.send(msg)
    return invite_url
