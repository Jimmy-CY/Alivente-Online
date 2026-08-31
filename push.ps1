.\Push-PendingChanges.ps1 -Push `
  -Message "One stat tile in base, and a verdict that colours the figure rather than the box" `
  -Body @'
Four screens had each built the same tile: .pd-stat on Tenant Payment
Behaviour (borrowing .alv-card for a surface), .ia-kpi in the Issues Analysis
modal, and .summary-stat twice over in Financial Indicators and Vacancy
Management - near enough the same bytes in two files. Fifteen tiles, four
implementations. When Payment Behaviour shipped on 29 Aug its own CSS said why
it stopped short: "one page is not enough to invent one". Four is.

base gains .alv-stats (the grid) and .alv-stat / -value / -label, plus the
three verdicts .alv-stat-good / -attn / -bad, the two-up phone grid, and the
print treatment the tile used to borrow from .alv-card.

THE DECISION THIS ROUND MAKES: a verdict colours the FIGURE, not the tile.
Financial Indicators and Vacancy Management wash the whole box green, amber or
red; Payment Behaviour washed it amber. A tile reading "3 / NEEDS IMPROVEMENT"
already says which verdict it is, in words, directly under the figure - so the
wash spends the loudest signal on the page repeating it. The same objection the
tables spent nine rounds settling. The verdict colours come from base's own
--alv-good / --alv-warn / --alv-bad, so a tile and the pill in the table below
it cannot drift apart.

The tile also brings its OWN surface. Stacking .alv-card underneath one to get
a border is what made .pd-stat need a paragraph of comment explaining what it
was subtracting back out.

SCOPE: ONE screen migrates - Tenant Payment Behaviour, the smallest and the one
already known good. The Issues Analysis strip and the two Financials modals are
the next two rounds, which open those files for their tables anyway; migrating
their tiles now would mean opening them twice. No modal density (.alv-stats-sm)
ships either: nothing this round renders is in a dialog, and CSS nothing uses
is CSS nobody has looked at.

SECTION 4b. test_payment_days.py hardcoded .pd-summary, .pd-stat and
.pd-stat-warn in its Playwright fixture and asserted the tile IS a card. That
expectation is superseded, not wrong, so it MOVES - polarity reversed - and now
reads base's rules rather than the page's. Two of its checks would otherwise
have gone on passing while reading a selector that exists nowhere, which is a
control that cannot fail. That suite goes 48 -> 53 checks and gains the
rendered assertion that a verdict does not wash the tile.

67 checks in test_alv_stat.py, of which the ones that matter are rendered in a
real browser: all three verdicts leave the tile's background identical to a
plain tile, and each figure resolves to EXACTLY the token colour rather than a
lookalike. Section 3 carries its own control - a tile with an inline red
background is rendered beside the real ones and the probe must see it, because
every other check in that section asserts an ABSENCE of colour and an absence
is what a blind probe reports for free. Also asserted: the three verdicts are
three genuinely different colours (Outstanding Invoices once shipped a "scale"
of two near-identical pale blues with a grey between them), the fallback
property --alv-stats-cols really drives a five-up strip, four tiles hold equal
width so a long label cannot starve its neighbours, and every token the
component references is DEFINED in base rather than merely named.
'@ `
  -Checks "python test_alv_stat.py","python test_payment_days.py","python test_card_standard.py","python test_detail_property.py","python test_table_standard.py","python test_ageing_scale.py","python test_oi_migration.py","python test_button_sweep.py"
