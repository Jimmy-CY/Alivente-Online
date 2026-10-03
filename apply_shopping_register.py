# -*- coding: utf-8 -*-
"""REGISTRATION FOR THE SHOPPING LIST BATCH - SL-1, SL-2, SL-3

Three rounds on one page, one suite, one gate entry. Demetri asked for the
batch; the registration follows the same shape the DB-9 bundle used.

ONE SUITE FOR THREE ROUNDS, said plainly because it is a departure. The
house pattern is a suite per round, and it is the right one when the rounds
touch different files. These three touch ONE file, in the same three
places, and three suites would each read the whole of it - which is the
duplication the filter census is still paying for five times over. The
suite has three sections, one per round, and each keeps its own backup
suffix so every claim is still measured against the state its round was
built on.

Backups: .bak_shopreg. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_shopreg'
ROOT = os.getcwd()
CRLF = {}
RND = os.path.join(ROOT, 'alv_rounds.py')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
NEW_ROUNDS = ['.bak_printguard', '.bak_shopbar', '.bak_shoptone']


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
            raise SystemExit('SREG: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('SREG: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('REGISTRATION - SL-1, SL-2, SL-3%s' % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(RND)
if NEW_ROUNDS[-1] in t:
    print('  alv_rounds.py            already lists all three')
else:
    t = swap(t, "    '.bak_fixedpop',\n]",
             "    '.bak_fixedpop',\n"
             + ''.join("    '%s',\n" % r for r in NEW_ROUNDS) + ']',
             'the end of ROUNDS', RND)
    if not CHECK:
        back_up(RND, raw)
        write(RND, t)
    print('  alv_rounds.py            %s' % ', '.join(NEW_ROUNDS))

t, raw = read(PS1)
if 'test_shopping_list.py' in t:
    print('  Push-PendingChanges.ps1  already registered')
else:
    t = swap(t, "    'test_fixed_popup.py'\n)",
             """    'test_fixed_popup.py'
    # The Shopping List: SL-1 the print guard, SL-2 the bar, SL-3 the
    # colours. ONE suite for three rounds because they are one programme
    # on one page - three suites would each read the whole of it. Its
    # section 1 is the functional bug, and it checks the three guards
    # SEPARATELY, because a keyboard Ctrl+P reaches none of the other two.
    'test_shopping_list.py'
)""", 'the end of $suites', PS1)

    t = swap(t, '$sentinels = @(\n',
             "$sentinels = @(\n"
             "    @{ File = 'pages\\templates\\meal_plan_shopping_list.html'; "
             "Text = 'function hasPrintableList()'; "
             "What = 'SL-1: Print refuses when there is nothing to print' },\n"
             "    @{ File = 'pages\\templates\\meal_plan_shopping_list.html'; "
             "Text = 'id=\"printBtn\" hidden'; "
             "What = 'SL-1: and the button is not there until there is' },\n"
             "    @{ File = 'pages\\templates\\meal_plan_shopping_list.html'; "
             "Text = 'function setBar(step)'; "
             "What = 'SL-2: one bar, and it says which step you are on' },\n"
             "    @{ File = 'pages\\templates\\meal_plan_shopping_list.html'; "
             "Text = 'step-navigation'; Absent = $true; Code = $true; "
             "What = 'SL-2: and both bottom bars are gone' },\n"
             "    @{ File = 'pages\\templates\\meal_plan_shopping_list.html'; "
             "Text = 'share-whatsapp'; "
             "What = 'SL-3: the one kept literal is named, not stray' },\n"
             "    @{ File = 'pages\\templates\\meal_plan_shopping_list.html'; "
             "Text = '#28a745'; Absent = $true; Code = $true; "
             "What = 'SL-3: and the green is gone - a step is not a verdict' "
             "},\n", 'the head of $sentinels', PS1)
    if not CHECK:
        back_up(PS1, raw)
        write(PS1, t, bom=True)
    print('  Push-PendingChanges.ps1  1 suite, 6 sentinels')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

import ast
import subprocess

ast.parse(read(RND)[0])
sys.modules.pop('alv_rounds', None)
sys.path.insert(0, ROOT)
from alv_rounds import ROUNDS
for r in NEW_ROUNDS:
    if r not in ROUNDS:
        raise SystemExit('SREG: %s did not reach ROUNDS' % r)
if ROUNDS[-3:] != NEW_ROUNDS:
    raise SystemExit('SREG: they are not the last three in build order: %s'
                     % ROUNDS[-4:])
if len(ROUNDS) != len(set(ROUNDS)):
    raise SystemExit('SREG: ROUNDS has a duplicate')
print('  ROUNDS lists %d rounds, the three last and in build order'
      % len(ROUNDS))

ps = read(PS1)[0]
n_s = len(re.findall(r"'test_[a-z0-9_]+\.py'", ps))
n_t = len(re.findall(r'@\{ *File *=', ps))
print('  $suites lists %d suite(s), $sentinels %d row(s)' % (n_s, n_t))

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
if len(rows) != n_t:
    raise SystemExit('SREG: %d of %d sentinel rows parse' % (len(rows), n_t))


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
    raise SystemExit('SREG: %d sentinel(s) do not resolve:\n   %s'
                     % (len(stale), '\n   '.join(stale[:8])))
print('  and all %d sentinels resolve against the tree' % len(rows))

r = subprocess.run([sys.executable, 'test_shopping_list.py'],
                   capture_output=True, text=True, cwd=ROOT, timeout=1800)
tail = [ln for ln in r.stdout.split('\n') if 'passed,' in ln]
if r.returncode != 0:
    bad = [ln for ln in r.stdout.split('\n') if 'FAIL' in ln][:6]
    raise SystemExit('SREG: the suite fails:\n   %s'
                     % '\n   '.join(bad or [r.stderr[-400:]]))
print('  test_shopping_list.py%s' % (tail[-1] if tail else ' rc 0'))

print('-' * 74)
print('  One page, three rounds, one suite, one gate entry.')
print('=' * 74)
