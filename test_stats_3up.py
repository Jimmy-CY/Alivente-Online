# -*- coding: utf-8 -*-
"""test_stats_3up.py - Section P round P5, 1 Oct 2026.

Demetri, on the Task List: "Can we fit Total Tasks, Completed and
Pending in one line, in smaller boxes (for the mobile)."

base takes every stats strip to two columns below 768px, so a strip of
three reads 2 + 1. .alv-stats.is-3up opts a strip of THREE into three
across, and tightens the padding and the type with it.

WHY THE TYPE HAD TO MOVE TOO, measured rather than assumed. Three across
at base's existing phone sizes holds its label at 386px and wraps below
it - and 360 is an ordinary Android width:

    width   3-up at base sizes      3-up tightened
    320     label 37px (two lines)  16px
    360     label 37px (two lines)  16px
    386     label 19px              16px

AND WHY overflow-wrap IS IN THERE. This page has a Greek switch, and the
Greek labels are long single words. Measured before it was added, with
the Greek branch rendered: the label SPILLED OUT of its 83px box at 320
and 360. The backup spilled at 320 already, so this round both fixes
that and stops itself from spreading it to 360.

SECTION 3 MEASURES BOTH LANGUAGES. A fixture that resolves {% if %} to
one branch picks a language, and this page's English and Greek labels
are different lengths - "Total Tasks" against
"Συνολικές Εργασίες". Measuring one and reporting it as the page is the
mistake this suite exists not to make.

SECTION 5 IS THE RISK. The opt-in sits in base, and fsr has FIVE stats
and tenant_payment_days four. Three of fsr's would be 77px wide. So the
suite checks that nothing with a different count wears the class, and
that fsr is still two-up.
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


def _goto(pg, path):
    try:
        pg.goto('file://' + path)
    except Exception as e:
        print('  !! the browser could not open %s: %s' % (path, e))
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)
try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS = []
    as_left_by = None

SUFFIX = '.bak_stats3up'
ME = 'test_stats_3up.py'
PATCHER = 'apply_stats_3up.py'
PS1 = 'Push-PendingChanges.ps1'
REL = 'projects/project_task_list.html'
EXE = '/opt/pw-browsers/chromium'
BOOT = 'test_fixture_bootstrap413.css'
WIDTHS = (320, 360, 386, 414)
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)

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
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def css_of(t):
    return re.sub(r'/\*.*?\*/', ' ', '\n'.join(
        m.group(1) for m in STYLE.finditer(t)), flags=re.S)


def styles_raw(t):
    return '\n'.join(re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
                     for m in STYLE.finditer(t))


def markup_of(t):
    t = re.sub(r'\{#.*?#\}', '', t, flags=re.S)
    return re.sub(r'<(script|style)\b.*?</\1>', '',
                  re.sub(r'<!--.*?-->', '', t, flags=re.S), flags=re.S)


def one_branch(t, keep_if):
    """Resolve every {% if %} to ONE arm. keep_if picks which - this page
    puts Greek in the if and English in the else, and the two are very
    different lengths."""
    while True:
        stack = []
        for m in TAG.finditer(t):
            k = m.group(1)
            if k == 'if':
                stack.append([m.start(), m.end(), None, None])
            elif k in ('elif', 'else'):
                if stack and stack[-1][2] is None:
                    stack[-1][2] = m.start()
                    stack[-1][3] = m.end()
            elif k == 'endif':
                if not stack:
                    return t
                s, fe, cut, ae = stack.pop()
                if cut is not None:
                    t = ((t[:s] + t[fe:cut] + t[m.end():]) if keep_if
                         else (t[:s] + t[ae:m.start()] + t[m.end():]))
                    break
        else:
            return t


def strip_of(src, keep_if):
    """The stats strip, with one language chosen."""
    b = markup_of(one_branch(src, keep_if))
    i = b.find('alv-stats')
    if i < 0:
        i = b.find('task-summary')
    if i < 0:
        return ''
    a = b.rfind('<div', 0, i)
    d, j = 0, b.find('>', a) + 1
    for m in re.finditer(r'<div\b|</div\s*>', b[j:]):
        d += 1 if m.group(0).startswith('<div') else -1
        if d == -1:
            j = j + m.end()
            break
    return re.sub(r'\{\{.*?\}\}', '5',
                  re.sub(r'\{%.*?%\}', '', b[a:j], flags=re.S), flags=re.S)


PATH = alv_tree.join(REL.replace('/', os.sep))
BPATH = alv_tree.path_of('base.html')
now = (as_left_by(PATH, SUFFIX, read) if as_left_by else read(PATH))
was = read(PATH + SUFFIX) if os.path.isfile(PATH + SUFFIX) else None
base = (as_left_by(BPATH, SUFFIX, read) if as_left_by else read(BPATH))
bwas = read(BPATH + SUFFIX) if os.path.isfile(BPATH + SUFFIX) else None

print('=' * 74)
print('%s - P5, THREE STATS ON ONE LINE' % ME)
print('=' * 74)

# ==========================================================================
head('1. base CARRIES THE OPT-IN, INSIDE ITS PHONE BLOCK')
# ==========================================================================
bcss = css_of(base)
ok(bool(re.search(r'\.alv-stats\.is-3up\s*\{[^}]*repeat\(3, 1fr\)', bcss)),
   'base draws .alv-stats.is-3up at three columns')
for sel, what in (
        (r'\.alv-stats\.is-3up \.alv-stat\s*\{', 'a tighter stat box'),
        (r'\.alv-stats\.is-3up \.alv-stat-value\s*\{', 'a smaller value'),
        (r'\.alv-stats\.is-3up \.alv-stat-label\s*\{', 'a smaller label')):
    ok(bool(re.search(sel, bcss)), '  and %s' % what)
lab = re.search(r'\.alv-stats\.is-3up \.alv-stat-label\s*\{([^}]*)\}', bcss)
ok(lab is not None and 'overflow-wrap' in lab.group(1),
   '  and the label can break a long word - which Greek needs',
   lab.group(1) if lab else '')
# it must be INSIDE the phone media query, or it fires on the desktop
at = base.find('.alv-stats.is-3up')
ok(at > 0 and base.count('{', 0, at) - base.count('}', 0, at) == 1,
   'the opt-in sits inside the phone block, not at top level',
   'depth %d' % (base.count('{', 0, at) - base.count('}', 0, at)))
ok('repeat(2, 1fr)' in bcss,
   'and the two-column default is still there for everyone else')

# ==========================================================================
head('2. THE TASK LIST OPTS IN, AND REALLY HAS THREE STATS')
# ==========================================================================
m = markup_of(now)
ok('alv-stats task-summary is-3up' in m, 'the strip wears is-3up')
n = len(re.findall(r'class="alv-stat(?:\s|")', m))
ok(n == 3, '  and it is a strip of three', '%d stats found' % n)

# ==========================================================================
head('3. ONE ROW, IN BOTH LANGUAGES, AT FOUR WIDTHS')
# ==========================================================================
try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False
BOOTP = os.path.join(ROOT, BOOT)


def measure(bsrc, psrc, keep_if, tag):
    """rows, box heights and whether any label spills its box."""
    from playwright.sync_api import sync_playwright
    page = os.path.join(SCRATCH, 'f_%s.html' % tag)
    with open(page, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><html><head><meta charset="utf-8">'
                 '<meta name="viewport" content="width=device-width,'
                 'initial-scale=1"><style>%s</style><style>%s</style>'
                 '<style>%s</style></head><body class="has-sidebar">'
                 '<div class="main-content with-sidebar">%s</div>'
                 '</body></html>'
                 % (read(BOOTP), styles_raw(bsrc), styles_raw(psrc),
                    strip_of(psrc, keep_if)))
    out = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        for w in WIDTHS:
            ctx = br.new_context(viewport={'width': w, 'height': 700})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            _goto(pg, page)
            tops = pg.eval_on_selector_all(
                '.alv-stat', 'es => es.map(e => Math.round('
                             'e.getBoundingClientRect().top))')
            hs = pg.eval_on_selector_all(
                '.alv-stat', 'es => es.map(e => Math.round('
                             'e.getBoundingClientRect().height))')
            spill = pg.eval_on_selector_all(
                '.alv-stat-label',
                'es => es.some(e => e.scrollWidth > e.clientWidth + 1)')
            out[w] = (len(set(tops)), hs, spill)
            ctx.close()
        br.close()
    return out


if not have_pw or not os.path.isfile(BOOTP):
    skip('the strip in a browser', 'playwright or the fixture is absent')
else:
    for lang, keep in (('English', False), ('Greek', True)):
        got = measure(base, now, keep, 'a_%s' % lang)
        for w in WIDTHS:
            rows, hs, spill = got[w]
            ok(rows == 1, '%-8s %dpx  one row' % (lang, w),
               'it is %d rows' % rows)
            ok(len(set(hs)) == 1,
               '%-8s %dpx    and the three boxes are the same height'
               % ('', w), 'heights %s' % hs)
            ok(not spill,
               '%-8s %dpx    and no label spills its box' % ('', w))
        print('       %-8s box heights %s'
              % (lang, [got[w][1][0] for w in WIDTHS]))

# ==========================================================================
head('4. THE CONTROL - WITHOUT THE CLASS IT IS TWO ROWS AGAIN')
# ==========================================================================
if not have_pw or not os.path.isfile(BOOTP) or was is None or bwas is None:
    skip('the control', 'playwright, the fixture or a backup is absent')
else:
    got = measure(bwas, was, False, 'b_English')
    rows = [got[w][0] for w in WIDTHS]
    ok(all(r == 2 for r in rows),
       'the backup really was two rows at every width - not a tautology',
       'rows %s' % rows)
    print('       before, English: rows %s, box heights %s'
          % (rows, [got[w][1][0] for w in WIDTHS]))
    # and the class alone is what changes it
    stripped = now.replace('alv-stats task-summary is-3up',
                           'alv-stats task-summary')
    ok(stripped != now, 'the control really did change the page')
    got2 = measure(base, stripped, False, 'c_English')
    rows2 = [got2[w][0] for w in WIDTHS]
    ok(all(r == 2 for r in rows2),
       '  and taking is-3up off today\'s page puts it back to two rows',
       'rows %s' % rows2)

# ==========================================================================
head('5. THE STRIPS THAT MUST NOT TAKE IT')
# ==========================================================================
# The opt-in lives in base, so the failure this round could cause is a
# four- or five-stat strip wearing it and losing a column.
counts = {}
for q in alv_tree.templates():
    if os.path.basename(q) == 'base.html':
        continue
    src = (now if alv_tree.rel(q) == alv_tree.rel(PATH) else read(q))
    b = markup_of(src)
    n = len(re.findall(r'class="alv-stat(?:\s|")', b))
    if n:
        counts[alv_tree.rel(q).replace(os.sep, '/')] = (n, 'is-3up' in b)
bad = {k: v for k, v in counts.items() if v[1] and v[0] != 3}
ok(not bad, 'no strip with a count other than three wears is-3up', bad)
for k, (n, has) in sorted(counts.items()):
    print('       %-46s %d stat(s)  %s'
          % (k, n, 'is-3up' if has else '-'))
# fsr is the one that would be hurt, so it is named
fsr = counts.get('fsr.html')
ok(fsr is not None and not fsr[1],
   'fsr has %s stats and does NOT wear it'
   % (fsr[0] if fsr else '?'))

print('')
print('  NOT SWEPT IN: finance/financial_indicators and')
print('  finance/vacancy_management also show three stats and could take')
print('  this. Demetri asked about the Task List, and nobody has walked')
print('  those two screens. A decision, not an oversight.')

# ==========================================================================
head('6. THE GATE')
# ==========================================================================
ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(ME in t, 'this suite is on the gate  %s' % PS1)
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the patcher is not - a gate runs suites, not rounds')
else:
    skip('the gate', '%s not on disk' % PS1)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
for p in (PATH, BPATH):
    ok(os.path.isfile(p + SUFFIX),
       '%-34s has its backup' % os.path.basename(p))

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
