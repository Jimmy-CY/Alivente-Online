# -*- coding: utf-8 -*-
"""test_lease_rule.py - Section DB round DB-8, 2 Oct 2026.

Demetri, on the dashboard: "The Expiring Leases section doesn't add up. The
section shows three expiring leases (with less than 90 days to go), but the
button only shows 2."

It was not arithmetic. Two functions answered two different questions, six
inches apart on one screen, under one name:

    PANEL   expiring_no_successor(within_days=90)
            ending within a FIXED 90 days, no successor lease on the
            property                                            -> THREE
    BUTTON  get_expiring_leases()
            tenant_current='Yes' AND today past (lease_end minus the
            TENANT'S OWN renewal_period) AND renewal_status 'pending'
                                                                -> TWO

SECTION 1 IS THE CLAIM: there is one rule now, and the button CALLS the
panel's function rather than copying it. A copied rule is two rules again
the first time either is edited, which is how this started.

SECTION 2 IS THE COST, ASSERTED RATHER THAN HIDDEN. The per-tenant renewal
lead time is gone - a lease needing six months' notice is now flagged at
ninety days like every other one. Demetri took that trade knowingly. The
old implementation is KEPT AND UNCALLED so the idea is not lost, and this
suite asserts nothing calls it, so it cannot drift back into service
without a round saying so.

SECTION 3 IS THE TWO COLUMNS THAT STOPPED BEING TRUE. Both tables printed
`item.renewal_date` and the literal string PENDING. Neither survives: there
is no renewal period in the new rule, and PENDING was only ever true
because the OLD query filtered on it - a constant dressed as data.

WHAT THIS SUITE CANNOT DO, SAID FIRST. It cannot tell you the count is 3 on
Live; that is a fact about the database, not the code. It asserts that ONE
function decides it, that both tables read only keys that function
produces, and that no key it stopped producing is still read.
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
import ast

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_leaserule'
ME = 'test_lease_rule.py'
PATCHER = 'apply_lease_rule.py'
PS1 = 'Push-PendingChanges.ps1'

VIEW = os.path.join(ROOT, 'pages', 'views', 'notifications_dashboard.py')
SVC = os.path.join(ROOT, 'pages', 'services', 'portfolio_insights.py')
HOME = os.path.join(ROOT, 'pages', 'templates', 'home.html')
NOTI = os.path.join(ROOT, 'pages', 'templates', 'notifications.html')

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
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


V = now(VIEW)
TREE = ast.parse(V)
FNS = dict((n.name, n) for n in ast.walk(TREE)
           if isinstance(n, ast.FunctionDef))
SRC = ast.get_source_segment(V, FNS['get_expiring_leases']) \
    if 'get_expiring_leases' in FNS else ''

print('=' * 74)
print('%s - DB-8, ONE DEFINITION OF AN EXPIRING LEASE' % ME)
print('=' * 74)

# ==========================================================================
head('1. ONE RULE, AND THE BUTTON CALLS IT RATHER THAN COPYING IT')
# ==========================================================================
ok('get_expiring_leases' in FNS, 'get_expiring_leases is still there')
ok('expiring_no_successor' in SRC,
   'and it calls expiring_no_successor - the panel\'s own function')
ok('within_days=90' in SRC, '  with the panel\'s 90-day window')
ok('cursor.execute' not in SRC,
   '  and runs no query of its own any more')

# THE IMPORT RESOLVES. Django is not importable here, but a mistyped
# dotted path only shows up when the dashboard is opened, and the file and
# the name are both checkable without loading anything.
m = re.search(r'from ([\w.]+) import expiring_no_successor', SRC)
ok(bool(m), 'the import names a module')
if m:
    mod = os.path.join(ROOT, *m.group(1).split('.')) + '.py'
    ok(os.path.isfile(mod), '  which is a real file: %s'
       % os.path.relpath(mod, ROOT).replace(os.sep, '/'), mod)
    if os.path.isfile(mod):
        defs = [n.name for n in ast.walk(ast.parse(read(mod)))
                if isinstance(n, ast.FunctionDef)]
        ok('expiring_no_successor' in defs,
           '  and really defines expiring_no_successor')

if was(VIEW):
    W = was(VIEW)
    ok('tenant_renewal_period' in W and 'cursor.execute' in W,
       'CONTROL: it used to run its own query on tenant_renewal_period')
    wsrc = ast.get_source_segment(
        W, dict((n.name, n) for n in ast.walk(ast.parse(W))
                if isinstance(n, ast.FunctionDef))['get_expiring_leases'])
    ok('expiring_no_successor' not in wsrc,
       '  and did not call the panel\'s function at all')
else:
    skip('the view controls', 'no %s backup' % SUFFIX)
    skipped += 1

# ==========================================================================
head('2. THE COST IS KEPT, NAMED, AND NOT CALLED')
# ==========================================================================
ok('_get_expiring_leases_before_db8' in FNS,
   'the old rule is kept under its own name')
OLD = ast.get_source_segment(V, FNS['_get_expiring_leases_before_db8']) \
    if '_get_expiring_leases_before_db8' in FNS else ''
ok('tenant_renewal_period' in OLD,
   '  and it really is the old rule - it carries the renewal period')
callers = [n for n in ast.walk(TREE) if isinstance(n, ast.Call)
           and isinstance(n.func, ast.Name)
           and n.func.id == '_get_expiring_leases_before_db8']
ok(not callers, '  and NOTHING calls it, so it cannot drift back into '
   'service without a round saying so',
   [n.lineno for n in callers])
ok('six months' in OLD or 'lead time' in OLD,
   '  with the reason it was kept written beside it')

# ==========================================================================
head('3. AND NEITHER TABLE READS A KEY THE RULE NO LONGER PRODUCES')
# ==========================================================================
produced = set(re.findall(r"'(\w+)':", SRC))
for k in ('prop_name', 'prop_country', 'tenant_name', 'lease_end_date',
          'days_to_end', 'renewal_status'):
    ok(k in produced, 'the mapping produces %s' % k, sorted(produced))
ok('renewal_date' not in produced,
   'and NOT renewal_date - the new rule cannot compute one', sorted(produced))

ANCHOR = {HOME: 'function buildExpiringContent',
          NOTI: 'const items = this.data.expiringLeases'}
for path, label in ((HOME, 'home.html'), (NOTI, 'notifications.html')):
    body = now(path)
    i = body.find(ANCHOR[path])
    if i < 0:
        skip('%s' % label, 'no builder to anchor on')
        continue
    j = body.find('</table>', i)
    seg = body[i:j if j > i else i + 2500]
    seg = re.sub(r'<!--.*?-->', '', seg, flags=re.S)
    seg = re.sub(r'/\*.*?\*/', '', seg, flags=re.S)
    used = set(re.findall(r'item\.(\w+)', seg))
    ok(not (used - produced), '%-20s reads only keys the rule produces'
       % label, sorted(used - produced))
    ok('renewal_date' not in used, '  and no longer reads renewal_date')
    ok('days_to_end' in used, '  and shows days_to_end, as the panel does')
    ok(not re.search(r'status-warning">PENDING<', seg),
       '  with no hard-coded PENDING')
    ok('Renewal Due By' not in body and 'Days to End' in body,
       '  and its heading reads Days to End')
    if was(path):
        w = was(path)
        ok('renewal_date' in w and 'status-warning">PENDING<' in w,
           '  CONTROL: it read renewal_date and printed PENDING before')
    else:
        skip('%s control' % label, 'no %s backup' % SUFFIX)

# ==========================================================================
head('4. REGISTERED, AND THE PUSH GATE STILL RESOLVES')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_mealrow'),
       '  and AFTER .bak_mealrow, the round it followed')
except Exception as e:
    skip('ROUNDS', str(e))

_Q = r"'((?:[^']|'')*)'|\"((?:[^\"]|\"\")*)\""
SF = re.compile(r"\b(File|Text|What)\s*=\s*(?:%s)" % _Q)
SG = re.compile(r"\b(Absent|Code)\s*=\s*\$(true|false)")
rows = []
for line in ps.split('\n'):
    if '@{' not in line or 'File' not in line:
        continue
    f = {}
    for k, sq, dq in SF.findall(line):
        f[k] = sq.replace("''", "'") if sq else dq.replace('""', '"')
    for k, v in SG.findall(line):
        f[k] = (v == 'true')
    if 'File' in f and 'Text' in f:
        rows.append(f)
rawrows = len(re.findall(r'@\{ *File *=', ps))
ok(len(rows) == rawrows,
   'the sentinel table parses %d of %d rows' % (len(rows), rawrows))


def _strip(x):
    x = re.sub(r'<!--.*?-->', '', x, flags=re.S)
    x = re.sub(r'\{#.*?#\}', '', x, flags=re.S)
    x = re.sub(r'/\*.*?\*/', '', x, flags=re.S)
    x = re.sub(r'(?m)^\s*//.*$', '', x)
    return re.sub(r'(?m)^\s*#.*$', '', x)


stale = []
for r in rows:
    p = os.path.join(ROOT, *r['File'].replace('\\', '/').split('/'))
    if not os.path.isfile(p):
        stale.append('%s FILE MISSING' % r['File'])
        continue
    b = read(p)
    if r.get('Code'):
        b = _strip(b)
    if (r['Text'].lower() in b.lower()) != (not r.get('Absent')):
        stale.append('%s %s %r' % (r['File'],
                     'NOT FOUND' if not r.get('Absent') else 'IS BACK',
                     r['Text'][:46]))
ok(not stale, 'and all %d of them still resolve' % len(rows),
   '\n'.join(stale[:6]))
print('\n    $suites now lists %d suite(s).'
      % len(re.findall(r"'test_[a-z0-9_]+\.py'", ps)))

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)

