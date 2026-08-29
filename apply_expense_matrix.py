#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""One expense, every year, every property - and two components base lacked.

WHAT WAS ASKED FOR. On the Expenses screen, a second view: pick an expense
line type and see a table with the years across the top, the contributing
properties down the side, scrolling sideways, with the property name and the
totals staying put.

FOUR THINGS WERE DECIDED BEFORE ANY OF THIS WAS BUILT:

  * Years run from the earliest year that line type has history for, through
    NEXT year - the P&L already projects one year forward.
  * One line type at a time, chosen from a picker. Stacking every line type
    would make the page the whole budget, which is the P&L's job.
  * Budgeted figures only. Actual Expenses is a different table with its own
    screen; two numbers per cell would need a second toggle and a decision
    nobody has taken.
  * It does not need to print. A frozen column and a sideways scroll mean
    nothing on paper, so no print rules were written and the matrix is
    hidden from them along with the rest of the furniture.

AND ONE MORE, TAKEN AFTER READING THE RESOLVER AND PUT BACK TO THE USER
BECAUSE IT MOVES FIGURES: NO PRO-RATING.

`property_annual_budgeted_expenses` counts a property's budget only from the
month it came into service, using its earliest lease start as a proxy for the
purchase - so a property bought in September carries four months of Company
Tax in its first year rather than twelve. That is right for the P&L, which is
answering "what did this cost me that year".

It is wrong here. The charge is distributed by value whether or not you owned
a property all year, so a pro-rated matrix would have a 2023 column summing to
less than the charge while its footer claimed to BE the charge. This screen
answers "how is this charge split"; the P&L answers the other question. The
matrix does not pro-rate, and says so under the table, so the difference is
documented rather than discovered.

TWO COMPONENTS ENTER base.html, BOTH OVERDUE.

  1. `.alv-seg`, a segmented control. Deferred twice on the grounds that one
     use does not justify a component. tenant_payment_days and
     financial_indicators each hand-roll one; this is the third asker, which
     is the point at which the rule says build it.
  2. `.alv-matrix`, a horizontally scrolling table with frozen edges. This one
     could NOT be `.table-container`: base sets `overflow: clip` there
     precisely so a sticky heading can pin, and a matrix needs
     `overflow-x: auto`. They are opposite requirements wearing one name -
     which is exactly the collision the sticky sweep walked around when it
     found `financial_indicators.html` and `vacancy_management.html` using
     `.table-container` for a horizontal scroller. Naming the pattern here is
     what lets those two stop colliding.

DELIBERATELY OUT OF SCOPE, so this round does not quietly become three:
migrating those two pages onto `.alv-matrix`, and the two hand-rolled toggles
onto `.alv-seg`. Both are follow-on rounds.

A CELL IS THE SUM OF THE TWELVE RESOLVED MONTHS, and a cell of zero renders
as an em-dash, not as 0.00. That is the same rule the share-of-zero round
applied to membership: a share of zero is not a share. It is what lets you
see that a property was in the split until 2024 and then was not, which the
Expenses list cannot currently show at all.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, ast, shutil

ROOT   = os.path.dirname(os.path.abspath(__file__))
TPL    = os.path.join(ROOT, 'pages', 'templates')
BASE   = os.path.join(TPL, 'base.html')
PAGE   = os.path.join(TPL, 'finance_expense.html')
VIEW   = os.path.join(ROOT, 'pages', 'views', 'finance.py')
CHECK  = '--check' in sys.argv
SUFFIX = '.bak_expmatrix'

# ---------------------------------------------------------------------------
# 1. base.html - the two components
# ---------------------------------------------------------------------------
BASE_ANCHOR = '/* ===== ALV-ICON-COLOURS v1 ===== */'

BASE_CSS = '''/* ===== ALV-SEG v1 ===== */
/* A segmented control: two or three views of the same screen, one of them
   current. Deferred twice as "one use does not justify a component" -
   tenant_payment_days and financial_indicators each hand-roll one, and this
   is the third asker.

   It is NOT the pill scale and NOT the button tones. A segment is not a verb
   you press to make something happen; it is which view you are looking at,
   so the pressed one is filled and the rest are quiet, and nothing here
   carries a semantic colour. */
.alv-seg {
    display: inline-flex;
    border: 1px solid var(--alv-line);
    border-radius: var(--alv-radius-sm);
    overflow: hidden;
    background: var(--alv-paper);
}
.alv-seg > * {
    appearance: none;
    border: 0;
    background: transparent;
    font: inherit;
    font-size: 13px;
    font-weight: 600;
    color: var(--alv-ink-soft);
    padding: 7px 14px;
    cursor: pointer;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    white-space: nowrap;
}
.alv-seg > * + * { border-left: 1px solid var(--alv-line); }
.alv-seg > [aria-pressed="true"],
.alv-seg > [aria-current="page"] {
    background: var(--alv-accent);
    color: var(--alv-on-accent);
}
.alv-seg > *:focus-visible { outline: 2px solid var(--alv-accent); outline-offset: -2px; }
@media (hover: hover) and (pointer: fine) {
    .alv-seg > *:not([aria-pressed="true"]):not([aria-current="page"]):hover {
        background: var(--alv-accent-soft);
        color: var(--alv-accent-ink);
    }
}

/* ===== ALV-MATRIX v1 ===== */
/* A table read across as well as down: years, months, buckets. It scrolls
   sideways and freezes its first column.

   THIS COULD NOT BE .table-container. That one sets `overflow: clip` on
   purpose - a sticky heading pins to its nearest SCROLLING ancestor, so a
   scroll container swallows it. A matrix needs `overflow-x: auto`, which is
   the opposite requirement. Two components, two names.

   Worth knowing when the next page needs one: financial_indicators.html and
   vacancy_management.html already use the NAME .table-container for exactly
   this, which is the collision the sticky sweep reported as its group D and
   deliberately left alone. They belong on this, in a round of their own. */
.alv-matrix-scroll {
    overflow-x: auto;
    background: var(--alv-paper);
    border-radius: var(--alv-radius);
}
table.alv-matrix {
    border-collapse: separate;
    border-spacing: 0;
    width: 100%;
    font-family: var(--alv-font-ui);
    font-variant-numeric: tabular-nums;
}
.alv-matrix th,
.alv-matrix td {
    padding: 10px 14px;
    white-space: nowrap;
    border-bottom: 1px solid var(--alv-line-soft);
    background: var(--alv-paper);
}
.alv-matrix thead th {
    position: sticky;
    top: 0;
    z-index: 2;
    background: var(--alv-surface);
    color: var(--alv-ink-strong);
    font-size: 13.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .01em;
    text-align: right;
    box-shadow: inset 0 -1px 0 var(--alv-line);
}
/* The frozen edges. Each needs a background of its own - a sticky cell is
   painted over by whatever scrolls under it otherwise - and a higher stacking
   order where the two overlap at the corners. */
.alv-matrix th.alv-matrix-row-head,
.alv-matrix td.alv-matrix-row-head {
    position: sticky;
    left: 0;
    z-index: 1;
    text-align: left;
    font-weight: 600;
    min-width: 190px;
    box-shadow: 1px 0 0 var(--alv-line);
}
.alv-matrix th.alv-matrix-total,
.alv-matrix td.alv-matrix-total {
    position: sticky;
    right: 0;
    z-index: 1;
    background: var(--alv-surface);
    box-shadow: -1px 0 0 var(--alv-line);
}
.alv-matrix thead th.alv-matrix-row-head,
.alv-matrix thead th.alv-matrix-total { z-index: 4; }
.alv-matrix td { text-align: right; }
@media (hover: hover) and (pointer: fine) {
    .alv-matrix tbody tr:hover td { background: var(--alv-accent-soft); }
}
.alv-matrix tfoot td {
    position: sticky;
    bottom: 0;
    z-index: 2;
    background: var(--alv-surface);
    font-weight: 700;
    box-shadow: inset 0 1px 0 var(--alv-line);
}
.alv-matrix tfoot td.alv-matrix-row-head,
.alv-matrix tfoot td.alv-matrix-total { z-index: 3; }
/* A cell where the property was not in the distribution at all. NOT zero -
   the whole point is that you can tell "was not in it" from "was in it and
   cost nothing", which is the distinction the Expenses list loses. */
.alv-matrix .alv-matrix-absent { color: var(--alv-ink-faint); }

@media print {
    /* Decided: this view does not print. A frozen column and a sideways
       scroll have no meaning on paper, so it goes with the rest of the
       furniture rather than printing something misleading. */
    .alv-seg, .alv-matrix-scroll { display: none !important; }
}

'''

# ---------------------------------------------------------------------------
# 2. finance.py - the figures
# ---------------------------------------------------------------------------
VIEW_HELPER = '''def expense_matrix(line_type_id, today_year=None):
    """One line type, resolved year by year, property by property.

    Returns {line_type, years, rows, totals, grand_total, first_year} where a
    row is {prop_id, prop_name, cells, total} and a cell is either a Decimal
    or None. NONE MEANS "not in the distribution that year" - a figure of
    zero is reported as None, deliberately, so the screen can draw a dash and
    the reader can tell a property that left from one that cost nothing.

    THE FIGURES COME FROM THE SAME RESOLVER THE P&L USES,
    resolve_year_months_bulk, rather than a second implementation of
    effective dating. Two answers to "what did this row carry in 2024" is one
    more than this system can afford.

    IT DOES NOT PRO-RATE. property_annual_budgeted_expenses counts a
    property's budget only from the month it came into service, which is
    right for the P&L - it is answering "what did this cost me". This screen
    answers "how is this charge split", and the charge is distributed by
    value whether or not the property was owned all year. Pro-rating here
    would leave a column summing to less than the charge under a footer
    claiming to be the charge. The template says so under the table.

    Carries no decorators: it is a helper, not a view.
    """
    from django.db.models import Min as _Min

    rows_qs = (expense.objects
               .filter(expense_line_types_id=line_type_id)
               .select_related('prop'))
    by_prop = {}
    for e in rows_qs:
        by_prop.setdefault(e.prop_id, {'prop_name': (e.prop.prop_name
                                                     if e.prop else 'Unknown'),
                                       'sources': []})
        by_prop[e.prop_id]['sources'].append(e)
    if not by_prop:
        return {'line_type': None, 'years': [], 'rows': [], 'totals': [],
                'grand_total': Decimal('0'), 'first_year': None}

    try:
        lt = expense_line_types.objects.get(expense_line_types_id=line_type_id)
    except expense_line_types.DoesNotExist:
        lt = None

    # The earliest year this line type actually CHANGED in.
    #
    # NOT the earliest history row. FH_BASELINE_DATE is 2000-01-01 and it is a
    # SENTINEL, not a date: _ensure_baseline writes one row at it the first
    # time a long-standing figure is edited, meaning "and it held this before
    # anybody recorded a change". Reading it as data made this table open on
    # the year 2000 and draw twenty-eight identical columns - the same figure
    # restated once a year for a quarter of a century, which is the baseline
    # being resolved forward, not a history.
    #
    # A baseline says the figure reaches back indefinitely, so it gives no
    # earliest year at all. With nothing but baselines, nothing has ever
    # changed and there is no past worth a column: start at the current year.
    _now = today_year or date.today().year
    _src_ids = [e.expense_id for v in by_prop.values() for e in v['sources']]
    _first = (FinancialFigureHistory.objects
              .filter(kind=FinancialFigureHistory.KIND_BUDGET,
                      source_pk__in=_src_ids)
              .exclude(effective_date=FH_BASELINE_DATE)
              .aggregate(_m=_Min('effective_date'))['_m'])
    first_year = _first.year if _first else _now
    if first_year > _now:
        first_year = _now
    years = list(range(first_year, _now + 2))          # through NEXT year

    prop_ids = list(by_prop.keys())
    cells = {pid: [] for pid in prop_ids}
    for y in years:
        vals_map = resolve_year_months_bulk(
            prop_ids, FinancialFigureHistory.KIND_BUDGET, y)
        for pid in prop_ids:
            total = Decimal('0')
            for e in by_prop[pid]['sources']:
                vals = vals_map.get(e.expense_id)
                if vals is not None:
                    for v in vals:
                        total += (v or 0)
                else:
                    # No history for this row: its live cells apply, which is
                    # the same fallback the P&L takes.
                    for m in MONTHS:
                        total += (getattr(e, 'expense_' + m, 0) or 0)
            cells[pid].append(total if total else None)

    rows = []
    for pid in prop_ids:
        _c = cells[pid]
        rows.append({
            'prop_id': pid,
            'prop_name': by_prop[pid]['prop_name'],
            'cells': _c,
            'total': sum((v for v in _c if v is not None), Decimal('0')),
        })
    # A property that carried nothing in ANY year is not a contributor to
    # this distribution and would draw a row of dashes.
    rows = [r for r in rows if r['total']]
    rows.sort(key=lambda r: (r['prop_name'] or '').lower())

    # Summed from the rows the table draws, not from a second query - the
    # lesson the Valuations round left, where a TOTAL counted a valuation the
    # table never showed.
    totals = [sum((r['cells'][i] for r in rows if r['cells'][i] is not None),
                  Decimal('0')) for i in range(len(years))]
    return {
        'line_type': lt,
        'years': years,
        'rows': rows,
        'totals': totals,
        'grand_total': sum(totals, Decimal('0')),
        'first_year': first_year,
    }


'''

VIEW_HELPER_ANCHOR = """# ============================================================================
# Expense
# ============================================================================

@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def finance_expense(request):"""

VIEW_HELPER_NEW = ("""# ============================================================================
# Expense
# ============================================================================

""" + VIEW_HELPER + """@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def finance_expense(request):""")

VIEW_OLD_TAIL = """    props_data = _fh_attach_expense_history(list(props_data))
    return render(request, "finance_expense.html", {"props_data": props_data})"""
VIEW_NEW_TAIL = """    props_data = _fh_attach_expense_history(list(props_data))

    # The second view. Chosen by a GET parameter rather than by JavaScript so
    # the state is in the URL - it can be linked, bookmarked and reloaded, and
    # the matrix is not built at all when nobody is looking at it.
    view_mode = 'matrix' if request.GET.get('view') == 'matrix' else 'property'
    matrix = None
    matrix_line_types = list(
        expense_line_types.objects
        .filter(expense_line_types_id__in=expense.objects.values(
            'expense_line_types_id'))
        .order_by('expense_line_types_name'))
    selected_lt = None
    if view_mode == 'matrix' and matrix_line_types:
        try:
            selected_lt = int(request.GET.get('lt') or 0)
        except (TypeError, ValueError):
            selected_lt = 0
        if selected_lt not in [l.expense_line_types_id for l in matrix_line_types]:
            selected_lt = matrix_line_types[0].expense_line_types_id
        matrix = expense_matrix(selected_lt)

    return render(request, "finance_expense.html", {
        "props_data": props_data,
        "view_mode": view_mode,
        "matrix": matrix,
        "matrix_line_types": matrix_line_types,
        "selected_lt": selected_lt,
    })"""

# ---------------------------------------------------------------------------
# 3. finance_expense.html
# ---------------------------------------------------------------------------
PAGE_OLD_CARD = """    <!-- Expense Card -->
    <div class="expense-card">"""
PAGE_NEW_CARD = """    {% if matrix_line_types %}
    <div class="expense-view-bar">
        <div class="alv-seg" role="group" aria-label="View">
            <a href="?view=property" {% if view_mode != 'matrix' %}aria-current="page"{% endif %}>
                <i class="fas fa-layer-group"></i> By property
            </a>
            <a href="?view=matrix{% if selected_lt %}&amp;lt={{ selected_lt }}{% endif %}"
               {% if view_mode == 'matrix' %}aria-current="page"{% endif %}>
                <i class="fas fa-table"></i> Year on year
            </a>
        </div>
        {% if view_mode == 'matrix' %}
        <form method="get" class="expense-view-picker">
            <input type="hidden" name="view" value="matrix">
            <label for="matrix-lt">Expense line type</label>
            <select name="lt" id="matrix-lt" class="form-control"
                    onchange="this.form.submit()">
                {% for lt in matrix_line_types %}
                    <option value="{{ lt.expense_line_types_id }}"
                        {% if lt.expense_line_types_id == selected_lt %}selected{% endif %}>
                        {{ lt.expense_line_types_name }}
                    </option>
                {% endfor %}
            </select>
            <noscript><button type="submit" class="btn action-secondary">Show</button></noscript>
        </form>
        {% endif %}
    </div>
    {% endif %}

    {% if view_mode == 'matrix' %}
    <div class="expense-card">
        {% if matrix and matrix.rows %}
        <div class="alv-matrix-scroll" tabindex="0"
             aria-label="{{ matrix.line_type.expense_line_types_name }} by year and property">
            <table class="alv-matrix">
                <thead>
                    <tr>
                        <th class="alv-matrix-row-head" scope="col">Property</th>
                        {% for y in matrix.years %}<th scope="col">{{ y }}</th>{% endfor %}
                        <th class="alv-matrix-total" scope="col">Total</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in matrix.rows %}
                    <tr>
                        <td class="alv-matrix-row-head">{{ row.prop_name }}</td>
                        {% for c in row.cells %}
                            {% if c %}<td>{{ c|floatformat:2|intcomma }}</td>
                            {% else %}<td class="alv-matrix-absent">&mdash;</td>{% endif %}
                        {% endfor %}
                        <td class="alv-matrix-total">{{ row.total|floatformat:2|intcomma }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
                <tfoot>
                    <tr>
                        <td class="alv-matrix-row-head">Charge for the year</td>
                        {% for t in matrix.totals %}<td>{{ t|floatformat:2|intcomma }}</td>{% endfor %}
                        <td class="alv-matrix-total">{{ matrix.grand_total|floatformat:2|intcomma }}</td>
                    </tr>
                </tfoot>
            </table>
        </div>
        <div class="expense-matrix-note">
            A dash means the property was not in this distribution that year &mdash;
            not that it cost nothing. Figures are <strong>budgeted</strong>, and are
            <strong>not pro-rated</strong> to the months a property was owned, so
            each column is the whole charge for that year. The P&amp;L pro-rates a
            property&rsquo;s first year and will show less for it.
        </div>
        {% else %}
        <div class="alv-empty">
            <div class="alv-empty-title">Nothing to show for this expense line type</div>
            <p>No property carries a figure for it in any year.</p>
        </div>
        {% endif %}
    </div>
    {% else %}

    <!-- Expense Card -->
    <div class="expense-card">"""

PAGE_OLD_END = """        </table>
    </div>

</div>"""
PAGE_NEW_END = """        </table>
    </div>
    {% endif %}

</div>"""

# There are two <style> blocks on this page; anchor on the first rule of
# the first one rather than on the tag.
PAGE_OLD_STYLE = """<style>
.expense-container {"""
PAGE_CSS = """<style>
/* The view bar. base owns the segmented control itself; this is only where
   it sits on this page. */
.expense-view-bar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 14px;
    margin-bottom: 14px;
}
.expense-view-picker {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin: 0;
    font-size: 13px;
    color: var(--alv-ink-soft);
}
.expense-view-picker label { margin: 0; font-weight: 600; }
.expense-view-picker select { width: auto; min-width: 190px; }
.expense-matrix-note {
    padding: 12px 16px;
    border-top: 1px solid var(--alv-line);
    background: var(--alv-surface);
    font-size: 12.5px;
    color: var(--alv-ink-soft);
}
@media print { .expense-view-bar, .expense-matrix-note { display: none !important; } }

.expense-container {"""

# finance_expense.html ALREADY loads humanize at the top - the first version
# of this patcher added a second one at {% block content %}. Harmless in
# Django, untidy in the file, and it would have read as this round needing
# something the page already had. Assert it instead of adding it.
PAGE_OLD_LOAD = None
PAGE_NEW_LOAD = None


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
    for p in (BASE, PAGE, VIEW):
        if not os.path.exists(p):
            sys.exit('! %s not found - run from the repo root' % p)

    b, pg, vs = read(BASE), read(PAGE), read(VIEW)

    if '.alv-matrix-scroll' in b:
        print('  expense matrix                already applied')
        print('\n  0 file(s) changed')
        return

    # FH_BASELINE_DATE is a sentinel the helper must recognise; import it
    # rather than writing 2000-01-01 down a second time.
    vs = one(vs,
             '    FinancialFigureHistory, record_expense_history, record_revenue_history,',
             '    FinancialFigureHistory, FH_BASELINE_DATE,\n'
             '    record_expense_history, record_revenue_history,',
             'the models import')
    b = one(b, BASE_ANCHOR, BASE_CSS + BASE_ANCHOR, 'the base.html anchor')
    vs = one(vs, VIEW_HELPER_ANCHOR, VIEW_HELPER_NEW, 'the finance_expense view')
    vs = one(vs, VIEW_OLD_TAIL, VIEW_NEW_TAIL, 'the finance_expense render')
    pg = one(pg, PAGE_OLD_CARD, PAGE_NEW_CARD, 'the expense card opener')
    pg = one(pg, PAGE_OLD_END, PAGE_NEW_END, 'the expense card close')
    pg = one(pg, PAGE_OLD_STYLE, PAGE_CSS, 'the first style block')

    # ---- self-check BEFORE anything is written
    bad = []
    try:
        tree = ast.parse(vs)
    except SyntaxError as exc:
        sys.exit('! the patched finance.py does not parse: %s' % exc)
    fns = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}

    if 'expense_matrix' not in fns:
        bad.append('the helper is not defined')
    else:
        h = fns['expense_matrix']
        if h.decorator_list:
            bad.append('the helper picked up a decorator - it is not a view')
        # The DOCSTRING names both of these while explaining the decision, and
        # ast.unparse includes it - twelfth instance of a check reading prose,
        # this one inside a Python docstring. Ask the CALLS instead.
        _called = {n.func.id for n in ast.walk(h)
                   if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        if 'resolve_year_months_bulk' not in _called:
            bad.append('the helper does not call the P&L resolver')
        if 'property_annual_budgeted_expenses' in _called:
            bad.append('the helper pro-rates - the decision was that it does not')
        _body = ast.unparse(ast.Module(body=h.body[1:], type_ignores=[]))
        if 'total if total else None' not in _body:
            bad.append('a zero cell is not reported as absent')
        if 'FH_BASELINE_DATE' not in _body:
            bad.append('the baseline sentinel is counted as a real year - '
                       'the table will open on 2000')
    if 'FH_BASELINE_DATE' not in vs.split('def expense_matrix')[0]:
        bad.append('FH_BASELINE_DATE is used but never imported')
    _fe = ast.unparse(fns['finance_expense'])
    for want in ('view_mode', 'matrix_line_types', 'expense_matrix('):
        if want not in _fe:
            bad.append('finance_expense does not supply %s' % want)
    if 'login_required' not in [getattr(d, 'id', getattr(getattr(d, 'func', None), 'id', ''))
                                for d in fns['finance_expense'].decorator_list]:
        bad.append('finance_expense lost @login_required')

    # base owns the components, the page owns only where they sit.
    _bc = nocomment(b)
    for want in ('.alv-seg', '.alv-matrix-scroll', 'table.alv-matrix'):
        if want not in _bc:
            bad.append('base.html does not define %s' % want)
    # NOT split on the section comment - nocomment() has just removed it. The
    # rules themselves are what the claim is about anyway; asking the comment
    # would be the same mistake as reading prose for code, taken from the
    # other end.
    if not re.search(r'\.alv-matrix-row-head[^{]*\{[^}]*position:\s*sticky',
                     _bc, re.S):
        bad.append('the first column does not freeze')
    if not re.search(r'\.alv-matrix-total[^{]*\{[^}]*position:\s*sticky',
                     _bc, re.S):
        bad.append('the total column does not freeze')
    _pc = nocomment(pg)
    for gone in ('.alv-seg {', 'table.alv-matrix {'):
        if gone in _pc:
            bad.append('the page redefines %s, which base owns' % gone)
    if not re.search(r'\.alv-matrix-scroll\s*\{[^}]*overflow-x', _bc):
        bad.append('the scroller rule is not what it claims to be')
    # ... and the clip/auto distinction is the whole reason for a second name.
    if re.search(r'\.table-container\s*\{[^}]*overflow-x:\s*auto', _bc):
        bad.append('.table-container was given overflow-x - that breaks every '
                   'sticky heading in the system')

    # Structure.
    for name, text in (('base.html', b), ('finance_expense.html', pg)):
        c = nocomment(text)
        css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', text, re.S))
        if css.count('{') != css.count('}'):
            bad.append('%s CSS braces do not balance' % name)
        # base.html is a shell and a stylesheet - it has no tables of its own,
        # and it DOES mention <table> in a comment explaining a rule. Balance
        # the table family only where tables live.
        _tags = (('div',) if name == 'base.html'
                 else ('div', 'table', 'tbody', 'thead', 'tfoot'))
        for tag in _tags:
            a = len(re.findall(r'<%s\b' % tag, text))
            z = len(re.findall(r'</%s\s*>' % tag, text))
            if a != z:
                bad.append('%s %s tags do not balance (%d/%d)' % (name, tag, a, z))
        for o, cl in ((r'\{%\s*if\b', r'\{%\s*endif\s*%\}'),
                      (r'\{%\s*for\b', r'\{%\s*endfor\s*%\}'),
                      (r'\{%\s*with\b', r'\{%\s*endwith\s*%\}')):
            if len(re.findall(o, text)) != len(re.findall(cl, text)):
                bad.append('%s: a Django block does not balance (%s)' % (name, o))
        for i, line in enumerate(text.split('\n'), 1):
            if line.count('{#') != line.count('#}'):
                bad.append('%s line %d opens a {# it does not close' % (name, i))
                break
        for blk in re.findall(r'<script[^>]*>(.*?)</script>', c, re.S):
            if blk.count('{') != blk.count('}'):
                bad.append('%s: a script block does not balance' % name)
                break
    if '{% load humanize %}' not in pg:
        bad.append('intcomma is used without loading humanize')
    if pg.count('{% load humanize %}') != 1:
        bad.append('humanize is loaded %d times - once is enough'
                   % pg.count('{% load humanize %}'))

    if bad:
        sys.exit('! expense matrix self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    print('  base.html                   .alv-seg - the segmented control, third asker')
    print('  base.html                   .alv-matrix - scrolls sideways, freezes both edges')
    print('  pages/views/finance.py      expense_matrix() on the P&L resolver, no pro-rating')
    print('  finance_expense.html        a second view: one line type, year on year')

    if not CHECK:
        for path, out in ((BASE, b), (PAGE, pg), (VIEW, vs)):
            bk = path + SUFFIX
            if not os.path.exists(bk):
                shutil.copy2(path, bk)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(out)

    print('\n  3 file(s) %s' % ('would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
