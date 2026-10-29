# -*- coding: utf-8 -*-
"""apply_housekeeping_five.py - round HK-5, 29 Oct 2026.

RELEASE 38 - HOUSEKEEPING. His decisions of 29 October:

    - cron-service/start.sh is corrected: it named check_lease_renewals,
      which does not exist, and began with a byte-order mark. Railway does
      not run it - the cron-service's Custom Start Command loops and calls
      check_lease_renewal_and_invoices at 06:00 UTC, and his run log of
      29 Oct shows it working - so this is tidying, not a repair.
    - The help gives the run time as 06:00 UTC: 08:00 Cyprus time in
      winter, 09:00 in summer (it said "about 08:00" all year).
    - The Cyprus Greek lease's premises line is built once in
      lease_template.py; the template writes {{ property_address_line_greek }}
      instead of six parts joined by commas. Address (Greek) wins when set.
    - admin_clear and the dead 'api/' exemption are removed.
    - The pyHanko pins stay (xhtml2pdf requires them); test_esign_pdf says so.

Stands on GL-3. Idempotent. Edits backed up to .bak_housekeep5, start.sh
and the Cyprus Greek template included; ships this patcher and its suite.
No migration.
"""
import os
import re
import sys

SUFFIX = '.bak_housekeep5'
MARK = 'HK-5, 29 Oct 2026'
CHECK = False
CREATES = (
    'test_housekeeping_five.py',
)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

START = os.path.join('cron-service', 'start.sh')
START_BYTES = (
    b'#!/bin/sh\n'
    b"# HK-5, 29 Oct 2026 - RAILWAY DOES NOT RUN THIS FILE. The cron-service's\n"
    b'# Custom Start Command is a loop that calls check_lease_renewal_and_invoices\n'
    b'# at 06:00 UTC every day (his screenshot and the run log of 29 Oct). This\n'
    b'# file named check_lease_renewals, a command that does not exist, and began\n'
    b'# with a byte-order mark sh could not read - kept, corrected, so that\n'
    b'# running it by hand does what the daily job does.\n'
    b'set -e\n'
    b'cd /app\n'
    b'exec python manage.py check_lease_renewal_and_invoices\n'
)
GREEKDOC = os.path.join('pages', 'templates', 'lease_templates',
                        'cyprus_greek_lease_template.docx')
OLD_LINE = ('{{ property_address1_greek }}, {{ property_address2_greek }}, '
            '{{ property_suburb_greek }}, {{ property_city_greek }}, '
            '{{ property_province_greek }}, {{ property_pcode }}')
NEW_LINE = '{{ property_address_line_greek }}'

SWAPS = [
    (os.path.join('pages', 'views', 'lease_template.py'), [
        (r'''        'property_city_greek': translate_to_greek(property_obj.prop_city or ''),
        'property_province_greek': translate_to_greek(property_obj.prop_province or ''),

        # Lease terms
''',
         r'''        'property_city_greek': translate_to_greek(property_obj.prop_city or ''),
        'property_province_greek': translate_to_greek(property_obj.prop_province or ''),
        # HK-5, 29 Oct 2026 - THE PREMISES LINE OF THE CYPRUS GREEK LEASE,
        # built once. The template joined six parts with commas, so a blank
        # part printed ", ," ("Λευκωσία, , 2054"). The property's Address
        # (Greek), when filled, is written as typed - his wording, not a
        # word-by-word translation; otherwise the translated parts that
        # are not blank, then the post code.
        'property_address_line_greek': (
            (getattr(property_obj, 'prop_address_greek', '') or '').strip()
            or ', '.join(p for p in (
                translate_to_greek((v or '').strip()) for v in (
                    property_obj.prop_address1, property_obj.prop_address2,
                    property_obj.prop_suburb, property_obj.prop_city,
                    property_obj.prop_province))
                if p and p.strip())
            + (', ' + property_obj.prop_pcode.strip()
               if (property_obj.prop_pcode or '').strip() else '')),

        # Lease terms
'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <div class="alert" style="background:#e7f5f8; border-left:4px solid #0e7c8b;">
      <i class="fas fa-robot"></i> <strong>There is no Generate Invoices card any more &mdash; and nothing to press.</strong>
      <p class="mb-1 mt-2">Rent invoices for collection are created by a background job that runs <strong>once a day, each morning at about 08:00 Cyprus time</strong> (06:00 UTC), all month. It always dates them the <strong>1st of the current month</strong> and skips any tenant who already has one, so it is <em>self-healing</em>: add a tenant on the 15th and their invoice appears the next morning, correctly dated the 1st.</p>
      <!-- HK-1, 26 Oct 2026 - ONCE A DAY, not on a five-minute cycle: that is what the Railway cron service actually runs (his screenshot). It cannot run more often, because each run also sends the daily digest emails. -->
      <p class="mb-0">The button that used to sit here duplicated that job, and did it worse &mdash; it created invoices without an amount, which the job always sets. It was removed on 25 Aug 2026, having never created an invoice that survives on Live.</p>
''',
         r'''    <div class="alert" style="background:#e7f5f8; border-left:4px solid #0e7c8b;">
      <i class="fas fa-robot"></i> <strong>There is no Generate Invoices card any more &mdash; and nothing to press.</strong>
      <p class="mb-1 mt-2">Rent invoices for collection are created by a background job that runs <strong>once a day, each morning at 06:00 UTC</strong> &mdash; 08:00 Cyprus time in winter, 09:00 in summer &mdash; all month. It always dates them the <strong>1st of the current month</strong> and skips any tenant who already has one, so it is <em>self-healing</em>: add a tenant on the 15th and their invoice appears the next morning, correctly dated the 1st.</p>
      <!-- HK-1, 26 Oct 2026 - ONCE A DAY, not on a five-minute cycle: that is what the Railway cron service actually runs (his screenshot). It cannot run more often, because each run also sends the daily digest emails. -->
      <p class="mb-0">The button that used to sit here duplicated that job, and did it worse &mdash; it created invoices without an amount, which the job always sets. It was removed on 25 Aug 2026, having never created an invoice that survives on Live.</p>
'''),
        (r'''        <p class="mb-1"><strong>Language</strong> options depend on the country chosen:</p>
        <ul class="mb-1">
          <li><strong>Cyprus</strong> &rarr; English or Greek</li>
          <li><strong>Greece</strong> &rarr; Greek</li>
          <li><strong>Spain</strong> &rarr; Spanish (when launched)</li>
''',
         r'''        <p class="mb-1"><strong>Language</strong> options depend on the country chosen:</p>
        <ul class="mb-1">
          <li><strong>Cyprus</strong> &rarr; English or Greek. The Greek lease writes the premises from the property's <strong>Address (Greek)</strong> when it is filled in; otherwise the address parts are translated word by word.</li>
          <li><strong>Greece</strong> &rarr; Greek</li>
          <li><strong>Spain</strong> &rarr; Spanish (when launched)</li>
'''),
        (r'''      <div class="card-body">
        <h6 style="color:#0e7c8b;"><i class="fas fa-bell"></i> <strong>Reminders</strong></h6>
        <p class="mb-0">On <strong>day 3</strong> and on <strong>the day before the closing day</strong> (day 3 and day 6 of the usual seven), to whoever has not signed &mdash; never to somebody who has. They go out with the <strong>morning run, at about 08:00 Cyprus time</strong>. Each reminder carries a <strong>fresh link</strong>; the earlier one stops working.</p>
      </div>
    </div>
''',
         r'''      <div class="card-body">
        <h6 style="color:#0e7c8b;"><i class="fas fa-bell"></i> <strong>Reminders</strong></h6>
        <p class="mb-0">On <strong>day 3</strong> and on <strong>the day before the closing day</strong> (day 3 and day 6 of the usual seven), to whoever has not signed &mdash; never to somebody who has. They go out with the <strong>morning run, at 06:00 UTC</strong> (08:00 Cyprus time in winter, 09:00 in summer). Each reminder carries a <strong>fresh link</strong>; the earlier one stops working.</p>
      </div>
    </div>
'''),
    ]),
    (os.path.join('pages', 'help_content', 'operational.html'), [
        (r'''      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>Tenant invoices &mdash; automatic</strong></h6>
        <p class="mb-0" style="font-size:13px;">A background job runs <strong>once a day, each morning at about 08:00 Cyprus time</strong>. It does nothing for most of the month, then in the <strong>last five days</strong> it drafts an invoice for each flagged tenant for the <em>month ahead</em>. You review and approve; a second job numbers, e-mails and files them. Your only job is approving.</p>
      </div>
    </div>
''',
         r'''      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>Tenant invoices &mdash; automatic</strong></h6>
        <p class="mb-0" style="font-size:13px;">A background job runs <strong>once a day, each morning at 06:00 UTC</strong> (08:00 Cyprus time in winter, 09:00 in summer). It does nothing for most of the month, then in the <strong>last five days</strong> it drafts an invoice for each flagged tenant for the <em>month ahead</em>. You review and approve; a second job numbers, e-mails and files them. Your only job is approving.</p>
      </div>
    </div>
'''),
        (r'''           data-tab-icon="fa-users">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-users"></i> The automatic monthly cycle</h6>
    <p>Tenant rent invoices are handled on a schedule, so you never draft them by hand. A background job runs <strong>once a day, each morning at about 08:00 Cyprus time</strong> (06:00 UTC), all month; for most of the month it has nothing to do. The cycle:</p>
    <!-- HK-1, 26 Oct 2026 - ONCE A DAY, not on a five-minute cycle: what the Railway cron service actually runs. Each run also sends the daily digests, so it cannot run more often. -->

''',
         r'''           data-tab-icon="fa-users">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-users"></i> The automatic monthly cycle</h6>
    <p>Tenant rent invoices are handled on a schedule, so you never draft them by hand. A background job runs <strong>once a day, each morning at 06:00 UTC</strong> &mdash; 08:00 Cyprus time in winter, 09:00 in summer &mdash; all month; for most of the month it has nothing to do. The cycle:</p>
    <!-- HK-1, 26 Oct 2026 - ONCE A DAY, not on a five-minute cycle: what the Railway cron service actually runs. Each run also sends the daily digests, so it cannot run more often. -->

'''),
    ]),
    (os.path.join('pages', 'views', 'administration.py'), [
        (r'''- upload_title_deed      : Upload a property title-deed PDF to
                           STATIC_ROOT/title_deeds.
- admin_clear            : Delete generated report PDFs from
                           STATIC_ROOT/reports.

Auth tiers
----------
superuser only            -> admin_clear (@user_passes_test is_superuser)
login only                -> my_profile
can_access_administration -> admin_apms
''',
         r'''- upload_title_deed      : Upload a property title-deed PDF to
                           STATIC_ROOT/title_deeds.

HK-5, 29 Oct 2026 - admin_clear is gone: no page linked to it, nothing
writes to STATIC_ROOT/reports any more, and it deleted files on a GET.

Auth tiers
----------
login only                -> my_profile
can_access_administration -> admin_apms
'''),
        (r'''"""

import glob
import os
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
    user_passes_test,
)
from django.contrib.auth.models import User
''',
         r'''"""

import os
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
)
from django.contrib.auth.models import User
'''),
        (r'''    return redirect('admin_apms')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_clear(request):
    # Clear generated report PDFs. Path derived from STATIC_ROOT (same
    # pattern as the lease/title-deed dirs above) so this works on Live;
    # the previous hard-coded local Windows path made this a no-op there.
    file_path = os.path.join(settings.STATIC_ROOT, 'reports', '*.pdf')
    files = glob.glob(file_path)
    for f in files:
        os.remove(f)
    return redirect("admin_apms")
''',
         r'''    return redirect('admin_apms')

'''),
    ]),
    (os.path.join('pages', 'urls.py'), [
        (r'''    path('admin_apms/', views.admin_apms, name='admin_apms'),
    path('personal/', views.personal_page, name='personal_page'),
    path('admin_clear/', views.admin_clear, name='admin_clear'),
    path('upload_title_deed/', views.upload_title_deed, name='upload_title_deed'),
    path('title_deeds_management/', views.title_deeds_management, name='title_deeds_management'),
''',
         r'''    path('admin_apms/', views.admin_apms, name='admin_apms'),
    path('personal/', views.personal_page, name='personal_page'),
    # HK-5, 29 Oct 2026 - admin_clear/ removed: no page linked to it.
    path('upload_title_deed/', views.upload_title_deed, name='upload_title_deed'),
    path('title_deeds_management/', views.title_deeds_management, name='title_deeds_management'),
'''),
    ]),
    (os.path.join('pages', 'middleware.py'), [
        (r'''            'sign/',
            'accounts/',
            'api/',  # If you have API endpoints
            # DP-1, 22 Oct 2026 - THE DEPLOY PROBE.
            #
''',
         r'''            'sign/',
            'accounts/',
            # HK-5, 29 Oct 2026 - 'api/' removed: nothing is mounted under
            # it, and an exempt prefix with nothing behind it is a door
            # left open for whatever is added there next.
            # DP-1, 22 Oct 2026 - THE DEPLOY PROBE.
            #
'''),
        (r'''            # login form as the running version for ever.
            #
            # ON ITS OWN LINE RATHER THAN UNDER 'api/'. That prefix is
            # already exempt and would have carried this for free - but
            # nothing is mounted under api/ anywhere in the tree, so it
            # is dead configuration, and hiding a deliberate public
            # endpoint inside dead configuration is how the reason gets
            # lost. This one says what it is.
            'version/',
            'media/',  # Media files
''',
         r'''            # login form as the running version for ever.
            #
            # ON ITS OWN LINE, with its own reason. (The 'api/' prefix
            # that could have carried it was dead configuration and HK-5
            # removed it.)
            'version/',
            'media/',  # Media files
'''),
        (r'''            # ---------- ADMINISTRATION ----------
            ('admin_apms', 'auth.can_access_administration'),
            ('admin_clear', 'auth.can_access_administration'),
            ('user-administration', 'auth.can_access_administration'),
            ('setup-permissions', 'auth.can_access_administration'),
''',
         r'''            # ---------- ADMINISTRATION ----------
            ('admin_apms', 'auth.can_access_administration'),
            ('user-administration', 'auth.can_access_administration'),
            ('setup-permissions', 'auth.can_access_administration'),
'''),
    ]),
    (os.path.join('test_esign_pdf.py'), [
        (r'''# this round leaves them exactly where they are - and says so here,
# so the finding is not lost between rounds.
ok('pyHanko' in NOW[REQ] and 'pyHanko' in OLD[REQ],
   'CONTROL: the unused pyHanko pins are left alone - removing them '
''',
         r'''# this round leaves them exactly where they are - and says so here,
# so the finding is not lost between rounds.
#
# HK-5, 29 Oct 2026 - AND THEY MUST STAY. xhtml2pdf 0.2.16 (receipts and
# the PDF reports) declares Requires-Dist pyHanko >=0.12.1 and
# pyhanko-certvalidator >=0.19.5. Nothing imports them because xhtml2pdf
# does; taking the pins out would not remove them, it would only let pip
# choose their versions.
ok('pyHanko' in NOW[REQ] and 'pyHanko' in OLD[REQ],
   'CONTROL: the unused pyHanko pins are left alone - removing them '
'''),
    ]),
    (os.path.join('test_deploy_probe.py'), [
        (r'''   'the exempt line carries its reason, so the next person to read '
   'that list knows what it is for')
ok("'api/'" in NOW[MID],
   'GUARD: api/ is still exempt and this round did not quietly change '
   'it - nothing is mounted there, which is worth knowing and is not '
   'this round to decide')


''',
         r'''   'the exempt line carries its reason, so the next person to read '
   'that list knows what it is for')
# HK-5, 29 Oct 2026 - decided: the dead 'api/' prefix is gone. Asked of
# the code, so a comment naming it does not count.
ok("'api/'" not in T.python_code_only(NOW[MID]),
   'api/ is no longer exempt - nothing was mounted there (HK-5)')


'''),
    ]),
    (os.path.join('test_help_physical_invoices.py'), [
        (r'''      'once a day, each morning' in OV and 'once a day, each morning' in TEN
      and 'every five minutes' not in OV + TEN)
check('  and the cron service runs the command that drives this',
      'check_lease_renewals' in read(os.path.join(ROOT, 'cron-service',
                                                  'start.sh')))
check('  which calls the prepare command',
      "call_command('prepare_physical_invoices')" in RUN_SRC)
''',
         r'''      'once a day, each morning' in OV and 'once a day, each morning' in TEN
      and 'every five minutes' not in OV + TEN)
# HK-5, 29 Oct 2026 - CORRECTED: Railway does not run start.sh. The
# cron-service's Custom Start Command loops and calls the job at 06:00 UTC
# (his screenshot and run log, 29 Oct). start.sh named check_lease_renewals,
# which does not exist; it now names the command that does.
check('  and the cron service runs the command that drives this',
      'python manage.py check_lease_renewal_and_invoices' in read(
          os.path.join(ROOT, 'cron-service', 'start.sh')))
check('  which calls the prepare command',
      "call_command('prepare_physical_invoices')" in RUN_SRC)
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
    raise SystemExit('HK-5 REFUSED: %s' % msg)


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
    if "'test_housekeeping_five.py'" in read(pq):
        print('HK-5 already applied.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_greek_pair.py'" not in read(pq):
        refuse('GL-3 is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, rel)):
            refuse('%s is missing - it ships with this patcher; copy it in '
                   'first.' % rel)

    # ---- THE SWAPS
    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    # ---- REGISTRATION
    q = out.get(pq, read(pq))
    q = swap(q, """    'test_greek_pair.py'
)""", """    'test_greek_pair.py',
    # HK-5, 29 Oct 2026 - housekeeping: the daily job, the Cyprus Greek
    # premises line, admin_clear and api/.
    'test_housekeeping_five.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'pages/services/greek_lease_plural.py'; Text = 'def pluralise(';""",
        """    @{ File = 'cron-service/start.sh'; Text = 'python manage.py check_lease_renewal_and_invoices'; What = 'HK-5: the daily job runs the command that exists - without it the 06:00 UTC run fails and physical invoices, e-signing expiry and reminders never happen' },
    @{ File = 'pages/services/greek_lease_plural.py'; Text = 'def pluralise(';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_greek_pair.py',
]""", """    'test_greek_pair.py',
    # HK-5, 29 Oct 2026 - housekeeping.
    'test_housekeeping_five.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_greekpair',
]""", """    '.bak_greekpair',
    # HK-5, 29 Oct 2026 - housekeeping: the daily job, the Cyprus Greek
    # premises line, admin_clear and api/.
    '.bak_housekeep5',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # HK-5, 29 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE TWO FILES THAT ARE NOT TEXT SWAPS
    # start.sh is written as exact bytes: a text swap would keep the BOM
    # and fit() would turn its new lines into CRLF, the two faults this
    # round removes.
    ps = os.path.join(root, START)
    if not os.path.isfile(ps):
        refuse('%s is missing' % START)
    with open(ps, 'rb') as f:
        cur = f.read()
    if b'check_lease_renewals' not in cur:
        refuse('%s does not name check_lease_renewals - it has changed '
               'shape since this round was written' % START)
    # The Cyprus Greek template: one paragraph, edited with python-docx,
    # its first run kept for the formatting.
    pg = os.path.join(root, GREEKDOC)
    from docx import Document
    gdoc = Document(pg)
    hits = [p for p in gdoc.paragraphs if p.text.strip() == OLD_LINE]
    if len(hits) != 1:
        refuse('%s: the premises line was found %d time(s), expected 1'
               % (GREEKDOC, len(hits)))

    # ---------------------------------------------------------- THE GATES
    if "'property_address_line_greek': (" not in out[os.path.join(
            root, 'pages', 'views', 'lease_template.py')]:
        refuse('lease_template.py does not build the premises line.')

    if CHECK:
        print('HK-5 --check: %d file(s) would change, none written; %d '
              'ship with it.' % (len(out), len(CREATES)))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    if not os.path.exists(ps + SUFFIX):
        with open(ps + SUFFIX, 'wb') as f:
            f.write(cur)
    with open(ps, 'wb') as f:
        f.write(START_BYTES)
    if not os.path.exists(pg + SUFFIX):
        with open(pg, 'rb') as f:
            keep = f.read()
        with open(pg + SUFFIX, 'wb') as f:
            f.write(keep)
    para = hits[0]
    for r in para.runs[1:]:
        r._r.getparent().remove(r._r)
    para.runs[0].text = NEW_LINE
    gdoc.save(pg)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('HK-5 applied - the daily job runs the real command; the Cyprus '
          'Greek premises line is built once; admin_clear and api/ gone.')
    print('      No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
