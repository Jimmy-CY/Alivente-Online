.\Push-PendingChanges.ps1 -Push `
  -Message "The phone card view was printing: screen and, five times, plus the actions it was hiding by accident" `
  -Body @'
REPORTED FROM A PRINT PREVIEW, AND NOT A FAULT OF THE ROUND THAT REVEALED IT.

base turns .alv-table into cards on a phone from a block written

    @media (max-width: 768px)

with no `screen`. On paper the viewport is the PAGE BOX: A4 portrait is 210mm,
about 190mm of content after default margins, which is ~718 CSS px at 96dpi.
Under 768. So the phone block fired on every printed page and every table came
out as a stack of cards, with data-label prefixes and no heading. Letter
portrait is the same story.

Measured, at 718px with print media emulated:

                        screen 1200          print 718
    thead               table-header-group   none
    tbody tr            table-row            block
    tbody td            table-cell           block
    td::before          none                 "Amount"

THIS IS SYSTEM-WIDE. It reaches every .alv-table - the nine list pages and
everything migrated since - and has been true since the table standard shipped.
It went unnoticed because the pages printed most often carry their own @media
print block, and because a page of cards is legible enough to look like a
choice rather than a bug. It surfaced now because the two Financials detail
tables are ones you would actually print.

THE FIX IS ONE WORD, FIVE TIMES: `screen and` on the five blocks in base that
are screen affordances - rows to cards, the two-up stat strip, the mobile
action bar, the jQuery-UI menu, and the filter button that drops its label.
None of them has any business on paper.

DELIBERATELY NOT TOUCHED: the <=991px block that swaps the sidebar for the top
nav. It fires on paper today and hides the sidebar, which is what a printed
page wants. Qualifying it would put the desktop sidebar layout on paper and
move every margin on every page - a change nobody asked for, to fix nothing.
The suite asserts it is still there, so a later tidy-up cannot take it out
without saying why.

THE CONSEQUENCE THAT SHIPS WITH IT. Until now the Actions column did not print
BY ACCIDENT: the phone block hid .desktop-action-cell, and base's print block
hid .mobile-action-bar, so neither survived. Qualify the media query and the
icon buttons start appearing on paper. So the print block gains
.desktop-action-cell, .alv-table .cell-actions and .row-actions by name.
Fixing the query alone would have traded one wrong output for a subtler one -
a row of small grey icons on paper reads as a printing artefact rather than as
a decision, and would have sat there for months.

20 checks in test_print_media.py, rendered at four combinations of width and
media. The two that matter:

  * THE FIX: at 718px with print media the table is a TABLE, the heading is a
    table-header-group so it repeats on every page, the totals band is a
    table-footer-group so it does too, no data-label prefixes print, and
    neither action bar appears.
  * THE CONTROL: the SAME 718px width must give CARDS on screen and a TABLE on
    paper. A 718px window is a narrow window and cards are right there; what
    was wrong was that PAPER counted as one. If both came out as tables the
    breakpoint would merely have moved, and every other check would still
    pass. A second control renders 390px on screen and requires the card view
    to still work, because a fix that killed it everywhere would also satisfy
    every "it is a table now" assertion.

SECTION 4b, FOUND BY THE PUSH GATE. test_action_standard.py locates the phone
half of the action bar by searching base for the literal
`@media (max-width: 768px)`, and six checks read that slice. After this round
the string is `screen and`, find() returns -1, and the slice is empty.

Note WHICH six failed: the text ones. Every RENDERED mobile check in that suite
passed - the primary still flexes, the More button still appears, Back still
keeps its 44px target - because those render at 375px on SCREEN, where the
block still applies. Behaviour untouched, expectation stale.

That suite already carried this lesson in its own comment: an earlier version
anchored on a marker that lived only inside a comment, found nothing, and ran
every mobile check against an empty string. The bool(MOBILE) guard added then
is what fired first here, exactly as intended.

The locator moves to the EXACT new spelling rather than tolerating both, since
the bare form must not come back - and the suite gains a check that the block
is screen-only, so it becomes a second place guarding this fix. 74 -> 75.

The patcher now guards PER FILE rather than per round: base was already patched
when the gate found this, and a single early return would have left the round
unable to finish itself.

Left behind: Show-PrintLeak.py, read-only. A page-local `@media (max-width: N)`
block leaks the same way, and the scanner reports which templates carry one,
how many are already guarded, and whether the template has ever been thought
about for paper at all. That round should be sized from its output rather than
from a guess.
'@ `
  -Checks "python test_print_media.py","python test_action_standard.py","python test_grade_tables.py","python test_ind_modal.py","python test_pl_drill.py","python test_alv_stat.py","python test_payment_days.py","python test_table_standard.py","python test_card_standard.py","python test_sticky_sweep.py","python test_button_sweep.py"
