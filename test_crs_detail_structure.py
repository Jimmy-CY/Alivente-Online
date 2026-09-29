# -*- coding: utf-8 -*-
"""test_crs_detail_structure.py - Section X round X9, 29 Sep 2026.

X8 changed everything you could see on this page and nothing
structural. X9 takes the two structural clusters: the eight section cards
with the form inside them, and the four validation tables.

SECTION 1 IS NOT A STYLING CHANGE. The validation table overflowed on a
phone and was CLIPPED, not scrollable - so the Fix column, which is where
a draft submission gets corrected, was unreachable. Demetri's standing
rule is that every Add/Edit screen must work on a phone. This suite
measures it at 390px before and after.

SECTION 2 is the section cards and the form.

SECTION 3 is .form-actions, which this round KEEPS and three rounds
deleted - for a structural reason, not a change of mind.

SECTION 4 is the retone, including four colour KEYWORDS that a hex audit
cannot see.

SECTION 5 is what is left for X10.
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

SUFFIX = '.bak_crsdets'
ME = 'test_crs_detail_structure.py'
PATCHER = 'apply_crs_detail_structure.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = os.path.join(ROOT, 'crs', 'templates', 'crs', 'submission_detail.html')
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


def rule(css, sel):
    return [m.group(2) for m in RULE.finditer(css) if bare(m.group(1)) == sel]


print('=' * 74)
print('%s - X9, SUBMISSION DETAIL: SECTIONS, FORM, TABLES' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE PHONE FIX - THIS ONE IS NOT ABOUT LOOKS')
# ==========================================================================
ok('validation-table' in mw, 'CONTROL: the page has a validation table')
ok(not re.search(r'@media[^{]*\{[^}]*validation-table', cw, re.S)
   and 'validation-table' not in cw.split('@media')[-1],
   '  and its phone block never mentioned it - there was no phone '
   'handling at all')
ok('class="table alv-table validation-table"' in mn,
   'all four tables now wear base\'s .alv-table',
   mn.count('class="table alv-table validation-table"'))
ok(mn.count('class="table alv-table validation-table"') == 4,
   '  all FOUR of them')

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
  const t = document.querySelector('.validation-table');
  if (!t) return null;
  const r = t.getBoundingClientRect();
  const td = t.querySelector('tbody td');
  const th = t.querySelector('thead');
  return {
    w: Math.round(r.width),
    viewport: window.innerWidth,
    overflows: Math.round(r.right) > window.innerWidth,
    thead: th ? getComputedStyle(th).display : '-',
    td: td ? getComputedStyle(td).display : '-',
    label: td ? getComputedStyle(td, '::before').content : '-',
  };
}"""


def measure(text_, width, tag):
    from playwright.sync_api import sync_playwright
    fx = os.path.join(SCRATCH, '%s_%d.html' % (tag, width))
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write(fixture(text_))
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
    b390, a390 = measure(pw_, 390, 'b'), measure(pn, 390, 'a')
    ok(b390 and b390['overflows'],
       'CONTROL: at 390px the table was %dpx wide in a %dpx viewport, and '
       'OVERFLOWED' % (b390['w'], b390['viewport']), b390)
    ok(a390 and not a390['overflows'],
       '  and now fits: %dpx in %dpx' % (a390['w'], a390['viewport']), a390)
    ok(a390 and a390['td'] == 'block' and a390['thead'] == 'none',
       '  because base turns the rows into cards and hides the head', a390)
    ok(b390 and b390['td'] == 'table-cell' and b390['thead'] != 'none',
       '  CONTROL: before, it was still a five-column table', b390)
    b12, a12 = measure(pw_, 1280, 'b'), measure(pn, 1280, 'a')
    ok(a12 and a12['td'] == 'table-cell' and not a12['overflows'],
       '  and at 1280px it is still a table, and still fits', a12)
    ok(abs(a12['w'] - b12['w']) < 40,
       '  at a width within 40px of before (%d -> %d) - the desktop did '
       'not move' % (b12['w'], a12['w']))

# EVERY CELL LABELLED, AND AGAINST THE RIGHT COLUMN.
labels = re.findall(r'<td[^>]*data-label="([^"]+)"', mn)
ok(len(labels) == 19, '19 cells carry a data-label', len(labels))
bad = []
for tb in re.finditer(r'<table class="table alv-table validation-table">'
                      r'(.*?)</table>', mn, re.S):
    seg = tb.group(1)
    ths = [' '.join(re.sub(r'<[^>]+>', '', x).split())
           for x in re.findall(r'<th>.*?</th>', seg, re.S)]
    tds = re.findall(r'<td[^>]*data-label="([^"]+)"', seg)
    if tds != ths:
        bad.append((ths, tds))
ok(not bad,
   '  and each table\'s labels match its own headers, column for column - '
   'FOUR tables with four DIFFERENT column sets, which the first draft of '
   'the round assumed were two identical ones and was refused for', bad)

# ==========================================================================
head('2. THE SECTIONS WERE .form-card UNDER ANOTHER NAME')
# ==========================================================================
ok('.detail-section' in sels(cw) and '.detail-section-title' in sels(cw),
   'CONTROL: the page had its own section card and title')
prev = rule(cw, '.detail-section-title')
ok(prev and 'var(--crs-dark)' in prev[0],
   '  and the title was painted from the module alias', prev)
ok('.detail-section' not in sels(cn)
   and '.detail-section-title' not in sels(cn),
   'both are gone')
ok(mn.count('form-card') == 8, '  eight .form-card sections',
   mn.count('form-card'))
ok(mn.count('<h3 class="form-section-title">') == 8,
   '  each titled with an h3, as the house writes it')
ok(mn.count('class="form-group"') == 5
   and mn.count('form-group form-group-full') == 1,
   '  six .form-group fields', [mn.count('class="form-group"'),
                                mn.count('form-group form-group-full')])
ok(mn.count('alv-req') == 5, '  five required markers on .alv-req')
ok(mn.count('class="form-text"') == 14, '  fourteen help lines')
ok('.form-group-full' in sels(cn),
   '  and the grid-span rule was RENAMED, not deleted - base owns no such '
   'class, so deleting it would have left the field un-spanned')

# THE COMPOUND RULE, FOR THE SECOND TIME.
ok('.form-field .form-control' in sels(cw),
   'CONTROL: a COMPOUND RULE duplicated base\'s .form-control - the same '
   'rule X4 found on fi_form')
old = rule(cw, '.form-field .form-control')
ok(old and '1px solid #ced4da' in ' '.join(old[0].split()),
   '  with a 1px hex border where base sets 2px of --alv-line', old)
ok('.form-field .form-control' not in sels(cn),
   '  and it is DELETED, not retoned. Two pages carried it; '
   'test_compound_rules.py was waiting on both')
for gone in ('detail-section', 'form-field', 'req', 'field-help'):
    ok(not has_class(mn, gone), '  and .%s is gone from the markup' % gone)

# ==========================================================================
head('3. .form-actions IS KEPT - AND THREE ROUNDS DELETED ONE')
# ==========================================================================
ok('.form-actions' in sels(cn),
   'the per-section submit row stays')
forms = mn.count('<form method="post"')
ok(forms >= 3,
   '  because this page is eight sections holding %d separate forms, not '
   'one entry screen' % forms, forms)
ok(mn.count('page-action-buttons') == 1,
   '  there is one page bar, and it holds Help and Back - no single '
   'primary to lift into it')
for other in ('country_form.html', 'fi_form.html', 'submission_start.html'):
    p = os.path.join(ROOT, 'crs', 'templates', 'crs', other)
    ok('.form-actions' not in sels('\n'.join(STYLE.findall(read(p)))),
       '  CONTROL: %-22s has none - it is ONE form, so the house lifts '
       'its primary into the bar' % other)
fa = rule(cn, '.form-actions')
ok(fa and not re.findall(r'#[0-9a-fA-F]{3,8}\b', fa[0]),
   '  and the kept rule carries no hex', fa)

# ==========================================================================
head('4. THE RETONE, INCLUDING FOUR KEYWORDS A HEX AUDIT CANNOT SEE')
# ==========================================================================
# SCOPE IS READ OUT OF THE PATCHER, NOT IMPORTED FROM IT. A patcher is a
# SCRIPT: importing one to borrow a list executes the whole round, which
# is how X0 came to print its summary in the middle of a suite's run.
# Parsing the literal costs three lines and cannot do that.
_src = read(os.path.join(ROOT, PATCHER))
# THE CLOSING BRACKET IS THE ONE AT THE START OF A LINE, not the first
# one after `SCOPE = [`. X10's scope contains
# `.excel-upload-row input[type="file"]`, so a search for the first `]`
# stops INSIDE a selector and the list comes back seven items long
# instead of thirty-six. X9's copy of this parse survived only because
# none of its selectors happened to contain a bracket.
_i = _src.index('SCOPE = [')
SCOPE = re.findall(r"'([^']+)'", _src[_src.index('[', _i):
                                      _src.index('\n]', _i)])
ok(len(SCOPE) >= 15, 'this round owns %d named rules' % len(SCOPE), SCOPE[:4])
ok(all(s.startswith('.') for s in SCOPE),
   '  and the list parsed cleanly out of the patcher source rather than '
   'being imported from it - importing a patcher runs the round')
dirty = []
for sel in SCOPE:
    b = rule(cn, sel)
    if not b:
        dirty.append((sel, 'VANISHED'))
        continue
    h = re.findall(r'#[0-9a-fA-F]{3,8}\b', b[0])
    k = re.findall(r'(?:^|[;{])\s*(?:colou?r|background(?:-color)?)\s*:\s*'
                   r'(white|black|red|green|blue|grey|gray)\b', b[0], re.I)
    if h or k or 'var(--crs-' in b[0]:
        dirty.append((sel, h + k + (['alias'] if 'var(--crs-' in b[0]
                                    else [])))
ok(not dirty, '  and every one of them is clean - no hex, no keyword, no '
   'module alias', dirty)

kw_w = [bare(m.group(1)) for m in RULE.finditer(cw)
        if re.search(r'(?:^|[;{])\s*(?:colou?r|background(?:-color)?)\s*:'
                     r'\s*white\b', m.group(2), re.I)]
kw_n = [bare(m.group(1)) for m in RULE.finditer(cn)
        if re.search(r'(?:^|[;{])\s*(?:colou?r|background(?:-color)?)\s*:'
                     r'\s*white\b', m.group(2), re.I)]
ok(len(kw_w) > len(kw_n),
   'CONTROL: %d rules painted with the KEYWORD white; %d remain, and the '
   'ones that went were this round\'s' % (len(kw_w), len(kw_n)),
   {'before': kw_w, 'after': kw_n})
ok(len(kw_n) > 0,
   '  the rest are in the Excel, XML and lifecycle clusters - X10. '
   'Standard 3.1 names keywords because a hex-based audit cannot see '
   'them at all', kw_n)
for sel, tok in (('.row-error td', 'var(--alv-bad-soft)'),
                 ('.row-correction td', 'var(--alv-warn-soft)')):
    b = rule(cn, sel)
    ok(b and tok in b[0],
       '  %-20s -> %s, the token that already means what the row means'
       % (sel, tok), b)

# ==========================================================================
head('5. WHAT IS LEFT FOR X10')
# ==========================================================================
ok('--crs-' in nocmt(pn),
   'the --crs-* alias SURVIVES - X8 retoned it rather than deleting it, '
   'because readers remain')
left = len(re.findall(r'var\(--crs-', pn))
ok(left >= 4,
   '  %d reader(s) left, all in the lifecycle, Excel and XML clusters '
   'that X10 owns' % left, left)
for keep in ('.lifecycle-event', '.excel-current, .xml-current',
             '.xml-modal-header'):
    ok(keep in sels(cn), '  KEPT for X10: %s' % keep)
rest = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', nocmt(cn))))
was = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', nocmt(cw))))
ok(len(rest) < len(was),
   '  distinct hexes fell from %d to %d' % (len(was), len(rest)))
ok(len(rest) > 0, '  and are not zero - X10 finishes the page', rest)
# NOT AN ASSERTION ABOUT THE REGISTER. The first draft read
# crs_outstanding() live and required this page to be in it - true when
# X9 was written, false the moment X10 landed and emptied it. Exactly
# the shape of X1's count breaking when X2 arrived. A suite asserts what
# ITS OWN round guarantees; the register belongs to whichever round is
# last. What X9 guarantees is that it left work behind, and `now()`
# reads the page as X9 left it, so that stays true forever.
ok('--crs-' in nocmt(pn) and left >= 4,
   '  and X9 left the page unfinished on purpose - %d alias reader(s) '
   'still in the clusters X10 owns' % left)

# ==========================================================================
head('6. CONTROLS, AND THE GATE')
# ==========================================================================
ok(bare('/* banner */ .fix-btn') == '.fix-btn',
   'the selector reader strips a comment banner (lesson 21)')
broken = [' '.join(c.split())[:60] for c in re.findall(r'/\*.*?\*/', cn, re.S)
          if '{' in c or '}' in c]
ok(not broken, '  and no CSS comment carries a brace', broken)
ok('.detail-section' in sels(cw),
   'reverting the page puts its own section card back, so section 2 would '
   'FAIL - a revert is caught')

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
if ROUNDS and SUFFIX in ROUNDS and '.bak_crsdetc' in ROUNDS:
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_crsdetc'),
       '  and after X8, which it depends on (lesson 54)', ROUNDS[-3:])
ps1 = read(os.path.join(ROOT, PS1)) if os.path.isfile(PS1) else ''
ok(ME in ps1, '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NEXT: X10 - the lifecycle timeline, the Excel panel and the XML')
print('  modal. It deletes the --crs-* alias for good, clears the last')
print('  colour keywords, and adds submission_detail to CRS_HOUSE. That')
print('  finishes the module, and the WAITING register in alv_tree.py')
print('  starts coming down.')
print('=' * 74)
sys.exit(1 if failed else 0)
