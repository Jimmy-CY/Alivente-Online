.\Push-PendingChanges.ps1 -Push `
  -Message "P&L drill-downs: the two identical fragments onto the standard, and a wrapper that scrolls" `
  -Body @'
FIRST THING TO KNOW: THE MODAL DOES NOT OWN ITS TABLE. Clicking a Revenue or
Expense figure on the P&L fires an AJAX request at ANOTHER page and scrapes a
table out of the reply -

    var $table = $temp.find('table.table').first();
    $('#revenueDetailsContent').html($('<div class="table-responsive">').append($table));

- keeping the TABLE ELEMENT and discarding everything around it: headings,
wrapper divs, an empty-state alert sitting outside the table. That decides what
this round may change. Whatever the modal must show has to be INSIDE the table,
and the wrapper has to be built in the page doing the scraping.

TWO OF THE THREE FRAGMENTS WERE THE SAME FILE. revenue_details.html and
budget_expense_details.html differed in the loop variable and one sentence of
empty-state prose. Nothing else. Both carried Bootstrap `table table-sm
table-bordered` with `thead-light`, a totals row in the TBODY with
`style="background-color: #f8f9fa"` inline, and `text-right` on every money
cell - which the page then repeated as a :nth-child(2) rule, so three rules
aligned one column.

They are now `table alv-table` (the pairing act_expense.html already uses, and
the one the scraper's own `table.table` selector needs), `.num` on the money
column, a real <tfoot> so the total repeats on every printed page, and base's
.alv-empty instead of an alert. Both keep data-label attributes, so the modal
gets base's phone card view for free.

THE WRAPPER IS THE INTERESTING PART. Deliberately NOT .table-container - that
is `overflow: clip` by design, and this one has to scroll, because a month of
revenue is longer than a modal. The 60vh the page already had keeps its
behaviour under a name of its own, .pl-drill, instead of leaning on Bootstrap's
.table-responsive.

And because it scrolls, base's sticky .alv-table heading finally has a scroll
container to stick TO: Property / Amount now holds its place through a long
list. The sticky sweep spent a round on containers that scroll when they should
not; this is the same mechanism, the right way round, and the suite proves it
by scrolling the element 400px and requiring that the ROWS moved while the
HEADING did not - "the heading is at the top" being true for free if the scroll
never happened. A control renders the same table inside .table-container and
requires that it does NOT scroll.

63 checks in test_pl_drill.py. Beyond the scroll: the two fragments are
compared as SHAPES with the loop variable and the empty sentence removed, so
they cannot quietly stop being copies, and that comparison has its own control
proving it can tell two shapes apart. Also asserted: the tfoot is base's rather
than a tbody row in disguise (different background, 2px top border), .num
aligns head, body and foot together, the P&L's OWN grid keeps its wrapper
because this round is the modals only, and the empty state sits inside the
table where the scraper can reach it.

CAUGHT BY THE PATCHER'S OWN SELF-CHECK, WORTH RECORDING: the first draft
documented the fragments with a five-line {# #} Django comment. Django comments
do not span lines, so it would have printed four lines of prose above the
table. The balance check fired and nothing was written. Both files now use an
HTML comment, which the scraper discards anyway.

ALSO FOUND, DELIBERATELY NOT TOUCHED: total_expense_details.html renders
through total_expense_details_view at a live URL that no template in the system
links to - 120 lines and a view, unreachable. Removing a URL is a different
class of change from restyling a table, so it goes on the list.

NEXT TWO ROUNDS, agreed: the Financial Indicators / Vacancy Management modal
(one modal duplicated across two files, stating each verdict five times -
legend, row tint, mobile row tint, badge, summary tile), then Vacancy's
Detailed Property Data table, the .table-container name collision those two
pages carry, and the last hand-rolled segmented control.
'@ `
  -Checks "python test_pl_drill.py","python test_pl_indicators.py","python test_pl_invoice.py","python test_pl_historical.py","python test_help_pl.py","python test_act_expenses.py","python test_alv_stat.py","python test_payment_days.py","python test_button_sweep.py"
