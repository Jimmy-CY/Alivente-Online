# -*- coding: utf-8 -*-
"""test_js_buttons.py - round E11, 13 Oct 2026.

A GATE THAT SAYS "NOTHING IS LEFT" MUST BE ASKED OF EVERYTHING.

E11 is five script-built buttons and the corpus of the census that was
supposed to find them.

THE FIVE
    map_ingredients_nutrition.html   Reload Queue x2   btn-info  -> action-primary
    map_ingredients_nutrition.html   Back to Ingredients btn-secondary -> action-secondary
    unit_conversions_wizard.html     Back to Ingredients btn-info  -> action-secondary
    unit_conversions_management.html Save, per row     btn-primary -> action-primary

THE CORPUS
    test_button_sweep section 10 says "nothing is left" over
    sb.templates(False) - 117 of the application's 142 pages. All five
    sat on the other 25. The census now has its own corpus of 142 and a
    CONTROL that says so, because the widening is one identifier and an
    identifier is easy to put back.

WHAT IS ASKED LIVE AND WHAT IS ASKED OF A BACKUP
    The five conversions are a SNAPSHOT of this round, so the before is
    .bak_jsbtn and the after is the file. The counters in other suites
    are snapshots too, so they are read through as_left_by - fifth
    round running. The register totals, the scanner's behaviour and the
    contrast numbers are INVARIANTS and are read live, because an
    invariant read off a backup stops being a control.

WHAT IS NOT PROVED HERE
    That action-secondary is the right answer for a Back. It is a
    decision, taken 13 Oct against the measurement: action-back reads
    5.53 and the chosen tone reads less, and it was chosen anyway
    because map_ingredients_nutrition's own scoped branch already writes
    it two lines away and because unit_conversions_wizard's Back is the
    only control on its card. The suite checks the decision was carried
    out, not that it was right.
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

import alv_tree

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

code_only = alv_tree.code_only
python_code_only = alv_tree.python_code_only

SUFFIX = '.bak_jsbtn'
ME = 'test_js_buttons.py'
PATCHER = 'apply_js_buttons.py'
DRIFT = 'Show-ButtonDrift.py'
SWEEP = 'test_button_sweep.py'
PS1 = 'Push-PendingChanges.ps1'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

# NO NARROW TEMPLATE ROOT. X0's rule, and the first draft of this file
# broke it fourteen times: a label goes back to a file through
# alv_tree.last_path(), which knows both roots, not through a join onto a
# pages/templates constant that knows one. test_waiting_down section 3
# counts those joins across everything on CONVERTED and caught all
# fourteen - inside the round whose whole point is that a gate has to be
# asked of everything. Recorded rather than quietly repaired.
MAP = 'map_ingredients_nutrition.html'
WIZ = 'unit_conversions_wizard.html'
MGT = 'unit_conversions_management.html'

N_BUTTONS, N_PAGES = 5, 3
# RT-1, 18 Oct 2026 - the application is 139 pages. Four meal-plan screens
# were retired and the planner replaced them: 142 - 4 + 1. The SWEEP
# SCOPE does not move - 117 was and is the narrow half, and the pages
# the flag hides are still the recipe and meal-plan side.
CENSUS_NARROW, CENSUS_WIDE = 126, 151   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 125, 150)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins both halves.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join both halves - but they contribute ZERO scanner hits, measured: their controls wear .ls-btn, a class of their own, because the pages cannot extend base and so cannot use the house one.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. BOTH halves move: unlike meal_plan_print this is an ordinary pages/templates page, so it joins the sweep scope as well as the application count.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. The narrow half does not move: the sweep scope is the 117 pages it has always been.   # (WIDE was 141)   # RD-1, 19 Oct 2026 - the
# quick-look pair. (wide was 139, and 142 before MN-1 retired four
# meal-plan screens.)
HITS_LOOSE, HITS_TIGHT = 694, 692   # ES-7, 25 Oct 2026 - three more house .btn controls on the Signature and Stamp screen, measured by this census. Both matchers rise by the same three.   # (was 691, 689)   # ES-6, 25 Oct 2026 - the envelope page's bar: Approve and attach, Decline, View signed lease and Back. Both matchers rise by the same four.   # (was 687, 685)   # ES-3b, 24 Oct 2026 - Create and sign, Back, and Choose a different tenant. Both matchers rise by the same three. MEASURED PER ROUND rather than split by eye: ES-4 ships four templates in the same bundle and its share is zero, because its buttons are not house .btn ones.   # (was 684, 682)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 680, 678)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. Both matchers rise by the same three.   # (was 677, 675)   # PP-1, 20 Oct 2026 - the printable plan's two bar controls, Print and Back. Both matchers rise by the same two.   # (was 675, 673)   # RD-1, 19 Oct 2026 - one scanner
# hit per new template, and BOTH matchers rise by the same two.
# (was 673, 671)   # RT-1, 18 Oct 2026 - thirty-three scanner hits went with the four retired screens, and both matchers fall by the same thirty-three.   # (was 706, 704)
TAIL_MARKUP, TAIL_SCRIPT, TAIL_IN_REGION = 433, 36, 2
NESTED_LABELS = 8
MGT_MARKUP_BOOT = 4
CONVERTED_NOW, WAITING_NOW, CEILING_NOW, ALIAS_NOW = 72, 2, 38, 55

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


def was(p):
    """The file as E11 found it. Scoped: most files have no backup of
    this round and never needed one."""
    b = alv_tree.bak_path(p, SUFFIX)
    return read(b) if os.path.isfile(b) else read(p)


def left_page(rel):
    """A TEMPLATE as E11 left it. left() above is for repo-root files;
    a page needs alv_tree.path_of first, and RS-1a is the round that
    found out this suite needed it at all."""
    p = alv_tree.last_path(rel)
    if as_left_by is None:
        return read(p)
    return as_left_by(p, SUFFIX, read)


def left(name):
    """Another suite's file AS E11 LEFT IT. Fifth round running: a
    snapshot claim about a counter has to read the counter through the
    round list, or the next round moving it makes this suite report that
    E11 did something it did not."""
    p = os.path.join(ROOT, name)
    if as_left_by is None:
        return read(p)
    return as_left_by(p, SUFFIX, read)


def srgb(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def lum_rgb(r, g, b):
    return 0.2126 * srgb(r) + 0.7152 * srgb(g) + 0.0722 * srgb(b)


def cr_css(a, b):
    """Contrast between two computed `rgb(r, g, b)` strings."""
    pa = [int(x) for x in re.findall(r'\d+', a)[:3]]
    pb = [int(x) for x in re.findall(r'\d+', b)[:3]]
    la, lb = lum_rgb(*pa), lum_rgb(*pb)
    hi, lo = max(la, lb), min(la, lb)
    return round((hi + 0.05) / (lo + 0.05), 2)


# The five, as code rather than as prose, so a check cannot drift from
# what the round did.
FIVE = (
    (MAP, 'class="btn btn-info"><i class="fas fa-redo"></i> Reload Queue</a>',
     'class="btn action-primary"><i class="fas fa-redo"></i> '
     'Reload Queue</a>'),
    (MAP, '<a href="?" class="btn btn-info" style="margin-right:10px;">',
     '<a href="?" class="btn action-primary" style="margin-right:10px;">'),
    (MAP, '<a href="{% url \'ingredient_base_units_management\' %}" '
          'class="btn btn-secondary">',
     '<a href="{% url \'ingredient_base_units_management\' %}" '
     'class="btn action-secondary">'),
    (WIZ, '<a href="{% url \'ingredient_base_units_management\' %}" '
          'class="btn btn-info">',
     '<a href="{% url \'ingredient_base_units_management\' %}" '
     'class="btn action-primary">'),
    (MGT, '<button type="button" class="btn btn-sm btn-primary w-100" '
          'onclick="saveSingleMissingConversion(${index})" '
          'style="height: 38px;">',
     '<button type="button" class="btn btn-sm action-primary w-100" '
     'onclick="saveSingleMissingConversion(${index})">'),
)

SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script>', re.S | re.I)

print('=' * 74)
print('%s - E11, A GATE MUST BE ASKED OF EVERYTHING' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE FIVE - BEFORE FROM THE BACKUP, AFTER FROM THE FILE')
# ==========================================================================
done, pages = 0, set()
for pg, old, new in FIVE:
    p = alv_tree.last_path(pg)
    b, a = was(p), read(p)
    hit = (b.count(old) == 1 and a.count(old) == 0
           and b.count(new) == 0 and a.count(new) == 1)
    ok(hit, '%-32s %s' % (pg[:32], new[-46:]),
       'before %d/%d  after %d/%d'
       % (b.count(old), b.count(new), a.count(old), a.count(new)))
    if hit:
        done += 1
        pages.add(pg)

ok(done == N_BUTTONS and len(pages) == N_PAGES,
   '%d button(s) on %d page(s), every one of them' % (N_BUTTONS, N_PAGES),
   '%d on %d' % (done, len(pages)))

# THE INLINE HEIGHT. The class change fixes the colour; this is what
# fixes the tap target, and they are two different edits to one tag.
mb, ma = was(alv_tree.last_path(MGT)), read(alv_tree.last_path(MGT))
ok(mb.count('style="height: 38px;"') == 1
   and ma.count('style="height: 38px;"') == 0,
   'the per-row Save loses its inline height - base can reach 44px now',
   '%d -> %d' % (mb.count('style="height: 38px;"'),
                 ma.count('style="height: 38px;"')))

# AND THE FOUR IN THAT PAGE'S MARKUP ARE STILL THERE. "I only touched
# the script ones" is a claim until something checks it. These four are
# the recipe-side sweep's, not E11's.
# REPAIRED BY RS-1a, 13 Oct 2026. THIS WAS READ LIVE AND IT IS A
# SNAPSHOT. The claim is "E11 did not touch this page's markup", which
# is a fact about the day E11 ran - and RS-1a then converted all four of
# those buttons, because they were four of its thirty-five. Read live,
# E11's own suite reported that E11 had done something it did not.
#
# Sixth time this distinction has bitten in this project, and the first
# where the round that made the mistake had the rule written in its own
# docstring. It did not fail E11's sweep because nothing had moved yet;
# it failed the moment the next round landed, which is the sweep working
# and the round not.
ml = left_page(MGT)
n_markup = (ml.count('class="btn btn-secondary"')
            + ml.count('class="btn btn-primary"'))
ok(n_markup == MGT_MARKUP_BOOT,
   '%s kept its %d Bootstrap-toned button(s) IN MARKUP - read as E11 '
   'left it; RS-1a took them later' % (MGT[:28], MGT_MARKUP_BOOT),
   '%d found' % n_markup)
ok(mb.count('class="btn btn-secondary"') == ml.count(
       'class="btn btn-secondary"')
   and mb.count('class="btn btn-primary"') == ml.count(
       'class="btn btn-primary"'),
   '  and E11 moved none of them')

# CONTROL: the scripts are still scripts. A round that deleted the block
# would pass every count above.
for pg in (MAP, WIZ, MGT):
    a = read(alv_tree.last_path(pg))
    n = sum(1 for _ in SCRIPT.finditer(a))
    ok(n == sum(1 for _ in SCRIPT.finditer(was(alv_tree.last_path(pg))))
       and n > 0,
       'CONTROL: %-32s still carries its %d script block(s)' % (pg[:32], n))

# ==========================================================================
head('2. THE CENSUS - ASKED OF THE SCANNER, OVER THE WHOLE APPLICATION')
# ==========================================================================
sys.path.insert(0, ROOT)
import importlib.util                                           # noqa: E402

_spec = importlib.util.spec_from_file_location(
    '_sb_e11', os.path.join(ROOT, DRIFT))
sb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sb)

wide, narrow = sb.templates(True), sb.templates(False)
ok(len(wide) == CENSUS_WIDE and len(narrow) == CENSUS_NARROW,
   'the application is %d page(s); the sweep scope is %d'
   % (CENSUS_WIDE, CENSUS_NARROW), '%d and %d' % (len(wide), len(narrow)))
ok(len([f for f in wide if sb.is_recipe_side(f)]) == CENSUS_WIDE
   - CENSUS_NARROW,
   '  and the %d the flag used to hide are the recipe/meal-plan side'
   % (CENSUS_WIDE - CENSUS_NARROW))

# CONTROL: widening the CENSUS did not widen the ROOT. test_drift_root
# already asserts this of templates(True); E11 now depends on it, so it
# is asserted here too rather than assumed from over there.
ok(not [f for f in wide if f.startswith('crs/')],
   'CONTROL: the wide census is still pages/templates - no crs/ page in it',
   '%d listed' % len([f for f in wide if f.startswith('crs/')]))


def census(text_of):
    hits = {}
    for f in wide:
        h = sb.js_buttons(text_of(alv_tree.last_path(f)))
        if h:
            hits[f] = h
    return hits


after = census(read)
ok(not after,
   'NOTHING is left: 0 Bootstrap-toned script button(s) across all %d '
   'page(s)' % CENSUS_WIDE,
   '; '.join('%s %d' % (k, len(v)) for k, v in list(after.items())[:4]))

# THE FORWARD HALF. A guard that only ever loosens asserts nothing: say
# what was there, read from the backups, so this cannot be satisfied by
# the scanner going blind.
before = census(was)
ok(sum(len(v) for v in before.values()) == N_BUTTONS
   and len(before) == N_PAGES,
   '  and there were %d in %d page(s) before, read from the backups'
   % (N_BUTTONS, N_PAGES),
   '%d in %d' % (sum(len(v) for v in before.values()), len(before)))

# CONTROL: the scanner would still see one on the day no page has any.
ok([h[0] for h in sb.js_buttons(
       '<script>var h = `<div class="page-action-bar">'
       '<button class="btn btn-info">Go</button></div>`;</script>')]
   == ['Go'],
   'CONTROL: .. and it still finds a planted one, so it has not gone blind')

# CONTROL: the narrow corpus is what USED to answer, and it answered 0.
# This is the whole finding in one line.
ok(not [f for f in narrow if sb.js_buttons(
            was(alv_tree.last_path(f)))],
   'CONTROL: over the OLD %d-page corpus the answer was 0 before the '
   'round too - the corpus was the fault, not the scanner' % CENSUS_NARROW)

# ==========================================================================
head('3. THE REGEX - THE TOKEN btn, NOT THE LETTERS btn')
# ==========================================================================
PAT = re.compile(r'BTN = re\.compile\((.*?), re\.S\)', re.S)


def btn_of(text):
    """The pattern as the FILE spells it, not as this suite retypes it.

    The parentheses matter: the assignment is an implicit concatenation
    across indented continuation lines, and eval() of that without them
    is an IndentationError.
    """
    m = PAT.search(text)
    if not m:
        return None
    return re.compile(eval('(' + m.group(1) + ')', {'re': re}),  # noqa: S307
                      re.S)


# REPAIRED BY VC-1, 14 Oct 2026 - AND IT WAS READ LIVE.
#
# `tight` is E11's pattern, and E11's pattern is a SNAPSHOT. Read live it
# became VC-1's - which put <label> in the tag list - so this section
# priced two rounds in one number: 706 and 704 came back as 1119 and
# 721, and "exactly 2 pages change" came back as 58.
#
# AND THE PATTERN WAS NOT THE WHOLE OF IT, which the first repair here
# got wrong. Swapping only `tight` back still failed, because the
# numbers below are a snapshot of the TOOL and not just of its regex:
# VC-1 also added two LEAVE entries, a POSITION name and a PAINTED row
# where _scan used to drop a button in silence. Every one of those
# changes the LENGTH of what _scan returns.
#
# So the whole comparison is run against Show-ButtonDrift AS E11 LEFT
# IT, loaded beside the live one out of this process's own SCRATCH
# directory, and handed back the repo's ROOT and TPL because a module
# that finds the templates from its own __file__ would look for them
# next to the copy.
#
# NINTH OCCURRENCE OF THE as_left_by LESSON, and the SECOND about the
# INSTRUMENT rather than the pages - RS-1b made the first, for RS-1a,
# the day before.
def _tool_as_e11_left_it():
    q = os.path.join(SCRATCH, 'show_buttondrift_as_e11_left_it.py')
    with open(q, 'w', encoding='utf-8') as fh:
        fh.write(left(DRIFT))
    sp = importlib.util.spec_from_file_location('_sb_e11', q)
    mod = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(mod)
    mod.ROOT, mod.TPL = sb.ROOT, sb.TPL
    return mod


sb_then = _tool_as_e11_left_it()
tight = btn_of(left(DRIFT))
loose = btn_of(was(os.path.join(ROOT, DRIFT)))
if not ok(tight is not None and loose is not None,
          'both BTN patterns read out of the code, not retyped'):
    skip('section 3', 'the BTN assignment could not be located')
else:
    def hits(rx, cls):
        return bool(rx.search('<a class="%s">x</a>' % cls))

    REAL = ('btn', 'btn btn-sm', 'btn action-primary', 'action-primary',
            'btn-sm btn action-danger', 'back-button')
    TAIL = ('icon-action-btn', 'icon-action-btn icon-delete', 'btn-trends',
            'add-new-btn-link', 'recipe-edit-btn', 'conv-preset-btn')
    ok(all(hits(tight, c) for c in REAL),
       'it still matches every real shape (%d of them, .btn and unpaired '
       'house tones)' % len(REAL),
       [c for c in REAL if not hits(tight, c)])
    ok(not any(hits(tight, c) for c in TAIL),
       'and none of the %d page-local component names - head, middle or '
       'tail' % len(TAIL),
       [c for c in TAIL if hits(tight, c)])
    # CONTROL, read from the backup: the OLD pattern matched all six, so
    # this is a repair and not a restatement.
    ok(all(hits(loose, c) for c in TAIL),
       'CONTROL: the pattern E11 replaced matched all %d of them' % len(TAIL),
       [c for c in TAIL if not hits(loose, c)])
    ok(all(hits(loose, c) for c in REAL),
       '  CONTROL: .. and the real shapes too, so nothing real was lost')

    # PRICED, over the whole application, both ways - AND WITH THE TOOL
    # E11 LEFT, not the live one. See the note beside sb_then above: the
    # count is a property of the whole scanner, and VC-1 changed three
    # other things in it.
    def scan_hits(rx):
        keep, n = sb_then.BTN, 0
        sb_then.BTN = rx
        try:
            for f in wide:
                # AND THE PAGES AS E11 LEFT THEM. left_page() is three
                # hundred lines up and this was the one place in the
                # file still reading them live - which is why the count
                # came back 709 and 707 once VC-1 moved three buttons
                # onto .icon-action-btn and off .btn.
                raw = left_page(f)
                sb_then.JS_REENABLED = sb_then.js_reenabled_ids(raw)
                n += len(sb_then._scan(f, sb_then.markup_of(raw)))
        finally:
            sb_then.BTN = keep
        return n

    n_t, n_l = scan_hits(tight), scan_hits(loose)
    ok(n_t == HITS_TIGHT and n_l == HITS_LOOSE,
       'scanner hits over all %d page(s): %d loose, %d tight'
       % (CENSUS_WIDE, HITS_LOOSE, HITS_TIGHT), '%d and %d' % (n_l, n_t))

    # The two that go were ALREADY skipped rows with a reason. A row that
    # was being acted on would be a different round.
    def rows(rx, f):
        keep = sb_then.BTN
        sb_then.BTN = rx
        try:
            raw = left_page(f)
            sb_then.JS_REENABLED = sb_then.js_reenabled_ids(raw)
            return sb_then._scan(f, sb_then.markup_of(raw))
        finally:
            sb_then.BTN = keep

    moved, why_all = [], []
    for f in wide:
        a = [(h[0], h[1], h[3], h[4], h[7]) for h in rows(tight, f)]
        b = [(h[0], h[1], h[3], h[4], h[7]) for h in rows(loose, f)]
        if a != b:
            moved.append(f)
            why_all += [h[4] for h in b if h not in a]
    ok(len(moved) == TAIL_IN_REGION,
       'exactly %d page(s) change at all' % TAIL_IN_REGION,
       '%d: %s' % (len(moved), moved[:4]))
    ok(all(w for w in why_all) and len(why_all) == TAIL_IN_REGION,
       '  and every row that goes was already SKIPPED, with a reason',
       why_all)

    # RECORDED, NOT FIXED. finditer does not overlap, so a control nested
    # inside another control is invisible. Written down as a number so the
    # next person meets it as a known shape rather than a surprise.
    lt = read(alv_tree.last_path('lease_timeline.html'))
    spans = len(re.findall(r'class="btn-label-(?:full|short)"', lt))
    ok(spans == NESTED_LABELS,
       'RECORDED: %d nested label span(s) in lease_timeline that BTN '
       'swallows - finditer does not overlap' % NESTED_LABELS,
       '%d found' % spans)
    ok(len(tight.findall(
           '<button class="btn action-secondary">'
           '<span class="btn-label-full">Previous</span></button>')) == 1,
       '  CONTROL: the outer button matches once and the span not at all')

# ==========================================================================
head('4. RENDERED - WHAT THE FIVE LOOK LIKE, AT 1280 AND AT 390')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

LOOK = r"""() => {
  const b = document.querySelector('#probe');
  const s = getComputedStyle(b);
  let p = b.parentElement, behind = 'rgb(255, 255, 255)';
  while (p) {
    const c = getComputedStyle(p).backgroundColor;
    if (c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent') {
      behind = c; break;
    }
    p = p.parentElement;
  }
  const r = b.getBoundingClientRect();
  return {bg: s.backgroundColor, behind: behind, fg: s.color,
          bc: s.borderTopColor, bw: s.borderTopWidth,
          h: Math.round(r.height * 10) / 10};
}"""

# page, the wrapper the script builds, the inline style it writes, the
# class before, the class after, what it is
CASES = (
    (MAP, 'wizard-done', 'margin-right:10px;', 'btn btn-info',
     'btn action-primary', 'Reload Queue', True),
    (MAP, 'wizard-done', '', 'btn btn-secondary',
     'btn action-secondary', 'Back, beside a primary', False),
    (WIZ, 'wizard-done', '', 'btn btn-info',
     'btn action-primary', 'Back, ALONE = card verb', True),
    (MGT, 'col-md-2', 'height: 38px;', 'btn btn-sm btn-primary w-100',
     'btn btn-sm action-primary w-100', 'the per-row Save', False),
)


def css_of(t):
    return '\n'.join(re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
                     for m in re.finditer(r'<style[^>]*>(.*?)</style>',
                                          t, re.S | re.I))


if sync_playwright is None or not os.path.isfile(BOOT):
    skip('section 4', 'playwright or the Bootstrap fixture is missing')
else:
    boot = read(BOOT)
    base = css_of(read(alv_tree.last_path('base.html')))
    n = [0]

    def look(br, page_css, wrap, style, cls, w):
        n[0] += 1
        mk = ('<div class="%s"><a id="probe" class="%s" style="%s" '
              'href="#">Back to Ingredients</a></div>' % (wrap, cls, style))
        html = ('<!doctype html><html><head><meta charset="utf-8">'
                '<title>b</title><style>%s</style><style>%s</style>'
                '<style>%s</style></head><body class="has-sidebar">'
                '<div class="main-content with-sidebar">%s</div>'
                '</body></html>' % (boot, base, page_css, mk))
        fx = os.path.join(SCRATCH, '_e11_%03d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        ctx = br.new_context(viewport={'width': w, 'height': 900})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        r = pg.evaluate(LOOK)
        ctx.close()
        return r

    # THE EXECUTABLE PATH IS THIS CONTAINER'S, NOT EVERY MACHINE'S.
    # The house pattern, which test_surface_border and test_modal_overlay
    # both use: hand Playwright an executable_path ONLY when that path
    # exists, and otherwise let it find its own browser. Written the other
    # way, this suite CRASHED on Demetri's Windows box - and a crash blocks
    # a push exactly as hard as a failure and says far less about why,
    # which is the sentence already standing in this file's own console
    # preamble. So: the house fallback, and a guard that SKIPS with the
    # reason rather than ending the run.
    _kw = {'executable_path': EXE} if os.path.exists(EXE) else {}
    with sync_playwright() as br0:
        try:
            br = br0.chromium.launch(**_kw)
        except Exception as _e:
            skip('section 4', 'no browser could be launched: %s'
                 % str(_e).split('\n')[0][:90])
            br = None
        if br is not None:
            try:
                tall = []
                for pgname, wrap, style, old, new, what, same in CASES:
                    pcss = css_of(read(alv_tree.last_path(pgname)))
                    b38 = look(br, pcss, wrap, style, old, 390)
                    # after: the class moved AND, for the Save, the inline
                    # height went with it
                    a_style = '' if 'height' in style else style
                    a44 = look(br, pcss, wrap, a_style, new, 390)
                    tall.append((pgname, what, b38['h'], a44['h']))
                    ok(b38['h'] < 44 and a44['h'] >= 44,
                       '%-24s %-20s phone %.0fpx -> %.0fpx'
                       % (pgname[:24], what[:20], b38['h'], a44['h']),
                       '%s -> %s' % (b38, a44))

                    d1 = look(br, pcss, wrap, style, old, 1280)
                    d2 = look(br, pcss, wrap, a_style, new, 1280)
                    if same:
                        ok(d1['bg'] == d2['bg'],
                           '  and it is THE SAME COLOUR either way (%s) - base '
                           'already recolours .btn-info to the accent' % d1['bg'],
                           '%s vs %s' % (d1['bg'], d2['bg']))
                    else:
                        ok(d1['bg'] != d2['bg'],
                           '  and the colour really moves: %s -> %s'
                           % (d1['bg'], d2['bg']))
                    if pgname == MGT:
                        c1 = cr_css(d1['fg'], d1['bg'])
                        c2 = cr_css(d2['fg'], d2['bg'])
                        ok(c1 < 4.5 <= c2,
                           '  THE ONE REAL CONTRAST FAILURE: %.2f -> %.2f, '
                           'under 4.5 and over it' % (c1, c2),
                           '%s on %s  ->  %s on %s'
                           % (d1['fg'], d1['bg'], d2['fg'], d2['bg']))

                ok(all(b < 44 for _p, _w, b, _a in tall)
                   and all(a >= 44 for _p, _w, _b, a in tall),
                   'every one of the %d shapes was under 44px on a phone and '
                   'none is now' % len(tall),
                   tall)

                # THE TWO BACKS GET DIFFERENT TONES, AND THE REASON IS A
                # NUMBER. Measured on the same white success card, label
                # contrast and the button's OWN EDGE against that card:
                pcss = css_of(read(alv_tree.last_path(WIZ)))
                tones = {}
                for cls in ('btn btn-secondary', 'btn btn-info',
                            'btn action-secondary', 'btn action-primary',
                            'btn action-back'):
                    r = look(br, pcss, 'wizard-done', '', cls, 1280)
                    fill = (r['bg'] if r['bg'] not in ('rgba(0, 0, 0, 0)',
                                                       'transparent')
                            else r['behind'])
                    edge = (None if r['bg'] in ('rgba(0, 0, 0, 0)',
                                                'transparent')
                            else cr_css(r['bc'], r['behind'])
                            if r['bc'] not in ('rgba(0, 0, 0, 0)',
                                               'transparent') else None)
                    tones[cls] = (cr_css(r['fg'], fill), edge)
                    print('       %-22s label %5.2f   own edge vs card %s'
                          % (cls, tones[cls][0],
                             ('%.2f' % edge) if edge else 'none'))

                ok(tones['btn action-secondary'][0]
                   > tones['btn btn-secondary'][0],
                   'action-secondary reads its LABEL better than the solid grey '
                   'it replaces (%.2f vs %.2f)'
                   % (tones['btn action-secondary'][0],
                      tones['btn btn-secondary'][0]))
                ok(tones['btn action-secondary'][1] is not None
                   and tones['btn action-secondary'][1] < 3.0,
                   '  and its own EDGE on a white card is under 3:1 (%.2f) - '
                   'which is why the LONE one is not this tone'
                   % tones['btn action-secondary'][1])
                ok(tones['btn action-primary'][1] is not None
                   and tones['btn action-primary'][1] >= 3.0
                   and tones['btn action-primary'][0] >= 4.5,
                   'action-primary carries BOTH: label %.2f and edge %.2f, so '
                   'the card whose only control it is gets that one'
                   % tones['btn action-primary'],
                   tones['btn action-primary'])
                # AND THE 1.24 IS NOT THIS ROUND'S. B-2 moved the border token
                # to it on 6 Oct and recorded the move as the decision. Asked
                # of base rather than asserted in prose.
                ok('--alv-line:' in base
                   and re.search(r'--alv-line:\s*#e3e8ea', base) is not None,
                   '  CONTROL: the edge colour is base\'s own --alv-line '
                   '(#e3e8ea), decided by B-2 - E11 does not move it')

                # CONTROL: the probe can report NO change, so "it moved" is a
                # measurement and not a property of the harness.
                pcss = css_of(read(alv_tree.last_path(MAP)))
                s1 = look(br, pcss, 'wizard-done', '', 'btn action-secondary',
                          1280)
                s2 = look(br, pcss, 'wizard-done', '', 'btn action-secondary',
                          1280)
                ok(s1 == s2,
                   'CONTROL: the same class twice measures identically - the '
                   'probe reports differences, it does not invent them',
                   '%s vs %s' % (s1, s2))
            finally:
                br.close()

# ==========================================================================
head('5. THE REGISTERS, AND THE CLAIM THIS ROUND IS REALLY ABOUT')
# ==========================================================================
ok(ME in alv_tree.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
# REPAIRED BY RS-1a: this was `==`, which is a snapshot dressed as an
# invariant - every later round moves the register. What is true for
# ever is that E11 ADDED one and the register never shrinks past it; the
# exact number E11 left is asked of the pin below, through as_left_by.
ok(len(alv_tree.CONVERTED) >= CONVERTED_NOW,
   'CONVERTED holds at least the %d E11 left' % CONVERTED_NOW,
   len(alv_tree.CONVERTED))
wd = left(WD)
ok('CONVERTED_N = %d' % CONVERTED_NOW in wd,
   '  and %s says %d, read as E11 left it' % (WD, CONVERTED_NOW))
ok('CEILING = %d' % CEILING_NOW in wd,
   '  the walker ceiling is unchanged at %d - both new files use alv_tree'
   % CEILING_NOW)

ok(len(alv_tree.WAITING) == WAITING_NOW,
   'WAITING still holds %d' % WAITING_NOW, len(alv_tree.WAITING))
ok(SWEEP in alv_tree.WAITING,
   '  and %s is STILL held - E11 widened its census, not its walk' % SWEEP)
held = alv_tree.WAITING.get(SWEEP, '')
ok('markup scope' in held and '142' in held,
   '  its reason now names the MARKUP scope and the %d-page census'
   % CENSUS_WIDE, held[:120])
# E-10's precedent, on this same entry: when the numbers in a held reason
# move, the superseded wording has to be gone, not merely outnumbered.
ok('in the tool census against 151' not in str(alv_tree.WAITING),
   '  and no reason still calls 117 "the tool census" - there are two '
   'censuses now')

co = left(CO)
ok('ok(len(aliased) == %d,' % ALIAS_NOW in co,
   '%s pins %d alias(es), read as E11 left it' % (CO, ALIAS_NOW))
for n in (ME, PATCHER):
    ok(re.search(r'(?m)^code_only = alv_tree\.',
                 read(os.path.join(ROOT, n))) is not None,
       '  %s aliases the house stripper at column zero' % n)
ok(re.search(r'(?m)^def code_only\(',
             read(os.path.join(ROOT, ME))) is None
   and re.search(r'(?m)^def python_code_only\(',
                 read(os.path.join(ROOT, ME))) is None,
   '  CONTROL: and this suite defines neither of them')

# REPAIRED BY RS-1a: "last" is true until the next round appends. What
# the order has to say is that this round comes AFTER the one before it,
# which is what as_left_by walks.
ok(SUFFIX in ROUNDS and '.bak_surfborder' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_surfborder'),
   '%s sits after .bak_surfborder in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-4:] if ROUNDS else 'empty')
ps1 = read(os.path.join(ROOT, PS1))
for n in (ME,):
    ok("'%s'" % n in ps1, '%s is on the push gate' % n)

# THE CLAIM. Asked of the suite's own source, because the point of E11
# is that the corpus is right - and a corpus is a line of code.
sw = read(os.path.join(ROOT, SWEEP))
# AND THIS FILE DOES NOT RESOLVE A LABEL AGAINST ONE ROOT. Asked of
# this suite's own source, because the first draft did it fourteen
# times and a round should carry the control for the mistake it made.
_me = read(os.path.join(ROOT, ME))
ok('alv_tree.last_path(' in _me,
   'this suite turns a label back into a file through alv_tree.path_of')
# The needle is BUILT, not written. Spelt out in one piece it would be
# the very shape the detector counts, and this file would fail its own
# check - which is the prose-versus-code problem one layer down.
_narrow = 'os.path.' + 'join(T,'
ok(_me.count(_narrow) == 0,
   '  and not once against a pages/templates root of its own',
   _me.count(_narrow))

ok('JS_FILES = sb.templates(True)' in sw,
   '%s section 10 reads the WHOLE application for its census' % SWEEP)
ok('for f in JS_FILES:' in sw,
   '  and the census loop uses it')
ok('FILES = sb.templates(False)' in sw,
   '  while FILES - the MARKUP walk - is untouched at templates(False)')
ok('not the sweep scope of' in sw,
   '  and a CONTROL says the census corpus is wider than the walk, so '
   'the widening cannot be quietly undone')

# ==========================================================================
head('WHAT THIS ROUND DOES NOT PROVE')
# ==========================================================================
print('  Not that these are the right tones for a Back. action-back reads')
print('  5.53 and was not chosen: the one beside a Reload Queue takes')
print('  action-secondary, because the same file writes that two lines')
print('  away, and the one ALONE on its card takes action-primary,')
print('  because a lone control is that card verb and action-secondary')
print('  edge reads 1.24 on white. Both are decisions, taken against the')
print('  measured numbers above. The suite checks they were carried out.')
print('')
print('  Not that the recipe side is clean. 57 buttons there disagree with')
print('  the classifier and 13 more are UNCLASSIFIED, across 25 pages.')
print('  That is its own round. E11 only stopped the census from calling')
print('  them absent.')
print('')
print('  Not that the three script-built modal headers were work. Base')
print('  took their rules on 24 Sep and test_modal_overlay renders them.')
print('')
print('=' * 74)
print(' %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
sys.exit(1 if failed else 0)
