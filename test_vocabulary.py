# -*- coding: utf-8 -*-
"""test_vocabulary.py - round VC-1, 14 Oct 2026.

THE GATE ASKS EVERY PAGE. VC-1 IS ABOUT WHAT IT CANNOT NAME.

RS-1b took the drift gate from 117 pages to 142 and said in its own suite
that it had not widened the VOCABULARY. Four holes, each measured before
anything was changed:

  a TAG         three controls are a <label>, and BTN matched
                a|button|span. Two of the three are property-side.
  two COLOURS   BOOTSTRAP carried six of Bootstrap's eight outline
                variants. btn-outline-light was on two buttons at
                2.97:1 on a green card header.
  a HOUSE name  action-field-add was on NO list, so Demetri's own
                decision of 30 Sep was invisible on three buttons.
  a DROP        _scan discarded an uncoloured button BEFORE asking
                whether its wrapper had a decision on it.

WHAT THIS SUITE DOES THAT A COMMENT CANNOT
    Section 2 runs the OLD scanner - Show-ButtonDrift.py as VC-1 found
    it, loaded from this round's own backup - and fails if it can still
    see what it was blind to. A claim that a tool used to miss something
    is worth nothing unless the old tool is still there to be asked.

AND ONE THING VC-1 NEARLY DID WRONG
    The first build registered .share-grid on LEAVE. That wrapper holds
    four buttons and three already carried house tones - including the
    disabled Email RS-1b had fixed the day before. A LEAVE entry
    short-circuits every button in its wrapper, so it would have
    silenced yesterday's own fix. Section 8 pins what is already
    silenced that way - EIGHT buttons, three of them action-primary Save
    buttons on property_assets - so the number cannot grow unnoticed.

WHAT IS ASKED OF A BACKUP AND WHAT IS ASKED LIVE
    The nine markup changes are this round's snapshot: before is
    .bak_vocab, after is the file. The vocabulary, the gate and the
    painted count are INVARIANTS and are read live.
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

SUFFIX = '.bak_vocab'
ME = 'test_vocabulary.py'
PATCHER = 'apply_vocabulary.py'
DRIFT = 'Show-ButtonDrift.py'
RA = 'alv_rowactions.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

N_LABELS = 3
N_TONED = 5
N_ROW_ACTIONS = 3
N_REGISTER = 8
N_FIELD_ADD = 3
N_PAINTED = 0
N_SILENCED, N_SILENCED_ENTRIES = 0, 0   # LV-1, 16 Oct 2026 - five wrappers moved to DECIDED and four dead ones were deleted, so no wrapper silences a decided button any more, and no entry holds one.   # (was 8, 2)
CONVERTED_NOW, ALIAS_NOW = 76, 63

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
    """The file as VC-1 found it. A page this round never touched has no
    backup and is its own before, which is what makes section 9 mean
    anything."""
    b = p + SUFFIX
    return read(b) if os.path.isfile(b) else read(p)


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


_spec = importlib.util.spec_from_file_location('_sb_vc1',
                                               os.path.join(ROOT, DRIFT))
sb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sb)

_rspec = importlib.util.spec_from_file_location('_ra_vc1',
                                                os.path.join(ROOT, RA))
ra = importlib.util.module_from_spec(_rspec)
_rspec.loader.exec_module(ra)

_pspec = importlib.util.spec_from_file_location('_ap_vc1',
                                                os.path.join(ROOT, PATCHER))
ap = importlib.util.module_from_spec(_pspec)
_pspec.loader.exec_module(ap)


# THE OLD SCANNER, loaded from this round's own backup. A claim that a tool
# used to be blind to something is worth nothing unless the old tool is
# still there to be asked - the same move RS-1b made for RS-1a's snapshot,
# one round on. ROOT and TPL are handed back, because a module that works
# out where the templates are from its own __file__ would look for them
# beside the copy.
def _tool_as_vc1_found_it():
    src = os.path.join(ROOT, DRIFT + SUFFIX)
    if not os.path.isfile(src):
        return None
    p = os.path.join(SCRATCH, 'show_buttondrift_before_vc1.py')
    with open(p, 'w', encoding='utf-8') as f:
        f.write(read(src))
    s = importlib.util.spec_from_file_location('_sb_before', p)
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    mod.ROOT, mod.TPL = sb.ROOT, sb.TPL
    return mod


sb_before = _tool_as_vc1_found_it()

GATE = sb.templates(True)
BOTH = sorted(alv_tree.rel(p) for p in alv_tree.templates()
              if alv_tree.rel(p) != 'base.html')
HOUSE_TONES = {'action-primary', 'action-secondary', 'action-danger',
               'action-back', 'back-button', 'action-add-new'}

print('=' * 74)
print('%s - VC-1, THE GATE VOCABULARY' % ME)
print('=' * 74)


def scan_of(rel, text):
    sb.JS_REENABLED = sb.js_reenabled_ids(text)
    return sb._scan(rel, sb.markup_of(text))


# ==========================================================================
head('1. THE VOCABULARY ITSELF')
# ==========================================================================
ok('label' in sb.BTN.pattern.split('class=')[0],
   'BTN matches a <label> as well as a|button|span',
   sb.BTN.pattern[:70])
for c in ('btn-outline-light', 'btn-outline-dark', 'btn-link'):
    ok(c in sb.BOOTSTRAP, '  BOOTSTRAP lists %s' % c)
ok(len([c for c in sb.BOOTSTRAP if 'outline' in c]) == 8,
   '  which is all eight of Bootstrap outline colours, not six',
   len([c for c in sb.BOOTSTRAP if 'outline' in c]))
ok('action-field-add' in sb.POSITION and 'action-field-add' in sb.HOUSE,
   'action-field-add is a POSITION class, so HOUSE contains it')
ok(sb.skip_reason('btn action-field-add'),
   '  and it has its own skip_reason, like .action-filter',
   sb.skip_reason('btn action-field-add'))

# AND THE REASON THE NAME ALONE WAS NOT ENOUGH, measured rather than
# asserted: without the skip_reason the tool would hand it a tone.
ok(sb.plan_bar([('(icon only)', 'btn action-field-add',
                 '<button class="btn action-field-add">')])[0]
   == 'action-secondary'
   and sb.rebuild('btn action-field-add', 'action-secondary')
   == 'btn action-secondary action-field-add',
   '  CONTROL: with only the name, plan_bar would tone it and rebuild '
   'would write a second class onto three correct buttons')

ok(hasattr(sb, 'print_painted'),
   'there is a report for a button painted somewhere the tool cannot name')
_dm = python_code_only(read(os.path.join(ROOT, DRIFT)))
ok(_dm.count('print_painted(painted)') == 2,
   '  and BOTH report branches call it - the clean one and the drift one',
   _dm.count('print_painted(painted)'))

# ==========================================================================
head('2. THE OLD SCANNER, ASKED - it really was blind to these')
# ==========================================================================
if sb_before is None:
    skip('section 2', 'no %s backup to load the old scanner from' % DRIFT)
else:
    ok('label' not in sb_before.BTN.pattern.split('class=')[0],
       'the scanner VC-1 found did NOT match a <label>')
    ok('btn-outline-light' not in sb_before.BOOTSTRAP
       and 'btn-link' not in sb_before.BOOTSTRAP,
       '  and did not list btn-outline-light or btn-link')
    ok('action-field-add' not in sb_before.HOUSE,
       '  and HOUSE did not contain action-field-add')

    # The three labels, counted with the old tool over the tree as VC-1
    # found it: zero. With the new tool over the same tree: three.
    then = now = 0
    for r in BOTH:
        old_text = was(alv_tree.path_of(r))
        m_old = sb_before.markup_of(old_text)
        m_new = sb.markup_of(old_text)
        then += len([1 for b in sb_before.BTN.finditer(m_old)
                     if b.group(1).lower() == 'label'])
        now += len([1 for b in sb.BTN.finditer(m_new)
                    if b.group(1).lower() == 'label'])
    ok(then == 0 and now == N_LABELS,
       'over the tree as VC-1 found it: the old scanner saw %d <label> '
       'control(s), the new one sees %d' % (0, N_LABELS),
       '%d then, %d now' % (then, now))

# ==========================================================================
head('3. THE THREE <label> CONTROLS')
# ==========================================================================
LABELS = (('property_assets.html', 'Take Photo'),
          ('edit_asset.html', 'Take Photo'),
          ('my_profile.html', 'Upload Photo'))
found = []
for r in BOTH:
    m = sb.markup_of(read(alv_tree.path_of(r)))
    for b in sb.BTN.finditer(m):
        if b.group(1).lower() == 'label':
            found.append((r, sb.label_of(b.group(3)), b.group(2)))
ok(len(found) == N_LABELS,
   'exactly %d <label> control(s) carry a btn token, across both roots'
   % N_LABELS, found)
ok(sorted(r for r, _l, _c in found) == sorted(r for r, _l in LABELS),
   '  and they are the three file pickers, not something else',
   sorted(r for r, _l, _c in found))
ok(all('action-secondary' in c for _r, _l, c in found),
   '  every one wears action-secondary now',
   [(r, c) for r, _l, c in found if 'action-secondary' not in c])
ok(not [1 for _r, _l, c in found
        if any(x in sb.BOOTSTRAP for x in c.split())],
   '  and not one still carries a Bootstrap colour')
ok(all(any(x in sb.BOOTSTRAP for x in
           re.search(r'class="([^"]*)"',
                     re.search(r'<label[^>]*btn[^>]*>',
                               was(alv_tree.path_of(r))).group(0)
                     ).group(1).split())
       for r, _l in LABELS),
   '  CONTROL: all three DID carry one in the backups - that is the '
   'round definition')

# ==========================================================================
head('4. connectivity_error - the primary DECIDED said it was all along')
# ==========================================================================
_ce = 'error_pages/connectivity_error.html'
_hits = [h for h in scan_of(_ce, read(alv_tree.path_of(_ce)))
         if 'try again' in h[1].lower()]
ok(len(_hits) == 1 and 'action-primary' in _hits[0][3],
   'Try Again carries action-primary', _hits)
ok(not sb.drifting(_hits[0]), '  and the classifier agrees with it')
ok(sb.DECIDED.get('button-group') and
   any(t == 'action-primary' for _f, t in sb.DECIDED['button-group']),
   "  and DECIDED['button-group'] is what says so - a decision that was "
   'already on the register', sb.DECIDED.get('button-group'))
if sb_before is not None:
    _old = sb_before.markup_of(was(alv_tree.path_of(_ce)))
    sb_before.JS_REENABLED = sb_before.js_reenabled_ids(
        was(alv_tree.path_of(_ce)))
    _seen = [h for h in sb_before._scan(_ce, _old)
             if 'try again' in h[1].lower()]
    ok(not _seen,
       '  CONTROL: the old scanner dropped it entirely - a decided '
       'wrapper could not reach a button with no colour', _seen)

# ==========================================================================
head('5. THE PAINTED BUCKET - counted, and empty')
# ==========================================================================
painted = []
drift = undecided = 0
for r in GATE:
    for h in scan_of(r, read(alv_tree.path_of(r))):
        if h[0] == 'PAINTED':
            painted.append((r, h[1], h[3]))
        elif h[0] == 'UNCLASSIFIED':
            undecided += 1
        elif sb.drifting(h):
            drift += 1
ok(len(painted) == N_PAINTED,
   'no button takes its colour from page CSS, an inline style or '
   'JavaScript (%d)' % len(painted), painted[:6])
ok(drift == 0 and undecided == 0,
   '  and over all %d page(s): 0 drifting, 0 undecided' % len(GATE),
   '%d drifting, %d undecided' % (drift, undecided))

# THE BUCKET IS NOT EMPTY BECAUSE IT CANNOT FILL. An empty counter that
# could never report anything is the blind spot with a name on it.
_probe = sb.scan_text('_probe.html',
                      '<div class="nowhere-on-any-register">'
                      '<button class="btn" style="background:#f00">Go'
                      '</button></div>')
ok([h[0] for h in _probe] == ['PAINTED'],
   '  CONTROL: and the bucket still reports one when there is one',
   [h[0] for h in _probe])

# AND IT WAS SEVENTEEN - asked of the OLD TOOL with its OWN vocabulary and
# its OWN registers, over the tree as VC-1 found it. Measuring it with the
# new tool proves nothing: the new tool's LEAVE entries and POSITION name
# account for most of them, so the same question comes back as 2.
#
# The old drop was `not boot and not has_house`, before decided_tone, so
# this re-implements exactly that condition against sb_before. Seventeen
# buttons met it and every one was discarded in silence.
if sb_before is not None:
    _then = []
    for r in sb_before.templates(True):
        t = was(alv_tree.path_of(r))
        m = sb_before.markup_of(t)
        claimed = {h[5] for h in sb_before._scan(r, m)}
        for b in sb_before.BTN.finditer(m):
            names = b.group(2).split()
            if any(c in sb_before.BOOTSTRAP for c in names):
                continue
            if any(c in sb_before.HOUSE for c in names):
                continue
            if b.start() in claimed:
                continue
            _then.append((r, sb_before.label_of(b.group(3)), b.group(2)))
    ok(len(_then) == 17,
       '  and the tree VC-1 found had %d such button(s), every one '
       'discarded in silence' % 17, len(_then))
    ok(len({r for r, _l, _c in _then}) == 8,
       '  across %d page(s)' % 8, len({r for r, _l, _c in _then}))

# ==========================================================================
head('6. THREE CONTROLS THAT BECAME ROW ACTIONS')
# ==========================================================================
_if = read(alv_tree.path_of('ingredient_families.html'))
# THE TOKEN, NOT THE ATTRIBUTE - repaired by PH-2, 14 Oct 2026. This read
# `class="row-actions"` exactly, and PH-2 made the wrapper
# `class="alv-card-aside row-actions"`: the pair is still in .row-actions
# and the inline style is still gone, so the claim held and only the match
# broke. Splitting the class list is also stricter than either - a page
# that renamed the wrapper to `row-actions-wide` still fails here, which a
# substring match would not notice.
#
# AND NO BACKSLASH IN THE NEEDLE, WHICH IS NOT STYLE. The first repair
# wrote a word-boundary regex, and this text is a PAYLOAD inside a
# non-raw triple-quoted string in apply_panel_heads.py: the two
# characters backslash-b became a literal BACKSPACE in the file it wrote,
# and the check failed against a page it was sitting in. Same family as
# the docstring escaping that broke test_surface_border.py on 13 Oct.
ok([c for _cl in re.findall('class="([^"]*)"', _if)
    for c in _cl.split() if c == 'row-actions']
   and 'display: flex; gap: 6px;' not in _if,
   'ingredient_families wraps its pair in .row-actions, and the inline '
   'style is gone')
_base = read(alv_tree.path_of('base.html'))
_ra_css = re.search(r'\.row-actions\s*\{([^}]*)\}', _base)
ok(_ra_css and 'inline-flex' in _ra_css.group(1)
   and 'gap: 6px' in _ra_css.group(1),
   '  and base styles .row-actions inline-flex with a 6px gap - which is '
   'what the inline style said, so the layout did not move',
   _ra_css.group(1) if _ra_css else None)
ok(_if.count('icon-action-btn icon-edit') == 1
   and _if.count('icon-action-btn icon-delete') == 1,
   '  the pencil is icon-edit and the trash is icon-delete')
ok('btn-outline-light' not in _if,
   '  and btn-outline-light is gone from the page')
ok('btn-outline-light' in was(alv_tree.path_of('ingredient_families.html')),
   '  CONTROL: it was there in the backup')

_ps = read(alv_tree.path_of('pantry_staples.html'))
ok('icon-action-btn icon-delete' in _ps and 'btn-link' not in _ps,
   'pantry_staples Remove is the house row-action control')
ok('fa-trash' in _ps and 'fa-times' not in _ps,
   '  and its glyph is fa-trash, because a class carries ONE picture - '
   'the row-action guard refused fa-times on icon-delete')
ok('pantry_staples.html' in ra.NAMED
   and ra.NAMED['pantry_staples.html']['count'] == 1
   and ra.NAMED['pantry_staples.html']['classes'] == ('icon-delete',),
   '  and it is on alv_rowactions.NAMED, with the four of its shape',
   ra.NAMED.get('pantry_staples.html'))
# MD-1, 18 Oct 2026 - still three pages, three controls now. E33 wrote
# create_meal_plan's recipe row once instead of three times.
ok(len(ra.NAMED) == 3
   and sum(v['count'] for v in ra.NAMED.values()) == 3,
   '  which makes three such controls on three pages',
   {k: v['count'] for k, v in ra.NAMED.items()})
ok(ra.FAMILY.get('edit') < ra.FAMILY.get('delete'),
   '  CONTROL: and FAMILY already sorts edit before delete, so the pair '
   'passes the order guard on the day it was written')

# ==========================================================================
head('7. THE TOGGLE THAT WAS PAINTED BY JAVASCRIPT')
# ==========================================================================
_cm = read(alv_tree.path_of('create_meal_plan.html'))
_cm_code = code_only(_cm)
ok('favouritesToggleBtn' in _cm and 'aria-pressed' in _cm,
   'create_meal_plan Favourites carries aria-pressed')
ok('btn action-secondary w-100' in _cm,
   '  and a house tone instead of an inline style')
ok('btn.style.background' not in _cm_code
   and 'favBtn.style.background' not in _cm_code,
   '  and no JavaScript paints it any more',
   [l for l in _cm_code.split('\n') if '.style.background' in l][:3])
ok("setAttribute('aria-pressed'" in _cm_code,
   '  the handler sets the attribute instead')
ok('.btn.action-secondary[aria-pressed="true"]' in _base,
   '  and base.html already answered this - B-1 wrote it on 2 Oct for '
   'the identical control on recipe_management')
ok('btn.style.background' in code_only(
    was(alv_tree.path_of('create_meal_plan.html'))),
   '  CONTROL: the backup really does paint it in JavaScript')

# ==========================================================================
head('8. WHAT A LEAVE ENTRY SILENCES - the mistake this round nearly made')
# ==========================================================================
# A LEAVE entry short-circuits EVERY button in its wrapper. The first build
# of VC-1 registered .share-grid, which holds four buttons and already had
# three house-toned ones in it - including the disabled Email RS-1b fixed
# the day before. Registering it would have silenced yesterday's own fix.
ok('share-grid' not in sb.LEAVE,
   'share-grid is NOT on LEAVE - its one undecided button got a house '
   'class in the markup instead')
_wa = read(alv_tree.path_of('meal_plan_shopping_list.html'))
ok('btn action-secondary share-btn share-whatsapp' in _wa,
   '  and that button is the WhatsApp tile, now action-secondary like '
   'its three siblings')

# LV-1, 16 Oct 2026 - THE PIN IS ZERO NOW, and the census below is
# unchanged so it can say so in the same words it used to say eight.
# .filter-header, .filter-header-right, .input-group-append,
# .pdf-viewer-controls and .zoom-controls moved to DECIDED, where the
# tool CHECKS them; four dead entries were deleted; status-action-form
# is the one that stays, and VC-1's own measurement below is why.
silenced = collections.defaultdict(list)
for r in GATE:
    m = sb.markup_of(read(alv_tree.path_of(r)))
    for b in sb.BTN.finditer(m):
        if not (set(b.group(2).split()) & HOUSE_TONES):
            continue
        for n in sb.innermost_wrapper(m, b.start()):
            if n in sb.LEAVE:
                silenced[n].append((r, sb.label_of(b.group(3)),
                                    b.group(2)))
_n = sum(len(v) for v in silenced.values())
ok(_n == N_SILENCED and len(silenced) == N_SILENCED_ENTRIES,
   'exactly %d already-decided button(s) sit inside a LEAVE wrapper, on '
   '%d entries' % (N_SILENCED, N_SILENCED_ENTRIES),
   '%d on %d: %s' % (_n, len(silenced),
                     {k: len(v) for k, v in silenced.items()}))
ok(sorted(silenced) == [],
   '  there is no wrapper left that silences a decided button - '
   '.filter-header and .input-group-append both went to DECIDED in LV-1',
   sorted(silenced))
ok(len([1 for v in silenced.values() for _r, _l, c in v
        if 'action-primary' in c]) == 0,
   '  and in particular NOT the three action-primary Save buttons on '
   'property_assets, which were the sharp end of this for three rounds')
for k in sorted(silenced):
    for r, lab, c in silenced[k][:5]:
        print('         .%-20s %-28s %-16s %s'
              % (k, r[:28], lab[:16], c[:34]))

# AND THE ENTRY VC-1 DID ADD SILENCES NOTHING THAT WAS BEING CHECKED.
_sa = [c for r in GATE
       for b in sb.BTN.finditer(sb.markup_of(read(alv_tree.path_of(r))))
       for c in [b.group(2)]
       if 'status-action-form' in sb.innermost_wrapper(
           sb.markup_of(read(alv_tree.path_of(r))), b.start())]
ok('status-action-form' in sb.LEAVE,
   'status-action-form IS on LEAVE - eight invoice status buttons')
ok(len(_sa) == N_REGISTER
   and not [c for c in _sa if set(c.split()) & HOUSE_TONES],
   '  and NOT ONE of the eight carried a house tone, so this entry '
   'silences nothing that was being checked',
   [c for c in _sa if set(c.split()) & HOUSE_TONES])
_civ = read(alv_tree.path_of('customer_invoice_form.html'))
ok(all(('.%s {' % n) in _civ.replace('\n', ' ').replace('  ', ' ')
       or ('.' + n) in _civ for n in
       ('btn-delete', 'btn-duplicate', 'btn-approve', 'btn-send',
        'btn-unapprove')),
   '  the page defines all five itself')
ok(len(re.findall(r'--alv-(?:bad|good|warn|accent|on-accent)',
                  _civ[_civ.index('.btn-delete'):][:1400])) >= 5,
   '  on house tokens - --alv-bad, --alv-good, --alv-warn, --alv-accent, '
   '--alv-on-accent - which is why VC-1 names them and does not retone '
   'them')

# ==========================================================================
head('9. THE CONTROL - nothing else moved')
# ==========================================================================
TOUCHED = {'property_assets.html', 'edit_asset.html', 'my_profile.html',
           'error_pages/connectivity_error.html',
           'ingredient_families.html', 'pantry_staples.html',
           'create_meal_plan.html', 'meal_plan_shopping_list.html'}
moved = [r for r in BOTH
         if read(alv_tree.path_of(r)) != was(alv_tree.path_of(r))]
ok(sorted(moved) == sorted(TOUCHED),
   'exactly %d template(s) changed, and they are the named ones'
   % len(TOUCHED), sorted(set(moved) ^ TOUCHED))
ok(len(moved) == 8, '  which is %d of %d' % (8, len(BOTH)), len(moved))

# A FIXED POINT ON ITS OWN OUTPUT, with the WIDER vocabulary.
_again = []
for r in GATE:
    for h in scan_of(r, read(alv_tree.path_of(r))):
        if h[7] or h[0] in ('UNCLASSIFIED', 'PAINTED'):
            continue
        if h[3].split() != h[4].split():
            _again.append((r, h[1], h[3], h[4]))
ok(not _again,
   'and the classifier is still a fixed point, now that it can see more',
   _again[:4])

# ==========================================================================
head('10. THE REGISTERS')
# ==========================================================================
ok(ME in alv_tree.CONVERTED, '%s is on alv_tree.CONVERTED' % ME)
# A FLOOR, NOT AN EQUALITY - PH-2, 14 Oct 2026, and this is the third
# round to make this repair in six days.
ok(len(alv_tree.CONVERTED) >= CONVERTED_NOW,
   '  CONVERTED holds at least %d' % CONVERTED_NOW,
   len(alv_tree.CONVERTED))
# AN ORDER, NOT "NEWEST" - PH-2, 14 Oct 2026. "Newest" is true for one
# day. RS-1a repaired this exact check inside E11's suite, RS-1b inside
# its own, and VC-1 was written with it the same afternoon.
ok(SUFFIX in ROUNDS and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_rsb'),
   '%s is in alv_rounds.ROUNDS, after RS-1b' % SUFFIX, ROUNDS[-3:])
_ps1 = read(os.path.join(ROOT, PS1))
ok("'test_vocabulary.py'" in _ps1, 'the push script runs this suite')
ok('--strict --recipes' in _ps1,
   "  and still runs the drift guard over all 142 pages - RS-1b's line, "
   'untouched')
ok(re.search(r'(?m)^code_only = alv_tree\.',
             read(os.path.join(ROOT, PATCHER))) is not None
   and re.search(r'(?m)^code_only = alv_tree\.',
                 read(os.path.join(ROOT, ME))) is not None,
   '  and both halves of this round alias the one stripper')

# ==========================================================================
head('11. RENDERED - the two contrast repairs')
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
          h: Math.round(r.height * 10) / 10};
}"""


def css_of(t):
    return '\n'.join(re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
                     for m in re.finditer(r'<style[^>]*>(.*?)</style>',
                                          t, re.S | re.I))


# Each row: what it is, the class before, the class after, and the
# wrapper it actually sits in - because the ingredient_families pair sits
# on a SOLID GREEN card header and measuring it on white would prove
# nothing about the page.
PAIRS = (
    ('my_profile Upload Photo', 'btn btn-sm btn-outline-primary',
     'btn action-secondary btn-sm', '', 'repair'),
    ('Take Photo, on a form card', 'btn btn-outline-info',
     'btn action-secondary', '', 'move'),
    # NOT A REPAIR, AND I TOLD DEMETRI IT WAS. See the check below the
    # loop: base.html overrides .bg-success to --alv-good, so this glyph
    # was never on Bootstrap green and never at 2.97:1.
    ('ingredient_families, on its green header',
     'btn btn-sm btn-outline-light', 'icon-action-btn icon-delete',
     'card-header bg-success text-white', 'move'),
    ('connectivity_error Try Again', 'btn', 'btn action-primary',
     '', 'move'),
)

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('section 11', 'playwright or the Bootstrap fixture is missing')
else:
    boot = read(BOOT)
    base_css = css_of(_base)
    n = [0]

    def look(br, cls, wrap, w):
        n[0] += 1
        inner = ('<button id="probe" class="%s">Example</button>' % cls)
        # NESTED AS THE PAGE NESTS IT. A .card-header measured without
        # its .card is not the surface the button sits on, and the first
        # draft of this section read 4.86 where the page reads 2.97.
        mk = ('<div class="card"><div class="%s" style="padding:14px">'
              '%s</div></div>' % (wrap, inner)
              if wrap else
              '<div style="padding:14px">%s</div>' % inner)
        html = ('<!doctype html><html><head><meta charset="utf-8">'
                '<title>b</title><style>%s</style><style>%s</style>'
                '</head><body class="has-sidebar">'
                '<div class="main-content with-sidebar">%s</div>'
                '</body></html>' % (boot, base_css, mk))
        fx = os.path.join(SCRATCH, '_vc%03d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        ctx = br.new_context(viewport={'width': w, 'height': 400})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        r = pg.evaluate(LOOK)
        ctx.close()
        return r

    # THE EXECUTABLE PATH IS THIS CONTAINER'S, NOT EVERY MACHINE'S.
    # test_js_buttons crashed Demetri's push on exactly this line on 13
    # Oct at suite 337 of 337, because it passed the path
    # unconditionally. A crash blocks a push as hard as a failure and
    # says far less about why.
    _kw = {'executable_path': EXE} if os.path.exists(EXE) else {}
    with sync_playwright() as pw0:
        try:
            br = pw0.chromium.launch(**_kw)
        except Exception as _e:
            skip('section 11', 'no browser could be launched: %s'
                 % str(_e).split('\n')[0][:90])
            br = None
        if br is not None:
            try:
                repairs = 0
                for what, old, new, wrap, kind in PAIRS:
                    a = look(br, old, wrap, 1280)
                    b = look(br, new, wrap, 1280)
                    fa = a['bg'] if a['bg'] not in (
                        'rgba(0, 0, 0, 0)', 'transparent') else a['behind']
                    fb = b['bg'] if b['bg'] not in (
                        'rgba(0, 0, 0, 0)', 'transparent') else b['behind']
                    ca, cb = cr_css(a['fg'], fa), cr_css(b['fg'], fb)
                    if kind == 'repair':
                        got = ok(ca < 4.5 <= cb,
                                 '%-38s is a real contrast repair: '
                                 '%.2f -> %.2f' % (what, ca, cb),
                                 '%.2f -> %.2f' % (ca, cb))
                        repairs += 1 if got else 0
                    else:
                        ok(a['bg'] != b['bg'] or a['fg'] != b['fg'],
                           '%-38s moves visibly  %s -> %s'
                           % (what, a['bg'], b['bg']),
                           '%s/%s vs %s/%s' % (a['bg'], a['fg'],
                                               b['bg'], b['fg']))
                        ok(cb >= 4.5,
                           '  and reads at %.2f:1 afterwards' % cb, cb)
                ok(repairs == 1,
                   'ONE of the four is a repair of a failing contrast - '
                   'my_profile at 3.98:1', repairs)

                # AND THE CLAIM I GOT WRONG, PINNED SO IT STAYS WRONG
                # ON RECORD.
                #
                # I told Demetri the ingredient_families glyph was at
                # 2.97:1 and failing. It is not. My standalone probe
                # hard-coded Bootstrap's green, rgb(40, 167, 69), as the
                # fallback fill - and base.html OVERRIDES .bg-success to
                # var(--alv-good), rgb(30, 125, 79). On the colour the
                # page actually paints, the glyph reads 4.86:1 and
                # PASSES. The change is still right, on the other four
                # grounds in the patcher's note; it is not a contrast
                # repair, and a probe that supplies its own answer when
                # the DOM will not is how I came to say it was.
                _hdr = look(br, 'btn btn-sm btn-outline-light',
                            'card-header bg-success text-white', 1280)
                _green = _hdr['behind']
                _was_cr = cr_css(_hdr['fg'], _green)
                ok(_green == 'rgb(30, 125, 79)',
                   'CORRECTION: .bg-success renders as %s, the house '
                   '--alv-good, because base overrides it' % _green,
                   _green)
                ok(_was_cr >= 4.5,
                   '  so the glyph was at %.2f:1 and PASSING, not the '
                   '2.97:1 I reported' % _was_cr, _was_cr)

                # ON A PHONE. The two Take Photo labels are mobile-ONLY,
                # so a tap target is the one thing that must be there.
                tall = look(br, 'btn action-secondary', '', 390)['h']
                ok(tall >= 38,
                   'and a house secondary renders at %.0fpx at 390px wide'
                   % tall, tall)

                # CONTROL: the probe can report NO difference.
                s1 = look(br, 'btn action-secondary', '', 1280)
                s2 = look(br, 'btn action-secondary', '', 1280)
                ok(s1 == s2,
                   'CONTROL: the same class twice measures identically - '
                   'a probe that always reports a change proves nothing',
                   s1)
            finally:
                br.close()

# ==========================================================================
head('WHAT THIS ROUND DOES NOT PROVE')
# ==========================================================================
print('  Not that nothing is painted outside the tool\'s vocabulary. It')
print('  proves no BUTTON is. bg-success, bg-info, bg-danger and')
print('  bg-warning appear 14 times on 10 pages - wcim_results 3,')
print('  pantry_staples 2, projects/projects_detail 2 and seven others -')
print('  on PANELS, where no button census has ever been asked. That is a')
print('  bigger surface than the buttons were and it is its own round.')
print('')
print('  Not that a LEAVE entry is safe. Section 8 pins EIGHT')
print('  already-decided buttons that one hides today, three of them')
print('  action-primary Save buttons. VC-1 declined to make it eleven.')
print('  LEAVE-as-a-silencer is the next thing in this line of work.')
print('')
print('  Not that the eight invoice status buttons are the right colour.')
print('  They are on house tokens and they are now on the register, which')
print('  is a different claim. Five solid fills in one row is a design')
print('  question and Demetri has not been asked it.')
print('')
print('=' * 74)
print(' %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
sys.exit(1 if failed else 0)
