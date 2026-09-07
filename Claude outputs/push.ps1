.\Push-PendingChanges.ps1 -Push `
  -Message "The main Issues list joins the table standard - and an anchor comes out of a button" `
  -Body @'
First of the 26-page table-standard queue written down in
claude/print_leak_round.md.

THIRTY-NINE PAGE RULES BEHIND ONE TABLE, AND THIRTY-TWO OF THEM WERE THINGS
BASE ALREADY DOES.

    .status-badge + .status-success/-warning/-danger    4  -> .alv-pill*
    .action-btn + hover + a + hover a                   4  -> .status-btn
    .delete-issue-btn + hover + focus                   3  -> .icon-delete
    21 rules rebuilding base's phone cards by hand     21  -> .alv-table
    (three of those were a third empty state            3  -> .alv-empty)
    .sortable + .sort-icon family                       7  STAYS

AN ANCHOR WAS NESTED INSIDE A BUTTON, and that is the defect rather than the
tidy-up. The Comments control was

    <button class="btn btn-light action-btn"><a href="...">Comments</a></button>

which is not valid HTML - a nested interactive element, which every browser
resolves however it likes. It is one <a> now, wearing base's .status-btn, with
the word kept: Comments is the main way into an issue on this screen, and an
icon alone would hide the primary action to save a few pixels. The suite
asserts this against the PARSED DOM rather than the source, because the whole
point is that the browser rewrites it.

THE STATUS MAP GAINED A BRANCH THAT IS NOT AN ALARM. Resolved -> good,
Unresolved -> attention, and anything else -> NEUTRAL. It used to be
status-danger: a status that is neither of the two known ones is
UNRECOGNISED, and unrecognised is not a failure. Same map the Comments Report
round settled on 2 Sep.

DELETE STOPS BEING A FILLED RED SQUARE. base's quiet .icon-action-btn
.icon-delete, the same control Properties, Tenants and Customers already use.
Measured: filled rgb(220,53,69) before, an outline with danger ink after.

AND THE ROUND ALMOST LIFTED SOMETHING INTO BASE THAT SHOULD NOT GO THERE.
`.sortable` looked like a clear base candidate - FOUR templates carry a
sortable header, which is well past the bar that finally justified .alv-seg.
Measured, they are not one thing:

    fsr                     .sortable         .sort-asc/.sort-desc,
                            icon inline after the label, 7 rules
    passport_management     .sortable-header  no icon, no state, 2 rules
    financial_indicators    .sortable-header  .sorted-asc/.sorted-desc,
                            icon absolutely positioned right, 11 rules
    vacancy_management      .sortable-header  same family, 5 rules

Two class names, two state vocabularies, two icon placements - and the
deciding fact: `.sorted-asc` and `.sorted-desc` appear NOWHERE in
financial_indicators or vacancy_management, not in markup and not in script,
so those state rules are dead; and passport_management has a cursor and a
hover but no sort indicator at all. The system contains exactly ONE working,
stateful sortable header and it is this one. It stays page-local and takes
tokens. Four askers turned out to be one. The other three carry more dead
rules for a later sweep.

INLINE COLUMN WIDTHS STAY, correcting something said while the round was
being agreed. The proposal had the six `style="width: ..."` going "so the
table can size itself". Measured against a page that has already migrated -
customer_list.html - widths on <th> are house-consistent; it carries five.
They stay, with the two action columns merged into one.

113 checks, and the structural one is rendered at TWO WIDTHS. The page used
to ship one set of cells and 21 rules that rebuilt them as cards; it ships
two sets now and base decides which appears. Measured:

    1280px   desktop cell = table-cell    phone bar = none
     420px   desktop cell = none          phone bar = grid

Exactly one at each. That check exists because THIS ROUND'S OWN BEFORE/AFTER
PICTURE GOT IT WRONG: a fixture forced .desktop-action-cell visible for the
desktop shot and the override leaked into the phone shot, which then showed
both rows. The markup was right and the picture was not.

THREE CHECK BUGS AND TWO BLIND SPOTS, ALL FOUND BEFORE SHIPPING, AND THE
BLIND SPOTS ARE THE ONES WORTH RECORDING.

  A SUBSTRING TEST CATCHES EVERY SUPERSTRING. The patcher asked
  `'action-btn' not in markup` and failed on a correct file: icon-action-btn
  and mobile-action-btn both contain it, and desktop-action-cell contains
  action-cell. It splits class attributes into TOKENS now, with a control
  that fails if the tokeniser ever returns nothing.

  A CLAIM CARRIED OVER FROM THE WRONG FILE. The suite asserted this page's
  @media was still bare, which was true of the two round-D files but not of
  fsr.html - it WAS in the print round's 34 and was guarded on 2 Sep. The
  check now asserts the guard is still there, plus that no bare one crept
  back, which is the claim worth keeping.

  TWO KINDS OF HOOK TREATED AS ONE. .sort-asc and .sort-desc are written BY
  the script at runtime and never appear in the template, so demanding them
  in the markup failed on a correct file. What they need is a RULE.

  BLIND SPOT ONE: the rendered section probes a SYNTHETIC row, so it tests
  BASE, not this page. A negative control proved it - deleting the phone
  action bar from the template left the suite at 104/104. The page's own
  markup is now asserted separately, and that control fails.

  BLIND SPOT TWO: `'.sortable.sort-asc' in css` passed on a file whose
  sort-asc COLOUR rule had been broken, because the two states share a
  grouped colour rule and have separate glyph rules - so the string survived
  in the sibling. A text check cannot tell a partial regression from a whole
  one. The indicator is RENDERED now, in three states, and read against
  base's own --alv-accent. That control fails too.

CLASS NAMES THE SCRIPT NEEDS ARE KEPT while their RULES are deleted, the same
move the Notify round made. The sorter reads .sortable and its data-sort,
finds rows by .issue-row and their data-property / data-date / data-status,
and the delete flow finds .delete-issue-btn by six data attributes. Every one
survives and is asserted; losing one leaves a table that renders correctly
and does nothing.

NOT THIS ROUND. resolved_issues_report.html carries `<span style="color:
red;">Resolution: N days</span>` - an INLINE style spelling the keyword
`red`, on a resolved issue, which no token can reach and which no hex-based
colour audit can see. A scan found ten such sites across six templates and
zero keyword colours inside any <style> block, so it is purely an inline
pattern. Its own small round, sized the way the print leaks were.

fsr.html   104,096 -> 102,550 bytes.
'@ `
  -Checks "python test_issues_table.py","python test_ia_drill.py","python test_ia_tiles.py","python test_ia_palette.py","python test_print_leaks.py","python test_fsr_palette.py","python test_notify_btns.py","python test_comment_tint.py","python test_comments_report.py","python test_fi_seg.py","python test_button_sweep.py","python test_sticky_sweep.py","python test_filter_toggle.py","python test_action_standard.py","python test_table_standard.py","python test_card_standard.py","python test_print_media.py","python test_pl_drill.py","python test_alv_stat.py"
