# -*- coding: utf-8 -*-
"""test_view_seg.py - Section MC round MC-1, 3 Oct 2026.

Demetri: "Can we move the List/Calendar Switch button up and make it
conform to our standards ... I should have the List/Calendar toggle in
the Calendar view to be able to switch to List view again."

THE THIRD SENTENCE WAS A BUG REPORT. Both halves were in the Calendar
page's markup. The Calendar page's copy of the CSS painted them

    .view-toggle          background: rgba(255, 255, 255, 0.2)
    .view-toggle .toggle-btn  color: rgba(255, 255, 255, 0.7)

on a white page - written for a coloured header bar the page no longer
has. Only .active, which paints its own background, stayed visible. So
one calendar icon floated alone and there was no way back to the list.

WHAT THIS SUITE IS FOR, beyond asserting the seg is there: section 4
RENDERS the old control and the new one and asks the browser what the
contrast actually is. A suite that only reads class names would have
passed the broken page every day it was broken - the class names were
all correct. The eye was the only instrument that could see it, and
this section is that eye, written down.

SECTION 5 IS THE CONTROL. It renders the OLD css and must find the
inactive half unreadable. If that control ever passes, the premise of
this round is wrong and the suite says so instead of staying quiet.
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

SUFFIX = '.bak_viewseg'
ME = 'test_view_seg.py'
PATCHER = 'apply_view_seg.py'
PS1 = 'Push-PendingChanges.ps1'
PAGES = ('meal_plans.html', 'meal_plan_calendar.html')
CURRENT = {'meal_plans.html': 'meal_plans',
           'meal_plan_calendar.html': 'meal_plan_calendar'}
DEAD = ('view-toggle-row', 'view-toggle', 'toggle-btn')
FIXTURE = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

# SCRATCH. Nothing this suite writes belongs beside the repo; a suite that
# leaves files behind is a suite that makes the next sweep lie.
SCRATCH = tempfile.mkdtemp(prefix='alv_viewseg_')

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


# CO-1, 3 Oct 2026 - this was written out here, as it was in 46
# other files. It lives in alv_tree now, with the repair that
# stops `accept="image/*"` reading as a comment opener and hiding
# 94 lines of the Add Passport form from every gate in the tree.
code_only = alv_tree.code_only


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


BASEP = alv_tree.path_of('base.html')
BASE = read(BASEP)
BCSS = css_of(BASE)
FIX = read(FIXTURE) if os.path.exists(FIXTURE) else ''

NOW = {p: now(alv_tree.path_of(p)) for p in PAGES}
CODE = {p: code_only(NOW[p]) for p in PAGES}
WAS = {p: was(alv_tree.path_of(p)) for p in PAGES}

print('=' * 74)
print('%s - MC-1, THE SWITCH BECOMES A SEGMENT' % ME)
print('=' * 74)

# ==========================================================================
head('1. BASE OWNS THE CONTROL, AND BOTH PAGES WEAR IT')
# ==========================================================================
for sel in ('.alv-seg', '.alv-seg > *',
            '.alv-seg > [aria-current="page"]'):
    ok(sel in BCSS, 'base defines %s' % sel)
ok('background: var(--alv-accent)' in
   BCSS[BCSS.find('.alv-seg > [aria-pressed="true"]'):
        BCSS.find('.alv-seg > [aria-pressed="true"]') + 300],
   'and the current segment is filled with the accent, not a literal')

for p in PAGES:
    n = CODE[p].count('class="alv-seg"')
    ok(n == 1, '%s wears exactly one seg' % p, 'found %d' % n)

# ==========================================================================
head('2. IT IS IN THE ACTION BAR, NOT ON A ROW OF ITS OWN')
# ==========================================================================
# His words were "move the List/Calendar Switch button up". A seg that
# sits in the bar is up; a seg that sits under the bar has only been
# restyled. So this asks WHERE, not just WHETHER.
for p in PAGES:
    t = CODE[p]
    try:
        bar = t.index('<div class="page-action-buttons">')
        seg = t.index('class="alv-seg"')
        end = t.index('</div>', t.index('action-back"'))
    except ValueError as e:
        ok(False, '%s has a bar, a seg and a Back' % p, str(e))
        continue
    ok(bar < seg < end, '%s has the seg inside the action bar' % p,
       'bar at %d, seg at %d, bar ends %d' % (bar, seg, end))
    # AND BEFORE BACK, which carries margin-left:auto, so Back stays hard
    # right and nothing else in the bar moves.
    ok(seg < t.index('action-back"'),
       '  and before Back, which keeps its margin-left: auto')

# ==========================================================================
head('3. TWO HALVES, ONE CURRENT, AND IT IS THE RIGHT ONE')
# ==========================================================================
for p in PAGES:
    t = CODE[p]
    i = t.index('<div class="alv-seg"')
    block = t[i:t.index('</div>', i)]
    halves = re.findall(r"\{% url '(\w+)' %\}([^>]*)>", block)
    ok(len(halves) == 2, '%s seg has two halves' % p,
       [h for h, _ in halves])
    cur = [h for h, rest in halves if 'aria-current="page"' in rest]
    ok(cur == [CURRENT[p]], '  and %s is the current one' % CURRENT[p], cur)
    ok('class="active"' not in block and 'toggle-btn' not in block,
       '  marked with aria-current, not class="active" - the standard\'s '
       'hook for the fill AND what a screen reader needs')
    ok('role="group"' in t[i - 60:i + 120] or 'role="group"' in block
       or 'role="group"' in t[i:i + 120],
       '  and the pair is a labelled group')

# THE ONE-WAY STREET. This is the gate that would have caught the report.
for p in PAGES:
    for url in ("{% url 'meal_plans' %}", "{% url 'meal_plan_calendar' %}"):
        ok(url in CODE[p], '%s can reach %s' % (p, url.split("'")[1]))

# ==========================================================================
head('4. THE OLD CONTROL IS GONE - CLASS, RULES AND LITERALS')
# ==========================================================================
for p in PAGES:
    for d in DEAD:
        n = len(re.findall(r'\b%s\b' % re.escape(d), CODE[p]))
        ok(n == 0, '%s carries no %s in code' % (p, d), 'still %d' % n)

# Counted against the backup, not asserted absolute. meal_plans.html uses
# #dee2e6 twice - once on the toggle hover, once on the empty-state icon -
# and this round touched one of them. A gate that claimed the colour was
# gone from the page would be claiming more than the round did.
DROP = {
    'meal_plans.html': ('#5a6fd6', '#495057', '#dee2e6', '#6c757d'),
    'meal_plan_calendar.html': ('rgba(255, 255, 255, 0.2)',
                                'rgba(255, 255, 255, 0.7)',
                                'rgba(255, 255, 255, 0.1)', '#f8f9fa'),
}
for p, lits in DROP.items():
    if not WAS[p]:
        skip('the literal drop on %s' % p, 'no %s backup' % SUFFIX)
        continue
    w = code_only(WAS[p])
    for lit in lits:
        d = w.count(lit) - CODE[p].count(lit)
        ok(d == 1, '%s dropped one use of %s' % (p, lit),
           '%d before, %d after' % (w.count(lit), CODE[p].count(lit)))

# AND A CLAIM THE ROUND IS ENTITLED TO MAKE. The first draft of this one
# said #5a6fd6 was gone from BOTH pages and failed: the Calendar page
# carries a SECOND purple, on .add-recipe-btn:hover, which this round
# never touched. Tenth time this week an instrument has been handed a
# substring when the thing meant was a place. So the claim is made per
# page, and the one MC-1 is not entitled to remove is pinned by name so
# MC-3 can take it and this gate will say so when it does.
ok('#5a6fd6' not in CODE['meal_plans.html'],
   '#5a6fd6 is gone from meal_plans.html')
LEFT_FOR_MC3 = {'.add-recipe-btn:hover': 'the second purple, MC-3 takes it'}
for m in re.finditer(r'#5a6fd6', CODE['meal_plan_calendar.html']):
    seg = CODE['meal_plan_calendar.html'][max(0, m.start() - 200):m.start()]
    where = [k for k in LEFT_FOR_MC3 if k in seg]
    ok(bool(where),
       'the Calendar page\'s remaining #5a6fd6 is the pinned one on %s'
       % (where[-1] if where else '?'),
       'an unpinned purple at line %d'
       % (CODE['meal_plan_calendar.html'].count('\n', 0, m.start()) + 1))

# ==========================================================================
head('5. WHAT THE BROWSER SEES - BOTH HALVES, AND THE CONTROL')
# ==========================================================================
# A suite that reads class names would have passed the broken Calendar
# page every day it was broken: every class name on it was correct. What
# was wrong was a COLOUR against a GROUND, and only a renderer can see
# that. So: render both controls and compare each half's ink with the
# paper behind it.
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
    skip('the rendered contrast checks', 'playwright not installed')

JS = """() => {
  const pick = e => {
    const s = getComputedStyle(e);
    let bg = s.backgroundColor, n = e;
    while ((bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent') && n.parentElement) {
      n = n.parentElement; bg = getComputedStyle(n).backgroundColor;
    }
    return {fg: s.color, bg: bg,
            w: Math.round(e.getBoundingClientRect().width),
            h: Math.round(e.getBoundingClientRect().height)};
  };
  const r = document.querySelector('.alv-seg, .view-toggle');
  if (!r) return null;
  return {halves: [...r.children].map(pick),
          overflow: document.documentElement.scrollWidth
                    > document.documentElement.clientWidth};
}"""

_PW = _BR = None


def browser():
    # ONE BROWSER, NOT ONE PER RENDER - the lesson test_secondary_visible
    # paid 90 seconds to learn.
    global _PW, _BR
    if _BR is None:
        _PW = sync_playwright().start()
        _BR = _PW.chromium.launch()
    return _BR


def render(page_css, html, width):
    doc = ('<!doctype html><meta charset=utf-8>'
           '<style>%s</style><style>%s</style><style>%s</style>'
           '<style>body{margin:0;padding:8px;background:#fff}</style>'
           '<body><div class="page-action-buttons">%s</div>'
           % (FIX, BCSS, page_css, html))
    pg = browser().new_page(viewport={'width': width, 'height': 300})
    # OFFLINE on purpose: a render that waits on a CDN measures the CDN.
    pg.route(re.compile(r'^https?://'), lambda r: r.abort())
    pg.set_content(doc, wait_until='domcontentloaded')
    try:
        return pg.evaluate(JS)
    finally:
        pg.close()


def lum(rgb):
    m = re.findall(r'[\d.]+', rgb or '')
    if len(m) < 3:
        return None
    c = []
    for v in m[:3]:
        v = float(v) / 255.0
        c.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(fg, bg):
    a, b = lum(fg), lum(bg)
    if a is None or b is None:
        return None
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


TAGS = re.compile(r'\{%.*?%\}|\{\{.*?\}\}|\{#.*?#\}', re.S)


def seg_html(src, cls):
    i = src.index('<div class="%s"' % cls)
    j = src.index('</div>', src.index('</a>', i)) + 6
    return TAGS.sub('', src[i:j])


if sync_playwright is not None and FIX:
    for p in PAGES:
        try:
            html = seg_html(NOW[p], 'alv-seg')
        except ValueError:
            ok(False, '%s: no seg to render' % p)
            continue
        for w, label in ((1280, 'desktop'), (390, 'phone')):
            r = render(css_of(NOW[p]), html, w)
            if not ok(r and len(r['halves']) == 2,
                      '%s renders two halves at %s' % (p, label)):
                continue
            for n, hf in enumerate(r['halves']):
                cr = ratio(hf['fg'], hf['bg'])
                ok(cr is not None and cr >= 3.0,
                   '  half %d is readable at %s (%.1f:1)'
                   % (n + 1, label, cr or 0),
                   '%s on %s' % (hf['fg'], hf['bg']))
                ok(hf['w'] > 30 and hf['h'] > 20,
                   '  half %d has real size at %s (%dx%d)'
                   % (n + 1, label, hf['w'], hf['h']))
            ok(not r['overflow'],
               '  and the bar does not scroll sideways at %s' % label)
else:
    skip('the rendered contrast checks', 'no browser or no fixture')

# ==========================================================================
head('6. THE CONTROL - THE OLD CALENDAR TOGGLE MUST FAIL THIS')
# ==========================================================================
# If this passes, the Calendar page was never broken and the premise of
# this round is wrong. A control that cannot fail is not a control.
CAL = 'meal_plan_calendar.html'
if not WAS[CAL]:
    skip('the white-on-white control', 'no %s backup' % SUFFIX)
elif sync_playwright is None or not FIX:
    skip('the white-on-white control', 'no browser or no fixture')
else:
    ok('rgba(255, 255, 255, 0.7)' in WAS[CAL],
       'the Calendar page really did paint its toggle ink white')
    old = render(css_of(WAS[CAL]), seg_html(WAS[CAL], 'view-toggle'), 1280)
    if ok(old and len(old['halves']) == 2,
          'the old control renders its two halves'):
        bad = [n for n, h in enumerate(old['halves'])
               if (ratio(h['fg'], h['bg']) or 99) < 3.0]
        ok(len(bad) == 1,
           'CONTROL: exactly one half of the OLD control was unreadable - '
           'the List half, which is what he could not find', bad)
        rs = ['%.1f' % (ratio(h['fg'], h['bg']) or 0)
              for h in old['halves']]
        print('         old contrast, List then Calendar: %s' % ', '.join(rs))

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
