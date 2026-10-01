# -*- coding: utf-8 -*-
"""test_bar_stretch.py - Section I round I1, 30 Sep 2026.

Demetri, on Issues (Comments) at 386px: "This is not right in Issues."

Measured on fsr_details at his width: Edit Issue 34px wide with its text
overflowing the box, and Back 386px wide starting at x=42, running off
the screen. One rule on the page did it:

    .page-action-buttons > .btn,
    .page-action-buttons > a { width: 100%; text-align: center; }

Same specificity as base's `.page-action-buttons .action-back { width:
44px }`, and a later stylesheet, so the page won on order alone. Both
controls then demanded the full width in a nowrap row, squashed each
other, and min-width:0 let the primary shrink below its own text.

SECTION 1 IS THE ONE THAT MATTERS, and it is tree-wide rather than about
the ten. NO page may set a width on a button inside .page-action-buttons.
This is the THIRD time this defect has been found - T1 in the report
heads, D1 on property_detail, and now ten more - so the check is written
to catch the eleventh rather than to confirm the ten.

SECTION 3 DRAWS ALL TEN, before and after, and asks the browser whether
the button's content overflows its box. Nine of the ten were clipped;
the tenth had nothing but a Back, stretched across the phone, which is
character for character the defect T1 existed to remove.
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

SUFFIX = '.bak_barstretch'
ME = 'test_bar_stretch.py'
PATCHER = 'apply_bar_stretch.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)
WIDE = 386      # Demetri's own viewport

# The ten the screenshot led to: one rule each, stretching every button
# in the bar to the full width of the phone.
TEN = ('customer_form.html', 'finance_valuations_add.html',
       'finance_valuations_edit.html', 'fsr_details.html',
       'projects/project_subtasks_add.html',
       'projects/project_tasks_add.html',
       'projects/project_tasks_delete.html',
       'projects/project_tasks_edit.html',
       'projects/projects_add.html', 'projects/projects_edit.html')
# And two the GATE found rather than the screenshot: a near-complete copy
# of base's phone bar with 38px where base says 44px. Measured before
# being touched - the heights never applied, because a later rule of
# base's won. The one live effect was Back at 50px.
COPIES = ('finance_expense_types.html', 'finance_revenue_types.html')
# Matched the net, and are NOT this defect.
NOT_THIS = {'properties_edit.html': 'sizes the wrapper, not a button',
            'tenant_edit.html': 'the same wrapper rule',
            'recipe_management.html': 'sizes a dropdown base has no name for'}

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
    return re.sub(r'/\*.*?\*/', ' ', '\n'.join(STYLE.findall(t)), flags=re.S)


def markup_of(t):
    return re.sub(r'<(script|style)\b.*?</\1>', '',
                  re.sub(r'<!--.*?-->', '', t, flags=re.S), flags=re.S)


def left(rel):
    p = alv_tree.join(rel.replace('/', os.sep))
    return (as_left_by(p, SUFFIX, read) if as_left_by else read(p))


# WIDTH, NOT min-width. `\bwidth` matches the width inside `min-width`,
# because a hyphen is a word boundary - the first version of this gate
# reported three pages for `min-width: 0`, which is base's own rule
# copied and is not a stretch at all.
REAL_WIDTH = re.compile(r'(?<![-\w])width\s*:')
# A control in the bar, not something INSIDE a control. A badge that
# sizes itself is not a button stretching across a phone.
CONTROL = re.compile(r'(?:\.btn|\bbutton\b|\ba\b|\.action-(?:primary|'
                     r'secondary|back|danger|filter|more-btn))\s*$')
# Named exceptions, each with a reason, in the manner of
# Show-ButtonDrift's LEAVE. An exception has to be argued, not assumed.
ALLOWED = {
    '.page-action-buttons .dropdown-btn-container .dropdown-btn':
        'recipe_management: a dropdown inside the bar, which base has no '
        'name for - it is not a .btn taking a row with Back',
}


def sizes_a_bar_button(css):
    """Every rule that sets a real WIDTH on a control inside the action
    bar. The bar's own width is a different question and is not asked."""
    out = []
    for m in re.finditer(r'([^{}]*page-action-buttons[^{}]*)\{([^}]*)\}', css):
        sel = ' '.join(m.group(1).split())
        if sel.endswith('page-action-buttons') or 'page-action-buttons-' in sel:
            continue          # the container, or a named variant of it
        if sel in ALLOWED:
            continue
        if not CONTROL.search(sel):
            continue
        if REAL_WIDTH.search(m.group(2)):
            out.append('%s { %s }' % (sel[:60], ' '.join(m.group(2).split())[:50]))
    return out


def bar_of(t):
    """The action bar element, balanced on <div>, Django resolved to the
    branch a permitted user sees."""
    b = markup_of(t)
    m = re.search(r'<div[^>]*class="[^"]*page-action-buttons[^"]*"[^>]*>', b)
    if not m:
        return None
    i, d = m.start(), 0
    for x in re.finditer(r'<div\b|</div>', b[i:]):
        d += 1 if x.group(0) != '</div>' else -1
        if d == 0:
            seg = b[i:i + x.end()]
            break
    else:
        return None
    seg = re.sub(r'\{%\s*(?:if|endif|else)\b[^%]*%\}', '', seg)
    seg = re.sub(r'\{%.*?%\}', '#', seg, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'X', seg, flags=re.S)


base = read(alv_tree.path_of('base.html'))

print('=' * 74)
print('%s - I1, TEN PAGES STOP STRETCHING THEIR ACTION BAR' % ME)
print('=' * 74)

# ==========================================================================
head('1. NO PAGE SIZES A BUTTON IN THE ACTION BAR')
# ==========================================================================
# Tree-wide, and written to catch the ELEVENTH. This defect has now been
# found three times - T1 in the report heads, D1 on property_detail, and
# these ten - so confirming the ten is not the useful question.
offenders = {}
for q in alv_tree.templates():
    rel = alv_tree.rel(q)
    if os.path.basename(q) == 'base.html':
        continue
    bad = sizes_a_bar_button(css_of(read(q)))
    if bad:
        offenders[rel] = bad
ok(not offenders,
   'not one page in the tree sets a width on a button in '
   '.page-action-buttons',
   '\n'.join('%s: %s' % (k, v[0]) for k, v in list(offenders.items())[:4]))

# AND base DOES, which is why no page needs to.
bcss = css_of(base)
ok(bool(re.search(r'\.page-action-buttons \.action-back\s*\{[^}]*width:\s*'
                  r'44px', bcss)),
   '  base makes Back a 44px square on a phone')
ok(bool(re.search(r'\.page-action-buttons \.action-primary\s*\{[^}]*'
                  r'flex:\s*1 1 auto', bcss)),
   '  and lets the primary take the rest of the row')

# ==========================================================================
head('2. THE TEN, AND WHAT EACH OF THEM SAID')
# ==========================================================================
for rel in TEN + COPIES:
    p = alv_tree.join(rel.replace('/', os.sep))
    ok(os.path.isfile(p), '%-36s is where alv_tree says' % rel)
    bak = p + SUFFIX
    if not os.path.isfile(bak):
        skip(rel, 'no %s backup' % SUFFIX)
        continue
    was = sizes_a_bar_button(css_of(read(bak)))
    want = 1 if rel in TEN else 1      # the copy pages size Back only
    ok(len(was) == want,
       '  %-34s CONTROL: it sized a bar control' % '', was)
    ok(not sizes_a_bar_button(css_of(left(rel))),
       '  %-34s and has none now' % '')
    # THE MARKUP DID NOT MOVE. This round is CSS only.
    strip = lambda s: re.sub(r'<style\b.*?</style>', '', s, flags=re.S)
    ok(strip(read(bak)) == strip(left(rel)),
       '  %-34s markup byte-identical' % '')

# ==========================================================================
head('3. CHROMIUM: AT 386px, HIS OWN WIDTH')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)

BOOT = ''
_b = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
if os.path.isfile(_b):
    BOOT = read(_b)

LOOK = '''() => {
  const bar = document.querySelector(".page-action-buttons");
  if (!bar) return {err: "no bar"};
  const kids = [...bar.children].map(e => {
     const r = e.getBoundingClientRect();
     return {t: (e.textContent||"").trim().slice(0, 12),
             w: Math.round(r.width), h: Math.round(r.height),
             r: Math.round(r.right),
             clipped: e.scrollWidth > e.clientWidth + 1};
  });
  return {kids: kids, barR: Math.round(bar.getBoundingClientRect().right),
          scrollW: document.documentElement.scrollWidth,
          clientW: document.documentElement.clientWidth};
}'''

if HAVE_PW and BOOT:
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': WIDE, 'height': 800})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        def draw(pcss, mk, name):
            f = os.path.join(SCRATCH, name)
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write('<!doctype html><html><head><meta charset="utf-8">'
                         '<style>%s</style><style>%s</style>'
                         '<style>%s</style></head><body>%s</body></html>'
                         % (BOOT, css_of(base), pcss, mk))
            _goto(pg, f)
            pg.wait_for_timeout(80)
            return pg.evaluate(LOOK)

        clipped_before = 0
        for rel in TEN:
            p = alv_tree.join(rel.replace('/', os.sep))
            bak = p + SUFFIX
            now = left(rel)
            mk = bar_of(now)
            if not mk:
                ok(False, '%s - no action bar found' % rel)
                continue
            b = draw(css_of(now), mk, 'n_%s.html' % rel.replace('/', '_'))
            name = rel.split('/')[-1].replace('.html', '')
            if os.path.isfile(bak):
                was = read(bak)
                a = draw(css_of(was), bar_of(was) or mk,
                         'w_%s.html' % rel.replace('/', '_'))
                print('     %-26s before %-22s after %s'
                      % (name,
                         ' '.join('%d%s' % (k['w'], '!' if k['clipped']
                                            else '') for k in a['kids']),
                         ' '.join('%d' % k['w'] for k in b['kids'])))
                if any(k['clipped'] for k in a['kids']):
                    clipped_before += 1
            # NOTHING IS CLIPPED NOW.
            bad = [k['t'] for k in b['kids'] if k['clipped']]
            ok(not bad, '  %-24s nothing is clipped' % name, bad)
            # BACK IS A 44px SQUARE, hard against the right of the bar.
            backs = [k for k in b['kids'] if k['w'] <= 60]
            ok(bool(backs), '  %-24s Back is a square, not a band' % '',
               [k['w'] for k in b['kids']])
            if backs:
                ok(backs[-1]['w'] >= 44 and backs[-1]['h'] >= 44,
                   '  %-24s and still a 44px target' % '',
                   '%dx%d' % (backs[-1]['w'], backs[-1]['h']))
                ok(abs(b['barR'] - backs[-1]['r']) <= 2,
                   '  %-24s sitting at the right edge' % '',
                   'gap %d' % (b['barR'] - backs[-1]['r']))
            ok(b['scrollW'] <= b['clientW'] + 1,
               '  %-24s and nothing runs off the screen' % '',
               '%d in %d' % (b['scrollW'], b['clientW']))
        ok(clipped_before == 9,
           'CONTROL: nine of the ten had a CLIPPED button before this round',
           clipped_before)
        br.close()
elif not BOOT:
    skip('the renders', 'test_fixture_bootstrap413.css is not on disk')
else:
    skip('the renders', 'playwright unavailable')

# ==========================================================================
head('4. REPORTED, NOT CHANGED')
# ==========================================================================
for rel, why in sorted(NOT_THIS.items()):
    p = alv_tree.path_of(rel)
    ok(os.path.isfile(p), '%-28s %s' % (rel, why))
    ok(not os.path.isfile(p + SUFFIX),
       '  %-26s and this round did not touch it' % '')
twice = []
for rel in TEN:
    seg = bar_of(left(rel)) or ''
    if len(re.findall(r'action-back(?![\w-])', seg)) > 1:
        twice.append(rel)
print('')
print('  TWO pages draw Back TWICE in one bar:')
for r in twice:
    print('     %s' % r)
print('  Not this round - it is about width, not about how many Backs a')
print('  bar should hold - but nobody meant to draw it twice.')
ok(sorted(twice) == ['projects/project_tasks_edit.html',
                     'projects/projects_edit.html'],
   'and it is those two, named so the set cannot grow in silence', twice)

# ==========================================================================
head('5. THE GATE')
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

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
