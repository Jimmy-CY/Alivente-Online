"""test_required_sweep.py - every required field says so, in one spelling.

    python test_required_sweep.py

Run from the repo root, after apply_required_sweep.py.

WHAT THIS SUITE IS FOR

  * SECTION 2 checks each page against its own backup: markers were added
    and NOTHING else changed.

  * SECTION 3 IS THE CLAIM WORTH MAKING. Across the whole corpus, every
    control carrying `required` whose label can be identified unambiguously
    must carry a marker. It is measured with a floor and the exceptions are
    named, so a screen added next month with an unmarked required field
    shows up here rather than in a support message.

  * SECTION 4 RENDERS ONE. A class name in the markup proves nothing about
    what a reader sees; the asterisk is measured in a browser for colour and
    for being visible at all. base's own `--alv-bad` is the value it must
    resolve to - if Bootstrap's red ever came back, this is what would say
    so.

  * SECTION 5 reports the mirror image: labels that SAY a field is required
    beside a control that does not enforce it. Reported, never failed -
    adding `required` changes what a form accepts, which is behaviour.

WHAT THIS SUITE CANNOT DO, SAID FIRST. It cannot tell you whether the right
fields are the required ones - that is a business question. And where a
label carries no `for` attribute it infers the association from position,
which is a heuristic; it says so wherever it does.
"""
import asyncio
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
FIXTURE = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
MARK = '<span class="alv-req">*</span>'

SKIP = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
        'unit_conversions', 'celebration_', 'import_recipe',
        'map_ingredients', 'measurement_units', 'household_member',
        'categories_management')

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


def visible(t):
    """Scripts, styles and comments BLANKED - same length, so offsets still
       line up, but nothing inside them is reachable. The first required
       round wrapped the `*` in accept="image/*" and broke a file picker."""
    def blank(m):
        return ' ' * len(m.group(0))
    t = re.sub(r'<(script|style)[^>]*>.*?</\1>', blank, t, flags=re.S)
    return re.sub(r'<!--.*?-->', blank, t, flags=re.S)


def rel_of(p):
    return os.path.relpath(p, T).replace(os.sep, '/')


TEMPLATES = []
for _d, _s, _fs in os.walk(T):
    for _f in _fs:
        if _f.endswith('.html'):
            _p = os.path.join(_d, _f)
            _r = rel_of(_p)
            if _r != 'base.html' and not any(s in _r for s in SKIP):
                TEMPLATES.append(_p)
TEMPLATES.sort()


def sites(src):
    """(marked, unmarked, undecidable) for one template.

       A site is a control carrying `required` whose label can be named:
       either by `<label for=...>`, or - where no `for` exists - by the
       nearest preceding label with NO OTHER CONTROL between it and this
       one. That second form is a heuristic and the third bucket is what it
       refuses to guess at."""
    vis = visible(src)
    labels = [(m.start(), m.end(), m.group(0))
              for m in re.finditer(r'<label\b[^>]*>.*?</label>', vis, re.S)]
    marked, unmarked, unknown = [], [], []
    for m in re.finditer(r'<(?:input|select|textarea)\b[^>]*>', vis, re.I):
        if not re.search(r'\brequired\b', m.group(0), re.I):
            continue
        i = re.search(r'\bid\s*=\s*"([^"]+)"', m.group(0))
        cid = i.group(1) if i else None
        lab = None
        if cid:
            for a, b, t in labels:
                if re.search(r'\bfor\s*=\s*"' + re.escape(cid) + r'"', t):
                    lab = t
                    break
        if lab is None:
            prev = [x for x in labels if x[1] <= m.start()]
            if prev:
                a, b, t = prev[-1]
                between = vis[b:m.start()]
                if (not re.search(r'<(?:input|select|textarea)\b', between,
                                  re.I)) and len(between) <= 400:
                    lab = t
        if lab is None:
            unknown.append(cid or '(no id)')
        elif 'alv-req' in lab:
            marked.append(cid or '(no id)')
        else:
            unmarked.append(cid or '(no id)')
    return marked, unmarked, unknown


# ===========================================================================
head('1. base still owns the one spelling')
# ===========================================================================
B = read(BASE)
_css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', B, re.S))
_rule = re.search(r'\.alv-req\s*\{([^}]*)\}', _css)
check('base declares .alv-req', _rule is not None)
if _rule:
    check('  in a colour base owns, not a literal',
          'var(--alv-bad)' in _rule.group(1),
          re.sub(r'\s+', ' ', _rule.group(1)).strip())
check('  CONTROL: and --alv-bad is actually declared',
      re.search(r'--alv-bad\s*:', _css) is not None)

# ===========================================================================
head('2. the pages this round moved, against their own backups')
# ===========================================================================
MOVED = [p for p in TEMPLATES if os.path.exists(p + '.bak_reqs')]
check('the round left backups to compare against', len(MOVED) >= 14,
      '%d found' % len(MOVED))
_added = 0
for p in MOVED:
    rel = rel_of(p)
    now, was = read(p), read(p + '.bak_reqs')
    d = now.count(MARK) - was.count(MARK)
    _added += d
    check('%-36s gained %2d marker(s)' % (rel, d), d > 0)
    # NOTHING BUT MARKERS. Strip from BOTH sides - several of these pages
    # already had markers, so stripping one side only fails correct work.
    check('  and nothing else changed',
          now.replace(' ' + MARK, '') == was.replace(' ' + MARK, ''))
    for tag in ('div', 'form', 'label', 'span'):
        a = (len(re.findall(r'<%s\b' % tag, visible(now)))
             - len(re.findall(r'</%s>' % tag, visible(now))))
        b = (len(re.findall(r'<%s\b' % tag, visible(was)))
             - len(re.findall(r'</%s>' % tag, visible(was))))
        if a != b:
            check('  <%s> balance unchanged' % tag, False, '%+d -> %+d'
                  % (b, a))
print('        %d marker(s) added in total.' % _added)
check('  it added what the round said it would', _added >= 75,
      '%d' % _added)

# ===========================================================================
head('3. the whole corpus - every required field that can be named is marked')
# ===========================================================================
M, U, K = [], [], []
for p in TEMPLATES:
    a, b, c = sites(read(p))
    M += [(rel_of(p), x) for x in a]
    U += [(rel_of(p), x) for x in b]
    K += [(rel_of(p), x) for x in c]
print('        %d required control(s) carry a marker; %d do not; %d have no '
      'label\n        this suite is willing to infer.'
      % (len(M), len(U), len(K)))
for rel, cid in U:
    print('          UNMARKED  %-38s %s' % (rel, cid))
check('no required field with an identifiable label is unmarked', not U,
      '%d unmarked' % len(U))
# A REPORT WITH A FLOOR, not an equality - a hardcoded corpus count has
# failed correct work twelve times here.
check('  CONTROL: and there really are marked fields to have got wrong',
      len(M) >= 100, '%d' % len(M))
if K:
    print('        NOT JUDGED - no label this suite will infer:')
    for rel, cid in K:
        print('          %-38s %s' % (rel, cid))
check('  the undecidable set is small and named', len(K) <= 4, '%d' % len(K))

# ===========================================================================
head('4. rendered - the asterisk is visible, and in the colour base owns')
# ===========================================================================
if not os.path.exists(FIXTURE):
    print('  SKIP  test_fixture_bootstrap413.css not found')
else:
    async def _run():
        from playwright.async_api import async_playwright
        # A REAL LABEL FROM A REAL TEMPLATE, not one typed here.
        src = read(os.path.join(T, 'properties_add.html'))
        m = re.search(r'<label\b[^>]*>[^<]*(?:<strong>.*?</strong>)?\s*'
                      + re.escape(MARK) + r'</label>', src, re.S)
        if m is None:
            check('a real marked label was found to render', False)
            return
        page = ('<!doctype html><meta charset="utf-8"><style>%s\n%s</style>'
                '<body><div class="form-group">%s'
                '<input class="form-control"></div></body>'
                % (read(FIXTURE), _css, m.group(0)))
        async with async_playwright() as pw:
            b = await pw.chromium.launch()
            pg = await b.new_page(viewport={'width': 900, 'height': 400})
            blocked = []

            async def _off(route, request):
                blocked.append(request.url)
                await route.abort()
            await pg.route(re.compile(r'^https?://'), _off)
            await pg.set_content(page, wait_until='domcontentloaded')
            info = await pg.evaluate("""() => {
                const s = document.querySelector('.alv-req');
                if (!s) return null;
                const c = getComputedStyle(s);
                const r = s.getBoundingClientRect();
                return {colour: c.color, weight: c.fontWeight,
                        w: r.width, h: r.height, text: s.textContent};
            }""")
            await b.close()
            check('  the network was blocked', not blocked,
                  '%d request(s)' % len(blocked))
            check('the marker renders at all', info is not None)
            if info:
                check('  and it is the asterisk', info['text'].strip() == '*')
                check('  and it has a box, so it is visible',
                      info['w'] > 0 and info['h'] > 0,
                      '%.1f x %.1f' % (info['w'], info['h']))
                # --alv-bad is #b3261e
                check('  and it is base\'s --alv-bad, not Bootstrap\'s red',
                      info['colour'] == 'rgb(179, 38, 30)', info['colour'])
                check('  CONTROL: and it is NOT #dc3545, the old value',
                      info['colour'] != 'rgb(220, 53, 69)', info['colour'])
    try:
        asyncio.run(_run())
    except Exception as e:
        check('the marker renders', False, '%s: %s' % (type(e).__name__,
                                                       str(e)[:60]))

# ===========================================================================
head('5. the mirror image - reported, never failed')
# ===========================================================================
# A label that SAYS required beside a control that does not enforce it. This
# round does not touch them: adding `required` changes what a form ACCEPTS,
# which is behaviour, not styling, and wants its own round with the person
# who knows the business rule.
BACK = []
for p in TEMPLATES:
    vis = visible(read(p))
    ids = set()
    for m in re.finditer(r'<(?:input|select|textarea)\b[^>]*>', vis, re.I):
        if re.search(r'\brequired\b', m.group(0), re.I):
            i = re.search(r'\bid\s*=\s*"([^"]+)"', m.group(0))
            if i:
                ids.add(i.group(1))
    for m in re.finditer(r'<label\b([^>]*)>(.*?)</label>', vis, re.S):
        if 'alv-req' not in m.group(2):
            continue
        fo = re.search(r'\bfor\s*=\s*"([^"]+)"', m.group(1))
        if fo and fo.group(1) not in ids:
            BACK.append((rel_of(p), fo.group(1)))
print('        %d label(s) mark a field required beside a control that does '
      'not\n        enforce it. Reported, not swept.' % len(BACK))
_by = {}
for rel, cid in BACK:
    _by.setdefault(rel, []).append(cid)
for rel in sorted(_by):
    print('          %-38s %s' % (rel, ', '.join(_by[rel][:5])
                                  + (' ...' if len(_by[rel]) > 5 else '')))
check('this is a report, and it found the ones already known', len(BACK) >= 1,
      '%d' % len(BACK))

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
print('\n  NOT PROVED HERE: that the RIGHT fields are the required ones.')
print('  That is a business question, not one a parser can answer.')
if FAILED:
    print('\n  failures:')
    for x in FAILED[:20]:
        print('   - %s' % x)
print('=' * 72)
sys.exit(1 if FAIL else 0)
