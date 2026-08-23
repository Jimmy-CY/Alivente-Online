#!/usr/bin/env python3
"""
apply_prorata_delete_guard.py
=============================

A pro-rata expense row cannot be deleted on its own.

Why
---
A pro-rata row is not a figure in its own right - it is a SHARE of the amount
held on the line type. Company Tax is 3,300 an instalment, sliced across ten
properties by current value. Nothing in the database enforces that the slices
add back up to the whole.

Delete Palikaridi's row and the other nine still hold shares computed for a
TEN-way split. The line now totals about 5,940 a year against a charge that is
still 6,600, and nothing anywhere flags it. The P&L simply reports less tax
than is owed.

Un-ticking Palikaridi on the edit screen does something different and correct:
the same 3,300 is re-divided across the remaining nine, and Palikaridi is
closed with a zero snapshot from the chosen date - the identical effect on that
row as "stop it from a date", with the distribution kept whole.

So the two routes are not two ways of doing one thing. One is right; the other
loses money from the report silently.

What changes
------------
1. The Expenses list greys out Delete on a pro-rata row, with a tooltip
   pointing at the edit screen. Same treatment the list already gives a row
   the user has no permission to delete.

2. `finance_expense_delete` refuses one server-side. A greyed-out control is a
   hint, not a guard - the POST can still be replayed.

   Both modes are blocked, not just "stop". A single slice of a distribution is
   never independently a mistake: either the whole distribution is wrong, and
   the line type is deleted with "remove completely", or one property does not
   belong, and un-ticking is the answer.

3. The pro-rata panel on the edit screen gains a line about what un-ticking
   actually does to the total. The remaining properties absorb the freed share,
   so the charge stays whole - which is right for a portfolio charge being
   apportioned, and wrong if the property was sold and the charge itself has
   dropped. The software cannot tell those apart; the note asks.

A row whose line type is no longer marked pro-rata becomes deletable again,
which is correct - at that point it is a standalone figure.

Files touched
-------------
  pages/views/finance.py                        finance_expense_delete guard
  pages/templates/finance_expense.html          Delete greyed out
  pages/templates/finance_expense_edit.html     the redistribution note

Idempotent; backs each file up on first run (.bak_prdelete).

    python apply_prorata_delete_guard.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))

FINANCE = os.path.join(ROOT, 'pages', 'views', 'finance.py')
TPL = os.path.join(ROOT, 'pages', 'templates')
LIST_FORM = os.path.join(TPL, 'finance_expense.html')
EDIT_FORM = os.path.join(TPL, 'finance_expense_edit.html')

FIN_SENTINEL = 'That is a pro-rata expense'
LIST_SENTINEL = 'btn-row-delete-disabled" title="Pro-rata'
EDIT_SENTINEL = 'take up its share'


# ---------------------------------------------------------------------------
# 1. finance.py - refuse it server-side
# ---------------------------------------------------------------------------

FIN_ANCHOR = '''        exp = get_object_or_404(expense, expense_id=expense_id)
        with transaction.atomic():
'''

FIN_NEW = '''        exp = get_object_or_404(expense, expense_id=expense_id)

        # A pro-rata row is a SHARE of the amount held on the line type, not a
        # figure in its own right. Remove one row and the rest still hold
        # shares computed for a larger split, so the line quietly stops adding
        # up to the charge actually owed - and nothing flags it.
        #
        # Un-ticking the property on the edit screen re-divides the amount
        # across the others and closes this row with the same zero snapshot.
        # That is the correct operation, so it is the only one offered.
        #
        # Blocked for BOTH modes. One slice of a distribution is never
        # independently a mistake: either the whole distribution is wrong (in
        # which case the line type is deleted) or one property does not belong
        # (in which case it is un-ticked).
        if ((getattr(exp.expense_line_types, 'expense_line_types_prorata', '')
                or '').strip().lower() == 'yes'):
            messages.error(
                request,
                "That is a pro-rata expense, so it cannot be deleted on its "
                "own \\u2014 the other properties would be left holding shares of a "
                "larger split and the line would no longer add up. Edit the "
                "line and un-tick the property instead: the rest take up its "
                "share, and this one stops from the date you choose.")
            return redirect('finance_expense')

        with transaction.atomic():
'''


# ---------------------------------------------------------------------------
# 2. the Expenses list - grey it out
# ---------------------------------------------------------------------------

LIST_OLD = '''                                                <form method="post" action="{% url 'finance_expense_delete' exp.expense_id %}"
                                                      class="row-action-form js-delete-form"
                                                      data-label="{{ pro.prop_name }} &mdash; {{ exp.expense_line_types.expense_line_types_name }}"
                                                      data-history="{{ exp.fh_count|default:0 }}"
                                                      data-history-from="{% if exp.fh_from %}{{ exp.fh_from|date:'M Y' }}{% endif %}">
                                                    {% csrf_token %}
                                                    <input type="hidden" name="delete_mode" value="close">
                                                    <input type="hidden" name="effective_date" value="">
                                                    <button type="button" class="btn-row-delete js-delete-open">
                                                        <i class="fas fa-trash-alt"></i> Delete
                                                    </button>
                                                </form>
'''

LIST_NEW = '''                                                {% if exp.expense_line_types.expense_line_types_prorata == 'Yes' %}
                                                    {# A share of the line type amount - deleting one row would leave the others holding shares of a larger split. #}
                                                    <span class="btn-row-delete-disabled" title="Pro-rata expense &mdash; remove this property by editing the line and un-ticking it, so the others take up its share">
                                                        <i class="fas fa-trash-alt"></i> Delete
                                                    </span>
                                                {% else %}
                                                <form method="post" action="{% url 'finance_expense_delete' exp.expense_id %}"
                                                      class="row-action-form js-delete-form"
                                                      data-label="{{ pro.prop_name }} &mdash; {{ exp.expense_line_types.expense_line_types_name }}"
                                                      data-history="{{ exp.fh_count|default:0 }}"
                                                      data-history-from="{% if exp.fh_from %}{{ exp.fh_from|date:'M Y' }}{% endif %}">
                                                    {% csrf_token %}
                                                    <input type="hidden" name="delete_mode" value="close">
                                                    <input type="hidden" name="effective_date" value="">
                                                    <button type="button" class="btn-row-delete js-delete-open">
                                                        <i class="fas fa-trash-alt"></i> Delete
                                                    </button>
                                                </form>
                                                {% endif %}
'''


# ---------------------------------------------------------------------------
# 3. the edit screen - say what un-ticking does to the total
# ---------------------------------------------------------------------------

EDIT_OLD = '''            <div class="prorata-banner">
                <i class="fas fa-info-circle"></i>
                This expense type distributes a fixed amount across selected properties based on their current value.
                Properties already in this distribution are pre-selected below.
            </div>
'''

EDIT_NEW = '''            <div class="prorata-banner">
                <i class="fas fa-info-circle"></i>
                This expense type distributes a fixed amount across selected properties based on their current value.
                Properties already in this distribution are pre-selected below.
                <br>
                <strong>Removing a property?</strong> Un-tick it here rather than deleting its
                expense &mdash; the properties you leave ticked take up its share, and the
                un-ticked one stops from the date above while keeping its earlier years.
                The total stays the same, so if the charge itself has changed, update the
                amount on the Expense Line Type first.
            </div>
'''


# ---------------------------------------------------------------------------

def sniff(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return raw.decode(enc).replace('\r\n', '\n'), enc, nl


def write_back(path, text, enc, nl):
    bak = path + '.bak_prdelete'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    with open(path, 'w', encoding=enc, newline='') as fh:
        fh.write(text.replace('\n', nl) if nl == '\r\n' else text)


def main():
    for p in (FINANCE, LIST_FORM, EDIT_FORM):
        if not os.path.exists(p):
            print('! %s not found - run from the project root'
                  % os.path.relpath(p, ROOT))
            return 1

    fin_src, fin_enc, fin_nl = sniff(FINANCE)
    list_src, list_enc, list_nl = sniff(LIST_FORM)
    edit_src, edit_enc, edit_nl = sniff(EDIT_FORM)

    if 'js-delete-form' not in list_src:
        print('! apply_delete_choice.py has not been applied.')
        print('  Run that first - this guards the control it adds.')
        return 1

    fin_done = FIN_SENTINEL in fin_src
    list_done = LIST_SENTINEL in list_src
    edit_done = EDIT_SENTINEL in edit_src

    if fin_done and list_done and edit_done:
        print('= already applied - nothing to do')
        return 0

    problems = []

    def need(label, src, anchor, times=1):
        n = src.count(anchor)
        if n != times:
            problems.append('%s: matched %d times, expected %d' % (label, n, times))

    if not fin_done:
        need('finance.py delete lookup', fin_src, FIN_ANCHOR)
    if not list_done:
        need('expenses list delete form', list_src, LIST_OLD)
    if not edit_done:
        need('edit screen pro-rata banner', edit_src, EDIT_OLD)

    if problems:
        for p in problems:
            print('! ' + p)
        print('  Aborting - nothing written.')
        return 1

    if not fin_done:
        fin_src = fin_src.replace(FIN_ANCHOR, FIN_NEW, 1)
    if not list_done:
        list_src = list_src.replace(LIST_OLD, LIST_NEW, 1)
    if not edit_done:
        edit_src = edit_src.replace(EDIT_OLD, EDIT_NEW, 1)

    try:
        compile(fin_src, 'finance.py', 'exec')
    except SyntaxError as exc:
        print('! patched finance.py does not compile: %s (line %s)'
              % (exc.msg, exc.lineno))
        print('  Nothing written.')
        return 1

    if CHECK:
        print('= check only: every anchor matched and finance.py compiles, '
              'nothing written')
        return 0

    if not fin_done:
        write_back(FINANCE, fin_src, fin_enc, fin_nl)
        print('+ pages/views/finance.py     pro-rata rows refused server-side')
    if not list_done:
        write_back(LIST_FORM, list_src, list_enc, list_nl)
        print('+ pages/templates/finance_expense.html        Delete greyed out')
    if not edit_done:
        write_back(EDIT_FORM, edit_src, edit_enc, edit_nl)
        print('+ pages/templates/finance_expense_edit.html   redistribution note')

    print('')
    print('Backups: .bak_prdelete alongside each file. No migration needed.')
    print('Verify:  python test_delete_choice.py')
    print('         python manage.py check')
    return 0


if __name__ == '__main__':
    sys.exit(main())
