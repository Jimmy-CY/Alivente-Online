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
     RA08, 20 Nov 2026 - but Google counts even free searches against its
     daily limit (100 a day on this project), and the watcher used it up:
     Google is now tried only while it is failing, once an hour, and the
     web workers share one watch (one check per 15 minutes in all, kept
     in the database). Real Suggest-things-to-do calls say how Google is
     the rest of the time. Google's own reason is kept and shown.
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


def google_reason(body):
    """RA08 - Google's own words for a refusal, from its error body: the
    limit by name ("SearchTextRequest per day, limit 100") or its message.
    Never the key (Google does not send it back; anything key-like is cut
    out anyway)."""
    import json
    import re
    try:
        err = json.loads(body or '{}').get('error') or {}
    except (ValueError, AttributeError):
        return ''
    for d in err.get('details') or []:
        m = d.get('metadata') or {}
        if m.get('quota_limit'):
            name = re.sub(r'PerProject$', '', m['quota_limit'])
            name = re.sub(r'Per(Day|Minute)', r' per \1', name).replace(
                ' per Day', ' per day').replace(' per Minute', ' per minute')
            lim = m.get('quota_limit_value')
            return 'Google says: quota exceeded - %s%s.' % (
                name, ' (limit %s)' % lim if lim else '')
    msg = re.sub(r'AIza[0-9A-Za-z_\-]{10,}', '[key]',
                 str(err.get('message') or ''))
    return ('Google says: %s' % msg.strip())[:160] if msg.strip() else ''


def classify_google(status, body=''):
    why = google_reason(body)
    if status in (400, 401, 403):
        p, d = 'refused', ('The key was refused, or billing or the Places '
                           'API (New) is switched off - check Google Cloud '
                           'and GOOGLE_PLACES_KEY on Railway.')
    elif status == 429:
        p, d = 'limit', WORDS['limit']
    else:
        p, d = 'down', WORDS['down']
    return p, ('%s %s' % (d, why)).strip()[:255]


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
        p, d = classify_google(e.code, _body(e))
        return False, p, d
    except Exception:                                   # noqa: BLE001
        return False, 'down', WORDS['down']
    return True, '', ''


def _body(e):
    try:
        return e.read().decode('utf-8', 'replace')[:4000]
    except Exception:                                   # noqa: BLE001
        return ''


GOOGLE_RETRY = dt.timedelta(minutes=60)
WATCH = '_watch'


def _my_turn(now):
    """RA08 - one check per 15 minutes for the whole app, however many web
    workers run a watcher: the first to move the shared mark wins."""
    from django.db.models import Q
    from .models import KeyStatus
    KeyStatus.objects.get_or_create(service=WATCH)
    return bool(KeyStatus.objects.filter(service=WATCH).filter(
        Q(last_checked__isnull=True) |
        Q(last_checked__lte=now - dt.timedelta(seconds=EVERY - 60))
    ).update(last_checked=now))


def google_due(now):
    """RA08 - Google is tried only while it is failing (or its key is
    missing), at most once an hour; when it works, real calls say so."""
    from .models import KeyStatus
    if not (os.environ.get('GOOGLE_PLACES_KEY') or '').strip():
        return True                     # missing: said without any call
    row = KeyStatus.objects.filter(service='google_places').first()
    if row is None or row.ok:
        return False
    return row.last_checked is None or \
        row.last_checked <= now - GOOGLE_RETRY


def check_all(now=None, force=False):
    """Anthropic (free, no daily limit); Google only when due (or forced,
    by hand); then the email if one is due. A watcher whose turn it is not
    does nothing."""
    now = now or _now()
    if not force and not _my_turn(now):
        return False
    ok, p, d = probe_anthropic()
    save('anthropic', ok, p, d, now=now)
    if force or google_due(now):
        ok, p, d = probe_google()
        save('google_places', ok, p, d, now=now)
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
