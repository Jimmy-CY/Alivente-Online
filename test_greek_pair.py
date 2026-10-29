# -*- coding: utf-8 -*-
"""test_greek_pair.py - round GL-3, 29 Oct 2026.

RELEASE 36 - THE GREEK DETAILS PER TENANT, AND NO SECOND ΔΕΗ FIELD. His
decisions of 29 October:

    - the ΔΕΗ field GL-1 added is removed: it duplicated Electricity
      Details, which every property in every country has. A Greek lease
      reads the number from there ("Meter: 3138572" -> 3138572);
    - Floor and Parking on both property reports, and the street line
      without a space before each comma ("Apartment , Afaias 15 , ...");
    - the long address on the property dashboard's report no longer runs
      under the next column;
    - father's name, ΑΦΜ and ΔΟΥ for a property in GREECE only, PER
      TENANT, minimised: a Greek Details button under each person's
      Passport/ID opens a pop-up for that person;
    - a Greek lease with a second tenant names both, "καλούμενοι εφεξής
      από κοινού «οι μισθωτές»", and every reference after it is plural.
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
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_greekpair'
ME = 'test_greek_pair.py'
PATCHER = 'apply_greek_pair.py'
PS1 = 'Push-PendingChanges.ps1'
MARKS = ('GL-3, 29 Oct 2026',)

J = os.path.join
TPL = J(ROOT, 'pages', 'templates')
MODELS = J(ROOT, 'pages', 'models.py')
FORMS = J(ROOT, 'pages', 'forms.py')
PROPS = J(ROOT, 'pages', 'views', 'properties.py')
TENANTS = J(ROOT, 'pages', 'views', 'tenants.py')
LEASE = J(ROOT, 'pages', 'views', 'lease_template.py')
GEN = J(TPL, 'generate_lease_agreement.html')
TEDIT = J(TPL, 'tenant_edit.html')
TADD = J(TPL, 'tenant_add.html')
PEDIT = J(TPL, 'properties_edit.html')
PADD = J(TPL, 'properties_add.html')
REPORT = J(TPL, 'property_report.html')
DETAIL = J(TPL, 'property_detail.html')
HELP = J(ROOT, 'pages', 'help_content', 'administration.html')
OLDGL = J(ROOT, 'test_greek_lease.py')
OLDGE = J(ROOT, 'test_generate_esign.py')
GATE = J(ROOT, PS1)
EDITED = [MODELS, FORMS, PROPS, TENANTS, LEASE, GEN, TEDIT, TADD, PEDIT,
          PADD, REPORT, DETAIL]
UNDATED = [HELP, OLDGL, OLDGE]
MIGRATION = J(ROOT, 'pages', 'migrations', '0115_greek_pair.py')
PLURAL = J(ROOT, 'pages', 'services', 'greek_lease_plural.py')
SHIPS = (MIGRATION, PLURAL)

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
from alv_rounds import as_left_by                          # noqa: E402

NOW = dict((p, as_left_by(p, SUFFIX, read)) for p in EDITED + UNDATED)
OLD = dict((p, was(p)) for p in EDITED + UNDATED)


def py(src):
    return T.python_code_only(src)


def claims(src):
    out = []
    m = py(src[MODELS])
    out.append(('prop_deh_number' not in m and 'def deh_number(self):' in m
                and 'def street_address(self):' in m,
                'no ΔΕΗ column: the number is read from Electricity Details, '
                'and the street line is joined on the model'))
    out.append((all('%s = models.CharField(max_length=' % f in m for f in (
        'tenant_2_father_name', 'tenant_2_afm', 'tenant_2_doy')),
        'the second tenant has his own father\'s name, ΑΦΜ and ΔΟΥ'))
    f = py(src[FORMS])
    out.append(('"prop_deh_number",' not in f
                and "'tenant_2_father_name', 'tenant_2_afm', 'tenant_2_doy',"
                in f, 'the forms follow: no ΔΕΗ, the second tenant\'s three'))
    out.append(("new_tenant.tenant_2_afm = original_tenant.tenant_2_afm"
                in py(src[TENANTS]), 'Duplicate for Renewal copies them'))
    p = py(src[PROPS])
    out.append(("'prop_deh_number': property_obj.deh_number," in p
                and "'tenant_2_afm': tenant_obj.tenant_2_afm or ''," in p,
                'Generate is handed the ΔΕΗ number from Electricity Details '
                'and the second tenant\'s details'))
    lt = py(src[LEASE])
    out.append(("gr_deh = _gr('gr_deh', property_obj, 'deh_number')" in lt
                and "('prop_electricity', 'gr_deh', 255)" in lt,
                'the lease reads ΔΕΗ from Electricity Details and a typed one '
                'fills a blank Electricity Details'))
    out.append(("'tenant_2_afm': gr2_afm," in lt
                and "('tenant_2_afm', 'gr_2_afm', 20)," in lt
                and 'pluralise(temp_file.name, {' in lt,
                'the second tenant\'s details reach the lease, go back onto '
                'the record, and two tenants make the lease plural'))
    g = src[GEN]
    out.append(('id="gr-2-afm"' in g
                and "glGap(document.getElementById('gr-2-afm'))" in g,
                'Generate asks for the second tenant\'s three when there is '
                'one'))
    for pth, name in ((TEDIT, 'Tenant Edit'), (TADD, 'Tenant Add')):
        t = T.code_only(src[pth])
        out.append(('id="gd-btn-1"' in t and 'id="gd-btn-2"' in t
                    and 'id="greekDetailsModal"' in t
                    and "o.getAttribute('data-country')" in src[pth]
                    and 'data-country="{{ results.prop_country|lower }}"' in t
                    and 'id="gl-tenant-row"' not in t
                    and "'gd-2-father', 'gd-2-afm', 'gd-2-doy'" in src[pth],
                    '%s: a Greek Details button per person, the pop-up, and '
                    'Remove Second Tenant empties his' % name))
    for pth, name in ((PEDIT, 'Property Edit'), (PADD, 'Property Add')):
        out.append(('id="prop_deh_number"' not in T.code_only(src[pth]),
                    '%s has no ΔΕΗ box' % name))
    for pth, name in ((REPORT, 'Property Details Report'),
                      (DETAIL, 'the property dashboard\'s report')):
        t = T.code_only(src[pth])
        out.append(('{{ property.street_address }}' in t
                    and "{{ property.prop_floor|default:'Not Available' }}" in t
                    and "{{ property.prop_parking_space|default:'Not "
                        "Available' }}" in t,
                    '%s shows Floor and Parking, and the street line '
                    'without a space before a comma' % name))
    out.append(('max-width: 100%;' in src[DETAIL]
                [src[DETAIL].find('.detail-value {'):][:400],
                '  and a long value wraps inside its column there'))
    return out


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
for p in SHIPS:
    ok(os.path.isfile(p), '%s ships with the round' % os.path.relpath(p, ROOT))
mig = read(MIGRATION) if os.path.isfile(MIGRATION) else ''
ok("('pages', '0114_greek_address_generated_lease')" in mig
   and "RemoveField(model_name='props', name='prop_deh_number')" in mig
   and "prop_electricity='Meter: %s'" in mig
   and "if not (p.prop_electricity or '').strip():" in mig,
   'migration 0115: a ΔΕΗ number moves into a BLANK Electricity Details '
   'before the column goes')
dated = [os.path.relpath(p, ROOT) for p in EDITED
         if not any(mk in NOW[p] for mk in MARKS)]
ok(not dated, 'the round dates itself in every file it edited',
   ', '.join(dated))

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backups')
# ==========================================================================
for cond, msg in claims(OLD):
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
    from pages.services import greek_lease_plural as GP
    from docx import Document
    connection.ensure_connection()
    M.props.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3', 'no database: %s' % str(_e).split('\n')[0][:70])


class Rollback(Exception):
    pass


def doc_text(path):
    return '\n'.join(p.text for p in Document(path).paragraphs)


if have_db:
    import datetime as dt
    ok(M.props(prop_electricity='Meter: 3138572').deh_number == '3138572'
       and M.props(prop_electricity='3138573').deh_number == '3138573'
       and M.props(prop_electricity='Not Available').deh_number == '',
       'Electricity Details "Meter: 3138572" is the ΔΕΗ number 3138572')
    ok(M.props(prop_address1='First Floor Apartment ', prop_address2=' Afaias 15',
               prop_suburb='Palaio Psychiko').street_address
       == 'First Floor Apartment, Afaias 15, Palaio Psychiko',
       'the street line has no space before a comma')
    try:
        with transaction.atomic():
            flat = M.props.objects.create(
                prop_name='GL3 Flat', prop_country='Greece',
                prop_available_for_rent='Yes', prop_status='Active',
                prop_address1='Second Floor Apartment ',
                prop_address2=' Afaias 15 ', prop_suburb='Palaio Psychiko',
                prop_floor='2', prop_parking_space='P2',
                prop_electricity='Meter: 3138573',
                prop_address_greek='οδός Αφαίας αρ. 15, Παλαιό Ψυχικό, '
                                   '154 52')
            cy = M.props.objects.create(
                prop_name='GL3 Cyprus', prop_country='Cyprus',
                prop_available_for_rent='Yes', prop_address1='Foti Pitta 13')
            L = dict(tenant_type='Individual', tenant_current='Yes',
                     tenant_rental_type='Monthly',
                     tenant_lease_start_date=dt.date(2026, 1, 1),
                     tenant_lease_end_date=dt.date(2026, 12, 31),
                     tenant_rent=1250)
            ten = M.tenant.objects.create(
                prop=flat, tenant_name='Ioannis Tzifas',
                tenant_father_name='Γεωργίου', tenant_afm='111',
                tenant_doy='Ψυχικού', tenant_2_name='Kyriaki Liaskoviti',
                tenant_2_email='k@example.com', **L)
            solo = M.tenant.objects.create(prop=cy, tenant_name='GL3 Solo', **L)
            ad = {'start_date': '2026-01-01', 'end_date': '2026-12-31',
                  'monthly_rent': '1250', 'security_deposit': '2500',
                  'extension_period': '12', 'extension_date': '2027-12-31',
                  'has_second_tenant': True,
                  'second_tenant_data': {'tenant_name': 'Kyriaki Liaskoviti'},
                  'gr_2_father_name': 'Νικολάου', 'gr_2_afm': '222',
                  'gr_2_doy': 'Χαλανδρίου'}
            out = doc_text(LT.generate_lease_document(
                'greece', 'greek', flat, ten, ad))
            ok('Ioannis Tzifas του Γεωργίου' in out
               and 'και η/ο Kyriaki Liaskoviti του Νικολάου' in out
               and 'Α.Φ.Μ.: 222, ΔΟΥ: Χαλανδρίου' in out
               and 'καλούμενοι εφεξής από κοινού «οι μισθωτές»' in out,
               'two tenants: the lease names both, each with their own '
               'father, ΑΦΜ and ΔΟΥ')
            ok('Οι μισθωτές ευθύνονται να αποκαταστήσουν' in out
               and 'υπαιτιότητά τους' in out and 'ΟΙ ΜΙΣΘΩΤΕΣ' in out
               and not GP.LEFT.search(out),
               '  and every reference after it is plural - no singular '
               '"μισθώτρια" left')
            ok('ΔΕΗ είναι 3138573.' in out,
               '  and the ΔΕΗ number comes from Electricity Details')
            one = doc_text(LT.generate_lease_document(
                'greece', 'greek', flat, ten,
                dict(ad, has_second_tenant=False, second_tenant_data={})))
            ok('καλούμενη εφεξής η « μισθώτρια»' in one
               and 'Kyriaki' not in one and 'Η ΜΙΣΘΩΤΡΙΑ' in one,
               'one tenant: the lease is the singular one it always was')

            LT._save_greek_back('greece', str(ten.pk), ten, flat, ad)
            ten.refresh_from_db()
            ok(ten.tenant_2_afm == '222' and ten.tenant_2_doy == 'Χαλανδρίου',
               'what Generate was told about the second tenant goes onto '
               'the record')
            LT._save_greek_back('greece', str(ten.pk), ten, flat,
                                dict(ad, gr_2_afm='999'))
            ten.refresh_from_db()
            ok(ten.tenant_2_afm == '222', '  blanks only')
            LT._save_greek_back('greece', str(ten.pk), ten, flat, dict(
                ad, gr_2_doy='X', second_tenant_data={'tenant_name': 'Other'}))
            ten.refresh_from_db()
            ok(ten.tenant_2_doy == 'Χαλανδρίου',
               '  and never onto a record that names a different second '
               'tenant')

            u = User.objects.create_user('gl3', 'gl3@example.com', 'x',
                                         is_superuser=True, is_staff=True)
            c = Client(SERVER_NAME='localhost')
            c.force_login(u)
            r = c.get('/tenant_edit/%d' % ten.pk)
            h = r.content.decode('utf-8')
            ok(r.status_code == 200 and 'id="gd-btn-1"' in h
               and 'id="gd-btn-2"' in h and 'id="greekDetailsModal"' in h
               and 'value="222"' in h and 'id="tenant_afm"' not in h,
               'Tenant Edit: a Greek Details button per person and the '
               'pop-up - no open row of boxes')
            ok('data-country="greece"' in h and 'data-country="cyprus"' in h,
               '  the property options carry their country, which decides')
            post = dict((k, v) for k, v in {
                'tenant_type': 'Individual', 'tenant_current': 'Yes',
                'tenant_name': 'Ioannis Tzifas', 'tenant_contact_number': '1',
                'tenant_email': 'i@example.com', 'tenant_2_name':
                'Kyriaki Liaskoviti', 'tenant_2_email': 'k@example.com',
                'tenant_father_name': 'Γεωργίου', 'tenant_afm': '111',
                'tenant_doy': 'Ψυχικού', 'tenant_2_father_name': 'Νικολάου',
                'tenant_2_afm': '333', 'tenant_2_doy': 'Χαλανδρίου',
                'tenant_lease_start_date': '2026-01-01',
                'tenant_lease_end_date': '2026-12-31',
                'tenant_rental_type': 'Monthly', 'tenant_rent': '1250',
                'tenant_deposit': '2500', 'tenant_levies': '0',
                'tenant_payment_terms': '0', 'prop': str(flat.pk)}.items())
            r = c.post('/tenant_edit_commit/%d' % ten.pk, post)
            ten.refresh_from_db()
            ok(ten.tenant_2_afm == '333',
               '  and Save keeps what the pop-up put in',
               'status %s' % r.status_code)
            h = c.get('/property_report/%d' % flat.pk).content.decode('utf-8')
            ok('Second Floor Apartment, Afaias 15, Palaio Psychiko' in h
               and '>P2<' in h.replace(' ', ''),
               'Property Details Report: Floor, Parking, and the street line')
            h = c.get('/property_detail/%d/property-report/' % flat.pk
                      ).content.decode('utf-8')
            ok('Second Floor Apartment, Afaias 15, Palaio Psychiko' in h
               and '>P2<' in h.replace(' ', ''),
               '  and the property dashboard\'s report')
            h = c.get('/properties_edit/%d' % flat.pk).content.decode('utf-8')
            ok('Meter: 3138573' in h and 'prop_deh_number' not in h,
               'Property Edit: one place for the meter number')
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
ok("Text = 'def pluralise('" in gate,
   '  with a sentinel on the two-tenant Greek lease')
wd = read(J(ROOT, 'test_waiting_down.py'))
nm = re.search(r'CONVERTED_N = (\d+)', wd)
ok(nm and int(nm.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (nm.group(1) if nm else '?', len(T.CONVERTED)))
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')
nob = [os.path.relpath(p, ROOT) for p in EDITED + UNDATED
       if not os.path.isfile(p + SUFFIX)]
ok(not nob, '  every file it edited has its backup', ', '.join(nob))

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
