# -*- coding: utf-8 -*-
"""apply_series_scale.py - Section D, round D5: base earns a series scale,
and two charts stop repainting themselves.

    python apply_series_scale.py --check     dry run, nothing written
    python apply_series_scale.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

Decided 23 Sep. See claude/d5_decisions.md and
claude/d5_chart_colours_survey.md. Everything below was MEASURED - the
colours through a palette validator, the repaint by reading what the two
charts index their colours by.

  1. TWO LINES WERE THE SAME COLOUR.

       financial_indicators   the PORTFOLIO AVERAGE #0e7c8b and the 12th
                              property #00838f          delta-E  2.0
       act_expense            properties 10 and 11
                              #d6336c and #c2255c       delta-E  5.0

     The floor is 15; below it they cannot be told apart at all. Both
     twelve-colour arrays FAILED a validator outright, and the two arrays
     shared not one value with each other.

     Base now carries eight hues that pass every check. The order is
     load-bearing - the checks run on ADJACENT pairs, and two re-orderings
     tried here dropped CVD separation into the band that is legal only
     with a second encoding. A ninth property takes slot 1 again with a
     second MARK: a dash on financial_indicators, which is a line chart,
     and a point SHAPE on act_expense, where a property is a dot and a
     dash would say nothing. Neither chart can use the other's, because
     financial_indicators already uses shape for the year.

  2. BOTH CHARTS REPAINTED THEMSELVES WHEN YOU FILTERED.

     financial_indicators counted `ci` over the TICKED properties, so
     unticking one changed the colour of every property below it.
     act_expense's endpoint omits a property with no data in the chosen
     years, so changing the YEAR RANGE reshuffled the colours.

     Both views now pass a `slot` - a property's rank among ALL
     properties, ordered by prop_id. Unticking, filtering and ADDING a
     property move nothing. No migration.

  3. THE PORTFOLIO LINE WAS TOLD APART BY COLOUR ALONE, and its colour
     was delta-E 2.0 from a property's. It is heavier now: 4 against 2.

  4. THE STATUS LITERALS. 59 sites on two pages, counted rather than
     remembered - the survey had said twelve. cashflow_forecast drew its
     own teal #0f766e ten times, delta-E 4.5 from the house accent: a
     second, almost identical teal nobody could see was different.

     Its income and outflow bars keep the colours they have - accent and
     bad - named rather than spelled, and flat rather than gradient,
     because there is no token for a gradient's light end.

     Six rules on that page were DEAD: .legend-color and .timeline-bar in
     .red, .orange and .green are never put on an element, in markup or in
     any string a script builds. They go. The .summary-card headers keep
     theirs - those ARE applied, and they paint a time horizon in status
     colours, which is a question for its own round.

     vacancy_management painted three INDICATORS and the bars below them
     out of the same green / amber / red, so one colour meant two things
     on one screen. The indicators are categories and take series tokens;
     the bars are a grading and take grade steps; the portfolio average
     line takes ink, because it is what the bars are measured against.
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

CHECK = '--check' in sys.argv
T = os.path.join('pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
SUFFIX = '.bak_series'
SUITE = 'test_series_scale.py'
PS1 = 'Push-PendingChanges.ps1'
ROUNDS_FILE = 'alv_rounds.py'
BASE = os.path.join(T, 'base.html')

report, problems, planned = [], [], {}
CRLF = {}
swept = []


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    CRLF[p] = '\r\n' in raw
    return raw.replace('\r\n', '\n')


def write(p, text):
    if CRLF.get(p):
        text = text.replace('\n', '\r\n')
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


WHY = {}
SCALE = """        /* THE SERIES SCALE - one colour per THING, on a chart.
           ===== ALV SERIES SCALE v1 ===== 23 Sep 2026

           act_expense and financial_indicators each drew one mark per
           property from its own hardcoded array of twelve colours, and the
           two arrays shared not one value. Run through a palette validator,
           both FAILED, and two pairs were the same colour to a reader with
           ordinary sight:

             financial_indicators  the PORTFOLIO line #0e7c8b and the 12th
                                   property #00838f      delta-E  2.0
             act_expense           properties 10 and 11
                                   #d6336c and #c2255c   delta-E  5.0

           The floor is 15. Below it the two cannot be told apart at all -
           and on Financial Indicators the collision was with the portfolio
           average, the line every property is being compared against.

           THE HOUSE INKS CANNOT DO THIS JOB, and that was measured before
           this scale was written. The five tag inks were tried first: all
           five fall below the chroma floor (they read as grey on a chart
           surface), moss and clay separate by delta-E 2.1 under protanopia,
           slate and plum by 7.5 in ordinary sight. Those inks were drawn to
           sit BEHIND TEXT IN A CHIP, where low chroma is the whole point. A
           2px mark on white is a different job and needs more colour. A
           second, more muted attempt failed the same two checks. So this
           scale is louder than the rest of the palette on purpose.

           VALIDATED, not chosen by eye:
             lightness band    all 8 inside L 0.43-0.77   PASS
             chroma floor      all 8 >= 0.1               PASS
             CVD separation    worst adjacent 9.1         PASS
             normal vision     worst adjacent 19.6        PASS
             contrast          3 slots under 3:1          WARN - relieved by
                               the legend both charts already carry

           THE ORDER IS LOAD-BEARING. The checks are run on ADJACENT pairs,
           so re-ordering can break them: two re-orderings tried here
           dropped CVD separation to 6.1 and 6.9, into the band that is
           legal only with a second encoding. This order is the validated
           one, rotated by one place so that BLUE - the only hue within
           delta-E 15 of the accent, at 12.4 - lands in the last slot
           instead of the first. Rotation preserves every adjacent pair.
           Check any change with a validator; do not eyeball it.

           NOT A STATUS COLOUR. good, warn, bad and the grade steps are
           reserved for what a number MEANS. These say only WHICH thing a
           mark belongs to, and a chart must never borrow one for the other.

           EIGHT, AND NO NINTH HUE. A ninth series does not get a generated
           colour - it takes slot 1 again with a second MARK, so no two
           series are ever identical: a dash on a line chart, a different
           point shape where the mark is a dot. Sixteen distinguishable
           series; past that a chart needs fewer things on it, not more
           colours.                                  [test_series_scale.py] */
        --alv-series-1:   #eb6834;   /* orange  */
        --alv-series-2:   #1baf7a;   /* aqua    */
        --alv-series-3:   #eda100;   /* yellow  */
        --alv-series-4:   #e87ba4;   /* magenta */
        --alv-series-5:   #008300;   /* green   */
        --alv-series-6:   #4a3aa7;   /* violet  */
        --alv-series-7:   #e34948;   /* red     */
        --alv-series-8:   #2a78d6;   /* blue    */

"""

# ==========================================================================
# The edit tables. Every anchor was checked to appear exactly once before
# this file was written; the patcher checks again and refuses if not.
# ==========================================================================
BASE_ANCHOR = "        /* Action colours for the icon buttons. */\n"

# --- the two views: a property's SLOT, not its place in a filtered list ---
EXP_VIEW = os.path.join('pages', 'views', 'expenses.py')
FIN_VIEW = os.path.join('pages', 'views', 'finance.py')

SLOT_NOTE = (
    "    # THE CHART'S COLOUR FOLLOWS THE PROPERTY, not its place in this\n"
    "    # list. %s\n"
    "    # The slot is a property's rank among ALL properties, ordered by the\n"
    "    # one thing about it that never changes. Adding a property appends;\n"
    "    # nothing already on the chart moves. [D5]\n"
    "    slot_of = {pid: i for i, pid in enumerate(\n"
    "        props.objects.order_by('prop_id').values_list('prop_id',\n"
    "                                                      flat=True))}\n\n")

EDITS = {}
BASE_DOC = '__base_doc__'
# LATER, and in the same file: base's own standards block INDEXES the
# vocabulary base carries, and test_standards_doc counts the tokens the
# index names against the tokens that exist. A new family that is not in
# the index is a family the standard does not know about - so it goes in,
# beside the two scales it sits nearest.
EDITS[BASE_DOC] = [(
    # The block states a COUNT, and test_standards_doc checks it against
    # what base really declares - a count is a measurement, and it moves
    # with the decision rather than being left to drift (lesson 14).
    "  54 design tokens and the component classes below.",
    "  62 design tokens and the component classes below."), (
    "    Grading    --alv-grade-1 .. --alv-grade-5  (+ -soft)\n",
    "    Grading    --alv-grade-1 .. --alv-grade-5  (+ -soft)\n"
    "    Series     --alv-series-1 .. --alv-series-8   one colour per THING\n"
    "               on a chart - never a status, never cycled past eight\n")]

EDITS[EXP_VIEW] = [(
    "    properties = []\n"
    "    for p in props.objects.all().order_by('prop_country', 'prop_name'):\n",
    SLOT_NOTE % ("The list below DROPS a property with no data in the\n"
                 "    # chosen years, so its index moved whenever the year range\n"
                 "    # moved - and the chart repainted itself when it did.")
    + "    properties = []\n"
      "    for p in props.objects.all().order_by('prop_country', 'prop_name'):\n"), (
    "            properties.append({\n"
    "                'prop_id': p.prop_id,\n",
    "            properties.append({\n"
    "                'prop_id': p.prop_id,\n"
    "                'slot': slot_of.get(p.prop_id, 0),\n")]

EDITS[FIN_VIEW] = [(
    "    prop_series = []\n"
    "    for prop in properties:\n"
    "        pm = meta[prop.prop_id]\n"
    "        prop_series.append({\n"
    "            'id': prop.prop_id,\n"
    "            'name': pm['name'],\n",
    SLOT_NOTE % ("`properties` here is filtered to Active, and the chart\n"
                 "    # then drew only the TICKED ones - so unticking one property\n"
                 "    # repainted every property below it.")
    + "    prop_series = []\n"
      "    for prop in properties:\n"
      "        pm = meta[prop.prop_id]\n"
      "        prop_series.append({\n"
      "            'id': prop.prop_id,\n"
      "            'slot': slot_of.get(prop.prop_id, 0),\n"
      "            'name': pm['name'],\n")]

# --- act_expense: a property is a DOT here, so lap two is a SHAPE --------
ACT = os.path.join(T, 'act_expense.html')
EDITS[ACT] = [(
    "    var PALETTE = ['#0e7c8b','#e8590c','#2f9e44','#7048e8','#1c7ed6',"
    "'#e64980','#f08c00','#0ca678','#5c7cfa','#d6336c','#c2255c','#495057'];\n",
    "    // THE SERIES SCALE, read from base - see ALV SERIES SCALE v1. The\n"
    "    // twelve colours that used to be here failed a palette validator:\n"
    "    // properties 10 and 11 were delta-E 5.0 apart, which is the same\n"
    "    // colour to anyone looking at it, and slot 1 was the accent, which\n"
    "    // is the portfolio's own teal on the other chart.\n"
    "    //\n"
    "    // A NINTH PROPERTY DOES NOT GET A NINTH COLOUR. It takes slot 1\n"
    "    // again with a different POINT SHAPE. On this chart a property is a\n"
    "    // dot, not a line, so a dash would say nothing - which is why the\n"
    "    // second mark here is a shape and on financial_indicators, where\n"
    "    // shape already means the year, it is a dash. [D5]\n"
    "    var SERIES_FALLBACK = ['#eb6834','#1baf7a','#eda100','#e87ba4',\n"
    "                           '#008300','#4a3aa7','#e34948','#2a78d6'];\n"
    "    var SERIES = SERIES_FALLBACK.map(function(fb, i){\n"
    "        return anTok('series-' + (i + 1), fb);\n"
    "    });\n"
    "    var SERIES_SHAPES = ['circle', 'triangle'];\n"
    "    function seriesColour(slot){\n"
    "        return SERIES[(slot || 0) % SERIES.length];\n"
    "    }\n"
    "    function seriesShape(slot){\n"
    "        return SERIES_SHAPES[Math.floor((slot || 0) / SERIES.length)\n"
    "                             % SERIES_SHAPES.length];\n"
    "    }\n"), (
    "            var col = PALETTE[idx % PALETTE.length];\n",
    "            var col = seriesColour(p.slot), shape = seriesShape(p.slot);\n"), (
    "                    pointRadius: pts.map(function(_,i){ return 3+5*(i/(n-1)); }),\n"
    "                    pointHoverRadius: 9\n",
    "                    pointRadius: pts.map(function(_,i){ return 3+5*(i/(n-1)); }),\n"
    "                    pointStyle: shape,\n"
    "                    pointHoverRadius: 9\n"), (
    "                pointBorderColor:'#fff', pointBorderWidth:2, pointRadius:8, pointHoverRadius:10\n",
    "                pointBorderColor:'#fff', pointBorderWidth:2, pointRadius:8,\n"
    "                pointStyle: shape, pointHoverRadius:10\n")]

# --- financial_indicators: a true line chart, so lap two is a DASH -------
FI = os.path.join(T, 'finance', 'financial_indicators.html')
EDITS[FI] = [(
    "    var PALETTE = ['#e67e22', '#2c82c9', '#27ae60', '#8e44ad', "
    "'#c0392b', '#16a085',\n                   '#d35400', '#2980b9', "
    "'#f39c12', '#7f8c8d', '#c2185b', '#00838f'];\n",
    "    // THE SERIES SCALE, read from base - see ALV SERIES SCALE v1. The\n"
    "    // twelve colours that used to be here put #00838f in slot 12, which\n"
    "    // is delta-E 2.0 from PORT above - the PORTFOLIO AVERAGE line, the\n"
    "    // one every property is being compared against. With twelve\n"
    "    // properties selected, one of them WAS the portfolio line.\n"
    "    //\n"
    "    // A NINTH PROPERTY DOES NOT GET A NINTH COLOUR. It takes slot 1\n"
    "    // again with a DASHED line. Shape is not available here: styleFor\n"
    "    // already uses it to mark the current and future years. [D5]\n"
    "    var AN_CS = getComputedStyle(document.documentElement);\n"
    "    function anTok(name, fallback){\n"
    "        var v = AN_CS.getPropertyValue('--alv-' + name);\n"
    "        return (v && v.trim()) || fallback;\n"
    "    }\n"
    "    var SERIES_FALLBACK = ['#eb6834','#1baf7a','#eda100','#e87ba4',\n"
    "                           '#008300','#4a3aa7','#e34948','#2a78d6'];\n"
    "    var SERIES = SERIES_FALLBACK.map(function(fb, i){\n"
    "        return anTok('series-' + (i + 1), fb);\n"
    "    });\n"
    "    function seriesColour(slot){\n"
    "        return SERIES[(slot || 0) % SERIES.length];\n"
    "    }\n"
    "    function seriesDash(slot){\n"
    "        return Math.floor((slot || 0) / SERIES.length) % 2 ? [6, 4] : [];\n"
    "    }\n"), (
    "            var color = PALETTE[ci % PALETTE.length]; ci++;\n"
    "            out.push(Object.assign({ label: p.name, data: p[ind].slice(i0, i1 + 1) }, styleFor(color, vYears)));\n",
    "            // p.slot, NOT ci: ci counted only the TICKED properties, so\n"
    "            // unticking one repainted every property below it. [D5]\n"
    "            out.push(Object.assign(\n"
    "                { label: p.name, data: p[ind].slice(i0, i1 + 1) },\n"
    "                styleFor(seriesColour(p.slot), vYears,\n"
    "                         { dash: seriesDash(p.slot) })));\n"), (
    "    function styleFor(color, years) {\n"
    "        return {\n"
    "            borderColor: color, backgroundColor: color, tension: 0.25, spanGaps: true,\n"
    "            pointBackgroundColor: color,\n",
    "    function styleFor(color, years, opts) {\n"
    "        // WIDTH IS AN ENCODING HERE. The portfolio line used to be told\n"
    "        // apart from a property only by its colour, and its colour was\n"
    "        // delta-E 2.0 from one of them. It is heavier now, so it reads\n"
    "        // as the baseline in grey scale, in print, and to a reader who\n"
    "        // cannot separate the two hues. [D5]\n"
    "        opts = opts || {};\n"
    "        return {\n"
    "            borderColor: color, backgroundColor: color, tension: 0.25, spanGaps: true,\n"
    "            borderWidth: opts.width || 2,\n"
    "            borderDash: opts.dash || [],\n"
    "            pointBackgroundColor: color,\n"), (
    "        var out = [Object.assign({ label: 'Portfolio', data: DATA.portfolio[ind].slice(i0, i1 + 1) }, styleFor(PORT, vYears))];\n"
    "        var ids = selectedIds(), ci = 0;\n",
    "        var out = [Object.assign(\n"
    "            { label: 'Portfolio', data: DATA.portfolio[ind].slice(i0, i1 + 1) },\n"
    "            styleFor(PORT, vYears, { width: 4 }))];\n"
    "        var ids = selectedIds();\n")]

# ==========================================================================
# The status literals. Two pages, counted rather than remembered: the survey
# said "5 and 7" and it is 59. Each swap carries the number of sites it must
# find, and the patcher prints every line it changes.
# ==========================================================================
CFF = os.path.join(T, 'finance', 'cashflow_forecast.html')
VAC = os.path.join(T, 'finance', 'vacancy_management.html')

# Whole declarations first, so the gradients are gone before the literal
# sweep below runs. The two bars lose their gradient and become a flat token
# fill: there is no token for a gradient's light end, and inventing two
# would be adding tokens to the system that nothing asked for. What is left
# is the same two colours, flat - and flat is what a chart mark should be.
EDITS[CFF] = [(
    "    .legend-color.income{background:linear-gradient(135deg,#0f9488 0%,"
    "#0f766e 100%);}\n"
    "    .legend-color.outflow{background:linear-gradient(135deg,#e2685f 0%,"
    "#d9534f 100%);}\n"
    "    .timeline-bar.cf-bar-income{background:linear-gradient(135deg,"
    "#0f9488 0%,#0f766e 100%) !important;}\n"
    "    .timeline-bar.cf-bar-out{background:linear-gradient(135deg,#e2685f "
    "0%,#d9534f 100%) !important;}\n",
    "    /* Money in is the house accent, money out is the bad token - the\n"
    "       same two colours these already were, named instead of spelled,\n"
    "       and flat rather than a gradient. [D5] */\n"
    "    .legend-color.income{background:var(--alv-accent);}\n"
    "    .legend-color.outflow{background:var(--alv-bad);}\n"
    "    .timeline-bar.cf-bar-income{background:var(--alv-accent) !important;}\n"
    "    .timeline-bar.cf-bar-out{background:var(--alv-bad) !important;}\n"), (
    # DEAD. Neither .red, .orange nor .green is ever put on an element on
    # this page - not in markup, not in any string a script builds. Six
    # rules, twelve literals, worn by nothing. The summary-card headers
    # above keep theirs: those ARE applied.
    "\n.legend-color.red { background: linear-gradient(135deg, #dc3545 0%, "
    "#c82333 100%); }\n"
    ".legend-color.orange { background: linear-gradient(135deg, #fd7e14 0%, "
    "#e8630a 100%); }\n"
    ".legend-color.green { background: linear-gradient(135deg, #28a745 0%, "
    "#218838 100%); }\n",
    "\n"), (
    "\n.timeline-bar.red { background: linear-gradient(135deg, #dc3545 0%, "
    "#c82333 100%); }\n"
    ".timeline-bar.orange { background: linear-gradient(135deg, #fd7e14 0%, "
    "#e8630a 100%); }\n"
    ".timeline-bar.green { background: linear-gradient(135deg, #28a745 0%, "
    "#218838 100%); }\n",
    "\n")]

# --- vacancy_management: three CATEGORIES and one GRADING, told apart ----
EDITS[VAC] = [(
    "                color: '#28a745', \n",
    "                color: anTok('series-1', '#eb6834'),\n"), (
    "                color: '#fd7e14', \n",
    "                color: anTok('series-2', '#1baf7a'),\n"), (
    "                color: '#e74c3c', \n",
    "                color: anTok('series-3', '#eda100'),\n"), (
    "                if (value === 0) return '#28a745';\n"
    "                return value <= portfolioAverage ? '#28a745' : value <= "
    "portfolioAverage * 1.2 ? '#ffc107' : '#dc3545';\n"
    "            } else {\n"
    "                return value >= portfolioAverage ? '#28a745' : value >= "
    "portfolioAverage * 0.8 ? '#ffc107' : '#dc3545';\n"
    "            }\n",
    "                if (value === 0) return GRADE_GOOD;\n"
    "                return value <= portfolioAverage ? GRADE_GOOD\n"
    "                     : value <= portfolioAverage * 1.2 ? GRADE_MID\n"
    "                     : GRADE_BAD;\n"
    "            } else {\n"
    "                return value >= portfolioAverage ? GRADE_GOOD\n"
    "                     : value >= portfolioAverage * 0.8 ? GRADE_MID\n"
    "                     : GRADE_BAD;\n"
    "            }\n"), (
    "                    borderColor: '#ff6b35',\n",
    "                    // A REFERENCE LINE, not a series. It is the thing\n"
    "                    // every bar is measured against, so it takes ink\n"
    "                    // rather than a colour that could be mistaken for\n"
    "                    // one of the grades beside it. [D5]\n"
    "                    borderColor: anTok('ink-soft', '#5b6b73'),\n")]

# The token reader, and the three grade steps the bars use. Placed at the
# top of the page's own script, before anything reads them.
EDITS[VAC].insert(0, (
    "<script>\n"
    "// Global variables\n"
    "let dashboardInstance = null;\n",
    "<script>\n"
    "// THE TOKENS, read from base - see ALV SERIES SCALE v1 and the grading\n"
    "// scale. This page painted three INDICATORS (three categories) and the\n"
    "// bars BELOW them (a grading against the portfolio average) out of the\n"
    "// same green / amber / red, so the same colour meant two different\n"
    "// things on one screen. The indicators take series tokens; the bars\n"
    "// take grade steps; the average line takes ink. [D5]\n"
    "const AN_CS = getComputedStyle(document.documentElement);\n"
    "function anTok(name, fallback){\n"
    "    const v = AN_CS.getPropertyValue('--alv-' + name);\n"
    "    return (v && v.trim()) || fallback;\n"
    "}\n"
    "const GRADE_GOOD = anTok('grade-1', '#1e7d4f');\n"
    "const GRADE_MID  = anTok('grade-3', '#5b6b73');\n"
    "const GRADE_BAD  = anTok('grade-5', '#b3261e');\n"
    "\n"
    "// Global variables\n"
    "let dashboardInstance = null;\n"))

# --- the plain literal sweep, per page, with the count each must find ----
# Applied INSIDE these two files only, after the edits above have removed
# every literal that belonged to a rule being rewritten or deleted.
SWEEP = {
    CFF: [('#0f766e', 'var(--alv-accent)',   8),
          ('#c0392b', 'var(--alv-bad)',      5),
          ('#2c3e50', 'var(--alv-ink)',      7),
          ('#f8f9fa', 'var(--alv-surface)',  6),
          ('#dee2e6', 'var(--alv-line)',     8),
          ('#e9ecef', 'var(--alv-line)',     1),
          ('#cfe3e0', 'var(--alv-accent-line)', 1),
          ('#0e7c8b', 'var(--alv-accent)',  13),
          ('#0a5e6a', 'var(--alv-accent-ink)', 5)],
    VAC: [('#2c3e50', 'var(--alv-ink)',      5)],
}

WHY = {
    BASE: '+ ALV SERIES SCALE v1',
    EXP_VIEW: "passes each property's slot",
    FIN_VIEW: "passes each property's slot",
    ACT: 'reads the scale; a dot takes a SHAPE for lap two',
    FI: 'reads the scale; a line takes a DASH; Portfolio is heavier',
    CFF: 'income/outflow named, six dead rules gone',
    VAC: 'three categories and one grading, told apart',
}

# --- base takes the scale ------------------------------------------------
if not os.path.isfile(BASE):
    problems.append('%s not found' % BASE)
else:
    b = read(BASE)
    if 'ALV SERIES SCALE v1' in b:
        report.append('%-40s already holds the series scale' % 'base.html')
    elif b.count(BASE_ANCHOR) != 1:
        problems.append('base.html: the anchor was found %d time(s)'
                        % b.count(BASE_ANCHOR))
    else:
        cur = b.replace(BASE_ANCHOR, SCALE + BASE_ANCHOR, 1)
        # and the standards index, in the same file and the same breath
        for old_, new_ in EDITS[BASE_DOC]:
            if new_ in cur:
                continue
            if cur.count(old_) != 1:
                problems.append('base.html: the standards index anchor was '
                                'found %d time(s)' % cur.count(old_))
                continue
            cur = cur.replace(old_, new_, 1)
        planned[BASE] = (b, cur)
        report.append('%-40s %s, and the standards index names it'
                      % ('base.html', WHY[BASE]))

# --- the anchored edits --------------------------------------------------
for path in (EXP_VIEW, FIN_VIEW, ACT, FI, CFF, VAC):
    if not os.path.isfile(path):
        problems.append('%s not found' % path)
        continue
    src = read(path)
    cur, n, done = src, 0, 0
    for old, new in EDITS[path]:
        # Which "already applied?" question to ask depends on the SHAPE of
        # the edit, and getting it wrong is silent:
        #   an INSERTION keeps its anchor, so "is the old text gone" is
        #   never true and the edit repeats every run (lesson 27);
        #   a REMOVAL's replacement is a newline, which is trivially
        #   present, so "is the new text here" is true before it has run
        #   and the edit NEVER happens - which is what the six dead rules
        #   on cashflow_forecast did on the first dry run of this patcher.
        # So ask the growing edits one question and the shrinking ones the
        # other.
        if len(new) > len(old):
            if new in cur:
                done += 1
                continue
        elif old not in cur:
            done += 1
            continue
        if cur.count(old) != 1:
            problems.append('%s: anchor found %d time(s): %r'
                            % (path, cur.count(old), old.strip()[:56]))
            continue
        cur = cur.replace(old, new, 1)
        n += 1
    # --- the literal sweep, inside this file only, counted ---------------
    for lit, tok, want in SWEEP.get(path, []):
        got = cur.count(lit)
        if got == 0:
            continue
        if got != want:
            problems.append('%s: %s is on %d site(s), expected %d - the '
                            'count was measured, so a different number '
                            'means the file moved under this round'
                            % (os.path.basename(path), lit, got, want))
            continue
        for ln in cur.split('\n'):
            if lit in ln:
                swept.append((os.path.basename(path), lit, tok,
                              ' '.join(ln.split())[:74]))
        cur = cur.replace(lit, tok)
        n += got
    if n:
        if path.endswith('.py'):
            try:
                compile(cur, path, 'exec')
            except SyntaxError as e:
                problems.append('%s would not compile: line %s'
                                % (path, e.lineno))
        planned[path] = (src, cur)
        report.append('%-40s %s (%d edit(s))'
                      % (os.path.basename(path), WHY[path], n))
    elif done == len(EDITS[path]):
        report.append('%-40s already done' % os.path.basename(path))

# --- self-checks: what the round must NOT have done ---------------------
for path, (src, cur) in list(planned.items()):
    name = os.path.basename(path)
    if path == BASE:
        # DECLARATIONS, not mentions: the standards index names the family
        # twice more, which is the point of an index.
        _decl = len(re.findall(r'--alv-series-\d:\s*#', cur))
        if _decl != 8:
            problems.append('base.html: %d series token(s) declared, '
                            'expected 8' % _decl)
        continue
    if path.endswith('.html'):
        if cur.count('{') != cur.count('}'):
            problems.append('%s: braces are unbalanced' % name)
        if sorted(re.findall(r'\bid="([^"]+)"', cur)) \
                != sorted(re.findall(r'\bid="([^"]+)"', src)):
            problems.append('%s: an id changed' % name)
        if cur.count('{%') != src.count('{%') \
                or cur.count('{{') != src.count('{{'):
            problems.append('%s: a Django tag changed' % name)
    if path in (ACT, FI):
        if 'PALETTE' in cur:
            problems.append('%s: a PALETTE is left behind' % name)
        if re.search(r'var (col|color) = \w+\[\w+ % ', cur):
            problems.append('%s: a colour is still taken by POSITION' % name)
    if path == CFF:
        for dead in ('.legend-color.red', '.timeline-bar.red',
                     '.legend-color.green', '.timeline-bar.green'):
            if dead in cur:
                problems.append('%s: %s survived' % (name, dead))
        if 'linear-gradient(135deg,var(--alv-accent)' in cur:
            problems.append('%s: a bar kept a gradient of one colour' % name)
    if path == VAC:
        if 'GRADE_GOOD' not in cur or 'anTok' not in cur:
            problems.append('%s: the token reader did not land' % name)

# --- registered, and on the gate ----------------------------------------
if os.path.isfile(ROUNDS_FILE):
    r = read(ROUNDS_FILE)
    if "'%s'" % SUFFIX in r:
        report.append('%-40s already lists this round' % ROUNDS_FILE)
    elif r.count("    '.bak_field',\n]") != 1:
        problems.append('%s: cannot find the end of ROUNDS (.bak_field) - '
                        'apply_filter_field.py first' % ROUNDS_FILE)
    else:
        planned[ROUNDS_FILE] = (r, r.replace(
            "    '.bak_field',\n]",
            "    '.bak_field',\n    '%s',\n]" % SUFFIX, 1))
        report.append('%-40s learns %s' % (ROUNDS_FILE, SUFFIX))
else:
    problems.append('%s missing' % ROUNDS_FILE)

GATE_NOTE = """    # Section D round D5: base owns the series scale, a property keeps its
    # colour when the chart is filtered, and 59 status literals take tokens,
    'test_series_scale.py'"""
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-40s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        if not m:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            planned[PS1] = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-40s + %s' % (PS1, SUITE))
else:
    problems.append('%s missing' % PS1)

print('\n' + '=' * 78)
print('SECTION D, ROUND D5 - THE SERIES SCALE - %s'
      % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 78)
for line in report:
    print('  ' + line)
if swept:
    print('\n  EVERY LITERAL THIS ROUND REPLACED, and the line it sat on:')
    for f, lit, tok, ln in swept:
        print('    %-26s %-9s -> %-22s %s' % (f[:26], lit, tok, ln[:52]))
print('')
if problems:
    print('!' * 78)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 78)
    for p in sorted(set(problems)):
        print('  FAIL %s' % p)
    sys.exit(1)
if not planned:
    print('  Nothing to do - this round has already been applied.')
    sys.exit(0)
if CHECK:
    print('  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)
for path, (src, text) in sorted(planned.items()):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        CRLF[bak] = CRLF.get(path)
        write(bak, src)
    write(path, text)
print('  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
print('')
print('  Next:  python %s' % SUITE)
