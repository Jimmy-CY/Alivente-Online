# -*- coding: utf-8 -*-
"""apply_row_actions.py - Section D, round D3: the row pill comes home,
the last four script buttons are decided, and three stale LEAVE reasons go.

    python apply_row_actions.py --check     dry run, nothing written
    python apply_row_actions.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

Decided 23 Sep, from claude/d3_survey.md.

  A. EDIT'S COLOUR DEPENDED ON WHICH MODULE YOU WERE IN.
     Six Financials pages draw a labelled row Edit, each from its own
     near-identical copy of the same CSS. Read off the stylesheets:

       finance_revenue            Edit GREEN  #28a745
       finance_revenue_types      Edit GREEN  #28a745
       finance_revenue_line_types Edit GREEN  #28a745
       finance_expense_types      Edit RED    #dc3545
       finance_expense            Edit RED    #dc3545   Delete #a71d2a
       finance_expense_line_types Edit RED    #dc3545   Delete GREY #6c757d

     The colour was tracking the MODULE, not the action - and on
     finance_expense_line_types the pair was inverted, with the
     destructive button quiet and the safe one shouting. Base's own
     standard says "Colour is by WEIGHT, not by verb", and the standing
     instruction on record is that all Financials sub-modules take the
     same format as the rest of the system.

     So base takes the component, exactly as it took the filter chip:
     `.btn-row-edit` and `.btn-row-delete` keep their names, so no markup
     changes and no template tag or permission block is at risk - the six
     pages join by DELETING their copies. Edit takes --alv-edit and
     Delete takes --alv-danger, the same two colours the ICON row actions
     already use, because they are the same two actions in another shape.

     Two things travel with the move and are improvements, not accidents:
       - the disabled variants keep pointer-events AUTO. finance_expense
         worked that out first and wrote the reason down - a disabled
         control still has to be able to say WHY, and its `title` never
         appears while pointer-events is none. Five pages did not have it;
         now all six do.
       - the two `-types` pages padded 5px 12px where the other four
         padded 5px 14px. Base takes 14px, so the six finally agree.

     The two `-types` pages KEEP their own tablet-card rule
     (`.rev-type-card` / `.exp-type-card` at 1024px): that is a layout
     only those two have, and it is genuinely theirs.

  B. THE LAST FOUR BUTTONS BUILT INSIDE <script>.
     Show-ButtonDrift has reported these as undecided since the button
     sweep, because a button assigned into a modal footer has no wrapper
     in the markup to say what it is. Decided by hand, from what the
     house already does:

       cashflow_forecast  Close   btn-secondary -> action-secondary
       cashflow_forecast  Back    btn-info      -> action-secondary
       cashflow_forecast  Close   btn-secondary -> action-secondary
       asset_detail       Open File btn-info    -> action-primary

     Close in a modal footer is action-secondary on twelve pages already.
     Back in a modal footer is action-secondary too - properties_edit's
     "Back to the property" is the precedent; action-back is a BAR
     position and loses its shape outside one. Open File is the one thing
     you can do on a card that says the file cannot be previewed, which
     is the same shape as `pdf-viewer-error`, already DECIDED as primary.

  C. THREE LEAVE REASONS THAT ARE NO LONGER TRUE.
     Show-ButtonDrift gives eight buttons the reason "segmented toggle -
     colour is state". None of the three wrappers is a segmented toggle:

       selection-buttons   Select All / Select None - two one-shot
                           actions. D2 made vacancy_management's pair
                           house secondaries; the twin already was.
       fi-trend-controls   its buttons are ALREADY btn action-secondary.
       pd-toolbar          holds ONE link at a time, in an {% if %}/
                           {% else %}, and both branches write the same
                           class - so no colour carries any state.

     All three move from LEAVE to DECIDED as secondaries, which turns a
     silence into a standard the tool can check. The first two already
     comply. pd-toolbar does not, so tenant_payment_days' two links are
     retoned here - the same finding the running list recorded as
     "tenant_payment_days .pd-toggle".

Not in this round: the filter fields' fourteen page-level 44px rules
(D4), and the two 12-colour chart palettes (D5).
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
SUFFIX = '.bak_rowact'
SUITE = 'test_row_actions.py'
PS1 = 'Push-PendingChanges.ps1'
ROUNDS_FILE = 'alv_rounds.py'
DRIFT = 'Show-ButtonDrift.py'

BASE = os.path.join(T, 'base.html')
CFF = os.path.join(T, 'finance', 'cashflow_forecast.html')
ASSET = os.path.join(T, 'asset_detail.html')
TPD = os.path.join(T, 'tenant_payment_days.html')
SIX = ['finance_revenue.html',
       'finance_revenue_types.html',
       'finance_revenue_line_types.html',
       'finance_expense_types.html',
       'finance_expense.html',
       'finance_expense_line_types.html']

# ==========================================================================
# A. Base takes the row pill
# ==========================================================================
PILL_ANCHOR = """      /* ========================================================== PILLS */
"""
PILL = """      /* ================================================== ROW ACTIONS,
         WITH A WORD ===== ALV ROW PILL v1 ===== 23 Sep 2026

         The labelled row action - Edit and Delete with the word, not only
         the icon above - which six Financials pages each carried a copy
         of. The copies had drifted into saying something untrue: Edit was
         GREEN on the three revenue pages and RED on the three expense
         pages, so the colour tracked which MODULE you were in rather than
         what the button did; and on finance_expense_line_types the pair
         was inverted, Edit red and Delete grey, so the destructive one was
         the quiet one. Decision 3.1 - colour means something - and the
         instruction that every Financials sub-module takes the same format
         as the rest of the system.

         THE SAME TWO COLOURS AS .icon-edit AND .icon-delete ABOVE. They
         are the same two actions in a different shape, and a page that
         shows Edit as an icon must not disagree with a page that shows it
         as a word. The BORDER stays 2px solid in the action's own colour,
         which is the weight these six already had - this round changes the
         hue, not the shape.

         pointer-events stays AUTO on the disabled variants. finance_expense
         worked that out first and wrote the reason beside it: a disabled
         control still has to be able to say WHY it is disabled, and its
         `title` never appears while pointer-events is none. Five of the six
         did not have it. Now all six do.

         A page joins by DELETING its copy - no markup changes, so no
         template tag and no permission block is ever at risk.
                                                  [test_row_actions.py] */
      .btn-row-edit,
      .btn-row-delete,
      .btn-row-edit-disabled,
      .btn-row-delete-disabled {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 5px 14px;
        border-radius: var(--alv-radius-sm);
        border: 2px solid var(--alv-line);
        background: var(--alv-paper);
        font-family: inherit;
        font-size: 13px;
        font-weight: 500;
        line-height: 1.5;
        text-decoration: none;
        transition: background-color .15s ease, border-color .15s ease,
                    color .15s ease;
      }
      .btn-row-edit   { color: var(--alv-edit);   border-color: var(--alv-edit); }
      .btn-row-delete { color: var(--alv-danger); border-color: var(--alv-danger);
                        cursor: pointer; }
      .btn-row-edit:hover {
        background: var(--alv-edit);
        border-color: var(--alv-edit);
        color: #fff;
        text-decoration: none;
      }
      .btn-row-delete:hover {
        background: var(--alv-danger);
        border-color: var(--alv-danger);
        color: #fff;
      }
      .btn-row-edit:focus-visible,
      .btn-row-delete:focus-visible {
        outline: 2px solid var(--alv-accent);
        outline-offset: 2px;
      }
      /* A permission the user does not have is SHOWN, not hidden - the
         same decision the icon row actions take above. */
      .btn-row-edit-disabled,
      .btn-row-delete-disabled {
        background: var(--alv-surface);
        color: var(--alv-ink-faint);
        border-color: var(--alv-line);
        cursor: not-allowed;
        pointer-events: auto;
      }
      /* On a phone the row becomes a card and the action takes the width,
         which four of the six already did for themselves. Unscoped, so the
         two that put their copy behind a card class - and were therefore
         still 34px on a phone - get it as well.

         min-height, and 44 rather than the 43 those four copies actually
         measured. 9px of padding on 14px type came to 43px with the two
         borders, one short of the target standard 3.4 has promised for
         weeks, and nobody had measured it. The ALV TAP TARGET block does
         not reach this control, because a row pill is not a .btn. */
      @media screen and (max-width: 768px) {
        .btn-row-edit,
        .btn-row-delete,
        .btn-row-edit-disabled,
        .btn-row-delete-disabled {
          width: 100%;
          justify-content: center;
          padding: 9px 14px;
          font-size: 14px;
          min-height: 44px;
        }
      }
      /* ===== /ALV ROW PILL v1 ===== */

"""

# The selectors each page hands over. Cut by SELECTOR, brace-aware, each
# required to appear exactly once - never by tidying the file, which is
# how the filter-chip round went wrong once (lesson 16).
CUT = {
    'finance_revenue.html': [
        '.btn-row-edit', '.btn-row-edit:hover', '.btn-row-edit-disabled',
        '.btn-row-edit, .btn-row-edit-disabled'],
    'finance_revenue_types.html': [
        '.btn-row-edit', '.btn-row-edit:hover', '.btn-row-edit-disabled'],
    'finance_revenue_line_types.html': [
        '.btn-row-edit', '.btn-row-edit:hover', '.btn-row-edit-disabled',
        '.btn-row-edit, .btn-row-edit-disabled'],
    'finance_expense_types.html': [
        '.btn-row-edit', '.btn-row-edit:hover', '.btn-row-edit-disabled'],
    'finance_expense.html': [
        '.btn-row-edit', '.btn-row-edit:hover', '.btn-row-edit-disabled',
        '.btn-row-delete', '.btn-row-delete:hover', '.btn-row-delete-disabled',
        '.btn-row-edit-disabled, .btn-row-delete-disabled',
        '.btn-row-edit, .btn-row-edit-disabled, .btn-row-delete, '
        '.btn-row-delete-disabled'],
    'finance_expense_line_types.html': [
        '.btn-row-edit', '.btn-row-edit:hover',
        '.btn-row-delete', '.btn-row-delete:hover',
        '.btn-row-edit-disabled, .btn-row-delete-disabled',
        '.btn-row-edit, .btn-row-edit-disabled, .btn-row-delete, '
        '.btn-row-delete-disabled'],
}
# What each page KEEPS, and why. Checked after the cut, so a selector that
# should have survived cannot be swept up by a wider match.
KEEPS = {
    'finance_revenue_types.html': '.rev-type-card .btn-row-edit',
    'finance_expense_types.html': '.exp-type-card .btn-row-edit',
}

# ==========================================================================
# B. The four buttons built inside <script>
# ==========================================================================
EDITS = {}
EDITS[CFF] = [(
    '    modalFooter.innerHTML = `<button type="button" '
    'class="btn btn-secondary" data-dismiss="modal">Close</button>`;\n',
    '    modalFooter.innerHTML = `<button type="button" '
    'class="btn action-secondary" data-dismiss="modal">Close</button>`;\n'), (
    '        <button type="button" class="btn btn-info" '
    'onclick="showMonthlyView()">\n',
    '        <button type="button" class="btn action-secondary" '
    'onclick="showMonthlyView()">\n'), (
    # Widened to take the line above it. The narrow form was unique in
    # the file, but its REPLACEMENT was not: line 190 already carries the
    # same button at deeper indentation, so `new in cur` matched a suffix
    # of that line and the patcher believed this edit was already done.
    # An anchor has to be unique after it is applied, not only before.
    '        </button>\n'
    '        <button type="button" class="btn btn-secondary" '
    'data-dismiss="modal">Close</button>\n',
    '        </button>\n'
    '        <button type="button" class="btn action-secondary" '
    'data-dismiss="modal">Close</button>\n')]

# The THIRD copy of the Select All / Select None widget. It was hidden
# behind the `selection-buttons` LEAVE reason this round removes, and it
# surfaced the moment the reason went - which is the argument for moving
# a LEAVE to DECIDED rather than deleting it. Same change D2 made to
# vacancy_management. `.pl-select-all-group` keeps welding Select All to
# + Inactive: that is geometry, and geometry is the group's business.
# `.btn-sm` goes with the class, as nothing else on the page wore it.
PL = os.path.join(T, 'finance_pl_act.html')
EDITS[PL] = [(
    '                    <button class="btn btn-info btn-sm" '
    'id="selectAllBtn" onclick="event.stopPropagation();"\n',
    '                    <button class="btn action-secondary" '
    'id="selectAllBtn" onclick="event.stopPropagation();"\n'), (
    '{% if has_inactive %}<button class="btn btn-secondary btn-sm" '
    'id="selectAllIncBtn" onclick="event.stopPropagation();"\n',
    '{% if has_inactive %}<button class="btn action-secondary" '
    'id="selectAllIncBtn" onclick="event.stopPropagation();"\n'), (
    '                <button class="btn btn-secondary btn-sm" '
    'id="selectNoneBtn" onclick="event.stopPropagation();">Select None'
    '</button>\n',
    '                <button class="btn action-secondary" '
    'id="selectNoneBtn" onclick="event.stopPropagation();">Select None'
    '</button>\n'), (
    '.btn-sm { padding: 5px 10px; font-size: 12px; border-radius: 4px; }\n',
    '')]
EDITS[ASSET] = [(
    '                <a href="${url}" target="_blank" class="btn btn-info">'
    'Open File</a>\n',
    '                <a href="${url}" target="_blank" '
    'class="btn action-primary">Open File</a>\n')]

# ==========================================================================
# C. pd-toolbar is not a segmented toggle
# ==========================================================================
EDITS[TPD] = [(
    "        <a href=\"{% url 'tenant_payment_days' %}\" "
    'class="btn btn-outline-secondary btn-sm">\n',
    "        <a href=\"{% url 'tenant_payment_days' %}\" "
    'class="btn action-secondary">\n'), (
    "        <a href=\"{% url 'tenant_payment_days' %}?all=1\" "
    'class="btn btn-outline-secondary btn-sm">\n',
    "        <a href=\"{% url 'tenant_payment_days' %}?all=1\" "
    'class="btn action-secondary">\n')]

# The tool. Three reasons leave LEAVE and become DECIDED secondaries, so
# the tool can CHECK them instead of staying silent about them.
DRIFT_EDITS = [(
    "    'fi-trend-controls': 'segmented toggle - colour is state',\n"
    "    'pd-toolbar': 'segmented toggle - colour is state',\n"
    "    'selection-buttons': 'segmented toggle - colour is state',\n",
    ""), (
    "    'timeline-controls-group': [('*', S)],\n",
    "    'timeline-controls-group': [('*', S)],\n"
    "    # D3, 23 Sep. These three were LEAVE, all three with the reason\n"
    "    # \"segmented toggle - colour is state\". None of them is a\n"
    "    # segmented toggle: selection-buttons is Select All / Select None,\n"
    "    # two one-shot actions; fi-trend-controls already carried house\n"
    "    # tones; and pd-toolbar holds ONE link at a time in an if/else,\n"
    "    # with both branches writing the same class. Moved here so the\n"
    "    # tool CHECKS them rather than staying silent about them.\n"
    "    'selection-buttons':       [('*', S)],\n"
    "    'fi-trend-controls':       [('*', S)],\n"
    "    'pd-toolbar':              [('*', S)],\n"), (
    # The reason also survived in js_buttons' own docstring comment, where
    # it explained why a LEAVE carries across into a script-built button.
    # The mechanism is right; the example it used is not.
    "            # A wrapper already on the LEAVE list was decided once, in\n"
    "            # markup, and the decision does not change because the div\n"
    "            # happens to be built by JavaScript. financial_indicators and\n"
    "            # vacancy_management both put their Select All / Select None\n"
    "            # pair in .selection-buttons - a segmented toggle whose colour\n"
    "            # IS its state. Carry the reason across rather than asking for\n"
    "            # the same four decisions a second time.\n",
    "            # A wrapper already on the LEAVE list was decided once, in\n"
    "            # markup, and the decision does not change because the div\n"
    "            # happens to be built by JavaScript - a row action inside a\n"
    "            # .btn-group is a row action wherever the div came from.\n"
    "            # Carry the reason across rather than asking for the same\n"
    "            # decision a second time.\n"
    "            #\n"
    "            # This used to cite .selection-buttons as the example, and\n"
    "            # called it a segmented toggle whose colour IS its state.\n"
    "            # It is not one - it is Select All and Select None, two\n"
    "            # one-shot actions - and D3 (23 Sep) moved it to DECIDED.\n")]

# ==========================================================================
# LATER - test_button_sweep.py
# ==========================================================================
# That suite guards the button sweep's findings, and this round CLOSES the
# last of them. Its own comment asked for exactly this:
#
#   "when the last page is decided there is no state in which eight
#    existed, and the control retires with the finding it guards"
#
# So: the HISTORICAL claims are re-pointed at the pages as the SWEEP left
# them, which is this round's backup, and stay at eight in four; and the
# LIVE checks that counted what was still undone are rewritten to say the
# work is finished, rather than lowered to zero and left looking like a
# guard. What is kept in every case is a claim asked of the SCANNER, which
# a finished corpus cannot make vacuous.
SWEEP = 'test_button_sweep.py'
SWEEP_EDITS = [(
    # The tenants toolbar. D3 retoned it, so the claim about what the
    # SWEEP left has to read the file the sweep left.
    "_pd = load(os.path.join(TPL, 'tenant_payment_days.html'))\n"
    "check('the tenants segmented toggle is untouched',\n"
    "      _pd.count('btn-outline-secondary') >= 2)\n",
    "# D3, 23 Sep: `pd-toolbar` was never a segmented toggle - it holds ONE\n"
    "# link at a time in an {% if %}/{% else %}, and both branches wrote the\n"
    "# same class - so the round retoned it. What the SWEEP left alone is\n"
    "# still the claim, so it is read from the sweep's own copy.\n"
    "_pdp = os.path.join(TPL, 'tenant_payment_days.html')\n"
    "_pd = load(_pdp + '.bak_rowact') if os.path.exists(_pdp + '.bak_rowact')"
    " \\\n    else load(_pdp)\n"
    "check('the tenants toolbar was untouched BY THE SWEEP',\n"
    "      _pd.count('btn-outline-secondary') >= 2)\n"), (
    "          'finance/vacancy_management.html': '.bak_three'}\n",
    "          'finance/vacancy_management.html': '.bak_three',\n"
    "          # D3, 23 Sep: the last two script-built pages are decided.\n"
    "          # With these the count is eight in four again, and there is\n"
    "          # now no state in which eight are undecided - which is what\n"
    "          # the note above said would happen.\n"
    "          'finance/cashflow_forecast.html': '.bak_rowact',\n"
    "          'asset_detail.html': '.bak_rowact'}\n"), (
    "      # 6 in 3 until D2 decided vacancy_management's pair. What is\n"
    "      # left is the four this suite names below, on two pages.\n"
    "      len(_all) >= 4 and len(_js) >= 2)\n",
    "      # 6 in 3 until D2 decided vacancy_management's pair; 4 in 2 until\n"
    "      # D3 decided cashflow_forecast's three and asset_detail's one.\n"
    "      # THE FINDING IS CLOSED, so this is no longer a floor - it is the\n"
    "      # statement that nothing is left. The scanner-level CONTROL below\n"
    "      # is what still guards the scan itself.\n"
    "      len(_all) == 0 and len(_js) == 0 and len(_open) == 0)\n"), (
    "check('the undecided ones are still reported (cashflow_forecast, "
    "asset_detail)',\n"
    "      len(_js.get('finance/cashflow_forecast.html', [])) == 3\n"
    "      and len(_js.get('asset_detail.html', [])) == 1)\n",
    "# The two that were last. Named, so that closing them is recorded here\n"
    "# rather than showing only as a number going to zero.\n"
    "check('the last two are decided too (cashflow_forecast, asset_detail)',\n"
    "      not _js.get('finance/cashflow_forecast.html')\n"
    "      and not _js.get('asset_detail.html'))\n"
    "check('.. and they carry house tones now, in the script',\n"
    "      'btn action-secondary' in load(os.path.join(\n"
    "          TPL, 'finance', 'cashflow_forecast.html'))\n"
    "      and 'btn action-primary' in load(os.path.join(\n"
    "          TPL, 'asset_detail.html')))\n"), (
    "_LEAVE_REASON = 'segmented toggle - colour is state'\n"
    "_was_open = [h for h in _was_all if not h[5]]\n"
    "check('HISTORICAL: four of the eight carried a LEAVE reason (%d)'\n"
    "      % (len(_was_all) - len(_was_open)),\n"
    "      len(_was_all) - len(_was_open) == 4\n"
    "      and all(h[5] == _LEAVE_REASON for h in _was_all if h[5]))\n",
    "# The reason those four carried was 'segmented toggle - colour is\n"
    "# state', and D3 removed it: .selection-buttons is Select All and\n"
    "# Select None, two one-shot actions, not a toggle. The REASON cannot\n"
    "# be recomputed with today's tool, so the shape of the finding is what\n"
    "# is kept - four of the eight sat in the one wrapper the sweep had\n"
    "# decided in markup, which is the fact the carry-across existed for.\n"
    "_LEAVE_REASON = 'row actions'\n"
    "_was_sel = [h for h in _was_all if h[2] and 'selection-buttons' in h[2]]\n"
    "check('HISTORICAL: four of the eight sat in .selection-buttons (%d)'\n"
    "      % len(_was_sel), len(_was_sel) == 4)\n"), (
    "check('CONTROL: a LEAVE wrapper carries its reason into a script-built '\n"
    "      'button, whether or not a live page still has one',\n"
    "      [h[5] for h in sb.js_buttons(\n"
    "          '<script>var h = `<div class=\"selection-buttons\">'\n"
    "          '<button class=\"btn btn-info btn-sm\">Select All</button>'\n"
    "          '</div>`;</script>')] == [_LEAVE_REASON])\n",
    "# Asked with a wrapper that is STILL on the LEAVE list, since the one\n"
    "# this used before is not any more. The claim is unchanged.\n"
    "check('CONTROL: a LEAVE wrapper carries its reason into a script-built '\n"
    "      'button, whether or not a live page still has one',\n"
    "      [h[5] for h in sb.js_buttons(\n"
    "          '<script>var h = `<div class=\"btn-group\">'\n"
    "          '<button class=\"btn btn-info btn-sm\">Edit</button>'\n"
    "          '</div>`;</script>')] == [_LEAVE_REASON])\n"), (
    "check('a real .innerHTML target IS reported (cashflow_forecast "
    "modalFooter)',\n"
    "      any(h[3] == 'modalFooter'\n"
    "          for h in _js.get('finance/cashflow_forecast.html', [])))\n",
    "# Asked of the scanner, not of the corpus: cashflow_forecast's three\n"
    "# are decided, and a control that needed an undecided page would have\n"
    "# retired with them instead of going on meaning something.\n"
    "check('CONTROL: a real .innerHTML target IS reported',\n"
    "      [h[3] for h in sb.js_buttons(\n"
    "          '<script>modalFooter.innerHTML = `<button '\n"
    "          'class=\"btn btn-info\">Close</button>`;</script>')]\n"
    "      == ['modalFooter'])\n"), (
    "check('finance/cashflow_forecast.html script block is untouched '\n"
    "      '(btn btn-info still there)',\n"
    "      'btn btn-info' in load(os.path.join(TPL, "
    "'finance/cashflow_forecast.html')))\n",
    "check('finance/cashflow_forecast.html script block was untouched BY '\n"
    "      'THE SWEEP (btn btn-info still there when it finished)',\n"
    "      'btn btn-info' in _as_swept('finance/cashflow_forecast.html'))\n"), (
    "check('a clean --strict run still prints the <script> finding',\n"
    "      'BUILT INSIDE <script>' in _r10.stdout)\n",
    "# It printed the finding for as long as there was one. There is not,\n"
    "# so what the clean run must now say is that nothing is left - and\n"
    "# the two halves together still make this impossible to satisfy by\n"
    "# the report going quiet about a finding that survives.\n"
    "check('with none left, the clean run says nothing is undecided',\n"
    "      'Nothing drifting, and nothing undecided' in _r10.stdout\n"
    "      and 'BUILT INSIDE <script>' not in _r10.stdout)\n")]

EDITS[SWEEP] = SWEEP_EDITS

report, problems, planned = [], [], {}
CRLF = {}
cut_log = {}


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


def norm(sel):
    return ' '.join(sel.replace('\n', ' ').split())


def style_blocks(text):
    """(start, end) of every <style> block's CONTENTS.

    The cut below must never see markup. Five of the six pages carry a
    `<span class="btn-row-edit-disabled">` in the table, and a cutter
    loose in the whole file would have to be trusted not to touch it.
    It is not trusted; it is not shown it.
    """
    return [(m.start(1), m.end(1)) for m in
            re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S | re.I)]


def rules_in(css):
    """(selector, start, end, body) for every rule at ANY depth.

    Depth matters: four of the six pages put their full-width rule inside
    `@media screen and (max-width: 768px)`, and a cutter that only looked
    at the top level found none of them.
    """
    out = []
    stack = []
    run = 0
    for m in re.finditer(r'[{}]', css):
        i = m.start()
        if m.group(0) == '{':
            # The RAW run decides where the rule starts on the page; the
            # comment-stripped copy decides what the selector SAYS. Using
            # the stripped length against the raw offset left a stray "/"
            # behind on the three pages whose rule is written
            # `/* Edit button */ .btn-row-edit {` - caught by --check.
            raw = css[run:i]
            sel = re.sub(r'/\*.*?\*/', '', raw, flags=re.S)
            stack.append((sel, run + len(raw) - len(raw.lstrip()), i))
            run = i + 1
        else:
            if stack:
                sel, a, br = stack.pop()
                out.append((norm(sel), a, i + 1, css[br + 1:i]))
            run = i + 1
    return out


def cut_rule(text, selector):
    """Remove ONE rule whose selector list is exactly `selector`.

    Anchored on the selector and brace-matched, inside the <style> blocks
    only, so nothing else in the file is touched - no reflowing and no
    blank-line collapsing anywhere (lesson 16: a patcher that tidies the
    whole file has left its scope).
    Returns (new_text, removed_declarations) or (None, reason).
    """
    want = norm(selector)
    hits = []
    for s, e in style_blocks(text):
        css = text[s:e]
        for sel, a, b, body in rules_in(css):
            if sel == want:
                hits.append((s + a, s + b, body))
    if len(hits) != 1:
        return None, '%r matched %d time(s)' % (want, len(hits))
    a, b, body = hits[0]
    # Take the newline the rule sat on, and nothing else.
    while b < len(text) and text[b] in ' \t':
        b += 1
    if b < len(text) and text[b] == '\n':
        b += 1
    return text[:a] + text[b:], ' '.join(body.split())


def css_selectors(text):
    """Every selector in this page's <style> blocks, and nothing else."""
    out = []
    for s, e in style_blocks(text):
        out += [sel for sel, _a, _b, _body in rules_in(text[s:e])]
    return out


# --- A: base takes the pill ---------------------------------------------
if not os.path.isfile(BASE):
    problems.append('%s not found' % BASE)
else:
    b = read(BASE)
    if 'ALV ROW PILL v1' in b:
        report.append('%-42s already holds the row pill' % 'base.html')
    elif b.count(PILL_ANCHOR) != 1:
        problems.append('base.html: the PILLS heading was found %d time(s)'
                        % b.count(PILL_ANCHOR))
    else:
        planned[BASE] = (b, b.replace(PILL_ANCHOR, PILL + PILL_ANCHOR, 1))
        report.append('%-42s + ALV ROW PILL v1' % 'base.html')

# --- A: the six give theirs up ------------------------------------------
for name in SIX:
    p = os.path.join(T, name)
    if not os.path.isfile(p):
        problems.append('%s not found' % p)
        continue
    src = read(p)
    # Asked of the page's SELECTORS, not of a substring: the two `-types`
    # pages keep a `.rev-type-card .btn-row-edit` rule, which contains the
    # string `.btn-row-edit,` and made a substring guard claim there was
    # still work to do on a page already finished.
    if not any(norm(sel) in [norm(x) for x in CUT[name]]
               for sel in css_selectors(src)):
        report.append('%-42s already gave up its copy' % name)
        continue
    cur, removed, bad = src, [], False
    for sel in CUT[name]:
        out, info = cut_rule(cur, sel)
        if out is None:
            problems.append('%s: %s' % (name, info))
            bad = True
            continue
        cur, _ = out, None
        removed.append((norm(sel), info))
    if bad:
        continue
    left = [s for s in css_selectors(cur) if 'btn-row' in s]
    want_left = [KEEPS[name]] if name in KEEPS else []
    if [x.split(',')[0].strip() for x in left] != want_left:
        problems.append('%s: after the cut these btn-row rules are left: %s '
                        '(expected %s)'
                        % (name, [x[:44] for x in left], want_left))
        continue
    planned[p] = (src, cur)
    cut_log[name] = removed
    report.append('%-42s gives up %d rule(s)%s'
                  % (name, len(removed),
                     ', keeps its card rule' if name in KEEPS else ''))

# --- B and C: the buttons -----------------------------------------------
WHY = {CFF: 'its three modal-footer buttons are decided',
       ASSET: 'Open File is the primary on that card',
       TPD: 'the toolbar link is a house secondary, not a toggle',
       PL: 'the third Select All pair joins the other two',
       SWEEP: 'LATER: the sweep judges its round on what it left'}
for path in (CFF, ASSET, TPD, PL, SWEEP):
    if not os.path.isfile(path):
        problems.append('%s not found' % path)
        continue
    src = read(path)
    cur, n, done = src, 0, 0
    for old, new in EDITS[path]:
        # `old` gone is the test for "already applied", not `new` present:
        # a replacement can legitimately appear elsewhere in the file.
        if old not in cur:
            done += 1
            continue
        if cur.count(old) != 1:
            problems.append('%s: anchor found %d time(s): %r'
                            % (path, cur.count(old), old.strip()[:56]))
            continue
        cur = cur.replace(old, new, 1)
        n += 1
    if n:
        planned[path] = (src, cur)
        report.append('%-42s %s (%d edit(s))'
                      % (os.path.basename(path), WHY[path], n))
    elif done == len(EDITS[path]):
        report.append('%-42s already done' % os.path.basename(path))

# --- C: the tool ---------------------------------------------------------
if not os.path.isfile(DRIFT):
    problems.append('%s not found' % DRIFT)
else:
    src = read(DRIFT)
    cur, n, done = src, 0, 0
    for old, new in DRIFT_EDITS:
        if new and new in cur:
            done += 1
            continue
        if not new and old not in cur:
            done += 1
            continue
        if cur.count(old) != 1:
            problems.append('%s: anchor found %d time(s)'
                            % (DRIFT, cur.count(old)))
            continue
        cur = cur.replace(old, new, 1)
        n += 1
    if n:
        try:
            compile(cur, DRIFT, 'exec')
        except SyntaxError as e:
            problems.append('%s would not compile: line %s' % (DRIFT, e.lineno))
        planned[DRIFT] = (src, cur)
        report.append('%-42s three LEAVEs become DECIDED secondaries (%d)'
                      % (DRIFT, n))
    elif done == len(DRIFT_EDITS):
        report.append('%-42s already updated' % DRIFT)

# --- self-checks: what the round must NOT have done ---------------------
for path, (src, cur) in list(planned.items()):
    name = os.path.basename(path)
    if name in CUT:
        for word in ('#28a745', '#dc3545', '#a71d2a', '#6c757d'):
            near = [ln for ln in cur.split('\n')
                    if word in ln and 'btn-row' in ln]
            if near:
                problems.append('%s: %s still sits on a btn-row rule'
                                % (name, word))
        if src.count('class="btn-row') != cur.count('class="btn-row'):
            problems.append('%s: the MARKUP changed - this round moves CSS '
                            'only' % name)
        if cur.count('{') != cur.count('}'):
            problems.append('%s: braces are unbalanced after the cut' % name)
    if path == BASE:
        for word in ('#28a745', '#dc3545', '#a71d2a'):
            if word in cur and word not in src:
                problems.append('base.html: %s was introduced' % word)
    if path in (CFF, ASSET, TPD, PL) and path is not SWEEP:
        for tone in ('btn btn-info', 'btn btn-secondary',
                     'btn btn-outline-secondary'):
            if tone in cur:
                problems.append('%s: %r is still on the page this round '
                                'says it retoned' % (name, tone))
        if path is PL and 'btn-sm' in cur:
            problems.append('%s: a .btn-sm is left behind' % name)

# --- registered, and on the gate ----------------------------------------
if os.path.isfile(ROUNDS_FILE):
    r = read(ROUNDS_FILE)
    if "'%s'" % SUFFIX in r:
        report.append('%-42s already lists this round' % ROUNDS_FILE)
    elif r.count("    '.bak_three',\n]") != 1:
        problems.append('%s: cannot find the end of ROUNDS (.bak_three) - '
                        'apply_small_three.py first' % ROUNDS_FILE)
    else:
        planned[ROUNDS_FILE] = (r, r.replace(
            "    '.bak_three',\n]", "    '.bak_three',\n    '%s',\n]" % SUFFIX,
            1))
        report.append('%-42s learns %s' % (ROUNDS_FILE, SUFFIX))
else:
    problems.append('%s missing' % ROUNDS_FILE)

GATE_NOTE = """    # Section D round D3: base owns the labelled row action, the last
    # four script-built buttons are decided, and three stale LEAVE
    # reasons are gone,
    'test_row_actions.py'"""
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-42s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        if not m:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            planned[PS1] = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-42s + %s' % (PS1, SUITE))
else:
    problems.append('%s missing' % PS1)

print('\n' + '=' * 78)
print('SECTION D, ROUND D3 - THE ROW PILL COMES HOME - %s'
      % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 78)
for line in report:
    print('  ' + line)
if cut_log:
    print('\n  WHAT EACH PAGE HANDED OVER, declaration by declaration:')
    for name in SIX:
        for sel, body in cut_log.get(name, []):
            print('    %-30s %-46s %s'
                  % (name[:30], sel[:46], body[:70]))
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
