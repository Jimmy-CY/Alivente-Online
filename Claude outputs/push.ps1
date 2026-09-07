.\Push-PendingChanges.ps1 -Push `
  -Message "One way to say 'required', in a colour we own - 112 sites, seven spellings, one rule" `
  -Body @'
Opening move of the input-screen programme (section 4), and sized by
Show-RequiredMarkers.py, which is committed beside the patcher.

SEVEN SPELLINGS, THREE OUTCOMES, AND NOT ONE OF THEM OURS.

An asterisk inside a <label> is how this system says a field is required. It
did it 112 times across 33 templates, in seven shapes:

    text-danger                   58   Bootstrap's own class
    required-mark                 32   a page rule, hardcoding #dc3545
    (inline) color: red            9   an inline style
    required                       9   a page rule, hardcoding #dc3545
    req                            2   a page rule, hardcoding #dc3545
    (bare asterisk, no element)    1   nothing at all
    required-marker text-danger    1   both at once

Rendered, those seven produced THREE outcomes:

    #dc3545   102 sites   Bootstrap's red, reached by four spellings - three
                          of which hardcoded the value in EIGHTEEN separate
                          page rules
    red         9 sites   #FF0000, visibly louder than the other 102
    inherit     1 site    body text; the signal was a character, not a colour

base's own --alv-bad #b3261e appeared NOWHERE among them. The system said
"required" in a colour it did not own, and if Bootstrap ever left, 102
asterisks would have turned black.

base gains one rule - `.alv-req { color: var(--alv-bad); margin-left: 2px;
font-weight: 600 }` - every site becomes `<span class="alv-req">*</span>`,
and the eighteen page rules go, taking eighteen hand-written #dc3545 with
them. Measured before and after: three computed colours become one, and it is
base's.

THE ROUND CORRUPTED THREE FILES BEFORE IT SHIPPED, and how it was caught is
the part worth recording.

The bare-asterisk rule matched any `*` in a label that was not already in a
span. Three of the four "bare markers" it found were not markers at all: they
were the `*` inside `accept="image/*"` on a file input nested in the label.
The patcher wrapped one, producing

    accept="image/<span class="alv-req">*</span>"

which breaks the attribute AND the file picker's filter, on my_profile,
edit_asset and property_assets.

IT PASSED EVERY GUARD. The patcher cross-checks its per-file count against
the SCANNER's before writing - and the scanner had the same bug, so the two
agreed perfectly. TWO IMPLEMENTATIONS OF ONE RULE DO NOT DRIFT, BUT ONE WRONG
RULE IMPLEMENTED TWICE IS STILL WRONG: a cross-check between tools that share
a definition tests agreement, not correctness. It was caught by reading what
those four labels actually said, which is the only thing that could have
caught it.

Both tools blank tags before looking now, so no attribute value is reachable,
and the corrected count is 112 across 33 - the first scan said 115 across 34.
The suite does NOT ask the scanner anything: it asks the files, and requires
that no <span> appears inside ANY attribute value anywhere, with each
accept="..." byte-identical to its backup. Putting the defect back fails it.

34 checks, three negative controls, all three failing as designed: restore
the attribute defect, pin base to Bootstrap's #dc3545 instead of --alv-bad,
or revert one page to its old spelling.

AND A NEGATIVE CONTROL THAT SILENTLY DID NOTHING. The base-pinning control
searched for `color: var(--alv-bad);\n        margin-left` - with a bare \n,
against a CRLF file. It never matched, the injection never happened, and the
control reported a clean pass on an untouched tree. A control that cannot
fail is worse than no control, and this one could not even be applied. Fixed
by reading the file's own line ending first. Same trap the patchers have
handled since August; the controls had not caught up.

WHAT IS NOT TOUCHED, DELIBERATELY. `text-danger` stays wherever it is not a
required marker - it is a general Bootstrap utility this system uses for
error text and warnings, and twelve files still carry it. Only asterisk spans
inside labels moved. The recipe / meal-plan side is excluded as it is from
every sweep here.

STILL OPEN, AND FOUND BY THE SAME SCAN: resolved_issues_report.html writes
`<span style="color: red;">Resolution: N days</span>` on a RESOLVED issue -
inline, so no token reaches it, and a keyword, so no hex audit sees it. Round
D fixed this exact figure on the Friday report; that is the third screen. Its
own small round.

SECTION 4b, ELEVENTH OCCURRENCE, and the plain kind. test_sticky_sweep.py
asserts per page that the sticky round changed the STYLESHEET and left the
MARKUP byte-for-byte alone, measured live against .bak_sticky. True of that
round, and true until a later round legitimately edits one of its six pages.
This one does: passport_management.html carries six required markers.

Checked rather than assumed which of the six were affected - only that one;
the other five have no .bak_alvreq. The suite already has the mechanism, a
LATER map pointing a page's historical comparison at the snapshot the later
round leaves, and it gains one line as the fifth entry. The claim does not
change - still "the sweep did not touch the markup" - it is just measured
between two snapshots rather than against a file somebody else now owns. The
patcher asserts that snapshot exists before pointing at it, so it cannot
trade a false failure for a different one.

base.html plus 33 templates, and test_sticky_sweep.py.
112 sites, 18 page rules retired.
'@ `
  -Checks "python test_required_marker.py","python test_sticky_sweep.py","python test_issues_table.py","python test_map_tiles.py","python test_ia_drill.py","python test_ia_tiles.py","python test_ia_palette.py","python test_print_leaks.py","python test_fsr_palette.py","python test_notify_btns.py","python test_comment_tint.py","python test_fi_seg.py","python test_button_sweep.py","python test_action_standard.py","python test_table_standard.py","python test_card_standard.py","python test_detail_property.py"
