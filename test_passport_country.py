# -*- coding: utf-8 -*-
"""test_passport_country.py - round PC-1, 28 Oct 2026.

RELEASE 31 - THE PASSPORT/ID COUNTRY, AND ONE BLOCK PER PERSON IN
GENERATE. His decisions of 28 October, renders approved:

    - The tenant record keeps the country that issued each Passport/ID,
      for both people (migration 0111), chosen from one list - Cyprus
      and Greece first - so it is spelt one way.
    - Tenant Add and Edit: the country shares the Passport/ID box, his
      option A - the row stays four columns.
    - The Tenant report and the Property Dashboard show it beside the
      number: "991960 · Cyprus".
    - Generate Lease Agreement: each tenant is one block - Name,
      Passport/ID, its country, Email, Phone, Address. A line the record
      fills is text; a blank one is a box in its own place, and what is
      typed there goes back to the record (blanks only, never an
      overwrite). Two tenants stand side by side and the property
      becomes a strip above them (his layout A); Add Second Tenant opens
      that layout with empty boxes and the address ticked Same as
      Tenant. The company layout is unchanged.
    - Found on the way: Duplicate for Renewal never copied the Passport/
      IDs or the Company Reg Number. It copies them now, with the
      countries.
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

SUFFIX = '.bak_passcountry'
ME = 'test_passport_country.py'
PATCHER = 'apply_passport_country.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'PC-1, 28 Oct 2026'

J = os.path.join
TPL = J(ROOT, 'pages', 'templates')
MODELS = J(ROOT, 'pages', 'models.py')
FORMS = J(ROOT, 'pages', 'forms.py')
TENANTS = J(ROOT, 'pages', 'views', 'tenants.py')
PROPS = J(ROOT, 'pages', 'views', 'properties.py')
ISSUES = J(ROOT, 'pages', 'views', 'issues.py')
LEASE = J(ROOT, 'pages', 'views', 'lease_template.py')
ADD = J(TPL, 'tenant_add.html')
EDIT = J(TPL, 'tenant_edit.html')
REPORT = J(TPL, 'tenant_report.html')
DASH = J(TPL, 'property_detail.html')
GEN = J(TPL, 'generate_lease_agreement.html')
GATE = J(ROOT, PS1)
SETTINGS = J(ROOT, 'mysite', 'settings.py')
EDITED = (MODELS, FORMS, TENANTS, PROPS, ISSUES, LEASE, ADD, EDIT, REPORT,
          DASH, GEN, SETTINGS, J(ROOT, 'test_joint_contact.py'),
          J(ROOT, 'test_surface_border.py'))
MIGRATION = J(ROOT, 'pages', 'migrations', '0111_tenant_id_country.py')
COUNTRIES = J(ROOT, 'pages', 'countries.py')
TAG = J(ROOT, 'pages', 'templatetags', 'alv_countries.py')

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

NOW = dict((p, as_left_by(p, SUFFIX, read)) for p in EDITED)
OLD = dict((p, was(p)) for p in EDITED)


def py(src):
    return T.python_code_only(src)


def claims(src):
    out = []
    m = py(src[MODELS])
    out.append(('tenant_id_country = models.CharField(max_length=100, '
                'blank=True)' in m
                and 'tenant_2_id_country = models.CharField(max_length=100, '
                'blank=True)' in m,
                'the tenant record keeps both Passport/ID countries, blank '
                'by default'))
    f = py(src[FORMS])
    out.append(("'tenant_id_country', 'tenant_2_id_country'," in f,
                'TenantForm names them, so a save keeps them'))
    for p, name in ((ADD, 'Tenant Add'), (EDIT, 'Tenant Edit')):
        t = T.code_only(src[p])
        out.append(('{% load alv_countries %}' in t
                    and t.count('class="input-group alv-id-pair"') == 2
                    and 'name="tenant_id_country"' in t
                    and 'name="tenant_2_id_country"' in t
                    and t.count('{% id_country_options') == 2
                    and "'tenant_2_id_country'," in src[p],
                    '%s: each Passport/ID box holds its country, option A, '
                    'and Remove Second Tenant clears it' % name))
    out.append(('"builtins": ["pages.templatetags.alv_countries"]' in
                py(src[SETTINGS]),
                'the country tag is a template builtin, so a page renders '
                'it with or without a load - and so do the suites that '
                'render a slice of one'))
    d = py(src[TENANTS])
    out.append((all('new_tenant.%s = original_tenant.%s' % (c, c) in d
                    for c in ('tenant_company_reg_no', 'tenant_id_number',
                              'tenant_id_country', 'tenant_2_id_number',
                              'tenant_2_id_country')),
                'Duplicate for Renewal copies the identity numbers and '
                'their countries'))
    out.append(("'tenant_id_country': tenant_obj.tenant_id_country or ''"
                in py(src[PROPS]),
                'Generate is handed the countries with the rest of the '
                'tenant'))
    for p, v, name in ((REPORT, 'tenant', 'Tenant report'),
                       (DASH, 'active_tenant', 'Property Dashboard')):
        t = T.code_only(src[p])
        out.append((' <span class="alv-id-country">{{ %s.tenant_id_country'
                    '|default:"" }}</span>' % v in t
                    and '{{ %s.tenant_2_id_country|default:"" }}' % v in t
                    and '.alv-id-country:not(:empty)::before' in src[p],
                    '%s shows each country beside its number' % name))
    out.append(("'tenant_id_country', 'tenant_2_id_country'," in
                py(src[ISSUES]),
                '  and the report fetches them rather than a query each'))
    g = T.code_only(src[GEN])
    once = all(g.count('id="%s"' % i) == 1 for i in (
        'existing-tenant-passport', 'existing-tenant-passport-country',
        'second-tenant-name', 'second-tenant-passport',
        'second-tenant-passport-country', 'second-tenant-email',
        'second-tenant-phone', 'second-tenant-address',
        'existing-tenant-registration'))
    out.append((once and 'id="gl-people"' in g
                and 'id="gl-property-strip"' in g
                and '<div class="col-md-6" id="second-tenant-section"' in g,
                'Generate: one block per person, Tenant 2 a column beside '
                'the first, every box the save reads still there once'))
    out.append(('<select class="form-control gl-input" id="existing-tenant-'
                'passport-country"' in g
                and '<select class="form-control gl-input" id="second-'
                'tenant-passport-country"' in g
                and '<select class="form-control" id="new-tenant-passport-'
                'country"' in g,
                '  and every Passport/ID country there is the one list'))
    sec = g[g.find('id="existing-tenant-section"'):
            g.find('<div id="new-tenant-section"')]
    out.append(('existing-tenant-passport' not in sec
                and 'existing-tenant-registration' in sec,
                '  the old Additional Information section keeps only the '
                'company\'s registration number'))
    js = T.code_only_js(src[GEN])
    out.append(('function glLine(' in js and 'function glSecond(' in js
                and 'function glLayout(' in js and 'function esc(' in js,
                '  and the script that fills a block, locks a known line '
                'and switches the layout'))
    lt = py(src[LEASE])
    out.append(('def _save_identity_back(' in lt
                and '_save_identity_back(tenant_id, tenant_obj, '
                'additional_data)' in lt,
                'a Passport/ID or country typed in Generate goes back to '
                'the record'))
    return out


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
for p in (MIGRATION, COUNTRIES, TAG):
    ok(os.path.isfile(p), '%s ships with the round' % os.path.relpath(p, ROOT))
mig = read(MIGRATION) if os.path.isfile(MIGRATION) else ''
ok("('pages', '0110_notification_type_cash_receipt')" in mig
   and mig.count('migrations.AddField(') == 2
   and "name='tenant_id_country'" in mig
   and "name='tenant_2_id_country'" in mig,
   'migration 0111 adds the two columns after 0110, and nothing else')
dated = [os.path.relpath(p, ROOT) for p in EDITED if MARK not in NOW[p]]
ok(not dated, 'the round dates itself in every file it edited',
   ', '.join(dated))

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backups')
# ==========================================================================
held = [m for c, m in claims(OLD) if c]
ok(not held, 'CONTROL: not one of this round\'s claims held before it',
   '\n'.join(held))

# ==========================================================================
head('3. THE LIST AND THE TAG')
# ==========================================================================
from pages.countries import (ID_COUNTRIES, ID_COUNTRIES_TOP,   # noqa: E402
                             ID_COUNTRIES_REST)
ok(ID_COUNTRIES_TOP == ['Cyprus', 'Greece'] and
   ID_COUNTRIES[:2] == ['Cyprus', 'Greece'],
   'Cyprus and Greece come first')
ok(ID_COUNTRIES_REST == sorted(ID_COUNTRIES_REST)
   and len(set(ID_COUNTRIES)) == len(ID_COUNTRIES)
   and not set(ID_COUNTRIES_TOP) & set(ID_COUNTRIES_REST),
   '  then the rest A to Z, each once (%d in all)' % len(ID_COUNTRIES))
ok(all(c in ID_COUNTRIES for c in ('United Kingdom', 'Russia', 'Ukraine',
                                   'Israel', 'Lebanon', 'South Africa')),
   '  and the ones his tenancies meet are on it')

django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.template import Context, Template
    django_up = True
except Exception as e:                                       # noqa: BLE001
    skip('sections 3 and 4', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])

if django_up:
    def opts(v):
        return Template('{% load alv_countries %}{% id_country_options v %}'
                        ).render(Context({'v': v}))
    h = opts('Greece')
    ok(h.startswith('<option value="">Country</option>')
       and '<option value="Greece" selected>Greece</option>' in h
       and h.count(' selected') == 1,
       'the tag selects the saved country, after a blank "Country"')
    h = opts('Kypros')
    ok('<option value="Kypros" selected>Kypros</option>' in h
       and h.count(' selected') == 1,
       '  and offers a value typed before the list, rather than losing it '
       'on the next save')
    h = opts('<b>x</b>')
    ok('<b>' not in h, '  escaped')
    ok(opts('').count(' selected') == 0, '  and selects nothing when blank')

# ==========================================================================
head('4. DRIVEN - the record, the renewal, the report, the save-back')
# ==========================================================================


class Rollback(Exception):
    """Nothing this suite writes survives it."""


have_db = False
if django_up:
    try:
        from django.contrib.auth.models import User
        from django.db import connection, transaction
        from django.test import Client
        import pages.models as M
        from pages.forms import TenantForm
        from pages.views import lease_template as LT
        connection.ensure_connection()
        M.tenant.objects.exists()
        have_db = True
    except Exception as _e:                                   # noqa: BLE001
        skip('section 4', 'no database: %s' % str(_e).split('\n')[0][:70])

if have_db:
    import datetime as dt
    try:
        with transaction.atomic():
            prop = M.props.objects.create(
                prop_name='PC1 Flat', prop_country='Cyprus',
                prop_available_for_rent='Yes')
            base = dict(prop=prop, tenant_type='Individual',
                        tenant_current='Yes', tenant_rental_type='Monthly',
                        tenant_lease_start_date=dt.date(2026, 10, 1),
                        tenant_lease_end_date=dt.date(2027, 9, 30))
            t = M.tenant.objects.create(
                tenant_name='Chrystalla Example',
                tenant_contact_number='+35799000001',
                tenant_email='chrystalla@example.com',
                tenant_id_number='991960',
                tenant_2_name='Antigoni Example',
                tenant_2_contact_number='+35799000002',
                tenant_2_email='antigoni@example.com',
                tenant_2_id_number='895733', **base)

            ok('tenant_id_country' in TenantForm().fields
               and 'tenant_2_id_country' in TenantForm().fields,
               'the form carries both countries')

            u = User.objects.create_superuser(
                username='pc1check', email='pc1@example.com',
                password='not-a-real-password')
            c = Client(SERVER_NAME='localhost')
            c.force_login(u)

            body = c.get('/tenant_edit/%d' % t.pk).content.decode()
            ok('name="tenant_id_country"' in body
               and 'name="tenant_2_id_country"' in body
               and '<option value="Cyprus">Cyprus</option>' in body,
               'Tenant Edit renders both country selects')

            # THE SAVE - through the form the commit view uses.
            from django.forms.models import model_to_dict
            data = {k: ('' if v is None else v)
                    for k, v in model_to_dict(t).items()}
            data.update(tenant_id_country='Cyprus',
                        tenant_2_id_country='Greece', prop=prop.pk)
            f = TenantForm(data, instance=t)
            valid = f.is_valid()
            ok(valid, 'an edit with both countries is valid', f.errors)
            if valid:
                f.save()
            t.refresh_from_db()
            ok((t.tenant_id_country, t.tenant_2_id_country)
               == ('Cyprus', 'Greece'),
               '  and the record keeps them',
               (t.tenant_id_country, t.tenant_2_id_country))

            body = c.get('/tenant_report/%d' % t.pk).content.decode()
            ok('991960 <span class="alv-id-country">Cyprus</span>' in body
               and '895733 <span class="alv-id-country">Greece</span>'
               in body,
               'the Tenant report shows "991960 · Cyprus" and the second '
               'tenant\'s alike')

            from pages.views.tenants import duplicate_tenant_view
            from django.test import RequestFactory
            from django.contrib.messages.storage.fallback import \
                FallbackStorage
            rq = RequestFactory().post('/x/')
            rq.user = u
            setattr(rq, 'session', c.session)
            setattr(rq, '_messages', FallbackStorage(rq))
            before = set(M.tenant.objects.values_list('pk', flat=True))
            duplicate_tenant_view(rq, t.pk)
            new = M.tenant.objects.exclude(pk__in=before).first()
            ok(new is not None and (new.tenant_id_number,
                                    new.tenant_id_country,
                                    new.tenant_2_id_number,
                                    new.tenant_2_id_country) ==
               ('991960', 'Cyprus', '895733', 'Greece'),
               'Duplicate for Renewal carries both Passport/IDs and their '
               'countries', new and (new.tenant_id_number,
                                     new.tenant_id_country,
                                     new.tenant_2_id_number,
                                     new.tenant_2_id_country))

            # THE SAVE-BACK.
            prop2 = M.props.objects.create(
                prop_name='PC1 Flat 2', prop_country='Cyprus',
                prop_available_for_rent='Yes')
            blank = M.tenant.objects.create(
                tenant_name='Elisavet Example',
                tenant_email='elisavet@example.com',
                tenant_contact_number='+30694000000',
                **dict(base, prop=prop2))
            got = LT._save_identity_back(str(blank.pk), blank, {
                'existing_tenant_data': {'tenant_passport_id': '543900',
                                         'tenant_passport_country':
                                             'Greece'}})
            blank.refresh_from_db()
            ok((blank.tenant_id_number, blank.tenant_id_country)
               == ('543900', 'Greece'),
               'Generate fills a blank Passport/ID and country on the '
               'record', got)
            got = LT._save_identity_back(str(blank.pk), blank, {
                'existing_tenant_data': {'tenant_passport_id': 'OTHER',
                                         'tenant_passport_country':
                                             'Cyprus'}})
            blank.refresh_from_db()
            ok(got is None and blank.tenant_id_country == 'Greece'
               and blank.tenant_id_number == '543900',
               '  and never overwrites one - that is Edit Tenant\'s job')

            M.tenant.objects.filter(pk=t.pk).update(tenant_2_id_country='')
            t.refresh_from_db()
            LT._save_identity_back(str(t.pk), t, {
                'has_second_tenant': True,
                'second_tenant_data': {'tenant_name': 'Somebody Else',
                                       'tenant_passport_country':
                                           'Israel'}})
            t.refresh_from_db()
            ok(t.tenant_2_id_country == '',
               'a second person who is not the record\'s second tenant '
               'does not have their country pinned to that name')
            LT._save_identity_back(str(t.pk), t, {
                'has_second_tenant': True,
                'second_tenant_data': {'tenant_name': 'Antigoni Example',
                                       'tenant_passport_country':
                                           'Greece'}})
            t.refresh_from_db()
            ok(t.tenant_2_id_country == 'Greece',
               '  the record\'s own second tenant does')

            prop3 = M.props.objects.create(
                prop_name='PC1 Flat 3', prop_country='Cyprus',
                prop_available_for_rent='Yes')
            co = M.tenant.objects.create(
                tenant_name='Example Limited', tenant_type='Company',
                tenant_email='co@example.com',
                **{k: v for k, v in dict(base, prop=prop3).items()
                   if k != 'tenant_type'})
            ok(LT._save_identity_back(str(co.pk), co, {
                'existing_tenant_data': {'tenant_passport_id': '1',
                                         'tenant_passport_country':
                                             'Cyprus'}}) is None,
               'a company is never given a passport')
            ok(LT._save_identity_back('new_tenant', t, {}) is None,
               'nor a new tenant, who has no row')

            body = c.get('/generate-lease-agreement/').content.decode()
            ok(body.count('<option value="Greece">Greece</option>') >= 3,
               'Generate offers the one list in all three country boxes')
            raise Rollback()
    except Rollback:
        pass

# ==========================================================================
head('5. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("Text = 'def _save_identity_back('" in gate,
   '  with a sentinel on the save-back')
wd = read(J(ROOT, 'test_waiting_down.py'))
nm = re.search(r'CONVERTED_N = (\d+)', wd)
ok(nm and int(nm.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (nm.group(1) if nm else '?', len(T.CONVERTED)))
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')
nob = [os.path.relpath(p, ROOT) for p in EDITED
       if not os.path.isfile(p + SUFFIX)]
ok(not nob, '  every file it edited has its backup', ', '.join(nob))

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
