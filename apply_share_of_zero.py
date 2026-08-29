#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A share of zero is not a share.

THE REPORT. Un-tick an inactive property from a pro-rata split, save, and it
comes back TICKED next time the screen is opened - with the amber banner up
again, and the next Calculate Pro-Rata handing its share straight back. Two
zeroed rows sit in the Expenses list looking correct while the screens that
decide who is in the distribution carry on counting them.

THE CAUSE, IN ONE WORD: MEMBERSHIP.

`_fh_close_expense` does not delete an un-ticked row. It sets the amount and
all twelve months to zero and KEEPS it, deliberately:

    Deleting the row instead would take its PAST with it - the P&L only
    re-colours rows that still exist, so every prior year would silently
    lose that property's share.

That is right, and it is not what went wrong. What went wrong is that three
separate places then ask *does a row exist* when what they mean is *does it
carry a share*:

  1. `finance_expense_edit`   - which checkboxes are pre-ticked.
  2. `preview_valuation_change` - who is in the split, and therefore in the
     denominator every other property is divided by.
  3. .. and the same call decides `affected_expenses`, which is which
     distributions the preview shows at all.

So a released property is still "linked", still ticked, still funded.

ONE HELPER, USED IN ALL THREE, so the screens cannot drift apart again.

WHAT MOVES AND WHAT DOES NOT - said plainly, because half of this changes
money and half of it cannot.

  * THE PRE-TICKS CANNOT MOVE A FIGURE. A row at zero contributes nothing to
    any P&L period, so leaving it un-ticked and letting the next save close
    it again changes no number anywhere. What changes is that the release
    STICKS.
  * THE VALUATION PREVIEW DOES MOVE FIGURES, and that is the point. A
    property carrying nothing leaves the denominator, so the ten that were
    funding it stop. The pot is unchanged - it is fixed by the line type -
    so every remaining share rises. This was item 8.1, and framing it as
    membership rather than as "should inactive properties be excluded"
    is what made it answerable: it is not a policy about inactive
    properties, it is that a property with no share is not in the split.
  * THE COMMIT CANNOT DISAGREE WITH THE PREVIEW.
    `finance_valuations_edit_and_recalc_commit` replays the preview payload
    row by row rather than rebuilding the set, so narrowing the preview
    narrows the save. The suite asserts that, because it is the reason this
    round touches one function instead of two.

THE EDGE THIS ROUND ACCEPTS, NAMED RATHER THAN HIDDEN. A property with a
current value of 0 computes a share of 0, so its row is 0, so it too comes up
un-ticked. It contributes nothing either way, and one click puts it back -
visibly, rather than silently holding a share it cannot carry.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, ast, shutil

ROOT   = os.path.dirname(os.path.abspath(__file__))
VIEW   = os.path.join(ROOT, 'pages', 'views', 'finance.py')
CHECK  = '--check' in sys.argv
SUFFIX = '.bak_shareofzero'

HELPER = '''def carries_a_share(qs):
    """The rows in `qs` that actually hold money.

    An un-ticked pro-rata row is CLOSED, not deleted - _fh_close_expense
    zeroes the amount and all twelve months and keeps the row, so the P&L can
    still colour earlier years. That is deliberate. What is not deliberate is
    that three screens then read "a row exists" as "this property is in the
    distribution", so a released property came back ticked, the inactive
    banner kept firing, and the next recalculation handed its share back.

    One helper for all three, so they cannot drift apart again.

    A NULL amount counts as no share too: it is a row that has never carried
    anything. Both are excluded by the same test.
    """
    return qs.exclude(expense_amount=0).exclude(expense_amount__isnull=True)


def _fh_close_expense(exp):'''

OLD_HELPER_ANCHOR = 'def _fh_close_expense(exp):'

OLD_LINKED = """    linked_property_ids = list(
        expense.objects.filter(
            expense_line_types_id=existing_expense.expense_line_types_id,
            expense_types_id=existing_expense.expense_types_id,
        ).values_list('prop_id', flat=True)
    )"""
NEW_LINKED = """    # Which boxes are pre-ticked. A row closed by a previous un-tick is
    # still here - kept on purpose, so earlier years keep their share - but
    # it is no longer in the distribution, and ticking it again is how the
    # share got handed back.
    linked_property_ids = list(
        carries_a_share(expense.objects.filter(
            expense_line_types_id=existing_expense.expense_line_types_id,
            expense_types_id=existing_expense.expense_types_id,
        )).values_list('prop_id', flat=True)
    )"""

OLD_AFFECTED = """        affected_expenses = expense.objects.filter(
            prop_id=pv.prop_id,
            expense_line_types__expense_line_types_prorata='Yes',
        ).select_related('expense_line_types')"""
NEW_AFFECTED = """        # Which distributions this valuation actually reaches. A closed row
        # is not one of them - showing its line type would draw a group in
        # which nothing moves.
        affected_expenses = carries_a_share(expense.objects.filter(
            prop_id=pv.prop_id,
            expense_line_types__expense_line_types_prorata='Yes',
        )).select_related('expense_line_types')"""

OLD_LT = """            lt_expenses = expense.objects.filter(expense_line_types_id=lt_id).select_related('prop')
            unique_prop_ids = set(e.prop_id for e in lt_expenses)"""
NEW_LT = """            # THE DENOMINATOR. Everything below divides by the total current
            # value of THIS set, so a property that carries nothing must not
            # be in it - every other property was funding its share.
            lt_expenses = carries_a_share(
                expense.objects.filter(expense_line_types_id=lt_id)
            ).select_related('prop')
            unique_prop_ids = set(e.prop_id for e in lt_expenses)"""

EDITS = [
    ('one helper answers "does this row carry a share?"',
     OLD_HELPER_ANCHOR, HELPER),
    ('the edit screen pre-ticks only properties that carry one',
     OLD_LINKED, NEW_LINKED),
    ('the preview shows only distributions this valuation reaches',
     OLD_AFFECTED, NEW_AFFECTED),
    ('and its denominator counts only properties that carry a share',
     OLD_LT, NEW_LT),
]


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def main():
    if not os.path.exists(VIEW):
        sys.exit('! %s not found - run from the repo root' % VIEW)
    src = read(VIEW)

    if 'def carries_a_share' in src:
        print('  a share of zero                already applied')
        print('\n  0 file(s) changed')
        return

    out = src
    for name, old, new in EDITS:
        n = out.count(old)
        if n != 1:
            sys.exit('! "%s" did not match exactly once (%d) - the file may '
                     'already have been edited:\n%s' % (name, n, old[:160]))
        out = out.replace(old, new, 1)

    # ---- self-check BEFORE anything is written
    bad = []
    try:
        tree = ast.parse(out)
    except SyntaxError as exc:
        sys.exit('! the patched finance.py does not parse: %s' % exc)

    fns = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    if 'carries_a_share' not in fns:
        bad.append('the helper is not defined at all')
    else:
        h = ast.unparse(fns['carries_a_share'])
        for want in ("exclude(expense_amount=0)",
                     "exclude(expense_amount__isnull=True)"):
            if want not in h:
                bad.append('the helper does not %s' % want)

    # Every site that decides membership goes through it, and NO OTHER site
    # was changed. Counted, so a fourth caller appearing later is a decision
    # somebody has to make rather than something that happens quietly.
    n_calls = len(re.findall(r'\bcarries_a_share\(', out)) - 1   # less the def
    if n_calls != 3:
        bad.append('expected 3 call sites, found %d' % n_calls)
    for fn_name in ('finance_expense_edit', 'preview_valuation_change'):
        if fn_name not in fns:
            bad.append('%s vanished' % fn_name)
        elif 'carries_a_share' not in ast.unparse(fns[fn_name]):
            bad.append('%s does not use the helper' % fn_name)

    # THE ARITHMETIC IS UNTOUCHED. This round changes WHO is in the set, and
    # must not change what is done to them.
    prev = ast.unparse(fns['preview_valuation_change'])
    for keep in ("r['new_amount'] = round(pr_amount * r['current_value_new'] / total_cv_new, 2)",
                 "r['delta'] = round(r['new_amount'] - r['old_amount'], 2)",
                 "r['share_percentage_new'] = round(r['current_value_new'] / total_cv_new * 100, 2)"):
        if keep not in prev:
            bad.append('an existing calculation changed or moved: %s' % keep)

    # And the commit still REPLAYS the preview rather than rebuilding the set
    # - which is the reason narrowing one function is enough.
    commit = ast.unparse(fns.get('finance_valuations_edit_and_recalc_commit',
                                 ast.parse('def _(): pass').body[0]))
    if "preview_data['line_types']" not in commit:
        bad.append('the commit no longer replays the preview payload - it '
                   'would now need narrowing of its own')
    if 'expense_line_types__expense_line_types_prorata' in commit:
        bad.append('the commit has grown a participant set of its own')

    # The closing helper it all rests on is still there and still keeps rows.
    close = ast.unparse(fns.get('_fh_close_expense',
                                ast.parse('def _(): pass').body[0]))
    if '.delete()' in close or 'exp.expense_amount = 0' not in close:
        bad.append('_fh_close_expense no longer zeroes-and-keeps, which is '
                   'the whole premise of this round')

    if bad:
        sys.exit('! share-of-zero self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    for name, _o, _n in EDITS:
        print('  %s' % name)

    if not CHECK:
        b = VIEW + SUFFIX
        if not os.path.exists(b):
            shutil.copy2(VIEW, b)
        with open(VIEW, 'w', encoding='utf-8') as f:
            f.write(out)

    print('\n  1 file(s) %s' % ('would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
