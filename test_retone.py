# -*- coding: utf-8 -*-
"""test_retone.py - Section R round R1, 30 Sep 2026.

The last of the green. Forty-four controls wore Bootstrap's btn-success,
btn-warning or btn-outline-success, and base's standards block says why
they had been left alone:

    THE BUTTON FAMILIES ARE DELIBERATELY NOT ANSWERED ... An action takes
    .action-primary or .action-secondary, BY WEIGHT.

So this round tints nothing. It reads each control and gives it the
weight its consequence deserves - the rule Demetri agreed for CRS and
again for the mapping of 29 Sep, with the last two calls answered on
30 Sep.

SECTION 4 IS THE ONE THAT MATTERS: a retoned button is drawn in Chromium
beside a button that was already correct, and the two are compared. A
round about weight that left a control looking different from the house
control it is meant to be would have failed at the only thing it set out
to do.
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
    from alv_rounds import ROUNDS
except Exception:
    ROUNDS = []

SUFFIX = '.bak_retone'
ME = 'test_retone.py'
PATCHER = 'apply_retone.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
FAM = re.compile(r'\bbtn-(?:outline-)?(?:success|warning)\b')
LEFT = 'property_assets.html'
DEEDS = 'title_deeds_management.html'
ADMIN = 'user_administration.html'
NOTIF = 'personal_notification_settings.html'

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


def nocom(t):
    """Comments out, all four kinds. base's standards block NAMES every
    one of these classes in prose several times over, and so does this
    round's own patcher."""
    t = re.sub(r'<!--.*?-->|\{#.*?#\}', '', t, flags=re.S)
    t = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', '', t,
               flags=re.S | re.I)
    return re.sub(r'/\*.*?\*/', '', t, flags=re.S)


def css_of(t):
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S))


# The table the round worked from, read off the patcher so the two agree.
patcher = read(os.path.join(ROOT, PATCHER))
CLASSES = {}
for _n in ast.walk(ast.parse(patcher)):
    if (isinstance(_n, ast.Assign) and _n.targets
            and getattr(_n.targets[0], 'id', '') == 'CLASSES'):
        CLASSES = ast.literal_eval(_n.value)
        break

base = read(alv_tree.path_of('base.html'))
BOOT = ''
_b = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
if os.path.isfile(_b):
    BOOT = read(_b)

print('=' * 74)
print('%s - R1, TONE BY CONSEQUENCE' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE GREEN IS GONE')
# ==========================================================================
left = {}
for p in alv_tree.templates():
    rel = alv_tree.rel(p)
    if rel == 'base.html':
        continue
    hits = FAM.findall(nocom(read(p)))
    if hits:
        left[rel] = len(hits)
# NONE LEFT SINCE D3, 30 Sep 2026. R1 left three behind on
# property_assets - the + buttons welded into an input group, which
# Show-ButtonDrift excluded by name because Bootstrap owned their
# geometry. Demetri looked straight at them and asked why they were
# green, so base gained .action-field-add and they took it: Bootstrap
# still owns the geometry, which is what the exclusion protected, but
# not the colour. See test_field_add.py.
#
# An EXACT empty, not a floor: a Bootstrap tone reappearing anywhere is
# the whole thing this round exists to notice.
ok(not left,
   'no Bootstrap tone is left anywhere in the tree - R1 took forty-four '
   'and D3 took the last three', left)
ok(not re.search(r"className = 'btn btn-(?:success|warning|danger)'",
                 nocom(read(alv_tree.join(ADMIN)))),
   'and no page assigns one in script either')

was_total = 0
for rel in sorted(CLASSES):
    p = alv_tree.join(rel.replace('/', os.sep)) + SUFFIX
    if os.path.isfile(p):
        was_total += len(FAM.findall(nocom(read(p))))
ok(was_total >= 35,
   'CONTROL: the backups carry %d of them' % was_total, was_total)

# ==========================================================================
head('2. EVERY ONE, BY NAME')
# ==========================================================================
# A CONTROL A LATER ROUND REMOVED - PU-1b, 3 Oct 2026.
#
# This suite records what RE-TONE swapped and checks the NEW class is
# still there. RE-1 did not re-green the Create/Edit Recipe save - it
# DELETED it, because the save moved into the action bar. The claim that
# matters, "nothing wears the old class", is still true; "the new class is
# still present" never was the point and cannot survive a round that
# removes the element.
#
# So a removal is ALLOWED ONLY WHEN IT IS NAMED, and the old class must
# still be absent. An element that disappears without a line here still
# fails, which is what keeps this a gate.
REMOVED_BY = {
    ('preview_imported_recipe.html', 'btn action-primary btn-lg'):
        'RE-1, 3 Oct 2026 - the save moved to the action bar',
}

total = 0
for rel in sorted(CLASSES):
    t = read(alv_tree.join(rel.replace('/', os.sep)))
    good = []
    for was, now, n, what in CLASSES[rel]:
        c = t.count('class="%s"' % now)
        gone = (rel, now) in REMOVED_BY
        if gone:
            # Named as removed: the new class may be absent, but the OLD
            # one must not have come back in its place.
            good.append(c == 0 and t.count('class="%s"' % was) == 0)
        else:
            good.append(c >= n)
        total += n
    ok(all(good), '%-36s %d control(s)'
       % (rel, sum(n for _w, _n, n, _l in CLASSES[rel])),
       [(w, n) for (w, n, _c, _l), g in zip(CLASSES[rel], good) if not g])
ok(total == 41,
   'forty-one by class name, plus three the round handled one at a time',
   total)

# WEIGHT, NOT TINT. The round must not have painted anything.
painted = []
for rel in sorted(CLASSES):
    t = read(alv_tree.join(rel.replace('/', os.sep)))
    for m in re.finditer(r'(?:^|[,{}\s])\.(action-primary|action-secondary)'
                         r'\s*\{([^}]*)\}', nocom(css_of(t)), re.M):
        if re.search(r'(?<!-)\b(background|color)\s*:', m.group(2)):
            painted.append('%s .%s' % (rel, m.group(1)))
ok(not painted,
   'and NOT ONE page paints .action-primary or .action-secondary - this '
   'round gave weight, not colour, which is the rule base states', painted)

# ==========================================================================
head('3. THE THREE THE ROUND HANDLED ONE AT A TIME')
# ==========================================================================
t = read(alv_tree.join(DEEDS))
mk = re.sub(r'<(script|style)\b.*?</\1>', '', nocom(t), flags=re.S)
m = re.search(r'<button[^>]*icon-action-btn[^>]*>.*?</button>', mk, re.S)
ok(m is not None, '%s: View is a row action now' % DEEDS)
if m:
    b = ' '.join(m.group(0).split())
    # .icon-document, NOT .icon-view - RA-2, 5 Oct 2026.
    #
    # R2 put this control in the row wearing .icon-view and left it on
    # fa-scroll, and the two lines here recorded that pair. RA-2 found
    # .icon-view wearing FOUR different glyphs across the tree - an eye,
    # an invoice, a PDF and this scroll - and gave each picture its own
    # name. Opening a title deed is .icon-document on fa-file-contract
    # now, which is the same colour and the same place in the row.
    #
    # The CLAIM of R2's section 3 is untouched by that: View became a
    # row action, it is named, and it sits in the action cell it was
    # already in. Only the spelling of the name moved, and this suite
    # tracks the live tree and records later rounds by name - D3 and
    # RB-1 are both already in here the same way.
    ok('icon-document' in b, '  wearing .icon-document, which base declares')
    ok('title=' in b and 'aria-label=' in b,
       '  and named - an icon-only control with no label is a control '
       'nobody can read', b[:90])
    ok('fa-file-contract' in b,
       '  drawing fa-file-contract - a document, which is what a title '
       'deed is, and the glyph .icon-document carries everywhere')
    i_cell = mk.rfind('desktop-action-cell', 0, mk.index('icon-action-btn'))
    ok(i_cell > 0,
       '  in the .desktop-action-cell it was already sitting in')
bak = alv_tree.join(DEEDS) + SUFFIX
if os.path.isfile(bak):
    ok('btn btn-sm btn-success' in read(bak),
       '  CONTROL: it was a green word-button in that cell')
else:
    skip('the deeds control', 'no backup')

t = read(alv_tree.join(ADMIN))
ok("submitBtn.className = 'btn action-primary';" in t,
   '%s: Enable is the house primary' % ADMIN)
ok("submitBtn.className = 'btn action-danger';" in t,
   '  and Disable the house danger - a user losing access is the '
   'destructive half of that pair')
bak = alv_tree.join(ADMIN) + SUFFIX
if os.path.isfile(bak):
    ok("'btn btn-success'" in read(bak) and "'btn btn-danger'" in read(bak),
       '  CONTROL: both were Bootstrap before')
else:
    skip('the admin control', 'no backup')

t = read(alv_tree.join(NOTIF))
ok('.notification-card .btn-success' not in nocom(t),
   '%s: the rule with nothing to reach is gone' % NOTIF)
ok(len(re.findall(r'class="[^"]*\bbtn-success\b', nocom(t))) == 0,
   '  and the page really had no such element - that is why it was dead')
ok(len(re.findall(r'class="[^"]*\baction-primary\b', nocom(t))) >= 2,
   '  its Save buttons wear .action-primary, which an earlier round gave '
   'them and this rule was never told about')
ok('.page-action-buttons .action-primary' in nocom(css_of(base)),
   '  and base says the same thing for the class they wear now')

# ==========================================================================
head('4. CHROMIUM: A RETONED BUTTON IS THE HOUSE BUTTON')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)

if HAVE_PW and BOOT:
    fx = os.path.join(SCRATCH, 'retone.html')
    page_css = css_of(read(alv_tree.join('view_recipe.html')))
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><html><head><meta charset="utf-8">'
                 '<style>%s</style><style>%s</style><style>%s</style>'
                 '</head><body><div class="page-action-buttons">'
                 '<button class="btn action-primary" id="house">Add New'
                 '</button>'
                 '<button class="btn action-primary" id="retoned">'
                 'Save &amp; Recalculate</button>'
                 '<button class="btn action-secondary" id="sec">Email'
                 '</button>'
                 '<button class="btn btn-success" id="green">was green'
                 '</button>'
                 '</div></body></html>' % (BOOT, css_of(base), page_css))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1280, 'height': 400})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        _goto(pg, fx)
        pg.wait_for_timeout(180)
        seen = pg.evaluate('''() => {
            const g = id => {
              const c = getComputedStyle(document.getElementById(id));
              return [c.backgroundColor, c.color, c.borderTopColor,
                      c.fontWeight, c.height];
            };
            return {house: g("house"), retoned: g("retoned"),
                    sec: g("sec"), green: g("green")};
        }''')
        ok(seen['retoned'] == seen['house'],
           'a retoned primary is IDENTICAL to a primary that was already '
           'right - same fill, same ink, same border, same weight, same '
           'height', seen)
        ok(seen['sec'] != seen['house'],
           '  and a secondary is not a primary - weight still means '
           'something', seen['sec'])
        ok(seen['retoned'][0] != seen['green'][0],
           '  and neither is the green it used to be', seen['green'])
        ok('rgb(179, 38, 30)' not in seen['retoned']
           and 'rgb(179, 38, 30)' not in seen['sec'],
           'and nothing in this round came out RED - not one of the '
           'forty-four deletes anything, so none of them is a danger')
        br.close()
else:
    skipped += 4

# ==========================================================================
head('5. THE HOUSE\'S OWN DRIFT SCANNER')
# ==========================================================================
import subprocess
drift = os.path.join(ROOT, 'Show-ButtonDrift.py')
if os.path.isfile(drift):
    try:
        r = subprocess.run([sys.executable, drift, '--strict'],
                           capture_output=True, text=True, timeout=600)
        ok(r.returncode == 0,
           'Show-ButtonDrift --strict, the scanner the push gate runs, '
           'still reports nothing drifting', r.stdout[-400:])
        n = re.search(r'(\d+) button\(s\) are deliberately left alone',
                      r.stdout)
        if n:
            print('     %s buttons are deliberately left alone, one fewer '
                  'than before -' % n.group(1))
            print('     the title-deed View joined the row actions.')
    except Exception as e:
        skip('the drift scanner', str(e)[:60])
else:
    skip('the drift scanner', 'Show-ButtonDrift.py not on disk')

# ==========================================================================
head('6. REPORTED, NOT CHANGED')
# ==========================================================================
t = read(alv_tree.join(LEFT))
ok(len(FAM.findall(nocom(t))) == 0,
   '%s gave up its three as well - D3, 30 Sep' % LEFT)
ok('input-group-append' in nocom(t),
   '  and they are still welded into an input group, which is why only '
   'their colour moved and their geometry did not')
ok('action-field-add' in nocom(t),
   '  wearing base\'s .action-field-add now')
adm = nocom(read(alv_tree.join(ADMIN)))
ok("'modal-header bg-success text-white'" in adm,
   'RECORDED: %s still paints its confirm modal header bg-success and '
   'bg-danger in script, where base has .alv-modal-head and '
   '--danger. That is a component question, not a button one, and it is '
   'the next thing on this page.' % ADMIN)

# ==========================================================================
head('7. THE GATE')
# ==========================================================================
ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(ME in t, 'this suite is on the gate  %s' % PS1)
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the patcher is not - a gate runs suites, not rounds')
else:
    skip('the gate', '%s not on disk' % PS1)
    skip('the gate', '%s not on disk' % PS1)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('')
print('  NOT PROVED HERE: that every one of the forty-four was given the')
print('  RIGHT weight. That is a judgement, made control by control in the')
print('  mapping Demetri reviewed on 29 Sep and signed off on 30 Sep; what')
print('  this suite proves is that each one now carries the class that')
print('  mapping names, and that the class does what base says it does.')
print('=' * 74)
sys.exit(1 if failed else 0)
