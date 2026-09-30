# -*- coding: utf-8 -*-
"""test_filter_frame.py - Section H round H1, 30 Sep 2026.

base has owned the FIELD inside the house filter panel since 23 Sep. It
owned none of the FRAME, and nine pages wrote that out themselves -
thirty-one rules saying three things, with four pages declaring the
header TWICE and the first declaration never rendering at all.

SECTION 3 IS THE ONE THAT MATTERS. The claim is that what renders does
not move except where this round says it does, so every one of the nine
panels is drawn in Chromium before and after, with its own stylesheet,
and the two are compared declaration by declaration.

SECTION 4 IS THE DEFECT. Seven of the nine headers said cursor: pointer,
two lit up on hover, and five carried a stopPropagation on the Clear All
button - and NOT ONE of the nine binds a click to .filter-header. The
guard is the proof: it exists to stop a click reaching a parent handler,
and there is no parent handler left.
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

SUFFIX = '.bak_filterframe'
ME = 'test_filter_frame.py'
PATCHER = 'apply_filter_frame.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)
FRAME = ('.filter-grid', '.filter-header', '.filter-title')

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
    return '\n'.join(STYLE.findall(t))


def decls(body):
    out = {}
    for d in body.split(';'):
        if ':' in d:
            k, v = d.split(':', 1)
            out[k.strip()] = ' '.join(v.split())
    return out


def top_level(text, sel):
    """Every rule for EXACTLY this selector at the top level of a style
    block. The round's own helper, because a suite that measured a
    different set of rules from the round would be testing agreement
    rather than correctness."""
    pat = re.compile(r'(?:(?<=^)|(?<=[,{}\s]))' + re.escape(sel)
                     + r'\s*\{[^{}]*\}', re.M)
    hits = []
    for sm in STYLE.finditer(text):
        bare = re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)),
                      sm.group(1), flags=re.S)
        for m in pat.finditer(bare):
            if (bare.count('{', 0, m.start())
                    - bare.count('}', 0, m.start())) == 0:
                hits.append(m.group(0))
    return hits


def effective(text, sel):
    d = {}
    for r in top_level(text, sel):
        d.update(decls(r[r.index('{') + 1:-1]))
    return d


# The nine, and what each keeps - read off the patcher so the two agree.
import ast as _ast
patcher = read(os.path.join(ROOT, PATCHER))
PANELS = {}
for _n in _ast.walk(_ast.parse(patcher)):
    if (isinstance(_n, _ast.Assign) and _n.targets
            and getattr(_n.targets[0], 'id', '') == 'PANELS'):
        PANELS = _ast.literal_eval(_n.value)
        break
HOUSE = {}
for _n in _ast.walk(_ast.parse(patcher)):
    if (isinstance(_n, _ast.Assign) and _n.targets
            and getattr(_n.targets[0], 'id', '') == 'HOUSE'):
        HOUSE = dict((k, dict(v)) for k, v in
                     _ast.literal_eval(_n.value).items())
        break

base = read(alv_tree.path_of('base.html'))
BOOT = ''
_b = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
if os.path.isfile(_b):
    BOOT = read(_b)

print('=' * 74)
print('%s - H1, THE FILTER PANEL\'S FRAME' % ME)
print('=' * 74)

# ==========================================================================
head('1. base OWNS THE FRAME NOW')
# ==========================================================================
ok(len(PANELS) == 9, 'the round names nine pages', len(PANELS))
for sel in FRAME:
    hits = top_level(base, sel)
    ok(len(hits) == 1, 'base declares %-15s exactly once' % sel, len(hits))
    if hits:
        got = decls(hits[0][hits[0].index('{') + 1:-1])
        ok(got == HOUSE[sel], '  %s' % '; '.join('%s: %s' % kv for kv in
                                                 sorted(got.items()))[:62],
           got)
ok(not re.search(r'#[0-9a-fA-F]{3,8}\b',
                 ' '.join(' '.join(top_level(base, s)) for s in FRAME)),
   'and not one of the three carries a hex - the frame is painted from '
   'tokens')

bak = alv_tree.path_of('base.html') + SUFFIX
if os.path.isfile(bak):
    was = read(bak)
    ok(not any(top_level(was, s) for s in FRAME),
       'CONTROL: before this round base declared none of the three')
else:
    skip('the base control', 'no %s backup' % SUFFIX)

# THE VALUES ARE NOT NEW. This is the claim the round rests on, so it is
# measured rather than asserted: the one page that has been through a
# styling round already said all three, exactly.
cel = alv_tree.path_of('celebration_management.html') + SUFFIX
if os.path.isfile(cel):
    w = read(cel)
    same = []
    for sel in FRAME:
        e = effective(w, sel)
        own = dict((k, v) for k, v in e.items()
                   if k not in PANELS['celebration_management.html'][sel]['keep'])
        same.append((sel, own == HOUSE[sel], own))
    ok(all(s[1] for s in same),
       'AND THE VALUES ARE NOT NEW: celebration_management, the one copy '
       'that has been through a styling round, already said all three '
       'exactly - base adopted the reviewed copy rather than inventing a '
       'look', [(s[0], s[2]) for s in same if not s[1]])
else:
    skip('the reviewed copy', 'no backup of celebration_management')

# ==========================================================================
head('2. THE NINE KEEP ONLY WHAT IS THEIRS')
# ==========================================================================
for rel in sorted(PANELS):
    p = alv_tree.join(rel.replace('/', os.sep))
    t = read(p)
    leftovers = {}
    for sel in FRAME:
        e = effective(t, sel)
        if e:
            leftovers[sel] = e
    want = dict((s, PANELS[rel][s]['keep']) for s in FRAME
                if PANELS[rel].get(s, {}).get('keep'))
    ok(leftovers == want,
       '%-34s %s' % (rel, ('keeps ' + '; '.join(
           '%s %s' % (s.replace('.filter-', ''),
                      ','.join(sorted(v))) for s, v in sorted(want.items())))
           if want else 'keeps nothing'),
       'left %s\nwant %s' % (leftovers, want))

allowed = {'grid-template-columns', 'flex-wrap', 'flex', 'min-width',
           'margin-bottom'}
stray = []
for rel in sorted(PANELS):
    t = read(alv_tree.join(rel.replace('/', os.sep)))
    for sel in FRAME:
        for k in effective(t, sel):
            if k not in allowed:
                stray.append('%s %s %s' % (rel, sel, k))
ok(not stray,
   'and nothing a page kept is something base says - the only survivors '
   'are the column template, a wrap, a flex and one margin', stray)

# ==========================================================================
head('3. CHROMIUM: THE PANELS DO NOT MOVE')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)

PANEL = ('<div class="alv-filter is-open" id="p">'
         '<div class="filter-header" id="h">'
         '<h5 class="filter-title" id="ti"><i></i> Filters</h5>'
         '<button class="btn btn-outline-secondary btn-sm">Clear All</button>'
         '</div>'
         '<div class="filter-grid" id="g">'
         '<div class="filter-group"><label class="filter-label">A</label>'
         '<select class="filter-select"><option>x</option></select></div>'
         '<div class="filter-group"><label class="filter-label">B</label>'
         '<select class="filter-select"><option>x</option></select></div>'
         '</div></div>')

LOOK = '''() => {
  const g = id => {
    const c = getComputedStyle(document.getElementById(id));
    return {display: c.display, cols: c.gridTemplateColumns,
            gap: c.gap, align: c.alignItems,
            just: c.justifyContent, mb: c.marginBottom,
            pb: c.paddingBottom, border: c.borderBottomWidth + " "
              + c.borderBottomStyle + " " + c.borderBottomColor,
            colour: c.color, size: c.fontSize, weight: c.fontWeight,
            cursor: c.cursor, wrap: c.flexWrap};
  };
  return {header: g("h"), title: g("ti"), grid: g("g")};
}'''

if HAVE_PW and BOOT:
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1280, 'height': 900})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        def draw(page_css, base_css, name):
            f = os.path.join(SCRATCH, name)
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write('<!doctype html><html><head><meta charset="utf-8">'
                         '<style>%s</style><style>%s</style>'
                         '<style>%s</style></head><body>%s</body></html>'
                         % (BOOT, base_css, page_css, PANEL))
            _goto(pg, f)
            pg.wait_for_timeout(45)
            return pg.evaluate(LOOK)

        base_was = read(bak) if os.path.isfile(bak) else base
        moved, cursors, colours = [], 0, 0
        for rel in sorted(PANELS):
            p = alv_tree.join(rel.replace('/', os.sep))
            if not os.path.isfile(p + SUFFIX):
                continue
            a = draw(css_of(read(p + SUFFIX)), css_of(base_was),
                     'was_%s.html' % rel.replace('/', '_'))
            b = draw(css_of(read(p)), css_of(base),
                     'now_%s.html' % rel.replace('/', '_'))
            if a['header']['cursor'] == 'pointer':
                cursors += 1
            if a['title']['colour'] != b['title']['colour']:
                colours += 1
            diffs = {}
            for part in ('header', 'title', 'grid'):
                for k in a[part]:
                    if k == 'cursor':
                        continue
                    if a[part][k] != b[part][k]:
                        diffs['%s.%s' % (part, k)] = (a[part][k], b[part][k])
            print('     %-34s %s' % (rel, ' '.join(sorted(diffs)) or
                                     'identical'))
            # WHAT THIS ROUND IS ALLOWED TO MOVE, named one by one. The
            # first version of this check said "nothing moved but colour
            # and the separator" and then listed five things that had -
            # every one of them intended. A claim a round cannot keep is
            # worse than a smaller claim it can.
            for k, v in diffs.items():
                if k in ('title.colour', 'header.border', 'title.border'):
                    continue                      # grey -> token
                if k == 'title.size' and v == ('20px', '18px'):
                    continue   # the page never sized it; base does, 18px
                if k == 'header.gap' and v[0] == 'normal':
                    continue   # the page had none; base puts 12px between
                if (k in ('header.mb', 'header.pb') and v[0] == '0px'
                        and rel in ('invoices.html', 'projects/projects.html')):
                    continue   # the two with no separator gain the house one
                moved.append('%s %s %s' % (rel, k, v))
        ok(not moved,
           'and the ONLY things that moved are the ones this round names: '
           'two greys become their tokens, six titles go 20px to 18px '
           'because no page had ever sized them, four headers gain the '
           '12px between title and Clear All, and the two panels with no '
           'separator gain the house one', '\n'.join(moved[:5]))
        ok(cursors == 7,
           'CONTROL: seven of the nine headers DID say cursor: pointer '
           'before this round', cursors)
        ok(colours >= 8,
           '  and at least eight titles changed colour, from #2c3e50 to '
           'the ink token', colours)
        now = draw(css_of(read(alv_tree.join('properties.html'))),
                   css_of(base), 'cur.html')
        ok(now['header']['cursor'] == 'auto',
           'and the header cursor is back to auto - it is a heading',
           now['header']['cursor'])
        br.close()
elif not HAVE_PW:
    skipped += 4
else:
    skipped += 4

# ==========================================================================
head('4. THE HEADER THAT STOPPED BEING A BUTTON')
# ==========================================================================
# The panel is opened by the house Filter button on all eleven pages that
# have one. Nothing has clicked the header for some rounds.
binds = []
for rel in sorted(PANELS):
    t = read(alv_tree.join(rel.replace('/', os.sep)))
    mk = re.sub(r'<(script|style)\b.*?</\1>', '', t, flags=re.S)
    mk = re.sub(r'<!--.*?-->', '', mk, flags=re.S)
    m = re.search(r'<div[^>]*class="[^"]*\bfilter-header\b[^"]*"[^>]*>', mk)
    js = re.sub(r'(?m)^\s*//.*$', '',
                '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script>', t,
                                     re.S)))
    if m and 'onclick' in m.group(0):
        binds.append('%s markup' % rel)
    if 'filter-header' in js:
        binds.append('%s script' % rel)
ok(not binds,
   'NOT ONE of the nine binds a click to .filter-header - no onclick in '
   'the markup, and no script that so much as names the class', binds)

cur = [rel for rel in sorted(PANELS)
       if 'cursor' in ' '.join(top_level(
           read(alv_tree.join(rel.replace('/', os.sep))), '.filter-header'))]
ok(not cur, 'and no header says cursor: pointer any more', cur)
hov = [rel for rel in sorted(PANELS)
       if '.filter-header:hover' in read(
           alv_tree.join(rel.replace('/', os.sep)))]
ok(not hov, '  nor lights up when you pass over it', hov)
guards = [rel for rel in sorted(PANELS)
          if 'onclick="event.stopPropagation();"' in read(
              alv_tree.join(rel.replace('/', os.sep)))]
ok(not guards,
   '  nor guards against a click reaching a parent handler that does not '
   'exist', guards)

back = [rel for rel in sorted(PANELS)
        if os.path.isfile(alv_tree.join(rel.replace('/', os.sep)) + SUFFIX)]
if back:
    was_cur = [rel for rel in back
               if 'cursor' in ' '.join(top_level(
                   read(alv_tree.join(rel.replace('/', os.sep)) + SUFFIX),
                   '.filter-header'))]
    was_g = [rel for rel in back
             if 'onclick="event.stopPropagation();"' in read(
                 alv_tree.join(rel.replace('/', os.sep)) + SUFFIX)]
    ok(len(was_cur) == 7, 'CONTROL: seven said it before', was_cur)
    ok(len(was_g) == 5, '  and five carried the guard', was_g)
else:
    skip('the controls', 'no backups')

# ==========================================================================
head('5. THE DEAD DECLARATIONS')
# ==========================================================================
# Four pages declared .filter-header TWICE, the second overriding the
# first. Everything in the first that the second restated had never
# rendered - and the survey that read only the first rule got the wrong
# answer for four of the nine pages, which is how this was found.
twice = sorted(rel for rel in PANELS
               if PANELS[rel].get('.filter-header', {}).get('rules', 1) > 1)
ok(len(twice) == 4,
   'four pages declared .filter-header twice, and the first never '
   'rendered', twice)
for rel in twice:
    p = alv_tree.join(rel.replace('/', os.sep)) + SUFFIX
    if os.path.isfile(p):
        ok(len(top_level(read(p), '.filter-header')) == 2,
           '  %-32s CONTROL: it really did' % rel)
    else:
        skip(rel, 'no backup')
for rel in sorted(PANELS):
    t = read(alv_tree.join(rel.replace('/', os.sep)))
    for sel in FRAME:
        n = len(top_level(t, sel))
        if n > 1:
            ok(False, '%s still declares %s %d times' % (rel, sel, n))
ok(True, 'and no page declares any of the three more than once now')

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
    skip('the gate', '%s not on disk' % PS1)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)

print('')
print('  STILL COPIED, and named so the set cannot grow back in silence:')
print('  recipe_management writes the same frame under recipe-filter-*')
print('  names of its own, and passport_management has no frame rules at')
print('  all. Neither is in this round.')
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
