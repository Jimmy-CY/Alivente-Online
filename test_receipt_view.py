# -*- coding: utf-8 -*-
"""test_receipt_view.py - round RV-1, 23 Oct 2026.

G2: THE RECEIPT HAD NO SCREEN THAT SHOWED THE RECORD.

Outstanding since 16 October as "the Physical Invoice detail shape
without the PDF". Re-measured on 23 October before building, and the
description had drifted: the list HAS had a LOOK action since RC-1
(the pdf icon, through components/pdf_viewer.html), CashReceipt HAS a
pdf_file, and an Edit screen already owns changing a receipt.

THE REAL GAP IS NARROWER AND IT IS REAL. The PDF shows the receipt AS
ISSUED. Nothing showed the record behind it: who voided it and why,
who edited it and when, when it was emailed, the property, the method,
the bank reference, the payer's address, telephone and email.

void_reason IS THE CLEAREST CASE, and section 2 measures it: the
column is captured on every void, stored, and before this round was
displayed on NO template in the application.

SECTION 3 DRIVES THE SCREEN with a receipt that has had a whole life -
issued, emailed, edited by somebody else, then voided with a reason -
and section 4 drives one that has only been issued, because "only the
events that happened" is the claim and a four-event receipt cannot
show it.
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

SUFFIX = '.bak_receiptview'
ME = 'test_receipt_view.py'
PATCHER = 'apply_receipt_view.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'RV-1, 23 Oct 2026'

VIEWS = os.path.join(ROOT, 'pages', 'views', 'receipts.py')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'cash_receipt_detail.html')
GATE = os.path.join(ROOT, PS1)
FILES = (VIEWS, URLS)

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


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402

NOW = dict((p, read(p)) for p in FILES)


def detail_body(src):
    code = T.python_code_only(src, payloads=True)
    a = code.find('def cash_receipt_detail')
    if a < 0:
        return ''
    body = code[a:]
    nxt = re.search(r'\n@login_required', body[1:])
    return body[:nxt.start() + 1] if nxt else body


def claims(d):
    v = T.python_code_only(d[VIEWS], payloads=True)
    u = d[URLS]
    body = detail_body(d[VIEWS])
    return {
        'there is a view that shows the record':
            bool(body),
        '  and it is READ ONLY':
            bool(body) and not any(w in body for w in (
                '.save(', '.delete(', '.update(', '.create(',
                'request.POST')),
        '  guarded by the READING permission, not the editing one':
            'can_access_receipts' in v[max(0, v.find(
                'def cash_receipt_detail') - 220):v.find(
                'def cash_receipt_detail')] if body else False,
        '  and it reads void_reason, which nothing displayed before':
            'void_reason' in body,
        'the history is built in the view and ordered':
            'trail.sort(' in body,
        'the name is EXPORTED, or the URLconf cannot see it':
            '"cash_receipt_detail"' in v[v.find('__all__'):
                                         v.find('__all__') + 600],
        'and there is a route to it':
            'name="cash_receipt_detail"' in u,
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, held in claims(NOW).items():
    ok(held, msg)

ok(os.path.isfile(TPL), 'the screen is on disk', TPL)
TPLSRC = T.code_only(read(TPL)) if os.path.isfile(TPL) else ''
ok('rv-trail' in TPLSRC, '  and it draws a history')
# NOT A TENTH .detail-row. Nine templates each define their own and
# base defines none; this page owns an rv-* prefix instead.
ok(not re.search(r'\.detail-(row|label|value|group)\s*\{', TPLSRC),
   '  without adding a tenth copy of .detail-row')
ok(TPLSRC.count('page-action-buttons') == 1,
   '  one action bar, as base 3.4 requires')


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
OLD = dict((p, was(p)) for p in FILES)
held = [m for m, v in claims(OLD).items() if v]
ok(not held, 'CONTROL: not one of this round holds before it',
   '\n'.join(held))

# AND THE MEASUREMENT THAT IS THE REASON FOR THE ROUND.
#
# void_reason is captured on every void and stored, and before this
# round it reached no page at all. Asked of the tree rather than
# remembered - and asked in the two places it could have been:
#
#   NO TEMPLATE NAMES IT, then or now. It travels to this screen as
#   the generic `note` on a history event, so the template never says
#   the word. That is why "which templates mention it" - the first
#   version of this claim - measured nothing and failed.
wearers = []
for f in sorted(glob.glob(os.path.join(ROOT, 'pages', 'templates',
                                       '**', '*.html'), recursive=True)):
    if '.bak_' in f:
        continue
    if 'void_reason' in read(f):
        wearers.append(os.path.basename(f))
ok(not wearers,
   'CONTROL: no template names void_reason - it reaches this screen '
   'as a history note, which is why counting templates proves nothing',
   wearers)

#   AND THE BACKUP HAD NOWHERE TO SHOW IT. The only functions that
#   touched the column were the two that WRITE it.
oldv = T.python_code_only(OLD[VIEWS], payloads=True)
ok(not detail_body(OLD[VIEWS]),
   'CONTROL: there was no view that could show it')
ok(oldv.count('void_reason') and 'render(' not in oldv[
       oldv.find('void_reason'):oldv.find('void_reason') + 400],
   'CONTROL: and the places that named it WROTE it - nothing between '
   'the column and a page')


# ==========================================================================
head('3. DRIVEN - a receipt that has had a whole life')
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
    skip('sections 3 and 4', 'no database')
else:
    import datetime as dt
    from decimal import Decimal
    from django.contrib.auth.models import User
    from django.test import Client
    from django.urls import reverse
    from django.utils import timezone
    from pages.models import CashReceipt, props, tenant as Tenant

    try:
        # THE EXPORT, ASKED OF DJANGO RATHER THAN OF THE TEXT.
        #
        # pages/views/__init__.py does `from .receipts import *`, which
        # obeys __all__ - so a view missing from that list does not
        # exist as far as the URLconf is concerned. This round applied
        # cleanly with every gate green and reverse() still raised
        # AttributeError on a module that plainly held the function.
        url = reverse('cash_receipt_detail', args=[1])
        ok(url.endswith('/1/'),
           'the route RESOLVES - __all__ really does export the view',
           url)

        me = User.objects.create_superuser('rv1boss', 'rv1@x.test', 'x')
        me.first_name, me.last_name = 'Demetri', 'Manias'
        me.save()
        clerk = User.objects.create_user('rv1clerk', password='x',
                                         first_name='Athina',
                                         last_name='P')
        cl = Client()
        cl.force_login(me)

        p = props.objects.create(prop_name='Flat 3, Nikis Avenue',
                                 prop_country='Cyprus')
        t = Tenant.objects.create(tenant_name='Andreas Georgiou', prop=p)
        now = timezone.now()

        r = CashReceipt.objects.create(
            receipt_number='CR-00184',
            receipt_date=dt.date(2026, 10, 3),
            amount=Decimal('1450.00'), currency='EUR',
            description='October rent and the water share.',
            method='transfer', reference='SEPA 9920-4471',
            doc_format='electronic', tenant=t, prop=p,
            payer_name='Andreas Georgiou',
            payer_address='Flat 3, 14 Nikis Avenue\nLimassol 3025',
            payer_tel='+357 99 123 456',
            payer_email='a.georgiou@example.com')
        CashReceipt.objects.filter(pk=r.pk).update(
            pdf_file='cash_receipts/CR-00184.pdf',
            created_at=now - dt.timedelta(days=20), created_by=me,
            sent_at=now - dt.timedelta(days=20),
            edited_at=now - dt.timedelta(days=11), edited_by=clerk,
            is_void=True, voided_at=now - dt.timedelta(days=2),
            voided_by=me,
            void_reason='Paid twice - the second transfer was returned.')

        resp = cl.get(reverse('cash_receipt_detail', args=[r.pk]))
        ok(resp.status_code == 200, 'the screen renders',
           resp.status_code)
        html = resp.content.decode('utf-8', 'replace')

        # THE SIX THINGS THE PDF DOES NOT CARRY.
        for what, needle in (
                ('the void reason', 'the second transfer was returned'),
                ('who voided it', 'Voided'),
                ('who edited it, by name', 'Athina P'),
                ('that it was emailed', 'Emailed'),
                ('the property', 'Flat 3, Nikis Avenue'),
                ('the bank reference', 'SEPA 9920-4471'),
                ('the payer email', 'a.georgiou@example.com'),
                ('the payer telephone', '+357 99 123 456')):
            ok(needle in html, '  it shows %s' % what, needle)

        # THE LABELS, NOT THE STORED CODES. get_*_display, not the raw
        # column - a fixture using method='bank' on 23 October proved
        # that create() does not validate a choice and the raw value
        # comes straight through.
        ok('Bank Transfer' in html,
           '  and the METHOD LABEL, not the stored code')
        ok('Electronic' in html, '  and the document format label')

        # ORDER. Oldest first, so it reads downward the way the
        # receipt's life ran.
        order = re.findall(r'rv-event-what">(\w+)<', html)
        ok(order == ['Issued', 'Emailed', 'Edited', 'Voided'],
           'the history runs OLDEST FIRST', order)
        # THE MARKUP, NOT THE STYLESHEET. `.rv-event.rv-void` is a
        # rule in the inline <style> on EVERY receipt page; the claim
        # is whether a LIST ITEM wears the class. Same trap as
        # `is-out` on the print sheet yesterday.
        ok('class="rv-event rv-void"' in html,
           '  and Void is the one event that carries a colour',
           re.findall(r'class="rv-event[^"]*"', html))

        # READ ONLY, ASKED OF THE RENDERED PAGE.
        ok('<form' not in html.split('page-action-buttons')[1],
           'the screen has no form below the bar - Edit owns changing '
           'a receipt')
        # SCOPED TO THIS PAGE'S OWN MARKUP. base.html carries a
        # logout form on every page in the application, so asking the
        # whole document whether it posts measures base, not this
        # screen.
        mine = html[html.find('page-action-buttons'):html.find('<style>')]
        ok('<form' not in mine and 'method="post"' not in mine.lower(),
           '  and nothing between the bar and the stylesheet posts')

        # EDIT IS NOT OFFERED ON A VOID RECEIPT.
        # THE RENDERED PATH, NOT THE URL NAME. `cash_receipt_edit` is
        # what {% url %} is GIVEN, never what it emits - so the first
        # version of this claim could not have failed, on any page, in
        # any state. It passed and measured nothing.
        edit_href = '/receipts/%s/edit/' % r.pk
        ok(edit_href not in html,
           'a VOID receipt offers no Edit - there is nothing to change',
           edit_href)

        # ==============================================================
        head('4. DRIVEN - and a receipt that has only been issued')
        # ==============================================================
        # "ONLY THE EVENTS THAT HAPPENED" is the claim, and a receipt
        # with four of them cannot show it. An absent edited_at is not
        # "edited: never", it is not an event.
        r2 = CashReceipt.objects.create(
            receipt_number='CR-00185',
            receipt_date=dt.date(2026, 10, 18),
            amount=Decimal('620.50'), currency='EUR',
            description='Deposit, second instalment.',
            method='cash', doc_format='printed', prop=p,
            payer_name='Maria Christodoulou')
        CashReceipt.objects.filter(pk=r2.pk).update(created_by=me)

        resp2 = cl.get(reverse('cash_receipt_detail', args=[r2.pk]))
        ok(resp2.status_code == 200, 'the plain receipt renders',
           resp2.status_code)
        h2 = resp2.content.decode('utf-8', 'replace')
        order2 = re.findall(r'rv-event-what">(\w+)<', h2)
        ok(order2 == ['Issued'],
           'ONE event, not four with three saying never', order2)
        ok('class="rv-event rv-void"' not in h2,
           '  and nothing is coloured',
           re.findall(r'class="rv-event[^"]*"', h2))
        # THE HREF, NOT THE WORDS. "View receipt" appears in a
        # STANDARDS COMMENT inside base.html, on every page in the
        # application - which is the fourth time today a text
        # instrument has read a comment as content.
        ok('/receipts/%s/pdf/' % r2.pk not in h2,
           '  and a receipt with no PDF offers no View receipt')
        ok('/receipts/%s/edit/' % r2.pk in h2,
           '  while a LIVE receipt does offer Edit')

        # AND THE PERMISSION IS THE READING ONE, DRIVEN.
        plain = User.objects.create_user('rv1reader', password='x')
        cl2 = Client()
        cl2.force_login(plain)
        resp3 = cl2.get(reverse('cash_receipt_detail', args=[r2.pk]))
        ok(resp3.status_code in (302, 403),
           'and a user without receipt access is refused',
           resp3.status_code)
    except Exception as exc:
        ok(False, 'sections 3 and 4 ran to the end', repr(exc)[:300])


# ==========================================================================
head('5. REGISTRATION')
# ==========================================================================
ok(not glob.glob(os.path.join(ROOT, 'pages', 'migrations',
                              '*' + SUFFIX)),
   'this round backed up no migration - every field it reads existed')
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1, '  exactly once')
ok('def cash_receipt_detail' in gate, 'and a sentinel watches the view')
ok('rv-trail' in gate, 'and one watches the history')

print('')
print('=' * 74)
print('WHAT THIS ROUND DOES NOT PROVE')
print('=' * 74)
print('  Not that anybody can reach the screen. IR-1 makes the receipt')
print('  number a link to it, in the same push. A screen built in one')
print('  round and reached in the next is two claims that can each be')
print('  checked.')
print('')
print('  Not that the other eight record-bearing models have a screen')
print('  like this. Only the receipt was asked for.')
print('')
print('  Not that .detail-row should stay duplicated nine times. This')
print('  page declines to be the tenth; promoting the component into')
print('  base is a system-wide round nobody has taken.')
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
