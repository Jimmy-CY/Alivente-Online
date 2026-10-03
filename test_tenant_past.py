# -*- coding: utf-8 -*-
"""test_tenant_past.py - Section TN round TN-1, 2 Oct 2026.

Demetri, with two screenshots side by side: "I want to include this
'Include Past Tenants' button on the Tenants Module. Default (only current
tenants) with the option to include Past Tenants."

A tenant record is PER LEASE, so one person with three terms is three rows.
His screenshot shows Chrystalla Katelari three times at Apolloneon, one
Active and two Inactive, and Sacha Mamou twice at Palikaridi. The list had
no default narrowing at all.

SECTION 2 IS THE ONE REAL DECISION, AND IT IS WHERE THIS COULD HAVE GONE
WRONG. The page already filters on tenant_current through `act`. If someone
picks Inactive from the filter panel while the default narrows to current,
the two rules contradict each other and the page returns NOTHING while
showing Inactive as selected. So the default is an `elif` AFTER the chosen
status, and the suite asserts that order - not that both lines exist, but
that the specific one is tested first.

WHAT THIS SUITE CANNOT DO. It cannot tell you how many rows Live returns;
that is a fact about the database. It asserts which rule decides, in which
order, and that the toggle can always turn itself off again.
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

SUFFIX = '.bak_tenantpast'
ME = 'test_tenant_past.py'
PATCHER = 'apply_tenant_past.py'
PS1 = 'Push-PendingChanges.ps1'
VIEW = os.path.join(ROOT, 'pages', 'views', 'tenants.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'tenant.html')
REF = os.path.join(ROOT, 'pages', 'templates', 'tenant_lease_agreement.html')

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


# CO-1, 3 Oct 2026 - this was written out here, as it was in 46
# other files. It lives in alv_tree now, with the repair that
# stops `accept="image/*"` reading as a comment opener and hiding
# 94 lines of the Add Passport form from every gate in the tree.
import alv_tree
code_only = alv_tree.code_only


V = now(VIEW)
FN = [n for n in ast.walk(ast.parse(V)) if isinstance(n, ast.FunctionDef)
      and n.name == 'tenant_page']
SRC = ast.get_source_segment(V, FN[0]) if FN else ''
TPL_NOW = now(TPL)
CODE = code_only(TPL_NOW)

print('=' * 74)
print('%s - TN-1, CURRENT TENANTS BY DEFAULT' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE LIST OPENS ON CURRENT TENANCIES')
# ==========================================================================
ok(bool(FN), 'tenant_page is there and parses')
ok("request.GET.get('all') == '1'" in SRC, 'the toggle is read from ?all=1')
ok("tenant_current='Yes'" in SRC, 'and the default narrows to current')
ok("'show_all': show_all" in SRC, 'show_all reaches the template')
ok("'filter_qs'" in SRC, 'and so does the query the toggle must carry')
ok("_keep.pop('all', None)" in SRC,
   "and `all` is STRIPPED from it - or the link could never turn itself off")

if was(VIEW):
    W = was(VIEW)
    wfn = [n for n in ast.walk(ast.parse(W))
           if isinstance(n, ast.FunctionDef) and n.name == 'tenant_page']
    wsrc = ast.get_source_segment(W, wfn[0]) if wfn else ''
    ok("tenant_current='Yes'" not in wsrc,
       'CONTROL: there was no default narrowing at all before this round')
    ok("request.GET.get('all')" not in wsrc,
       '  and no toggle to read')
else:
    skip('the view controls', 'no %s backup' % SUFFIX)
    skipped += 1

# ==========================================================================
head('2. AND A CHOSEN STATUS BEATS THE DEFAULT')
# ==========================================================================
# THE ORDER IS THE CLAIM, not the presence of two lines. The page filters
# on tenant_current through `act`; if the default were tested first, or as
# a second `if`, picking Inactive would return NOTHING while showing
# Inactive as selected.
ok('elif not show_all:' in SRC,
   'the default is an ELIF, not a second independent filter')
if 'if selected_status:' in SRC and 'elif not show_all:' in SRC:
    ok(SRC.index('if selected_status:') < SRC.index('elif not show_all:'),
       'and the CHOSEN status is tested first, so it wins')
else:
    ok(False, 'both branches are present', SRC[:200])

ok('{% if not selected_status %}' in TPL_NOW,
   'the toggle hides when a status has been chosen - it would otherwise '
   'describe something other than what is on screen')

# ==========================================================================
head('3. THE CONTROL IS THE ONE THE OTHER PAGE ALREADY HAS')
# ==========================================================================
for frag in ('Include past tenants', 'Current tenants only',
             'fas fa-users', 'fas fa-user-check'):
    ok(frag in TPL_NOW, 'tenant.html carries %r' % frag)
ref = read(REF)
for frag in ('Include past tenants', 'Current tenants only'):
    ok(frag in ref,
       '  and tenant_lease_agreement says it the same way: %r' % frag)

ok(TPL_NOW.count('all=1') >= 1, 'the link adds all=1')
ok("{{ filter_qs }}all=1" in TPL_NOW,
   '  after the carried filter, so the search and the selects survive it')

# A-BAR ORDER HOLDS - secondary, filter, Back.
i_t = CODE.find('Include past tenants')
i_f = CODE.find('class="btn action-filter"')
i_b = CODE.find('class="btn action-back"')
ok(-1 < i_t < i_f < i_b,
   'and the bar reads secondary, filter, Back - A-BAR order',
   '%d / %d / %d' % (i_t, i_f, i_b))

if was(TPL):
    ok('Include past tenants' not in was(TPL),
       'CONTROL: the page had no such control before this round')
else:
    skip('the template control', 'no %s backup' % SUFFIX)

# THE MARKUP STILL CLOSES.
for tag, close in (('if', 'endif'), ('for', 'endfor')):
    a = len(re.findall(r'\{%\s*' + tag + r'\b', CODE))
    b = len(re.findall(r'\{%\s*' + close + r'\s*%\}', CODE))
    ok(a == b, 'every {%% %s %%} closes - %d / %d' % (tag, a, b))
_body = re.sub(r'<(script|style)\b.*?</\1>', '', CODE, flags=re.S)
ok(len(re.findall(r'<div\b', _body)) == len(re.findall(r'</div\s*>', _body)),
   'and every <div> closes')
ok(not [i for i, ln in enumerate(TPL_NOW.split('\n'), 1)
        if '{#' in ln and '#}' not in ln],
   'no Django comment spans lines - the lexer has no DOTALL')

# ==========================================================================
head('4. REGISTERED, AND THE PUSH GATE STILL RESOLVES')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_leaserule'),
       '  and AFTER .bak_leaserule, the round it followed')
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

