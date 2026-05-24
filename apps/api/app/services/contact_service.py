from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from app.core.config import settings
from app.core.security import random_id
from app.services.email_service import send_email

CONTACT_DIR = settings.storage_dir / 'contact'
CONTACT_DIR.mkdir(parents=True, exist_ok=True)
CONTACT_FILE = CONTACT_DIR / 'messages.json'



def _load() -> list[dict[str, Any]]:
    if not CONTACT_FILE.exists():
        return []
    try:
        return json.loads(CONTACT_FILE.read_text(encoding='utf-8'))
    except Exception:
        return []


def _save(rows: list[dict[str, Any]]) -> None:
    tmp = CONTACT_FILE.with_suffix('.tmp')
    tmp.write_text(json.dumps(rows, indent=2), encoding='utf-8')
    tmp.replace(CONTACT_FILE)


def create_message(payload: dict[str, Any], request_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    email = str(payload.get('email') or '').strip().lower()
    if not email or '@' not in email:
        raise ValueError('A valid email address is required.')
    message = str(payload.get('message') or '').strip()
    if len(message) < 10:
        raise ValueError('Please enter a message with at least 10 characters.')
    row = {
        'id': random_id('msg'),
        'first_name': str(payload.get('first_name') or '').strip()[:80],
        'last_name': str(payload.get('last_name') or '').strip()[:80],
        'email': email,
        'subject': str(payload.get('subject') or 'Website contact').strip()[:160],
        'message': message[:5000],
        'status': 'new',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'request_meta': request_meta or {},
    }
    rows = _load()
    rows.insert(0, row)
    _save(rows[:1000])
    # Notify admin if SMTP configured; otherwise written to dev outbox/logs.
    body = f"New Privacy Toolbox contact message\n\nFrom: {row['first_name']} {row['last_name']} <{email}>\nSubject: {row['subject']}\n\n{row['message']}"
    send_email(settings.contact_admin_email, f"Privacy Toolbox contact: {row['subject']}", body, meta={'contact_id': row['id']})
    return {'ok': True, 'id': row['id']}


def list_messages() -> list[dict[str, Any]]:
    return _load()


def mark_message(message_id: str, status: str = 'read') -> dict[str, Any]:
    rows = _load()
    for row in rows:
        if row.get('id') == message_id:
            row['status'] = status
            row['updated_at'] = datetime.now(timezone.utc).isoformat()
            _save(rows)
            return row
    raise ValueError('Message not found.')
