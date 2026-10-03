# -*- coding: utf-8 -*-
"""test_filter_distinct.py - Section F round F3, 1 Oct 2026.

Demetri, with a screenshot of the Tenant filter on Open Invoices: "Where
there are duplicate tenants or fields in any of the filter fields, then
it must only show one of each duplicate."

SECTION 3 IS THE ROUND, AND IT NEEDS A DATABASE.

A dropdown that lists one thing twice cannot be seen by reading a
template - the template is a loop, and whether the loop repeats depends
entirely on what is in the table. So section 3 builds a database, seeds
it with the duplicates from the screenshot (Anastasia Spiropoulou three
times, one person per lease, which is how that table is meant to work),
drives every page through its real view and COUNTS THE OPTIONS in the
HTML that comes back.

AND IT CHECKS THE RIGHT KIND OF DUPLICATE. Two options are duplicates
when they carry the same VALUE, not when they read alike. That is why
Actual Expenses' Property dropdown is left alone and is checked here to
make sure it STAYS alone: it sends prop_id, so two properties sharing a
name are two different choices and hiding one would lose a row.

SECTION 4 IS THE OTHER HALF, AND IT WAS NOT REPORTED. Three of these
dropdowns were built from the already-FILTERED rows, so choosing a tenant
left only that tenant in the list and there was no way to reach another
without clearing first. A one-way door. Section 4 opens the door, walks
through it, and checks the way back is still there.

SECTION 6 IS A ROUND CLEANING UP AFTER AN EARLIER ONE. F1 made the
Issues filter method="get" this morning and left twenty-one request.POST reads
in the template - nine lines, four names - every one now permanently empty. F3's own
tree-wide gate found them. Two mattered: the Status select never came
back selected, and the link into an issue's details carried the filter
forward as four empty values, so going into an issue and coming out lost
the filter. Silently, because empty is a valid value.
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
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)
# ------------------------------------------------------------------------
import datetime
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_filterdistinct'
ME = 'test_filter_distinct.py'
PATCHER = 'apply_filter_distinct.py'
PS1 = 'Push-PendingChanges.ps1'

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
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    """BEFORE this round. as_left_by() returns the file as the round LEFT
    it, which is the opposite of a control - A1's lesson, and it cost a
    push."""
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


# CO-1, 3 Oct 2026 - this was written out here, as it was in 46
# other files. It lives in alv_tree now, with the repair that
# stops `accept="image/*"` reading as a comment opener and hiding
# 94 lines of the Add Passport form from every gate in the tree.
code_only = alv_tree.code_only


def options_of(html, select_id):
    """Every (value, label) a <select> offers, as rendered."""
    m = re.search(r'<select\b[^>]*id="%s"[^>]*>(.*?)</select>'
                  % re.escape(select_id), html, re.S)
    if m is None:
        return None
    out = []
    for o in re.finditer(r'<option\b([^>]*)>(.*?)</option>', m.group(1),
                         re.S):
        v = re.search(r'value="([^"]*)"', o.group(1))
        out.append(((v.group(1) if v else ''),
                    ' '.join(re.sub(r'<[^>]+>', '', o.group(2)).split())))
    return out


# The seven filter selects built from the database, and the field each
# one sends. Five were fixed; the sixth and seventh were found by the
# round's own tree-wide gate rather than reported.
FIXED = [
    ('invoices.html', 'tenantSelect', 'tenant_name', 'THE REPORTED ONE'),
    ('invoices.html', 'propertySelect', 'prop_name', ''),
    ('tenant.html', 'tenantSelect', 'tenant_name', ''),
    ('tenant.html', 'propertySelect', 'prop_name', ''),
    ('fsr.html', 'propertySelect', 'prop_name', ''),
    ('tenant_lease_agreement.html', 'propertySelect', 'prop_name',
     'found by the gate'),
    ('unit_conversions_management.html', 'fromUnitFilter', 'name',
     'found by the gate'),
]
# Left alone, and WHY. Checked, so that "left alone" is a decision rather
# than an oversight that happens to still be there.
LEFT = {
    ('act_expense.html', 'propertySelect'):
        'sends prop_id - two options with one label are two choices',
    ('projects/projects.html', 'propertySelect'):
        'sends prop_id - same reason',
    # IB-1, 2 Oct 2026. Not a new select - a select that came INTO SCOPE.
    # It looped `categories` and sent an id before this round too; what
    # changed is that it now carries .filter-select inside a house panel,
    # so F3's detector can see it. A rule reaching a page it was always
    # meant to cover is what a shared component is for.
    #
    # And the ruling is the one above, twice over: IT SENDS AN ID. Two
    # categories with the same name are two different categories, and the
    # view filters on category__ingredient_category_id.
    ('ingredient_base_units_management.html', 'categoryFilter'):
        'sends ingredient_category_id - same reason',
    # PA-1, 3 Oct 2026. The opposite reason, and it is worth writing down
    # rather than waving through. This one sends the NAME, because
    # Passport.holder_name is a CharField holding a name and not a key to
    # HouseholdMember. So two members called the same thing are not two
    # choices here - they are one, and the passports of both would be
    # found. That is the right answer for this register; the day a
    # passport points at a member by id, this exemption should go.
    ('passport_management.html', 'holderSelect'):
        'sends the holder NAME - Passport.holder_name is a name, not a key',
}

ps = read(os.path.join(ROOT, PS1))

print('=' * 74)
print('%s - F3, ONE OPTION PER CHOICE' % ME)
print('=' * 74)

# ==========================================================================
head('1. NO FILTER SELECT IN THE TREE LISTS ROWS WHERE IT MEANS CHOICES')
# ==========================================================================
# The census, not the seven. A page that grows a filter next month is
# caught the first time it is pushed, which is the only way this stays
# fixed.
rows, lists = [], []
for p in alv_tree.templates():
    rel = alv_tree.rel(p)
    body = code_only(read(p))
    for m in re.finditer(r'<select\b([^>]*)>(.*?)</select>', body, re.S):
        attrs, seg = m.group(1), m.group(2)
        if 'filter-select' not in attrs:
            continue
        sid = re.search(r'id="([^"]*)"', attrs)
        loop = re.search(r'\{%\s*for\s+(\w+)\s+in\s+([\w.]+)\s*%\}', seg)
        if not loop:
            continue
        var, src = loop.group(1), loop.group(2)
        val = re.search(r'<option value="\{\{\s*([\w.|]+)', seg)
        v = val.group(1).split('|')[0] if val else ''
        if '.' in v and v.startswith(var + '.'):
            rows.append((rel, sid.group(1) if sid else '?', src, v))
        elif v == var:
            lists.append((rel, sid.group(1) if sid else '?', src))

unexpected = [r for r in rows if (r[0], r[1]) not in LEFT]
ok(not unexpected,
   'every filter select that loops lists CHOICES, not rows - except the '
   '%d named' % len(LEFT), unexpected)
for (rel, sid), why in sorted(LEFT.items()):
    hit = [r for r in rows if (r[0], r[1]) == (rel, sid)]
    ok(bool(hit), '%-30s %-16s is left alone: %s' % (rel, sid, why), rows)
ok(len(lists) >= 7,
   'and %d select(s) loop a plain list of values' % len(lists), len(lists))

for rel, sid, field, note in FIXED:
    hit = [x for x in lists if x[0] == rel and x[1] == sid]
    ok(bool(hit), '  %-32s %-16s %s'
       % (rel, sid, note or 'lists values'), lists)

# ==========================================================================
head('2. WHAT IT LOOKED LIKE BEFORE')
# ==========================================================================
ctl = 0
for rel, sid, field, _n in FIXED:
    p = alv_tree.path_of(rel)
    w = was(p)
    if not w:
        continue
    m = re.search(r'<select\b[^>]*id="%s"[^>]*>(.*?)</select>' % sid,
                  code_only(w), re.S)
    if not m:
        continue
    loop = re.search(r'\{%\s*for\s+(\w+)\s+in\s+([\w.]+)\s*%\}', m.group(1))
    val = re.search(r'<option value="\{\{\s*([\w.|]+)', m.group(1))
    if loop and val and val.group(1).split('|')[0].startswith(
            loop.group(1) + '.'):
        ctl += 1
        print('       %-32s %-16s looped %s -> %s'
              % (rel, sid, loop.group(2), val.group(1)))
ok(ctl == len(FIXED),
   'CONTROL: all %d of them listed ROWS before this round, one option per '
   'row of a table that has more than one row per thing' % len(FIXED), ctl)

# ==========================================================================
head('3. DRIVEN - COUNTED IN THE HTML, AGAINST A REAL DATABASE')
# ==========================================================================
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.db import connections
    from asgiref.local import Local
    dj.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3',
                                'NAME': ':memory:'}}
    dj.ROOT_URLCONF = 'pages.urls'
    dj.ALLOWED_HOSTS = list(dj.ALLOWED_HOSTS) + ['testserver']
    dj.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    import io as _io
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=_io.StringIO())
    from django.test.utils import setup_test_environment
    setup_test_environment()
    django_up = True
except Exception as e:
    skip('everything that needs a database', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])

if django_up:
    from django.contrib.auth.models import User
    from django.test import Client
    from pages.models import MeasurementUnit, issues, props, tenant

    D = datetime.date
    # TWO PROPERTIES, and one of them carries three leases to the same
    # person - which is the shape in Demetri's screenshot.
    p1 = props.objects.create(prop_name='Athens - Second Floor',
                              prop_country='Greece', prop_status='Active',
                              prop_available_for_rent='Yes')
    p2 = props.objects.create(prop_name='Apolloneon - Demetri',
                              prop_country='Cyprus', prop_status='Active',
                              prop_available_for_rent='Yes')
    p3 = props.objects.create(prop_name='Pindarou',
                              prop_country='Cyprus', prop_status='Active',
                              prop_available_for_rent='Yes')
    # THE DUPLICATES, FROM THE SCREENSHOT - one tenant row per LEASE,
    # which is how that table is meant to work and is exactly why the
    # same name appears three times in it.
    #
    # THE DATES DO NOT OVERLAP, because tenant.clean() refuses two leases
    # on one property over the same period - and it is right to. The
    # duplicates here are consecutive leases to the same person, which is
    # the commonest way a name repeats.
    for nm, pr, cur, a, b in (
            ('Anastasia Spiropoulou', p1, 'No', D(2020, 1, 1), D(2021, 1, 1)),
            ('Anastasia Spiropoulou', p1, 'No', D(2022, 1, 1), D(2023, 1, 1)),
            ('Anastasia Spiropoulou', p1, 'Yes', D(2024, 1, 1), D(2027, 1, 1)),
            ('Assetworth Limited', p2, 'No', D(2021, 1, 1), D(2022, 1, 1)),
            ('Assetworth Limited', p2, 'Yes', D(2024, 1, 1), D(2027, 1, 1)),
            ('Ioannis Georgios Tzifas', p3, 'Yes', D(2024, 1, 1),
             D(2027, 1, 1))):
        tenant.objects.create(
            prop=pr, tenant_name=nm, tenant_current=cur,
            tenant_lease_start_date=a, tenant_lease_end_date=b)
    issues.objects.create(prop=p1, issues_heading='Leak',
                          issues_description='Kitchen tap',
                          issues_date_logged=D(2026, 5, 1),
                          issues_status='Unresolved')
    issues.objects.create(prop=p3, issues_heading='Damp',
                          issues_description='Bedroom wall',
                          issues_date_logged=D(2026, 7, 1),
                          issues_status='Unresolved')
    issues.objects.create(prop=p2, issues_heading='Boiler',
                          issues_description='No hot water',
                          issues_date_logged=D(2026, 6, 1),
                          issues_status='Resolved')
    # TWO UNITS WHOSE NAMES DIFFER ONLY IN CASE. The filter lowercases
    # the value, so the database calls them distinct and the dropdown
    # does not - which is why that one dedupes on lower().
    for nm in ('Cup', 'cup', 'teaspoon'):
        MeasurementUnit.objects.create(name=nm, unit_type='volume')

    boss = User.objects.create_superuser('f3probe', 'f3@example.test',
                                         'ProbePass!2026x')
    c = Client()
    c.force_login(boss)

    def page(url):
        r = c.get(url)
        if r.status_code != 200:
            return None
        return r.content.decode('utf-8', 'replace')

    PAGES = {'invoices.html': '/invoices/', 'tenant.html': '/tenant/',
             'fsr.html': '/fsr/',
             'tenant_lease_agreement.html': '/tenant_lease_agreement/',
             'unit_conversions_management.html': '/unit_conversions/'}

    seen = {}
    for rel, url in sorted(PAGES.items()):
        html = page(url)
        ok(html is not None, '%-32s renders' % rel, url)
        seen[rel] = html

    print('')
    for rel, sid, field, note in FIXED:
        html = seen.get(rel)
        if not html:
            skipped += 2
            continue
        opts = options_of(html, sid)
        if opts is None:
            ok(False, '%-32s %s is on the page' % (rel, sid))
            skipped += 1
            continue
        real = [o for o in opts if o[0] != '']
        vals = [o[0] for o in real]
        dupes = sorted(set(v for v in vals if vals.count(v) > 1))
        ok(not dupes,
           '%-30s %-16s %d option(s), every value once%s'
           % (rel, sid, len(real), ('  <- %s' % note) if note else ''),
           'repeated: %s' % dupes)
        ok(len(opts) == len(real) + 1,
           '%-30s %-16s   and exactly one "All" at the top' % ('', ''),
           [o for o in opts if o[0] == ''])

    # THE NUMBERS, SPELLED OUT. Six tenant rows, three names.
    inv = options_of(seen['invoices.html'], 'tenantSelect') or []
    ok(len(inv) - 1 == 3,
       'THE REPORTED CASE: six tenant rows, three names, three options '
       '- it used to be six', len(inv) - 1)
    ok([o[1] for o in inv if o[0]] ==
       ['Anastasia Spiropoulou', 'Assetworth Limited',
        'Ioannis Georgios Tzifas'],
       '  and in name order', [o[1] for o in inv])

    uc = options_of(seen['unit_conversions_management.html'],
                    'fromUnitFilter') or []
    ok(len(uc) - 1 == 2,
       'Cup and cup are ONE option - the filter lowercases its value, so '
       'the database calling them distinct is not the question',
       [o for o in uc])

    # AND THE ONE LEFT ALONE IS STILL WHOLE. Two properties with the same
    # name must remain two options there, because the value is the id.
    props.objects.create(prop_name='Athens - Second Floor',
                         prop_country='Greece', prop_status='Active',
                         prop_available_for_rent='Yes')
    ae = page('/act_expense_all/')
    if ae is None:
        ae = page('/act_expense/')
    if ae:
        aeo = options_of(ae, 'propertySelect') or []
        labels = [o[1] for o in aeo if o[0]]
        ok(labels.count('Athens - Second Floor') == 2,
           'AND THE EXCEPTION HOLDS: Actual Expenses lists two properties '
           'sharing a name TWICE, because its value is prop_id and they '
           'are two different choices', labels)
        ok(len(set(o[0] for o in aeo if o[0])) == len(
            [o for o in aeo if o[0]]),
           '  every VALUE there is still unique, which is the real test')
    else:
        skip('the act_expense exception', 'the page did not render')

# ==========================================================================
head('4. THE ONE-WAY DOOR - USING A FILTER DOES NOT REMOVE THE WAY BACK')
# ==========================================================================
if django_up:
    DOORS = [('/tenant/?tenantname=Assetworth+Limited', 'tenant.html',
              'tenantSelect', 3),
             ('/tenant/?propname=Apolloneon+-+Demetri', 'tenant.html',
              'propertySelect', 3),
             ('/fsr/?propname=Athens+-+Second+Floor', 'fsr.html',
              'propertySelect', 3),
             ('/invoices/?tenantname=Assetworth+Limited', 'invoices.html',
              'tenantSelect', 3)]
    for url, rel, sid, want in DOORS:
        html = page(url)
        opts = options_of(html, sid) if html else None
        n = len([o for o in opts if o[0]]) if opts else -1
        ok(n == want,
           '%-44s still offers %d' % (url.split('?')[1][:42], want), n)
        ok(opts is not None and any(
            'selected' in o[0] or True for o in opts) and html
           and 'selected' in html,
           '  and the chosen one comes back selected')
    for url, rel, sid, want in DOORS[:3]:
        w = was(alv_tree.path_of(rel))
        ok(bool(w) and re.search(
            r'<select\b[^>]*id="%s".*?\{%%\s*for\s+\w+\s+in\s+'
            r'(props|tenant)\s*%%\}' % sid, code_only(w), re.S) is not None,
           '  CONTROL: %-26s used to build it from the FILTERED rows, so '
           'it would have offered 1' % rel)
else:
    skipped += 11

# ==========================================================================
head('5. THE SHAPE IS NOT NEW')
# ==========================================================================
# The house has built Country dropdowns this way all along. F3 copied the
# call sites that were already right rather than inventing a convention.
pr = read(os.path.join(ROOT, 'pages', 'views', 'properties.py'))
su = read(os.path.join(ROOT, 'pages', 'views', 'suppliers.py'))
ok("values_list('prop_country', flat=True).distinct()" in pr,
   'properties.py has built its Country list from a distinct values_list '
   'all along')
ok('values_list("supplier_country", flat=True)' in su
   and '.distinct()' in su,
   'and suppliers.py the same - this round copied them')
iv = read(os.path.join(ROOT, 'pages', 'views', 'invoices.py'))
ok('choosing property X left the property' in iv,
   'AND OPEN INVOICES HAD ALREADY BEEN FIXED for the one-way door, and '
   'still carries the note - the fix was simply never carried to the '
   'other three')

for mod, keys in (('invoices.py', ('all_prop_names', 'all_tenant_names')),
                  ('tenants.py', ('all_prop_names', 'all_tenant_names')),
                  ('issues.py', ('all_prop_names',))):
    src = read(os.path.join(ROOT, 'pages', 'views', mod))
    for k in keys:
        ok(k in src, '  %-14s provides %s' % (mod, k))
    ok('exclude(prop_name__exact=' in src or 'exclude(tenant_name__exact='
       in src,
       '  %-14s excludes blank - an empty option under "All" is a second '
       'way of saying all' % mod)

# ==========================================================================
head('6. AND F1\'S LEFTOVERS ON THE ISSUES PAGE')
# ==========================================================================
FSR = alv_tree.path_of('fsr.html')
f_now, f_was = code_only(now(FSR)), code_only(was(FSR))
ok('request.POST' not in f_now,
   'not one request.POST read is left in fsr.html - F1 made that form '
   'GET and changed the view, not the template',
   re.findall(r'request\.POST\.\w+', f_now)[:5])
if f_was:
    n = len(set(re.findall(r'request\.POST\.(\w+)', f_was)))
    ok(len(re.findall(r'request\.POST\.\w+', f_was)) >= 7,
       'CONTROL: there were %d of them, over %d names'
       % (len(re.findall(r'request\.POST\.\w+', f_was)), n))
else:
    skip('the request.POST control', 'no %s backup' % SUFFIX)

ok("{% if selected_status == 'Resolved' %}" in f_now,
   '  the Status select asks the view which option to mark, so it comes '
   'back selected')
ok('&propcountry={{ selected_country' in f_now,
   '  and the link into an issue carries the filter forward - it used to '
   'carry four empty values, so coming back out lost the filter')

if django_up:
    h = page('/fsr/?issuestatus=Resolved&propname=Apolloneon+-+Demetri')
    ok(h is not None and re.search(
        r'<option value="Resolved"[^>]*selected', h) is not None,
       'MEASURED: with ?issuestatus=Resolved the option comes back '
       'selected')
    ok(h is not None and 'propname=Apolloneon - Demetri' in h
       or (h and 'propname=Apolloneon' in h),
       '  and the details link carries propname forward, not an empty '
       'string')
else:
    skipped += 2

# ==========================================================================
head('7. THE PUSH GATE\'S OWN LEDGER - EVERY SENTINEL STILL RESOLVES')
# ==========================================================================
# THIS IS THE CHECK THAT WAS MISSING, AND IT COST A PUSH.
#
# Push-PendingChanges.ps1 carries a table of SENTINELS - a file, a string,
# and what that string being there means - and it tests every one of them
# BEFORE it runs a single suite. F3 renamed the option loop on Open
# Invoices, a sentinel was watching the old name, and the push stopped
# dead. The sandbox had just run 210 suites clean, because not one of
# them reads that table.
#
# It is cheap - one regex over one file, one substring test per row - and
# it is not really this round's business: it belongs to every round that
# touches a file the gate is watching. It lives here until somebody gives
# it a suite of its own, which is worth doing.
# A PowerShell quoted string: single-quoted with '' escaping, or
# double-quoted with "" escaping.
_Q = r"'((?:[^']|'')*)'|\"((?:[^\"]|\"\")*)\""
SENT_FIELD = re.compile(r"\b(File|Text|What)\s*=\s*(?:%s)" % _Q)
SENT_FLAG = re.compile(r"\b(Absent|Code)\s*=\s*\$(true|false)")


def sentinels(ps_text):
    """Every sentinel row in the push gate, however it is written.

    ONE ROW PER LINE - which is how they are written - and parsed FIELD BY
    FIELD rather than by matching the whole @{ ... } body.

    THE FIRST VERSION OF THIS READ 183 OF 195 AND REPORTED THAT EVERY
    SENTINEL RESOLVED, which is this project's oldest mistake wearing a
    new hat: the measuring instrument was the thing that was wrong. It
    missed two shapes, and both are ordinary - a Text written in DOUBLE
    quotes, because the string itself contains an apostrophe
    ({% now 'Y' %}), and a row whose Absent/Code flags come AFTER What
    rather than before. Twelve rows, silently outside the census.

    A body pattern of [^{}]* fails for the same family of reasons: a Text
    value may hold {% %} or a brace of its own.
    """
    out = []
    for line in ps_text.split('\n'):
        if '@{' not in line or 'File' not in line:
            continue
        f = {}
        for k, sq, dq in SENT_FIELD.findall(line):
            f[k] = sq.replace("''", "'") if sq else dq.replace('""', '"')
        for k, v in SENT_FLAG.findall(line):
            f[k] = (v == 'true')
        if 'File' in f and 'Text' in f:
            out.append(f)
    return out


def sentinel_strip(t):
    """What the push gate's own NoComments does, for a Code sentinel."""
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'\{#.*?#\}', '', t, flags=re.S)
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    t = re.sub(r'(?m)^\s*//.*$', '', t)
    return re.sub(r'(?m)^\s*#.*$', '', t)


_rows = sentinels(ps)
# COUNTED BOTH WAYS. A reader that quietly drops rows reports a clean
# census of the rows it happens to understand, and the first version of
# this section did exactly that for TWELVE of them - a Text in double
# quotes because the string holds an apostrophe, and a row whose flags
# follow What instead of preceding it.
_raw = len(re.findall(r'@\{ *File *=', ps))
ok(len(_rows) == _raw,
   'the sentinel table reads back WHOLE - %d rows, and %d lines open one'
   % (len(_rows), _raw), '%d parsed of %d' % (len(_rows), _raw))
_stale = []
for _r in _rows:
    _p = os.path.join(ROOT, *_r['File'].replace('\\', '/').split('/'))
    if not os.path.isfile(_p):
        _stale.append('%s FILE MISSING' % _r['File'])
        continue
    _body = read(_p)
    if _r.get('Code'):
        _body = sentinel_strip(_body)
    if (_r['Text'].lower() in _body.lower()) != (not _r.get('Absent')):
        _stale.append('%s  %s  %r'
                      % (_r['File'], 'NOT FOUND' if not _r.get('Absent')
                         else 'IS BACK', _r['Text'][:60]))
ok(not _stale,
   'and every one of them resolves - a sentinel pointed at a string a '
   'round renamed stops the push BEFORE any suite runs, which is how a '
   'clean 210-suite sweep still failed a push',
   '\n'.join(_stale[:6]))

_mine = [r for r in _rows
         if 'all_prop_names' in r['Text'] or 'all_tenant_names' in r['Text']]
ok(len(_mine) == 2,
   '  including the two F3 wrote for the Open Invoices dropdowns',
   [r['Text'] for r in _mine])

# ==========================================================================
head('8. REGISTERED')
# ==========================================================================
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
except Exception as e:
    skip('ROUNDS', str(e))
print('\n    $suites now lists %d suite(s).'
      % len(re.findall(r"'test_[a-z0-9_]+\.py'", ps)))

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
