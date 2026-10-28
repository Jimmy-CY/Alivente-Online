# -*- coding: utf-8 -*-
"""test_receipt_email.py - round CR-2, 27 Oct 2026.

EMAILING A CASH RECEIPT - his decisions of 27 October, render approved
("That is perfect").

    - A paper-plane in each Receipts row, between Duplicate and Void (and
      "Email receipt" on the Receipt Details bar), greyed while the receipt
      has no email address, and never live on a void one.
    - A confirmation pop-up shows To, Cc, subject, the attached PDF and the
      exact message before anything is sent.
    - TO is always the receipt's own address(es). The new "Cash Receipt to
      Payer" card in Notification Settings adds any further To and any Cc;
      with only a Cc set it goes To the payer, Cc the people named; with
      no card at all, to the payer alone (no catch-all address).
    - Sent -> "Issued \u00b7 Sent". An edit afterwards puts it back to Issued,
      so it is plain the corrected copy has not gone out. Send again is
      always there. The history says who it was emailed to.
    - Printed-format receipts may be emailed too, with a warning.
    - The email is the e-signing kind: branded, logo under the sign-off,
      no contact details. Duplicate already copied the email address.
    - And Receipts gets the Help module it never had (his ask, the same
      evening): issuing, the list, emailing, Receipt Details.

One migration (0110): CashReceipt.sent_to, and the new notification type.
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

import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_receiptemail'
ME = 'test_receipt_email.py'
PATCHER = 'apply_receipt_email.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'CR-2, 27 Oct 2026'

J = os.path.join
MODELS = J(ROOT, 'pages', 'models.py')
VIEW = J(ROOT, 'pages', 'views', 'receipts.py')
NOTIF = J(ROOT, 'pages', 'views', 'notifications.py')
EMAILU = J(ROOT, 'pages', 'email_utils.py')
URLS = J(ROOT, 'pages', 'urls.py')
LIST_T = J(ROOT, 'pages', 'templates', 'cash_receipts.html')
DET_T = J(ROOT, 'pages', 'templates', 'cash_receipt_detail.html')
SET_T = J(ROOT, 'pages', 'templates', 'notification_settings.html')
BASE = J(ROOT, 'pages', 'templates', 'base.html')
MIG = J(ROOT, 'pages', 'migrations', '0110_notification_type_cash_receipt.py')
HELP_O = J(ROOT, 'pages', 'help_content', 'operational.html')
GATE = J(ROOT, PS1)
EDITED = (MODELS, VIEW, NOTIF, EMAILU, URLS, LIST_T, DET_T, SET_T, BASE,
          HELP_O)
SHIPPED = (MIG,)

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
    with open(p, encoding='utf-8-sig', errors='replace') as f:
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

NOW = dict((p, read(p)) for p in EDITED + SHIPPED)
OLD = dict((p, was(p)) for p in EDITED)


def claims(src):
    m = T.python_code_only(src[MODELS])
    v = T.python_code_only(src[VIEW])
    mig = src.get(MIG, '')
    lt = src[LIST_T]
    return [
        ("sent_to = models.TextField(" in m and 'def is_sent(self)' in m
         and 'self.edited_at <= self.sent_at' in m
         and "('cash_receipt_payer', 'Cash Receipt to Payer')" in m,
         'the receipt records who it was emailed to, and knows whether it is '
         'sent and not edited since'),
        ("name='sent_to'" in mig and "'cash_receipt_payer'" in mig,
         '  and migration 0110 carries both'),
        ("'cash_receipt_payer': {'to': [], 'cc': []}" in src[EMAILU]
         and "'cash_receipt_payer'," in src[NOTIF]
         and 'value="cash_receipt_payer"' in src[SET_T],
         'the Cash Receipt to Payer card is on Notification Settings, and '
         'with no card saved nobody is added'),
        ('def cash_receipt_send(' in v and 'BrandedEmail(' in v
         and 'def _send_lists(' in v and 'def _status(' in v
         and "name=\"cash_receipt_send\"" in src[URLS],
         'a receipt can be emailed - routed, branded, To the payer first'),
        ('class="icon-action-btn icon-send"' in lt
         and 'No email address - edit the receipt to add one' in lt
         and 'mobile-action-bar cols-5' in lt and 'id="receiptSendModal"' in lt
         and 'openReceiptSend(this' in src[DET_T]
         and '.mobile-action-bar.cols-5' in src[BASE],
         'the paper-plane is in the row, greyed without an address, on the '
         'phone bar, and on the details page'),
        ('data-module-slug="cash_receipts"' in src[HELP_O]
         and 'Cash Receipt to Payer' in src[HELP_O]
         and 'data-tab-name="Emailing"' in src[HELP_O],
         'Receipts has a Help module at last, emailing included - his ask'),
    ]


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
missing = [os.path.relpath(p, ROOT) for p in EDITED + SHIPPED
           if MARK not in NOW[p]]
ok(not missing, 'the round dates itself in every file it touched',
   ', '.join(missing))

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backups')
# ==========================================================================
before = dict(OLD)
before[MIG] = ''
held = [m for c, m in claims(before) if c]
ok(not held, 'CONTROL: not one of this round claims held before it',
   '\n'.join(held))
ok(not os.path.isfile(MIG + SUFFIX),
   'CONTROL: the migration has no backup, because this round INVENTED it')

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    import datetime as dt
    import html as H
    import shutil
    import tempfile
    from django.contrib.auth.models import Permission, User
    from django.core import mail
    from django.db import connection, transaction
    from django.test import Client, override_settings
    from django.utils import timezone
    import pages.models as M
    django_up = True
except Exception as e:                                       # noqa: BLE001
    skip('section 3', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])


class Rollback(Exception):
    """Nothing this suite writes survives it."""


have_db = False
if django_up:
    try:
        connection.ensure_connection()
        M.CashReceipt.objects.exists()
        have_db = True
    except Exception as _e:                                   # noqa: BLE001
        skip('section 3', 'no database: %s' % str(_e).split('\n')[0][:70])

if have_db:
    tmp = tempfile.mkdtemp(prefix='cr2_')
    over = override_settings(
        MEDIA_ROOT=tmp,
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    over.enable()
    try:
        with transaction.atomic():
            from pages.permissions import ensure_permissions
            ensure_permissions()
            M.NotificationRecipient.objects.filter(
                notification_type='cash_receipt_payer').delete()
            prop = M.props.objects.create(prop_name='CR2 Flat',
                                          prop_country='Cyprus')
            n = [0]

            def a_receipt(email, **kw):
                n[0] += 1
                return M.CashReceipt.objects.create(
                    receipt_number='CR2-%03d' % n[0],
                    receipt_date=dt.date(2026, 10, 1), amount='465.00',
                    description='50%% Rent for October 2026 - CR2 Flat',
                    method='transfer', payer_name='Antoine Example',
                    payer_email=email, prop=prop, **kw)

            with_mail = a_receipt('antoine@example.com; second@example.com')
            no_mail = a_receipt('')
            printed = a_receipt('dorian@example.com', doc_format='printed')

            u = User.objects.create_user(username='cr2clerk',
                                         password='not-a-real-password')
            for code in ('can_access_receipts', 'can_edit_receipts'):
                u.user_permissions.add(Permission.objects.get(codename=code))
            u = User.objects.get(pk=u.pk)
            c = Client(SERVER_NAME='localhost')
            c.force_login(u)

            body = c.get('/receipts/').content.decode('utf-8', 'replace')
            url_with = '/receipts/%d/send/' % with_mail.pk
            url_none = '/receipts/%d/send/' % no_mail.pk
            ok('data-url="%s"' % url_with in body,
               'the list offers to email a receipt that has an address')
            ok('data-url="%s"' % url_none not in body
               and 'No email address - edit the receipt to add one' in body,
               '  and greys it, with the reason, on one that has none')
            ok('data-to="antoine@example.com, second@example.com"' in body,
               '  the pop-up shows both of the payer\'s addresses as To')

            # ---- NO CARD: the payer only, no catch-all address
            mail.outbox = []
            r = c.post(url_with)
            ok(r.status_code == 302 and len(mail.outbox) == 1,
               'Send emails it, once', '%s %d' % (r.status_code,
                                                  len(mail.outbox)))
            if mail.outbox:
                m0 = mail.outbox[0]
                ok(m0.to == ['antoine@example.com', 'second@example.com']
                   and not m0.cc,
                   '  with no card saved, to the payer alone - nobody added',
                   '%r / %r' % (m0.to, m0.cc))
                ok(any(a[0] == '%s.pdf' % with_mail.receipt_number
                       for a in m0.attachments),
                   '  with the receipt PDF attached')
                ok('Tel:' not in m0.body and 'Mobile:' not in m0.body
                   and 'Alivente Limited' in m0.body,
                   '  signed Alivente Limited, with no contact details')
            with_mail.refresh_from_db()
            ok(with_mail.is_sent and 'antoine@example.com' in with_mail.sent_to,
               '  and the receipt records it, and who it went to',
               with_mail.sent_to)
            body = c.get('/receipts/').content.decode('utf-8', 'replace')
            # THE PILLS, not the page: the Receipts help on this page
            # names the status too.
            ok(len(re.findall(r'<span class="alv-pill alv-pill-info"[^>]*>'
                              r'Issued \u00b7 Sent</span>',
                              H.unescape(body))) == 1,
               'the list now reads Issued \u00b7 Sent for it')
            det = c.get('/receipts/%d/' % with_mail.pk).content.decode(
                'utf-8', 'replace')
            ok('to antoine@example.com' in det,
               '  and its history says who it was emailed to')

            # ---- AN EDIT AFTERWARDS: back to plain Issued
            M.CashReceipt.objects.filter(pk=with_mail.pk).update(
                edited_at=timezone.now() + dt.timedelta(seconds=5))
            with_mail.refresh_from_db()
            ok(not with_mail.is_sent,
               'an edit after sending puts it back to Issued - the corrected '
               'copy has not gone out')

            # ---- THE CARD: extra To and a Cc
            M.NotificationRecipient.objects.create(
                notification_type='cash_receipt_payer', to_addresses='',
                cc_addresses='office@example.com', created_by=u)
            mail.outbox = []
            c.post('/receipts/%d/send/' % printed.pk)
            ok(len(mail.outbox) == 1
               and mail.outbox[0].to == ['dorian@example.com']
               and mail.outbox[0].cc == ['office@example.com'],
               'with only a Cc on the card it goes To the payer, Cc the card',
               mail.outbox and (mail.outbox[0].to, mail.outbox[0].cc))

            # ---- REFUSALS
            mail.outbox = []
            r = c.post(url_none)
            ok(r.status_code == 302 and mail.outbox == [],
               'a receipt with no address sends nothing')
            M.CashReceipt.objects.filter(pk=printed.pk).update(is_void=True)
            r = c.post('/receipts/%d/send/' % printed.pk)
            ok(mail.outbox == [], '  nor does a void one')
            viewer = User.objects.create_user(username='cr2viewer',
                                              password='not-a-real-password')
            viewer.user_permissions.add(
                Permission.objects.get(codename='can_access_receipts'))
            cv = Client(SERVER_NAME='localhost')
            cv.force_login(viewer)
            ok(cv.post(url_with).status_code == 403 and mail.outbox == [],
               '  nor anybody who cannot edit receipts')

            # ---- DUPLICATE CARRIES THE ADDRESS
            body = c.get('/receipts/new/?duplicate=%d' % with_mail.pk
                         ).content.decode('utf-8', 'replace')
            ok('antoine@example.com; second@example.com' in body,
               'Duplicate copies the email address across')
            raise Rollback
    except Rollback:
        pass
    finally:
        over.disable()
        shutil.rmtree(tmp, ignore_errors=True)

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("Text = 'def cash_receipt_send('" in gate,
   '  with a sentinel on the send view')
wd = read(J(ROOT, 'test_waiting_down.py'))
nm = re.search(r'CONVERTED_N = (\d+)', wd)
ok(nm and int(nm.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (nm.group(1) if nm else '?', len(T.CONVERTED)))
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX),
       '  %s has its backup' % os.path.relpath(p, ROOT))


print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
