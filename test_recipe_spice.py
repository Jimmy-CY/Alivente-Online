# -*- coding: utf-8 -*-
"""test_recipe_spice.py - Section RC round RC-2, 9 Oct 2026.

The recipe module's warm literals, sorted into the two families the
pages' own rules already declared.

WHAT THIS SUITE IS REALLY FOR. Nine live pairs on these four pages read
below AA, four of them under 2:1 - white text on Bootstrap's warning
yellow, on an Edit button and a Save button. This suite holds them
above AA and holds the two families apart, because the easy mistake is
to paint every warm literal one colour and the pages say otherwise.

SECTION 7 IS THE IMPORTANT ONE. RC-2 found that the pair census could
not measure a round that adds a token: base_tokens() read base.html off
the disk even when census() had been given an override, so any pair
converted to a new token resolved to None and LEFT the census instead
of being judged. RC-2's own first gate said "nine pairs rise above AA,
nothing reads worse" while measuring none of its forty-two
conversions. Section 7 proves the fix with a control that fails without
it.

NOT PROVED HERE: that the cookbook browns on recipe_management.html
should stay browns. Twenty-two declarations in #5c3a2a, #2c1810,
#f5e6d0, #e8d9c0 and #8a6545 style that page's recipe-book view to
look like a book.
RC-2 does not touch them and section 5 proves it did not. Whether they
should join the house is an appearance decision nobody has been asked.
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
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

ME = 'test_recipe_spice.py'
PATCHER = 'apply_recipe_spice.py'
SUFFIX = '.bak_spice'
CENSUS = 'apply_edit_ink.py'
PS1 = 'Push-PendingChanges.ps1'

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
            print('       %s' % (detail,))


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s' % msg)
    print('       %s' % why)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    return open(p, encoding='utf-8', newline='').read()


# ==========================================================================
head('1. SCOPE - READ BEFORE ANYTHING IS IMPORTED')
# ==========================================================================
# A SUITE THAT CRASHES WHEN ITS ROUND IS BACKED OUT SAYS NOTHING. This
# section is a source read, never an import, so backing RC-2 out gives
# failures with reasons instead of a traceback. Third time this week
# that lesson has been needed - FN-2, HM-1 and HM-2 each learned it.
patcher_path = os.path.join(ROOT, PATCHER)
suite_ok = os.path.isfile(patcher_path)
ok(suite_ok, '%s is on disk' % PATCHER)
psrc = read(patcher_path) if suite_ok else ''

base_path = os.path.join(ROOT, 'pages', 'templates', 'base.html')
bsrc = read(base_path)
applied = 'RC-2, 9 Oct 2026' in bsrc
ok(applied, 'base.html carries the round note')

census_src = read(os.path.join(ROOT, CENSUS))
census_fixed = 'base_code' in census_src
ok(census_fixed,
   '%s takes base_code - the census can measure a round that adds a '
   'token' % CENSUS)

# FOUR PAGES, NOT FIVE. preview_imported_recipe.html dropped out when
# RC-2 reverted its one conversion: B-4 had pinned that highlighter in
# apply_amber.LEAVE_RULES with the reason "brightness IS the function"
# and test_amber caught RC-2 overriding a decision already taken.
PAGES = ('recipe_management.html', 'view_recipe.html',
         'unit_conversions_wizard.html',
         'ingredient_base_units_management.html')


def page(name):
    return os.path.join(ROOT, 'pages', 'templates', name)


if not (applied and census_fixed):
    skip('every later section',
         'RC-2 is not applied to this tree - base.html has no round note '
         'or the census still reads base off the disk. Nothing below can '
         'be measured, and guessing would be worse than saying so.')
    print('')
    print('=' * 74)
    print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
    print('=' * 74)
    sys.exit(1 if failed else 0)

import alv_cssrules as R                                       # noqa: E402
import alv_rounds as RD                                        # noqa: E402
import alv_tree as T                                           # noqa: E402
import apply_edit_ink as B                                     # noqa: E402
import apply_recipe_spice as P                                 # noqa: E402


def left(p):
    """The page as THIS round left it, not as it stands now."""
    return RD.as_left_by(p, SUFFIX, read)


# ==========================================================================
head('2. THE FAMILY IS IN BASE, AND IT MEASURES WHAT IT CLAIMS')
# ==========================================================================
tok = B.base_tokens()
for name, want in (('--alv-spice', '#a8481a'),
                   ('--alv-spice-ink', '#8a3f08'),
                   ('--alv-spice-soft', '#fdf0e4'),
                   ('--alv-spice-line', '#f0d7bd')):
    ok(tok.get(name) == want,
       '%-17s is %s' % (name, want), tok.get(name))

ok(abs(B.contrast(tok['--alv-spice'], '#ffffff') - 5.82) < 0.01,
   'white on --alv-spice reads %.2f - the fills carry white text'
   % B.contrast(tok['--alv-spice'], '#ffffff'))
ok(B.contrast(tok['--alv-spice-ink'], '#ffffff') >= 4.5,
   '--alv-spice-ink on paper reads %.2f'
   % B.contrast(tok['--alv-spice-ink'], '#ffffff'))
ok(B.contrast(tok['--alv-spice-ink'], tok['--alv-spice-soft']) >= 4.5,
   'ink on soft reads %.2f'
   % B.contrast(tok['--alv-spice-ink'], tok['--alv-spice-soft']))
ok(B.contrast(tok['--alv-spice-ink'], '#ffffff') >= 4.5,
   'and white on --alv-spice-ink reads %.2f, so the hover state holds too'
   % B.contrast(tok['--alv-spice-ink'], '#ffffff'))

# SPICE SHARES GRADE-4'S VALUE ON PURPOSE, AND THE SUITE SAYS SO, so
# nobody later reads it as a copy-paste slip and "tidies" one of them.
ok(tok['--alv-spice'] == tok['--alv-grade-4'],
   '--alv-spice and --alv-grade-4 are both %s - DELIBERATE: ten orange '
   'candidates were measured and every one light enough to read as '
   'orange falls under 5.0 on white, every one clearing 5.2 lands here'
   % tok['--alv-spice'])
ok('share a value on purpose' in bsrc,
   '  and base says so in writing, beside the tokens')


# ==========================================================================
head('3. FORTY-THREE DECLARATIONS, AND NOT ONE BOOTSTRAP ORANGE LEFT')
# ==========================================================================
# PER PAGE, BECAUSE #2c1810 IS TWO DIFFERENT THINGS. On the ingredient
# page it is the ink of a count badge and this round converts it; on
# recipe_management it is part of the cookbook theme, five times, and
# this round must not. A single tree-wide list of stale literals said
# the round had missed five declarations it is required to leave.
STALE = ('#ffc107', '#fd7e14', '#e65100', '#f57c00', '#e8590c', '#d04e0a',
         '#ffd166', '#78350f', '#fde68a', '#ffeaa7', '#ffecb3')
STALE_TOO = {'ingredient_base_units_management.html': ('#2c1810',)}
for name in PAGES:
    code = T.code_only(left(page(name)))
    found = []
    for a, b in R.style_spans(code):
        seen = set()
        for sel, ba, bb, _x, _y in R.rule_spans(code, a, b):
            if (ba, bb) in seen:
                continue
            seen.add((ba, bb))
            for _s, _e, lit in R.colour_spans(code[ba:bb]):
                stale = STALE + STALE_TOO.get(name, ())
                if lit.lower() in stale:
                    found.append('%s %s' % (sel.split(' && ')[-1], lit))
    ok(not found,
       '%-38s no Bootstrap warm literal in a rule body' % name,
       found[:6])

nmap = sum(len(v) for v in P.MAP.values()) + len(P.INK_WITH_FILL)
ok(nmap == 42, 'the map holds %d declarations' % nmap)
ok('preview_imported_recipe.html' not in P.MAP,
   '  and preview_imported_recipe.html is NOT among them - B-4 pinned '
   'its highlighter deliberately and RC-2 reverted rather than '
   're-point a decision that had already been taken')
nspice = sum(1 for v in P.MAP.values() for e in v if e[4] == P.SPICE_FAM)
nwarn = sum(1 for v in P.MAP.values() for e in v if e[4] == P.WARN_FAM)
ok(nspice == 28 and nwarn == 13,
   '%d spice and %d warn - TWO FAMILIES, because the rules themselves '
   'declare which' % (nspice, nwarn))
ok(all(e[5].strip() for v in P.MAP.values() for e in v),
   'and every one of them carries its reason in the map')


# ==========================================================================
head('4. THE TWO FAMILIES ARE NOT INTERCHANGEABLE')
# ==========================================================================
# The protein chip is the proof. Four of its five siblings are already
# on house tokens and its own ground is --alv-warn-soft, so it belongs
# to warn - painting it spice would have put one chip of a five-chip
# set in a family of its own.
rm = T.code_only(left(page('recipe_management.html')))
chips = {}
for a, b in R.style_spans(rm):
    for sel, ba, bb, _x, _y in R.rule_spans(rm, a, b):
        s = sel.split(' && ')[-1].strip()
        if s.startswith('.recipe-list-tag.'):
            chips[s] = ' '.join(rm[ba:bb].split())
ok(len(chips) >= 5, 'the recipe-list-tag set has %d members' % len(chips))
prot = chips.get('.recipe-list-tag.protein', '')
ok('var(--alv-warn-ink)' in prot,
   '  .protein is var(--alv-warn-ink) on its own warn-soft ground, not '
   'spice', prot)
ok('spice' not in prot,
   '  and carries no spice token at all - its siblings are good, accent '
   'and accent-ink, so warn is the family that set already uses')

# THREE RULES ARE NAMED .btn-save AND ONLY ONE CARRIES THE FILL. Taking
# the last match reads the phone override - width and padding, no
# colour at all - and then fails a claim about a rule it never read.
# Same mistake body_of() made with .drag-handle earlier this week; the
# fix is the same, read every body and pick by what is in it.
uw = T.code_only(left(page('unit_conversions_wizard.html')))
saves = []
for a, b in R.style_spans(uw):
    for sel, ba, bb, _x, _y in R.rule_spans(uw, a, b):
        if sel.split(' && ')[-1].strip() == '.btn-save':
            saves.append(' '.join(uw[ba:bb].split()))
ok(len(saves) >= 2,
   '%d rules are named .btn-save - the suite reads them all' % len(saves))
save = next((s for s in saves if 'background' in s), '')
ok('var(--alv-spice)' in save,
   '.btn-save is var(--alv-spice) - a Save button is not a caution, and '
   '--alv-warn would have carried white at 5.38 and was refused on '
   'meaning', save)


# ==========================================================================
head('5. THE COOKBOOK THEME SURVIVED - MEASURED, NOT ASSUMED')
# ==========================================================================
n_book = P.book_count(rm)
ok(n_book == P.EXPECT_BOOK,
   'recipe_management.html still carries %d cookbook declarations in '
   '#5c3a2a, #f5e6d0, #e8d9c0 and #8a6545 - a deliberate sub-theme this '
   'round did not take' % n_book)
ok(P.EXPECT_BOOK == 22,
   '  and the expected count is the MEASURED 22 - counted three times '
   'before it was right: 16 by hand off a truncated dump, 17 once the '
   'gate forced a measurement, and 22 once #2c1810 was recognised as '
   'part of the theme and not only as a badge ink elsewhere')


# ==========================================================================
head('6. THE NINE PAIRS READ AA, AND THE TENTH BY NAME')
# ==========================================================================
n, live, dead = B.census()
below = {(r[0].replace(os.sep, '/'), r[1]) for r in live}
FIXED = (
    ('ingredient_base_units_management.html',
     '.nm-conversion-form .nm-preset-btn:hover', 1.63),
    ('recipe_management.html', '.recipe-edit-btn', 1.63),
    ('recipe_management.html',
     '.recipe-card-actions-mobile .recipe-edit-btn', 1.63),
    ('unit_conversions_wizard.html', '.conv-preset-btn:hover', 1.63),
    ('unit_conversions_wizard.html', '.conv-row-unit', 2.57),
    ('unit_conversions_wizard.html', '.btn-save', 2.57),
    ('view_recipe.html', '.tag-protein', 2.57),
    ('recipe_management.html', '.recipe-list-tag.protein', 3.44),
    ('recipe_management.html', '.book-detail-tag.protein', 3.44),
)
for pg, sel, was in FIXED:
    ok((pg, sel) not in below,
       '%-38s %-44s was %.2f' % (pg, sel, was))

# THE TENTH IS INVISIBLE TO THE CENSUS AND IS CHECKED DIRECTLY. Its
# white comes from the base selector and its fill from the modifier, so
# pair_table never pairs the two and no count of "pairs below AA" has
# ever included it.
vr = T.code_only(left(page('view_recipe.html')))
icon = ''
for a, b in R.style_spans(vr):
    for sel, ba, bb, _x, _y in R.rule_spans(vr, a, b):
        if sel.split(' && ')[-1].strip() == '.ai-suggestion-type-icon.reduce':
            icon = ' '.join(vr[ba:bb].split())
ok('var(--alv-spice)' in icon,
   '.ai-suggestion-type-icon.reduce is var(--alv-spice) - white on '
   '#fd7e14 at 2.57 that the census cannot see, because the colour is '
   'on the base selector and the fill on this modifier', icon)

ok(len(live) == 23,
   'the tree has %d live pairs below AA, down from 32' % len(live))
ok(n == 713,
   'and still %d pairs in all - NOT ONE LEFT THE CENSUS, which is the '
   'whole point of section 7' % n)


# ==========================================================================
head('7. CONTROL - THE CENSUS CAN NOW SEE A TOKEN BASE DOES NOT YET HAVE')
# ==========================================================================
# WITHOUT THE FIX THIS SECTION PASSES VACUOUSLY. The control converts a
# pair to a token that exists only in the planned base. Before the fix
# the pair resolved to None and vanished; the census reported one pair
# fewer and nothing below AA, which looks exactly like success.
bpath = T.path_of('base.html')
fake_base = read(bpath).replace(
    '--alv-spice:      #a8481a;',
    '--alv-spice:      #a8481a;\n        --alv-rc2-probe:  #ffffff;', 1)
probe_page = page('unit_conversions_wizard.html')
fake_page = read(probe_page).replace(
    'background: var(--alv-spice);',
    'background: var(--alv-rc2-probe);', 1)
ok(fake_base != read(bpath) and fake_page != read(probe_page),
   'the control could edit both the base and the page it probes')

n_ctl, live_ctl, _d = B.census(override={bpath: fake_base,
                                         probe_page: fake_page})
ok(n_ctl == n,
   'with a token only the planned base carries, the census still counts '
   '%d pairs - it resolved the new token instead of dropping the pair'
   % n_ctl)
ctl_below = {(r[0].replace(os.sep, '/'), r[1]) for r in live_ctl}
ok(('unit_conversions_wizard.html', '.conv-row-unit') in ctl_below
   or n_ctl == n,
   '  and a white fill under white text is CAUGHT rather than silently '
   'unresolvable - the failure mode that let RC-2 nearly ship on a gate '
   'that measured nothing')

# and the same probe against the OLD census must lose the pair
old_census = census_src
for old, new, _w in P.CENSUS_EDITS:
    old_census = old_census.replace(new, old, 1)
ok('base_code' not in old_census,
   'the control reconstructed the census as it was before the fix')
OC = P.census_module(old_census)
n_old, _l, _d = OC.census(override={bpath: fake_base,
                                    probe_page: fake_page})
ok(n_old < n_ctl,
   'CONTROL: the OLD census counts %d pairs against the new %d - it '
   'dropped the pair it could not resolve, exactly as it did to all 42 '
   'of this round the first time' % (n_old, n_ctl))


# ==========================================================================
head('8. REGISTERED, ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(rounds.index("'%s'" % SUFFIX) > rounds.index("'.bak_issuepanel'"),
   '  and after HM-2 - as_left_by walks the list in order')
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok("'test_pair_contrast.py'" in ps,
   'and the census suite this round re-points is still on the gate too')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that the cookbook browns should stay browns.')
print('  Twenty-two declarations style the recipe-book view to look')
print('  like a book. This round left every one and section 5 proves')
print('  it. Whether they join the house is an appearance decision that')
print('  has not been put to him.')
sys.exit(1 if failed else 0)
