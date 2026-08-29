#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A closed row with no past is holding nothing, and can say so.

THE REPORT. Dikaiosynis shows two Company Tax rows at zero in the Expenses
list. They appear in no year of the P&L and in no column of the new
year-on-year matrix. Delete is greyed out. So the system is holding a record
it cannot justify and will not let go of.

WHY THE ROW IS KEPT AT ALL, and why that reasoning does not reach this case.
`_fh_close_expense` zeroes an un-ticked pro-rata row and keeps it:

    Deleting the row instead would take its PAST with it - the P&L only
    re-colours rows that still exist, so every prior year would silently
    lose that property's share.

Correct - when there IS a past. The matrix proved there is not: Dikaiosynis
carried nothing in any year. The row anchors an empty history. The
justification has expired and nobody noticed, because nothing ever asked.

AND THE DELETE GUARD TESTS THE WRONG THING. It refuses every pro-rata row,
for a reason that is exactly right about a LIVE one:

    Remove one row and the rest still hold shares computed for a larger
    split, so the line quietly stops adding up to the charge actually owed.

A CLOSED row holds no share. The others were re-divided when it was
un-ticked. Removing it changes no figure anywhere. The guard is refusing on a
hazard that no longer exists - it tests what the row IS, not what it HOLDS.

That is the fourth time in a week: membership decided by kind or by existence
rather than by content. The anchor rule, the linked set, the valuation
denominator, and now this.

WHAT THIS ROUND DOES.

  * Two facts are attached to every row the Expenses list draws:
    `is_closed` (carries nothing now) and `fh_has_past` (its history carries
    something). One extra query for the page, beside the one already there.
  * A closed row reads CLOSED rather than a bare zero. A zero and a closure
    are different things, and the list drew them identically - the same
    distinction the matrix makes with a dash.
  * A pro-rata row may be deleted WHEN IT IS SPENT: closed, and with nothing
    in its history. The refusal stands in every other case, and now says
    which case it is - "still carries a share" and "closed, but 2023 and
    2024 still report it" are different sentences and different advice.

WHAT IT DOES NOT DO. It does not delete anything by itself, it does not
change what a live row can do, and it moves no figure - a row that carries
nothing and whose history carries nothing contributes nothing to any year,
which is precisely why removing it is safe. The suite proves that rather
than asserting it.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, ast, shutil

ROOT   = os.path.dirname(os.path.abspath(__file__))
TPL    = os.path.join(ROOT, 'pages', 'templates')
PAGE   = os.path.join(TPL, 'finance_expense.html')
VIEW   = os.path.join(ROOT, 'pages', 'views', 'finance.py')
CHECK  = '--check' in sys.argv
SUFFIX = '.bak_spentrow'

# ---------------------------------------------------------------------------
# 1. the two facts, attached where the counts already are
# ---------------------------------------------------------------------------
V_OLD_ATTACH = """    for _prop_row in properties:
        for _exp_row in _prop_row.expense_set.all():
            _n, _first = summary.get(_exp_row.expense_id, (0, None))
            _exp_row.fh_count = _n
            _exp_row.fh_from = _first
    return properties"""
V_NEW_ATTACH = """    # WHICH ROWS HAVE A PAST WORTH KEEPING.
    #
    # A closed pro-rata row is kept so the P&L can still colour the years it
    # carried a share in. That reasoning needs there to BE such a year. A row
    # whose every snapshot is zero or empty anchors nothing, and the Expenses
    # list was drawing it as an ordinary expense of zero with Delete greyed
    # out - a record the system could neither justify nor release.
    #
    # One more query for the whole page: the source_pks that have at least one
    # snapshot carrying something. A Q across the thirteen columns rather than
    # thirteen queries or a Python pass over every snapshot ever written.
    try:
        _q = Q()
        for _f in ('amount',) + tuple(_FH_MONTHS):
            _q |= Q(**{_f + '__isnull': False}) & ~Q(**{_f: 0})
        carried = set(FinancialFigureHistory.objects
                      .filter(kind=FinancialFigureHistory.KIND_BUDGET)
                      .filter(_q)
                      .values_list('source_pk', flat=True))
    except Exception:
        # Fail-safe in the same direction as the count above: if this cannot
        # be worked out, every row is treated as HAVING a past, which is the
        # conservative answer - it keeps Delete greyed out rather than
        # offering to remove something whose history we could not read.
        logger.exception('_fh_attach_expense_history: past scan failed')
        carried = None

    for _prop_row in properties:
        for _exp_row in _prop_row.expense_set.all():
            _n, _first = summary.get(_exp_row.expense_id, (0, None))
            _exp_row.fh_count = _n
            _exp_row.fh_from = _first
            _exp_row.is_closed = not (_exp_row.expense_amount or 0)
            _exp_row.fh_has_past = (True if carried is None
                                    else _exp_row.expense_id in carried)
            # SPENT: it holds nothing and never did. Only these may be
            # removed, and only these are offered a Delete.
            _exp_row.is_spent = _exp_row.is_closed and not _exp_row.fh_has_past
    return properties"""

# ---------------------------------------------------------------------------
# 2. the guard learns what the row HOLDS
# ---------------------------------------------------------------------------
V_OLD_GUARD = """        if ((getattr(exp.expense_line_types, 'expense_line_types_prorata', '')
                or '').strip().lower() == 'yes'):
            messages.error(
                request,
                "That is a pro-rata expense, so it cannot be deleted on its "
                "own \\u2014 the other properties would be left holding shares of a "
                "larger split and the line would no longer add up. Edit the "
                "line and un-tick the property instead: the rest take up its "
                "share, and this one stops from the date you choose.")
            return redirect('finance_expense')"""
V_NEW_GUARD = """        # ... EXCEPT when the row holds nothing and never did.
        #
        # The paragraph above is exactly right about a LIVE row. A CLOSED one
        # holds no share - the others were re-divided when it was un-ticked -
        # so removing it changes no figure anywhere. And if its history is
        # empty too, there is no past for the row to anchor. The guard was
        # testing what the row IS rather than what it HOLDS.
        _is_prorata = ((getattr(exp.expense_line_types,
                                'expense_line_types_prorata', '')
                        or '').strip().lower() == 'yes')
        _closed = not (exp.expense_amount or 0)
        _has_past = _expense_has_past(exp.expense_id)

        if _is_prorata and not (_closed and not _has_past):
            # Two different situations, and they need different advice.
            if _closed and _has_past:
                messages.error(
                    request,
                    "That row is already closed, and it is kept on purpose: "
                    "earlier years still report the share it carried. "
                    "Removing it would take that past with it.")
            else:
                messages.error(
                    request,
                    "That is a pro-rata expense, so it cannot be deleted on "
                    "its own \\u2014 the other properties would be left holding "
                    "shares of a larger split and the line would no longer "
                    "add up. Edit the line and un-tick the property instead: "
                    "the rest take up its share, and this one stops from the "
                    "date you choose.")
            return redirect('finance_expense')

        if _is_prorata:
            # Spent: closed, and with nothing behind it. Closing it again
            # would do nothing, so the only meaningful operation is removal.
            mode = 'purge'"""

V_OLD_HELPER = """def _fh_attach_expense_history(properties):"""
V_NEW_HELPER = '''def _expense_has_past(expense_id):
    """Does this row's history carry anything at all?

    One row, asked directly - the list page answers the same question for
    every row at once in _fh_attach_expense_history. Both go through the same
    definition: a snapshot carries something when any of the twelve months or
    the amount is set and not zero.

    Fails CLOSED: if the history cannot be read, the answer is "yes, it has a
    past", which keeps a row rather than removing one on a guess.
    """
    try:
        _q = Q()
        for _f in ('amount',) + tuple(_FH_MONTHS):
            _q |= Q(**{_f + '__isnull': False}) & ~Q(**{_f: 0})
        return (FinancialFigureHistory.objects
                .filter(kind=FinancialFigureHistory.KIND_BUDGET,
                        source_pk=expense_id)
                .filter(_q).exists())
    except Exception:
        logger.exception('_expense_has_past failed - assuming it has one')
        return True


def _fh_attach_expense_history(properties):'''

V_OLD_IMPORT = "from django.db.models import (Count, Min, OuterRef, Prefetch, Subquery, Sum)"
V_NEW_IMPORT = "from django.db.models import (Count, Min, OuterRef, Prefetch, Q, Subquery, Sum)"

V_OLD_MONTHS = """from pages.models import (
    props, prop_values,"""
V_NEW_MONTHS = """from pages.models import (
    _FH_MONTHS,
    props, prop_values,"""

# ---------------------------------------------------------------------------
# 3. the list says which
# ---------------------------------------------------------------------------
P_OLD_CELL = """                                    <td class="amount-cell">€ {{ exp.expense_amount|floatformat:0|intcomma }}</td>"""
P_NEW_CELL = """                                    {# A zero and a closure are different things, and this cell drew them identically. #}
                                    {# Same distinction the year-on-year matrix makes with a dash. #}
                                    <td class="amount-cell">
                                        {% if exp.is_closed %}
                                            <span class="exp-closed-pill"
                                                  title="{% if exp.fh_has_past %}Closed - kept because earlier years still report the share it carried{% else %}Closed, and it carried nothing in any year{% endif %}">Closed</span>
                                        {% else %}
                                            € {{ exp.expense_amount|floatformat:0|intcomma }}
                                        {% endif %}
                                    </td>"""

P_OLD_DELETE = """                                                {% if exp.expense_line_types.expense_line_types_prorata == 'Yes' %}
                                                    {# A share of the line type amount - deleting one row would leave the others holding shares of a larger split. #}
                                                    <span class="btn-row-delete-disabled" title="Pro-rata expense &mdash; remove this property by editing the line and un-ticking it, so the others take up its share">
                                                        <i class="fas fa-trash-alt"></i> Delete
                                                    </span>
                                                {% else %}"""
P_NEW_DELETE = """                                                {% if exp.expense_line_types.expense_line_types_prorata == 'Yes' and not exp.is_spent %}
                                                    {# A share of the line type amount - deleting one row would leave the others holding shares of a larger split. #}
                                                    {# Unless it is SPENT: closed, and carrying nothing in its history either. Then it holds no share and anchors no past. #}
                                                    <span class="btn-row-delete-disabled" title="{% if exp.is_closed %}Already closed &mdash; kept because earlier years still report the share it carried{% else %}Pro-rata expense &mdash; remove this property by editing the line and un-ticking it, so the others take up its share{% endif %}">
                                                        <i class="fas fa-trash-alt"></i> Delete
                                                    </span>
                                                {% else %}"""

P_CSS_ANCHOR = """.expense-view-bar {"""
P_CSS = """/* A row that has been closed. It is not an expense of zero - it is a row
   that stopped, kept only so the years it did carry still resolve. The
   neutral tone, because a closure is not a verdict. */
.exp-closed-pill {
    display: inline-block;
    padding: 1px 9px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .02em;
    background: var(--alv-neutral-soft);
    color: var(--alv-neutral);
}

.expense-view-bar {"""

EDITS_VIEW = [
    ('Q is imported', V_OLD_IMPORT, V_NEW_IMPORT),
    ('and the month field names, so they are not written down twice',
     V_OLD_MONTHS, V_NEW_MONTHS),
    ('one definition of "does this row have a past"', V_OLD_HELPER, V_NEW_HELPER),
    ('every listed row carries is_closed / fh_has_past / is_spent',
     V_OLD_ATTACH, V_NEW_ATTACH),
    ('and the delete guard asks what the row HOLDS, not what it is',
     V_OLD_GUARD, V_NEW_GUARD),
]
EDITS_PAGE = [
    ('a closed row reads CLOSED, not a bare zero', P_OLD_CELL, P_NEW_CELL),
    ('and a SPENT one can finally be removed', P_OLD_DELETE, P_NEW_DELETE),
    ('the pill is on a house token', P_CSS_ANCHOR, P_CSS),
]


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def one(text, old, new, what):
    n = text.count(old)
    if n != 1:
        sys.exit('! %s did not match exactly once (%d) - the file may already '
                 'have been edited:\n%s' % (what, n, old[:200]))
    return text.replace(old, new, 1)


def nocomment(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    # NO re.S on {# #}. Django's lexer has no DOTALL, so a comment that opens
    # on one line and closes on the next is NOT a comment - it is rendered
    # text. Stripping it here with re.S would make this function agree that a
    # broken comment is fine, which is exactly how the broken one got past.
    text = re.sub(r'\{#[^\r\n]*?#\}', '', text)

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


def main():
    for p in (PAGE, VIEW):
        if not os.path.exists(p):
            sys.exit('! %s not found - run from the repo root' % p)
    vs, pg = read(VIEW), read(PAGE)

    if 'def _expense_has_past' in vs:
        print('  spent rows                    already applied')
        print('\n  0 file(s) changed')
        return

    for name, old, new in EDITS_VIEW:
        vs = one(vs, old, new, name)
    for name, old, new in EDITS_PAGE:
        pg = one(pg, old, new, name)

    # ---- self-check BEFORE anything is written
    bad = []
    try:
        tree = ast.parse(vs)
    except SyntaxError as exc:
        sys.exit('! the patched finance.py does not parse: %s' % exc)
    fns = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}

    if '_expense_has_past' not in fns:
        bad.append('the helper is not defined')
    else:
        h = ast.unparse(ast.Module(body=fns['_expense_has_past'].body[1:],
                                   type_ignores=[]))
        if 'return True' not in h:
            bad.append('the helper does not fail closed')
        if '_FH_MONTHS' not in h:
            bad.append('the helper does not read the month columns')

    # get_source_segment, NOT unparse: ast.unparse re-parenthesises, so a
    # source-form condition never appears verbatim in it. The first version
    # of this check looked for the written form in the normalised output and
    # reported the guard unchanged when it had changed correctly.
    _del = ast.get_source_segment(vs, fns['finance_expense_delete']) or ''
    if '_expense_has_past' not in _del:
        bad.append('the delete guard does not ask whether the row has a past')
    _test = [n.test for n in ast.walk(fns['finance_expense_delete'])
             if isinstance(n, ast.If)
             and '_is_prorata' in ast.unparse(n.test)]
    if not _test or not all(x in ast.unparse(_test[0])
                            for x in ('_closed', '_has_past')):
        bad.append('the guard still refuses on KIND rather than on content')
    # A LIVE pro-rata row must still be refused. That is the half of the old
    # reasoning which is still entirely correct, and the one worth losing
    # sleep over if it went.
    if 'the other properties would be left holding' not in _del:
        bad.append('the refusal for a live pro-rata row is gone')
    if "mode = 'purge'" not in _del:
        bad.append('a spent row is closed again rather than removed, which '
                   'would do nothing at all')

    _att = ast.unparse(fns['_fh_attach_expense_history'])
    for want in ('is_closed', 'fh_has_past', 'is_spent'):
        if want not in _att:
            bad.append('the list does not attach %s' % want)
    if 'carried = None' not in _att:
        bad.append('the page does not fail safe when the history cannot be read')

    _pc = nocomment(pg)
    if 'exp-closed-pill' not in _pc:
        bad.append('the closed pill is not drawn')
    if 'not exp.is_spent' not in _pc:
        bad.append('a spent row is still refused a Delete')
    if not re.search(r'\.exp-closed-pill\s*\{[^}]*var\(--alv-neutral', _pc):
        bad.append('the pill carries a literal rather than a house token')
    if re.search(r'\.exp-closed-pill\s*\{[^}]*#[0-9a-fA-F]{3,6}', _pc):
        bad.append('a raw hex entered the page for it')

    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', pg, re.S))
    if css.count('{') != css.count('}'):
        bad.append('CSS braces do not balance')
    for tag in ('div', 'td', 'span'):
        a = len(re.findall(r'<%s\b' % tag, pg))
        z = len(re.findall(r'</%s\s*>' % tag, pg))
        if a != z:
            bad.append('%s tags do not balance (%d/%d)' % (tag, a, z))
    # The check every other patcher in this project carries and this one was
    # written without. It is the one that catches a multi-line {# #}.
    for i, line in enumerate(pg.split('\n'), 1):
        if line.count('{#') != line.count('#}'):
            bad.append('line %d opens a {# comment it does not close on the '
                       'same line - Django would RENDER it' % i)
            break
    for o, c in ((r'\{%\s*if\b', r'\{%\s*endif\s*%\}'),
                 (r'\{%\s*for\b', r'\{%\s*endfor\s*%\}'),
                 (r'\{%\s*with\b', r'\{%\s*endwith\s*%\}')):
        if len(re.findall(o, pg)) != len(re.findall(c, pg)):
            bad.append('a Django block no longer balances (%s)' % o)

    if bad:
        sys.exit('! spent-row self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    for name, _o, _n in EDITS_VIEW + EDITS_PAGE:
        print('  %s' % name)

    if not CHECK:
        for path, out in ((VIEW, vs), (PAGE, pg)):
            b = path + SUFFIX
            if not os.path.exists(b):
                shutil.copy2(path, b)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(out)

    print('\n  2 file(s) %s' % ('would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
