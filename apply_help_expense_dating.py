#!/usr/bin/env python3
"""
apply_help_expense_dating.py
============================

Bring the Expenses help in line with what the screens now do.

Three modules live in pages/help_content/configuration.html:

    finance_expense_types        Expense Types
    finance_expense_line_types   Expense Line Types
    finance_expense              Expenses

Each gains one new tab covering effective dating and the new delete choice,
inserted before its Tips tab so Tips stays last.

Three existing statements are also CORRECTED, because they now describe
behaviour that no longer exists:

  1. elt-prorata: "Deleting a Pro-Rata Line Type cascades hard. Every Expense
     record ... is deleted." - it now offers stop-from-a-date as well.

  2. exp-prorata step 6: un-ticked properties have "their Expense records
     removed" - they are now zeroed and snapshotted, so earlier years keep
     their figures.

  3. exp-prorata edit mode: "deletes all original pro-rata records and
     recreates them" - that was the bug that orphaned the Company Tax history.
     Rows are now matched and updated in place.

Leaving those in place would be worse than having no help at all: they would
tell someone to expect the old behaviour and, in case 3, describe the very
defect that was fixed.

Idempotent; backs the file up on first run (.bak_helpdating).

    python apply_help_expense_dating.py [--check]
"""

import os
import re
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))
HELP = os.path.join(ROOT, 'pages', 'help_content', 'configuration.html')

SENTINEL = 'data-tab-slug="exp-dating"'


# ---------------------------------------------------------------------------
# Corrections to statements that are no longer true
# ---------------------------------------------------------------------------

FIX_1_OLD = """      <li><strong>Deleting a Pro-Rata Line Type cascades hard.</strong> Every Expense record on every property using this Line Type is deleted. The Confirm Delete modal lists all of them &mdash; read carefully.</li>"""

FIX_1_NEW = """      <li><strong>Deleting a Pro-Rata Line Type asks what you mean.</strong> The Confirm Delete modal lists every linked Expense and then offers two options: <em>Stop these expenses from a date</em> (they are zeroed from that date, earlier years keep their real figures, and the Line Type is kept because those rows still point at it) or <em>Remove the line type and everything on it</em> (the Line Type, its Expenses and their history are all deleted, so past years stop showing them). See the <em>Dates &amp; Deleting</em> tab.</li>"""

FIX_2_OLD = """      <li>For properties that <strong>were previously included but are now un-ticked</strong> (Edit mode only) &rarr; their Expense records are <strong>removed</strong> as part of the recalculation</li>"""

FIX_2_NEW = """      <li>For properties that <strong>were previously included but are now un-ticked</strong> (Edit mode only) &rarr; their Expense records are <strong>zeroed from the "Applies from" date</strong>, not deleted. The row stays, showing 0, so every earlier year keeps the share that property genuinely carried. The freed share is taken up by the properties still ticked.</li>"""

FIX_3_OLD = """      <li>On <strong>Confirm &amp; Update</strong>, the system <strong>deletes all original pro-rata records</strong> for this Line Type+Type combination and <strong>recreates them</strong> based on the new selection. This is how it cleanly handles additions, removals, and amount changes in one operation.</li>"""

FIX_3_NEW = """      <li>On <strong>Confirm &amp; Update</strong>, the system <strong>matches each existing record and updates it in place</strong>. Records are only created for properties genuinely new to the distribution, and un-ticked ones are zeroed rather than deleted. This matters: each Expense record carries its own history, and history is tied to the record. Deleting and recreating the rows &mdash; which is what this screen used to do &mdash; broke that link and cost three years of Company Tax figures.</li>"""


# ---------------------------------------------------------------------------
# 1. Expense Types - how the month pattern meets the effective date
# ---------------------------------------------------------------------------

ET_ANCHOR = '  <article data-tab-slug="et-tips"\n'

ET_TAB = '''  <article data-tab-slug="et-dating"
           data-tab-name="Timing &amp; Dates"
           data-tab-icon="fa-calendar-day">
    <h5 style="color:#17a2b8; font-weight:700;"><i class="fas fa-calendar-day"></i> How the timing pattern meets the "Applies from" date</h5>
    <p>Every change to a budgeted figure now carries an <strong>Applies from</strong> date. The Expense Type decides <em>which months hold the money</em>; the date decides <em>from which month the new figure counts</em>. The two work together, and that combination surprises people the first time.</p>

    <div class="alert" style="background:#e7f5f8; border-left:4px solid #17a2b8;">
      <strong>The rule, in one line</strong>
      <p class="mb-0 mt-2">A new figure applies to every <strong>payment month on or after</strong> the Applies from date. Payment months <strong>before</strong> it keep whatever applied previously.</p>
    </div>

    <h6 style="margin-top:20px; color:#2c3e50; font-weight:700;"><i class="fas fa-flask"></i> A one-month type: the surprise</h6>
    <p><em>Financials (Cyprus)</em> uses the <strong>June</strong> Expense Type &mdash; the whole annual amount sits in the June cell. Suppose the audit fee rises from &euro;2,810 to &euro;3,000 and you make that change on <strong>22 August 2026</strong>, leaving the date as today:</p>
    <ul>
      <li>June 2026 has already passed, so it keeps <strong>&euro;2,810</strong></li>
      <li>June 2027 is the first payment month on or after the date, so it takes <strong>&euro;3,000</strong></li>
      <li><strong>2026 therefore still reads &euro;2,810</strong> and 2027 onward reads &euro;3,000</li>
    </ul>
    <p>That is usually right &mdash; the 2026 invoice really was &euro;2,810. But if the increase applies to the 2026 audit, date the change <strong>1 January 2026</strong> (any date up to June works) so the June cell picks it up.</p>

    <h6 style="margin-top:20px; color:#2c3e50; font-weight:700;"><i class="fas fa-flask"></i> A twelve-month type: the year splits</h6>
    <p>A <strong>Monthly</strong> type behaves differently. Change &euro;100 a month to &euro;120 effective 1 August 2026 and that year reads:</p>
    <ul>
      <li>January to July at <strong>&euro;100</strong> = &euro;700</li>
      <li>August to December at <strong>&euro;120</strong> = &euro;600</li>
      <li>2026 total <strong>&euro;1,300</strong>; 2027 onward &euro;1,440</li>
    </ul>
    <p>Nothing is lost or invented &mdash; the year is simply a blend of the two rates, which is what actually happened.</p>

    <h6 style="margin-top:20px; color:#2c3e50; font-weight:700;"><i class="fas fa-info-circle"></i> Details worth knowing</h6>
    <ul>
      <li><strong>Only the month matters, not the day.</strong> A change dated the 3rd and one dated the 27th of the same month behave identically. A figure cannot change mid-month.</li>
      <li><strong>A figure carries forward forever</strong> until another change supersedes it. There is no "end date" &mdash; to make something apply for one year only, enter a second change dated the following January.</li>
      <li><strong>Changing the Expense Type rewrites which months carry the amount.</strong> The new pattern's months take the figure and every other month is cleared, so switching Quarterly to Monthly is a real change to the year's shape, not a label swap.</li>
      <li><strong>Dates can be in the past or the future.</strong> Backdating inserts a period between two existing ones without disturbing anything after it, and you can enter next year's figure in advance.</li>
    </ul>
  </article>

'''


# ---------------------------------------------------------------------------
# 2. Expense Line Types - the date on an amount change, and deleting
# ---------------------------------------------------------------------------

ELT_ANCHOR = '  <article data-tab-slug="elt-tips"\n'

ELT_TAB = '''  <article data-tab-slug="elt-dating"
           data-tab-name="Dates &amp; Deleting"
           data-tab-icon="fa-calendar-day">
    <h5 style="color:#17a2b8; font-weight:700;"><i class="fas fa-calendar-day"></i> Dating a Pro-Rata Amount change</h5>
    <p>For a Pro-Rata Line Type, this page is the <strong>only</strong> place the figure can be changed &mdash; Expense Amount is locked on the Expense record itself. So this is where the effective date has to be set, and an <strong>Applies from</strong> box appears the moment you alter the Pro-Rata Amount.</p>

    <div class="alert" style="background:#e7f5f8; border-left:4px solid #17a2b8;">
      <strong>It only appears when it is needed</strong>
      <p class="mb-0 mt-2">Renaming a Line Type or editing its Description changes no figures, so no date is asked for. Change the <strong>Pro-Rata Amount</strong> on a Line Type that has linked Expenses and the box appears, because that change cascades to every one of them.</p>
    </div>

    <h6 style="margin-top:20px; color:#2c3e50; font-weight:700;"><i class="fas fa-question-circle"></i> Which date should you use?</h6>
    <ul>
      <li><strong>Already invoiced this year at the old amount?</strong> Leave the date as today. A charge whose payment month has already passed keeps what it was billed at, and the new amount takes over next year.</li>
      <li><strong>This year is at the new amount?</strong> Date it <strong>1 January of this year</strong>, so the payment month picks it up.</li>
      <li><strong>Correcting a figure you keyed wrongly?</strong> Use the same date as the entry you are correcting &mdash; not today &mdash; or the wrong figure stays in the months before it.</li>
    </ul>
    <p>The date applies to <strong>every</strong> Expense the recalculation touches, which is the whole distribution.</p>

    <h5 style="margin-top:28px; color:#dc3545; font-weight:700;"><i class="fas fa-trash-alt"></i> Deleting a Line Type: two different things</h5>
    <p>The Confirm Delete modal lists every linked Expense and then asks which you mean. They are not two ways of doing one thing.</p>

    <div class="alert" style="background:#e7f5f8; border-left:4px solid #17a2b8;">
      <strong>Stop these expenses from a date</strong>
      <ul class="mb-0 mt-2">
        <li>Every linked Expense is <strong>zeroed from the date you choose</strong> and that zero is recorded</li>
        <li><strong>Earlier years keep their real figures</strong> &mdash; a 2024 P&amp;L still shows what 2024 actually cost</li>
        <li>The rows stay in the Expenses list showing 0, and the P&amp;L stops showing the line once every month is zero</li>
        <li><strong>The Line Type itself is kept.</strong> It has to be: those Expense rows carry the history and they point at it. It stays in your list holding nothing.</li>
      </ul>
    </div>

    <div class="alert" style="background:#fdeaec; border-left:4px solid #dc3545;">
      <strong>Remove the line type and everything on it</strong>
      <ul class="mb-0 mt-2">
        <li>The Line Type, its Expenses <strong>and their history</strong> are all deleted</li>
        <li><strong>Past years stop showing them too.</strong> A 2024 P&amp;L re-run afterwards will report less than 2024 actually cost</li>
        <li>For a Line Type that should never have existed &mdash; a duplicate, a typo, a test &mdash; not for something that has genuinely ended</li>
        <li>This cannot be undone</li>
      </ul>
    </div>

    <p><strong>The trade in one line:</strong> you can keep the past, or you can tidy the list, but not both. A Line Type sitting in the list with zeros against it is the honest record of something that used to cost money.</p>
    <p>A Line Type with <strong>no</strong> linked Expenses has no history to preserve, so it is simply deleted with no question asked.</p>
  </article>

'''


# ---------------------------------------------------------------------------
# 3. Expenses - the full picture
# ---------------------------------------------------------------------------

EXP_ANCHOR = '  <article data-tab-slug="exp-tips"\n'

EXP_TAB = '''  <article data-tab-slug="exp-dating"
           data-tab-name="Dates &amp; History"
           data-tab-icon="fa-calendar-day">
    <h5 style="color:#17a2b8; font-weight:700;"><i class="fas fa-history"></i> Every figure is dated</h5>
    <p>A budgeted Expense is not one number &mdash; it is a <strong>history of numbers, each with a date it took effect</strong>. When the P&amp;L is run for a year it asks, month by month, "what figure was in force then?" That is why a 2024 report keeps saying what 2024 cost even after this year's budget changes.</p>

    <p>Every Add and Edit form therefore carries an <strong>Applies from</strong> box.</p>

    <div class="alert" style="background:#e7f5f8; border-left:4px solid #17a2b8;">
      <strong>The two defaults, and why they differ</strong>
      <ul class="mb-0 mt-2">
        <li><strong>Adding</strong> &mdash; prefilled with <strong>1 January of the current year</strong>. A budget line is an annual thing; entering the 2026 budget in August almost always means it for the whole of 2026, not from August.</li>
        <li><strong>Editing</strong> &mdash; prefilled with <strong>today</strong>. A change takes effect when it takes effect.</li>
      </ul>
    </div>

    <h6 style="margin-top:20px; color:#2c3e50; font-weight:700;"><i class="fas fa-flask"></i> The same new expense, four different dates</h6>
    <p>&euro;100 a month, entered on 22 August 2026. Only the date typed in differs:</p>

    <table class="table table-sm table-bordered" style="font-size:0.85rem;">
      <thead style="background:#f8f9fa;">
        <tr><th>Applies from</th><th class="text-right">2024</th><th class="text-right">2025</th><th class="text-right">2026</th><th class="text-right">2027</th></tr>
      </thead>
      <tbody>
        <tr><td>1 Jan 2024 &mdash; catching up an expense that has been running</td><td class="text-right">1,200</td><td class="text-right">1,200</td><td class="text-right">1,200</td><td class="text-right">1,200</td></tr>
        <tr><td>1 Jan 2026 &mdash; this year's budget <em>(the default when adding)</em></td><td class="text-right">0</td><td class="text-right">0</td><td class="text-right">1,200</td><td class="text-right">1,200</td></tr>
        <tr><td>22 Aug 2026 &mdash; it genuinely starts now</td><td class="text-right">0</td><td class="text-right">0</td><td class="text-right">500</td><td class="text-right">1,200</td></tr>
        <tr><td>1 Jan 2027 &mdash; next year's budget, entered early</td><td class="text-right">0</td><td class="text-right">0</td><td class="text-right">0</td><td class="text-right">1,200</td></tr>
      </tbody>
    </table>

    <p>Four dates, four correct answers. Nothing appears in a year the expense did not exist in, and a backdated entry reaches exactly as far back as you tell it to.</p>

    <h6 style="margin-top:20px; color:#2c3e50; font-weight:700;"><i class="fas fa-info-circle"></i> What a change does <em>not</em> do</h6>
    <ul>
      <li><strong>It does not rewrite earlier years.</strong> Change a figure today and last year's P&amp;L is untouched &mdash; unless you deliberately backdate the change into it.</li>
      <li><strong>It does not change the day, only the month.</strong> Dated the 3rd or the 27th, the effect is the same.</li>
      <li><strong>It does not expire.</strong> A figure carries forward until another change supersedes it. For a one-year-only figure, enter a second change dated the following January.</li>
    </ul>

    <h5 style="margin-top:28px; color:#dc3545; font-weight:700;"><i class="fas fa-trash-alt"></i> Deleting: two different things</h5>
    <p>Because history only applies to rows that still exist, deleting a row removes it from <strong>every</strong> year, closed ones included. That is sometimes exactly right and sometimes badly wrong, so the Delete button asks.</p>

    <div class="alert" style="background:#e7f5f8; border-left:4px solid #17a2b8;">
      <strong>Stop it from a date</strong> &mdash; preselected
      <ul class="mb-0 mt-2">
        <li>For something that has genuinely ended: a service cancelled, a property sold, a charge that no longer applies</li>
        <li>The row is zeroed from the date you choose and that zero is recorded</li>
        <li><strong>Every earlier year keeps the figures it really had</strong></li>
        <li>The row stays in the Expenses list showing 0, and can be given an amount again later</li>
      </ul>
    </div>

    <div class="alert" style="background:#fdeaec; border-left:4px solid #dc3545;">
      <strong>Remove it completely</strong>
      <ul class="mb-0 mt-2">
        <li>For something that should never have been recorded: a duplicate, a mis-keyed row, a test entry</li>
        <li>The row <strong>and its history</strong> are deleted, so past years stop showing it too</li>
        <li>This cannot be undone</li>
      </ul>
    </div>

    <p>The dialog names the row and tells you how much history it carries &mdash; for example <em>"4 history snapshots, earliest Jan 2024"</em> &mdash; so the choice is informed. It always opens on the safe option, even if you chose the other one a moment earlier on a different row.</p>

    <h6 style="margin-top:20px; color:#2c3e50; font-weight:700;"><i class="fas fa-eye"></i> Where a stopped expense still shows</h6>
    <p>Stopping an expense from, say, September 2026 leaves it looking like this:</p>
    <ul>
      <li><strong>2024, 2025 P&amp;L</strong> &mdash; the line, with its real figures, unchanged</li>
      <li><strong>2026 P&amp;L</strong> &mdash; the line, with real amounts up to August and 0 afterwards</li>
      <li><strong>2027 onward</strong> &mdash; nothing. The P&amp;L hides a line whose months are all zero</li>
      <li><strong>The Expenses list</strong> &mdash; the row is still there at 0. It has to exist for 2024 and 2025 to keep their figures</li>
    </ul>

    <h5 style="margin-top:28px; color:#dc3545; font-weight:700;"><i class="fas fa-balance-scale"></i> Pro-Rata rows cannot be deleted</h5>
    <p>On a Pro-Rata line the Delete button is <strong>greyed out</strong>. This is deliberate, and it is not an inconvenience &mdash; it prevents a silent error.</p>

    <p>A pro-rata row is not a figure in its own right. It is a <strong>share</strong> of the amount held on the Line Type. Company Tax is &euro;3,300 an instalment sliced across ten properties, and nothing forces the slices to add back up to the whole. Delete one row and the other nine still hold shares calculated for a <strong>ten-way</strong> split &mdash; so the line quietly totals less than the tax actually owed, and no report flags it.</p>

    <div class="alert" style="background:#e7f5f8; border-left:4px solid #17a2b8;">
      <strong>Remove a property from a distribution by editing, not deleting</strong>
      <ol class="mb-0 mt-2">
        <li>Open <strong>Edit</strong> on any Expense in that distribution</li>
        <li>Set <strong>Applies from</strong> to the date the change takes effect</li>
        <li><strong>Un-tick</strong> the property you are removing</li>
        <li>Calculate and confirm</li>
      </ol>
    </div>

    <p>The result is the correct one on both sides: the removed property is <strong>zeroed from that date and keeps every earlier year</strong> &mdash; identical to "stop it from a date" &mdash; and the properties still ticked <strong>take up its share</strong>, so the charge stays whole.</p>

    <div class="alert alert-warning" style="border-left:4px solid #ffc107;">
      <i class="fas fa-exclamation-triangle"></i> <strong>The total stays the same.</strong> Un-ticking redistributes the existing amount; it does not reduce it. If the charge itself has changed &mdash; you sold the property and the bill genuinely dropped &mdash; change the Pro-Rata Amount on the Expense Line Type <em>first</em>, then un-tick.
    </div>

    <p>To remove a whole distribution rather than one property, delete the <strong>Line Type</strong>, which offers the same two choices for the entire group.</p>
  </article>

'''


# ---------------------------------------------------------------------------

def sniff(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return raw.decode(enc).replace('\r\n', '\n'), enc, nl


def main():
    if not os.path.exists(HELP):
        print('! %s not found - run from the project root'
              % os.path.relpath(HELP, ROOT))
        return 1

    src, enc, nl = sniff(HELP)

    if SENTINEL in src:
        print('= already applied - nothing to do')
        return 0

    problems = []

    def need(label, anchor, times=1):
        n = src.count(anchor)
        if n != times:
            problems.append('%s: matched %d times, expected %d' % (label, n, times))

    need('Expense Types tips tab', ET_ANCHOR)
    need('Line Types tips tab', ELT_ANCHOR)
    need('Expenses tips tab', EXP_ANCHOR)
    need('line-type cascade bullet', FIX_1_OLD)
    need('un-ticked properties bullet', FIX_2_OLD)
    need('delete-and-recreate bullet', FIX_3_OLD)

    # Each tips tab must sit inside the module it belongs to - the file holds
    # seven modules and an anchor in the wrong one would file the tab under
    # Revenue.
    for slug, anchor in (('finance_expense_types', ET_ANCHOR),
                         ('finance_expense_line_types', ELT_ANCHOR),
                         ('finance_expense', EXP_ANCHOR)):
        marker = 'data-module-slug="%s"' % slug
        if marker not in src:
            problems.append('%s: module section not found' % slug)
            continue
        start = src.index(marker)
        nxt = src.find('<section data-module-slug=', start + 1)
        end = nxt if nxt != -1 else len(src)
        if not (start < src.index(anchor) < end):
            problems.append('%s: its tips tab is outside the section' % slug)

    if problems:
        for p in problems:
            print('! ' + p)
        print('  Aborting - nothing written.')
        return 1

    src = src.replace(FIX_1_OLD, FIX_1_NEW, 1)
    src = src.replace(FIX_2_OLD, FIX_2_NEW, 1)
    src = src.replace(FIX_3_OLD, FIX_3_NEW, 1)
    src = src.replace(ET_ANCHOR, ET_TAB + ET_ANCHOR, 1)
    src = src.replace(ELT_ANCHOR, ELT_TAB + ELT_ANCHOR, 1)
    src = src.replace(EXP_ANCHOR, EXP_TAB + EXP_ANCHOR, 1)

    # Every <article> opened must be closed, or the help modal renders as soup.
    # Comments are stripped first: the header block documents the format with
    # two `<article data-tab-slug="...">` examples that are not tags.
    body = re.sub(r'<!--.*?-->', '', src, flags=re.S)
    opened = body.count('<article ')
    closed = body.count('</article>')
    if opened != closed:
        print('! article tags are unbalanced after the edit (%d open, %d close)'
              % (opened, closed))
        print('  Nothing written.')
        return 1

    if CHECK:
        print('= check only: every anchor matched, each tab lands in the right '
              'module and the article tags balance, nothing written')
        return 0

    bak = HELP + '.bak_helpdating'
    if not os.path.exists(bak):
        shutil.copy2(HELP, bak)
    with open(HELP, 'w', encoding=enc, newline='') as fh:
        fh.write(src.replace('\n', nl) if nl == '\r\n' else src)

    print('+ pages/help_content/configuration.html')
    print('    Expense Types       + "Timing & Dates"')
    print('    Expense Line Types  + "Dates & Deleting"')
    print('    Expenses            + "Dates & History"')
    print('    3 statements corrected that described the old behaviour')
    print('')
    print('Backup: .bak_helpdating. Open the Help modal on each of the three')
    print('screens and check the new tab appears before Tips.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
