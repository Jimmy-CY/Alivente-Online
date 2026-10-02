# -*- coding: utf-8 -*-
"""test_sentinels.py - Section S round S-1, 2 Oct 2026.

Push-PendingChanges.ps1 carries a table of sentinel rows - a file, a string,
and whether that string should be present or absent - and it checks EVERY
ONE OF THEM BEFORE IT STARTS A SINGLE SUITE. Nothing has ever tested the
table itself.

F3 is what that costs. A round renamed `{% for prop in all_props %}`, every
one of 210 suites passed, the sweep was clean, and the push stopped dead on
a sentinel nobody had updated. A clean sweep is not a clean push, and the
thing standing between them had no suite.

Since then the sentinel check has been COPY-PASTED into the tail of every
round suite - six of them now carry their own private copy of the same
reader. That is better than nothing and it is not a test of the table; it
is six chances to write the reader slightly differently.

WHAT THIS SUITE ASSERTS

  1. THE READER SEES EVERY ROW. It counts the parsed rows against the raw
     `@{ File =` lines and fails if they disagree. The first version of
     this reader parsed 183 of 195 and reported a clean census, because it
     could not see a double-quoted Text nor an Absent that came after What
     - and I told Demetri all 195 had been checked and had to correct it.

  2. AND THE READER IS ITSELF TESTED, against a fixture carrying the exact
     three shapes that defeated it: a double-quoted Text, a flag after
     What, and a doubled apostrophe inside a single-quoted string. These
     are CONTROLS - they must parse, and a deliberately broken row in the
     same fixture must NOT.

  3. EVERY ROW RESOLVES. Present means present, absent means absent, and
     the named file exists.

  4. EVERY ROW IS DISCRIMINATING, which is the claim no round has made.
     A sentinel that would pass whatever the tree looked like checks
     nothing. For each row this suite finds the oldest backup of its file
     and asks whether the sentinel would have come out the OTHER WAY there.
     A row that reads the same in every version of its file is reported by
     name. Files with no backup at all are counted and named, not failed -
     a file no round has touched has nothing to compare against, and that
     is a fact about the file rather than a fault in the row.

  5. NO ROW IS A DUPLICATE, and no suite is listed twice.

WHAT THIS SUITE DOES NOT DO. It does not require a sentinel per round, and
it does not judge whether a row is a GOOD choice of string. It judges that
the row is read, that it resolves, and that it could ever have failed.
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
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _goto(pg, path):
    try:
        pg.goto('file://' + path)
    except Exception as e:
        print('  !! the browser could not open %s: %s' % (path, e))
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)

ME = 'test_sentinels.py'
PS1 = 'Push-PendingChanges.ps1'

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
            for line in str(detail).split('\n')[:10]:
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


# ==========================================================================
# THE READER. Line-based and field-by-field, because PowerShell's hashtable
# literal is not a thing a single regex reads correctly: Text may be single-
# or double-quoted, a single-quoted string doubles its own apostrophes, and
# the Absent and Code flags may appear before OR after What.
# ==========================================================================
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


def strip_comments(t):
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'\{#.*?#\}', '', t, flags=re.S)
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    t = re.sub(r'(?m)^\s*//.*$', '', t)
    return re.sub(r'(?m)^\s*#.*$', '', t)


def holds(row, text):
    """Does this row's claim hold against `text`?"""
    if row.get('Code'):
        text = strip_comments(text)
    return (row['Text'].lower() in text.lower()) == (not row.get('Absent'))


PS = os.path.join(ROOT, PS1)
PS_TEXT = read(PS)
ROWS = parse(PS_TEXT)
RAW = len(re.findall(r'@\{ *File *=', PS_TEXT))

print('=' * 74)
print('%s - S-1, THE TABLE THAT RUNS BEFORE EVERY SUITE' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE READER SEES EVERY ROW')
# ==========================================================================
ok(RAW > 150, 'the table is there - %d raw rows' % RAW, RAW)
ok(len(ROWS) == RAW,
   'and the reader parses all %d of them' % RAW,
   'parsed %d of %d - the missing ones are at lines %s'
   % (len(ROWS), RAW,
      sorted(set(range(1, PS_TEXT.count('\n') + 1))
             - set(r['_line'] for r in ROWS))[:6] if ROWS else '?'))

dq = [r for r in ROWS if '"' in r['Text']]
flagged = [r for r in ROWS if r.get('Absent') or r.get('Code')]
print('        %d row(s) carry a quote in their text; %d carry a flag.'
      % (len(dq), len(flagged)))

# ==========================================================================
head('2. CONTROL: THE READER, TESTED ON WHAT DEFEATED IT')
# ==========================================================================
# The first version of this reader parsed 183 of 195 and reported a clean
# census. These are the exact three shapes it could not see.
FIXTURE = '''$sentinels = @(
    @{ File = 'a\\b.html'; Text = 'plain single'; What = 'ordinary' },
    @{ File = 'a\\b.html'; Text = "has a ' apostrophe"; What = 'double-quoted Text' },
    @{ File = 'a\\b.html'; Text = 'tail flag'; What = 'flag AFTER What'; Absent = $true },
    @{ File = 'a\\b.html'; Text = 'it''s doubled'; What = 'doubled apostrophe' },
    @{ File = 'a\\b.html'; Text = 'both'; Absent = $true; Code = $true; What = 'flags before What' },
)
'''
fx = parse(FIXTURE)
ok(len(fx) == 5, 'the reader parses all five shapes', len(fx))
by = {r.get('What'): r for r in fx}
ok(by.get('double-quoted Text', {}).get('Text') == "has a ' apostrophe",
   '  a DOUBLE-QUOTED Text containing an apostrophe',
   by.get('double-quoted Text'))
ok(by.get('flag AFTER What', {}).get('Absent') is True,
   '  an Absent flag that comes AFTER What', by.get('flag AFTER What'))
ok(by.get('doubled apostrophe', {}).get('Text') == "it's doubled",
   '  and a doubled apostrophe, unescaped back to one',
   by.get('doubled apostrophe'))
ok(by.get('flags before What', {}).get('Code') is True,
   '  and flags that come before it')

# AND A ROW IT MUST NOT ACCEPT - a control that has to FAIL, not crash.
BROKEN = "    @{ File = 'a\\b.html'; What = 'no Text at all' },\n"
ok(parse(BROKEN) == [],
   'CONTROL: a row with no Text is REFUSED, not guessed at', parse(BROKEN))
ok(parse('    # @{ File = commented out }\n') == [],
   'CONTROL: and a line that is not a row is not read as one')

# ==========================================================================
head('3. EVERY ROW RESOLVES AGAINST THE TREE AS IT STANDS')
# ==========================================================================
missing, stale = [], []
for r in ROWS:
    p = os.path.join(ROOT, *r['File'].replace('\\', '/').split('/'))
    if not os.path.isfile(p):
        missing.append('line %d  %s' % (r['_line'], r['File']))
        continue
    if not holds(r, read(p)):
        stale.append('line %d  %s  %s %r'
                     % (r['_line'], r['File'],
                        'NOT FOUND' if not r.get('Absent') else 'IS BACK',
                        r['Text'][:46]))
ok(not missing, 'every row names a file that exists',
   '\n'.join(missing[:8]))
ok(not stale, 'and every one of the %d claims holds' % len(ROWS),
   '\n'.join(stale[:8]))

# ==========================================================================
head('4. AND EVERY ROW COULD EVER HAVE FAILED')
# ==========================================================================
# THE CLAIM NO ROUND HAS MADE. A sentinel that reads the same whatever the
# tree looks like is a row that checks nothing, and it passes forever.
#
# EVERY backup of the row's file is tried, not just the oldest - and the
# first draft of this check got that wrong in a way worth keeping. It
# compared against the OLDEST backup only, and reported seven rows as
# blind. One of them was C-1's `}In compact` ABSENT sentinel: that string
# did not exist in the oldest backup either, because the stray close-
# comment it guards against only arrived on 25 Sep, halfway through this
# file's history. A claim that holds at the START and holds NOW can still
# have failed in the middle, which is exactly the window a sentinel is for.
#
# So a row is discriminating if ANY version of its file disagrees with it.


def backups_of(path):
    folder, name = os.path.split(path)
    return sorted((os.path.join(folder, n) for n in os.listdir(folder or '.')
                   if n.startswith(name + '.bak_')),
                  key=os.path.getmtime)


blind, nobak = [], []
checked = 0
for r in ROWS:
    p = os.path.join(ROOT, *r['File'].replace('\\', '/').split('/'))
    if not os.path.isfile(p):
        continue
    baks = backups_of(p)
    if not baks:
        nobak.append(r['File'])
        continue
    checked += 1
    if all(holds(r, read(b)) for b in baks):
        blind.append('line %d  %s  %r  (%d version(s) tried)'
                     % (r['_line'], r['File'], r['Text'][:44], len(baks)))
ok(checked > 100,
   '%d row(s) have a backup to be compared against' % checked, checked)
if nobak:
    print('        %d row(s) name a file no round has ever backed up: %s'
          % (len(nobak), ', '.join(sorted(set(nobak))[:4])))
# FOUR ROWS ARE PINNED, NOT FIXED, and the difference matters.
#
# S-1 rewrote four rows that were weak for a demonstrable reason: a
# duplicate pair both standing on `overflow: clip;`, which base says twice,
# so deleting either declaration left both sentinels passing on the
# survivor; and two rows on strings base says 2 and 10 times over, which
# could not have failed however much of the rule was deleted.
#
# THESE FOUR ARE DIFFERENT. Each occurs exactly once in the file it names
# and each names the thing it guards. They have simply never been absent,
# because no round has ever removed them - which is what a sentinel
# guarding against a FUTURE deletion looks like, and is correct. They are
# pinned here so the set cannot quietly grow: a fifth is reported the day
# it is written.
PINNED = {
    'pd-detail-table':
        'the class the payment-days detail table is keyed by - never '
        'removed in the 8 versions of that page this repo holds',
    'can_access_administration -> admin_apms':
        'a permission rename, backed up once',
    'def cash_receipt_commit':
        'the view behind the receipts commit, backed up twice',
    'showInvoiceModalLikeExisting(':
        'the P&L invoice modal entry point, never removed in 24 versions',
}
unpinned = [b for b in blind
            if not any(k.lower() in b.lower() for k in PINNED)]
ok(not unpinned,
   'and the %d that never discriminate are the %d known ones, no more'
   % (len(blind), len(PINNED)), '\n'.join(unpinned[:8]))
for k in sorted(PINNED):
    hit = [b for b in blind if k.lower() in b.lower()]
    ok(bool(hit), '  PINNED  %-42s %s' % (k[:42], PINNED[k][:34]),
       'no longer in the set - has it started discriminating? then unpin it')
ok(len(blind) == len(PINNED),
   '  and the set is exactly %d, not %d' % (len(PINNED), len(blind)),
   '\n'.join(blind[:8]))

# ==========================================================================
head('5. NO ROW IS A DUPLICATE, AND NO SUITE IS LISTED TWICE')
# ==========================================================================
seen = {}
dupes = []
for r in ROWS:
    k = (r['File'].lower(), r['Text'].lower(), bool(r.get('Absent')),
         bool(r.get('Code')))
    if k in seen:
        dupes.append('lines %d and %d  %s  %r'
                     % (seen[k], r['_line'], r['File'], r['Text'][:40]))
    else:
        seen[k] = r['_line']
ok(not dupes, 'all %d rows are distinct' % len(ROWS), '\n'.join(dupes[:6]))

m = re.search(r'\$suites\s*=\s*@\((.*?)^\)', PS_TEXT, re.S | re.M)
ok(bool(m), 'the $suites list is there')
suites = re.findall(r"'(test_[a-z0-9_]+\.py)'", m.group(1)) if m else []
ok(len(suites) == len(set(suites)),
   '%d suites, none listed twice' % len(suites),
   sorted(s for s in set(suites) if suites.count(s) > 1))
absent = [s for s in suites if not os.path.isfile(os.path.join(ROOT, s))]
ok(not absent, 'and every one of them is on disk', absent)
ok(ME in suites, '  including this one')

# EVERY ROW'S FILE IS IN THE REPO, not above it.
outside = [r['File'] for r in ROWS if r['File'].startswith(('..', '/', 'C:'))]
ok(not outside, 'and no row reaches outside the repo', outside[:4])

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
