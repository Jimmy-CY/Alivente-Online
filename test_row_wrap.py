# -*- coding: utf-8 -*-
"""test_row_wrap.py - Section RA round RA-3, 5 Oct 2026.

RA-2 widened the drift report and found 37 of the tree's 119 icon buttons
outside any .row-actions wrapper. The glyph census could reach them once
widened; the ORDERING standard still could not, because order is a
property of a group and there was no group. RA-3 makes the groups on eight
pages: 14 runs, 21 buttons - and repairs the two tags that were hiding a
ninth page's wrapper from the tooling altogether.

SPLIT BY PAGE, NOT BY SHAPE - section 5 is the record of why. I first
proposed carving this by what each button sits in. Three pages MIX those
shapes, and converting by shape would have left a .row-actions holding
one action while two siblings stood outside it. The report would then
read the group as complete and check the order of a fragment, which is
worse than leaving the page alone. So: nine pages converted whole, and
the four mixed or scripted pages held back entire.

SECTION 3 IS THE ONE THAT EARNS ITS KEEP, and it is about a button that
was already broken. crs/fi_form.html drew its delete button at 15.5px -
under half its size - because the row is a grid whose actions column is
40px and a bare button, as a flex item, was being shrunk to fit. Wrapped,
it stops shrinking and takes its proper 34px, which was 1px more than the
page had. The wrapper did not break that page; it revealed that the
button had been squashed for as long as the row has been a grid. The
column goes to 44px - the house tap floor - and both numbers come right.
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
import subprocess
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
import alv_tree
import alv_rowactions as RA

try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_rowwrap'
ME = 'test_row_wrap.py'
PATCHER = 'apply_row_wrap.py'
PS1 = 'Push-PendingChanges.ps1'
BOOTF = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

from apply_row_wrap import (EXPECT, loose, runs_of, FI_FORM,
                            GRID_NEW, ASSET, TAGS)

HELD_BACK = ['create_meal_plan.html', 'household_member_management.html',
             'invoices.html', 'physical_invoice_list.html']

FAILS = []


def ok(cond, msg, detail=''):
    if cond:
        print('  ok    %s' % msg)
    else:
        print('  FAIL  %s' % msg)
        if detail:
            for line in str(detail).rstrip().splitlines()[:8]:
                print('        %s' % line)
        FAILS.append(msg)
    return bool(cond)


def head(t):
    print('\n' + t)


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX)


def path_of(rel):
    hits = [q for q in alv_tree.templates()
            if alv_tree.rel(q).replace(os.sep, '/') == rel]
    return hits[0] if hits else None


print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. sixteen runs, twenty-four buttons, nine pages')

tot_runs = tot_btns = 0
for name, (want_runs, want_btns) in sorted(EXPECT.items()):
    p = path_of(name)
    if not p or not os.path.exists(p + SUFFIX):
        ok(False, '%s has a backup' % name)
        continue
    before = runs_of(was(p))
    got = (len(before), sum(len(r) for r in before))
    ok(got == (want_runs, want_btns),
       '%-38s had %d loose run(s) of %d button(s)' % (name, got[0], got[1]),
       'expected %d of %d' % (want_runs, want_btns))
    tot_runs += got[0]
    tot_btns += got[1]
    ok(not loose(now(p)), '  and has none loose now', loose(now(p)))
# FOURTEEN AND TWENTY-ONE, NOT SIXTEEN AND TWENTY-FOUR. asset_detail.html
# left the round: its three buttons were already in a wrapper, and the
# only reason the tooling could not see it was a <span> closed with
# </button> and a .row-actions <span> never closed at all. Wrapping them
# again nested one wrapper inside another, which test_detail_property
# caught. The two tags are repaired instead, and the page needs nothing
# else. RA-2's census of 37 loose buttons was really 34.
ok((tot_runs, tot_btns) == (14, 21),
   '  %d runs, %d buttons in all' % (tot_runs, tot_btns),
   'expected 14 and 21')

# ==========================================================================
head('1b. the page that was never loose')

ap = path_of(ASSET)
a_was = was(ap) if os.path.exists(ap + SUFFIX) else ''
ok(bool(a_was), '%s has a backup' % ASSET)
if a_was:
    opens = len(re.findall(r'<span\b', a_was))
    closes = len(re.findall(r'</span>', a_was))
    ok(opens != closes,
       '%s really was unbalanced - %d <span>, %d </span>'
       % (ASSET, opens, closes),
       'it balanced - then wrappers() was blind for another reason')
    ok(len(RA.wrappers(a_was)) == 0,
       '  and wrappers() could see NOTHING on it, wrapper included',
       'it saw %d - then the three buttons were never miscounted'
       % len(RA.wrappers(a_was)))
    ok('row-actions' in a_was,
       '  though the page had carried a .row-actions all along')

    a_now = now(ap)
    o2, c2 = len(re.findall(r'<span\b', a_now)), len(re.findall(r'</span>', a_now))
    ok(o2 == c2, '  the tags are repaired - %d and %d' % (o2, c2))
    w = RA.wrappers(alv_tree.code_only(a_now))
    ok(len(w) == 1, '  and wrappers() now sees exactly one', len(w))
    ok(w and len(RA.BTN_FULL.findall(w[0][2])) == 3,
       '  holding all three buttons, as it always meant to')
    ok(not loose(a_now), '  so the page has nothing loose and needed no wrapper')
    # AND NOT A WRAPPER INSIDE A WRAPPER, which is what wrapping it gave.
    ok('row-actions' not in w[0][2] if w else False,
       '  with no second wrapper inside the first')

# ==========================================================================
head('2. each run became ONE wrapper, around the whole group')

for name in sorted(EXPECT):
    p = path_of(name)
    if not p or not os.path.exists(p + SUFFIX):
        continue
    before = runs_of(was(p))
    wraps = RA.wrappers(alv_tree.code_only(now(p)))
    # every run's buttons must now sit inside one wrapper, together
    inner_counts = [len(RA.BTN_FULL.findall(w[2])) for w in wraps]
    want = sorted(len(r) for r in before)
    ok(sorted(c for c in inner_counts if c) == want,
       '%-38s wrappers hold %s button(s)'
       % (name, '+'.join(str(c) for c in sorted(c for c in inner_counts if c))),
       'the runs were %s - a group split across two wrappers would read as '
       'two action columns' % '+'.join(str(x) for x in want))

# ==========================================================================
head('3. the button that had been squashed all along')

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

FA_STUB = ('i[class*="fa-"]{display:inline-block;width:1em;height:1em;'
           'vertical-align:-0.125em;background:#bbb;}')


def css_of(x):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', x, re.S | re.I))


def detag(s):
    s = re.sub(r'\{%\s*(block|endblock|extends|load|csrf_token)[^%]*%\}', '', s)
    s = re.sub(r'\{%\s*(else|endif|endfor|empty)\s*%\}', '', s)
    s = re.sub(r'\{%[^%]*%\}', '', s)
    s = re.sub(r'\{\{[^}]*\}\}', 'Sample', s)
    return re.sub(r'\{#.*?#\}', '', s, flags=re.S)


BASECSS = css_of(alv_tree.code_only(now(alv_tree.path_of('base.html'))))


def page_html(raw):
    body = re.sub(r'<style[^>]*>.*?</style>', '', raw, flags=re.S | re.I)
    body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.S | re.I)
    return ('<!doctype html><html><head><meta charset="utf-8"><style>%s</style>'
            '<style>%s</style><style>%s</style><style>%s</style></head>'
            '<body style="margin:0">%s</body></html>'
            % (read(BOOTF), BASECSS, FA_STUB, css_of(raw), detag(body)))


SIZES = """() => {
  const d = document.documentElement;
  return {over: d.scrollWidth - d.clientWidth,
          boxes: [...document.querySelectorAll('.icon-action-btn')]
            .map(b => { const r = b.getBoundingClientRect();
                        return Math.round(r.width*10)/10 + 'x'
                             + Math.round(r.height); })};
}"""


def paint(raw, width, br):
    pg = br.new_page(viewport={'width': width, 'height': 1000})
    pg.set_content(page_html(raw))
    pg.wait_for_timeout(240)
    r = pg.evaluate(SIZES)
    pg.close()
    return r


if sync_playwright is None:
    print('  --    the renders  (playwright missing)')
else:
    exe = '/opt/pw-browsers/chromium'
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))
        fi = path_of(FI_FORM)
        a, b = paint(was(fi), 1180, br), paint(now(fi), 1180, br)
        ok(a['boxes'] and float(a['boxes'][0].split('x')[0]) < 20,
           'crs/fi_form drew its button at %s - under half its size'
           % (a['boxes'][0] if a['boxes'] else '?'),
           'it did not, so the finding behind the 44px column is wrong')
        ok(b['boxes'] and float(b['boxes'][0].split('x')[0]) == 34.0,
           '  and now draws it at %s, the size it is everywhere else'
           % (b['boxes'][0] if b['boxes'] else '?'))
        ok(b['over'] == 0,
           '  with no overflow, because the column went to 44px',
           'overflow %+d - the grid widening did not take' % b['over'])
        ok(GRID_NEW in now(fi), '  and the grid says 44px, the tap floor')

        # EVERY OTHER PAGE: the wrapper must not have moved a button.
        head('4. and on the other eight, nothing moved')
        for name in sorted(EXPECT):
            if name == FI_FORM:
                continue
            p = path_of(name)
            for w in (1180, 390):
                x, y = paint(was(p), w, br), paint(now(p), w, br)
                ok(x['boxes'] == y['boxes'] and x['over'] == y['over'],
                   '%-38s @%-5d %d button(s), unchanged'
                   % (name, w, len(y['boxes'])),
                   'was %s over %+d; now %s over %+d'
                   % (','.join(sorted(set(x['boxes'])))[:26], x['over'],
                      ','.join(sorted(set(y['boxes'])))[:26], y['over']))
        br.close()

# ==========================================================================
head('5. the four pages held back, held back whole')

# COUNTED INCLUDING SCRIPT HERE, which loose() excludes on purpose.
# create_meal_plan.html builds all three of its buttons inside a
# JavaScript template literal, so loose() - whose job is to tell the
# patcher what it may safely edit - correctly reports none. Asking it
# "are they still loose?" got the answer "there are none", and this
# section passed a page it was meant to be guarding. Count what is
# THERE, not what is editable.
def unwrapped_anywhere(src):
    spans = [(a, b) for a, b, _ in RA.wrappers(src)]
    return [m for m in RA.BTN_FULL.finditer(src)
            if not any(a <= m.start() < b for a, b in spans)]


WHY = {
    'create_meal_plan.html': 'built inside a JavaScript template literal',
    'household_member_management.html': 'mixes plain markup with two forms',
    'invoices.html': 'its one button is inside a form, inside a cell',
    'physical_invoice_list.html': 'five of its six are each in their own form',
}

for name in HELD_BACK:
    p = path_of(name)
    n = len(unwrapped_anywhere(now(p))) if p else 0
    ok(p is not None and n > 0,
       '%-38s still has %d unwrapped, as intended - %s'
       % (name, n, WHY[name]),
       'it has none - then it was converted, and this round claims it was '
       'not')
    if p:
        ok(not os.path.exists(p + SUFFIX),
           '  and this round did not touch it at all')

# NO PAGE IS HALF CONVERTED. This is the whole reason for splitting by
# page: a wrapper holding one action while its siblings stand outside is
# worse than no wrapper, because the report then checks the order of a
# fragment and calls it clean.
mixed = []
for p in alv_tree.templates():
    src = alv_tree.code_only(now(p))
    if RA.wrappers(src) and unwrapped_anywhere(src):
        mixed.append(alv_tree.rel(p))
ok(not mixed,
   'and no page in the tree has a wrapper AND a loose button',
   '\n'.join(mixed))

# ==========================================================================
head('6. what the report says now')

out = subprocess.run([sys.executable, 'Show-RowActionDrift.py'],
                     capture_output=True, text=True, cwd=ROOT).stdout
m = re.search(r'(\d+) wrapper\(s\) on (\d+) page\(s\)', out)
ok(m is not None, 'the report runs')
if m:
    print('      %s wrapper(s) on %s page(s)' % (m.group(1), m.group(2)))
    ok(int(m.group(1)) >= 41,
       '  %s wrappers, up from 30 before RA-3' % m.group(1), m.group(1))
m2 = re.search(r'NOT IN A \.row-actions WRAPPER - (\d+) button', out)
ok(m2 is not None and int(m2.group(1)) == 13,
   '  and %s loose button(s) left, down from 37'
   % (m2.group(1) if m2 else '?'),
   'the four held-back pages hold 13 between them')
ok('Every action column is in house order.' in out,
   '  every column, the 16 new ones included, is in house order')
ok('Nothing drifting' in out, '  and nothing is drifting')

# ==========================================================================
head('7. the control - a wrapper that splits a group')

victim = path_of('categories_management.html')
ok(victim is not None, 'a victim page was found')
if victim:
    src = now(victim)
    # Plant the mistake this round exists to avoid: a run split in two.
    planted = src.replace('<span class="row-actions">', '', 1)
    ok(planted != src, '  the control could be planted')
    ok(bool(loose(planted)),
       '  and the census catches a group left outside a wrapper',
       'it did not - then section 1 proves nothing')
    ok(not loose(now(victim)), '  and the page itself is clean again')

# ==========================================================================
head('8. registration')

ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s is in the push suites' % ME)

# ==========================================================================
print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
print()
print('  NOT PROVED HERE: that the 13 buttons still loose are harmless.')
print('  They are on four pages this round deliberately did not touch -')
print('  three that mix forms with plain markup, and one that builds its')
print('  buttons inside a JavaScript template literal. RA-3b and RA-3c.')
