# -*- coding: utf-8 -*-
"""test_ref_link.py - round IR-1, 23 Oct 2026.

G1: TWO REGISTERS FOR ONE KIND OF IDENTIFIER.

Demetri, 16 October: the receipt number is small grey monospace; the
invoice number is a teal link. It then sat on the outstanding list for
a week behind the note "it is a BASE component, so this reaches every
.ref in the application".

SECTION 2 MEASURES THAT NOTE AND IT WAS FALSE. `.alv-table .ref` was
defined once in base.html and worn on EXACTLY ONE CELL of ONE page.
True of the rule, false of the practice - and the difference is a week
of a small change looking like a dangerous one.

AND IT WAS NOT A LINK AT ALL. The receipt number was grey text because
there was nowhere for it to go; RV-1 built the destination in this
same push.

ONE RULE, NOT TWO COPIES. physical_invoice_list carried its own
.pi-number-link with the same three declarations. Both pages now take
.alv-ref-link from base, so "one register for one kind of identifier"
is something the stylesheet says rather than something that happens to
be true today. Section 1 asks that the component is defined ONCE in
the whole tree.

MEASURED ON 23 OCTOBER, before and after, same page, same two rows:

    before   not a link   rgb(138,151,157)  w400  ui-monospace
    after    /receipts/3/ rgb(14,124,139)   w600  system

and the CELL height did not move - 57px desktop, 39px phone, both
ways. The first version of that measurement read the cell before and
the link after, and nearly reported a layout regression that was an
artefact of asking two different questions.
"""

# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------

import glob
import io
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_reflink'
ME = 'test_ref_link.py'
PATCHER = 'apply_ref_link.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'IR-1, 23 Oct 2026'

BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
RECEIPTS = os.path.join(ROOT, 'pages', 'templates', 'cash_receipts.html')
INVOICES = os.path.join(ROOT, 'pages', 'templates',
                        'physical_invoice_list.html')
GATE = os.path.join(ROOT, PS1)
FILES = (BASE, RECEIPTS, INVOICES)

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot '
                      'run - and a control that does not run is the whole '
                      'reason the 17 Oct push failed.' % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


# DOES ANY class ATTRIBUTE CARRY THE TOKEN `ref` EXACTLY?
#
# NOT a \bref\b search. A hyphen is a word boundary, so that pattern
# matches inside `alv-ref-link` - the class this round ADDS - and the
# patcher's own gate refused the round for the thing it had just
# written. Tokens are the only version that asks what was meant.
def wears_ref(src):
    for m in re.finditer(r'class="([^"]*)"', src):
        if 'ref' in m.group(1).split():
            return True
    return False


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402

NOW = dict((p, read(p)) for p in FILES)


def claims(d):
    b = T.code_only(d[BASE])
    r = T.code_only(d[RECEIPTS])
    i = T.code_only(d[INVOICES])
    return {
        'there is ONE identifier-link component':
            '.alv-ref-link {' in b,
        '  and it is the invoice register - accent, 600, underline':
            ('color: var(--alv-accent)' in b.split('.alv-ref-link {')[1]
             .split('}')[0] if '.alv-ref-link {' in b else False),
        '  and the dead monospace rule is GONE, not shadowed':
            '.alv-table .ref' not in b,
        'the receipt number wears it':
            'alv-ref-link' in r,
        '  and opens the record behind the receipt':
            "{% url 'cash_receipt_detail' row.pk %}" in r,
        '  and no longer wears the deleted class':
            not wears_ref(r),
        'both invoice links take the SAME rule':
            i.count('alv-ref-link') == 2,
        '  and the local copy is gone':
            'pi-number-link' not in i,
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, held in claims(NOW).items():
    ok(held, msg)

# ONE DEFINITION IN THE WHOLE TREE. Two copies of a rule is how two
# registers happen in the first place.
defs = []
for f in sorted(glob.glob(os.path.join(ROOT, 'pages', 'templates',
                                       '**', '*.html'), recursive=True)):
    if '.bak_' in f:
        continue
    if re.search(r'\.alv-ref-link\s*\{', read(f)):
        defs.append(os.path.basename(f))
ok(defs == ['base.html'],
   'the component is defined ONCE, in base', defs)

# AND NOTHING ANYWHERE STILL WEARS THE DELETED CLASS.
wearers = []
for f in sorted(glob.glob(os.path.join(ROOT, 'pages', '**', '*.html'),
                          recursive=True)):
    if '.bak_' in f:
        continue
    if wears_ref(read(f)):
        wearers.append(os.path.basename(f))
ok(not wearers,
   'and no template still wears class="ref", whose rule is gone',
   wearers)


# ==========================================================================
head('2. THE CONTROL - and the note that blocked this for a week')
# ==========================================================================
OLD = dict((p, was(p)) for p in FILES)
held = [m for m, v in claims(OLD).items() if v]
ok(not held, 'CONTROL: not one of this round holds before it',
   '\n'.join(held))

oldb = T.code_only(OLD[BASE])
ok('.alv-table .ref {' in oldb,
   'CONTROL: the monospace rule really was in base')
ok('ui-monospace' in oldb.split('.alv-table .ref {')[1].split('}')[0],
   '  monospace, as Demetri reported on 16 October')
ok('--alv-ink-soft' in oldb.split('.alv-table .ref {')[1].split('}')[0],
   '  and muted, against the invoice number\'s accent')
ok(wears_ref(T.code_only(OLD[RECEIPTS])),
   'CONTROL: and the receipt cell wore it')
ok('pi-number-link' in T.code_only(OLD[INVOICES]),
   'CONTROL: while the invoice list carried its own separate copy')

# THE MEASUREMENT THAT UNBLOCKED THE ROUND.
#
# The outstanding note said this "reaches every .ref in the
# application". Asked of the tree as it stood BEFORE the round: one
# file, one cell. A week of caution for a one-page change.
before_wearers = []
for f in sorted(glob.glob(os.path.join(ROOT, 'pages', '**', '*' + SUFFIX),
                          recursive=True)):
    if wears_ref(read(f)):
        before_wearers.append(os.path.basename(f)[:-len(SUFFIX)])
ok(before_wearers == ['cash_receipts.html'],
   'CONTROL: and exactly ONE page wore it, not "every table in the '
   'application" - the note was true of the rule and false of the '
   'practice', before_wearers)


# ==========================================================================
head('3. DRIVEN - the rendered list')
# ==========================================================================
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.test.utils import setup_test_environment
    setup_test_environment()
    from django.db import connections
    from asgiref.local import Local
    dj.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    dj.ROOT_URLCONF = 'mysite.urls'
    dj.ALLOWED_HOSTS = list(dj.ALLOWED_HOSTS) + ['testserver']
    dj.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    import logging as _logging
    _logging.getLogger('django.request').setLevel(_logging.ERROR)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    django_up = True
except Exception as e:
    skip('everything that needs a database',
         'Django would not start: %s' % str(e).split('\n')[0][:90])

if not django_up:
    skip('section 3', 'no database')
else:
    import datetime as dt
    from decimal import Decimal
    from django.contrib.auth.models import User
    from django.test import Client
    from pages.models import CashReceipt, props

    try:
        me = User.objects.create_superuser('ir1boss', 'ir1@x.test', 'x')
        cl = Client()
        cl.force_login(me)
        p = props.objects.create(prop_name='Flat 3, Nikis Avenue',
                                 prop_country='Cyprus')
        made = []
        for n, day, amt, who in (('CR-00182', 3, '950.00', 'Eleni Pavlou'),
                                 ('CR-00183', 7, '1450.00', 'A Georgiou')):
            r = CashReceipt.objects.create(
                receipt_number=n, receipt_date=dt.date(2026, 10, day),
                amount=Decimal(amt), currency='EUR',
                description='Rent', method='transfer',
                doc_format='electronic', prop=p, payer_name=who)
            CashReceipt.objects.filter(pk=r.pk).update(created_by=me)
            made.append(r)

        resp = cl.get('/receipts/')
        ok(resp.status_code == 200, 'the receipts list renders',
           resp.status_code)
        html = resp.content.decode('utf-8', 'replace')

        # THE CELL HOLDS A LINK, and it points at that row's receipt.
        cells = re.findall(
            r'<td data-label="Receipt #"[^>]*>(.*?)</td>', html, re.S)
        ok(len(cells) == 2, 'two receipt cells', len(cells))
        # MATCHED BY NUMBER, NOT BY POSITION. The list is newest
        # first, so zipping creation order against display order
        # paired each receipt with the other one's cell and reported
        # correct links as wrong.
        for r in made:
            mine = [c for c in cells if r.receipt_number in c]
            want = '/receipts/%s/' % r.pk
            ok(len(mine) == 1 and 'class="alv-ref-link"' in mine[0]
               and want in mine[0],
               '  %s links to its OWN record' % r.receipt_number,
               (mine[0].strip()[:120] if mine else 'no cell') +
               '\n  wanted ' + want)

        # AND NOTHING IN THE PAGE STILL WEARS THE DELETED CLASS.
        ok(not wears_ref(html),
           'and the rendered page wears no class="ref"')

        # THE DESTINATION REALLY EXISTS - a link painted like a link
        # that 404s is worse than grey text.
        follow = cl.get('/receipts/%s/' % made[0].pk)
        ok(follow.status_code == 200,
           'and following it reaches the record, not a 404',
           follow.status_code)
    except Exception as exc:
        ok(False, 'section 3 ran to the end', repr(exc)[:300])


# ==========================================================================
head('4. REGISTRATION')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1, '  exactly once')
ok('alv-ref-link' in gate, 'and a sentinel watches the component')
ok('.alv-table .ref' in gate,
   'and one watches that the dead rule stays dead')

print('')
print('=' * 74)
print('WHAT THIS ROUND DOES NOT PROVE')
print('=' * 74)
print('  Not that the tap target is big enough. The link measures')
print('  78x20 on a phone, under the 44px the house asks of Add and')
print('  Edit screens. It is now EXACTLY the invoice number\'s target,')
print('  because after this round they are the same rule - so the')
print('  question is pre-existing and applies to both. Flagged on')
print('  23 October rather than fixed inside a round about colour.')
print('')
print('  Not that every identifier in the application is now one')
print('  register. Two were measured and two were joined. Anything')
print('  that paints an id with its own local rule is unexamined.')
print('')
print('  Not that monospace was the wrong choice. It aligned a column')
print('  of numbers, and that is a real thing to lose. Demetri chose')
print('  consistency over alignment on 23 October, knowing the cost.')
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
