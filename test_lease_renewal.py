#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""lease_renewal_report agrees with tenant_report about a declined renewal.

Run from the repo root. Needs Playwright's chromium.

THE POINT. Every other item on the outstanding list was inherited; this one we
caused. The Tenants push moved tenant_report to paint a declined renewal AMBER
and left this page painting it RED. The check that matters is not "declined is
amber" - it is that the TWO PAGES SAY THE SAME THING, read from both files, so
that changing one and not the other fails here rather than in front of a user.
"""
import os, re, sys, asyncio

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL  = os.path.join(ROOT, 'pages', 'templates')
LR   = os.path.join(TPL, 'lease_renewal_report.html')
TR   = os.path.join(TPL, 'tenant_report.html')

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


BASE = read(os.path.join(TPL, 'base.html'))
LRT, TRT = read(LR), read(TR)
_bs = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
BOOTSTRAP = read(_bs) if os.path.exists(_bs) else ''

head('1. the two pages agree - read from both files')
_lr = re.findall(r'<span class="alv-pill (alv-pill-\w+)">', LRT)
check('lease_renewal_report has three status pills', len(_lr) == 3, str(_lr))
check('  pending and declined wear the SAME one',
      len(_lr) >= 2 and _lr[0] == _lr[1], '%s vs %s' % (_lr[0], _lr[1]) if len(_lr) >= 2 else '')
check('  and vacant is the neutral one',
      len(_lr) == 3 and _lr[2] == 'alv-pill-neutral', _lr[2] if len(_lr) == 3 else '')
# tenant_report decides its pill in a template conditional; pull the arm that
# handles 'declined' rather than trusting the file's order.
_m = re.search(r"tenant_renewal_status == 'declined'\s*%\}\s*(alv-pill-\w+)", TRT)
check('tenant_report names a pill for declined', _m is not None,
      _m.group(1) if _m else '')
check('  AND IT IS THE SAME PILL - the two pages cannot disagree again',
      _m is not None and len(_lr) >= 2 and _m.group(1) == _lr[1],
      '%s / %s' % (_m.group(1) if _m else '?', _lr[1] if len(_lr) > 1 else '?'))

head('2. the old vocabulary is gone, screen AND print')
for dead in ('card-status-bar', 'status-bar-pending', 'status-bar-declined',
             'status-bar-vacant'):
    check('  %-22s survives nowhere' % dead, dead not in LRT)
check('  no Bootstrap red is left', '#dc3545' not in LRT,
      '' if '#dc3545' not in LRT else 'still there')
check('  and the print block no longer forces three colours',
      'print-color-adjust' not in css_of(LRT) or
      'status-bar' not in css_of(LRT))
check('.highlight-red survives, on the token',
      re.search(r'\.highlight-red\s*\{[^}]*var\(--alv-bad\)', css_of(LRT)) is not None)
check('  because those dates really have passed - red is right there',
      'highlight-red' in LRT)

head('3. the cards are base\'s, and nothing was orphaned')
check('three card heads', len(re.findall(r'<div class="alv-card-head">', LRT)) == 3)
check('  each card carries .alv-card beside its own name',
      len(re.findall(r'<div class="alv-card renewal-card', LRT)) == 3)
check('  the h3 survived - a card head is not a reason to lose a heading',
      len(re.findall(r'<h3 class="property-name">', LRT)) == 3)
_b = LRT.find('<div class="alv-card-body tenant-details">')
_msg = LRT.find('<p class="card-message">')
check('  the declined message sits INSIDE a card body', 0 < _b < _msg,
      'body at %d, message at %d' % (_b, _msg))
_c = css_of(LRT)
check('  CSS braces balance (%d/%d)' % (_c.count('{'), _c.count('}')),
      _c.count('{') == _c.count('}'))
check('  div tags balance',
      len(re.findall(r'<div\b', LRT)) == len(re.findall(r'</div\s*>', LRT)))
check('  and the template tags do',
      len(re.findall(r'\{%\s*if\b', LRT)) == len(re.findall(r'\{%\s*endif\s*%\}', LRT))
      and len(re.findall(r'\{%\s*for\b', LRT)) == len(re.findall(r'\{%\s*endfor\s*%\}', LRT)))

# ---------------------------------------------------------------------------
# What the file says and what the reader sees are two different questions. The
# markup above is right in both the amber-icon case and the grey-icon case,
# because the icon's colour is decided by base's `.alv-card > .alv-card-head
# .fas { color: var(--alv-ink-faint) }` beating `.alv-pill-attn` on
# specificity. Nothing you can grep for. So the rest of this renders it.
#
# Colours are compared against the TOKEN, resolved in the same browser, not
# against a hex I typed here. A check that hardcodes rgb(154, 106, 8) starts
# failing the day --alv-warn is retuned, which is the opposite of what it is
# for: it should fail when this page stops agreeing with the system, not when
# the system moves.
# ---------------------------------------------------------------------------
NEW_FRAG = ("<div class='report-container'>"
            "<div class='alv-card renewal-card tenant-card'>"
            "<div class='alv-card-head'><h3 class='property-name'>12 Oak Avenue</h3>"
            "<span class='alv-pill alv-pill-attn' id='pend'>"
            "<i class='fas fa-clock' id='pend-i'></i> Renewal pending</span></div>"
            "<div class='alv-card-body tenant-details'>"
            "<div class='detail-row'><span class='detail-label'>Lease End:</span>"
            "<span class='detail-value highlight-red' id='hl'>2026-02-28</span></div>"
            "</div></div>"
            "<div class='alv-card renewal-card declined-renewal-card'>"
            "<div class='alv-card-head'><h3 class='property-name'>88 Marine Drive</h3>"
            "<span class='alv-pill alv-pill-attn' id='decl'>"
            "<i class='fas fa-times-circle'></i> Renewal declined</span></div>"
            "<div class='alv-card-body tenant-details'>"
            "<p class='card-message' id='msg'>Tenant has declined to renew.</p>"
            "</div></div>"
            "<div class='alv-card renewal-card vacant-property-card'>"
            "<div class='alv-card-head'><h3 class='property-name'>5 Kloof Street</h3>"
            "<span class='alv-pill alv-pill-neutral' id='vac'>"
            "<i class='fas fa-home'></i> Vacant</span></div>"
            "<div class='alv-card-body tenant-details'>x</div></div></div>")

OLD_FRAG = ("<div class='report-container'>"
            "<div class='renewal-card tenant-card'>"
            "<div class='card-status-bar status-bar-pending' id='pend'>"
            "<i class='fas fa-clock' id='pend-i'></i> RENEWAL PENDING</div>"
            "<h3 class='property-name'>12 Oak Avenue</h3>"
            "<div class='tenant-details'>"
            "<div class='detail-row'><span class='detail-label'>Lease End:</span>"
            "<span class='detail-value highlight-red' id='hl'>2026-02-28</span></div>"
            "</div></div>"
            "<div class='renewal-card declined-renewal-card'>"
            "<div class='card-status-bar status-bar-declined' id='decl'>"
            "<i class='fas fa-times-circle'></i> RENEWAL DECLINED</div>"
            "<h3 class='property-name'>88 Marine Drive</h3>"
            "<p class='card-message' id='msg'>Tenant has declined to renew.</p>"
            "<div class='tenant-details'>x</div></div>"
            "<div class='renewal-card vacant-property-card'>"
            "<div class='card-status-bar status-bar-vacant' id='vac'>"
            "<i class='fas fa-home'></i> VACANT - NEEDS NEW TENANT</div>"
            "<h3 class='property-name'>5 Kloof Street</h3></div></div>")

PROBE = """() => {
  const tok = v => { const d = document.createElement('span');
    d.style.color = 'var(' + v + ')'; document.body.appendChild(d);
    const c = getComputedStyle(d).color; d.remove(); return c; };
  const cs = id => getComputedStyle(document.getElementById(id));
  const box = el => el.getBoundingClientRect();
  const o = {};
  for (const k of ['pend', 'decl', 'vac']) {
    const e = document.getElementById(k);
    o[k] = e ? cs(k).color : null;
    o[k + '-bg'] = e ? cs(k).backgroundColor : null;
  }
  o['pend-i'] = document.getElementById('pend-i')
              ? cs('pend-i').color : null;
  o.msg = document.getElementById('msg') ? cs('msg').color : null;
  o.hl  = document.getElementById('hl')  ? cs('hl').color  : null;
  const card = document.querySelector('.renewal-card');
  o.shadow   = getComputedStyle(card).boxShadow;
  o.overflow = getComputedStyle(card).overflowY;
  o.cardbg   = getComputedStyle(card).backgroundColor;
  o.border   = getComputedStyle(card).borderTopWidth;
  const head = document.querySelector('.renewal-card .alv-card-head');
  if (head) {
    const p = document.getElementById('pend');
    o.gap = box(head).right - box(p).right;      // pill to the head's edge
    o.headw = box(head).width;
  }
  for (const v of ['--alv-warn', '--alv-neutral', '--alv-ink', '--alv-bad',
                   '--alv-ink-faint', '--alv-warn-soft', '--alv-neutral-soft',
                   '--alv-paper'])
    o['T' + v] = tok(v);
  return o; }"""


async def render(base_txt, page_txt, frag, strip=None):
    """One page, one fragment, one set of computed values.

    `strip` removes a declaration from the PAGE css before rendering. That is
    how the constructed controls below work: take the finished page, remove
    the one line under test, and show the defect come back. A control that
    cannot fail proves nothing, and the cheapest way to be sure this one can
    is to make the failure happen on purpose.
    """
    from playwright.async_api import async_playwright
    css = css_of(page_txt)
    if strip:
        if strip not in css:
            return {'_stripfail': strip}
        css = css.replace(strip, '')
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page(viewport={'width': 1200, 'height': 900})
        await pg.set_content(
            "<style>%s</style><style>%s</style><style>%s</style>"
            "<body style='padding:20px'>%s</body>"
            % (BOOTSTRAP, css_of(base_txt), css, frag))
        await pg.wait_for_timeout(60)
        out = await pg.evaluate(PROBE)
        await br.close()
        return out


async def main():
    head('4. the fragments match the files they claim to represent')
    # A control built from a fragment I typed is worth exactly as much as the
    # fragment's resemblance to the page. So: every class the fragments use
    # must actually appear in the file each one stands for.
    _bak = LR + '.bak_leaserenewal'
    if not os.path.exists(_bak):
        check('the backup exists to compare against', False,
              '(run apply_lease_renewal.py first)')
        return
    OLDT = read(_bak)
    for frag, txt, name in ((NEW_FRAG, LRT, 'after'), (OLD_FRAG, OLDT, 'before')):
        cls = set(re.findall(r"class='([^']+)'", frag))
        cls = {c for group in cls for c in group.split()}
        missing = sorted(c for c in cls if c not in txt)
        check('the %-6s fragment uses only classes that page has' % name,
              not missing, ', '.join(missing))

    head('5. what a reader actually sees')
    now = await render(BASE, LRT, NEW_FRAG)
    warn, neut = now['T--alv-warn'], now['T--alv-neutral']
    check('pending  wears the warn token', now['pend'] == warn,
          '%s vs %s' % (now['pend'], warn))
    check('declined wears the warn token TOO - the whole round',
          now['decl'] == warn, '%s vs %s' % (now['decl'], warn))
    check('  and they are indistinguishable, text and fill',
          now['pend'] == now['decl'] and now['pend-bg'] == now['decl-bg'],
          '%s/%s' % (now['pend-bg'], now['decl-bg']))
    check('vacant is the neutral one, and is NOT the same as those two',
          now['vac'] == neut and now['vac'] != warn, now['vac'])
    check('  fills differ too, so the difference survives a greyscale print',
          now['vac-bg'] != now['pend-bg'],
          '%s vs %s' % (now['vac-bg'], now['pend-bg']))
    check("the pill's ICON wears the pill's colour, not the head's grey",
          now['pend-i'] == warn and now['pend-i'] != now['T--alv-ink-faint'],
          '%s (head grey is %s)' % (now['pend-i'], now['T--alv-ink-faint']))
    check('the declined message is ink, no longer an error red',
          now['msg'] == now['T--alv-ink'] and now['msg'] != now['T--alv-bad'],
          now['msg'])
    check('  but an overdue date IS still red - meaning was moved, not lost',
          now['hl'] == now['T--alv-bad'], now['hl'])

    head("6. the card is base's card, not a lookalike")
    check('no page shadow survives', now['shadow'] in ('none', ''), now['shadow'])
    check('overflow is base\'s clip, not the page\'s hidden',
          now['overflow'] == 'clip', now['overflow'])
    check('  which matters: hidden makes the card a scroll container',
          now['overflow'] != 'hidden')
    check('the background comes from the paper token, not hardcoded white',
          now['cardbg'] == now['T--alv-paper'], now['cardbg'])
    check('base draws the border', now['border'] == '1px', now['border'])
    # Measured with a SHORT property name on purpose. With a realistic name
    # the title alone fills the column, so the pill ends up at the far edge
    # whether `justify-content` is there or not - and the control below duly
    # failed to fail. A control that cannot fail is worse than no control,
    # because it is read as evidence. A short title is the only case where
    # the declaration is what puts the pill there.
    short = await render(BASE, LRT, NEW_FRAG.replace('12 Oak Avenue', '1 A St'))
    check('the status sits at the far end of the head (%.0fpx from its edge)'
          % short['gap'], short['gap'] <= 20,
          'short title, head is %.0fpx wide' % short['headw'])

    head('7. the negative controls - each defect, made to happen again')
    was = await render(BASE, OLDT, OLD_FRAG)
    check('CONTROL: before this round the two DID disagree',
          was['pend-bg'] != was['decl-bg'],
          '%s vs %s' % (was['pend-bg'], was['decl-bg']))
    check('  declined was Bootstrap red', was['decl-bg'] == 'rgb(220, 53, 69)',
          was['decl-bg'])
    check('  pending was Bootstrap amber', was['pend-bg'] == 'rgb(255, 193, 7)',
          was['pend-bg'])
    check('  and the message was red as well',
          was['msg'] == 'rgb(220, 53, 69)', str(was['msg']))
    check('  the card carried its own shadow',
          was['shadow'] not in ('none', ''), str(was['shadow']))

    # Constructed controls: the finished page minus one declaration.
    icon = await render(BASE, LRT, NEW_FRAG,
                        strip='.renewal-card > .alv-card-head > .alv-pill '
                              'i.fas { color: inherit; }')
    check('CONTROL: remove the icon rule and the icon greys again',
          icon.get('pend-i') == now['T--alv-ink-faint'],
          icon.get('_stripfail') or str(icon.get('pend-i')))
    gapc = await render(BASE, LRT, NEW_FRAG.replace('12 Oak Avenue', '1 A St'),
                        strip='justify-content: space-between;')
    check('CONTROL: remove space-between and the pill slides back to the title',
          gapc.get('gap', 0) > 20,
          gapc.get('_stripfail') or '%.0fpx from the edge' % gapc.get('gap', -1))

asyncio.run(main())

# The summary sits OUT here, not at the end of main(), because main() returns
# early when the backups are missing. Inside, that early return skipped the
# exit code entirely: a suite with eight failures behind it would have
# reported success to the push script by never getting as far as sys.exit.
print('\n' + '=' * 72)
print(' %d passed, %d failed' % (_p, _f))
for x in _fails:
    print('   FAILED: %s' % x)
print('=' * 72)
sys.exit(1 if _f else 0)
