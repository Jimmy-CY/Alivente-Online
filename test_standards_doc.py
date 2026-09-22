# -*- coding: utf-8 -*-
"""test_standards_doc.py - base.html's standards block records the
decisions of 16-22 Sep, and nothing else in base moved.

    python test_standards_doc.py

Run from the repo root, after apply_standards_doc.py.

test_standards_block.py already keeps the block's SHAPE honest - one copy,
no tags, no braces, every token, component and suite it names real. This
suite keeps its CONTENT from losing what was decided: each decision below
must still be written down, and each claim that names a class or a suite
must still be true. If a later round reverses one, it edits the block AND
this list - which is the point.

  1. The decisions are recorded.
  2. The claims are true: the gate runs every suite on disk; the named
     classes exist in base; base declares the token count it says.
  3. Scope: outside the block, base is byte-for-byte what it was.
     CONTROL: before this round the block did not say these things.
  4. It is on the gate.
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

import os
import re
import sys
import glob

ROOT = os.getcwd()
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
if not os.path.isfile(BASE):
    sys.exit('! pages/templates/base.html not found - run from the repo root')
SUFFIX = '.bak_stddoc'
PS1 = 'Push-PendingChanges.ps1'
ME = 'test_standards_doc.py'

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
            print('         %s' % str(detail)[:200])
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


BLK = re.compile(r'\{%\s*comment\s*%\}(.*?)\{%\s*endcomment\s*%\}', re.S)
B = read(BASE)
m = BLK.search(B)
DOC = ' '.join(m.group(1).split()) if m else ''

# Each decision, as a phrase the block must carry. A later round that
# reverses one edits the block and this list together.
DECISIONS = [
    ('the gate runs every suite', 'EVERY SUITE IN THE REPO RUNS ON THE PUSH GATE'),
    ('no suite is known to fail', 'NONE IS KNOWN TO FAIL'),
    ('patchers keep line endings', 'LINE ENDINGS KEPT'),
    ('rounds are registered', 'ROUNDS in `alv_rounds.py`'),
    ('the revert test', 'Run it against the REVERTED tree'),
    ('judge a round on the file as it left it',
     'JUDGE THE ROUND ON THE FILE AS THE ROUND LEFT IT'),
    ('the all-suites sweep', 'THE ALL-SUITES SWEEP'),
    ('the heading markup', 'h2.page-title-h2 and h4.page-subtitle-h4'),
    ('the bar is first in the form', 'THE BAR IS THE FIRST THING IN THE FORM'),
    ('16px on a phone', 'SIXTEEN PIXELS ON A PHONE'),
    ('one name for the date', 'ONE FIELD, ONE NAME'),
    ('no button prints', 'NO BUTTON PRINTS'),
    ('no phone rule on paper', 'A PHONE RULE NEVER REACHES PAPER'),
    ('pop-up headers', '3.9 POP-UPS'),
    ('red only for delete', 'that, and only that'),
    ('the report title', '3.10 REPORTS'),
    ('the brand on paper only', 'On paper, and only on paper, ALIVENTE ONLINE'),
    ('a failing suite is not a failing page',
     'A FAILING SUITE IS NOT ALWAYS A FAILING PAGE'),
    ('a missing class hides a fault', 'A STANDARD CAN BE ESCAPED BY A MISSING CLASS'),
    ('exact-token counts', 'A SURVEY COUNT MUST BE OF THE EXACT TOKEN'),
    ('duplicated can mean dead', 'DUPLICATED CAN MEAN DEAD'),
    ('the current plan', 'claude/outstanding_review_21_sep.md'),
    ('Personal is the part never reviewed', 'PERSONAL HAS NEVER BEEN REVIEWED'),
    ('the revision date', 'Revised 22 September 2026'),
]

# ==========================================================================
head('1. THE DECISIONS ARE WRITTEN DOWN')
# ==========================================================================
ok(bool(DOC), 'base carries the standards block')
for what, phrase in DECISIONS:
    ok(' '.join(phrase.split()) in DOC, what, phrase)
ok('41 suites' not in DOC and 'ADMINISTRATION AND PERSONAL' not in DOC,
   'the stale claims are gone: 41 suites, and Administration unreviewed')

# ==========================================================================
head('2. WHAT IT CLAIMS IS TRUE')
# ==========================================================================
ps = read(PS1) if os.path.isfile(PS1) else ''
i = ps.find('$suites = @(')
gate = set(re.findall(r"'(test_[a-z0-9_]+\.py)'", ps[i:ps.find('\n)', i)])) \
    if i >= 0 else set()
disk = set(os.path.basename(p) for p in glob.glob(os.path.join(ROOT,
                                                               'test_*.py')))
off = sorted(disk - gate)
ok(gate and not off, 'every suite on disk is on the gate, as the block says',
   'not on the gate: %s' % ', '.join(off[:6]))
css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', B, re.S))
defined = set()
for mm in re.finditer(r'([^{}]+)\{', re.sub(r'/\*.*?\*/', '', css, flags=re.S)):
    defined.update(re.findall(r'\.([a-zA-Z][\w-]*)', mm.group(1)))
named = set(re.findall(r'\.((?:alv|page|form|print)-[a-z0-9-]+)', DOC))
ghost = sorted(c for c in named if c not in defined)
ok(not ghost, 'every class the block names is defined in base (%d named)'
   % len(named), ghost)
ok('.alv-modal-head--danger' in DOC and 'alv-modal-head--danger' in defined,
   '  CONTROL: including the one written in full')
toks = set(re.findall(r'(--alv-[a-z0-9-]+)\s*:', css))
said = re.search(r'(\d+) design tokens', DOC)
ok(said and int(said.group(1)) == len(toks),
   'base declares the %s tokens the block says' % (said.group(1) if said
                                                   else '?'),
   '%d declared' % len(toks))

# ==========================================================================
head('3. ONLY THE BLOCK CHANGED')
# ==========================================================================
bak = BASE + SUFFIX
if os.path.isfile(bak):
    sys.path.insert(0, ROOT)
    try:
        from alv_rounds import as_left_by
        left = as_left_by(BASE, SUFFIX, read)
    except Exception:
        left = B
    W = read(bak)
    ok(BLK.sub('', W) == BLK.sub('', left),
       'outside the standards block, base is what it was')
    wdoc = ' '.join(BLK.search(W).group(1).split()) if BLK.search(W) else ''
    missing = [w for w, p in DECISIONS if ' '.join(p.split()) not in wdoc]
    ok(len(missing) >= len(DECISIONS) - 2,
       'CONTROL: before this round the block recorded almost none of them',
       '%d of %d missing' % (len(missing), len(DECISIONS)))
else:
    skip('scope', 'no %s' % bak)

# ==========================================================================
head('4. IT IS ON THE GATE')
# ==========================================================================
ok(ME in gate, '%s runs %s on every push' % (PS1, ME))

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
sys.exit(1 if failed else 0)
