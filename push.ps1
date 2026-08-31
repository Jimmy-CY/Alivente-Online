.\Push-PendingChanges.ps1 -Push `
  -Message "A grading scale with names, the two detail tables on the standard, and group D closed" `
  -Body @'
THE HEAT MAP HAD NO TOKENS BEHIND IT. Every cell of the Financial Indicators
detail table took an inline background from

    const hue = (1 - t) * 120;
    return `background-color: hsl(${hue}, 62%, 90%);`;

Unlike the row tints deleted on 31 Aug, this colour carries REAL information -
where a property sits in the distribution for that metric - so it does not go.
But a continuous rainbow computed in JavaScript is outside the token system,
cannot be printed, cannot be checked, and puts red next to green.

base gains .alv-grade-1..5: five steps, best to worst, on the same mechanism as
.alv-age-* (a step class sets two custom properties, an application class
consumes them). Deliberately NOT the same family - ageing runs "not ageing" to
"severe" and begins at good, while a grade runs across a distribution and has a
MIDDLE. Ends anchored on tokens that already exist: step 1 IS --alv-good, step
5 IS --alv-bad, step 3 is neutral, exactly as .alv-age-4 IS --alv-bad. A scale
whose ends float free of the semantics around it drifts, and this one had
drifted all the way to hsl().

Colour is REDUNDANT here rather than load-bearing: every graded cell also
prints its figure, so a reader who cannot separate the two ends still has the
number. The suite asserts that, because it is the condition under which a
green-to-red scale is defensible at all.

THE BUG THIS ROUND NEARLY SHIPPED, AND WHAT CAUGHT IT. The first draft read the
comment above the old ramp - "0 = red (worst) .. 120 = green (best)" - as
describing t, and mapped Math.floor((1 - t) * 5). That comment describes the
HUE, not t. gradeColumn sorts BEST FIRST and stores position / (n - 1), so t=0
is the best property in its column. The draft therefore inverted the entire
table: every figure still looked plausible, and the suite confirmed it, because
a suite proves the code does what you specified.

What caught it was rendering the BEFORE panel of the comparison image and
seeing the best-ranked row come out pink. Reading the code would not have done
it; asking what the code PRODUCES did. Both halves are now asserted - that
gradeColumn still sorts best-first, and that the step function reads t that way
round - so the direction cannot silently flip.

FOUND BY RENDERING, SECOND ONE. `.highlighted-column` painted the sorted column
`background: #e3f2fd !important`, and !important in a stylesheet beats an
inline style - so sorting a column ERASED the grading in the very column the
reader had just asked to look at. That was true before this round too. The mark
moves to the column's edges and its weight, where it cannot compete with the
scale, and the suite renders a sorted and an unsorted cell of the same step and
requires them to match.

GROUP D IS CLOSED. Both pages redefined .table-container as a horizontal
scroller while base uses that name for a CLIPPING panel. base's own comment
says these two pages "belong on this, in a round of their own". This is that
round, and the answer is not a rename: the redefinition is DELETED and the
sideways scroll gets its own name, .ind-wide.

NOT base's .alv-matrix-scroll, which was the obvious home - it carries
display:none inside @media print, because the expense matrix deliberately does
not print. These tables do print, and did. Moving them onto that name would
have stopped it silently.

THE TABLES. .data-table becomes .alv-table; the PORTFOLIO row moves out of the
tbody into a real <tfoot>, so it repeats on every printed page; every cell
gains a data-label. Vacancy's hand-rolled .table-panel / .table-header /
.table-title becomes .alv-card / .alv-card-head / .alv-card-title - the same
three CSS rules were DEAD in financial_indicators.html, whose markup uses
.fi-section. And two more hand-rolled phone views go: a hundred lines of card
CSS in Financial Indicators, and Vacancy's "Please rotate your device" prompt.
base's card view does both, and needs no instructions.

TWO SECTION 4b EDITS, both scope guards that had to invert.
  * test_sticky_sweep.py has now moved this expectation three times: first
    because neither page used .alv-table, then because the .alv-table they
    gained sat outside the redefined name, and now because the redefinition
    itself is gone. It asserts the strongest form: the pages must NOT redefine
    .table-container, and nothing on them claims the name.
  * test_ind_modal.py asserted that the rotate prompt, .data-table and the
    collision were still ahead of it - a deliberate guard on the previous
    round's scope. The work it guarded is done, so it inverts.

73 checks in test_grade_tables.py. The rendered ones: the five steps are five
DIFFERENT colours with enough separation between neighbours to read as an
order - with a control that fails on a deliberately flat scale, because
Outstanding Invoices once shipped two near-identical pale blues with a grey
between them and it encoded no ordering at all - the graded cell still prints
its figure, the sorted column is marked without a background, the tfoot is
base's, and at 390px the cards carry the tint and the labels.

financial_indicators.html 92,953 -> 91,003 bytes.
vacancy_management.html    53,100 -> 52,092 bytes.

STILL TO COME on these two pages: the last hand-rolled segmented control (the
Budget / Actuals .btn-group plus this page's other btn-outline-info buttons),
and the banding logic that has drifted between the two files.
'@ `
  -Checks "python test_grade_tables.py","python test_sticky_sweep.py","python test_ind_modal.py","python test_pl_drill.py","python test_alv_stat.py","python test_payment_days.py","python test_pl_indicators.py","python test_card_standard.py","python test_table_standard.py","python test_button_sweep.py"
