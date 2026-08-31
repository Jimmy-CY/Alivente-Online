.\Push-PendingChanges.ps1 -Push `
  -Message "The indicator modal: one markup in both files, and a verdict said once instead of five times" `
  -Body @'
Financial Indicators and Vacancy Management carry THE SAME MODAL - same ids
(propertyDetailsModal, modalPropertyTable, excellentCount / goodCount /
poorCount), same five columns, same legend, same three summary tiles. Two
copies kept in step by hand, and they had already drifted.

THE VERDICT WAS STATED FIVE TIMES PER ROW:

    1. a swatch in the legend above the table
    2. a row tint     .performance-excellent  rgba(40,167,69,.1)  !important
    3. the SAME tint again in the phone block, plus a 4px left border
    4. the badge      .performance-badge.excellent  solid #28a745
    5. the summary tile  .summary-stat.excellent  washed green

Four of the five are colour. The badge stays as .alv-pill-good / -attn / -bad;
the tiles stay as .alv-stat, the component built for exactly this on 30 Aug;
the tints and the legend go. Same argument the stat tile settled - a row that
says NEEDS IMPROVEMENT in words does not also need to be red.

THE TWO COPIES HAD DIVERGED ON MOBILE, in the most expensive way: each solved
the same problem differently and neither used base.

  * financial_indicators.html converted the table to cards in ~90 lines of CSS
    under #modalPropertyTable - hiding the head, blocking the cells, styling
    the name as a card title, positioning the badge, injecting data-labels.
  * vacancy_management.html built a SECOND DOM - #modalPropertyCards, filled in
    the same loop as the rows, with .mpc-header / .mpc-name / .mpc-rank /
    .mpc-row / .mpc-label / .mpc-value / .mpc-badge-row - and toggled the two
    with display:none.

base's .alv-table has done this for every list page since the table standard
shipped. Both are gone. The modal markup in the two files is now byte-identical
and the suite asserts exactly that, with a control proving the comparison can
tell two strings apart.

THE RANK COLUMN STAYS, DESKTOP ONLY, as it already behaved. That needs one
deliberate rule and it is written down: base promotes the FIRST cell of a card
to its title, and here the first cell is the rank, which is hidden - so the
name cell is told to be the title. The suite renders that at 390px rather than
trusting it.

THE VALUE COLUMN LOSES ITS INLINE COLOUR. Every row carried
`<strong style="color: ${indicator.color}">`, so an entire column was painted
one colour - which distinguishes nothing, and was the accent arriving as a
literal through JavaScript. Scoped: indicator.color still paints the indicator
cards and the single Portfolio Average figure, and neither of those is the
fault.

THE BAND-TO-PILL MAP IS NAMED, NOT INTERPOLATED. PERF_PILL sits beside the
banding code in each file, same shape as BAND_PILL in the tenants view, and the
suite reads the JS for every value performanceClass can be ASSIGNED and
requires each to have an entry - so a fourth band cannot appear with no colour.

SECTION 4b. test_sticky_sweep.py left these two pages alone and said why: the
.table-container name collision was harmless BECAUSE neither page used
.alv-table at all. This round makes the modal table .alv-table, so that premise
stops holding. The expectation is superseded, not wrong, so it MOVES to what
actually keeps the collision harmless - .alv-table never sits inside the
.table-container these pages redefine, because the modal has .ind-drill. Three
checks where there was one.

That moved check produced the eighteenth instance of "a check that reads TEXT
catches PROSE", this time in a comment this round wrote: the new comment quotes
the expectation it superseded, so the patcher's guard against the old line
found it in the explanation of why it is gone. Guard now strips Python comment
lines, and has a control requiring the explanation to still be there.

87 checks in test_ind_modal.py, of which the ones that matter are rendered:
three verdicts produce ONE row background (with a control row carrying an
inline red wash, so the probe is known to be able to see one), the three pill
colours are three different colours, the tile figures ARE --alv-good /
--alv-warn / --alv-bad rather than lookalikes, and at 390px the rank is hidden
while the property name is the card title.

WHAT THIS ROUND DOES NOT DO. It does not touch the BANDING LOGIC, which has
already drifted between the two files - financial_indicators.html special-cases
expensesToRevenue, avgDaysToFill and vacancyCost where vacancy_management.html
has one generic branch. That is business logic and belongs to whoever owns the
thresholds; it goes on the list. Nor does it touch Vacancy's Detailed Property
Data table, its rotate-to-landscape prompt, the .table-container name both
pages redefine, or the last hand-rolled segmented control. That is the next
round, and the suite asserts all four are still there.

financial_indicators.html 96,563 -> 92,953 bytes.
vacancy_management.html    56,437 -> 53,100 bytes.
'@ `
  -Checks "python test_ind_modal.py","python test_sticky_sweep.py","python test_pl_indicators.py","python test_pl_drill.py","python test_alv_stat.py","python test_payment_days.py","python test_table_standard.py","python test_button_sweep.py"
