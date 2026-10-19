# -*- coding: utf-8 -*-
"""test_retired.py - round RT-1, 18 Oct 2026.

WHAT THE TREE DOES WITH A PAGE IT USED TO HAVE.

MN-1 retired four meal-plan templates and EIGHTY OF THE 370 SUITES WENT
RED - not one of them on the planner. They were historical rounds whose
censuses still counted a page the tree no longer has.

    A census of what a round did is a claim about the past. Reading it
    off today's disk is correct only while the past is still on the
    disk.

THE CLAIM THIS SUITE EXISTS TO MAKE IS SECTION 6. Twenty-two of those
suites were re-aimed and NOT ONE DIGIT IN THEM MOVED, because the rounds
they describe did what they did whatever the tree does next. Thirty
others moved a number, every one of them a count of the tree as it
stands, and every one carrying a sentence saying what left with the page.
A suite that drifts from one list to the other fails here, which is the
point: the next round that files a historical number down has to come
past this check.

Sections 1 to 5 are the machinery that made that possible - the
register, the accessors, the two calls alv_rounds.as_left_by gained, and
touched_by, which applies Demetri's pre-flight rule to a census:
enumerate from the .bak files on disk, never from a list.

Section 10 is the control. Every claim above is re-asked of alv_tree and
alv_rounds AS THIS ROUND FOUND THEM, where every one must fail.
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
import importlib.util
import io
import os
import re
import subprocess
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

import alv_tree                                               # noqa: E402
import alv_rounds                                             # noqa: E402

SUFFIX = '.bak_retired'
ME = 'test_retired.py'
PATCHER = 'apply_retired.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
IMPACT = 'alv_impact.py'
RA = 'alv_rowactions.py'
MARK = 'RT-1, 18 Oct 2026'

GONE = ('meal_plans.html', 'meal_plan_calendar.html',
        'create_meal_plan.html', 'view_meal_plan.html')

# THE TWO LISTS THIS ROUND IS ABOUT, AND THE CLAIM IS THE SPLIT.
#
# Twenty-two historical suites were re-aimed and NOT ONE DIGIT IN THEM
# MOVED. That is the whole thesis: a census of what a round did is a
# claim about the past, and the past did not change when four pages left
# the tree. Twenty-eight others DID move, every one of them a count of
# the tree as it stands - and each carries a note in its own file saying
# what left with the page, so that nobody later reads the smaller number
# as the round's own size.
#
# Both lists are asserted below by comparing each suite against its own
# .bak_retired backup, with comments blanked. A suite that drifts from
# one list to the other fails here, which is the point: the next round
# that files a historical number down has to come past this check.
KEPT = (
    'test_accent_ink.py', 'test_action_bar.py', 'test_back_label.py',
    'test_bar_top.py', 'test_btn_tone.py', 'test_colour_good_bad.py',
    'test_colour_neutrals.py', 'test_colour_tail.py',
    'test_colour_tokens.py', 'test_dr2_values.py',
    'test_entry_sections.py', 'test_js_escape.py', 'test_label_weight.py',
    'test_meal_plan_buttons.py', 'test_more_css.py',
    'test_page_title.py', 'test_personal_heads.py',
    'test_recipe_photos.py', 'test_recipe_spice.py', 'test_retone.py',
    'test_user_slash.py', 'test_zoom_guards.py',
)
MOVED = (
    'test_crs_print.py', 'test_css_order.py', 'test_css_standalone.py',
    'test_cssrules_outside.py', 'test_custom_control.py',
    'test_dead_files.py', 'test_drift_root.py', 'test_from_calendar.py',
    'test_heading_standard.py', 'test_help_label.py',
    'test_house_title.py', 'test_important_base.py', 'test_js_buttons.py',
    'test_last_menus.py', 'test_lazy_images.py', 'test_modal_heads2.py',
    'test_more_menu.py', 'test_neutrals.py', 'test_pair_contrast.py',
    'test_radius_token.py',
    'test_recipe_side_b.py', 'test_recipe_tones.py',
    'test_row_action_order.py', 'test_row_exempt.py', 'test_row_wrap.py',
    'test_subtree_tones.py', 'test_surface_border.py',
    'test_surface_deep.py', 'test_tree_roots.py',
    'test_vocabulary.py',
)
N_DEAD_SENTINELS = 16

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
            for line in str(detail).splitlines()[:6]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def head(t):
    print('\n' + '=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def was(p):
    """The file as THIS round found it - its .bak_retired backup."""
    b = p + SUFFIX
    return read(b) if os.path.isfile(b) else ''


def digits(text):
    """Every integer literal in the CODE, comments blanked.

    python_code_only is the house stripper and it is load-bearing here:
    this round writes a great many comments that quote the numbers they
    explain - "(was 96)", "142 - 4 + 1" - and to a substring search a
    comment about a number is a number.
    """
    return re.findall(r'(?<![\w.])\d+(?![\w.])',
                      alv_tree.python_code_only(text, payloads=True))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. THE REGISTER SAYS WHAT IS TRUE OF THE DISK')
# ==========================================================================
ok(hasattr(alv_tree, 'RETIRED'), 'alv_tree carries the register')
ok(sorted(alv_tree.RETIRED) == sorted(GONE),
   'it names the four pages MN-1 retired, and no others',
   sorted(alv_tree.RETIRED))
for label, (suf, why) in sorted(alv_tree.RETIRED.items()):
    live = [os.path.join(r, label) for r in alv_tree.roots()
            if os.path.isfile(os.path.join(r, label))]
    ok(not live, '%-26s really is gone from the tree' % label, live)
    bak = [r for r in alv_tree.roots()
           if os.path.isfile(os.path.join(r, label) + suf)]
    ok(bak, '  and its %s is beside the hole it left' % suf)
    ok(re.match(r'^[A-Z]+-\d+[a-z]?, \d+ \w+ 20\d\d - ', why),
       '  and the reason names a round and a date', why)
ok(sorted(alv_tree.retired_labels()) == sorted(GONE),
   'retired_labels() agrees, and it asks the DISK rather than the '
   'register - a page put back stops being counted the moment it returns',
   alv_tree.retired_labels())

# ==========================================================================
head('2. THE ACCESSORS, EACH ON A LIVE PAGE AND A RETIRED ONE')
# ==========================================================================
LIVE = 'properties.html'
DEAD = 'create_meal_plan.html'

ok(os.path.basename(alv_tree.last_path(LIVE)) == LIVE,
   'last_path on a live page is the page',
   alv_tree.last_path(LIVE))
ok(os.path.basename(alv_tree.last_path(DEAD)) == DEAD + '.bak_planner',
   'last_path on a retired page is the text beside the hole',
   alv_tree.last_path(DEAD))
try:
    alv_tree.last_path('not_a_page_at_all.html')
    ok(False, 'last_path REFUSES a label that is neither')
except IOError as e:
    ok('not in RETIRED either' in str(e),
       'last_path REFUSES a label that is neither, and says so', str(e))

ok(alv_tree.nominal(alv_tree.last_path(DEAD))
   == alv_tree.join(DEAD),
   'nominal takes the retirement suffix back off')
ok(alv_tree.nominal(alv_tree.last_path(LIVE))
   == alv_tree.last_path(LIVE),
   '  and leaves a live page alone')

ok(os.path.basename(alv_tree.bak_path(alv_tree.last_path(DEAD),
                                      '.bak_lblwt'))
   == DEAD + '.bak_lblwt',
   'bak_path finds a retired page backup, not a backup of its backup')
ok(os.path.isfile(alv_tree.bak_of(DEAD, '.bak_lblwt')),
   '  and bak_of does it from the label, which is where a suite starts')

ok(os.path.basename(alv_tree.last_join(DEAD))
   == DEAD + '.bak_planner',
   'last_join resolves a retired page')
ok(not os.path.isfile(alv_tree.last_join('still_not_a_page.html')),
   '  and stays FORGIVING for a label that was never there - isfile() '
   'answers False, which is what every guard built on join() asks')

# ==========================================================================
head('3. path_of STILL REFUSES, AND NOW IT SAYS WHO TOOK THE PAGE')
# ==========================================================================
try:
    alv_tree.path_of(DEAD)
    ok(False, 'path_of refuses a retired label')
except IOError as e:
    ok('was retired by' in str(e) and 'MN-1' in str(e),
       'path_of refuses a retired label and names the round that took it')
    ok('last_path' in str(e),
       '  and says which accessor a historical claim should use instead')
try:
    alv_tree.path_of('nope_not_here.html')
    ok(False, 'and it still refuses an ordinary typo')
except IOError as e:
    ok('no template named' in str(e),
       '  and it still refuses an ordinary typo, in the old words')

# ==========================================================================
head('4. THE ONE SHARED WALK - alv_rounds.as_left_by')
# ==========================================================================
# SIXTY-ODD SUITES READ A PAGE THROUGH THIS AS now(). The two calls it
# gained are the reason most of this round was one line per suite.
nom = alv_tree.join(DEAD)
by_nominal = alv_rounds.as_left_by(nom, '.bak_lblwt', read)
by_last = alv_rounds.as_left_by(alv_tree.last_path(DEAD),
                                '.bak_lblwt', read)
ok(by_nominal == by_last and by_nominal,
   'it answers the same text whether it is handed the page or its last '
   'text', '%d and %d bytes' % (len(by_nominal), len(by_last)))
# AND THE END OF THE WALK READS SOMETHING. The last suffix in ROUNDS has
# no later round, so this is the branch that used to read the file.
ok(alv_rounds.as_left_by(nom, alv_rounds.ROUNDS[-1], read),
   '  and the END of the walk reads the last text, not a missing file')

# ==========================================================================
head('5. touched_by - A ROUND ENUMERATES FROM ITS OWN BACKUPS')
# ==========================================================================
# THE SAME RULE THE PRE-FLIGHT LIVES BY, applied to a census.
for suf in ('.bak_coltok', '.bak_lblwt'):
    by_disk = set(alv_tree.touched_by(suf))
    by_walk = set(p for p in alv_tree.templates()
                  if os.path.isfile(p + suf))
    ok(by_walk < by_disk,
       '%s: the walk sees %d page(s), the backups %d'
       % (suf, len(by_walk), len(by_disk)))
    ok(all(os.path.isfile(p + suf) for p in by_disk),
       '  and every page it names really carries that backup')
    missed = sorted(os.path.basename(p) for p in by_disk - by_walk)
    ok(all(n in GONE for n in missed),
       '  and the only pages the walk missed are the retired ones',
       missed)

# ==========================================================================
head('6. NOT ONE NUMBER MOVED IN THE 22 HISTORICAL SUITES')
# ==========================================================================
# THIS IS THE ROUND. Everything above is machinery; this is the claim the
# machinery exists to make true.
drifted = []
for name in KEPT:
    p = os.path.join(ROOT, name)
    old = was(p)
    if not old:
        skip('%-28s every number unchanged' % name, 'no backup')
        continue
    a, b = digits(old), digits(read(p))
    if a != b:
        diff = [(x, y) for x, y in zip(a, b) if x != y][:3]
        drifted.append('%s: %s' % (name, diff or '%d vs %d literals'
                                   % (len(a), len(b))))
ok(not drifted, 'all %d historical suites keep every integer they had'
   % len(KEPT), '\n'.join(drifted))
print('        A census of what a round did is a claim about the past.')
print('        Reading it off today\'s disk is correct only while the')
print('        past is still on the disk.')

# AND THE ONES THAT DID MOVE, MOVED - which is what makes the list above
# a finding rather than a tautology. A round that changed nothing would
# pass section 6 by doing nothing.
still = []
for name in MOVED:
    p = os.path.join(ROOT, name)
    old = was(p)
    if not old:
        skip('%-28s a number moved' % name, 'no backup')
        continue
    if digits(old) == digits(read(p)):
        still.append(name)
ok(not still, 'CONTROL: and all %d present-tense suites really did move '
   'a number' % len(MOVED), still)

# EVERY ONE OF THEM SAYS SO IN ITS OWN FILE. A number that changes
# without a sentence beside it is the thing this programme keeps paying
# for, so the mark is asserted, not hoped for.
unmarked = [n for n in MOVED
            if MARK not in read(os.path.join(ROOT, n))]
ok(not unmarked,
   '  and every one carries this round\'s mark where the number changed',
   unmarked)

# ==========================================================================
head('7. THE SIXTEEN DEAD SENTINELS')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
old_ps = was(os.path.join(ROOT, PS1))
rows = re.findall(r"(?m)^\s*@\{\s*File\s*=\s*'([^']+)'", ps)
old_rows = re.findall(r"(?m)^\s*@\{\s*File\s*=\s*'([^']+)'", old_ps)
dead_now = [f for f in rows
            if os.path.basename(f.replace('\\', '/')) in GONE]
dead_was = [f for f in old_rows
            if os.path.basename(f.replace('\\', '/')) in GONE]
ok(not dead_now, 'not one sentinel row names a retired page', dead_now)
ok(len(dead_was) == N_DEAD_SENTINELS,
   'CONTROL: there were %d of them before this round' % N_DEAD_SENTINELS,
   len(dead_was))
# EVERY LIVE ROW SURVIVED, which is the precise claim and the one that
# does not go stale. The net total moved by fourteen and not sixteen,
# because MH-2 adds two rows of its own in the same push - so a check on
# the TOTAL would fail on a round that did exactly what it said.
lost = [f for f in old_rows if f not in rows
        and os.path.basename(f.replace('\\', '/')) not in GONE]
ok(not lost, '  and not one row on a page that is still there went with '
   'them', lost)
ok(len(old_rows) - len(rows) >= N_DEAD_SENTINELS - 2,
   '  the table is %d rows, down from %d' % (len(rows), len(old_rows)))
print('        A sentinel on a retired page is the push script')
print('        asserting the shape of a file nothing serves - which is')
print('        the failure -Message and -Checks were built to prevent.')

# ==========================================================================
head('8. THE SELECTOR READS BOTH HALVES OF AN INSTRUMENT')
# ==========================================================================
impact = load(os.path.join(ROOT, IMPACT), '_alv_impact_rt1')
ok(hasattr(impact, 'patcher_of'), 'alv_impact gained patcher_of')
ok(os.path.basename(impact.patcher_of('test_recipe_side_b.py') or '')
   == 'apply_recipe_side_b.py',
   '  and it finds a suite\'s patcher beside it')
four = ['pages/templates/%s' % n for n in GONE]
picked, _named, _wide = impact.select(four)

old_src = was(os.path.join(ROOT, IMPACT))
if not old_src:
    skip('CONTROL: the old selector could not see them', 'no backup')
else:
    ns = {'__name__': '_impact_before', '__file__':
          os.path.join(ROOT, IMPACT)}
    exec(compile(old_src, IMPACT, 'exec'), ns)
    before, _n, _w = ns['select'](four)
    extra = sorted(set(picked) - set(before))
    ok(extra, 'reading the patchers finds %d suite(s) the old selector '
       'could not see' % len(extra), extra)
    ok('test_recipe_side_b.py' in extra,
       '  including test_recipe_side_b.py, which never WRITES the name - '
       'it reads apply_recipe_side_b.EDITS at run time')
    ok(set(before) < set(picked),
       '  and it loses none of what the old one found')

# ==========================================================================
head('9. THE EXEMPTIONS THAT CAME OFF, RATHER THAN MOVING TO A BACKUP')
# ==========================================================================
# AN EXEMPTION FOR A PAGE NOBODY CAN REACH IS A LINE NOBODY CAN CHECK.
# Three of them went for that one reason, and the argument is the same
# each time: these registers name a control a reader can find and a
# report can print.
ra = load(os.path.join(ROOT, RA), '_alv_rowactions_rt1')
ok(not any(n in ra.NAMED for n in GONE),
   'alv_rowactions.NAMED names no retired page', sorted(ra.NAMED))
ok(all(alv_tree.path_of(n) for n in ra.NAMED),
   '  and every page it DOES name is in this checkout - path_of, which '
   'refuses a retired one')
old_ra = was(os.path.join(ROOT, RA))
ok(old_ra and 'create_meal_plan.html' in old_ra,
   'CONTROL: it named create_meal_plan.html before this round')

pc = read(os.path.join(ROOT, 'test_pair_contrast.py'))
ok('.recipe-selector-card-placeholder' not in
   alv_tree.python_code_only(pc, payloads=True),
   'the WCAG inactive-control exemption lost its placeholder card')
ok('.recipe-selector-card-placeholder' in
   alv_tree.python_code_only(was(os.path.join(
       ROOT, 'test_pair_contrast.py')), payloads=True),
   'CONTROL: it was pinned there before this round')

rw = read(os.path.join(ROOT, 'test_row_wrap.py'))
ok("'create_meal_plan.html'" not in
   alv_tree.python_code_only(rw, payloads=True).split('HELD_BACK')[1][:400],
   'and the held-back list lost it too')

# ==========================================================================
head('10. THE CONTROL - NONE OF THIS WORKED BEFORE THE ROUND')
# ==========================================================================
# Every claim above re-asked of alv_tree AS THIS ROUND FOUND IT. Each one
# must FAIL, or the round did nothing and the suite cannot tell.
old_tree = was(os.path.join(ROOT, TREE))
if not old_tree:
    skip('the whole control register', 'no %s backup' % SUFFIX)
else:
    ns = {'__name__': '_alv_tree_before'}
    exec(compile(old_tree, TREE, 'exec'), ns)
    for fn in ('RETIRED', 'retired', 'last_path', 'last_of', 'nominal',
               'bak_path', 'bak_of', 'touched_by', 'last_join',
               'retired_labels'):
        ok(fn not in ns, 'CONTROL: alv_tree had no %s' % fn)
    try:
        ns['path_of'](DEAD)
        ok(False, 'CONTROL: and path_of refused the page, saying nothing')
    except IOError as e:
        ok('retired' not in str(e),
           'CONTROL: and its refusal said nothing about a round',
           str(e)[:90])

old_rounds = was(os.path.join(ROOT, 'alv_rounds.py'))
if not old_rounds:
    skip('CONTROL: as_left_by could not take a retired page', 'no backup')
else:
    ns2 = {'__name__': '_alv_rounds_before'}
    exec(compile(old_rounds, 'alv_rounds.py', 'exec'), ns2)
    # IT DID NOT RAISE. It answered, and the answer was wrong - which
    # is worse, and is why test_btn_tone reported "13 now, 8 before" on
    # a round that changed neither. Handed a retired page's last text,
    # the old walk looked for <that text>.bak_<later round>, found
    # nothing, and read the last text itself: the page as MN-1 found
    # it, not as BT-1 left it. Both are real texts of that page and
    # neither is the pair the claim is about.
    old_answer = ns2['as_left_by'](alv_tree.last_path(DEAD),
                                   '.bak_lblwt', read)
    new_answer = alv_rounds.as_left_by(alv_tree.last_path(DEAD),
                                       '.bak_lblwt', read)
    ok(old_answer != new_answer,
       'CONTROL: the old walk answered a DIFFERENT text for a retired '
       'page - %d bytes against %d' % (len(old_answer), len(new_answer)))
    ok(old_answer == read(alv_tree.last_path(DEAD)),
       '  and what it answered was the page as MN-1 found it, which is '
       'not what "as that round left it" means')

# ==========================================================================
head('11. REGISTERED, ON THE GATE, AND IT PARSES')
# ==========================================================================
ok('.bak_retired' in alv_rounds.ROUNDS,
   '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(alv_rounds.ROUNDS.index('.bak_retired')
   > alv_rounds.ROUNDS.index('.bak_planner'),
   '  and AFTER .bak_planner, the round whose hole it is about')
ok(ME in alv_tree.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
ok("'%s'" % ME in ps, '  and in the $suites list on the gate')
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)

wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
ok('CONVERTED_N = %d' % len(alv_tree.CONVERTED) in wd,
   'test_waiting_down counts %d converted suite(s)'
   % len(alv_tree.CONVERTED))

bad = []
for name in KEPT + MOVED + (TREE, IMPACT, RA, 'alv_rounds.py'):
    try:
        ast.parse(read(os.path.join(ROOT, name)))
    except SyntaxError as e:
        bad.append('%s: line %s' % (name, e.lineno))
ok(not bad, 'all %d file(s) this round touched still parse'
   % (len(KEPT) + len(MOVED) + 4), bad)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
if failed:
    sys.exit(1)
