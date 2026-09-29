# -*- coding: utf-8 -*-
"""test_waiting_down.py - Section X round X11, 29 Sep 2026.

WHAT THIS ROUND DID, AND THEREFORE WHAT THIS SUITE JUDGES.

    1. alv_tree.join() - the way back. X0 widened the walk and the label
       and left 155 sites reading os.path.join(T, rel) with T fixed at
       pages/templates, so a CRS label resolved to a path that cannot
       exist. One of them crashed the laptop's gate on 28 Sep. All 155
       are converted here.

    2. Thirteen suites off WAITING and onto CONVERTED - each RUN against
       the wide tree first, each passing.

    3. The register rewritten: 46 converted, 14 waiting, 1 indirect, and
       not one of the fifteen reasons blames CRS any more, because not
       one of them is blocked by CRS any more.

    4. X0's own suite stopped asserting the register and started
       asserting its own 33 (lesson 17).

    5. The debt ceiling 64 -> 51, measured with X0's detector.

THE CONTROL THAT MATTERS IS SECTION 6. A gate that cannot see a failure
reports success, so this suite proves the bug it fixed is real: the path
os.path.join(pages_root, 'crs/index.html') is NOT a file, and
alv_tree.join('crs/index.html') IS. If the first ever becomes a file this
suite says so, because then the whole premise moved.

NOT PROVED HERE: that the fifteen still on WAITING are blocked by exactly
what their reasons say. Those reasons were re-measured by running the
suites; a reason is prose, and prose cannot be gated.
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
import ast
import glob
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)

SUFFIX = '.bak_waitdown'
ME = 'test_waiting_down.py'
PATCHER = 'apply_waiting_down.py'
X0_SUITE = 'test_tree_roots.py'
PS1 = 'Push-PendingChanges.ps1'

CONVERTED_N = 46
WAITING_N = 14
INDIRECT_N = 1
CEILING = 51
JOINS_IN_X0 = 155      # dormant in the 26 X0 had already widened
JOINS_IN_FREED = 38    # in the thirteen this round widens
JOINS_CLOSED = JOINS_IN_X0 + JOINS_IN_FREED

FREED = [
    'test_accent_shades.py', 'test_bar_top.py', 'test_body_backs.py',
    'test_deeper_teal.py', 'test_entry_headings.py', 'test_entry_panel.py',
    'test_heading_components.py', 'test_heading_prefix.py',
    'test_heading_standard.py', 'test_panel_title.py',
    'test_projects_heading.py', 'test_required_sweep.py',
    'test_save_and_cancel.py',
]
LISTY = ['test_accent_shades.py', 'test_deeper_teal.py']

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
            if '.bak_' not in f:
                out.append(os.path.basename(f))
    return out


def joins_T(text):
    return len(re.findall(r'os\.path\.join\(\s*T\s*,', text))


def walks_own_root(text):
    """X0's detector, verbatim, so section 5 measures what X0's gate
    measures. Two detectors and one constant is how X0's first ceiling
    came out wrong."""
    walked = set(re.findall(r'os\.walk\(\s*([A-Za-z_][\w.]*)\s*\)', text))
    holders = set()
    for v in walked:
        holders.update(re.findall(r'^\s*for\s+%s\s+in\s+([A-Za-z_]\w*)\s*:'
                                  % re.escape(v), text, re.M))
    for v in walked | holders:
        m = re.search(r'^\s*%s\s*=\s*(.+?)(?=\n\S|\n\s*\n|\Z)'
                      % re.escape(v), text, re.M | re.S)
        if m and re.search(r'''['"]templates['"]''', m.group(1)):
            return True
    return False


print('=' * 74)
print('%s - X11, THE REGISTER STARTS COMING DOWN' % ME)
print('=' * 74)

# ==========================================================================
head('1. alv_tree.join() - THE WAY BACK')
# ==========================================================================
ok(hasattr(alv_tree, 'join'), 'alv_tree has join()')
rts = alv_tree.roots()
pages_root, crs_root = rts[0], rts[1]

ok(alv_tree.join('properties.html') == os.path.join(pages_root,
                                                    'properties.html'),
   'a pages label answers EXACTLY what os.path.join(T, ...) answered - the '
   'pages side does not move', alv_tree.join('properties.html'))
ok(alv_tree.join('crs/index.html') == os.path.join(
       crs_root, 'crs', 'index.html'),
   'a CRS label answers the file in the CRS app, which is the bug',
   alv_tree.join('crs/index.html'))
ok(os.path.isfile(alv_tree.join('crs/index.html')),
   '  and that answer is a file that exists')
ok(alv_tree.join('projects', 'project_task_list.html')
   == os.path.join(pages_root, 'projects', 'project_task_list.html'),
   'several parts join as os.path.join does')
ok(alv_tree.join('projects/project_task_list.html')
   == alv_tree.join('projects', 'project_task_list.html'),
   '  and a forward-slash label is the same answer, because the callers '
   'hand it both')

# THE FORGIVING PART, WHICH IS THE WHOLE REASON join() IS NOT path_of().
missing = alv_tree.join('no_such_template.html')
ok(missing == os.path.join(pages_root, 'no_such_template.html'),
   'a label no root holds answers the FIRST root - so the dozens of sites '
   'that ask os.path.exists() get False, not a crash', missing)
ok(not os.path.exists(missing), '  and exists() duly says False')
raised = False
try:
    alv_tree.path_of('no_such_template.html')
except IOError:
    raised = True
ok(raised, '  while path_of() still RAISES on the same label, because it is '
   'for code asserting a fact, not asking a question')

ok(alv_tree.join('crs/index.html') == alv_tree.path_of('crs/index.html'),
   'for a file that IS there the two agree exactly')

# ==========================================================================
head('2. THE THIRTEEN, FREED')
# ==========================================================================
ok(len(FREED) == 13, 'this round names 13 suites', len(FREED))
no_imp, still_walks, still_joins, not_wide, no_bak = [], [], [], [], []
for n in FREED:
    t = read(os.path.join(ROOT, n))
    if not re.search(r'^import alv_tree$', t, re.M):
        no_imp.append(n)
    if walks_own_root(t):
        still_walks.append(n)
    if joins_T(t):
        still_joins.append(n)
    wide = ('alv_tree.walk3()' in t) or ('alv_tree.roots()' in t)
    if not wide:
        not_wide.append(n)
    if not os.path.isfile(os.path.join(ROOT, n + SUFFIX)):
        no_bak.append(n)
ok(not no_imp, '  every one imports alv_tree', no_imp)
ok(not not_wide, '  every one reaches the tree through alv_tree', not_wide)
ok(not still_walks, '  and none still walks a root of its own', still_walks)
ok(not still_joins, '  and none still joins onto T', still_joins)
ok(not no_bak, '  each has a %s backup' % SUFFIX, no_bak)

# The two X0 refused, and the shape it refused them for.
for n in LISTY:
    t = read(os.path.join(ROOT, n))
    ok('SEARCH_DIRS = alv_tree.roots() + [' in t,
       '  %-22s has its LIST widened, not replaced' % n.replace('.py', ''))
    ok('help_content' in t and 'static' in t,
       '    and still covers help_content and static, which walk3() would '
       'have silently dropped')

ok(set(FREED) <= set(alv_tree.CONVERTED),
   '  all thirteen are on CONVERTED now',
   sorted(set(FREED) - set(alv_tree.CONVERTED)))
ok(not (set(FREED) & (set(alv_tree.WAITING) | set(alv_tree.WAITING_INDIRECT))),
   '  and none is still on WAITING',
   sorted(set(FREED) & set(alv_tree.WAITING)))

# ==========================================================================
head('3. NOT ONE DORMANT LOOKUP LEFT IN THE WIDE TREE')
# ==========================================================================
offenders = {}
for n in alv_tree.CONVERTED:
    c = joins_T(read(os.path.join(ROOT, n)))
    if c:
        offenders[n] = c
ok(not offenders,
   'no suite that walks the WIDE tree still resolves a label against the '
   'narrow root - all %d sites are closed (%d dormant in the 26 X0 had '
   'already widened, %d in the thirteen freed here)'
   % (JOINS_CLOSED, JOINS_IN_X0, JOINS_IN_FREED),
   '\n'.join('%s x%d' % (k, v) for k, v in sorted(offenders.items())))

was_x0 = was_freed = 0
for n in alv_tree.CONVERTED:
    b = os.path.join(ROOT, n + SUFFIX)
    if os.path.isfile(b):
        if n in FREED:
            was_freed += joins_T(read(b))
        else:
            was_x0 += joins_T(read(b))
ok(was_x0 == JOINS_IN_X0,
   '  and the backups prove the %d, so the number is not a story'
   % JOINS_IN_X0, was_x0)
ok(was_freed == JOINS_IN_FREED,
   '  and the %d in the thirteen too' % JOINS_IN_FREED, was_freed)

# ==========================================================================
head('4. THE REGISTER, AND WHAT IT SAYS NOW')
# ==========================================================================
ok(len(alv_tree.CONVERTED) == CONVERTED_N, 'CONVERTED holds %d'
   % CONVERTED_N, len(alv_tree.CONVERTED))
ok(len(alv_tree.WAITING) == WAITING_N, 'WAITING holds %d' % WAITING_N,
   len(alv_tree.WAITING))
ok(len(alv_tree.WAITING_INDIRECT) == INDIRECT_N, 'WAITING_INDIRECT holds %d'
   % INDIRECT_N, len(alv_tree.WAITING_INDIRECT))
lists = [set(alv_tree.CONVERTED), set(alv_tree.WAITING),
         set(alv_tree.WAITING_INDIRECT), set(alv_tree.ALREADY_WIDE)]
overlap = sorted({n for i, a in enumerate(lists) for b in lists[i + 1:]
                  for n in a & b})
ok(not overlap, '  and every name is on exactly one list', overlap)
gone = sorted(n for n in (list(alv_tree.CONVERTED) + list(alv_tree.WAITING)
                          + list(alv_tree.WAITING_INDIRECT)
                          + alv_tree.ALREADY_WIDE)
              if not os.path.isfile(os.path.join(ROOT, n)))
ok(not gone, '  and every name is a file that exists', gone)

# THE REASONS. Ten CRS rounds landed; a register that still blames CRS
# sends the next reader to the wrong module.
blames = sorted(n for n, why in list(alv_tree.WAITING.items())
                + list(alv_tree.WAITING_INDIRECT.items())
                if 'CRS' in why)
ok(not blames,
   'not one of the %d held reasons blames CRS any more - every one was '
   're-measured by running the suite' % (WAITING_N + INDIRECT_N), blames)

lying = [n for n in alv_tree.WAITING
         if not walks_own_root(read(os.path.join(ROOT, n)))]
ok(not lying, '  and every suite still on WAITING really does still walk '
   'the narrow root', lying)

print('')
print('  STILL HELD - %d, none of them on CRS:' % (WAITING_N + INDIRECT_N))
for n in sorted(list(alv_tree.WAITING) + list(alv_tree.WAITING_INDIRECT)):
    why = alv_tree.WAITING.get(n) or alv_tree.WAITING_INDIRECT[n]
    print('     %-26s %s' % (n.replace('.py', ''), why.replace('\n', ' ')))

# ==========================================================================
head('5. THE DEBT, LOWER')
# ==========================================================================
own = sorted(n for n in scripts()
             if n not in (X0_SUITE, 'apply_tree_roots.py', ME, PATCHER)
             and walks_own_root(read(os.path.join(ROOT, n))))
ok(len(own) == CEILING,
   '%d script(s) still walk a hard-coded template root' % CEILING, len(own))
x0 = read(os.path.join(ROOT, X0_SUITE))
ok('WALKERS_OWN_ROOT_MAX = %d' % CEILING in x0,
   "  and X0's gate has been lowered to the same %d, so the gain is locked "
   'in' % CEILING,
   re.findall(r'WALKERS_OWN_ROOT_MAX = \d+', x0))
ok('WALKERS_OWN_ROOT_MAX = 64' not in x0,
   '  and the old 64 is gone, not commented out beside it')
left = [n for n in own if n.startswith('test_')]
ok(len(left) == WAITING_N,
   '  of what is left, %d are suites - exactly the WAITING list - and the '
   'rest are the historical patchers and Show- scripts, which walked what '
   'they walked' % WAITING_N, left)

# ==========================================================================
head("6. THE BUG WAS REAL - and X0's SUITE JUDGES ITS OWN 33")
# ==========================================================================
bad = os.path.join(pages_root, 'crs', 'index.html')
ok(not os.path.exists(bad),
   'os.path.join(pages_root, crs/index.html) is NOT a file - which is what '
   'every one of the 155 sites was computing', bad)
ok(os.path.isfile(alv_tree.join('crs/index.html')),
   '  and join() answers one that is, so the fix is the difference between '
   'those two lines')

ok('MINE = [' in x0, "X0's suite pins its own 33 as MINE")
m = re.search(r'^MINE = \[(.*?)^\]', x0, re.M | re.S)
mine = sorted(re.findall(r"'([^']+\.py)'", m.group(1))) if m else []
ok(len(mine) == 33, '  and MINE holds 33 names', len(mine))
ok(set(mine) <= set(alv_tree.CONVERTED),
   '  all of which are still on the live register',
   sorted(set(mine) - set(alv_tree.CONVERTED)))
ok(not (set(mine) & set(FREED)),
   "  and none of them is one of X11's thirteen - X0 judges X0's work",
   sorted(set(mine) & set(FREED)))
ok('for n in MINE:' in x0 and 'ok(len(MINE) == 33' in x0,
   '  section 2 of it now reads MINE, not the register')
ok('known = (set(CONVERT)' in x0,
   '  while section 3 keeps reading the LIVE register, which is the part '
   'that catches the next census that builds its own root')

# ==========================================================================
head('7. THE FIFTH CATEGORY, AND WHY THE NET STAYED CRUDE')
# ==========================================================================
# X0's section 3 finds a walking suite with a plain substring test, and
# fails if one is on none of the register's lists. THIS SUITE LANDED IN IT:
# it carries the words os.walk in two string literals - the detector it
# borrows from X0, and the CONTROL that proves the detector works.
#
# The cheap fix was to make the substring test cleverer. That would have
# traded a net that catches shapes nobody has thought of for one that
# catches only the shapes we have. X0's detector was once too clever and
# went blind to a list of roots - the exact blind spot X0 existed to close.
# So the net stays crude and the exception is named.
ok(hasattr(alv_tree, 'MENTIONS_ONLY'),
   'alv_tree has a fifth list, MENTIONS_ONLY')
ok(ME in getattr(alv_tree, 'MENTIONS_ONLY', {}),
   '  and this suite is on it, accounted for rather than excused')

mine_src = read(os.path.join(ROOT, ME))
ok(len(re.findall(r'os\.walk\(', mine_src)) >= 2,
   '  the words really are in here, twice, which is why it was caught',
   len(re.findall(r'os\.walk\(', mine_src)))
calls = [n for n in ast.walk(ast.parse(mine_src))
         if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
         and n.func.attr == 'walk'
         and getattr(n.func.value, 'id', '') == 'os']
ok(not calls,
   '  and the PARSE TREE says it never calls os.walk - measured from the '
   'tree, not from reading itself', ['line %d' % c.lineno for c in calls])

crude = [n for n in scripts()
         if n.startswith('test_') and 'os.walk(' in read(os.path.join(ROOT, n))]
known = (set(alv_tree.CONVERTED) | set(alv_tree.WAITING)
         | set(alv_tree.WAITING_INDIRECT) | set(alv_tree.ALREADY_WIDE)
         | set(alv_tree.MENTIONS_ONLY) | {X0_SUITE})
ok(not sorted(set(crude) - known),
   'every one of the %d suites the crude test finds is on exactly one of '
   'the five lists' % len(crude), sorted(set(crude) - known))
ok('MENTIONS = alv_tree.MENTIONS_ONLY' in x0,
   "  and X0's suite reads the fifth list, so it agrees")

# ==========================================================================
head('8. CONTROLS, AND THE GATE')
# ==========================================================================
sample = 'test_page_title.py'
b = os.path.join(ROOT, sample + SUFFIX)
if os.path.isfile(b):
    ok(joins_T(read(b)) == 21,
       'CONTROL: reverting %s puts its 21 narrow lookups back, so section 3 '
       'would FAIL - a revert is caught' % sample.replace('.py', ''),
       joins_T(read(b)))
else:
    skipped += 1
    print('  skip the revert control  (no backup yet)')

b = os.path.join(ROOT, 'test_bar_top.py' + SUFFIX)
if os.path.isfile(b):
    ok(walks_own_root(read(b)),
       'CONTROL: and reverting test_bar_top puts its own root back, so '
       'section 2 would FAIL too')
else:
    skipped += 1
    print('  skip the second revert control  (no backup yet)')

ok(joins_T("p = os.path.join(T, rel)") == 1,
   'CONTROL: the detector this suite counts with does find the shape it is '
   'counting')
ok(joins_T("p = alv_tree.join(rel)") == 0,
   '  and does not find it in the converted shape')
ok(walks_own_root("T = os.path.join(ROOT, 'pages', 'templates')\n"
                  "for d, s, f in os.walk(T):\n    pass\n"),
   "CONTROL: X0's detector finds a narrow walk")
ok(not walks_own_root("for d, s, f in alv_tree.walk3():\n    pass\n"),
   '  and does not find one in a widened suite')

ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(ME in t, 'this suite is on the gate  %s' % PS1)
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the PATCHER is not - a gate runs suites, not rounds')
else:
    skipped += 2
    print('  skip the gate checks  (%s not staged)' % PS1)

try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS, so a later '
       'round editing these files cannot break an earlier suite' % SUFFIX)
    # NOT "and it is the last entry". It was, for about an hour, and then
    # X12 appended one - and this line failed with nothing wrong, which is
    # lesson 17 landing inside the suite that was written to explain
    # lesson 17. What X11 guarantees is its PLACE: after every round that
    # existed when it landed. Where the list ends belongs to whoever is
    # last, and that will never be this round again.
    ok(ROUNDS.count(SUFFIX) == 1, '  exactly once', ROUNDS.count(SUFFIX))
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_crsdetr'),
       '  and after .bak_crsdetr, the last round that existed when X11 '
       'landed - which is the ordering as_left_by() actually needs',
       '%d vs %d' % (ROUNDS.index(SUFFIX), ROUNDS.index('.bak_crsdetr')))
except Exception as e:
    failed += 1
    print('  FAIL alv_rounds could not be read: %s' % e)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('')
print('  NOT PROVED HERE: that the fifteen reasons still on the register')
print('  are accurate. They were re-measured by running the suites, and')
print('  prose cannot be gated - only the absence of the word CRS can.')
print('=' * 74)
sys.exit(1 if failed else 0)
