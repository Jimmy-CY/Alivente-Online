"""test_resolved_report.py - the report of good news stops shouting.

    python test_resolved_report.py

Run from the repo root, after apply_resolved_report.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 2 DRIVES A BROWSER, because "the red is gone" is a computed
    value and no amount of reading the file settles it. Round D's lesson,
    now the ninth time it has paid: `.comment-submit` sat 4px taller and
    bolder on the same teal for a week, invisible to a colour audit, and the
    Analysis drill-down would have gone Bootstrap blue on a rescope that
    read correctly. So the figure is RENDERED - before and after, from the
    real stylesheets - and the measured colour must move off pure red and
    onto base's neutral pill ink.

  * SECTION 3 IS THE ONE THAT ALMOST SHIPPED A DEFECT. This round adds a
    rule, `.issue-description .issue-age`. The Friday report spells the same
    rule `.issue-heading .issue-age`, because that is where ITS pill sits;
    here the pill sits inside the description. Copying both halves across -
    which is what "match the Friday report exactly" invites - would have
    added a selector matching nothing, in the round that deletes two rules
    for exactly that. So the suite asks the BROWSER whether the rule reaches
    the pill, rather than asking the file whether the rule is present.

  * SECTION 4 checks the two dead rules were dead. `.resolution-time` and
    `.comment-user` are deleted here; the evidence that this was safe is not
    "they looked unused" but that no markup, no script and no other template
    in the repo names either one.

  * SECTION 5 RENDERS THE PRINT SHEET. This is a report; it gets printed.
    Round D proved the neutral chip survives mono print rather than becoming
    an invisible grey box, and the same figure on this page must too.

WHAT THIS SUITE CANNOT DO, SAID PLAINLY. Sections 2, 3 and 5 render a
FIXTURE built from base.html plus this page's own <style> - not the Django
page. A green tick there is a fact about those stylesheets applied to that
markup. It cannot see a view that stops sending `days_to_resolve`. The
Issues-table round learned this the hard way: deleting the phone action bar
left its suite at 104/104, because a rendered check on a synthetic fixture
tests BASE. So section 1 reads the real template, and section 6 asserts the
template still parses and still carries the loop the view feeds.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
RIR = os.path.join(T, 'resolved_issues_report.html')
FSR = os.path.join(T, 'friday_status_report.html')
BASE = os.path.join(T, 'base.html')
BAK = RIR + '.bak_rir'
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


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


def nocomment(t):
    """CSS and HTML comments removed. Twenty-four times in this project a
       check that reads text has read PROSE instead - three of them inside a
       patcher's own explanation of the thing it was checking. Every question
       below about `red`, about a selector, about a hex, is asked of code."""
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    return re.sub(r'/\*.*?\*/', '', t, flags=re.S)


def markup_of(t):
    return re.sub(r'<(script|style)[^>]*>.*?</\1>', '', nocomment(t), flags=re.S)


if not os.path.exists(RIR):
    sys.exit('! %s not found - run from the repo root' % RIR)
if not os.path.exists(BAK):
    sys.exit('! no resolved_issues_report.html.bak_rir - '
             'run apply_resolved_report.py first.')

F, WAS = read(RIR), read(BAK)
FCSS, WCSS = css_of(nocomment(F)), css_of(nocomment(WAS))
FMK, WMK = markup_of(F), markup_of(WAS)
BCSS = css_of(read(BASE))

# ===========================================================================
head('1. the alarm on the page that only carries good news')
# ===========================================================================
check('CONTROL: the comment stripper strips',
      'the turnaround beside each one was painted' not in FCSS)
check('CONTROL: .. and leaves the code it is meant to leave',
      '.issue-description' in FCSS and '.property-card' in FCSS)

check('no inline red survives', 'color: red' not in FMK)
check('  CONTROL: there WAS one', 'color: red' in WMK)
check('no inline style survives at all - there was only ever the one',
      'style="' not in FMK)
check('  CONTROL: the old file had exactly one',
      WMK.count('style="') == 1, str(WMK.count('style="')))
check('no colour keyword survives anywhere in the markup',
      not re.search(r'color\s*:\s*(?:red|green|blue|orange|yellow)\b', FMK, re.I))

# THE SAME FIGURE ON TWO SCREENS. Not "looks like" - the identical class list,
# taken from the Friday report at run time rather than typed in here, so the
# check follows that page if it ever changes.
if os.path.exists(FSR):
    _m = re.search(r'<span class="([^"]*)">Resolution:', read(FSR))
    check('the Friday report shows this figure', _m is not None)
    if _m:
        check('  and this page spells the class list identically',
              ('<span class="%s">Resolution:' % _m.group(1)) in FMK,
              _m.group(1))
else:
    print('  SKIP  friday_status_report.html not present')

check('the dangling dash is gone - it separated two runs of TEXT and there '
      'are no longer two', ') -' not in FMK)
check('  CONTROL: it was there', ') -' in WMK)
check('the description still reads as a bracketed phrase',
      '({{ issue.description }})' in FMK)

# ===========================================================================
head('2. what the browser actually paints')
# ===========================================================================
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('  SKIP  playwright not installed - sections 2, 3 and 5 need it')
    sync_playwright = None

FIX = read(FIXTURE) if os.path.exists(FIXTURE) else ''
check('the Bootstrap fixture is present - without it the render is not the '
      'page', bool(FIX))

CARD = ('<div class="report-content"><div class="property-card">'
        '<div class="issue-header">'
        '<strong class="issue-heading">Renewal of lease agreement</strong>'
        '<span class="issue-description"> (Confirmed via email)%s %s</span>'
        '</div></div></div>')
NEW_FIG = ('<span class="alv-pill alv-pill-neutral issue-age">'
           'Resolution: 0 days</span>')
OLD_FIG = '<span style="color: red;">Resolution: 0 days</span>'

MEASURE = """() => {
    const s = document.querySelector('.issue-description span');
    const c = getComputedStyle(s);
    const d = getComputedStyle(document.querySelector('.issue-description'));
    // GROUND, not backgroundColor. On the print sheet the pill's own
    // background is rgba(0,0,0,0) - transparent - and a check that reads
    // that as "black" concludes black-on-black and calls a perfectly
    // legible chip illegible. What the reader sees is the first opaque
    // surface behind it, so walk up until one is found.
    let g = 'rgb(255, 255, 255)';
    for (let e = s; e; e = e.parentElement) {
        const b = getComputedStyle(e).backgroundColor;
        const m = b.match(/[\\d.]+/g);
        if (m && (m.length < 4 || parseFloat(m[3]) > 0)) { g = b; break; }
    }
    return {colour: c.color, ml: c.marginLeft, bg: c.backgroundColor,
            ground: g, desc: d.color, box: s.getBoundingClientRect().width};
}"""


def render(page_css, fig, dash, extra=''):
    html = ('<!doctype html><meta charset=utf-8>'
            '<style>%s</style><style>%s</style><style>%s</style>'
            '<style>%s</style><body>%s</body>'
            % (FIX, BCSS, page_css, extra, CARD % (dash, fig)))
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={'width': 900, 'height': 400})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg.set_content(html, wait_until='domcontentloaded')
        out = pg.evaluate(MEASURE)
        br.close()
    return out


def rgb(s):
    return tuple(int(x) for x in re.findall(r'\d+', s)[:3])


NOW = BEFORE = None
if sync_playwright is not None and FIX:
    NOW = render(FCSS, NEW_FIG, '')
    BEFORE = render(WCSS, OLD_FIG, ' -')

    check('BEFORE: the turnaround rendered as pure red',
          rgb(BEFORE['colour']) == (255, 0, 0), BEFORE['colour'])
    check('AFTER:  it does not', rgb(NOW['colour']) != (255, 0, 0),
          NOW['colour'])
    check('  and it is not any kind of alarm - no channel dominates',
          max(rgb(NOW['colour'])) - min(rgb(NOW['colour'])) < 60,
          NOW['colour'])
    # It must be BASE's pill ink, not merely "not red" - inheriting the
    # description's grey would also pass "not red" and would lose the chip.
    check('  it wears a pill background rather than sitting as loose text',
          rgb(NOW['bg']) != rgb(BEFORE['bg']) and NOW['bg'] != 'rgba(0, 0, 0, 0)',
          NOW['bg'])
    check('  and its ink differs from the description it sits in, so the '
          'figure still reads as a distinct thing',
          rgb(NOW['colour']) != rgb(NOW['desc']),
          '%s vs %s' % (NOW['colour'], NOW['desc']))

# ===========================================================================
head('3. the rule this round ADDED must match something')
# ===========================================================================
# The trap: the Friday report spells this `.issue-heading .issue-age` because
# that is where its pill sits. Copying both halves across would add a dead
# selector in the round that removes two. Asked of the browser, not the file.
check('the page does not carry the Friday report\'s selector, which reaches '
      'nothing here', '.issue-heading .issue-age' not in FCSS)
check('  because the pill sits inside .issue-description on this page',
      re.search(r'<span class="issue-description">(?:(?!</span>).)*?issue-age',
                FMK, re.S) is not None)

if NOW is not None:
    check('the spacing rule REACHES the pill - 8px of margin, measured',
          NOW['ml'] == '8px', NOW['ml'])
    # The control: same markup, same base, but the page rule withheld. If the
    # margin is 8px either way then base was doing it and this rule is dead.
    _no_rule = render(re.sub(r'(?s)\.issue-description \.issue-age\s*\{.*?\}',
                             '', FCSS), NEW_FIG, '')
    check('  CONTROL: without the page rule it is not 8px, so the rule is the '
          'thing doing it', _no_rule['ml'] != '8px', _no_rule['ml'])

# ===========================================================================
head('4. the two dead rules were dead')
# ===========================================================================
for sel, why in (('.resolution-time', 'a rule for the very figure above, '
                                      'overridden by the inline style'),
                 ('.comment-user', 'a chip no markup wore')):
    check('%-18s is gone' % sel,
          not re.search(r'(?m)^\s*' + re.escape(sel) + r'\s*[,{]', FCSS), why)
    check('  CONTROL: it was there', re.search(
        r'(?m)^\s*' + re.escape(sel) + r'\s*[,{]', WCSS) is not None)
    # DEAD means nothing anywhere wore it - not "it looked unused".
    _worn = []
    for _n in sorted(os.listdir(T)):
        if not _n.endswith('.html'):
            continue
        if sel[1:] in markup_of(read(os.path.join(T, _n))):
            _worn.append(_n)
    check('  and no template in the repo wears it', not _worn, str(_worn[:4]))

check('the comment authors still show as text, which was left open on '
      'purpose rather than folded in',
      'comment-date' in FMK and 'alv-tag' not in FMK)

# ===========================================================================
head('5. it is a report, so it gets printed')
# ===========================================================================
if NOW is not None:
    _print = ('@media print{}'  # placeholder so the string is never empty
              )
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={'width': 900, 'height': 400})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg.set_content('<!doctype html><meta charset=utf-8>'
                       '<style>%s</style><style>%s</style><style>%s</style>'
                       '<body>%s</body>'
                       % (FIX, BCSS, FCSS, CARD % ('', NEW_FIG)),
                       wait_until='domcontentloaded')
        pg.emulate_media(media='print')
        _p = pg.evaluate(MEASURE)
        # And in mono, where a grey chip on a grey ground would vanish.
        pg.emulate_media(media='print', forced_colors='active')
        _mono = pg.evaluate(MEASURE)
        br.close()
    def lum(c):
        r, g, b = [x / 255.0 for x in rgb(c)]
        f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

    def contrast(a, b):
        x, y = sorted((lum(a), lum(b)))
        return (y + 0.05) / (x + 0.05)

    check('the chip is still there on the print sheet', _p['box'] > 10,
          '%.0fpx wide' % _p['box'])
    # AGAINST THE GROUND, not against its own background. The pill's
    # background goes transparent in print - the chip prints as text on
    # paper - and reading rgba(0,0,0,0) as black concludes black-on-black.
    check('  and its text is legible against what is actually behind it',
          contrast(_p['colour'], _p['ground']) >= 4.5,
          '%s on %s = %.1f:1' % (_p['colour'], _p['ground'],
                                 contrast(_p['colour'], _p['ground'])))
    check('  and it does not disappear in forced monochrome',
          _mono['box'] > 10
          and contrast(_mono['colour'], _mono['ground']) >= 4.5,
          '%s on %s = %.1f:1' % (_mono['colour'], _mono['ground'],
                                 contrast(_mono['colour'], _mono['ground'])))
    check('  CONTROL: the ratio is measuring something - the old pure red on '
          'paper scored worse than this does',
          contrast('rgb(255, 0, 0)', 'rgb(255, 255, 255)')
          < contrast(_p['colour'], _p['ground']),
          '%.1f:1 vs %.1f:1' % (contrast('rgb(255, 0, 0)',
                                         'rgb(255, 255, 255)'),
                                contrast(_p['colour'], _p['ground'])))

# ===========================================================================
head('6. base, the tokens, and what the round did NOT touch')
# ===========================================================================
_hex = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', FCSS)))
check('no colour is spelled by hand any more', not _hex, str(_hex))
check('  CONTROL: eight were', len(set(re.findall(
    r'#[0-9a-fA-F]{3,8}\b', WCSS))) >= 7,
    str(len(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', WCSS)))))
check('no bare `white` keyword survives',
      not re.search(r':\s*white\b', FCSS, re.I))

_tok = sorted(set(re.findall(r'var\(\s*(--alv-[a-z0-9-]+)', FCSS)))
check('the page now references base (%d token(s))' % len(_tok), len(_tok) >= 5,
      ', '.join(t.replace('--alv-', '') for t in _tok))
check('  CONTROL: it referenced base NOWHERE before',
      not re.search(r'var\(\s*--alv-', WCSS))
_missing = [t for t in _tok if (t + ':') not in BCSS]
check('  and base declares every one of them', not _missing, str(_missing))
for _need in ('.alv-pill', '.alv-pill-neutral'):
    check('base defines %s' % _need, _need in BCSS)

# NOT THIS ROUND, asserted so the record stays reliable. The print round
# measured this block and classified it as needing a read, not a fix; a later
# round quietly reversing that would make the classification worthless.
check('the bare phone query is still bare - that is the print round\'s call',
      re.search(r'@media\s*\(\s*max-width:\s*768px\s*\)', F) is not None)
check('the print block is untouched',
      re.search(r'(?s)@media print\{.*?\n    \}', F.replace(' {', '{'))
      is not None)
for hook in ('{% for property in properties %}', '{% for issue in property.issues %}',
             'days_to_resolve', "{% url 'fsr' %}"):
    check('the page keeps %s' % hook, hook in F)

# The template must still parse. THE 500 this session came from a patcher
# whose balance check ended in `or True` and asserted nothing.
_stack = []
_fault = None
_OPEN = {'if': 'endif', 'for': 'endfor', 'block': 'endblock', 'with': 'endwith'}
_CLOSE = {v: k for k, v in _OPEN.items()}
for _m3 in re.finditer(r'\{%\s*(\w+)', F):
    _t = _m3.group(1)
    if _t in _OPEN:
        _stack.append(_t)
    elif _t in _CLOSE:
        if not _stack or _OPEN[_stack.pop()] != _t:
            _fault = _t
            break
check('every Django tag is balanced', _fault is None and not _stack,
      _fault or (','.join(_stack) if _stack else ''))
try:
    import django
    from django.conf import settings
    from django.template import Engine
    if not settings.configured:
        # staticfiles must be installed or `{% load static %}` - the second
        # line of this template - raises "'static' is not a registered tag
        # library", which is a fact about this suite's settings and nothing
        # at all about the file being checked.
        settings.configure(TEMPLATES=[], USE_TZ=True,
                           INSTALLED_APPS=['django.contrib.staticfiles'])
        django.setup()
    # Engine() does NOT auto-discover tag libraries - that is the
    # DjangoTemplates BACKEND's job, and using the bare Engine skips it. So
    # `{% load static %}` fails here for a reason that lives in this suite,
    # not in the template. Hand it the library it needs.
    Engine(dirs=[T], libraries={
        'static': 'django.templatetags.static'}).from_string(F)
    check('  and Django itself parses the file', True)
except ImportError:
    print('  SKIP  django not importable - the walker above stands alone')
except Exception as e:
    check('  and Django itself parses the file', False, str(e)[:70])

for _blk in re.findall(r'<style[^>]*>(.*?)</style>', F, re.S):
    check('the stylesheet is brace-balanced',
          _blk.count('{') == _blk.count('}'),
          '%d vs %d' % (_blk.count('{'), _blk.count('}')))

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
print('\n  NOT PROVED HERE: that the view still sends days_to_resolve. The')
print('  render is a fixture of base + this page\'s <style>; it tests those')
print('  stylesheets, not Django. Open the report over a real date range.')
if FAILED:
    print('\n  failures:')
    for x in FAILED[:20]:
        print('   - %s' % x)
print('=' * 72)
sys.exit(1 if FAIL else 0)
