"""test_comment_tint.py - colour stops encoding who wrote a comment.

    python test_comment_tint.py

Run from the repo root, after apply_comment_tint.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 2 RENDERS all three comment surfaces and asks the browser the only
    question that matters: do two comments by DIFFERENT authors look the same?
    THE FIXTURE MUST RENDER WHAT THE PAGE RENDERS. Its report rows were
    <table class="report-table"> until 2 Sep, when the Comments Report round
    deleted that class - after which the table was styled by NOTHING and this
    section passed 80 of 80 on two unstyled rows, because every check here
    asserts an ABSENCE of difference. A stale harness that fails tells you it
    is stale; one that passes just stops testing. It is .alv-table now.
    Same row background, same text colour, same weight. A control renders a
    deliberately washed row beside them, so "they match" cannot pass on a
    probe that is blind.
  * SECTION 1 hunts the six expressions of the split across three files - the
    row wash, the author's name colour, the history-card wash, the legend, and
    the two .detail-row rules that coloured the comment TEXT - and asserts the
    author chip carries ONE tone, because two would rebuild the split.
  * IT ALSO GUARDS A NON-COSMETIC FIX: two of the three screens chose the
    colour by comparing a username to the string literal 'SS'. That literal is
    gone. The OTHER comparison, `== user_initials`, decides who may edit a
    comment and must survive - so the suite requires it to still be there.
"""
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
CR = os.path.join(T, 'comments_report.html')
FS = os.path.join(T, 'friday_status_report.html')
FD = os.path.join(T, 'fsr_details.html')

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


for p in (BASE, CR, FS, FD):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the repo root' % p)
BS, C, F, D = read(BASE), read(CR), read(FS), read(FD)
if 'alv-tag comment-author' not in C:
    print('\n! not patched - run apply_comment_tint.py first.')
    sys.exit(1)
BC, CC, FC, DC = (nocomment_html(x) for x in (BS, C, F, D))
FILES = (('comments_report', C, CC), ('friday_status_report', F, FC),
         ('fsr_details', D, DC))

# ===========================================================================
head('1. six expressions of one split, in three files')
# ===========================================================================
check("CONTROL: the round's prose still names admin-comment",
      'admin-comment' in C)
check('CONTROL: .. and it is gone once stripped', 'admin-comment' not in CC)

for name, raw, c in FILES:
    for _dead in ('admin-comment', 'user-comment', 'admin-comment-item',
                  'user-comment-item', 'admin-user', 'regular-user',
                  'ss-comment', 'regular-comment', 'color-legend',
                  'legend-color'):
        check('%s: %s is gone' % (name, _dead),
              not re.search(r'(?<![\w-])%s(?![\w-])' % _dead, c))
    for _lit in ('#fff3e0', '#ffe0b2', '#e65100', '#1565c0', '#ff8c00',
                 '#bbdefb', '#90caf9', '#ffcc80'):
        check('%s: the wash literal %s is gone' % (name, _lit), _lit not in c)
    check('%s: the author is a chip' % name,
          'alv-tag comment-author' in c)
    # ONE tone was the decision. A second rebuilds the split in miniature.
    check('  and it carries no tone of its own',
          not re.search(r'alv-tag comment-author[^"]*alv-tag-', c)
          and not re.search(r'\.comment-author\s*\{[^}]*background', c))

# THE NON-COSMETIC HALF.
for name, raw, c in (('friday_status_report', F, FC), ('fsr_details', D, DC)):
    check("%s: no username is compared to the literal 'SS'" % name,
          "issues_details_user == 'SS'" not in c)
check('fsr_details KEEPS the comparison that decides who may EDIT',
      'user_initials' in DC)
check('  which is a different thing from the wash, and stays',
      re.search(r'issues_details_user == user_initials', DC) is not None)

check('base owns the chip', '.alv-tag' in BC)
check('  and the tag family borrows no verdict token',
      not re.search(r'\.alv-tag\s*\{[^}]*var\(--alv-(good|warn|bad)', BC))

# ===========================================================================
head('2. rendered: do two authors look the same?')
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

    CHIP = '<span class="alv-tag comment-author">%s</span>'

    FIX = """<!doctype html><meta charset=utf-8>
<style>%s</style><style>%s</style><style>%s</style><style>%s</style>
<style>body{margin:0;padding:10px}
 /* CONTROL: one row painted on purpose, so the probe is known to see it. */
 #washed { background: rgb(255, 243, 224) !important; }
 #washed .comment-text { color: rgb(255, 140, 0) !important; }
</style>

<table class="alv-table"><tbody>
  <tr id="rowA"><td class="comment-cell"><span class="comment-text">first</span></td>
      <td class="user-cell" data-label="User">%s</td></tr>
  <tr id="rowB"><td class="comment-cell"><span class="comment-text">second</span></td>
      <td class="user-cell" data-label="User">%s</td></tr>
</tbody></table>

<div class="comment-item" id="cardA"><div class="comment-meta">%s</div>
  <div class="comment-text">first</div></div>
<div class="comment-item" id="cardB"><div class="comment-meta">%s</div>
  <div class="comment-text">second</div></div>

<div class="detail-row" id="detA"><span class="detail-comment">
  <span class="comment-date">2026-09-01</span> %s
  <span class="comment-text">first</span></span></div>
<div class="detail-row" id="detB"><span class="detail-comment">
  <span class="comment-date">2026-09-01</span> %s
  <span class="comment-text">second</span></span></div>
<div class="detail-row" id="washed"><span class="detail-comment">
  <span class="comment-date">2026-09-01</span> %s
  <span class="comment-text">third</span></span></div>
""" % (BOOT, css(BS), css(C), css(D),
       CHIP % 'SS', CHIP % 'DM', CHIP % 'SS', CHIP % 'DM',
       CHIP % 'SS', CHIP % 'DM', CHIP % 'SS')

    _f = os.path.join(tempfile.gettempdir(), 'comment_tint_fixture.html')
    with open(_f, 'w', encoding='utf-8') as fh:
        fh.write(FIX)

    PROBE = """() => {
      const cs = s => getComputedStyle(document.querySelector(s));
      const grab = id => {
        const r = cs('#' + id);
        const t = cs('#' + id + ' .comment-text');
        return {bg: r.backgroundColor, border: r.borderLeftColor,
                text: t.color, weight: t.fontWeight};
      };
      const chip = cs('.comment-author');
      return {
        A: grab('rowA'), B: grab('rowB'),
        cA: grab('cardA'), cB: grab('cardB'),
        dA: grab('detA'), dB: grab('detB'),
        washed: grab('washed'),
        chipBg: chip.backgroundColor, chipColor: chip.color,
        chips: [...document.querySelectorAll('.comment-author')]
                 .map(e => getComputedStyle(e).backgroundColor),
      };
    }"""

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': 1200, 'height': 900})
        pg.goto('file://' + _f)
        R = pg.evaluate(PROBE)
        b.close()

    # CONTROL FIRST: every check below asserts an ABSENCE of difference, and
    # an absence is what a broken probe reports for free.
    check('CONTROL: the probe can see a washed row when there is one',
          R['washed']['bg'] != R['dA']['bg']
          and R['washed']['text'] != R['dA']['text'],
          '%s / %s' % (R['washed']['bg'], R['washed']['text']))

    for label, a, b_ in (('the report rows', R['A'], R['B']),
                         ('the history cards', R['cA'], R['cB']),
                         ('the issue comments', R['dA'], R['dB'])):
        check('TWO AUTHORS, same background: %s' % label, a['bg'] == b_['bg'],
              '%s vs %s' % (a['bg'], b_['bg']))
        check('  same left edge', a['border'] == b_['border'],
              '%s vs %s' % (a['border'], b_['border']))
        check('  and the comment TEXT is one colour and one weight',
              a['text'] == b_['text'] and a['weight'] == b_['weight'],
              '%s %s vs %s %s' % (a['text'], a['weight'],
                                  b_['text'], b_['weight']))

    check('every author chip is the SAME tone',
          len(set(R['chips'])) == 1, str(set(R['chips'])))
    check('  and it is a real chip, not transparent',
          R['chipBg'] not in ('rgba(0, 0, 0, 0)', 'transparent'), R['chipBg'])

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('\n  failures:')
    for f in FAILED:
        print('   - %s' % f)
print('=' * 72)
sys.exit(1 if FAIL else 0)
