# -*- coding: utf-8 -*-
"""test_crs_fi_list.py - Section X round X3, 28 Sep 2026.

Demetri, having listed the Country Configurations defects: "All of the
above need to apply for the Reporting Financial Institutions."

They do, almost literally. Measured against country_list.html as X1 found
it, fi_list.html declared the SAME rules with eight additions - so this
round is X1 again, plus the four things that are genuinely this page's
own: the IN count badge, and three pieces of furniture inside the view
modal.

SECTION 3a IS THE ONE REAL DECISION - the count badge, and why it takes
-info and -neutral rather than -good.

SECTION 1 IS THE GREEN, GONE. Measured in a browser, before and after,
at 1280 and 390.

SECTION 2 IS THE HELP BUTTON, and the reason it was the only green
control in a bar where Back carried the same Bootstrap class.

SECTION 3 IS THE TABLE - the house component, with a phone card layout
that comes from base rather than from five hand-numbered nth-child rules.

SECTION 4 IS THE MODAL.

SECTION 5 IS WHAT THE ROUND LEFT ALONE, AND WHY. A round that cannot say
what it did not do is a round that will be blamed for it later.
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
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_crsfi'
ME = 'test_crs_fi_list.py'
PATCHER = 'apply_crs_fi_list.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = os.path.join(ROOT, 'crs', 'templates', 'crs', 'fi_list.html')
BASE = os.path.join(T, 'base.html')
HOUSE = os.path.join(T, 'suppliers.html')   # the control: a house list page
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'

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
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')
MODAL_IF = re.compile(
    r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)
TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)


def bare(s):
    """Lesson 21 - strip CSS comments before ANY selector comparison."""
    return ' '.join(re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).split())


def nocmt(s):
    """The same, for a body or a whole file. X1's own patcher failed its
    first hex gate on the explanatory comment it had just written."""
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)


def sels(css):
    return [bare(m.group(1)) for m in RULE.finditer(css)]


def markup(t):
    return re.sub(r'<(script|style)\b.*?</\1>', '', t, flags=re.S | re.I)


def has_class(mk, name):
    """A whole class token, not a substring. `action-icon` is inside
    `mobile-action-icon`, and the patcher's first gate fell for it."""
    return bool(re.search(r'(?<![\w-])' + re.escape(name) + r'(?![\w-])', mk))


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)), flags=re.S)
            for m in STYLE.finditer(t)]


def one_branch(t):
    while True:
        stack = []
        for m in TAG.finditer(t):
            k = m.group(1)
            if k == 'if':
                stack.append([m.start(), m.end(), None])
            elif k in ('elif', 'else'):
                if stack and stack[-1][2] is None:
                    stack[-1][2] = m.start()
            elif k == 'endif':
                if not stack:
                    return t
                s, fe, cut = stack.pop()
                if cut is not None:
                    t = t[:s] + t[fe:cut] + t[m.end():]
                    break
        else:
            return t


def body_of(t):
    t = one_branch(t)
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
        b = re.sub(rx, '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'AT', b, flags=re.S)


pn, pw_ = now(PAGE), was(PAGE)
cn = '\n'.join(STYLE.findall(pn))
cw = '\n'.join(STYLE.findall(pw_))
mn, mw = markup(pn), markup(pw_)

print('=' * 74)
print('%s - X3, REPORTING FINANCIAL INSTITUTIONS - THE LIST' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE GREEN IS GONE, AND SO IS THE LOCAL PALETTE')
# ==========================================================================
ok('--crs-dark' in cw and '--crs-light' in cw,
   'CONTROL: the page DID declare its own palette - #28a745 and #d4edda')
ok('--crs-' not in nocmt(pn),
   '  and nothing in it reads a --crs-* token any more',
   re.findall(r'--crs-\w+', nocmt(pn))[:4])
ok(':root' not in sels(cn), '  the :root block that held them is gone')

hexes_w = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', nocmt(cw))))
hexes_n = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', nocmt(cn))))
ok(len(hexes_w) == 11, 'CONTROL: the page carried %d hexes' % len(hexes_w),
   hexes_w)
ok(not hexes_n, '  and now carries none at all', hexes_n)
kw = re.findall(r'(?:^|[;{])\s*(?:colou?r|background(?:-color)?|border'
                r'(?:-\w+)?-colou?r)\s*:\s*(white|black|red|green|blue|grey|'
                r'gray)\b', nocmt(cn), re.I)
ok(not kw, '  and no colour KEYWORD either, which a hex audit cannot see',
   kw)

# The panel is not retoned. It is gone.
ok('.crs-panel' in sels(cw) and '.crs-panel-container' in sels(cw),
   'CONTROL: the page wrapped everything in .crs-panel - a 3px border and '
   'a tinted fill')
ok('.crs-panel' not in sels(cn) and not has_class(mn, 'crs-panel'),
   '  and it is DELETED, not retoned - a house list page has no outer '
   'panel at all')
house_mk = markup(read(HOUSE))
ok('table-container' in house_mk and 'alv-card' not in house_mk,
   '  CONTROL: which is measured, not assumed - suppliers.html has a '
   '.table-container and no card around it')

# ==========================================================================
head('2. THE HELP BUTTON, AND WHY IT ALONE WAS GREEN')
# ==========================================================================
ok('action-icon' in mw,
   'CONTROL: Help carried `action-icon`, a class base has NEVER owned')
base_css = read(BASE)
ok(not has_class(base_css, 'action-icon'),
   '  base really has no such class - it owns .icon-action-btn and '
   '.mobile-action-icon, and neither is that name')
ok('btn-success' in mw and 'action-back' in mw,
   '  CONTROL: Back carried btn-success too, and rendered correctly - '
   'because .action-back IS base\'s, and base is read after Bootstrap')
ok(not has_class(mn, 'btn-success') and not has_class(mn, 'action-icon'),
   'neither survives')
ok('btn action-secondary' in mn,
   '  and Help is now the house Help button')
house_help = [p for p in alv_tree.templates()
              if 'aria-label="Help"' in markup(read(p))]
ok(len(house_help) >= 3,
   '  which is how the %d pages with a Help control write it'
   % len(house_help),
   [alv_tree.rel(p) for p in house_help])
ok(not has_class(mn, 'btn-info'),
   '  and Add Country drops the redundant btn-info - it already carried '
   '.action-primary, so the teal was arriving twice')

# ==========================================================================
head('3. THE TABLE IS THE HOUSE TABLE')
# ==========================================================================
ok(mn.count('class="table alv-table crs-fi-table"') == 1,
   'the table wears .alv-table')
ok(mn.count('<div class="table-container">') == 1,
   '  inside exactly one .table-container')
labels = re.findall(r'data-label="([^"]+)"', mn)
ok(labels == ['Name', 'Residence', 'INs', 'Status', 'Last Updated'],
   '  and every cell carries a data-label, in column order', labels)
nth = [s for s in sels(cw) if 'nth-child' in s and '::before' in s]
ok(len(nth) == 5,
   'CONTROL: the page hand-numbered %d ::before rules to label those same '
   'columns on a phone' % len(nth), nth)
ok(not [s for s in sels(cn) if 'nth-child' in s],
   '  and not one survives - base reads the attribute, so inserting a '
   'column can no longer mislabel every column after it')
ok(mn.count('class="desktop-action-cell cell-actions"') == 2,
   '  the actions column is marked on the header cell and the body cell')
ok(mn.count('class="mobile-action-bar"') == 1,
   '  and the phone gets a real action bar, which this page never had')
for icon in ('icon-view', 'icon-edit', 'icon-delete'):
    ok('icon-action-btn %s' % icon in mn, '  row action: %s' % icon)
ok(not has_class(mn, 'action-btn') and not has_class(mn, 'btn-view'),
   '  and the three hand-rolled squares are gone')
ok('alv-pill alv-pill-good' in mn and 'alv-pill alv-pill-neutral' in mn,
   'Active / Inactive are .alv-pill, not coloured text')
ok(not has_class(mn, 'status-active'),
   '  and .status-active, which wrote #28a745 directly, is gone')
ok(mn.count('alv-empty') >= 3,
   'the empty state is base\'s .alv-empty with a title and a hint')
ok(not has_class(mn, 'crs-empty'), '  and .crs-empty is gone')

# ==========================================================================
head('3a. THE IN COUNT BADGE - A COUNT IS NOT A HEALTH READING')
# ==========================================================================
ok('.in-count' in sels(cw),
   'CONTROL: the count was a solid badge painted from --crs-dark')
ok('.in-count-empty' in sels(cw),
   '  repainted grey at 60%% opacity when the count was zero')
ok('.in-count' not in sels(cn) and not has_class(mn, 'in-count'),
   'both are gone, and the cell takes base\'s own pill')
ins = mn[mn.index('data-label="INs"'):mn.index('data-label="Status"')]
ok('alv-pill alv-pill-info' in ins,
   '  a non-zero count is .alv-pill-info - standard 3.1 calls --alv-info '
   'informational, neutral emphasis, which is what a count in a table is')
ok('alv-pill-neutral' in ins, '  and a zero count is -neutral')
ok('alv-pill-good' not in ins and 'alv-pill-bad' not in ins,
   '  and NEITHER is a health tone. -good on a non-zero count would make '
   'that colour mean two things at once, which is the thing 3.1 forbids',
   ins.strip()[:90])
st = mn[mn.index('data-label="Status"'):mn.index('data-label="Last Updated"')]
ok('alv-pill-good' in st,
   '  while Status, which IS a health reading, keeps -good - so the two '
   'pills in one row read as one family rather than two inventions')

# ==========================================================================
head('4. THE VIEW MODAL')
# ==========================================================================
ok('bg-info' in mw, 'CONTROL: the header was painted with Bootstrap bg-info')
ok('modal-header alv-modal-head' in mn,
   '  and now wears base\'s .alv-modal-head')
ok(not has_class(mn, 'bg-info'), '  with no Bootstrap colour class left')
ok('btn action-secondary" data-dismiss="modal">Close' in mn,
   '  and Close is the house secondary')
ok(mn.count('view-ins-table') >= 1,
   '  the nested IN table is still there, under its own name')
for k in ('.view-row', '.view-row label', '.view-section-h',
          '.view-block', '.view-empty', '.view-ins-table'):
    ok(k in sels(cn), '  KEPT: %s - base does not own it' % k)
ok('.view-ins-table' in sels(cn) and 'alv-table' not in
   ' '.join(s for s in sels(cn) if 'view-ins' in s),
   '  and the nested IN table is NOT .alv-table, deliberately - base\'s '
   'table carries a phone card layout, a row-action grammar and a sticky '
   'head, none of which a three-row list inside a dialog wants')
for s in ('.view-block', '.view-empty', '.view-ins-table th',
          '.view-ins-table td'):
    body = [m.group(2) for m in RULE.finditer(cn) if bare(m.group(1)) == s]
    ok(body and not re.findall(r'#[0-9a-fA-F]{3,8}\b', body[0]),
       '  %s carries no hex' % s, body)
sec = [m.group(2) for m in RULE.finditer(cn)
       if bare(m.group(1)) == '.view-section-h']
ok(sec and 'var(--alv-accent)' in sec[0],
   '  .view-section-h takes the house accent, not --crs-dark', sec)

# ==========================================================================
head('5. RENDERED, BEFORE AND AFTER, AT BOTH WIDTHS')
# ==========================================================================
try:
    import playwright  # noqa: F401
    HAVE = True
except Exception:
    HAVE = False

boot = read(BOOT) if os.path.isfile(BOOT) else ''
base_t = read(BASE)


def fixture(page_text):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>%s</head>'
            '<body class="has-sidebar"><div class="main-content '
            'with-sidebar">%s</div></body></html>'
            % (boot, '\n'.join(styles_of(base_t)),
               ''.join('<style>%s</style>' % c for c in styles_of(page_text)),
               body_of(page_text)))


PROBE = """() => {
  const g = (el, p) => el ? getComputedStyle(el)[p] : null;
  const vis = e => !!(e && e.offsetParent !== null
                      && e.getBoundingClientRect().height > 0);
  const help = [...document.querySelectorAll('button,a')].find(
      e => (e.getAttribute('aria-label')||'') === 'Help');
  const panel = document.querySelector('.crs-panel, .table-container');
  const st = document.querySelector('.status-active, .alv-pill');
  const mh = document.querySelector('.modal-header');
  return {
    help_bg: g(help, 'backgroundColor'),
    panel_bw: g(panel, 'borderTopWidth'),
    panel_border: g(panel, 'borderTopColor'),
    status_color: g(st, 'color'),
    modal_solid: g(mh, 'backgroundColor'),
    modal_grad: (g(mh, 'backgroundImage') || 'none').slice(0, 30),
    desktop_cell: vis(document.querySelector('td.desktop-action-cell')),
    mobile_bar: vis(document.querySelector('.mobile-action-bar')),
  };
}"""

GREEN = 'rgb(40, 167, 69)'
PALE_GREEN = 'rgb(212, 237, 218)'


def measure(text, width, tag):
    from playwright.sync_api import sync_playwright
    fx = os.path.join(SCRATCH, '%s_%d.html' % (tag, width))
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write(fixture(text))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': width, 'height': 1000})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        _goto(pg, fx)
        out = pg.evaluate(PROBE)
        br.close()
    return out


if not HAVE:
    skip('the rendered probe', 'playwright is not installed')
else:
    for width in (1280, 390):
        b = measure(pw_, width, 'before')
        a = measure(pn, width, 'after')
        print('  -- %dpx' % width)
        ok(b['help_bg'] == GREEN,
           '  CONTROL: Help was Bootstrap green %s' % GREEN, b['help_bg'])
        ok(a['help_bg'] != GREEN,
           '  and is not any more (%s)' % a['help_bg'])
        ok(b['panel_bw'] == '3px' and b['panel_border'] == GREEN,
           '  CONTROL: the panel had a 3px green border', b)
        ok(a['panel_bw'] == '0px',
           '  and there is no border at all now', a['panel_bw'])
        ok(b['status_color'] == GREEN,
           '  CONTROL: Active was green text', b['status_color'])
        ok(a['status_color'] != GREEN and a['status_color'] is not None,
           '  and is now the house good ink (%s)' % a['status_color'])
        ok('linear-gradient' in a['modal_grad'],
           '  the modal header is base\'s gradient', a['modal_grad'])
        ok(a['desktop_cell'] is (width == 1280),
           '  the desktop action cell is %s'
           % ('shown' if width == 1280 else 'hidden'))
        ok(a['mobile_bar'] is (width == 390),
           '  and the phone action bar is %s'
           % ('shown' if width == 390 else 'hidden'))

    # THE CONTROL THAT MATTERS: the CRS page must now behave like a house
    # list page, not merely differently from how it used to.
    h = measure(read(HOUSE), 390, 'house')
    a = measure(pn, 390, 'after')
    ok(h['mobile_bar'] == a['mobile_bar']
       and h['desktop_cell'] == a['desktop_cell'],
       'CONTROL: at 390px the CRS table now behaves exactly as '
       'suppliers.html does - bar shown, desktop cell hidden',
       {'suppliers': h, 'crs': a})

# ==========================================================================
head('6. WHAT THIS ROUND LEFT ALONE, AND WHY')
# ==========================================================================
ok(mn.count('<center>') == 1,
   'the message block keeps its <center> - that is the message-bar round, '
   'which is system-wide and has a settings.py precondition',
   mn.count('<center>'))
for h6 in re.findall(r'<h[1-6]\b[^>]*>.*?</h[1-6]>', mn, re.S):
    ok('<center>' not in h6,
       '  but no HEADING wraps itself in one any more',
       ' '.join(h6.split())[:60])
ok('ALIVENTE ONLINE -' in mw and 'ALIVENTE ONLINE -' not in mn,
   '  and the title drops the brand prefix')
# ASSERTED AGAINST A REGISTER, NOT A NUMBER. The first draft of this
# check counted: "the other 7 CRS pages still carry the local palette". X2
# made it 6 and this suite failed - correctly by its own words, and
# uselessly, because nothing it guards had regressed. alv_tree.CRS_HOUSE
# is the list of CRS pages that have had their round; a round that
# finishes a page adds itself there and no suite needs editing.
green = [n for n in alv_tree.crs_pages()
         if '--crs-dark' in nocmt(read(os.path.join(
             ROOT, 'crs', 'templates', n)))]
ok(sorted(green) == sorted(alv_tree.crs_outstanding()),
   'exactly the CRS pages that have NOT had their round still carry the '
   'local palette - %d of %d' % (len(green), len(alv_tree.crs_pages())),
   {'still green': green, 'expected': alv_tree.crs_outstanding()})
ok(all(n not in green for n in alv_tree.CRS_HOUSE),
   '  and every page the register calls done really is',
   [n for n in alv_tree.CRS_HOUSE if n in green])
print('')
print('  CRS PAGES STILL TO DO - %d:' % len(alv_tree.crs_outstanding()))
for n in alv_tree.crs_outstanding():
    print('     %s' % n)

# ==========================================================================
head('7. CONTROLS, AND THE GATE')
# ==========================================================================
ok(bare('/* banner */ .view-code') == '.view-code',
   'the selector reader strips a comment banner (lesson 21)')
ok(has_class('class="mobile-action-icon"', 'mobile-action-icon')
   and not has_class('class="mobile-action-icon"', 'action-icon'),
   '  and a class test does not fire on a longer name that contains it - '
   'the patcher\'s first gate read action-icon inside mobile-action-icon')
ok('--crs-dark' in nocmt(pw_),
   'reverting the page brings the palette back, so section 1 would FAIL - '
   'a revert is caught')

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
if ROUNDS and SUFFIX in ROUNDS and '.bak_crsform' in ROUNDS:
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_crsform'),
       '  and after the round before it (lesson 54)', ROUNDS[-3:])
ps1 = read(os.path.join(ROOT, PS1)) if os.path.isfile(PS1) else ''
ok(ME in ps1, '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)
ok(PAGE in alv_tree.templates(),
   'and X0 is why this suite can see the page at all - it is one of the '
   '%d templates alv_tree walks' % len(alv_tree.templates()))

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NEXT: fi_form.html - the Add / Edit Reporting FI screen, which')
print('  is country_form again PLUS an inline formset of identification')
print('  numbers: twenty more rules, its own nth-child phone labels, and')
print('  a compound .in-cell .form-control that duplicates base. Then')
print('  Submissions, which is three pages and the biggest of them.')
print('=' * 74)
sys.exit(1 if failed else 0)
