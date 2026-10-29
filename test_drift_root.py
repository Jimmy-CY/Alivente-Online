"""test_drift_root.py - round E-10, 11 Oct 2026.

    python test_drift_root.py

Run from the repo root.

WHAT THIS SUITE CANNOT DO, SAID FIRST

It cannot tell you whether the CRS app has any OTHER button defect. It
reports what the classifier can see, and the classifier looks inside an
action bar and a modal footer and nowhere else. It does not read anchors
in a card, icon-only controls, or buttons built inside <script>.

WHAT IT GUARDS

Show-ButtonDrift.py built one path once and resolved every name it was
ever handed against it, so a label from the CRS root named a file that
has never existed and scan() died with a FileNotFoundError instead of a
verdict. Three things printed a reassurance over the top of that: this
round's released suite, apply_no_primary.py's bare `except Exception:
continue`, and a paragraph saying nothing in the tree was in a position
one button had been in for a fortnight.

SECTION 4 IS THE ONE THAT EARNS ITS KEEP. It renders a switched-off
danger button and measures it grey, then renders the same fixture with
this round's own block cut out of base's stylesheet and measures the red
coming back. Without that second measurement the rule is an argument.

SECTION 5 is the claim the release rests on - that the tree is a fixed
point of the classifier, over every page in both roots, twice.

SECTION 7 counts what section 4's paragraph used to assert.

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
import importlib.util
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import alv_cssrules                                             # noqa: E402
import alv_rounds                                               # noqa: E402
import alv_tree                                                 # noqa: E402

SUFFIX = '.bak_driftroot'
PATCHER = 'apply_drift_root.py'
ME = os.path.basename(__file__)
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
SBD = os.path.join(ROOT, 'Show-ButtonDrift.py')

RELEASED = ('test_disabled_state.py',)
DANGER_PAGE = 'crs/submission_detail.html'
BOOTSTRAP_PAGES = ('crs/country_list.html', 'crs/fi_list.html',
                   'crs/submission_list.html')
CRS_N = 8
N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 93, 92   # GL-3, 29 Oct 2026 - the Greek Details pop-up brings one .modal-footer to Tenant Edit and one to Tenant Add. Both matchers rise by the same two.   # (was 91, 90)   # CR-2, 27 Oct 2026 - the receipt email pop-up brings one .modal-footer to Receipts and one to Receipt Details. Both matchers rise by the same two.   # (was N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 89, 88)   # CP-2, 21 Oct 2026 - three dialogs leave the planner and two arrive, so one .modal-footer wrapper goes. BOTH matchers fall by the same one, which is what an ordinary wrapper does and is the point of keeping the pair.   # (was 90, 89)   # RD-1 and RD-2, 19 Oct 2026 - the recipe quick-look dialog and the Move dialog each bring one .modal-footer. BOTH matchers rise by the same 2, which is what an ordinary wrapper does.   # (was 88, 87)   # MO-1, 19 Oct 2026 - two more dialogs on the planner - a planned night, and leftovers. Both matchers rise by the same 2, which is what an ordinary wrapper does.   # (was 86, 85)   # MW-1, 19 Oct 2026 - the planner gains three dialogs - copy a week, save a Menu, apply a Menu - and each brings one .modal-footer. Both matchers rise by the same 3, which is what an ordinary wrapper does.   # (was 83, 82)   # RT-1, 18 Oct 2026 - six .modal-footer wrappers went with the four meal-plan screens MN-1 retired, and the planner brought none. BOTH matchers fall by the same six, which is the point of keeping the pair: the wrappers that left were ordinary ones.   # (was 89, 88)   # CC-2, 17 Oct 2026 - the contact detail modal adds one .modal-footer. Both matchers rise by the same one.   # (was 88, 87)   # CC-1, 15 Oct 2026 - the celebration day sheet adds one .modal-footer. Both matchers rise by the same one.   # (was 87, 86)   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers went, and each took one .modal-footer wrapper with it. Both matchers fall by the same two, which is itself the point: the wrappers that left were ordinary ones.   # (was 89, 88)
GREY = 'rgb(233, 236, 239)'
GREY_INK = 'rgb(138, 151, 157)'
DANGER_INK = 'rgb(179, 38, 30)'

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
check('  and the CRS root really is a second template root',
      len(alv_tree.roots()) == 2, '%d root(s)' % len(alv_tree.roots()))
crs = [alv_tree.rel(p) for p in alv_tree.templates()
       if alv_tree.rel(p).startswith('crs/')]
check('  holding %d page(s) - the eight the tool could not open' % len(crs),
      len(crs) == CRS_N, '%d' % len(crs))

# ---------------------------------------------------------------------- 2
head('2. THE TOOL RESOLVES A NAME; ITS CENSUS IS UNCHANGED')

src = read(SBD)
was = before(SBD)

check('Show-ButtonDrift has a resolver', 'def resolve(name):' in src)
left = re.findall(r'os\.path\.join\(TPL,\s*\w+\)', code_lines(src))
check('  and no site resolves a name against the one root', not left,
      '%d left: %s' % (len(left), left[:2]))
check('  CONTROL: and the backup proves there were six',
      len(re.findall(r'os\.path\.join\(TPL,\s*\w+\)', code_lines(was))) == 6,
      '%d' % len(re.findall(r'os\.path\.join\(TPL,\s*\w+\)',
                            code_lines(was))))

# THE CENSUS IS NOT THE RESOLUTION, and this round leaves it alone on
# purpose: apply_button_sweep.py reads sb.TPL and test_button_sweep.py
# reads sb.templates(False), whose narrow root rebuilds a pre-sweep tree
# from its own backups.
check('  the census still walks TPL, exactly once',
      code_lines(src).count('os.walk(TPL)') == 1,
      '%d' % code_lines(src).count('os.walk(TPL)'))
check('    and TPL still means pages/templates',
      "TPL = os.path.join(ROOT, 'pages', 'templates')" in src)
check('    so apply_button_sweep still reads the scope it stands on',
      'TPL = sb.TPL' in read(os.path.join(ROOT, 'apply_button_sweep.py')))

sys.argv = [sys.argv[0]]
_spec = importlib.util.spec_from_file_location('sbd', SBD)
sb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sb)

# MEASURED, NOT READ. The claim is that scan() opens a CRS page, so the
# check opens one.
opened, raised = [], []
for rel in crs:
    try:
        sb.scan(rel)
        opened.append(rel)
    except Exception as e:
        raised.append('%s: %s' % (rel, str(e)[:48]))
check('scan() opens all %d CRS page(s)' % len(crs), not raised,
      '; '.join(raised[:2]))
check('  CONTROL: and the tool census does NOT list them - '
      'resolution widened, scope did not',
      not [f for f in sb.templates(True) if f.startswith('crs/')],
      '%d listed' % len([f for f in sb.templates(True)
                         if f.startswith('crs/')]))
check('    CONTROL: while the census is not empty',
      len(sb.templates(False)) >= 100, '%d' % len(sb.templates(False)))
print('        The eight came back as FileNotFoundError, and the suite that')
print('        found them turns a crash into a line of drift - so eight')
print('        unopenable pages read as eight drifting buttons. Twelve')
print('        really did drift, behind them.')

# A SHARED TOOL THAT GAINS A DEPENDENCY OWNS EVERY HARNESS THAT COPIES
# IT. test_button_sweep rebuilds a pre-sweep tree in a temp directory
# three times over and copies the tool into it. The moment the tool
# imports alv_tree those three copies run a tool whose import fails -
# and the failure arrives as an EMPTY REPORT rather than an error,
# because the harness greps stdout for lines and finds none. Six checks
# in that suite went red together and not one of them said ImportError.
bs_p = os.path.join(ROOT, 'test_button_sweep.py')
bs, bsw = read(bs_p), before(bs_p)
holds = re.findall(r"shutil\.copy2\(os\.path\.join\(ROOT,[^\n]*\n?[^\n]*",
                   bs)
lists = len(re.findall(r"'alv_tree\.py'", bs))
check('every harness that copies the tool copies alv_tree too - %d site(s)'
      % lists, lists == 3, '%d' % lists)
check('  CONTROL: and the backup copied it in none of them',
      "'alv_tree.py'" not in bsw,
      '%d' % len(re.findall(r"'alv_tree\.py'", bsw)))
check('  and the experiment is unchanged - those trees hold one root, '
      'and alv_tree SKIPS a root that is not on disk',
      'if os.path.isdir(p) and p not in out' in read(
          os.path.join(ROOT, 'alv_tree.py')))

# ---------------------------------------------------------------------- 3
head('3. A CLASS IS A TOKEN, NOT A SUBSTRING')

# ON LITERALS, so it cannot go vacuous the day the tree happens to carry
# no awkward wrapper.
def n_footers(markup):
    return len(sb.footers(sb.markup_of(markup)))


BTN = '<button class="btn action-secondary">Download</button>'
check('xml-modal-footer is NOT a modal footer',
      n_footers('<div class="xml-modal-footer">%s</div>' % BTN) == 0)
check('  CONTROL: and modal-footer still is',
      n_footers('<div class="modal-footer">%s</div>' % BTN) == 1)
check('  CONTROL: with a second class beside it, too - the loose match '
      'was doing real work',
      n_footers('<div class="modal-footer mt-3">%s</div>' % BTN) == 1)
check('  CONTROL: and before it, as well',
      n_footers('<div class="d-flex modal-footer">%s</div>' % BTN) == 1)

loose = re.compile(r'<div[^>]*class="[^"]*modal-footer[^"]*"[^>]*>')
tight = re.compile(r'<div[^>]*class="[^"]*(?<![-\w])modal-footer'
                   r'(?![-\w])[^"]*"[^>]*>')
nl = nt = 0
odd = []
for p in alv_tree.templates():
    mk = read(p)
    a, b = len(loose.findall(mk)), len(tight.findall(mk))
    nl += a
    nt += b
    if a != b:
        odd.append(alv_tree.rel(p))
check('tree-wide the two matchers differ by one wrapper: %d and %d' % (nl, nt),
      (nl, nt) == (N_FOOTER_SUBSTRING, N_FOOTER_TOKEN), '%d, %d' % (nl, nt))
check('  and the page that moves is %s' % DANGER_PAGE, odd == [DANGER_PAGE],
      '%s' % odd)

dp = alv_tree.last_path(DANGER_PAGE)
dnow = read(dp)
check('  so the XML Viewer Download is still paper, not teal',
      'id="xmlViewerDownload" href="#" class="btn action-secondary"' in dnow)
check('    CONTROL: and it was secondary before this round too - the '
      'promotion was the TOOL asking, not the page drifting',
      'id="xmlViewerDownload" href="#" class="btn action-secondary"'
      in before(dp))
print('        The tool docstring is about a matcher that could not see two')
print('        thirds of the bars. This is the other direction of the same')
print('        error, and it is one instance wide in 151 templates.')

# ---------------------------------------------------------------------- 4
head('4. BASE GREYS A SWITCHED-OFF DANGER - and it is the round')

bp = alv_tree.last_path('base.html')
B, BW = read(bp), before(bp)
for sel in ('.action-danger.disabled-btn',
            '.btn.action-danger.disabled-btn',
            '.btn.action-danger:disabled',
            '.btn.action-danger[disabled]',
            '.btn.action-danger[aria-disabled="true"]'):
    check('  base declares %s' % sel, sel in B)
check('  CONTROL: and the backup proves it declared NONE of them',
      '.action-danger.disabled-btn' not in BW)
check('  the same five shapes the primary block already used',
      B.count('[aria-disabled="true"]') >= 2)
# POSITION IS LOAD-BEARING, the way it is for the back-button block
# twenty rules above: a bare `disabled` attribute does not stop :hover,
# so a later rule of equal specificity has to be the disabled one.
check('  and it sits BELOW the danger colour and its hover',
      0 < B.find('.action-danger:hover') < B.find('.action-danger.disabled'),
      '%d vs %d' % (B.find('.action-danger:hover'),
                    B.find('.action-danger.disabled')))

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

if sync_playwright is None:
    skip('the switched-off danger renders grey', 'playwright not installed')
    skip('CONTROL: a live danger is still red', 'ditto')
    skip('CONTROL: and without the new block the red comes back', 'ditto')
else:
    boot = read(os.path.join(ROOT, 'test_fixture_bootstrap413.css'))
    bcss = re.sub(r'\{%.*?%\}', '', css_of(B), flags=re.S)
    # THE CONTROL THAT MAKES THE MEASUREMENT MEAN SOMETHING: the same
    # fixture with E-10's own block cut out of the stylesheet. If the
    # colour does not come back, the grey was never this round's.
    cut = re.sub(r'\.action-danger\.disabled-btn,[^{}]*\{[^{}]*\}', '', bcss)
    if cut == bcss:
        check('CONTROL: the stylesheet-minus-this-round could be built',
              False, 'the block was not found to remove')
        cut = bcss
    refused = []

    def shades(css):
        doc = ('<!doctype html><html><head><meta charset="utf-8">'
               '<link rel="stylesheet" href="https://example.invalid/x.css">'
               '<style>%s</style><style>%s</style>'
               '<style>*{transition:none!important}</style></head><body>'
               '<div class="form-card">'
               '<button id="off" class="btn action-danger" disabled>Close'
               '</button>'
               '<button id="live" class="btn action-danger">Close</button>'
               '<button id="pair" class="btn action-secondary action-danger '
               'disabled-btn" disabled>Close</button>'
               '</div></body></html>' % (boot, css))
        fx = os.path.join(SCRATCH, 'e10_%d.html' % (len(css) % 999983))
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(doc)
        pw = sync_playwright().start()
        try:
            br = pw.chromium.launch()
            ctx = br.new_context(viewport={'width': 900, 'height': 300})

            def _abort(route):
                refused.append(route.request.url)
                route.abort()

            ctx.route(re.compile(r'^https?://'), _abort)
            pg = ctx.new_page()
            _goto(pg, fx)
            pg.wait_for_timeout(110)
            out = {}
            for i in ('off', 'live', 'pair'):
                out[i] = pg.eval_on_selector(
                    '#' + i,
                    "e => { const s = getComputedStyle(e);"
                    " return [s.backgroundColor, s.color].join('|'); }")
            ctx.close()
            br.close()
            return out
        finally:
            pw.stop()

    withr, without = shades(bcss), shades(cut)
    check('CONTROL: the fixture asked for a remote stylesheet and the '
          'browser REFUSED it, both times', len(refused) == 2,
          '%d refused' % len(refused))
    check('a switched-off danger renders grey: %s' % withr['off'],
          withr['off'] == '%s|%s' % (GREY, GREY_INK), withr['off'])
    check('  and so does the paired, class-marked twin - one answer, '
          'not two', withr['pair'] == withr['off'],
          '%s vs %s' % (withr['pair'], withr['off']))
    check('  CONTROL: while a LIVE danger is still red',
          DANGER_INK in withr['live'], withr['live'])
    check('  CONTROL: and with this round block cut out of base, the red '
          'comes back - %s' % without['off'],
          DANGER_INK in without['off'], without['off'])
    print('        That last line is the whole round. Before it, the only')
    print('        dimming on that button was Bootstrap .btn:disabled at')
    print('        .65 opacity - a faint red button where every other')
    print('        switched-off control in the system is grey.')

# ---------------------------------------------------------------------- 5
head('5. THE TWELVE, AND THE TREE AS A FIXED POINT')

def plan(rel, text=None):
    raw = text if text is not None else read(alv_tree.last_path(rel))
    sb.JS_REENABLED = sb.js_reenabled_ids(raw)
    return sb._scan(rel, sb.markup_of(raw))


rels = sorted(alv_tree.rel(p) for p in alv_tree.templates())
scope = [r for r in rels if r != 'base.html' and not sb.is_recipe_side(r)]
drift, hits = [], 0
for r in scope:
    for h in plan(r):
        hits += 1
        if h[7]:
            continue
        if h[3].split() != h[4].split():
            drift.append('%s %s: %s -> %s' % (r, h[1][:16], h[3][:28],
                                              h[4][:28]))
for d in drift[:6]:
    print('        %s' % d)
check('no button in the WHOLE tree disagrees with the classifier',
      not drift, '%d do' % len(drift))
check('  CONTROL: over %d page(s) and %d button(s), not an empty scan'
      % (len(scope), hits), len(scope) >= 120 and hits >= 500,
      '%d pages, %d hits' % (len(scope), hits))

# A CLASSIFIER MUST BE A FIXED POINT ON ITS OWN OUTPUT. The sweep's own
# round records why: reading only `btn-danger` made the rule depend on
# the class it removes, so a second run flipped a delete button to a
# solid teal primary.
twice = []
for r in scope:
    for h in plan(r):
        if h[7]:
            continue
        if h[3].split() != h[4].split():
            twice.append(r)
check('  and the second pass over that same output agrees', not twice,
      '%d' % len(twice))

# CONTROL: THEY WERE REALLY THERE. Read from the backups, so the claim
# is against what this round replaced and not against a memory.
#
# AND READ TWICE, BY BOTH MATCHERS, BECAUSE THE TWO HALVES OF THIS ROUND
# ARE SEPARABLE. The first draft of this check asserted twelve and got
# eleven, which was the check being wrong and not the round: read by the
# tool AS E-10 LEAVES IT, the old pages carry eleven. The twelfth existed
# only because the old matcher read `xml-modal-footer` as `modal-footer`
# and promoted a Download. So the number is eleven real plus one the
# instrument was asking for, and the difference between the two readings
# is exactly the promotion this round refuses.
def drifting_in(text, rel):
    return len([h for h in plan(rel, text)
                if not h[7] and h[3].split() != h[4].split()])


OLD_PAGES = [(r, before(alv_tree.last_path(r)))
             for r in BOOTSTRAP_PAGES + (DANGER_PAGE,)]
tight_n = sum(drifting_in(t, r) for r, t in OLD_PAGES)
_saved = sb.footers
sb.footers = lambda m: [('modal footer', a, z) for a, z in sb.spans(
    m, r'<div[^>]*class="[^"]*modal-footer[^"]*"[^>]*>')]
try:
    loose_n = sum(drifting_in(t, r) for r, t in OLD_PAGES)
finally:
    sb.footers = _saved

check('  CONTROL: the backups carry %d real drifting button(s)' % tight_n,
      tight_n == 11, '%d' % tight_n)
check('    six of them wearing Bootstrap on %d CRS modal(s)'
      % len(BOOTSTRAP_PAGES),
      sum(drifting_in(t, r) for r, t in OLD_PAGES
          if r != DANGER_PAGE) == 6,
      '%d' % sum(drifting_in(t, r) for r, t in OLD_PAGES
                 if r != DANGER_PAGE))
check('    and the OLD matcher found one more - %d - which is the '
      'promotion it was asking for by substring' % loose_n,
      loose_n == tight_n + 1, '%d vs %d' % (loose_n, tight_n))
print('        Eleven real, plus one the instrument invented. The master')
print('        logged twelve; eleven of them were the pages and the')
print('        twelfth was the tool.')

# AND FOUR OF THE TWELVE ARE SAID TO BE NOTHING. Measured in section 4:
# a bare action-danger and the pair render identically. The pair went on
# anyway, because a fixed point is what releases the suite - and saying
# so is the difference between a finding and a sales pitch.
nowt = len(re.findall(r'class="btn action-secondary action-danger"', dnow))
check('the four that measure identical are paired anyway', nowt == 4,
      '%d' % nowt)
check('  and the one that does not - the switched-off Close - carries '
      'the class as well',
      'class="btn action-secondary action-danger disabled-btn" disabled>'
      in dnow)

# ---------------------------------------------------------------------- 6
head('6. THE SWALLOW THAT HID ALL OF IT')

np = os.path.join(ROOT, 'apply_no_primary.py')
check('apply_no_primary no longer swallows a crash',
      'except Exception:\n        continue' not in code_lines(read(np)))
check('  and reports it as what it is',
      'the scan raised' in read(np))
check('  CONTROL: and the backup proves it swallowed',
      'except Exception:\n        continue' in code_lines(before(np)))
print('        It walks the whole tree and calls the same scan(). It')
print('        crashed on eight of 125 pages, swallowed it, and printed')
print('        "no button disagrees with the classifier" for a fortnight.')
print('        A control that cannot fail is worse than no control.')

# ---------------------------------------------------------------------- 7
head('7. WHAT IS STILL TRUE, COUNTED RATHER THAN ASSERTED')

off_back = []
for p in alv_tree.templates():
    for m in re.finditer(r'<(?:button|input|a)\b[^>]*>',
                         alv_tree.code_only(read(p))):
        tag = m.group(0)
        if 'action-back' not in tag and 'back-button' not in tag:
            continue
        if (re.search(r'\sdisabled(?=[\s>=/])', tag)
                or 'aria-disabled="true"' in tag
                or 'disabled-btn' in tag):
            off_back.append('%s %s' % (alv_tree.rel(p),
                                       ' '.join(tag.split())[:40]))
print('        switched-off action-back controls in the tree: %d'
      % len(off_back))
for x in off_back[:4]:
    print('          %s' % x)
check('base has no [disabled] rule for .action-back, and nothing needs one',
      ('.action-back.disabled-btn' in B) == bool(off_back),
      '%d control(s), rule %s' % (len(off_back),
                                  'present' if '.action-back.disabled-btn'
                                  in B else 'absent'))
check('  CONTROL: and the census can find a switched-off control when '
      'there is one',
      len(re.findall(r'\sdisabled(?=[\s>=/])',
                     alv_tree.code_only(dnow))) >= 1)
print('        THIS IS THE SHAPE OF THE SENTENCE THAT HID A REAL BUTTON.')
print('        The suite printed "nothing in the tree is in that position"')
print('        as a claim. It is a COUNT, so it is counted - and the day it')
print('        stops being zero, the rule follows it instead of the')
print('        paragraph quietly going false.')

# ---------------------------------------------------------------------- 8
head('8. WIDENED, RELEASED, AND EVERY NUMBER THAT COUNTS IT')

for n in RELEASED:
    s = read(os.path.join(ROOT, n))
    check('  %s walks through alv_tree' % n, 'alv_tree.walk3()' in s)
    own = re.findall(r'os\.walk\((T|TPL|ROOT)\)', code_lines(s))
    check('    and walks no root of its own', not own, '%s' % own)
    check('    and resolves nothing through it either',
          not re.findall(r'os\.path\.(?:join|relpath)\([^()]*,\s*T\)',
                         code_lines(s)))
    check('    with the danger tone on its list - the other half of the '
          'blindness',
          "'action-danger'" in s and 'TONES = ' in s)
    # AND THE CONTROL THAT WAS LEANING ON THE DEFECT. Its own section 1
    # proved its search was not vacuous with "danger has no attribute
    # rule", which this round makes false. A control that goes false on
    # the round that fixes what it was leaning on has to move, not be
    # deleted.
    check('    and its not-vacuous control moved to a tone base really '
          'does not cover',
          "'.btn.action-back[disabled]' not in B" in code_lines(s))
    check('      CONTROL: and the backup proves it leaned on the danger '
          'tone', "'.btn.action-danger[disabled]' not in B"
          in code_lines(before(os.path.join(ROOT, n))))
    check('    off alv_tree.WAITING', n not in alv_tree.WAITING)
    check('    on alv_tree.CONVERTED', n in alv_tree.CONVERTED)

check('none of the %d this round released is still held' % len(RELEASED),
      not [n for n in RELEASED if n in alv_tree.WAITING],
      '%s' % [n for n in RELEASED if n in alv_tree.WAITING])
check('  CONTROL: and WAITING is not empty - %d still held'
      % len(alv_tree.WAITING), len(alv_tree.WAITING) > 0)
check('  and no WAITING reason still says 120 templates against 146 - '
      'both numbers had moved',
      '120 templates, not 146' not in str(alv_tree.WAITING))

x0 = read(os.path.join(ROOT, 'test_tree_roots.py'))
wd = read(os.path.join(ROOT, 'test_waiting_down.py'))


def pin(text, name):
    """A pinned number, whether it is assigned alone or in a tuple.

    test_bar_height writes `N_BAR, N_ROW, N_MODAL = 265, 110, 98`, and
    the one-name reader every suite in this repo carries answers None
    for two of those three and - worse - 265 for one of them, because
    `N_MODAL = (\\d+)` never matches and an unanchored `N_BAR` pattern
    reaches the first number on the line. Both halves of that happened
    here, on the first run of this check.
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
check('    and Show-ButtonDrift is STILL on that list, deliberately',
      'os.walk(TPL)' in code_lines(src))
# AND THE TWO CENSUSES THE TWELVE WALK INTO, found by the sweep.
# DB-5, 12 Oct 2026 - AS E-10 LEFT THEM, not as they stand today.
# These two lines read the live files, so the first later round to
# re-pin either census made this suite report that E-10 had done
# something it had not. DB-5 was that round. A suite asking about
# its OWN round must never read the live file - lesson 40, and the
# three checks below now pass for every round after this one too.
bh = alv_rounds.as_left_by(
    os.path.join(ROOT, 'test_bar_height.py'), SUFFIX, read)
pc = alv_rounds.as_left_by(
    os.path.join(ROOT, 'test_pair_contrast.py'), SUFFIX, read)
check('D-1 heights re-pinned - 7 into modals, 4 into cards',
      pin(bh, 'N_MODAL') == 98 and pin(bh, 'N_LOOSE') == 82,
      '%s, %s' % (pin(bh, 'N_MODAL'), pin(bh, 'N_LOOSE')))
check('  and they ROSE, because that census selects the two position '
      'tones and not the danger tone',
      pin(bh, 'N_MODAL') > pin(before(os.path.join(
          ROOT, 'test_bar_height.py')), 'N_MODAL'))
check('  CONTROL: the twelve distinct loose heights did not move',
      pin(bh, 'N_LOOSE_H') == 12, '%s' % pin(bh, 'N_LOOSE_H'))
check('B-4b pair census re-pinned - five selectors, one block',
      pin(pc, 'EXPECT_PAIRS')
      == pin(before(os.path.join(ROOT, 'test_pair_contrast.py')),
             'EXPECT_PAIRS') + 5,
      '%s' % pin(pc, 'EXPECT_PAIRS'))
check('  and the same five join the INACTIVE exemption, written down',
      pin(pc, 'EXPECT_INACTIVE')
      == pin(before(os.path.join(ROOT, 'test_pair_contrast.py')),
             'EXPECT_INACTIVE') + 5
      and pc.count(".btn.action-danger[aria-disabled=") == 1,
      '%s' % pin(pc, 'EXPECT_INACTIVE'))
check('    CONTROL: and test_recipe_spice still DERIVES that number '
      'rather than holding a copy',
      'EXPECT_PAIRS = (\\d+)' in read(
          os.path.join(ROOT, 'test_recipe_spice.py')))
print('        NOT TAKEN: one `btn action-danger btn-sm` on')
print('        act_expense.html is still invisible to D-1 census, which')
print('        selects action-primary, -secondary, -back, -filter,')
print('        -more-btn and -icon and no danger tone. Widening someone')
print('        else census is their round. This one re-pins what it moved.')

check('CONVERTED_N agrees with the live register',
      pin(wd, 'CONVERTED_N') == len(alv_tree.CONVERTED),
      '%s vs %d' % (pin(wd, 'CONVERTED_N'), len(alv_tree.CONVERTED)))
check('  and WAITING_N too',
      pin(wd, 'WAITING_N') == len(alv_tree.WAITING),
      '%s vs %d' % (pin(wd, 'WAITING_N'), len(alv_tree.WAITING)))

# AND THE TWO AGGREGATES E-1b PINNED ONE ROUND AGO.
hc = read(os.path.join(ROOT, 'test_held_contrast.py'))
check('test_held_contrast no longer pins the size of the register',
      'len(alv_tree.WAITING) == WAITING_AFTER' not in code_lines(hc))
check('  nor the ceiling at a number',
      "== CEILING_AFTER" not in code_lines(hc))
check('  CONTROL: and its backup proves it pinned both',
      'len(alv_tree.WAITING) == WAITING_AFTER'
      in code_lines(before(os.path.join(ROOT, 'test_held_contrast.py'))))
check('  while what it DOES claim - that its own two came off - survives',
      'neither of the two this round released is still held' in hc)
print('        E-1b repaired this exact shape in E-1a own suite and wrote')
print('        the rule down in the same round: a pinned COUNT moves, a')
print('        pinned DECISION does not, and a pinned AGGREGATE was never')
print('        either. Then it pinned two. Third round running.')

# ---------------------------------------------------------------------- 9
head('9. REGISTERED, ON THE GATE')

ps = read(PS1)
check('%s is in the $suites list' % ME, "'%s'" % ME in ps)
check('  and this round is on alv_rounds.ROUNDS', SUFFIX in alv_rounds.ROUNDS)
check('  and this suite is on alv_tree.CONVERTED', ME in alv_tree.CONVERTED)
check('  and the gate still runs the drift guard it has always run',
      '--strict' in ps and 'Show-ButtonDrift.py' in ps)
# A STANDARD THAT IS ONLY IN A SUITE IS A STANDARD THE NEXT PAGE COPIED
# FROM AN OLD ONE WILL QUIETLY LEAVE - the gate's own words, and the
# reason the sentinel table exists beside the suites.
for txt, why in (('.btn.action-danger[disabled]', 'the switched-off danger'),
                 ('btn btn-danger', 'the CRS delete tone'),
                 ('btn btn-secondary', 'and its Cancel')):
    check('  %s is sentinelled - %s' % (why, txt),
          "Text = '%s'" % txt in ps)
check('    and the two Bootstrap rows are ABSENT rows, which is what they '
      'claim', ps.count("Absent = $true; Code = $true },") >= 2)

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
print('  NOT PROVED HERE: that the CRS app has no OTHER button defect.')
print('  The classifier does not look at anchors outside a bar or a')
print('  footer, at icon-only controls, or at anything built inside')
print('  <script>, and the --js census over those eight pages has not')
print('  been run. 57 buttons on the recipe side still drift, excluded')
print('  by name as they have been since the sweep.')
sys.exit(1 if FAIL else 0)
