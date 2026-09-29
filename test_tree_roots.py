# -*- coding: utf-8 -*-
"""test_tree_roots.py - Section X round X0, 28 Sep 2026.

THE BLIND SPOT THIS SUITE EXISTS TO CLOSE.
    Demetri reported the CRS Reporting screens were green. They are. No
    gate in this programme had ever looked at them, because every census
    walks pages/templates and the CRS templates live in crs/templates/crs/
    - a separate Django app, mounted at /crs/ by mysite/urls.py.

    A gate that cannot see a file does not fail. It agrees. That is what
    makes this class of bug expensive: the instrument reports success.

SECTION 1 IS THE TREE ITSELF - both roots, 146 templates, and the zero
basename collisions that dozens of other suites depend on without saying
so.

SECTION 2 IS THE CONVERSION - 33 suites now walk via alv_tree.

SECTION 3 IS THE PART THAT MATTERS IN SIX MONTHS. Every walking suite in
the repo must appear in exactly ONE of three lists: converted, waiting on
a named CRS round, or walking the repo already. A suite in none of them
fails this gate. That is what stops a future census from quietly building
its own root, which is the mistake this whole round is paying for.

SECTION 4 IS THE DEBT, counted and falling. 103 scripts walked a
hard-coded template root before this round. The number may go DOWN and
never up.
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
# ------------------------------------------------------------------------

import glob
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s - it IS this round' % e)
try:
    from alv_rounds import ROUNDS
except Exception as e:
    ROUNDS = []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_treeroots'
ME = 'test_tree_roots.py'
PATCHER = 'apply_tree_roots.py'
PS1 = 'Push-PendingChanges.ps1'

# Measured 28 Sep, with the app staged from the laptop.
MAIN_N = 138
CRS_N = 8
TOTAL_N = MAIN_N + CRS_N

CRS_PAGES = [
    'crs/country_form.html', 'crs/country_list.html', 'crs/fi_form.html',
    'crs/fi_list.html', 'crs/index.html', 'crs/submission_detail.html',
    'crs/submission_list.html', 'crs/submission_start.html',
]

# THE DEBT, AND WHY THE NUMBER IS MEASURED AND NOT DERIVED.
#     The first version of this constant was written as `103 - 33`: the
#     count of walking scripts, less the ones X0 converts. It was wrong,
#     and this gate caught it at 60 against a ceiling of 70. The 103 came
#     from a DIFFERENT detector - one that matched any script mentioning
#     pages/templates anywhere - while the gate counts scripts whose
#     WALKED ROOT is built from a template path. Two detectors, one
#     constant, and the arithmetic looked sound.
#
#     So it is measured with the gate's own detector, after the round, and
#     it may only FALL. Each later round that converts a census lowers it.
WALKERS_OWN_ROOT_MAX = 51

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


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def scripts():
    out = []
    for pat in ('test_*.py', 'apply_*.py', 'Show-*.py', 'probe_*.py'):
        for f in sorted(glob.glob(os.path.join(ROOT, pat))):
            if '.bak_' in f:
                continue
            out.append(os.path.basename(f))
    return out


def walks_own_root(text):
    """Calls os.walk on a root this file built from a template path.

    THE FIRST VERSION OF THIS ONLY LOOKED AT SCALARS, AND THE ROUND'S OWN
    GATE CAUGHT IT. It read `X = os.path.join(ROOT, 'pages', 'templates')`
    and stopped there, so it declared test_accent_shades and
    test_deeper_teal innocent - both of which walk

        SEARCH_DIRS = [os.path.join(ROOT, 'pages', 'templates'),
                       os.path.join(ROOT, 'pages', 'help_content'),
                       os.path.join(ROOT, 'static')]
        for d in SEARCH_DIRS:
            for dirpath, dirnames, filenames in os.walk(d):

    A LIST of roots, iterated. Exactly the same blind spot this round
    exists to close, committed inside the tool built to close it: the
    detector could not see a shape nobody had written it for. So the
    assignment is read across continuation lines, and a walk over any
    variable bound in a `for ... in <LIST>` counts too.
    """
    walked = set(re.findall(r'os\.walk\(\s*([A-Za-z_][\w.]*)\s*\)', text))
    holders = set()
    for v in walked:
        # The loop variable case: `for d in SEARCH_DIRS:` ... os.walk(d)
        holders.update(re.findall(r'^\s*for\s+%s\s+in\s+([A-Za-z_]\w*)\s*:'
                                  % re.escape(v), text, re.M))
    for v in walked | holders:
        m = re.search(r'^\s*%s\s*=\s*(.+?)(?=\n\S|\n\s*\n|\Z)'
                      % re.escape(v), text, re.M | re.S)
        if m and re.search(r'''['"]templates['"]''', m.group(1)):
            return True
    return False


print('=' * 74)
print('%s - X0, THE TEMPLATE TREE GETS ITS SECOND ROOT' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE TREE')
# ==========================================================================
rts = alv_tree.roots()
ok(len(rts) == 2, 'alv_tree knows 2 roots', [alv_tree.rel(r) or r for r in rts])
for parts, why in alv_tree.TEMPLATE_ROOTS:
    p = os.path.join(ROOT, *parts)
    ok(os.path.isdir(p), '  %-18s exists   (%s)' % ('/'.join(parts), why))

all_t = alv_tree.templates()
main = [p for p in all_t if os.path.join('pages', 'templates') in p]
crs = [p for p in all_t if os.path.join('crs', 'templates') in p]
ok(len(main) == MAIN_N, 'pages/templates holds %d templates' % MAIN_N,
   len(main))
ok(len(crs) == CRS_N, 'crs/templates holds %d - AND NO GATE HAD SEEN THEM'
   % CRS_N, len(crs))
ok(len(all_t) == TOTAL_N, 'the tree is %d templates, not %d'
   % (TOTAL_N, MAIN_N))
ok(sorted(alv_tree.rel(p) for p in crs) == CRS_PAGES,
   '  and they are the eight CRS Reporting screens',
   sorted(alv_tree.rel(p) for p in crs))

# THE FACT DOZENS OF OTHER SUITES DEPEND ON WITHOUT SAYING SO.
names = [os.path.basename(p) for p in all_t]
dupes = sorted({n for n in names if names.count(n) > 1})
ok(not dupes,
   'all %d basenames are DISTINCT - which is what lets every suite that '
   'keys its expectations by basename keep working across the wider tree'
   % len(names), dupes)

ok(alv_tree.rel(os.path.join(ROOT, 'crs', 'templates', 'crs', 'index.html'))
   == 'crs/index.html', 'rel() labels a CRS page below its own root')
ok(alv_tree.rel(os.path.join(ROOT, 'pages', 'templates', 'projects',
                             'project_gantt.html'))
   == 'projects/project_gantt.html', '  and a subdirectory page likewise')
ok(len(alv_tree.templates(include_base=False)) == TOTAL_N - 1,
   '  include_base=False drops exactly base.html')
ok(len(alv_tree.roots(SCRATCH)) == 0,
   'CONTROL: roots() on a tree with neither directory returns none, so a '
   'suite run against a scratch copy is not forced to invent them')
ok(len(list(alv_tree.walk3())[0]) == 3,
   'walk3 yields os.walk\'s own 3-tuple, so a converted loop keeps its '
   'arity and its variable names')

# ==========================================================================
head('2. THE 33 CONVERTED SUITES')
# ==========================================================================
CONVERT = alv_tree.CONVERTED
WAITING = alv_tree.WAITING
INDIRECT = alv_tree.WAITING_INDIRECT
ALREADY_WIDE = alv_tree.ALREADY_WIDE
# The fifth category, added by X11. A suite that carries the words
# os.walk in a string literal and never calls it - see
# alv_tree.MENTIONS_ONLY for why the crude test below was kept and
# the exception named instead.
MENTIONS = alv_tree.MENTIONS_ONLY

# X0's OWN THIRTY-THREE, PINNED - lesson 17.
#     This section checks that each converted suite imports alv_tree,
#     walks via walk3(), no longer builds a root, and carries a
#     .bak_treeroots backup. All four are true of the suites X0
#     converted, and the fourth cannot be true of any later round's -
#     X11's thirteen carry .bak_waitdown. Reading the live register here
#     made X0's suite fail the day X11 landed, with nothing wrong.
#
#     A suite asserts what ITS OWN round guarantees. The register belongs
#     to whichever round is last, and section 3 below keeps reading it
#     live, because catching the NEXT census that builds its own root is
#     the whole point of it.
MINE = [
    'test_accent_ink.py', 'test_action_bar.py', 'test_admin_banner.py',
    'test_admin_headings.py', 'test_admin_repair.py',
    'test_applies_from.py', 'test_avatar.py', 'test_console_encoding.py',
    'test_div_balance.py', 'test_entry_sections.py', 'test_filter_field.py',
    'test_filter_gap.py', 'test_finance_headings.py',
    'test_form_components.py', 'test_house_header.py', 'test_hub_bar.py',
    'test_label_fit.py', 'test_last_menus.py', 'test_map_provider.py',
    'test_more_css.py', 'test_more_menu.py', 'test_named_bars.py',
    'test_one_action_bar.py', 'test_page_title.py', 'test_palette.py',
    'test_print_buttons.py', 'test_report_head.py', 'test_row_personal.py',
    'test_secondary_visible.py', 'test_small_controls.py',
    'test_table_admin.py', 'test_tap_target.py', 'test_zoom_guards.py',
]

bad_imp, bad_walk, bad_rel = [], [], []
for n in MINE:
    t = read(os.path.join(ROOT, n))
    if not re.search(r'^import alv_tree$', t, re.M):
        bad_imp.append(n)
    if 'alv_tree.walk3()' not in t:
        bad_walk.append(n)
    if walks_own_root(t):
        bad_rel.append(n)
ok(len(MINE) == 33, '33 suites were converted', len(MINE))
ok(not set(MINE) - set(CONVERT),
   '  and all 33 are still on the live register',
   sorted(set(MINE) - set(CONVERT)))
ok(not bad_imp, '  every one imports alv_tree', bad_imp)
ok(not bad_walk, '  every one walks via alv_tree.walk3()', bad_walk)
ok(not bad_rel, '  and none still walks a root of its own', bad_rel)

ok(all(os.path.isfile(os.path.join(ROOT, n + SUFFIX)) for n in MINE),
   '  each has a %s backup' % SUFFIX,
   [n for n in MINE if not os.path.isfile(os.path.join(ROOT, n + SUFFIX))])

# CONTROL: the round is real. A backup must still walk the narrow root.
sample = MINE[0] + SUFFIX
if os.path.isfile(os.path.join(ROOT, sample)):
    ok(walks_own_root(read(os.path.join(ROOT, sample))),
       'CONTROL: reverting %s puts its own root back, so section 2 would '
       'FAIL - a revert is caught' % MINE[0])
else:
    skipped += 1
    print('  skip the revert control  (no backup yet)')

# ==========================================================================
head('3. EVERY WALKING SUITE IS ACCOUNTED FOR')
# ==========================================================================
walking = [n for n in scripts()
           if n.startswith('test_') and n != ME
           and 'os.walk(' in read(os.path.join(ROOT, n))]
known = (set(CONVERT) | set(WAITING) | set(INDIRECT)
         | set(ALREADY_WIDE) | set(MENTIONS))
orphans = sorted(set(walking) - known)
ok(not orphans,
   'every one of the %d walking suites is in exactly one list - converted, '
   'waiting on a named round, or already walking the repo' % len(walking),
   'NOT ACCOUNTED FOR: %s\n'
   '  A new census that builds its own pages/templates root lands here. '
   'That is the mistake X0 is paying for; add it to CONVERT if it passes '
   'with the wider tree, or to WAITING against the round that will let it.'
   % orphans)
lists = [set(CONVERT), set(WAITING), set(INDIRECT),
         set(ALREADY_WIDE), set(MENTIONS)]
overlap = sorted({n for i, a in enumerate(lists) for b in lists[i + 1:]
                  for n in a & b})
ok(not overlap, '  and in exactly one, not two', overlap)
missing = sorted(n for n in list(WAITING) + list(INDIRECT)
                 + list(MENTIONS) + ALREADY_WIDE
                 if not os.path.isfile(os.path.join(ROOT, n)))
ok(not missing, '  and every name in the register is a file that exists',
   missing)

# A suite on WAITING must still walk its own root. If someone converts one
# without taking it off the list, the register has started lying.
lying = [n for n in WAITING
         if not walks_own_root(read(os.path.join(ROOT, n)))]
ok(not lying,
   '  every WAITING suite still walks the narrow root - so the list cannot '
   'quietly rot into a list of things already done', lying)

print('')
print('  STILL WAITING ON THE CRS ROUNDS - %d suite(s):' % len(WAITING))
for n in sorted(WAITING):
    print('     %-28s %s' % (n.replace('.py', ''), WAITING[n]))

# ==========================================================================
head('4. THE DEBT, COUNTED AND FALLING')
# ==========================================================================
own = sorted(n for n in scripts()
             if n != ME and n != PATCHER
             and walks_own_root(read(os.path.join(ROOT, n))))
ok(len(own) <= WALKERS_OWN_ROOT_MAX,
   '%d script(s) still walk a hard-coded template root - the ceiling is %d '
   'and it may only FALL' % (len(own), WALKERS_OWN_ROOT_MAX),
   'If this rose, a new census built its own root. If it fell, lower '
   'WALKERS_OWN_ROOT_MAX in this file to lock the gain in.')
ok(len(own) == WALKERS_OWN_ROOT_MAX,
   '  and it is exactly %d, so the ceiling is not stale'
   % WALKERS_OWN_ROOT_MAX, len(own))

# ==========================================================================
head('5. CONTROLS, AND THE GATE')
# ==========================================================================
ok(walks_own_root("T = os.path.join(R, 'pages', 'templates')\n"
                  "for a, b, c in os.walk(T):\n    pass\n"),
   'the detector sees a root built from a templates path')
ok(not walks_own_root("R = os.path.dirname(__file__)\n"
                      "for a, b, c in os.walk(R):\n    pass\n"),
   '  and does NOT see one that walks the repo - which is why '
   'test_banner_pages and test_standards_block are left alone')
ok(not walks_own_root('for a, b, c in alv_tree.walk3():\n    pass\n'),
   '  and does not see a converted loop')

# THE ONE THE FIRST DRAFT GOT WRONG. Keep it executable so it cannot be
# got wrong again.
ok(walks_own_root("DIRS = [os.path.join(R, 'pages', 'templates'),\n"
                  "        os.path.join(R, 'static')]\n"
                  "for d in DIRS:\n"
                  "    for a, b, c in os.walk(d):\n        pass\n"),
   '  and it DOES see a root inside a list that is iterated - the shape '
   'the first draft of this detector was blind to, which is the same '
   'mistake as the one the whole round is paying for')

# And the patcher must refuse that shape rather than convert it: walk3()
# covers the template tree only, so converting a SEARCH_DIRS walk would
# silently drop help_content and static.
src = read(os.path.join(ROOT, PATCHER))
ok("rhs.lstrip().startswith(('[', '('))" in src,
   'the patcher REFUSES a list-shaped root instead of converting it',
   'apply_tree_roots.template_var must not turn a walk over '
   '[templates, help_content, static] into a walk over templates alone')

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
if ROUNDS and SUFFIX in ROUNDS and '.bak_filtergap' in ROUNDS:
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_filtergap'),
       '  and after the round before it (lesson 54)', ROUNDS[-3:])
ps1 = read(os.path.join(ROOT, PS1)) if os.path.isfile(PS1) else ''
ok(ME in ps1, '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)
ok(os.path.isfile(os.path.join(ROOT, 'alv_tree.py')),
   'alv_tree.py is beside this suite')

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  WHAT THIS ROUND DOES NOT DO: it does not make one CRS pixel')
print('  different. It makes the module VISIBLE to %d of this programme\'s'
      % len(CONVERT))
print('  suites, and it names the %d standards it fails against the rounds'
      % len(WAITING))
print('  that will fix them. The green Demetri reported is X1 onwards.')
print('=' * 74)
sys.exit(1 if failed else 0)
