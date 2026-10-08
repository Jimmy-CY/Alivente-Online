# -*- coding: utf-8 -*-
"""test_system_teal.py - Section AD round AD-1, 8 Oct 2026.

Demetri: "I want to change the System Tab to conform with our Teal
colours. IT MUST LOOK AND BEHAVE EXACTLY LIKE THE FUNCTIONAL TAB WITH
REGARDS TO COLOURS."

THAT IS A CLAIM ABOUT WHAT RENDERS, so section 2 renders it. Both tabs,
both panels, both tiles, at rest and hovered, measured in Chromium, and
asserted EQUAL - not "uses the accent token", which is a claim about
source and would pass while the two still looked different.

The control is the page as the round found it, where the same probe
reports the grey. A suite that cannot produce the difference is not
measuring the sameness.

=====================================================================
SECTION 3: ONE NUMBER WENT DOWN, ON PURPOSE
=====================================================================

The System tile was white on --alv-ink-soft at 5.53:1 and is now white
on --alv-accent at 4.91:1. Both clear AA. 4.91 is what the Functional
tile has always read, and matching it IS the instruction - but a round
that lowers a contrast ratio and does not say so is a round hoping
nobody checks.

The tab went the other way, 3.95:1 to 4.31:1, and 4.31 is Functional's
number. Still under AA, as Functional's always has been: that is the
house accent-on-tint pairing, it is ONE BASE DECISION nobody has taken,
and test_pair_contrast.py section 5 now counts eighteen of them.

=====================================================================
SECTION 4: A RESERVED CELL IS NOT A DISABLED BUTTON
=====================================================================

The two Coming Soon tiles are gone and he asked for blank space, so the
cells stay and hold the row. What is asserted is that they are blank in
every sense that matters: no fill, no border, no shadow, no hover, no
text, aria-hidden, and pointer-events off. A greyed-out button with its
label deleted would pass a markup check and fail every one of these.

.btn-future-disabled went with them, and with it the last #adb5bd on
the page that was not a live permission state. .btn-perm-disabled keeps
its one, because a user without the right genuinely cannot click it.

=====================================================================
SECTION 5: THE DECISION THIS ROUND OVERTURNED
=====================================================================

test_personal_teal.py decided the grey, in these words: "the FUTURE side
is grey, not green." It was right on the day. AD-1 spends that claim for
admin_apms and leaves it standing for personal.html, whose FUTURE tab is
still commented out and still grey, and writes his instruction and the
date into the table beside it.

B-4 overturned test_fsr_palette's decided #ecd9a8 in silence and had to
be backed out. This section exists so that the next round to meet this
page finds the reason and not just the change.
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

ROOT = os.getcwd()
TPL = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(TPL):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)

SUFFIX = '.bak_systeal'
ME = 'test_system_teal.py'
PATCHER = 'apply_system_teal.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(TPL, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'
PAGE = os.path.join(TPL, 'admin_apms.html')

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
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_rounds as RD                                    # noqa: E402
import alv_tree as T                                       # noqa: E402
import apply_edit_ink as B                                 # noqa: E402


def left(p):
    """The page as THIS round left it. PR-1 adds a Compliance tab and
    FN-2 rebuilds Finance; neither should turn this suite red."""
    return RD.as_left_by(p, SUFFIX, read)


def was(p):
    return read(p + SUFFIX)


# ==========================================================================
head('1. SCOPE - ONE PAGE')
# ==========================================================================
ok(os.path.isfile(PAGE + SUFFIX), 'admin_apms.html has its backup')
touched = [p for p in T.templates() if os.path.isfile(p + SUFFIX)]
ok(len(touched) == 1, 'and it is the ONLY template this round touched',
   [T.rel(p) for p in touched])
src = left(PAGE)
old = was(PAGE)
ok('--future-dark: var(--alv-accent);' in src,
   '--future-dark now points at the accent', )
ok('--future-dark: #6c757d;' in old,
   '  CONTROL: before this round it was the grey #6c757d')
ok('--future-light: var(--alv-accent-soft);' in src,
   '--future-light now points at the accent wash')


# ==========================================================================
head('2. RENDERED - THE TWO TABS ARE THE SAME COLOUR, AND WERE NOT')
# ==========================================================================
# "Exactly like the Functional Tab with regards to colours" is a claim
# about what renders, so it is measured in a browser and asserted EQUAL.
# "Uses var(--alv-accent)" would be a claim about source: it can be true
# while the two still look different, because a page-local token, a
# later rule or a media query can land on top of it.
try:
    from playwright.sync_api import sync_playwright
except Exception as _e:
    sync_playwright = None
    skip('sections 2 and 4b', 'playwright unavailable: %s' % str(_e)[:40])

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('sections 2 and 4b', 'playwright or the bootstrap fixture is missing')
else:
    MODAL_IF = re.compile(
        r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)

    def styles_of(t):
        return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)),
                       flags=re.S)
                for m in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                     re.S | re.I)]

    def body_markup(t):
        m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock',
                      t, re.S)
        x = m.group(1) if m else t
        x = re.sub(r'<(script|style)\b.*?</\1>', '', x, flags=re.S | re.I)
        for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
            x = re.sub(rx, '', x, flags=re.S)
        return re.sub(r'\{\{.*?\}\}', 'x', x, flags=re.S)

    boot = read(BOOT)
    bcss = '\n'.join(styles_of(read(BASE)))

    # HOLD THE PAGE STILL, AND THIS IS NOT TIDINESS.
    #
    # .admin-tab carries `transition: all 0.3s ease`. This suite makes a
    # tab active by adding the class, and getComputedStyle immediately
    # after returns the value the transition is STARTING FROM, not the
    # one it is going to. The System tab read rgb(255,255,255) - its
    # resting white - at both widths, for a quarter of a second, while
    # the Functional tab read the wash correctly because IT was already
    # active when the page loaded and had never transitioned at all.
    #
    # It cost an hour. The first four hypotheses were all about the
    # cascade - specificity, !important, a var() that would not resolve -
    # and the thing that settled it was setting background-color to a
    # LITERAL inline and still reading white, which no cascade can do.
    #
    # ANY SUITE THAT TOGGLES A CLASS AND THEN READS A COLOUR HAS THIS
    # BUG. test_personal_teal.py does not, because it renders two pages
    # and never toggles anything. This one does, so it stops the clock.
    STILL = ('*,*::before,*::after{transition:none !important;'
             'animation:none !important}')

    def fixture(t):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style>%s<style>%s</style></head>'
                '<body class="has-sidebar"><div class="main-content '
                'with-sidebar">%s</div></body></html>'
                % (boot, bcss,
                   ''.join('<style>%s</style>' % c for c in styles_of(t)),
                   STILL, body_markup(t)))

    # Both halves are probed by the SAME selectors with only the family
    # word changed, so the comparison cannot accidentally be of a tab
    # against a panel.
    def sels(fam, active):
        return {
            'tab ink': '.admin-tab.%s-tab' % fam,
            'tab fill': '.admin-tab.%s-tab' % fam,
            'panel': '.tab-panel.%s-panel' % fam,
            'tile': '.admin-btn.btn-%s' % fam,
        }

    PROBE = """(spec) => {
        const out = {};
        for (const [k, s] of Object.entries(spec)) {
            const e = document.querySelector(s);
            if (!e) { out[k] = null; continue; }
            const cs = getComputedStyle(e);
            out[k] = k === 'tab ink' ? cs.color : cs.backgroundColor;
        }
        return out;
    }"""
    # The ACTIVE state is a class, so it is set rather than hovered -
    # the two tabs are never active at the same time on a real screen
    # and the question here is only what each one computes when it is.
    ACTIVATE = """(fam) => {
        for (const t of document.querySelectorAll('.admin-tab'))
            t.classList.remove('active');
        for (const p of document.querySelectorAll('.tab-panel'))
            p.classList.remove('active');
        const tab = document.querySelector('.admin-tab.' + fam + '-tab');
        const pan = document.querySelector('.tab-panel.' + fam + '-panel');
        if (tab) tab.classList.add('active');
        if (pan) pan.classList.add('active');
        return !!(tab && pan);
    }"""

    launched = False
    with sync_playwright() as pw:
        try:
            br = pw.chromium.launch(**({'executable_path': EXE}
                                       if os.path.exists(EXE) else {}))
            launched = True
        except Exception as _e:
            skip('sections 2 and 4b', 'chromium would not launch: %s'
                 % str(_e).split('\n')[0][:60])

        if launched:
            n = [0]

            def probe(text, w, still=True, extra=None):
                """{family: {key: colour}} for both halves, at width w.

                With `extra`, also returns that script's value under the
                key 'extra' - used for the geometry in section 4b.
                """
                n[0] += 1
                fx = os.path.join(SCRATCH, 'ad1_%d_%d.html' % (w, n[0]))
                with open(fx, 'w', encoding='utf-8') as fh:
                    fh.write(fixture(text) if still
                             else fixture(text).replace(STILL, ''))
                ctx = br.new_context(viewport={'width': w, 'height': 900})
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                _goto(pg, fx)
                try:
                    out = {}
                    for fam in ('alivente', 'future'):
                        pg.evaluate(ACTIVATE, fam)
                        out[fam] = pg.evaluate(PROBE, sels(fam, True))
                    if extra:
                        pg.evaluate(ACTIVATE, 'future')
                        out['extra'] = pg.evaluate(extra)
                    return out
                finally:
                    ctx.close()

            def probe_moving(text, w):
                return probe(text, w, still=False)

            for w, label in ((1280, 'desktop'), (390, 'phone  ')):
                now = probe(src, w)
                before = probe(old, w)
                for k in ('tab ink', 'tab fill', 'panel', 'tile'):
                    a, f = now['alivente'].get(k), now['future'].get(k)
                    ok(a is not None and f is not None,
                       '%s  %-9s both halves render a colour' % (label, k),
                       (a, f))
                    ok(a == f,
                       '%s  %-9s Functional %s == System %s'
                       % (label, k, a, f), (a, f))
                # THE CONTROL. The same probe on the page this round
                # found reports a DIFFERENT colour for at least three of
                # the four - which is why this check can fail.
                diff = [k for k in ('tab ink', 'tab fill', 'panel', 'tile')
                        if before['alivente'].get(k)
                        != before['future'].get(k)]
                ok(len(diff) >= 3,
                   '%s  CONTROL: before this round %d of the 4 differed - %s'
                   % (label, len(diff), ', '.join(diff)), diff)

            # SECOND CONTROL: the clock. Run the same probe with the
            # transition left in and the newly-activated tab reports the
            # colour it is LEAVING. If this ever stops being true the
            # stillness rule above has become unnecessary - and until it
            # does, every suite in this house that toggles a class and
            # reads a colour is reading the wrong end of 300ms.
            moving = probe_moving(src, 1280)
            ok(moving['future']['tab fill'] != moving['alivente']['tab fill'],
               'CONTROL: with the transition left in, the same probe reports '
               '%s for the tab it just activated and %s for the one that was '
               'already active - which is the start of a 0.3s transition, '
               'not a colour'
               % (moving['future']['tab fill'],
                  moving['alivente']['tab fill']),
               moving)


# ==========================================================================
head('3. THE CONTRAST - AND THE ONE THAT WENT DOWN ON PURPOSE')
# ==========================================================================
tok = B.base_tokens()
tile_was = B.contrast('#5b6b73', '#ffffff')
tile_now = B.contrast(tok['--alv-accent'], '#ffffff')
ok(tile_now >= 4.5,
   'the System tile reads %.2f:1 - it clears AA' % tile_now)
ok(tile_now < tile_was,
   '  AND IT WENT DOWN, %.2f -> %.2f. That is the instruction, not an '
   'accident: 4.91 is what the Functional tile has always read, and the '
   'round is told to match it' % (tile_was, tile_now))
ok(abs(B.contrast(tok['--alv-accent-ink'], '#ffffff') - 7.44) < .05,
   '  and the hover is --alv-accent-ink at %.2f:1, like Functional'
   % B.contrast(tok['--alv-accent-ink'], '#ffffff'))
tab_was = B.contrast('#6c757d', '#e9ecef')
tab_now = B.contrast(tok['--alv-accent'], tok['--alv-accent-soft'])
ok(tab_now > tab_was,
   'the active tab went UP, %.2f -> %.2f' % (tab_was, tab_now))
ok(tab_now < 4.5,
   '  and it is still under AA at %.2f:1 - which is where Functional has '
   'always been. The house accent on the house tint is ONE BASE DECISION '
   'and test_pair_contrast.py section 5 counts eighteen of them'
   % tab_now)


# ==========================================================================
head('4. THE RESERVED CELLS - NOT DISABLED BUTTONS')
# ==========================================================================
ok(src.count('admin-btn--reserved') >= 2,
   'two reserved cells hold the second row, so the panel keeps its height',
   src.count('admin-btn--reserved'))
cells = re.findall(r'<div class="admin-btn admin-btn--reserved"[^>]*>(.*?)'
                   r'</div>', src, re.S)
ok(len(cells) == 2 and not any(c.strip() for c in cells),
   '  and both are EMPTY - no icon, no label, nothing to read out',
   [c[:40] for c in cells])
ok(src.count('aria-hidden="true"></div>') >= 2,
   '  both are aria-hidden, so a screen reader is not told about a blank')
body = T.code_only(src)
ok('.btn-future-disabled' not in body,
   '.btn-future-disabled is gone from the live stylesheet - the two tiles '
   'were its only users')
# IN THE CODE, NOT THE RECORD OF IT. The note that replaces the rule
# has to say what it removed to be worth reading, and it says the words.
# This round refused itself twice on exactly that before it ever ran.
ok('Coming Soon' not in body,
   '  and the words are gone from what the browser is sent - the note that '
   'explains the cut still says them, and it is allowed to')
ok(body.count('#adb5bd') == 1,
   '  one live #adb5bd left, and it is .btn-perm-disabled - a user without '
   'the right genuinely cannot click that one', body.count('#adb5bd'))
ok('.admin-btn.btn-perm-disabled' in body,
   '  which is still there, untouched')
# The rule itself, not just the class name.
ok(re.search(r'\.admin-btn--reserved\s*\{[^}]*pointer-events:\s*none',
             body, re.S),
   '  and the reserved cell takes pointer-events: none, so it cannot be '
   'clicked even by a script that finds it')
ok(re.search(r'\.admin-btn--reserved\s*\{[^}]*box-shadow:\s*none',
             body, re.S),
   '  and box-shadow: none, so it does not inherit the tile drop shadow '
   'and read as a button somebody has disabled')


# ==========================================================================
head('4b. HELD ON A DESKTOP, GONE ON A PHONE - MEASURED')
# ==========================================================================
# Demetri, after seeing the renders: "On the phone, can we remove the
# blank spaces and have the tab bottom just below the last button?"
#
# A RESERVED CELL EARNS ITS KEEP AT TWO COLUMNS AND NOT AT ONE. At 1280
# the two cells sit BESIDE the live tiles and cost no height at all; at
# 390 the grid is single-column and each becomes a full row of nothing,
# running the panel a quarter of a screen past its last button. Same
# markup, opposite effect, and the difference is the column count.
#
# THIS IS MEASURED, NOT READ. "display: none is in the mobile block" is
# a claim about source; what he asked about is where the panel's bottom
# edge lands, so the probe reads the two bounding boxes and subtracts.
GAP = """() => {
    const pan = document.querySelector('.tab-panel.future-panel');
    const tiles = [...pan.querySelectorAll('.admin-btn')]
        .filter(e => getComputedStyle(e).display !== 'none');
    const res = [...pan.querySelectorAll('.admin-btn--reserved')];
    // The last tile WITH CONTENT. A reserved cell is still a tile, so
    // measuring to the last of them would report a tidy gap while two
    // empty rows sat above it - which is the exact thing he asked to be
    // rid of, reported as a pass.
    const filled = tiles.filter(e => e.textContent.trim());
    const last = filled[filled.length - 1].getBoundingClientRect();
    return {gap: Math.round(pan.getBoundingClientRect().bottom - last.bottom),
            height: Math.round(pan.getBoundingClientRect().height),
            tiles: filled.length,
            reservedShown: res.filter(
                e => getComputedStyle(e).display !== 'none').length,
            pad: Math.round(parseFloat(getComputedStyle(pan).paddingBottom))};
}"""
if sync_playwright is None or not os.path.isfile(BOOT) or not launched:
    skip('section 4b', 'the browser was not available')
else:
    with sync_playwright() as pw2:
        br2 = pw2.chromium.launch(**({'executable_path': EXE}
                                     if os.path.exists(EXE) else {}))
        try:
            def geom(text, w):
                fx = os.path.join(SCRATCH, 'ad1_gap_%d.html' % w)
                with open(fx, 'w', encoding='utf-8') as fh:
                    fh.write(fixture(text))
                ctx = br2.new_context(viewport={'width': w, 'height': 900})
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                _goto(pg, fx)
                try:
                    pg.evaluate(ACTIVATE, 'future')
                    return pg.evaluate(GAP)
                finally:
                    ctx.close()

            ph = geom(src, 390)
            de = geom(src, 1280)
            ok(ph['reservedShown'] == 0,
               'phone    the reserved cells do not render at all',
               ph)
            ok(ph['gap'] <= ph['pad'] + 4,
               'phone    the panel ends %dpx below the last button, and its '
               'own bottom padding is %dpx - so nothing but the padding is '
               'under it' % (ph['gap'], ph['pad']), ph)
            ok(de['reservedShown'] == 2,
               'desktop  and BOTH cells are still there at two columns', de)
            # AND THEY COST A ROW THERE, WHICH IS THE POINT. He asked
            # for the cells to be reserved so the panel keeps its height
            # and growth lands in a space already drawn - that is a row
            # of held space, not no space. The first version of this
            # check claimed they "cost no height either" and the
            # measurement said 193px, which is one tile row. The
            # measurement was right and the sentence was wrong.
            de_bare = geom(src.replace(
                '<div class="admin-btn admin-btn--reserved" '
                'aria-hidden="true"></div>', ''), 1280)
            ok(de['gap'] >= 120,
               'desktop  and they HOLD A ROW - the panel runs %dpx past its '
               'last button, which is the reserved row he asked to keep'
               % de['gap'], de)
            ok(de['height'] - de_bare['height'] >= 120,
               '  CONTROL: take the two cells out and the desktop panel '
               'loses %dpx, one whole row. On the phone that same row is '
               'two, which is why it goes there and stays here'
               % (de['height'] - de_bare['height']),
               (de, de_bare))
            # THE CONTROL. Put the cells back at phone width and the gap
            # grows by a whole row - which is what he was looking at.
            loud = geom(src.replace(
                """    .admin-btn--reserved {
      display: none;
    }""", '    /* control: the cells left in */'), 390)
            ok(loud['gap'] > ph['gap'] + 80
               and loud['height'] > ph['height'] + 80,
               'CONTROL: with the cells left in, the phone panel runs %dpx '
               'past its last BUTTON instead of %dpx, and the panel itself '
               'is %dpx tall instead of %dpx - two empty rows, which is what '
               'he was looking at'
               % (loud['gap'], ph['gap'], loud['height'], ph['height']),
               (ph, loud))
        finally:
            br2.close()


# ==========================================================================
head('5. THE DECISION THIS ROUND OVERTURNED, AND WHOSE IT WAS')
# ==========================================================================
pt = read(os.path.join(ROOT, 'test_personal_teal.py'))
ok("'personal.html': ('--future-dark: #6c757d',)" in pt,
   "test_personal_teal still asserts personal.html keeps the grey - its "
   "FUTURE tab is commented out and this round does not touch that page")
ok("'admin_apms.html': ()" in pt,
   'and the admin_apms half of that claim is spent')
ok('AD-1, 8 OCT 2026' in pt and 'exactly like the Functional Tab' in pt,
   '  with his instruction and the date written in beside it, so the next '
   'reader finds the reason and not just the change')
ok('backed out' in pt,
   '  and the note names B-4, which overturned a decision in silence and '
   'had to be backed out. That is why this one is written down')


# ==========================================================================
head('6. REGISTERED, ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
pc = read(os.path.join(ROOT, 'test_pair_contrast.py'))
# PR-1, 8 Oct 2026: A FLOOR, NOT AN EQUALITY. This read
# `'EXPECT_PAIRS = 714' in pc` - the census's value on the day - and PR-1
# added a tab, which is a pair, so it read 716 and AD-1 went red for a
# change that was none of its business. What AD-1 proved is that the
# census GREW when it learnt to read a page's own :root; 701 is the
# number that cannot come back.
_pairs = int(re.search(r'EXPECT_PAIRS = (\d+)', pc).group(1))
ok(_pairs >= 714,
   'and the pair census went 701 -> 714 and is now %d, because this round '
   'taught it to read a page own :root - every tab rule in the tree is '
   'written in one and not a single one of them was being counted'
   % _pairs)
ok(_pairs > 701,
   '  which is the claim that survives: 701 was what it could see before, '
   'and no later round can take it back there')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that the tab SHOULD be teal. That was his call,')
print('  it overturns a decision another round took on purpose, and the')
print('  only thing that makes it safe is that both the old reason and')
print('  the new one are written down where the next reader will look.')
sys.exit(1 if failed else 0)
