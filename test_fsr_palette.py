"""test_fsr_palette.py - round D: the Issues module's last two screens.

    python test_fsr_palette.py

Run from the repo root, after apply_fsr_palette.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 3 DRIVES A BROWSER, and it carries the round's central claim.
    "The red is a scale now" is a computed colour, not a class name: a
    template can carry `alv-age-3` and still render grey if base never
    defined it, or if a page rule outranks it. So the four ages are RENDERED
    and their colours read back, and they must be FOUR DIFFERENT colours in
    ageing order.

    THE CONTROL IS THE OTHER HALF. The same four are rendered from
    .bak_fsrpal, where they must all come out the SAME red - otherwise "four
    different colours" would pass just as well on a probe that never worked.

  * SECTION 4 IS THE PAPER HALF, and it is why a chip was chosen over
    coloured text. Printed in mono the colour is gone; the WORDS must still
    be there. base's own note says a scale is defensible only when "every
    graded cell prints its own figure", so the round has to meet that test
    rather than cite it.

  * SECTION 5 measures .comment-submit, which is the subtle one. base wins
    the colour, so a colour audit finds nothing - the drift was 4px of height
    and a font weight. It is measured against its own Cancel button, and
    controlled against the backup where the two must DIFFER.

  * SECTION 6 asserts what the round did NOT do: the bare phone queries are
    still bare, the Notify round's tint is untouched, and the comment-tint
    round's note still reads exactly as it did.

WHY THE BANDS ARE READ OUT OF fsr.html. The Analysis modal computes them in
JavaScript from a dataset; this screen gets days_open from the view, so it
bands in a Django {% if %} chain. Two spellings of one rule. Retyping 30 / 90
/ 180 here would make this suite a THIRD source of truth, and all three would
agree right up until somebody changed one. So the thresholds are parsed from
fsr.html and the template chain is checked against them.
"""
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
FIXTURE = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
FSR = os.path.join(T, 'friday_status_report.html')
FD = os.path.join(T, 'fsr_details.html')
IA = os.path.join(T, 'fsr.html')
BASE = os.path.join(T, 'base.html')

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


def css_of(src):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', src, re.S))


def nocomment(t):
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


for _p in (FSR, FD, IA, BASE):
    if not os.path.exists(_p):
        sys.exit('! %s not found - run from the repo root' % _p)
_baks = {p: p + '.bak_fsrpal' for p in (FSR, FD)}
if not all(os.path.exists(b) for b in _baks.values()):
    sys.exit('! no .bak_fsrpal backups - run apply_fsr_palette.py first.')

S, D = read(FSR), read(FD)
S_WAS, D_WAS = read(_baks[FSR]), read(_baks[FD])
SNC, DNC = nocomment(S), nocomment(D)
BASE_CSS = css_of(read(BASE))

# ===========================================================================
head('1. no colour is spelled by hand any more')
# ===========================================================================
for name, now, was in (('friday_status_report.html', SNC, nocomment(S_WAS)),
                       ('fsr_details.html', DNC, nocomment(D_WAS))):
    c_now, c_was = css_of(now), css_of(was)
    hexes_now = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', c_now)))
    hexes_was = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', c_was)))
    # fsr_details keeps ONE: the Notify round's page-local warn tint, decided
    # last night with a single asker. A check wider than its round reports the
    # rest of the file as a defect.
    allowed = ['#ecd9a8'] if 'details' in name else []
    check('%-26s spells %s by hand' % (name, allowed or 'nothing'),
          hexes_now == allowed, str(hexes_now))
    check('  CONTROL: it spelled %d before the round' % len(hexes_was),
          len(hexes_was) >= 12, str(hexes_was))
    check('  and no bare `white` keyword either - same literal, other spelling',
          not re.search(r':\s*white\b', c_now, re.I))
    check('  CONTROL: there WERE bare whites',
          bool(re.search(r':\s*white\b', c_was, re.I)))
    check('  it now references base', len(set(re.findall(
        r'--alv-[a-z0-9-]+', c_now))) >= 7,
        '%d tokens' % len(set(re.findall(r'--alv-[a-z0-9-]+', c_now))))
    check('  CONTROL: it referenced %d before'
          % len(set(re.findall(r'--alv-[a-z0-9-]+', c_was))),
          len(set(re.findall(r'--alv-[a-z0-9-]+', c_was))) <= 2)

# Every token it now names has to EXIST in base, or the colour falls back to
# nothing and the page renders unstyled text on white.
for name, now in (('FSR', SNC), ('FD', DNC)):
    used = set(re.findall(r'var\(\s*(--alv-[a-z0-9-]+)', css_of(now)))
    missing = [t for t in used if (t + ':') not in BASE_CSS]
    check('%s: every token it uses is declared in base' % name, not missing,
          str(missing))

# WHITE IS TWO TOKENS. The edit-issue modal's dialog is --alv-paper; the text
# on its teal gradient is --alv-on-accent. Interchangeable only by accident.
check('the gradient header takes on-accent ink, not paper',
      re.search(r'\.ei-modal-header\s*\{[^}]*color:\s*var\(--alv-on-accent\)',
                css_of(DNC)) is not None)
check('  and the dialog itself takes paper',
      re.search(r'\.ei-modal-content\s*\{[^}]*background:\s*var\(--alv-paper\)',
                css_of(DNC)) is not None)

# ===========================================================================
head('2. the six rules nothing rendered')
# ===========================================================================
# Checked against markup, scripts and every other template before deleting.
# The suite pins them absent so they cannot drift back in with a copy-paste.
for name, now, was, sels in (
        ('fsr_details.html', DNC, nocomment(D_WAS),
         ('.issue-date', '.btn-info', '.ei-edit-btn', '.status-title')),
        ('friday_status_report.html', SNC, nocomment(S_WAS),
         ('.back-button',))):
    for sel in sels:
        pat = re.compile(r'(?m)^\s*' + re.escape(sel) + r'\s*[,{:]')
        check('%-26s %-14s is gone' % (name, sel),
              not pat.search(css_of(now)))
        check('  CONTROL: it WAS declared', bool(pat.search(css_of(was))))

# The live half of the same family must NOT have gone with it.
for sel in ('.ei-modal', '.ei-modal-header', '.ei-input', '.ei-label',
            '.ei-modal-footer'):
    check('  .. but %-18s survives - only the unused one went' % sel,
          sel in css_of(DNC))

# ===========================================================================
head('3. the browser: is the red a scale now?')
# ===========================================================================
# THE BANDS ARE THE MODAL'S, read rather than retyped.
_ia = read(IA)
_m = re.search(r'var\s+AGE_BANDS\s*=\s*\[(.*?)\]\s*;', _ia, re.S)
BANDS = []
if _m:
    for obj in re.findall(r'\{([^{}]*)\}', _m.group(1)):
        lo = re.search(r'\bmin\s*:\s*(\d+)', obj)
        hi = re.search(r'\bmax\s*:\s*([\d.e+]+)', obj)
        cl = re.search(r'\bcls\s*:\s*[\'"]([\w-]+)', obj)
        if lo and hi and cl:
            hv = float(hi.group(1))
            BANDS.append((int(lo.group(1)),
                          None if hv >= 10 ** 8 else int(hv), cl.group(1)))
check('fsr.html still defines four ageing bands', len(BANDS) == 4,
      str([(a, b, c) for a, b, c in BANDS]))

if len(BANDS) == 4:
    parts = []
    for i, (lo, hi, cls) in enumerate(BANDS):
        kw = 'if' if i == 0 else 'elif'
        parts.append('{%% else %%}%s' % cls if hi is None
                     else '{%% %s issue.days_open <= %d %%}%s' % (kw, hi, cls))
    chain = ''.join(parts) + '{% endif %}'
    check('the template chain spells EXACTLY those thresholds', chain in SNC,
          '' if chain in SNC else chain[:70])
    # The other direction, or the check above passes on a file with no chip.
    check('  CONTROL: the pre-round file had no chain at all',
          '{% if issue.days_open <=' not in nocomment(S_WAS))
    check('  and the classes it names are base\'s, not new ones',
          all(('.' + c) in BASE_CSS for _, _, c in BANDS))

check('the two age chips and three neutral pills are in the markup',
      SNC.count('alv-age-pill') == 2
      and SNC.count('alv-pill alv-pill-neutral') == 3,
      '%d chips, %d pills' % (SNC.count('alv-age-pill'),
                              SNC.count('alv-pill alv-pill-neutral')))
check('  CONTROL: the pre-round file had the two red classes',
      'days-open' in nocomment(S_WAS)
      and 'resolution-time' in nocomment(S_WAS))

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('  SKIP  playwright not installed')
    sync_playwright = None

FIX = read(FIXTURE) if os.path.exists(FIXTURE) else ''


def band_of(days):
    for lo, hi, cls in BANDS:
        if days >= lo and (hi is None or days <= hi):
            return cls
    return BANDS[0][2]


def probe(pg, page_css, spans, media='screen'):
    """Render the page's own CSS over base's and read the ink back."""
    body = ''.join('<div id="p%d">%s</div>' % (i, s)
                   for i, s in enumerate(spans))
    html = ('<!doctype html><meta charset=utf-8><style>%s</style>'
            '<style>%s</style><style>%s</style>'
            '<div class="report-content"><div class="status-card">'
            '<div class="property-card"><h5 class="issue-heading">%s</h5>'
            '</div></div></div>' % (FIX, BASE_CSS, page_css, body))
    f = os.path.join(tempfile.gettempdir(), 'fsrprobe.html')
    with open(f, 'w', encoding='utf-8') as fh:
        fh.write(html)
    pg.goto('file://' + f)
    pg.emulate_media(media=media)
    return pg.evaluate(
        """n => Array.from({length:n}, (_, i) => {
             const e = document.getElementById('p'+i).firstElementChild
                       || document.getElementById('p'+i);
             const c = getComputedStyle(e);
             return {color: c.color, bg: c.backgroundColor,
                     radius: c.borderRadius, text: e.textContent.trim()};
           })""", len(spans))


# ONE SAMPLE PER BAND, DERIVED FROM THE BANDS - not four numbers typed out.
# The first draft used [0, 12, 64, 257] and failed, and the failure was the
# CHECK's: 0 and 12 are both inside the 0-30 band, so two of the four samples
# were always going to share an ink. A set of samples is a fact about the
# sample. Ask the bands which days to render.
AGES = [(lo + 76) if hi is None else (lo + hi) // 2 for lo, hi, _ in BANDS]
if sync_playwright is not None:
    NOW_CSS = css_of(S)
    WAS_CSS = css_of(S_WAS)
    now_spans = ['<span class="alv-age-pill issue-age %s">%d days open</span>'
                 % (band_of(a), a) for a in AGES] + \
                ['<span class="alv-pill alv-pill-neutral issue-age">'
                 'Resolution: 9 days</span>']
    was_spans = ['<span class="days-open">- %d days open</span>' % a
                 for a in AGES] + \
                ['<span class="resolution-time">- Resolution: 9 days</span>']
    with sync_playwright() as pw:
        _b = pw.chromium.launch()
        pg = _b.new_page(viewport={'width': 1100, 'height': 700})

        got = probe(pg, NOW_CSS, now_spans)
        inks = [g['color'] for g in got[:4]]
        check('the four ages render in FOUR different inks',
              len(set(inks)) == 4, str(inks))
        check('  and each carries a tint behind it, not bare text',
              all(g['bg'] not in ('rgba(0, 0, 0, 0)', 'transparent')
                  for g in got[:4]))
        # THE TWO HALVES OF THE DEFECT, stated separately. Before the round
        # every one of these was the same red; the claim is not "they all
        # differ" but that days INSIDE a band agree and days ACROSS bands do
        # not. "New Issue" is the days_open == 0 branch and must be quiet.
        _same = probe(pg, NOW_CSS, [
            '<span class="alv-age-pill issue-age %s">New Issue</span>'
            % band_of(0),
            '<span class="alv-age-pill issue-age %s">12 days open</span>'
            % band_of(12),
            '<span class="alv-age-pill issue-age %s">257 days open</span>'
            % band_of(257)])
        check('  "New Issue" and 12 days share an ink - same band, same thing',
              _same[0]['color'] == _same[1]['color'],
              '%s vs %s' % (_same[0]['color'], _same[1]['color']))
        check('  .. and 257 days does NOT, which is the whole point',
              _same[2]['color'] != _same[1]['color'],
              '%s vs %s' % (_same[2]['color'], _same[1]['color']))
        check('  the turnaround on a CLOSED issue is neutral, not on the scale',
              got[4]['color'] not in inks, got[4]['color'])
        check('  and it is pill-shaped, so it reads as a state',
              '9999px' in got[4]['radius'] or '999px' in got[4]['radius']
              or float(got[4]['radius'].split('px')[0]) >= 9,
              got[4]['radius'])

        # THE CONTROL. Same five, the pre-round file: all four ages the SAME.
        was = probe(pg, WAS_CSS, was_spans)
        was_inks = [w['color'] for w in was[:4]]
        check('CONTROL: before the round all four were ONE colour',
              len(set(was_inks)) == 1, str(set(was_inks)))
        check('  .. and it was pure red', was_inks[0] == 'rgb(255, 0, 0)',
              was_inks[0])
        check('  .. and so was a RESOLVED issue\'s turnaround - good news, red',
              was[4]['color'] == 'rgb(255, 0, 0)', was[4]['color'])
        check('  .. and "New Issue", the days_open == 0 branch, red too',
              probe(pg, WAS_CSS,
                    ['<span class="days-open">- New Issue</span>'])[0]['color']
              == 'rgb(255, 0, 0)')

        # ===================================================================
        head('4. on paper: the scale is redundant, not load-bearing')
        # ===================================================================
        # base's own condition for a defensible scale. A printed report often
        # comes out mono, and the reader who loses the colour must still have
        # the figure.
        paper = probe(pg, NOW_CSS, now_spans, media='print')
        check('every chip still prints its own figure',
              all(re.search(r'\d', p['text']) or 'New' in p['text']
                  for p in paper), str([p['text'] for p in paper]))
        check('  including the words, not just the number',
              all('days' in p['text'] for p in paper[:4]),
              str([p['text'] for p in paper[:4]]))
        # And the thing it replaced could not have passed this.
        was_paper = probe(pg, WAS_CSS, was_spans, media='print')
        check('CONTROL: the old red printed as ONE ink, carrying nothing',
              len(set(w['color'] for w in was_paper[:4])) == 1)

        # ===================================================================
        head('5. Save Comment stops out-shouting its own Cancel')
        # ===================================================================
        def pair(page_css):
            html = ('<!doctype html><meta charset=utf-8><style>%s</style>'
                    '<style>%s</style><style>%s</style>'
                    '<div style="width:1100px">'
                    '<button class="btn action-primary comment-submit" id="a">'
                    'Save Comment</button>'
                    '<button class="btn action-secondary" id="b">Cancel'
                    '</button></div>' % (FIX, BASE_CSS, page_css))
            f = os.path.join(tempfile.gettempdir(), 'fdbtn.html')
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write(html)
            pg.goto('file://' + f)
            pg.emulate_media(media='screen')
            return pg.evaluate(
                """() => ['a','b'].map(id => {
                     const e = document.getElementById(id);
                     const c = getComputedStyle(e);
                     return {h: Math.round(e.getBoundingClientRect().height),
                             fw: c.fontWeight, bg: c.backgroundColor};
                   })""")

        a, b = pair(css_of(D))
        check('Save Comment is the same height as its Cancel',
              a['h'] == b['h'], '%dpx vs %dpx' % (a['h'], b['h']))
        check('  and the same weight', a['fw'] == b['fw'],
              '%s vs %s' % (a['fw'], b['fw']))
        check('  while KEEPING the primary tone - only the skin went',
              a['bg'] != b['bg'], a['bg'])
        wa, wb = pair(css_of(D_WAS))
        check('CONTROL: before the round it was TALLER than its own Cancel',
              wa['h'] > wb['h'], '%dpx vs %dpx' % (wa['h'], wb['h']))
        check('  .. and bolder, which is the half a colour audit cannot see',
              wa['fw'] != wb['fw'], '%s vs %s' % (wa['fw'], wb['fw']))
        check('  .. on exactly the same teal, which is why nobody noticed',
              wa['bg'] == a['bg'], '%s vs %s' % (wa['bg'], a['bg']))
        _b.close()

# ===========================================================================
head('6. what the round did NOT do')
# ===========================================================================
# The empty state joined base's. Four page rules plus two in @print plus four
# on the phone, for a component ten other pages already share.
check('the empty state is base\'s now',
      'alv-empty-title' in SNC and 'alv-empty-hint' in SNC)
check('  and none of the hand-rolled four survives',
      not re.search(r'\.no-issues-', css_of(SNC)))
check('  CONTROL: all four were there before',
      len(set(re.findall(r'\.(no-issues-[\w-]+)', css_of(nocomment(S_WAS)))))
      >= 4)

# The badges said WHICH VARIANT, not how things are going. Both neutral.
check('neither report-type badge claims a verdict',
      'badge-success' not in SNC and 'badge-info' not in SNC)
check('  CONTROL: one was filled teal and one filled green',
      '#28a745' in nocomment(S_WAS) and 'badge-success' in nocomment(S_WAS))

# THE BARE PHONE QUERIES STAY BARE. The print round measured what these
# blocks DO and classified them as needing a read, not a fix. A later round
# quietly reversing that would make the record unreliable.
for name, txt in (('friday_status_report.html', S), ('fsr_details.html', D)):
    bare = re.findall(r'@media\s*\(\s*max-width:\s*768px\s*\)', txt)
    check('%-26s keeps its bare phone query - the print round\'s call'
          % name, bool(bare), '%d' % len(bare))

# The Notify round's page-local tint, decided last night with one asker.
check('the Notify round\'s warn tint is untouched', '#ecd9a8' in DNC)
check('  and its buttons still carry base\'s inline button',
      DNC.count('status-btn') >= 2)

# THE SWEEP MUST NOT HAVE ENTERED A COMMENT. friday_status_report carries the
# comment-tint round's note, which says the old wash set text to "#ff8c00 or
# #0e7c8b". A blanket replace would have rewritten that into a claim about
# tokens the 1 Sep round never made.
_NOTE = 'author and body all set to #ff8c00 or #0e7c8b at weight 600'
for name, txt in (('friday_status_report.html', S), ('fsr_details.html', D)):
    check('%-26s the tint round\'s note reads as it did' % name, _NOTE in txt)

for name, txt in (('friday_status_report.html', S), ('fsr_details.html', D)):
    for blk in re.findall(r'<style[^>]*>(.*?)</style>', txt, re.S):
        check('%-26s braces balance' % name, blk.count('{') == blk.count('}'))
    check('  and its Django if/endif balance',
          txt.count('{% if') + txt.count('{% elif') >= txt.count('{% endif %}'))

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('\n  failures:')
    for x in FAILED[:20]:
        print('   - %s' % x)
print('=' * 72)
sys.exit(1 if FAIL else 0)
