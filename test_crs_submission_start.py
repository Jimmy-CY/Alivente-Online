# -*- coding: utf-8 -*-
"""test_crs_submission_start.py - Section X round X7, 28 Sep 2026.

Demetri: "The Add / Edit Country should comply to our standards. No Green
border, Create button should be teal."

X1 did the list and its view modal; X2 does the entry screen, and with it
Country Configurations is house end to end.

SECTION 1 IS THE GREEN BORDER, deleted for the reason X1 measured: a
house entry screen has no outer panel, so there is nothing there to
retone.

SECTION 2 IS THE CREATE BUTTON, WHICH DID NOT ONLY CHANGE COLOUR. The
house puts the primary in the bar at the TOP beside Back and has no
footer row. This page had Back alone at the top and a footer holding
Cancel AND Create Country - two controls going to the same place, which
is the defect test_save_and_cancel.py names. Doing only the colour would
have left the screen failing two suites and looking compliant.

SECTION 3 IS THE FORM COMPONENTS, which base has owned all along.

SECTION 4 IS WHAT IS KEPT AND WHY IT IS NOT A DEVIATION.

SECTION 5 RENDERS IT, at 1280 and 390, against a house entry screen.
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

SUFFIX = '.bak_crsstart'
ME = 'test_crs_submission_start.py'
PATCHER = 'apply_crs_submission_start.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = os.path.join(ROOT, 'crs', 'templates', 'crs', 'submission_start.html')
BASE = os.path.join(T, 'base.html')
# The control: a house entry screen that already passes every form suite.
HOUSE = os.path.join(T, 'finance_expense_types_add.html')
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
    return ' '.join(re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).split())


def nocmt(s):
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)


def sels(css):
    return [bare(m.group(1)) for m in RULE.finditer(css)]


def markup(t):
    """Scripts, styles AND COMMENTS out - the general form. Three gates
    in this section of the programme have now fired on prose a round
    wrote about itself: lesson 21 on a selector, X1's hex gate on a CSS
    comment naming the retired token, and X2's Cancel gate on the HTML
    comment explaining why Cancel was removed."""
    t = re.sub(r'<(script|style)\b.*?</\1>', '', t, flags=re.S | re.I)
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


def has_class(mk, name):
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
print('%s - X7, THE START SUBMISSION SCREEN' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE GREEN BORDER, DELETED RATHER THAN RETONED')
# ==========================================================================
ok('--crs-dark' in cw and '#28a745' in cw,
   'CONTROL: the page declared the module palette')
ok('.crs-panel' in sels(cw),
   '  and wrapped the whole form in a 3px border of it')
ok('--crs-' not in nocmt(pn), 'nothing reads a --crs-* token any more',
   re.findall(r'--crs-\w+', nocmt(pn))[:4])
ok('.crs-panel' not in sels(cn) and not has_class(mn, 'crs-panel'),
   '  and .crs-panel is gone, not retoned')
house_mk = markup(read(HOUSE))
ok('form-card' in house_mk and 'crs-panel' not in house_mk,
   '  CONTROL: measured, not assumed - the house entry screen has '
   '.form-card sections and no outer panel')
hexes_w = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', nocmt(cw))))
ok(len(hexes_w) == 7, 'CONTROL: the page carried %d hexes' % len(hexes_w),
   hexes_w)
ok(not re.findall(r'#[0-9a-fA-F]{3,8}\b', nocmt(cn)),
   '  and now carries none',
   sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', nocmt(cn)))))

# ==========================================================================
head('2. THE PRIMARY DID NOT ONLY CHANGE COLOUR - IT MOVED')
# ==========================================================================
ok('class="btn btn-success"' in mw,
   'CONTROL: Create Country was Bootstrap green in a footer row')
ok('.form-actions' in sels(cw),
   '  the footer row this page had, which the house does not')
ok('Cancel' in mw and mw.count("crs:submission_list") >= 2,
   '  and it offered Cancel AND Back, both going to the list - the '
   'defect test_save_and_cancel names')

ok('.form-actions' not in sels(cn) and not has_class(mn, 'form-actions'),
   'the footer row is gone')
ok('Cancel' not in mn, '  and so is Cancel - Back already is it')
ok(mn.count('<form method="post" novalidate') == 1,
   'there is exactly one form')
ok(mn.index('<form method="post"') < mn.index('page-action-buttons'),
   '  and it opens ABOVE the bar, which is what lets the primary be a '
   'submit - the one structural move in this round')
bar = mn[mn.index('<div class="page-action-buttons">'):]
bar = bar[:bar.index('</div>', bar.index('action-back'))]
ok('action-primary' in bar and 'action-back' in bar,
   '  the bar holds the primary and Back')
ok(bar.index('action-primary') < bar.index('action-back'),
   '  in that order')
ok('type="submit"' in bar, '  and the primary is a submit')
ok(not has_class(mn, 'btn-success') and not has_class(mn, 'btn-secondary'),
   'no Bootstrap colour class survives anywhere on the page')
hbar = house_mk[house_mk.index('<div class="page-action-buttons">'):]
hbar = hbar[:hbar.index('</div>', hbar.index('action-back'))]
ok('action-primary' in hbar and 'type="submit"' in hbar,
   'CONTROL: which is exactly how the house entry screen writes its bar')

# ==========================================================================
head('3. THE FORM COMPONENTS BASE HAS OWNED ALL ALONG')
# ==========================================================================
ok(mn.count('form-card') == 1, 'one .form-card section', mn.count('form-card'))
ok(mn.count('<h3 class="form-section-title">') == 1,
   '  titled with an h3, as the house writes it')
ok('.form-section-title' not in sels(cn),
   '  and the page no longer OVERRIDES base\'s own class')
over = [m.group(2) for m in RULE.finditer(cw)
        if bare(m.group(1)) == '.form-section-title']
ok(over and 'var(--crs-dark)' in over[0],
   '  CONTROL: it did, and it painted base\'s component green', over)
ok(mn.count('class="form-group"') == 2
   and mn.count('form-group form-group-full') == 3,
   '  five .form-group fields', [mn.count('class="form-group"'),
                                 mn.count('form-group form-group-full')])
ok(mn.count('alv-req') == 4, '  four required markers on .alv-req',
   mn.count('alv-req'))
ok(mn.count('class="form-text"') == 3, '  three help lines on .form-text',
   mn.count('class="form-text"'))
for gone in ('form-section', 'form-field', 'form-field-full', 'req',
             'field-help'):
    ok(not has_class(mn, gone), '  and .%s is gone' % gone)

# ==========================================================================
head('4. KEPT, AND WHY THAT IS NOT A DEVIATION')
# ==========================================================================
for k in ('.form-grid', '.form-group-full', '.field-error',
          '.form-section-note',
          '.nil-checkbox-label input[type="checkbox"]'):
    ok(k in sels(cn), '  KEPT: %s' % k)
grids = [alv_tree.rel(p) for p in alv_tree.templates()
         if 'form-card' in read(p)
         and re.search(r'\.form-(?:grid|row-2)\s*\{[^}]*grid-template-columns',
                       read(p))]
ok(len(grids) >= 9,
   '  .form-grid is a house convention base has not hoisted yet - %d other '
   'form pages already do exactly this' % len(grids), grids[:6])
ge = [m.group(2) for m in RULE.finditer(cn) if bare(m.group(1)) == '.form-grid']
ok(ge and '1fr 1fr' in ge[0] and '18px 22px' in ge[0],
   '  and it now says it the way finance_expense_add says it', ge)
fe = [m.group(2) for m in RULE.finditer(cn)
      if bare(m.group(1)) == '.field-error']
ok(fe and 'var(--alv-bad)' in fe[0],
   '  .field-error keeps its job and loses its hex', fe)

# ==========================================================================
head('5. RENDERED AT BOTH WIDTHS, AGAINST A HOUSE ENTRY SCREEN')
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
  const panel = document.querySelector('.crs-panel, .form-card');
  // FIND THE SUBMIT WHEREVER IT IS, then say where that was. The first
  // draft looked only inside .page-action-buttons and so found nothing
  // on the BEFORE page - where the primary sat in a footer row. That is
  // the round's whole point, and a probe that cannot see the old
  // position cannot measure the move.
  const prim = document.querySelector('[type=submit]');
  const grid = document.querySelector('.form-grid');
  const card = document.querySelector('.form-card');
  return {
    outer_bw: g(document.querySelector('.crs-panel'), 'borderTopWidth')
              || 'NO PANEL',
    outer_bc: g(document.querySelector('.crs-panel'), 'borderTopColor')
              || 'NO PANEL',
    primary_bg: g(prim, 'backgroundColor'),
    primary_txt: prim ? prim.textContent.trim().slice(0, 24) : null,
    primary_in_bar: !!(prim && prim.closest('.page-action-buttons')),
    footer_row: !!document.querySelector('.form-actions'),
    grid_cols: g(grid, 'gridTemplateColumns'),
    card_bg: (g(card, 'backgroundImage') || 'NO CARD').slice(0, 26),
    title_title: g(document.querySelector('.form-section-title'), 'color'),
  };
}"""

GREEN = 'rgb(40, 167, 69)'


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
        ok(b['outer_bw'] == '3px' and b['outer_bc'] == GREEN,
           '  CONTROL: the form sat in a 3px green border', b)
        ok(a['outer_bw'] == 'NO PANEL',
           '  and there is no outer panel at all now')
        ok(b['primary_bg'] == GREEN,
           '  CONTROL: the primary was Bootstrap green', b['primary_bg'])
        ok(b['footer_row'] and not b['primary_in_bar'],
           '  CONTROL: and it sat in a footer row, not in the bar', b)
        ok(a['primary_bg'] != GREEN and a['primary_bg'] is not None,
           '  and is now the house primary (%s)' % a['primary_bg'])
        ok(a['primary_in_bar'] and not a['footer_row'],
           '  IN THE BAR, with no footer row left - the move, not just '
           'the colour', a)
        ok(a['primary_txt'] and a['primary_txt'].startswith('Create'),
           '  and it is still the Create control (%s)' % a['primary_txt'])
        want = 1 if width == 390 else 2
        ok(len((a['grid_cols'] or '').split()) == want,
           '  the grid is %d column(s) at %dpx' % (want, width),
           a['grid_cols'])
    a = measure(pn, 1280, 'after')
    h = measure(read(HOUSE), 1280, 'house')
    ok(a['card_bg'] == h['card_bg'],
       'CONTROL: the section cards paint exactly as the house entry '
       'screen\'s do', {'crs': a['card_bg'], 'house': h['card_bg']})
    ok(a['title_title'] == h['title_title'],
       '  and so do the section titles, which used to be green',
       {'crs': a['title_title'], 'house': h['title_title']})

# ==========================================================================
head('6. THE HEADING, AND WHAT THE ROUND LEFT ALONE')
# ==========================================================================
ok('ALIVENTE ONLINE -' in mw and 'ALIVENTE ONLINE -' not in mn,
   'the title drops the brand prefix')
for h6 in re.findall(r'<h[1-6]\b[^>]*>.*?</h[1-6]>', mn, re.S):
    ok('<center>' not in h6, '  and no heading wraps itself in <center>',
       ' '.join(h6.split())[:60])
ok(mn.count('page-subtitle-h4') == 1,
   '  and it gains the subtitle every house entry screen carries')
ok(mn.count('<center>') == 1,
   'the message block keeps its <center> - that is the message-bar round',
   mn.count('<center>'))
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
ok(markup('<p>a</p><!-- Cancel --><p>b</p>') == '<p>a</p><p>b</p>',
   'the markup reader strips HTML COMMENTS - X2\'s Cancel gate fired on '
   'the comment this round writes explaining why Cancel went')
ok(bare('/* x */ .form-grid') == '.form-grid',
   '  and the selector reader strips CSS comments (lesson 21)')
ok('--crs-dark' in nocmt(pw_),
   'reverting the page brings the palette back, so section 1 would FAIL - '
   'a revert is caught')

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
if ROUNDS and SUFFIX in ROUNDS and '.bak_crssub' in ROUNDS:
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_crssub'),
       '  and after the round before it (lesson 54)', ROUNDS[-3:])
ps1 = read(os.path.join(ROOT, PS1)) if os.path.isfile(PS1) else ''
ok(ME in ps1, '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NEXT: Reporting Financial Institutions - fi_list.html and')
print('  fi_form.html, which are the same two shapes again. Then')
print('  Submissions, which is three pages and the biggest of them.')
print('=' * 74)
sys.exit(1 if failed else 0)
