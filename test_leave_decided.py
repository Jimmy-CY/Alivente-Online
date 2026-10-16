# -*- coding: utf-8 -*-
"""test_leave_decided.py - round LV-1, 16 Oct 2026.

LEAVE WAS A SCOPE DECISION BEING USED AS A SILENCER.

Show-ButtonDrift.py carries two registers for a button that sits in no
recognised bar:

    DECIDED   wrapper -> [(label fragment, tone)]   the tool CHECKS these
    LEAVE     wrapper -> reason                     the tool says NOTHING

A LEAVE entry short-circuits EVERY button in its wrapper. Ten entries
covered 41 buttons across the 142 gate pages, and the report had never
once mentioned any of them.

WHAT THIS SUITE PROVES THAT A COMMENT CANNOT
    Section 2 RE-RUNS BOTH CENSUSES - the ten-entry register over the
    backups, the one-entry register over the files - and counts the
    silenced buttons BY WRAPPER, because three LEAVE entries share one
    reason string and counting reasons would answer neither question.
    41 before, 8 after, 33 of them brought into view, 25 of those 33
    wearing a raw Bootstrap colour. Those are the round, measured, not
    the round as planned.

    Section 8 renders the four distinct Bootstrap spellings that went in
    beside the one house class that came out, and asserts the shape of
    the claim rather than any colour: the four USED TO DIFFER from one
    another and now do not differ at all.

NUMBERS, AND WHICH MACHINE MEASURED THEM
    Every assertion here is a RELATION, a count or a computed colour.
    There is no asserted text width anywhere in this file; see the sixth
    failure in claude/standard_delivery_preflight.md for why.

THE BEFORE PICTURE OF A REGISTER IS THE REGISTER
    Section 1 IMPORTS the backup of Show-ButtonDrift.py as a module and
    asks its dictionaries, rather than grepping the text. A register is
    Python, so the right question is a Python one.

WHAT THIS ROUND DOES NOT DECIDE
    Whether the invoice status row should be five solid fills. That is
    the one LEAVE entry left, it holds eight page-defined buttons that
    are already on house tokens, and VC-1 measured them on 14 Oct. It is
    a design question for its own round; this suite only pins that it is
    the ONLY thing still hidden.
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

import importlib.util
import os
import re
import sys

import alv_tree

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by  # noqa: F401
except Exception as e:
    as_left_by = None
    print('  !! alv_rounds could not be imported: %s' % e)

code_only = alv_tree.code_only

SUFFIX = '.bak_leavedecided'
DRIFT = 'Show-ButtonDrift.py'
VOCAB = 'test_vocabulary.py'
ME = 'test_leave_decided.py'
PATCHER = 'apply_leave_decided.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

CONVERTED_NOW, ALIAS_NOW = 90, 91
LEAVE_WAS, LEAVE_NOW = 10, 1
DEAD = ('btn-group', 'subtask-actions', 'project-status-container',
        'passport-filter-header')
MOVED = ('filter-header', 'filter-header-right', 'input-group-append',
         'pdf-viewer-controls', 'zoom-controls')
SURVIVOR = 'status-action-form'
# MEASURED, NOT REMEMBERED. The wrapper census the round was planned
# from, re-run here against the backups. The first draft of the
# patcher's own table wrote 11 against .input-group-append; the
# instrument said 8, and these are the instrument's numbers.
CENSUS_WAS = {'filter-header': 16, 'filter-header-right': 1,
              'input-group-append': 8, 'pdf-viewer-controls': 5,
              'zoom-controls': 3, SURVIVOR: 8}
N_SILENCED_WAS = 41          # every button the ten entries covered
N_GONE = 33                  # the nine entries that leave take these
N_KEPT = 8                   # the survivor keeps these
N_EDITS = 25                 # ... and 25 of the 33 wore a Bootstrap colour
N_HOUSE_ALREADY = 8          # the other 8 wore a house tone, unchecked
N_SAVES = 3
N_FILES = 17
PHONES = (320, 360, 390, 414)
PHONE_FLOOR = 44   # what base declares; section 8 reads it back

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
            for line in str(detail).split('\n')[:6]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def css_of(t):
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style\s*>', t, re.S))


def load(name, source, path):
    """Import a module from SOURCE rather than from disk.

    The before picture of a REGISTER is the register itself, and the
    register is Python. Reading the backup as text and grepping it would
    be a worse question than importing it and asking.
    """
    spec = importlib.util.spec_from_loader(name, loader=None)
    mod = importlib.util.module_from_spec(spec)
    mod.__file__ = path
    exec(compile(source, path, 'exec'), mod.__dict__)
    return mod


D_PATH = os.path.join(ROOT, DRIFT)
D_NOW = read(D_PATH)
APPLIED = os.path.isfile(D_PATH + SUFFIX)
D_WAS = read(D_PATH + SUFFIX) if APPLIED else D_NOW
SB = load('sb_lv_now', D_NOW, D_PATH)
SB_WAS = load('sb_lv_was', D_WAS, D_PATH)
BASE = read(alv_tree.path_of('base.html'))
C_BASE = css_of(code_only(BASE))

print('')
print('test_leave_decided.py - round LV-1, 16 Oct 2026')
print('  register : %s   LEAVE and DECIDED' % DRIFT)
print('  state    : %s' % ('APPLIED - the backup holds the ten-entry '
                           'register' if APPLIED
                           else 'NOT APPLIED - before and after are the '
                                'same text, and the CONTROLs will say so'))


def was_text(rel):
    """A gate page as LV-1 found it."""
    p = SB.resolve(rel)
    b = p + SUFFIX
    return read(b if os.path.isfile(b) else p)


def silenced(mod, before):
    """Every button a LEAVE entry hides, counted BY WRAPPER.

    A hit's reason can come from LEAVE or from skip_reason, and three
    LEAVE entries share one reason STRING - so counting reasons answers
    neither question. The wrapper is what a LEAVE entry is keyed on, so
    the wrapper is what gets counted.
    """
    reasons = set(mod.LEAVE.values())
    per = {}
    for rel in mod.templates(True):
        t = was_text(rel) if before else read(mod.resolve(rel))
        mk = mod.markup_of(t)
        for h in mod.scan_text(rel, t):
            if h[7] in reasons:
                w = mod.innermost_wrapper(mk, h[5])
                n = w[0] if w else '(none)'
                per.setdefault(n, [0, 0])
                per[n][0] += 1
                if h[2]:
                    per[n][1] += 1
    return per


# ==========================================================================
head('1. TEN REGISTER ENTRIES BECAME ONE')
# ==========================================================================
# Show-ButtonDrift carries two registers for a button that sits in no
# bar: DECIDED, which the tool CHECKS, and LEAVE, about which it says
# nothing at all. A LEAVE entry short-circuits EVERY button in its
# wrapper, which is how it came to be used as a silencer.
ok(len(SB_WAS.LEAVE) == LEAVE_WAS,
   'CONTROL: LEAVE held %d entries' % LEAVE_WAS, len(SB_WAS.LEAVE))
ok(len(SB.LEAVE) == LEAVE_NOW,
   'and holds %d now' % LEAVE_NOW, sorted(SB.LEAVE))
ok(list(SB.LEAVE) == [SURVIVOR],
   'the one left is %s - eight page-defined buttons already on house '
   'tokens, which VC-1 measured on 14 Oct' % SURVIVOR, list(SB.LEAVE))

for n in DEAD:
    ok(n not in SB.LEAVE and n not in SB.DECIDED,
       '  %-26s DELETED from both registers' % n)
    ok(not APPLIED or n in SB_WAS.LEAVE,
       '    CONTROL: and was on LEAVE')
for n in MOVED:
    ok(n in SB.DECIDED and n not in SB.LEAVE,
       '  %-26s MOVED to DECIDED, where the tool checks it' % n)
    ok(not APPLIED or n in SB_WAS.LEAVE,
       '    CONTROL: and was on LEAVE')
    ok(not APPLIED or n not in SB_WAS.DECIDED,
       '    CONTROL: and was not on DECIDED')

# D3 MADE THIS JOURNEY FIRST, and said why in the file.
# D3's note wraps across two lines, so the question is asked of the
# words rather than of the line - a claim that depends on where a comment
# happened to break is a claim about formatting.
_d3 = ' '.join(D_NOW.replace('#', ' ').split())
ok('Moved here so the tool CHECKS them rather than staying silent' in _d3,
   'D3 moved three entries the same way on 23 Sep, and its reason is '
   'still in the file - this round finishes that work rather than '
   'inventing a third register')
ok('moved there so the tool CHECKS them' in _d3,
   '  and LV-1 gives the same reason for its five, in the same words')

# THE SAVE IS NAMED BEFORE THE BLANKET. A bare ('*', secondary) on
# .input-group-append would demote three deliberate Save buttons.
#
# ASKED WITH .get, NOT WITH A SUBSCRIPT. Run against a tree this round
# has been backed out of, the first cut of these three lines raised
# KeyError and took the remaining seven sections with it - and a suite
# that CRASHES cannot tell anybody whether a round is half-applied. See
# the FOURTH failure in claude/standard_delivery_preflight.md: a crash
# is not a result.
iga = SB.DECIDED.get('input-group-append')
ok(bool(iga),
   'input-group-append is on DECIDED at all', sorted(SB.DECIDED))
ok(bool(iga) and iga[0][0] == 'save',
   'input-group-append names `save` FIRST, so first-match-wins keeps the '
   'three property_assets Saves primary', iga)
ok(bool(iga) and iga[-1][0] == '*',
   '  and the blanket is LAST, where it catches everything else', iga)
ok(all(SB.DECIDED.get(n) and SB.DECIDED[n][-1][0] == '*' for n in MOVED),
   'each of the five ends in a blanket, so no button in them is '
   'unclassified any more',
   [n for n in MOVED if not SB.DECIDED.get(n)])


# ==========================================================================
head('2. IT WAS A SILENCER, AND THIS IS THE NUMBER')
# ==========================================================================
# THE INSTRUMENT IS ASKED, NOT THE PLAN. These two censuses are the
# round's whole justification, re-run from the backups every time this
# suite runs.
if not APPLIED:
    skip('the two censuses', 'not applied - they would be the same walk')
else:
    was = silenced(SB_WAS, True)
    now = silenced(SB, False)
    t_was = sum(v[0] for v in was.values())
    t_now = sum(v[0] for v in now.values())
    b_was = sum(v[1] for v in was.values())
    ok(t_was == N_SILENCED_WAS,
       'CONTROL: the ten entries silenced %d buttons across the gate '
       'pages' % N_SILENCED_WAS, (t_was, was))
    for n in sorted(CENSUS_WAS):
        ok(was.get(n, [0])[0] == CENSUS_WAS[n],
           '  %-26s %3d' % (n, CENSUS_WAS[n]), was.get(n))
    ok(t_now == N_KEPT,
       'and %d are silenced now - every one of them in %s'
       % (N_KEPT, SURVIVOR), (t_now, now))
    ok(list(now) == [SURVIVOR],
       '  nothing else on 142 pages is hidden from the report',
       list(now))
    ok(t_was - t_now == N_GONE,
       'so %d buttons came into view, which is what this round is'
       % N_GONE, t_was - t_now)
    ok(b_was == N_EDITS,
       'and %d of them wore a RAW BOOTSTRAP COLOUR the report had never '
       'once mentioned' % N_EDITS, b_was)
    ok(N_GONE - N_EDITS == N_HOUSE_ALREADY,
       'the other %d already wore a house tone and were simply never '
       'checked - three of them action-primary Saves'
       % N_HOUSE_ALREADY)
    ok(now.get(SURVIVOR, [0, 0])[1] == 0,
       'and the survivor hides no Bootstrap colour at all, which is why '
       'it is allowed to stay', now.get(SURVIVOR))


# ==========================================================================
head('3. TWENTY-FIVE BUTTONS, AND THE PAGE KEPT ITS OWN CLASS')
# ==========================================================================
# The edits were PLANNED BY THE TOOL from scan_text offsets, not typed.
# What that produced is asked here of the files.
pages = sorted(set(
    p for p in (SB.resolve(r) for r in SB.templates(True))
    if os.path.isfile(p + SUFFIX)))
ok(len(pages) == N_FILES,
   '%d template(s) carry a backup from this round' % N_FILES, len(pages))

BOOTWORDS = ('btn-secondary', 'btn-outline-secondary', 'btn-light',
             'btn-outline-primary', 'btn-primary', 'btn-danger',
             'btn-success', 'btn-info', 'btn-warning')
n_edits = n_kept_local = 0
still = []
for p in pages:
    a, b = code_only(read(p)), code_only(read(p + SUFFIX))

    def classes(t):
        return [m.group(1) for m in
                re.finditer(r'<(?:button|a)\b[^>]*class="([^"]*)"', t)]
    ca, cb = classes(a), classes(b)
    if len(ca) != len(cb):
        still.append('%s: the button COUNT moved, %d -> %d'
                     % (os.path.relpath(p, ROOT), len(cb), len(ca)))
        continue
    for x, y in zip(cb, ca):
        if x == y:
            continue
        n_edits += 1
        if 'action-secondary' not in y.split():
            still.append('%s: %r -> %r is not a secondary'
                         % (os.path.relpath(p, ROOT), x, y))
        if any(w in y.split() for w in BOOTWORDS):
            still.append('%s: %r still carries a Bootstrap colour'
                         % (os.path.relpath(p, ROOT), y))
        # EVERY CLASS THAT IS NOT THE COLOUR SURVIVES. pdf-control-btn
        # and pi-clear-all are the page's own geometry; a retone that
        # dropped them would move the buttons as well as recolour them.
        local = [c for c in x.split()
                 if c not in BOOTWORDS and c not in ('btn', 'btn-sm')]
        if local:
            if all(c in y.split() for c in local):
                n_kept_local += 1
            else:
                still.append('%s: %r lost %s'
                             % (os.path.relpath(p, ROOT), x, local))

ok(not still, 'every retone is a COLOUR SWAP and nothing else', still)
ok(n_edits == N_EDITS or not APPLIED,
   '%d button(s) changed class, which is the number the patcher planned'
   % N_EDITS, n_edits)
ok(n_kept_local >= 6 or not APPLIED,
   'and the %d that carried a page class of their own kept it - '
   'pdf-control-btn and pi-clear-all are geometry, not colour'
   % n_kept_local, n_kept_local)
ok(re.search(r'\.btn\.action-secondary\s*\{', C_BASE) is not None,
   'base owns .btn.action-secondary, so the 25 take their colour from '
   'one rule rather than 25 class attributes')


# ==========================================================================
head('4. THE THREE SAVES KEEP action-primary')
# ==========================================================================
assets = alv_tree.path_of('property_assets.html')
A_NOW = code_only(read(assets))
saves = [m.group(1) for m in
         re.finditer(r'<button\b[^>]*class="([^"]*)"[^>]*>(?:(?!</button).)*'
                     r'Save', A_NOW, re.S)
         if 'action-primary' in m.group(1)]
ok(len(saves) >= N_SAVES,
   'property_assets still draws %d action-primary Save button(s)'
   % len(saves), saves)
ok(not any('action-secondary' in c for c in saves),
   'and not one of them was demoted by the blanket', saves)
# AND THE PATCHER REFUSES IF THAT EVER CHANGES, which is a claim about
# the patcher and is read from the patcher - WHEN IT IS THERE. Step 4
# of the pre-flight moves a round's new files aside before re-running
# its suite, so during that run this file is not on disk, and reading
# it outright ended the run four sections early. A missing file is an
# answer; a traceback is not.
_patp = os.path.join(ROOT, PATCHER)
pat = read(_patp) if os.path.isfile(_patp) else ''
ok(bool(pat), '%s is on disk to be asked' % PATCHER)
ok('is not naming Save first' in pat,
   'the patcher refuses outright if its own plan would retone a Save - '
   'a gate that refuses rather than doing half')


# ==========================================================================
head('5. THE TOOL NOW REPORTS ON WHAT IT USED TO HIDE')
# ==========================================================================
drifting = []
undecided = []
for rel in SB.templates(True):
    t = read(SB.resolve(rel))
    for h in SB.scan_text(rel, t):
        if h[7]:
            continue
        if SB.drifting(h):
            drifting.append('%s: %r' % (rel, h[3]))
        if h[0] == 'UNCLASSIFIED':
            undecided.append('%s: %r' % (rel, h[3]))
ok(not drifting,
   'nothing on the %d gate pages is drifting' % len(SB.templates(True)),
   drifting[:6])
ok(not undecided,
   'and nothing is undecided - a register entry that hides a button is '
   'not the same as a decision about it', undecided[:6])


# ==========================================================================
head('6. THE PIN GOES TO ZERO, AND KEEPS ITS CONTROL')
# ==========================================================================
v = read(os.path.join(ROOT, VOCAB))
ok('N_SILENCED, N_SILENCED_ENTRIES = 0, 0' in v,
   '%s pins the silenced count at ZERO, where it pinned 8' % VOCAB)
ok('(was 8, 2)' in v,
   '  and says what it pinned before, in the house shape')
ok('share-grid' in v,
   'and it KEEPS the share-grid control that explains why the pin exists '
   '- VC-1 nearly registered that wrapper and silenced the previous '
   "day's own fix")
ok('THE PIN IS ZERO NOW' in v,
   'the census note says the pin is zero rather than leaving the reader '
   'to infer it from a number')


# ==========================================================================
head('7. REGISTERED, ON THE GATE')
# ==========================================================================
ok(ME in alv_tree.CONVERTED,
   '%s is in alv_tree.CONVERTED' % ME)
try:
    import alv_rounds
    ok(SUFFIX in alv_rounds.ROUNDS,
       '%s is in alv_rounds.ROUNDS' % SUFFIX)
    # ASKED WITH `in`, NOT WITH .index. Run on a tree this round has
    # been backed out of, .index raised ValueError inside this try and
    # the handler reported `alv_rounds is importable` as FAILED - which
    # it plainly was, since the line above it had just read it. A
    # handler that catches the wrong thing says the wrong thing.
    _r = alv_rounds.ROUNDS
    ok(SUFFIX in _r and '.bak_deedonecol' in _r
       and _r.index(SUFFIX) > _r.index('.bak_deedonecol'),
       '  and sits AFTER .bak_deedonecol - the two rounds ship in one '
       'push and LV-1 bumps the shared counters on top of TD-2',
       _r[-3:])
except Exception as e:
    ok(False, 'alv_rounds is importable', e)

ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1,
   '%s runs this suite' % PS1)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)
# DT-1, 16 Oct 2026 - AS THIS ROUND LEFT THEM, NOT AS THEY STAND.
# These three read the live files until DT-1 bumped both an hour later
# and every one of them failed. A shared counter is read through
# as_left_by, which walks ROUNDS forward and hands back the next round's
# backup - the text LV-1 actually wrote. TD-2's suite was written this
# way; this one was not, and that is the whole difference.


def as_lv_left(name):
    p = os.path.join(ROOT, name)
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


wd = as_lv_left('test_waiting_down.py')
ok('CONVERTED_N = %d' % CONVERTED_NOW in wd,
   'test_waiting_down counted %d converted suites when LV-1 left it'
   % CONVERTED_NOW)
co = as_lv_left('test_code_only.py')
ok('ok(len(aliased) == %d,' % ALIAS_NOW in co,
   'test_code_only counted %d files aliasing code_only' % ALIAS_NOW)
ok('45 patchers and 46 suites' in co,
   '  split 45 patchers and 46 suites - TD-2 made it 44 and 45, and this '
   'round was one of each on top')


# ==========================================================================
head('8. RENDERED BEFORE AND AFTER - FOUR BOOTSTRAP TONES BECOME ONE')
# ==========================================================================
# THE CLAIM IS A RELATION. Four distinct Bootstrap spellings went in and
# one house class came out, so the test is that the four USED TO DIFFER
# from one another and now do not differ at all. There is no asserted
# text width anywhere in this file; see the sixth failure in
# claude/standard_delivery_preflight.md for why that rule exists.
try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False

SPELLINGS = (('outline-secondary', 'btn btn-outline-secondary btn-sm'),
             ('secondary', 'btn btn-secondary btn-sm'),
             ('light', 'btn btn-sm btn-light pdf-control-btn'),
             ('outline-primary', 'btn btn-sm btn-outline-primary'))
AFTER = 'btn action-secondary btn-sm'

LOOK = """() => {
  const g = e => getComputedStyle(e);
  const out = {};
  for (const e of document.querySelectorAll('button')) {
    const r = e.getBoundingClientRect();
    out[e.id] = {bg: g(e).backgroundColor, ink: g(e).color,
                 border: g(e).borderTopColor,
                 w: Math.round(r.width), h: Math.round(r.height)};
  }
  return out;
}"""

if not have_pw or not os.path.isfile(BOOT):
    skip('the four tones in a browser',
         'playwright or the fixture is absent')
else:
    from playwright.sync_api import sync_playwright

    def markup(before):
        rows = []
        for n, (name, cls) in enumerate(SPELLINGS):
            rows.append('<button id="b%d" class="%s">Clear All</button>'
                        % (n, cls if before else AFTER))
        return ('<div class="filter-header">%s</div>'
                % ''.join(rows))

    def fixture(name, body):
        p = os.path.join(SCRATCH, name)
        with open(p, 'w', encoding='utf-8') as fh:
            # Transitions off: the claim is the value a rule ARRIVES at.
            fh.write('<!doctype html><html><head><meta charset="utf-8">'
                     '<meta name="viewport" content="width=device-width,'
                     'initial-scale=1"><style>%s</style><style>%s</style>'
                     '<style>body{margin:0;background:#fff}'
                     '*{transition:none !important}</style></head>'
                     '<body>%s</body></html>'
                     % (read(BOOT), C_BASE, body))
        return p

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        try:
            f_was = fixture('lv_was.html', markup(True))
            f_now = fixture('lv_now.html', markup(False))
            seen = {}
            for w in PHONES + (1280,):
                for lbl, f in (('was', f_was), ('now', f_now)):
                    ctx = br.new_context(viewport={'width': w,
                                                   'height': 900})
                    ctx.route(re.compile(r'^https?://'),
                              lambda r: r.abort())
                    pg = ctx.new_page()
                    _goto(pg, f)
                    pg.wait_for_timeout(50)
                    seen[(lbl, w)] = pg.evaluate(LOOK)
                    ctx.close()

            a, b = seen[('now', 1280)], seen[('was', 1280)]
            tone = lambda d: (d['bg'], d['ink'], d['border'])
            was_tones = {tone(b['b%d' % n]) for n in range(len(SPELLINGS))}
            now_tones = {tone(a['b%d' % n]) for n in range(len(SPELLINGS))}
            ok(len(was_tones) == len(SPELLINGS),
               '1280px  CONTROL: the four Bootstrap spellings drew %d '
               'DIFFERENT tones' % len(was_tones), sorted(was_tones))
            ok(len(now_tones) == 1,
               '1280px  and they draw ONE tone now: bg %s, ink %s, border '
               '%s' % next(iter(now_tones)), sorted(now_tones))
            for n, (name, _cls) in enumerate(SPELLINGS):
                ok(tone(a['b%d' % n]) != tone(b['b%d' % n]),
                   '1280px    %-18s moved' % name,
                   (tone(b['b%d' % n]), tone(a['b%d' % n])))
            # A SECONDARY IS PAPER WITH A LINE, which is what base says.
            paper = re.search(r'--alv-paper:\s*([^;]+);', C_BASE)
            ok(paper is not None,
               '1280px  base declares --alv-paper, which is the ground a '
               'secondary stands on')
            ok(a['b0']['bg'] == 'rgb(255, 255, 255)',
               '1280px  and the retoned button stands on it: %s'
               % a['b0']['bg'])

            # ON A DESKTOP ONLY THE COLOUR MOVED. Asserted as a
            # one-pixel band: a half-pixel read as a misalignment once
            # already - see test_bar_height section 3.
            for n, (name, _cls) in enumerate(SPELLINGS):
                k = 'b%d' % n
                ok(abs(a[k]['h'] - b[k]['h']) <= 1,
                   '1280px    %-18s is the same height, within a pixel '
                   '(%d -> %d)' % (name, b[k]['h'], a[k]['h']))

            # ON A PHONE THE ROUND GAVE AWAY MORE THAN A COLOUR, and
            # this was NOT the intention - the first cut of this suite
            # asserted the height was unmoved at every width and failed
            # at all four phone sizes. base's phone block gives
            # `.btn.action-secondary` a min-height of 44px, and
            # Bootstrap's btn-sm had these 25 at 31. A control a LEAVE
            # entry was hiding was also a control three pixels short of
            # a thumb, on every phone, and nothing in this project could
            # have reported that while the entry was there.
            # THE FLOOR IS READ FROM base, NOT TYPED. 44 is a number
            # base declares; a suite that writes it out is a suite that
            # keeps agreeing with itself after base stops saying it.
            _floor = re.search(r'\.btn\.action-secondary,[^{]*\{[^}]*'
                               r'min-height:\s*(\d+)px', C_BASE, re.S)
            ok(_floor is not None,
               'base declares a phone minimum for a secondary, and that '
               'is where the next claim comes from')
            FLOOR = int(_floor.group(1)) if _floor else 44
            ok(FLOOR == PHONE_FLOOR,
               '  it is %dpx, which is the house floor' % FLOOR)
            for w in PHONES:
                a, b = seen[('now', w)], seen[('was', w)]
                for n, (name, _cls) in enumerate(SPELLINGS):
                    k = 'b%d' % n
                    ok(b[k]['h'] < a[k]['h'],
                       '%4dpx    CONTROL: %-18s was SHORTER before '
                       '(%d -> %d)' % (w, name, b[k]['h'], a[k]['h']))
                    ok(a[k]['h'] >= FLOOR,
                       '%4dpx      and now meets the %dpx base declares'
                       % (w, FLOOR))
                ok(len({a['b%d' % n]['h']
                        for n in range(len(SPELLINGS))}) == 1,
                   '%4dpx    and all four are the SAME height as each '
                   'other' % w,
                   [a['b%d' % n]['h'] for n in range(len(SPELLINGS))])
        finally:
            br.close()


# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
if failed:
    print('')
    print('  WHAT THIS ROUND IS, in one line:')
    print('  LEAVE stops being a silencer. Ten register entries become')
    print('  one - four were dead, five were decisions nobody had written')
    print('  down - and the 25 Bootstrap-coloured buttons they were')
    print('  hiding take the tone their own siblings already wear. The')
    print('  three property_assets Saves keep action-primary, because')
    print('  DECIDED names Save before the blanket.')
sys.exit(1 if failed else 0)
