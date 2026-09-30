# -*- coding: utf-8 -*-
"""test_house_title.py - Section G round G3a, 30 Sep 2026.

base declares the page title twice:

    .page-title-h2 { text-align: center; ... }
    @media screen and (max-width: 768px) { .page-title-h2 { font-size: 1.25rem; } }

THE PHONE RULE REACHES THE CLASS AND NOTHING ELSE. A page that wrote
`<h2><center>TITLE</center></h2>` looked identical on a desktop and kept
Bootstrap's 2rem on a phone - 32px against 20px. Properties, Suppliers,
Tenants and Finance were among the twenty-one pages doing it.

base's own standards block said of them: "22 list pages still write
h2 > center, which renders the same and is a mechanical tidy for a later
round, not a second standard." RENDERS THE SAME IS FALSE ON A PHONE, so
it was not a mechanical tidy either. The note is corrected in the same
round, and section 5 reads it back.

SECTION 1 MEASURES THE FINDING and section 3 measures every one of the
twenty-one pages, before and after, in the same document with that
page's own stylesheet - because three of them size h2 BY ELEMENT in a
landscape-phone block, and adding a class does not stop an element
selector matching.

SECTION 6 is the round's third part. G3a's own patcher was miscounted by
the debt census in test_tree_roots: it carried a comment explaining that
it used alv_tree rather than walking a root of its own, and NAMED the
call it was avoiding. The detector read the prose. It strips comments
now, in both copies.
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
import difflib
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

SUFFIX = '.bak_housetitle'
ME = 'test_house_title.py'
PATCHER = 'apply_house_title.py'
PS1 = 'Push-PendingChanges.ps1'
CLS = 'page-title-h2'
EXE = '/opt/pw-browsers/chromium'
X0, X11 = 'test_tree_roots.py', 'test_waiting_down.py'

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
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S))


def inert(t):
    """Comments out - HTML, Django and CSS. The standards block in base
    is itself a Django comment several thousand words long and full of
    the exact spellings this suite hunts for."""
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', '', t,
               flags=re.S | re.I)
    t = re.sub(r'\{#.*?#\}', '', t, flags=re.S)
    return re.sub(r'/\*.*?\*/', '', t, flags=re.S)


# The twenty-one, read off the patcher so the two cannot disagree.
patcher = read(os.path.join(ROOT, PATCHER))
JOBS = re.findall(r"^\s*\('([^']+\.html)',\s*'([^']*)'\),\s*$", patcher, re.M)

# AS G3a LEFT IT - lesson 17. Every claim below is about what G3a did
# to base and to twenty-one pages; a later round editing the same files
# must not turn this suite's own scope check into a list of strays. G3b
# was that round, on 30 Sep.
try:
    from alv_rounds import as_left_by as _left
    base = _left(alv_tree.path_of('base.html'), SUFFIX, read)
except Exception:
    base = read(alv_tree.path_of('base.html'))

# BOOTSTRAP 4.1.3, THE REPO'S OWN COPY. The whole finding is that an
# unclassed h2 keeps BOOTSTRAP's 2rem, so a fixture without Bootstrap
# measures the browser's 1.5em instead and reports 24px - which is a real
# number about a page that does not exist. The house keeps a local copy
# precisely so a render never waits on a CDN.
BOOT = ''
_boot = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
if os.path.isfile(_boot):
    BOOT = read(_boot)

print('=' * 74)
print('%s - G3a, THE HOUSE TITLE WHERE THE PHONE RULE CAN REACH IT' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE FINDING: 32px AGAINST 20px, ON A PHONE')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)

ok(len(JOBS) == 21, 'the round names twenty-one pages', len(JOBS))
ok(bool(BOOT), 'the repo\'s own Bootstrap 4.1.3 is in the fixture, so an '
               'unclassed h2 is measured against the stylesheet the live '
               'page actually loads', len(BOOT))
ok(re.search(r'@media screen and \(max-width: 768px\)[^}]*\{[^{}]*'
             r'\.page-title-h2\s*\{[^}]*font-size', base, re.S) is not None
   or re.search(r'\.page-title-h2\s*\{\s*font-size:\s*1\.25rem', base)
   is not None,
   'base sizes .page-title-h2 on a phone, and only the class')

if HAVE_PW:
    fx = os.path.join(SCRATCH, 'finding.html')
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><html><head><meta charset="utf-8">'
                 '<style>%s</style><style>%s</style></head><body>'
                 '<h2 id="old"><center>PROPERTIES</center></h2>'
                 '<h2 id="new" class="%s">PROPERTIES</h2>'
                 '</body></html>' % (BOOT, css_of(base), CLS))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 390, 'height': 844})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        _goto(pg, fx)
        pg.wait_for_timeout(150)
        phone = pg.evaluate('''() => ({
            old: getComputedStyle(document.getElementById("old")).fontSize,
            now: getComputedStyle(document.getElementById("new")).fontSize})''')
        ok(phone['old'] == '32px',
           'ON A PHONE the old spelling is 32px - Bootstrap\'s 2rem, '
           'untouched by base', phone)
        ok(phone['now'] == '20px',
           '  and the class is 20px, which is what base meant all along',
           phone)
        pg.set_viewport_size({'width': 1280, 'height': 900})
        pg.wait_for_timeout(150)
        desk = pg.evaluate('''() => ({
            old: getComputedStyle(document.getElementById("old")).fontSize,
            now: getComputedStyle(document.getElementById("new")).fontSize})''')
        ok(desk['old'] == desk['now'] == '32px',
           'ON A DESKTOP they really are identical - which is why base\'s '
           'note called it a mechanical tidy, and why nobody noticed', desk)
        br.close()
else:
    skipped += 3

# ==========================================================================
head('2. ALL TWENTY-ONE, AND NONE LEFT ANYWHERE')
# ==========================================================================
for rel, title in JOBS:
    t = inert(read(alv_tree.join(rel.replace('/', os.sep))))
    ok('<h2 class="%s">%s</h2>' % (CLS, title) in t,
       '%-38s %s' % (rel, title))

left = []
for p in alv_tree.templates():
    if re.search(r'<h2[^>]*>\s*<center>', inert(read(p)), re.I):
        left.append(alv_tree.rel(p))
ok(not left,
   'and NO template in the tree still writes h2 > center - all of them, '
   'not just the twenty-one this round names', left)

wearers = [alv_tree.rel(p) for p in alv_tree.templates()
           if re.search(r'<h[1-6][^>]*class="[^"]*\b%s\b' % CLS, inert(read(p)))]
ok(len(wearers) == 117,
   '117 templates now wear the class, which is the number base\'s note '
   'states', len(wearers))

# WHAT IS DELIBERATELY LEFT: the hand-rolled headers. They are a content
# decision - an icon, an inline colour, a descriptive paragraph, a record
# name - not a class swap, and naming them stops the set growing back in
# silence.
hand = sorted(alv_tree.rel(p) for p in alv_tree.templates()
              if re.search(r'<h2[^>]*class="[^"]*mb-1', inert(read(p))))
print('     hand-rolled headers left for a content decision: %d' % len(hand))
for h in hand:
    print('       %s' % h)
ok(not any(h in dict(JOBS) for h in hand),
   '  and not one of them is in this round', hand)

# ==========================================================================
head('3. EVERY ONE OF THE TWENTY-ONE, AT 390, BEFORE AND AFTER')
# ==========================================================================
# With THAT PAGE'S OWN STYLESHEET, because three of them size h2 by
# element in a landscape-phone block and adding a class does not stop an
# element selector matching. A page that was 14px by its own rule must
# still be 14px.
if HAVE_PW:
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 390, 'height': 844})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        shrank, held, missing = [], [], []
        for rel, title in JOBS:
            path = alv_tree.join(rel.replace('/', os.sep))
            if not os.path.isfile(path + SUFFIX):
                missing.append(rel)
                continue
            page_css = css_of(read(path))
            f = os.path.join(SCRATCH, rel.replace('/', '_').replace(
                '.html', '') + '_390.html')
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write('<!doctype html><html><head><meta charset="utf-8">'
                         '<style>%s</style><style>%s</style>'
                         '<style>%s</style></head><body>'
                         '<h2 id="old"><center>%s</center></h2>'
                         '<h2 id="new" class="%s">%s</h2>'
                         '</body></html>'
                         % (BOOT, css_of(base), page_css, title, CLS,
                            title))
            _goto(pg, f)
            pg.wait_for_timeout(60)
            r = pg.evaluate('''() => ({
                old: getComputedStyle(document.getElementById("old")).fontSize,
                now: getComputedStyle(
                    document.getElementById("new")).fontSize})''')
            a, b = float(r['old'][:-2]), float(r['now'][:-2])
            (shrank if b < a else held).append((rel, r['old'], r['now']))
        for rel, a, b in shrank:
            ok(True, '%-38s %s -> %s' % (rel, a, b))
        print('')
        for rel, a, b in held:
            print('     %-38s %s -> %s   (the page sizes h2 itself)'
                  % (rel, a, b))
        ok(len(shrank) + len(held) + len(missing) == 21,
           'every page in the round was measured', len(shrank) + len(held))
        ok(len(shrank) >= 17,
           '%d of the twenty-one got SMALLER on a phone - that is the '
           'defect, removed' % len(shrank), len(shrank))
        ok(all(float(b[:-2]) <= float(a[:-2]) for _r, a, b in shrank + held),
           'and NOT ONE of them got bigger')
        ok(all(float(b[:-2]) <= 20.0 for _r, a, b in shrank),
           '  none of the ones that moved is above base\'s 20px',
           [x for x in shrank if float(x[2][:-2]) > 20.0])
        ok(not held,
           '  and on a PORTRAIT phone every one of them moved - no page '
           'was already smaller here', held)

        # ---- THE LANDSCAPE PHONE, which is where the element rules live.
        # Two of these pages size h2 BY ELEMENT inside
        #   @media (orientation: landscape) and (max-height: 500px)
        # at 14px and 16px. Adding a CLASS does not stop an ELEMENT
        # selector matching, and the round's claim that it leaves them
        # alone is only worth anything if it is rendered where they fire.
        land = []
        for rel, title in JOBS:
            css = re.sub(r'/\*.*?\*/', '',
                         css_of(read(alv_tree.join(rel.replace('/', os.sep)))),
                         flags=re.S)
            for m in re.finditer(r'@media[^{]*orientation:\s*landscape[^{]*\{',
                                 css):
                if re.search(r'(?<![\w.-])h2\s*[,{]', css[m.end():m.end() + 1400]):
                    land.append((rel, title))
                    break
        ok(len(land) >= 2,
           'two or more of the twenty-one size h2 by ELEMENT in a '
           'landscape-phone block', [r for r, _ in land])
        pg.set_viewport_size({'width': 844, 'height': 390})
        kept = []
        for rel, title in land:
            path = alv_tree.join(rel.replace('/', os.sep))
            f = os.path.join(SCRATCH, 'land_' + rel.replace('/', '_'))
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write('<!doctype html><html><head><meta charset="utf-8">'
                         '<style>%s</style><style>%s</style>'
                         '<style>%s</style></head><body>'
                         '<h2 id="old"><center>%s</center></h2>'
                         '<h2 id="new" class="%s">%s</h2>'
                         '</body></html>'
                         % (BOOT, css_of(base), css_of(read(path)), title,
                            CLS, title))
            _goto(pg, f)
            pg.wait_for_timeout(60)
            r = pg.evaluate('''() => ({
                old: getComputedStyle(document.getElementById("old")).fontSize,
                now: getComputedStyle(
                    document.getElementById("new")).fontSize})''')
            kept.append((rel, r['old'], r['now']))
            print('     %-38s landscape %s -> %s' % (rel, r['old'], r['now']))
        ok(kept and all(a == b for _r, a, b in kept),
           'AND IN LANDSCAPE THEY DO NOT MOVE AT ALL - the page\'s own '
           'element rule still wins over a class, which is why this had '
           'to be rendered rather than reasoned about', kept)
        ok(all(float(b[:-2]) < 20.0 for _r, _a, b in kept),
           '  and each keeps its own smaller size, not base\'s 20px',
           kept)
        if missing:
            skip('%d page(s) unmeasured' % len(missing), 'no backup')
        br.close()
else:
    skipped += 5

# ==========================================================================
head('4. ONE LINE PER PAGE, AND NOTHING ELSE')
# ==========================================================================
scoped, unscoped = 0, []
for rel, title in JOBS:
    path = alv_tree.join(rel.replace('/', os.sep))
    if not os.path.isfile(path + SUFFIX):
        continue
    try:
        _now = _left(path, SUFFIX, read)
    except Exception:
        _now = read(path)
    a, b = read(path + SUFFIX).split('\n'), _now.split('\n')
    ops = [o for o in difflib.SequenceMatcher(None, a, b,
                                              autojunk=False).get_opcodes()
           if o[0] != 'equal']
    if (len(ops) == 1 and ops[0][0] == 'replace'
            and ops[0][2] - ops[0][1] == 1 and ops[0][4] - ops[0][3] == 1
            and '<center>' in a[ops[0][1]] and CLS in b[ops[0][3]]):
        scoped += 1
    else:
        unscoped.append('%s: %s' % (rel, ops[:2]))
ok(not unscoped,
   'all %d page edits are ONE line replaced by one line, the heading and '
   'nothing else' % scoped, '\n'.join(unscoped[:4]))
ok(scoped == 21, '  and there are twenty-one of them', scoped)

# ==========================================================================
head('5. base\'S NOTE NOW SAYS WHAT IS TRUE')
# ==========================================================================
note = re.search(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', base,
                 re.S | re.I)
doc = note.group(0) if note else ''
ok(bool(doc), 'base carries its standards block')
ok('renders the same and' not in doc,
   'the claim that h2 > center "renders the same" is gone - it was true '
   'on a desktop and false on a phone')
ok('32px against 20px' in doc,
   '  replaced by the measurement, so the next reader has the number')
ok('117 pages' in doc, '  and the count is the one section 2 just checked')
bak = alv_tree.path_of('base.html') + SUFFIX
if os.path.isfile(bak):
    old = read(bak)
    ok('renders the same and' in old,
       'CONTROL: before this round the note said exactly that')
    ok(inert(old) == inert(base),
       '  and OUTSIDE the comment base is byte-identical - this round '
       'changed prose, not a rule')
else:
    skip('the note control', 'no %s backup of base' % SUFFIX)
    skip('the note control', 'no %s backup of base' % SUFFIX)

# ==========================================================================
head('6. THE DEBT CENSUS READS CODE, NOT PROSE')
# ==========================================================================
# This round's own patcher was counted as a walker because a COMMENT in it
# named os.walk of a template root. Every other gate in this repo strips
# comments first; this one reads Python and did not.
det = {}
for name in (X0, X11):
    p = os.path.join(ROOT, name)
    if not os.path.isfile(p):
        skip(name, 'not on disk')
        continue
    t = read(p)
    det[name] = t
    ok('def code_only(' in t and 'text = code_only(text)' in t,
       '%-24s strips comments before it detects' % name)
    ok('import tokenize' in t,
       '  %-22s with tokenize, which knows a # inside a string is not a '
       'comment' % '')
if len(det) == 2:
    def body(t):
        # CODE, not comments - the two copies have never been byte
        # identical: X0 carries one explanatory line X11 does not, and
        # has since the day X11 copied it. What must not differ is what
        # they DO, so compare what runs.
        m = re.search(r'def walks_own_root\(text\):.*?\n(?=\S)', t, re.S)
        if not m:
            return ''
        s = re.sub(r'""".*?"""', '', m.group(0), flags=re.S)
        s = re.sub(r'(?m)^\s*#.*$', '', s)
        return '\n'.join(ln for ln in s.split('\n') if ln.strip())
    ok(body(det[X0]) == body(det[X11]) != '',
       'and the two copies still DO the same thing - X11\'s own words: '
       'two detectors and one constant is how X0\'s first ceiling came '
       'out wrong',
       '\n'.join(list(difflib.unified_diff(body(det[X0]).split('\n'),
                                           body(det[X11]).split('\n'),
                                           lineterm=''))[:6]))

# THE CONTROL, RUN. Lift the real detector out and put the exact shape
# that fooled it through it.
if X0 in det:
    ns = {}
    src = det[X0]
    grabs = [re.search(r'^def %s\(.*?\n(?=^\S)' % f, src, re.M | re.S)
             for f in ('code_only', 'walks_own_root')]
    if all(grabs):
        exec('import io, os, re, tokenize\n'
             + '\n'.join(g.group(0) for g in grabs), ns)
        w = ns['walks_own_root']
        ok(not w("T = os.path.join(R, 'pages', 'templates')\n"
                 "# this file does not os.walk(T)\n"
                 "for p in alv_tree.templates():\n    pass\n"),
           'a walk that exists only in a COMMENT is not counted - the '
           'shape that failed two suites on 30 Sep')
        ok(w("T = os.path.join(R, 'pages', 'templates')\n"
             "for a, b, c in os.walk(T):\n    pass\n"),
           '  and a real one still is: the fix removes prose, not sight')
        ok(not w('"""A docstring about os.walk(T) and templates."""\n'
                 "T = os.path.join(R, 'pages', 'templates')\n"),
           '  and a DOCSTRING naming it is not counted either')
        me = read(os.path.join(ROOT, PATCHER))
        ok(not w(me),
           '  and this round\'s own patcher, which is where the fault was '
           'found, is not counted - it reads the tree through alv_tree')
        ok('os.walk(ROOT)' in me,
           '  although it still says so in a comment, deliberately, so '
           'the shape stays in the repo for the control to be about')
    else:
        skip('the detector control', 'could not lift it out of %s' % X0)

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
print('  NOT IN THIS ROUND, on purpose: the h5 > center descriptive lines')
print('  (base declares no .page-subtitle-h5 - giving them a class means')
print('  adding one to base, which is a round of its own) and the six')
print('  hand-rolled headers named in section 2, which carry an icon, an')
print('  inline colour or a record name and want a content decision.')
print('=' * 74)
sys.exit(1 if failed else 0)
