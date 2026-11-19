# -*- coding: utf-8 -*-
"""pages/key_health.py - RA04, 19 Nov 2026. An email when a key stops
working, instead of features quietly stopping.

Demetri, 19 Nov: "If there is a problem with the key in the future, also
with the Anthropic key, can the system send me an email letting me
know.... instead of just to stop working?" - then: "The email should go
to me only. Leave the working again email. Let's increase the time to 60
minutes of failing. Just one email daily, covering all keys - and showing
the status of all keys"; "The email, ONLY if their is a problem on one
key".

How it knows
  1. Every real call to Anthropic (all of them go through the SDK's
     messages.create, wrapped here once at start-up) and to Google Places
     (travel/gplaces.py) reports how it went.
  2. On Railway, a watcher in the web process checks both keys every 15
     minutes with calls that cost nothing: Anthropic's list of models,
     and Google's IDs-only place search (no charge at any volume).
  Only problems someone has to fix count: a key refused, missing or
  switched off, out of credit, over a limit - or a service not answering
  at all. A request we got wrong (400 for any other reason) is ours, not
  the key's.

When it emails
  A key has been failing for 60 minutes with no success in between, and
  no email has gone today. One email, to Demetri only (KEY_ALERT_EMAIL on
  Railway, else the first superuser's address), listing every key and
  how it is. Nothing when all is well; no "working again" email.

Never the key itself - not in the table, the email or a log. Never from a
test (every suite is a test_*.py script) and never off Railway, unless a
caller asks.
"""
import datetime as dt
import logging
import os
import sys
import threading
import time

logger = logging.getLogger(__name__)

FAIL_FOR = dt.timedelta(minutes=60)
EVERY = 15 * 60
SERVICES = [
    ('anthropic', 'Anthropic (the AI)', 'ANTHROPIC_API_KEY',
     'reading forwarded booking emails, looking up places and hotels, '
     'Suggest things to do, Plan my days, recipe import, invoice checks, '
     'translations, gift ideas and the Wellness daily line'),
    ('google_places', 'Google Places', 'GOOGLE_PLACES_KEY',
     'checking suggested things to do for opening days, distance, rating '
     'and price'),
]
LABEL = {k: n for k, n, _e, _u in SERVICES}
WORDS = {
    'missing': '%s is not set on Railway.',
    'refused': 'The key was refused - check %s on Railway, and that it is '
               'still active.',
    'credit': 'Out of credit or billing stopped - top it up in the '
              "provider's console.",
    'limit': 'Over a usage limit - check the limits in the provider\'s '
             'console.',
    'down': 'The service did not answer.',
}
_seen_ok = {}


def _quiet():
    """Never from a test script."""
    return os.path.basename(sys.argv[0] or '').startswith('test_')


def _now():
    from django.utils import timezone
    return timezone.now()


# ----------------------------------------------------------- what failed
def classify_anthropic(e):
    """(problem, detail) for an Anthropic error that someone must fix;
    None for one that is our own (a bad request)."""
    status = getattr(e, 'status_code', None)
    msg = str(e).lower()
    name = type(e).__name__
    if 'credit balance' in msg or 'billing' in msg:
        return 'credit', WORDS['credit']
    if status == 401 or name == 'AuthenticationError':
        return 'refused', WORDS['refused'] % 'ANTHROPIC_API_KEY'
    if status == 403 or name == 'PermissionDeniedError':
        return 'refused', WORDS['refused'] % 'ANTHROPIC_API_KEY'
    if status == 429 or name == 'RateLimitError':
        return 'limit', WORDS['limit']
    if (status and status >= 500) or name in ('APIConnectionError',
                                              'APITimeoutError'):
        return 'down', WORDS['down']
    if 'api_key' in msg and ('must be set' in msg or 'not set' in msg):
        return 'missing', WORDS['missing'] % 'ANTHROPIC_API_KEY'
    return None


def classify_google(status):
    if status in (400, 401, 403):
        return 'refused', ('The key was refused, or billing or the Places '
                           'API (New) is switched off - check Google Cloud '
                           'and GOOGLE_PLACES_KEY on Railway.')
    if status == 429:
        return 'limit', WORDS['limit']
    return 'down', WORDS['down']


# ------------------------------------------------------------- recording
def record(service, ok, problem='', detail=''):
    """Note how a call went - in the background, on its own database
    connection, so a caller's transaction is never touched."""
    if _quiet():
        return
    if ok:
        last = _seen_ok.get(service)
        if last and time.time() - last < 600:
            return
        _seen_ok[service] = time.time()
    else:
        _seen_ok.pop(service, None)

    def go():
        from django.db import close_old_connections
        try:
            save(service, ok, problem, detail)
            if not ok:
                maybe_email()
        except Exception:                               # noqa: BLE001
            logger.exception('key health %s', service)
        finally:
            close_old_connections()
    threading.Thread(target=go, daemon=True).start()


def save(service, ok, problem='', detail='', now=None):
    from .models import KeyStatus
    now = now or _now()
    row, _ = KeyStatus.objects.get_or_create(service=service)
    row.last_checked = now
    if ok:
        row.ok, row.problem, row.detail = True, '', ''
        row.failing_since, row.last_ok = None, now
    else:
        if row.ok or row.failing_since is None:
            row.failing_since = now
        row.ok, row.problem, row.detail = False, problem[:20], detail[:255]
    row.save()
    return row


# ------------------------------------------------------------ the email
def recipient():
    to = (os.environ.get('KEY_ALERT_EMAIL') or '').strip()
    if to:
        return to
    from django.contrib.auth.models import User
    u = User.objects.filter(is_superuser=True, is_active=True).exclude(
        email='').order_by('id').first()
    return u.email if u else ''


def _when(t):
    from django.utils import timezone
    t = timezone.localtime(t)
    return '%s %d %s at %s' % (t.strftime('%a'), t.day, t.strftime('%b'),
                               t.strftime('%H:%M'))


def lines(now=None):
    """Every key and how it is, in words."""
    from .models import KeyStatus
    rows = {r.service: r for r in KeyStatus.objects.all()}
    out = []
    for k, name, env, uses in SERVICES:
        r = rows.get(k)
        if r is None or r.last_checked is None:
            state = 'Not checked yet.'
        elif r.ok:
            state = 'Working (last checked %s).' % _when(r.last_checked)
        else:
            state = 'NOT WORKING since %s. %s' % (
                _when(r.failing_since or r.last_checked), r.detail)
        out.append({'service': k, 'name': name, 'ok': bool(r and r.ok),
                    'state': state, 'uses': uses})
    return out


def due(now=None):
    """A key failing for 60 minutes, and no email yet today."""
    from django.utils import timezone
    from .models import KeyStatus
    now = now or _now()
    today = timezone.localdate(now)
    if KeyStatus.objects.filter(emailed_on=today).exists():
        return False
    return KeyStatus.objects.filter(
        ok=False, failing_since__lte=now - FAIL_FOR).exists()


def maybe_email(now=None, send=None):
    """Send the one email of the day, if one is due. True if sent."""
    from django.core.mail import EmailMessage
    from django.utils import timezone
    from .models import KeyStatus
    now = now or _now()
    if not due(now):
        return False
    today = timezone.localdate(now)
    for k, _n, _e, _u in SERVICES:
        KeyStatus.objects.get_or_create(service=k)
    # One sender only, however many web workers notice at once.
    if not KeyStatus.objects.exclude(emailed_on=today).update(
            emailed_on=today):
        return False
    to = recipient()
    if not to:
        logger.warning('key health: nobody to email')
        return False
    ls = lines(now)
    bad = [x['name'] for x in ls if not x['ok']]
    body = ['A key Alivente Online uses has stopped working for an hour or '
            'more.', '']
    for x in ls:
        body.append('%s: %s' % (x['name'], x['state']))
        if not x['ok']:
            body.append('  Not working because of it: %s.' % x['uses'])
        body.append('')
    body += ['Fix it in the provider\'s console or on Railway (Variables). '
             'Alivente checks again every 15 minutes; this email comes at '
             'most once a day, and only while a key has a problem.', '',
             'Alivente Online']
    msg = EmailMessage(
        subject='Alivente Online - %s not working' % ' and '.join(bad),
        body='\n'.join(body), to=[to])
    (send or (lambda m: m.send(fail_silently=False)))(msg)
    return True


# --------------------------------------------------------------- checks
def probe_anthropic():
    key = (os.environ.get('ANTHROPIC_API_KEY') or '').strip()
    if not key:
        return False, 'missing', WORDS['missing'] % 'ANTHROPIC_API_KEY'
    try:
        import anthropic
        anthropic.Anthropic(api_key=key).models.list(limit=1)
    except Exception as e:                              # noqa: BLE001
        c = classify_anthropic(e) or ('down', WORDS['down'])
        return False, c[0], c[1]
    return True, '', ''


def probe_google(opener=None):
    import json
    import urllib.error
    import urllib.request
    key = (os.environ.get('GOOGLE_PLACES_KEY') or '').strip()
    if not key:
        return False, 'missing', WORDS['missing'] % 'GOOGLE_PLACES_KEY'
    req = urllib.request.Request(
        'https://places.googleapis.com/v1/places:searchText',
        data=json.dumps({'textQuery': 'Nicosia', 'maxResultCount': 1}
                        ).encode('utf-8'), method='POST',
        # IDs only: Google's free tier at any volume.
        headers={'Content-Type': 'application/json', 'X-Goog-Api-Key': key,
                 'X-Goog-FieldMask': 'places.id'})
    try:
        with (opener or urllib.request.urlopen)(req, timeout=10) as r:
            r.read()
    except urllib.error.HTTPError as e:
        p, d = classify_google(e.code)
        return False, p, d
    except Exception:                                   # noqa: BLE001
        return False, 'down', WORDS['down']
    return True, '', ''


def check_all(now=None):
    """Both keys, then the email if one is due."""
    for service, probe in (('anthropic', probe_anthropic),
                           ('google_places', probe_google)):
        ok, p, d = probe()
        save(service, ok, p, d, now=now)
    return maybe_email(now)


# ------------------------------------------------------------- start-up
def wrap_anthropic():
    """Every messages.create reports how it went - once, at start-up."""
    try:
        from anthropic.resources.messages import Messages
    except Exception:                                   # noqa: BLE001
        return False
    if getattr(Messages.create, '_alv_watched', False):
        return True
    orig = Messages.create

    def create(self, *a, **kw):
        try:
            out = orig(self, *a, **kw)
        except Exception as e:
            c = classify_anthropic(e)
            if c:
                record('anthropic', False, c[0], c[1])
            raise
        record('anthropic', True)
        return out
    create._alv_watched = True
    Messages.create = create
    return True


def start_watcher():
    """On Railway's web process only: check every 15 minutes."""
    if _quiet() or not os.environ.get('RAILWAY_ENVIRONMENT'):
        return False
    if 'gunicorn' not in ' '.join(sys.argv) and \
            'runserver' not in sys.argv:
        return False

    def loop():
        from django.db import close_old_connections
        time.sleep(120)
        while True:
            try:
                check_all()
            except Exception:                           # noqa: BLE001
                logger.exception('key health watcher')
            finally:
                close_old_connections()
            time.sleep(EVERY)
    threading.Thread(target=loop, daemon=True, name='alv-key-health').start()
    return True
