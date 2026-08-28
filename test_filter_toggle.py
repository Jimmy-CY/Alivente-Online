#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The filter panel has one owner, one control, and one place to look.

Run from the repo root.  Needs Playwright's chromium, like the other browser
suites.

WHAT THIS IS DEFENDING. Before this round four pages each recorded "is the
panel open" SEVEN times - a class, a second class, an inline style.cssText, a
data- attribute, a sessionStorage key, a window global and a module global -
because each new mechanism was added when the previous one failed to stick.
The checks below are mostly about there being exactly ONE of things.
"""
import os, re, sys, json, asyncio

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL  = os.path.join(ROOT, 'pages', 'templates')

PAGES = ['suppliers.html', 'properties.html', 'tenant.html', 'fsr.html',
         'act_expense.html', 'invoices.html', 'projects/projects.html',
         'passport_management.html',
         # Joined in the Physical Invoices round, once it had chips to fall
         # back on. It was excluded for a SAFETY reason, not a scheduling one,
         # and the fix was to remove the reason rather than the exclusion.
         'physical_invoice_list.html']

_n_pass = _n_fail = 0
_fails = []


def check(name, ok, extra=''):
    global _n_pass, _n_fail
    if ok:
        _n_pass += 1
        print('  PASS  %s %s' % (name, extra))
    else:
        _n_fail += 1
        _fails.append(name)
        print('  FAIL  %s %s' % (name, extra))
    return ok


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


def rules(t):
    # STRIP COMMENTS FIRST. A comment containing braces - and the component's
    # own comment quotes `.page-action-buttons .action-secondary { display:
    # none }` to explain why the Filter button is not a secondary - makes a
    # naive rule regex read the comment as a rule and the real rule as part
    # of a selector. This suite reported ".btn.action-filter is not defined"
    # about a rule sitting right there in the file.
    out = []
    css = re.sub(r'/\*.*?\*/', '', css_of(t), flags=re.S)
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
        sel = ' '.join(m.group(1).split())
        if sel and not sel.startswith('@'):
            out.append((sel, m.group(2)))
    return out


def element_span(t, start):
    d = 0
    for m in re.finditer(r'<div\b|</div\s*>', t[start:]):
        d += 1 if m.group(0).startswith('<div') else -1
        if d == 0:
            return start, start + m.end()
    return start, None


# ===========================================================================
head_written = False
BASE = read(os.path.join(TPL, 'base.html'))

# The pinned Bootstrap the live pages load. Without it this suite measures a
# page that does not exist - see the note in the browser section.
_bs = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
BOOTSTRAP = read(_bs) if os.path.exists(_bs) else ''

head('1. base.html owns the component, and owns it once')
bcss = css_of(BASE)
bsel = [s for s, _ in rules(BASE)]
check('base defines .alv-filter', '.alv-filter' in bsel)
check('  hidden is the DEFAULT, not a class you add',
      any(s == '.alv-filter' and 'display: none' in b for s, b in rules(BASE)))
check('  and .is-open is what shows it',
      any(s == '.alv-filter.is-open' and 'display: block' in b for s, b in rules(BASE)))
check('base defines .btn.action-filter', '.btn.action-filter' in bsel)
check('  paired with .btn, or a page .btn-info beats it',
      all(s.startswith('.btn.action-filter') or not s.startswith('.action-filter')
          or s.startswith('.action-filter-count') or '.page-action-buttons' in s
          for s in bsel if 'action-filter' in s))
check('  the pressed state is visibly different',
      any('[aria-pressed="true"]' in s for s in bsel))
check('base defines the chips row', '.alv-filter-active' in bsel)
check('  it is HIDDEN by default - no flash of an empty "Active filters:"',
      any(s == '.alv-filter-active' and 'display: none' in b for s, b in rules(BASE)))
check('  and shown by a class the script sets',
      '.alv-filter-active.has-filters' in bsel)
check('the component script is present', 'alv-filter script v1' in BASE)
check('  and exactly once', BASE.count('alv-filter script v1') == 1)
check('  the CSS block is there exactly once', BASE.count('ALV-FILTER v1') == 1)
check('base braces still balance (%d/%d)' % (bcss.count('{'), bcss.count('}')),
      bcss.count('{') == bcss.count('}'))
check('no Django tag leaked into the component CSS',
      '{%' not in bcss and '{{' not in bcss)
# The mobile survival rule is the whole reason .action-filter is not a
# secondary - base hides those at 768px.
check('base still hides ordinary secondaries on a phone',
      re.search(r'\.page-action-buttons \.action-secondary\s*\{[^}]*display:\s*none',
                bcss) is not None)
check('  but gives .action-filter a width there instead',
      re.search(r'\.page-action-buttons \.action-filter\s*\{[^}]*width:\s*44px',
                bcss) is not None)

head('2. the seven mechanisms are gone')
MECH = [('a second class, .force-expanded', r'force-expanded'),
        ('inline style.cssText',            r'style\.cssText\s*\+='),
        ('the data- attribute',             r'data-force-expanded'),
        ('the sessionStorage FORCE_ keys',  r'sessionStorage\.\w+Item\(\s*[\'"]FORCE_'),
        ('the window global',               r'window\.\w*(?:PANEL|EXPANDED)\w*\s*='),
        ('the module global',               r'PANEL_IS_MANUALLY_EXPANDED'),
        ('the className regex strip',       r'className\s*=\s*\w+\.className\.replace\(')]
for label, rx in MECH:
    hits = [p for p in PAGES if re.search(rx, read(os.path.join(TPL, p.replace('/', os.sep))))]
    check('%s is gone from every migrated page' % label, not hits,
          '' if not hits else 'still in: ' + ', '.join(hits))
check('  and the chevron went with the gesture it described',
      not any('filter-toggle-icon' in read(os.path.join(TPL, p.replace('/', os.sep)))
              for p in PAGES))
check('  no page still binds a toggle to its header',
      not any(re.search(r'filter-header[^>]*onclick=',
                        read(os.path.join(TPL, p.replace('/', os.sep)))) for p in PAGES))

head('3. every migrated page, statically')
for p in PAGES:
    t = read(os.path.join(TPL, p.replace('/', os.sep)))
    short = p.split('/')[-1]
    check('%-26s has exactly one Filter button' % short,
          len(re.findall(r'class="btn action-filter"', t)) == 1)
    check('%-26s   the button names its panel' % short,
          re.search(r'aria-controls="(\w+)"', t) is not None)
    pm = re.search(r'<div class="alv-filter [^"]*"[^>]*id="(\w+)"', t)
    ok = pm is not None
    check('%-26s   the panel carries .alv-filter and an id' % short, ok)
    if not ok:
        continue
    check('%-26s   aria-controls matches that id' % short,
          re.search(r'aria-controls="%s"' % pm.group(1), t) is not None)
    check('%-26s   the page keeps its OWN panel class too' % short,
          re.search(r'<div class="alv-filter [\w-]*filter-panel', t) is not None)
    pa, pz = element_span(t, pm.start())
    cm = re.search(r'<div class="alv-filter-active"', t)
    check('%-26s   the chips are OUTSIDE the panel' % short,
          cm is not None and pz is not None and not (pa < cm.start() < pz))
    check('%-26s   nothing pins the chips shut inline' % short,
          cm is None or 'style=' not in t[cm.start():t.index('>', cm.start())])
    check('%-26s   something on the page makes a .filter-tag' % short,
          'filter-tag' in t)
    panel_cls = re.search(r'<div class="alv-filter ([\w-]+)"', t).group(1)
    check('%-26s   .%s still declares padding' % (short, panel_cls),
          any(s == '.' + panel_cls and 'padding' in b for s, b in rules(t)))
    c = css_of(t)
    check('%-26s   its CSS braces balance' % short, c.count('{') == c.count('}'))
    check('%-26s   its div tags balance' % short,
          len(re.findall(r'<div\b', t)) == len(re.findall(r'</div\s*>', t)))

head('4. the page that used to be excluded')
# It was left out because hiding a panel with nothing behind it makes a
# filtered list indistinguishable from an unfiltered one. That is fixed at the
# root - the chips exist now - so the exclusion is gone. This checks the
# REASON was addressed, not merely that a button appeared.
_pi = read(os.path.join(TPL, 'physical_invoice_list.html'))
check('physical_invoice_list has chips to fall back on',
      'alv-filter-active' in _pi and 'filter-tag' in _pi)
check('  built in the view, not four nested ifs per chip',
      '{% for c in filter_chips %}' in _pi)
check('  and each chip removes ONLY itself', 'c.remove' in _pi)
check('  its panel is no longer forced open', 'filter-panel expanded' not in _pi)


head('5. the negative control - would ANY of this fail on the old page?')
# A suite that passes on the un-migrated page is measuring nothing. The
# backups are the honest comparison: they are what these pages looked like
# before the round.
_probes = [
    ('a Filter button in the bar', lambda t: 'class="btn action-filter"' in t),
    ('the panel named .alv-filter', lambda t: '<div class="alv-filter ' in t),
    ('no .force-expanded anywhere', lambda t: 'force-expanded' not in t),
    ('no chevron', lambda t: 'filter-toggle-icon' not in t),
    ('no header onclick', lambda t: not re.search(r'filter-header[^>]*onclick=', t)),
    ('no inline style.cssText', lambda t: not re.search(r'style\.cssText\s*\+=', t)),
]
_would = 0
_bak_seen = 0
for p in PAGES:
    b = os.path.join(TPL, p.replace('/', os.sep)) + '.bak_filter'
    if not os.path.exists(b):
        continue
    _bak_seen += 1
    old = read(b)
    for label, fn in _probes:
        if not fn(old):
            _would += 1
check('backups were found to compare against (%d)' % _bak_seen, _bak_seen > 0)
check('  %d of the %d checks above FAIL on the pre-round pages'
      % (_would, _bak_seen * len(_probes)), _would >= _bak_seen * 3,
      '(if this were 0 the suite would be measuring nothing)')
# and the one thing that must be TRUE of the old pages, or the round was
# solving a problem that did not exist
_chips_inside = 0
for p in PAGES:
    b = os.path.join(TPL, p.replace('/', os.sep)) + '.bak_filter'
    if not os.path.exists(b):
        continue
    old = read(b)
    pm = re.search(r'<div class="[\w-]*filter-panel"', old)
    cm = re.search(r'<div class="[\w-]*active-filters"', old)
    if pm and cm:
        pa, pz = element_span(old, pm.start())
        if pz and pa < cm.start() < pz:
            _chips_inside += 1
check('  and the chips really WERE inside the panel before (%d page(s))'
      % _chips_inside, _chips_inside >= 6,
      '- which is what made hiding it unsafe')

head('6. the browser - one mechanism, driven')


def flatten(s):
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r'\{%\s*if[^%]*%\}((?:(?!\{%\s*(?:if|else|endif)).)*?)\{%\s*else\s*%\}'
                   r'((?:(?!\{%\s*(?:if|else|endif)).)*?)\{%\s*endif\s*%\}', r'\1', s, flags=re.S)
        s = re.sub(r'\{%\s*if[^%]*%\}((?:(?!\{%\s*(?:if|else|endif)).)*?)\{%\s*endif\s*%\}',
                   r'\1', s, flags=re.S)
    s = re.sub(r'\{%[^%]*%\}', '', s)
    return re.sub(r'\{\{[^}]*\}\}', 'x', s)


def fragment(t):
    """Bar through end of panel. Walks the panel's own divs - a regex that
    stopped at a closing tag at a fixed indentation once ran past its element
    into an upload modal and every measurement after it was taken on the
    wrong thing."""
    a = t.find('<div class="page-action-buttons">')
    pm = re.search(r'<div class="alv-filter [^"]*"', t)
    if a < 0 or not pm:
        return None
    _, z = element_span(t, pm.start())
    return None if z is None else flatten(t[a:z])


head('5b. every <script> still PARSES')
# THE CHECK THAT WOULD HAVE SAVED TWO ROUNDS.
#
# Twice now an edit has produced a <script> that does not parse - once by
# deleting `if (EXTERNAL_INTERFERENCE_DETECTED) {` and orphaning its closing
# brace, once by stripping a call out of `if (checkForActiveFilters()) {` and
# leaving `if () {`. A block that does not parse defines NOTHING, so every
# function in it silently ceases to exist. The page renders perfectly and does
# nothing at all, and no check that looks for undefined names can see it,
# because nothing ever runs to be undefined.
#
# Compared against the BACKUP rather than judged absolutely: the flattener
# here is crude and mangles at least one pre-existing block on act_expense,
# which is not this round's business. Only a block that parsed BEFORE and
# fails AFTER is a regression.
async def parse_check():
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page()
        await pg.goto('about:blank')

        async def ok(src):
            return await pg.evaluate(
                "s => { try { new Function(s); return true } catch (e) "
                "{ return e instanceof SyntaxError ? false : true } }", src)

        for p in PAGES:
            live = os.path.join(TPL, p.replace('/', os.sep))
            bak = live + '.bak_filter'
            if not os.path.exists(bak):
                continue
            short = p.split('/')[-1]
            pat = r'<script(?![^>]*src=)[^>]*>(.*?)</script>'
            before = [flatten(b) for b in re.findall(pat, read(bak), re.S)]
            after = [flatten(b) for b in re.findall(pat, read(live), re.S)
                     if 'alv-filter script' not in b]
            bad = []
            for i, src in enumerate(after):
                if i < len(before) and await ok(before[i]) and not await ok(src):
                    bad.append(i)
            check('%-26s no <script> stopped parsing (%d block(s))'
                  % (short, len(after)), not bad,
                  '' if not bad else 'block(s) %s' % bad)
        await br.close()

asyncio.run(parse_check())


async def drive():
    from playwright.async_api import async_playwright
    comp = re.search(r'<script>\s*/\* ===== alv-filter script v1 =====.*?</script>',
                     BASE, re.S)
    if not check('the component script could be lifted from base.html', comp is not None):
        return
    comp_js = re.sub(r'</?script>', '', comp.group(0))
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        for p in PAGES:
            short = p.split('/')[-1]
            t = read(os.path.join(TPL, p.replace('/', os.sep)))
            frag = fragment(t)
            if not check('%-26s fragment extracted' % short, frag is not None):
                continue
            if not check('%-26s   and no Django tag survived it' % short,
                         '{%' not in frag):
                continue
            pid = re.search(r'<div class="alv-filter [^"]*"[^>]*id="(\w+)"', t).group(1)
            tags = re.search(r'<div class="[\w-]*filter-tags" id="(\w+)"', t)
            if not check('%-26s   it has a chips container' % short, tags is not None):
                continue
            tags = tags.group(1)
            # THE PAGE'S OWN SCRIPTS GO IN TOO. Without them this harness
            # cannot see a page whose JS throws - and it could not see one,
            # while `if (PANEL_IS_MANUALLY_EXPANDED)` sat there referencing a
            # global the round had deleted. Every reference would have been a
            # ReferenceError killing the rest of its handler, and 254 checks
            # passed anyway. A harness that runs only the code you wrote will
            # only ever find faults in the code you wrote.
            page_js = '\n'.join(
                '(function(){try{%s}catch(e){window.__pageErr=(window.__pageErr||[]);'
                'window.__pageErr.push(String(e));}})();' % flatten(b)
                for b in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', t, re.S)
                if 'alv-filter script' not in b)
            # A GLOBAL ERROR HANDLER, NOT JUST try/catch.
            #
            # The try/catch below wraps each script block, which catches
            # errors thrown while the block RUNS. Almost nothing on these
            # pages throws then: the work happens inside a DOMContentLoaded
            # callback that fires later, by which time the try/catch has long
            # since returned. So the bug that shipped - a ReferenceError on
            # the first line of that callback, which stopped every filter
            # listener from being attached - was completely invisible here,
            # and re-creating it by hand still produced a clean run.
            # window.onerror sees it. try/catch never could.
            trap = ("window.__pageErr=[];window.addEventListener('error',"
                    "function(e){window.__pageErr.push(String(e.message||e.error));});")
            # BOOTSTRAP FIRST, exactly as base.html loads it. This harness
            # rendered without it until now, which made every Bootstrap
            # interaction invisible - including `.form-control { height:
            # calc(2.25rem + 2px) }`, which pins a select to 38px while these
            # panels need 42. The selects were clipping their own value on
            # every one of these pages and I reported them as "identical
            # before and after", because in a page with no Bootstrap they
            # were. A harness missing the framework the real page loads can
            # only ever measure a page that does not exist.
            doc = ("<!doctype html><html><head><meta charset='utf-8'>"
                   "<style>%s</style><style>%s</style>"
                   "<style>%s</style></head><body><div style='padding:20px'>%s</div>"
                   "<script>%s</script><script>%s</script><script>%s</script></body></html>"
                   % (BOOTSTRAP, css_of(BASE), css_of(t), frag, trap, comp_js, page_js))
            f = os.path.join(ROOT, '_filt_%s.html' % short.replace('.html', ''))
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write(doc)
            pg = await br.new_page(viewport={'width': 1440, 'height': 900})
            await pg.goto('file://' + f)
            st = lambda: pg.evaluate("""(a)=>{const g=(e,p)=>getComputedStyle(e)[p];
                const P=document.getElementById(a[0]),B=document.querySelector('.action-filter');
                const C=B.querySelector('.action-filter-count'),H=document.querySelector('.alv-filter-active');
                return {disp:g(P,'display'),pressed:B.getAttribute('aria-pressed'),
                        count:C.textContent,countDisp:g(C,'display'),
                        chips:g(H,'display'),inside:P.contains(H),
                        // How many form controls in the panel are actually
                        // VISIBLE. A panel that opens to reveal its own
                        // header and nothing else passed every other check
                        // in this file: display:none on .filter-content
                        // survived on one page because only the rule that
                        // UNDID it was dropped. "It opens" is not the claim
                        // that matters; "you can use it" is.
                        fields:[...P.querySelectorAll('select,input,textarea')]
                                 .filter(e=>e.getBoundingClientRect().height>0).length,
                        w:B.getBoundingClientRect().width};}""", [pid])
            await pg.wait_for_timeout(80)
            errs = await pg.evaluate("()=>window.__pageErr||[]")
            # ANY ReferenceError IS A FAULT - with a named allowlist for
            # the things this harness genuinely cannot load, and nothing
            # else. The first version of this check did the opposite: it
            # listed the identifiers the round removed and ignored everything
            # else. That is backwards, and it shipped a broken page.
            #
            # `const wasForceExpanded = sessionStorage.getItem('FORCE_...')`
            # was deleted as a dead statement while `if (wasForceExpanded ||
            # ...)` two lines below still referenced it. The name was not on
            # my list, so 264 checks passed while the page threw on the first
            # line of its DOMContentLoaded handler and never attached a
            # single filter listener. Search, the country dropdown, Enter and
            # Clear All were all dead. The user found it in thirty seconds.
            EXTERNAL = ('$', 'jQuery', 'bootstrap', 'Chart', 'html2canvas',
                        'XLSX', 'moment')
            def _external(msg):
                # [\w$] - `$` is not a \w, and jQuery is the single most
                # likely name to be missing in a fragment harness. The first
                # version of this line used \w+ and so allow-listed nothing.
                # re.SEARCH, not match: window.onerror reports
                # "Uncaught ReferenceError: ...", so an anchored match found
                # nothing and the allowlist silently allow-listed nothing.
                m = re.search(r"ReferenceError: ([\w$]+) is not defined", msg)
                return bool(m) and m.group(1) in EXTERNAL
            refs = [e for e in errs if 'ReferenceError' in e and not _external(e)]
            check('%-26s no undefined name in its own scripts' % short,
                  not refs, '' if not refs else str(refs[:2])[:140])
            await pg.evaluate("(id)=>{document.getElementById(id).innerHTML='';}", tags)
            await pg.wait_for_timeout(50)
            s = await st()
            check('%-26s closed on load' % short, s['disp'] == 'none', s['disp'])
            check('%-26s   button agrees' % short, s['pressed'] == 'false')
            check('%-26s   empty chips row takes no space' % short, s['chips'] == 'none')
            closed_fields = s['fields']
            check('%-26s   and its fields are unreachable while closed' % short,
                  closed_fields == 0, str(closed_fields))
            await pg.click('.action-filter'); s = await st()
            check('%-26s   one click opens it' % short, s['disp'] == 'block', s['disp'])
            check('%-26s   ...and REVEALS ITS FIELDS (%d visible)'
                  % (short, s['fields']), s['fields'] > 0)
            # A CONTROL MUST BE TALL ENOUGH FOR ITS OWN VALUE. Measured by
            # cloning it and releasing the height - no formula, no guess at
            # line metrics. Whether Bootstrap's fixed height actually clips
            # depends on the font, so the machine that renders this must not
            # be the thing that decides: the natural height is.
            clipped = await pg.evaluate("""(id)=>{
              const p=document.getElementById(id);
              return [...p.querySelectorAll('select.form-control,input.form-control')]
                .map(e=>{const r=e.getBoundingClientRect(); if(!r.height) return null;
                  const c=e.cloneNode(true);
                  c.style.cssText+='height:auto!important;position:absolute;visibility:hidden';
                  e.parentNode.appendChild(c);
                  const nat=c.getBoundingClientRect().height; c.remove();
                  return nat > r.height + 0.5 ? [Math.round(r.height), Math.round(nat)] : null;})
                .filter(Boolean);}""", pid)
            check('%-26s   every control is tall enough to READ' % short,
                  not clipped, '' if not clipped else
                  'rendered/natural %s' % clipped[:3])
            await pg.click('.action-filter'); s = await st()
            check('%-26s   a second closes it' % short, s['disp'] == 'none')
            await pg.evaluate("""(id)=>{document.getElementById(id).innerHTML=
                '<span class="filter-tag">a<button class="remove-tag">x</button></span>'
                +'<span class="filter-tag">b</span>';}""", tags)
            await pg.wait_for_timeout(60); s = await st()
            check('%-26s   two chips drive the count to 2' % short, s['count'] == '2', s['count'])
            check('%-26s   and reveal the row' % short, s['chips'] != 'none')
            await pg.evaluate("(id)=>{document.getElementById(id).innerHTML='';}", tags)
            await pg.wait_for_timeout(60); s = await st()
            check('%-26s   CONTROL: removing them hides both again' % short,
                  s['count'] == '' and s['countDisp'] == 'none' and s['chips'] == 'none')
            await pg.click('.action-filter')
            await pg.evaluate("(id)=>{const f=document.querySelector('#'+id+' form');"
                              "if(f) f.dispatchEvent(new Event('submit'));}", pid)
            flag = await pg.evaluate("()=>sessionStorage.getItem('alvFilterOpen')")
            check('%-26s   its own submit remembers the panel was open' % short,
                  flag == '1', str(flag))
            await pg.reload(); s = await st()
            check('%-26s   so the reload reopens it' % short, s['disp'] == 'block', s['disp'])
            left = await pg.evaluate("()=>sessionStorage.getItem('alvFilterOpen')")
            check('%-26s   and the flag is CONSUMED' % short, left is None, str(left))
            await pg.reload(); s = await st()
            check('%-26s   CONTROL: a real reload starts closed' % short, s['disp'] == 'none')
            await pg.set_viewport_size({'width': 375, 'height': 800}); await pg.reload()
            s = await st()
            check('%-26s   375px: Filter survives the collapse' % short, s['w'] > 20,
                  '%.0fpx' % s['w'])
            sec = await pg.evaluate("()=>{const e=document.querySelector("
                                    "'.page-action-buttons .action-secondary');"
                                    "return e?e.getBoundingClientRect().width:-1}")
            check('%-26s   CONTROL: a secondary is hidden there' % short, sec <= 0,
                  '%.0fpx' % sec)
            await pg.close()
            os.remove(f)
        await br.close()

asyncio.run(drive())

print('\n' + '=' * 72)
print(' %d passed, %d failed' % (_n_pass, _n_fail))
for f in _fails:
    print('   FAILED: %s' % f)
print('=' * 72)
sys.exit(1 if _n_fail else 0)
