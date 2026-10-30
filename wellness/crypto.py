# -*- coding: utf-8 -*-
"""wellness/crypto.py - WL-2, 30 Oct 2026. The journal's lock.

DECISION 5, 30 OCT: journal text is encrypted at rest. A copy of the
database - a backup, a dump, somebody with a SQL prompt - shows tokens,
not words.

THE KEY IS ITS OWN SETTING, WELLNESS_JOURNAL_KEY, set in Railway's
variables. It is deliberately NOT derived from SECRET_KEY: rotating the
app's secret one day must never make every journal unreadable. Generate
one with

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

KEEP A COPY SOMEWHERE SAFE. Without the key the entries cannot be read by
anybody, including us - that is what encrypted means.

Without the variable (a laptop, the gate) a key is derived from
SECRET_KEY so development works; wellness/views.py says so on the journal
page for a superuser, so Live is never left on the fallback unnoticed.

Several keys may be given, comma-separated, newest first: MultiFernet
writes with the first and reads with any, so a key can be rotated
without losing an entry.
"""
import base64
import hashlib
import json
import os

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from django.conf import settings

ENV = 'WELLNESS_JOURNAL_KEY'


def configured():
    return bool(os.environ.get(ENV, '').strip())


def _fernet():
    raw = os.environ.get(ENV, '').strip()
    if raw:
        keys = [Fernet(k.strip().encode()) for k in raw.split(',')
                if k.strip()]
        return MultiFernet(keys)
    derived = base64.urlsafe_b64encode(hashlib.sha256(
        ('wellness-journal:' + settings.SECRET_KEY).encode()).digest())
    return MultiFernet([Fernet(derived)])


def seal(data):
    """dict -> token (str)."""
    return _fernet().encrypt(json.dumps(data).encode('utf-8')).decode()


def open_(token):
    """token -> dict. An entry that cannot be opened (the wrong key)
    comes back saying so, rather than crashing the page."""
    if not token:
        return {}
    try:
        return json.loads(_fernet().decrypt(token.encode()).decode('utf-8'))
    except (InvalidToken, ValueError):
        return {'locked': True}
