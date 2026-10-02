# -*- coding: utf-8 -*-
"""IB-1, PART 2 - REGISTRATION

A round is not finished when it works. It is finished when the gate knows
about it, because the next person to run the sweep is the gate.

Three places, and each answers a different question:

    alv_rounds.ROUNDS          what order the rounds happened in, which is
                               what as_left_by() needs to answer "the file
                               as THAT round left it"
    $suites                    what the push runs
    $sentinels                 whether the TREE arrived with the gate -
                               checked BEFORE any suite, because a clean
                               sweep of a half-delivered tree is worse than
                               no sweep at all

THE DELIVERY ERROR THIS MORNING is why the third one matters. A gate
carrying DB-8 and TN-1 sentinels went out with only B-1c's files; the push
refused with four sentinel FAILs, correctly, and the fix was to rebuild the
gate to match the tree rather than to force past it.

Backups: .bak_ingfilter, the same suffix as part 1.
Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_ingfilter'
ROOT = os.getcwd()
CRLF = {}


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8-sig'), raw


def write(path, text, bom=False):
    data = text.encode('utf-8')
    if bom:
        data = b'\xef\xbb\xbf' + data
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
            raise SystemExit('IB1R: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('IB1R: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('IB-1 PART 2 - REGISTRATION%s' % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

RND = os.path.join(ROOT, 'alv_rounds.py')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')

# ==========================================================================
# 1. ROUNDS - in the order the rounds happened.
# ==========================================================================
t, raw = read(RND)
if "'.bak_ingfilter'" in t:
    print('  alv_rounds.py            already lists .bak_ingfilter')
else:
    t = swap(t, """    '.bak_favnote',
]""", """    '.bak_favnote',
    '.bak_ingfilter',
]""", 'the end of ROUNDS', RND)
    if not CHECK:
        back_up(RND, raw)
        write(RND, t)
    print('  alv_rounds.py            .bak_ingfilter, after .bak_favnote')

# ==========================================================================
# 2. $suites and $sentinels.
# ==========================================================================
t, raw = read(PS1)

SUITE_OLD = """    'test_tenant_past.py'
)"""
SUITE_NEW = """    'test_tenant_past.py'
    # The ingredient filter folds away. Its section 2 is the one that
    # matters: a live search may only promise what the server delivers,
    # so the suite re-asks the VIEW - name__icontains and nothing else,
    # no Paginator - rather than trusting the markup that names them.
    'test_ingredient_filter.py'
)"""

SENT_OLD = """$sentinels = @(
"""
SENT_NEW = """$sentinels = @(
    @{ File = 'pages\\templates\\ingredient_base_units_management.html'; Text = 'data-live-search-cell="Ingredient Name"'; What = 'IB-1: the ingredient search narrows as you type' },
    @{ File = 'pages\\templates\\ingredient_base_units_management.html'; Text = 'class="btn action-filter" id="filterBtn"'; What = 'IB-1: the filter folds behind a button' },
    @{ File = 'pages\\templates\\ingredient_base_units_management.html'; Text = 'filter-bar'; Absent = $true; Code = $true; What = 'IB-1: and the always-open card is gone' },
    # NO APOSTROPHE IN A SENTINEL TEXT. PowerShell escapes one inside a
    # single-quoted string by DOUBLING it, not with a backslash, and the
    # first cut of this row wrote THE HEADER\\'S - which reached the gate as
    # a backslash and resolved against nothing. The text below says the
    # same thing and has no quote in it at all.
    @{ File = 'pages\\templates\\base.html'; Text = 'TWO LABELS - IB-1, 2 Oct 2026'; What = 'IB-1: base swaps the panel header labels instead of a fifth local copy' },
"""

if 'test_ingredient_filter.py' in t:
    print('  Push-PendingChanges.ps1  already registered')
else:
    t = swap(t, SUITE_OLD, SUITE_NEW, 'the end of $suites', PS1)
    t = swap(t, SENT_OLD, SENT_NEW, 'the head of $sentinels', PS1)
    if not CHECK:
        back_up(PS1, raw)
        write(PS1, t, bom=True)
    print('  Push-PendingChanges.ps1  suite registered, four sentinels added')

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

t = read(RND)[0]
try:
    ast.parse(t)
except SyntaxError as e:
    raise SystemExit('IB1R: alv_rounds.py no longer parses: %s' % e)
sys.path.insert(0, ROOT)
for _m in ('alv_rounds',):
    sys.modules.pop(_m, None)
from alv_rounds import ROUNDS
if SUFFIX not in ROUNDS:
    raise SystemExit('IB1R: %s did not reach ROUNDS' % SUFFIX)
if ROUNDS.index(SUFFIX) != len(ROUNDS) - 1:
    raise SystemExit('IB1R: %s is not last - it is the most recent round'
                     % SUFFIX)
if len(ROUNDS) != len(set(ROUNDS)):
    dup = [r for r in ROUNDS if ROUNDS.count(r) > 1]
    raise SystemExit('IB1R: ROUNDS has a duplicate: %s' % sorted(set(dup)))
print('  ROUNDS lists %d rounds, %s last, none twice' % (len(ROUNDS), SUFFIX))

ps = read(PS1)[0]
n_suites = len(re.findall(r"'test_[a-z0-9_]+\.py'", ps))
n_sent = len(re.findall(r'@\{ *File *=', ps))
if "'test_ingredient_filter.py'" not in ps:
    raise SystemExit('IB1R: the suite is not in $suites')
print('  $suites lists %d suite(s), $sentinels %d row(s)'
      % (n_suites, n_sent))

# EVERY SENTINEL STILL RESOLVES - the whole table, not only the new rows,
# because a gate that half-resolves refuses the push either way.
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
if len(rows) != n_sent:
    raise SystemExit('IB1R: %d of %d sentinel rows parse - a row this gate '
                     'cannot read is a row it cannot check'
                     % (len(rows), n_sent))


def _strip(x):
    x = re.sub(r'<!--.*?-->', '', x, flags=re.S)
    x = re.sub(r'\{#.*?#\}', '', x, flags=re.S)
    x = re.sub(r'/\*.*?\*/', '', x, flags=re.S)
    return re.sub(r'(?m)^\s*//.*$', '', x)


stale = []
for r in rows:
    p = os.path.join(ROOT, *r['File'].replace('\\', '/').split('/'))
    if not os.path.isfile(p):
        stale.append('%s FILE MISSING' % r['File'])
        continue
    with open(p, encoding='utf-8', errors='replace') as fh:
        b = fh.read()
    if r.get('Code'):
        b = _strip(b)
    if (r['Text'].lower() in b.lower()) != (not r.get('Absent')):
        stale.append('%s %s %r' % (r['File'],
                     'NOT FOUND' if not r.get('Absent') else 'IS BACK',
                     r['Text'][:46]))
if stale:
    raise SystemExit('IB1R: %d sentinel(s) do not resolve:\n   %s'
                     % (len(stale), '\n   '.join(stale[:6])))
print('  and all %d sentinels resolve against the tree' % len(rows))

# THE ABSENT ROW IS THE INTERESTING ONE: it claims .filter-bar is gone from
# CODE. Proved both ways here, because an Absent sentinel that can never
# fire is a row of reassurance and nothing else.
_tpl = os.path.join(ROOT, 'pages', 'templates',
                    'ingredient_base_units_management.html')
with open(_tpl, encoding='utf-8', errors='replace') as fh:
    _raw = fh.read()
if 'filter-bar' not in _raw:
    raise SystemExit('IB1R: the premise is wrong - the round LEAVES a note '
                     'naming .filter-bar, and the Absent row exists to show '
                     'that stripping comments is what makes it absent')
if 'filter-bar' in _strip(_raw):
    raise SystemExit('IB1R: .filter-bar survives in code')
print('  CONTROL: .filter-bar is in the file and NOT in the code - which is '
      'the whole reason that row carries Code = $true')

# AND THE SUITE PASSES, NOW THAT IT CAN SEE ITS OWN REGISTRATION.
r = subprocess.run([sys.executable, 'test_ingredient_filter.py'],
                   capture_output=True, text=True, cwd=ROOT, timeout=1800)
tail = [ln for ln in r.stdout.split('\n') if 'passed,' in ln]
if r.returncode != 0:
    bad = [ln for ln in r.stdout.split('\n') if 'FAIL' in ln][:6]
    raise SystemExit('IB1R: the suite fails:\n   %s'
                     % '\n   '.join(bad or [r.stderr[-400:]]))
print('  test_ingredient_filter.py%s' % (tail[-1] if tail else ' rc 0'))

print('-' * 74)
print('  The gate knows about the round. A sweep that passes now means')
print('  something it did not mean five minutes ago.')
print('=' * 74)
