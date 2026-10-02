# -*- coding: utf-8 -*-
"""test_tabs.py - Section AE round AE-2, 2 Oct 2026.

Demetri raised it as "the non-selected tab colour". The census turned it
into something else.

SECTION 4 IS THE ROUND. base had no tab rule at all, and the template
that renders 205 of this app's 213 tabs wrote its colour INLINE, per tab,
from {% if forloop.first %}. First is not active: Bootstrap's plugin moves
the .active class when you click, and it cannot touch an inline style -
which beats every stylesheet there is. So section 4 renders a help tab
strip, MOVES .active the way the plugin does, and reads the colours back.
Before this round that measured

    Overview   active=false   rgb(14,124,139)   <- still teal
    Filters    active=true    rgb(73,80,87)

and that is what the control below asserts, from the backup, so the claim
is a measurement rather than a story.

SECTION 5 IS THE TWO RISKS, BOTH MEASURABLE. Lifting a component into
base can break two things that have nothing to do with tabs:

  THE TOP NAV wears .nav-link ten times in base.html - every menu item,
  the bell, the profile link. A rule on the bare class would repaint the
  whole navigation bar, so section 5 renders the real navbar markup
  before and after and asserts not one pixel of it moved.

  THE REVIEWED COPY is the Issues Analysis bar, and base took its rules
  verbatim. If that bar moves, base did not take them verbatim.

SECTION 6 IS THE ONE DEMETRI ACTUALLY REPORTED: no tab anywhere in the
tree still resting on Bootstrap's #007bff.
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
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_tabs'
ME = 'test_tabs.py'
PATCHER = 'apply_tabs.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)

BASE = alv_tree.path_of('base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

# Every template that styled a tab before this round, and what it gave up.
GAVE_UP = {
    'help_modal_shell.html':
        'the inline colour on all 205 tabs, and the strip\'s 2px border',
    'act_expense.html': 'three #manageModal rules - size and scrolling',
    'notifications.html': 'two rules painting ANOTHER template\'s component',
    'projects/projects_edit.html': 'four rules - box tabs and a phone block',
    'projects/project_tasks_edit.html': 'the same four again',
    'fsr.html': 'three rules, which are base\'s now, verbatim',
}
BOOTSTRAP_BLUE = 'rgb(0, 123, 255)'

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


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    """BEFORE this round. as_left_by() returns the file as the round LEFT
    it, which is the opposite of a control - A1's lesson, and it cost a
    push."""
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


def code_only(text):
    """Comments blanked, length preserved.

    A CHECK THAT A NAME IS ABSENT MUST NOT READ PROSE. The notes this
    round left behind name #007bff, #495057 and the rules they replaced,
    because recording what was removed is what a note is for. Six gates
    across two rounds read those notes as the defect before the
    instrument was fixed rather than the record reworded."""
    def blank(m):
        return re.sub(r'[^\n]', ' ', m.group(0))
    text = re.sub(r'<!--.*?-->', blank, text, flags=re.S)
    text = re.sub(r'\{#.*?#\}', blank, text, flags=re.S)
    return re.sub(r'/\*.*?\*/', blank, text, flags=re.S)


def css_of(t):
    return '\n'.join(STYLE.findall(t))


B_NOW, B_WAS = now(BASE), was(BASE)

print('=' * 74)
print('%s - AE-2, THE TAB STANDARD' % ME)
print('=' * 74)

# ==========================================================================
head('1. base OWNS THE TAB NOW, AND DID NOT BEFORE')
# ==========================================================================
ok('ALV TABS v1' in B_NOW, 'base carries the ALV TABS block')
ok(B_NOW.count('ALV TABS v1') == 2, '  once, opened and closed',
   B_NOW.count('ALV TABS v1'))
if B_WAS:
    ok('ALV TABS v1' not in B_WAS, 'CONTROL: it was not there before')
    ok(not re.search(r'(?m)^[^\n{}]*\.nav-tabs[^\n{}]*\{', css_of(B_WAS)),
       '  and base declared NOTHING about tabs at all - not one '
       '.nav-tabs rule in 3,600 lines')
else:
    skip('the base control', 'no %s backup' % SUFFIX)

_blk = B_NOW[B_NOW.index('/* ===== ALV TABS v1'):
             B_NOW.index('/* ===== /ALV TABS v1')]
_decl = re.sub(r'/\*.*?\*/', '', _blk, flags=re.S)
for want in ('.alv-tabs', '.alv-tab', '.nav-tabs .nav-link'):
    ok(want in _decl, '  it declares %s' % want)
for tok in ('var(--alv-line)', 'var(--alv-ink-soft)',
            'var(--alv-accent-ink)', 'var(--alv-accent)'):
    ok(tok in _decl, '  on %s' % tok)
ok(not re.search(r'#[0-9a-fA-F]{3,8}\b', _decl),
   '  and not one literal colour in the declarations')
ok(re.search(r'#[0-9a-fA-F]{3,8}\b', _blk) is not None,
   '    CONTROL: but the prose DOES name the literals it replaced')

# NOT ONE BARE .nav-link. The top nav wears it ten times in this very
# file; a rule on the bare class would repaint the whole navigation.
bare = []
for m in re.finditer(r'(?m)^([^\n{}]*\.nav-link[^\n{}]*)\{',
                     css_of(code_only(B_NOW))):
    for sel in m.group(1).split(','):
        sel = sel.strip()
        if sel and '.nav-link' in sel and '.nav-tabs' not in sel:
            bare.append(sel)
ok(not bare,
   'and NOT ONE bare .nav-link rule - every selector is scoped to '
   '.nav-tabs, because the TOP NAV wears .nav-link too', bare[:4])
navlinks = len(re.findall(r'class="[^"]*\bnav-link\b',
                          re.sub(r'<(script|style)\b.*?</\1>', '',
                                 code_only(B_NOW), flags=re.S)))
ok(navlinks >= 8,
   '  CONTROL: base\'s own navigation wears .nav-link %d time(s), which '
   'is what makes that scoping load-bearing' % navlinks, navlinks)

# ==========================================================================
head('2. THE LOOK WAS NOT CHOSEN - IT WAS LIFTED')
# ==========================================================================
# ALV-SEG's note settled what a tab bar is, and said base would get one
# when a second page asked. Read it, rather than restating it.
seg = B_NOW[B_NOW.index('/* ===== ALV-SEG v1'):]
seg = seg[:seg.index('.alv-seg {')]
ok('NOT A TAB BAR' in seg,
   'ALV-SEG\'s note already said what a tab bar is, and that it is not a '
   'segment')
ok('underline under the current one' in seg,
   '  "full width, with an underline under the current one"')
ok('that is when base gets one' in seg,
   '  and that base would get one when a second page asked')
ok('border-bottom: 3px solid transparent' in _decl
   and 'border-bottom-color: var(--alv-accent)' in _decl,
   '  which is exactly what this component does - an underline, not a fill')

F_WAS = was(alv_tree.path_of('fsr.html'))
if F_WAS:
    ok('.ia-tab{border:none' in F_WAS
       and 'var(--alv-ink-soft)' in F_WAS,
       'AND THE VALUES ARE NOT NEW: the Issues Analysis bar was already '
       'entirely on tokens - the one tab copy in the tree that had been '
       'through a styling round')
    for d in ('gap:4px', 'border-bottom:3px solid transparent',
              'font-weight:600', 'flex:1 1 0'):
        ok(d.replace(':', ': ') in _decl.replace('  ', ' ')
           or d in _decl.replace(' ', ''),
           '  base says %s, as that copy did' % d)
else:
    skip('the reviewed-copy control', 'no fsr backup')

# ==========================================================================
head('3. EVERY PAGE GAVE UP ITS COPY')
# ==========================================================================
left = []
for p in alv_tree.templates():
    rel = alv_tree.rel(p)
    if rel == 'base.html':
        continue
    for m in re.finditer(r'(?m)^([^\n{}]*(?:\.nav-tabs|\.nav-link|\.ia-tab)'
                         r'[^\n{}]*)\{', css_of(code_only(read(p)))):
        left.append('%s: %s' % (rel, ' '.join(m.group(1).split())))
ok(not left, 'not one page styles a tab any more', left[:6])

for rel, gave in sorted(GAVE_UP.items()):
    w = was(alv_tree.path_of(rel))
    if not w:
        skip('  %s control' % rel, 'no backup')
        continue
    n = len(re.findall(r'(?m)^([^\n{}]*(?:\.nav-tabs|\.nav-link|\.ia-tab)'
                       r'[^\n{}]*)\{', css_of(code_only(w))))
    inline = len(re.findall(r'style="[^"]*color:', code_only(w)))
    ok(n > 0 or inline > 0,
       '  CONTROL: %-32s had %d rule(s) - %s' % (rel, n, gave), n)

# ==========================================================================
head('4. MEASURED - THE TEAL THAT COULD NOT FOLLOW THE CLICK')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)

HS = alv_tree.path_of('help_modal_shell.html')


def help_strip(text):
    """The help shell's tab strip as it renders for a 3-tab module - from
    the template itself, with the loop unrolled, so the fixture cannot
    disagree with the page in the way that matters."""
    mk = code_only(text)
    ul = re.search(r'<ul class="nav nav-tabs".*?</ul>', mk, re.S)
    if not ul:
        return ''
    blk = ul.group(0)
    item = re.search(r'\{%\s*for tab in module\.tabs\s*%\}(.*?)'
                     r'\{%\s*endfor\s*%\}', blk, re.S)
    if not item:
        return ''
    # BOTH FORMS OF THE TAG, and the first draft of this handled only
    # one. The shell writes {% if forloop.first %}active{% endif %} for
    # the class and, before AE-2, {% if forloop.first %}A{% else %}B
    # {% endif %} for the colour. A pattern that stops at {% endif %}
    # captures "A{% else %}B" and keeps BOTH branches on the first item -
    # which rendered color:#0e7c8b#495057, an invalid value, and the
    # browser fell back to Bootstrap's blue. The control then reported
    # blue-grey-blue and failed, correctly: the fixture was wrong, and
    # measuring it is how that was found rather than assumed.
    IFELSE = re.compile(r'\{%\s*if forloop\.first\s*%\}(.*?)'
                        r'(?:\{%\s*else\s*%\}(.*?))?\{%\s*endif\s*%\}',
                        re.S)
    out = []
    for i, name in enumerate(('Overview', 'Filters', 'Reports')):
        one = IFELSE.sub(
            (lambda m: m.group(1)) if i == 0
            else (lambda m: m.group(2) or ''), item.group(1))
        one = one.replace('{{ tab.name }}', name)
        one = re.sub(r'\{\{.*?\}\}', 't%d' % i, one)
        one = re.sub(r'\{%.*?%\}', '', one, flags=re.S)
        out.append(one)
    shell = blk[:item.start()] + ''.join(out) + blk[item.end():]
    return re.sub(r'\{\{.*?\}\}', 'x', shell)


LOOK = '''() => [...document.querySelectorAll('.nav-tabs .nav-link')].map(a => ({
  text: a.textContent.trim(),
  active: a.classList.contains('active'),
  colour: getComputedStyle(a).color,
  under: getComputedStyle(a).borderBottomColor,
  underW: getComputedStyle(a).borderBottomWidth
}))'''
CLICK = '''() => {
  const a = [...document.querySelectorAll('.nav-tabs .nav-link')];
  a[0].classList.remove('active'); a[1].classList.add('active');
}'''

if HAVE_PW and os.path.isfile(BOOT):
    boot = read(BOOT)

    def draw(pg, base_text, shell_text, name):
        f = os.path.join(SCRATCH, name)
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write('<!doctype html><html><head><meta charset="utf-8">'
                     '<style>%s</style><style>%s</style></head><body>'
                     '<div class="container">%s</div></body></html>'
                     % (boot, css_of(base_text), help_strip(shell_text)))
        _goto(pg, f)
        pg.wait_for_timeout(40)
        return pg.evaluate(LOOK)

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1280, 'height': 700})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        H_NOW, H_WAS = now(HS), was(HS)

        a = draw(pg, B_NOW, H_NOW, 'now.html')
        ok(len(a) == 3, 'the help strip renders three tabs', len(a))
        if a:
            ok(a[0]['active'] and a[0]['under'] != 'rgba(0, 0, 0, 0)',
               'AS OPENED: the first tab is current and carries the '
               'underline', a[0])
            ok(all(t['under'] == 'rgba(0, 0, 0, 0)' for t in a[1:]),
               '  and the other two carry none', [t['under'] for t in a[1:]])
            ok(all(t['colour'] != BOOTSTRAP_BLUE for t in a),
               '  and NOT ONE of them is Bootstrap\'s #007bff',
               [t['colour'] for t in a])
        pg.evaluate(CLICK)
        pg.wait_for_timeout(30)
        b = pg.evaluate(LOOK)
        ok(b and not b[0]['active'] and b[0]['under'] == 'rgba(0, 0, 0, 0)',
           'AFTER THE CLICK: tab one is no longer current and LOSES the '
           'underline', b[0] if b else None)
        ok(b and b[1]['active'] and b[1]['under'] != 'rgba(0, 0, 0, 0)',
           '  and the tab you opened gains it', b[1] if b else None)
        ok(b and b[0]['colour'] == b[2]['colour'],
           '  and tab one reads the same as the one nobody touched',
           [t['colour'] for t in b] if b else None)

        # THE CONTROL, AND IT IS THE DEFECT ITSELF.
        if H_WAS and B_WAS:
            c = draw(pg, B_WAS, H_WAS, 'was.html')
            pg.evaluate(CLICK)
            pg.wait_for_timeout(30)
            d = pg.evaluate(LOOK)
            ok(d and d[0]['colour'] != d[2]['colour'],
               'CONTROL: before this round, clicking tab two left tab ONE '
               'teal - %s against %s on the untouched one'
               % (d[0]['colour'] if d else '?', d[2]['colour'] if d else '?'),
               [t['colour'] for t in d] if d else None)
            ok(d and d[1]['active'] and d[1]['colour'] == d[2]['colour'],
               '  while the tab you were actually reading looked like the '
               'ones you were not - an inline style cannot move when the '
               'plugin moves .active',
               [(t['active'], t['colour']) for t in d] if d else None)
        else:
            skip('the stuck-teal control', 'no backup')

        # ==================================================================
        head('5. AND THE TWO THINGS A BASE RULE COULD HAVE BROKEN')
        # ==================================================================
        # THE TOP NAV. base wears .nav-link on every menu item.
        NAV = ('<nav class="navbar navbar-expand-lg navbar-dark bg-dark">'
               '<ul class="navbar-nav">'
               '<li class="nav-item"><a class="nav-link" href="#">'
               'Properties</a></li>'
               '<li class="nav-item"><a class="nav-link active" href="#">'
               'Tenants</a></li>'
               '</ul></nav>')
        NAVLOOK = '''() => [...document.querySelectorAll('.navbar .nav-link')]
          .map(a => { const c = getComputedStyle(a); return {
            colour: c.color, size: c.fontSize, weight: c.fontWeight,
            pad: c.padding, border: c.borderBottomWidth,
            w: Math.round(a.getBoundingClientRect().width),
            h: Math.round(a.getBoundingClientRect().height) }; })'''

        def nav(base_text, name):
            f = os.path.join(SCRATCH, name)
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write('<!doctype html><html><head><meta charset="utf-8">'
                         '<style>%s</style><style>%s</style></head><body>%s'
                         '</body></html>' % (boot, css_of(base_text), NAV))
            _goto(pg, f)
            pg.wait_for_timeout(40)
            return pg.evaluate(NAVLOOK)

        if B_WAS:
            n_now, n_was = nav(B_NOW, 'nav_now.html'), nav(B_WAS,
                                                           'nav_was.html')
            ok(n_now == n_was,
               'THE TOP NAVIGATION DID NOT MOVE - colour, size, weight, '
               'padding, border and box, both links',
               'now %s\nwas %s' % (n_now, n_was))
        else:
            skip('the top-nav control', 'no base backup')

        # THE REVIEWED COPY. base took its rules verbatim; if the bar
        # moved, it did not.
        FSR = alv_tree.path_of('fsr.html')
        IA = ('<div class="ia-tabs alv-tabs">'
              '<button class="ia-tab alv-tab active">By property</button>'
              '<button class="ia-tab alv-tab">Open-issue aging</button>'
              '<button class="ia-tab alv-tab">Logged vs resolved</button>'
              '</div>')
        IA_WAS = IA.replace(' alv-tabs', '').replace(' alv-tab', '')
        IALOOK = '''() => [...document.querySelectorAll('button')].map(a => {
          const c = getComputedStyle(a); return {
            colour: c.color, under: c.borderBottomColor,
            underW: c.borderBottomWidth, size: c.fontSize,
            weight: c.fontWeight, pad: c.padding,
            w: Math.round(a.getBoundingClientRect().width) }; })'''

        def ia(base_text, page_text, markup, name):
            f = os.path.join(SCRATCH, name)
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write('<!doctype html><html><head><meta charset="utf-8">'
                         '<style>%s</style><style>%s</style><style>%s</style>'
                         '</head><body><div id="issuesAnalysisModal">'
                         '<div style="width:900px">%s</div></div></body>'
                         '</html>' % (boot, css_of(base_text),
                                      css_of(page_text), markup))
            _goto(pg, f)
            pg.wait_for_timeout(40)
            return pg.evaluate(IALOOK)

        if F_WAS and B_WAS:
            i_now = ia(B_NOW, read(FSR), IA, 'ia_now.html')
            i_was = ia(B_WAS, F_WAS, IA_WAS, 'ia_was.html')
            ok(i_now == i_was,
               'AND THE REVIEWED COPY DID NOT MOVE EITHER - the Issues '
               'Analysis bar renders identically from base as it did from '
               'its own three rules', 'now %s\nwas %s' % (i_now, i_was))
        else:
            skip('the reviewed-copy render', 'no backup')
        br.close()
elif not HAVE_PW:
    skipped += 12
else:
    skip('the browser sections', 'no bootstrap fixture')
    skipped += 11

# ==========================================================================
head('6. WHAT DEMETRI REPORTED - NO TAB RESTS ON BOOTSTRAP BLUE')
# ==========================================================================
# Said in the source as well as measured above: nothing in the tree hands
# a tab to Bootstrap's own .nav-link colour any more, because base's rule
# is later and at equal specificity.
bs_i = B_NOW.index('bootstrap@4.1.3/dist/css/bootstrap.min.css')
tabs_i = B_NOW.index('/* ===== ALV TABS v1')
ok(bs_i < tabs_i,
   'bootstrap.min.css is linked ABOVE the component, so base wins at '
   'equal specificity - .nav-tabs .nav-link.active is 0,3,0 in both',
   '%d / %d' % (bs_i, tabs_i))
ok('#007bff' not in css_of(code_only(B_NOW)),
   '  and base names Bootstrap\'s blue nowhere in its own CSS')

tabbed = []
for p in alv_tree.templates():
    mk = re.sub(r'<(script|style)\b.*?</\1>', '', code_only(read(p)),
                flags=re.S)
    n = len(re.findall(r'class="[^"]*\bnav-link\b[^"]*"', mk))
    if 'nav-tabs' in mk and n:
        tabbed.append((alv_tree.rel(p), n))
print('')
for rel, n in sorted(tabbed):
    print('     %-36s %d tab link(s) in markup' % (rel, n))
ok(len(tabbed) >= 4, '%d template(s) carry a Bootstrap tab bar' % len(tabbed),
   tabbed)

# ==========================================================================
head('7. REGISTERED')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
except Exception as e:
    skip('ROUNDS', str(e))
print('\n    $suites now lists %d suite(s).'
      % len(re.findall(r"'test_[a-z0-9_]+\.py'", ps)))

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
