# -*- coding: utf-8 -*-
"""test_overdue_date.py - Section TD round TD-1, 4 Oct 2026.

Demetri, on the Projects task list on a phone:

    "The Date, in Red, on a Task in the Task List on mobile, should fit the
     "!" on the right of the date, and not on the next line."

The span holds a date and a warning icon written on separate source lines,
so there is a space between them, and a space is a wrap opportunity. Narrow
the column enough and that is where it breaks.

HOW THIS SUITE MEASURES A WRAP, and why not the obvious way. Range
getClientRects() returns one rect per text fragment, not one per line: the
date is a text node and the icon is an element, so the count is two whether
or not the span wrapped. The first build of this suite read that count as a
line count and reported two lines in both directions, which would have
passed happily on an unfixed tree.

HEIGHT is the honest metric. One line is 15px, two is 39px. Section 3
narrows the container from 140px down to 60px and watches it:

    before   140:15  120:15  100:39  90:39  80:39  60:39
    after    140:15  120:15  100:15  90:15  80:15  60:15

So the threshold was 100px, the card column on a subtask card is under it,
and after the round there is no threshold at all. Section 3 asserts BOTH
rows - the before one as much as the after one - because a fix that cannot
be shown to have changed anything has not been shown to be a fix.

WHAT nowrap COSTS, and section 4 bounds it. A span that will not wrap can
overflow instead. The pair is 102px; the suite checks that the END of the
span still lands inside the card at 390, 360 and 320, so nothing is pushed
out of sight to buy the fix.
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

SCRATCH = _tempfile.mkdtemp(prefix='alv_overdue_')
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

SUFFIX = '.bak_overduedate'
ME = 'test_overdue_date.py'
PATCHER = 'apply_overdue_date.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

PAGE = os.path.join(alv_tree.roots()[0], 'projects', 'project_task_list.html')

BOXES = (140, 120, 100, 90, 80, 60)
ONE_LINE = 20          # a single 13px line measures 15; 20 is the margin

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
    """read(p + SUFFIX). Never read(p) against a frozen backup."""
    return read(p + SUFFIX)


# ------------------------------------------------------------- section 1

def section_1():
    print('\n1. the rule, and where it lives')
    if not ok(os.path.isfile(PAGE), 'project_task_list.html found'):
        return
    text = now(PAGE)
    m = re.search(r'\.date-value\s*\{(.*?)\}', text, re.S)
    ok(m is not None, 'the page declares .date-value')
    body = m.group(1) if m else ''
    ok(re.search(r'white-space\s*:\s*nowrap', body) is not None,
       '.date-value does not wrap',
       'this is the round')

    before = was(PAGE)
    mb = re.search(r'\.date-value\s*\{(.*?)\}', before, re.S)
    ok(mb is not None and 'nowrap' not in mb.group(1),
       'and it did wrap before the round',
       'if it did not, section 3 cannot fail in either direction')

    # One page, one name. A local class that spreads is a tree-wide change
    # nobody asked for.
    users = [alv_tree.rel(p) for p in alv_tree.templates()
             if 'date-value' in read(p)]
    ok(users == ['projects/project_task_list.html'],
       '.date-value is still used by exactly one page',
       'now used by %s' % users)


# ------------------------------------------------------------- section 2

def section_2():
    print('\n2. the markup that made the gap is unchanged')
    text = now(PAGE)
    ok('overdue-icon' in text, 'the warning icon is still rendered')
    m = re.search(r'<span class="date-value \{%.*?overdue.*?%\}">(.*?)</span>',
                  text, re.S)
    ok(m is not None, 'the overdue span is still shaped as this round read it')
    if m:
        ok('\n' in m.group(1),
           'the date and the icon are still on separate source lines',
           'if someone closed the gap in the markup instead, say so in the '
           'round rather than leaving two fixes for one defect')


# ------------------------------------------------------------- browser

SPAN = ('<span class="date-value overdue">\n  01/02/2026\n  '
        '<i class="fas fa-exclamation-triangle overdue-icon"></i>\n</span>')

DOC = ('<!doctype html><html><head><meta charset="utf-8">'
       '<style>%s</style><style>%s</style><style>%s</style>'
       '<style>body{margin:0}'
       # Font Awesome is a CDN away from this sandbox, so the glyph is
       # drawn here. Its width is what matters, not its shape.
       '.overdue-icon:before{content:"\\26A0";font-family:sans-serif}'
       '</style></head><body><div class="main-content with-topnav">'
       '<div id="box" style="width:%dpx">%s</div></div></body></html>')

LOOK = '''() => {
  const s = document.querySelector('.date-value.overdue');
  const b = s.getBoundingClientRect();
  const box = document.getElementById('box').getBoundingClientRect();
  return {h: Math.round(b.height), w: Math.round(b.width),
          right: Math.round(b.right), boxRight: Math.round(box.right)};
}'''

try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)


def section_3_and_4():
    print('\n3. rendered: the pair stays on one line however narrow it gets')
    if not HAVE_PW:
        skip('the browser sections', 'no playwright')
        return
    if not os.path.isfile(BOOT):
        skip('the browser sections', 'no bootstrap fixture')
        return

    boot = read(BOOT)
    base_css = '\n'.join(STYLE.findall(read(alv_tree.path_of('base.html'))))
    css_now = '\n'.join(STYLE.findall(now(PAGE)))
    css_was = '\n'.join(STYLE.findall(was(PAGE)))

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 390, 'height': 300})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        try:
            def run(css, bw):
                f = os.path.join(SCRATCH, 'probe.html')
                with open(f, 'w', encoding='utf-8') as fh:
                    fh.write(DOC % (boot, base_css, css, bw, SPAN))
                _goto(pg, f)
                pg.wait_for_timeout(80)
                return pg.evaluate(LOOK)

            hw = {b: run(css_was, b)['h'] for b in BOXES}
            hn = {b: run(css_now, b)['h'] for b in BOXES}
            print('        before  %s'
                  % '  '.join('%d:%d' % (b, hw[b]) for b in BOXES))
            print('        after   %s'
                  % '  '.join('%d:%d' % (b, hn[b]) for b in BOXES))

            for b in BOXES:
                ok(hn[b] <= ONE_LINE,
                   'one line in a %dpx column' % b,
                   '%dpx tall - it wrapped' % hn[b])

            broke = [b for b in BOXES if hw[b] > ONE_LINE]
            ok(broke,
               'the page really did wrap before the round',
               'it never wrapped at any width tested, so there was nothing '
               'to fix and this suite proves nothing')
            print('        it wrapped at %s - the card column on a subtask '
                  'card is under that.'
                  % ', '.join('%dpx' % b for b in broke))

            print('\n4. and nothing is pushed out of the card to pay for it')
            for w in (390, 360, 320):
                pg.set_viewport_size({'width': w, 'height': 300})
                r = run(css_now, w - 40)
                ok(r['right'] <= r['boxRight'] + 1,
                   'the span ends inside the card at %d' % w,
                   'span right %d, card right %d' % (r['right'], r['boxRight']))
        finally:
            br.close()


# ------------------------------------------------------------- section 5

def section_5():
    print('\n5. registration')
    for f in (PATCHER, ME):
        ok(os.path.isfile(os.path.join(ROOT, f)), '%s is on disk' % f)
    try:
        ok(SUFFIX in read(os.path.join(ROOT, 'alv_rounds.py')),
           '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
    except Exception as e:
        ok(False, 'alv_rounds.py readable', e)
    try:
        ok(ME in read(os.path.join(ROOT, PS1)),
           '%s is in the push suites' % ME)
    except Exception as e:
        ok(False, '%s readable' % PS1, e)


def main():
    print('test_overdue_date.py - TD-1, the date keeps its warning')
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
    print('test_overdue_date.py: all checks passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
