# -*- coding: utf-8 -*-
"""SECTION S, ROUND S-1 - THE TABLE THAT RUNS BEFORE EVERY SUITE

Push-PendingChanges.ps1 carries 210 sentinel rows and checks every one of
them BEFORE it starts a single suite. Nothing has ever tested the table.

F3 is what that costs: a round renamed `{% for prop in all_props %}`, all
210 suites passed, the sweep was clean, and the push stopped dead on a
sentinel nobody had updated. A clean sweep is not a clean push, and the
thing standing between them had no suite of its own.

test_sentinels.py is that suite. Writing it found four faults in the table
it was written to guard, and this patcher fixes them.

==========================================================================
1. A DUPLICATE ROW
==========================================================================
    line 216  base.html  'overflow: clip;'  'and the container lets them'
    line 229  base.html  'overflow: clip;'  'a card cannot trap a sticky heading'

Two rows, two different facts, ONE string - and base says `overflow: clip;`
exactly twice, once on .table-container and once on .alv-card. So each row
was half-checking both rules: delete either declaration and both sentinels
still pass on the survivor.

Each row gets the string that belongs to IT. Not the bare declaration but
the declaration plus the comment line that names which element it is on,
because that is the only text in the file that distinguishes them.

==========================================================================
2. AND TWO ROWS THAT COULD NOT FAIL
==========================================================================
    'pointer-events: none'        base says it 2 times
    'display: none !important'    base says it 10 times

A sentinel is a string that should be there. If the string is there ten
times, deleting the rule it guards leaves nine - so the row passes, the
push goes ahead, and the fault ships. Checked against all 89 backups of
base.html that this repo holds: neither has EVER been absent, which is
another way of saying neither has ever checked anything.

    'pointer-events: none'      guards .disabled-btn, where base's own note
                                says "without it a disabled anchor is still
                                a working link"
    'display: none !important'  guards the print block that hides the row
                                actions

Both get a string that occurs once and that names the rule.

==========================================================================
3. WHAT IS LEFT, NAMED RATHER THAN FIXED
==========================================================================
Four rows still never discriminate against any state this repo holds:

    tenant_payment_days.html  'pd-detail-table'                  8 versions
    administration.py         'can_access_administration -> ...'  1 version
    receipts.py               'def cash_receipt_commit'           2 versions
    finance_pl_act.html       'showInvoiceModalLikeExisting('    24 versions

These are not weak in the way the two above were - each occurs exactly
once and names the thing it guards. They have simply never been absent,
because no round has ever removed them. That is what a sentinel guarding
against a FUTURE deletion looks like, and it is correct.

So they are pinned by name in the suite rather than fixed, with the count
of backups each was tried against - and if a fifth appears, the suite says
so on the day it is written.

Backups: .bak_sentinels. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_sentinels'
ROOT = os.getcwd()
PS = os.path.join(ROOT, 'Push-PendingChanges.ps1')


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
            raise SystemExit('S1: %s is not a byte copy' % bak)


def swap(text, old, new, what, crlf):
    o, n = old.replace('\r\n', '\n'), new.replace('\r\n', '\n')
    if crlf:
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('S1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('SECTION S, ROUND S-1 - THE SENTINEL TABLE%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw, crlf = read(PS)

# The four rows, replaced with strings that occur ONCE in the file they
# name and that say which rule they are standing on.
FIXES = [
    ("""    @{ File = 'pages\\templates\\base.html';                Text = 'overflow: clip;';             What = 'and the container lets them' },""",
     """    @{ File = 'pages\\templates\\base.html';                Text = 'and at top:0 with clip'; What = 'the TABLE container clips rather than hides, so a sticky heading has something to stick to' },""",
     'the first overflow:clip row'),
    ("""    @{ File = 'pages\\templates\\base.html';                Text = 'overflow: clip;';                What = 'a card cannot trap a sticky heading' },""",
     """    @{ File = 'pages\\templates\\base.html';                Text = 'so a sticky heading inside a card has nothing'; What = 'the CARD clips rather than hides, same fault and same fix as the table container' },""",
     'the second overflow:clip row'),
    ("""    @{ File = 'pages\\templates\\base.html';                Text = 'pointer-events: none';            What = 'a disabled button is not a live link' },""",
     """    @{ File = 'pages\\templates\\base.html';                Text = 'still a working link'; What = 'a disabled button is not a live link - base says pointer-events twice, so the row names THIS one' },""",
     'the pointer-events row'),
    ("""    @{ File = 'pages\\templates\\base.html';                Text = 'display: none !important';        What = 'paper stops printing the furniture' },""",
     """    @{ File = 'pages\\templates\\base.html';                Text = '.no-print { display: none !important; }'; What = 'paper stops printing the furniture - base says that declaration ten times, so the row names the rule' },""",
     'the print row'),
]

if 'base says pointer-events twice' in t:
    print('  Push-PendingChanges.ps1  already strengthened')
else:
    for old, new, what in FIXES:
        t = swap(t, old, new, what, crlf)
    if not CHECK:
        back_up(PS, raw)
        write(PS, t, crlf)
    print('  Push-PendingChanges.ps1  4 rows strengthened - 1 duplicate '
          'split, 2 that could not fail, 1 that named the wrong rule')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
t = read(PS)[0]
_Q = r"'((?:[^']|'')*)'|\"((?:[^\"]|\"\")*)\""
FIELD = re.compile(r"\b(File|Text|What)\s*=\s*(?:%s)" % _Q)
FLAG = re.compile(r"\b(Absent|Code)\s*=\s*\$(true|false)")


def parse(ps_text):
    rows = []
    for n, line in enumerate(ps_text.split('\n'), 1):
        if '@{' not in line or 'File' not in line:
            continue
        f = {'_line': n}
        for k, sq, dq in FIELD.findall(line):
            f[k] = sq.replace("''", "'") if sq else dq.replace('""', '"')
        for k, v in FLAG.findall(line):
            f[k] = (v == 'true')
        if 'File' in f and 'Text' in f:
            rows.append(f)
    return rows


rows = parse(t)
rawrows = len(re.findall(r'@\{ *File *=', t))
if len(rows) != rawrows:
    raise SystemExit('S1: %d raw rows, parsed %d' % (rawrows, len(rows)))
was = parse(read(PS + SUFFIX)[0])
if len(rows) != len(was):
    raise SystemExit('S1: the table had %d rows and now has %d - this round '
                     'rewrites four, it adds and removes none'
                     % (len(was), len(rows)))
print('  the table still has %d rows, all parsed' % len(rows))

# NO DUPLICATES.
seen, dup = {}, []
for r in rows:
    k = (r['File'].lower(), r['Text'].lower(), bool(r.get('Absent')),
         bool(r.get('Code')))
    if k in seen:
        dup.append('lines %d and %d  %r' % (seen[k], r['_line'],
                                            r['Text'][:40]))
    seen[k] = r['_line']
if dup:
    raise SystemExit('S1: %d duplicate row(s) remain:\n   %s'
                     % (len(dup), '\n   '.join(dup)))
d_was = len(was) - len({(r['File'].lower(), r['Text'].lower(),
                         bool(r.get('Absent')), bool(r.get('Code')))
                        for r in was})
print('  and no two are the same (%d duplicate(s) before)' % d_was)

# EVERY ROW STILL RESOLVES.
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
        stale.append('line %d %s %r' % (r['_line'], r['File'], r['Text'][:44]))
if stale:
    raise SystemExit('S1: %d row(s) no longer resolve:\n   %s'
                     % (len(stale), '\n   '.join(stale[:6])))
print('  every one of them resolves against the tree')

# AND THE FOUR NEW STRINGS OCCUR EXACTLY ONCE IN THE FILE THEY NAME, which
# is the whole point of rewriting them.
base = read(os.path.join(ROOT, 'pages', 'templates', 'base.html'))[0]
for _old, new, what in FIXES:
    m = FIELD.findall(new)
    text = [sq.replace("''", "'") if sq else dq.replace('""', '"')
            for k, sq, dq in m if k == 'Text'][0]
    n = base.lower().count(text.lower())
    if n != 1:
        raise SystemExit('S1: %r occurs %d times in base.html, not once - '
                         'that is the fault this round was fixing'
                         % (text[:46], n))
    print('      %-48s occurs once' % (repr(text[:46])))

# AND EACH OF THE FOUR WOULD NOW HAVE FAILED AGAINST SOME VERSION OF base.
folder = os.path.join(ROOT, 'pages', 'templates')
baks = [os.path.join(folder, n) for n in os.listdir(folder)
        if n.startswith('base.html.bak_')]
blind = []
for _old, new, what in FIXES:
    text = [sq.replace("''", "'") if sq else dq.replace('""', '"')
            for k, sq, dq in FIELD.findall(new) if k == 'Text'][0]
    if all(text.lower() in read(b)[0].lower() for b in baks):
        blind.append('%r still passes against all %d versions of base'
                     % (text[:44], len(baks)))
if blind:
    print('  NOTE: %d of the four has never been absent in %d backups:'
          % (len(blind), len(baks)))
    for b in blind:
        print('      %s' % b)
else:
    print('  and each of the four comes out the other way in at least one '
          'of the %d base backups' % len(baks))

print('-' * 74)
print('=' * 74)
