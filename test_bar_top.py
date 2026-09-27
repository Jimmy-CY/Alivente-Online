# -*- coding: utf-8 -*-
"""test_bar_top.py - Section G round G2, 27 Sep 2026.

Judges three fixes to the action bar, all of them counted before they were
made and all of them re-counted here:

  1. THE BAR SITS BELOW THE TITLE. 68 pages already did; 8 did not, and all
     8 were Personal. The block moved and not a byte of it changed - section
     1 asserts that by comparing the moved block to the backup byte for byte.
  2. A BACK BUTTON SAYS "BACK". 94 said exactly that; 12 said something
     longer. The VISIBLE word changes; the aria-label keeps the destination,
     because a screen reader has no page around it to read from.
  3. A BACK BUTTON HAS NO COLOUR. 14 carried a Bootstrap colour class - 13
     btn-secondary and one btn-success. The house Back is `btn action-back`
     and nothing else.

THE FIRST SCOPE WAS DRAWN BY THE WRONG INSTRUMENT. The census that set this
round's size read only the controls INSIDE a .page-action-buttons bar, so
every Back sitting outside one was invisible to it - and two of the loudest
were: celebration_management's grey "Back to Dashboard" and
recipe_management's GREEN Back, both Personal, both on pages this round is
about. A file-wide count found four more. Section 4 pins the file-wide
number so a bar-only count can never set the scope again.

FOUR ARE LEFT ALONE ON PURPOSE and section 5 says which and why. A round
that quietly swept them would be claiming a judgement it never made.
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
# ------------------------------------------------------------------------

import os
import re
import sys

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_bartop'
ME = 'test_bar_top.py'
PATCHER = 'apply_bar_top.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(T, 'base.html')

TITLE_CLS = 'page-title-h2'
SUB_CLS = 'page-subtitle-h4'
BAR_CLS = 'page-action-buttons'
BACK_CLS = 'action-back'
LABEL_CLS = 'action-back-label'

MOVE = [
    'categories_management.html',
    'ingredient_base_units_management.html',
    'map_ingredients_nutrition.html',
    'meal_plan_shopping_list.html',
    'measurement_units_management.html',
    'preview_imported_recipe.html',
    'unit_conversions_management.html',
    'unit_conversions_wizard.html',
]

# (file, index, the word before, the colour class before)
BACKS = [
    ('categories_management.html', 0, 'Back to Recipe Management', None),
    ('celebration_management.html', 0, 'Back to Dashboard', 'btn-secondary'),
    ('create_meal_plan.html', 0, 'Cancel', 'btn-secondary'),
    ('ingredient_base_units_management.html', 0,
     'Back to Recipe Management', 'btn-secondary'),
    ('lease_timeline.html', 0, 'Back to Tenants', None),
    ('map_ingredients_nutrition.html', 0, 'Back to Recipe', 'btn-secondary'),
    ('map_ingredients_nutrition.html', 1, 'Back', 'btn-secondary'),
    ('meal_plan_calendar.html', 0, 'Back', 'btn-secondary'),
    ('meal_plan_shopping_list.html', 0, 'Back to Meal Plan', 'btn-secondary'),
    ('meal_plans.html', 0, 'Back to Recipes', 'btn-secondary'),
    ('measurement_units_management.html', 0,
     'Back to Recipe Management', 'btn-secondary'),
    ('preview_imported_recipe.html', 0, None, 'btn-secondary'),
    ('recipe_management.html', 0, 'Back', 'btn-success'),
    ('unit_conversions_management.html', 0,
     'Back to Recipe Management', 'btn-secondary'),
    ('unit_conversions_wizard.html', 0, 'Back to Recipe', 'btn-secondary'),
    ('unit_conversions_wizard.html', 1, 'Back', 'btn-secondary'),
    ('view_meal_plan.html', 0, 'Back to Meal Plans', 'btn-secondary'),
    ('view_recipe.html', 0, 'Back', 'btn-success'),
]
# What the round did NOT touch, and the reason. Asserted, not asserted away.
LEFT = {
    ('create_meal_plan.html', 0):
        'its word is "Cancel" - that is a form, and Cancel may be right',
    ('projects/project_task_list.html', 0):
        'its label is {% if greek %} - a language toggle, not a stray label',
    ('act_expense.html', 3):
        'a DRILL-DOWN return inside a report - it names where it goes '
        'because it goes somewhere on the same page',
    ('error_pages/connectivity_error.html', 0):
        'an error page with no action bar and no arrow',
}
# The four the bar-only census could not see.
MISSED_BY_BAR_ONLY = ('celebration_management.html', 'recipe_management.html',
                      'act_expense.html', 'lease_timeline.html')

COLOUR = re.compile(r'\bbtn-(?:secondary|success|light|info|primary|dark|'
                    r'warning|danger)\b')
HTML_C = re.compile(r'<!--.*?-->', re.S)
DJ_CB = re.compile(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', re.S | re.I)
DJ_C = re.compile(r'\{#.*?#\}', re.S)
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
LABEL_SPAN = re.compile(r'<span[^>]*class="[^"]*(?<![\w-])' + LABEL_CLS
                        + r'(?![\w-])[^"]*"[^>]*>(.*?)</span\s*>', re.S)
ARROW = re.compile(r'<i\b[^>]*fa-arrow-left[^>]*>\s*</i\s*>', re.S)

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
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
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


def now(p):
    """The file as THIS round left it. See alv_rounds.py."""
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


def _sp(m):
    return re.sub(r'[^\n]', ' ', m.group(0))


def blanked(t):
    """Comments blanked on the RAW text FIRST, then script and style bodies -
    the house order is defeated by accept="image/*" (lesson 58)."""
    t = HTML_C.sub(_sp, t)
    t = DJ_CB.sub(_sp, t)
    t = DJ_C.sub(_sp, t)
    for rx in (STYLE, SCRIPT):
        out, pos = [], 0
        for m in rx.finditer(t):
            out.append(t[pos:m.start(1)])
            out.append(re.sub(r'[^\n]', ' ', m.group(1)))
            pos = m.end(1)
        out.append(t[pos:])
        t = ''.join(out)
    return t


def div_end(scan, start):
    d = 0
    for m in re.finditer(r'</?div\b', scan[start:]):
        d += 1 if m.group(0) == '<div' else -1
        if d == 0:
            j = scan.find('>', start + m.end())
            return j + 1
    return None


def bar_span(text):
    scan = blanked(text)
    m = re.search(r'<div[^>]*class="[^"]*(?<![\w-])' + BAR_CLS
                  + r'(?![\w-])[^"]*"[^>]*>', scan)
    if not m:
        return None
    e = div_end(scan, m.start())
    return None if e is None else (m.start(), e)


def title_at(text):
    m = re.search(r'<h2[^>]*class="[^"]*(?<![\w-])' + TITLE_CLS
                  + r'(?![\w-])[^"]*"[^>]*>', blanked(text))
    return m.start() if m else None


def backs_in(text):
    """Every action-back control in the file, as (start, end). FILE-WIDE -
    a bar-only version of this is what drew the wrong scope."""
    scan = blanked(text)
    out = []
    for m in re.finditer(r'<(a|button|span)\b[^>]*class="([^"]*)"[^>]*>', scan):
        if BACK_CLS not in m.group(2).split():
            continue
        tag, d, end = m.group(1), 0, None
        for t in re.finditer(r'</?%s\b' % tag, scan[m.start():]):
            d += 1 if t.group(0) == '<' + tag else -1
            if d == 0:
                end = scan.find('>', m.start() + t.end()) + 1
                break
        if end:
            out.append((m.start(), end))
    return out


def backs_in_bar_only(text):
    """The census that set the first scope. Kept so section 4 can show
    exactly what it could not see."""
    span = bar_span(text)
    if span is None:
        return []
    inner = text[span[0]:span[1]]
    return [m for m in backs_in(inner)]


def label_of(html):
    m = LABEL_SPAN.search(html)
    inner = m.group(1) if m else ARROW.sub('', html)
    inner = re.sub(r'<[^>]+>', '', inner)
    if '{%' in inner or '{{' in inner:
        return None
    return ' '.join(inner.split()) or None


def templates():
    out = []
    for d, _s, fs in os.walk(T):
        for f in fs:
            if f.endswith('.html'):
                out.append(os.path.join(d, f))
    return sorted(out)


def rel_of(p):
    return os.path.relpath(p, T).replace(os.sep, '/')


# ==========================================================================
head('1. THE BAR MOVED, AND NOTHING IN IT CHANGED')
# ==========================================================================
moved = 0
for rel in MOVE:
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    a, b = was(p), now(p)
    sa, sb = bar_span(a), bar_span(b)
    ta, tb = title_at(a), title_at(b)
    if not ok(None not in (sa, sb, ta, tb),
              '%-40s has a bar and a title before and after' % rel,
              '%s %s %s %s' % (sa, sb, ta, tb)):
        continue
    ok(sa[0] < ta, '  it really was ABOVE the title - otherwise this '
       'proves nothing', '%d vs %d' % (sa[0], ta))
    ok(sb[0] > tb, '  and it is below now', '%d vs %d' % (sb[0], tb))
    # THE BLOCK IS THE SAME BLOCK. A move that rewrote it would pass the two
    # checks above and still be the wrong round.
    block_a, block_b = a[sa[0]:sa[1]], b[sb[0]:sb[1]]
    if rel in [r for r, _i, _l, _c in BACKS]:
        # this file's Back was also relabelled, so compare everything except
        # the control itself
        strip = lambda s: re.sub(r'<(a|button)\b[^>]*action-back.*?</\1\s*>',
                                 '@BACK@', s, flags=re.S)
        block_a, block_b = strip(block_a), strip(block_b)
        ok('@BACK@' in block_b, '  its Back control is inside the bar')
    ok(block_a == block_b,
       '  the block is byte for byte what it was - a move, not a rewrite',
       '%d bytes vs %d' % (len(block_a), len(block_b)))
    moved += 1
ok(moved == 8, 'all eight bars moved', moved)

# AND THE 68 THAT WERE ALREADY RIGHT ARE STILL RIGHT.
above = [rel_of(p) for p in templates()
         if rel_of(p) != 'base.html'
         and bar_span(read(p)) and title_at(read(p)) is not None
         and bar_span(read(p))[0] < title_at(read(p))]
ok(not above, 'NO page in the tree puts its action bar above its title',
   above)
below = sum(1 for p in templates()
            if rel_of(p) != 'base.html' and bar_span(read(p))
            and title_at(read(p)) is not None)
ok(below >= 70, 'CONTROL: and %d page(s) have both to be judged - the check '
   'is not passing on an empty set' % below, below)

# ==========================================================================
head('2. A BACK BUTTON SAYS "BACK"')
# ==========================================================================
relabelled = 0
for rel, idx, want, _col in BACKS:
    if (rel, idx) in LEFT:
        continue
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip('%s [%d]' % (rel, idx), 'not on disk')
        continue
    a, b = was(p), now(p)
    sa, sb = backs_in(a), backs_in(b)
    if not ok(len(sa) > idx and len(sb) > idx,
              '%-38s [%d] is there before and after' % (rel, idx),
              '%d before, %d after' % (len(sa), len(sb))):
        continue
    before_lbl = label_of(a[sa[idx][0]:sa[idx][1]])
    after = b[sb[idx][0]:sb[idx][1]]
    ok(before_lbl == want,
       '  it said %r' % (want if want else '(a conditional)'), before_lbl)
    ok(label_of(after) == 'Back', '  and says "Back" now', label_of(after))
    # THE DESTINATION IS NOT LOST - it moves to where a screen reader
    # reads it, not to where nobody does.
    if 'aria-label=' in a[sa[idx][0]:sa[idx][1]]:
        aa = re.search(r'aria-label="([^"]*)"', a[sa[idx][0]:sa[idx][1]])
        ab = re.search(r'aria-label="([^"]*)"', after)
        ok(ab is not None and aa.group(1) == ab.group(1),
           '  its aria-label still says where it goes: %r' % aa.group(1),
           ab.group(1) if ab else None)
    # AND THE WORD CAN HIDE ON A PHONE. Four of these put the label as bare
    # text, so base could not hide it and the control was a full-width pill
    # where every other page shows a 44px arrow.
    ok(LABEL_SPAN.search(after) is not None,
       '  the word is inside .%s, so base can hide it on a phone' % LABEL_CLS)
    ok(re.search(r'href=|onclick=', after) is not None,
       '  and it still goes somewhere')
    relabelled += 1
WANT_RELABEL = len([b for b in BACKS if (b[0], b[1]) not in LEFT])
ok(relabelled == WANT_RELABEL,
   '%d label(s) shortened to Back' % WANT_RELABEL, relabelled)

long_left = []
for p in templates():
    rel = rel_of(p)
    for s, e in backs_in(read(p)):
        lbl = label_of(read(p)[s:e])
        if lbl and lbl.lower() != 'back':
            long_left.append((rel, lbl))
# Three, not four: project_task_list's label is a conditional, so it reads
# as no single word at all and never appears in this list.
ok(len(long_left) == 3,
   'three Back controls still say something else - Cancel, Back to '
   'overview, Go Back - and section 5 names each',
   long_left)

# ==========================================================================
head('3. A BACK BUTTON HAS NO COLOUR')
# ==========================================================================
decoloured = 0
for rel, idx, _w, col in BACKS:
    if col is None:
        continue
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip('%s [%d]' % (rel, idx), 'not on disk')
        continue
    a, b = was(p), now(p)
    sa, sb = backs_in(a), backs_in(b)
    if len(sa) <= idx or len(sb) <= idx:
        skip('%s [%d]' % (rel, idx), 'index gone')
        continue
    ha, hb = a[sa[idx][0]:sa[idx][1]], b[sb[idx][0]:sb[idx][1]]
    m = COLOUR.search(ha)
    ok(m is not None and m.group(0) == col,
       '%-38s [%d] wore .%s' % (rel, idx, col),
       m.group(0) if m else None)
    ok(COLOUR.search(hb) is None, '  and wears no colour class now',
       COLOUR.search(hb).group(0) if COLOUR.search(hb) else '')
    ok('btn' in re.search(r'class="([^"]*)"', hb).group(1).split(),
       '  it is still a .btn, as properties.html line 74 is')
    decoloured += 1
WANT_COLOUR = len([b for b in BACKS if b[3] is not None])
ok(decoloured == WANT_COLOUR,
   '%d colour class(es) stripped' % WANT_COLOUR, decoloured)

coloured_left = []
for p in templates():
    for s, e in backs_in(read(p)):
        m = COLOUR.search(re.search(r'class="([^"]*)"',
                                    read(p)[s:e]).group(1))
        if m:
            coloured_left.append((rel_of(p), m.group(0)))
ok(not coloured_left,
   'NO Back control in the tree carries a Bootstrap colour class',
   coloured_left)

# ==========================================================================
head('4. THE SCOPE WAS DRAWN BY THE WRONG INSTRUMENT')
# ==========================================================================
# The census that sized this round looked only inside a .page-action-buttons
# bar. Four Back controls sit outside one, and two of them were the loudest
# things on the pages this round is about.
#
# READ AS THIS ROUND LEFT IT (lesson 40). This section is a claim about the
# state G2 found, so it must read now(), not the live file. H2 has since
# moved celebration_management's Back INTO the bar - correctly - and against
# the live file "the bar-only census could not see it" became false.
seen_by_bar_only = 0
seen_file_wide = 0
for p in templates():
    t = now(p)
    if rel_of(p) == 'base.html':
        continue
    seen_by_bar_only += len(backs_in_bar_only(t))
    seen_file_wide += len(backs_in(t))
ok(seen_file_wide > seen_by_bar_only,
   'a file-wide count finds %d Back control(s); a bar-only count finds %d'
   % (seen_file_wide, seen_by_bar_only),
   'if these were equal the lesson would be untestable')
for rel in MISSED_BY_BAR_ONLY:
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    t = now(p)
    ok(len(backs_in(t)) > len(backs_in_bar_only(t)),
       '%-38s has a Back the bar-only census could not see' % rel,
       '%d file-wide, %d in the bar'
       % (len(backs_in(t)), len(backs_in_bar_only(t))))
cm = os.path.join(T, 'celebration_management.html')
rm = os.path.join(T, 'recipe_management.html')
if os.path.isfile(cm) and os.path.isfile(rm):
    ok(COLOUR.search(was(cm)[slice(*backs_in(was(cm))[0])]) is not None
       and COLOUR.search(was(rm)[slice(*backs_in(was(rm))[0])]) is not None,
       '  and the two the first scope missed really were painted - a grey '
       'pill and a GREEN Back, both on Personal pages this round is about')

# ==========================================================================
head('5. WHAT THIS ROUND DID NOT DO, AND WHY')
# ==========================================================================
for (rel, idx), why in sorted(LEFT.items()):
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    a, b = was(p), now(p)
    sa, sb = backs_in(a), backs_in(b)
    if len(sa) <= idx or len(sb) <= idx:
        skip('%s [%d]' % (rel, idx), 'index gone')
        continue
    ha, hb = a[sa[idx][0]:sa[idx][1]], b[sb[idx][0]:sb[idx][1]]
    ok(label_of(ha) == label_of(hb),
       '%-38s [%d] keeps its word - %s' % (rel, idx, why),
       '%r -> %r' % (label_of(ha), label_of(hb)))
print('\n        Each of those four is a judgement, not an oversight. A '
      'round that\n        swept them would be claiming one it never made.')

# ==========================================================================
head('6. CONTROLS - checks that would catch a vacuous suite')
# ==========================================================================
_sec = len([b for b in BACKS if b[3] == 'btn-secondary'])
_suc = len([b for b in BACKS if b[3] == 'btn-success'])
ok(len(MOVE) == 8 and len(BACKS) == 18,
   'eight bars moved and eighteen Back controls read',
   '%d, %d' % (len(MOVE), len(BACKS)))
# COUNTED OFF THE TABLE, NOT TYPED IN. Every hardcoded corpus number in this
# tree has eventually failed correct work; this one already did, the moment
# the scope widened from 14 controls to 16.
ok(_sec + _suc == len([b for b in BACKS if b[3] is not None]),
   '  every colour in the table is secondary or success: %d + %d'
   % (_sec, _suc))
ok(_sec == 14 and _suc == 2,
   '  %d were btn-secondary and %d btn-success (GREEN)' % (_sec, _suc))

# THE CLASS MATCH IS NOT FOOLED BY A HYPHEN (lesson 30) - .action-back-label
# contains .action-back, and a substring match would count every label span
# as a Back control.
ok(BACK_CLS not in 'action-back-label'.split(),
   'the class match is by token - action-back-label is not action-back')
ok(len(backs_in('<a class="action-back-label">x</a>')) == 0,
   '  and the finder agrees')
ok(len(backs_in('<a class="btn action-back">x</a>')) == 1,
   '  while it does find one beside another class')

# THE COLOUR MATCH TAKES A COLOUR, NOT A SIZE. btn-sm is on two of these
# controls and is a size, not a paint job; stripping it would change the
# control this round says it is not changing.
ok(COLOUR.search('btn btn-sm action-back') is None,
   'btn-sm is a size, not a colour - it is left alone')
ok(COLOUR.search('btn btn-secondary action-back') is not None,
   '  and btn-secondary is caught')
sm = [rel_of(p) for p in templates()
      if re.search(r'class="[^"]*\bbtn-sm\b[^"]*\baction-back\b'
                   r'|class="[^"]*\baction-back\b[^"]*\bbtn-sm\b', read(p))]
ok(len(sm) >= 2, '  and %d page(s) still carry it, untouched' % len(sm), sm)

# THE HOUSE FORM, READ OFF THE HOUSE.
props = os.path.join(T, 'properties.html')
if os.path.isfile(props):
    m = [read(props)[s:e] for s, e in backs_in(read(props))]
    ok(m and COLOUR.search(m[0]) is None and label_of(m[0]) == 'Back',
       'properties.html - the page this round was told to match - has an '
       'uncoloured Back that says "Back"',
       (label_of(m[0]) if m else None))
else:
    skip('properties.html', 'not on disk')

# A REVERT MUST FAIL, NOT CRASH.
cm = os.path.join(T, 'categories_management.html')
if os.path.isfile(cm + SUFFIX):
    old = was(cm)
    ok(bar_span(old)[0] < title_at(old),
       'reverting categories_management puts the bar back above the title, '
       'so the check that says it is below would FAIL - a revert is caught')
    ok(label_of(old[slice(*backs_in(old)[0])]) == 'Back to Recipe Management',
       '  and its long label comes back too')
else:
    skip('the revert check', 'no %s backup' % SUFFIX)

# REGISTERED, AND ON THE GATE.
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
# NOT "AND IT IS THE NEWEST ROUND". That check passes on the day it is
# written and fails on the day the next round is registered - lesson 54,
# which was already written down when this suite asked for it anyway. H1
# was registered the same afternoon and turned it red. What is worth
# asserting is the ORDER: this round came after the one it builds on, so
# as_left_by unwinds them the right way round.
ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_pagetitle'),
   '  and it is registered AFTER .bak_pagetitle, the round it builds on',
   '%s at %d, .bak_pagetitle at %d'
   % (SUFFIX, ROUNDS.index(SUFFIX), ROUNDS.index('.bak_pagetitle'))
   if SUFFIX in ROUNDS and '.bak_pagetitle' in ROUNDS else ROUNDS[-3:])
ps1 = os.path.join(ROOT, PS1)
ok(os.path.isfile(ps1) and ME in read(ps1), '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
