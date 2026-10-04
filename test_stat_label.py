# -*- coding: utf-8 -*-
"""test_stat_label.py - Section SL round SL-1, 4 Oct 2026.

Demetri, on the Projects task list switched to Greek:

    "The Completed Box Cuts off in Greek."

It was not cut off. It was drawn 41px past the right edge of its own tile,
across the border and over the tile beside it, because ΟΛΟΚΛΗΡΩΜΕΝΕΣ is one
word, `.alv-stat-label` had nothing to break on, and `.alv-stat` sets no
overflow. A browser does not clip what it is not told to clip.

THIS SUITE IS MOSTLY A BROWSER. A claim about whether a word fits in a box
is a measurement, and the text of a stylesheet is not one. Section 3 renders
the real base.html - the file as SL-1 left it and the file as SL-1 found it -
and compares scrollWidth against clientWidth on every label at six widths.
Before: 41px over at 1200 and above, 61px at 992. After: zero, everywhere.

WHY SIX WIDTHS AND NOT ONE. The defect lived only where base's 3-up phone
rule does not apply. That rule has carried `overflow-wrap: break-word` for
weeks, so a phone-only check would have found nothing wrong before the round
and nothing changed after it, and would have passed in both directions. A
suite that cannot fail is not a suite.

THE ORPHAN IS NOT A FAILURE HERE, AND SECTION 4 SAYS SO OUT LOUD. Breaking
inside a word can leave one character alone on the second line; on a 360px
phone the Greek for Completed breaks as ΟΛΟΚΛΗΡΩΜΕΝΕ / Σ. Demetri was shown
all three options rendered and chose the smallest:

    "Break the word (Recommended)"

So section 4 MEASURES the orphan and reports it without failing. If a later
round drops `text-transform: uppercase` - the lever that actually removes it
- that number goes to zero and this section will say so.
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

SCRATCH = _tempfile.mkdtemp(prefix='alv_statlabel_')
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
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_statlabel'
ME = 'test_stat_label.py'
PATCHER = 'apply_stat_label.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)

BASE = alv_tree.path_of('base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

# The label this round is about, and the page it was found on. Read from
# the template so the suite cannot test a string the app no longer holds.
TASKLIST = os.path.join(alv_tree.roots()[0], 'projects',
                        'project_task_list.html')

WIDTHS = (1920, 1440, 1200, 992, 768, 390, 360)

FAILS = []


def ok(cond, msg, detail=''):
    if cond:
        print('  ok    %s' % msg)
    else:
        print('  FAIL  %s' % msg)
        if detail:
            for line in str(detail).rstrip().splitlines():
                print('        %s' % line)
        FAILS.append(msg)
    return bool(cond)


def skip(msg, why):
    print('  --    %s skipped: %s' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    """The file as SL-1 found it. read(p + SUFFIX), never read(p) - a
    frozen backup is a different file, and reading the live one here is
    the defect this house has now made five times."""
    return read(p + SUFFIX)


# ------------------------------------------------------------- section 1

def section_1():
    print('\n1. the component carries the break, the variant does not')
    text = now(BASE)

    m = re.search(r'\.alv-stat-label\s*\{(.*?)\}', text, re.S)
    ok(m is not None, 'base declares .alv-stat-label')
    body = m.group(1) if m else ''
    ok('overflow-wrap' in body and 'break-word' in body,
       '.alv-stat-label breaks a long word',
       'this is the whole round')

    m3 = re.search(r'\.alv-stats\.is-3up \.alv-stat-label\s*\{(.*?)\}',
                   text, re.S)
    ok(m3 is not None, 'the 3-up variant still exists')
    if m3:
        ok('overflow-wrap' not in m3.group(1),
           'the 3-up variant no longer repeats it',
           'two rules declaring one thing is how they come to disagree')

    before = was(BASE)
    mb = re.search(r'\.alv-stat-label\s*\{(.*?)\}', before, re.S)
    ok(mb is not None and 'overflow-wrap' not in mb.group(1),
       'and it was not there before the round',
       'if it already was, this round changed nothing and the browser '
       'section below cannot fail')


# ------------------------------------------------------------- section 2

def section_2():
    print('\n2. the page that found it still has the labels')
    if not ok(os.path.isfile(TASKLIST), 'project_task_list.html found'):
        return
    text = read(TASKLIST)
    ok('alv-stats' in text and 'is-3up' in text,
       'the task summary uses the house stat component')
    n = len(re.findall(r'class="alv-stat-label"', text))
    ok(n == 3, 'three stat labels on the task list', 'found %d' % n)
    ok('Ολοκληρωμένες' in text,
       'the Greek label this round is named after is still there',
       'if the wording changed, re-measure before trusting this suite')


# -------------------------------------------------------- browser set-up

GR = [('5', 'Συνολικές Εργασίες'), ('0', 'Ολοκληρωμένες'),
      ('5', 'Εκκρεμείς')]
EN = [('5', 'Total Tasks'), ('0', 'Completed'), ('5', 'Pending')]

TILES = ('<div class="alv-stat"><div class="alv-stat-value">%s</div>'
         '<div class="alv-stat-label">%s</div></div>')

DOC = ('<!doctype html><html lang="el"><head><meta charset="utf-8">'
       '<style>%s</style><style>%s</style>'
       '<style>.task-summary{--alv-stats-cols:3}'
       'body{margin:0;background:#eef2f7}</style></head><body>'
       '<div class="main-content with-topnav"><div class="container">'
       '<div class="row"><div class="col-md-4" id="w" style="padding:10px">'
       '<div class="alv-stats task-summary is-3up">%s</div>'
       '</div></div></div></div></body></html>')

# scrollWidth against clientWidth is the question "does the text fit in the
# box it was given", asked of the browser rather than of a font metric
# table. The orphan count is the second line of a broken word being one
# character wide - measured with a Range, because the DOM has no other way
# to ask where a line box ended.
LOOK = '''() => {
  const out = [];
  document.querySelectorAll('.alv-stat-label').forEach(l => {
    const r = document.createRange();
    r.selectNodeContents(l);
    const rects = [...r.getClientRects()].map(x => Math.round(x.width));
    out.push({
      text: l.textContent.trim(),
      over: Math.round(l.scrollWidth - l.clientWidth),
      lines: rects.length,
      rects: rects,
      orphan: rects.length > 1 && Math.min(...rects) < 24
    });
  });
  return out;
}'''

try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)


def measure(pg, css, rows, width):
    f = os.path.join(SCRATCH, 'probe.html')
    with open(f, 'w', encoding='utf-8') as fh:
        fh.write(DOC % (read(BOOT), css,
                        ''.join(TILES % (v, l) for v, l in rows)))
    pg.set_viewport_size({'width': width, 'height': 320})
    _goto(pg, f)
    pg.wait_for_timeout(120)
    return pg.evaluate(LOOK)


# ------------------------------------------------------------- section 3

def section_3_and_4():
    print('\n3. rendered: no label leaves its tile, at any width')
    if not HAVE_PW:
        skip('the browser sections', 'no playwright')
        return
    if not os.path.isfile(BOOT):
        skip('the browser sections', 'no bootstrap fixture')
        return

    css_now = '\n'.join(STYLE.findall(now(BASE)))
    css_was = '\n'.join(STYLE.findall(was(BASE)))

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1200, 'height': 320})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        try:
            worst_was = {}
            worst_now = {}
            for w in WIDTHS:
                worst_was[w] = max(x['over']
                                   for x in measure(pg, css_was, GR, w))
                worst_now[w] = max(x['over']
                                   for x in measure(pg, css_now, GR, w))

            for w in WIDTHS:
                ok(worst_now[w] == 0,
                   'Greek labels stay inside their tiles at %d' % w,
                   '%dpx over' % worst_now[w])

            # THE CONTROL. The round must have CHANGED something, or every
            # check above would pass on an untouched tree and prove nothing.
            over_before = [w for w in WIDTHS if worst_was[w] > 0]
            ok(over_before,
               'the old base.html really did overflow somewhere',
               'it did not - either the backup is not pre-round or the '
               'defect was never reproducible, and section 3 is vacuous')
            print('        before the round: %s'
                  % ', '.join('%d:%dpx' % (w, worst_was[w])
                              for w in WIDTHS if worst_was[w]))

            for w in (1920, 1440, 1200, 992, 390, 360):
                res = measure(pg, css_now, EN, w)
                ok(max(x['over'] for x in res) == 0,
                   'English labels stay inside their tiles at %d' % w,
                   'the round must not have cost the common case anything')

            print('\n4. the orphan, measured and deliberately allowed')
            total = 0
            for w in WIDTHS:
                res = measure(pg, css_now, GR, w)
                n = sum(1 for x in res if x['orphan'])
                total += n
                if n:
                    bits = [(x['text'], x['rects'])
                            for x in res if x['orphan']]
                    print('        %4d  %d orphan(s)  %s' % (w, n, bits))
            print('        %d in total across %d widths.' % (total, len(WIDTHS)))
            print('        NOT a failure. Demetri was shown this rendered '
                  'beside the')
            print('        alternative and chose "Break the word '
                  '(Recommended)" over')
            print('        dropping uppercase, which is the only thing that '
                  'removes it.')
        finally:
            br.close()


# ------------------------------------------------------------- section 5

def section_5():
    print('\n5. registration')
    for f in (PATCHER, ME):
        ok(os.path.isfile(os.path.join(ROOT, f)), '%s is on disk' % f)
    try:
        rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
        ok(SUFFIX in rounds,
           '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
           'as_left_by cannot place this round without it')
    except Exception as e:
        ok(False, 'alv_rounds.py readable', e)
    try:
        ps1 = read(os.path.join(ROOT, PS1))
        ok(ME in ps1, '%s is in the push suites' % ME)
    except Exception as e:
        ok(False, '%s readable' % PS1, e)


def main():
    print('test_stat_label.py - SL-1, a stat label stays in its tile')
    section_1()
    section_2()
    section_3_and_4()
    section_5()
    print('\n%s' % ('-' * 68))
    if FAILS:
        print('FAILED %d check(s):' % len(FAILS))
        for f in FAILS:
            print('  - %s' % f)
        return 1
    print('test_stat_label.py: all checks passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
