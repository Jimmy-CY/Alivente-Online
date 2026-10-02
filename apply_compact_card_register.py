# -*- coding: utf-8 -*-
"""C-1, PART 2 - REGISTER THE ROUND.

Three entries, in three files, each of which a suite checks:

    alv_rounds.ROUNDS          '.bak_compactcard', last - the list is
                               append-only, and as_left_by() walks it
                               forward, so position is meaning.
    Push-PendingChanges.ps1    'test_compact_card.py' in $suites.
    Push-PendingChanges.ps1    three sentinel rows.

THE THIRD SENTINEL IS THE ONE WORTH HAVING. It is an ABSENT check for the
string `}In compact`, the stray close-comment that killed two rules on this
page for a week. If anything ever puts it back - or writes another like it -
the push stops before a single suite runs.

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
SUFFIX = '.bak_compactcard'
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
            raise SystemExit('C1REG: %s is not a byte copy' % bak)


def swap(text, old, new, what, crlf):
    o, n = old.replace('\r\n', '\n'), new.replace('\r\n', '\n')
    if crlf:
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('C1REG: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('C-1 PART 2 - REGISTRATION%s' % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 1. alv_rounds.ROUNDS
# ==========================================================================
P = os.path.join(ROOT, 'alv_rounds.py')
t, raw, crlf = read(P)
if "'.bak_compactcard'," in t:
    print('  alv_rounds.py            already lists .bak_compactcard')
else:
    t = swap(t, "    '.bak_barorder',\n]",
             "    '.bak_barorder',\n    '.bak_compactcard',\n]",
             'the end of ROUNDS', crlf)
    if not CHECK:
        back_up(P, raw)
        write(P, t, crlf)
    print('  alv_rounds.py            .bak_compactcard appended to ROUNDS')

# ==========================================================================
# 2. $suites
# ==========================================================================
PS = os.path.join(ROOT, 'Push-PendingChanges.ps1')
t, raw, crlf = read(PS)
NEW_SUITE = """    # The compact contact card - one line a name, no icon and no
    # pill until the card is opened. Its section 2 draws the cards at
    # three column counts and reads the name\'s TRUE text width with a
    # Range, because a clipped flex item lies about its own width. Its
    # section 3 is the one no suite had: CSS comments must balance,
    # tree-wide - two rules on that page had been discarded by the
    # parser since 25 Sep while the braces balanced perfectly.
    'test_compact_card.py'
)"""
if "'test_compact_card.py'" in t:
    print('  Push-PendingChanges.ps1  already lists test_compact_card.py')
else:
    t = swap(t, "    'test_bar_order.py'\n)",
             "    'test_bar_order.py'\n" + NEW_SUITE,
             'the end of $suites', crlf)
    if not CHECK:
        back_up(PS, raw)
        write(PS, t, crlf)
    print('  Push-PendingChanges.ps1  test_compact_card.py appended to '
          '$suites')

# ==========================================================================
# 3. THE SENTINELS. One per page, each naming a string that exists only
#    because this round ran - so a tree that has lost the round fails the
#    gate BEFORE any suite is started.
#
#    Text is single-quoted PowerShell, and a sentinel whose text contains
#    an apostrophe has to double it. None of these do; they are chosen so
#    none has to.
# ==========================================================================
ROWS = """    @{ File = 'pages\\templates\\celebration_management.html'; Text = 'span class="contact-name"'; What = 'C-1: the contact name has a span of its own' },
    @{ File = 'pages\\templates\\celebration_management.html'; Text = 'THE COLLAPSED COMPACT CARD IS A LIST ROW'; What = 'C-1: the compact card rules are on the page' },
    @{ File = 'pages\\templates\\celebration_management.html'; Text = '}In compact'; Absent = $true; What = 'C-1: the stray close-comment that killed two rules has not come back' },
"""
t, raw, crlf = read(PS)
if 'C-1: the contact name has a span of its own' in t:
    print('  Push-PendingChanges.ps1  already carries the 3 C-1 sentinels')
else:
    m = re.search(r'(?m)^(\s*)\$sentinels = @\(\n', t)
    if not m:
        raise SystemExit('C1REG: no $sentinels table found')
    t = t[:m.end()] + ROWS + t[m.end():]
    if not CHECK:
        back_up(PS, raw)
        write(PS, t, crlf)
    print('  Push-PendingChanges.ps1  3 C-1 sentinel rows added')

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

if "'.bak_compactcard'" not in rounds:
    raise SystemExit('C1REG: .bak_compactcard is not in ROUNDS')
order = re.findall(r"'(\.bak_[a-z0-9]+)'", rounds)
if order[-1] != '.bak_compactcard':
    raise SystemExit('C1REG: .bak_compactcard is not LAST in ROUNDS - %s'
                     % order[-3:])
print('  ROUNDS ends with .bak_compactcard, after .bak_barorder')

suites = re.findall(r"'(test_[a-z0-9_]+\.py)'", t)
if 'test_compact_card.py' not in suites:
    raise SystemExit('C1REG: test_compact_card.py is not in $suites')
if len(suites) != len(set(suites)):
    dup = sorted(s for s in set(suites) if suites.count(s) > 1)
    raise SystemExit('C1REG: $suites lists a suite twice: %s' % dup)
print('  $suites lists %d suites, test_compact_card.py at %d, none twice'
      % (len(suites), suites.index('test_compact_card.py') + 1))

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
    raise SystemExit('C1REG: the push gate has %d sentinel rows, parsed %d'
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
    raise SystemExit('C1REG: %d sentinel(s) do not resolve:\n   %s'
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
    if not str(r.get('What', '')).startswith('C-1:'):
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
    raise SystemExit('C1REG: %d sentinel(s) that check nothing:\n   %s'
                     % (len(blind), '\n   '.join(blind)))
print('  and all 3 of them FAIL against the backups, which is the point')

print('-' * 74)
print('=' * 74)
