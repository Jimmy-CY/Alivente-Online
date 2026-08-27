"""test_detail_property - the Property module's detail and report screens.

    python test_detail_property.py

STATIC: three files converted, and the CSS base.html now owns deleted from
each - without taking the page-specific half with it.

BROWSER: the four things that can only be answered by rendering.

  1. STICKY INSIDE A CARD. This round exists partly to fix a bug I wrote:
     .alv-card { overflow: hidden } makes the card the scroll container, so
     a heading inside it never sticks. The control puts hidden back and
     demands the heading scroll away - if it does not, the fix proves
     nothing.

  2. A COUNT IS NOT A CATEGORY. The tag dot moved onto the tone classes, so
     a toneless count tag has no dot and a toned category tag does. Both
     halves are asserted, because only asserting the first would pass on a
     stylesheet with no dots at all.

  3. THE COLLAPSED ACTIONS CELL. Invoice + Action became one column. The
     risk in that edit is a permission conditional silently moving to the
     wrong button, so the rendered cell is counted on BOTH branches.

  4. EXPIRED IS AMBER. Not red (it is not a failure) and not grey (it is
     not merely inactive). Measured against the two it must not be.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')

R, A, D = 'property_report.html', 'property_assets.html', 'asset_detail.html'

results = []


def check(label, ok):
    results.append((label, bool(ok)))


def read(name):
    p = os.path.join(TPL, name)
    if not os.path.exists(p):
        sys.exit('! pages/templates/%s not found - run from the root' % name)
    return open(p, encoding='utf-8-sig', errors='replace').read().replace(
        '\r\n', '\n')


BASE = read('base.html')
SRC = {R: read(R), A: read(A), D: read(D)}


def strip_comments(s):
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)


def css_of(t):
    return strip_comments(
        ''.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S | re.I)))


CSS = dict((k, css_of(v)) for k, v in SRC.items())
_i = BASE.find('--alv-table-std')
BLOCK = strip_comments(BASE[_i:BASE.find('</style>', _i)]) if _i >= 0 else ''


def rules_naming(css, name):
    return len(re.findall(r'(?<![\w-])%s(?![\w-])' % re.escape(name), css))


# EXACT floors, one line each. `all(count >= 1 for ...)` over a group
# looked like coverage and was not: a control that deleted the
# `.empty-state-card` base rule left `.empty-state-card h4` and `... p`
# behind, the count stayed >= 1, and the whole group still passed. Same
# shape as the .filter-panel near-miss two rounds ago.
KEPT = {
    R: (('.report-container', 3), ('.property-card', 3), ('.section-title', 2),
        ('.detail-row', 2), ('.stats-card', 2), ('.muted', 1),
        ('.no-assets-info', 1)),
    A: (('.asset-thumb', 1), ('.summary-grid', 1), ('.view-toggle-group', 4),
        ('.empty-state-card', 4), ('.photo-upload-controls', 2),
        ('.modal-header', 1), ('.asset-name-cell', 1)),
    D: (('.photo-grid', 1), ('.photo-tile', 4), ('.warranty-grid', 2),
        ('.detail-row', 2), ('.maintenance-total', 1),
        ('.asset-header-thumb', 3),
        # .action-more-wrapper was here and had to move: the action-bar
        # round that follows this one hoists it into base.html, so pinning
        # it as page-owned made THIS suite fail the moment the NEXT round
        # ran. An expectation can outlive the decision it encoded - and it
        # can also outlive the round that owned it. test_action_standard.py
        # now asserts the page has no copy left.
        ('.maintenance-empty', 1), ('.notes-section', 2)),
}


def kept(name):
    for sel, floor in KEPT[name]:
        got = rules_naming(CSS[name], sel)
        check('  KEPT %-22s %d rules (need %d)' % (sel, got, floor),
              got >= floor)


# ============================================== base.html, the corrections
check('a card clips with clip, not hidden',
      re.search(r'\.alv-card \{[^}]*overflow:\s*clip', BLOCK) is not None)
check('  so it cannot become the scroll container',
      re.search(r'\.alv-card \{[^}]*overflow:\s*hidden', BLOCK) is None)
check('there is a fifth tag tone', '.alv-tag-plum' in BLOCK)
# Not `'.alv-tag::before' not in BLOCK` - the print block legitimately
# carries `.alv-tag::before { opacity: 1 }`, so that substring survives and
# the check would have been asserting the wrong thing. What moved is the
# DOT ITSELF, which is the rule that declares `content`.
check('  and the dot hangs off the TONES, not off every tag',
      '.alv-tag-sky::before' in BLOCK
      and re.search(r'\.alv-tag::before\s*\{[^}]*content:', BLOCK) is None)

# ================================================== property_report.html
t, c = SRC[R], CSS[R]
check('report: both tables joined the standard',
      len(re.findall(r'<table[^>]*\balv-table\b', t)) == 2)
check('  and kept their own names for the page-specific half',
      'alv-table categories-table' in t and 'alv-table assets-table' in t)
check('  no header is centred by hand any more',
      '<th class="text-center">' not in t)
check('  Count is a number', '<th class="count-col num">' in t
      and 'data-label="Count" class="count-col num"' in t)
check('report: Status is a pill on the semantic scale',
      'alv-pill-good{% else %}alv-pill-neutral' in t)
check('  Available for Rent too', t.count('alv-pill-good{% else %}'
                                          'alv-pill-neutral') == 2)
check('  the expired-warranty count is amber, not red',
      'alv-pill alv-pill-attn">{{ expired_warranties }}' in t)
check('  and it lost its inline background colour',
      'style="background-color: #dc3545' not in t)
check('  the warranty column reads as pills',
      'alv-pill alv-pill-good">Active' in t
      and 'alv-pill alv-pill-attn">Expired' in t)
check('  and the tick and cross went with the colour',
      '✓ Active' not in t and '✗ Expired' not in t)
check('  Category is a tag', 'alv-tag alv-tag-slate' in t)
for gone in ('.assets-table', '.categories-table', '.badge-success',
             '.badge-available', '.warranty-active', '.warranty-expired'):
    n = rules_naming(c, gone)
    # .categories-table survives ONLY in the mobile opt-out, which also
    # names .alv-table. Anything else would be a leftover.
    want = 0
    check('  %-20s has %d rules left (expected %d)' % (gone, n, want),
          n == want)
check('  and no page-level override fights the mobile conversion',
      '.categories-table.alv-table' not in c)
kept(R)
check('  and its print block is still there', '@media print' in c)

# ================================================== property_assets.html
t, c = SRC[A], CSS[A]
check('assets: the table joined the standard',
      len(re.findall(r'<table[^>]*\balv-table\b', t)) == 1)
check('  the summary panel is a card', 'alv-card-head' in t
      and 'alv-card-body' in t)
check('  and each group is a card with its count as an aside',
      'alv-card-aside alv-tag">{{ asset_list|length }}' in t)
check('  the table sits inside a container inside that card',
      re.search(r'<div class="table-container">\s*<table[^>]*alv-table', t)
      is not None)
check('  Warranty Expiry is no longer centred by hand',
      '<th class="text-center">Warranty Expiry</th>' not in t)
check('  Subcategory is a tag', 'alv-tag alv-tag-slate' in t)
check('  and warranty reads as pills',
      'alv-pill alv-pill-good">Active' in t
      and 'alv-pill alv-pill-attn">Expired' in t)
for gone in ('.asset-table', '.warranty-active', '.warranty-expired',
             '.category-header', '.category-section', '.summary-card'):
    check('  %-20s has no rules left' % gone, rules_naming(c, gone) == 0)
kept(A)

# ==================================================== asset_detail.html
t, c = SRC[D], CSS[D]
# Count the CARDS, not every class starting with alv-card - the first
# draft counted alv-card-head and alv-card-body too and got 20.
_cards = len(re.findall(r'class="alv-card(?: alv-card-lead)?"', t))
check('detail: four cards (%d), one of them leading' % _cards,
      _cards == 4 and 'class="alv-card alv-card-lead"' in t)
check('  no Bootstrap colour bar survives',
      not any(x in t for x in ('bg-primary', 'bg-info text-white',
                               'bg-success', 'bg-secondary')))
check('  the warranty state moved to a pill that can change',
      'alv-card-aside alv-pill alv-pill-good">Active' in t
      and 'alv-card-aside alv-pill alv-pill-attn">Expired / N/A' in t)
check('  Days Remaining stayed text - a duration is not a status',
      'color: var(--alv-good)">{{ asset.warranty_days_remaining }}' in t
      and 'alv-pill-good">{{ asset.warranty_days_remaining }}' not in t)
check('  the photo thumb has a visible border again',
      'border: 2px solid var(--alv-line)' in c
      and 'rgba(255, 255, 255, 0.4)' not in c)
check('  the maintenance table joined the standard',
      len(re.findall(r'<table[^>]*\balv-table\b', t)) == 1)
check('  Invoice and Action became ONE column',
      t.count('<th class="cell-actions">Actions</th>') == 1
      and '<th class="text-center">Invoice</th>' not in t
      and '<th class="text-center">Action</th>' not in t)
check('  and one cell holds all three buttons',
      t.count('class="desktop-action-cell cell-actions"') == 1
      and t.count('<span class="row-actions">') == 1)
check('  Cost is a number', 'class="num cost-cell"' in t)
check('  Type is a tag on five tones plus a plain fallback',
      all(('alv-tag-' + x) in t for x in
          ('sky', 'clay', 'slate', 'moss', 'plum'))
      and 'badge badge-' not in t)
# The whole risk of the collapse, and a count is not enough to see it. A
# control that replaced the actions cell's `{% if perms... %}` with
# `{% if False %}` left the file-wide count untouched (the page header and
# the mobile More menu carry their own) and rendered identically, because
# the harness resolves a conditional structurally rather than evaluating
# it. So the check looks INSIDE the collapsed cell.
_cell = re.search(r'<td[^>]*class="desktop-action-cell cell-actions"[^>]*>'
                  r'(.*?)</td>', t, re.S)
check('  the collapsed actions cell could be isolated', _cell is not None)
_in = _cell.group(1) if _cell else ''
check('  it guards edit and delete on the edit permission (%d)'
      % _in.count('{% if perms.auth.can_edit_properties %}'),
      _in.count('{% if perms.auth.can_edit_properties %}') == 1)
check('  and shows the invoice button only when there is an invoice',
      _in.count('{% if record.invoice %}') == 1)
check('  no other condition crept into that cell',
      len(re.findall(r'\{%\s*if\s', _in)) == 2)
check('  every permission conditional survived elsewhere too (%d)'
      % t.count('perms.auth.can_edit_properties'),
      t.count('perms.auth.can_edit_properties') >= 3)
check('  the edit handler kept its six arguments',
      re.search(r'openEditMaintenance\(\s*\{\{ record\.id \}\},', t) is not None
      and t.count('record.description|escapejs') == 1)
check('  and delete kept its record id',
      'confirmDeleteMaintenance({{ record.id }})' in t)
check('  the disabled twins are still rendered, not dropped',
      t.count('icon-disabled') >= 3)
for gone in ('.maintenance-table', '.detail-card', '.card-header-row'):
    check('  %-20s has no rules left' % gone, rules_naming(c, gone) == 0)
kept(D)

for name in (R, A, D):
    check('%s: no unclosed Django comment' % name,
          not any('{#' in ln and '#}' not in ln for ln in SRC[name].split('\n')))
    check('  its tags balance (%d/%d)'
          % (SRC[name].count('{%'), SRC[name].count('%}')),
          SRC[name].count('{%') == SRC[name].count('%}'))
    check('  and its CSS braces do (%d/%d)'
          % (CSS[name].count('{'), CSS[name].count('}')),
          CSS[name].count('{') == CSS[name].count('}'))

# ============================================================== IN A BROWSER
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('')
    for label, ok in results:
        print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad = sum(0 if ok else 1 for _, ok in results)
    print('')
    print('  SKIP  Chromium checks skipped - playwright not installed')
    print('')
    print('%d of %d failed' % (bad, len(results)) if bad
          else 'All %d checks passed. (browser checks skipped)' % len(results))
    sys.exit(1 if bad else 0)

BOOT = None
for cand in (os.path.join(ROOT, 'test_fixture_bootstrap413.css'),
             '/tmp/bootstrap.min.css'):
    if os.path.exists(cand):
        BOOT = open(cand, encoding='utf-8').read()
        break

if BOOT is None:
    print('')
    print('  !! test_fixture_bootstrap413.css missing - browser checks skipped')
else:
    _c = re.sub(r'<!--.*?-->', '', BASE, flags=re.S)
    STD = '\n'.join(b for b in re.findall(r'<style[^>]*>(.*?)</style>',
                                          _c, re.S | re.I)
                    if '--alv-paper' in strip_comments(b)
                    or '--alv-accent:' in strip_comments(b))
    check('the standard CSS could be lifted from base.html', bool(STD.strip()))

    def shell(body, extra=''):
        return ('<!doctype html><meta charset=utf-8><style>%s</style>'
                '<style>%s</style><style>%s</style>'
                '<body style="margin:0;padding:16px;background:#fff">%s</body>'
                % (BOOT, STD, extra, body))

    def rgb(v):
        m = re.findall(r'\d+', v or '')
        return tuple(int(x) for x in m[:3]) if len(m) >= 3 else None

    def cs(pg, sel, *props):
        got = pg.evaluate(
            """([s,p])=>{const e=document.querySelector(s); if(!e) return null;
               const c=getComputedStyle(e); const o={};
               p.forEach(k=>o[k]=c.getPropertyValue(k)); return o;}""",
            [sel, list(props)])
        if got is None:
            check('element %s exists' % sel, False)
            return dict((p, None) for p in props)
        return got

    tmp = os.path.join(ROOT, '_detail_probe.html')
    try:
        with sync_playwright() as p:
            exe = '/opt/pw-browsers/chromium'
            br = (p.chromium.launch(executable_path=exe)
                  if os.path.exists(exe) else p.chromium.launch())
            pg = br.new_page(viewport={'width': 1100, 'height': 600})

            # ---- 1. a sticky heading inside a card -----------------------
            rows = ''.join('<tr><td>Asset %d</td><td>Lounge</td></tr>' % i
                           for i in range(40))
            card = ('<div class="alv-card %s"><div class="alv-card-head">'
                    'Maintenance History</div><div class="table-container">'
                    '<table class="table alv-table"><thead><tr><th>Name</th>'
                    '<th>Room</th></tr></thead><tbody>%s</tbody></table>'
                    '</div></div>')
            # Side by side, NOT stacked. Stacked, the control's heading
            # is still below the fold after a 600px scroll and reads as
            # "never sticks" for the wrong reason - the same mistake this
            # project made once before on the .table-container control.
            open(tmp, 'w', encoding='utf-8').write(shell(
                '<div style="display:flex;gap:16px;align-items:flex-start">'
                '<div style="flex:1">' + card % ('', rows) + '</div>'
                '<div style="flex:1">' + card % ('ctl', rows) + '</div>'
                '</div>',
                '.alv-card.ctl { overflow: hidden; }'))
            pg.goto('file://' + tmp)
            pg.wait_for_timeout(200)
            pg.evaluate('window.scrollTo(0, 600)')
            pg.wait_for_timeout(250)
            tops = pg.evaluate(
                """()=>['.alv-card:not(.ctl)','.alv-card.ctl'].map(s=>
                   Math.round(document.querySelector(s+' thead th')
                   .getBoundingClientRect().top))""")
            check('a heading INSIDE a card still sticks (top=%d)' % tops[0],
                  -1 <= tops[0] <= 2)
            check('  CONTROL: with overflow hidden it scrolls away (top=%d)'
                  % tops[1], tops[1] < -100)
            check('  so the clip change is what makes it work',
                  tops[0] > tops[1] + 100)

            # ---- 2. a count is not a category ---------------------------
            open(tmp, 'w', encoding='utf-8').write(shell(
                '<span class="alv-tag" id="count">3</span>'
                '<span class="alv-tag alv-tag-clay" id="cat">Repair</span>'
                '<span class="alv-tag alv-tag-sky" id="c2">Scheduled</span>'
                '<span class="alv-tag alv-tag-plum" id="c3">Service</span>'
                '<span class="alv-tag alv-tag-moss" id="c4">Cleaning</span>'
                '<span class="alv-tag alv-tag-slate" id="c5">Inspection</span>'
                '<span class="alv-pill alv-pill-good" id="good">Active</span>'
                '<span class="alv-pill alv-pill-attn" id="attn">Expired</span>'
                '<span class="alv-pill alv-pill-bad" id="bad">Failed</span>'
                '<span class="alv-pill alv-pill-neutral" id="neu">Inactive</span>'))
            pg.goto('file://' + tmp)
            pg.wait_for_timeout(150)
            dot = lambda i: pg.evaluate(   # noqa: E731
                "()=>getComputedStyle(document.getElementById('%s'),"
                "'::before').content" % i)
            check('a count tag has no dot (%s)' % dot('count'),
                  dot('count') in ('none', 'normal', ''))
            check('  CONTROL: a category tag still has one (%s)' % dot('cat'),
                  dot('cat') not in ('none', 'normal', ''))
            tones = [rgb(cs(pg, '#' + i, 'background-color')['background-color'])
                     for i in ('cat', 'c2', 'c3', 'c4', 'c5')]
            check('  the five tones are five different colours',
                  len(set(tones)) == 5)

            # ---- 3. amber, and not the two it must not be ---------------
            attn = rgb(cs(pg, '#attn', 'background-color')['background-color'])
            bad = rgb(cs(pg, '#bad', 'background-color')['background-color'])
            neu = rgb(cs(pg, '#neu', 'background-color')['background-color'])
            good = rgb(cs(pg, '#good', 'background-color')['background-color'])
            check('Expired is amber %s' % (attn,),
                  attn is not None and attn[0] > attn[2] + 15)
            check('  and NOT the danger tint %s' % (bad,), attn != bad)
            check('  and NOT the inactive grey %s' % (neu,), attn != neu)
            check('  Active is still green %s' % (good,),
                  good is not None and good[1] > good[0] + 5)

            # ---- 4. the collapsed actions cell --------------------------
            m = re.search(r'<table[^>]*maintenance-table.*?</table>',
                          SRC[D], re.S)
            check('the maintenance table markup could be located',
                  m is not None)
            if m:
                def resolve(frag, branch):
                    prev = None
                    while prev != frag:
                        prev = frag
                        frag = re.sub(
                            r'\{%\s*if[^%]*%\}((?:(?!\{%\s*(?:if|endif)).)*?)'
                            r'\{%\s*else\s*%\}((?:(?!\{%\s*(?:if|endif)).)*?)'
                            r'\{%\s*endif\s*%\}',
                            lambda x: x.group(1 if branch == 0 else 2),
                            frag, flags=re.S)
                        frag = re.sub(
                            r'\{%\s*if[^%]*%\}((?:(?!\{%\s*(?:if|endif)).)*?)'
                            r'\{%\s*endif\s*%\}', r'\1', frag, flags=re.S)
                    return frag

                f = m.group(0)
                body = re.search(r'<tbody>(.*?)</tbody>', f, re.S).group(1)
                body = re.sub(r'\{%\s*(for|endfor)[^%]*%\}', '', body)
                # One row on each branch: permitted, and not.
                two = ''.join('<tr class="b%d">%s</tr>' % (
                    b, re.sub(r'</?tr[^>]*>', '',
                              re.sub(r'\{[{%][^}%]*[%}]\}', 'x',
                                     resolve(body, b))))
                    for b in (0, 1))
                f = f[:f.find('<tbody>')] + '<tbody>' + two + '</tbody></table>'
                f = re.sub(r'\{[{%][^}%]*[%}]\}', 'x', f)
                open(tmp, 'w', encoding='utf-8').write(shell(
                    '<div class="table-container">' + f + '</div>'))
                pg.goto('file://' + tmp)
                pg.wait_for_timeout(200)
                n0 = pg.evaluate("()=>document.querySelectorAll("
                                 "'tr.b0 .row-actions > *').length")
                n1 = pg.evaluate("()=>document.querySelectorAll("
                                 "'tr.b1 .row-actions > *').length")
                cells = pg.evaluate("()=>document.querySelectorAll("
                                    "'tr.b0 td').length")
                check('permitted: three buttons in ONE cell (%d buttons, '
                      '%d cells)' % (n0, cells), n0 == 3)
                check('  and not permitted: still three, all disabled (%d)'
                      % n1, n1 == 3)
                check('  the disabled ones really are disabled',
                      pg.evaluate("()=>document.querySelectorAll("
                                  "'tr.b1 .row-actions .icon-disabled')"
                                  ".length") >= 2)
                off = pg.evaluate(
                    """()=>{const th=document.querySelector('th.cell-actions');
                       const sp=document.querySelector('tr.b0 .row-actions');
                       if(!th||!sp) return null;
                       const r=document.createRange(); r.selectNodeContents(th);
                       const lr=r.getBoundingClientRect(),
                             sr=sp.getBoundingClientRect();
                       return (lr.left+lr.width/2)-(sr.left+sr.width/2);}""")
                check('  and the Actions heading sits over them (%s)'
                      % ('%+.1fpx' % off if off is not None else 'not measured'),
                      off is not None and abs(off) <= 1.5)

            # ---- 5. the count table stays a table on a phone ------------
            cat = re.search(r'<table[^>]*categories-table.*?</table>',
                            SRC[R], re.S)
            check('the count table markup could be located', cat is not None)
            if cat:
                f = re.sub(r'\{%\s*(for|endfor)[^%]*%\}', '', cat.group(0))
                f = re.sub(r'\{[{%][^}%]*[%}]\}', 'x', f)
                open(tmp, 'w', encoding='utf-8').write(
                    shell(f, CSS[R]))
                pg.set_viewport_size({'width': 375, 'height': 700})
                pg.goto('file://' + tmp)
                pg.wait_for_timeout(200)
                d = pg.evaluate(
                    """()=>{const t=document.querySelector('table');
                       return {th:getComputedStyle(
                                 t.querySelector('thead')).display,
                               td:getComputedStyle(
                                 t.querySelector('tbody td')).display,
                               w:Math.round(t.getBoundingClientRect().width)};}""")
                # It converts to cards like every other table. The
                # first draft made it opt out; base.html carries
                # `.alv-table tbody td:first-child` at specificity (0,2,2)
                # and sets padding/border/text-align with !important, so
                # the opt-out took eight lines of counter-override per
                # page. Three cards read fine.
                check('mobile: the count table converts like the rest (%s)'
                      % d['th'], d['th'] == 'none')
                check('  its cells become blocks (%s)' % d['td'],
                      d['td'] in ('block', 'flex'))
                check('  and it fits the viewport (%dpx)' % d['w'],
                      d['w'] <= 375)
            br.close()
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

print('')
bad = 0
for label, ok in results:
    print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad += 0 if ok else 1
print('')
print('%d of %d failed' % (bad, len(results)) if bad
      else 'All %d checks passed.' % len(results))
sys.exit(1 if bad else 0)
