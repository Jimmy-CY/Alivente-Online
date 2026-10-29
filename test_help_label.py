"""test_help_label.py - round HL-1, 12 Oct 2026.

    python test_help_label.py

Run from the repo root.

WHAT THIS SUITE CANNOT DO, SAID FIRST

It cannot tell you whether a Help button should keep its word on a
phone. 64 of the system's 65 already do, and this round makes it 65;
the alternative - teaching base to square a Help button the way it
squares a Back button - is a different round and a different argument.

WHAT IT GUARDS

`<span class="action-back-label"> Help</span>` on a control that is
.action-secondary and not .action-back. D-2 removed the identical span
from workspace_management.html on 23 September and could not see this
one, because its census walks pages/templates and the CRS reporting
screens are a second Django template root.

SECTION 4 IS THE ONE THAT EARNS ITS KEEP, and it earns it twice. It
renders the bar at 375px before and after and measures that NOTHING
MOVED - this round repaints nothing and says so. Then it renders the
same two fixtures with the unscoped `.action-back-label { display: none }`
that 77 pages carried before D7 removed every one, and measures the old
markup losing the word Help while the new markup keeps it. That is the
round: not a repaint, a trap removed.

SECTION 3 is the claim the release rests on - that across BOTH roots
every element wearing that class now says Back.

A SKIPPED CHECK IS COUNTED IN THE SUMMARY.
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
    """Open a local fixture, and SAY SOMETHING if the browser will not.

    Every tool here carries a paragraph about a crash blocking a push
    exactly as hard as a failure while saying far less about why - and
    then calls goto bare. This is that paragraph, kept.
    """
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

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import alv_cssrules                                             # noqa: E402
import alv_rounds                                               # noqa: E402
import alv_tree                                                 # noqa: E402

SUFFIX = '.bak_helplabel'
PATCHER = 'apply_help_label.py'
ME = os.path.basename(__file__)
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')

RELEASED = ('test_small_three.py',)
PAGE = 'crs/submission_detail.html'
PRECEDENT = 'workspace_management.html'
SPAN = ('<i class="fas fa-question-circle"></i>'
        '<span class="action-back-label"> Help</span>')
BARE = '<i class="fas fa-question-circle"></i> Help'
LABELS_TOTAL = 133   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 132)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 131)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page. A new PAGE with a house Back, so the tree-wide count moves by exactly one.   # (was 130)   # ES-3b, 24 Oct 2026 - the Send for Signature screen. A new PAGE with a house Back, which carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 129)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 128)   # RV-1, 23 Oct 2026 - the Receipt Details Back. A new PAGE, and a house Back carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 127)   # PP-1, 20 Oct 2026 - the printable plan's Back. It wore .action-secondary in the first draft and five suites objected; wearing the house class means carrying the house label span, which base hides on a phone so the control becomes a square icon.   # (was 126)   # RT-1, 18 Oct 2026 - three Back labels went with the four meal-plan screens MN-1 retired, and the planner brought none   # (was 129)   # PJ-1, 15 Oct 2026 - the same duplicate Back, counted by its label span. The check below it compares the backup and so falls by one with it.   # (was 130)   # DB-5, 12 Oct 2026 - the dashboard Back gains the house label   # (was 129)   # AFTER this round. 130 before - the Help one.
HELP_TOTAL = 47   # CX-1, 29 Oct 2026 - Task List and Gantt Chart gain Help, bare text like their siblings   # (was 45)   # HK-4, 28 Oct 2026 - Project Details gains Help, his finding; bare text like its siblings   # (was 44)   # ES-8, 25 Oct 2026 - the Lease Signing register gains its own Help, his request; a bare-text Help secondary like its siblings.   # (was 43)   # RT-1, 18 Oct 2026 - three of MH-1 five Help buttons went with the screens they sat on. The guide is unchanged and still reached from the planner and the shopping list.   # (was 46)   # MH-1, 18 Oct 2026 - the five meal-plan screens, which had no Help control at all   # (was 41)   # DB-5, 12 Oct 2026 - and a Help secondary joins the bar   # (was 40)
# The shape 77 pages carried before D7 removed every one of them.
UNSCOPED = '.action-back-label { display: none; }'

PASS = FAIL = SKIP = 0
FAILED = []


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  ok   %s' % name)
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL %s%s' % (name, ('  [%s]' % extra) if extra else ''))
    return ok


def skip(name, why):
    global SKIP
    SKIP += 1
    print('  skip %s - %s' % (name, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def before(p):
    b = alv_tree.bak_path(p, SUFFIX)
    if not os.path.exists(b):
        print('')
        print('  !! %s has no %s backup.' % (os.path.basename(p), SUFFIX))
        print('     This suite judges the round against what it replaced,')
        print('     so it cannot run until %s has.' % PATCHER)
        sys.exit(1)
    return read(b)


def css_of(text):
    return '\n'.join(re.sub(r'/\*.*?\*/', '', text[a:b], flags=re.S)
                     for a, b in alv_cssrules.style_spans(text))


# E15, 13 Oct 2026 - WAS a private copy. Nine had grown
# under four names and three algorithms, and all three
# algorithms were wrong. alv_tree owns it now.
# payloads=True, the default: this file asks what the code
# DOES, so a triple-quoted payload is code and survives.
code_lines = alv_tree.python_code_only


print(__doc__.strip().split('\n')[0])

# ---------------------------------------------------------------------- 1
head('1. SCOPE')

check('%s is on disk' % PATCHER, os.path.isfile(os.path.join(ROOT, PATCHER)))
for n in RELEASED:
    check('  %s is still here' % n, os.path.isfile(os.path.join(ROOT, n)))
check('  and the page is in the SECOND template root',
      alv_tree.last_path(PAGE) != os.path.join(ROOT, 'pages', 'templates',
                                             PAGE.replace('/', os.sep)))
print('        That is the whole reason D-2 could not see it. Its census')
print('        walked pages/templates, and this page is not under it.')

# ---------------------------------------------------------------------- 2
head('2. THE SPAN IS GONE, AND THE CLASS IS NOT')

p = alv_tree.last_path(PAGE)
now, was = read(p), before(p)
check('the Help button no longer calls its label a Back label',
      SPAN not in now)
check('  CONTROL: and the backup proves it did', SPAN in was)
check('  it writes bare text instead', BARE in now)
check('    which is byte-for-byte the shape D-2 gave %s' % PRECEDENT,
      BARE in read(alv_tree.last_path(PRECEDENT)))

# THE CLASS ITSELF MUST SURVIVE ON THAT PAGE. A round that removes the
# one wrong use by removing the class would pass a check that only
# looked for the span.
check('  and the Back button beside it still wears the class',
      'action-back-label' in now)
m = re.search(r'<a[^>]*class="btn action-back"[\s\S]*?</a>', now)
check('    CONTROL: on the control that IS a back button',
      m is not None and 'action-back-label' in m.group(0))
check('  the label count on this page fell by exactly one',
      now.count('action-back-label') == was.count('action-back-label') - 1,
      '%d from %d' % (now.count('action-back-label'),
                      was.count('action-back-label')))

# ---------------------------------------------------------------------- 3
head('3. ACROSS BOTH ROOTS, EVERY BACK LABEL NOW SAYS BACK')


def labels():
    out = []
    for q in alv_tree.templates():
        src = alv_tree.code_only(read(q))
        for mm in re.finditer(r'<span class="action-back-label"[^>]*>'
                              r'(.*?)</span>', src, re.S):
            txt = ' '.join(re.sub(r'\{%.*?%\}', '', mm.group(1),
                                  flags=re.S).split())
            out.append((alv_tree.rel(q), txt))
    return out


rows = labels()
odd = [r for r in rows
       if 'back' not in r[1].lower() and 'cancel' not in r[1].lower()]
check('no element labels a non-Back, non-Cancel control as a Back',
      not odd, '%s' % odd[:2])
check('  CONTROL: over %d label(s) in the tree, not an empty scan'
      % len(rows), len(rows) == LABELS_TOTAL, '%d' % len(rows))
# AND IT FELL BY EXACTLY ONE. A count pinned at the figure AFTER a round
# that removes something is half a claim; the backup carries the other
# half. The first draft pinned 130, which was the BEFORE count, and the
# suite failed on the round working exactly as intended.
rows_was = len(re.findall(r'<span class="action-back-label"', was))
check('    and this page carried one more before it', rows_was
      == len(re.findall(r'<span class="action-back-label"', now)) + 1,
      '%d then, %d now' % (rows_was,
                           len(re.findall(r'<span class="action-back-label"',
                                          now))))
greek = [r for r in rows if any(ord(c) > 0x370 for c in r[1])]
check('  CONTROL: and the Greek one is still here and still a Back',
      len(greek) == 1 and 'back' in greek[0][1].lower(),
      '%s' % greek)
print('        It sits behind the language switch and reads the Greek word')
print('        then the English one. A census that could not see it would')
print('        have reported this round complete a label early.')

helps, bare = [], []
for q in alv_tree.templates():
    for mm in re.finditer(r'<button[^>]*data-target="#\w*HelpModal"[^>]*>'
                          r'(.*?)</button>', read(q), re.S):
        if 'action-more-item' in mm.group(0):
            continue
        helps.append(alv_tree.rel(q))
        if 'action-back-label' not in mm.group(1):
            bare.append(alv_tree.rel(q))
check('all %d Help control(s) in the tree write bare text' % len(helps),
      len(bare) == len(helps) == HELP_TOTAL,
      '%d bare of %d' % (len(bare), len(helps)))
print('        D-2 said 18 of 20, counting exactly this way. Both')
print('        numbers were true of one root. The count has doubled')
print('        since September and the exception was still one.')

# ---------------------------------------------------------------------- 4
head('4. NOTHING ON SCREEN MOVES - AND THE TRAP IS REAL. MEASURED.')

bp = alv_tree.last_path('base.html')
B = read(bp)
scoped = re.search(r'\.action-back\s+\.action-back-label\s*,\s*'
                   r'\.back-button\s+\.action-back-label\s*\{[^{}]*'
                   r'display:\s*none', B)
check('base hides the label only INSIDE a back button', scoped is not None)
check('  and only below 768px', '@media screen and (max-width: 768px)' in B)
# THE DETECTOR, AND THE ONE IT REPLACES.
#
# The first control written here was
#     (?<![-\w\s])\.action-back-label\s*\{[^{}]*display:\s*none
# and it CANNOT FIRE: the lookbehind excludes a space, so an indented
# rule never matches - and every page rule in this codebase is
# indented. Dropping the \s does not fix it either, it matches base's
# own SCOPED `.action-back .action-back-label`. Neither reads a
# selector; both read characters near one.
#
# A control that cannot fail is worse than no control, and that one was
# mine, in the round before this one. This splits the selector list on
# commas and compares a WHOLE TOKEN, which is the shape D7 removed 77
# times - and section 5b proves it can fire by pointing it at the
# frozen files where the rule still exists.
def unscoped(text):
    hits = []
    for mm in re.finditer(r'(?m)^[ \t]*([^\n{}]+?)\s*\{([^{}]*)\}',
                          text):
        for sel in mm.group(1).split(','):
            if sel.strip() == '.action-back-label':
                hits.append(' '.join(mm.group(2).split())[:40])
    return hits


live_rule = [alv_tree.rel(q) for q in alv_tree.templates()
             if alv_tree.rel(q) != 'base.html'
             and unscoped(css_of(read(q)))]
check('  CONTROL: and no unscoped copy survives anywhere in the tree',
      not live_rule, '%s' % live_rule[:3])
check('    CONTROL: while base DOES define the class, scoped - so the '
      'detector is not simply blind to it',
      'action-back-label' in css_of(read(bp)) and not unscoped(css_of(read(bp))))
print('        77 pages carried one. D7 removed every one, and that is')
print('        what makes this a trap rather than a live defect.')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

if sync_playwright is None:
    skip('the word Help renders at 375px, before and after', 'no playwright')
    skip('CONTROL: with the unscoped rule back, only the OLD one loses it',
         'ditto')
else:
    boot = read(os.path.join(ROOT, 'test_fixture_bootstrap413.css'))
    bcss = re.sub(r'\{%.*?%\}', '', css_of(B), flags=re.S)
    refused = []

    def bar(src):
        """The page action bar, Django stripped innermost-first."""
        i = src.index('<div class="page-action-buttons">')
        j = src.index('</div>', src.index('action-back', i))
        seg = src[i:j + 6]
        seg = re.sub(r'\{#.*?#\}', '', seg, flags=re.S)
        prev = None
        while prev != seg:
            prev = seg
            seg = re.sub(r'\{%[^%]*%\}', '', seg, flags=re.S)
        seg = re.sub(r'\{\{[^}]*\}\}', 'x', seg)
        # Font Awesome is blocked; give the icons something to be.
        seg = re.sub(r'<i class="fas fa-[^"]*"></i>', '&#9679;', seg)
        return seg

    def words(seg, extra=''):
        doc = ('<!doctype html><html><head><meta charset="utf-8">'
               '<link rel="stylesheet" href="https://example.invalid/x.css">'
               '<style>%s</style><style>%s</style><style>%s</style>'
               '<style>*{transition:none!important}</style></head>'
               '<body style="margin:0">%s</body></html>'
               % (boot, bcss, extra, seg))
        fx = os.path.join(SCRATCH, 'hl1_%d.html' % (len(doc) % 999983))
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(doc)
        pw = sync_playwright().start()
        try:
            br = pw.chromium.launch()
            ctx = br.new_context(viewport={'width': 375, 'height': 500})

            def _abort(route):
                refused.append(route.request.url)
                route.abort()

            ctx.route(re.compile(r'^https?://'), _abort)
            pg = ctx.new_page()
            _goto(pg, fx)
            pg.wait_for_timeout(120)
            out = pg.eval_on_selector(
                '.page-action-buttons',
                "e => e.innerText.replace(/\\s+/g, ' ').trim()")
            ctx.close()
            br.close()
            return out
        finally:
            pw.stop()

    old_bar, new_bar = bar(was), bar(now)
    old_txt, new_txt = words(old_bar), words(new_bar)
    check('CONTROL: the fixture asked for a remote stylesheet and the '
          'browser REFUSED it, both times', len(refused) == 2,
          '%d refused' % len(refused))
    check('at 375px the bar reads the same before and after: %r' % new_txt,
          old_txt == new_txt, '%r vs %r' % (old_txt, new_txt))
    check('  and the word Help is in it', 'Help' in new_txt, new_txt)
    check('  CONTROL: while the word Back is NOT - base squares the back '
          'button on a phone', 'Back' not in new_txt, new_txt)
    print('        So this round repaints nothing, and says so.')

    # THE TRAP, DEMONSTRATED. The same fixture plus the unscoped rule
    # the system carried 77 times.
    old_trap, new_trap = words(old_bar, UNSCOPED), words(new_bar, UNSCOPED)
    check('  with that unscoped rule back, the OLD markup loses the word',
          'Help' not in old_trap, old_trap)
    check('    and the new markup keeps it', 'Help' in new_trap, new_trap)
    check('    CONTROL: and the rule really did something - the two '
          'differ', old_trap != new_trap,
          '%r vs %r' % (old_trap, new_trap))
    print('        That is the round: not a repaint, a trap removed. One')
    print('        unscoped copy on this page and the Help button becomes')
    print('        a bare question mark in a circle.')

# --------------------------------------------------------------------- 4b
head('4b. BL-2 - FIVE FAILURES, FIVE OF THEM THE READER')

bl = read(os.path.join(ROOT, 'test_back_label.py'))
blw = before(os.path.join(ROOT, 'test_back_label.py'))

check('test_back_label reads a page it never touched LIVE',
      'FOR A PAGE IT TOUCHED' in bl)
# RT-1, 18 Oct 2026 - THE SPELLING OF THE BACKUP'S PATH MOVED, AND THE
# CLAIM DID NOT. test_back_label now asks alv_tree.bak_path for its
# own backup, because a retired page's backups sit beside the hole it
# left rather than beside its last text. What this check is about is
# the FALLBACK - that a page the round never touched is read LIVE -
# so it accepts either spelling of the question above it.
check('  which is the live file when the round left no backup',
      re.search(r'if not os\.path\.isfile\(\s*(?:p \+ SUFFIX'
                r'|alv_tree\.bak_path\(p, SUFFIX\))\):\s*\n'
                r'\s*return read\(p\)', bl) is not None)
check('  CONTROL: and the backup proves it did not',
      'FOR A PAGE IT TOUCHED' not in blw)
check('  while a page it DID touch is still read as that round left it',
      'as_left_by(p, SUFFIX, read)' in code_lines(bl))

# THE MEASUREMENT THE ROUND RESTS ON, and the one that proves the
# detector above can fire.
live_n, frozen_n, frozen_pages = 0, 0, []
for q in alv_tree.templates():
    rel = alv_tree.rel(q)
    if rel == 'base.html':
        continue
    if unscoped(css_of(read(q))):
        live_n += 1
    froz = alv_rounds.as_left_by(q, '.bak_backlabel', read)
    if unscoped(css_of(froz)):
        frozen_n += 1
        frozen_pages.append(rel)
check('LIVE, no page in either root carries an unscoped copy',
      live_n == 0, '%d' % live_n)
check('  but through as_left_by, %d do - and that is the whole of what '
      'this suite was reporting' % frozen_n, frozen_n == 7, '%d' % frozen_n)
check('    CONTROL: and every one of them is a CRS page, frozen at a '
      'moment that belongs to another round',
      all(r.startswith('crs/') for r in frozen_pages), '%s' % frozen_pages)
print('        A later CRS round removed all seven. as_left_by handed')
print('        back whichever round happened to open them next.')
print('        THIRD ROUND RUNNING: E-1b made the identical repair to')
print('        test_contrast and wrote the rule down while doing it.')

# AND TWO PINNED AGGREGATES THAT A WIDER CORPUS BREAKS.
check('the portrait claim is derived, not pinned at one page',
      'before_on == [FIXED]' not in code_lines(bl)
      and 'FIXED in before_on' in bl)
check('  and the landscape one too',
      'land_before == [FIXED]' not in code_lines(bl)
      and 'FIXED in land_before' in bl)
check('  CONTROL: and the backup proves both WERE pinned',
      'before_on == [FIXED]' in code_lines(blw)
      and 'land_before == [FIXED]' in code_lines(blw))
check('  while what BL-1 can claim forever survives - that ITS page '
      'showed the word and does not now',
      'measured on that page, not inferred ' in bl)
print('        Widened, five pages showed the word before, not one.')
print('        The other four are real beneficiaries BL-1 never counted:')
print('        their Back sits outside a .page-action-buttons bar, so old')
print('        base three-ancestors-deep rule never reached them.')
print('        NOT ONE APPLICATION FILE CHANGED FOR BL-2.')

# ---------------------------------------------------------------------- 5
head('5. WIDENED, RELEASED, AND EVERY NUMBER THAT COUNTS IT')

for n in RELEASED:
    s = read(os.path.join(ROOT, n))
    check('  %s walks through alv_tree' % n, 'alv_tree.walk3()' in s)
    own = re.findall(r'os\.walk\((T|TPL|ROOT)\)', code_lines(s))
    check('    and walks no root of its own', not own, '%s' % own)
    check('    resolves nothing through it either',
          not re.search(r'os\.path\.join\(\s*T\s*,', code_lines(s)))
    check('    and takes no label back against it',
          not re.search(r'os\.path\.relpath\([^)]*,\s*T\)',
                        code_lines(s), re.S))
    check('    off alv_tree.WAITING', n not in alv_tree.WAITING)
    check('    on alv_tree.CONVERTED', n in alv_tree.CONVERTED)

check('none of the %d this round released is still held' % len(RELEASED),
      not [n for n in RELEASED if n in alv_tree.WAITING],
      '%s' % [n for n in RELEASED if n in alv_tree.WAITING])
check('  CONTROL: and WAITING is not empty - %d still held'
      % len(alv_tree.WAITING), len(alv_tree.WAITING) > 0)

x0 = read(os.path.join(ROOT, 'test_tree_roots.py'))
wd = read(os.path.join(ROOT, 'test_waiting_down.py'))


def pin(text, name):
    """A pinned number, whether assigned alone or in a tuple.

    E-10 wrote this because the one-name reader every suite here carries
    answers 265 for N_MODAL in `N_BAR, N_ROW, N_MODAL = 265, 110, 98`.
    """
    for m2 in re.finditer(r'(?m)^([A-Z_][A-Z_0-9, ]*?)\s*=\s*([^\n#]+)',
                          text):
        names = [x.strip() for x in m2.group(1).split(',')]
        vals = [v.strip() for v in m2.group(2).split(',')]
        if name in names and len(names) == len(vals):
            v = vals[names.index(name)]
            return int(v) if re.match(r'^\d+$', v) else None
    return None


check('the walker ceiling and test_waiting_down agree',
      pin(wd, 'CEILING') == pin(x0, 'WALKERS_OWN_ROOT_MAX'),
      '%s vs %s' % (pin(wd, 'CEILING'), pin(x0, 'WALKERS_OWN_ROOT_MAX')))
check('  CONTROL: and it FELL - the file says it may only fall',
      pin(x0, 'WALKERS_OWN_ROOT_MAX')
      < pin(before(os.path.join(ROOT, 'test_tree_roots.py')),
            'WALKERS_OWN_ROOT_MAX'),
      '%s' % pin(x0, 'WALKERS_OWN_ROOT_MAX'))
check('CONVERTED_N agrees with the live register',
      pin(wd, 'CONVERTED_N') == len(alv_tree.CONVERTED),
      '%s vs %d' % (pin(wd, 'CONVERTED_N'), len(alv_tree.CONVERTED)))
check('  and WAITING_N too',
      pin(wd, 'WAITING_N') == len(alv_tree.WAITING),
      '%s vs %d' % (pin(wd, 'WAITING_N'), len(alv_tree.WAITING)))

# --------------------------------------------------------------------- 5b
head('5b. GT-1 - THE SUBJECT IS ASKED FOR AT THE TOP')

psw = before(PS1)
ps_now = read(PS1)

i_pre = ps_now.find('if ($Apply -and -not $Message) {')
i_suites = ps_now.find('$suites = @(')
i_real = ps_now.find("Bad 'No commit subject.'")
check('the gate asks for a commit subject before it runs anything',
      i_pre > 0 and i_pre < i_suites,
      'pre-flight at %d, suites at %d' % (i_pre, i_suites))
check('  CONTROL: and the backup asked only at the end',
      'if ($Apply -and -not $Message) {' not in psw)
check('  the REAL check is still there, and still at the end',
      ps_now.count("Bad 'No commit subject.'") == 1 and i_real > i_suites,
      'real check at %d' % i_real)
print('        A round that MOVES a control rather than putting one in')
print('        front of it has removed a control. The guard beside')
print('        Head Commit is what actually stops the commit; this is a')
print('        pre-flight with the same words.')

# IT MUST NOT BLOCK A DRY RUN. A dry run has no subject to want, and
# blocking one would be a NEW rule arriving under cover of an earlier
# one.
seg = ps_now[i_pre:i_pre + 120] if i_pre > 0 else ''
check('  and it fires only when something would be committed',
      seg.startswith('if ($Apply -and -not $Message)'), seg[:50])
check('    CONTROL: -Push sets $Apply, so a push is covered too',
      'if ($Push) { $Apply = $true }' in ps_now)
print('        E-10 paid 330 suites, two drift guards, makemigrations and')
print('        the Django check, and was then refused for want of a')
print('        one-line subject. That is the 45 minutes this costs three')
print('        seconds now.')

# --------------------------------------------------------------------- 5c
head('5c. TN-1 - THE DUPLICATE BUTTON, DEAD ON LIVE')

TENANTS = os.path.join(ROOT, 'pages', 'views', 'tenants.py')
tn, tnw = read(TENANTS), before(TENANTS)

# THE DUPLICATE FUNCTION, NOT THE WHOLE FILE. The first draft of the
# check below searched all of tenants.py for
# `tenant_lease_agreement_status = "No Lease Agreement"` and failed -
# because line 412 writes exactly that, in the DELETE path, where it is
# correct. A control that reads a wider scope than its claim finds
# somebody else's correct code and calls it a fault.
def duplicate_body(src):
    i = src.index('def duplicate_tenant_view')
    rest = src[i:]
    j = rest.find('\ndef ')
    return rest[:j] if j > 0 else rest


dup, dupw = duplicate_body(tn), duplicate_body(tnw)

check('duplicate_tenant_view no longer assigns None to the status column',
      'tenant_lease_agreement_status = None' not in dup)
check('  CONTROL: and the backup proves it did',
      'tenant_lease_agreement_status = None' in dupw)
check('  it assigns the empty string instead',
      "tenant_lease_agreement_status = ''" in dup)
check('    which is what a tenant added through the form gets - the '
      'field is blank=True with no default',
      re.search(r'tenant_lease_agreement_status\s*=\s*models\.CharField\('
                r'[^)]*blank=True', read(os.path.join(ROOT, 'pages',
                                                      'models.py')), re.S)
      is not None)
check('    and NOT "No Lease Agreement", which is the had-one-deleted '
      'state and would be a third spelling',
      'tenant_lease_agreement_status = "No Lease Agreement"' not in dup)
check('      CONTROL: while the DELETE path still writes it, correctly',
      'tenant_lease_agreement_status = "No Lease Agreement"' in tn)

# THE CLAIM THIS RESTS ON, asked of the migration and not of the error
# message: the column really is NOT NULL, and it was made so on purpose.
mig = read(os.path.join(ROOT, 'pages', 'migrations',
                        '0095_none_columns.py'))
check("0095_none_columns lists the column it tightened",
      "('tenant', 'tenant_lease_agreement_status')" in mig)
check('  and alters it to a CharField with no null=True',
      re.search(r"name='tenant_lease_agreement_status',\s*\n\s*field="
                r'models\.CharField\((?:(?!null=True)[^)])*\)', mig)
      is not None)
print('        A MIGRATION MOVED AND ONE ASSIGNMENT DID NOT MOVE WITH IT.')
print('        Before 0095 the column took NULL and Duplicate worked.')
print('        After it, MySQL answered 1048 and the renewal button was')
print('        dead on Live. SQLite would have accepted the row, which is')
print('        why a local run never showed it - the sandbox cannot catch')
print('        this class of fault, and this check is what stands in for')
print('        the database that can.')

# AND THE REST OF THE DUPLICATE PATH, since the next NOT NULL column
# assigned None would fail in exactly the same way one error later.
nones = re.findall(r'new_tenant\.(\w+)\s*=\s*None', dup)
tight = [n for n in nones
         if "('tenant', '%s')" % n in mig]
check('no other field in the duplicate path assigns None to a column '
      '0095 tightened', not tight, '%s' % tight)
check('  CONTROL: and the path really does assign None to something - '
      'the date fields, which ARE nullable', len(nones) >= 2,
      '%s' % nones)

# ---------------------------------------------------------------------- 6
head('6. REGISTERED, ON THE GATE')

ps = read(PS1)
check('%s is in the $suites list' % ME, "'%s'" % ME in ps)
check('  and this round is on alv_rounds.ROUNDS', SUFFIX in alv_rounds.ROUNDS)
check('  and this suite is on alv_tree.CONVERTED', ME in alv_tree.CONVERTED)
check('  and the span is sentinelled as ABSENT',
      "Text = '<span class=\"action-back-label\"> Help</span>'" in ps)

# THE LAST ROW OF A POWERSHELL ARRAY LITERAL CARRIES NO COMMA. E-10
# shipped one that did; the gate would not parse, so nothing in it ran -
# no suite, no drift guard, nothing staged - and no suite could have
# caught it, because the file that will not start is the file that runs
# the suites. This reads the structure instead of a substring.
blk = ps[ps.index('$sentinels = @('):]
blk = blk[:blk.index('\n)\n')]
body = [l.rstrip() for l in blk.split('\n')
        if l.strip() and not l.strip().startswith('#')]
check('  and $sentinels does not end in a comma',
      not body[-1].endswith(','), body[-1][-40:])
check('    CONTROL: and the array is really there - %d row(s)'
      % len([l for l in blk.split('\n') if l.strip().startswith('@{')]),
      len([l for l in blk.split('\n') if l.strip().startswith('@{')]) > 300)
print('        A comma is NOT required between rows - a newline separates')
print('        elements inside @() just as a comma does, and three rows in')
print('        that table end in a bare brace in the middle of it. The')
print('        first version of this check demanded one on every row and')
print('        refused on those three: a rule invented rather than')
print('        measured, written while fixing a bug caused by the same.')

# ----------------------------------------------------------------------
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (PASS, FAIL, SKIP))
print('=' * 74)
if FAILED:
    print('')
    for f in FAILED:
        print('  FAILED  %s' % f)
if SKIP:
    print('')
    print('  %d check(s) DID NOT RUN. That is not the same as passing.'
          % SKIP)
print('')
print('  NOT PROVED HERE: that a Help button SHOULD keep its word on a')
print('  phone. 39 of the 40 already say so and this one joins them;')
print('  the alternative - teaching base to square a Help button too -')
print('  is a different round and a different argument.')
sys.exit(1 if FAIL else 0)
