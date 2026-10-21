# -*- coding: utf-8 -*-
"""test_sl_range_row.py - round SH-2, 21 Oct 2026.

THE DATE RANGE WAS A SECOND ACTION BAR, SITTING ABOVE THE FIRST.

Demetri, testing SL-7 on Live:

    "On the Shopping List, for the date range, the date pickers should
     be FAR narrower and fit on one line, with the Show these days
     button. We are using up far too much space at the top of the
     page."
    "the date pickers for Shopping List should go under the Generate
     List, Help and Back Button (above Review Ingredients and
     Shopping List)"

HE WAS DESCRIBING THE STANDARD. SL-7 wrote the range as
`class="sl-range page-action-buttons"` and put it above the real bar,
and base 3.4 forbids both halves of that: "One .page-action-buttons
row per page", and "nothing sits above the bar".

AND THE WIDTH WAS NOT A STYLE CHOICE, it was the absence of one.
.sl-range had no rule anywhere in the project. The form was laid out
entirely by the bar class it had borrowed, and its inputs were
.form-control - width 100%. Measured at 1000px: each date input was
976px wide and the row was 221px tall.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. One bar on the page, the range below it and above
      the steps, its button a secondary, and the form still a GET
      carrying both names.

  2   THE CONTROL. Re-asked of the pre-round file: two bars, the
      form first, and a primary inside it.

  3   RENDERED, at 1000 and 390, before and after. The height and
      the input widths are the finding, and only a layout engine can
      report them.

  4   Scope, registration and the gate.

RUN IT AGAINST THE REVERTED TREE AND IT MUST FAIL, NOT CRASH.
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

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_slrangerow'
ME = 'test_sl_range_row.py'
PATCHER = 'apply_sl_range_row.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'SH-2, 21 Oct 2026'

TPL = os.path.join(ROOT, 'pages', 'templates',
                   'meal_plan_shopping_list.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
FIXCSS = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
GATE = os.path.join(ROOT, PS1)
FILES = (TPL,)

BARS = re.compile(r'<(?:div|form)\b[^>]*class="[^"]*\bpage-action-buttons\b')

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
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot '
                      'run - and a control that does not run is the whole '
                      'reason the 17 Oct push failed.' % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402

NOW = dict((p, read(p)) for p in FILES)


def range_at(code):
    """Where the range form's opening tag starts, or -1.

    MATCHED AS A CLASS, not as a string. Before this round the
    attribute read class="sl-range page-action-buttons", so an exact
    find of 'class="sl-range"' missed it entirely and the CONTROL
    reported the form as absent - which is the same mistake in a
    suite that the patcher's own gate made first.
    """
    for m in re.finditer(r'<form\b[^>]*class="([^"]*)"[^>]*>', code):
        if 'sl-range' in m.group(1).split():
            return m.start()
    return -1


def form_of(code):
    """The range form, from its OPENING TAG to its close.

    From the tag, not from the class attribute: method="get" sits
    earlier in the same tag, so a window opened at the attribute
    reports it missing on a form that has it.
    """
    j = range_at(code)
    if j < 0:
        return ''
    k = code.find('</form>', j)
    return code[j:k + 7] if k > j else ''


def claims(bundle):
    code = T.code_only(bundle[TPL])
    bars = [m.start() for m in BARS.finditer(code)]
    frm = form_of(code)
    c = {}
    c['ONE ACTION BAR ON THE PAGE - the finding'] = (len(bars) == 1)
    c['  the range is not one of them'] = (
        bool(frm) and 'page-action-buttons' not in frm)
    c['  it sits BELOW the bar'] = (
        bool(bars) and bool(frm)
        and range_at(code) > bars[0])
    # NOT HERE: "above the steps". The old form sat above the BAR,
    # which is above the steps, so it was above them too - a guard on
    # the new position, not a thing this round changed. Section 1.
    c['  its button is a secondary, not a second primary'] = (
        bool(frm) and 'action-primary' not in frm
        and 'action-secondary' in frm)
    c['  and the dates are sized to a date'] = (
        'sl-range-date' in code and 'width: auto' in code)
    c['  each label welded to its own input'] = (
        code.count('class="sl-range-pair"') == 2)
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

code = T.code_only(NOW[TPL])
frm = form_of(code)
# GUARDS - true before and after, and the round must not have broken
# them. Not in the dict above: the control re-asks that, and a guard
# put there fails for being correct.
ok('class="step-indicator"' in code
   and range_at(code) < code.find('class="step-indicator"'),
   'and it sits ABOVE the steps - with the claim above, that places '
   'it exactly where he asked: between the bar and Review Ingredients')
for probe in ('method="get"', 'name="from"', 'name="to"',
              'type="submit"'):
    ok(probe in frm, 'the form is still a GET carrying %s' % probe)
pblock = code[code.index('@media print'):] if '@media print' in code else ''
ok('.sl-range' in pblock,
   'and it still prints nothing - .sl-range is in SL-1 hide list')


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = {TPL: was(TPL)}
oldcode = T.code_only(BEFORE[TPL])
oldbars = [m.start() for m in BARS.finditer(oldcode)]
ok(len(oldbars) == 2,
   'CONTROL: before this round the page had TWO action bars',
   len(oldbars))
ok(oldcode[oldbars[0]:oldbars[0] + 120].find('<form') >= 0,
   'CONTROL: and the first one was the range form')
ok('action-primary' in form_of(oldcode),
   'CONTROL: whose button was a primary, beside Generate List')
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: and not one of this round claims held',
   'what held: %r' % (held,))


# ==========================================================================
head('3. RENDERED, at 1000 and 390 - BEFORE AND AFTER')
# ==========================================================================
# THE FINDING IS A MEASUREMENT. "Far too much space at the top of the
# page" is a height, and "FAR narrower" is a width; neither can be
# read out of a stylesheet that does not exist. The form is rendered
# alone, against base's real CSS, at both widths.
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

if sync_playwright is None or not os.path.isfile(FIXCSS):
    skip('the row renders', 'playwright or the Bootstrap fixture is absent')
else:
    BCSS = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style\s*>',
                                read(BASE), re.S | re.I))
    FIX = read(FIXCSS)

    def fill(t):
        t = re.sub(r'\{%.*?%\}', '', t, flags=re.S)
        t = re.sub(r'\{\{.*?\}\}', '2026-10-19', t, flags=re.S)
        return re.sub(r'\{#.*?#\}', '', t, flags=re.S)

    def measure(br, src, width):
        css = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style\s*>',
                                   src, re.S | re.I))
        raw = src[src.index('<form method="get"'):
                  src.index('</form>', src.index('<form method="get"')) + 7]
        doc = ('<!doctype html><meta charset=utf-8><style>%s</style>'
               '<style>%s</style><style>%s</style>'
               '<style>body{margin:0;padding:12px;background:#fff}</style>'
               '<body>%s' % (FIX, BCSS, css, fill(raw)))
        pg = br.new_page(viewport={'width': width, 'height': 320})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg.set_content(doc, wait_until='domcontentloaded')
        try:
            return pg.evaluate("""() => {
                const f = document.querySelector('form');
                const d = [...document.querySelectorAll('input[type=date]')];
                const b = document.querySelector('button');
                return {h: Math.round(f.getBoundingClientRect().height),
                        dates: d.map(x => Math.round(
                            x.getBoundingClientRect().width)),
                        btnW: Math.round(b.getBoundingClientRect().width),
                        lines: new Set(d.concat([b]).map(
                            e => Math.round(
                                e.getBoundingClientRect().top))).size};
            }""")
        finally:
            pg.close()

    with sync_playwright() as pw:
        br = pw.chromium.launch()
        try:
            for w, where in ((1000, 'desktop'), (390, 'phone')):
                a = measure(br, BEFORE[TPL], w)
                b = measure(br, NOW[TPL], w)
                print('')
                print('  --- %s, %dpx ---' % (where, w))
                print('     before  %3dpx tall  dates %s  button %dpx'
                      % (a['h'], a['dates'], a['btnW']))
                print('     after   %3dpx tall  dates %s  button %dpx'
                      % (b['h'], b['dates'], b['btnW']))
                if where == 'desktop':
                    ok(b['h'] < a['h'],
                       'desktop: the row is shorter - %dpx, was %dpx'
                       % (b['h'], a['h']), (a['h'], b['h']))
                    ok(b['lines'] == 1,
                       '  and everything is on ONE line, which is what '
                       'he asked for', b['lines'])
                    ok(max(b['dates']) < 250,
                       '  the dates are sized to a date: %s' % b['dates'],
                       b['dates'])
                    ok(max(a['dates']) > 600,
                       '  CONTROL: they really were stretched - %s'
                       % a['dates'], a['dates'])
                else:
                    ok(b['lines'] <= 2,
                       'phone: two lines at most, no orphaned label',
                       b['lines'])
                    ok(b['btnW'] > 100,
                       '  and the button is readable at %dpx - it was '
                       '%dpx before, with its words clipped'
                       % (b['btnW'], a['btnW']), (a['btnW'], b['btnW']))
                    # NOT "shorter on a phone". It is TALLER - 94px
                    # against 48 - and that is the right trade: the old
                    # row fitted by squeezing its button to 34px.
                    ok(b['dates'] and min(b['dates']) > 100,
                       '  and both dates are still usable: %s'
                       % b['dates'], b['dates'])
        finally:
            br.close()


# ==========================================================================
head('4. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once')
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_sl_range_row as PATCH                          # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
