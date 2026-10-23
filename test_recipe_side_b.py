# -*- coding: utf-8 -*-
"""test_recipe_side_b.py - round RS-1b, 14 Oct 2026.

THE RECIPE SIDE FINISHES, AND THE PUSH GATE STOPS LYING.

RS-1b takes the 18 disagreements the instrument reported and the 13
controls nobody had ever decided, drops one wrong entry off the role
register, names three bar buttons that are not their page's verb, and
then changes one line in the push script:

    Show-ButtonDrift.py --strict              117 of 142 pages
    Show-ButtonDrift.py --strict --recipes              142

THREE RULES PROVED WRONG, AND PROVED WRONG HERE
    A comment saying "I tested this and it was wrong" is a comment. So
    section 2 RUNS both withdrawn rules against all 142 pages and fails
    if either one stops being wrong - because the day somebody proposes
    the navigation rule again, the answer should be a failing check and
    not an argument. One of them Demetri had already approved, on my
    say-so, from four examples.

WHAT IS ASKED OF A BACKUP AND WHAT IS ASKED LIVE
    The 31 class lists are this round's snapshot: before is .bak_rsb,
    after is the file. The gate, the registers and the fixed-point
    property are INVARIANTS and are read live. Seventh and eighth
    occurrences of that distinction are in RS-1a's suite, repaired by
    this round - the eighth being the first about the INSTRUMENT rather
    than the pages: a snapshot has to be read by the tool of its day,
    because this round changed what the tool thinks of those pages.

WHAT THIS ROUND DOES NOT PROVE
    That the gate now sees every button. It sees every PAGE. Seventeen
    buttons across eight pages carry neither a Bootstrap colour the tool
    LISTS nor a house class, and section 6 counts them rather than
    leaving them to be rediscovered - two of them `btn-outline-light`,
    which is a Bootstrap colour the vocabulary does not list.
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
import collections
import importlib.util

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

SUFFIX = '.bak_rsb'
ME = 'test_recipe_side_b.py'
PATCHER = 'apply_recipe_side_b.py'
DRIFT = 'Show-ButtonDrift.py'
SWEEP = 'test_button_sweep.py'
TONES = 'test_recipe_tones.py'
PS1 = 'Push-PendingChanges.ps1'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

N_EDITS, N_PAGES = 31, 13
N_DRIFT, N_DECIDED = 18, 13
GATE_WAS, GATE_NOW = 118, 143   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. The same pair as test_js_buttons and test_recipe_tones: an ordinary pages/templates page joins the sweep scope and the page count alike.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. (GATE_NOW was 141)   # RD-1, 19 Oct 2026 - the quick-look
# pair. (GATE_NOW was 139)   # RT-1, 18 Oct 2026 - the wide census is four meal-plan screens smaller and one planner larger. The narrow half does not move.   # (GATE_NOW was 142)

# The three bar buttons that are not their page's verb, and the eleven
# bars the rule I proposed would have touched.
N_NAMED = 3
# RE-DERIVED HERE, NOT TAKEN FROM MY SURVEY. The survey said the
# navigation rule matched 11 bars and was wrong on 6. Both numbers were
# mine and both were low: it matches 12, and TEN of the twelve already
# ship as .action-primary - a shipped decision each. The survey's
# conditional-label numbers (10 and 9) are 9 and 7 when the test is
# written once and asked of both template roots.
# RT-1, 18 Oct 2026 - 13 AND 11. This is the rule RS-1b REFUSED, measured
# against the live corpus so that the refusal keeps being justified.
# MN-1's planner has a Shopping List link in its action bar and it
# ships as .action-primary, so the rule would now reverse eleven
# shipped decisions instead of ten. The refusal gets stronger, not
# weaker, which is why this count is read and not frozen.
N_NAV_RULE_HITS, N_NAV_RULE_PRIMARY = 12, 10   # PP-1, 20 Oct 2026 - the planner leaves the set. The rule needs a bar whose only non-Back item is a link, and the planner bar now holds Print as well as Shopping List.   # (was 13, 11)   # (was 12, 10)
N_COND_LABEL, N_COND_LABEL_PRIMARY = 9, 7

# Buttons the scan cannot see at all: no Bootstrap colour it LISTS, no
# house class. Counted, not described.
N_INVISIBLE, N_INVISIBLE_PAGES = 17, 8
N_OUTLINE_LIGHT = 2

CONVERTED_NOW, ALIAS_NOW = 75, 61

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
    """The file as THIS round found it. A page RS-1b did not touch has no
    backup and is its own before, which is what makes the control in
    section 5 mean anything."""
    # RT-1, 18 Oct 2026 - see alv_tree.bak_path: a retired page's
    # backups stay where they were, beside the hole it left.
    b = alv_tree.bak_path(p, SUFFIX)
    return read(b) if os.path.isfile(b) else read(p)


def left(name):
    p = os.path.join(ROOT, name)
    if as_left_by is None:
        return read(p)
    return as_left_by(p, SUFFIX, read)


_spec = importlib.util.spec_from_file_location('_sb_rs1b',
                                               os.path.join(ROOT, DRIFT))
sb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sb)

_pspec = importlib.util.spec_from_file_location('_ap_rs1b',
                                                os.path.join(ROOT, PATCHER))
ap = importlib.util.module_from_spec(_pspec)
_pspec.loader.exec_module(ap)

TONE_NAMES = {'action-primary', 'action-secondary', 'action-danger',
              'action-back', 'action-add-new'}


def scan_of(rel, text):
    sb.JS_REENABLED = sb.js_reenabled_ids(text)
    return sb._scan(rel, sb.markup_of(text))


# TWO CORPORA, AND SAYING WHICH IS WHICH IS THE POINT.
#
# GATE is Show-ButtonDrift's own scope - pages/templates, 142 pages -
# which is what `--strict --recipes` asks and therefore what every claim
# about the gate has to be asked of.
#
# BOTH is every template in the repo, 150, because alv_tree walks the
# CRS root as well. The withdrawn rules below are measured over BOTH, and
# they have to be: three of the bars the navigation rule would have
# demoted are CRS pages, and a rule proved harmless on the narrower set
# would be proved on the wrong thing.
#
# AND SO: THE GATE IS 142 OF 150. The eight CRS pages sit outside
# templates() by a stated position in Show-ButtonDrift itself - two
# callers stand on that scope - and test_drift_root.py owns them.
# Widening templates() is a different round, and this one does not
# pretend otherwise.
GATE = sb.templates(True)
SWEPT = sb.templates(False)
BOTH = sorted(alv_tree.rel(p) for p in alv_tree.templates()
              if alv_tree.rel(p) != 'base.html')


def pages(side=None):
    if side is None:
        return GATE
    if side == 'other':
        return SWEPT
    return [r for r in GATE if sb.is_recipe_side(r)]



def srgb(v):
    v = v / 255.0
    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4


def cr_css(a, b):
    pa = [int(x) for x in re.findall(r'\d+', a)[:3]]
    pb = [int(x) for x in re.findall(r'\d+', b)[:3]]
    la = 0.2126 * srgb(pa[0]) + 0.7152 * srgb(pa[1]) + 0.0722 * srgb(pa[2])
    lb = 0.2126 * srgb(pb[0]) + 0.7152 * srgb(pb[1]) + 0.0722 * srgb(pb[2])
    hi, lo = max(la, lb), min(la, lb)
    return round((hi + 0.05) / (lo + 0.05), 2)


print('=' * 74)
print('%s - RS-1b, THE RECIPE SIDE FINISHES AND THE GATE WIDENS' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE 31 CLASS LISTS - BEFORE FROM THE BACKUP, AFTER FROM THE FILE')
# ==========================================================================
ok(len(ap.EDITS) == N_EDITS,
   'the patcher plans %d edit(s)' % N_EDITS, len(ap.EDITS))
ok(len({e[0] for e in ap.EDITS}) == N_PAGES,
   '  across %d page(s)' % N_PAGES, len({e[0] for e in ap.EDITS}))

missing = [e[0] for e in ap.EDITS
           if not os.path.isfile(alv_tree.bak_of(e[0], SUFFIX))]
ok(not missing, '  and every one of those pages has a backup of this round',
   sorted(set(missing)))

gone = [(p, o[:60]) for p, o, _n, _w in ap.EDITS
        if o in read(alv_tree.last_path(p))]
ok(not gone, 'not one of the %d old open tags survives in its page'
   % N_EDITS, gone)

here = [(p, n[:60]) for p, _o, n, _w in ap.EDITS
        if n not in read(alv_tree.last_path(p))]
ok(not here, '  and every one of the %d new ones is there' % N_EDITS, here)

back = [(p, o[:60]) for p, o, _n, _w in ap.EDITS
        if o not in was(alv_tree.last_path(p))]
ok(not back, '  and the backups hold all %d of the old ones' % N_EDITS, back)

# EVERY ONE OF THE 13 DECISIONS CARRIES A BOOTSTRAP COLOUR BEFORE AND A
# HOUSE TONE AFTER. That is the round's definition, not a count.
_boot_before, _tone_after = [], []
for p, o, n, w in ap.EDITS:
    cls_o = re.search(r'class="([^"]*)"', o).group(1).split()
    cls_n = re.search(r'class="([^"]*)"', n).group(1).split()
    if any(c in sb.BOOTSTRAP for c in cls_o):
        if not any(c in TONE_NAMES for c in cls_n):
            _tone_after.append((p, w))
        _boot_before.append((p, w))
ok(len(_boot_before) == N_DECIDED,
   'exactly %d of the %d were wearing a Bootstrap colour - the ones '
   'nobody had decided' % (N_DECIDED, N_EDITS), len(_boot_before))
ok(not _tone_after, '  and every one of those now wears a house tone',
   _tone_after)

# ==========================================================================
head('2. THE TWO RULES I PROPOSED, RUN - BOTH STILL WRONG')
# ==========================================================================
# A comment saying a rule was tested and rejected is a comment. These RUN.


def bars_of(rel, text):
    m = sb.markup_of(text)
    for n, a, z in sb.bars(m):
        items = []
        for b in sb.BTN.finditer(m[a:z]):
            t = b.group(0)[:b.group(0).index('>') + 1]
            items.append((sb.label_of(b.group(3)), b.group(2), t,
                          b.group(3)))
        yield n, items


def real_items(items):
    """The buttons a bar actually offers - Back, More, Help and Cancel are
    none of them, which is the lone-verb rule's own vocabulary.

    SUBSTRING, NOT LIST MEMBERSHIP, and that is not a style choice: the
    More toggle is spelt `action-more-btn`, so an `in cls.split()` test
    misses it and admin_apms reads as a bar with two real buttons. It
    did, in the first draft of this suite, and the count came out 11 -
    which is how my survey got 11 as well.
    """
    out = []
    for lab, cls, tag, inner in items:
        low = lab.lower()
        if ('action-back' in cls or 'back-button' in cls
                or 'action-more' in cls or 'action-filter' in cls
                or low.strip() == 'back'):
            continue
        if low.startswith('help') or sb.is_cancel(lab):
            continue
        out.append((lab, cls, tag, inner))
    return out


# THE NAVIGATION RULE: "a bar whose only non-Back item is a link to
# another page is navigation, not the page's verb." Demetri approved it.
# I had tested it on four examples.
nav_hits = []
for r in BOTH:
    for _n, items in bars_of(r, read(alv_tree.last_path(r))):
        real = real_items(items)
        if len(real) != 1:
            continue
        lab, cls, tag, _inner = real[0]
        if not tag.lower().startswith('<a '):
            continue
        href = re.search(r'href\s*=\s*"([^"]*)"', tag)
        h = (href.group(1) if href else '').strip()
        if h and h != '#' and 'javascript' not in h.lower():
            nav_hits.append((r, lab, cls))
ok(len(nav_hits) == N_NAV_RULE_HITS,
   'the navigation rule I proposed matches %d bar(s) across both '
   'template roots (%d pages)' % (N_NAV_RULE_HITS, len(BOTH)),
   '%d: %s' % (len(nav_hits), [(r, l) for r, l, _c in nav_hits]))

# AND THE TEST THAT MATTERS: how many of them are ALREADY the page's
# primary? Each of those is a decision somebody took and shipped, and the
# rule would have reversed it sight unseen.
nav_primary = [(r, l) for r, l, c in nav_hits if 'action-primary' in c]
ok(len(nav_primary) == N_NAV_RULE_PRIMARY,
   '  and %d of the %d already ship as .action-primary - the rule would '
   'have reversed %d shipped decisions'
   % (N_NAV_RULE_PRIMARY, N_NAV_RULE_HITS, N_NAV_RULE_PRIMARY),
   '%d: %s' % (len(nav_primary), nav_primary))
ok(any('submit fsr' in l.lower() for _r, l in nav_primary),
   '  CONTROL: Submit FSR is one of them - a fault Demetri reported and '
   'this programme fixed')
ok(sorted(l for r, l, c in nav_hits if 'action-primary' not in c)
   == ['Families', 'Start over'],
   '  and the only two it would have got RIGHT are the two this round '
   'names by hand instead',
   sorted(l for r, l, c in nav_hits if 'action-primary' not in c))

# THE CHOOSER RULE: "a label built from a template conditional is a
# chooser, not a verb." Read off the button's INNER markup, because
# label_of has already flattened both branches into one string by the
# time anyone sees a label.
cond = []
for r in BOTH:
    for _n, items in bars_of(r, read(alv_tree.last_path(r))):
        for lab, cls, _tag, inner in real_items(items):
            if re.search(r'\{%\s*if\b', inner):
                cond.append((r, lab, cls))
ok(len(cond) == N_COND_LABEL,
   'the chooser rule I proposed matches %d bar button(s)' % N_COND_LABEL,
   '%d: %s' % (len(cond), [(r, l) for r, l, _c in cond]))
cond_primary = [(r, l) for r, l, c in cond if 'action-primary' in c]
ok(len(cond_primary) == N_COND_LABEL_PRIMARY,
   '  and %d of them already ship as .action-primary - Create Country, '
   'Create FI, Issue Receipt, Add Customer, Save as Draft, Save Recipe '
   'and a Print' % N_COND_LABEL_PRIMARY,
   '%d: %s' % (len(cond_primary), cond_primary))
ok(not [1 for _r, l, c in cond
        if 'calendar view' in l.lower() and 'action-primary' in c],
   '  CONTROL: and the one button the rule was FOR is not among them - '
   "celebration_calendar's toggle is the only reason it was tempting")

# ==========================================================================
head('3. THE MAP THAT REPLACED THEM, AND THE REGISTER ENTRY THAT WENT')
# ==========================================================================
ok(hasattr(sb, 'NOT_THE_VERB') and hasattr(sb, 'not_the_verb'),
   '%s carries NOT_THE_VERB and not_the_verb()' % DRIFT)
ok(len(sb.NOT_THE_VERB) == N_NAMED,
   '  %d page(s) are named in it' % N_NAMED, len(sb.NOT_THE_VERB))
noreason = [(p, f) for p, v in sb.NOT_THE_VERB.items()
            for f, why in v if not why or len(why) < 20]
ok(not noreason, '  and every entry carries a reason, not just a name',
   noreason)
ok(sb.not_the_verb('pantry_staples.html', 'Families')
   and sb.not_the_verb('celebration_calendar.html',
                       'Calendar View  Timeline View')
   and sb.not_the_verb('wcim_results.html', 'Start over'),
   '  all three are found by page and label')
ok(sb.not_the_verb('crs/country_list.html', 'Add Country') is None
   and sb.not_the_verb('friday_status_report.html', 'Submit FSR') is None,
   '  CONTROL: and it says nothing about Add Country or Submit FSR - a '
   'map can only be wrong where it was written')
ok(sb.not_the_verb(None, 'Families') is None,
   '  CONTROL: and nothing at all when no page is given')

ok('d-flex' not in sb.DECIDED,
   "d-flex is off the role register - it is a Bootstrap layout utility")
ok("'d-flex' WAS HERE" in read(os.path.join(ROOT, DRIFT)),
   '  and the line it occupied says so, with what it reached')
layout_left = [n for n in ('text-center', 'alert', 'col-md-6', 'detail-row',
                           'col-12') if n in sb.DECIDED]
ok(len(layout_left) == 5,
   '  CONTROL: five layout names are still on it and are recorded as '
   'such, not quietly removed too', layout_left)

# AND THE HAZARD DROPPING IT WOULD HAVE BEEN, HAD RS-1a NOT RUN FIRST.
# Two buttons under a d-flex were drift ONLY because d-flex was on the
# register. Read the pre-RS-1a pages with today's tool and they are
# UNCLASSIFIED - which would have failed the gate. They carry house
# classes today, so they do not.
_resets = []
for r in ('ingredient_families.html', 'pantry_staples.html'):
    for h in scan_of(r, read(alv_tree.last_path(r))):
        if h[1].strip().lower() == 'reset':
            _resets.append((r, h[0], h[3]))
ok(len(_resets) == 2
   and all(k != 'UNCLASSIFIED' and 'action-secondary' in c
           for _r, k, c in _resets),
   'the two Reset buttons d-flex used to speak for are classified '
   'without it, because RS-1a gave them house classes first', _resets)

# ==========================================================================
head('4. THE THREE SUPPRESSED PROMOTIONS - EACH BAR, EACH REASON')
# ==========================================================================
for rel, label, keep in (('pantry_staples.html', 'Families',
                          'action-secondary'),
                         ('wcim_results.html', 'Start over',
                          'action-secondary'),
                         ('celebration_calendar.html', 'Calendar View',
                          'action-secondary')):
    hits = [h for h in scan_of(rel, read(alv_tree.last_path(rel)))
            if label.lower() in h[1].lower()]
    ok(len(hits) == 1 and keep in hits[0][3] and not sb.drifting(hits[0]),
       '%-28s %-16s stays a %s and is not drift'
       % (rel, label, keep), hits)
    ok(bool(sb.not_the_verb(rel, label)),
       '  with the reason on record: %s'
       % (sb.not_the_verb(rel, label) or '(none)'))

# AND THE PROMOTION I HAD WRONG IN THE SURVEY. Of every modal-footer
# primary in the application exactly two are a link to another page, and
# the house already ships one of them.
foot_links = []
for r in pages():
    text = read(alv_tree.last_path(r))
    m = sb.markup_of(text)
    for w, a, z in sb.footers(m):
        items, tags = [], []
        for b in sb.BTN.finditer(m[a:z]):
            t = b.group(0)[:b.group(0).index('>') + 1]
            items.append((sb.label_of(b.group(3)), b.group(2), t))
            tags.append(t)
        for (lab, _c, t), tone in zip(items, sb.plan_footer(items)):
            if tone != 'action-primary' or not t.lower().startswith('<a '):
                continue
            h = re.search(r'href\s*=\s*"([^"]*)"', t)
            if h and h.group(1).strip() not in ('', '#'):
                foot_links.append((r, lab))
# 2 -> 3 - RD-1, 19 Oct 2026. The quick-look dialog is modelled on
# wcim_recipe_quick_view and carries the same Open full recipe in its
# footer for the same reason, so it joins this list rather than being
# an exception to it.
ok(len(foot_links) == 3,
   'exactly 3 modal-footer primaries in the application are a link to '
   'another page', foot_links)
ok(sorted(r for r, _l in foot_links)
   == ['properties_edit.html', 'recipe_quicklook.html',
       'wcim_recipe_quick_view.html'],
   '  and they are properties_edit (shipped as action-primary since '
   'the footer round) and this round\'s Open full recipe', foot_links)
ok('class="btn action-primary"' in read(
    alv_tree.last_path('properties_edit.html')),
   '  CONTROL: properties_edit really does ship a solid primary there - '
   'the precedent is on disk, not in my memory')

# ==========================================================================
head('5. THE GATE - AND WHAT IT STILL CANNOT SEE')
# ==========================================================================
ps1 = read(os.path.join(ROOT, PS1))
ok('& python $guard --strict --recipes' in ps1,
   'the push gate runs the drift guard with --recipes')
ok(ps1.count('--strict --recipes') >= 2,
   '  and says so in the line it prints, so the log names the scope',
   ps1.count('--strict --recipes'))
ok(len(sb.templates(False)) == GATE_WAS
   and len(sb.templates(True)) == GATE_NOW,
   '  which takes it from %d page(s) to %d' % (GATE_WAS, GATE_NOW),
   '%d -> %d' % (len(sb.templates(False)), len(sb.templates(True))))
ok('walks every\n# template' not in ps1,
   '  and the sentence that claimed it walked every template while it '
   'asked 117 is gone')

# THE GATE ACTUALLY PASSES, run here rather than asserted about.
drift, undecided = 0, 0
for r in pages():
    for h in scan_of(r, read(alv_tree.last_path(r))):
        if h[0] == 'UNCLASSIFIED':
            undecided += 1
        elif sb.drifting(h):
            drift += 1
ok(drift == 0 and undecided == 0,
   'over all %d page(s): 0 drifting, 0 undecided' % GATE_NOW,
   '%d drifting, %d undecided' % (drift, undecided))

# A FIXED POINT ON ITS OWN OUTPUT. Feed the classifier what it just
# produced; it must propose nothing. This is the property that lets
# --strict be a gate rather than a perpetual to-do list.
moved = []
for r in pages():
    for h in scan_of(r, read(alv_tree.last_path(r))):
        if h[7] or h[0] == 'UNCLASSIFIED':
            continue
        if h[3].split() != h[4].split():
            moved.append((r, h[1], h[3], h[4]))
ok(not moved, '  and the classifier is a fixed point on the swept tree',
   moved[:4])

# WHAT IT STILL CANNOT SEE. Counted, so the claim is measured.
inv = collections.Counter()
outline_light = []
for r in pages():
    m = sb.markup_of(read(alv_tree.last_path(r)))
    for b in sb.BTN.finditer(m):
        names = b.group(2).split()
        if any(c in ('btn-outline-light', 'btn-outline-dark') for c in names):
            outline_light.append((r, sb.label_of(b.group(3))))
        if not any(c in sb.BOOTSTRAP for c in names) \
                and not any(c in sb.HOUSE for c in names):
            inv[r] += 1
# PAID BY VC-1, 14 Oct 2026, AND THE CLAIM IS TURNED OVER.
#
# RS-1b found seventeen of these on eight pages and said so here rather
# than leaving them to be rediscovered. VC-1 took every one: three were
# correct house buttons whose class was on no list, two were
# btn-outline-light, one was a toggle painted by JavaScript, one should
# have been a primary by a decision already on the register, three became
# row actions, and the last eight - the invoice status rows - are on the
# register with a reason because they were already on house tokens.
#
# What is left is those eight, and they are NAMED now, which is a
# different thing from invisible. The number is pinned here so RS-1b's
# own finding cannot quietly grow back.
ok(sum(inv.values()) == 8 and len(inv) == 2,
   '%d button(s) in %d page(s) carry neither a listed Bootstrap colour '
   'nor a house class - VC-1 took %d of the %d RS-1b found, and named '
   'the rest' % (8, 2, N_INVISIBLE - 8, N_INVISIBLE),
   '%d in %d: %s' % (sum(inv.values()), len(inv), dict(inv)))
ok(sorted(inv) == ['customer_invoice_form.html',
                   'physical_invoice_edit.html'],
   '  and they are the two invoice status rows, on LEAVE with a reason',
   sorted(inv))
# ALSO PAID. btn-outline-light is in BOOTSTRAP since VC-1 and the two
# buttons that wore it are the house row-action pair now.
ok(len(outline_light) == 0,
   '  %d of them wear btn-outline-light, which IS a Bootstrap colour and '
   'which BOOTSTRAP does not list' % N_OUTLINE_LIGHT, outline_light)
ok('btn-outline-light' in sb.BOOTSTRAP,
   '  and the vocabulary IS wider now - RS-1b declined to do it in the '
   'same breath as its own sweep, and VC-1 did it on 14 Oct')
for r, n in inv.most_common():
    print('         %-40s %d' % (r, n))

# ==========================================================================
head('6. ONE DEFINITION OF A VERB - BOTH COPIES OF THE RULE')
# ==========================================================================
sweep = read(os.path.join(ROOT, SWEEP))
ok('sb.not_the_verb(' in sweep,
   "%s section 9 asks the tool about a named exception too" % SWEEP)
ok('sb.is_chooser(' in sweep,
   '  as it already did about a chooser - the PM-1 lesson, kept')
ok(python_code_only(read(os.path.join(ROOT, DRIFT))).count(
    'def not_the_verb(') == 1,
   '  and the rule is defined exactly once, in the tool')
ok('page=name' in read(os.path.join(ROOT, DRIFT)),
   '  plan_bar is given the page it is planning, which it never had')
ok(re.search(r'def plan_bar\(items, in_bar=False, page=None\)',
             read(os.path.join(ROOT, DRIFT))) is not None,
   '  by a keyword with a default, so every existing call still works')

# ==========================================================================
head('7. THE CONTROL - THE 117 PAGES DID NOT MOVE')
# ==========================================================================
swept = [r for r in pages('other')]
ok(len(swept) == GATE_WAS, 'the property side is %d page(s)' % GATE_WAS,
   len(swept))
touched = [r for r in swept
           if os.path.isfile(alv_tree.bak_of(r, SUFFIX))]
ok(not touched, '  and not one of them has a backup of this round',
   touched)
diff = [r for r in swept
        if read(alv_tree.last_path(r)) != was(alv_tree.last_path(r))]
ok(not diff, '  and not one of them changed by a byte', diff)

# RS-1a'S SUITE, REPAIRED - the seventh and eighth occurrences.
tn = read(os.path.join(ROOT, TONES))
ok('def as_rs1a_left_it(' in tn and 'REPAIRED BY RS-1b' in tn,
   "RS-1a's suite reads its handover counts as a snapshot, not live")
ok("buckets('recipe', read)\nok(now['bootstrap'] == 0" in tn,
   '  and its one real INVARIANT is still read live')
ok('sb_then = _tool_as_rs1a_left_it()' in tn,
   '  and the snapshot is read by the TOOL RS-1a left, because this '
   'round changed what the tool thinks of those pages')
ok("ok('--strict --recipes' in ps1," in tn,
   "  and RS-1a's claim that RS-1b owed it the wider gate is turned "
   'over, not deleted')

# ==========================================================================
head('8. THE REGISTERS')
# ==========================================================================
ok(ME in alv_tree.CONVERTED, '%s is on alv_tree.CONVERTED' % ME)
ok(len(alv_tree.CONVERTED) >= CONVERTED_NOW,
   '  CONVERTED holds at least %d' % CONVERTED_NOW,
   len(alv_tree.CONVERTED))
# A FLOOR AND AN ORDER, NOT AN EQUALITY - the repair RS-1a made to E11
# for this exact check, two rounds ago. "Newest" is true for one day.
ok(SUFFIX in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_pxphotos'),
   '%s is in alv_rounds.ROUNDS, after PX-1' % SUFFIX, ROUNDS[-3:])
ok(SWEEP not in alv_tree.CONVERTED,
   '  CONTROL: and test_button_sweep is STILL not released - its markup '
   'walk rebuilds a pre-sweep tree and stays narrow by design, which is '
   'why the GATE widened and that SUITE did not')
ok("'test_recipe_side_b.py'" in ps1,
   'the push script runs this suite')
ok(re.search(r'(?m)^code_only = alv_tree\.',
             read(os.path.join(ROOT, PATCHER))) is not None
   and re.search(r'(?m)^code_only = alv_tree\.',
                 read(os.path.join(ROOT, ME))) is not None,
   '  and both halves of this round alias the one stripper')

# ==========================================================================
head('9. RENDERED - WHAT EACH OF THE 13 DECISIONS LOOKS LIKE')
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
          bd: s.borderColor,
          h: Math.round(r.height * 10) / 10};
}"""

# One row per DISTINCT transition among the 13, with what it is for.
PAIRS = (
    ('btn btn-outline-secondary', 'btn action-secondary',
     'the servings stepper, Clear All, Skip extras', 'move'),
    ('btn btn-primary', 'btn action-secondary',
     'the search button welded to its field', 'move'),
    ('btn btn-outline-danger w-100', 'btn action-secondary w-100',
     'Clear Filters stops being red', 'move'),
    ('btn btn-sm btn-danger', 'btn action-secondary action-danger btn-sm',
     'Remove reads destructive by tone, not by fill', 'move'),
    ('btn btn-info btn-lg', 'btn action-primary btn-lg',
     'Extract Recipe with AI', 'same-ish'),
    ('btn btn-outline-primary', 'btn action-secondary',
     'calendar Previous and Next', 'move'),
    ('btn btn-outline-primary', 'btn action-primary',
     'Try again, the way out of an AI error', 'repair'),
    ('btn btn-secondary', 'btn action-secondary',
     'Print, beside three house siblings', 'move'),
    ('btn btn-info', 'btn action-secondary',
     'Copy, beside three house siblings', 'move'),
)


def css_of(t):
    return '\n'.join(re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
                     for m in re.finditer(r'<style[^>]*>(.*?)</style>',
                                          t, re.S | re.I))


if sync_playwright is None or not os.path.isfile(BOOT):
    skip('section 9', 'playwright or the Bootstrap fixture is missing')
else:
    boot = read(BOOT)
    base = css_of(read(alv_tree.last_path('base.html')))
    n = [0]

    def look(br, cls, w):
        n[0] += 1
        mk = ('<div class="recipe-probe-wrap"><button id="probe" '
              'class="%s">Example</button></div>' % cls)
        html = ('<!doctype html><html><head><meta charset="utf-8">'
                '<title>b</title><style>%s</style><style>%s</style>'
                '</head><body class="has-sidebar">'
                '<div class="main-content with-sidebar">%s</div>'
                '</body></html>' % (boot, base, mk))
        fx = os.path.join(SCRATCH, '_rsb%03d.html' % n[0])
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
    # test_js_buttons crashed Demetri's push on exactly this line on 13
    # Oct, at suite 337 of 337, because it passed the path
    # unconditionally. A crash blocks a push as hard as a failure and
    # says far less about why - which is the sentence already standing
    # in this file's own console preamble.
    _kw = {'executable_path': EXE} if os.path.exists(EXE) else {}
    with sync_playwright() as pw0:
        try:
            br = pw0.chromium.launch(**_kw)
        except Exception as _e:
            skip('section 9', 'no browser could be launched: %s'
                 % str(_e).split('\n')[0][:90])
            br = None
        if br is not None:
            try:
                moves = 0
                for old, new, what, kind in PAIRS:
                    a = look(br, old, 1280)
                    b = look(br, new, 1280)
                    fa = a['bg'] if a['bg'] not in (
                        'rgba(0, 0, 0, 0)', 'transparent') else a['behind']
                    fb = b['bg'] if b['bg'] not in (
                        'rgba(0, 0, 0, 0)', 'transparent') else b['behind']
                    ca, cb = cr_css(a['fg'], fa), cr_css(b['fg'], fb)
                    if kind == 'repair':
                        ok(cb >= 4.5,
                           '%-30s now reads at %.2f:1 against its fill'
                           % (what, cb), '%.2f -> %.2f' % (ca, cb))
                    elif kind == 'same-ish':
                        ok(cb >= 4.5,
                           '%-30s reads at %.2f:1' % (what, cb), cb)
                    else:
                        got = ok(a['bg'] != b['bg'] or a['fg'] != b['fg']
                                 or a['bd'] != b['bd'],
                                 '%-30s moves visibly  %s -> %s'
                                 % (what, a['bg'], b['bg']),
                                 '%s/%s/%s vs %s/%s/%s'
                                 % (a['bg'], a['fg'], a['bd'],
                                    b['bg'], b['fg'], b['bd']))
                        moves += 1 if got else 0
                        ok(cb >= 4.5,
                           '  and still reads at %.2f:1 after the move' % cb,
                           cb)
                ok(moves == 7,
                   'seven of the nine transitions are a visible change',
                   moves)

                # ON A PHONE. Every one of the thirteen is reachable on a
                # phone and none of them is in an action bar, so none can
                # be hidden by base's More-menu rule - but the TAP TARGET
                # still has to be there.
                phone = [(what, look(br, new, 390)['h'])
                         for _o, new, what, _k in PAIRS]
                short = [(w, h) for w, h in phone if h < 44]
                ok(not short,
                   'and every one of the nine is at least 44px tall at '
                   '390px wide', short)

                # CONTROL: the probe can report NO difference.
                s1 = look(br, 'btn action-secondary', 1280)
                s2 = look(br, 'btn action-secondary', 1280)
                ok(s1 == s2,
                   'CONTROL: the same class twice measures identically - a '
                   'probe that always reports a change proves nothing', s1)
            finally:
                br.close()

# ==========================================================================
head('WHAT THIS ROUND DOES NOT PROVE')
# ==========================================================================
print('  Not that the gate sees every BUTTON. It sees every PAGE. Section')
print('  5 counts %d buttons in %d pages that carry neither a listed'
      % (N_INVISIBLE, N_INVISIBLE_PAGES))
print('  Bootstrap colour nor a house class, two of them wearing')
print('  btn-outline-light - a Bootstrap colour the vocabulary does not')
print('  list. Widening BOOTSTRAP surfaces property-side drift in the')
print('  same breath, so it is its own round and not a line in this one.')
print('')
print('  Not that celebration_calendar\'s view toggle is fixed. It is')
print('  NAMED. A house marker class for a view toggle, the way .alv-seg')
print('  marks a segment, is the principled answer and it touches')
print('  base.html. When it lands, that entry comes off the map.')
print('')
print('  Not that the 13 decisions are the right colours. They follow')
print('  precedents already on disk - login.html for a welded icon')
print('  button, three Clear Alls for filter chrome, pdf-viewer-error for')
print('  a retry, properties_edit for a footer link - and section 9')
print('  renders every transition. Demetri decides colour.')
print('')
print('=' * 74)
print(' %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
sys.exit(1 if failed else 0)
