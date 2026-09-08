"""test_banner_pages.py - the teal page banner is gone, and nothing went with
   it that should have stayed.

    python test_banner_pages.py

Run from the repo root, after apply_banner_pages.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 3 MEASURES A DEFECT THIS ROUND DELIBERATELY DOES NOT FIX, which
    is the more useful thing it does. base hides
    `.page-action-buttons .action-secondary` below 768px on the assumption
    that an `.action-more-btn` will surface it, and neither of these two
    pages has one - so their Help buttons are unreachable on a phone.

    A draft of this round promoted both to `action-primary`.
    test_button_sweep.py refused it, and THE GUARD WAS RIGHT: its classifier
    holds that Help is never the verb, and the promotion wrote an exception
    to a correct rule. The real fault is that `.action-secondary` carries
    two meanings - "quieter than the primary" to the classifier, "hidden
    below 768px because the More menu carries it" to base - which agree on
    22 bars and contradict on 11. Promoting two buttons would have treated
    two instances and left nine.

    So this section asserts the tones are UNTOUCHED, so a later draft cannot
    quietly promote them again; measures the hidden button and prints it as
    a known-unfixed number for the base round to inherit; and proves against
    base itself that the hide is real, so that round starts from a
    measurement rather than an argument.

  * SECTION 2 RENDERS THE BANNERS, because "the teal is gone" is a computed
    value. Text checks pass on a file whose gradient moved rather than left.
    Before and after, desktop and phone, from the real stylesheets.

  * SECTION 4 measures comments_report's figure. Its old `.stat-box` was
    `rgba(255,255,255,0.2)` - a white 20%-alpha tile that only exists as a
    shape on a dark ground. On paper it is invisible. The suite measures the
    old tile against white and the new `.alv-stat` against white, and the
    round is only right if the second is legible where the first is not.

  * SECTION 5 asserts what the round did NOT do. Modal headers keep their
    teal - that is the next round - so a suite that demanded no teal anywhere
    would pass only on work nobody agreed to. The remaining count is pinned
    with a floor so the modal round inherits a number.

WHAT THIS SUITE CANNOT DO, SAID FIRST. Every render is a FIXTURE: base's
stylesheet plus the page's own <style> plus the page's markup with the Django
tags stripped. It is not the Django page. It cannot see a view that stops
sending `comment_count`, and it cannot check an icon, because Font Awesome is
a CDN request and every render here refuses the network on purpose. A 44px
Back button measures 44px whether or not an arrow ever arrives inside it.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
FIXTURE = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

PAGES = {
    'occupancy_trends.html': ('.page-header', '<div class="page-header">',
                              '{% if error %}'),
    'notification_settings.html': ('.settings-header',
                                   '<div class="settings-header">',
                                   '{% for msg'),
    'comments_report.html': ('.report-header',
                             '<div class="page-action-buttons">',
                             '<div class="table-container">'),
}

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


def nocomment(t):
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    return re.sub(r'/\*.*?\*/', '', t, flags=re.S)


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


def markup_of(t):
    return re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t, flags=re.S)


for _n in PAGES:
    if not os.path.exists(os.path.join(T, _n)):
        sys.exit('! %s not found - run from the repo root' % _n)
    if not os.path.exists(os.path.join(T, _n + '.bak_banner')):
        sys.exit('! no %s.bak_banner - run apply_banner_pages.py first.' % _n)

NOW = {n: read(os.path.join(T, n)) for n in PAGES}
WAS = {n: read(os.path.join(T, n + '.bak_banner')) for n in PAGES}
BCSS = css_of(read(BASE))

# ===========================================================================
head('1. the band is gone from the stylesheet')
# ===========================================================================
check('CONTROL: the comment stripper strips',
      'THE TEAL BANNER WENT' not in nocomment(NOW['comments_report.html']))
check('CONTROL: .. and leaves the code',
      '.report-header' in css_of(nocomment(NOW['comments_report.html'])))

for name, (sel, _a, _b) in PAGES.items():
    css = css_of(nocomment(NOW[name]))
    was = css_of(nocomment(WAS[name]))
    band = re.search(r'(?m)^[ \t]*' + re.escape(sel) + r'[ \t]*\{([^{}]*)\}', css)
    check('%-26s %s survives as a rule' % (name, sel), band is not None)
    if band:
        b = band.group(1)
        check('  no gradient', 'linear-gradient' not in b)
        check('  no teal literal', not re.search(r'#0e7c8b|#0a5e6a', b))
        check('  no background at all', 'background' not in b)
        check('  and it no longer dresses for a dark ground',
              not re.search(r'color:\s*(?:white|#fff\b)', b))
        check('  the band\'s padding and radius went with its fill',
              'padding' not in b and 'border-radius' not in b)
    wasband = re.search(r'(?m)^[ \t]*' + re.escape(sel) + r'[ \t]*\{([^{}]*)\}', was)
    check('  CONTROL: it WAS a gradient',
          wasband is not None and 'linear-gradient' in wasband.group(1))
    check('  the round says why it went', 'THE TEAL BANNER WENT' in NOW[name])

# ===========================================================================
head('2. what the browser paints')
# ===========================================================================
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('  SKIP  playwright not installed - sections 2, 3 and 4 need it')
    sync_playwright = None

FIX = read(FIXTURE) if os.path.exists(FIXTURE) else ''
check('the Bootstrap fixture is present', bool(FIX))


def fixture(name, new, start, stop):
    """One document per variant. The first draft of this harness put all six
       panels in ONE page, each with its own <style> - and every stylesheet
       then applied to every panel, because `.page-header` is `.page-header`.
       All six measured as a gradient, including the three that had none."""
    src = NOW[name] if new else WAS[name]
    mk = markup_of(src)
    i, j = mk.find(start), mk.find(stop, mk.find(start))
    blk = mk[i:j] if i >= 0 and j > i else mk[:2000]
    blk = re.sub(r'\{%\s*if[^%]*%\}|\{%\s*endif\s*%\}|\{%\s*else\s*%\}', '', blk)
    blk = blk.replace('{{ comment_count }}', '47')
    blk = re.sub(r'\{[{%][^}]*[}%]\}', '', blk)
    return ('<!doctype html><meta charset=utf-8><style>%s</style>'
            '<style>%s</style><style>%s</style>'
            '<style>body{margin:0;padding:16px;background:#fff}</style>'
            '<body>%s</body>' % (FIX, BCSS, css_of(src), blk))


def paint(html, width, js, arg=None):
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={'width': width, 'height': 500})
        # OFFLINE. Font Awesome and the map tiles are CDN requests; a render
        # that waits for them measures the network, and one that gets them
        # measures whatever the CDN served today.
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg.set_content(html, wait_until='domcontentloaded')
        out = pg.evaluate(js, arg) if arg is not None else pg.evaluate(js)
        br.close()
    return out


BAND_JS = """(sel) => {
    const e = document.querySelector(sel);
    if (!e) return null;
    const c = getComputedStyle(e);
    return {grad: c.backgroundImage !== 'none', bg: c.backgroundColor,
            ink: c.color, pad: c.paddingLeft};
}"""


def rgb(s):
    return tuple(int(x) for x in re.findall(r'\d+', s)[:3])


INK = None
if sync_playwright is not None and FIX:
    INK = rgb(paint('<style>%s</style><body><i id=x></i>' % BCSS, 900,
                    """() => getComputedStyle(document.body).color""") or
              'rgb(33,52,60)')
    for name, (sel, a, b) in PAGES.items():
        for width, tag in ((980, 'desktop'), (430, 'phone  ')):
            now = paint(fixture(name, True, a, b), width, BAND_JS, sel)
            was = paint(fixture(name, False, a, b), width, BAND_JS, sel)
            check('%-26s %s BEFORE painted a gradient' % (name, tag),
                  was is not None and was['grad'])
            check('  AFTER it paints none', now is not None and not now['grad'],
                  str(now and now['bg']))
            check('  BEFORE its ink was white',
                  was is not None and rgb(was['ink']) == (255, 255, 255),
                  str(was and was['ink']))
            check('  AFTER its ink is dark on paper',
                  now is not None and sum(rgb(now['ink'])) < 300,
                  str(now and now['ink']))

# ===========================================================================
head('3. the Help button that would have vanished on a phone')
# ===========================================================================
# THE ROUND'S SHARPEST CLAIM. base hides .page-action-buttons
# .action-secondary below 768px, expecting an .action-more-btn to surface it.
# notification_settings has no More menu, so Help had to be promoted.
ROW_JS = """() => {
    const r = document.querySelector('.page-action-buttons');
    if (!r) return null;
    return [...r.children].map(e => {
        const b = e.getBoundingClientRect();
        return {cls: e.className, w: Math.round(b.width),
                display: getComputedStyle(e).display};
    });
}"""
# THIS SECTION MEASURES A DEFECT THIS ROUND DID NOT FIX, ON PURPOSE.
#
# base hides `.page-action-buttons .action-secondary` below 768px, on the
# assumption that an `.action-more-btn` will surface it. Neither of these two
# pages has one, so their Help buttons are unreachable on a phone.
#
# A draft of this round promoted both to `action-primary`.
# test_button_sweep.py refused it and the guard was RIGHT: its classifier
# holds that Help is never the verb, and the promotion wrote an exception to
# a correct rule. The fault is that `.action-secondary` carries two meanings -
# "quieter than the primary" to the classifier, "hidden below 768px because
# the More menu carries it" to base - and they agree on 22 bars and
# contradict on 11. Two promotions would have treated two instances and left
# nine.
#
# So the suite does not assert the fix. It asserts the TONES ARE UNTOUCHED,
# so a later draft cannot quietly promote them again, and it MEASURES the
# defect so the base round inherits a number rather than a memory.
PHONE = ('notification_settings.html', 'occupancy_trends.html')
for pg_name in PHONE:
    mk = markup_of(NOW[pg_name])
    was = markup_of(WAS[pg_name])
    now_h = re.search(r'<button[^>]*HelpModal[^>]*>', mk)
    was_h = re.search(r'<button[^>]*HelpModal[^>]*>', was)
    now_c = re.search(r'class="([^"]*)"', now_h.group(0)) if now_h else None
    was_c = re.search(r'class="([^"]*)"', was_h.group(0)) if was_h else None
    check('%-26s Help keeps the tone the button sweep gave it' % pg_name,
          now_c is not None and 'action-secondary' in now_c.group(1),
          now_c.group(1) if now_c else 'not found')
    check('  and this round changed no tone at all',
          now_c is not None and was_c is not None
          and set(now_c.group(1).split()) - {'help-btn'}
          == set(was_c.group(1).split()) - {'help-btn'},
          '%s -> %s' % (was_c.group(1) if was_c else '?',
                        now_c.group(1) if now_c else '?'))

if sync_playwright is not None and FIX:
    for pg_name in PHONE:
        html = fixture(pg_name, True, *PAGES[pg_name][1:])
        row = paint(html, 430, ROW_JS)
        check('%-26s has an action row on a phone' % pg_name, row is not None,
              str(len(row or [])) + ' item(s)')
        if not row:
            continue
        sec = [x for x in row if 'action-secondary' in x['cls']]
        # KNOWN AND UNFIXED. Reported as a measurement, not a pass or a fail:
        # asserting it is broken would make the base round's fix look like a
        # regression, and asserting it is fixed would be false today.
        print('        KNOWN, NOT FIXED HERE: %d secondary button(s) compute '
              'to %s at 430px' % (len(sec),
                                  sec[0]['display'] if sec else 'n/a'))
        check('  Back is still there as base\'s 44px square, so nobody is '
              'stranded on this page',
              any('action-back' in x['cls'] and x['display'] != 'none'
                  and 40 <= x['w'] <= 60 for x in row),
              ', '.join('%s %dpx' % (x['cls'], x['w']) for x in row))
        d = paint(html, 980, ROW_JS)
        check('  and on the desktop the row still has two controls',
              d is not None and len(d) == 2, str(len(d or [])))

# The defect is real, so it is measured once against BASE rather than argued.
if sync_playwright is not None and FIX:
    probe = ('<!doctype html><meta charset=utf-8><style>%s</style>'
             '<body><div class="page-action-buttons">'
             '<button class="btn action-secondary" id="s">Help</button>'
             '<a class="btn action-back" id="b">Back</a></div>' % BCSS)
    hid = paint(probe, 430, """() => getComputedStyle(
        document.getElementById('s')).display""")
    check('CONTROL: base really does hide .action-secondary below 768px - '
          'this is the fault the next round fixes in base', hid == 'none',
          str(hid))
    shown = paint(probe, 980, """() => getComputedStyle(
        document.getElementById('s')).display""")
    check('  CONTROL: .. and does not on the desktop', shown != 'none',
          str(shown))

# ===========================================================================
head('4. the figure that only existed on a dark ground')
# ===========================================================================
cr = 'comments_report.html'
_crmk = markup_of(nocomment(NOW[cr]))
_crcss = css_of(nocomment(NOW[cr]))
check('the count is base\'s .alv-stat now',
      'alv-stat-value' in _crmk and 'alv-stat-label' in _crmk)
check('  CONTROL: it was a .stat-box', 'stat-box' in markup_of(WAS[cr]))
check('  and no .stat-box rule survives',
      not re.search(r'(?m)^[ \t]*\.stat-box\b', _crcss))
for need in ('.alv-stat', '.alv-stat-value', '.alv-stat-label'):
    check('  base defines %s' % need, need in BCSS)

TILE_JS = """(sel) => {
    const e = document.querySelector(sel);
    if (!e) return null;
    const c = getComputedStyle(e);
    return {bg: c.backgroundColor, border: c.borderTopColor,
            bw: c.borderTopWidth, ink: getComputedStyle(
                e.firstElementChild || e).color};
}"""
if sync_playwright is not None and FIX:
    a, b = PAGES[cr][1:]
    now = paint(fixture(cr, True, a, b), 980, TILE_JS, '.alv-stat')
    was = paint(fixture(cr, False, a, b), 980, TILE_JS, '.stat-box')
    check('BEFORE: the tile was a 20%-alpha white, which is nothing on paper',
          was is not None and re.match(r'rgba\(255, 255, 255, 0\.2',
                                       was['bg']) is not None,
          str(was and was['bg']))
    check('AFTER:  it has an opaque ground of its own',
          now is not None and 'rgba' not in now['bg'], str(now and now['bg']))
    check('  and a real border, so it reads as a tile without a band behind it',
          now is not None and float(now['bw'].rstrip('px')) >= 1,
          str(now and now['bw']))

# THE PRINT BLOCK. The print round emptied it and said so; this round removed
# the shell.
check('the print block that held only the banner fill is gone',
      'print-color-adjust' not in _crcss)
check('  CONTROL: it was there', 'print-color-adjust' in css_of(WAS[cr]))
check('  and no empty @media print shell was left behind',
      not re.search(r'@media print\s*\{\s*\}', _crcss))
check('the action row this round did NOT touch is unchanged',
      re.search(r'<div class="page-action-buttons">.*?</div>', _crmk, re.S)
      is not None and 'Print Report' in _crmk)

# ===========================================================================
head('5. what the round did NOT do')
# ===========================================================================
# MODAL HEADERS KEEP THEIR TEAL. A suite that demanded none anywhere would
# pass only on work nobody agreed to.
_modal = 0
for name in PAGES:
    for m in re.finditer(r'(?m)^[ \t]*[^{\n]*modal-header[^{\n]*\{([^{}]*)\}',
                         css_of(nocomment(NOW[name]))):
        if 'linear-gradient' in m.group(1):
            _modal += 1
check('the teal modal headers on these pages are untouched - that is the '
      'next round', _modal >= 2, '%d still teal' % _modal)

_left = sum(len(re.findall(r'#0e7c8b|#0a5e6a', css_of(nocomment(NOW[n]))))
            for n in PAGES)
print('        %d teal literal(s) remain across the three pages - modal '
      'headers,\n        links, badges and focus rings. The modal round '
      'inherits this number.' % _left)
check('  and the number is a floor, not a silence', _left >= 8, str(_left))

# .action-bar: only occupancy_trends' copy went.
_all = [n for n in os.listdir(T) if n.endswith('.html')]
_ab = sorted(n for n in _all
             if re.search(r'class="[^"]*\baction-bar\b',
                          markup_of(read(os.path.join(T, n)))))
check('occupancy_trends no longer uses .action-bar',
      'occupancy_trends.html' not in _ab)
# THE CORPUS HALF ONLY WHEN THERE IS A CORPUS. This ran red in a build
# sandbox holding six templates - a fact about that directory, not about the
# round. A floor asserted against a partial tree is a check that fails
# correct work, which is worse than no check.
if len(_all) >= 60:
    check('  and the other .action-bar pages are untouched - a name base does '
          'not define, on a name-count that is its own survey',
          len(_ab) >= 25, '%d still use it' % len(_ab))
else:
    print('  SKIP  only %d template(s) here - the .action-bar corpus count '
          'needs the whole tree' % len(_all))

_cm = os.path.join(T, 'categories_management.html')
if os.path.exists(_cm):
    check('categories_management is untouched - it is recipe-side, and only '
          'the NAME-based exclusion list missed it',
          'linear-gradient' in css_of(read(_cm)))

for name in PAGES:
    txt = NOW[name]
    stack, fault = [], None
    OPEN = {'if': 'endif', 'for': 'endfor', 'block': 'endblock',
            'with': 'endwith'}
    CLOSE = {v: k for k, v in OPEN.items()}
    for m in re.finditer(r'\{%\s*(\w+)', txt):
        t = m.group(1)
        if t in OPEN:
            stack.append(t)
        elif t in CLOSE:
            if not stack or OPEN[stack.pop()] != t:
                fault = t
                break
    check('%-26s every Django tag is balanced' % name,
          fault is None and not stack, fault or ','.join(stack))
    # <div> balance, because this round unwrapped a block on one of them.
    opens = len(re.findall(r'<div\b', markup_of(txt)))
    closes = len(re.findall(r'</div>', markup_of(txt)))
    check('  and every <div> is closed', opens == closes,
          '%d open, %d close' % (opens, closes))
    for blk in re.findall(r'<style[^>]*>(.*?)</style>', txt, re.S):
        check('  the stylesheet is brace-balanced',
              blk.count('{') == blk.count('}'),
              '%d vs %d' % (blk.count('{'), blk.count('}')))

try:
    import django
    from django.conf import settings
    from django.template import Engine
    if not settings.configured:
        settings.configure(TEMPLATES=[], USE_TZ=True,
                           INSTALLED_APPS=['django.contrib.staticfiles',
                                           'django.contrib.humanize'])
        django.setup()
    # A bare Engine() does not auto-discover tag libraries - that is the
    # DjangoTemplates BACKEND's job - so every `{% load %}` these pages use
    # has to be handed over by name, and a missing one reports as a template
    # fault when it is a fact about this suite's settings. Handing them over
    # one at a time turned into three rounds of the same failure (static,
    # then humanize, then the project's own help_modal_tags), so the list is
    # DISCOVERED instead: Django's own, plus every templatetags module in
    # the repo.
    libs = {'static': 'django.templatetags.static',
            'humanize': 'django.contrib.humanize.templatetags.humanize',
            'i18n': 'django.templatetags.i18n',
            'l10n': 'django.templatetags.l10n',
            'tz': 'django.templatetags.tz'}
    for _dir, _sub, _files in os.walk(ROOT):
        if os.path.basename(_dir) != 'templatetags':
            continue
        _app = os.path.basename(os.path.dirname(_dir))
        for _f in _files:
            if _f.endswith('.py') and _f != '__init__.py':
                libs.setdefault(_f[:-3], '%s.templatetags.%s' % (_app, _f[:-3]))
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    eng = Engine(dirs=[T], libraries=libs)
    for name in PAGES:
        eng.from_string(NOW[name])
    check('Django itself parses all three', True, '%d librar(y/ies) handed over'
          % len(libs))
except ImportError:
    print('  SKIP  django not importable - the walkers above stand alone')
except Exception as e:
    # AN UNRESOLVABLE {% load %} IS NOT A TEMPLATE FAULT. It means this
    # checkout has no such templatetags module for the suite to hand over -
    # true of a partial tree, and a fact about the checkout rather than the
    # round. Reporting it as a failure would light the gate red on correct
    # work; the tag WALKER above still covers what this round could break.
    if 'is not a registered tag library' in str(e):
        print('  SKIP  %s - no templatetags module found for it in this '
              'checkout' % str(e).split('.')[0])
    else:
        check('Django itself parses all three', False, str(e)[:70])

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
print('\n  NOT PROVED HERE: that the views still send what these pages show,')
print('  and nothing about icons - Font Awesome is a CDN request and every')
print('  render above refuses the network on purpose. Open the three pages.')
if FAILED:
    print('\n  failures:')
    for x in FAILED[:20]:
        print('   - %s' % x)
print('=' * 72)
sys.exit(1 if FAIL else 0)
