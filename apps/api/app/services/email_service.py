from __future__ import annotations

import json
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from app.core.config import settings

OUTBOX_DIR = settings.storage_dir / 'email_outbox'
OUTBOX_DIR.mkdir(parents=True, exist_ok=True)


def _save_outbox(to_email: str, subject: str, body: str, meta: dict[str, Any] | None = None) -> None:
    payload = {
        'to': to_email,
        'subject': subject,
        'body': body,
        'meta': meta or {},
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    path = OUTBOX_DIR / f"email_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{abs(hash(to_email))}.json"
    path.write_text(json.dumps(payload, indent=2), encoding='utf-8')


def send_email(to_email: str, subject: str, body: str, *, html: str | None = None, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    if not settings.smtp_host:
        _save_outbox(to_email, subject, body, meta)
        print(f"[dev-email] To: {to_email} | Subject: {subject}\n{body}")
        return {'sent': False, 'mode': 'dev_outbox', 'detail': 'SMTP is not configured. Email written to dev outbox/logs.'}

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    msg['To'] = to_email
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype='html')

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
    return {'sent': True, 'mode': 'smtp'}


def send_verification_code(to_email: str, code: str, name: str = '') -> dict[str, Any]:
    subject = 'Your Privacy Toolbox verification code'
    body = (
        f"Hi {name or 'there'},\n\n"
        f"Your Privacy Toolbox verification code is: {code}\n\n"
        f"This code expires in {settings.verification_code_ttl_minutes} minutes. "
        "If you did not create this account, you can ignore this email.\n\n"
        "Privacy Toolbox"
    )
    html = f"""
    <div style='font-family:Inter,Arial,sans-serif;line-height:1.6;color:#0f172a'>
      <h2>Verify your Privacy Toolbox account</h2>
      <p>Use this code to verify your email address:</p>
      <p style='font-size:28px;font-weight:800;letter-spacing:6px;background:#eef6ff;padding:16px;border-radius:14px;display:inline-block'>{code}</p>
      <p>This code expires in {settings.verification_code_ttl_minutes} minutes.</p>
    </div>
    """
    return send_email(to_email, subject, body, html=html, meta={'verification_code': code})
