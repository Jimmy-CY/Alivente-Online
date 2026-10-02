# -*- coding: utf-8 -*-
"""ML-1, PART 2 - REGISTER THE ROUND.

Three entries, in three files, each of which a suite checks:

    alv_rounds.ROUNDS          '.bak_mealrow', last - the list is
                               append-only, and as_left_by() walks it
                               forward, so position is meaning.
    Push-PendingChanges.ps1    'test_meal_row.py' in $suites.
    Push-PendingChanges.ps1    three sentinel rows, two of them ABSENT.

THE ABSENT SENTINEL IS THE ONE WORTH HAVING. It looks for the shape this
round removed from the Favourites link - a Django tag choosing between two
Bootstrap colours - and if it comes back, the push stops before a single
suite runs.

THE GUARD IS ON WHAT THE ENTRY ADDS, NOT ON THE ANCHOR IT IS ADDED AFTER.
apply_tabs.py derived its guard from the anchor text - new.split("'")[1]
handed it 'test_tabs.py', which was already in the file - so the patcher
declared itself done before it had written anything. Each block below
tests for a string that exists ONLY once this round has run.

Backups: .bak_barorder, same suffix as part 1, so as_left_by() sees one
round and not two.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_mealrow'
ROOT = os.getcwd()


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    return raw.decode('utf-8'), raw, (b'\r\n' in raw)


def write(path, text, crlf):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n') if crlf
            else data.replace(b'\r\n', b'\n'))
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
            raise SystemExit('ML1REG: %s is not a byte copy' % bak)


def swap(text, old, new, what, crlf):
    o, n = old.replace('\r\n', '\n'), new.replace('\r\n', '\n')
    if crlf:
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('ML1REG: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('ML-1 PART 2 - REGISTRATION%s' % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 1. alv_rounds.ROUNDS
# ==========================================================================
P = os.path.join(ROOT, 'alv_rounds.py')
t, raw, crlf = read(P)
if "'.bak_mealrow'," in t:
    print('  alv_rounds.py            already lists .bak_mealrow')
else:
    t = swap(t, "    '.bak_sentinels',\n]",
             "    '.bak_sentinels',\n    '.bak_mealrow',\n]",
             'the end of ROUNDS', crlf)
    if not CHECK:
        back_up(P, raw)
        write(P, t, crlf)
    print('  alv_rounds.py            .bak_mealrow appended to ROUNDS')

# ==========================================================================
# 2. $suites
# ==========================================================================
PS = os.path.join(ROOT, 'Push-PendingChanges.ps1')
t, raw, crlf = read(PS)
NEW_SUITE = """    # The Meal Plans row, onto base's row-action strip. Its section
    # 2 draws the five controls against a PLAIN base page and against
    # the page's own CSS, and demands they come out identical - a page
    # that merely looks similar is a page that copied the component
    # again. 54 local rules fell to 43 and 24 literals to 13.
    'test_meal_row.py'
)"""
if "'test_meal_row.py'" in t:
    print('  Push-PendingChanges.ps1  already lists test_meal_row.py')
else:
    t = swap(t, "    'test_sentinels.py'\n)",
             "    'test_sentinels.py'\n" + NEW_SUITE,
             'the end of $suites', crlf)
    if not CHECK:
        back_up(PS, raw)
        write(PS, t, crlf)
    print('  Push-PendingChanges.ps1  test_meal_row.py appended to $suites')

# ==========================================================================
# 3. THE SENTINELS. One per page, each naming a string that exists only
#    because this round ran - so a tree that has lost the round fails the
#    gate BEFORE any suite is started.
#
#    Text is single-quoted PowerShell, and a sentinel whose text contains
#    an apostrophe has to double it. None of these do; they are chosen so
#    none has to.
# ==========================================================================
ROWS = """    @{ File = 'pages\\templates\\meal_plans.html'; Text = 'icon-action-btn icon-view'; What = 'ML-1: the row is on the house action strip' },
    @{ File = 'pages\\templates\\base.html'; Text = '.icon-list       { color: var(--alv-view)'; What = 'ML-1: base carries the shopping-list NAME on the view colour' },
    @{ File = 'pages\\templates\\meal_plans.html'; Text = 'onclick="confirmDelete('; Absent = $true; Code = $true; What = 'ML-1: the plan name is not written into a handler' },
"""
t, raw, crlf = read(PS)
if 'ML-1: the row is on the house action strip' in t:
    print('  Push-PendingChanges.ps1  already carries the 3 ML-1 sentinels')
else:
    m = re.search(r'(?m)^(\s*)\$sentinels = @\(\n', t)
    if not m:
        raise SystemExit('ML1REG: no $sentinels table found')
    t = t[:m.end()] + ROWS + t[m.end():]
    if not CHECK:
        back_up(PS, raw)
        write(PS, t, crlf)
    print('  Push-PendingChanges.ps1  3 ML-1 sentinel rows added')

print('-' * 74)

if CHECK:
    print('  --check: nothing written')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
t = read(PS)[0]
rounds = read(P)[0]

if "'.bak_mealrow'" not in rounds:
    raise SystemExit('ML1REG: .bak_mealrow is not in ROUNDS')
order = re.findall(r"'(\.bak_[a-z0-9]+)'", rounds)
if order[-1] != '.bak_mealrow':
    raise SystemExit('ML1REG: .bak_mealrow is not LAST in ROUNDS - %s'
                     % order[-3:])
print('  ROUNDS ends with .bak_mealrow, after .bak_sentinels')

suites = re.findall(r"'(test_[a-z0-9_]+\.py)'", t)
if 'test_meal_row.py' not in suites:
    raise SystemExit('ML1REG: test_meal_row.py is not in $suites')
if len(suites) != len(set(suites)):
    dup = sorted(s for s in set(suites) if suites.count(s) > 1)
    raise SystemExit('ML1REG: $suites lists a suite twice: %s' % dup)
print('  $suites lists %d suites, test_meal_row.py at %d, none twice'
      % (len(suites), suites.index('test_meal_row.py') + 1))

# EVERY SENTINEL RESOLVES - including the four this script just wrote. The
# reader is line-based and field-by-field, and it COUNTS BOTH WAYS,
# because the first version of it parsed 183 of 195 and reported a clean
# census: it could not see a double-quoted Text, nor an Absent that came
# after What.
_Q = r"'((?:[^']|'')*)'|\"((?:[^\"]|\"\")*)\""
SF = re.compile(r"\b(File|Text|What)\s*=\s*(?:%s)" % _Q)
SG = re.compile(r"\b(Absent|Code)\s*=\s*\$(true|false)")
rows = []
for line in t.split('\n'):
    if '@{' not in line or 'File' not in line:
        continue
    f = {}
    for k, sq, dq in SF.findall(line):
        f[k] = sq.replace("''", "'") if sq else dq.replace('""', '"')
    for k, v in SG.findall(line):
        f[k] = (v == 'true')
    if 'File' in f and 'Text' in f:
        rows.append(f)
rawrows = len(re.findall(r'@\{ *File *=', t))
if len(rows) != rawrows:
    raise SystemExit('ML1REG: the push gate has %d sentinel rows, parsed %d'
                     % (rawrows, len(rows)))


def strip(x):
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
    b = read(p)[0]
    if r.get('Code'):
        b = strip(b)
    if (r['Text'].lower() in b.lower()) != (not r.get('Absent')):
        stale.append('%s %s %r' % (r['File'],
                                   'NOT FOUND' if not r.get('Absent')
                                   else 'IS BACK', r['Text'][:50]))
if stale:
    raise SystemExit('ML1REG: %d sentinel(s) do not resolve:\n   %s'
                     % (len(stale), '\n   '.join(stale[:6])))
print('  all %d sentinels resolve, the 3 new ones included' % len(rows))

# AND THE FOUR NEW ONES REALLY WOULD FIRE. A sentinel that passes on a tree
# that has lost the round is a sentinel that checks nothing - so each is
# tested against the BACKUP, where the round has not happened yet, and must
# come out the other way.
import importlib
spec = None
blind = []
for r in rows:
    if not str(r.get('What', '')).startswith('ML-1:'):
        continue
    p = os.path.join(ROOT, *r['File'].replace('\\', '/').split('/'))
    bak = p + SUFFIX
    if not os.path.isfile(bak):
        blind.append('%s has no %s backup to test against' % (r['File'],
                                                              SUFFIX))
        continue
    b = read(bak)[0]
    if r.get('Code'):
        b = strip(b)
    if (r['Text'].lower() in b.lower()) == (not r.get('Absent')):
        blind.append('%s would have passed BEFORE the round: %r'
                     % (r['File'], r['Text'][:46]))
if blind:
    raise SystemExit('ML1REG: %d sentinel(s) that check nothing:\n   %s'
                     % (len(blind), '\n   '.join(blind)))
print('  and all 3 of them FAIL against the backups, which is the point')

print('-' * 74)
print('=' * 74)
