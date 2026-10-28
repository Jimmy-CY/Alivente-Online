# -*- coding: utf-8 -*-
"""test_customer_view.py - round NV-1d, 16 Oct 2026.

A VIEW BUTTON NEEDS SOMETHING TO VIEW.

Demetri: "On Customers (In Invoices), can we add a View button next to
the Edit and Delete?"

WHAT THIS SUITE PROVES THAT A COMMENT CANNOT
    Section 1 asserts there is NO customer detail route, which is the
    only reason a modal is the right answer. If one ever appears, View
    should become a link and this suite says so before anybody guesses.
    Section 7 OPENS THE MODAL IN A BROWSER, twice, and proves the second
    click swaps the sheet rather than stacking a second one - which is
    the whole risk of a pattern that holds every record at once.

THE PAGE SHADOWS `$`
    Inside the filter IIFE, line 240 of customer_list.html is
    `function $(id) { return document.getElementById(id); }`. That is
    where all this page's DOM wiring lives, so it is where a click
    handler naturally goes - and written there, `$(document).on(...)`
    throws, because getElementById of a document is null. Section 4
    pins the handler to plain DOM and window.jQuery, and section 7
    proves the page loads with no console error.

NUMBERS, AND WHICH MACHINE MEASURED THEM
    Nothing here asserts a text width. The one layout number is the
    phone bar's TRACK COUNT, which is a declared grid and not a
    measurement of any string. See the sixth failure in
    claude/standard_delivery_preflight.md.

WHAT THIS ROUND DOES NOT PROVE
    That the four fields are the right four. They are every field on
    InvoiceCustomer the list does not already show, apart from the
    record's own timestamps, which nobody asked for.
"""
# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------

import os
import re
import sys

import alv_tree

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by  # noqa: F401
except Exception as e:
    as_left_by = None
    print('  !! alv_rounds could not be imported: %s' % e)

code_only = alv_tree.code_only
python_code_only = alv_tree.python_code_only

SUFFIX = '.bak_custview'
PAGE = 'customer_list.html'
VIEW = os.path.join('pages', 'views', 'physical_invoices.py')
ME = 'test_customer_view.py'
PATCHER = 'apply_customer_view.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
JQ = os.path.join(ROOT, 'test_fixture_jquery360.js')

CONVERTED_NOW, ALIAS_NOW = 88, 87
NOTE = 'NV-1d, 16 Oct 2026 - '
ROW_N = 114
SHEET_ROWS = 7
HIDDEN = ('billing_address', 'billing_tel', 'email_cc', 'email_body')

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:6]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def css_of(t):
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style\s*>', t, re.S))


def js_of(t):
    return '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script\s*>', t, re.S))


PATH = alv_tree.path_of(PAGE)
VPATH = os.path.join(ROOT, VIEW)
NOW, VNOW = read(PATH), read(VPATH)
# A ROUND'S OWN BEFORE IS ITS OWN BACKUP, read directly.
WAS = read(PATH + SUFFIX) if os.path.isfile(PATH + SUFFIX) else read(PATH)
VWAS = (read(VPATH + SUFFIX) if os.path.isfile(VPATH + SUFFIX)
        else read(VPATH))
B_NOW, B_WAS = code_only(NOW), code_only(WAS)
C_NOW = css_of(B_NOW)
J_NOW, J_WAS = js_of(B_NOW), js_of(B_WAS)
V_NOW, V_WAS = python_code_only(VNOW), python_code_only(VWAS)


def fn_of(src, name):
    """One function's source, so a file-wide check cannot stand in."""
    i = src.find('def %s(' % name)
    if i < 0:
        return ''
    j = src.find('\ndef ', i + 1)
    return src[i:j if j > 0 else len(src)]


# ==========================================================================
head('1. THERE WAS NO CUSTOMER TO VIEW, AND THAT IS WHY IT IS A MODAL')
# ==========================================================================
urls = read(os.path.join(ROOT, 'pages', 'urls.py'))
named = sorted(set(re.findall(r"name=[\"']([a-z_]*customer[a-z_]*)[\"']",
                              urls)))
ok('customer_detail' not in named,
   'there is NO customer detail route - list, add, edit, delete - which '
   'is the only reason a read-only sheet is the right shape', named)
for need in ('customer_list', 'customer_edit', 'customer_delete'):
    ok(need in named, '  %s is there' % need)
ok(len(named) >= 3,
   '  and if a detail route ever appears, View should become a LINK and '
   'this section is where that gets noticed')

models = read(os.path.join(ROOT, 'pages', 'models.py'))
m = re.search(r'class InvoiceCustomer\b.*?(?=\nclass )', models, re.S)
ok(m is not None, 'InvoiceCustomer is in pages/models.py')
fields = set(re.findall(r'(?m)^\s{4}(\w+)\s*=\s*models\.', m.group(0))
             if m else [])
for f in HIDDEN:
    ok(f in fields, '  the model really has %s' % f)
ok('created_at' in fields and 'updated_at' in fields,
   'and it has created_at and updated_at, which the sheet does NOT show '
   "- nobody asked what a customer record's own timestamps are")


# ==========================================================================
head('2. THE FOUR HIDDEN FIELDS REACH THE TEMPLATE, WITH NO NEW QUERY')
# ==========================================================================
f_now, f_was = fn_of(V_NOW, 'customer_list'), fn_of(V_WAS, 'customer_list')
ok(f_now != '', 'customer_list is in %s' % VIEW)
for f in HIDDEN:
    ok('"%s": c.%s' % (f, f) in f_now,
       '  %-16s is built in customer_list OWN loop' % f)
    ok('"%s": c.%s' % (f, f) not in f_was,
       '  CONTROL: and was not' % () if False else
       '  CONTROL: and %s was not' % f)
# SCOPED, BECAUSE THE WORD IS ELSEWHERE IN THIS FILE. billing_address
# appears in a profile read, an edit POST and a create, all in other
# functions - a file-wide check refused a correct round on them.
ok(V_WAS.count('billing_address') >= 3,
   'CONTROL: billing_address was already in this file %d time(s), in '
   'other functions - which is why every check here is function-scoped'
   % V_WAS.count('billing_address'))
ok('annotate' in f_now and f_now.count('.filter(') == f_was.count('.filter('),
   'and the queryset is untouched - the same annotate, the same filters, '
   'so this round added no query')
ok(f_now.count('for c in customers') == 1,
   '  and still one loop over objects it already had')


# ==========================================================================
head('3. MARKUP A GATE CAN READ, NOT A BUILT STRING')
# ==========================================================================
ok(B_NOW.count('id="customerModal"') == 1,
   'there is one modal on the page')
ok(B_NOW.count('class="cust-sheet"') == 1,
   'with ONE sheet inside the for loop - so the page holds a sheet per '
   'customer as markup', B_NOW.count('class="cust-sheet"'))
sheet = re.search(r'<div class="cust-sheet"[^>]*>(.*?)\n\s*</div>',
                  B_NOW, re.S)
ok(sheet is not None and sheet.group(1).count('cust-sheet-row')
   == SHEET_ROWS,
   'and the sheet draws %d rows' % SHEET_ROWS,
   sheet.group(1).count('cust-sheet-row') if sheet else 0)
for f in HIDDEN[:3]:
    ok('row.%s' % f in B_NOW, '  including row.%s' % f)
ok('row.email_body' not in sheet.group(1) if sheet else False,
   '  and NOT email_body, which is a saved e-mail greeting and belongs '
   'in the edit form rather than in front of a reader')

# THE GATE TESTS WHAT IS WRITTEN. The page's own `tags.innerHTML = ''`
# CLEARS the filter chips before rebuilding them with createTextNode -
# the careful thing, not the careless one - and a gate that banned the
# word refused it.
writes = [m2.group(1).strip() for m2 in
          re.finditer(r'innerHTML\s*=\s*([^;\n]+)', J_NOW)]
ok(writes and all(w in ("''", '""') for w in writes),
   'every innerHTML on this page is an empty CLEAR, never a build: %s'
   % writes, writes)
ok("tags.innerHTML = ''" in J_NOW,
   "  and the page's own chip clear is still there - it rebuilds with "
   'createTextNode, which is the rule this sheet keeps too')
ok('createTextNode' in J_NOW,
   '  as does the chip builder it sits beside')


# ==========================================================================
head('4. THE PAGE SHADOWS `$`, SO THE HANDLER DOES NOT USE IT')
# ==========================================================================
ok('function $(id) { return document.getElementById(id); }' in J_NOW,
   'line 240 of this page defines $ as getElementById - inside the '
   'filter IIFE, which is where all its DOM wiring lives')
key = "closest('.js-cust-view')"
ok(key in J_NOW, 'the View handler is on the page')
if key in J_NOW:
    _k = J_NOW.find(key)
    _i = J_NOW.rfind('(function', 0, _k) if _k >= 0 else -1
    hs = J_NOW[_i:] if _i >= 0 else ''
    ok(re.search(r'(?<![\w.])\$\s*\(', hs) is None,
       '  and it uses no bare $( at all - written in the IIFE above, '
       '`$(document).on(...)` throws, because getElementById of a '
       'document is null and null has no .on')
    ok('window.jQuery' in hs,
       '  it reaches Bootstrap by its real name instead')
    ok('addEventListener' in hs and 'closest' in hs,
       '  and binds with plain DOM and a delegated closest()')
    ok('textContent' in hs,
       '  writing the title with textContent, because a customer name is '
       'data somebody typed')
# HK-3, 28 Oct 2026 - the page no longer loads its own copy; base.html
# loads the one jQuery in <head>, ahead of every page's scripts.
_bsrc = read(alv_tree.path_of('base.html'))
ok(0 <= _bsrc.find('code.jquery.com/jquery-3.6.0') < _bsrc.find('</head>'),
   'jQuery really is on the page, so window.jQuery is not a hope')


# ==========================================================================
head('5. VIEW IS A LOOK, SO IT SORTS FIRST AND NEEDS NO PERMISSION')
# ==========================================================================
strip = re.search(r'<div class="row-actions">(.*?)</div>', B_NOW, re.S)
ok(strip is not None, 'the desktop strip is there')
if strip:
    # find(), NOT index(). On a tree where this round is not applied
    # there is no js-cust-view, and str.index RAISES - a traceback
    # instead of a verdict, which step 4 of the pre-flight exists to
    # catch and which cost a push on 15 Oct.
    body = strip.group(1)
    _v, _e, _d = (body.find('js-cust-view'), body.find('icon-edit'),
                  body.find('icon-delete'))
    ok(_v >= 0 and _e >= 0 and _v < _e,
       'View comes before Edit in the strip', (_v, _e))
    ok(_e >= 0 and _d >= 0 and _e < _d,
       '  and Edit before Delete', (_e, _d))
    ok('js-cust-view' in body.split('{% if perms')[0],
       'and View is OUTSIDE the permission test - reading a record whose '
       'other columns are already on screen is not editing invoices')
ok(len(re.findall(r'class="[^"]*\bjs-cust-view\b[^"]*"', B_NOW)) == 2,
   'there are two View controls - the desktop strip and the phone bar',
   len(re.findall(r'class="[^"]*\bjs-cust-view\b[^"]*"', B_NOW)))
ok('js-cust-view' not in B_WAS,
   'CONTROL: and neither existed before this round')
ok('icon-action-btn icon-view' in B_NOW,
   'the desktop one is base icon-view, the sixth name on --alv-view')

try:
    import alv_rowactions as RA
    ok(RA.FAMILY['view'] < RA.FAMILY['edit'] < RA.FAMILY['delete'],
       'the vocabulary sorts view (LOOK %d), edit (CHANGE %d), delete '
       '(DESTROY %d) - the markup is not told that order'
       % (RA.FAMILY['view'], RA.FAMILY['edit'], RA.FAMILY['delete']))
except Exception as e:
    skip('the vocabulary order', 'alv_rowactions: %s' % e)


# ==========================================================================
head('6. THE BAR ASKS FOR AS MANY COLUMNS AS IT DRAWS')
# ==========================================================================
ok('{% if not perms.auth.can_edit_invoices %} cols-2' in B_NOW,
   'the column count is conditional: cols-2 when the bar draws two')
# AND THREE IS NOT NAMED. base declares cols-1, cols-2 and cols-4 and
# deliberately no cols-3, because .mobile-action-bar is already
# repeat(3, 1fr) - ten pages wear the bare class for that reason. The
# first cut of this round asked for cols-3, which styles nothing.
_bar_cls = re.search(r'<td class="(mobile-action-bar[^"]*)"', B_NOW)
ok(_bar_cls and 'cols-3' not in _bar_cls.group(1),
   '  and names NOTHING when it draws three, because three is base own '
   'default and cols-3 styles nothing',
   _bar_cls.group(1) if _bar_cls else None)
ok('mobile-action-bar cols-2' in B_WAS,
   'CONTROL: and it was a flat cols-2 before')
bar = re.search(r'<td class="mobile-action-bar[^"]*"[^>]*>(.*?)</td>',
                B_NOW, re.S)
ok(bar is not None, 'the phone bar is there')
if bar:
    # VIEW IS COMMON TO BOTH ARMS, which is the point of it needing no
    # permission - so it is counted once, outside the branch, and each
    # arm is counted on top. The first cut of this probe split on
    # {% else %} and reported the read-only arm drawing one control,
    # which is true of the ARM and false of the BAR.
    common = bar.group(1).split('{% if perms')[0]
    arms = bar.group(1).split('{% if perms')[1].split('{% else %}')
    ok(common.count('mobile-action-btn') == 1,
       '  View is drawn once, outside the permission branch',
       common.count('mobile-action-btn'))
    ok(len(arms) == 2, '  and the branch has two arms', len(arms))
    ok(arms[0].count('mobile-action-btn') == 2,
       '  an editor gets Edit and Delete on top of it - three in all',
       arms[0].count('mobile-action-btn'))
    ok(arms[1].count('mobile-action-btn') == 1,
       '  a reader gets one disabled Edit - TWO in all, where before '
       'this round the read-only bar drew ONE control in a two-column '
       'grid', arms[1].count('mobile-action-btn'))
_bcss = css_of(code_only(read(alv_tree.path_of('base.html'))))
ok('.mobile-action-bar.cols-2' in _bcss,
   'base declares cols-2, so the two-control arm asks rather than '
   'declares')
ok('.mobile-action-bar.cols-3' not in _bcss,
   '  and declares NO cols-3 - three is .mobile-action-bar own grid, '
   'which is why the three-control arm names nothing')
ok(re.search(r'\.mobile-action-bar\s*\{[^}]*repeat\(3,\s*1fr\)',
             _bcss) is not None,
   '  measured: the bar defaults to repeat(3, 1fr)')

# THE FALSIFIED SENTINEL, RE-POINTED BY THIS ROUND'S PATCHER.
ps = read(os.path.join(ROOT, PS1))
ok("Text = '{% if not perms.auth.can_edit_invoices %} cols-2'" in ps,
   'and the gate row that claimed a flat cols-2 on this page is '
   're-pointed - the conditional class made it false, and test_sentinels '
   'names a row like that by line within one run')
ok("'pages\\templates\\customer_list.html';       Text = "
   "'mobile-action-bar cols-2'" not in ps,
   '  with the old claim gone, not left beside it')


# ==========================================================================
head('7. RENDERED - THE SHEET OPENS, AND THE SECOND CLICK SWAPS IT')
# ==========================================================================
try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False

ROWS = [('7', 'Acme Marine Ltd'), ('9', 'Blue Harbour SA')]
MARKUP = ('<table><tbody>' + ''.join(
    '<tr><td><span class="row-actions">'
    '<button type="button" class="icon-action-btn icon-view js-cust-view" '
    'data-cust="%s" data-name="%s" title="View Customer">'
    '<i class="fas fa-eye"></i></button></span></td></tr>' % (pk, nm)
    for pk, nm in ROWS) + '</tbody></table>'
    + '<div class="modal fade" id="customerModal"><div class="modal-dialog">'
      '<div class="modal-content"><div class="modal-header alv-modal-head">'
      '<h5 class="modal-title" id="customerModalLabel">Customer</h5></div>'
      '<div class="modal-body" id="customerModalBody">' + ''.join(
          '<div class="cust-sheet" id="cust-sheet-%s" hidden>'
          '<div class="cust-sheet-row"><span class="cust-sheet-key">'
          'Customer</span><span class="cust-sheet-val">%s</span></div>'
          '</div>' % (pk, nm) for pk, nm in ROWS)
    + '</div></div></div></div>')

LOOK = """() => {
  const shown = [...document.querySelectorAll('.cust-sheet')]
      .filter(e => !e.hidden).map(e => e.id);
  return {shown: shown,
          title: document.getElementById('customerModalLabel').textContent,
          n: document.querySelectorAll('.cust-sheet').length};
}"""

if not have_pw or not os.path.isfile(BOOT):
    skip('the sheet in a browser', 'playwright or the fixture is absent')
else:
    from playwright.sync_api import sync_playwright
    # THE HANDLER, LIFTED FROM THE PAGE RATHER THAN RETYPED. A probe
    # that re-implements the thing under test proves only that the probe
    # works - NV-1c's suite did exactly that and swallowed a control.
    hs = ''
    if key in J_NOW:
        _k = J_NOW.find(key)
        _i = J_NOW.rfind('(function', 0, _k) if _k >= 0 else -1
        hs = J_NOW[_i:] if _i >= 0 else ''
        _e = hs.rfind('})();')
        hs = hs[:_e + 5] if _e >= 0 else ''
    if not hs:
        skip('the sheet in a browser', 'the handler could not be lifted')
    else:
        p = os.path.join(SCRATCH, 'cust.html')
        with open(p, 'w', encoding='utf-8') as fh:
            fh.write('<!doctype html><html><head><meta charset="utf-8">'
                     '<meta name="viewport" content="width=device-width,'
                     'initial-scale=1"><style>%s</style><style>%s</style>'
                     '<style>%s</style>'
                     '<style>body{margin:0}*{transition:none !important}'
                     '</style></head><body>%s<script>%s</script></body>'
                     '</html>'
                     % (read(BOOT),
                        css_of(code_only(read(alv_tree.path_of(
                            'base.html')))),
                        C_NOW, MARKUP, hs))
        with sync_playwright() as pw:
            br = pw.chromium.launch(**({'executable_path': EXE}
                                       if os.path.exists(EXE) else {}))
            try:
                ctx = br.new_context(viewport={'width': 1280,
                                               'height': 800})
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                errs = []
                pg.on('pageerror', lambda e: errs.append(str(e)))
                _goto(pg, p)
                pg.wait_for_timeout(60)

                a = pg.evaluate(LOOK)
                ok(a['n'] == 2 and a['shown'] == [],
                   'on load the page holds %d sheets and shows none'
                   % a['n'], a)

                pg.eval_on_selector('[data-cust="7"]',
                                    'e => e.click()')
                pg.wait_for_timeout(60)
                b = pg.evaluate(LOOK)
                ok(b['shown'] == ['cust-sheet-7'],
                   'clicking the first View shows its sheet and only its '
                   'sheet', b)
                ok(b['title'] == 'Acme Marine Ltd',
                   '  and the title is that customer, written with '
                   'textContent', b['title'])

                # THE CLICK IS DISPATCHED, NOT POINTED. An open modal
                # intercepts the pointer, which is correct modal
                # behaviour - a pg.click here times out and reads like a
                # broken control.
                pg.eval_on_selector('[data-cust="9"]',
                                    'e => e.click()')
                pg.wait_for_timeout(60)
                c = pg.evaluate(LOOK)
                ok(c['shown'] == ['cust-sheet-9'],
                   'the second click SWAPS the sheet - it does not stack '
                   'a second one, which is the whole risk of holding '
                   'every record at once', c)
                ok(c['title'] == 'Blue Harbour SA',
                   '  and the title follows it', c['title'])
                ok(not errs,
                   'and the page raised no error at all - which is what '
                   'the $ shadow would have done had the handler used it',
                   errs[:3])
                ctx.close()

                # --- THE CONTROL: the handler as it was first written.
                q = os.path.join(SCRATCH, 'cust_dollar.html')
                with open(q, 'w', encoding='utf-8') as fh:
                    fh.write('<!doctype html><html><head>'
                             '<meta charset="utf-8"></head><body>'
                             '<script>'
                             'function $(id) { return '
                             'document.getElementById(id); }\n'
                             'try { $(document).on("click", function(){}); }'
                             'catch (e) { window.__err = e.message; }'
                             '</script></body></html>')
                ctx = br.new_context(viewport={'width': 800, 'height': 400})
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                _goto(pg, q)
                pg.wait_for_timeout(40)
                msg = pg.evaluate("() => window.__err || ''")
                ok('null' in msg.lower() or 'undefined' in msg.lower(),
                   "CONTROL: with this page's $ in scope, $(document).on "
                   'throws - %r - so the handler avoiding $ is not a '
                   'style preference' % msg, msg)
                ctx.close()
            finally:
                br.close()


# ==========================================================================
head('8. REGISTERED, ON THE GATE')
# ==========================================================================
ok(ME in ps, '%s runs this suite' % PS1)
ok(ME in read(os.path.join(ROOT, 'alv_tree.py')),
   'alv_tree.CONVERTED names it')
ok(SUFFIX in read(os.path.join(ROOT, 'alv_rounds.py')),
   'alv_rounds.ROUNDS names %s' % SUFFIX)
ok("Text = 'js-cust-view'" in ps,
   'and the gate carries a row for the View itself')
ok("Text = 'cust-sheet-row'" in ps,
   '  one for the sheet being markup')
ok('Text = \'"billing_address": c.billing_address\'' in ps,
   '  and one naming the row AS IT IS BUILT - billing_address alone is '
   'in that file three times already, so the bare word could never have '
   'failed')
# A FLOOR, NOT A PIN - this is the last of the four NV rounds, but a
# later round will move these again.
wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
co = read(os.path.join(ROOT, 'test_code_only.py'))
bh = read(os.path.join(ROOT, 'test_bar_height.py'))
ok(NOTE + 'this round own suite' in wd,
   "the converted count carries this round's note")
ok(NOTE + 'this round own patcher and suite' in co,
   'and so does the alias count')
ok(NOTE + 'the View button in the desktop strip' in bh,
   'and the table-row census names the View button')
ok(len(alv_tree.CONVERTED) >= CONVERTED_NOW,
   '  CONVERTED holds at least %d' % CONVERTED_NOW,
   len(alv_tree.CONVERTED))
# THE ROW COUNT, NOT THE OTHER TWO - RV-1, 23 Oct 2026.
# This read `= 267, (\d+), 95`, pinning the BAR and MODAL
# counts incidentally. RV-1 adds a page whose bar carries
# three controls, N_BAR moved 267 -> 270, and the claim
# failed on a number it does not care about.
_r = re.search(r'N_BAR, N_ROW, N_MODAL = \d+, (\d+), \d+', bh)
ok(_r and int(_r.group(1)) >= ROW_N,
   '  and the table-row count is at least %d - 110 plus NV-1b two, '
   'NV-1c one and this round one, each measured per page' % ROW_N,
   _r.group(1) if _r else None)


# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NV-1d: Customers has a View, and because this application has')
print('  no customer detail route it opens a read-only sheet - the shape')
print('  Demetri described for receipts in the same batch of findings.')
print('')
print('  It carries the FOUR fields the table has no room for, with no')
print('  new route and no new query: the loop already held the object.')
print('')
print('  Built as MARKUP a gate can read, and wired with plain DOM and')
print('  window.jQuery, because line 240 of this page defines $ as')
print('  getElementById - section 7 proves what the other spelling does.')
print('')
sys.exit(1 if failed else 0)
