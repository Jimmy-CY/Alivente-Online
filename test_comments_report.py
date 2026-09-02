"""test_comments_report.py - the Comments Report table joins the standard.

    python test_comments_report.py

Run from the repo root, after apply_comments_report.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 2 RENDERS the page at three widths and two media, because every
    interesting claim here is a CASCADE claim and CSS does not tell you who
    won. Three of them cannot be read off the source at all:
      - the comment cell is base's card TITLE on a phone, and this page
        overrides it. base's rule and the obvious override are BOTH (0,2,2);
        a tie is decided by document order across two files. Rendered, or
        not known.
      - the phone Delete sits inside a <form> inside a GRID, so the form is
        the grid item and the button is its child. Whether the button fills
        the cell is a layout question.
      - the page-local @media block was unqualified, so it fired on paper.
        The fix is one word and its proof is a print-media render.
  * SECTION 3 is the CONTROL half. Every "it is a table now" check would
    still pass if the card view had simply been killed everywhere, and every
    "they look the same" check passes on a probe that sees nothing. So the
    card view is required to STILL WORK at 390px, and a deliberately styled
    element is measured beside the ones under test.
  * SECTION 1 hunts the page's re-implementation of the standard by name,
    and SECTION 4 asserts the banner is UNTOUCHED - it belongs to its own
    round, and a round that quietly widens is worse than one that stops.
"""
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
CR = os.path.join(T, 'comments_report.html')

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


def nocomment_html(text):
    """Strip HTML comments, single-line Django comments, CSS comments and JS
       line comments. A CHECK THAT READS TEXT CATCHES PROSE - this suite's
       own explanations name every class it says is gone."""
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{#[^\n]*?#\}', '', text)   # NOT re.S - Django has no DOTALL

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


for p in (BASE, CR):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the repo root' % p)
BS, C = read(BASE), read(CR)
if 'class="alv-table"' not in C:
    print('\n! not patched - run apply_comments_report.py first.')
    sys.exit(1)
BC, CC = nocomment_html(BS), nocomment_html(C)

# ===========================================================================
head('1. the page stops re-implementing the table standard')
# ===========================================================================
check("CONTROL: the round's prose still names .report-table",
      'report-table' in C)
check('CONTROL: .. and it is gone once stripped', 'report-table' not in CC)

for dead in ('report-table', 'status-badge', 'status-resolved',
             'status-unresolved', 'status-open', 'btn-delete-icon',
             'delete-cell'):
    check('%s is gone' % dead,
          not re.search(r'(?<![\w-])%s(?![\w-])' % dead, CC))

# The drifted literals those rules carried - and ONLY the ones that were
# unique to them. A first draft of this scan also asked for #f8f9fa, #dee2e6,
# #dc3545 and #495057, and reported four failures for colours that live in
# the MODAL and in .user-cell, neither of which this round touches. A check
# wider than its round reports the rest of the file as a defect. The four are
# named here so a later reader knows they were considered and left.
for lit in ('#e9ecef',                                        # td rule
            '#d4edda', '#155724', '#c3e6cb',                  # resolved
            '#fff3cd', '#856404', '#ffeaa7',                  # unresolved
            '#d1ecf1', '#0c5460', '#bee5eb',                  # open
            '#c82333', 'rgba(220, 53, 69',                    # delete hover
            '#999'):                                          # the em-dash
    check('  and so is the literal %s' % lit, lit not in CC)

check('the table is an .alv-table', 'class="alv-table"' in CC)
check('  wrapped in the standard .table-container',
      re.search(r'class="table-container"[\s\S]{0,400}class="alv-table"',
                CC) is not None)

for lbl in ('Date', 'Property', 'Status', 'User'):
    check('  and the %s cell carries a data-label' % lbl,
          CC.count('data-label="%s"' % lbl) == 1)
check('  the COMMENT cell carries none - it is the card title',
      re.search(r'<td class="comment-cell"(?![^>]*data-label="\w)', CC)
      is not None)

# THE STATUS MAP LIVES TWICE, and that is the point of checking it twice.
check('status: Resolved is the good pill', CC.count('alv-pill-good') == 2,
      '%d (template + JS map)' % CC.count('alv-pill-good'))
check('  Unresolved and Open are both attn', CC.count('alv-pill-attn') == 3,
      '%d (template ORs them, the JS map spells both)'
      % CC.count('alv-pill-attn'))
check('  and anything else is neutral, not a verdict',
      CC.count('alv-pill-neutral') == 2)
check('  the JS is a MAP, not a ternary that can drift from the template',
      'STATUS_PILL' in CC and 'alv-pill ${statusClass}' in CC)

check('delete is the house icon button',
      'icon-action-btn icon-delete' in CC)
check('  in a .desktop-action-cell .cell-actions with .row-actions',
      re.search(r'desktop-action-cell cell-actions', CC) is not None
      and 'class="row-actions"' in CC)
check('  with a phone tile beside it',
      'mobile-action-bar cols-1' in CC
      and 'mobile-action-icon icon-color-delete' in CC)
check('  and BOTH still post to delete_comment with a csrf token',
      CC.count("{% url 'delete_comment' item.comment_id %}") == 2
      and CC.count('{% csrf_token %}') == 2)
check('  and both still carry the period, so the redirect lands back here',
      CC.count('name="period"') == 2)

check('no inline text-align survives on the table',
      not re.search(r'<t[hd][^>]*style="[^"]*text-align', CC))

# THE PRINT LEAK, page-local twin.
check('the page block is screen-only',
      '@media (max-width: 768px)' not in C
      and '@media screen and (max-width: 768px)' in C)

# ===========================================================================
head('2. rendered: who actually wins')
# ===========================================================================
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('  SKIP  playwright not installed')
    sync_playwright = None

BOOT = None
for _c in (os.path.join(ROOT, 'test_fixture_bootstrap413.css'),
           '/tmp/bootstrap.min.css'):
    if os.path.exists(_c):
        BOOT = open(_c, encoding='utf-8').read()
        break
if BOOT is None:
    print('  !! test_fixture_bootstrap413.css missing - browser checks skipped')
    sync_playwright = None

if sync_playwright is not None:
    def css(src):
        return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', src, re.S))

    LONG = ('Roof flashing above the second-floor bathroom has lifted again '
            'and the ceiling stain has spread about 40cm since the last '
            'inspection; the contractor wants access on a weekday morning.')

    # base's <style> blocks come FIRST, then the page's - the real document
    # order, because that is the whole question for the comment cell.
    FIX = """<!doctype html><meta charset=utf-8>
<style>%s</style><style>%s</style><style>%s</style>
<style>body{margin:0;padding:0}
 /* CONTROL: an element styled on purpose, so a probe that reports nothing
    is distinguishable from a probe that reports agreement. */
 #loud { font-weight: 800 !important; font-size: 27px !important; }
</style>

<div class="report-container">
  <div class="report-header">
    <div class="report-header-left"><h1>Comments Report</h1></div>
    <div class="stat-box"><div class="stat-value">42</div>
      <div class="stat-label">Total Comments</div></div>
  </div>
  <div class="table-container">
    <table class="alv-table">
      <thead><tr>
        <th style="width: 35%%">Comment</th>
        <th style="width: 10%%">Date</th>
        <th style="width: 16%%">Property</th>
        <th class="status-cell" style="width: 11%%">Status</th>
        <th style="width: 11%%">User</th>
        <th class="cell-actions" style="width: 7%%">Actions</th>
      </tr></thead>
      <tbody>
        <tr id="r1">
          <td class="comment-cell" id="cmt">%s</td>
          <td class="date-cell" data-label="Date">01/09/2026</td>
          <td class="property-cell" data-label="Property">Kingsway 12</td>
          <td class="status-cell" data-label="Status">
            <span class="alv-pill alv-pill-good" id="pill">Resolved</span></td>
          <td class="user-cell" data-label="User">
            <span class="alv-tag comment-author">SS</span></td>
          <td class="desktop-action-cell cell-actions" data-label="">
            <span class="row-actions"><form style="display:inline">
              <button type="submit" class="icon-action-btn icon-delete"
                      id="del">D</button></form></span></td>
          <td class="mobile-action-bar cols-1" data-label="">
            <form><button type="submit" class="mobile-action-btn" id="mdel">
              <i class="mobile-action-icon icon-color-delete">T</i>
              <span class="mobile-action-label">Delete</span></button></form></td>
        </tr>
        <tr id="r2">
          <td class="comment-cell">Short one.</td>
          <td class="date-cell" data-label="Date">02/09/2026</td>
          <td class="property-cell" data-label="Property">Elm Court</td>
          <td class="status-cell" data-label="Status">
            <span class="alv-pill alv-pill-neutral">Deferred</span></td>
          <td class="user-cell" data-label="User">
            <span class="alv-tag comment-author">DM</span></td>
          <td class="desktop-action-cell cell-actions" data-label="">
            <span class="row-actions"><form style="display:inline">
              <button class="icon-action-btn icon-delete">D</button>
            </form></span></td>
          <td class="mobile-action-bar cols-1" data-label="">
            <form><button class="mobile-action-btn">
              <i class="mobile-action-icon icon-color-delete">T</i>
              <span class="mobile-action-label">Delete</span></button></form></td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
<div id="loud">control</div>
""" % (BOOT, css(BS), css(C), LONG)

    _f = os.path.join(tempfile.gettempdir(), 'comments_report_fixture.html')
    with open(_f, 'w', encoding='utf-8') as fh:
        fh.write(FIX)

    PROBE = """() => {
      const cs = s => getComputedStyle(document.querySelector(s));
      const box = s => {
        const e = document.querySelector(s);
        if (!e) return null;
        const r = e.getBoundingClientRect();
        return {w: Math.round(r.width), h: Math.round(r.height),
                x: Math.round(r.left), y: Math.round(r.top)};
      };
      const pre = s => {
        const e = document.querySelector(s);
        return getComputedStyle(e, '::before').content;
      };
      // A <td>'s box is the ROW's height, so comparing two cells' boxes says
      // nothing about vertical-align. A Range over the cell's contents gives
      // where the TEXT actually sits, which is the thing top vs middle moves.
      const textTop = s => {
        const e = document.querySelector(s);
        const r = document.createRange();
        r.selectNodeContents(e);
        const b = r.getBoundingClientRect();
        return Math.round(b.top);
      };
      const cmt = cs('#cmt');
      return {
        thead:  cs('thead').display,
        tr:     cs('#r1').display,
        td:     cs('.date-cell').display,
        datePre: pre('.date-cell'),
        cmtPre:  pre('#cmt'),
        cmtSize: cmt.fontSize, cmtWeight: cmt.fontWeight,
        cmtMax:  cmt.maxWidth,
        loudSize: cs('#loud').fontSize, loudWeight: cs('#loud').fontWeight,
        pillBg: cs('#pill').backgroundColor,
        deskCell: cs('.desktop-action-cell').display,
        mobBar:  cs('.mobile-action-bar').display,
        bDesk: box('#del'), bMob: box('#mdel'),
        barBox: box('.mobile-action-bar'),
        cmtBox: box('#cmt'), rowBox: box('#r1'),
        dateBox: box('.date-cell'),
        cmtTextTop: textTop('#cmt'), dateTextTop: textTop('.date-cell'),
        dateVAlign: cs('.date-cell').verticalAlign,
        headBg: cs('.report-header').backgroundImage,
        bodyScrollW: document.documentElement.scrollWidth,
      };
    }"""

    def shot(pw, width, media):
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': width, 'height': 1000})
        pg.goto('file://' + _f)
        if media:
            pg.emulate_media(media=media)
        r = pg.evaluate(PROBE)
        b.close()
        return r

    with sync_playwright() as pw:
        DESK = shot(pw, 1200, 'screen')
        PAPER = shot(pw, 718, 'print')     # A4 portrait content box
        NARROW = shot(pw, 718, 'screen')   # the SAME width, on screen
        PHONE = shot(pw, 390, 'screen')

    # -- THE CONTROL, first. -------------------------------------------------
    check('CONTROL: the probe can read a deliberately styled element',
          DESK['loudSize'] == '27px' and DESK['loudWeight'] == '800',
          '%s / %s' % (DESK['loudSize'], DESK['loudWeight']))

    # -- desktop -------------------------------------------------------------
    check('desktop: it is a real table',
          DESK['thead'] == 'table-header-group'
          and DESK['tr'] == 'table-row' and DESK['td'] == 'table-cell')
    check('  no data-label prefixes leak onto the desktop view',
          DESK['datePre'] in ('none', 'normal', '""'), DESK['datePre'])
    check('  the pill is tinted, not transparent',
          DESK['pillBg'] not in ('rgba(0, 0, 0, 0)', 'transparent'),
          DESK['pillBg'])
    check('  the desktop action cell shows and the phone bar does not',
          DESK['deskCell'] == 'table-cell' and DESK['mobBar'] == 'none',
          '%s / %s' % (DESK['deskCell'], DESK['mobBar']))
    check('  the icon button is the house 34px square',
          DESK['bDesk']['w'] == 34 and DESK['bDesk']['h'] == 34,
          '%dx%d' % (DESK['bDesk']['w'], DESK['bDesk']['h']))
    # base sets vertical-align: middle; this page keeps top. Measured on the
    # TEXT, not the cell - a td's box is the row's height either way, which
    # is how the first draft of this check passed 119px against 119px and
    # proved nothing.
    check('  the row is tall enough for top vs middle to differ at all',
          DESK['rowBox']['h'] >= 60, '%dpx' % DESK['rowBox']['h'])
    check('  and the date TEXT sits on the comment\'s first line, not its middle',
          abs(DESK['cmtTextTop'] - DESK['dateTextTop']) <= 3,
          'comment text y=%d date text y=%d (row %dpx)'
          % (DESK['cmtTextTop'], DESK['dateTextTop'], DESK['rowBox']['h']))
    check('  which is vertical-align: top, against base\'s middle',
          DESK['dateVAlign'] == 'top', DESK['dateVAlign'])

    # -- phone ---------------------------------------------------------------
    check('phone: rows become cards', PHONE['tr'] == 'block'
          and PHONE['thead'] == 'none')
    check('  and the labels come from data-label, not a content literal',
          'Date' in PHONE['datePre'], PHONE['datePre'])
    check('  the comment cell takes no label - it IS the card title',
          PHONE['cmtPre'] in ('none', 'normal', '""'), PHONE['cmtPre'])

    # THE CASCADE QUESTION. base makes td:first-child 16px/600. This page
    # overrides it, and both selectors are (0,2,2) before the extra `tr`.
    check('  BUT the comment reads at BODY weight, not as a 16px headline',
          PHONE['cmtWeight'] in ('400', 'normal')
          and PHONE['cmtSize'] == '14px',
          '%s %s' % (PHONE['cmtSize'], PHONE['cmtWeight']))
    # THE CAP IS INVISIBLE AT 390px - the viewport is under 500 anyway. It
    # only bites on a wide phone or a narrow window, so it is measured at
    # 718px on screen, where a 500px cap would leave the card 200px short.
    check('  and its 500px desktop cap comes off, measured where it would bite',
          NARROW['cmtBox']['w'] >= NARROW['rowBox']['w'] - 40,
          'comment %dpx in a %dpx card'
          % (NARROW['cmtBox']['w'], NARROW['rowBox']['w']))

    check('  the desktop action cell steps aside for the phone bar',
          PHONE['deskCell'] == 'none' and PHONE['mobBar'] == 'grid',
          '%s / %s' % (PHONE['deskCell'], PHONE['mobBar']))
    # THE FORM-INSIDE-A-GRID QUESTION.
    check('  the Delete tile fills its column despite the <form> between them',
          abs(PHONE['bMob']['w'] - PHONE['barBox']['w']) <= 2,
          'button %dpx in a %dpx bar'
          % (PHONE['bMob']['w'], PHONE['barBox']['w']))
    check('  and it clears the 44px touch target',
          PHONE['bMob']['h'] >= 44, '%dpx' % PHONE['bMob']['h'])
    check('  nothing pushes the page sideways',
          PHONE['bodyScrollW'] <= 392, '%dpx' % PHONE['bodyScrollW'])

    # -- paper ---------------------------------------------------------------
    check('PRINT: at 718px on paper it is a TABLE, not a stack of cards',
          PAPER['thead'] == 'table-header-group'
          and PAPER['tr'] == 'table-row' and PAPER['td'] == 'table-cell',
          '%s / %s / %s' % (PAPER['thead'], PAPER['tr'], PAPER['td']))
    check('  no data-label prefix prints',
          PAPER['datePre'] in ('none', 'normal', '""'), PAPER['datePre'])
    check('  and neither action bar prints',
          PAPER['deskCell'] == 'none' and PAPER['mobBar'] == 'none',
          '%s / %s' % (PAPER['deskCell'], PAPER['mobBar']))
    check('  the pill outlines instead of tinting',
          PAPER['pillBg'] in ('rgba(0, 0, 0, 0)', 'transparent'),
          PAPER['pillBg'])

# ===========================================================================
head('3. controls: the fix must not be "the card view is gone"')
# ===========================================================================
if sync_playwright is not None:
    # THE ONE THAT MATTERS. Every check above would still pass if the phone
    # view had simply been deleted - a table is a table at any width. The
    # SAME 718px must give cards on screen and a table on paper, or the
    # breakpoint has merely moved.
    check('the SAME 718px gives CARDS on screen and a TABLE on paper',
          NARROW['tr'] == 'block' and PAPER['tr'] == 'table-row',
          'screen=%s print=%s' % (NARROW['tr'], PAPER['tr']))
    check('  and 390px still builds a card, so nothing was killed outright',
          PHONE['tr'] == 'block' and PHONE['mobBar'] == 'grid')
    check('  a printed page is not just a narrow screen: labels differ',
          NARROW['datePre'] != PAPER['datePre'],
          'screen=%s print=%s' % (NARROW['datePre'], PAPER['datePre']))

# ===========================================================================
head('4. scope: the banner belongs to its own round')
# ===========================================================================
check('the teal gradient banner is untouched',
      'linear-gradient(135deg, #0e7c8b 0%, #0a5e6a 100%)' in C
      and '.report-header {' in C)
check('  and so is its .stat-box', '.stat-box {' in C
      and 'rgba(255, 255, 255, 0.2)' in C)
if sync_playwright is not None:
    check('  rendered: the banner still carries a gradient',
          'gradient' in DESK['headBg'], DESK['headBg'][:48])
# CC, not C. The new print block's own comment LISTS the rules it handed
# back to base - including .page-action-buttons - so reading the raw file
# finds the round's explanation of the removal and calls it the removal
# failing. Nineteenth instance of the same lesson.
_PRINT = CC[CC.index('@media print'):CC.index('@media screen and')]
check("the page's print block keeps ONLY what base cannot know",
      '.report-header' in _PRINT
      and 'page-action-buttons' not in _PRINT
      and 'modal' not in _PRINT, _PRINT.strip()[:60].replace('\n', ' '))

# The tint round's work, and the modal, must both survive.
check('the author chip survives the round',
      CC.count('alv-tag comment-author') == 2)
check('the modal still builds and still opens on a comment click',
      'showIssueDetails' in CC and 'issue-details-compact' in CC)
check('  and its comment history is still .comment-item',
      'class="comment-item"' in CC)

# Django comments do not span lines - a multi-line {# #} PRINTS.
for m in re.finditer(r'\{#', C):
    check('a {# #} comment stays on one line',
          '#}' in C[m.start():].split('\n')[0])

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('\n  failures:')
    for f in FAILED:
        print('   - %s' % f)
print('=' * 72)
sys.exit(1 if FAIL else 0)
