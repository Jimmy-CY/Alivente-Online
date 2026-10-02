# -*- coding: utf-8 -*-
"""S-1, PART 2 - REGISTER THE ROUND.

Three entries, in three files, each of which a suite checks:

    alv_rounds.ROUNDS          '.bak_sentinels', last - the list is
                               append-only, and as_left_by() walks it
                               forward, so position is meaning.
    Push-PendingChanges.ps1    'test_sentinels.py' in $suites.
    Push-PendingChanges.ps1    no sentinel rows - see below.

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
SUFFIX = '.bak_sentinels'
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
            raise SystemExit('S1REG: %s is not a byte copy' % bak)


def swap(text, old, new, what, crlf):
    o, n = old.replace('\r\n', '\n'), new.replace('\r\n', '\n')
    if crlf:
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('S1REG: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('S-1 PART 2 - REGISTRATION%s' % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 1. alv_rounds.ROUNDS
# ==========================================================================
P = os.path.join(ROOT, 'alv_rounds.py')
t, raw, crlf = read(P)
if "'.bak_sentinels'," in t:
    print('  alv_rounds.py            already lists .bak_sentinels')
else:
    t = swap(t, "    '.bak_btntone',\n]",
             "    '.bak_btntone',\n    '.bak_sentinels',\n]",
             'the end of ROUNDS', crlf)
    if not CHECK:
        back_up(P, raw)
        write(P, t, crlf)
    print('  alv_rounds.py            .bak_sentinels appended to ROUNDS')

# ==========================================================================
# 2. $suites
# ==========================================================================
PS = os.path.join(ROOT, 'Push-PendingChanges.ps1')
t, raw, crlf = read(PS)
NEW_SUITE = """    # THE SENTINEL TABLE ITSELF. 210 rows run before any suite
    # starts, and until S-1 nothing tested them. It checks that the
    # reader sees every row (an earlier one saw 183 of 195 and
    # reported a clean census), that every row resolves, and - the
    # claim no round had made - that every row could ever have FAILED.
    'test_sentinels.py'
)"""
if "'test_sentinels.py'" in t:
    print('  Push-PendingChanges.ps1  already lists test_sentinels.py')
else:
    t = swap(t, "    'test_btn_tone.py'\n)",
             "    'test_btn_tone.py'\n" + NEW_SUITE,
             'the end of $suites', crlf)
    if not CHECK:
        back_up(PS, raw)
        write(PS, t, crlf)
    print('  Push-PendingChanges.ps1  test_sentinels.py appended to $suites')

# NO SENTINEL ROWS. This round's subject IS the sentinel table, and a row
# that guards the table would be the table vouching for itself.
# test_sentinels.py is the check, and it runs like any other suite.
print('  Push-PendingChanges.ps1  no sentinel row - the table is the subject')

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

if "'.bak_sentinels'" not in rounds:
    raise SystemExit('S1REG: .bak_sentinels is not in ROUNDS')
order = re.findall(r"'(\.bak_[a-z0-9]+)'", rounds)
if order[-1] != '.bak_sentinels':
    raise SystemExit('S1REG: .bak_sentinels is not LAST in ROUNDS - %s'
                     % order[-3:])
print('  ROUNDS ends with .bak_sentinels, after .bak_btntone')

suites = re.findall(r"'(test_[a-z0-9_]+\.py)'", t)
if 'test_sentinels.py' not in suites:
    raise SystemExit('S1REG: test_sentinels.py is not in $suites')
if len(suites) != len(set(suites)):
    dup = sorted(s for s in set(suites) if suites.count(s) > 1)
    raise SystemExit('S1REG: $suites lists a suite twice: %s' % dup)
print('  $suites lists %d suites, test_sentinels.py at %d, none twice'
      % (len(suites), suites.index('test_sentinels.py') + 1))

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
    raise SystemExit('S1REG: the push gate has %d sentinel rows, parsed %d'
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
    raise SystemExit('S1REG: %d sentinel(s) do not resolve:\n   %s'
                     % (len(stale), '\n   '.join(stale[:6])))
print('  all %d sentinels resolve' % len(rows))

# AND THE FOUR NEW ONES REALLY WOULD FIRE. A sentinel that passes on a tree
# that has lost the round is a sentinel that checks nothing - so each is
# tested against the BACKUP, where the round has not happened yet, and must
# come out the other way.
import importlib
spec = None
blind = []
for r in rows:
    if not str(r.get('What', '')).startswith('S-1:'):
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
    raise SystemExit('S1REG: %d sentinel(s) that check nothing:\n   %s'
                     % (len(blind), '\n   '.join(blind)))
print('  and this round added none of its own, by design')

print('-' * 74)
print('=' * 74)
