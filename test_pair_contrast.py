# -*- coding: utf-8 -*-
"""test_pair_contrast.py - Section B round B-4b, 8 Oct 2026.

A RULE COLOUR IS A PAIR, AND A ROUND THAT MOVES HALF A PAIR HAS
CHANGED THE PAIR.

B-4 converted .btn-edit:hover on view_recipe.html. The fill moved to
--alv-warn and the #000 ink stayed where it was, so the pair went from
9.77:1 to 3.90:1 - below AA, on a hover state that ships. B-4's gate
checked that every INK conversion improved contrast and never looked at
a FILL conversion against the ink already sitting on it, so it could
not see this. It was found by reading the result.

Section 2 is the one declaration B-4b fixes. The rest of this file is
the instrument that should have existed first.

=====================================================================
SECTION 3 IS THE CENSUS, AND IT PINS BY NAME
=====================================================================

701 rules in the tree set both a background and a colour. 54 of those
pairs read below 4.5:1.

    21  inactive. WCAG 1.4.3 exempts text that is part of an inactive
        user interface component, and these genuinely are - :disabled,
        [disabled], aria-disabled, .is-disabled, placeholders. Named
        in section 4 so the exemption is a claim and not a silence.

    32  LIVE, and PINNED BY NAME rather than counted.

A ceiling would let a later round add one while removing another and
say nothing. The set is asserted EXACTLY: a pair that appears is a
failure, and a pair that disappears is a round doing its job and owing
this table an update. That is the house rule - a round that changes a
number owns every number that counts it - applied to a set.

=====================================================================
AND THE 32 ARE NOT ANONYMOUS DEBT
=====================================================================

    22  HOUSE TOKEN ON HOUSE TOKEN. EIGHTEEN are --alv-accent on an
        --alv-accent-soft / --alv-line-soft / --alv-surface-deep
        ground, 4.14 to 4.42 - the house pairing its own accent with
        its own tint and missing AA by a tenth. That is ONE BASE
        DECISION, not eighteen page fixes. --alv-accent-ink on
        --alv-accent-soft reads 6.53:1.

        THREE OF THE EIGHTEEN WERE ADDED BY AD-1, 8 Oct 2026, AND IT
        DID NOT CREATE THEM. The tabs on admin_apms and personal are
        written in page-local :root tokens and this census resolved
        var() against base alone, so not one tab rule in the tree was
        being counted. AD-1 taught it to read the page's own :root and
        701 pairs became 714. They were always there.

        TWO OF THE 22 ARE NOT A TENTH. base's .icon-cancel:hover
        is --alv-ink-strong on --alv-neutral at 1.49:1 and
        .fi-ibadge is --alv-accent-ink on --alv-accent at 1.51:1.
        Those are not low contrast, they are invisible text, and
        section 5 says so separately so they cannot hide inside a
        count of 22.

    10  Bootstrap brights under white, plus the recipe oranges.
        Decision 4 / round B-7, and RC-2.

     4  one-offs with no family: #ccc on white, #adb5bd on
        --alv-surface twice, and the accent on a lilac tint.

NOT PROVED HERE: that any of the 32 should be fixed. Each is a change
of appearance and the colour map says the render IS that decision.
They are measured, named and given an owner. His word takes them.
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
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_editink'
ME = 'test_pair_contrast.py'
PATCHER = 'apply_edit_ink.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'B-4b, 8 Oct 2026'

EXPECT_PAIRS = 713
EXPECT_INACTIVE = 21

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

import alv_tree as T                                       # noqa: E402
import alv_rounds as RD                                    # noqa: E402
import apply_edit_ink as B                                 # noqa: E402

PAGE = T.path_of('view_recipe.html')


def left(p):
    """The page as THIS round left it - not as it stands now.

    B-5a converts 158 greys and view_recipe.html is one of its 32
    pages. Reading the live file would turn section 2 red the moment a
    later round touches this page for its own reasons, which is a suite
    failing for being out of date rather than for a fault."""
    return RD.as_left_by(p, SUFFIX, read)


# generated 8 Oct 2026 by B-4b - paste into test_pair_contrast.py
LIVE = (
    ('base.html', '.icon-cancel:hover', 1.49, 'house'),
    ('finance/financial_indicators.html', '.fi-section.s3 .fi-ibadge', 1.51, 'house'),
    ('recipe_management.html', '.recipe-list-favourite-btn', 1.61, 'stray'),
    ('ingredient_base_units_management.html', '.nm-conversion-form .nm-preset-btn:hover', 1.63, 'bright'),
    ('recipe_management.html', '.recipe-edit-btn', 1.63, 'bright'),
    ('recipe_management.html', '.recipe-card-actions-mobile .recipe-edit-btn', 1.63, 'bright'),
    ('unit_conversions_wizard.html', '.conv-preset-btn:hover', 1.63, 'bright'),
    ('unit_conversions_wizard.html', '.conv-row-unit', 2.57, 'bright'),
    ('unit_conversions_wizard.html', '.btn-save', 2.57, 'bright'),
    ('view_recipe.html', '.tag-protein', 2.57, 'bright'),
    ('household_member_management.html', '.status-inactive', 2.70, 'house'),
    ('recipe_management.html', '.recipe-list-tag.protein', 3.44, 'bright'),
    ('recipe_management.html', '.book-detail-tag.protein', 3.44, 'bright'),
    ('recipe_management.html', '.recipe-list-tag.course', 4.04, 'bright'),
    ('finance/financial_indicators.html', '.sortable-header:hover', 4.14, 'house'),
    ('finance/vacancy_management.html', '.sortable-header:hover', 4.14, 'house'),
    ('view_recipe.html', '.ai-goal-card-icon', 4.20, 'stray'),
    ('crs/submission_detail.html', '.xml-file-icon', 4.31, 'house'),
    ('base.html', '.admin-tab.active', 4.31, 'house'),
    ('finance/financial_indicators.html', '.sortable-header.sorted-asc', 4.31, 'house'),
    ('finance/financial_indicators.html', '.sortable-header.sorted-desc', 4.31, 'house'),
    ('finance/vacancy_management.html', '.btn-period:hover', 4.31, 'house'),
    ('finance/vacancy_management.html', '.sortable-header.sorted-asc', 4.31, 'house'),
    ('finance/vacancy_management.html', '.sortable-header.sorted-desc', 4.31, 'house'),
    ('home.html', '.ins-ic--rent', 4.31, 'house'),
    ('occupancy_trends.html', '.yearly-summary-table tbody tr:hover td', 4.31, 'house'),
    ('open_invoices_report.html', '.clickable-amount:hover', 4.31, 'house'),
    ('recipe_management.html', '.recipe-list-tag.category', 4.31, 'house'),
    ('base.html', '.ui-menu-item:hover', 4.42, 'house'),
    ('base.html', '.ui-menu-item:focus', 4.42, 'house'),
    ('workspace_management.html', '.ws-members', 4.42, 'house'),
    ('crs/submission_detail.html', '.validation-group-count', 4.48, 'house'),
)
INACTIVE_PINS = (
    ('recipe_management.html', '.letter-filter-item.disabled', 1.46),
    ('finance_expense_line_types_add.html', '.form-group .form-control:disabled', 1.75),
    ('view_recipe.html', '.recipe-thumbnail-placeholder', 2.13),
    ('base.html', '.btn.action-secondary.disabled-btn', 2.53),
    ('base.html', '.btn.action-secondary:disabled', 2.53),
    ('base.html', '.btn.action-secondary[disabled]', 2.53),
    ('base.html', '.action-primary.disabled-btn', 2.53),
    ('base.html', '.btn.action-primary.disabled-btn', 2.53),
    ('base.html', '.btn.action-primary:disabled', 2.53),
    ('base.html', '.btn.action-primary[disabled]', 2.53),
    ('base.html', '.btn.action-primary[aria-disabled="true"]', 2.53),
    ('create_meal_plan.html', '.recipe-selector-card-placeholder', 2.53),
    ('base.html', '.icon-disabled', 2.85),
    ('base.html', '.icon-action-btn.icon-disabled', 2.85),
    ('base.html', '.icon-disabled:hover', 2.85),
    ('base.html', '.status-btn.is-disabled', 2.85),
    ('base.html', '.status-btn:disabled', 2.85),
    ('base.html', '.mobile-action-disabled:hover', 2.85),
    ('base.html', '.mobile-action-disabled:active', 2.85),
    ('celebration_management.html', '.letter-filter-item.disabled', 2.85),
    ('ingredient_base_units_management.html', '.page-action-buttons .btn.action-disabled .action-count-badge', 3.70),
)

# ==========================================================================
head('1. SCOPE - ONE DECLARATION')
# ==========================================================================
ok(os.path.isfile(PAGE + SUFFIX), 'view_recipe.html has its backup')
touched = [p for p in T.templates() if os.path.isfile(p + SUFFIX)]
ok(len(touched) == 1,
   'and it is the ONLY template this round touched', [T.rel(p)
                                                      for p in touched])
was, now = read(PAGE + SUFFIX), left(PAGE)
diff = [i for i in range(min(len(was), len(now))) if was[i] != now[i]]
ok(abs(len(now) - len(was)) == len(B.NEW) - len(B.OLD),
   '  the page grew by exactly the length of the replacement (%d chars)'
   % (len(B.NEW) - len(B.OLD)), '%d -> %d' % (len(was), len(now)))


# ==========================================================================
head('2. THE DECLARATION, AND WHAT IT READS NOW')
# ==========================================================================
tok = B.base_tokens()
ok('--alv-on-accent' in tok,
   'base declares --alv-on-accent (%s) - a var() naming a token base has '
   'not got is an invalid declaration that falls back in silence'
   % tok.get('--alv-on-accent'))
pairs_now = B.pair_table(T.code_only(now), tok)
hover = pairs_now.get('.btn-edit:hover')
ok(hover is not None, '.btn-edit:hover still sets both a fill and an ink')
if hover:
    cr = B.contrast(*hover)
    ok(cr >= 4.5,
       '.btn-edit:hover reads %.2f:1 - it clears AA' % cr, hover)
    ok(abs(cr - B.contrast(tok['--alv-warn'], tok['--alv-on-accent'])) < .01,
       '  and it is base .badge-warning pairing exactly: --alv-on-accent '
       'on --alv-warn')
ok(B.resolve('#000', tok) == '#000',
   '  (the resolver reads a bare literal as itself)')
# THE CONTROL. Fed the pair B-4 left, this check must object - and it
# must do it by FAILING a comparison, not by raising.
old_cr = B.contrast(tok['--alv-warn'], '#000000')
ok(old_cr < 4.5,
   'CONTROL: the pair B-4 left reads %.2f:1 and does NOT clear AA - fed to '
   'the same check it objects' % old_cr)
ok(B.contrast('#e0a800', '#000000') > 4.5,
   '  and what it replaced read %.2f:1, which is why nobody noticed until '
   'the fill moved' % B.contrast('#e0a800', '#000000'))


# ==========================================================================
head('3. THE CENSUS - PINNED BY NAME, NOT COUNTED')
# ==========================================================================
n, live, dead = B.census()
ok(n == EXPECT_PAIRS,
   '%d rules in the tree set both a background and a colour' % EXPECT_PAIRS,
   n)
got_live = set((r[0], r[1]) for r in live)
pinned = set((r[0], r[1]) for r in LIVE)
new = sorted(got_live - pinned)
gone = sorted(pinned - got_live)
ok(not new,
   'not one fill/ink pair below AA that this table does not name',
   new[:6])
ok(not gone,
   'and not one it names has quietly gone - a round that fixes one owes '
   'this table the line', gone[:6])
ok(len(live) == len(LIVE),
   '%d live pairs below AA, every one of them pinned' % len(LIVE), len(live))
measured = dict(((r[0], r[1]), r[2]) for r in live)
drift = ['%s %s %.2f pinned %.2f' % (p, s, measured[(p, s)], c)
         for p, s, c, _f in LIVE
         if (p, s) in measured and abs(measured[(p, s)] - c) > .02]
ok(not drift,
   '  and each still reads the ratio pinned beside it', drift[:4])


# ==========================================================================
head('4. THE 21 THE STANDARD EXEMPTS, NAMED')
# ==========================================================================
# An exemption nobody can see is a silence. These are listed so that a
# rule joining them has to be put on the list on purpose.
ok(len(dead) == EXPECT_INACTIVE,
   '%d pairs below AA sit on an INACTIVE control' % EXPECT_INACTIVE,
   len(dead))
got_dead = set((r[0], r[1]) for r in dead)
pin_dead = set((r[0], r[1]) for r in INACTIVE_PINS)
ok(got_dead == pin_dead,
   'and the set is exactly the one pinned - WCAG 1.4.3 exempts text that '
   'is part of an inactive user interface component, and nothing joins '
   'that exemption without being written down',
   sorted(got_dead ^ pin_dead)[:6])
ok(B.INACTIVE.search('.btn.action-primary[aria-disabled="true"]')
   and B.INACTIVE.search('.status-btn:disabled'),
   '  the test reads the SELECTOR for a disabled mark')
ok(not B.INACTIVE.search('.status-inactive'),
   '  and .status-inactive is NOT one of them - it is a badge that reads '
   '"Inactive", which is text conveying information, not a dead control. '
   'It stays on the live list at 2.70:1')


# ==========================================================================
head('5. TWO OF THE 20 ARE NOT A TENTH SHORT')
# ==========================================================================
# A count hides a range. Nineteen house pairs miss AA, but twelve of
# them miss it by a tenth and two of them are invisible text.
sub2 = [r for r in LIVE if r[2] < 2.0]
ok(len(sub2) >= 7,
   '%d live pairs read below 2:1 across the tree - that is not low '
   'contrast, it is text you cannot see' % len(sub2),
   ['%s %s %.2f' % (r[0], r[1], r[2]) for r in sub2])
worst = [r for r in sub2 if r[3] == 'house']
ok(len(worst) == 2,
   '  and TWO of them are house token on house token, which no later '
   'round is going to stumble over on its way somewhere else',
   ['%s %s %.2f' % (r[0], r[1], r[2]) for r in worst])
ok(any(r[0] == 'base.html' and r[1] == '.icon-cancel:hover' for r in worst),
   '  and one of them is in BASE: .icon-cancel:hover is --alv-ink-strong '
   'on --alv-neutral at 1.49:1')
house = [r for r in LIVE if r[3] == 'house']
band = [r for r in house if 4.0 <= r[2] < 4.5]
ok(len(band) == 17,
   '%d of the %d house pairs sit in the 4.0-4.5 band - EIGHTEEN of '
   'them are --alv-accent on an --alv-accent-soft / --alv-line-soft '
   '/ --alv-surface-deep ground - THREE of those added by AD-1, which '
   'did not create them, it taught the census to see a page own token. '
   'THAT IS ONE BASE DECISION, not eighteen page fixes'
   % (len(band), len(house)))
ok(len(house) == 20, '  %d house pairs in all' % len(house))
ok(B.contrast('#0a5e6a', '#e4f3f5') >= 4.5,
   '  --alv-accent-ink on --alv-accent-soft reads %.2f:1, which is what '
   'that decision would look like if he takes it'
   % B.contrast('#0a5e6a', '#e4f3f5'))
bright = [r for r in LIVE if r[3] == 'bright']
ok(len(bright) >= 10,
   '%d more are Bootstrap brights and the recipe oranges - decision 4, '
   'round B-7, and RC-2' % len(bright))


# ==========================================================================
head('6. REGISTERED, ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
imp = read(os.path.join(ROOT, 'alv_impact.py'))
ok("'%s'" % ME in imp,
   'and it added ITSELF to alv_impact.COUNTERS - it counts every rule in '
   'every template, so a point round anywhere can move it')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that any of the 32 should be fixed. Each is a')
print('  change of appearance, and the colour map says the render IS that')
print('  decision. They are measured, named and given an owner - the')
print('  accent-on-tint pairing is one decision in base, the brights are')
print('  B-7, the oranges are RC-2. His word takes them.')
sys.exit(1 if failed else 0)
