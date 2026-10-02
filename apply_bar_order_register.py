# -*- coding: utf-8 -*-
"""A-BAR, PART 2 - REGISTER THE ROUND.

Three entries, in three files, each of which a suite checks:

    alv_rounds.ROUNDS          '.bak_barorder', last - the list is
                               append-only, and as_left_by() walks it
                               forward, so position is meaning.
    Push-PendingChanges.ps1    'test_bar_order.py' in $suites.
    Push-PendingChanges.ps1    four sentinel rows, one per page touched.

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
SUFFIX = '.bak_barorder'
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
            raise SystemExit('ABAR2: %s is not a byte copy' % bak)


def swap(text, old, new, what, crlf):
    o, n = old.replace('\r\n', '\n'), new.replace('\r\n', '\n')
    if crlf:
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('ABAR2: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('A-BAR PART 2 - REGISTRATION%s' % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 1. alv_rounds.ROUNDS
# ==========================================================================
P = os.path.join(ROOT, 'alv_rounds.py')
t, raw, crlf = read(P)
if "'.bak_barorder'," in t:
    print('  alv_rounds.py            already lists .bak_barorder')
else:
    t = swap(t, "    '.bak_issuestats',\n]",
             "    '.bak_issuestats',\n    '.bak_barorder',\n]",
             'the end of ROUNDS', crlf)
    if not CHECK:
        back_up(P, raw)
        write(P, t, crlf)
    print('  alv_rounds.py            .bak_barorder appended to ROUNDS')

# ==========================================================================
# 2. $suites
# ==========================================================================
PS = os.path.join(ROOT, 'Push-PendingChanges.ps1')
t, raw, crlf = read(PS)
NEW_SUITE = """    # The ORDER of the action bar - primary, secondaries, filter,
    # Back - asserted for the first time, across all 123 bars and all
    # 142 variants their {% if %} branches can render. Its section 4
    # draws the three moved bars in Chromium and reads the controls
    # back BY THEIR x POSITION, because base lays the bar out with
    # flex and flex has four ways to disagree with the markup.
    'test_bar_order.py'
)"""
if "'test_bar_order.py'" in t:
    print('  Push-PendingChanges.ps1  already lists test_bar_order.py')
else:
    t = swap(t, "    'test_issue_stats.py'\n)",
             "    'test_issue_stats.py'\n" + NEW_SUITE,
             'the end of $suites', crlf)
    if not CHECK:
        back_up(PS, raw)
        write(PS, t, crlf)
    print('  Push-PendingChanges.ps1  test_bar_order.py appended to $suites')

# ==========================================================================
# 3. THE SENTINELS. One per page, each naming a string that exists only
#    because this round ran - so a tree that has lost the round fails the
#    gate BEFORE any suite is started.
#
#    Text is single-quoted PowerShell, and a sentinel whose text contains
#    an apostrophe has to double it. None of these do; they are chosen so
#    none has to.
# ==========================================================================
ROWS = """    @{ File = 'pages\\templates\\physical_invoice_list.html'; Text = 'Desktop: [New Customer Invoice] [Help]'; What = 'A-BAR: Help sits BEHIND the primary on Physical Invoices' },
    @{ File = 'pages\\templates\\view_meal_plan.html'; Text = 'A-BAR, 2 Oct 2026. Back used to come FIRST here'; What = 'A-BAR: Back sits at the END of the bar on View Meal Plan' },
    @{ File = 'pages\\templates\\properties_edit.html'; Text = 'A-BAR, 2 Oct 2026. Assets came before Save'; What = 'A-BAR: Save sits ahead of Assets on the property edit form' },
    @{ File = 'pages\\templates\\celebration_calendar.html'; Text = 'class="btn btn-info"'; Absent = $true; Code = $true; What = 'A-BAR: the Calendar/Timeline toggle is no longer Bootstrap btn-info' },
"""
t, raw, crlf = read(PS)
if 'A-BAR: Help sits BEHIND the primary' in t:
    print('  Push-PendingChanges.ps1  already carries the 4 A-BAR sentinels')
else:
    m = re.search(r'(?m)^(\s*)\$sentinels = @\(\n', t)
    if not m:
        raise SystemExit('ABAR2: no $sentinels table found')
    t = t[:m.end()] + ROWS + t[m.end():]
    if not CHECK:
        back_up(PS, raw)
        write(PS, t, crlf)
    print('  Push-PendingChanges.ps1  4 A-BAR sentinel rows added')

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

if "'.bak_barorder'" not in rounds:
    raise SystemExit('ABAR2: .bak_barorder is not in ROUNDS')
order = re.findall(r"'(\.bak_[a-z0-9]+)'", rounds)
if order[-1] != '.bak_barorder':
    raise SystemExit('ABAR2: .bak_barorder is not LAST in ROUNDS - %s'
                     % order[-3:])
print('  ROUNDS ends with .bak_barorder, after .bak_issuestats')

suites = re.findall(r"'(test_[a-z0-9_]+\.py)'", t)
if 'test_bar_order.py' not in suites:
    raise SystemExit('ABAR2: test_bar_order.py is not in $suites')
if len(suites) != len(set(suites)):
    dup = sorted(s for s in set(suites) if suites.count(s) > 1)
    raise SystemExit('ABAR2: $suites lists a suite twice: %s' % dup)
print('  $suites lists %d suites, test_bar_order.py at %d, none twice'
      % (len(suites), suites.index('test_bar_order.py') + 1))

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
    raise SystemExit('ABAR2: the push gate has %d sentinel rows, parsed %d'
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
    raise SystemExit('ABAR2: %d sentinel(s) do not resolve:\n   %s'
                     % (len(stale), '\n   '.join(stale[:6])))
print('  all %d sentinels resolve, the 4 new ones included' % len(rows))

# AND THE FOUR NEW ONES REALLY WOULD FIRE. A sentinel that passes on a tree
# that has lost the round is a sentinel that checks nothing - so each is
# tested against the BACKUP, where the round has not happened yet, and must
# come out the other way.
import importlib
spec = None
blind = []
for r in rows:
    if not str(r.get('What', '')).startswith('A-BAR:'):
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
    raise SystemExit('ABAR2: %d sentinel(s) that check nothing:\n   %s'
                     % (len(blind), '\n   '.join(blind)))
print('  and all 4 of them FAIL against the backups, which is the point')

print('-' * 74)
print('=' * 74)
