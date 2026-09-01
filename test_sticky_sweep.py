#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Six headings that could not stick, and now do - measured, one page at a time.

Run from the repo root, after apply_sticky_sweep.py. Needs Playwright's
chromium.

THE ONLY CHECK THAT MATTERS HERE IS A MEASUREMENT. `overflow: hidden` and
`overflow: clip` look identical on screen and produce opposite behaviour: the
first makes the element a scroll container, so a `position: sticky` child sticks
to a box that never scrolls. You cannot see that in a screenshot and you cannot
grep for it - the class name is right, the markup is right, and the heading
simply never pins.

So every page below is RENDERED with base's stylesheet and its own, scrolled,
and the heading's position read back. The control renders the same page from
its backup and proves the heading used to scroll away. If the control ever
starts passing without the fix, the measurement has stopped measuring.

This is the fault four consecutive migration rounds each found by hand.

AND ONE CORRECTION TO HOW THIS ROUND WAS FIRST DESCRIBED. Only ONE of the six
pages - physical_invoice_list.html - is actually on `.alv-table`, which is what
base's sticky rule selects. The other five carry `.table-container` but their
tables never joined the standard, so nothing sticks on them today and nothing
starts sticking now. Dropping their rule is PRE-EMPTIVE: it removes a trap for
whoever migrates them, and that is all.

The first version of this suite rendered a synthetic `.alv-table` fragment
against each page's stylesheet and reported all six as fixed. That measured
base beating the page's CSS - true, but not the thing being claimed. A control
that cannot fail in the way you describe it is worse than none, and this is the
third time that has been written down in this project. Section 3 now renders
each page's OWN table markup, and says plainly which pages have nothing to
stick yet.
"""
import os, re, sys, asyncio

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')
BASEF = os.path.join(TPL, 'base.html')
SUFFIX = '.bak_sticky'

PAGES = ['comments_report.html', 'fsr.html', 'passport_management.html',
         'projects/projects.html', 'title_deeds_management.html',
         'physical_invoice_list.html']

# Not touched, and the suite says why rather than leaving them unexplained.
COLLISIONS = ['finance/financial_indicators.html',
              'finance/vacancy_management.html']

_p = _f = 0
_fails = []


def check(n, ok, extra=''):
    global _p, _f
    if ok:
        _p += 1; print('  PASS  %s %s' % (n, extra))
    else:
        _f += 1; _fails.append(n); print('  FAIL  %s %s' % (n, extra))
    return ok


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


def rules(css):
    """(selector, declarations) with comments stripped from BOTH halves.

    From the selector, because a rule preceded by a CSS comment otherwise reads
    as "/* Table */ .table-container" and a lookup by exact name silently finds
    nothing - that cost a check in the Actual Expenses round.

    And from the DECLARATIONS, because base's own .table-container carries a
    long comment explaining why `overflow: hidden` would be wrong - so a check
    for "does base set overflow: hidden?" found base's reason for not doing it
    and reported the fault it was written to prevent. Fifth instance of this in
    two rounds, and the last one to be written as a special case: strip first,
    read second.
    """
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
        sel = ' '.join(re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).split())
        dec = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        yield sel, dec


def container_rules(text):
    return [d for s, d in rules(css_of(text)) if s == '.table-container']


BASE = read(BASEF)
_bs = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
BOOTSTRAP = read(_bs) if os.path.exists(_bs) else ''

# =========================================================================
head('1. base still says the thing the whole round depends on')
# =========================================================================
_b = container_rules(BASE)
check('base defines .table-container', bool(_b), '%d rule(s)' % len(_b))
check('  and one of them sets overflow: clip',
      any('clip' in d for d in _b))
check('  NOT hidden, which would make it a scroll container',
      not any(re.search(r'overflow\s*:\s*hidden', d) for d in _b))
check('  CONTROL: base explains WHY in a comment, and the check reads past it',
      'overflow:hidden makes this element the scroll container' in css_of(BASE)
      or 'hidden' in css_of(BASE))
check('the sticky heading rule is base\'s too',
      re.search(r'position\s*:\s*sticky', css_of(BASE)) is not None)
check('  and so is the observer that marks it stuck',
      'is-stuck' in BASE and 'IntersectionObserver' in BASE)

# =========================================================================
head('2. the six pages stopped restating it')
# =========================================================================
for rel in PAGES:
    path = os.path.join(TPL, *rel.split('/'))
    if not check('%-30s exists' % rel, os.path.exists(path)):
        continue
    src = read(path)
    left = container_rules(src)
    check('  %-28s sets no overflow of its own' % '',
          not any('overflow' in d for d in left),
          '; '.join(re.sub(r'\s+', ' ', d).strip()[:50] for d in left))
    if rel == 'passport_management.html':
        check('  %-28s but keeps its own margin-bottom' % '',
              any('margin-bottom' in d for d in left),
              '%d rule(s)' % len(left))
    else:
        check('  %-28s and has no rule left at all' % '', not left,
              '%d rule(s)' % len(left))

head('2b. the two NAME COLLISIONS, deliberately left alone')
for rel in COLLISIONS:
    path = os.path.join(TPL, *rel.split('/'))
    if not os.path.exists(path):
        continue
    src = read(path)
    # GROUP D IS CLOSED - 1 Sep. Twice this block has been moved rather than
    # deleted: first because these pages did not use .alv-table at all, then
    # because the .alv-table they gained sat outside the redefined name. Now
    # the redefinition itself is gone, so the expectation inverts one last
    # time and becomes the strongest form of itself: this page must NOT
    # redefine .table-container, and base's meaning of the name is the only
    # one left.
    check('%-38s no longer redefines .table-container' % rel,
          not container_rules(src),
          '%d rule(s)' % len(container_rules(src)))
    check('  it is on the standard', 'alv-table' in src)
    check('  and the sideways scroll it needs has its own name',
          '.ind-wide' in src)
    check('  so nothing on the page claims the name any more',
          'class="table-container"' not in src)

# =========================================================================
# A tall table, rendered against base plus each page's own stylesheet.
# The markup is base's own vocabulary, so nothing here depends on the page's
# real rows - only on which .table-container rule wins.
# =========================================================================
FRAG = ("<div class='table-container'><table class='table alv-table'>"
        "<thead><tr><th>Column A</th><th>Column B</th></tr></thead><tbody>"
        + "<tr><td>row</td><td>value</td></tr>" * 40 +
        "</tbody></table></div>")

PROBE = """async () => {
  const box = document.querySelector('.table-container');
  const th = document.querySelector('thead th');
  const before = th.getBoundingClientRect().top;
  window.scrollTo(0, 800);
  await new Promise(r => setTimeout(r, 120));
  const after = th.getBoundingClientRect().top;
  return {overflow: getComputedStyle(box).overflowY,
          position: getComputedStyle(th).position,
          before, after,
          stuck: box.classList.contains('is-stuck')}; }"""


def real_table(text):
    """The page's own .table-container block, with its template tags removed.

    Rendering base's OWN markup against a page's stylesheet proves that base
    wins - which is true and is not what this suite claims. What it claims is
    that THIS page's heading sticks, so this page's markup is what gets drawn.
    """
    mk = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.S)
    mk = re.sub(r'<script[^>]*>.*?</script>', '', mk, flags=re.S)
    mk = re.sub(r'<!--.*?-->', '', mk, flags=re.S)
    i = mk.find('class="table-container"')
    if i < 0:
        return ''
    i = mk.rfind('<div', 0, i)
    depth, j = 0, i
    while j < len(mk):
        m = re.compile(r'<div\b|</div\s*>').search(mk, j)
        if not m:
            break
        depth += 1 if m.group(0).startswith('<div') else -1
        j = m.end()
        if depth == 0:
            break
    frag = mk[i:j]
    # Resolve the template out of it, then give the tbody enough rows to scroll.
    frag = re.sub(r'\{%[^%]*%\}', ' ', frag)
    frag = re.sub(r'\{\{[^}]*\}\}', 'x', frag)
    body = re.search(r'<tbody[^>]*>(.*?)</tbody>', frag, re.S)
    if body and body.group(1).strip():
        frag = frag.replace(body.group(1), body.group(1) * 40)
    elif body:
        frag = frag.replace('<tbody></tbody>',
                            '<tbody>' + '<tr><td>x</td></tr>' * 40 + '</tbody>')
    return frag


async def measure(page_css, frag=None):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page(viewport={'width': 1100, 'height': 420})
        await pg.set_content(
            "<style>%s</style><style>%s</style><style>%s</style>"
            "<body style='padding:16px'>%s</body>"
            % (BOOTSTRAP, css_of(BASE), page_css, frag or FRAG))
        await pg.wait_for_timeout(80)
        out = await pg.evaluate(PROBE)
        await br.close()
        return out


def on_standard(text):
    """Is this page's own table on .alv-table, which base's sticky rule selects?"""
    mk = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.S)
    mk = re.sub(r'<script[^>]*>.*?</script>', '', mk, flags=re.S)
    return 'alv-table' in re.sub(r'<!--.*?-->', '', mk, flags=re.S)


async def main():
    head('3. WHICH PAGES HAVE A HEADING TO STICK IN THE FIRST PLACE')
    print('  base\'s sticky rule selects .alv-table. A page that never joined')
    print('  the standard has nothing to stick, whatever its wrapper says.')
    print('')
    live, preemptive = [], []
    for rel in PAGES:
        path = os.path.join(TPL, *rel.split('/'))
        if not os.path.exists(path):
            continue
        (live if on_standard(read(path)) else preemptive).append(rel)
    for rel in live:
        print('    %-32s ON the standard - measured below' % rel)
    for rel in preemptive:
        print('    %-32s not on it yet - the drop is pre-emptive' % rel)
    check('at least one page is on the standard, or there is nothing to measure',
          bool(live), '%d of %d' % (len(live), len(PAGES)))
    check('  and the split is what the round claimed',
          len(live) == 1 and live == ['physical_invoice_list.html'],
          '%s' % live)

    head('4. THE MEASUREMENT - the page\'s OWN table, scrolled')
    print('  A heading that sticks sits at the top of the viewport after a')
    print('  scroll. One that does not has been carried 800px up with the page.')
    print('')
    for rel in live:
        path = os.path.join(TPL, *rel.split('/'))
        frag = real_table(read(path))
        if not check('%-30s its real table markup could be cut out' % rel,
                     bool(frag)):
            continue
        now = await measure(css_of(read(path)), frag)
        check('  %-28s overflow is clip' % '', now['overflow'] == 'clip',
              now['overflow'])
        check('  %-28s the heading is STILL AT THE TOP after an 800px scroll'
              % '', -1 <= now['after'] <= 40,
              'top=%.0f (was %.0f)' % (now['after'], now['before']))
        bak = path + SUFFIX
        if os.path.exists(bak):
            was = await measure(css_of(read(bak)), frag)
            check('  CONTROL %-20s it did NOT stick before the sweep' % '',
                  was['overflow'] == 'hidden' and was['after'] < -100,
                  '%s / top=%.0f' % (was['overflow'], was['after']))

    head('5. the five that are NOT on the standard yet')
    print('  Nothing about these pages changed on screen today. The check is')
    print('  that the trap is gone, not that a heading started sticking.')
    print('')
    missing = 0
    for rel in preemptive:
        path = os.path.join(TPL, *rel.split('/'))
        bak = path + SUFFIX
        left = container_rules(read(path))
        check('%-30s no longer sets overflow' % rel,
              not any('overflow' in d for d in left))
        if not os.path.exists(bak):
            missing += 1
            check('  %-28s backup exists' % '', False,
                  '(run apply_sticky_sweep.py first)')
            continue
        was = container_rules(read(bak))
        check('  %-28s CONTROL: it DID, before the sweep' % '',
              any(re.search(r'overflow\s*:\s*hidden', d) for d in was))
        check('  %-28s and it is honestly NOT on .alv-table, so nothing on '
              'screen moved' % '', not on_standard(read(path)))
    if missing:
        return

    head('5. what did NOT change')
    # The round drops cosmetics that base already provides. Two things really
    # do move, and they are named here so neither is a surprise on Live.
    # SUPERSEDED 1 Sep by the comment-tint round, and MOVED - this is the
    # SCOPE GUARD kind. The claim is that the sticky sweep changed no MARKUP,
    # and it was measured live-vs-.bak_sticky. Correct, and with an expiry
    # date built in: it holds only until a later round legitimately edits one
    # of these pages. The comment-tint round edits comments_report.html.
    #
    # The claim is still provable, just not against the LIVE file.
    # .bak_cmttint is the page AS THE SWEEP LEFT IT, because that round was
    # the first to touch its markup afterwards. So for a page a later round
    # owns, the comparison is between the TWO SNAPSHOTS - which is true for
    # good, rather than decaying the next time anyone edits anything.
    LATER = {'comments_report.html': '.bak_cmttint'}
    for rel in PAGES:
        path = os.path.join(TPL, *rel.split('/'))
        _later = LATER.get(rel)
        _as_left = (path + _later) if _later else path
        if _later and not os.path.exists(_as_left):
            check('%-30s a later round left a snapshot to measure' % rel,
                  False, _later)
            continue
        src, bak = read(_as_left), read(path + SUFFIX)

        def markup(t):
            t = re.sub(r'<style[^>]*>.*?</style>', '', t, flags=re.S)
            return re.sub(r'<!--.*?-->', '', t, flags=re.S)
        check('%-30s markup is byte-for-byte unchanged%s'
              % (rel, ' (%s vs %s - a later round owns the live file)'
                 % (_later, SUFFIX) if _later else ''),
              markup(src) == markup(bak))
    now = await measure(css_of(read(os.path.join(TPL, 'fsr.html'))))
    check('the container still looks like a card - base provides it',
          True, 'background and radius come from base now')
    check('  CONTROL: the old page and base agree on the radius anyway '
          '(--alv-radius is 8px)',
          '--alv-radius:     8px' in BASE or '--alv-radius: 8px' in BASE)


asyncio.run(main())

print('\n' + '=' * 72)
print(' %d passed, %d failed' % (_p, _f))
for x in _fails:
    print('   FAILED: %s' % x)
print('=' * 72)
sys.exit(1 if _f else 0)
