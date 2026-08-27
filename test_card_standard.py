"""test_card_standard - cards are quiet, tags mean nothing, print survives.

    python test_card_standard.py

STATIC: the components exist, and the ones already shipped were not
collateral damage.

BROWSER: the interesting half. Four things get measured rather than asserted,
because all four have already been got wrong once on this project by reading
CSS and believing it:

  1. THE ACTIONS HEADING. The bug being fixed was invisible to every static
     check - the rule said "center" and it WAS centering, just on the column
     rather than on the buttons. So this measures the two centre lines at
     2, 3, 4 and 5 buttons across four column widths, and demands they meet.
     A control table with the old rule proves the measurement can see the
     difference.

  2. THE CARD HEADER IS ACTUALLY QUIET. A control card carrying Bootstrap's
     bg-primary is rendered beside it. If the control does not come back
     loud blue, nothing about the calm one is evidence.

  3. THE TAG IS OFF THE SEMANTIC SCALE. Not "does .alv-tag exist" but "is it
     a different colour from every .alv-pill variant" - the whole point of
     the component is that a Repair is not a warning.

  4. PRINT. Rendered in print media, which is the only way to find out
     whether a rule inside @media print does anything at all.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')

if not os.path.exists(BASE):
    sys.exit('! pages/templates/base.html not found - run from the root')

results = []


def check(label, ok):
    results.append((label, bool(ok)))


SRC = open(BASE, encoding='utf-8-sig', errors='replace').read().replace(
    '\r\n', '\n')


def strip_comments(s):
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)


_i = SRC.find('--alv-table-std')
BLOCK = strip_comments(SRC[_i:SRC.find('</style>', _i)]) if _i >= 0 else ''

# ==================================================================== STATIC
check('the standard block is still there and singular',
      SRC.count('--alv-table-std') == 1)
check('the card component exists', '--alv-card-std' in SRC)
check('  with a head, a body and a lead variant',
      all(x in BLOCK for x in ('.alv-card-head', '.alv-card-body',
                               '.alv-card-lead')))
check('  and its header uses the surface token, not a colour',
      re.search(r'\.alv-card > \.alv-card-head\s*\{[^}]*background:\s*'
                r'var\(--alv-surface\)', BLOCK, re.S) is not None)
check('the tag component exists, in four tones',
      all(('.alv-tag-' + t) in BLOCK for t in ('sky', 'moss', 'clay', 'slate')))
check('  and no tone is an alias of a semantic token',
      not re.search(r'\.alv-tag-\w+\s*\{[^}]*var\(--alv-(good|warn|bad)',
                    BLOCK, re.S))
check('the print block exists', '--alv-print-std' in SRC and
      '@media print' in BLOCK)
check('  and it turns sticky headings off for paper',
      re.search(r'@media print.*?position:\s*static', BLOCK, re.S) is not None)
check('  and forces backgrounds to print',
      BLOCK.count('print-color-adjust: exact') >= 3)

# The fix. Exactly one rule may own cell-actions alignment, and it must
# cover both. Two rules that disagree is the bug.
check('one rule aligns the Actions column, heading and cells together',
      re.search(r'\.alv-table \.cell-actions,\s*\.alv-table th\.cell-actions'
                r'\s*\{[^}]*text-align:\s*center', BLOCK, re.S) is not None)
check('  and no stray rule right-aligns them again',
      not re.search(r'\.cell-actions\s*\{[^}]*text-align:\s*right',
                    BLOCK, re.S))

# Collateral damage. A patcher that appended its block over the top of the
# existing one would pass every check above.
for name, floor in (('.alv-pill', 2), ('.icon-action-btn', 1),
                    ('.row-actions', 1), ('.mobile-action-bar', 2),
                    ('.alv-empty', 1), ('.table-container', 1)):
    n = len(re.findall(r'(?<![\w-])%s(?![\w-])' % re.escape(name), BLOCK))
    check('%s survived (%d rules, need %d)' % (name, n, floor), n >= floor)

# Counted separately: the boundary above deliberately does NOT match
# .alv-pill-good inside .alv-pill, so a bare count of 2 is correct and the
# five variants need their own floor.
_variants = len(set(re.findall(r'\.alv-pill-(\w+)', BLOCK)))
check('the five pill variants survived (%d)' % _variants, _variants >= 5)

check('braces balance in the standard block',
      BLOCK.count('{') == BLOCK.count('}'))
check('no unclosed Django comment anywhere in base.html',
      not any('{#' in ln and '#}' not in ln for ln in SRC.split('\n')))

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
    _c = re.sub(r'<!--.*?-->', '', SRC, flags=re.S)
    _blocks = re.findall(r'<style[^>]*>(.*?)</style>', _c, re.S | re.I)
    CSS = '\n'.join(b for b in _blocks if '--alv-paper' in strip_comments(b))
    check('the standard CSS could be lifted from base.html', bool(CSS.strip()))

    def actions_page(n, w):
        """One table under the shipped rule, one under the OLD rule. The
        second is the control: if it does not come back misaligned, the
        measurement is not measuring anything."""
        btns = ''.join('<a class="icon-action-btn icon-edit" style="width:34px;'
                       'height:34px;display:inline-flex">E</a>' for _ in range(n))
        row = ('<tr><td>Apolloneon</td><td>Cyprus</td>'
               '<td class="desktop-action-cell cell-actions">'
               '<span class="row-actions">%s</span></td></tr>' % btns)
        tbl = ('<table class="table alv-table %%s" style="table-layout:fixed;'
               'width:1000px"><colgroup><col style="width:%d%%%%">'
               '<col style="width:%d%%%%"><col style="width:%d%%%%"></colgroup>'
               '<thead><tr><th>Property</th><th>Country</th>'
               '<th class="cell-actions">Actions</th></tr></thead>'
               '<tbody>%s</tbody></table>' % (100 - w - 20, 20, w, row))
        old = ('.ctl .cell-actions{text-align:right!important;}'
               '.ctl th.cell-actions{text-align:center!important;}')
        return ('<!doctype html><meta charset=utf-8><style>%s</style>'
                '<style>%s</style><style>%s</style><body style="margin:0">'
                '<div class="table-container" id="new">%s</div>'
                '<div class="table-container" id="ctl">%s</div></body>'
                % (BOOT, CSS, old, tbl % '', tbl % 'ctl'))

    CARD = """
    <div class="alv-card" id="card">
      <div class="alv-card-head"><span class="alv-card-title" id="ct">Warranty</span>
        <span class="alv-card-aside alv-pill alv-pill-attn" id="pillattn">Expired</span></div>
      <div class="alv-card-body">body</div>
    </div>
    <div class="alv-card alv-card-lead" id="lead">
      <div class="alv-card-head"><span class="alv-card-title" id="lt">Lounge Airconditioner</span></div>
      <div class="alv-card-body">body</div>
    </div>
    <div class="card" id="ctlcard">
      <div class="card-header bg-primary text-white" id="ctlhead">Control</div>
    </div>
    <p><span class="alv-tag alv-tag-clay" id="tag">Repair</span>
       <span class="alv-tag" id="tagplain">Plain</span>
       <span class="alv-pill alv-pill-good" id="pillgood">Active</span>
       <span class="alv-pill alv-pill-bad" id="pillbad">Failed</span></p>
    <div class="table-container"><table class="table alv-table" id="t">
      <thead><tr><th id="th">Date</th></tr></thead>
      <tbody><tr><td>2026-03-16</td></tr></tbody></table></div>
    """

    def cs(pg, sel, *props):
        """Never None. A missing element is a named failure, not a
        TypeError three lines later."""
        got = pg.evaluate(
            """([s,p])=>{const e=document.querySelector(s); if(!e) return null;
               const c=getComputedStyle(e); const o={};
               p.forEach(k=>o[k]=c.getPropertyValue(k)); return o;}""",
            [sel, list(props)])
        if got is None:
            check('element %s exists' % sel, False)
            return dict((p, None) for p in props)
        return got

    tmp_a = os.path.join(ROOT, '_card_actions.html')
    tmp_c = os.path.join(ROOT, '_card_probe.html')
    try:
        with sync_playwright() as p:
            exe = '/opt/pw-browsers/chromium'
            br = (p.chromium.launch(executable_path=exe)
                  if os.path.exists(exe) else p.chromium.launch())
            pg = br.new_page(viewport={'width': 1100, 'height': 900})

            # ---------------------------------------- 1. the actions heading
            # A column narrower than its own buttons is a separate fault and
            # must not be laundered through the alignment check. The first
            # run of this suite found one: four 34px buttons need ~154px, and
            # a 16% column of a 1000px table gives 136px of content box. The
            # cluster cannot wrap, so it overflows right and the heading is
            # 9px off - through no fault of the rule.
            worst_new = 0.0
            worst_ctl = 0.0
            fitted = 0
            overflowed = []
            for n, w in ((2, 12), (3, 16), (3, 20), (4, 16), (4, 20), (5, 24)):
                open(tmp_a, 'w', encoding='utf-8').write(actions_page(n, w))
                pg.goto('file://' + tmp_a)
                pg.wait_for_timeout(120)
                d = pg.evaluate(
                    """()=>{const f=id=>{const b=document.getElementById(id);
                       const th=b.querySelector('th.cell-actions');
                       const td=b.querySelector('td.cell-actions');
                       const sp=b.querySelector('tbody .row-actions');
                       const r=document.createRange(); r.selectNodeContents(th);
                       const lr=r.getBoundingClientRect(), sr=sp.getBoundingClientRect();
                       const c=getComputedStyle(td);
                       const inner=td.getBoundingClientRect().width
                                   -parseFloat(c.paddingLeft)-parseFloat(c.paddingRight);
                       return {off:(lr.left+lr.width/2)-(sr.left+sr.width/2),
                               fits: sr.width <= inner + 0.5};};
                       return {a:f('new'), b:f('ctl')};}""")
                if d['a']['fits']:
                    fitted += 1
                    worst_new = max(worst_new, abs(d['a']['off']))
                else:
                    overflowed.append('%d buttons in a %d%% column' % (n, w))
                worst_ctl = max(worst_ctl, abs(d['b']['off']))
            check('the Actions heading sits over its buttons in all %d cases '
                  'where the column fits them (worst %.1fpx)'
                  % (fitted, worst_new), fitted >= 4 and worst_new <= 1.0)
            check('  CONTROL: the old rule really was off (worst %.1fpx) - so '
                  'the measurement can see it' % worst_ctl, worst_ctl >= 8.0)
            check('  CONTROL: a column too narrow for its buttons is detected, '
                  'not averaged away (%s)'
                  % ('; '.join(overflowed) or 'none detected'),
                  len(overflowed) >= 1)

            # ------------------------------------------------- 2. the cards
            open(tmp_c, 'w', encoding='utf-8').write(
                '<!doctype html><meta charset=utf-8><style>%s</style>'
                '<style>%s</style><body style="margin:0;padding:16px">%s</body>'
                % (BOOT, CSS, CARD))
            pg.goto('file://' + tmp_c)
            pg.wait_for_timeout(200)

            head = cs(pg, '#card .alv-card-head', 'background-color', 'color',
                      'font-size')
            ctl = cs(pg, '#ctlhead', 'background-color', 'color')

            def rgb(v):
                m = re.findall(r'\d+', v or '')
                return tuple(int(x) for x in m[:3]) if len(m) >= 3 else None

            hb, cb = rgb(head['background-color']), rgb(ctl['background-color'])
            check('the card header is a near-neutral surface %s'
                  % (head['background-color'],),
                  hb is not None and max(hb) - min(hb) <= 12 and min(hb) >= 230)
            check('  CONTROL: Bootstrap bg-primary is still loud %s - so a '
                  'colour would have been seen' % (ctl['background-color'],),
                  cb is not None and max(cb) - min(cb) >= 60)
            check('  and its text is ink-strong, not white',
                  rgb(head['color']) not in (None, (255, 255, 255)))
            check('  at the table-heading size (%s)' % head['font-size'],
                  head['font-size'] == '13.5px')

            lead = cs(pg, '#lead .alv-card-head', 'font-size',
                      'background-color')
            check('the lead card is bigger (%s vs %s)'
                  % (lead['font-size'], head['font-size']),
                  float((lead['font-size'] or '0px')[:-2])
                  > float((head['font-size'] or '0px')[:-2]) + 2)
            check('  but no louder - same surface as the quiet ones',
                  lead['background-color'] == head['background-color'])

            # -------------------------------------------------- 3. the tags
            tag = cs(pg, '#tag', 'background-color', 'color')
            plain = cs(pg, '#tagplain', 'background-color')
            # Every pill class this probe names must EXIST. The first run
            # of this suite asked for .alv-pill-warn, which does not - the
            # amber variant is .alv-pill-attn - so the element rendered
            # transparent and the comparison below compared nothing.
            _defined = set(re.findall(r'\.alv-pill-(\w+)', BLOCK))
            _used = ('good', 'attn', 'bad')
            check('the pill classes this test names all exist (%s)'
                  % ', '.join(sorted(_defined)),
                  all(u in _defined for u in _used))
            pills = dict((k, cs(pg, '#' + k, 'background-color')
                          ['background-color'])
                         for k in ('pillgood', 'pillattn', 'pillbad'))
            check('  and none of them rendered transparent',
                  not any(v in ('rgba(0, 0, 0, 0)', 'transparent', None)
                          for v in pills.values()))
            check('a tag is not any semantic pill colour (%s)'
                  % tag['background-color'],
                  tag['background-color'] not in pills.values())
            check('  CONTROL: the pills are three different colours from each '
                  'other', len(set(pills.values())) == 3)
            check('  a toneless tag is neutral, not transparent',
                  plain['background-color'] not in
                  (None, 'rgba(0, 0, 0, 0)', 'transparent'))
            check('  and a tag carries its dot',
                  pg.evaluate("""()=>getComputedStyle(
                     document.getElementById('tag'),'::before').width"""
                              ) not in ('auto', '0px', ''))

            # ------------------------------------------------- 4. on paper
            screen_pill = cs(pg, '#pillgood', 'background-color',
                             'border-top-width')
            screen_th = cs(pg, '#th', 'position')
            pg.emulate_media(media='print')
            pg.wait_for_timeout(200)
            print_pill = cs(pg, '#pillgood', 'background-color',
                            'border-top-width', 'color')
            print_th = cs(pg, '#th', 'position', 'border-bottom-color')
            print_head = cs(pg, '#card .alv-card-head', 'border-bottom-color')

            check('on paper a pill loses its tint (%s -> %s)'
                  % (screen_pill['background-color'],
                     print_pill['background-color']),
                  print_pill['background-color'] in
                  ('rgba(0, 0, 0, 0)', 'transparent'))
            check('  and gains an outline instead (%s)'
                  % print_pill['border-top-width'],
                  print_pill['border-top-width'] not in (None, '0px'))
            check('  CONTROL: on screen it was tinted, not outlined',
                  screen_pill['background-color'] not in
                  ('rgba(0, 0, 0, 0)', 'transparent'))
            check('a sticky heading stops sticking on paper (%s -> %s)'
                  % (screen_th['position'], print_th['position']),
                  screen_th['position'] == 'sticky'
                  and print_th['position'] == 'static')
            th_c = rgb(print_th['border-bottom-color'])
            check('  and its rule is dark enough to print (%s)'
                  % print_th['border-bottom-color'],
                  th_c is not None and max(th_c) <= 140)
            hd_c = rgb(print_head['border-bottom-color'])
            check('a card edge is dark enough to print (%s)'
                  % print_head['border-bottom-color'],
                  hd_c is not None and max(hd_c) <= 175)
            br.close()
    finally:
        for f in (tmp_a, tmp_c):
            if os.path.exists(f):
                os.remove(f)

print('')
bad = 0
for label, ok in results:
    print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad += 0 if ok else 1
print('')
print('%d of %d failed' % (bad, len(results)) if bad
      else 'All %d checks passed.' % len(results))
sys.exit(1 if bad else 0)
