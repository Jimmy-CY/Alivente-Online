.\Push-PendingChanges.ps1 -Push `
  -Message "The Issues Analysis drill-down joins the table standard - and the Issues module is finished" `
  -Body @'
C3. The fifth and last screen of the Issues module.

THE FIFTH HAND-ROLLED TABLE, AND MOSTLY A DELETION.

`table.ia-tbl` was TWELVE rules - seven for the desktop table and five more
rebuilding it as phone cards: thead hidden, cells set to display:block, a
data-label prefix injected by ::before. With .ia-empty-row that is THIRTEEN
deleted, of which TWO come back rescoped, so ELEVEN are net gone. Every one
of the eleven is something base's .alv-table already does, and does the same
way.

THE MARKUP WAS ALREADY SHAPED FOR IT, which is why this was a rename rather
than a rebuild. drillRows() was ALREADY writing `data-label` on every cell
and `class="num"` on the figures - base's own conventions, arrived at
independently by whoever wrote the drill-down.

THREE THINGS MEASURED RATHER THAN ARGUED, because all three would have gone
the other way on reasoning alone.

  THE STICKY HEADING STILL WORKS, and this was the round's open question.
  base drives its heading shadow from an IntersectionObserver that runs ONCE
  at page load, over `.alv-table thead`, with the VIEWPORT as its root. This
  table is built by drillRows() long after load and scrolls inside the
  dialog, so that observer can never see it. But the STICKINESS is plain CSS
  - position:sticky on .alv-table thead th - and it pins against the nearest
  scrolling ancestor, which is .ia-drill-body. Rendered and measured: the
  heading's top sits exactly on the drill body's top after scrolling, in both
  the old table and the new. The round did not introduce stickiness; it kept
  it.

  ONLY THE SHADOW IS MISSING, AND IT IS NOT WORTH BUYING. base's .is-stuck
  cue adds a soft shadow under the pinned heading. Rendered on and off, side
  by side, the difference is one faint shadow - and the dialog already has a
  hard edge, a title bar and a drop shadow of its own, so the hint has almost
  nothing left to do. Left out DELIBERATELY, asserted as absent, and written
  into the file so it is not later mistaken for base's table misbehaving
  inside a dialog.

  THE .table-container WRAPPER IS OMITTED. It exists to give a page card its
  background, radius and shadow, and to be the hook .is-stuck toggles. The
  dialog supplies the first and clips the second, and the third is the cue we
  just declined. Rendered both ways: identical, and sticky pins in both. The
  simpler markup wins on evidence.

AND ONE DEFECT THE FIRST RENDER CAUGHT THAT WOULD HAVE SHIPPED SILENTLY.
`table.ia-tbl a.ia-link` was anchored to the class this round renames. Rename
the table and that rule stops matching, and every issue link in the
drill-down drops back to Bootstrap blue - which is exactly what the first
render showed. A rename is not a rename while another selector is anchored to
the old name. The rule is rescoped to `.ia-drill-body .alv-table a.ia-link`,
and the suite pins it as a COMPUTED COLOUR against base's own
--alv-accent-ink, with a control that reproduces the break: render the new
table against the old stylesheet and the link must come out blue.

THE OVERLAY STAYS HAND-ROLLED, and that is a decision. base has NO modal
component - the system uses Bootstrap modals, and this is a dialog INSIDE one
at z-index 2000, which Bootstrap does not do. One asker; base has twice
declined to build on one, most recently on 2 Sep when a compact stat density
was proposed, approved, built and then dropped after measuring. C1 already
tokenised these rules, so the overlay spells no colour by hand - only its
shape is still local, and the suite asserts base still has no modal component
so that "one asker" stays checkable rather than remembered.

DENSITY: BASE'S TABLE AS IT IS. base's rows are 71px against ia-tbl's 59px,
so the dialog shows three rows at a time instead of four. Considered, and
taken: the drill-down is a list you scan and scroll, not a page you read. A
compact variant in base would be its SECOND asker - tenant_payment_days
hand-rolls `.pd-table-compact tbody td { padding: 8px 12px }` against base's
11px 12px - and section 1.F stays open for a round with more askers than two.

C1'S NOTE WAS KEPT POINTING SOMEWHERE REAL. It records that the palette was
declared four times and that copy 3 lived in "the .ia-drill and table.ia-tbl
rules further down". Accurate history, but "further down" is a pointer in the
present tense, and after this round it points at nothing. Amended the way
base's .alv-seg note was on 2 Sep: the account is left standing and one line
says what has happened to it since. A note that has been kept up is the only
kind worth writing.

SECTION 4b, NINTH AND TENTH OCCURRENCES.

  THE NINTH IS THE BEST KIND, and the FOURTH guard this project has written
  that NAMES the round which would invalidate it. test_ia_tiles.py section 5
  said, in as many words:

      check('the .ia-drill overlay and its table are untouched - C3',
            'table.ia-tbl{' in FC and '.ia-drill{' in FC)

  That was C2 asserting it stayed in its lane. The claim was right and the
  work it pointed at has now happened. Following the refinement the EIGHTH
  occurrence forced, it is split by what each half is a claim ABOUT: the
  OVERLAY is still hand-rolled and still local, a claim about today, so that
  half stays on the live file; the TABLE is history, so it moves onto
  .bak_iadrill and gains a forward half saying C3 DID the work - because a
  guard that only ever loosens asserts nothing.

  THE TENTH IS THE PLAIN KIND. test_print_leaks.py asserts per file that the
  print round changed "ONLY the guard", measured live against .bak_leak.
  fsr.html is one of its 34 targets and this round edits it. Its LATER map
  already exists for exactly this and gains one line.

58 checks in test_ia_drill.py, and the ones carrying the round are rendered:
the dialog is built the way drillRows() builds it, dropped into a real
.ia-drill-body, scrolled, and measured - with every claim taken again from
.bak_iadrill, where the old table must give the old answer. All proved by
breaking them: un-rescope the link rule, take position:sticky out of base, or
rename a script hook, and the suite fails.

THREE COUNTING SLIPS THIS WEEK, ALL THE SAME MISTAKE, AND THIS ROUND MADE THE
THIRD. Round D printed file sizes with len() of a str - characters counted as
bytes, every figure eight short. Round D's own suite sampled ages [0,12,64,257]
and demanded four inks - two samples from one band, counted as four bands.
And this round's first draft counted the STRING `table.ia-tbl` (16
occurrences: one inside a comment, four inside a single grouped selector) and
called the answer "thirteen rules". The number is easy; the UNIT is the part
worth checking, and it is now checked - the suite counts rule OPENINGS on
comment-stripped text and states the arithmetic separately.

Also caught before shipping: the patcher's IDEMPOTENCE marker read prose. It
said `'ia-tbl' not in f`, and the note this round adds quotes that selector
while explaining the rescope - so the marker never fired and a second run
walked into its own anchor. It reads comment-stripped code now, plus a
one-line phrase from the note. And the marker for test_print_leaks.py matched
`'fsr.html'` in that suite's TARGETS list, a hundred lines above the map this
round edits - a marker that reads the whole file catches the data as readily
as the code.

NOT THIS ROUND. fsr.html's OTHER table - the main Issues list - is still
`table table-bordered table-striped` with 28 page rules behind it, about
twenty of them rebuilding base's phone cards by hand, plus hand-rolled action
cells, a third empty state, and a Comments control that nests an anchor
inside a button. It is the first of the 26-page table-standard queue written
down in claude/print_leak_round.md, and it is its own round.

fsr.html             102,586 -> 104,096 bytes.
test_ia_tiles.py      21,995 ->  23,199 bytes.
test_print_leaks.py   13,030 ->  13,121 bytes.
'@ `
  -Checks "python test_ia_drill.py","python test_ia_tiles.py","python test_ia_palette.py","python test_print_leaks.py","python test_fsr_palette.py","python test_notify_btns.py","python test_comment_tint.py","python test_comments_report.py","python test_fi_seg.py","python test_button_sweep.py","python test_sticky_sweep.py","python test_filter_toggle.py","python test_action_standard.py","python test_table_standard.py","python test_card_standard.py","python test_print_media.py","python test_pl_drill.py","python test_alv_stat.py","python test_grade_tables.py","python test_ind_modal.py"
