# -*- coding: utf-8 -*-
"""apply_ra04_key_email.py - round RA04, 19 Nov 2026.

RELEASE RA04 - AN EMAIL WHEN A KEY STOPS WORKING.

    Demetri, 19 Nov: "If there is a problem with the key in the future,
    also with the Anthropic key, can the system send me an email letting
    me know.... instead of just to stop working?"; "The email should go
    to me only. Leave the working again email. Let's increase the time to
    60 minutes of failing. Just one email daily, covering all keys - and
    showing the status of all keys"; "The email, ONLY if their is a
    problem on one key".

    - pages/key_health.py: every Anthropic call and every Google Places
      call reports how it went; on Railway's web process the two keys are
      checked every 15 minutes with calls that cost nothing.
    - One email a day at most, to KEY_ALERT_EMAIL (else the first
      superuser), only once a key has failed for 60 minutes; it shows
      every key's status. No "working again" email. Never the key.
    - python manage.py check_keys - check by hand.
    - Help: Administration, System.
    - Migration pages 0120 (key_status): run python manage.py migrate
      locally first.

The suite, key_health.py, check_keys.py and the migration ship beside
this patcher. Stands on RA03. Idempotent. Edits backed up to .bak_ra04.
"""
import os
import sys

SUFFIX = '.bak_ra04'
MARK = 'RA04, 19 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_ra04_key_email.py',
    'pages/key_health.py',
    'pages/management/commands/check_keys.py',
    'pages/migrations/0120_key_status.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    # RA03, 19 Nov 2026 - restaurants and cafes, checked on Google;
    # Select and Delete.
    'test_ra03_suggestions.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    # RA03, 19 Nov 2026 - restaurants and cafes, checked on Google;
    # Select and Delete.
    'test_ra03_suggestions.py',
    # RA04, 19 Nov 2026 - an email when a key stops working.
    'test_ra04_key_email.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # RA03, 19 Nov 2026 - restaurants and cafes, checked on Google.
    '.bak_ra03',
]

''',
         r'''    # RA03, 19 Nov 2026 - restaurants and cafes, checked on Google.
    '.bak_ra03',
    # RA04, 19 Nov 2026 - an email when a key stops working.
    '.bak_ra04',
]

'''),
    ]),
    (os.path.join('pages', 'apps.py'), [
        (r'''        post_migrate.connect(_ensure_permissions, sender=self,
                             dispatch_uid='pages.ensure_permissions')


''',
         r'''        post_migrate.connect(_ensure_permissions, sender=self,
                             dispatch_uid='pages.ensure_permissions')
        # RA04, 19 Nov 2026 - an email when a key stops working
        # (pages/key_health.py): every Anthropic call reports how it went,
        # and on Railway a watcher checks the keys every 15 minutes.
        try:
            from pages import key_health
            key_health.wrap_anthropic()
            key_health.start_watcher()
        except Exception:  # never stops the app starting
            pass


'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''           data-tab-icon="fa-cog">
    <h6 style="color:#6c757d; font-weight:700;"><i class="fas fa-cog"></i> System cards</h6>
    <p>Five cards (three active, two reserved for the future) covering account and application settings:</p>

''',
         r'''           data-tab-icon="fa-cog">
    <h6 style="color:#6c757d; font-weight:700;"><i class="fas fa-cog"></i> System cards</h6>
    <div class="alert" style="background:#e7f5f8; border-left:4px solid #0e7c8b;" data-key-email-help>
      <i class="fas fa-key"></i> <strong>When a key stops working, you get an email.</strong>
      <p class="mb-0 mt-2">Alivente uses two outside services: <strong>Anthropic</strong> (the AI &ndash; reading booking emails, looking up places, suggestions, Plan my days, recipe import, invoice checks, translations, gift ideas, the Wellness daily line) and <strong>Google Places</strong> (checking suggested things to do for opening days, distance, rating and price). Every 15 minutes Alivente checks both keys, at no cost, and every use of them counts too. If a key has been <strong>failing for an hour</strong> &ndash; refused, missing on Railway, out of credit, over a limit, or the service not answering &ndash; you get <strong>one email</strong> showing how every key is, and what is not working because of it. At most one a day, and only while there is a problem; nothing when all is well. It goes to <code>KEY_ALERT_EMAIL</code> on Railway if set, otherwise to the first superuser&rsquo;s address. The keys themselves are never shown or emailed. To check by hand: <code>python manage.py check_keys</code>.</p>
    </div>
    <p>Five cards (three active, two reserved for the future) covering account and application settings:</p>

'''),
    ]),
    (os.path.join('pages', 'models.py'), [
        (r'''        db_table = 'generated_lease'
        ordering = ['-created_at']
''',
         r'''        db_table = 'generated_lease'
        ordering = ['-created_at']


class KeyStatus(models.Model):
    """RA04, 19 Nov 2026 - how each outside service's key is doing
    (pages/key_health.py). Demetri: "If there is a problem with the key in
    the future, also with the Anthropic key, can the system send me an
    email letting me know.... instead of just to stop working?" - to him
    only, after 60 minutes of failing, one email a day at most covering
    every key, and only when there is a problem. The key itself is never
    stored here."""
    service = models.CharField(max_length=30, unique=True)
    ok = models.BooleanField(default=True)
    problem = models.CharField(max_length=20, blank=True, default='')
    detail = models.CharField(max_length=255, blank=True, default='')
    failing_since = models.DateTimeField(null=True, blank=True)
    last_ok = models.DateTimeField(null=True, blank=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    emailed_on = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'key_status'
        ordering = ['service']

    def __str__(self):
        return '%s: %s' % (self.service, 'ok' if self.ok else self.problem)
'''),
    ]),
    (os.path.join('travel', 'gplaces.py'), [
        (r'''            data = json.loads(r.read().decode('utf-8') or '{}')
    except urllib.error.HTTPError as e:
        # The key never goes into a log - only what went wrong.
        raise GoogleError('Google said %s.' % e.code)
    except Exception as e:                              # noqa: BLE001
        raise GoogleError('Google could not be reached (%s).'
                          % type(e).__name__)
    found = data.get('places') or []
    return shape(found[0]) if found else None


''',
         r'''            data = json.loads(r.read().decode('utf-8') or '{}')
    except urllib.error.HTTPError as e:
        # The key never goes into a log - only what went wrong. RA04 -
        # and the key's health hears of it (pages/key_health.py).
        _health(False, e.code)
        raise GoogleError('Google said %s.' % e.code)
    except Exception as e:                              # noqa: BLE001
        _health(False, None)
        raise GoogleError('Google could not be reached (%s).'
                          % type(e).__name__)
    _health(True)
    found = data.get('places') or []
    return shape(found[0]) if found else None


def _health(ok, status=None):
    try:
        from pages import key_health as KH
        if ok:
            KH.record('google_places', True)
        else:
            p, d = KH.classify_google(status)
            KH.record('google_places', False, p, d)
    except Exception:                                   # noqa: BLE001
        pass


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
    raise SystemExit('RA04 REFUSED: %s' % msg)


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
    if "'test_ra04_key_email.py'" in read(pq):
        print('RA04 already applied.')
        return 0
    if "'test_ra03_suggestions.py'" not in read(pq):
        refuse('RA03 (apply_ra03_suggestions.py) is not applied - this round registers after it.')
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
        print('RA04 --check: %d file(s) would change, none written; %d '
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
    print('RA04 applied - an email when a key stops working. Run: python manage.py migrate')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
