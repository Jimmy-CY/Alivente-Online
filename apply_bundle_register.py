# -*- coding: utf-8 -*-
"""REGISTRATION FOR THE BUNDLE - DB-9, UC-1 AND PU-1

Demetri: "Can we bundle these Lease Expiries with UC-1 (the Unit
Conversions pills) and PU-1 (the clipped popups)? and then we run one push
for all?"

One sweep, one gate, one push - so one registration, and the three rounds
go into ROUNDS in the order they were built, because as_left_by() answers
"the file as THAT round left it" by walking that list.

==========================================================================
AND TWO SENTINELS HAVE TO GO, WHICH IS THE INTERESTING PART
==========================================================================
DB-8's rows said the dashboard calls expiring_no_successor and keeps
_get_expiring_leases_before_db8. DB-9 removed both on purpose - the first
because it was the wrong function, the second because DB-9 restored the
rule it was keeping. A sentinel is a claim that the TREE arrived with the
gate; a sentinel for a decision that has been reversed is a claim about
yesterday, and it fails loudly, which is correct and is how this was found.

They are replaced rather than deleted. The new rows say the dashboard calls
renewal_due and that the cash-cliff function is ABSENT from it - the second
one an Absent row, so a future round quietly reaching for the wrong
function again is reported the day it does.

Backups: .bak_bundlereg. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_bundlereg'
ROOT = os.getcwd()
CRLF = {}

RND = os.path.join(ROOT, 'alv_rounds.py')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')

# In build order. as_left_by walks this list, so the order is a fact about
# what happened, not a preference.
NEW_ROUNDS = ['.bak_renewalwin', '.bak_convpills', '.bak_fixedpop']
NEW_SUITES = [
    ("test_conversion_pills.py",
     "    # A scope is not a verdict. The Applies To column was amber for\n"
     "    # one answer and green for the other, and neither is a judgement.\n"
     "    # Its section 3 proves a CSS rule never fired, from the siblings\n"
     "    # and then again in a browser."),
    ("test_fixed_popup.py",
     "    # The list popup was absolute inside an overflow: clip container,\n"
     "    # so it was cut at the container's edge. Its section 3 clicks the\n"
     "    # trigger in a real browser and measures what was painted."),
]


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
            raise SystemExit('REG: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('REG: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('REGISTRATION - DB-9, UC-1, PU-1%s' % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 1. ROUNDS.
# ==========================================================================
t, raw = read(RND)
if NEW_ROUNDS[-1] in t:
    print('  alv_rounds.py            already lists all three')
else:
    t = swap(t, "    '.bak_ingfilter',\n]",
             "    '.bak_ingfilter',\n"
             + ''.join("    '%s',\n" % r for r in NEW_ROUNDS) + ']',
             'the end of ROUNDS', RND)
    if not CHECK:
        back_up(RND, raw)
        write(RND, t)
    print('  alv_rounds.py            %s' % ', '.join(NEW_ROUNDS))

# ==========================================================================
# 2. $suites and $sentinels.
# ==========================================================================
t, raw = read(PS1)

if 'test_fixed_popup.py' in t:
    print('  Push-PendingChanges.ps1  already registered')
else:
    tail = "    'test_ingredient_filter.py'\n)"
    t = swap(t, tail,
             "    'test_ingredient_filter.py'\n"
             + ''.join("%s\n    '%s'\n" % (note, name)
                       for name, note in NEW_SUITES) + ')',
             'the end of $suites', PS1)

    # --- DB-8's two rows out, DB-9's three in.
    for stale, why in (
            ("    @{ File = 'pages\\views\\notifications_dashboard.py'; "
             "Text = 'expiring_no_successor'; What = 'DB-8: the button uses "
             "the panel rule' },\n",
             'DB-8: the button uses the panel rule'),
            ("    @{ File = 'pages\\views\\notifications_dashboard.py'; "
             "Text = '_get_expiring_leases_before_db8'; What = 'DB-8: the old "
             "rule is kept, uncalled' },\n",
             'DB-8: the old rule is kept, uncalled')):
        if stale not in t:
            raise SystemExit('REG: a DB-8 sentinel is not where this round '
                             'thinks: %s' % why)
        t = t.replace(stale, '', 1)

    NEW_SENT = (
        "$sentinels = @(\n"
        "    @{ File = 'pages\\services\\portfolio_insights.py'; "
        "Text = 'def renewal_due('; "
        "What = 'DB-9: one function decides the renewal window' },\n"
        "    @{ File = 'pages\\views\\notifications_dashboard.py'; "
        "Text = 'renewal_due(today=today, status=''pending'')'; "
        "What = 'DB-9: the Expiring Leases tile calls it' },\n"
        "    @{ File = 'pages\\views\\notifications_dashboard.py'; "
        "Text = 'expiring_no_successor'; Absent = $true; "
        "What = 'DB-9: and the dashboard does NOT reach for the cash cliff' "
        "},\n"
        "    @{ File = 'pages\\templates\\home.html'; "
        "Text = 'Inside their renewal period'; "
        "What = 'DB-9: the panel says what it shows' },\n"
        "    @{ File = 'pages\\templates\\unit_conversions_management.html'; "
        "Text = 'alv-pill alv-pill-info conversion-number'; "
        "What = 'UC-1: the quantity chips are house pills' },\n"
        "    @{ File = 'pages\\templates\\unit_conversions_management.html'; "
        "Text = '#ffc107'; Absent = $true; Code = $true; "
        "What = 'UC-1: and the amber is gone - a scope is not a verdict' },\n"
        "    @{ File = 'pages\\templates\\base.html'; "
        "Text = 'ALV POP v1'; "
        "What = 'PU-1: one popup component, in a fixed layer' },\n"
        "    @{ File = 'pages\\templates\\categories_management.html'; "
        "Text = 'ingredient-popup'; Absent = $true; Code = $true; "
        "What = 'PU-1: and the page keeps no copy of its own' },\n")
    t = swap(t, '$sentinels = @(\n', NEW_SENT, 'the head of $sentinels', PS1)

    if not CHECK:
        back_up(PS1, raw)
        write(PS1, t, bom=True)
    print('  Push-PendingChanges.ps1  2 suites, 8 sentinels in, 2 stale out')

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
    raise SystemExit('REG: alv_rounds.py no longer parses: %s' % e)
for m in ('alv_rounds',):
    sys.modules.pop(m, None)
sys.path.insert(0, ROOT)
from alv_rounds import ROUNDS
for r in NEW_ROUNDS:
    if r not in ROUNDS:
        raise SystemExit('REG: %s did not reach ROUNDS' % r)
if [ROUNDS.index(r) for r in NEW_ROUNDS] != \
        sorted(ROUNDS.index(r) for r in NEW_ROUNDS):
    raise SystemExit('REG: the three are out of build order in ROUNDS')
if ROUNDS[-3:] != NEW_ROUNDS:
    raise SystemExit('REG: they are not the last three: %s' % ROUNDS[-4:])
if len(ROUNDS) != len(set(ROUNDS)):
    dup = sorted(set(r for r in ROUNDS if ROUNDS.count(r) > 1))
    raise SystemExit('REG: ROUNDS has a duplicate: %s' % dup)
print('  ROUNDS lists %d rounds, the three last and in build order'
      % len(ROUNDS))

ps = read(PS1)[0]
n_suites = len(re.findall(r"'test_[a-z0-9_]+\.py'", ps))
n_sent = len(re.findall(r'@\{ *File *=', ps))
for name, _note in NEW_SUITES:
    if "'%s'" % name not in ps:
        raise SystemExit('REG: %s is not in $suites' % name)
if "'test_lease_rule.py'" not in ps:
    raise SystemExit('REG: test_lease_rule.py left $suites - DB-9 keeps it')
print('  $suites lists %d suite(s), $sentinels %d row(s)'
      % (n_suites, n_sent))

# EVERY SENTINEL RESOLVES - the whole table. A gate that half-resolves
# refuses the push either way, and the delivery error of this morning was
# a gate that arrived ahead of its tree.
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
    raise SystemExit('REG: %d of %d sentinel rows parse - a row the gate '
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
    raise SystemExit('REG: %d sentinel(s) do not resolve:\n   %s'
                     % (len(stale), '\n   '.join(stale[:8])))
print('  and all %d sentinels resolve against the tree' % len(rows))

# THE THREE Absent ROWS ARE THE ONES WORTH PROVING. An Absent row that can
# never fire is reassurance, not a gate - so each is shown to be absent
# from CODE and, where it applies, present in the file as prose.
for f, text, code_only in (
        ('pages/views/notifications_dashboard.py', 'expiring_no_successor',
         False),
        ('pages/templates/unit_conversions_management.html', '#ffc107', True),
        ('pages/templates/categories_management.html', 'ingredient-popup',
         True)):
    with open(os.path.join(ROOT, *f.split('/')), encoding='utf-8',
              errors='replace') as fh:
        body = fh.read()
    if text.lower() in (_strip(body) if code_only else body).lower():
        raise SystemExit('REG: %r is still in %s' % (text, f))
    print('    %-46s %r absent' % (f.split('/')[-1], text))

# AND THE THREE SUITES PASS, NOW THAT THEY CAN SEE THEIR REGISTRATION.
for name in ('test_lease_rule.py', 'test_conversion_pills.py',
             'test_fixed_popup.py'):
    r = subprocess.run([sys.executable, name], capture_output=True,
                       text=True, cwd=ROOT, timeout=1800)
    tail = [ln for ln in r.stdout.split('\n') if 'passed,' in ln]
    if r.returncode != 0:
        bad = [ln for ln in r.stdout.split('\n') if 'FAIL' in ln][:6]
        raise SystemExit('REG: %s fails:\n   %s'
                         % (name, '\n   '.join(bad or [r.stderr[-400:]])))
    print('  %-26s%s' % (name, tail[-1] if tail else ' rc 0'))

print('-' * 74)
print('  One gate for three rounds, and two sentinels about a decision')
print('  that was reversed are gone rather than forced past.')
print('=' * 74)
