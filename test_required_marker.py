"""test_required_marker.py - one required marker, in a colour we own.

    python test_required_marker.py

Run from the repo root, after apply_required_marker.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 2 IS THE ONE THAT MATTERS, and it exists because this round
    corrupted three files before it shipped. The bare-asterisk rule matched
    the `*` inside `accept="image/*"` on a file input nested in a label, and
    the patcher wrapped it:

        accept="image/<span class="alv-req">*</span>"

    - which breaks the attribute and the file picker's filter. The scanner
    had the SAME bug, so the patcher's cross-check against it agreed. Two
    implementations of one rule do not drift; one wrong rule implemented
    twice is still wrong, and a cross-check between tools that share a
    definition tests agreement rather than correctness.

    So this suite does not ask the scanner anything. It asks the FILES: no
    span may appear inside any attribute value, anywhere, and the three
    `accept="image/*"` must be intact.

  * SECTION 3 DRIVES A BROWSER, because "one colour" is a computed value.
    Before, the 112 sites rendered as THREE colours; after, they must render
    as ONE, and it must be base's --alv-bad rather than Bootstrap's #dc3545
    or the inline #FF0000. Both halves are measured, the control on the
    .bak_alvreq copies.

  * SECTION 4 asserts what the round did NOT do: text-danger survives where
    it is not a required marker, and every touched file still parses.
"""
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
FIXTURE = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
MARKER = 'alv-req'

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


def markup_of(s):
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
    return re.sub(r'<(script|style)[^>]*>.*?</\1>', '', s, flags=re.S)


def tag_fault(src):
    OPEN = {'if': 'endif', 'for': 'endfor', 'block': 'endblock',
            'with': 'endwith', 'comment': 'endcomment',
            'spaceless': 'endspaceless', 'autoescape': 'endautoescape'}
    CLOSE = {v: k for k, v in OPEN.items()}
    stack = []
    for m in re.finditer(r'\{%\s*(\w+)', src):
        t = m.group(1)
        ln = src.count('\n', 0, m.start()) + 1
        if t in OPEN:
            stack.append((t, ln))
        elif t in CLOSE:
            if not stack:
                return 'line %d: %s with nothing open' % (ln, t)
            top, at = stack.pop()
            if OPEN[top] != t:
                return ('line %d: %s closes {%% %s %%} from line %d'
                        % (ln, t, top, at))
    return 'unclosed {%% %s %%} from %d' % stack[-1] if stack else None


ALL = []
for d, _s, fs in os.walk(T):
    for fn in sorted(fs):
        if fn.endswith('.html') and '.bak_' not in fn:
            ALL.append(os.path.relpath(os.path.join(d, fn),
                                       T).replace(os.sep, '/'))
ALL.sort()
TOUCHED = [r for r in ALL
           if os.path.exists(os.path.join(T, *r.split('/')) + '.bak_alvreq')]
if not TOUCHED:
    sys.exit('! no .bak_alvreq backups - run apply_required_marker.py first.')

BASE_CSS = css_of(read(BASE))
FIX = read(FIXTURE) if os.path.exists(FIXTURE) else ''

# ===========================================================================
head('1. one spelling, one rule, and eighteen page rules gone')
# ===========================================================================
check('base declares .alv-req exactly once',
      len(re.findall(r'(?m)^\s*\.alv-req\s*\{', BASE_CSS)) == 1)
_m = re.search(r'\.alv-req\s*\{([^}]*)\}', BASE_CSS)
check('  and it points at base\'s own danger token',
      _m is not None and 'var(--alv-bad)' in _m.group(1))
check('  not at a hardcoded value',
      _m is not None and not re.search(r'#[0-9a-fA-F]{3,8}', _m.group(1)))
check('CONTROL: base did NOT declare it before',
      '.alv-req' not in css_of(read(BASE + '.bak_alvreq'))
      if os.path.exists(BASE + '.bak_alvreq') else True)

_sites = 0
for rel in ALL:
    _sites += markup_of(read(os.path.join(T, *rel.split('/')))).count(
        'class="%s"' % MARKER)
check('112 marker sites across the property side', _sites == 112, str(_sites))
check('  in 33 templates', len(TOUCHED) - 1 == 33 or len(TOUCHED) == 33,
      '%d touched (incl. base)' % len(TOUCHED))

# The eighteen page rules, and NOTHING else named them.
for cls in ('required-mark', 'required', 'req'):
    live = [r for r in ALL
            if re.search(r'\.' + cls + r'(?![\w-])',
                         css_of(read(os.path.join(T, *r.split('/')))))]
    check('no page still styles .%-14s' % cls, not live, str(live[:4]))
_was = 0
for rel in TOUCHED:
    b = os.path.join(T, *rel.split('/')) + '.bak_alvreq'
    for cls in ('required-mark', 'required', 'req'):
        _was += len(re.findall(r'(?m)^[ \t]*[^{}\n]*\.' + cls
                               + r'(?![\w-])[^{}\n]*\{', css_of(read(b))))
check('CONTROL: eighteen such rules existed before', _was == 18, str(_was))

# ===========================================================================
head('2. the defect this round shipped once, and must never ship again')
# ===========================================================================
# `accept="image/*"` on a file input inside a label. The bare-asterisk rule
# matched it and the patcher wrapped it in a span, breaking the attribute.
_inattr = []
for rel in ALL:
    src = read(os.path.join(T, *rel.split('/')))
    for m in re.finditer(r'=\s*"[^"]*<span[^"]*"', src):
        _inattr.append((rel, ' '.join(m.group(0).split())[:44]))
check('no <span> appears inside any attribute value, anywhere',
      not _inattr, str(_inattr[:3]))

_accept = [r for r in ALL
           if 'accept="image/' in read(os.path.join(T, *r.split('/')))]
check('CONTROL: there ARE accept="image/..." attributes to break',
      len(_accept) >= 3, '%d file(s)' % len(_accept))
# NOT a literal `accept="image/*"`: passport_management carries
# `accept="image/*,application/pdf"`, and demanding the short form failed on
# a correct file. Compare the attribute to what it WAS - which is the claim
# anyway, and works whatever the value.
for rel in _accept:
    p_ = os.path.join(T, *rel.split('/'))
    now = re.findall(r'accept="[^"]*"', read(p_))
    old = (re.findall(r'accept="[^"]*"', read(p_ + '.bak_alvreq'))
           if os.path.exists(p_ + '.bak_alvreq') else now)
    check('%-34s its accept attribute is byte-identical' % rel, now == old,
          '%s vs %s' % (now[:1], old[:1]))

# The one genuinely bare asterisk DID get an element.
_cat = os.path.join(T, 'categories_management.html')
if os.path.exists(_cat):
    check('the one真 bare asterisk got an element'.replace('真', ' genuinely '),
          'Category Name <span class="%s">*</span>' % MARKER
          in ' '.join(read(_cat).split()))

# Nothing outside a <label> was touched.
for rel in TOUCHED:
    if rel == 'base.html':
        continue
    p = os.path.join(T, *rel.split('/'))
    now, was = read(p), read(p + '.bak_alvreq')
    outside = re.sub(r'<label\b.*?</label>', '<label/>', markup_of(now),
                     flags=re.S)
    was_out = re.sub(r'<label\b.*?</label>', '<label/>', markup_of(was),
                     flags=re.S)
    if outside != was_out:
        check('%-34s nothing outside a <label> moved' % rel, False)
check('nothing outside a <label> moved, in any of the %d' % len(TOUCHED),
      True)

# ===========================================================================
head('3. the browser: three colours become one')
# ===========================================================================
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('  SKIP  playwright not installed')
    sync_playwright = None


def labels_with_star(src, n=3):
    mk = markup_of(src)
    out = []
    for m in re.finditer(r'<label\b[^>]*>.*?</label>', mk, re.S):
        if '*' in m.group(0):
            out.append(' '.join(m.group(0).split()))
        if len(out) >= n:
            break
    return out


SAMPLE = ['projects/projects_add.html', 'user_add.html',
          'finance_expense_add.html', 'customer_form.html',
          'passport_management.html', 'categories_management.html']
SAMPLE = [s for s in SAMPLE if s in TOUCHED]

if sync_playwright is not None and SAMPLE:
    def inks(new):
        parts = []
        for rel in SAMPLE:
            p = os.path.join(T, *rel.split('/'))
            src = read(p if new else p + '.bak_alvreq')
            parts.append('<style>%s</style>%s'
                         % (css_of(src), ''.join(labels_with_star(src))))
        html = ('<!doctype html><meta charset=utf-8><style>%s</style>'
                '<style>%s</style>%s'
                % (FIX, css_of(read(BASE if new else BASE + '.bak_alvreq')),
                   ''.join(parts)))
        f = os.path.join(tempfile.gettempdir(), 'req.html')
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(html)
        pg.goto('file://' + f)
        pg.wait_for_timeout(120)
        return pg.evaluate(
            """() => Array.from(document.querySelectorAll('label span'))
                 .map(s => getComputedStyle(s).color)""")

    with sync_playwright() as pw:
        _b = pw.chromium.launch()
        pg = _b.new_page(viewport={'width': 900, 'height': 700})
        now, was = inks(True), inks(False)
        check('CONTROL: the probe actually rendered some markers',
              len(now) >= 6, '%d span(s)' % len(now))
        check('every marker renders ONE colour', len(set(now)) == 1,
              str(sorted(set(now))))
        _bad = re.search(r'--alv-bad:\s*(#[0-9a-fA-F]{6})', BASE_CSS)
        if _bad:
            r, g, bl = (int(_bad.group(1)[i:i + 2], 16) for i in (1, 3, 5))
            want = 'rgb(%d, %d, %d)' % (r, g, bl)
            check('  and it is base\'s --alv-bad', set(now) == {want},
                  '%s vs %s' % (sorted(set(now)), want))
            check('  not Bootstrap\'s #dc3545',
                  'rgb(220, 53, 69)' not in now)
            check('  and not the inline red', 'rgb(255, 0, 0)' not in now)
        check('CONTROL: before the round they were THREE colours',
              len(set(was)) >= 2, str(sorted(set(was))))
        check('  including Bootstrap\'s and the louder inline one',
              'rgb(220, 53, 69)' in was and 'rgb(255, 0, 0)' in was,
              str(sorted(set(was))))
        _b.close()

# ===========================================================================
head('4. what the round did NOT do')
# ===========================================================================
# text-danger is a general Bootstrap utility. Only the asterisk spans in
# labels moved; every other use is somebody else's round.
# THE PROPERTY SIDE ONLY. celebration_management and
# household_member_management are recipe-side and the sweep skips them by
# design, so scanning ALL files reported the round as having missed two files
# it was never going to touch. A check whose scope is wider than its round
# reports failures that are not defects - the fifth time here.
RECIPE = ('recipe', 'meal_plan', 'wcim', 'pantry', 'ingredient',
          'celebration', 'household_member', 'unit_conversions',
          'measurement_units', 'map_ingredients', 'import_recipe',
          'preview_imported')
PROPERTY = [r for r in ALL if not any(k in r for k in RECIPE)]
check('CONTROL: the recipe side really is excluded, and is not empty',
      len(ALL) - len(PROPERTY) >= 5,
      '%d recipe-side of %d' % (len(ALL) - len(PROPERTY), len(ALL)))
_td = [r for r in PROPERTY
       if 'text-danger' in markup_of(read(os.path.join(T, *r.split('/'))))]
check('text-danger survives where it is NOT a required marker',
      len(_td) >= 3, '%d file(s) still use it' % len(_td))
for rel in _td[:4]:
    mk = markup_of(read(os.path.join(T, *rel.split('/'))))
    check('  %-32s .. and none of them is an asterisk span' % rel,
          not re.search(r'<span[^>]*text-danger[^>]*>\s*\*\s*</span>', mk))

for rel in TOUCHED:
    f = tag_fault(read(os.path.join(T, *rel.split('/'))))
    if f:
        check('%-34s still parses' % rel, False, f)
check('every touched template still parses (%d)' % len(TOUCHED), True)

check('the recipe side was left alone',
      not any(k in r for r in TOUCHED
              for k in ('recipe', 'meal_plan', 'wcim', 'pantry')))

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('\n  failures:')
    for x in FAILED[:20]:
        print('   - %s' % x)
print('=' * 72)
sys.exit(1 if FAIL else 0)
