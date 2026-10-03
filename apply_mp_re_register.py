# -*- coding: utf-8 -*-
"""REGISTRATION FOR MP-1 AND RE-1

The last two of Demetri's eight Recipes & Meal Plans items. Two rounds on
two different pages, so TWO suites - the house pattern, and the right one
here. The Shopping List trio shared a suite because they shared a file;
these do not.

Backups: .bak_mprereg. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_mprereg'
ROOT = os.getcwd()
CRLF = {}
RND = os.path.join(ROOT, 'alv_rounds.py')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
NEW_ROUNDS = ['.bak_mealbtn', '.bak_recipebar']


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
            raise SystemExit('MREG: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('MREG: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('REGISTRATION - MP-1, RE-1%s' % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(RND)
if NEW_ROUNDS[-1] in t:
    print('  alv_rounds.py            already lists both')
else:
    t = swap(t, "    '.bak_shoptone',\n]",
             "    '.bak_shoptone',\n"
             + ''.join("    '%s',\n" % r for r in NEW_ROUNDS) + ']',
             'the end of ROUNDS', RND)
    if not CHECK:
        back_up(RND, raw)
        write(RND, t)
    print('  alv_rounds.py            %s' % ', '.join(NEW_ROUNDS))

t, raw = read(PS1)
if 'test_recipe_bar_top.py' in t:
    print('  Push-PendingChanges.ps1  already registered')
else:
    t = swap(t, "    'test_shopping_list.py'\n)",
             """    'test_shopping_list.py'
    # The green Add Recipe and the red trashcans. Its section 2 is why it
    # was a round: four of the ten uses were inside JavaScript template
    # strings, so the day cards the page builds AFTER load would have kept
    # the old paint.
    'test_meal_plan_buttons.py'
    # Update at the top of Create/Edit Recipe. Its section 2 drives a real
    # browser, because a submit button outside its form fails SILENTLY -
    # the page looks right and pressing it does nothing.
    'test_recipe_bar_top.py'
)""", 'the end of $suites', PS1)
    t = swap(t, '$sentinels = @(\n',
             "$sentinels = @(\n"
             "    @{ File = 'pages\\templates\\create_meal_plan.html'; "
             "Text = 'icon-action-btn icon-delete'; "
             "What = 'MP-1: the trashcans are on the house row-action strip' "
             "},\n"
             "    @{ File = 'pages\\templates\\create_meal_plan.html'; "
             "Text = 'btn-add-recipe'; Absent = $true; Code = $true; "
             "What = 'MP-1: and the green Add Recipe is gone, script "
             "included' },\n"
             "    @{ File = 'pages\\templates\\preview_imported_recipe.html'; "
             "Text = 'form=\"saveRecipeForm\"'; "
             "What = 'RE-1: the bar Update owns the form it is outside of' "
             "},\n"
             "    @{ File = 'pages\\templates\\preview_imported_recipe.html'; "
             "Text = 'btn btn-secondary btn-lg'; Absent = $true; "
             "Code = $true; "
             "What = 'RE-1: and the bottom Cancel is gone' },\n",
             'the head of $sentinels', PS1)
    if not CHECK:
        back_up(PS1, raw)
        write(PS1, t, bom=True)
    print('  Push-PendingChanges.ps1  2 suites, 4 sentinels')

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
        raise SystemExit('MREG: %s did not reach ROUNDS' % r)
if ROUNDS[-2:] != NEW_ROUNDS:
    raise SystemExit('MREG: not the last two in build order: %s' % ROUNDS[-3:])
if len(ROUNDS) != len(set(ROUNDS)):
    raise SystemExit('MREG: ROUNDS has a duplicate')
print('  ROUNDS lists %d rounds, the two last and in build order'
      % len(ROUNDS))

ps = read(PS1)[0]
print('  $suites lists %d suite(s), $sentinels %d row(s)'
      % (len(re.findall(r"'test_[a-z0-9_]+\.py'", ps)),
         len(re.findall(r'@\{ *File *=', ps))))

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
if len(rows) != len(re.findall(r'@\{ *File *=', ps)):
    raise SystemExit('MREG: a sentinel row does not parse')


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
    raise SystemExit('MREG: %d sentinel(s) do not resolve:\n   %s'
                     % (len(stale), '\n   '.join(stale[:8])))
print('  and all %d sentinels resolve against the tree' % len(rows))

for name in ('test_meal_plan_buttons.py', 'test_recipe_bar_top.py'):
    r = subprocess.run([sys.executable, name], capture_output=True,
                       text=True, cwd=ROOT, timeout=1800)
    tail = [ln for ln in r.stdout.split('\n') if 'passed,' in ln]
    if r.returncode != 0:
        bad = [ln for ln in r.stdout.split('\n') if 'FAIL' in ln][:6]
        raise SystemExit('MREG: %s fails:\n   %s'
                         % (name, '\n   '.join(bad or [r.stderr[-400:]])))
    print('  %-28s%s' % (name, tail[-1] if tail else ' rc 0'))

print('-' * 74)
print('  Two pages, two rounds, two suites. The last two of the eight.')
print('=' * 74)
