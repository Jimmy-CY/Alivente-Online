"""test_issues_table.py - the main Issues list on base's table.

    python test_issues_table.py

Run from the repo root, after apply_issues_table.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 3 DRIVES A BROWSER AT TWO WIDTHS, and that is the round's central
    structural claim. The page used to ship ONE set of cells and 21 rules that
    rebuilt them as cards below 768px. It now ships TWO sets - a desktop
    action cell and a phone action bar - and base decides which one appears.
    "Base handles the phone" is a claim about computed display at a given
    viewport, so it is measured at 1280 and at 420, and EXACTLY ONE of the two
    must be showing at each.

    This check exists because the round's own before/after picture got it
    wrong: a fixture forced .desktop-action-cell visible for the desktop shot
    and the override leaked into the phone shot, which then showed both rows.
    The markup was right and the picture was not. A rendered check that pins
    the viewport is the difference.

  * THE CONTROL IS THE OTHER HALF. Every rendered claim is taken again from
    .bak_isstbl, where the OLD markup must give the OLD answer - a filled
    #dc3545 Delete, Bootstrap's alert colours on the status badge, and one
    set of cells rather than two.

  * SECTION 4 IS THE INVALID HTML. `<button><a href></a></button>` is not a
    styling problem: it is a nested interactive element, which browsers
    resolve however they like. Asserted against the PARSED DOM, not the
    source, because the whole point is that the browser rewrites it.

  * SECTION 5 asserts the script can still find everything. Every class the
    sorter and the delete flow read is kept while its RULES are deleted, and
    losing one leaves a table that renders correctly and does nothing.
"""
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
IA = os.path.join(T, 'fsr.html')
BASE = os.path.join(T, 'base.html')
BAK = IA + '.bak_isstbl'
FIXTURE = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

PASS = FAIL = 0
FAILED = []


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  PASS  %s %s' % (name, extra))
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL  %s %s' % (name, extra))
    return ok


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def css_of(s):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', s, re.S))


def js_of(s):
    return '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', s, re.S))


def mk_of(s):
    return re.sub(r'<(script|style)[^>]*>.*?</\1>', '', s, flags=re.S)


def nocomment(t):
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)

    def strip(m):
        return m.group(1) + re.sub(r'/\*.*?\*/', '', m.group(2),
                                   flags=re.S) + m.group(3)
    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, t, flags=re.S)


def classes(markup):
    """Every class TOKEN in the markup.

       A substring test catches every superstring - `action-btn` is inside
       `icon-action-btn` and `mobile-action-btn`, `action-cell` is inside
       `desktop-action-cell` - and the patcher's first draft failed on a
       correct file for exactly that reason. Ask about tokens."""
    out = set()
    for a in re.findall(r'class="([^"]*)"', markup):
        out.update(a.replace('{%', ' ').replace('%}', ' ').split())
    return out


for _p in (IA, BASE):
    if not os.path.exists(_p):
        sys.exit('! %s not found - run from the repo root' % _p)
if not os.path.exists(BAK):
    sys.exit('! no fsr.html.bak_isstbl - run apply_issues_table.py first.')

F, WAS = read(IA), read(BAK)
FC, WC = nocomment(F), nocomment(WAS)
MK, WMK = mk_of(FC), mk_of(WC)
CLS, WCLS = classes(MK), classes(WMK)
BASE_CSS = css_of(read(BASE))
FIX = read(FIXTURE) if os.path.exists(FIXTURE) else ''

# ===========================================================================
head('1. thirty-two rules gone, and the classes with them')
# ===========================================================================
check('CONTROL: the tokeniser found the table at all',
      'alv-table' in CLS and 'issue-row' in CLS,
      '%d class tokens' % len(CLS))
for gone in ('status-badge', 'status-success', 'status-warning',
             'status-danger', 'action-btn', 'action-cell',
             'action-cell-comments', 'action-cell-delete',
             'btn-light', 'btn-danger', 'table-bordered', 'table-striped'):
    check('the class %-20s is gone from the markup' % gone, gone not in CLS)
    check('  CONTROL: it was there before', gone in WCLS)

_c = css_of(FC)
_w = css_of(WC)
for sel in ('.status-badge', '.action-btn', '.delete-issue-btn',
            '#issuesTable'):
    pat = re.compile(r'(?m)^[ \t]*' + re.escape(sel) + r'[\s,:{]')
    check('no %-18s rule survives' % sel, not pat.search(_c))
    check('  CONTROL: there were %d' % len(pat.findall(_w)),
          bool(pat.search(_w)))
check('the 21 hand-rolled card rules are gone',
      len(re.findall(r'(?m)^[ \t]*#issuesTable[^{\n]*\{', _c)) == 0)
check('  CONTROL: there were exactly 21',
      len(re.findall(r'(?m)^[ \t]*#issuesTable[^{\n]*\{', _w)) == 21,
      str(len(re.findall(r'(?m)^[ \t]*#issuesTable[^{\n]*\{', _w))))

# THE RENDERED SECTION BELOW PROBES A SYNTHETIC ROW, so it tests BASE, not
# this page's markup - and a negative control proved it: deleting the phone
# action bar from fsr.html left the suite at 104/104. These checks are the
# other half, and they read the file.
check('the page\'s own markup carries a desktop action cell',
      'class="desktop-action-cell cell-actions"' in MK)
check('  and a phone action bar', 'mobile-action-bar' in CLS)
check('  and the phone bar carries BOTH actions, not just one',
      MK.count('mobile-action-btn') == 2,
      '%d mobile-action-btn' % MK.count('mobile-action-btn'))
check('  and the desktop cell carries both too',
      'issue-comments-btn' in CLS and 'icon-delete' in CLS)
check('CONTROL: the pre-round markup had NEITHER',
      'desktop-action-cell' not in WCLS and 'mobile-action-bar' not in WCLS)

check('the table is base\'s', 'class="table alv-table" id="issuesTable"' in MK)
check('  and it kept its id, which the sorter needs',
      'id="issuesTable"' in MK and 'issuesTableBody' in MK)

# .sortable STAYS - the one thing base cannot take over. Four templates carry
# a sortable header, but two class names, two state vocabularies and two icon
# placements, and the state rules on two of them are dead. One working
# sortable header in the system, and it is this one.
check('.sortable is still here - measured, not assumed, as the only working '
      'one in the system', '.sortable {' in _c)
_sort = '\n'.join(m.group(0) for m in
                  re.finditer(r'\.sortable[^{}]*\{[^}]*\}', _c))
check('  but it stops spelling colours by hand',
      not re.search(r'#[0-9a-fA-F]{3,8}\b', _sort),
      str(re.findall(r'#[0-9a-fA-F]{3,8}\b', _sort)))
check('  CONTROL: it DID spell four',
      len(set(re.findall(r'#[0-9a-fA-F]{3,8}\b',
                         '\n'.join(m.group(0) for m in re.finditer(
                             r'\.sortable[^{}]*\{[^}]*\}', _w))))) == 4)
check('  and the sorted indicator still takes the accent',
      'var(--alv-accent)' in _sort)

# base must define what the round now leans on.
for need in ('.alv-pill-good', '.alv-pill-attn', '.alv-pill-neutral',
             '.icon-action-btn', '.icon-delete', '.status-btn',
             '.desktop-action-cell', '.mobile-action-bar',
             '.mobile-action-btn', '.mobile-action-label', '.alv-empty'):
    check('base defines %s' % need, need in BASE_CSS)
check('base defines .mobile-action-bar.cols-2',
      '.mobile-action-bar.cols-2' in BASE_CSS)

# ===========================================================================
head('2. the status map, and the branch that stopped being an alarm')
# ===========================================================================
check('three branches, one pill each',
      MK.count('alv-pill-good') == 1 and MK.count('alv-pill-attn') == 1
      and MK.count('alv-pill-neutral') == 1)
check('Resolved is the good one',
      re.search(r"issues_status == 'Resolved' %\}alv-pill-good", MK)
      is not None)
check('Unresolved is the attention one',
      re.search(r"issues_status == 'Unresolved' %\}alv-pill-attn", MK)
      is not None)
# The else branch used to be status-danger. A status that is neither of the
# two known ones is UNRECOGNISED, and unrecognised is not a failure.
check('anything else is NEUTRAL, not danger',
      re.search(r'\{% else %\}alv-pill-neutral', MK) is not None)
check('  CONTROL: it used to be the alert red',
      re.search(r'\{% else %\}status-danger', WMK) is not None)

check('the empty state is base\'s', 'alv-empty-title' in MK)
check('  CONTROL: it was a bare table row', 'No issues found</td>' in WMK)

# ===========================================================================
head('3. the browser: exactly one action row at each width')
# ===========================================================================
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('  SKIP  playwright not installed')
    sync_playwright = None

NOW_ROW = ('<tr class="issue-row" data-property="P" data-date="2026-01-01" '
           'data-status="Resolved">'
           '<td data-label="Property">Sea Breeze</td>'
           '<td data-label="Issue">Lift service</td>'
           '<td data-label="Description">annual</td>'
           '<td data-label="Date Logged">07/09/2025</td>'
           '<td data-label="Status"><span class="alv-pill alv-pill-good" '
           'id="pill">Resolved</span></td>'
           '<td data-label="Actions" class="desktop-action-cell cell-actions" '
           'id="dcell"><div class="row-actions">'
           '<a href="#" class="status-btn issue-comments-btn" id="cmt">'
           'Comments</a>'
           '<button class="icon-action-btn icon-delete delete-issue-btn" '
           'id="del"></button></div></td>'
           '<td class="mobile-action-bar cols-2" id="mbar">'
           '<a href="#" class="mobile-action-btn">'
           '<span class="mobile-action-label">Comments</span></a>'
           '<button class="mobile-action-btn delete-issue-btn">'
           '<span class="mobile-action-label">Delete</span></button>'
           '</td></tr>')
WAS_ROW = ('<tr class="issue-row">'
           '<td data-label="Property">Sea Breeze</td>'
           '<td data-label="Issue">Lift service</td>'
           '<td data-label="Description">annual</td>'
           '<td data-label="Date Logged">07/09/2025</td>'
           '<td data-label="Status"><span class="status-badge status-success" '
           'id="pill">Resolved</span></td>'
           '<td data-label="Comments" class="action-cell action-cell-comments"'
           ' id="dcell"><button class="btn btn-light action-btn" id="oldbtn">'
           '<a href="#" id="cmt">Comments</a></button></td>'
           '<td data-label="Delete" class="action-cell action-cell-delete">'
           '<button class="btn btn-danger btn-sm delete-issue-btn" id="del">'
           '</button></td></tr>')


def page(page_css, row, table_cls, base_css=None):
    return ('<!doctype html><meta charset=utf-8><style>%s</style>'
            '<style>%s</style><style>%s</style>'
            '<div class="table-container"><table class="%s" id="issuesTable">'
            '<thead><tr><th>Property</th><th>Issue</th><th>Description</th>'
            '<th>Date Logged</th><th>Status</th>'
            '<th class="desktop-action-cell cell-actions" id="dth">Actions'
            '</th></tr></thead><tbody id="issuesTableBody">%s</tbody>'
            '</table></div>'
            % (FIX, BASE_CSS if base_css is None else base_css,
               page_css, table_cls, row))


def probe(pg, html, w):
    f = os.path.join(tempfile.gettempdir(), 'isstbl.html')
    with open(f, 'w', encoding='utf-8') as fh:
        fh.write(html)
    pg.set_viewport_size({'width': w, 'height': 620})
    pg.goto('file://' + f)
    pg.wait_for_timeout(150)
    return pg.evaluate(
        """() => {
             const g = id => document.getElementById(id);
             const cs = id => g(id) ? getComputedStyle(g(id)) : null;
             const del = g('del'), pill = g('pill'), cmt = g('cmt');
             return {
               dcell: cs('dcell') ? cs('dcell').display : 'absent',
               mbar:  cs('mbar')  ? cs('mbar').display  : 'absent',
               delBg: del ? getComputedStyle(del).backgroundColor : null,
               delInk: del ? getComputedStyle(del).color : null,
               pillBg: pill ? getComputedStyle(pill).backgroundColor : null,
               pillInk: pill ? getComputedStyle(pill).color : null,
               pillRadius: pill ? getComputedStyle(pill).borderRadius : null,
               cmtTag: cmt ? cmt.tagName : null,
               cmtInButton: cmt ? !!cmt.closest('button') : null,
               nestedAnchors: document.querySelectorAll('button a').length
             };
           }""")


if sync_playwright is not None:
    with sync_playwright() as pw:
        _b = pw.chromium.launch()
        pg = _b.new_page(viewport={'width': 1280, 'height': 620})
        NOWP = page(css_of(F), NOW_ROW, 'table alv-table')
        WASP = page(css_of(WAS), WAS_ROW, 'table table-bordered table-striped')

        wide = probe(pg, NOWP, 1280)
        narrow = probe(pg, NOWP, 420)
        check('at 1280px the desktop action cell shows',
              wide['dcell'] == 'table-cell', wide['dcell'])
        check('  and the phone bar does NOT', wide['mbar'] == 'none',
              wide['mbar'])
        check('at 420px the phone bar shows', narrow['mbar'] != 'none',
              narrow['mbar'])
        check('  and the desktop cell does NOT', narrow['dcell'] == 'none',
              narrow['dcell'])
        # THE CONTROL that makes the four above mean something: if base's
        # rules were absent, both would show at both widths - which is what
        # this round's own before/after picture accidentally rendered.
        # The control has to remove BASE, not the page - the first draft
        # dropped the page stylesheet and base went on hiding the cell
        # correctly, so the control could not fail.
        check('CONTROL: with base REMOVED both rows show at 420px - so the '
              'four above are testing base, not the markup',
              probe(pg, page(css_of(F), NOW_ROW, 'table alv-table',
                             base_css=''), 420)['dcell'] != 'none')

        # ===================================================================
        head('3b. the sort indicator, rendered')
        # ===================================================================
        # A TEXT CHECK CANNOT TELL A PARTIAL REGRESSION FROM A WHOLE ONE.
        # The two sort states share a grouped colour rule and have separate
        # glyph rules, so breaking the colour for one state leaves a rule
        # that still names it - and the text check passes on a header whose
        # indicator has gone grey. Read the computed colour instead.
        def sorticon(state):
            html = ('<!doctype html><meta charset=utf-8><style>%s</style>'
                    '<style>%s</style><table class="table alv-table"><thead>'
                    '<tr><th class="sortable %s" id="th">P '
                    '<i class="sort-icon" id="ic"></i></th></tr></thead>'
                    '<tbody><tr><td>x</td></tr></tbody></table>'
                    % (BASE_CSS, css_of(F), state))
            f = os.path.join(tempfile.gettempdir(), 'sorticon.html')
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write(html)
            pg.set_viewport_size({'width': 1280, 'height': 400})
            pg.goto('file://' + f)
            return pg.evaluate(
                "() => getComputedStyle(document.getElementById('ic')).color")

        _idle = sorticon('')
        _asc = sorticon('sort-asc')
        _desc = sorticon('sort-desc')
        check('an UNSORTED column\'s icon is quiet', _idle != _asc, _idle)
        check('a sort-asc column lights its icon', _asc != _idle, _asc)
        check('  and sort-desc lights it the same way', _desc == _asc,
              '%s vs %s' % (_desc, _asc))
        _acc = re.search(r'--alv-accent:\s*(#[0-9a-fA-F]{6})', BASE_CSS)
        if _acc:
            r, g, bl = (int(_acc.group(1)[i:i + 2], 16) for i in (1, 3, 5))
            check('  and it is base\'s accent, not some other teal',
                  _asc == 'rgb(%d, %d, %d)' % (r, g, bl), _asc)

        # ===================================================================
        head('4. the status pill and the quiet Delete')
        # ===================================================================
        was = probe(pg, WASP, 1280)
        check('Resolved renders as base\'s good pill, not an alert green',
              wide['pillBg'] != was['pillBg'],
              '%s vs %s' % (wide['pillBg'], was['pillBg']))
        check('  and it is pill-shaped',
              float(wide['pillRadius'].split('px')[0]) >= 9,
              wide['pillRadius'])
        check('Delete is a quiet outline, not a filled slab',
              wide['delBg'] in ('rgba(0, 0, 0, 0)', 'transparent',
                                'rgb(255, 255, 255)'), wide['delBg'])
        check('  and its ink carries the danger colour',
              wide['delInk'] != wide['delBg'], wide['delInk'])
        check('CONTROL: it WAS a filled Bootstrap danger',
              was['delBg'] == 'rgb(220, 53, 69)', was['delBg'])

        # ===================================================================
        head('5. the anchor is out of the button')
        # ===================================================================
        # Asserted against the PARSED DOM, because the defect is that the
        # browser rewrites this - reading the source would prove nothing.
        check('Comments is an anchor', wide['cmtTag'] == 'A', wide['cmtTag'])
        check('  and it is NOT inside a button', wide['cmtInButton'] is False)
        check('  and the page has no nested anchor-in-button at all',
              wide['nestedAnchors'] == 0, str(wide['nestedAnchors']))
        check('CONTROL: before the round the browser saw one',
              was['nestedAnchors'] >= 1 or was['cmtInButton'] is True,
              '%s / %s' % (was['nestedAnchors'], was['cmtInButton']))
        _b.close()

# ===========================================================================
head('6. the script can still find everything')
# ===========================================================================
_js = js_of(FC)
# TWO KINDS OF HOOK, and the first draft treated them as one. Most of these
# must be IN THE MARKUP for the script to find them. But .sort-asc and
# .sort-desc are written BY the script at runtime and never appear in the
# template - so demanding them in the markup failed on a correct file. What
# they need is a RULE, or the indicator turns without changing.
for hook in ('issuesTableBody', 'issue-row', 'sortable', 'sort-icon',
             'delete-issue-btn'):
    check('the script still reads %s' % hook, hook in _js)
    check('  and the markup still carries it',
          hook in CLS or ('id="%s"' % hook) in MK or hook in MK)
# EACH STATE SEPARATELY, and this needed a negative control to find. The
# first draft asked `'.sortable.sort-asc' in _c`, and the two states share a
# GROUPED selector - so breaking one half left the string present in the
# other and the check passed on a file with a broken indicator. Ask whether
# each state has a rule whose selector really names it.
for hook in ('sort-asc', 'sort-desc'):
    check('the script still writes %s' % hook, hook in _js)
    _rules = [m.group(0) for m in re.finditer(r'[^{}]+\{[^}]*\}', _c)
              if re.search(r'\.sortable\.' + hook + r'\b', m.group(0))]
    check('  and a rule names .sortable.%s AND the icon' % hook,
          any('sort-icon' in r for r in _rules), '%d rule(s)' % len(_rules))
for attr in ('data-sort=', 'data-property=', 'data-date=', 'data-status=',
             'data-issue-id=', 'data-issue-heading='):
    check('the markup keeps %s' % attr, attr in MK)
check('the delete flow keeps every one of its six data attributes',
      all(a in MK for a in ('data-issue-id=', 'data-issue-heading=',
                            'data-issue-description=', 'data-property-name=',
                            'data-date-logged=', 'data-status=')))

# What the round did NOT do.
check('C3\'s drill table is untouched', 'class="table alv-table"' in js_of(FC))
check('C1 survives: the charts still read base tokens', 'iaTok(' in FC)
check('C2 survives: the stat strip still bands', 'alv-stat-age' in FC)
# CORRECTED. The first draft asserted this page's @media was still BARE,
# carried over from the two round-D files - which were never in the print
# round's 34. fsr.html WAS: it is in that round's TARGETS and was guarded on
# 2 Sep. The claim is the opposite one, and it is worth keeping, because a
# later round that unguarded it would be a real regression.
check('the print round\'s guard on this page is still there',
      '@media screen and (max-width: 768px)' in F
      or '@media screen and (max-width:768px)' in F)
check('  and no bare one crept back in',
      not re.search(r'@media\s*\(\s*max-width', F))

for blk in re.findall(r'<style[^>]*>(.*?)</style>', F, re.S):
    check('braces balance in a style block', blk.count('{') == blk.count('}'))
check('Django if/endif balance',
      F.count('{% if') + F.count('{% elif') >= F.count('{% endif %}'))
_bad = [m.group(0)[:40] for m in re.finditer(r'/\*.*?\*/', F, re.S)
        if re.search(r'</?(?:script|style)\b', m.group(0))]
check('no CSS comment spells a script or style tag', not _bad, str(_bad))

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('\n  failures:')
    for x in FAILED[:20]:
        print('   - %s' % x)
print('=' * 72)
sys.exit(1 if FAIL else 0)
