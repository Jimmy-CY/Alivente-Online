# -*- coding: utf-8 -*-
"""apply_modal_heads2.py - round MH-2, 13 Oct 2026.

THE MODAL HEADERS, IN BOTH ROOTS - AND A LESSON ABOUT MEASURING.

`test_modal_heads` passes 13/0 and says so in its own words:

    EVERY modal header in the system wears the class - the single one
    that does not is the Recipe View close strip, and it is recorded

That is true of ONE ROOT. Counted across both:

    pages/templates      88 wear the class,  4 do not
    crs/templates/crs     3 wear the class,  5 do not

The master list calls this item "one close strip on one page" and
recommends it on the strength of that size. It is nine elements across
six pages, in two roots.


WHAT THE NINE ARE
-----------------
FOUR ARE THE ROUND, and they are identical to each other - delete
confirmations still in Bootstrap dialect on crs/country_list,
crs/fi_list, crs/submission_detail and crs/submission_list:

    <div class="modal-header bg-danger text-white">
      <h5 class="modal-title"><i class="fas fa-exclamation-triangle"></i>

Base defines `.alv-modal-head--danger` and SIXTEEN pages in the first
root already write `class="modal-header alv-modal-head
alv-modal-head--danger"`. One shape, sixteen times. This is a migration
with sixteen precedents, not a decision.

ONE IS THE INSTRUMENT INVENTING A FINDING. crs/submission_detail's
`xml-modal-header` matched only because the class NAME CONTAINS the
string `modal-header`. It is not a `.modal-header` at all - it is the
XML viewer's own chrome, with its own close button, and it is already
fully on house tokens.

    SECOND TIME, SAME ELEMENT FAMILY. E-10's drift tool reported twelve
    buttons and one of them was invented by substring-matching
    `xml-modal-footer`. The header twin of that mistake was sitting
    beside it and nobody looked. THIRD TIME this week counting DB-5's
    `.form-card` / `.form-card label`.

THREE ARE A KNOWN BLIND SPOT, NEWLY SHOWN TO BE WIDER. home.html twice
and notifications.html once build their header inside a <script>, in a
string. E11 logs TWENTY BUTTONS built that way and prices none of them;
nobody had logged that the same blind spot covers modal headers.
Demetri's decision, 13 Oct: log them beside E11 and price the whole
script-built set in one go. They are not touched here.

ONE IS THE RECORDED LEAVE - the Recipe View close strip, which renders
in an iframe. Already decided, still correct.


AND THE OTHER HALF: ELEVEN LOCAL RULES, AND FOUR WRONG ANSWERS
---------------------------------------------------------------
Eleven rules across ten pages set a background on a `.modal-header`.
Base writes `.alv-modal-head { background: ... !important }`, so the
question is which of them still paint anything.

I answered it four times and was wrong three times.

  1. Compared backgroundImage and backgroundColor.    ALL ELEVEN DEAD.
  2. Added padding, border-radius, border-bottom,
     display, align-items, justify-content.           THREE ARE LIVE.
  3. Added gap and flex-shrink.                       TWO MORE ARE.
  4. Enumerated the WHOLE computed style.             suppliers LIVE -
                                                      with no differing
                                                      property at all.

A RULE PROVED DEAD ON A SUBSET OF ITS DECLARATIONS IS NOT A RULE PROVED
DEAD, and every list I write is a subset of something. The fourth
version iterates getComputedStyle itself, so there is nothing left to
have forgotten.

The fourth version was wrong too, in a new way: 518 properties each
side, the two SETS identical, and the joined strings different.
REMOVING A RULE CHANGES THE ORDER THE BROWSER WALKS ITS OWN PROPERTY
LIST. An unordered comparison of an ordered dump is a false-positive
generator. Sorted, suppliers is dead.

WHAT THE SETTLED MEASUREMENT SAYS:

  SIX rules are dead in every declaration they carry, on six pages.
  They go.

  FIVE rules carry exactly one or two live declarations, on four pages.
  Only the dead declarations go; the rule stays with what it really
  does.

      comments_report                 keeps gap: 12px
      finance/cashflow_forecast       keeps border-radius: 8px 8px 0 0
      help_page .manual-modal         keeps border-radius: 4px 4px 0 0
      help_page .manual-preview-modal keeps that and flex-shrink: 0
      projects/projects_detail        keeps border-radius: 8px 8px 0 0

NOTHING ON SCREEN MOVES for any of the eleven, and this round proves it
by rendering rather than by arguing from specificity.

Worth recording and NOT fixed here: those five survivors show the modal
header's top corners are 8px on two pages, 4px on one and Bootstrap's
4.8px everywhere else. Base owns the header; it does not own its
radius. That is a real question and it is not this round's.


THE TWO SMALL ONES, RE-MEASURED
--------------------------------
THE FSR ITEM IS ONE LINE, NOT FIVE. The master says "a 1900-01-01
hidden input - fsr.html x4, fsr_add.html x1". Four of the five are
JAVASCRIPT SORT FALLBACKS - `a.dataset.date || '1900-01-01'`, in two
comparators, so a row with no date sorts oldest. Removing them breaks
date sorting on the report. Only fsr_add's hidden input is the item.

THE .form-card MARGIN IS THREE PAGES, NOT FOUR. edit_asset.html was
added to the list on 13 Oct and taken off the same day: its rule is
`.form-card label { margin-bottom: 4px }` - a LABEL margin inside a
form card, which is correct and normal. The survey matched `.form-card`
as a selector PREFIX. Acting on it would have pushed every label 22px
off its input.

The three real ones each read

    .form-card {
    <blank>
        margin-bottom: 14px;
    }

against base's 22px - and the blank line says an earlier round already
took everything else out of them. Removing the declaration leaves an
empty rule, so the rule goes with it.


WHAT THIS ROUND DOES NOT DO
---------------------------
It does not touch base - the class and all sixteen precedents exist. It
does not touch the three script-built headers, by decision. It does not
touch `accent-color: #dc3545` on the two finance pages: that is a
CHECKBOX tint, not a modal header, and `--alv-bad` is #b3261e, so it is
a visible change and a decision rather than a token swap. It does not
give base a header radius. And it does not widen `test_modal_heads`
past what it can honestly carry: the suite's LEAVE list grows by the
three script-built headers, named, with the reason.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import alv_tree                                            # noqa: E402

# THE HOUSE STRIPPER, ALIASED - not a private copy. alv_tree has had it
# since CO-1 on 3 Oct and test_code_only refuses any file that defines
# its own. DB-5 learned that the slow way yesterday.
code_only = alv_tree.code_only

SUFFIX = '.bak_modalhead2'
SUITE = 'test_modal_heads2.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
X0 = 'test_tree_roots.py'
MH = 'test_modal_heads.py'
CHECK = False

HOUSE = 'modal-header alv-modal-head alv-modal-head--danger'
PRECEDENTS = 16

CRS = ('crs/country_list.html', 'crs/fi_list.html',
       'crs/submission_detail.html', 'crs/submission_list.html')

OLD_HEAD = '<div class="modal-header bg-danger text-white">'
NEW_HEAD = '<div class="%s">' % HOUSE

# THE CLOSE BUTTON IS ANCHORED TO ITS OWN HEADER, NOT REPLACED LOOSE.
#
# `class="close text-white"` appears TWICE on three of these four pages,
# and the second one sits under a header that ALREADY wears
# .alv-modal-head. A loose replace would have taken both. So the whole
# header block is the anchor - open tag, title, close button, close tag
# - which is one occurrence per page and cannot reach the twin.
#
# Those three other `text-white` spellings are dead for exactly the
# reason this round is about: base's `.alv-modal-head .close` is
# !important. They are RECORDED, not touched: proving them dead needs
# its own render, and a round that sweeps a thing it has not measured
# is the habit this round exists to argue against.
OTHER_TEXT_WHITE = 3

HEAD_BLOCK = (
    '<div class="modal-header bg-danger text-white">\r\n'
    '        <h5 class="modal-title">\r\n'
    '          <i class="fas fa-exclamation-triangle"></i> @TITLE@\r\n'
    '        </h5>\r\n'
    '        @CLOSE@\r\n'
    '      </div>')
NEW_BLOCK = (
    '<div class="' + HOUSE + '">\r\n'
    '        <h5 class="modal-title">\r\n'
    '          <i class="fas fa-exclamation-triangle"></i> @TITLE@\r\n'
    '        </h5>\r\n'
    '        @CLOSE@\r\n'
    '      </div>')

# submission_detail writes its close on one line; the other three spread
# it over three. Both spellings, because an anchor that matches three of
# four is an anchor that half-applies.
CLOSE_3LINE = ('<button type="button" class="close" data-dismiss="modal">\r\n'
               '          <span>&times;</span>\r\n'
               '        </button>')
CLOSE_1LINE = ('<button type="button" class="close" data-dismiss="modal">'
               '<span>&times;</span></button>')

CRS_TITLES = {
    'crs/country_list.html': ('Delete Country Configuration', CLOSE_3LINE),
    'crs/fi_list.html': ('Delete Reporting FI', CLOSE_3LINE),
    'crs/submission_detail.html': ('Delete Draft Submission', CLOSE_1LINE),
    'crs/submission_list.html': ('Delete Submission', CLOSE_3LINE),
}


def crs_block(tpl, title, close, old):
    """The header block, in the before or after spelling."""
    c = close.replace('class="close"', 'class="close text-white"') \
        if old else close
    return tpl.replace('@TITLE@', title).replace('@CLOSE@', c)

# ------------------------------------------------------------------ 11
# Each anchor is the rule's EXACT text, read off disk. The replacement
# is what the rendered measurement says it really does - '' for the six
# that do nothing at all.
RULES = [
    ('comments_report.html',
     '.modal-header {\r\n'
     '    background: linear-gradient(135deg, var(--alv-accent) 0%,'
     ' var(--alv-accent-ink) 100%);\r\n'
     '    color: var(--alv-on-accent);\r\n'
     '    padding: 20px 30px;\r\n'
     '    display: flex;\r\n'
     '    justify-content: space-between;\r\n'
     '    align-items: center;\r\n'
     '    gap: 12px;\r\n'
     '}',
     '/* MH-2, 13 Oct 2026 - every declaration here but the gap was\r\n'
     '   outranked by base .alv-modal-head, which is !important.\r\n'
     '   Measured by rendering with and without, over the whole\r\n'
     '   computed style: only the gap moves. */\r\n'
     '.modal-header {\r\n'
     '    gap: 12px;\r\n'
     '}'),

    ('finance/cashflow_forecast.html',
     '.modal-header {\r\n'
     '    background: var(--alv-surface);\r\n'
     '    border-bottom: 1px solid var(--alv-line);\r\n'
     '    border-radius: 8px 8px 0 0;\r\n'
     '}',
     '/* MH-2 - the background and the border were outranked by base,\r\n'
     '   which is !important. The radius is not: base owns the header\r\n'
     '   and does not own its corners. 8px here, 4px on help_page and\r\n'
     '   Bootstrap 4.8px everywhere else - recorded, not fixed. */\r\n'
     '.modal-header {\r\n'
     '    border-radius: 8px 8px 0 0;\r\n'
     '}'),

    ('finance_expense_add.html',
     '#prorataPreviewModal .modal-header {\r\n'
     '    background: linear-gradient(135deg, var(--alv-bad) 0%,'
     ' #e83e8c 100%);\r\n'
     '    color: var(--alv-on-accent);\r\n'
     '    border-bottom: none;\r\n'
     '    padding: 16px 22px;\r\n'
     '}',
     '/* MH-2 - WAS a red-to-pink gradient on the Pro-Rata Preview\r\n'
     '   header. It has not painted since base took the component: an\r\n'
     '   id selector loses to !important however specific it is. The\r\n'
     '   header has worn .alv-modal-head the whole time. */'),

    ('finance_expense_edit.html',
     '#prorataPreviewModal .modal-header {\r\n'
     '    background: linear-gradient(135deg, var(--alv-bad) 0%,'
     ' #e83e8c 100%);\r\n'
     '    color: var(--alv-on-accent);\r\n'
     '    border-bottom: none;\r\n'
     '    padding: 16px 22px;\r\n'
     '}',
     '/* MH-2 - the twin of the rule on finance_expense_add, and dead\r\n'
     '   for the same reason. */'),

    ('finance_expense_line_types.html',
     '#deleteModal .modal-header {\r\n'
     '    background: linear-gradient(135deg, var(--alv-bad) 0%,'
     ' var(--alv-bad-ink) 100%);\r\n'
     '    color: var(--alv-on-accent);\r\n'
     '    border-bottom: none;\r\n'
     '    padding: 16px 22px;\r\n'
     '}',
     '/* MH-2 - dead. The header wears alv-modal-head--danger, and\r\n'
     '   base paints exactly this gradient from the token. */'),

    ('finance_expense_line_types_edit.html',
     '#prorataChangePreviewModal .modal-header {\n'
     '    background: linear-gradient(135deg, var(--alv-accent) 0%,'
     ' var(--alv-accent-ink) 100%);\n'
     '    color: var(--alv-on-accent);\n'
     '    border-bottom: none;\n'
     '    padding: 16px 22px;\n'
     '}',
     '/* MH-2 - dead, and it was a copy of base teal besides. NOTE the\n'
     '   bare LF: this is the one page of the ten that is not CRLF. */'),

    ('help_page.html',
     '  .manual-modal .modal-header {\r\n'
     '    background: linear-gradient(135deg, var(--alv-accent),'
     ' var(--alv-accent-ink));\r\n'
     '    color: var(--alv-on-accent);\r\n'
     '    border-radius: 4px 4px 0 0;\r\n'
     '  }',
     '  /* MH-2 - background and colour were outranked by base. The\r\n'
     '     4px radius is live and is left alone. */\r\n'
     '  .manual-modal .modal-header {\r\n'
     '    border-radius: 4px 4px 0 0;\r\n'
     '  }'),

    ('help_page.html',
     '  .manual-preview-modal .modal-header {\r\n'
     '    background: linear-gradient(135deg, var(--alv-accent),'
     ' var(--alv-accent-ink));\r\n'
     '    color: var(--alv-on-accent);\r\n'
     '    border-radius: 4px 4px 0 0;\r\n'
     '    flex-shrink: 0;\r\n'
     '  }',
     '  /* MH-2 - same, and the flex-shrink is live too. It took three\r\n'
     '     widenings of the probe to find that one. */\r\n'
     '  .manual-preview-modal .modal-header {\r\n'
     '    border-radius: 4px 4px 0 0;\r\n'
     '    flex-shrink: 0;\r\n'
     '  }'),

    ('occupancy_trends.html',
     '#yearDetailModal .modal-header {\r\n'
     '    background: linear-gradient(135deg, var(--alv-accent) 0%,'
     ' var(--alv-accent-ink) 100%);\r\n'
     '    color: var(--alv-on-accent);\r\n'
     '    border-bottom: none;\r\n'
     '    padding: 16px 22px;\r\n'
     '}',
     '/* MH-2 - dead, and a copy of base teal. */'),

    ('projects/projects_detail.html',
     '.modal-header {\r\n'
     '    background: var(--alv-surface);\r\n'
     '    border-bottom: 1px solid var(--alv-line);\r\n'
     '    border-radius: 8px 8px 0 0;\r\n'
     '}',
     '/* MH-2 - the twin of the cashflow_forecast rule. Only the radius\r\n'
     '   is live, and this page has FOUR headers wearing it. */\r\n'
     '.modal-header {\r\n'
     '    border-radius: 8px 8px 0 0;\r\n'
     '}'),

    ('suppliers.html',
     '.modal-header.bg-danger { background-color: var(--alv-bad)'
     ' !important; }',
     '/* MH-2 - dead for a DIFFERENT reason from the other ten. This one\r\n'
     '   carries !important itself, so it would win - but no element on\r\n'
     '   the page wears bg-danger any more. A rule with no target.\r\n'
     '   It is also the one that reported LIVE with no differing\r\n'
     '   property: 518 computed properties each side, the two sets\r\n'
     '   identical, the joined strings different. Removing a rule\r\n'
     '   changes the order the browser walks its own property list. */'),
]

DEAD_WHOLE = 6      # rules that go entirely
PART_LIVE = 5       # rules reduced to what they really do

# ------------------------------------------------------------------ 3
FORM_CARD = ('petty_cash_add.html', 'suppliers_add.html',
             'suppliers_edit.html')
FC_OLD = ('.form-card {\r\n'
          '        \r\n'
          '        margin-bottom: 14px;\r\n'
          '    }')
FC_NEW = ('/* MH-2, 13 Oct 2026 - WAS margin-bottom: 14px against base 22px.\r\n'
          '       The blank line above it said an earlier round had already\r\n'
          '       emptied this rule of everything else, so the declaration\r\n'
          '       and the rule go together. */')

# ------------------------------------------------------------------ 1
FSR = 'fsr_add.html'
# LF, NOT CRLF. fsr_add.html is one of the files in this tree that has
# no carriage returns at all - 74 bare line feeds, measured. An anchor
# written in the house spelling matches nothing here.
FSR_OLD = ('    <div class="form-group col-md-1">\n'
           '      <input type="hidden" id="issues_resolution_date"'
           ' name="issues_resolution_date" value="1900-01-01">\n'
           '    </div>\n')
FSR_NEW = ('    {# MH-2, 13 Oct 2026 - WAS a hidden input seeding #}\n'
           '    {# issues_resolution_date with 1900-01-01. The four other #}\n'
           '    {# spellings of that date, on fsr.html, are JavaScript #}\n'
           '    {# sort fallbacks - a.dataset.date || 1900-01-01 - in two #}\n'
           '    {# comparators, so a row with no date sorts oldest. They #}\n'
           '    {# stay. This one was the item. #}\n')

# What the three script-built headers are, so the LEAVE list can name
# them rather than hand-wave at them.
SCRIPT_BUILT = (
    ('home.html', 2),
    ('notifications.html', 1),
)

# A PINNED COUNT MOVES. test_code_only pins how many files alias the
# house stripper, and MH-2 adds two - a patcher and a suite. DB-5 moved
# it 45 -> 47 yesterday for the same reason, and learned the hard way
# that the anchor must include the trailing comma: replacing the string
# expression alone leaves the comma glued to a comment line, which is a
# SyntaxError in the suite that catches other people's syntax errors.
CO = 'test_code_only.py'
ALIAS_WAS, ALIAS_NOW = 47, 49

# AND DB-5's OWN SUITE, FOR THE REASON DB-5 WROTE DOWN YESTERDAY.
#
# test_dash_std asks whether DB-5 left CONVERTED_N at 67 and CEILING at
# 40, and asks it of test_waiting_down.py AS IT STANDS TODAY. MH-2 moves
# both, so DB-5's suite now reports that DB-5 did something it did not.
#
# DB-5 FIXED EXACTLY THIS IN test_drift_root - that suite read two
# census files live, and the first later round to re-pin either made it
# lie about E-10. DB-5 pointed those two lines at as_left_by and wrote
# the lesson into its own prose. AND THEN MADE THE SAME MISTAKE, THE
# SAME DAY, IN THE SUITE BESIDE IT.
#
# The fix is the same one and it is permanent: as_left_by walks ROUNDS
# forward from .bak_dashstd to the first later backup - which, after
# today, is .bak_modalhead2 - and hands back test_waiting_down.py
# exactly as DB-5 shipped it. The two numbers stay 67 and 40 and the
# checks pass for every round after this one.
DS = 'test_dash_std.py'

# FOUR MORE PINNED OBSERVATIONS THIS ROUND OWNS. None is a decision; all
# four are measurements of a tree that has moved.
IMP = 'test_important_base.py'
IMP_WAS, IMP_NOW = 858, 857          # suppliers' !important left with it
PC = 'test_pair_contrast.py'
PAIRS_WAS, PAIRS_NOW = 712, 704      # eight rules set both and are gone
HC = 'test_held_contrast.py'         # E-1b: modal_heads is STILL held
FCR = 'test_form_card_radius.py'     # FC-1: the three KEPT their margin
TS = 'test_table_suppliers.py'       # a FLOOR of 10 .modal rules

CONVERTED_WAS, CONVERTED_NOW = 67, 69
WAITING_WAS, WAITING_NOW = 3, 2
CEILING_WAS, CEILING_NOW = 40, 39


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('MH-2 REFUSED: %s' % msg)


def once(text, lit, where):
    n = text.count(lit)
    if n != 1:
        refuse('%s: %r appears %d time(s), expected exactly 1'
               % (where, lit[:70], n))


def exactly(text, lit, n, where):
    got = text.count(lit)
    if got != n:
        refuse('%s: %r appears %d time(s), expected exactly %d'
               % (where, lit[:70], got, n))


# ======================================================================
# WIDENING test_modal_heads - and the HEADER TWIN OF E-10's FIX
# ======================================================================
# The suite's own opener is
#
#     r'<div\s+class="([^"]*\b(?:modal-header|ei-modal-header)\b[^"]*)"'
#
# and `\b` matches inside `xml-modal-header`, because `-` is not a word
# character. So the XML viewer's chrome has been counted as a modal
# header all along - it simply never mattered while the walk could not
# reach the CRS root.
#
# E-10 fixed EXACTLY this on the footer side, in Show-ButtonDrift:
#
#     FOOTER_DIV = r'<div[^>]*class="[^"]*(?<![-\w])modal-footer(?![-\w])'
#
# so this is that fix, on its twin, three days later. Measured: 97
# headers seen loose, 96 with the exact class token, and the one that
# goes is the XML Viewer.
#
# WITH BOTH CHANGES THE SUITE'S EXISTING ASSERTION PASSES UNCHANGED.
# It says `len(naked) == 1 and naked[0].startswith('recipe_management')`.
# Widened and tightened, with the four CRS headers converted, naked IS
# one and it IS recipe_management - now across both roots instead of
# one. A widening that needs no new number is a widening that was right.
MH_IMPORT = ('import os\nimport re\nimport sys\n'
             'from collections import Counter\n')
MH_IMPORT_NEW = ('import os\nimport re\nimport sys\n'
                 'from collections import Counter\n\n'
                 'import alv_tree\n')

MH_WALK = 'for d, _, fs in os.walk(ROOT):'
MH_WALK_NEW = 'for d, _, fs in alv_tree.walk3():'

MH_REL = ("        rel = os.path.relpath(os.path.join(d, f), ROOT)"
          ".replace('\\\\', '/')")
MH_REL_NEW = '        rel = alv_tree.rel(os.path.join(d, f))'

MH_OPEN = ("OPEN = re.compile(r'<div\\s+class=\"([^\"]*\\b(?:modal-header"
           "|ei-modal-header)'\n"
           "                  r'\\b[^\"]*)\"([^>]*)>')")
MH_OPEN_NEW = (
    "# MH-2, 13 Oct 2026 - AN EXACT CLASS TOKEN, not \\b. `-` is not a\n"
    "# word character, so `\\bmodal-header\\b` matched inside\n"
    "# `xml-modal-header` - the CRS XML viewer's own chrome, which is not\n"
    "# a pop-up header at all and is already fully on house tokens. It\n"
    "# never mattered while this walk could not reach the second root.\n"
    "# E-10 made exactly this fix on the FOOTER side in\n"
    "# Show-ButtonDrift.py three days ago; this is its twin. Measured:\n"
    "# 97 headers seen loose, 96 with the token, and the one that goes\n"
    "# is the XML Viewer.\n"
    "OPEN = re.compile(r'<div\\s+class=\"([^\"]*(?<![-\\w])(?:modal-header"
    "|ei-modal-header)'\n"
    "                  r'(?![-\\w])[^\"]*)\"([^>]*)>')")

# The three script-built headers, named on the LEAVE list rather than
# fixed. Demetri's decision, 13 Oct: it is ONE blind spot, not two, and
# the whole script-built set gets priced in one round.
MH_LEAVE = ("LEAVE = {'recipe_management.html':\n"
            "         'the Recipe View modal renders in an IFRAME; its "
            "header is a '\n"
            "         'close strip - no border, 8px padding, and a title a "
            "script '\n"
            "         'fills in that is never shown. A pop-up header by "
            "markup, not '\n"
            "         'by intent. [E1]'}")
MH_LEAVE_NEW = (
    "LEAVE = {'recipe_management.html':\n"
    "         'the Recipe View modal renders in an IFRAME; its "
    "header is a '\n"
    "         'close strip - no border, 8px padding, and a title a "
    "script '\n"
    "         'fills in that is never shown. A pop-up header by "
    "markup, not '\n"
    "         'by intent. [E1]'}\n"
    "# NOT ON THE LIST ABOVE, AND NOT COUNTED - because mask() blanks\n"
    "# <script> before this walk ever sees them. home.html twice and\n"
    "# notifications.html once BUILD their modal header inside a\n"
    "# JavaScript string, so no header gate in this system can see\n"
    "# them. E11 logs twenty BUTTONS built the same way and prices\n"
    "# none; nobody had logged that the blind spot covers headers too.\n"
    "# Demetri's decision, 13 Oct 2026: it is ONE blind spot, not two,\n"
    "# and the whole script-built set gets priced in a single round\n"
    "# rather than chipped at. Recorded here so the next person reading\n"
    "# 'EVERY modal header in the system' knows what every means.\n"
    "SCRIPT_BUILT = {'home.html': 2, 'notifications.html': 1}")


def widen(text):
    """test_modal_heads onto alv_tree, and its opener onto a real class
    token. Returns the new text; refuses if any anchor is not unique."""
    for was, now in ((MH_IMPORT, MH_IMPORT_NEW),
                     (MH_WALK, MH_WALK_NEW),
                     (MH_REL, MH_REL_NEW),
                     (MH_OPEN, MH_OPEN_NEW),
                     (MH_LEAVE, MH_LEAVE_NEW)):
        once(text, was, MH)
        text = text.replace(was, now, 1)
    return text


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))

    # ---------------------------------------------------------------- 0
    # ALREADY APPLIED COMES FIRST, before any anchor is looked for, or a
    # second run reports a missing anchor as a broken file.
    first = alv_tree.join(CRS[0])
    if not os.path.isfile(first):
        refuse('%s is not on disk' % CRS[0])
    if HOUSE in read(first):
        print('MH-2  already applied - the CRS headers wear the house class.')
        return 0

    out = {}

    # ---------------------------------------------------------------- 1
    # THE FOUR CRS HEADERS. Sixteen precedents, one shape.
    prec = 0
    for p in alv_tree.templates():
        prec += code_only(read(p)).count('class="%s"' % HOUSE)
    if prec != PRECEDENTS:
        refuse('expected %d pages already writing %r, found %d - this round '
               'copies a precedent and must not invent one'
               % (PRECEDENTS, HOUSE, prec))

    for rel, (title, close) in CRS_TITLES.items():
        p = alv_tree.join(rel)
        t = read(p)
        was = crs_block(HEAD_BLOCK, title, close, True)
        once(t, was, rel)
        out[p] = t.replace(was, crs_block(NEW_BLOCK, title, close, False), 1)

    # CONTROL: the other three `close text-white` are left exactly alone.
    others = 0
    for rel in CRS:
        others += out[alv_tree.join(rel)].count('class="close text-white"')
    if others != OTHER_TEXT_WHITE:
        refuse('after the edit %d `close text-white` remain on the CRS '
               'pages, expected %d - those sit under headers that already '
               'wear the class and this round does not touch them'
               % (others, OTHER_TEXT_WHITE))

    # ---------------------------------------------------------------- 2
    # THE ELEVEN LOCAL RULES.
    whole = part = 0
    for rel, was, now in RULES:
        p = alv_tree.join(rel)
        t = out.get(p, read(p))
        once(t, was, rel)
        out[p] = t.replace(was, now, 1)
        if '{' in now:
            part += 1
        else:
            whole += 1
    if whole != DEAD_WHOLE or part != PART_LIVE:
        refuse('expected %d rules to go whole and %d to be reduced, got '
               '%d and %d' % (DEAD_WHOLE, PART_LIVE, whole, part))

    # ---------------------------------------------------------------- 3
    for rel in FORM_CARD:
        p = alv_tree.join(rel)
        t = out.get(p, read(p))
        once(t, FC_OLD, rel)
        out[p] = t.replace(FC_OLD, FC_NEW, 1)

    # ---------------------------------------------------------------- 4
    p = alv_tree.join(FSR)
    t = read(p)
    once(t, FSR_OLD, FSR)
    out[p] = t.replace(FSR_OLD, FSR_NEW, 1)
    if '1900-01-01' in code_only(out[p]):
        refuse('%s still carries 1900-01-01 in code' % FSR)
    fsr = read(alv_tree.join('fsr.html'))
    if fsr.count('1900-01-01') != 4:
        refuse('fsr.html no longer carries its four sort fallbacks - this '
               'round depends on them being four and being JavaScript')

    # ---------------------------------------------------------------- 5
    mh_p = os.path.join(root, MH)
    out[mh_p] = widen(read(mh_p))

    tree = read(os.path.join(root, TREE))
    line = [l for l in tree.split('\n') if l.strip().startswith("'%s':" % MH)]
    if len(line) != 1:
        refuse('%s is not on alv_tree.WAITING exactly once' % MH)
    start = tree.index(line[0])
    end = tree.index("',\n", start) + 3
    tree = tree[:start] + tree[end:]
    conv = "    'test_dash_std.py',\n]"
    once(tree, conv, TREE)
    out[os.path.join(root, TREE)] = tree.replace(
        conv,
        "    'test_dash_std.py',\n"
        "    # MH-2, 13 Oct 2026 - the last held suite that was work. It\n"
        "    # passed 13/0 while saying EVERY modal header in the system\n"
        "    # wears the class, which was true of one root. Widened it\n"
        "    # sees five more, four of them the round.\n"
        "    '%s',\n"
        "    # MH-2's own suite.\n"
        "    '%s',\n]" % (MH, SUITE), 1)

    rounds = read(os.path.join(root, ROUNDS))
    r_anchor = "    '.bak_dashstd',\n"
    once(rounds, r_anchor, ROUNDS)
    out[os.path.join(root, ROUNDS)] = rounds.replace(
        r_anchor, r_anchor + "    '%s',\n" % SUFFIX, 1)

    ps = read(os.path.join(root, PS1))
    p_anchor = "    'test_dash_std.py'\n)"
    once(ps, p_anchor, PS1)
    nps = ps.replace(
        p_anchor, "    'test_dash_std.py',\n    '%s'\n)" % SUITE, 1)

    s_anchor = ("    # -------------------------------------------- "
                "DB-5, 12 Oct 2026")
    once(nps, s_anchor, PS1)
    nps = nps.replace(
        s_anchor,
        "    # -------------------------------------------- MH-2, 13 Oct 2026\n"
        "    # The CRS delete confirmations are the house danger header\n"
        "    # now, like the sixteen in the first root. Bootstrap's\n"
        "    # bg-danger coming back here is the regression.\n"
        "    @{ File = 'crs\\templates\\crs\\submission_list.html'; "
        "Text = 'modal-header bg-danger'; "
        "What = 'the CRS delete header is base .alv-modal-head--danger'; "
        "Absent = $true; Code = $true }\n"
        + s_anchor, 1)

    blk = nps[nps.index('$sentinels = @('):]
    blk = blk[:blk.index('\n)\n')]
    body = [l.rstrip() for l in blk.split('\n')
            if l.strip() and not l.strip().startswith('#')]
    if body[-1].endswith(','):
        refuse('%s: the last thing in $sentinels ends in a comma - %r. That '
               'is a ParserError before the closing paren, and the script '
               'will not run AT ALL.' % (PS1, body[-1][-40:]))
    out[os.path.join(root, PS1)] = nps

    # A FLOOR IS A SAFETY NET, AND IT MOVES WHEN THE ROUND IS HONEST.
    # test_table_suppliers asserts the delete modal still has at least
    # ten rules, so that a deletion pass which took too much could not
    # pass every "is it gone?" check. MH-2 took one of the ten -
    # `.modal-header.bg-danger`, which had !important and no target -
    # and the floor moves by exactly that one rule, the way H9 moved it
    # from 7 to 2 when the More menu went home to base.
    ts = read(os.path.join(root, TS))
    t_was = "                           ('.modal', 10, 'delete modal')):"
    once(ts, t_was, TS)
    out[os.path.join(root, TS)] = ts.replace(
        t_was,
        "                           # MH-2, 13 Oct 2026 - 10 to 9. The rule\n"
        "                           # that went was .modal-header.bg-danger,\n"
        "                           # which carried !important and pointed at\n"
        "                           # an element no longer wearing bg-danger.\n"
        "                           # A rule with no target. The floor moves\n"
        "                           # by exactly one, the way H9 moved it\n"
        "                           # from 7 to 2.\n"
        "                           ('.modal', 9, 'delete modal')):", 1)

    imp = read(os.path.join(root, IMP))
    i_was = 'IMP_TREE = %d' % IMP_WAS
    once(imp, i_was, IMP)
    out[os.path.join(root, IMP)] = imp.replace(
        i_was,
        'IMP_TREE = %d   # MH-2, 13 Oct 2026 - suppliers\' one\n'
        '# !important left the tree with the rule that carried it: it beat\n'
        '# base, and pointed at an element that no longer wears bg-danger.\n'
        '# (was %d)' % (IMP_NOW, IMP_WAS), 1)

    pc = read(os.path.join(root, PC))
    p_was = 'EXPECT_PAIRS = %d' % PAIRS_WAS
    once(pc, p_was, PC)
    out[os.path.join(root, PC)] = pc.replace(
        p_was,
        'EXPECT_PAIRS = %d   # MH-2, 13 Oct 2026 - eight rules that set\n'
        '# both a background and a colour on a modal header went, because\n'
        '# base had been overriding every one of them.   # (was %d)'
        % (PAIRS_NOW, PAIRS_WAS), 1)

    # E-1b recorded that test_modal_heads was still held. It was, for
    # the reason it recorded. MH-2 is the round that answers it.
    hc = read(os.path.join(root, HC))
    h_was = "STILL_HELD = ('test_modal_heads.py', 'test_button_sweep.py')"
    once(hc, h_was, HC)
    out[os.path.join(root, HC)] = hc.replace(
        h_was,
        "# MH-2, 13 Oct 2026 - test_modal_heads comes off this list. E-1b\n"
        "# wrote that it STILL FAILED WIDENED, on the reason recorded\n"
        "# against it, and that was true: widened it found the Recipe View\n"
        "# close strip. What E-1b could not see is that widening it also\n"
        "# found four Bootstrap danger headers in the second root. MH-2\n"
        "# converted those and left the close strip on the LEAVE list with\n"
        "# its reason, which is what E-1b was waiting for.\n"
        "STILL_HELD = ('test_button_sweep.py',)", 1)

    h_chk = ("check('  and modal_heads for the reason recorded against"
             " it',\n"
             "      'Recipe View' in"
             " alv_tree.WAITING.get('test_modal_heads.py', ''),\n"
             "      alv_tree.WAITING.get('test_modal_heads.py',"
             " 'not held at all'))")
    once(out[os.path.join(root, HC)], h_chk, HC)
    out[os.path.join(root, HC)] = out[os.path.join(root, HC)].replace(
        h_chk,
        "# MH-2, 13 Oct 2026 - the reason did not go away, it MOVED. It\n"
        "# used to be a line on alv_tree.WAITING explaining why the suite\n"
        "# could not be widened; it is now a named entry on that suite's\n"
        "# own LEAVE list, which is a stronger place for it - a reader of\n"
        "# the suite finds it, where a reader of alv_tree never would.\n"
        "# Asking the live WAITING for it after the suite is released is\n"
        "# asking the wrong object.\n"
        "check('  and the Recipe View reason moved onto the suite LEAVE '\n"
        "      'list, where a reader of the suite will find it',\n"
        "      'Recipe View' in read(os.path.join(ROOT,\n"
        "                                        'test_modal_heads.py')),\n"
        "      'not on the LEAVE list either')", 1)

    # FC-1 deliberately LEFT these three margins, and said why: a round
    # that changes two things cannot say which one moved. It named the
    # margin as a second question about the same component. MH-2 is
    # that second question.
    fcr = read(os.path.join(root, FCR))
    f_was = "head('4. THE THREE THAT KEPT THEIR MARGIN')"
    once(fcr, f_was, FCR)
    nfcr = fcr.replace(
        f_was, "head('4. THE THREE MARGINS FC-1 LEFT, AND MH-2 TOOK')", 1)
    f_chk = ("    check('  %s still sets margin-bottom: 14px' % rel,\n"
             "          m2 is not None and 'margin-bottom: 14px' in"
             " m2.group(1),\n"
             "          '' if m2 is None else"
             " ' '.join(m2.group(1).split())[:40])")
    once(nfcr, f_chk, FCR)
    out[os.path.join(root, FCR)] = nfcr.replace(
        f_chk,
        "    # MH-2, 13 Oct 2026 - WAS 'still sets margin-bottom: 14px'.\n"
        "    # FC-1 left these three on purpose and said why: a round that\n"
        "    # changes two things cannot say which one moved, so the\n"
        "    # margin was named as a second question about the same\n"
        "    # component. MH-2 asked it. The rules were empty but for\n"
        "    # that one declaration - an earlier round had already taken\n"
        "    # everything else out - so the declaration and the rule went\n"
        "    # together, and all three pages take base's 22px.\n"
        "    check('  %s has given its margin up to base 22px' % rel,\n"
        "          m2 is None or 'margin-bottom: 14px' not in m2.group(1),\n"
        "          '' if m2 is None else"
        " ' '.join(m2.group(1).split())[:40])", 1)

    ds = read(os.path.join(root, DS))
    d_was = ("wd = os.path.join(ROOT, 'test_waiting_down.py')\n"
             "if os.path.isfile(wd):\n"
             "    w = read(wd)\n")
    once(ds, d_was, DS)
    out[os.path.join(root, DS)] = ds.replace(
        d_was,
        "# MH-2, 13 Oct 2026 - AS DB-5 LEFT IT, not as it stands today.\n"
        "# These two numbers moved the moment the next round touched the\n"
        "# census, and this suite then reported that DB-5 had done\n"
        "# something it had not. DB-5 made this very repair to\n"
        "# test_drift_root and wrote the lesson into its own prose - and\n"
        "# made the same mistake, the same day, in the suite beside it.\n"
        "# A suite asking about its OWN round must read the file as its\n"
        "# own round left it. Lesson 40, for the third time this week.\n"
        "wd = os.path.join(ROOT, 'test_waiting_down.py')\n"
        "if os.path.isfile(wd):\n"
        "    w = as_left_by(wd, SUFFIX, read) if as_left_by else read(wd)\n",
        1)

    co = read(os.path.join(root, CO))
    c_was = 'ok(len(aliased) == %d,' % ALIAS_WAS
    once(co, c_was, CO)
    nco = co.replace(c_was, 'ok(len(aliased) == %d,' % ALIAS_NOW, 1)
    c_txt = ("'%d file(s) alias it - 23 patchers and 24 suites'"
             " % len(aliased),")
    once(nco, c_txt, CO)
    out[os.path.join(root, CO)] = nco.replace(
        c_txt,
        "'%d file(s) alias it - 24 patchers and 25 suites' % len(aliased),"
        "   # MH-2, 13 Oct 2026 - two more   # (was 47, 23 and 24)", 1)

    wd = read(os.path.join(root, WD))
    for was, now in (
            ('CONVERTED_N = %d' % CONVERTED_WAS,
             'CONVERTED_N = %d   # MH-2, 13 Oct 2026 - test_modal_heads '
             'released,\n# plus this round own suite   # (was %d)'
             % (CONVERTED_NOW, CONVERTED_WAS)),
            ('WAITING_N = %d' % WAITING_WAS,
             'WAITING_N = %d   # MH-2 - the last held suite that was work '
             'comes off.\n# The two left are a parked decision and a '
             'deliberate narrowness.   # (was %d)'
             % (WAITING_NOW, WAITING_WAS)),
            ('CEILING = %d' % CEILING_WAS,
             'CEILING = %d   # MH-2 - one more census   # (was %d)'
             % (CEILING_NOW, CEILING_WAS))):
        once(wd, was, WD)
        wd = wd.replace(was, now, 1)
    out[os.path.join(root, WD)] = wd

    x0 = read(os.path.join(root, X0))
    c_was = 'WALKERS_OWN_ROOT_MAX = %d' % CEILING_WAS
    once(x0, c_was, X0)
    out[os.path.join(root, X0)] = x0.replace(
        c_was,
        'WALKERS_OWN_ROOT_MAX = %d   # MH-2, 13 Oct 2026 - one more\n'
        '# census converted, and it may only FALL.   # (was %d)'
        % (CEILING_NOW, CEILING_WAS), 1)

    # ---------------------------------------------------------------- 6
    if CHECK:
        print('')
        print('MH-2  check only - nothing written')
        print('MH-2  would put the %d CRS delete headers on base' % len(CRS))
        print('MH-2  .alv-modal-head--danger, the shape %d pages in the'
              % PRECEDENTS)
        print('MH-2  first root already write')
        print('MH-2  would take %d dead rules out whole and reduce %d more'
              % (DEAD_WHOLE, PART_LIVE))
        print('MH-2  to what they really do - measured by rendering each')
        print('MH-2  page with and without, over the WHOLE computed style')
        print('MH-2  would remove %d .form-card margins and one hidden'
              % len(FORM_CARD))
        print('MH-2  input, leaving the four JavaScript sort fallbacks')
        print('MH-2  would widen %s and tighten its opener to an exact' % MH)
        print('MH-2  class token - E-10 fix, header twin')
        print('MH-2  WAITING %d -> %d, CONVERTED %d -> %d, ceiling %d -> %d'
              % (WAITING_WAS, WAITING_NOW, CONVERTED_WAS, CONVERTED_NOW,
                 CEILING_WAS, CEILING_NOW))
        print('MH-2  %d file(s) would change' % len(out))
        return 0

    for p in sorted(out):
        backup(p)
        write(p, out[p])

    print('')
    print('MH-2  the %d CRS delete headers wear base .alv-modal-head--danger'
          % len(CRS))
    print('MH-2  now, the shape %d pages in the first root already had.'
          % PRECEDENTS)
    print('MH-2  %d dead rules came out whole and %d were reduced to what'
          % (DEAD_WHOLE, PART_LIVE))
    print('MH-2  they really do. NOTHING ON SCREEN MOVES for any of the')
    print('MH-2  eleven, and that is rendered, not argued: each page')
    print('MH-2  drawn with and without its own rule, compared over the')
    print('MH-2  WHOLE computed style, sorted. Three narrower versions of')
    print('MH-2  that probe each called a live rule dead.')
    print('MH-2  %s is widened and released, and its opener now reads an'
          % MH)
    print('MH-2  exact class token - the header twin of E-10 footer fix.')
    print('MH-2  Its assertion did not need a new number.')
    print('MH-2  WAITING %d -> %d, CONVERTED %d -> %d, ceiling %d -> %d'
          % (WAITING_WAS, WAITING_NOW, CONVERTED_WAS, CONVERTED_NOW,
             CEILING_WAS, CEILING_NOW))
    print('MH-2  %d file(s) changed' % len(out))
    print('MH-2  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
