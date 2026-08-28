#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""No form control renders shorter than the value it is showing.

Run from the repo root. Needs Playwright's chromium, like the other browser
suites.

WHY THIS EXISTS. Bootstrap 4.1.3 pins controls to a fixed 38px; thirty-odd
templates add 10px of padding on top without freeing it, so the chosen value
is shaved at the bottom. Whether it LOOKS broken depends on the font - it does
on Segoe UI, it did not on the Linux faces every render in this project was
made against - which is why it survived a table round, a button round and a
filter round unnoticed, and was found by a person looking at a dropdown.

So this suite does not judge by eye or by a formula for line metrics. It
clones each control, releases its height, and asks the browser what the
natural height is. The browser decides; the machine it runs on does not.
"""
import os, re, sys, glob, asyncio

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL  = os.path.join(ROOT, 'pages', 'templates')

_pass = _fail = 0
_fails = []


def check(name, ok, extra=''):
    global _pass, _fail
    if ok:
        _pass += 1
        print('  PASS  %s %s' % (name, extra))
    else:
        _fail += 1
        _fails.append(name)
        print('  FAIL  %s %s' % (name, extra))
    return ok


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


def flatten(s):
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r'\{%\s*if[^%]*%\}((?:(?!\{%\s*(?:if|else|endif)).)*?)\{%\s*else\s*%\}'
                   r'((?:(?!\{%\s*(?:if|else|endif)).)*?)\{%\s*endif\s*%\}', r'\1', s, flags=re.S)
        s = re.sub(r'\{%\s*if[^%]*%\}((?:(?!\{%\s*(?:if|else|endif)).)*?)\{%\s*endif\s*%\}',
                   r'\1', s, flags=re.S)
    s = re.sub(r'\{%[^%]*%\}', '', s)
    return re.sub(r'\{\{[^}]*\}\}', 'Sample Value', s)


BASE = read(os.path.join(TPL, 'base.html'))
_bs  = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
BOOTSTRAP = read(_bs) if os.path.exists(_bs) else ''

print('\n' + '-' * 72 + '\n 1. the rule itself\n' + '-' * 72)
check('the Bootstrap fixture is present', bool(BOOTSTRAP))
check('  and it really does pin a control to a fixed height',
      re.search(r'\.form-control\{[^}]*height:calc\(2\.25rem \+ 2px\)', BOOTSTRAP)
      is not None)
_rule = re.search(r'select\.form-control:not\(\[size\]\):not\(\[multiple\]\)\s*,\s*'
                  r'input\.form-control\s*,\s*textarea\.form-control\s*\{[^}]*height:\s*auto',
                  css_of(BASE), re.S)
check('base.html frees that height', _rule is not None)
check('  UNSCOPED - not just inside a filter panel',
      '.alv-filter select.form-control' not in BASE)
check('  and it matches Bootstrap\'s own :not() shape, or it loses (0,1,1) to (0,2,1)',
      _rule is not None and ':not([size]):not([multiple])' in _rule.group(0))

# ---------------------------------------------------------------------------
JS = """() => [...document.querySelectorAll(
        'input.form-control,select.form-control,textarea.form-control')]
  .map(e => {
    const r = e.getBoundingClientRect();
    if (!r.height) return null;                 // hidden: not this test's business
    const c = e.cloneNode(true);
    c.style.cssText += 'height:auto!important;position:absolute;visibility:hidden';
    e.parentNode.appendChild(c);
    const n = c.getBoundingClientRect().height;
    c.remove();
    return n > r.height + 0.5
      ? {tag: e.tagName.toLowerCase(), h: Math.round(r.height), n: Math.round(n)}
      : null;
  }).filter(Boolean)"""


async def sweep(free_height):
    """Render every template and count controls shorter than their content."""
    from playwright.async_api import async_playwright
    out = {}
    base_css = css_of(BASE)
    if not free_height:
        # the CONTROL run: put Bootstrap's constraint back, at a specificity
        # that beats ours, so the suite can prove it is measuring something
        base_css += ('\nhtml body select.form-control:not([size]):not([multiple]),'
                     'html body input.form-control,html body textarea.form-control'
                     '{height:calc(2.25rem + 2px)}')
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page(viewport={'width': 1900, 'height': 900})
        for p in sorted(glob.glob(os.path.join(TPL, '*.html'))
                        + glob.glob(os.path.join(TPL, '*', '*.html'))):
            rel = os.path.relpath(p, TPL).replace(os.sep, '/')
            if rel == 'base.html':
                continue
            t = read(p)
            if 'form-control' not in t:
                continue
            body = re.search(r'\{%\s*block content\s*%\}(.*?)\{%\s*endblock', t, re.S)
            html = flatten(re.sub(r'<script[^>]*>.*?</script>', '',
                                  (body.group(1) if body else t), flags=re.S))
            await pg.set_content(
                "<!doctype html><html><head><meta charset='utf-8'>"
                "<style>%s</style><style>%s</style><style>%s</style></head>"
                "<body>%s</body></html>" % (BOOTSTRAP, base_css, css_of(t), html))
            await pg.wait_for_timeout(30)
            try:
                bad = await pg.evaluate(JS)
            except Exception as e:            # a page that will not render is a
                bad = [{'tag': 'ERROR', 'h': 0, 'n': 0, 'err': str(e)[:60]}]
            if bad:
                out[rel] = bad
        await br.close()
    return out


async def main():
    print('\n' + '-' * 72 + '\n 2. every template that has a form control\n' + '-' * 72)
    clipped = await sweep(free_height=True)
    check('no control renders shorter than its own value (%d page(s) with a '
          'problem)' % len(clipped), not clipped)
    for rel, bad in sorted(clipped.items())[:12]:
        print('        %-34s %s' % (rel, ', '.join(
            '%s %d<%d' % (b['tag'], b['h'], b['n']) for b in bad[:4])))

    print('\n' + '-' * 72 + '\n 3. the negative control\n' + '-' * 72)
    # A suite that cannot fail is worth nothing. Put Bootstrap's fixed height
    # back at a specificity that wins, and the same sweep must light up.
    was = await sweep(free_height=False)
    _n = sum(len(v) for v in was.values())
    check('CONTROL: with the height pinned again, %d control(s) across %d '
          'page(s) DO clip' % (_n, len(was)), _n >= 20)
    for rel, bad in sorted(was.items())[:8]:
        print('        %-34s %d control(s)' % (rel, len(bad)))
    check('  so this suite is measuring something real', bool(was) and not clipped)

asyncio.run(main())

print('\n' + '=' * 72)
print(' %d passed, %d failed' % (_pass, _fail))
for f in _fails:
    print('   FAILED: %s' % f)
print('=' * 72)
sys.exit(1 if _fail else 0)
