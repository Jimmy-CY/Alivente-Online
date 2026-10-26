# -*- coding: utf-8 -*-
"""test_tenant_identity.py - round TI-1, 26 Oct 2026.

IDENTITY NUMBERS ON THE TENANT - AND THE SCREENS LAID OUT AS HE DREW THEM.

His decisions of 26 October, after two rounds of renders:
    - Company Reg Number (for a Company) and a Passport/ID for each
      Individual tenant, both people alike; all optional.
    - Add/Edit Tenant, Individual: Type | Status on the first line; Tenant
      Name | Tenant Passport/ID | Number | Email on the second - "just
      like the second tenant". Company: Type | Name | Status over Reg
      Number | Contact Person | Number | Email ("OK").
    - Report, Individual: Type ABOVE the sections; Tenant Information is
      Name, Passport/ID, Contact Number, Email, exactly like Second Tenant.
      Company report unchanged in shape ("perfect"). The property page's
      tenant panel the same.
    - Generate Lease Agreement fills the numbers in from the record.
    - "Tenant Passport/ID" and "Second Tenant Passport/ID" - his labels.
    - The Tenant Name hint follows the type: "Full name" / "Company name".
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
import shutil
import sys
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_tenantid'
ME = 'test_tenant_identity.py'
PATCHER = 'apply_tenant_identity.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'TI-1, 26 Oct 2026'

J = os.path.join
TPL = J(ROOT, 'pages', 'templates')
MODELS = J(ROOT, 'pages', 'models.py')
FORMS = J(ROOT, 'pages', 'forms.py')
PROPS_V = J(ROOT, 'pages', 'views', 'properties.py')
ADD_T = J(TPL, 'tenant_add.html')
EDIT_T = J(TPL, 'tenant_edit.html')
REPORT_T = J(TPL, 'tenant_report.html')
PROP_T = J(TPL, 'property_detail.html')
GEN_T = J(TPL, 'generate_lease_agreement.html')
HELP_O = J(ROOT, 'pages', 'help_content', 'operational.html')
MIG = J(ROOT, 'pages', 'migrations', '0109_ti1_identity_numbers.py')
GATE = J(ROOT, PS1)
EDITED = (MODELS, FORMS, PROPS_V, ADD_T, EDIT_T, REPORT_T, PROP_T, GEN_T,
          HELP_O)

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

NOW = dict((p, read(p)) for p in EDITED)
OLD = dict((p, was(p)) for p in EDITED)


def between(s, a, b):
    i = s.find(a)
    j = s.find(b, i + 1) if i >= 0 else -1
    return s[i:j] if i >= 0 and j > i else ''


def claims(src):
    m = T.python_code_only(src[MODELS])
    f = T.python_code_only(src[FORMS])
    pv = T.python_code_only(src[PROPS_V])
    add = T.code_only(src[ADD_T])
    edt = T.code_only(src[EDIT_T])
    rep = T.code_only(src[REPORT_T])
    prp = T.code_only(src[PROP_T])
    gen = src[GEN_T]
    out = [
        (all(('%s = models.CharField(max_length=50, blank=True)' % c) in m
             for c in ('tenant_company_reg_no', 'tenant_id_number',
                       'tenant_2_id_number')),
         'the tenant carries the three identity numbers, all optional'),
        ("'tenant_company_reg_no', 'tenant_id_number', 'tenant_2_id_number'"
         in f,
         '  and the form saves them - a column missing from fields is '
         'dropped without a word (T2-1)'),
    ]
    for name, s in (('Add', add), ('Edit', edt)):
        out.append((
            'id="ti-grid"' in s and 'is-individual' in s and 'is-company' in s
            and '<strong>Tenant Passport/ID</strong>' in s
            and '<strong>Second Tenant Passport/ID</strong>' in s
            and '<strong>Company Reg Number</strong>' in s
            and "grid.classList.toggle('is-company', company)" in s
            and "'Full name'" in s and "'Company name'" in s,
            '%s Tenant lays the fields out by type, with his labels' % name))
    out += [
        ('ti-type-row' in rep
         and 'Passport/ID:</span>' in rep
         and '{{ tenant.tenant_2_id_number|default:' in rep
         and 'Company Reg No:</span>' in rep,
         'the Tenant Details Report: Type above, a block per person, the '
         'Company Reg No for a company'),
        ('ti-type-row' in prp
         and '{{ active_tenant.tenant_id_number|default:' in prp
         and '{{ active_tenant.tenant_company_reg_no|default:' in prp,
         '  and the property page tenant panel the same'),
        ("'tenant_id_number': tenant_obj.tenant_id_number or ''" in pv
         and "tenantData.tenant_id_number || ''" in gen
         and "tenantData.tenant_2_id_number || ''" in gen
         and "tenantData.tenant_company_reg_no || ''" in gen,
         'Generate Lease Agreement fills the numbers in from the record'),
        ('<strong>Identity Numbers</strong>' in src[HELP_O],
         'the Tenants help describes them'),
    ]
    return out


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
missing = [os.path.relpath(p, ROOT) for p in EDITED if MARK not in NOW[p]]
ok(not missing, 'the round dates itself in every file it touched',
   ', '.join(missing))
mig = read(MIG) if os.path.isfile(MIG) else ''
ok('("pages", "0108_es7_house_marks")' in mig
   and mig.count('migrations.AddField(') == 3
   and 'RunPython' not in mig and 'RemoveField' not in mig,
   'migration 0109 adds three columns after 0108 and touches no data')

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backups')
# ==========================================================================
held = [m for c, m in claims(OLD) if c]
ok(not held, 'CONTROL: not one of this round claims held before it',
   '\n'.join(held))

# ==========================================================================
head('3. DRIVEN - saved, shown, handed to Generate')
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
    import json
    from django.contrib.auth.models import User
    from django.db import connection, transaction
    from django.test import Client
    import pages.models as M
    from pages.forms import TenantForm
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
        M.tenant.objects.filter(tenant_id_number='').exists()
        have_db = True
    except Exception as _e:                                   # noqa: BLE001
        skip('section 3', 'no database, or 0109 not applied: %s'
             % str(_e).split('\n')[0][:70])

PAGES = {}
if have_db:
    try:
        with transaction.atomic():
            boss = User.objects.create_superuser(
                'ti1boss', 'ti1.boss@example.com', 'not-a-real-password')
            c = Client(SERVER_NAME='localhost')
            c.force_login(boss)

            def prop(n):
                return M.props.objects.create(prop_name='TI-1 Flat %s' % n,
                                              prop_country='Cyprus')

            base = dict(tenant_lease_start_date='2026-12-01',
                        tenant_lease_end_date='2027-11-30',
                        tenant_rental_type='Monthly', tenant_deposit=500,
                        tenant_rent=500, tenant_levies=20,
                        tenant_payment_terms=0, tenant_renewal='Yes',
                        tenant_renewal_period=60, tenant_current='Yes')
            f = TenantForm(dict(base, prop=prop(1).pk,
                                tenant_type='Individual',
                                tenant_name='Eleni Test',
                                tenant_contact_number='+35799000001',
                                tenant_email='eleni.ti1@example.com',
                                tenant_id_number='K 123456',
                                tenant_2_name='Marios Test',
                                tenant_2_contact_number='+35799000002',
                                tenant_2_email='marios.ti1@example.com',
                                tenant_2_id_number='M 654321'))
            ok(f.is_valid(), 'a joint tenancy with both Passport/IDs is a '
               'valid form', f.errors.as_text()[:200])
            joint = f.save() if f.is_valid() else None
            ok(joint is not None and joint.tenant_id_number == 'K 123456'
               and joint.tenant_2_id_number == 'M 654321',
               '  and both numbers are SAVED, read back from the row')
            f = TenantForm(dict(base, prop=prop(2).pk,
                                tenant_type='Individual',
                                tenant_name='Andreas Test',
                                tenant_contact_number='+35799000003',
                                tenant_email='andreas.ti1@example.com'))
            single = f.save() if f.is_valid() else None
            ok(single is not None and single.tenant_id_number == '',
               'and they are OPTIONAL - a tenant with none saves',
               f.errors.as_text()[:200])
            f = TenantForm(dict(base, prop=prop(3).pk, tenant_type='Company',
                                tenant_name='Ti1 Holdings Limited',
                                tenant_contact_person='Nikos Test',
                                tenant_contact_number='+35722000000',
                                tenant_email='office.ti1@example.com',
                                tenant_company_reg_no='HE 999001'))
            co = f.save() if f.is_valid() else None
            ok(co is not None and co.tenant_company_reg_no == 'HE 999001',
               'a company saves its Reg Number', f.errors.as_text()[:200])

            if joint and single and co:
                def report(t):
                    r = c.get('/tenant_report/%d' % t.pk)
                    return r.status_code, r.content.decode('utf-8', 'replace')
                st, pj = report(joint)
                ok(st == 200 and 'K 123456' in pj and 'M 654321' in pj
                   and 'class="detail-row ti-type-row"' in pj
                   and 'Second Tenant' in pj
                   and 'Contact Information' not in pj,
                   'the joint report: both Passport/IDs, Type above, no '
                   'separate Contact Information', st)
                st, ps = report(single)
                ok(st == 200 and 'Second Tenant' not in ps
                   and 'Passport/ID:</span>' in ps and '&mdash;' in ps,
                   '  the single report: one block, a blank number shown '
                   'as a dash', st)
                st, pc = report(co)
                ok(st == 200 and 'HE 999001' in pc
                   and 'Contact Information' in pc
                   and 'Passport/ID:</span>' not in pc
                   and 'class="detail-row ti-type-row"' not in pc,
                   '  the company report keeps its shape, with the Reg No', st)
                r = c.post('/get-property-tenant-data/',
                           json.dumps({'property_id': joint.prop_id,
                                       'tenant_id': joint.pk}),
                           content_type='application/json')
                d = (r.json() or {}).get('tenant', {}) if r.status_code == 200 \
                    else {}
                ok(d.get('tenant_id_number') == 'K 123456'
                   and d.get('tenant_2_id_number') == 'M 654321',
                   'Generate is handed both numbers, so it can fill them in',
                   r.status_code)
                PAGES['edit_ind'] = c.get('/tenant_edit/%d' % joint.pk
                                          ).content.decode('utf-8', 'replace')
                PAGES['edit_co'] = c.get('/tenant_edit/%d' % co.pk
                                         ).content.decode('utf-8', 'replace')
                ok('is-individual' in PAGES['edit_ind']
                   and 'value="K 123456"' in PAGES['edit_ind']
                   and 'value="M 654321"' in PAGES['edit_ind'],
                   'Edit Tenant opens an Individual in its own layout, with '
                   'both numbers filled')
                ok('is-company' in PAGES['edit_co']
                   and 'value="HE 999001"' in PAGES['edit_co'],
                   '  and a Company in the company layout')
            raise Rollback
    except Rollback:
        pass

# ==========================================================================
head('4. MEASURED - the layout he drew, at 1280')
# ==========================================================================
BOOT = J(ROOT, 'test_fixture_bootstrap413.css')
try:
    from playwright.sync_api import sync_playwright
    import alv_offline                 # noqa: F401 - renders stay offline
except ImportError:
    sync_playwright = None
if not PAGES or sync_playwright is None or not os.path.isfile(BOOT):
    skip('section 4', 'no browser, fixture or rendered pages')
else:
    boot = read(BOOT)

    def offline(html):
        html = re.sub(r'<link[^>]+bootstrap[^>]*>', '<style>%s</style>'
                      % boot.replace('\\', '\\\\'), html, count=1)
        return re.sub(r'<script[^>]*src="https?://[^"]*"[^>]*></script>',
                      '', html)

    TOPS = """() => {
        const t = id => Math.round(document.getElementById(id)
                                   .getBoundingClientRect().top);
        const v = id => getComputedStyle(document.getElementById(id)
                        .closest('.col-12')).display !== 'none';
        return {type: t('tenant_type'), status: t('tenant_current'),
                name: t('tenant_name'), id: t('tenant_id_number'),
                num: t('tenant_contact_number'), email: t('tenant_email'),
                reg: v('tenant_company_reg_no'), idshown: v('tenant_id_number'),
                person: v('tenant_contact_person')};
    }"""
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        try:
            def measure(html):
                ctx = br.new_context(viewport={'width': 1280, 'height': 900})
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                pg.set_content(offline(html), wait_until='load')
                try:
                    return pg.evaluate(TOPS)
                finally:
                    ctx.close()
            g = measure(PAGES['edit_ind'])
            ok(g['type'] == g['status'] and g['name'] > g['type'],
               'Individual: Type and Status share the FIRST line, and the '
               'name is below them', g)
            ok(g['name'] == g['id'] == g['num'] == g['email'],
               '  and Name, Passport/ID, Number and Email are ONE line - '
               'like the second tenant', g)
            ok(g['idshown'] and not g['reg'] and not g['person'],
               '  with no Reg Number and no Contact Person', g)
            g = measure(PAGES['edit_co'])
            ok(g['type'] == g['name'] == g['status'],
               'Company: Type, Name and Status on the first line', g)
            ok(g['reg'] and g['person'] and not g['idshown'],
               '  Reg Number and Contact Person shown, no Passport/ID', g)
        finally:
            br.close()

# ==========================================================================
head('5. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("File = 'pages/forms.py'; Text = 'tenant_2_id_number'" in gate,
   '  with a sentinel on the form fields')
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
