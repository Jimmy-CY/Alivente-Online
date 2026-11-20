# -*- coding: utf-8 -*-
"""apply_ra08_google_quota.py - round RA08, 20 Nov 2026.

RELEASE RA08 - THE KEY WATCH STOPS USING UP GOOGLE'S DAILY LIMIT.

    20 Nov: Google refused every search from 20:10 the evening before -
    "Quota exceeded ... limit 'SearchTextRequest per day'" (limit 100 on
    the key's project). RA04's watcher tried Google every 15 minutes in
    each web worker, and even a free search counts against that limit.
    Demetri: "OK. Lt's make these changes."

    - Google is tried by the watcher only while it is failing, once an
      hour; when it works, real calls say how it is.
    - The web workers share one watch (a mark in key_status): one check
      per 15 minutes for the whole app.
    - The email and manage.py check_keys show Google's own reason (the
      limit by name); never the key. check_keys tries both keys at once.
    - Help: Administration, System.

The suite ships beside this patcher. Stands on RA07. Idempotent. Edits
backed up to .bak_ra08. No migration.
"""
import os
import sys

SUFFIX = '.bak_ra08'
MARK = 'RA08, 20 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_ra08_google_quota.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_ra06_kind_round.py',
    # RA07, 19 Nov 2026 - weather from Things to do; spending on trip days.
    'test_ra07_trip_days.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_ra06_kind_round.py',
    # RA07, 19 Nov 2026 - weather from Things to do; spending on trip days.
    'test_ra07_trip_days.py',
    # RA08, 20 Nov 2026 - the key watch spares Google's daily limit.
    'test_ra08_google_quota.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # RA07, 19 Nov 2026 - weather from Things to do; spending on trip days.
    '.bak_ra07',
]

''',
         r'''    # RA07, 19 Nov 2026 - weather from Things to do; spending on trip days.
    '.bak_ra07',
    # RA08, 20 Nov 2026 - the key watch spares Google's daily limit.
    '.bak_ra08',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <div class="alert" style="background:#e7f5f8; border-left:4px solid #0e7c8b;" data-key-email-help>
      <i class="fas fa-key"></i> <strong>When a key stops working, you get an email.</strong>
      <p class="mb-0 mt-2">Alivente uses two outside services: <strong>Anthropic</strong> (the AI &ndash; reading booking emails, looking up places, suggestions, Plan my days, recipe import, invoice checks, translations, gift ideas, the Wellness daily line) and <strong>Google Places</strong> (checking suggested things to do for opening days, distance, rating and price). Every 15 minutes Alivente checks both keys, at no cost, and every use of them counts too. If a key has been <strong>failing for an hour</strong> &ndash; refused, missing on Railway, out of credit, over a limit, or the service not answering &ndash; you get <strong>one email</strong> showing how every key is, and what is not working because of it. At most one a day, and only while there is a problem; nothing when all is well. It goes to <code>KEY_ALERT_EMAIL</code> on Railway if set, otherwise to the first superuser&rsquo;s address. The keys themselves are never shown or emailed. To check by hand: <code>python manage.py check_keys</code>.</p>
    </div>
    <p>Five cards (three active, two reserved for the future) covering account and application settings:</p>
''',
         r'''    <div class="alert" style="background:#e7f5f8; border-left:4px solid #0e7c8b;" data-key-email-help>
      <i class="fas fa-key"></i> <strong>When a key stops working, you get an email.</strong>
      <p class="mb-0 mt-2">Alivente uses two outside services: <strong>Anthropic</strong> (the AI &ndash; reading booking emails, looking up places, suggestions, Plan my days, recipe import, invoice checks, translations, gift ideas, the Wellness daily line) and <strong>Google Places</strong> (checking suggested things to do for opening days, distance, rating and price). Every use of a key counts as a check. Besides that, every 15 minutes Alivente checks the Anthropic key, at no cost; Google is tried only while it is failing, once an hour, because Google counts every search &ndash; even a free one &ndash; against a daily limit (100 a day on this project). If a key has been <strong>failing for an hour</strong> &ndash; refused, missing on Railway, out of credit, over a limit, or the service not answering &ndash; you get <strong>one email</strong> showing how every key is, and what is not working because of it. At most one a day, and only while there is a problem; nothing when all is well. It goes to <code>KEY_ALERT_EMAIL</code> on Railway if set, otherwise to the first superuser&rsquo;s address. The email and <code>check_keys</code> include Google&rsquo;s own reason when it gives one (for example <em>quota exceeded &ndash; SearchTextRequest per day (limit 100)</em>). The keys themselves are never shown or emailed. To check by hand: <code>python manage.py check_keys</code>.</p>
    </div>
    <p>Five cards (three active, two reserved for the future) covering account and application settings:</p>
'''),
    ]),
    (os.path.join('pages', 'key_health.py'), [
        (r'''     minutes with calls that cost nothing: Anthropic's list of models,
     and Google's IDs-only place search (no charge at any volume).
  Only problems someone has to fix count: a key refused, missing or
  switched off, out of credit, over a limit - or a service not answering
''',
         r'''     minutes with calls that cost nothing: Anthropic's list of models,
     and Google's IDs-only place search (no charge at any volume).
     RA08, 20 Nov 2026 - but Google counts even free searches against its
     daily limit (100 a day on this project), and the watcher used it up:
     Google is now tried only while it is failing, once an hour, and the
     web workers share one watch (one check per 15 minutes in all, kept
     in the database). Real Suggest-things-to-do calls say how Google is
     the rest of the time. Google's own reason is kept and shown.
  Only problems someone has to fix count: a key refused, missing or
  switched off, out of credit, over a limit - or a service not answering
'''),
        (r'''

def classify_google(status):
    if status in (400, 401, 403):
        return 'refused', ('The key was refused, or billing or the Places '
                           'API (New) is switched off - check Google Cloud '
                           'and GOOGLE_PLACES_KEY on Railway.')
    if status == 429:
        return 'limit', WORDS['limit']
    return 'down', WORDS['down']


''',
         r'''

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


'''),
        (r'''            r.read()
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

''',
         r'''            r.read()
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

'''),
    ]),
    (os.path.join('pages', 'management', 'commands', 'check_keys.py'), [
        (r'''each is (pages/key_health.py). Sends the problem email only if one is due
(a key failing for 60 minutes, none sent today). Never prints a key.

    python manage.py check_keys
''',
         r'''each is (pages/key_health.py). Sends the problem email only if one is due
(a key failing for 60 minutes, none sent today). Never prints a key.
RA08, 20 Nov 2026 - by hand, Google is tried too (one search of its 100 a
day); the watcher tries it only while it is failing.

    python manage.py check_keys
'''),
        (r'''
    def handle(self, *args, **options):
        sent = KH.check_all()
        for x in KH.lines():
            self.stdout.write('%s: %s' % (x['name'], x['state']))
''',
         r'''
    def handle(self, *args, **options):
        # RA08 - by hand, both keys are tried now (one Google search).
        sent = KH.check_all(force=True)
        for x in KH.lines():
            self.stdout.write('%s: %s' % (x['name'], x['state']))
'''),
    ]),
    (os.path.join('test_ra04_key_email.py'), [
        (r'''   os.path.isfile(J(PG, 'management', 'commands', 'check_keys.py')),
   'MIGRATION 0120 (the key_status table) and manage.py check_keys')
ok("_health(False, e.code)" in read(J(ROOT, 'travel', 'gplaces.py')),
   'GOOGLE PLACES reports how each call went')
try:
''',
         r'''   os.path.isfile(J(PG, 'management', 'commands', 'check_keys.py')),
   'MIGRATION 0120 (the key_status table) and manage.py check_keys')
# RA08 passes Google's reason too: "_health(False, e.code, body)".
ok("_health(False, e.code" in read(J(ROOT, 'travel', 'gplaces.py')),
   'GOOGLE PLACES reports how each call went')
try:
'''),
    ]),
    (os.path.join('travel', 'gplaces.py'), [
        (r'''        # The key never goes into a log - only what went wrong. RA04 -
        # and the key's health hears of it (pages/key_health.py).
        _health(False, e.code)
        raise GoogleError('Google said %s.' % e.code)
    except Exception as e:                              # noqa: BLE001
''',
         r'''        # The key never goes into a log - only what went wrong. RA04 -
        # and the key's health hears of it (pages/key_health.py).
        try:                            # RA08 - Google's own reason
            body = e.read().decode('utf-8', 'replace')[:4000]
        except Exception:                               # noqa: BLE001
            body = ''
        _health(False, e.code, body)
        raise GoogleError('Google said %s.' % e.code)
    except Exception as e:                              # noqa: BLE001
'''),
        (r'''

def _health(ok, status=None):
    try:
        from pages import key_health as KH
        if ok:
            KH.record('google_places', True)
        else:
            p, d = KH.classify_google(status)
            KH.record('google_places', False, p, d)
    except Exception:                                   # noqa: BLE001
''',
         r'''

def _health(ok, status=None, body=''):
    try:
        from pages import key_health as KH
        if ok:
            KH.record('google_places', True)
        else:
            p, d = KH.classify_google(status, body)
            KH.record('google_places', False, p, d)
    except Exception:                                   # noqa: BLE001
'''),
    ]),
]


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('RA08 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pq = os.path.join(root, PS1)
    if "'test_ra08_google_quota.py'" in read(pq):
        print('RA08 already applied.')
        return 0
    if "'test_ra07_trip_days.py'" not in read(pq):
        refuse('RA07 (apply_ra07_trip_days.py) is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('RA08 --check: %d file(s) would change, none written; %d '
              'ship with it.' % (len(out), len(CREATES)))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('RA08 applied - the key watch spares the Google daily limit.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
