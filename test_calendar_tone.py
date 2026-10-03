# -*- coding: utf-8 -*-
"""test_calendar_tone.py - Section MC round MC-3, 3 Oct 2026.

Demetri: "On Calendar view, we have a lot of changes to do to the colours
to bring them in line."

MC-2 took the five filled buttons. MC-3 took the rest, on both views, and
found three things that were more than colour. The first two are what
this suite mostly exists to hold:

FINDING 1 - ONE RULE WITH TWO FATES. meal_plans.html wrote its primary as
`btn btn-create action-primary`, and base's `.btn.action-primary` (0,2,0)
outranks `.btn-create` (0,1,0), so the green had had no effect there
since the day action-primary was added. The EMPTY STATE wrote
`btn btn-create btn-lg` with no action-primary at all, and there the
green was live. One rule, two fates, and nothing in the file said so.

FINDING 2 - A DISABLED BUTTON THAT RENDERED ENABLED. The no-permission
branch wrote `btn btn-create-disabled action-primary`, and by the same
specificity base painted it solid teal. A user with no permission to
create a meal plan saw a button that looked exactly like a working one.
Section 3 RENDERS both the old markup and the new and compares them with
base's own rule, because this is the one finding a reader cannot check
by eye: the bug was that it looked right.

FINDING 3 - ML-1 LEFT FOUR DEAD RULES in meal_plans.html, matching
nothing since the day it moved the rows onto .row-actions.

AND SECTION 5 IS THE REFUSAL. #28a745 is NOT in the sweep table. It
carried a CREATE button and a "this day has a meal" dot on one page, and
mapping both to one token would have painted a verb and a status the
same. The verb took the accent; the dots took --alv-good. This section
holds that apart so a later sweep cannot quietly merge them.
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
import shutil
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_caltone'
ME = 'test_calendar_tone.py'
PATCHER = 'apply_calendar_tone.py'
PS1 = 'Push-PendingChanges.ps1'
PAGES = ('meal_plans.html', 'meal_plan_calendar.html')
FIXTURE = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

SWEPT = ('#2c3e50', '#495057', '#6c757d', '#adb5bd', '#ccc', '#f8f9fa',
         '#e8e8e8', '#e9ecef', '#dee2e6', '#f0f0f0', '#e8f4ff', '#f8f9ff',
         '#5a6fd6', 'rgba(102, 126, 234, 0.1)')
BY_NAME = ('#28a745', '#218838')
TOKENS = ('--alv-ink', '--alv-ink-soft', '--alv-ink-faint', '--alv-surface',
          '--alv-surface-deep', '--alv-line', '--alv-line-soft',
          '--alv-accent', '--alv-accent-ink', '--alv-accent-soft',
          '--alv-accent-ring', '--alv-good', '--alv-neutral')
DEAD = ('btn-create', 'btn-create-disabled', 'meal-plan-actions',
        'btn-action-disabled')
# Shadows are a DEPTH, not a hue, and the tree has no token for one. A
# round that quietly ate them would be hard to notice.
SHADOWS = ('rgba(0, 0, 0, 0.0', 'rgba(0, 0, 0, 0.1')

SCRATCH = tempfile.mkdtemp(prefix='alv_caltone_')

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
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


def code_only(t):
    t = re.sub(r'\{#.*?#\}', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), t, flags=re.S)


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


def pat_for(lit):
    """A WORD BOUNDARY AFTER ')' IS NOT A BOUNDARY. \\b is right for
    #f8f9fa, which must not match #f8f9fab, and silently wrong for
    rgba(102, 126, 234, 0.1), which ends in ')' and is followed by ';' -
    two non-word characters with no boundary between them. The patcher
    hit this first and reported the purple focus ring as zero uses."""
    return re.escape(lit) + (r'\b' if lit[-1].isalnum() else '')


NOW = {p: now(alv_tree.path_of(p)) for p in PAGES}
CODE = {p: code_only(NOW[p]) for p in PAGES}
WAS = {p: code_only(was(alv_tree.path_of(p))) for p in PAGES}
BASE = read(alv_tree.path_of('base.html'))
FIX = read(FIXTURE) if os.path.exists(FIXTURE) else ''

print('=' * 74)
print('%s - MC-3, THE REST OF THE MEAL PLAN COLOURS' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE SWEEP - NO LITERAL SURVIVES, AND EVERY TOKEN EXISTS')
# ==========================================================================
for p in PAGES:
    bad = [l for l in SWEPT if re.search(pat_for(l), CODE[p])]
    ok(not bad, '%s carries none of the %d swept literals'
       % (p, len(SWEPT)), bad)
    bad = [l for l in BY_NAME if re.search(pat_for(l), CODE[p])]
    ok(not bad, '  nor %s, which were handled by name' % ' or '.join(BY_NAME),
       bad)

for tok in TOKENS:
    ok('%s:' % tok in BASE, 'base defines %s' % tok)

# A TOKEN THE PAGE ASKS FOR AND BASE DOES NOT HAVE IS A TRANSPARENT
# DECLARATION, which is invisible rather than wrong-coloured - the worst
# kind of failure to find by eye.
for p in PAGES:
    asked = set(re.findall(r'var\((--alv-[a-z-]+)', CODE[p]))
    missing = sorted(t for t in asked if '%s:' % t not in BASE)
    ok(not missing, '%s asks for %d tokens and base has them all'
       % (p, len(asked)), missing)

# ==========================================================================
head('2. FINDING 1 AND 3 - .btn-create AND FOUR DEAD RULES ARE GONE')
# ==========================================================================
L = 'meal_plans.html'
for d in DEAD:
    ok(not re.search(r'\b%s\b' % d, CODE[L]), '%s is gone from %s' % (d, L))

ok(CODE[L].count('class="btn action-primary btn-lg"') == 1,
   'the empty-state button wears action-primary like its sibling - it was '
   'the ONLY place .btn-create\'s green was ever live')
ok('btn btn-create action-primary' not in CODE[L],
   'and the bar primary no longer names a class that has no rule')

if WAS[L]:
    ok('btn btn-create btn-lg' in WAS[L],
       'CONTROL: the empty-state button really did carry btn-create with no '
       'action-primary beside it')
    ok(WAS[L].count('#28a745') >= 1,
       'CONTROL: and .btn-create really was #28a745')
else:
    skip('the btn-create controls', 'no %s backup' % SUFFIX)

# ==========================================================================
head('3. FINDING 2 - THE DISABLED BUTTON, MEASURED')
# ==========================================================================
# The one finding that cannot be checked by eye, because the bug was that
# it LOOKED right. Rendered, old markup and new, against base's own CSS.
ok('class="btn action-primary disabled-btn"' in CODE[L],
   'the no-permission span is .action-primary.disabled-btn')
m = re.search(r'\.btn\.action-primary\.disabled-btn[^{]*\{([^}]*)\}', BASE)
ok(bool(m) and 'background' in (m.group(1) if m else ''),
   'base repaints a disabled primary - so the class is not just a rename',
   m.group(1)[:120] if m else 'no rule at all')

if WAS[L]:
    ok('btn-create-disabled action-primary' in WAS[L],
       'CONTROL: the span really did carry action-primary, which outranked '
       'its own grey by (0,2,0) to (0,1,0)')
else:
    skip('the disabled control', 'no %s backup' % SUFFIX)

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
    skip('the rendered disabled checks', 'playwright not installed')

JS = """() => {
  const e = document.querySelector('#probe');
  if (!e) return null;
  const s = getComputedStyle(e);
  return {bg: s.backgroundColor, fg: s.color, pe: s.pointerEvents,
          op: s.opacity};
}"""

_PW = _BR = None


def browser():
    global _PW, _BR
    if _BR is None:
        _PW = sync_playwright().start()
        _BR = _PW.chromium.launch()
    return _BR


def render(page_css, html):
    doc = ('<!doctype html><meta charset=utf-8>'
           '<style>%s</style><style>%s</style><style>%s</style>'
           '<style>body{margin:0;padding:8px;background:#fff}</style>'
           '<body><div class="page-action-buttons">%s</div>'
           % (FIX, css_of(BASE), page_css, html))
    pg = browser().new_page(viewport={'width': 1280, 'height': 300})
    pg.route(re.compile(r'^https?://'), lambda r: r.abort())
    pg.set_content(doc, wait_until='domcontentloaded')
    try:
        return pg.evaluate(JS)
    finally:
        pg.close()


def norm(c):
    v = [int(float(x)) for x in re.findall(r'[\d.]+', c or '')[:3]]
    return tuple(v) if len(v) == 3 else None


if sync_playwright is not None and FIX and WAS[L]:
    live = render(css_of(NOW[L]),
                  '<a id="probe" class="btn action-primary">Create</a>')
    off = render(css_of(NOW[L]),
                 '<span id="probe" class="btn action-primary disabled-btn">'
                 'Create</span>')
    oldoff = render(css_of(was(alv_tree.path_of(L))),
                    '<span id="probe" class="btn btn-create-disabled '
                    'action-primary">Create</span>')
    if ok(all(x is not None for x in (live, off, oldoff)),
          'the three buttons render'):
        ok(norm(off['bg']) != norm(live['bg']),
           'TODAY: the switched-off primary is NOT the colour of a live one',
           'off %s, live %s' % (off['bg'], live['bg']))
        ok(off['pe'] == 'none',
           '  and it is not a working control either (pointer-events: none)',
           off['pe'])
        ok(norm(oldoff['bg']) == norm(live['bg']),
           'CONTROL: before this round it WAS the colour of a live one - '
           'which is the whole finding',
           'old-off %s, live %s' % (oldoff['bg'], live['bg']))
        print('         live %s / disabled now %s / disabled before %s'
              % (live['bg'], off['bg'], oldoff['bg']))
else:
    skip('the rendered disabled checks', 'no browser, fixture or backup')

# ==========================================================================
head('4. THE SHADOWS STAYED')
# ==========================================================================
# A depth is not a hue. A round that quietly ate the drop shadows while
# tidying colours would be very hard to spot in a diff of 35 lines.
for p in PAGES:
    if not WAS[p]:
        skip('the shadow count on %s' % p, 'no %s backup' % SUFFIX)
        continue
    for sh in SHADOWS:
        ok(WAS[p].count(sh) == CODE[p].count(sh),
           '%s kept all %d of its %s... shadows'
           % (p, CODE[p].count(sh), sh[:14]),
           '%d before, %d after' % (WAS[p].count(sh), CODE[p].count(sh)))

# ==========================================================================
head('5. THE REFUSAL - A VERB AND A STATUS ARE NOT ONE COLOUR')
# ==========================================================================
# #28a745 was deliberately kept OUT of the sweep table. On the calendar
# page it dressed a CREATE button and a "this day has a meal" dot, and
# one token for both would have said that a verb and a status are the
# same kind of thing.
C = 'meal_plan_calendar.html'
cal = CODE[C]


def decl_after(sel, prop='background'):
    i = cal.find(sel + ' {')
    if i < 0:
        i = cal.find(sel + '::after {')
    if i < 0:
        return None
    blk = cal[i:cal.find('}', i)]
    m = re.search(r'%s\s*:\s*([^;]+);' % prop, blk)
    return m.group(1).strip() if m else None


ok(decl_after('.create-plan-btn') == 'var(--alv-accent)',
   'the create button is a VERB and wears the accent',
   decl_after('.create-plan-btn'))
ok(decl_after('.create-plan-btn:hover') == 'var(--alv-accent-ink)',
   '  and its hover is the accent ink',
   decl_after('.create-plan-btn:hover'))
dot = decl_after('.mini-calendar-day.has-meal')
ok(dot == 'var(--alv-good)',
   'the has-meal dot is a STATUS and wears the palette green', dot)
ok(decl_after('.legend-dot.meal') == 'var(--alv-good)',
   '  and the legend swatch beside it says the same thing',
   decl_after('.legend-dot.meal'))
ok(decl_after('.create-plan-btn') != dot,
   'THE REFUSAL: the verb and the status are not the same colour, which a '
   'blanket #28a745 map would have made them')

# ==========================================================================
head('6. THE FOUR THE SWEEP COULD NOT REACH')
# ==========================================================================
# sweep_css enters <style> only. An inline style attribute and a string
# assigned to element.style are literals too, and a round that swept the
# stylesheet and left them would leave the page half-converted in exactly
# the places hardest to grep.
outside = re.sub(r'<style[^>]*>.*?</style>', '', NOW[C], flags=re.S)
for lit in ('#adb5bd', '#dee2e6', '#f0f0f0', '#e8f4ff'):
    ok(not re.search(pat_for(lit), code_only(outside)),
       '%s is gone from the markup and script of %s too' % (lit, C))
ok("element.style.background = 'var(--alv-accent-soft)'" in NOW[C],
   'including the one assigned in a script - a literal in JS is still a '
   'literal')

# ==========================================================================
head('7. REGISTERED, AND THE PUSH GATE STILL RESOLVES')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
except Exception as e:
    skip('ROUNDS', str(e))

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
ok(len(rows) == len(re.findall(r'@\{ *File *=', ps)),
   'the sentinel table parses %d rows' % len(rows))


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
    b = read(p)
    if r.get('Code'):
        b = _strip(b)
    if (r['Text'].lower() in b.lower()) != (not r.get('Absent')):
        stale.append('%s %s %r' % (r['File'],
                     'NOT FOUND' if not r.get('Absent') else 'IS BACK',
                     r['Text'][:46]))
ok(not stale, 'and all %d of them still resolve' % len(rows),
   '\n'.join(stale[:6]))

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
