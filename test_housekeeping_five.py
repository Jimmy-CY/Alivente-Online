# -*- coding: utf-8 -*-
"""test_housekeeping_five.py - round HK-5, 29 Oct 2026.

RELEASE 38 - HOUSEKEEPING. His decisions of 29 October:

    - cron-service/start.sh named check_lease_renewals - a command that
      does not exist - behind a byte-order mark sh could not read. Railway
      does not run it (the cron-service's Custom Start Command loops and
      calls check_lease_renewal_and_invoices at 06:00 UTC; his run log of
      29 Oct shows it working), so it is corrected rather than repaired.
    - The help gives the run time as 06:00 UTC: 08:00 Cyprus time in winter,
      09:00 in summer.
    - THE CYPRUS GREEK LEASE'S PREMISES LINE is built once: no ", ," for a
      blank part, and the property's Address (Greek) as typed when filled.
    - admin_clear (no page linked to it; deleted files on a GET) and the
      dead 'api/' exemption are removed.
    - The pyHanko pins STAY: xhtml2pdf requires them.
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

SUFFIX = '.bak_housekeep5'
ME = 'test_housekeeping_five.py'
PATCHER = 'apply_housekeeping_five.py'
PS1 = 'Push-PendingChanges.ps1'
MARKS = ('HK-5, 29 Oct 2026',)

J = os.path.join
START = J(ROOT, 'cron-service', 'start.sh')
CMD = J(ROOT, 'pages', 'management', 'commands',
        'check_lease_renewal_and_invoices.py')
LEASE = J(ROOT, 'pages', 'views', 'lease_template.py')
ADMIN = J(ROOT, 'pages', 'views', 'administration.py')
URLS = J(ROOT, 'pages', 'urls.py')
MID = J(ROOT, 'pages', 'middleware.py')
HELP = J(ROOT, 'pages', 'help_content', 'administration.html')
HELP_O = J(ROOT, 'pages', 'help_content', 'operational.html')
REQ = J(ROOT, 'mysite', 'cron-requirements.txt')
GREEKDOC = J(ROOT, 'pages', 'templates', 'lease_templates',
             'cyprus_greek_lease_template.docx')
GATE = J(ROOT, PS1)
EDITED = [START, LEASE, ADMIN, URLS, MID]
UNDATED = [HELP, HELP_O, J(ROOT, 'test_esign_pdf.py'), J(ROOT, 'test_deploy_probe.py'),
           J(ROOT, 'test_help_physical_invoices.py')]

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


def raw(p):
    with open(p, 'rb') as f:
        return f.read()


def docx_text(p):
    from docx import Document
    return '\n'.join(x.text for x in Document(p).paragraphs)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402


def claims(start_raw, lease, admin, urls, mid, greek):
    out = []
    out.append((not start_raw.startswith(b'\xef\xbb\xbf')
                and b'\r' not in start_raw
                and start_raw.startswith(b'#!/bin/sh\n'),
                'start.sh is plain LF with no byte-order mark, so sh reads '
                'its first line as the shebang it is'))
    # The commands only - the file's own comment names the old one.
    code = b'\n'.join(l for l in start_raw.split(b'\n')
                      if not l.lstrip().startswith(b'#'))
    out.append((b'python manage.py check_lease_renewal_and_invoices'
                in code and b'check_lease_renewals' not in code,
                '  and it runs check_lease_renewal_and_invoices, not the '
                'command that does not exist'))
    out.append(("'property_address_line_greek': (" in T.python_code_only(lease),
                'the Cyprus Greek premises line is built once in the code'))
    out.append(('{{ property_address_line_greek }}' in greek
                and '{{ property_province_greek }}' not in greek,
                '  and the template writes it, not six parts joined by '
                'commas'))
    out.append(('def admin_clear(' not in T.python_code_only(admin)
                and 'admin_clear' not in T.python_code_only(urls)
                and "'admin_clear'" not in T.python_code_only(mid),
                'admin_clear is gone: view, route and permission rule'))
    out.append(("'api/'" not in T.python_code_only(mid),
                'the dead api/ exemption is gone'))
    return out


def now():
    return claims(raw(START), read(LEASE), read(ADMIN), read(URLS),
                  read(MID), docx_text(GREEKDOC))


def before():
    return claims(raw(START + SUFFIX), was(LEASE), was(ADMIN), was(URLS),
                  was(MID), docx_text(GREEKDOC + SUFFIX))


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in now():
    ok(cond, msg)
hh = read(HELP) + read(HELP_O)
ok('about 08:00 Cyprus time' not in hh
   and hh.count('08:00 Cyprus time in winter, 09:00 in summer') == 4,
   'the help gives the run as 06:00 UTC - 08:00 in winter, 09:00 in summer')
ok(os.path.isfile(CMD), 'the command start.sh runs exists: '
   'check_lease_renewal_and_invoices.py')
req = read(REQ)
ok('pyHanko==' in req and 'pyhanko-certvalidator==' in req
   and 'xhtml2pdf==' in req,
   'GUARD: the pyHanko pins stay - xhtml2pdf requires them')
dated = [os.path.relpath(p, ROOT) for p in EDITED
         if not any(mk in read(p) for mk in MARKS)]
ok(not dated, 'the round dates itself in every file it edited',
   ', '.join(dated))

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backups')
# ==========================================================================
for cond, msg in before():
    ok(not cond, 'CONTROL: before this round - %s' % msg.strip())

# ==========================================================================
head('3. DRIVEN')
# ==========================================================================
have_db = False
try:
    import django
    django.setup()
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import User
    import pages.models as M
    from pages.views import lease_template as LT
    connection.ensure_connection()
    M.props.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3', 'no database: %s' % str(_e).split('\n')[0][:70])


class Rollback(Exception):
    pass


if have_db:
    import datetime as dt
    try:
        with transaction.atomic():
            p = M.props.objects.create(
                prop_name='HK5 Flat', prop_country='Cyprus',
                prop_available_for_rent='Yes',
                prop_address1='Savva Home 18, Office 103',
                prop_address2='Agias Annas 4', prop_suburb='Strovolos',
                prop_city='Nicosia', prop_province='', prop_pcode='2054')
            t = M.tenant.objects.create(
                prop=p, tenant_type='Individual', tenant_name='HK5 Tenant',
                tenant_current='Yes', tenant_rental_type='Monthly',
                tenant_lease_start_date=dt.date(2026, 11, 1),
                tenant_lease_end_date=dt.date(2027, 10, 31), tenant_rent=800)
            ad = {'start_date': '2026-11-01', 'end_date': '2027-10-31',
                  'monthly_rent': '800', 'security_deposit': '800',
                  'extension_period': '12', 'rental_increase': '0',
                  'communal_expenses': '0'}
            out = docx_text(LT.generate_lease_document('cyprus', 'greek',
                                                       p, t, ad))
            ok(', ,' not in out and ', 2054' in out,
               'a blank province leaves no ", ," in the Cyprus Greek lease')
            M.props.objects.filter(pk=p.pk).update(
                prop_address_greek='Σάββα Χόουμ 18, Γραφείο 103, Αγίας Άννας '
                                   '4, Στρόβολος, Λευκωσία 2054')
            p.refresh_from_db()
            out = docx_text(LT.generate_lease_document('cyprus', 'greek',
                                                       p, t, ad))
            ok('Σάββα Χόουμ 18, Γραφείο 103, Αγίας Άννας 4, Στρόβολος, '
               'Λευκωσία 2054' in out,
               '  and an Address (Greek) is written as typed')
            u = User.objects.create_user('hk5', 'hk5@example.com', 'x',
                                         is_superuser=True, is_staff=True)
            c = Client(SERVER_NAME='localhost')
            c.force_login(u)
            ok(c.get('/admin_clear/').status_code == 404,
               '/admin_clear/ answers 404')
            ok(c.get('/admin_apms/').status_code in (200, 301, 302),
               '  and Administration still opens')
            raise Rollback()
    except Rollback:
        pass

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("check_lease_renewal_and_invoices'; What = 'HK-5" in gate,
   '  with a sentinel on start.sh')
wd = read(J(ROOT, 'test_waiting_down.py'))
nm = re.search(r'CONVERTED_N = (\d+)', wd)
ok(nm and int(nm.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (nm.group(1) if nm else '?', len(T.CONVERTED)))
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')
nob = [os.path.relpath(p, ROOT) for p in EDITED + UNDATED + [GREEKDOC]
       if not os.path.isfile(p + SUFFIX)]
ok(not nob, '  every file it changed has its backup', ', '.join(nob))

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
