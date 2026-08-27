"""test_button_reach - one vocabulary, four surfaces, and paper.

    python test_button_reach.py

The round's whole claim is that a TONE is not bar behaviour. So the browser
half renders the same four class names in three different places - a page
bar, a modal footer, a report header - and demands the colour be identical
and the SIZING be different, because sizing belongs to whoever owns the
layout.

That second half is the one with teeth. If the tones set padding, the small
"quick add" buttons inside the Add Asset modal silently inflate to full
size. The control adds padding back and watches btn-sm stop meaning
anything.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')

MODALS = ('asset_detail.html', 'property_assets.html', 'suppliers.html')
BACKS = ('property_report.html', 'supplier_report.html',
         'lease_renewal_report.html', 'tenant_payment_days.html')

results = []


def check(label, ok):
    results.append((label, bool(ok)))


def read(name):
    p = os.path.join(TPL, name)
    if not os.path.exists(p):
        sys.exit('! pages/templates/%s not found - run from the root' % name)
    return open(p, encoding='utf-8-sig', errors='replace').read().replace(
        '\r\n', '\n')


def strip_comments(s):
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)


BASE = read('base.html')
_i = BASE.find('--alv-table-std')
BLOCK = strip_comments(BASE[_i:BASE.find('</style>', _i)]) if _i >= 0 else ''

# ===================================================== base.html structure
check('the action bar is still there', '--alv-actions-std' in BASE)
def tone_body(selector_re):
    """The declarations of a top-level tone rule, or None if there isn't one.

    Returning None matters. The first draft wrote
    `'padding' not in (re.search(...) or re.match('','')).group(0)`, and
    `re.match('','')` matches, so `.group(0)` is the empty string and the
    check was TRUE whatever base.html said. A check that cannot fail reads
    as coverage - the lesson this project keeps re-learning.
    """
    m = re.search(r'\n      (?:%s)[^{]*\{([^}]*)\}' % selector_re, BLOCK)
    return m.group(1) if m else None


for tone in ('.action-primary', '.action-secondary', '.action-danger'):
    check('%-18s is UNSCOPED' % tone,
          re.search(r'\n      %s\s*[,{]' % re.escape(tone), BLOCK) is not None)
    # The check that would have caught the regression. A bare tone is
    # (0,1,0) and TIES with a page's own .btn-info, which wins on document
    # order because a page's <style> comes after base.html. Properties and
    # Suppliers both have one, and both turned Help and Back solid teal.
    check('  and paired with .btn, or a page .btn-info beats it',
          '.btn%s' % tone in BLOCK)
    body = tone_body(re.escape(tone))
    check('  %-16s has a rule at all' % tone, body is not None)
    check('  %-16s sets no padding' % tone,
          body is not None and 'padding' not in body)

check('.action-back is unscoped and aliases .back-button',
      re.search(r'\n      \.action-back,\s*\n\s*\.back-button\s*[,{]', BLOCK)
      is not None)
check('  and both are paired with .btn too',
      '.btn.action-back' in BLOCK and '.btn.back-button' in BLOCK)
_bb = tone_body(r'\.action-back,[^{}]*')
check('  the aliased rule was found', _bb is not None)
check('  and it sets no padding either',
      _bb is not None and 'padding' not in _bb)
# The bar KEEPS its own sizing - that is layout, not tone.
check('the bar still owns sizing',
      re.search(r'\.page-action-buttons \.btn,[^{]*\{[^}]*padding:', BLOCK,
                re.S) is not None)
check('  and the whole mobile collapse',
      '.page-action-buttons .action-secondary { display: none; }' in BLOCK)

_p = BLOCK[BLOCK.find('@media print'):]
check('paper hides the furniture', 'display: none !important' in _p)
for f in ('.page-action-buttons', '.action-more-wrapper', '.back-button',
          '.view-toggle-row', '.filter-panel', '.no-print'):
    check('  %-22s is hidden on paper' % f,
          re.search(r'(?<![\w-])%s(?![\w-])' % re.escape(f), _p) is not None)
check('  but the table is NOT hidden - it is the point of the page',
      not re.search(r'\.alv-table[^{}]*,[^{]*display:\s*none', _p))
check('base.html braces still balance', BLOCK.count('{') == BLOCK.count('}'))

# ============================================================== the pages
for name in MODALS:
    t = read(name)
    check('%s: no green confirm' % name, 'btn-success' not in t)
    check('  no solid grey Cancel', 'class="btn btn-secondary"' not in t)
    check('  the dialogs can still be dismissed (%d)'
          % t.count('data-dismiss="modal"'),
          t.count('data-dismiss="modal"') >= 1)
    check('  and every footer button still has .btn for its sizing',
          not re.search(r'class="action-(?:primary|secondary)', t))
check('property_assets: the small quick-adds stayed small',
      read('property_assets.html').count('action-primary btn-sm') == 3)
check('suppliers: Delete Permanently is a danger TONE, not a fill',
      'action-secondary action-danger' in read('suppliers.html'))
check('asset_detail: Download is the primary of its dialog',
      'id="invoiceDownloadLink" href="#" class="btn action-primary"'
      in read('asset_detail.html'))
for name in BACKS:
    t = read(name)
    check('%s: Back is quiet' % name,
          'class="btn back-button"' in t and 'btn-info back-button' not in t)
_ea = read('edit_asset.html')
check('edit_asset: the yellow bar is gone',
      'bg-warning' not in _ea and 'alv-card alv-card-lead form-card' in _ea)
check('  Back uses the standard name now',
      'action-btn-back' not in _ea and 'class="btn action-back"' in _ea)
check('  Save is the primary, Cancel outlined',
      'class="btn action-primary"' in _ea
      and 'class="btn action-secondary"' in _ea
      and 'btn-success' not in _ea)
check('  and the white-on-yellow heading rule went with it',
      '.form-card .card-header h4' not in _ea)
check('  while the rest of the form card survived',
      _ea.count('.form-card') >= 4)

_se = read('suppliers_edit.html')
check('suppliers_edit: Save is the primary',
      'class="btn action-primary"' in _se and 'btn-info action-' not in _se)

for name in (('base.html',) + MODALS + BACKS
             + ('suppliers_edit.html', 'edit_asset.html')):
    t = read(name)
    check('%s: tags balance' % name, t.count('{%') == t.count('%}'))
    check('  no unclosed Django comment',
          not any('{#' in ln and '#}' not in ln for ln in t.split('\n')))

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

    BODY = (
        '<div class="page-action-buttons">'
        '<a class="btn action-primary" id="bar_p">Edit</a>'
        '<a class="btn action-secondary action-danger" id="bar_d">Delete</a>'
        '<a class="btn action-back" id="bar_b">Back</a></div>'
        '<div class="modal-footer" style="display:flex;gap:8px">'
        '<button class="btn action-secondary" id="mod_c">Cancel</button>'
        '<button class="btn action-primary" id="mod_p">Add Record</button>'
        '<button class="btn action-primary btn-sm" id="mod_s">Save</button>'
        '<button class="btn action-secondary action-danger" id="mod_d">'
        'Delete</button></div>'
        '<a class="btn back-button" id="rep_b">Back</a>'
        '<div class="view-toggle-row" id="toggle">Group by</div>'
        '<table class="table alv-table" id="tbl"><thead><tr><th>A</th></tr>'
        '</thead><tbody><tr><td>1</td></tr></tbody></table>')

    def rgb(v):
        m = re.findall(r'\d+', v or '')
        return tuple(int(x) for x in m[:3]) if len(m) >= 3 else None

    tmp = os.path.join(ROOT, '_reach_probe.html')
    try:
        try:
            with sync_playwright() as p:
                exe = '/opt/pw-browsers/chromium'
                br = (p.chromium.launch(executable_path=exe)
                      if os.path.exists(exe) else p.chromium.launch())
                pg = br.new_page(viewport={'width': 1000, 'height': 700})
                open(tmp, 'w', encoding='utf-8').write(
                    '<!doctype html><meta charset=utf-8><style>%s</style>'
                    '<style>%s</style><body style="margin:0;padding:16px;'
                    'background:#fff">%s</body>' % (BOOT, STD, BODY))
                pg.goto('file://' + tmp)
                pg.wait_for_timeout(200)

                def one(i):
                    v = pg.evaluate(
                        """(id)=>{const e=document.getElementById(id);
                           if(!e) return null; const c=getComputedStyle(e);
                           return {bg:c.backgroundColor,col:c.color,
                                   pt:parseFloat(c.paddingTop),
                                   pl:parseFloat(c.paddingLeft),
                                   h:Math.round(
                                     e.getBoundingClientRect().height)};}""",
                        i)
                    if v is None:
                        check('element #%s exists' % i, False)
                        return {'bg': 'absent', 'col': 'absent', 'pt': 0,
                                'pl': 0, 'h': 0}
                    return v

                bar_p, mod_p, mod_s = one('bar_p'), one('mod_p'), one('mod_s')
                bar_b, rep_b = one('bar_b'), one('rep_b')
                bar_d, mod_d = one('bar_d'), one('mod_d')
                mod_c = one('mod_c')

                # --- the colour is the same everywhere -------------------
                check('the primary is the same accent in a bar and a modal '
                      '(%s / %s)' % (bar_p['bg'], mod_p['bg']),
                      rgb(bar_p['bg']) == rgb(mod_p['bg'])
                      and rgb(bar_p['bg']) == (14, 124, 139))
                check('  Back is the same quiet in a bar and a report',
                      bar_b['bg'] == rep_b['bg']
                      and bar_b['bg'] in ('rgba(0, 0, 0, 0)', 'transparent'))
                check('  the danger tone is the same in both (%s)'
                      % mod_d['bg'],
                      rgb(bar_d['bg']) == rgb(mod_d['bg'])
                      and rgb(mod_d['bg']) == (255, 255, 255))
                check('  and Cancel is outlined, not solid grey (%s)'
                      % mod_c['bg'], rgb(mod_c['bg']) == (255, 255, 255))

                # --- the SIZING is not -----------------------------------
                check('the bar owns its own sizing (%gpx/%gpx vs modal '
                      '%gpx/%gpx)' % (bar_p['pt'], bar_p['pl'],
                                      mod_p['pt'], mod_p['pl']),
                      bar_p['pl'] != mod_p['pl'])
                check('  and btn-sm still means small (%dpx vs %dpx)'
                      % (mod_s['h'], mod_p['h']),
                      mod_s['h'] < mod_p['h'] and mod_s['pl'] < mod_p['pl'])

                # --- the regression, reproduced -------------------------
                # A page's own .btn-info, in a <style> AFTER base.html -
                # which is where every page's <style> sits. This is exactly
                # what Properties and Suppliers have, and what turned their
                # Help and Back solid teal when the tones were unscoped
                # without being paired with .btn.
                PAGE = ('.btn-info { background-color: #0e7c8b; color: #fff; '
                        'border: 1px solid #0e7c8b; }')
                open(tmp, 'w', encoding='utf-8').write(
                    '<!doctype html><meta charset=utf-8><style>%s</style>'
                    '<style>%s</style><style>%s</style>'
                    '<body style="margin:0;padding:16px;background:#fff">'
                    '<div class="page-action-buttons">'
                    '<a class="btn btn-info action-secondary" id="p_help">'
                    'Help</a>'
                    '<a class="btn btn-info action-back" id="p_back">Back</a>'
                    '</div></body>' % (BOOT, STD, PAGE))
                pg.goto('file://' + tmp)
                pg.wait_for_timeout(150)
                pp = pg.evaluate(
                    """()=>({help:getComputedStyle(
                         document.getElementById('p_help')).backgroundColor,
                       back:getComputedStyle(
                         document.getElementById('p_back')).backgroundColor});""")
                check('a page with its own .btn-info does NOT beat the tone '
                      '- Help stays outlined (%s)' % pp['help'],
                      rgb(pp['help']) == (255, 255, 255))
                check('  and Back stays quiet (%s)' % pp['back'],
                      pp['back'] in ('rgba(0, 0, 0, 0)', 'transparent'))

                # --- paper ------------------------------------------------
                open(tmp, 'w', encoding='utf-8').write(
                    '<!doctype html><meta charset=utf-8><style>%s</style>'
                    '<style>%s</style><body style="margin:0;padding:16px;'
                    'background:#fff">%s</body>' % (BOOT, STD, BODY))
                pg.goto('file://' + tmp)
                pg.wait_for_timeout(150)
                pg.emulate_media(media='print')
                pg.wait_for_timeout(150)
                pr = pg.evaluate(
                    """()=>{const d=s=>{const e=document.querySelector(s);
                       return e?getComputedStyle(e).display:'absent';};
                       return {bar:d('.page-action-buttons'),
                               rep:d('.back-button'),
                               tog:d('.view-toggle-row'),
                               tbl:d('.alv-table')};}""")
                check('on paper the action bar is gone (%s)' % pr['bar'],
                      pr['bar'] == 'none')
                check('  the report Back is gone (%s)' % pr['rep'],
                      pr['rep'] == 'none')
                check('  the Group-by toggle is gone (%s)' % pr['tog'],
                      pr['tog'] == 'none')
                check('  CONTROL: the TABLE is still there (%s)' % pr['tbl'],
                      pr['tbl'] not in ('none', 'absent'))
                br.close()
        except Exception as exc:
            check('the browser half ran to the end (%s: %s)'
                  % (type(exc).__name__, str(exc).split(chr(10))[0][:70]),
                  False)
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
