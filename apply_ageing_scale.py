#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""One ageing scale, and a report that stops disagreeing with itself.

THE REPORT SAID TWO THINGS ABOUT THE SAME INVOICE. An invoice fifteen days
late got an amber "15 days late" pill, from this rule in the page's own JS:

    daysOverdue > 90 ? severe : > 60 ? high : > 30 ? medium : > 0 ? low
                                                              : current

and was simultaneously counted in the CURRENT column, because the view buckets
it differently:

    if days_overdue <= 30:
        # Current (0-30 days - includes not yet due and up to 30 days overdue)

The comment admits the conflation. "Current" was doing two jobs - NOT YET DUE
and UP TO THIRTY DAYS LATE - so the pill split at 0 and the column split at 30,
and one screen gave one invoice two verdicts.

The buckets are now five, and they are the pill's own thresholds:

    not yet due   0 days          not on the ageing scale - it is not ageing
    past due      1-30            alv-age-1
    past due      31-60           alv-age-2
    past due      61-90           alv-age-3
    past due      91+             alv-age-4

THREE PARALLEL AGEING VOCABULARIES BECOME ONE. The page carried

  * .age-dot-current / -31-60 / -61-90 / -91-plus     Bootstrap green/amber/orange/red
  * .sparkline-segment-*                              the same four, restated
  * .days-pill-current / low / medium / high / severe FIVE steps, a different palette
  * .past-due-31-60 #e1f5fe, .past-due-61-90 #e0e4e7, .past-due-91-plus #e3f2fd

That last row is the interesting failure: two near-identical pale blues with a
grey between them. It LOOKS like a scale and encodes no ordering at all - a
reader learns nothing from it about which column is worse.

THE SCALE IS ONE SEVERITY CLASS PLUS ONE APPLICATION CLASS. `.alv-age-N` sets
two custom properties; `.alv-age-dot`, `.alv-age-fill`, `.alv-age-cell` and
`.alv-age-pill` consume them. So four steps drive a dot, a bar segment, a
column tint and a pill without four parallel families, and the next page that
needs ageing gets it for nothing. Named for ageing rather than a general
`.alv-seq-*`, per the decision of 27 Aug: generalise when a second page asks.

Ends anchored on tokens the system already has - step 2 IS --alv-warn and step
4 IS --alv-bad - so the scale cannot drift away from the semantics around it.

WHAT THIS ROUND DOES NOT DO. It does not migrate the page onto the table
standard: `.table-container`, `.alv-table`, the navy header band, the TOTALS
row that lives in the tbody rather than a tfoot, and the 37-line print block
that prints white on white are all part B. This round changes the buckets, the
scale, and the colours that express them.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, ast, shutil

ROOT  = os.path.dirname(os.path.abspath(__file__))
VIEW  = os.path.join(ROOT, 'pages', 'views', 'invoices.py')
BASE  = os.path.join(ROOT, 'pages', 'templates', 'base.html')
PAGE  = os.path.join(ROOT, 'pages', 'templates', 'open_invoices_report.html')
CHECK = '--check' in sys.argv
SUFFIX = '.bak_ageing'

SENTINEL = 'AGE_BUCKETS = ('

# ---------------------------------------------------------------------------
# 1. the view: five buckets, on the pill's own thresholds
# ---------------------------------------------------------------------------
V_OLD_HELPER = """@login_required
@permission_required('auth.can_access_invoices', raise_exception=True)
def open_invoices_report(request):
"""

V_NEW_HELPER = '''# THE AGEING BUCKETS, IN ONE PLACE.
#
# Ordered mild to severe, and the index IS the step on base's `.alv-age-N`
# scale: not_yet_due is 0, past_due_91_plus is 4. The report's pill classes are
# assigned from the same index, so a bucket and its colour cannot part company.
AGE_BUCKETS = (
    'not_yet_due',        # 0 - not ageing at all
    'past_due_1_30',      # 1
    'past_due_31_60',     # 2
    'past_due_61_90',     # 3
    'past_due_91_plus',   # 4
)


def age_bucket(days_overdue):
    """Which bucket a number of days overdue falls in.

    NOT YET DUE is not step zero of ageing, it is the absence of it - which is
    why it is a bucket of its own rather than the bottom of the scale.

    This replaced `if days_overdue <= 30: current_0_30`, whose own comment
    admitted the problem: "includes not yet due and up to 30 days overdue". The
    report's pill split at 0 and this column split at 30, so an invoice fifteen
    days late showed an amber "15 days late" chip while the column counted it
    as Current. One invoice, one screen, two verdicts.

    A FUNCTION rather than an inline chain, so the rule has one name and can be
    asked directly. The page's JavaScript mirrors these thresholds; the suite
    asserts the two agree at every boundary, because a mirror that nobody
    compares is how they drifted in the first place.
    """
    if days_overdue <= 0:
        return AGE_BUCKETS[0]
    if days_overdue <= 30:
        return AGE_BUCKETS[1]
    if days_overdue <= 60:
        return AGE_BUCKETS[2]
    if days_overdue <= 90:
        return AGE_BUCKETS[3]
    return AGE_BUCKETS[4]


@login_required
@permission_required('auth.can_access_invoices', raise_exception=True)
def open_invoices_report(request):
'''

V_OLD_TOTALS = """    debtors_age_analysis = []
    totals = {
        'total_outstanding': 0,
        'current_0_30': 0,
        'past_due_31_60': 0,
        'past_due_61_90': 0,
        'past_due_91_plus': 0
    }
"""
V_NEW_TOTALS = """    debtors_age_analysis = []
    totals = {'total_outstanding': 0}
    totals.update({_b: 0 for _b in AGE_BUCKETS})
"""

V_OLD_ROW = """        tenant_analysis = {
            'tenant_name': tenant_obj.tenant_name,
            'tenant_id': tenant_obj.tenant_id,  # Add tenant_id here too
            'total_outstanding': 0,
            'current_0_30': 0,
            'past_due_31_60': 0,
            'past_due_61_90': 0,
            'past_due_91_plus': 0
        }
"""
V_NEW_ROW = """        tenant_analysis = {
            'tenant_name': tenant_obj.tenant_name,
            'tenant_id': tenant_obj.tenant_id,  # Add tenant_id here too
            'total_outstanding': 0,
        }
        tenant_analysis.update({_b: 0 for _b in AGE_BUCKETS})
"""

V_OLD_BUCKET = """            if days_overdue <= 30:
                # Current (0-30 days - includes not yet due and up to 30 days overdue)
                tenant_analysis['current_0_30'] += amount
            elif 31 <= days_overdue <= 60:
                # Past due 31-60 days
                tenant_analysis['past_due_31_60'] += amount
            elif 61 <= days_overdue <= 90:
                # Past due 61-90 days
                tenant_analysis['past_due_61_90'] += amount
            else:
                # Past due 91+ days
                tenant_analysis['past_due_91_plus'] += amount
"""
V_NEW_BUCKET = """            tenant_analysis[age_bucket(days_overdue)] += amount
"""

V_OLD_ACC = """            totals['current_0_30'] += tenant_analysis['current_0_30']
            totals['past_due_31_60'] += tenant_analysis['past_due_31_60']
            totals['past_due_61_90'] += tenant_analysis['past_due_61_90']
            totals['past_due_91_plus'] += tenant_analysis['past_due_91_plus']
"""
V_NEW_ACC = """            # Over the tuple, not four written-out lines: adding a bucket
            # and forgetting to total it is exactly the class of fault this
            # round is here to fix.
            for _b in AGE_BUCKETS:
                totals[_b] += tenant_analysis[_b]
"""

EDITS_VIEW = [
    ('the ageing buckets get one name and one rule', V_OLD_HELPER, V_NEW_HELPER),
    ('the totals carry five buckets', V_OLD_TOTALS, V_NEW_TOTALS),
    ('and so does every tenant row', V_OLD_ROW, V_NEW_ROW),
    ('each invoice is bucketed by the rule, not by a chain in the view',
     V_OLD_BUCKET, V_NEW_BUCKET),
    ('  and every bucket reaches the totals, by construction',
     V_OLD_ACC, V_NEW_ACC),
]

# ---------------------------------------------------------------------------
# 2. base.html: the scale
# ---------------------------------------------------------------------------
B_TOK_ANCHOR = """        --alv-neutral:    #6b7780;
        --alv-neutral-soft: #eef1f2;"""
B_TOK = """        --alv-neutral:    #6b7780;
        --alv-neutral-soft: #eef1f2;

        /* A sequential scale, for AGEING. Four steps, mild to severe.
           Named for ageing rather than a general-purpose sequence: one use
           case does not justify a general scale, and the same restraint
           deferred the segmented toggle and the compact table until a second
           page asked.

           The ENDS ARE THE SEMANTIC TOKENS - step 2 is the warn colour and
           step 4 is the bad one - so this scale cannot drift away from the
           meaning of the statuses beside it. The two middle steps walk the
           hue between them. The soft variants also lighten monotonically, so
           a row of tinted cells reads left to right even for a reader who
           cannot separate the hues.

           There is deliberately no step for NOT YET DUE. That is the absence
           of ageing, not the first degree of it, and it takes the good token
           like any other healthy state. */
        --alv-age-1:      #8a7a12;
        --alv-age-1-soft: #fdf8e6;
        --alv-age-2:      #9a6a08;
        --alv-age-2-soft: #fbeec9;
        --alv-age-3:      #a8481a;
        --alv-age-3-soft: #f8e0cd;
        --alv-age-4:      #b3261e;
        --alv-age-4-soft: #f6d5d2;"""

B_CSS_ANCHOR = """.alv-matrix td { text-align: right; }"""
B_CSS = """.alv-matrix td { text-align: right; }

/* THE AGEING SCALE.
   One severity class carries the step; one application class decides what to
   do with it. So four steps drive a dot, a bar segment, a column tint and a
   pill without four parallel families of class - which is exactly what the
   Outstanding Invoices report had, three of them, disagreeing.
   Severity: .alv-age-0 (not ageing) .. .alv-age-4 (severe). */
.alv-age-0 { --age: var(--alv-good);   --age-soft: var(--alv-good-soft); }
.alv-age-1 { --age: var(--alv-age-1);  --age-soft: var(--alv-age-1-soft); }
.alv-age-2 { --age: var(--alv-age-2);  --age-soft: var(--alv-age-2-soft); }
.alv-age-3 { --age: var(--alv-age-3);  --age-soft: var(--alv-age-3-soft); }
.alv-age-4 { --age: var(--alv-age-4);  --age-soft: var(--alv-age-4-soft); }

.alv-age-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex: none;
    background: var(--age, var(--alv-neutral));
}
.alv-age-fill {
    height: 100%;
    background: var(--age, var(--alv-neutral));
}
.alv-age-cell { background: var(--age-soft, transparent); }
.alv-age-pill {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
    white-space: nowrap;
    background: var(--age-soft, var(--alv-neutral-soft));
    color: var(--age, var(--alv-ink));
}"""

EDITS_BASE = [
    ('base owns a sequential scale, for ageing', B_TOK_ANCHOR, B_TOK),
    ('  applied by a dot, a fill, a cell or a pill', B_CSS_ANCHOR, B_CSS),
]

# ---------------------------------------------------------------------------
# 3. the report: five columns, one vocabulary
# ---------------------------------------------------------------------------
P_OLD_HEAD = """                        <th>Current<br>(0 to 30 Days)</th>
                        <th>Past Due<br>(31 to 60 Days)</th>"""
P_NEW_HEAD = """                        <th>Not Yet Due</th>
                        <th>Past Due<br>(1 to 30 Days)</th>
                        <th>Past Due<br>(31 to 60 Days)</th>"""

P_OLD_CELLS = """                        <td class="amount-cell current">€{{ debtor.current_0_30|floatformat:0|add_thousand_separator }}</td>
                        <td class="amount-cell past-due-31-60">€{{ debtor.past_due_31_60|floatformat:0|add_thousand_separator }}</td>
                        <td class="amount-cell past-due-61-90">€{{ debtor.past_due_61_90|floatformat:0|add_thousand_separator }}</td>
                        <td class="amount-cell past-due-91-plus">€{{ debtor.past_due_91_plus|floatformat:0|add_thousand_separator }}</td>"""
P_NEW_CELLS = """                        <td class="amount-cell alv-age-cell alv-age-0">€{{ debtor.not_yet_due|floatformat:0|add_thousand_separator }}</td>
                        <td class="amount-cell alv-age-cell alv-age-1">€{{ debtor.past_due_1_30|floatformat:0|add_thousand_separator }}</td>
                        <td class="amount-cell alv-age-cell alv-age-2">€{{ debtor.past_due_31_60|floatformat:0|add_thousand_separator }}</td>
                        <td class="amount-cell alv-age-cell alv-age-3">€{{ debtor.past_due_61_90|floatformat:0|add_thousand_separator }}</td>
                        <td class="amount-cell alv-age-cell alv-age-4">€{{ debtor.past_due_91_plus|floatformat:0|add_thousand_separator }}</td>"""

P_OLD_TCELLS = """                        <td class="amount-cell current"><strong>€{{ totals.current_0_30|floatformat:0|add_thousand_separator }}</strong></td>
                        <td class="amount-cell past-due-31-60"><strong>€{{ totals.past_due_31_60|floatformat:0|add_thousand_separator }}</strong></td>
                        <td class="amount-cell past-due-61-90"><strong>€{{ totals.past_due_61_90|floatformat:0|add_thousand_separator }}</strong></td>
                        <td class="amount-cell past-due-91-plus"><strong>€{{ totals.past_due_91_plus|floatformat:0|add_thousand_separator }}</strong></td>"""
P_NEW_TCELLS = """                        <td class="amount-cell alv-age-cell alv-age-0"><strong>€{{ totals.not_yet_due|floatformat:0|add_thousand_separator }}</strong></td>
                        <td class="amount-cell alv-age-cell alv-age-1"><strong>€{{ totals.past_due_1_30|floatformat:0|add_thousand_separator }}</strong></td>
                        <td class="amount-cell alv-age-cell alv-age-2"><strong>€{{ totals.past_due_31_60|floatformat:0|add_thousand_separator }}</strong></td>
                        <td class="amount-cell alv-age-cell alv-age-3"><strong>€{{ totals.past_due_61_90|floatformat:0|add_thousand_separator }}</strong></td>
                        <td class="amount-cell alv-age-cell alv-age-4"><strong>€{{ totals.past_due_91_plus|floatformat:0|add_thousand_separator }}</strong></td>"""

P_OLD_SPARKDATA = """                         data-current="{{ debtor.current_0_30 }}"
                         data-due-31-60="{{ debtor.past_due_31_60 }}\""""
P_NEW_SPARKDATA = """                         data-not-yet-due="{{ debtor.not_yet_due }}"
                         data-due-1-30="{{ debtor.past_due_1_30 }}"
                         data-due-31-60="{{ debtor.past_due_31_60 }}\""""

_LEG = """                        <div class="age-segment-row">
                            <span class="age-dot age-dot-current"></span>
                            <span class="age-label">0-30 days:</span>
                            <span class="age-value">€{{ %s.current_0_30|floatformat:0|add_thousand_separator }}</span>
                        </div>
                        <div class="age-segment-row">
                            <span class="age-dot age-dot-31-60"></span>"""
_LEGN = """                        <div class="age-segment-row">
                            <span class="alv-age-dot alv-age-0"></span>
                            <span class="age-label">Not yet due:</span>
                            <span class="age-value">€{{ %s.not_yet_due|floatformat:0|add_thousand_separator }}</span>
                        </div>
                        <div class="age-segment-row">
                            <span class="alv-age-dot alv-age-1"></span>
                            <span class="age-label">1-30 days:</span>
                            <span class="age-value">€{{ %s.past_due_1_30|floatformat:0|add_thousand_separator }}</span>
                        </div>
                        <div class="age-segment-row">
                            <span class="alv-age-dot alv-age-2"></span>"""

P_OLD_LEG_D = _LEG % 'debtor'
P_NEW_LEG_D = _LEGN % ('debtor', 'debtor')
P_OLD_LEG_T = _LEG % 'totals'
P_NEW_LEG_T = _LEGN % ('totals', 'totals')

P_OLD_DOT61 = """                            <span class="age-dot age-dot-61-90"></span>"""
P_NEW_DOT61 = """                            <span class="alv-age-dot alv-age-3"></span>"""
P_OLD_DOT91 = """                            <span class="age-dot age-dot-91-plus"></span>"""
P_NEW_DOT91 = """                            <span class="alv-age-dot alv-age-4"></span>"""

P_OLD_JS_PILL = """            var daysClass = daysOverdue > 90 ? 'days-pill-severe' :
                            daysOverdue > 60 ? 'days-pill-high' :
                            daysOverdue > 30 ? 'days-pill-medium' :
                            daysOverdue > 0 ? 'days-pill-low' : 'days-pill-current';"""
P_NEW_JS_PILL = """            // THE SAME FIVE BANDS THE VIEW BUCKETS ON. These thresholds and
            // open_invoices_report's five branches are one decision; if they
            // ever part company an invoice gets two verdicts again, which is
            // the bug this round closed.
            var daysClass = daysOverdue > 90 ? 'alv-age-4' :
                            daysOverdue > 60 ? 'alv-age-3' :
                            daysOverdue > 30 ? 'alv-age-2' :
                            daysOverdue > 0 ? 'alv-age-1' : 'alv-age-0';"""

P_OLD_JS_USE = """                html += '<span class="days-pill ' + daysClass + '">' + daysOverdue + ' days late</span>';
            } else {
                html += '<span class="days-pill days-pill-current">Current</span>';"""
P_NEW_JS_USE = """                html += '<span class="alv-age-pill ' + daysClass + '">' + daysOverdue + ' days late</span>';
            } else {
                html += '<span class="alv-age-pill alv-age-0">Not yet due</span>';"""

P_OLD_JS_SPARK = """        const current = parseFloat(spark.dataset.current) || 0;
        const due3160 = parseFloat(spark.dataset['due-31-60']) || 0;
        const due6190 = parseFloat(spark.dataset['due-61-90']) || 0;
        const due91 = parseFloat(spark.dataset['due-91-plus']) || 0;"""
P_NEW_JS_SPARK = """        const notYetDue = parseFloat(spark.dataset['not-yet-due']) || 0;
        const due130 = parseFloat(spark.dataset['due-1-30']) || 0;
        const due3160 = parseFloat(spark.dataset['due-31-60']) || 0;
        const due6190 = parseFloat(spark.dataset['due-61-90']) || 0;
        const due91 = parseFloat(spark.dataset['due-91-plus']) || 0;"""

P_OLD_JS_SEG = """        const segments = [
            { value: current, className: 'sparkline-segment-current' },
            { value: due3160, className: 'sparkline-segment-31-60' },
            { value: due6190, className: 'sparkline-segment-61-90' },
            { value: due91, className: 'sparkline-segment-91-plus' }
        ];"""
P_NEW_JS_SEG = """        const segments = [
            { value: notYetDue, className: 'alv-age-0' },
            { value: due130, className: 'alv-age-1' },
            { value: due3160, className: 'alv-age-2' },
            { value: due6190, className: 'alv-age-3' },
            { value: due91, className: 'alv-age-4' }
        ];"""

P_OLD_JS_HTML = """                html += `<div class="sparkline-segment ${seg.className}" style="width: ${pct}%"></div>`;"""
P_NEW_JS_HTML = """                html += `<div class="alv-age-fill ${seg.className}" style="width: ${pct}%"></div>`;"""

# ---- the four colour families the scale replaces --------------------------
P_OLD_CSS_SPARK = """    .sparkline-segment {
        height: 100%;
    }
    .sparkline-segment-current { background-color: #28a745; }
    .sparkline-segment-31-60 { background-color: #ffc107; }
    .sparkline-segment-61-90 { background-color: #fd7e14; }
    .sparkline-segment-91-plus { background-color: #dc3545; }
"""
P_NEW_CSS_SPARK = """    /* The segments, the dots, the column tints and the pills all take their
       colour from base's ageing scale now. Four families of literal became
       one: .alv-age-N for the step, .alv-age-fill / -dot / -cell / -pill for
       what to do with it. */
"""

P_OLD_CSS_DOT = """    .age-dot-current { background-color: #28a745; }
    .age-dot-31-60 { background-color: #ffc107; }
    .age-dot-61-90 { background-color: #fd7e14; }
    .age-dot-91-plus { background-color: #dc3545; }
"""
P_NEW_CSS_DOT = ""

P_OLD_CSS_PILL = """    .days-pill-current {
        background: #d4edda;
        color: #155724;
    }
    .days-pill-low {
        background: #fff3cd;
        color: #856404;
    }
    .days-pill-medium {
        background: #ffe5d0;
        color: #b54708;
    }
    .days-pill-high {
        background: #f8d7da;
        color: #721c24;
    }
    .days-pill-severe {
        background: #dc3545;
        color: white;
    }
"""
P_NEW_CSS_PILL = ""

P_OLD_CSS_TINT = """.past-due-31-60 { background-color: #e1f5fe; }
.past-due-61-90 { background-color: #e0e4e7; }
.past-due-91-plus { background-color: #e3f2fd; }
"""
P_NEW_CSS_TINT = ""

P_OLD_OVERDUE = """.overdue {
    color: #dc3545;
    font-weight: bold;
}
"""
P_NEW_OVERDUE = """.overdue {
    color: var(--alv-bad);
    font-weight: bold;
}
"""

EDITS_PAGE = [
    ('the table gains a Not Yet Due column beside 1-30', P_OLD_HEAD, P_NEW_HEAD),
    ('  filled per tenant, tinted by step', P_OLD_CELLS, P_NEW_CELLS),
    ('  and in the totals row', P_OLD_TCELLS, P_NEW_TCELLS),
    ('the sparkline carries five values', P_OLD_SPARKDATA, P_NEW_SPARKDATA),
    ('  reads them', P_OLD_JS_SPARK, P_NEW_JS_SPARK),
    ('  and draws five segments off the scale', P_OLD_JS_SEG, P_NEW_JS_SEG),
    ('    on .alv-age-fill', P_OLD_JS_HTML, P_NEW_JS_HTML),
    ('the legend gains its two leading rows (per tenant)',
     P_OLD_LEG_D, P_NEW_LEG_D),
    ('  and in the totals card', P_OLD_LEG_T, P_NEW_LEG_T),
    ('the pill bands are the view\'s bands', P_OLD_JS_PILL, P_NEW_JS_PILL),
    ('  and it says "Not yet due" rather than "Current"',
     P_OLD_JS_USE, P_NEW_JS_USE),
]
EDITS_PAGE_ALL = [
    ('the 61-90 dots take the scale', P_OLD_DOT61, P_NEW_DOT61),
    ('the 91+ dots take the scale', P_OLD_DOT91, P_NEW_DOT91),
]

# The four literals left over once the scale lands. Three are "nothing owed"
# success states and one is the overdue row border - none of them is an ageing
# step, but leaving four Bootstrap literals behind would mean the suite's
# "no Bootstrap ageing literal survives" check had to be narrowed to excuse
# them, and a check narrowed to fit what is there stops being a check.
P_OLD_G1 = """.no-balances-icon {
    font-size: 4rem;
    color: #28a745;
    margin-bottom: 20px;
}
"""
P_NEW_G1 = """.no-balances-icon {
    font-size: 4rem;
    color: var(--alv-good);
    margin-bottom: 20px;
}
"""
P_OLD_G2 = """.sub-message {
    color: #28a745;
    font-weight: 500;
    font-size: 1rem !important;
}
"""
P_NEW_G2 = """.sub-message {
    color: var(--alv-good);
    font-weight: 500;
    font-size: 1rem !important;
}
"""
P_OLD_G3 = """.no-debt-message {
        margin-top: 8px;
        text-align: center;
        font-size: 13px;
        color: #28a745;
        font-weight: 500;
    }
"""
P_NEW_G3 = """.no-debt-message {
        margin-top: 8px;
        text-align: center;
        font-size: 13px;
        color: var(--alv-good);
        font-weight: 500;
    }
"""
P_OLD_BORD = """    .invoice-row-overdue {
        border-left: 3px solid #dc3545;
    }
"""
P_NEW_BORD = """    .invoice-row-overdue {
        border-left: 3px solid var(--alv-bad);
    }
"""

EDITS_PAGE_TOKENS = [
    ('the "nothing owed" green joins the good token', P_OLD_G1, P_NEW_G1),
    ('  in both places it is used', P_OLD_G2, P_NEW_G2),
    ('  and on mobile', P_OLD_G3, P_NEW_G3),
    ('the overdue row border joins the bad token', P_OLD_BORD, P_NEW_BORD),
]

EDITS_PAGE_CSS = [
    ('four families of literal colour go', P_OLD_CSS_SPARK, P_NEW_CSS_SPARK),
    ('  the dots', P_OLD_CSS_DOT, P_NEW_CSS_DOT),
    ('  the pills', P_OLD_CSS_PILL, P_NEW_CSS_PILL),
    ('  and the tint that encoded no order at all', P_OLD_CSS_TINT, P_NEW_CSS_TINT),
    ('overdue red joins the house token', P_OLD_OVERDUE, P_NEW_OVERDUE),
]


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read().replace('\r\n', '\n')


def one(text, old, new, what):
    n = text.count(old)
    if n != 1:
        sys.exit('! %s did not match exactly once (%d) - the file may already '
                 'have been edited:\n%s' % (what, n, old[:220]))
    return text.replace(old, new, 1)


def two(text, old, new, what):
    """Exactly twice - the legend is drawn per debtor AND for the totals."""
    n = text.count(old)
    if n != 2:
        sys.exit('! %s did not match exactly twice (%d):\n%s'
                 % (what, n, old[:220]))
    return text.replace(old, new)


def nocomment_html(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    # NOT re.S. Django's {# #} does not span lines, and a stripper more
    # permissive than the lexer it models certifies the faults it exists to
    # catch. That shipped once already.
    text = re.sub(r'\{#[^\n]*?#\}', '', text)

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


def nocomment_py(src):
    tree = ast.parse(src)
    for node in ast.walk(tree):
        body = getattr(node, 'body', None)
        if isinstance(body, list) and body and isinstance(body[0], ast.Expr) \
                and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            node.body = body[1:] or [ast.Pass()]
    return ast.unparse(tree)


def main():
    for p in (VIEW, BASE, PAGE):
        if not os.path.exists(p):
            sys.exit('! %s not found - run from the repo root' % p)
    vs, bs, pg = read(VIEW), read(BASE), read(PAGE)
    pg0 = pg          # the page as it stands, to measure the edit against

    if SENTINEL in vs:
        print('  ageing scale                   already applied')
        print('\n  0 file(s) changed')
        return

    for name, old, new in EDITS_VIEW:
        vs = one(vs, old, new, name)
    for name, old, new in EDITS_BASE:
        bs = one(bs, old, new, name)
    for name, old, new in EDITS_PAGE:
        pg = one(pg, old, new, name)
    for name, old, new in EDITS_PAGE_ALL:
        pg = two(pg, old, new, name)
    for name, old, new in EDITS_PAGE_CSS:
        pg = one(pg, old, new, name)
    for name, old, new in EDITS_PAGE_TOKENS:
        pg = one(pg, old, new, name)

    # ---- self-check BEFORE anything is written ----------------------------
    bad = []
    try:
        tree = ast.parse(vs)
    except SyntaxError as exc:
        sys.exit('! the patched invoices.py does not parse: %s' % exc)
    fns = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    if 'open_invoices_report' not in fns:
        sys.exit('! open_invoices_report is gone, nothing written')

    # THE VIEW MUST STILL BE PROTECTED. Read the decorator list off the tree,
    # not the file: inserting near a decorated function has silently moved the
    # decorators onto a neighbour in this project before, and the result
    # compiled cleanly with every searched-for string still present.
    _dec = [ast.unparse(d) for d in fns['open_invoices_report'].decorator_list]
    if not any('login_required' in d for d in _dec):
        bad.append('open_invoices_report lost @login_required')
    if not any('permission_required' in d for d in _dec):
        bad.append('open_invoices_report lost @permission_required')

    if 'age_bucket' not in fns:
        bad.append('the bucketing rule has no name of its own')
    else:
        _hb = nocomment_py(ast.get_source_segment(vs, fns['age_bucket']))
        # The thresholds, read as NUMBERS off the tree rather than as text.
        _cmp = sorted({c.value for n in ast.walk(fns['age_bucket'])
                       for c in getattr(n, 'comparators', [])
                       if isinstance(c, ast.Constant)
                       and isinstance(c.value, int)})
        if _cmp != [0, 30, 60, 90]:
            bad.append('the bucket thresholds are not 0/30/60/90 (%s)' % _cmp)
        if 'AGE_BUCKETS' not in _hb:
            bad.append('the rule does not return names from the one tuple')
    _rep = nocomment_py(ast.get_source_segment(vs, fns['open_invoices_report']))
    if 'current_0_30' in _rep:
        bad.append('the conflated bucket survives somewhere in the view')
    if 'age_bucket(' not in _rep:
        bad.append('the report does not use the rule it was given')
    if 'for _b in AGE_BUCKETS' not in _rep:
        bad.append('the totals are accumulated bucket by written-out bucket, '
                   'so a sixth could be added and never totalled')

    _bc = nocomment_html(bs)
    for _n in (1, 2, 3, 4):
        if '--alv-age-%d:' % _n not in _bc:
            bad.append('base has no --alv-age-%d token' % _n)
        if '--alv-age-%d-soft:' % _n not in _bc:
            bad.append('base has no --alv-age-%d-soft token' % _n)
    for _cls in ('.alv-age-dot', '.alv-age-fill', '.alv-age-cell',
                 '.alv-age-pill'):
        if not re.search(re.escape(_cls) + r'\s*[,{ ]', _bc):
            bad.append('%s is not defined in base.html' % _cls)
    # ENDS ANCHORED. If step 2 stops being the warn colour and step 4 the bad
    # one, the scale has drifted away from the semantics beside it.
    if '--alv-age-2:      #9a6a08' not in _bc:
        bad.append('step 2 is no longer the warn colour')
    if '--alv-age-4:      #b3261e' not in _bc:
        bad.append('step 4 is no longer the bad colour')

    _pc = nocomment_html(pg)
    # DEFINED, not merely referenced.
    for _cls in ('alv-age-dot', 'alv-age-fill', 'alv-age-cell', 'alv-age-pill'):
        if _cls in _pc and not re.search(r'\.%s\s*[,{ ]' % _cls, _bc):
            bad.append('%s is used on the page but defined nowhere' % _cls)
    for _dead in ('days-pill-', 'age-dot-current', 'age-dot-31-60',
                  'age-dot-61-90', 'age-dot-91-plus', 'sparkline-segment-',
                  'past-due-31-60', 'current_0_30'):
        if _dead in _pc:
            bad.append('%s survives on the page' % _dead)
    for _lit in ('#28a745', '#ffc107', '#fd7e14', '#dc3545'):
        if _lit in _pc:
            bad.append('the Bootstrap literal %s survives on the page' % _lit)
    if _pc.count('alv-age-cell') != 10:
        bad.append('the five columns are not tinted in both rows (%d cells)'
                   % _pc.count('alv-age-cell'))
    # Five legend rows, twice - per debtor and in the totals card.
    if _pc.count('alv-age-dot') != 10:
        bad.append('the legend does not carry five dots in both places (%d)'
                   % _pc.count('alv-age-dot'))
    # The page's own JS bands must be the view's bands.
    for _b in ('> 90', '> 60', '> 30', '> 0'):
        if _b not in _pc:
            bad.append('the pill lost its %s band' % _b)
    for _n in range(5):
        if "'alv-age-%d'" % _n not in _pc:
            bad.append('the pill never assigns alv-age-%d' % _n)

    # Structure.
    _th = len(re.findall(r'<th\b', pg))
    _css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', pg, re.S))
    if _css.count('{') != _css.count('}'):
        bad.append('page CSS braces do not balance')
    for o, c in ((r'\{%\s*if\b', r'\{%\s*endif\s*%\}'),
                 (r'\{%\s*for\b', r'\{%\s*endfor\s*%\}')):
        if len(re.findall(o, pg)) != len(re.findall(c, pg)):
            bad.append('a Django block no longer balances (%s)' % o)
    for _l in pg.split('\n'):
        if _l.count('{#') != _l.count('#}'):
            bad.append('a {# #} comment spans lines, which Django renders')
            break
    # BALANCE IS MEASURED AS A DELTA, not as equality. This page opens 52
    # <div> and closes 51 before anything is patched - a template with {% if %}
    # branches need not balance as raw text, and a check demanding equality
    # would fail on a file it never touched. What must hold is that THIS EDIT
    # opens and closes the same number of everything.
    _want = {'th': 1, 'td': 2, 'span': 6, 'div': 2}
    for tag in ('td', 'th', 'span', 'div'):
        _o = (len(re.findall(r'<%s\b' % tag, pg))
              - len(re.findall(r'<%s\b' % tag, pg0)))
        _c = (len(re.findall(r'</%s\s*>' % tag, pg))
              - len(re.findall(r'</%s\s*>' % tag, pg0)))
        if _o != _c:
            bad.append('the edit opens %d <%s> and closes %d' % (_o, tag, _c))
        elif _o != _want[tag]:
            bad.append('the edit adds %d <%s>, expected %d - the column or a '
                       'legend row is missing or doubled'
                       % (_o, tag, _want[tag]))
    # CONTROL on the stripper: this round's prose names every class it hunts.
    if SENTINEL in nocomment_py(ast.get_source_segment(
            vs, fns['open_invoices_report'])):
        bad.append('CONTROL: comments are not being stripped from the view')

    if bad:
        sys.exit('! ageing-scale self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    for name, _o, _n in (EDITS_VIEW + EDITS_BASE + EDITS_PAGE
                         + EDITS_PAGE_ALL + EDITS_PAGE_CSS
                         + EDITS_PAGE_TOKENS):
        print('  %s' % name)

    if not CHECK:
        for path, out in ((VIEW, vs), (BASE, bs), (PAGE, pg)):
            b = path + SUFFIX
            if not os.path.exists(b):
                shutil.copy2(path, b)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(out)

    print('\n  3 file(s) %s' % ('would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
