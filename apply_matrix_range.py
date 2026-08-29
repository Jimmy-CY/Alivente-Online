#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The matrix opens on the year the value changed, and says when a year straddles one.

TWO FAULTS, BOTH IN THE YEAR RANGE, AND THE SECOND ONE IS MINE FROM YESTERDAY.

1. TRUNCATED. `expense_matrix` derives its first year from the earliest
   NON-baseline snapshot. On Live, Company Tax's snapshots are

       2000-01-01  BASELINE
       2026-07-01              <- the charge changed, dated deliberately
       2026-08-24

   so the table opens on 2026 and draws two columns. 2024 and 2025 resolve
   perfectly well - to 7,000.00, from the baseline - and are simply never
   asked for. The day before, the same function read the sentinel AS DATA and
   drew twenty-eight columns back to the year 2000. One wrong answer was
   swapped for another.

   BOTH COME FROM ASKING WHEN SNAPSHOTS EXIST INSTEAD OF WHEN THE VALUE
   CHANGES. A baseline means "it held this before anybody recorded a change":
   it names no year, but the years before the first dated change are still
   real years with real answers.

   The rule here is arithmetic rather than a search:

       floor = max(earliest snapshot year INCLUDING the baseline,
                   earliest DATED change year - 1)
       no dated change at all -> the current year

   The first term is what stops the table reaching into years it cannot
   answer. Before its earliest snapshot a row resolves to nothing, the caller
   falls back to the row's LIVE cells, and the matrix would draw today's
   figure under a past year's heading. An earlier attempt at this walked
   backwards while the total kept changing and did exactly that - on Live it
   opened three line types on 2022, whose value was today's number echoed
   back. The clamp is the whole difference between a year that has an ANSWER
   and a year that merely has a NUMBER.

   The second term is what makes a change readable: one column showing what
   the charge was before it moved.

   Measured on Live before writing: 20 of 21 line types are unaffected,
   because only Company Tax has a baseline - _ensure_baseline fires the first
   time a long-standing figure is edited, and it is the only line that has
   happened to. Every other line was seeded at 2024-01-01, so its earliest
   snapshot and its first dated change are the same date and the two terms
   cancel. The fault will reach every line as each acquires a baseline.

2. A BLENDED YEAR READS AS A THIRD CHARGE. Company Tax is charged in January
   and July. The rate changed on 1 July 2026, so 2026 is

       jan 3,500.00 at the old rate  +  jul 3,299.99 at the new  =  6,799.99

   which is correct, confirmed against the Live P&L, and looks exactly like a
   third charge sitting between 7,000 and 6,600. That misreading cost a whole
   day: 6,799.99 was taken for a stale figure and a round was built to
   "correct" it, which would have restated a January instalment that had
   already gone out. If the number can do that to somebody reading the code,
   it will do it to somebody reading the table.

   A year is blended when the months carrying money in it do not all resolve
   from the SAME snapshot. That is a fact about provenance, so the resolver is
   asked for it rather than a second rule being invented beside it:
   `resolve_year_months_bulk(..., with_sources=True)` returns which snapshot
   supplied each month. One implementation, one answer.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, ast, shutil

ROOT   = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(ROOT, 'pages', 'models.py')
VIEW   = os.path.join(ROOT, 'pages', 'views', 'finance.py')
PAGE   = os.path.join(ROOT, 'pages', 'templates', 'finance_expense.html')
BASE   = os.path.join(ROOT, 'pages', 'templates', 'base.html')
SUITE  = os.path.join(ROOT, 'test_expense_matrix.py')
CHECK  = '--check' in sys.argv
SUFFIX = '.bak_matrixrange'

SENTINEL = 'WHEN THE VALUE CHANGES'

# ---------------------------------------------------------------------------
# 1. the resolver can say WHICH snapshot supplied each month
# ---------------------------------------------------------------------------
M_OLD_SIG = "def resolve_year_months_bulk(prop_ids, kind, year):"
M_NEW_SIG = "def resolve_year_months_bulk(prop_ids, kind, year, with_sources=False):"

M_OLD_LOOP = """    out = {}
    for src, versions in by_src.items():
        vals = []
        for m in range(1, 13):
            chosen = None
            for v in versions:              # ascending by effective_date
                if (v.effective_date.year, v.effective_date.month) <= (year, m):
                    chosen = v
                else:
                    break
            vals.append(getattr(chosen, _FH_MONTHS[m - 1]) if chosen is not None else None)
        out[src] = vals
    return out
"""

M_NEW_LOOP = """    out = {}
    prov = {}
    for src, versions in by_src.items():
        vals = []
        srcs = []
        for m in range(1, 13):
            chosen = None
            for v in versions:              # ascending by effective_date
                if (v.effective_date.year, v.effective_date.month) <= (year, m):
                    chosen = v
                else:
                    break
            vals.append(getattr(chosen, _FH_MONTHS[m - 1]) if chosen is not None else None)
            # WHICH SNAPSHOT ANSWERED THIS MONTH.
            #
            # Recorded in the same loop that chooses it, so provenance cannot
            # drift from the figure. A caller asking "does this year straddle
            # a change" would otherwise have to re-implement the choice, and
            # two answers to one question is how this system gets hurt.
            #
            # ONLY WHEN ASKED. Reading the primary key unconditionally made
            # this touch an attribute the caller never needed, and a suite
            # whose stub row legitimately has no pk died on it. A default
            # caller must be able to hand this function anything with the
            # thirteen fields it actually reads.
            if with_sources:
                srcs.append(chosen.financial_figure_history_id
                            if chosen is not None else None)
        out[src] = vals
        if with_sources:
            prov[src] = srcs
    return (out, prov) if with_sources else out
"""

# ---------------------------------------------------------------------------
# 2. the year range
# ---------------------------------------------------------------------------
V_OLD_RANGE = """    _now = today_year or date.today().year
    _src_ids = [e.expense_id for v in by_prop.values() for e in v['sources']]
    _first = (FinancialFigureHistory.objects
              .filter(kind=FinancialFigureHistory.KIND_BUDGET,
                      source_pk__in=_src_ids)
              .exclude(effective_date=FH_BASELINE_DATE)
              .aggregate(_m=_Min('effective_date'))['_m'])
    first_year = _first.year if _first else _now
    if first_year > _now:
        first_year = _now
    years = list(range(first_year, _now + 2))"""

V_NEW_RANGE = """    _now = today_year or date.today().year
    _src_ids = [e.expense_id for v in by_prop.values() for e in v['sources']]

    # WHEN THE VALUE CHANGES, not when snapshots exist.
    #
    # Two dates, doing two different jobs.
    #
    # _first is the earliest DATED change. FH_BASELINE_DATE is excluded from
    # it because the baseline is a SENTINEL, not a date - it means "and it
    # held this before anybody recorded a change", so it names no year.
    # Reading it as data once made this table open on 2000 and draw twenty-
    # eight identical columns.
    #
    # _earliest is the earliest snapshot of ANY kind, baseline included, and
    # it is the FLOOR. Before it there is no snapshot at all: the resolver
    # returns nothing, the caller falls back to the row's live cells, and this
    # table would draw today's figure under a past year's heading. Excluding
    # the baseline from the floor as well is what truncated Company Tax to
    # two columns while 2024 and 2025 resolved perfectly well from it.
    #
    # One year before the first change, so the reader can see what it was.
    _first = (FinancialFigureHistory.objects
              .filter(kind=FinancialFigureHistory.KIND_BUDGET,
                      source_pk__in=_src_ids)
              .exclude(effective_date=FH_BASELINE_DATE)
              .aggregate(_m=_Min('effective_date'))['_m'])
    _earliest = (FinancialFigureHistory.objects
                 .filter(kind=FinancialFigureHistory.KIND_BUDGET,
                         source_pk__in=_src_ids)
                 .aggregate(_m=_Min('effective_date'))['_m'])
    if _first is None:
        first_year = _now
    else:
        first_year = max(_earliest.year if _earliest else _now,
                         _first.year - 1)
    if first_year > _now:
        first_year = _now
    years = list(range(first_year, _now + 2))"""

# ---------------------------------------------------------------------------
# 3. which years straddle a change
# ---------------------------------------------------------------------------
V_OLD_CELLS = """    prop_ids = list(by_prop.keys())
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

"""

V_NEW_CELLS = """    prop_ids = list(by_prop.keys())
    cells = {pid: [] for pid in prop_ids}
    blended = []
    for y in years:
        vals_map, prov_map = resolve_year_months_bulk(
            prop_ids, FinancialFigureHistory.KIND_BUDGET, y, with_sources=True)
        # DOES THIS YEAR STRADDLE A CHANGE?
        #
        # Company Tax is charged in January and July; the rate changed on
        # 1 July 2026. So 2026 is January at the old rate plus July at the
        # new one - correct, and indistinguishable from a third charge unless
        # the table says so. Somebody reading the code took it for a stale
        # figure and built a round to "correct" it.
        #
        # The test is provenance, not arithmetic: the months that carry money
        # answered from more than ONE snapshot. Comparing the figures instead
        # would call a line blended whenever its months legitimately differ.
        # PER ROW, not per line. Every property has its own snapshots, so
        # pooling their ids across the line makes any multi-property line look
        # blended in every year. The year is blended when ONE row's money
        # months answered from more than one snapshot.
        _blend = False
        for pid in prop_ids:
            for e in by_prop[pid]['sources']:
                _v = vals_map.get(e.expense_id)
                _p = prov_map.get(e.expense_id)
                if _v is None or _p is None:
                    continue
                if len({_p[_i] for _i in range(12) if _v[_i]}) > 1:
                    _blend = True
                    break
            if _blend:
                break
        if _blend:
            blended.append(y)

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

"""

V_OLD_RET = """    return {
        'line_type': lt,
        'years': years,
        'rows': rows,
        'totals': totals,
        'grand_total': sum(totals, Decimal('0')),
        'first_year': first_year,
    }
"""

V_NEW_RET = """    return {
        'line_type': lt,
        'years': years,
        'rows': rows,
        'totals': totals,
        'grand_total': sum(totals, Decimal('0')),
        'first_year': first_year,
        'blended': blended,
    }
"""

# ---------------------------------------------------------------------------
# 4. the screen
# ---------------------------------------------------------------------------
P_OLD_HEAD = """                        {% for y in matrix.years %}<th scope="col">{{ y }}</th>{% endfor %}"""
P_NEW_HEAD = """                        {% for y in matrix.years %}{% if y in matrix.blended %}<th scope="col" class="alv-matrix-blend" title="This year straddles a change: the months before it carry the previous figure, the months after it the current one. The column is the two added together.">{{ y }} <span aria-hidden="true">&#8225;</span><span class="alv-visually-hidden">(straddles a change)</span></th>{% else %}<th scope="col">{{ y }}</th>{% endif %}{% endfor %}"""

P_OLD_NOTE = """            property&rsquo;s first year and will show less for it.
        </div>"""
P_NEW_NOTE = """            property&rsquo;s first year and will show less for it.
            {% if matrix.blended %}
            A year marked &#8225; <strong>straddles a change</strong>: the charge
            moved part-way through it, so the months before the change carry the
            previous figure and the months after it the current one. The column
            is the two added together, and will match neither the charge before
            nor the charge after.
            {% endif %}
        </div>"""

# A CLASS THE STYLESHEET HAS NEVER HEARD OF IS NOT A STYLE, IT IS A TYPO.
# `visually-hidden` does not exist in this system - the span carrying it would
# have rendered as visible text in the column heading. The suite checked that
# the class was REFERENCED, not that it was DEFINED, which is the same mistake
# this project keeps making in a new costume.
B_ANCHOR = """.alv-matrix td { text-align: right; }"""
B_CSS = """.alv-matrix td { text-align: right; }
/* A year that straddles a change: the months before it carry the previous
   figure and the months after it the current one, so the column matches
   neither charge. Marked rather than explained away - an unmarked blend reads
   as a third charge, and did. */
.alv-matrix thead th.alv-matrix-blend { color: var(--alv-warn); }
.alv-matrix thead th.alv-matrix-blend span[aria-hidden] {
    font-size: .9em;
    opacity: .85;
}
.alv-visually-hidden {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
    border: 0;
}"""

EDITS_MODELS = [
    ('the resolver can be asked which snapshot answered', M_OLD_SIG, M_NEW_SIG),
    ('  recorded in the same loop that chooses it', M_OLD_LOOP, M_NEW_LOOP),
]
EDITS_VIEW = [
    ('the range opens when the value changed, floored at the earliest snapshot',
     V_OLD_RANGE, V_NEW_RANGE),
    ('and a year answered by more than one snapshot is a blended year',
     V_OLD_CELLS, V_NEW_CELLS),
    ('  which the screen is told about', V_OLD_RET, V_NEW_RET),
]
EDITS_PAGE = [
    ('a blended column is marked', P_OLD_HEAD, P_NEW_HEAD),
    ('and the note says what the mark means', P_OLD_NOTE, P_NEW_NOTE),
]
EDITS_BASE = [
    ('the two new classes exist in the stylesheet', B_ANCHOR, B_CSS),
]

# ---------------------------------------------------------------------------
# 5. the 4b: an earlier suite MIRRORED the resolver instead of lifting it
# ---------------------------------------------------------------------------
# test_expense_matrix.py carried a hand-copy of resolve_year_months_bulk,
# introduced with the words "the project's own resolver, mirrored
# field-for-field". It diverged the instant the real one gained an optional
# argument, and fourteen unrelated checks died with a TypeError.
#
# The copy is not repaired here, it is DELETED. The real function reads
# _FH_MONTHS, _fh_date and FinancialFigureHistory out of its globals, and that
# module already defines all three, so it can simply be lifted - which is what
# the newer suites do, and why they did not break.
S_OLD_MIRROR = '''def resolve_year_months_bulk(prop_ids, kind, year):
    """The project's own resolver, mirrored field-for-field.

    Lifting it out of models.py would drag half the app in; it is fifteen
    lines and the shape that matters is which version wins for a month.
    """
    from collections import defaultdict
    rows = (FinancialFigureHistory.objects
            .filter(prop_id__in=list(prop_ids), kind=kind,
                    effective_date__lte=date(year, 12, 31))
            .order_by('source_pk', 'effective_date', 'changed_at'))
    by_src = defaultdict(list)
    for r in rows:
        by_src[r.source_pk].append(r)
    out = {}
    for src, versions in by_src.items():
        vals = []
        for m in range(1, 13):
            chosen = None
            for v in versions:
                if (v.effective_date.year, v.effective_date.month) <= (year, m):
                    chosen = v
                else:
                    break
            vals.append(getattr(chosen, _FH_MONTHS[m - 1])
                        if chosen is not None else None)
        out[src] = vals
    return out
'''

S_NEW_MIRROR = '''# THE RESOLVER IS LIFTED, NOT MIRRORED.
#
# This was a hand-copy of the project's resolver, added with the words "the
# project's own resolver, mirrored field-for-field". It diverged the moment
# the real one gained an optional with_sources argument, and took fourteen
# unrelated checks down with a TypeError. A copy of a thing is not a test of
# the thing.
#
# The real function reads _FH_MONTHS, _fh_date and FinancialFigureHistory out
# of its globals, all of which this module defines, so lifting it is a
# drop-in. It is exec'd just below `lift`, where that helper exists.
'''

S_OLD_PK = """class FinancialFigureHistory(models.Model):
    KIND_BUDGET = 'budget_expense'
    prop = models.ForeignKey(props, on_delete=models.CASCADE)"""

S_NEW_PK = """class FinancialFigureHistory(models.Model):
    KIND_BUDGET = 'budget_expense'
    # The real model's primary key, named. A stub that lifts the real resolver
    # has to carry the fields that resolver names - and provenance names this
    # one. Django would otherwise supply an implicit `id`, and the lift would
    # die on an attribute the stub never declared.
    financial_figure_history_id = models.AutoField(primary_key=True)
    prop = models.ForeignKey(props, on_delete=models.CASCADE)"""

S_OLD_LIFT = """_ns = {'expense': expense, 'expense_line_types': expense_line_types,
       'props': props, 'FinancialFigureHistory': FinancialFigureHistory,
       'resolve_year_months_bulk': resolve_year_months_bulk,"""

S_NEW_LIFT = """_MODELS_SRC = os.path.join(ROOT, 'pages', 'models.py')
if not os.path.exists(_MODELS_SRC):
    sys.exit('! pages/models.py not found - run from the project root')
with open(_MODELS_SRC, encoding='utf-8', errors='replace') as _f:
    _MD_SRC = _f.read().replace(chr(13) + chr(10), chr(10))
_res_ns = {'FinancialFigureHistory': FinancialFigureHistory,
           '_FH_MONTHS': _FH_MONTHS, '_fh_date': date}
exec(compile(lift(_MD_SRC, 'resolve_year_months_bulk'), 'resolver', 'exec'),
     _res_ns)
resolve_year_months_bulk = _res_ns['resolve_year_months_bulk']

_ns = {'expense': expense, 'expense_line_types': expense_line_types,
       'props': props, 'FinancialFigureHistory': FinancialFigureHistory,
       'resolve_year_months_bulk': resolve_year_months_bulk,"""


# The three checks that asserted YESTERDAY's rule, and one that passed for the
# wrong reason. Superseded deliberately - a baseline now lowers the floor by
# design, which is the whole round.
S_OLD_BASE = """_withbase = expense_matrix(LT.expense_line_types_id, today_year=NOW)
check('A BASELINE DOES NOT OPEN THE TABLE ON 2000',
      _withbase['years'][0] == 2023, str(_withbase['years'][:3]))
check('  the range is unchanged by it',
      _withbase['years'] == M['years'])"""

S_NEW_BASE = """_withbase = expense_matrix(LT.expense_line_types_id, today_year=NOW)
check('A BASELINE STILL DOES NOT OPEN THE TABLE ON 2000',
      _withbase['years'][0] > 2000, str(_withbase['years'][:3]))
# SUPERSEDED, deliberately. It used to assert the range was UNCHANGED by a
# baseline. It is not, any more: the floor is now the earliest snapshot of any
# kind, and a baseline is one - so the table can finally show the year BEFORE
# the first dated change, which is the year the reader needs in order to see
# what the figure changed FROM. Without a baseline that year cannot be
# answered at all and is still excluded.
check('  it opens exactly ONE year earlier, showing what came before',
      _withbase['years'][0] == M['years'][0] - 1,
      '%s vs %s' % (_withbase['years'][0], M['years'][0]))
check('  and gains exactly one column, not a reach back to the sentinel',
      len(_withbase['years']) == len(M['years']) + 1)"""

S_OLD_TOT = """check('  and it changes no figure in range - a later row wins every month',
      _withbase['totals'] == M['totals'],
      str(_withbase['totals'][:2]))"""

S_NEW_TOT = """# Every year the table ALREADY drew reports exactly what it did before: the
# resolver takes the latest row at or before each month, and those years all
# have a later one. The baseline speaks only for the new leading column.
check('  and it changes no figure in any year the table already drew',
      _withbase['totals'][1:] == M['totals'],
      str(_withbase['totals'][:2]))
check('  the new leading column is the one the baseline answers',
      _withbase['totals'][0] is not None)"""

S_OLD_ONLY = """_only = MADE['Ionion - Villa 24']
FinancialFigureHistory.objects.filter(prop=_only).delete()
FinancialFigureHistory.objects.create(
    prop=_only, kind=FinancialFigureHistory.KIND_BUDGET,
    source_pk=expense.objects.get(prop=_only,
                                  expense_line_types=LT).expense_id,
    effective_date=FH_BASELINE_DATE,
    **{('fh_' + m): Decimal('100') for m in MONTHS})
_baseonly = expense_matrix(LT.expense_line_types_id, today_year=NOW)
check('a line type whose only history is baselines starts at the CURRENT year',
      _baseonly['years'][0] >= 2023, str(_baseonly['years']))"""

S_NEW_ONLY = """# THE FIXTURE WAS WRONG, and the check passed anyway. It cleared history for
# ONE property, so the line type still had a dated change on a sibling row -
# so "only baselines" was never the case being tested, and `>= 2023` was
# satisfied by the ordinary range. Every dated row on the line has to go.
FinancialFigureHistory.objects.all().delete()
for _e in expense.objects.filter(expense_line_types=LT):
    FinancialFigureHistory.objects.create(
        prop=_e.prop, kind=FinancialFigureHistory.KIND_BUDGET,
        source_pk=_e.expense_id, effective_date=FH_BASELINE_DATE,
        **{('fh_' + m): Decimal('100') for m in MONTHS})
_baseonly = expense_matrix(LT.expense_line_types_id, today_year=NOW)
check('a line type whose only history is baselines starts at the CURRENT year',
      _baseonly['years'][0] == NOW, str(_baseonly['years']))
check('  CONTROL: and there really is no dated change left to open on',
      not FinancialFigureHistory.objects.exclude(
          effective_date=FH_BASELINE_DATE).exists())"""

EDITS_SUITE = [
    ('an earlier suite stops mirroring the resolver and lifts it',
     S_OLD_MIRROR, S_NEW_MIRROR),
    ('  and its stub model carries the pk the real resolver names',
     S_OLD_PK, S_NEW_PK),
    ('  from the real models.py, beside the matrix it already lifts',
     S_OLD_LIFT, S_NEW_LIFT),
    ('  and its baseline checks assert this rule, not yesterday\'s',
     S_OLD_BASE, S_NEW_BASE),
    ('  including the totals it no longer expects to be identical',
     S_OLD_TOT, S_NEW_TOT),
    ('  and the baseline-only fixture really clears every dated row',
     S_OLD_ONLY, S_NEW_ONLY),
]


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read().replace('\r\n', '\n')


def one(text, old, new, what):
    n = text.count(old)
    if n != 1:
        sys.exit('! %s did not match exactly once (%d) - the file may already '
                 'have been edited:\n%s' % (what, n, old[:200]))
    return text.replace(old, new, 1)


def nocomment_py(src):
    tree = ast.parse(src)
    for node in ast.walk(tree):
        body = getattr(node, 'body', None)
        if isinstance(body, list) and body and isinstance(body[0], ast.Expr) \
                and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            node.body = body[1:] or [ast.Pass()]
    return ast.unparse(tree)


def nocomment_html(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    # NOT re.S. Django's {# #} does not span lines - a comment opened on one
    # line and closed on the next is RENDERED TEXT, and a stripper more
    # permissive than the lexer it models certifies exactly the fault it
    # exists to catch. That shipped once already.
    text = re.sub(r'\{#[^\n]*?#\}', '', text)

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


def main():
    for p in (MODELS, VIEW, PAGE, BASE, SUITE):
        if not os.path.exists(p):
            sys.exit('! %s not found - run from the repo root' % p)
    md, vs, pg, bs = read(MODELS), read(VIEW), read(PAGE), read(BASE)
    su = read(SUITE)

    if SENTINEL in vs:
        print('  matrix range + blend marker    already applied')
        print('\n  0 file(s) changed')
        return

    for name, old, new in EDITS_MODELS:
        md = one(md, old, new, name)
    for name, old, new in EDITS_VIEW:
        vs = one(vs, old, new, name)
    for name, old, new in EDITS_PAGE:
        pg = one(pg, old, new, name)
    for name, old, new in EDITS_BASE:
        bs = one(bs, old, new, name)
    for name, old, new in EDITS_SUITE:
        su = one(su, old, new, name)

    # ---- self-check BEFORE anything is written -----------------------------
    bad = []
    for label, text in (('models.py', md), ('finance.py', vs)):
        try:
            ast.parse(text)
        except SyntaxError as exc:
            sys.exit('! the patched %s does not parse: %s' % (label, exc))

    mfns = {n.name: n for n in ast.walk(ast.parse(md))
            if isinstance(n, ast.FunctionDef)}
    vfns = {n.name: n for n in ast.walk(ast.parse(vs))
            if isinstance(n, ast.FunctionDef)}

    if 'resolve_year_months_bulk' not in mfns:
        sys.exit('! the resolver is gone, nothing written')
    if 'expense_matrix' not in vfns:
        sys.exit('! expense_matrix is gone, nothing written')

    _res = mfns['resolve_year_months_bulk']
    _rescode = nocomment_py(ast.get_source_segment(md, _res))
    _mat = nocomment_py(ast.get_source_segment(vs, vfns['expense_matrix']))

    # BACKWARDS COMPATIBILITY IS THE LOAD-BEARING PART. Six callers pass three
    # arguments and expect one dict back. Ask the signature, not the text.
    _args = [a.arg for a in _res.args.args]
    if _args[:3] != ['prop_ids', 'kind', 'year']:
        bad.append('the first three parameters moved, so every existing '
                   'caller breaks')
    if 'with_sources' not in _args:
        bad.append('the provenance flag is not a parameter')
    if len(_res.args.defaults) != 1:
        bad.append('with_sources is not optional, so every existing caller '
                   'breaks')
    if 'return (out, prov) if with_sources else out' not in _rescode:
        bad.append('the resolver does not still return a bare dict by default')
    # The pk must be read ONLY inside the flag. A default caller may hand this
    # function rows that have no primary key at all.
    if _rescode.count('financial_figure_history_id') != 1:
        bad.append('the snapshot pk is read somewhere other than the guarded '
                   'branch')
    _guarded = [n for n in ast.walk(_res)
                if isinstance(n, ast.If) and 'with_sources' in ast.unparse(n.test)
                and 'financial_figure_history_id' in ast.unparse(n)]
    if not _guarded:
        bad.append('reading the snapshot pk is not guarded by with_sources')

    # The floor. Without it the table reaches into fabricated years.
    if '_earliest' not in _mat:
        bad.append('the range has no floor at the earliest snapshot')
    if _mat.count('exclude(effective_date=FH_BASELINE_DATE)') != 1:
        bad.append('the baseline is excluded from both dates, or from '
                   'neither - it belongs in the floor and not in the change')
    if 'max(' not in _mat:
        bad.append('the floor and the first change are not combined')
    if 'with_sources=True' not in _mat:
        bad.append('the matrix does not ask for provenance')
    if "'blended': blended" not in _mat:
        bad.append('the screen is never told which years are blended')
    # Provenance, not arithmetic: comparing figures would call any line with
    # legitimately different months blended.
    if 'prov_map' not in _mat:
        bad.append('blendedness is decided some other way than provenance')

    _pc = nocomment_html(pg)
    if 'alv-matrix-blend' not in _pc:
        bad.append('the blended column is not marked')
    if 'y in matrix.blended' not in _pc:
        bad.append('the marker is not conditional on the year being blended')
    if 'straddles a change' not in _pc:
        bad.append('the note does not explain the mark')
    # CONTROL on the stripper: this round's prose is full of the words being
    # searched for, so if nocomment_html stopped working every check above
    # would be reading explanation instead of markup.
    if 'WHEN THE VALUE CHANGES' in nocomment_py(ast.get_source_segment(
            vs, vfns['expense_matrix'])):
        bad.append('CONTROL: comments are not being stripped from the view, '
                   'so the structural checks may be reading prose')

    # DEFINED, not merely referenced.
    _bc = nocomment_html(bs)
    for _cls in ('alv-matrix-blend', 'alv-visually-hidden'):
        if _cls in _pc and not re.search(r'\.%s\s*[,{ ]' % re.escape(_cls), _bc):
            bad.append('%s is used in the markup but defined nowhere in '
                       'base.html, so it styles nothing' % _cls)
    if not re.search(r'\.alv-matrix-blend[^}]*var\(--alv-warn\)', _bc, re.S):
        bad.append('the blend marker carries a literal rather than a house token')
    if re.search(r'\.alv-matrix-blend[^}]*#[0-9a-fA-F]{3,6}', _bc, re.S):
        bad.append('a raw hex entered the blend rule')
    try:
        ast.parse(su)
    except SyntaxError as exc:
        sys.exit('! the patched test_expense_matrix.py does not parse: %s' % exc)
    if 'resolve_year_months_bulk' in {n.name for n in ast.walk(ast.parse(su))
                                      if isinstance(n, ast.FunctionDef)}:
        bad.append('the older suite still DEFINES its own resolver, so the '
                   'copy can diverge again')
    if "lift(_MD_SRC, 'resolve_year_months_bulk')" not in su:
        bad.append('the older suite does not lift the real resolver')
    if 'financial_figure_history_id = models.AutoField' not in su:
        bad.append('the older suite\'s stub has no primary key, so the lifted '
                   'resolver cannot record provenance from it')

    _css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', bs, re.S))
    if _css.count('{') != _css.count('}'):
        bad.append('base.html CSS braces do not balance')

    for o, c in ((r'\{%\s*if\b', r'\{%\s*endif\s*%\}'),
                 (r'\{%\s*for\b', r'\{%\s*endfor\s*%\}')):
        if len(re.findall(o, pg)) != len(re.findall(c, pg)):
            bad.append('a Django block no longer balances (%s)' % o)
    for _l in pg.split('\n'):
        if _l.count('{#') != _l.count('#}'):
            bad.append('a {# #} comment spans lines, which Django renders as '
                       'visible text')
            break
    for tag in ('th', 'span'):
        a = len(re.findall(r'<%s\b' % tag, pg))
        z = len(re.findall(r'</%s\s*>' % tag, pg))
        if a != z:
            bad.append('%s tags do not balance (%d/%d)' % (tag, a, z))

    if bad:
        sys.exit('! matrix-range self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    for name, _o, _n in EDITS_MODELS + EDITS_VIEW + EDITS_PAGE + EDITS_BASE + EDITS_SUITE:
        print('  %s' % name)

    if not CHECK:
        for path, out in ((MODELS, md), (VIEW, vs), (PAGE, pg), (BASE, bs), (SUITE, su)):
            b = path + SUFFIX
            if not os.path.exists(b):
                shutil.copy2(path, b)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(out)

    print('\n  5 file(s) %s' % ('would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
