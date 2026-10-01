# -*- coding: utf-8 -*-
"""test_secondary_scope.py - Section I round I2, 30 Sep 2026.

Demetri, on Project Detail at 386px: "Where do I add the Task or Subtask?
Can't see the buttons on Mobile."

Because they were display: none. Three pages in the Projects module
carried `.action-secondary { display: none; }` inside their phone block,
UNSCOPED - a copy of base's rule with the scope dropped, and the scope
was the whole of it:

    .page-action-buttons:has(.action-more-btn) .action-secondary

base hides a secondary only inside a bar that HAS a More menu, because
the menu is where that action went. A secondary anywhere else has nowhere
to go, so hiding it removes the action outright.

ON projects_detail THAT WAS TEN CONTROLS: Gantt Chart, Duplicate
Project, Add Task, Add Subtask, Add First Task, four modal Cancels and a
Delete confirmation. Five of the ten are inside modals, so that page has
had dialogs on a phone that could be opened and not answered.

SECTION 3 IS THE CLAIM, and it has two halves that pull in opposite
directions - which is why a render rather than a reading. In a bar WITH
a More menu the secondary must STILL be hidden, because base's rule is
doing its job. Outside a bar it must be visible again. Measured:

    before   bar Help: none        Add Task: none
    after    bar Help: none        Add Task: inline-block
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

SUFFIX = '.bak_secscope'
ME = 'test_secondary_scope.py'
PATCHER = 'apply_secondary_scope.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)
PAGES = ('projects/project_task_list.html', 'projects/projects.html',
         'projects/projects_detail.html')
# What projects_detail stopped hiding. Named, because "ten controls" is a
# number and these are the things Demetri could not reach.
DETAIL = ('Gantt Chart', 'Duplicate Project', 'Add Task', 'Add Subtask',
          'Add First Task')

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


def unscoped_hides(css):
    """Every rule that hides a secondary from OUTSIDE an action bar."""
    out = []
    for m in re.finditer(r'([^{}]*\.action-secondary[^{}]*)\{([^}]*)\}', css):
        sel = ' '.join(m.group(1).split())
        if 'display: none' not in ' '.join(m.group(2).split()):
            continue
        if 'page-action-buttons' in sel:
            continue          # scoped to a bar, which is base's own shape
        out.append(sel[:70])
    return out


def secondaries(text):
    b = markup_of(text)
    out = []
    for m in re.finditer(r'<a[^>]*class="[^"]*action-secondary[^"]*"[^>]*>'
                         r'(.*?)</a>'
                         r'|<button[^>]*class="[^"]*action-secondary[^"]*"'
                         r'[^>]*>(.*?)</button>', b, re.S):
        txt = ' '.join((m.group(1) or m.group(2) or '').split())
        out.append(re.sub(r'<[^>]+>', '', txt).strip()[:24] or '(icon only)')
    return out


base = read(alv_tree.path_of('base.html'))

print('=' * 74)
print('%s - I2, A HIDE THAT LOST ITS SCOPE' % ME)
print('=' * 74)

# ==========================================================================
head('1. base HAS THE SCOPED RULE, AND NO PAGE HAS AN UNSCOPED ONE')
# ==========================================================================
bcss = css_of(base)
ok(bool(re.search(r'\.page-action-buttons:has\(\.action-more-btn\)\s*'
                  r'\.action-secondary\s*\{[^}]*display\s*:\s*none', bcss)),
   'base hides a secondary ONLY inside a bar that has a More menu')
# TREE-WIDE, and written to catch the fourth rather than confirm the three.
bad = {}
for q in alv_tree.templates():
    if os.path.basename(q) == 'base.html':
        continue
    hits = unscoped_hides(css_of(read(q)))
    if hits:
        bad[alv_tree.rel(q)] = hits
ok(not bad,
   'and not one page in the tree hides a secondary from outside a bar',
   '\n'.join('%s: %s' % (k, v[0]) for k, v in list(bad.items())[:4]))

# ==========================================================================
head('2. THE THREE, AND WHAT EACH STOPPED HIDING')
# ==========================================================================
for rel in PAGES:
    p = alv_tree.join(rel.replace('/', os.sep))
    bak = p + SUFFIX
    ok(not unscoped_hides(css_of(left(rel))),
       '%-38s hides nothing outside a bar' % rel)
    if not os.path.isfile(bak):
        skip(rel, 'no %s backup' % SUFFIX)
        continue
    was = read(bak)
    ok(len(unscoped_hides(css_of(was))) == 1,
       '  %-36s CONTROL: it had exactly one' % '',
       unscoped_hides(css_of(was)))
    # THE PAGE MUST HAVE A MORE MENU, or base's scoped rule would leave
    # its bar secondaries on screen and this round would have changed
    # the bar as well as the page.
    ok('action-more' in markup_of(left(rel)),
       '  %-36s and it has a More menu, so the bar is unchanged' % '')
    # THE MARKUP DID NOT MOVE.
    strip = lambda s: re.sub(r'<style\b.*?</style>', '', s, flags=re.S)
    ok(strip(was) == strip(left(rel)),
       '  %-36s markup byte-identical' % '')

lost = secondaries(left('projects/projects_detail.html'))
ok(len(lost) == 10,
   'projects_detail carries ten secondaries, and all ten were hidden',
   '%d: %s' % (len(lost), lost))
for name in DETAIL:
    ok(name in lost, '  %-36s is one of them' % name)
ok(lost.count('Cancel') == 4,
   '  and four of them are modal Cancels - dialogs that could be opened '
   'and not answered', lost.count('Cancel'))

# ==========================================================================
head('3. CHROMIUM: THE BAR STILL HIDES, THE PAGE DOES NOT')
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

# A bar WITH a More menu, and a secondary out in the content. The two
# have to behave differently, which is the whole point of the scope.
MK = ('<div class="page-action-buttons">'
      '<a class="btn action-primary">Add</a>'
      '<a class="btn action-secondary" id="inbar">Help</a>'
      '<button class="btn action-more-btn" id="more">...</button>'
      '<a class="btn action-back">Back</a></div>'
      '<div class="content">'
      '<a class="btn action-secondary btn-sm" id="addtask">Add Task</a>'
      '</div>')
LOOK = '''() => ({
  inbar: getComputedStyle(document.getElementById("inbar")).display,
  addtask: getComputedStyle(document.getElementById("addtask")).display,
  more: getComputedStyle(document.getElementById("more")).display})'''

if HAVE_PW and BOOT:
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 386, 'height': 700})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        def draw(pcss, name):
            f = os.path.join(SCRATCH, name)
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write('<!doctype html><html><head><meta charset="utf-8">'
                         '<style>%s</style><style>%s</style>'
                         '<style>%s</style></head><body>%s</body></html>'
                         % (BOOT, css_of(base), pcss, MK))
            _goto(pg, f)
            pg.wait_for_timeout(90)
            return pg.evaluate(LOOK)

        for rel in PAGES:
            p = alv_tree.join(rel.replace('/', os.sep))
            bak = p + SUFFIX
            now = draw(css_of(left(rel)), 'n_%s.html' % rel.replace('/', '_'))
            name = rel.split('/')[-1].replace('.html', '')
            ok(now['addtask'] != 'none',
               '%-26s a secondary in the CONTENT is visible on a phone'
               % name, now['addtask'])
            ok(now['inbar'] == 'none',
               '  %-24s and one in the BAR is still hidden - base\'s rule '
               'still works' % '', now['inbar'])
            ok(now['more'] != 'none',
               '  %-24s with the More menu there to hold it' % '',
               now['more'])
            if os.path.isfile(bak):
                was = draw(css_of(read(bak)),
                           'w_%s.html' % rel.replace('/', '_'))
                ok(was['addtask'] == 'none',
                   '  %-24s CONTROL: before, the content one was hidden too'
                   % '', was['addtask'])
        br.close()
elif not BOOT:
    skip('the renders', 'test_fixture_bootstrap413.css is not on disk')
else:
    skip('the renders', 'playwright unavailable')

# ==========================================================================
head('4. REPORTED, NOT CHANGED')
# ==========================================================================
# Three pages scope the same hide correctly and are none of this round's
# business - they are named so that "no page hides a secondary" above is
# read as "outside a bar", which is what it says.
for rel in ('properties_edit.html', 'tenant_edit.html',
            'recipe_management.html'):
    p = alv_tree.path_of(rel)
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    hits = [m for m in re.finditer(r'([^{}]*\.action-secondary[^{}]*)\{'
                                   r'([^}]*)\}', css_of(read(p)))
            if 'display: none' in ' '.join(m.group(2).split())]
    ok(bool(hits) and not os.path.isfile(p + SUFFIX),
       '%-28s scopes its own hide, and was not touched' % rel)
print('')
print('  AND THE MOBILE CARDS ON projects_detail ARE THE PAGE\'S OWN, not')
print('  base\'s .mobile-action-bar - Edit and Delete are coloured squares')
print('  rather than the house row actions. Demetri asked whether they are')
print('  standard. They are not, and that is a conversion the size of P1,')
print('  not a line in this round.')

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
