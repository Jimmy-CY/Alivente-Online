# -*- coding: utf-8 -*-
"""test_issue_stats.py - Section DB round DB-7, 2 Oct 2026.

Demetri, with a screenshot of Dashboard -> a property -> Issues: "we
still need to move these three summary boxes to the top of the page."

SECTION 3 IS THE CLAIM, AND IT NEEDS A BROWSER. "Above the table" is not
a thing a grep can settle: source order is necessary and not sufficient -
a float, a flex order, a grid-row or an absolute position can put an
element that comes first in the markup underneath the thing it precedes.
So section 3 renders the real fragment against base's real stylesheet and
reads back where the two actually landed, at desktop and on a phone.

SECTION 4 IS THE COMPONENT. base's ALV-STAT owns the card, the grid, the
figure and the uppercase label, and the page kept seventeen rules saying
all of it again - including three left borders in #28a745, #ffc107 and
#0e7c8b, and the same three colours again on the icons. The tiles are
measured against a plain base tile to show the page is adding nothing but
a column count.

THE ICONS ARE GONE, AND THAT IS THE STANDARD, not an oversight: base's
tile is a figure and the words for it, and no stat strip in this app has
an icon. Asserted here so it reads as a decision.
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
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_issuestats'
ME = 'test_issue_stats.py'
PATCHER = 'apply_issue_stats.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)

PAGE = alv_tree.path_of('property_detail.html')
BASE = alv_tree.path_of('base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

# The thirteen rules and four phone declarations the page gave up, and
# the literals in them.
GONE = ('summary-card', 'issues-summary', 'summary-icon', 'summary-number',
        'summary-label', 'summary-content')
LITERALS = ('#28a745', '#ffc107', '#6c757d')

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
    """BEFORE this round. as_left_by() returns the file as the round LEFT
    it, which is the opposite of a control - A1's lesson, and it cost a
    push."""
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


# CO-1, 3 Oct 2026 - this was written out here, as it was in 46
# other files. It lives in alv_tree now, with the repair that
# stops `accept="image/*"` reading as a comment opener and hiding
# 94 lines of the Add Passport form from every gate in the tree.
code_only = alv_tree.code_only


P_NOW, P_WAS = code_only(now(PAGE)), code_only(was(PAGE)) if was(PAGE) else ''

print('=' * 74)
print('%s - DB-7, THE ISSUE FIGURES' % ME)
print('=' * 74)

# ==========================================================================
head('1. THEY ARE ABOVE THE TABLE, AND THEY WERE BELOW IT')
# ==========================================================================
i_stats = P_NOW.find('alv-stats issues-stats')
i_table = P_NOW.find('issues-table-container')
ok(i_stats > 0 and i_table > 0 and i_stats < i_table,
   'the figures come before the table in the markup',
   '%d / %d' % (i_stats, i_table))
if P_WAS:
    w_sum = P_WAS.find('issues-summary')
    w_tab = P_WAS.find('issues-table-container')
    ok(w_sum > 0 and w_tab > 0 and w_sum > w_tab,
       'CONTROL: they came AFTER it before this round - on a property with '
       'sixteen issues, two screens down', '%d / %d' % (w_sum, w_tab))
else:
    skip('the ordering control', 'no %s backup' % SUFFIX)

ok('{% if property_issues %}' in P_NOW,
   'and they are still inside the property_issues guard')
_seg = P_NOW[P_NOW.index('{% if property_issues %}'):]
ok(_seg.find('alv-stats issues-stats') < _seg.find('{% else %}'),
   '  so a property with no issues shows its empty state, not three zeroes')

# ==========================================================================
head('2. ON base\'S TILE, WITH THE PAGE SAYING ONLY THE COLUMN COUNT')
# ==========================================================================
for g in GONE:
    ok(g not in P_NOW, 'the page has no %s left' % g)
if P_WAS:
    had = [g for g in GONE if g in P_WAS]
    ok(len(had) == len(GONE),
       'CONTROL: it had all six of those names', had)
    css_was = '\n'.join(STYLE.findall(P_WAS))
    n_rules = len(re.findall(r'(?m)^\.(?:summary|issues-summary)[^\n{}]*\{',
                             css_was))
    ok(n_rules >= 10,
       '  across %d top-level rule(s), for a component base already owns'
       % n_rules, n_rules)
    # PER-LITERAL COUNTS, NOT PRESENCE. The first draft asserted each
    # literal was "gone now" - and property_detail.html carries 112 of
    # them, so #28a745 appears seven more times in rules this round never
    # touched. The check was broader than the claim, for the tenth time
    # in five rounds. What is true, and worth saying, is how many
    # occurrences each rule-set took with it.
    css_now = '\n'.join(STYLE.findall(P_NOW))
    for lit, drop in (('#28a745', 2), ('#ffc107', 2), ('#0e7c8b', 2),
                      ('#2c3e50', 1), ('#6c757d', 1), ('#f8f9fa', 1),
                      ('#dee2e6', 1)):
        a, b = css_now.count(lit), css_was.count(lit)
        ok(b - a == drop,
           '  %s: %d -> %d, the %d the summary rules held'
           % (lit, b, a, drop), '%d -> %d' % (b, a))
else:
    skip('the rules control', 'no %s backup' % SUFFIX)

own = re.findall(r'(?m)^\.issues-stats\s*\{([^}]*)\}',
                 '\n'.join(STYLE.findall(P_NOW)))
ok(len(own) == 1, 'the page declares .issues-stats exactly once', len(own))
if own:
    keys = set(k.split(':')[0].strip() for k in own[0].split(';') if ':' in k)
    ok(keys <= {'--alv-stats-cols', 'margin-bottom'},
       '  and says only the column count and a margin - the one thing base '
       'leaves to a page, as it does for .filter-grid', sorted(keys))
    ok('--alv-stats-cols: 3' in own[0].replace('  ', ' '),
       '  three columns, because this screen has three figures', own[0])

seg = P_NOW[i_stats:i_table]
ok(seg.count('alv-stat-value') == 3 and seg.count('alv-stat-label') == 3,
   'three tiles, each a figure and the words for it', seg.count('alv-stat'))
ok('alv-stat alv-stat-good' in seg, '  Resolved takes the good tone')
ok('alv-stat alv-stat-attn' in seg, '  Unresolved takes attn')
ok(re.search(r'<div class="alv-stat">\s*<div class="alv-stat-value">'
             r'\{\{ total_issues_count \}\}', seg) is not None,
   '  and Total takes NO tone - a total is not a verdict', seg[-260:])
ok('fa-check-circle' not in seg and 'fa-clock' not in seg
   and 'fa-list' not in seg,
   'the three icons are gone - base\'s tile is a figure and a label, and '
   'no stat strip in this app has an icon')

# ==========================================================================
head('3. CHROMIUM - "ABOVE" IS A POSITION, NOT A LINE NUMBER')
# ==========================================================================
# Source order is necessary and not sufficient: a float, a flex order, a
# grid-row or an absolute position can put a first-in-markup element
# below the thing it precedes. So this measures the rendered box.
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)

FRAG_NOW = ('<div class="issues-section">'
            '<h5 class="section-heading">Property Issues</h5>'
            '<div class="alv-stats issues-stats" id="figs">'
            '<div class="alv-stat alv-stat-good"><div class="alv-stat-value">'
            '16</div><div class="alv-stat-label">Resolved</div></div>'
            '<div class="alv-stat alv-stat-attn"><div class="alv-stat-value">'
            '0</div><div class="alv-stat-label">Unresolved</div></div>'
            '<div class="alv-stat"><div class="alv-stat-value">16</div>'
            '<div class="alv-stat-label">Total Issues</div></div></div>'
            '<div class="issues-table-container" id="tbl">'
            '<table class="table"><tbody>'
            + '<tr><td>Issue</td><td>Something</td></tr>' * 16 +
            '</tbody></table></div></div>')
FRAG_WAS = ('<div class="issues-section">'
            '<h5 class="section-heading">Property Issues</h5>'
            '<div class="issues-table-container" id="tbl">'
            '<table class="table"><tbody>'
            + '<tr><td>Issue</td><td>Something</td></tr>' * 16 +
            '</tbody></table>'
            '<div class="issues-summary mt-3" id="figs"><div class="row">'
            '<div class="col-md-4"><div class="summary-card resolved">'
            '<div class="summary-content"><div class="summary-number">16</div>'
            '<div class="summary-label">Resolved</div></div></div></div>'
            '</div></div></div></div>')

LOOK = '''() => {
  const f = document.getElementById('figs').getBoundingClientRect();
  const t = document.getElementById('tbl').getBoundingClientRect();
  const tiles = [...document.querySelectorAll('.alv-stat, .summary-card')]
      .map(e => Math.round(e.getBoundingClientRect().width));
  return {figTop: Math.round(f.top), tabTop: Math.round(t.top),
          figBottom: Math.round(f.bottom), tiles: tiles,
          cols: getComputedStyle(document.getElementById('figs'))
                  .gridTemplateColumns};
}'''

if HAVE_PW and os.path.isfile(BOOT):
    boot, base_css = read(BOOT), '\n'.join(STYLE.findall(read(BASE)))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1280, 'height': 900})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        def draw(page_text, frag, name, w):
            f = os.path.join(SCRATCH, name)
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write('<!doctype html><html><head><meta charset="utf-8">'
                         '<style>%s</style><style>%s</style><style>%s</style>'
                         '</head><body><div class="container">%s</div>'
                         '</body></html>'
                         % (boot, base_css,
                            '\n'.join(STYLE.findall(page_text)), frag))
            pg.set_viewport_size({'width': w, 'height': 900})
            _goto(pg, f)
            pg.wait_for_timeout(45)
            return pg.evaluate(LOOK)

        for w, label in ((1280, 'desktop'), (390, 'phone')):
            r = draw(now(PAGE), FRAG_NOW, 'now%d.html' % w, w)
            ok(r['figBottom'] <= r['tabTop'],
               '%-8s the figures RENDER above the table - bottom %d, table '
               'top %d' % (label, r['figBottom'], r['tabTop']), r)
            ok(len(r['tiles']) == 3, '  three tiles', r['tiles'])
            if w == 1280:
                ok(len(r['cols'].split()) == 3,
                   '  in three columns', r['cols'])
                ok(len(set(r['tiles'])) == 1,
                   '  of equal width - %dpx each' % r['tiles'][0], r['tiles'])

        if P_WAS:
            r = draw(was(PAGE), FRAG_WAS, 'was.html', 1280)
            ok(r['figTop'] > r['tabTop'],
               'CONTROL: before this round they rendered BELOW it - %dpx '
               'down the page, past sixteen rows'
               % (r['figTop'] - r['tabTop']), r)
        else:
            skip('the before render', 'no %s backup' % SUFFIX)
        br.close()
elif not HAVE_PW:
    skipped += 7
else:
    skip('the browser section', 'no bootstrap fixture')
    skipped += 6

# ==========================================================================
head('4. NOTHING ELSE ON THE PAGE MOVED')
# ==========================================================================
if P_WAS:
    for what, pat in (('<div', r'<div\b'), ('</div', r'</div\s*>'),
                      ('<table', r'<table\b'), ('{% if', r'\{%\s*if\b'),
                      ('{% endif', r'\{%\s*endif\s*%\}'),
                      ('{% for', r'\{%\s*for\b')):
        a, b = len(re.findall(pat, P_NOW)), len(re.findall(pat, P_WAS))
        # TWENTY OUT, TEN IN. The old markup was a wrapper, a .row,
        # three .col-md-4, three .summary-card, and inside each card an
        # icon, a content box, a number and a label - 20 divs. base's
        # tile is a .alv-stats and, per tile, the tile plus a value and a
        # label - 10. Net minus ten, counted rather than guessed: the
        # first draft of this said minus one, having counted the wrapper
        # and forgotten everything inside it.
        want = b - 10 if what in ('<div', '</div') else b
        ok(a == want, '%-10s %d -> %d' % (what, b, a),
           '%d, wanted %d' % (a, want))
    f_a = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', P_NOW))
    f_b = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', P_WAS))
    ok(f_a < f_b, 'and the page lost %d literal colour(s): %d -> %d'
       % (f_b - f_a, f_b, f_a))
else:
    skip('the shape checks', 'no %s backup' % SUFFIX)

ok(not [i for i, line in enumerate(now(PAGE).split('\n'), 1)
        if '{#' in line and '#}' not in line],
   'no Django comment spans lines - the lexer has no DOTALL')
css = '\n'.join(STYLE.findall(P_NOW))
ok(css.count('{') == css.count('}'), 'and the CSS still balances')

# ==========================================================================
head('5. REGISTERED')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_jsescape'),
       '  and AFTER .bak_jsescape, the round it followed')
except Exception as e:
    skip('ROUNDS', str(e))
print('\n    $suites now lists %d suite(s).'
      % len(re.findall(r"'test_[a-z0-9_]+\.py'", ps)))

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
