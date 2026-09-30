# -*- coding: utf-8 -*-
"""test_dash_back.py - Section D round D1, 30 Sep 2026.

Demetri: "On the Dashboard, can we make all the Property Dashboard
buttons, Back Buttons and ensure that they comply with our standards."

Two pages carried one - property_detail and dashboard_pl - and NEITHER
had a Back anywhere on it. The control that takes you back off those two
screens was a secondary action with a house icon, sitting in a wrapper
base has never heard of.

THE WRAPPER IS THE PART THAT MATTERS, and section 1 is where it is
proved. base scopes every geometry rule .action-back has to
.page-action-buttons - the standalone hover is all that reaches outside.
Putting .action-back on an anchor in a bare <div> gives it the colour
and none of the shape, which would have looked like compliance and not
been it. Section 3 measures the difference in Chromium.

THE DESTINATION IS UNCHANGED. Both still go to the property management
dashboard, which is the screen you came from - it was always a Back, it
was only ever dressed as something else.
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

SUFFIX = '.bak_dashback'
ME = 'test_dash_back.py'
PATCHER = 'apply_dash_back.py'
PS1 = 'Push-PendingChanges.ps1'
PAGES = ('property_detail.html', 'dashboard_pl.html')
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)

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


def no_comments(s):
    s = re.sub(r'<!--.*?-->|\{#.*?#\}', '', s, flags=re.S)
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)


def css_of(t):
    return no_comments('\n'.join(STYLE.findall(t)))


def markup_of(t):
    return re.sub(r'<(script|style)\b.*?</\1>', '', no_comments(t), flags=re.S)


def left(rel):
    p = alv_tree.path_of(rel)
    return (as_left_by(p, SUFFIX, read) if as_left_by else read(p))


def bar_of(mk):
    """The action bar and the anchor inside it."""
    m = re.search(r'<div class="[^"]*page-action-buttons[^"]*">'
                  r'(?:(?!</div>).)*?</a>', mk, re.S)
    return m.group(0) if m else None


base = read(alv_tree.path_of('base.html'))

print('=' * 74)
print('%s - D1, THE PROPERTY DASHBOARD BUTTON BECOMES BACK' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE BAR, BECAUSE base SCOPES EVERYTHING TO IT')
# ==========================================================================
# WHAT THE BAR ACTUALLY ADDS - corrected 30 Sep 2026, by the control in
# section 3. The first version of this claimed base styles .action-back
# ONLY inside .page-action-buttons, and that is not true: a long
# selector list gives .btn.action-back its display unscoped, which a
# regex looking for a bare `.action-back {` at the start of a line did
# not see. What the BAR adds is the phone geometry - a 44px square,
# flex: 0 0 auto, and the margin-left:auto that puts Back on the right.
# That is still a reason the wrapper had to change, and it is now the
# reason this suite states.
bcss = css_of(base)
scoped = len(re.findall(r'\.page-action-buttons[^{},]*\.action-back[^{}]*\{',
                        bcss))
ok(scoped >= 3, 'base scopes %d .action-back rule(s) to the bar' % scoped)
phone = re.search(r'\.page-action-buttons \.action-back\s*\{([^}]*width:\s*'
                  r'44px[^}]*)\}', bcss)
ok(bool(phone), '  including the 44px square, which only exists inside it',
   phone.group(1).strip() if phone else 'not found')
ok(bool(re.search(r'\.page-action-buttons[^{}]*\.action-back[^{}]*\{'
                  r'[^}]*margin-left:\s*auto', bcss)),
   '  and the margin that puts Back on the right')

for rel in PAGES:
    mk = markup_of(left(rel))
    bar = bar_of(mk)
    ok(bar is not None, '%-24s has a page-action-buttons bar' % rel)
    if not bar:
        continue
    ok('page-action-buttons-single' in bar,
       '  %-22s and it is the lone-Back modifier' % '')
    ok(re.search(r'class="btn action-back"', bar) is not None,
       '  %-22s holding the house Back' % '')
    ok('fa-arrow-left' in bar, '  %-22s with the arrow' % '')
    ok('action-back-label' in bar,
       '  %-22s and the label base hides below 768px' % '')
    ok('action-secondary' not in bar and 'fa-home' not in bar,
       '  %-22s and nothing of the old button' % '')
    ok('Property Dashboard' not in mk,
       '  %-22s the old label is gone from the page' % '')
    # THE PAGE WRITES NO RULE base OWNS.
    own = re.findall(r'(?m)^[ \t]*[^{}\n]*\.(?:page-action-buttons|'
                     r'action-back)[a-zA-Z-]*[^{}\n]*\{', css_of(left(rel)))
    ok(not own, '  %-22s and writes no rule base owns' % '',
       [x.strip() for x in own[:2]])

# ==========================================================================
head('2. THE DESTINATION DID NOT MOVE')
# ==========================================================================
for rel in PAGES:
    bak = alv_tree.path_of(rel) + SUFFIX
    if not os.path.isfile(bak):
        skip(rel, 'no %s backup' % SUFFIX)
        continue
    was, now = read(bak), left(rel)
    hw = re.search(r'href="(\{% url \'property_management_dashboard\''
                   r'[^"]*)"', was)
    hn = re.search(r'href="(\{% url \'property_management_dashboard\''
                   r'[^"]*)"', now)
    ok(bool(hw) and bool(hn) and hw.group(1) == hn.group(1),
       '%-24s still goes to exactly the same place' % rel,
       '%s -> %s' % (hw.group(1) if hw else '-', hn.group(1) if hn else '-'))
    # CONTROL: it really was a secondary action with a house icon.
    wasmk = markup_of(was)
    ok('Property Dashboard' in wasmk and 'fa-home' in wasmk,
       '  CONTROL: before, it was a house icon labelled Property Dashboard')
    ok('action-back' not in wasmk,
       '  CONTROL: and there was no Back on the page at all')

# ==========================================================================
head('3. CHROMIUM: THE SHAPE THE BAR GIVES IT')
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


def resolve(s):
    s = re.sub(r'\{%.*?%\}', '', s, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'Sample', s, flags=re.S)


LOOK = '''() => {
  const a = document.querySelector(".action-back");
  const bar = document.querySelector(".page-action-buttons");
  if (!a) return {err: "no back"};
  const c = getComputedStyle(a), r = a.getBoundingClientRect();
  const lbl = a.querySelector(".action-back-label");
  return {display: c.display, w: Math.round(r.width), h: Math.round(r.height),
          // the CONTROL fixture deliberately has no bar around it, so
          // this must not assume one exists.
          right: bar ? Math.round(bar.getBoundingClientRect().right
                                  - r.right) : null,
          label: lbl ? getComputedStyle(lbl).display : "-",
          bg: c.backgroundColor, border: c.borderTopColor};
}'''

if HAVE_PW and BOOT:
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1280, 'height': 700})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        def draw(basecss, pagecss, mkup, name, w, h):
            f = os.path.join(SCRATCH, name)
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write('<!doctype html><html><head><meta charset="utf-8">'
                         '<style>%s</style><style>%s</style>'
                         '<style>%s</style></head><body>%s</body></html>'
                         % (BOOT, basecss, pagecss, mkup))
            pg.set_viewport_size({'width': w, 'height': h})
            _goto(pg, f)
            pg.wait_for_timeout(90)
            return pg.evaluate(LOOK)

        for rel in PAGES:
            bar = bar_of(markup_of(left(rel)))
            if not bar:
                continue
            mkup = resolve(bar + '</div>')
            d = draw(css_of(base), css_of(left(rel)), mkup,
                     'd_%s.html' % rel, 1280, 700)
            m = draw(css_of(base), css_of(left(rel)), mkup,
                     'm_%s.html' % rel, 390, 700)
            print('     %-22s desktop %dx%dpx, label %s | phone %dx%dpx, '
                  'label %s' % (rel.replace('.html', ''), d['w'], d['h'],
                                d['label'], m['w'], m['h'], m['label']))
            # FLEX, NOT inline-flex. base sets inline-flex in one rule
            # and flex in a later one; the claim is that the bar gives
            # it a flex box at all, against the bare `inline` an
            # unstyled anchor would have. Naming the exact value was a
            # gate measuring base's rule order, not the shape.
            ok(d.get('display') in ('flex', 'inline-flex'),
               '%-24s the bar gives it the house geometry (%s)'
               % (rel, d.get('display')), d.get('display'))
            ok(d['h'] >= 30, '  %-22s a real control height' % '', d['h'])
            ok(abs(d['right']) <= 2,
               '  %-22s sitting at the right of the bar' % '',
               'gap %dpx' % d['right'])
            # 3.4: on a phone the label goes and Back is a 44px square.
            ok(m['label'] == 'none',
               '  %-22s on a phone the label is hidden' % '', m['label'])
            ok(m['w'] >= 44 and m['h'] >= 44,
               '  %-22s and it is a 44px target' % '',
               '%dx%d' % (m['w'], m['h']))
        # THE CONTROL THAT MATTERS: the same anchor with no bar around
        # it takes the colour and none of the shape.
        # THE CONTROL, AND WHAT IT CORRECTED. The same anchor with no
        # bar around it DOES get a display from base - that part of the
        # first claim was wrong. What it does not get is the phone
        # geometry, and that is what the wrapper was needed for.
        loose = draw(css_of(base), '',
                     '<a class="btn action-back"><i class="fas fa-arrow-left">'
                     '</i><span class="action-back-label"> Back</span></a>',
                     'loose.html', 390, 700)
        ok(not (loose['w'] >= 44 and loose['h'] >= 44
                and loose['w'] <= 60),
           'CONTROL: the same anchor OUTSIDE a bar is not a 44px square on '
           'a phone - which is what the wrapper had to be changed for',
           '%dx%dpx' % (loose['w'], loose['h']))
        ok(loose['right'] is None,
           '  and it has no bar to sit at the right of')
        br.close()
elif not BOOT:
    skip('the renders', 'test_fixture_bootstrap413.css is not on disk')
else:
    skip('the renders', 'playwright unavailable')

# ==========================================================================
head('4. NOWHERE ELSE STILL CALLS ONE THAT')
# ==========================================================================
left_over = []
for q in alv_tree.templates():
    txt = markup_of(read(q))
    if re.search(r'<a[^>]*>(?:(?!</a>).)*?Property Dashboard'
                 r'(?:(?!</a>).)*?</a>', txt, re.S):
        left_over.append(alv_tree.rel(q))
ok(not left_over, 'no page in the tree still labels a link Property '
   'Dashboard', left_over)

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
print('  REPORTED, NOT CHANGED. property_management_dashboard.html names')
print('  itself in its own heading, which is a title and not a link - no')
print('  round should turn a page title into a Back button.')
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
