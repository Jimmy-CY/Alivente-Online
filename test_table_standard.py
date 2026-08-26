"""test_table_standard - does the hoisted vocabulary actually reach the page?

    python test_table_standard.py

Static checks confirm the block is in base.html and in the right place. But
CSS that parses is not CSS that applies, so the interesting half of this file
renders the real Bootstrap 4.1.3 plus the CSS lifted verbatim out of base.html
in headless Chromium and reads the computed styles back.

TWO LESSONS ARE BAKED IN HERE
-----------------------------
1. THE CONTROL TABLE. Every visual assertion is made twice: once on a table
   carrying .alv-table, and once on an identical table without it. If the
   control does NOT show zebra stripes and vertical grid lines, the test
   cannot tell the two apart and its passes mean nothing. So the control is
   asserted to be UGLY - that is what makes the real assertions load-bearing.

2. COMMENTS ARE NOT INERT. The first draft of the block explained itself with
   a sentence containing a literal style tag. Browsers ignore it; every regex
   that finds style blocks does not. This file's own CSS extraction silently
   pulled the wrong block and reported every colour as unset. So the extractor
   strips HTML comments first, and a static check refuses a comment that
   contains a style tag at all.

Playwright missing is a SKIP, not a failure - a dev machine without a browser
should not block a push. A browser check that runs and fails still fails.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
MARKER = '--alv-table-std'

if not os.path.exists(BASE):
    sys.exit('! pages/templates/base.html not found - run from the project root')

results = []


def check(label, ok):
    results.append((label, bool(ok)))


SRC = open(BASE, encoding='utf-8-sig').read().replace('\r\n', '\n')

# ==================================================== 1. IS IT THERE, AND WHERE
check('base.html carries the table standard', MARKER in SRC)

i_boot = SRC.find('bootstrap@4.1.3/dist/css/bootstrap.min.css')
i_acc = SRC.find('--alv-accent:')
i_std = SRC.find(MARKER)
i_head = SRC.find('</head>')

check('  Bootstrap 4.1.3 is still linked', i_boot >= 0)
check('  the accent block from eca9db8 survives', i_acc >= 0)
check('  order: bootstrap < accent < table-standard',
      0 <= i_boot < i_acc < i_std)
check('  and the whole lot is inside <head>', 0 <= i_std < i_head)

# The bug that cost this file an hour: a style tag inside an HTML comment.
_comment_zone = SRC[i_std:SRC.find('-->', i_std)] if i_std >= 0 else ''
check('  no literal style tag hidden in the explanatory comment',
      '<style' not in _comment_zone and '</style' not in _comment_zone)

# ------------------------------------------------- extract, comments stripped
_clean = re.sub(r'<!--.*?-->', '', SRC, flags=re.S)
_blocks = re.findall(r'<style[^>]*>(.*?)</style>', _clean, re.S | re.I)


def _decls_only(css):
    """CSS with its /* comments */ removed.

    Twice now, English prose inside a comment has impersonated markup: a
    sentence containing a style tag, and a sentence containing a token name
    followed by a colon. Both fooled a matcher looking at raw text. Anything
    deciding "which block is this?" must look at declarations, not at prose.
    """
    return re.sub(r'/\*.*?\*/', '', css, flags=re.S)


_accent = [b for b in _blocks if '--alv-accent:' in _decls_only(b)]
_std = [b for b in _blocks if '--alv-paper:' in _decls_only(b)]

check('  the accent block extracts cleanly', len(_accent) == 1)
check('  the standard block extracts cleanly', len(_std) == 1)

BLOCK = _std[0] if _std else ''
check('  its braces balance (%d pairs)' % BLOCK.count('{'),
      BLOCK.count('{') == BLOCK.count('}') and BLOCK.count('{') > 40)
check('  it contains no Django tag',
      not any(t in BLOCK for t in ('{%', '{{', '{#')))

# ============================================================ 2. THE VOCABULARY
# These names already existed in the templates. The whole point of the round is
# that they keep working, so a page can delete its copy and change nothing else.
for cls in ('.icon-action-btn', '.icon-edit', '.icon-view', '.icon-delete',
            '.icon-disabled', '.icon-approve', '.icon-unapprove', '.icon-send',
            '.desktop-action-cell', '.mobile-action-bar', '.mobile-action-btn',
            '.mobile-action-icon', '.mobile-action-label',
            '.mobile-action-disabled', '.icon-color-edit', '.icon-color-view',
            '.icon-color-delete', '.table-container', '.status-btn'):
    check('  %s is defined' % cls, cls in BLOCK)

check('  nothing was renamed: the old names are the new names',
      all(c in BLOCK for c in ('.icon-action-btn', '.mobile-action-bar')))

for cls in ('.alv-table', '.alv-pill', '.alv-pill-neutral', '.alv-empty'):
    check('  %s is defined (new)' % cls, cls in BLOCK)

for tok in ('--alv-paper', '--alv-ink', '--alv-line', '--alv-good', '--alv-bad',
            '--alv-warn', '--alv-neutral', '--alv-edit', '--alv-font-ui'):
    check('  token %s defined' % tok, tok + ':' in BLOCK)

check('  typography is routed through one token, not hardcoded',
      '--alv-font-ui:' in BLOCK and 'var(--alv-font-ui)' in BLOCK)
check('    and it still inherits - no webfont was smuggled in',
      re.search(r'--alv-font-ui:\s*inherit', BLOCK) is not None
      and 'fonts.googleapis' not in SRC)

check('  semantic colours are NOT aliases of the accent',
      '--alv-good:' in BLOCK and 'var(--alv-accent)' not in
      (re.search(r'--alv-good:\s*([^;]+);', BLOCK).group(1)
       if re.search(r'--alv-good:\s*([^;]+);', BLOCK) else ''))

check('  the mobile card conversion breaks at 768px',
      re.search(r'@media[^{]*max-width:\s*768px', BLOCK) is not None)
check('  :first-child is the card title (replacing 8 per-page rules)',
      're.' not in BLOCK and 'td:first-child' in BLOCK)

# ================================================================ 3. IN A BROWSER
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('')
    for label, ok in results:
        print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad = sum(0 if ok else 1 for _, ok in results)
    print('')
    print('  SKIP  Chromium checks skipped - playwright not installed')
    print('        (pip install playwright, then playwright install chromium)')
    print('')
    print('%d of %d failed' % (bad, len(results)) if bad
          else 'All %d checks passed. (browser checks skipped)' % len(results))
    sys.exit(1 if bad else 0)

# Bootstrap has to be the real thing - the whole question is who wins.
BOOT = None
for cand in ('/tmp/bootstrap.min.css',
             os.path.join(ROOT, 'node_modules', 'bootstrap', 'dist', 'css',
                          'bootstrap.min.css')):
    if os.path.exists(cand):
        BOOT = open(cand, encoding='utf-8').read()
        break
if BOOT is None:
    BOOT = ''
    check('  (Bootstrap CSS not found locally - cascade checks are weaker)',
          True)

CSS = (_accent[0] if _accent else '') + '\n' + BLOCK

ROW = ('<tr>'
       '<td data-label="Name" style="text-align:left">Andreas P.</td>'
       '<td data-label="Phone">99 123 456</td>'
       '<td data-label="Company">Kyriakou Ltd</td>'
       '<td data-label="Edit" class="desktop-action-cell">'
       '<a href="#" class="icon-action-btn icon-edit">E</a></td>'
       '<td data-label="Report" class="desktop-action-cell">'
       '<a href="#" class="icon-action-btn icon-view">V</a></td>'
       '<td data-label="Del" class="desktop-action-cell">'
       '<span class="icon-action-btn icon-disabled">D</span></td>'
       '<td class="mobile-action-bar">'
       '<a href="#" class="mobile-action-btn">'
       '<i class="mobile-action-icon icon-color-edit">E</i>'
       '<span class="mobile-action-label">Edit</span></a>'
       '<a href="#" class="mobile-action-btn">'
       '<i class="mobile-action-icon icon-color-view">V</i>'
       '<span class="mobile-action-label">Report</span></a>'
       '<span class="mobile-action-btn mobile-action-disabled">'
       '<i class="mobile-action-icon">D</i>'
       '<span class="mobile-action-label">Del</span></span></td></tr>')

HEAD = ('<thead><tr><th>Name</th><th>Phone</th><th>Company</th>'
        '<th>Edit</th><th>Report</th><th>Del</th></tr></thead>')

BASE_CLS = 'table table-bordered table-striped text-center suppliers-table'


def table(extra, tid):
    return ('<div class="table-container"><table class="%s%s" id="%s">%s'
            '<tbody>%s</tbody></table></div>'
            % (BASE_CLS, extra, tid, HEAD, ROW * 3))


PAGE = ('<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<style>%s</style><style>%s</style></head><body>'
        '%s%s'
        '<p><span class="alv-pill alv-pill-good" id="pgood">Paid</span>'
        '<span class="alv-pill alv-pill-neutral" id="pneutral">Inactive</span>'
        '<button class="status-btn" id="sbtn">Manage</button>'
        '<a class="btn btn-info" href="#" id="binfo">info</a></p>'
        '<div class="alv-empty" id="empty"><div class="alv-empty-title">'
        'No suppliers found</div></div>'
        '</body></html>'
        % (BOOT, CSS, table(' alv-table', 'std'), table('', 'ctl')))

tmp = os.path.join(ROOT, '_table_probe.html')
open(tmp, 'w', encoding='utf-8').write(PAGE)

try:
    with sync_playwright() as p:
        exe = '/opt/pw-browsers/chromium'
        browser = (p.chromium.launch(executable_path=exe)
                   if os.path.exists(exe) else p.chromium.launch())

        def styles(pg, sel, props):
            return pg.evaluate(
                """([s,ps])=>{const e=document.querySelector(s);
                   if(!e)return null;const c=getComputedStyle(e);
                   const o={};for(const p of ps)o[p]=c.getPropertyValue(p);
                   return o;}""", [sel, props])

        # ------------------------------------------------------- desktop
        pg = browser.new_page(viewport={'width': 1440, 'height': 900})
        pg.goto('file://' + tmp)

        tok = pg.evaluate(
            """()=>{const r=getComputedStyle(document.documentElement);
               const o={};for(const k of ['--alv-accent','--alv-paper',
               '--alv-edit','--alv-good','--alv-line'])
               o[k]=r.getPropertyValue(k).trim();return o;}""")
        check('tokens resolve in the browser (not just present in the file)',
              tok['--alv-paper'] == '#ffffff' and tok['--alv-edit'] == '#2563eb')
        check('  the accent from the previous round is still reachable',
              tok['--alv-accent'] == '#0e7c8b')

        # --- THE CONTROL MUST BE UGLY, or these assertions prove nothing.
        c_odd = styles(pg, '#ctl tbody tr:nth-child(1)', ['background-color'])
        c_td = styles(pg, '#ctl tbody td:nth-child(2)',
                      ['border-left-width', 'text-align'])
        check('CONTROL (no .alv-table) still has zebra striping',
              c_odd['background-color'] not in ('rgba(0, 0, 0, 0)',
                                                'transparent'))
        check('CONTROL still has vertical grid lines',
              c_td['border-left-width'] != '0px')

        s_odd = styles(pg, '#std tbody tr:nth-child(1)', ['background-color'])
        s_even = styles(pg, '#std tbody tr:nth-child(2)', ['background-color'])
        s_td = styles(pg, '#std tbody td:nth-child(2)',
                      ['border-left-width', 'border-right-width',
                       'border-top-width'])
        check('zebra striping is gone - decision 2',
              s_odd['background-color'] in ('rgba(0, 0, 0, 0)', 'transparent')
              and s_even['background-color'] in ('rgba(0, 0, 0, 0)',
                                                 'transparent'))
        check('vertical grid lines are gone',
              s_td['border-left-width'] == '0px'
              and s_td['border-right-width'] == '0px')
        check('  but the horizontal rule survives (rows stay trackable)',
              s_td['border-top-width'] == '1px')

        pg.hover('#std tbody tr:nth-child(1) td:nth-child(2)')
        hov = styles(pg, '#std tbody tr:nth-child(1)', ['background-color'])
        check('hovering a row tints it with the accent',
              hov['background-color'] == 'rgb(228, 243, 245)')

        e = styles(pg, '#std .icon-edit', ['color', 'width', 'height'])
        v = styles(pg, '#std .icon-view', ['color'])
        d = styles(pg, '#std .icon-disabled', ['color', 'cursor'])
        check('icon-edit reads blue, and is 34px square',
              e['color'] == 'rgb(37, 99, 235)' and e['width'] == '34px'
              and e['height'] == '34px')
        check('icon-view reads the house teal', v['color'] == 'rgb(14, 124, 139)')
        check('icon-disabled reads grey and refuses the cursor',
              d['cursor'] == 'not-allowed' and d['color'] == 'rgb(138, 151, 157)')

        pn = styles(pg, '#pneutral', ['background-color', 'color'])
        pgd = styles(pg, '#pgood', ['background-color', 'color'])
        check('Inactive is grey, not red - decision 3',
              pn['color'] == 'rgb(107, 119, 128)')
        check('  and a good state is green, distinct from the accent',
              pgd['color'] == 'rgb(30, 125, 79)')

        sb = styles(pg, '#sbtn', ['border-color', 'color'])
        check('a status that is still an action renders as a button',
              sb['border-color'] == 'rgb(168, 216, 222)')

        if BOOT:
            bi = styles(pg, '#binfo', ['background-color'])
            check('REGRESSION: btn-info is still the deeper teal',
                  bi['background-color'] == 'rgb(14, 124, 139)')

        check('the empty state is visible',
              pg.evaluate("()=>document.querySelector('#empty')"
                          ".getBoundingClientRect().height") > 40)

        check('desktop: the mobile action bar is hidden',
              styles(pg, '#std .mobile-action-bar', ['display'])['display']
              == 'none')
        check('desktop: the per-action cells are shown',
              styles(pg, '#std .desktop-action-cell', ['display'])['display']
              != 'none')
        pg.close()

        # -------------------------------------------------------- mobile
        pg = browser.new_page(viewport={'width': 375, 'height': 800})
        pg.goto('file://' + tmp)

        check('mobile: the header row is dropped',
              styles(pg, '#std thead', ['display'])['display'] == 'none')
        row = styles(pg, '#std tbody tr:nth-child(1)',
                     ['display', 'background-color', 'border-radius'])
        check('mobile: rows become cards',
              row['display'] == 'block'
              and row['background-color'] == 'rgb(255, 255, 255)'
              and row['border-radius'] == '8px')
        check('mobile: a labelled cell shows its data-label',
              pg.evaluate("()=>getComputedStyle(document.querySelector("
                          "'#std tbody td:nth-child(2)'),'::before').content")
              == '"Phone"')
        check('mobile: the first cell is the card title, with no label',
              pg.evaluate("()=>getComputedStyle(document.querySelector("
                          "'#std tbody td:first-child'),'::before').content")
              == 'none')
        bar = styles(pg, '#std .mobile-action-bar',
                     ['display', 'grid-template-columns'])
        check('mobile: the action bar is a 3-up grid',
              bar['display'] == 'grid'
              and len(bar['grid-template-columns'].split()) == 3)
        check('mobile: the per-action cells step aside',
              styles(pg, '#std .desktop-action-cell', ['display'])['display']
              == 'none')
        # Measure the standard table, NOT the document: the control table on
        # this same page is deliberately unconverted and therefore too wide,
        # so document.scrollWidth is expected to overflow. That it does is
        # the proof the conversion is doing real work - asserted below.
        w_std = pg.evaluate(
            "()=>document.querySelector('#std').scrollWidth")
        w_ctl = pg.evaluate(
            "()=>document.querySelector('#ctl').scrollWidth")
        check('mobile: the converted table fits the viewport (%dpx)' % w_std,
              w_std <= 375)
        check('CONTROL: the unconverted one does NOT fit (%dpx)' % w_ctl,
              w_ctl > 375)
        check('  so the conversion is measurably responsible',
              w_ctl > w_std)

        # And the control, again - it should NOT have converted.
        check('CONTROL: without .alv-table it keeps its header row',
              styles(pg, '#ctl thead', ['display'])['display']
              != 'none')
        pg.close()
        browser.close()
finally:
    if os.path.exists(tmp):
        os.remove(tmp)

# ================================================================== out
print('')
bad = 0
for label, ok in results:
    print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad += 0 if ok else 1
print('')
print('%d of %d failed' % (bad, len(results)) if bad
      else 'All %d checks passed.' % len(results))
sys.exit(1 if bad else 0)
