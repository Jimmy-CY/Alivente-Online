# -*- coding: utf-8 -*-
"""test_field_add.py - Section D round D3, 30 Sep 2026.

Demetri, on the Add New Asset panel: "Why are these + buttons in green.
They should be in teal."

Three of them on property_assets - add a category, add a subcategory,
add a supplier - all raw btn-outline-success, with not one line of CSS on
the page. They were green because nothing had ever decided otherwise.

THE PART WORTH READING TWICE. Show-ButtonDrift listed input-group-append
under LEAVE - "welded to an input; Bootstrap owns the geometry" - so the
drift report said "Nothing drifting" over three green buttons, week after
week, while Demetri was looking straight at them. A tool that reports a
decision has to report the decision that was actually made, and that one
had quietly stopped being defensible.

SECTION 3 IS THE MEASUREMENT. Chromium draws the panel before and after,
with Bootstrap loaded, and reads the button back: the green must be gone,
the accent must be there, and the SIZE must not have moved by a pixel -
because the geometry is the thing the LEAVE note was protecting and the
one thing this round must not disturb.
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


def _goto(pg, path):
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------
import ast
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

SUFFIX = '.bak_fieldadd'
ME = 'test_field_add.py'
PATCHER = 'apply_field_add.py'
PS1 = 'Push-PendingChanges.ps1'
DRIFT = 'Show-ButtonDrift.py'
PAGE = 'property_assets.html'
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)
ACCENT = 'rgb(14, 124, 139)'          # --alv-accent #0e7c8b
BOOTSTRAP_GREEN = 'rgb(40, 167, 69)'  # what btn-outline-success paints

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
    """Lesson 21. This round ships a long comment in base that names
    every selector below, and another in the drift tool."""
    return re.sub(r'/\*.*?\*/', ' ', re.sub(r'<!--.*?-->', '', s, flags=re.S),
                  flags=re.S)


def css_of(t):
    return no_comments('\n'.join(STYLE.findall(t)))


def markup_of(t):
    return re.sub(r'<(script|style)\b.*?</\1>', '',
                  re.sub(r'<!--.*?-->', '', t, flags=re.S), flags=re.S)


def left(rel):
    p = alv_tree.path_of(rel)
    return (as_left_by(p, SUFFIX, read) if as_left_by else read(p))


base_left = left('base.html')
page_left = left(PAGE)

print('=' * 74)
print('%s - D3, A SMALL ADD BUTTON WELDED TO A FIELD' % ME)
print('=' * 74)

# ==========================================================================
head('1. base HAS A NAME FOR IT NOW')
# ==========================================================================
css = css_of(base_left)
sels = {}
for m in re.finditer(r'([^{}]+)\{([^}]*)\}', css):
    sels[' '.join(m.group(1).split())] = m.group(2)
ok('.btn.action-field-add' in sels, 'base declares .btn.action-field-add')
ok('.btn.action-field-add:hover, .btn.action-field-add:focus' in sels,
   '  and a hover that fills rather than tints')
body = sels.get('.btn.action-field-add', '')
ok('var(--alv-accent)' in body, '  painted from the accent token', body)
ok(not re.search(r'#[0-9a-fA-F]{3,8}\b', body),
   '  with no literal colour', body)
# IT MUST NOT SET GEOMETRY. Bootstrap owns that here, and that is
# precisely why this button was left alone for so long.
geo = [k for k in ('width', 'height', 'min-width', 'padding', 'display')
       if re.search(r'\b' + k + r'\s*:', body)]
ok(not geo, '  and it sets no geometry - Bootstrap still owns that', geo)

# ==========================================================================
head('2. THE THREE WEAR IT, AND NOTHING ELSE CHANGED')
# ==========================================================================
mk = markup_of(page_left)
ok(mk.count('action-field-add') == 3,
   'three + buttons wear the new name', mk.count('action-field-add'))
ok('btn-outline-success' not in mk, '  and not one green one survives')
ok(len(re.findall(r'class="btn action-field-add"', mk)) == 3,
   '  each keeps the btn class, so the geometry comes with it')
ok(mk.count('input-group-append') >= 3,
   '  and each is still welded to its field')
ok(not re.search(r'\.action-field-add\b[^{}]*\{', css_of(page_left)),
   '  the page writes no rule of its own - base owns this')
bak = alv_tree.path_of(PAGE) + SUFFIX
if os.path.isfile(bak):
    was = read(bak)
    ok(was.count('btn-outline-success') == 3,
       'CONTROL: it really was three green ones before',
       was.count('btn-outline-success'))
    # NOTHING BUT THE CLASS NAME. Compared with the whitespace gone, so
    # a reflow could not hide an edit.
    strip = lambda s: re.sub(r'\s+', '', s)
    ok(strip(was).replace('btn btn-outline-success', 'btnaction-field-add')
       .replace('btnbtn-outline-success', 'btnaction-field-add')
       == strip(page_left),
       '  and the page changed by the class name and nothing else')
else:
    skip('the before and after', 'no %s backup' % SUFFIX)

# ==========================================================================
head('3. CHROMIUM: THE GREEN IS GONE AND THE SIZE IS NOT')
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

FIXTURE = ('<div class="input-group">'
           '<select class="form-control"><option>Select Category</option>'
           '</select>'
           '<div class="input-group-append">'
           '<button type="button" class="%s" id="b">'
           '<i class="fas fa-plus"></i></button>'
           '</div></div>')

LOOK = '''() => {
  const b = document.getElementById("b");
  const s = document.querySelector("select");
  const c = getComputedStyle(b), r = b.getBoundingClientRect();
  return {colour: c.color, border: c.borderTopColor, bg: c.backgroundColor,
          w: Math.round(r.width), h: Math.round(r.height),
          field: Math.round(s.getBoundingClientRect().height)};
}'''

if HAVE_PW and BOOT and os.path.isfile(bak):
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 560, 'height': 500})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        def draw(basecss, cls, name):
            f = os.path.join(SCRATCH, name)
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write('<!doctype html><html><head><meta charset="utf-8">'
                         '<style>%s</style><style>%s</style></head><body>%s'
                         '</body></html>'
                         % (BOOT, basecss, FIXTURE % cls))
            _goto(pg, f)
            pg.wait_for_timeout(60)
            return pg.evaluate(LOOK)

        a = draw(css_of(read(alv_tree.path_of('base.html') + SUFFIX)),
                 'btn btn-outline-success', 'was.html')
        b_ = draw(css_of(base_left), 'btn action-field-add', 'now.html')
        print('     before  %-22s %dx%dpx, field %dpx'
              % (a['colour'], a['w'], a['h'], a['field']))
        print('     after   %-22s %dx%dpx, field %dpx'
              % (b_['colour'], b_['w'], b_['h'], b_['field']))
        ok(a['colour'] == BOOTSTRAP_GREEN,
           'CONTROL: it really was Bootstrap green', a['colour'])
        ok(b_['colour'] == ACCENT, 'it is the house accent now', b_['colour'])
        ok(b_['border'] == ACCENT, '  and so is its border', b_['border'])
        ok('green' not in b_['colour'] and b_['colour'] != BOOTSTRAP_GREEN,
           '  with no green left anywhere on it')
        # THE GEOMETRY IS THE THING THIS ROUND MUST NOT MOVE.
        ok((a['w'], a['h']) == (b_['w'], b_['h']),
           '  and it is exactly the same size as before',
           'was %dx%d, now %dx%d' % (a['w'], a['h'], b_['w'], b_['h']))
        ok(abs(b_['h'] - b_['field']) <= 1,
           '  still the height of the field it is welded to',
           '%dpx against %dpx' % (b_['h'], b_['field']))
        br.close()
elif not BOOT:
    skip('the renders', 'test_fixture_bootstrap413.css is not on disk - a '
                        'fixture without Bootstrap cannot show what '
                        'btn-outline-success was painting')
elif not os.path.isfile(bak):
    skip('the renders', 'no %s backup' % SUFFIX)
else:
    skip('the renders', 'playwright unavailable')

# ==========================================================================
head('4. THE DRIFT TOOL REPORTS THE DECISION THAT WAS MADE')
# ==========================================================================
d = os.path.join(ROOT, DRIFT)
if not os.path.isfile(d):
    skip('the drift tool', 'not on disk')
else:
    t = read(d)
    try:
        ast.parse(t)
        ok(True, '%s parses' % DRIFT)
    except SyntaxError as e:
        ok(False, '%s parses' % DRIFT, e)
    ok("'input-group-append':" in re.sub(r'#.*', '', t),
       '  the LEAVE entry survives - seven welded buttons still need it')
    ok('action-field-add' in t,
       '  and its note names what replaced the three that left')
    # THE NOTE IS A COMMENT, NOT A RULE. A round that changed the
    # tool's behaviour while claiming to annotate it would be hiding an
    # edit in a comment.
    # AS THE FIELD-ADD ROUND LEFT IT - PM-1, 3 Oct 2026. This read the
    # tool as it stands now, so every later round that touches it breaks
    # a claim about this one. PN-1 added is_chooser on 3 Oct and did
    # exactly that. as_left_by walks forward to the next backup and
    # returns the file as THIS round left it.
    #
    # The file's own left() does this for templates; the drift tool is
    # not a template, so it is spelled out here.
    left_drift = (as_left_by(d, SUFFIX, read) if as_left_by else read(d))
    code = re.sub(r'#.*', '', left_drift)
    if os.path.isfile(d + SUFFIX):
        was_code = re.sub(r'#.*', '', read(d + SUFFIX))
        ok(re.sub(r'\s+', '', code) == re.sub(r'\s+', '', was_code),
           '  and only the comment changed - the tool itself is untouched')
    else:
        skip('the tool diff', 'no %s backup' % SUFFIX)

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
print('  REPORTED, NOT CHANGED. Seven buttons remain under the LEAVE entry')
print('  this round narrowed - welded to an input, and Bootstrap still')
print('  owning both their geometry and their colour. Nobody has asked')
print('  about those, so they stay named rather than quietly restyled.')
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
