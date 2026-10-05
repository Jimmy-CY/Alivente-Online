"""RA-5 - THE REGISTER OF CONTROLS THAT ARE NOT ACTION COLUMNS.

   RA-1 gave the app a row-action order and a report that finds the
   columns which have left it. RA-2 widened the report past .row-actions
   and found 37 icon buttons nobody had ever examined. RA-3 wrapped 21 of
   them, RA-3b the ten that live each in their own form. The report has
   ended every run since with:

       NOT IN A .row-actions WRAPPER - 4 button(s) on 2 page(s).
         create_meal_plan.html   3  icon-delete
         edit_asset.html         1  icon-delete

   AND THE SLOT FOR THOSE FOUR WAS CALLED RA-3c - wrap them. Reading the
   markup says they should not be wrapped at all. Every one is a single
   Remove button sitting beside the thing it removes:

       edit_asset        Remove, beside the invoice's file name
       create_meal_plan  Remove this recipe, x3, beside a recipe name
                         and its servings box

   A .row-actions around one control tells the report there is an action
   column with one action in it. That is the shape RA-3 refused on the
   form-shaped pages, and it would be inventing a column to satisfy a
   census. Demetri ruled on the edit_asset one when AI-1 built it -
   "Leave it named, it is not an action column" - and these are the same
   control in a different page.

   SO THE REPORT LEARNS TO SAY SO. Four buttons that are deliberately not
   in a column, carrying the reason they are not, read differently from
   four nobody has looked at, and the difference is the whole value of a
   drift report. The register lives in alv_rowactions beside the order
   itself, because the next reader will look there and not in a comment
   in the report.

   A REGISTER THAT CANNOT BE USED TO HIDE ANYTHING. Each entry pins an
   EXACT count. If one of those pages grows a fifth loose button it does
   not inherit the exemption - the count stops matching and the report
   calls it a problem, by name, and exits non-zero under --strict. An
   exemption that silently covered whatever appeared next to it would be
   worse than no register.

   WHAT THIS DOES NOT CLAIM, and the suite says it out loud: the register
   records a judgement about four controls. It is not a test that they
   are alone in their parent - test_row_exempt.py section 3 is, and it
   does that by reading the markup around each one.

   FILES: alv_rowactions.py, Show-RowActionDrift.py. [test_row_exempt.py]
"""
import os
import sys

SUFFIX = '.bak_rowexempt'

RA = 'alv_rowactions.py'
REPORT = 'Show-RowActionDrift.py'

# ---- what goes into alv_rowactions.py -----------------------------------
RA_ANCHOR = 'def wrappers(src):'

RA_BLOCK = '''# NAMED, NOT UNEXAMINED.                           [RA-5, 5 Oct 2026]
#
# A .row-actions wrapper is for a GROUP of actions in a row's action
# column. These four controls are not that: each is a single Remove
# button beside the one thing it removes, and wrapping it would tell the
# drift report there is an action column with one action in it - a column
# invented to satisfy a census.
#
# Demetri ruled on the edit_asset one when AI-1 built it: "Leave it
# named, it is not an action column." The three on create_meal_plan are
# the same control on a different page.
#
# THE COUNT IS THE POINT. Each entry pins an exact number. A page that
# grows one more loose button does not inherit the exemption - the count
# stops matching and the report calls it a problem by name. An exemption
# that covered whatever turned up next to it would be worse than none.
NAMED = {
    'edit_asset.html': {
        'count': 1,
        'classes': ('icon-delete',),
        'why': 'Remove the attached invoice - one control beside the file '
               'name it removes. AI-1, and Demetri: leave it named.',
    },
    'create_meal_plan.html': {
        'count': 3,
        'classes': ('icon-delete',),
        'why': 'Remove this recipe - one control at the end of each recipe '
               'row, beside the name and the servings box. Built inside a '
               'JavaScript template literal.',
    },
}


def named(page, hits):
    """(reason, exact) for a page's unwrapped buttons, or (None, None).

    `exact` is False when the register knows the page but the number of
    loose buttons on it has moved, which is the case the register must
    not quietly absorb.
    """
    e = NAMED.get(page)
    if not e:
        return None, None
    if len(hits) != e['count']:
        return e['why'], False
    for classes, _ in hits:
        if not any(c in e['classes'] for c in classes):
            return e['why'], False
    return e['why'], True


'''

# ---- what goes into Show-RowActionDrift.py ------------------------------
REP_OLD = """# NOT COUNTED AS DRIFT - named so the blind spot is visible, not so the
# report fails on work nobody has agreed to do. RA-3 wraps them.
if loose:
    n = sum(len(v) for v in loose.values())
    line('   NOT IN A .row-actions WRAPPER - %d button(s) on %d page(s).'
         % (n, len(loose)))
    line('   The ordering standard cannot be read on these. Until RA-2')
    line('   the glyph census could not see them either.')
    for pg in sorted(loose):
        seen = sorted({' '.join(c) or '(no icon class)'
                       for c, _ in loose[pg]})
        line('     %-40s %2d  %s' % (pg, len(loose[pg]), ', '.join(seen)))
    line()
"""

REP_NEW = '''# TWO LISTS, NOT ONE.                              [RA-5, 5 Oct 2026]
#
# Four buttons that are deliberately not in an action column, carrying
# the reason they are not, read differently from four nobody has looked
# at - and that difference is most of what a drift report is for. The
# register is in alv_rowactions.NAMED, beside the order itself.
#
# A page in the register whose count has MOVED is a problem, not an
# exemption: the register pins a number so that the next loose button on
# one of these pages is reported rather than inherited.
named_pages, bare = {}, {}
for pg, hits in loose.items():
    why, exact = RA.named(pg, hits)
    if why and exact:
        named_pages[pg] = (hits, why)
    elif why:
        problems += 1
        bare[pg] = hits
        line('   REGISTERED COUNT HAS MOVED - %s now has %d loose '
             'button(s).' % (pg, len(hits)))
        line('   alv_rowactions.NAMED exempts %d. The new one is not '
             'covered;' % RA.NAMED[pg]['count'])
        line('   look at it and either wrap it or add it to the register.')
        line()
    else:
        bare[pg] = hits

if named_pages:
    n = sum(len(v[0]) for v in named_pages.values())
    line('   NAMED, NOT IN A WRAPPER - %d button(s) on %d page(s).'
         % (n, len(named_pages)))
    line('   Single controls beside the thing they act on, by decision.')
    for pg in sorted(named_pages):
        hits, why = named_pages[pg]
        seen = sorted({' '.join(c) or '(no icon class)' for c, _ in hits})
        line('     %-40s %2d  %s' % (pg, len(hits), ', '.join(seen)))
        for ln in textwrap.wrap(why, 62):
            line('       %s' % ln)
    line()

# NOT COUNTED AS DRIFT - named so the blind spot is visible, not so the
# report fails on work nobody has agreed to do.
if bare:
    n = sum(len(v) for v in bare.values())
    line('   NOT IN A .row-actions WRAPPER - %d button(s) on %d page(s).'
         % (n, len(bare)))
    line('   The ordering standard cannot be read on these. Until RA-2')
    line('   the glyph census could not see them either.')
    for pg in sorted(bare):
        seen = sorted({' '.join(c) or '(no icon class)'
                       for c, _ in bare[pg]})
        line('     %-40s %2d  %s' % (pg, len(bare[pg]), ', '.join(seen)))
    line()
'''

IMPORT_OLD = 'import os'
IMPORT_NEW = 'import os\nimport textwrap'


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def backup(path):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def fit(text, block):
    if '\r\n' in text:
        return block.replace('\r\n', '\n').replace('\n', '\r\n')
    return block.replace('\r\n', '\n')


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    edits = 0

    ra = read(RA)
    if 'NAMED = {' not in ra:
        n = ra.count(RA_ANCHOR)
        if n != 1:
            raise SystemExit('RA-5: %s in %s matched %d times, expected 1'
                             % (RA_ANCHOR, RA, n))
        at = ra.index(RA_ANCHOR)
        ra = ra[:at] + fit(ra, RA_BLOCK) + ra[at:]
        edits += 1
        if not check:
            backup(RA)
            write(RA, ra)

    rep = read(REPORT)
    if 'NAMED, NOT IN A WRAPPER' not in rep:
        n = rep.count(REP_OLD)
        if n != 1:
            raise SystemExit('RA-5: the loose-button block in %s matched %d '
                             'times, expected 1 - the report has changed '
                             'since this was read' % (REPORT, n))
        rep = rep.replace(REP_OLD, fit(rep, REP_NEW), 1)
        if 'import textwrap' not in rep:
            k = rep.count(IMPORT_OLD)
            if k < 1:
                raise SystemExit('RA-5: %s has no %r to anchor the import on'
                                 % (REPORT, IMPORT_OLD))
            rep = rep.replace(IMPORT_OLD, fit(rep, IMPORT_NEW), 1)
        # THE REPORT MUST STILL BE ABLE TO RAISE A PROBLEM. The new block
        # adds to `problems`, and that name has to exist before it.
        if 'problems' not in rep[:rep.index('NAMED, NOT IN A WRAPPER')]:
            raise SystemExit('RA-5: `problems` is not in scope where the '
                             'register reports one')
        edits += 1
        if not check:
            backup(REPORT)
            write(REPORT, rep)

    print('RA-5  files changed : %d' % edits)
    if check:
        if edits:
            print('RA-5  NOT APPLIED')
            return 1
        print('RA-5  applied')
        return 0
    print('RA-5  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
