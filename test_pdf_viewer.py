# -*- coding: utf-8 -*-
"""test_pdf_viewer.py - round PV-1, 15 Oct 2026.

THIS APPLICATION ALREADY HAD A DOCUMENT VIEWER. TWO PAGES WROTE THEIR OWN.

Demetri, on the live site: "why in the Invoice Document viewer different
without all the share buttons, etc. Compare this to Actual Expenses."

WHAT THIS SUITE PROVES THAT A COMMENT CANNOT

    Section 3 RENDERS the shared viewer's footer at 390px under each
    page's own CSS, from the backup and from the file, with the real
    Bootstrap and jQuery fixtures. It fails if the buttons stop fitting.
    The numbers it prints for the backups are 754px and 963px of controls
    on a 390px screen - what this round would have shipped had the survey
    stopped at "include the component".

    Section 4 OPENS the viewer on top of the drill-down, closes it, and
    asserts the page behind is still locked. Its CONTROL removes the
    round's three-line handler and fails, so the check cannot pass for
    the wrong reason.

    Section 5 pins the DOCUMENT ORDER of the include. Both modals compute
    to z-index 1050 and the later one wins; the old viewer forced it with
    a hand-written 1060 and hid that. Move the include above the
    drill-down and this suite refuses.

WHAT IS ASKED OF A BACKUP AND WHAT IS ASKED LIVE
    The markup and CSS edits are this round's snapshot: before is
    .bak_pdfview, after is the file. The component itself, the census of
    who includes it, and the registers are INVARIANTS and are read live.

WHAT THIS ROUND DOES NOT PROVE
    That every page loads the component's dependencies once. 34 pages
    load a second jQuery over base's, and asset_detail is one of them.
    Section 7 counts them rather than leaving them to be rediscovered.
    It is a real defect and it is not this round's.
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
import importlib.util

import alv_tree

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

code_only = alv_tree.code_only
python_code_only = alv_tree.python_code_only

SUFFIX = '.bak_pdfview'
ME = 'test_pdf_viewer.py'
PATCHER = 'apply_pdf_viewer.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
BOOT_CSS = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
BOOT_JS = os.path.join(ROOT, 'test_fixture_bootstrap413.js')
JQ_JS = os.path.join(ROOT, 'test_fixture_jquery360.js')

PL = 'finance_pl_act.html'
AD = 'asset_detail.html'
PAGES = (PL, AD)
COMPONENT = os.path.join(ROOT, 'pages', 'templates', 'components',
                         'pdf_viewer.html')
INCLUDE = "{% include 'components/pdf_viewer.html' %}"

PHONE = 390
N_INCLUDERS = 13
N_HANDROLLED = 0
N_DUP_JQUERY = 0   # HK-3, 28 Oct 2026 - base loads jQuery once, in <head>, and every page's own copy is gone   # (was 33)
CONVERTED_NOW, ALIAS_NOW = 79, 69

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


def raw(p):
    with open(p, encoding='utf-8', errors='replace', newline='') as f:
        return f.read()


def was(p):
    """The file as PV-1 found it. A page this round never touched has no
    backup and is its own before - which is why section 1 checks the
    backups exist BY NAME before anything trusts a `was`."""
    b = p + SUFFIX
    return read(b) if os.path.isfile(b) else read(p)


def styles_of(t):
    return '\n'.join(
        re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
        for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S | re.I))


def component_markup():
    """The component with its Django comment and tags stripped - the
    markup, style and script a browser would actually receive."""
    t = read(COMPONENT)
    t = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', '', t,
               flags=re.S)
    return re.sub(r'\{%.*?%\}', '', t, flags=re.S)


_pspec = importlib.util.spec_from_file_location('_ap_pv1',
                                                os.path.join(ROOT, PATCHER))
ap = importlib.util.module_from_spec(_pspec)
_pspec.loader.exec_module(ap)

BASE_CSS = styles_of(read(alv_tree.path_of('base.html')))

print('=' * 74)
print('%s - PV-1, ONE DOCUMENT VIEWER' % ME)
print('=' * 74)

# ==========================================================================
head('1. SCOPE, AND THE BACKUPS EVERY BEFORE/AFTER BELOW RESTS ON')
# ==========================================================================
# as_left_by falls back to the LIVE file when it finds no backup. Correct
# and deliberate, and it means a missing backup turns a snapshot claim into
# a live read that reports plausible-looking wrong numbers instead of
# refusing. It cost a push on 14 Oct.
for r in PAGES:
    ok(os.path.isfile(alv_tree.path_of(r) + SUFFIX),
       '%-28s has its %s backup' % (r, SUFFIX))
for f in ('alv_tree.py', 'alv_rounds.py', PS1, 'test_waiting_down.py',
          'test_code_only.py'):
    ok(os.path.isfile(os.path.join(ROOT, f) + SUFFIX),
       '%-28s has its %s backup' % (f, SUFFIX))
ok(os.path.isfile(COMPONENT),
   'the shared component is on disk - this round includes it twice')
ok(not os.path.isfile(COMPONENT + SUFFIX),
   '  and this round did NOT change it: 13 pages depend on it')

# ==========================================================================
head('2. ONE VIEWER, AND THE OTHER TWO ARE GONE')
# ==========================================================================
for r in PAGES:
    p = alv_tree.path_of(r)
    before, now = was(p), read(p)
    ok('id="invoiceViewerModal"' in before,
       '%-22s DID declare a viewer of its own' % r)
    ok(now.count(INCLUDE) == 1,
       '  and now includes the shared one exactly once',
       now.count(INCLUDE))
    ok('invoiceViewerModal' not in code_only(now),
       '  with no reference to the old one left in code')
    ok('invoiceViewerContent' not in code_only(now),
       '  nor to its body')
    # THE OPENER CALLS THE COMPONENT, and falls back rather than throwing
    # if the component is ever dropped from the page.
    ok('openPdfViewer(' in code_only(now),
       '  and its opener calls openPdfViewer')
    ok("window.open(" in code_only(now),
       '  with a fallback if the component is ever not on the page')

# THE CENSUS, LIVE. A round that retires an implementation should be able
# to say how many are left.
inc = sorted(alv_tree.rel(p) for p in alv_tree.templates()
             if "components/pdf_viewer.html" in read(p))
hand = sorted(alv_tree.rel(p) for p in alv_tree.templates()
              if 'id="invoiceViewerModal"' in read(p))
ok(len(inc) >= N_INCLUDERS,
   '%d page(s) include the shared viewer' % len(inc), inc)
ok(len(hand) == N_HANDROLLED,
   'and %d page(s) still hand-roll one' % N_HANDROLLED, hand)

# AND asset_detail's OTHER viewer is untouched. A round that took the
# wrong modal would still pass every check above.
ad = read(alv_tree.path_of(AD))
ok('id="photoViewerModal"' in ad,
   "asset_detail's photo viewer is untouched - a different viewer for a "
   'different thing')

# ==========================================================================
head('3. THE PHONE FOOTER - RENDERED AT %dpx, BEFORE AND AFTER' % PHONE)
# ==========================================================================
# THE MEASUREMENT THAT JUSTIFIED THE SCOPING. Each page carries a blanket
# phone rule for modal footers; the shared viewer's footer is a modal
# footer. Before the exclusion the page rules overrule all three button
# widths, and the row stops fitting on a phone.
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

FOOTER_JS = """() => {
  const f = document.querySelector('.pdf-viewer-footer');
  if (!f) return null;
  const w = (s) => { const e = document.querySelector(s);
                     return e ? Math.round(e.getBoundingClientRect().width)
                              : null; };
  const btns = [...f.querySelectorAll('.btn')];
  return {dir: getComputedStyle(f).flexDirection,
          share: w('.pdf-action-share'),
          download: w('.pdf-action-download'),
          close: w('.pdf-action-close'),
          total: Math.round(btns.reduce(
                     (a, b) => a + b.getBoundingClientRect().width, 0)),
          rows: new Set(btns.map(
                     b => Math.round(b.getBoundingClientRect().top))).size};
}"""

STACK_JS = """() => {
  const cx = Math.round(window.innerWidth / 2);
  const cy = Math.round(window.innerHeight / 2);
  const top = document.elementFromPoint(cx, cy);
  const m = top && top.closest ? top.closest('.modal') : null;
  return {top: m ? m.id : (top ? (top.className || top.tagName) : 'nothing'),
          bodyClass: document.body.className,
          bodyOverflow: getComputedStyle(document.body).overflow,
          drillShown: document.getElementById('expenseDetailsModal')
                      ? document.getElementById('expenseDetailsModal')
                        .classList.contains('show') : null};
}"""

if sync_playwright is None or not all(
        os.path.isfile(f) for f in (BOOT_CSS, BOOT_JS, JQ_JS)):
    skip('sections 3-5', 'playwright or a Bootstrap/jQuery fixture is '
                         'missing')
else:
    BOOTC, BOOTJ, JQ = read(BOOT_CSS), read(BOOT_JS), read(JQ_JS)
    COMP = component_markup()

    def shell(page_css, extra_js=''):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,'
                'initial-scale=1"><title>t</title>'
                '<style>%s</style><style>%s</style><style>%s</style>'
                '</head><body>'
                '<div style="height:2400px">page</div>'
                '<div class="modal fade" id="expenseDetailsModal" '
                'tabindex="-1"><div class="modal-dialog modal-lg">'
                '<div class="modal-content">'
                '<div class="modal-header alv-modal-head">'
                '<h5 class="modal-title">Actual Expense Details</h5></div>'
                '<div class="modal-body" style="height:260px;overflow:auto">'
                '<div style="height:900px">rows</div></div></div></div></div>'
                '%s<script>%s</script><script>%s</script>%s</body></html>'
                % (BOOTC, BASE_CSS, page_css, COMP, JQ, BOOTJ, extra_js))

    # THE EXECUTABLE PATH IS THIS CONTAINER'S, NOT EVERY MACHINE'S.
    # test_js_buttons crashed Demetri's push on exactly this line on 13
    # Oct at suite 337 of 337. A crash blocks a push as hard as a failure
    # and says far less about why.
    _kw = {'executable_path': EXE} if os.path.exists(EXE) else {}
    with sync_playwright() as pw0:
        try:
            br = pw0.chromium.launch(**_kw)
        except Exception as _e:
            skip('sections 3-5', 'no browser could be launched: %s'
                 % str(_e).split('\n')[0][:90])
            br = None
        if br is not None:
            try:
                def footer_at(page_css, width=PHONE):
                    ctx = br.new_context(viewport={'width': width,
                                                   'height': 780})
                    ctx.route(re.compile(r'^https?://'),
                              lambda r: r.abort())
                    pg = ctx.new_page()
                    pg.set_content(shell(page_css))
                    pg.wait_for_timeout(200)
                    pg.evaluate("() => $('#pdfViewerModal').modal('show')")
                    pg.wait_for_timeout(420)
                    m = pg.evaluate(FOOTER_JS)
                    ctx.close()
                    return m

                for r in PAGES:
                    p = alv_tree.path_of(r)
                    b = footer_at(styles_of(was(p)))
                    n = footer_at(styles_of(read(p)))
                    if not b or not n:
                        skip('%s footer' % r, 'the viewer did not render')
                        continue
                    print('       %-20s before  %-14s share %3s  dl %3s  '
                          'close %3s  = %4dpx'
                          % (r[:20], b['dir'], b['share'], b['download'],
                             b['close'], b['total']))
                    print('       %-20s after   %-14s share %3s  dl %3s  '
                          'close %3s  = %4dpx'
                          % ('', n['dir'], n['share'], n['download'],
                             n['close'], n['total']))
                    ok(b['total'] > PHONE,
                       '%-22s the page rules DID overflow the viewer '
                       'footer (%dpx on a %dpx screen)'
                       % (r[:22], b['total'], PHONE), b)
                    ok(n['total'] <= PHONE,
                       '  and now the footer fits (%dpx)' % n['total'], n)
                    ok(n['rows'] == 1 and n['dir'] == 'row',
                       '  in ONE row, which is the layout the component '
                       'designed', n)
                    ok(n['download'] == 44 and n['close'] == 44,
                       '  with Download and Close at their 44px icon size',
                       n)
                    ok(n['share'] > n['download'],
                       '  and Share the wide one, as the component '
                       'intends', n)

                # ======================================================
                head('4. THE STACK, AND THE PAGE BEHIND IT')
                # ======================================================
                # Bootstrap 4 strips modal-open from <body> when the INNER
                # modal of a stacked pair closes. The page then scrolls
                # behind a modal that is still open. Not introduced by
                # this round - the hand-rolled viewer had it too.
                HANDLER = (
                    "<script>$(document).on('hidden.bs.modal', "
                    "'#pdfViewerModal', function () { "
                    "if ($('.modal.show, .modal.in').length) { "
                    "$('body').addClass('modal-open'); } });</script>")

                def stack_run(extra_js):
                    ctx = br.new_context(viewport={'width': 1180,
                                                   'height': 820})
                    ctx.route(re.compile(r'^https?://'),
                              lambda r: r.abort())
                    pg = ctx.new_page()
                    pg.set_content(shell(styles_of(read(
                        alv_tree.path_of(PL))), extra_js))
                    pg.wait_for_timeout(250)
                    pg.evaluate(
                        "() => $('#expenseDetailsModal').modal('show')")
                    pg.wait_for_timeout(420)
                    pg.evaluate("() => $('#pdfViewerModal').modal('show')")
                    pg.wait_for_timeout(420)
                    on_top = pg.evaluate(STACK_JS)
                    pg.evaluate("() => $('#pdfViewerModal').modal('hide')")
                    pg.wait_for_timeout(560)
                    after = pg.evaluate(STACK_JS)
                    ctx.close()
                    return on_top, after

                on_top, after = stack_run(HANDLER)
                ok(on_top['top'] == 'pdfViewerModal',
                   'the viewer opens ON TOP of the drill-down', on_top)
                ok(after['drillShown'],
                   '  and closing it leaves the drill-down open', after)
                ok('modal-open' in after['bodyClass']
                   and after['bodyOverflow'] == 'hidden',
                   '  with the page behind STILL locked (body %r, overflow '
                   '%s)' % (after['bodyClass'], after['bodyOverflow']),
                   after)

                # THE CONTROL. Without this round's three lines the same
                # run leaves the page scrolling - so the check above
                # cannot be passing for some other reason.
                _t2, after2 = stack_run('')
                ok('modal-open' not in after2['bodyClass']
                   and after2['bodyOverflow'] != 'hidden',
                   'CONTROL: without the handler the page behind UNLOCKS '
                   '(body %r, overflow %s) - which is the bug'
                   % (after2['bodyClass'], after2['bodyOverflow']), after2)
            finally:
                br.close()

# ==========================================================================
head('5. THE DOCUMENT ORDER, WHICH IS WHAT DECIDES THE STACK')
# ==========================================================================
# Both modals compute to z-index 1050. The later one in the document wins.
# The old viewer wrote `#invoiceViewerModal { z-index: 1060 }` and that
# worked, which is exactly why nobody had to know. Move the include above
# the drill-down and the viewer opens underneath it.
#
# READ WITH find(), NOT index(). Backed out, the include is not in the
# file and index() raises ValueError at module level - a traceback blocks
# a push exactly as hard as a failure and says far less about why. VB-1
# shipped the identical crash yesterday on RA.VERNACULAR[RM].
pl_now = read(alv_tree.path_of(PL))
_inc_at = pl_now.find(INCLUDE)
_drill_at = pl_now.find('id="expenseDetailsModal"')
ok(_inc_at > -1 and _drill_at > -1 and _inc_at > _drill_at,
   'the include sits AFTER #expenseDetailsModal in %s' % PL,
   'include at %d, drill-down at %d' % (_inc_at, _drill_at))
ok('z-index: 1060' not in code_only(pl_now),
   '  and the hand-written 1060 that used to force it is gone')
ok('#expenseDetailsModal { z-index: 1050; }' in pl_now,
   '  while the drill-down keeps its own, which is still doing work')

# AND THE SCOPING IS AN EXCLUSION, NOT AN OVERRIDE. An override would have
# tied with asset_detail's rule on specificity - its dialog also carries
# .modal-fullscreen-mobile - and been decided by source order.
ok(':not(.pdf-viewer-footer)' in code_only(pl_now),
   '%s excludes the viewer from its phone footer rule' % PL)
ok(':not(.pdf-viewer-modal-dialog)' in code_only(read(alv_tree.path_of(AD))),
   '%s does the same' % AD)
for r in PAGES:
    body = code_only(read(alv_tree.path_of(r)))
    ok('.pdf-viewer-footer .btn {' not in body
       and '.pdf-action-download {' not in body,
       '  %-22s and declares no counter-rule in the component\'s name'
       % r[:22])

# ==========================================================================
head('6. THE COMPONENT STILL DOES WHAT THE TWO PAGES GAVE UP')
# ==========================================================================
# A round that retires an implementation owes a list of what the
# replacement carries. Each of these was in one or both hand-rolled
# viewers; the component has all of them and three the pages never had.
comp = read(COMPONENT)
for frag, what in (
        ('pdfjsLib', 'PDF.js, so a PDF renders where an iframe cannot'),
        ('pdfViewerShareBtn', 'a Share control - the thing Demetri asked '
                              'about'),
        ('pdfViewerDownloadBtn', 'Download, which both pages had'),
        ('pdfViewerImageWrap', 'the image fallback, which both pages had'),
        ('pdfViewerError', 'an error state with a Download Instead, which '
                           'neither had'),
        ('modal-fullscreen-mobile', 'full-screen on a phone'),
        ('pdfZoomFit', 'zoom, which neither page had'),
        ('pdfNextPage', 'page navigation, which neither page had')):
    ok(frag in comp, '  the component carries %s' % what)

ok('navigator.share' in comp or 'canShare' in comp,
   '  and Share goes through the Web Share API rather than a link')

# THE SENTENCE THAT MADE THIS A DEFECT AND NOT A PREFERENCE. asset_detail
# told the user to open the file in another tab when its iframe failed.
# ASKED OF THE CODE, NOT OF THE FILE. The patcher's own comment QUOTES the
# apology while explaining why it went, so a raw text search finds it
# sitting in the file it was deleted from and reports the round undone.
# This check failed exactly that way before it was written properly -
# VB-1 made the identical mistake with an rgba triple the day before.
# code_only strips HTML and Django comments; it is the instrument.
ok('click here to open it in a new tab'
   in code_only(was(alv_tree.path_of(AD))),
   "asset_detail DID apologise for its iframe in its own markup")
ok('click here to open it in a new tab'
   not in code_only(read(alv_tree.path_of(AD))),
   '  and does not any more')

# ==========================================================================
head('7. THE GATES, AND THE REGISTERS')
# ==========================================================================
_spec = importlib.util.spec_from_file_location(
    '_sb_pv1', os.path.join(ROOT, 'Show-ButtonDrift.py'))
sb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sb)
drift = undecided = painted = 0
for r in sb.templates(True):
    rawp = read(alv_tree.path_of(r))
    sb.JS_REENABLED = sb.js_reenabled_ids(rawp)
    for h in sb._scan(r, sb.markup_of(rawp)):
        if h[0] == 'UNCLASSIFIED':
            undecided += 1
        elif h[0] == 'PAINTED':
            painted += 1
        elif sb.drifting(h):
            drift += 1
ok(drift == 0 and undecided == 0 and painted == 0,
   'the button gate is still clean over all %d page(s): 0 drifting, 0 '
   'undecided, 0 painted' % len(sb.templates(True)),
   '%d / %d / %d' % (drift, undecided, painted))

ok(ME in alv_tree.CONVERTED, '%s is on alv_tree.CONVERTED' % ME)
ok(len(alv_tree.CONVERTED) >= CONVERTED_NOW,
   '  CONVERTED holds at least %d' % CONVERTED_NOW,
   len(alv_tree.CONVERTED))
ok(SUFFIX in ROUNDS and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_verbs'),
   '%s is in alv_rounds.ROUNDS, after VB-1' % SUFFIX, ROUNDS[-3:])
_ps1 = read(os.path.join(ROOT, PS1))
ok("'test_pdf_viewer.py'" in _ps1, 'the push script runs this suite')
ok(re.search(r'(?m)^code_only = alv_tree\.',
             read(os.path.join(ROOT, PATCHER))) is not None
   and re.search(r'(?m)^code_only = alv_tree\.',
                 read(os.path.join(ROOT, ME))) is not None,
   '  and both halves of this round alias the one stripper')

# ==========================================================================
head('WHAT THIS ROUND DOES NOT PROVE')
# ==========================================================================
dup = sorted(alv_tree.rel(p) for p in alv_tree.templates()
             if 'code.jquery.com' in read(p)
             and alv_tree.rel(p) != 'base.html')
ok(len(dup) == N_DUP_JQUERY,
   '%d page(s) load a SECOND jQuery over base\'s - counted, not fixed'
   % N_DUP_JQUERY, len(dup))
print('')
print('  Not that these two pages load the component\'s dependencies')
print('  once. base.html loads jquery-3.6.0 and so do %d pages,' % len(dup))
print('  asset_detail among them. Two jQuery instances on a page is a')
print('  real defect - a plugin bound to the first is invisible to the')
print('  second - and it is a round of its own, not a rider on this one.')
print('')
print('  Not that the shared viewer is right for every document in the')
print('  application. asset_detail keeps a separate photoViewerModal,')
print('  deliberately: a photo lightbox is not a document viewer, and')
print('  folding it in would be a decision nobody has taken.')
print('')
print('  Not that the drill-down should be scraping another page\'s HTML')
print('  at all. It fetches act_expense_view and lifts table.table out')
print('  of the response, which is also why the icons in it are black -')
print('  that table\'s colour rules live on the page it came from. That')
print('  is a finding of its own and Demetri has it on the record.')
print('')
print('=' * 74)
print(' %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
sys.exit(1 if failed else 0)
