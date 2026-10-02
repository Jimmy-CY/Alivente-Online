# -*- coding: utf-8 -*-
"""TN-1, PART 2 - ONE ROOT CAUSE, THREE SYMPTOMS IN test_filter_get.py

The 222-suite sweep for DB-8 and TN-1 came back with one failure:

    RC=1  test_filter_get.py                              114 passed, 6 failed

Six FAILs, all on tenant.html, and all of them TN-1's doing. They are
CORRECT failures - the suite is asserting the behaviour TN-1 deliberately
changed - but they come from ONE fact, and the third one is worth writing
down because it is not what it looks like.

==========================================================================
THE ONE FACT
==========================================================================
test_filter_get.py builds its own rows:

    TenantModel.objects.create(tenant_name='Alpha Tenant', prop=a)
    TenantModel.objects.create(tenant_name='Beta Tenant', prop=b)

`tenant_current` is a blank CharField with no default, so both rows carry
the empty string. TN-1 narrows to tenant_current='Yes' when nothing is
asked for. Both rows vanish.

    3a  "/tenant/ shows both rows unfiltered"        0, not 2

and the two beside it, because they count the same rows.

==========================================================================
AND THE THIRD, WHICH IS NOT THE SAME THING
==========================================================================
    3c  "tenant.html differs ONLY by the method and the token line"
            ['<option value="Alpha Tenant" ...', '<option value="Beta ...']
        "and is exactly one line shorter - the token"      47 -> 48

Section 3c renders the page twice - once against the .bak_filterget
templates, once against the live ones - and diffs the filter panel. The
SAME view, the SAME database, both times. So a difference in the OPTIONS
cannot have come from the view.

It came from the templates:

    before   {% for tresults in tenant %}            the FILTERED rows
    after    {% for name in all_tenant_names %}      the WHOLE table

F3 moved that loop on 1 Oct for its own reason - a dropdown must keep the
way back out of the filter it is offering. So the OLD template lists the
rows that survived the filter, and TN-1's filter leaves none of them. The
old panel lost both options, the new one kept them, and a diff that should
have been one line SHORTER came out one line longer.

TWO ROUNDS A DAY APART, AGREEING ONLY BY ACCIDENT UNTIL ONE OF THEM MOVED.
F3's change is the reason the live page is still right, and the reason the
before/after diff went red.

Give the fixture rows the status they were always meant to have and all six
go green - because then the filtered set and the whole table are the same
two rows, and neither loop can tell them apart.

==========================================================================
WHAT THIS ROUND DOES NOT DO, DELIBERATELY
==========================================================================
Surveying the fix turned up a THREE-WAY SPLIT that is older than TN-1 and
is nobody's bug yet:

    tenant_lease_agreement    tenant_current='Yes'          exact
    tenant_page  (TN-1)       tenant_current='Yes'          exact
    tenant_payment_days_view  tenant_current__iexact='Yes'  case-insensitive

Three screens, one question, two answers. A row stored as 'yes' is a past
tenant on two of them and a current one on the third, and nothing on any of
the three screens would say why.

TN-1 is written to match the page Demetri pointed at - Tenant Lease
Agreements - so it is exact, and it stays exact. Making all three agree
changes what two screens show, which is a decision and not a repair. The
gate below PINS all three by name instead, so the split is reported on
every run and a fourth spelling is reported the day it is written.

Backups: .bak_tenantpast, the same suffix as part 1.
Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_tenantpast'
ROOT = os.getcwd()
CRLF = {}

# THE THREE, PINNED BY NAME. Not a census of a pattern - a list, so that a
# function added later is UNKNOWN rather than quietly folded in.
NARROWERS = {
    'tenant_lease_agreement':   "tenant_current='Yes'",
    'tenant_page':              "tenant_current='Yes'",
    'tenant_payment_days_view': "tenant_current__iexact='Yes'",
}


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('TN1b: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('TN1b: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('TN-1 PART 2 - THE FIXTURE THAT HAD NO STATUS%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

SUITE = os.path.join(ROOT, 'test_filter_get.py')
VIEW = os.path.join(ROOT, 'pages', 'views', 'tenants.py')

t, raw = read(SUITE)

if 'TN-1, 2 Oct 2026' in t:
    print('  test_filter_get.py       already carries the TN-1 note')
else:
    t = swap(t, """    TenantModel.objects.create(tenant_name='Alpha Tenant', prop=a)
    TenantModel.objects.create(tenant_name='Beta Tenant', prop=b)
""",
             """    # tenant_current='Yes' - TN-1, 2 Oct 2026. The Tenants list now
    # narrows to current tenants unless ?all=1 is asked for, and
    # tenant_current is a blank CharField with no default - so a row
    # created without one is not current, and these two disappeared from
    # every count in section 3.
    #
    # IT ALSO MOVED THE MARKUP DIFF IN 3c, which is the part worth
    # knowing. That section renders the panel against the .bak_filterget
    # templates and against the live ones - same view, same rows. The old
    # template lists its tenant options from `tenant`, the FILTERED set;
    # F3 moved the live one onto `all_tenant_names`, the whole table. So
    # with the rows filtered away the OLD panel lost both options and the
    # new one kept them, and a diff that should have been one line
    # shorter came out one line longer.
    #
    # Giving the rows the status they were always meant to have puts the
    # filtered set and the whole table back in agreement, which is the
    # only state in which those two loops are interchangeable.
    TenantModel.objects.create(tenant_name='Alpha Tenant', prop=a,
                               tenant_current='Yes')
    TenantModel.objects.create(tenant_name='Beta Tenant', prop=b,
                               tenant_current='Yes')
""", 'the two tenant fixture rows', SUITE)

    # TWO NUMBERS, NOT ONE. The table carried a single count and used it
    # for two different claims: how many values the view reads out of GET
    # NOW, and how many request.POST reads F1 took away. Those were equal
    # by construction - F1 moved each read from one dictionary to the
    # other - and TN-1 broke the coupling by adding a GET read that was
    # never a POST read. One number cannot answer both questions, and the
    # failure it produced named the wrong thing:
    #
    #     "the module lost EXACTLY 4 request.POST"     it lost 3
    #
    # So the column is split. n_get is a census of today; n_lost is a
    # claim about what F1 did, and it does not move again.
    t = swap(t, """FIVE = [
    ('fsr.html', '/fsr/', 'issues.py', 'fsr', 4),
    ('invoices.html', '/invoices/', 'invoices.py', 'invoices_page', 2),
    ('properties.html', '/properties/', 'properties.py',
     'properties_page', 3),
    ('suppliers.html', '/suppliers/', 'suppliers.py', 'suppliers', 2),
    ('tenant.html', '/tenant/', 'tenants.py', 'tenant_page', 3),
]
""",
             """# TWO COUNTS, NOT ONE - TN-1, 2 Oct 2026.
#
#   n_get   how many filter values the view reads out of request.GET TODAY.
#           A census. A round that adds a read comes here and says so.
#   n_lost  how many request.POST reads F1 took away. A claim about what
#           one round did, in October 2026, and it never moves again.
#
# They were ONE column until TN-1, and equal by construction: F1 moved
# each read from one dictionary to the other, so the number it added to
# GET was the number it removed from POST. TN-1 added `all` - the Include
# past tenants toggle - which was never a POST read, and the single column
# then reported "the module lost EXACTLY 4 request.POST" about a module
# that lost three. The count was right and the sentence was wrong, which
# is worse than a plain failure.
FIVE = [
    ('fsr.html', '/fsr/', 'issues.py', 'fsr', 4, 4),
    ('invoices.html', '/invoices/', 'invoices.py', 'invoices_page', 2, 2),
    ('properties.html', '/properties/', 'properties.py',
     'properties_page', 3, 3),
    ('suppliers.html', '/suppliers/', 'suppliers.py', 'suppliers', 2, 2),
    ('tenant.html', '/tenant/', 'tenants.py', 'tenant_page', 4, 3),
]
""", 'the FIVE table', SUITE)

    for old, new, what in (
            ("for page, _u, _m, _f, _n in FIVE:",
             "for page, _u, _m, _f, _n, _nl in FIVE:",
             'the section 1 loop'),
            ("for page, _u, mod, fn, n_reads in FIVE:",
             "for page, _u, mod, fn, n_reads, n_lost in FIVE:",
             'the section 2 loop'),
            ("""    ok(was.count('request.POST') - src.count('request.POST') == n_reads,
       '%-16s   and the module lost EXACTLY %d request.POST - the other '
       '%d are untouched' % ('', n_reads, src.count('request.POST')),""",
             """    ok(was.count('request.POST') - src.count('request.POST') == n_lost,
       '%-16s   and the module lost EXACTLY %d request.POST - the other '
       '%d are untouched' % ('', n_lost, src.count('request.POST')),""",
             'the POST-loss claim'),
            ("            for _p, _url, _m, _f, _nn in FIVE:\n"
             "                _got[(_p, _w)] = _panel_lines(",
             "            for _p, _url, _m, _f, _nn, _nl in FIVE:\n"
             "                _got[(_p, _w)] = _panel_lines(",
             'the 3c before/after loop'),
            ("        for _p, _url, _m, _f, _nn in FIVE:\n"
             "            _b, _a = _got[(_p, 'before')], _got[(_p, 'after')]",
             "        for _p, _url, _m, _f, _nn, _nl in FIVE:\n"
             "            _b, _a = _got[(_p, 'before')], _got[(_p, 'after')]",
             'the 3c diff loop'),
            ("for page, _u, mod, _f, _n in FIVE:",
             "for page, _u, mod, _f, _n, _nl in FIVE:",
             'the section 5 loop')):
        t = swap(t, old, new, what, SUITE)

    if not CHECK:
        back_up(SUITE, raw)
        write(SUITE, t)
    print('  test_filter_get.py       fixture rows are current; the GET '
          'census reads 4')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
import ast
import subprocess

s = read(SUITE)[0]
try:
    ast.parse(s)
except SyntaxError as e:
    raise SystemExit('TN1b: test_filter_get.py no longer parses: %s' % e)
n_status = len(re.findall(r"tenant_current='Yes'\)", s))
if n_status != 2:
    raise SystemExit('TN1b: the fixture sets a status on %d row(s), not 2'
                     % n_status)
if "'tenant_page', 4, 3)" not in s:
    raise SystemExit('TN1b: the tenants row of FIVE is not (4 read, 3 lost)')
if "'tenant_page', 3)" in s:
    raise SystemExit('TN1b: the old single-column row survives')
# EVERY UNPACK TAKES SIX. A row of six read by a loop expecting five is a
# ValueError at import, which is a crash and not a failure - so it is
# checked here rather than discovered on a push.
unpacks = re.findall(r'(?m)^\s*for\s+(.+?)\s+in FIVE:', s)
bad = [u for u in unpacks if len([x for x in u.split(',') if x.strip()]) != 6]
if bad:
    raise SystemExit('TN1b: %d loop(s) over FIVE do not unpack six: %s'
                     % (len(bad), bad[:3]))
if len(unpacks) != 5:
    raise SystemExit('TN1b: %d loops over FIVE, expected 5' % len(unpacks))
print('  test_filter_get.py parses, both rows carry a status, FIVE is '
      '(4 read, 3 lost) and all %d loops unpack six' % len(unpacks))

# THE PREMISE, ASKED OF THE MODEL RATHER THAN ASSUMED. If tenant_current
# ever gains a default of 'Yes' this fixture change becomes redundant - and
# this line is where that would be noticed.
mt = read(os.path.join(ROOT, 'pages', 'models.py'))[0]
m = re.search(r'^\s*tenant_current\s*=\s*models\.[^\n]*', mt, re.M)
if not m:
    raise SystemExit('TN1b: tenant_current is not where this round thinks')
if 'default=' in m.group(0):
    raise SystemExit('TN1b: tenant_current HAS a default now - %s'
                     % m.group(0).strip())
print('  and tenant_current still has no default, which is why it was blank')

# THE SPLIT, PINNED. Three functions, two spellings, reported every run.
vt = read(VIEW)[0]
try:
    vtree = ast.parse(vt)
except SyntaxError as e:
    raise SystemExit('TN1b: tenants.py no longer parses: %s' % e)
bodies = {n.name: (ast.get_source_segment(vt, n) or '')
          for n in ast.walk(vtree) if isinstance(n, ast.FunctionDef)}
for name, spelling in sorted(NARROWERS.items()):
    body = bodies.get(name)
    if body is None:
        raise SystemExit('TN1b: %s is gone - the pin is stale' % name)
    code = re.sub(r'(?m)#.*$', '', body)
    if spelling not in code:
        raise SystemExit('TN1b: %s no longer narrows with %r - the pin is '
                         'stale, or the split has been settled and this '
                         'round should say so' % (name, spelling))
    print('    %-26s %s' % (name, spelling))

# AND NO FOURTH ONE. Any other function narrowing on tenant_current is
# unknown to this round and is reported rather than absorbed.
extra = []
for name, body in bodies.items():
    if name in NARROWERS:
        continue
    code = re.sub(r'(?m)#.*$', '', body)
    if re.search(r"tenant_current(__iexact)?\s*=\s*'Yes'", code):
        extra.append(name)
if extra:
    raise SystemExit('TN1b: %d function(s) narrow on tenant_current and are '
                     'not pinned: %s' % (len(extra), ', '.join(sorted(extra))))
print('  three narrow on tenant_current, two spellings, and there is no '
      'fourth')

# THE CONTROL: the pin really can fail. Asked of a fabricated body, so a
# gate that had quietly stopped looking would be caught here.
_fake = "def x():\n    q = q.filter(tenant_current='No')\n"
if re.search(r"tenant_current(__iexact)?\s*=\s*'Yes'",
             re.sub(r'(?m)#.*$', '', _fake)):
    raise SystemExit('TN1b: the pin fires on a body that does not narrow')
_fake2 = "def x():\n    q = q.filter(tenant_current__iexact='Yes')\n"
if not re.search(r"tenant_current(__iexact)?\s*=\s*'Yes'",
                 re.sub(r'(?m)#.*$', '', _fake2)):
    raise SystemExit('TN1b: the pin misses a body that DOES narrow')
print('  CONTROL: the pin finds a narrowing body and spares one that is not')

# AND THE SUITES PASS. Both of them, whole.
for label in ('test_filter_get.py', 'test_tenant_past.py'):
    r = subprocess.run([sys.executable, label], capture_output=True,
                       text=True, cwd=ROOT, timeout=1800)
    tail = [ln for ln in r.stdout.split('\n') if 'passed,' in ln]
    if r.returncode != 0:
        bad = [ln for ln in r.stdout.split('\n') if 'FAIL' in ln][:6]
        raise SystemExit('TN1b: %s fails:\n   %s'
                         % (label, '\n   '.join(bad or [r.stderr[-400:]])))
    print('  %-24s%s' % (label, tail[-1] if tail else ' rc 0'))

print('-' * 74)
print('  A fixture that never said what it meant, and two template loops')
print('  that agreed by accident until one of them moved.')
print('=' * 74)
