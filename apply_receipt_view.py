# -*- coding: utf-8 -*-
"""apply_receipt_view.py - round RV-1, 23 Oct 2026.

G2: THE RECEIPT HAS NO SCREEN THAT SHOWS THE RECORD.

Outstanding since 16 October, described then as "the Physical Invoice
detail shape without the PDF" and never built. Re-measured on 23
October before building it, and the description had drifted:

  - the receipts list HAS had a LOOK action since RC-1 - the pdf icon
    opens the receipt through components/pdf_viewer.html;
  - CashReceipt HAS a pdf_file, so "without the PDF" is not true;
  - and an Edit screen exists and owns changing a receipt.

SO THE GAP IS NARROWER THAN THE NOTE SAID, and it is real. The PDF
shows the receipt AS ISSUED. Nothing in this application shows the
RECORD BEHIND IT:

    who voided it, when, and why
    who edited it and when - the list shows a badge, not a name
    when it was emailed
    the property it relates to
    the payment method and the bank reference
    the payer's address, telephone and email

Every one of those is a column on CashReceipt that no screen reads.
void_reason in particular is captured, stored, and has never once been
displayed anywhere.

READ ONLY, ON PURPOSE. Edit owns changing a receipt. A second screen
that could also change one is a second code path for one job, which is
the rule that kept store_display_jpeg to a single caller in SD-1.

THE HISTORY IS BUILT IN THE VIEW, not in four template branches - the
same reasoning RG-1 used for the printed sheet's heading. A template
that decides which events happened cannot be asked how many it drew,
and this round's suite asks exactly that.

NO ROUTE TO IT YET, AND THAT IS DELIBERATE. IR-1 makes the receipt
number a link to this page, in the same push. A screen built in one
round and reached in the next is two claims that can each be checked;
one round doing both is one claim that cannot say which half failed.

NO MIGRATION. Every field this screen reads already exists.

Idempotent. Every file backed up to .bak_receiptview.
"""
import os
import re
import sys

SUFFIX = '.bak_receiptview'
VIEWS = os.path.join('pages', 'views', 'receipts.py')
URLS = os.path.join('pages', 'urls.py')
TPL = os.path.join('pages', 'templates', 'cash_receipt_detail.html')
PS1 = 'Push-PendingChanges.ps1'
# D-1's BAR CENSUS, which this round moves.
#
# test_bar_height pins the number of controls in .page-action-buttons
# across the whole tree so the set cannot grow unnoticed. This round
# adds a PAGE, and its bar carries three: View receipt, Edit, Back.
# 267 -> 270, and the pin moves with the round that moved it rather
# than being relaxed.
BARH = 'test_bar_height.py'
# RC-1's ROUTE CENSUS, which this round also moves.
#
# test_cash_receipts NAMES the receipt routes rather than counting
# them - "because a count tells you something changed and not which",
# which is the right instinct and is why this edit is a name and not a
# number. It also checks each one is EXPORTED, which is exactly the
# __all__ fault this round hit on 23 October.
RC = 'test_cash_receipts.py'
# NV-1d's SUITE, which reads D-1's pin with an over-tight regex.
#
# test_customer_view asks whether the TABLE-ROW count is at least 114,
# and reads it with `N_BAR, N_ROW, N_MODAL = 267, (\\d+), 95` - which
# pins the BAR count and the MODAL count incidentally, neither of
# which it is asking about. Moving N_BAR from 267 to 270 made that
# regex miss and the claim fail on a number it does not care about.
#
# The claim is loosened to the shape, not relaxed: it still requires
# the row count and still requires the floor. Same lesson as the
# migration leaf yesterday - print the measurement, assert the shape.
# THREE SUITES DO THIS, NOT ONE - measured 23 October. Each asks
# about the TABLE-ROW count and each reads it with a regex that pins
# N_BAR at 267 and N_MODAL at 95 incidentally. Fixing them one sweep
# cycle at a time would have cost three more full sweeps.
CV = ('test_customer_view.py', 'test_deed_table.py',
      'test_notify_icon.py')
# AND BL-2's BACK-LABEL CENSUS. A new page brings a new Back, and the
# Back carries the house label span, so the tree-wide count moves by
# exactly one. 127 -> 128.
HL = 'test_help_label.py'
# AND THE HOUSE-TITLE CENSUS, which is kept in TWO places on purpose.
#
# test_house_title pins the number of templates wearing
# .page-title-h2, and base.html's own note states the same number -
# "the sentence above is the one thing keeping the two honest".
#
# THEY ARE NOT HONEST TODAY. The suite says 121 and base says 120:
# PP-1 moved the suite on 20 October when meal_plan_print joined, and
# left the note behind. This round adds a page, so both move to 122 -
# and the note is repaired on the way past rather than left saying a
# number nothing in the tree agrees with.
HT = 'test_house_title.py'
# AND J-2's JS-ESCAPE CENSUS, in the patcher that owns it.
#
# This round's screen carries three {{ ... |escapejs }} interpolations
# in the onclick that opens the PDF viewer, so TOTAL moves 192 -> 195.
#
# AND SO DOES ALREADY_SAFE, 45 -> 48, WHICH LOOKS WRONG AND IS NOT.
# That number is "how many already carried the filter BEFORE J-2 ran",
# and the suite reads the before-state through the backup of each file.
# A file a round CREATES has no backup for J-2's suffix, so the reader
# falls through to the live file - and this screen is therefore counted
# on both sides of the census. It is the honest consequence of adding a
# correct file rather than fixing an incorrect one.
JS = 'apply_js_escape.py'
# AND E11's BUTTON-SCANNER CENSUS, four numbers on two lines.
#
# A new PAGE joins both halves of the page count, and its three
# onclick controls join both scanner totals. PP-1's note says the
# narrow half "does not move" - that was true of meal_plan_print,
# which sits outside the sweep scope. This screen is an ordinary
# pages/templates page, so it joins the scope too.
JB = 'test_js_buttons.py'
# AND PH-2's LEAD-CARD PIN, 3 -> 4.
#
# The nearest precedent decides this. asset_detail.html - the screen
# this one is modelled on - carries .alv-card-lead on its first card
# AND a .page-title-h2, so a detail screen with a title does take one.
# The suite's WCIM exception is about a CHOOSER page whose h1 already
# names the screen, which is a different shape.
PH = 'test_panel_heads.py'
# AND RS-1b's SCOPE PIN - the same two numbers as the button census,
# 117 of 142, written out a second time in a second suite. Both move.
RT = 'test_recipe_tones.py'
# AND RS-1b's OTHER SUITE, which keeps the SAME two numbers in a named
# pair. 117 of 142 is now written in four places across three suites;
# both of its uses here come off this one constant.
RSB = 'test_recipe_side_b.py'
# AND H7's TEMPLATE WALK - a different pair of numbers for the same
# cause. 151 across both roots and every subdirectory, 125 in the flat
# pages/templates listing. A new page in pages/templates moves both.
ST = 'test_subtree_tones.py'
# AND X0's TREE SHAPE - MAIN_N, the pages/templates count that every
# other total in that suite is derived from. One constant, three
# claims downstream of it.
TR = 'test_tree_roots.py'
BASET = os.path.join('pages', 'templates', 'base.html')
ME = 'test_receipt_view.py'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'RV-1, 23 Oct 2026'
CHECK = False

# THE SCREEN SHIPS WITH THE ROUND. A template is a file, not a string
# in a patcher - the same rule LK-1 used for alv_plant.py and SI-1 for
# check_recipe_files.py.
CREATES = (TPL,)

# ==========================================================================
# THE VIEW
# ==========================================================================
V_WAS = '''@login_required
@permission_required('auth.can_access_receipts', raise_exception=True)
def cash_receipt_pdf(request, cash_receipt_id):'''

V_NOW = '''@login_required
@permission_required('auth.can_access_receipts', raise_exception=True)
def cash_receipt_detail(request, cash_receipt_id):
    """The RECORD behind the receipt. RV-1, 23 Oct 2026 - G2.

    NOT the document. The pdf icon in the list has opened the receipt
    itself since RC-1, through the same shared viewer this page
    includes. What no screen in this application has ever shown is
    what is stored ABOUT the receipt: who voided it and why, who
    edited it and when, when it was emailed, the property, the method,
    the bank reference, and the payer's address, telephone and email.

    void_reason is the clearest case. It is captured when a receipt is
    voided, it is stored, and before this screen it was never
    displayed anywhere at all.

    READ ONLY. cash_receipt_edit owns changing a receipt; a second
    screen that could also change one is a second code path for one
    job.

    can_access_receipts, NOT can_edit_receipts - the same permission
    the list and the PDF take. Reading the record is reading.
    """
    r = get_object_or_404(
        CashReceipt.objects.select_related(
            'tenant', 'customer', 'prop', 'created_by', 'edited_by',
            'voided_by'),
        pk=cash_receipt_id)

    # THE HISTORY IS BUILT HERE, not in four template branches.
    #
    # OLDEST FIRST, so it reads downward the way the receipt's life
    # ran. Each event is included only if it HAPPENED - an absent
    # edited_at is not "edited: never", it is not an event.
    #
    # A NAME OR NOTHING. created_by is SET_NULL, so a deleted user
    # leaves a row whose author is genuinely unknown; printing
    # "by None" would be a lie dressed as a fact.
    def _who(user):
        if not user:
            return ''
        return user.get_full_name() or user.get_username()

    trail = []
    if r.created_at:
        trail.append({'what': 'Issued', 'when': r.created_at,
                      'who': _who(r.created_by), 'note': '',
                      'tone': ''})
    if r.sent_at:
        trail.append({'what': 'Emailed', 'when': r.sent_at,
                      'who': '', 'note': '', 'tone': ''})
    if r.edited_at:
        trail.append({'what': 'Edited', 'when': r.edited_at,
                      'who': _who(r.edited_by),
                      'note': 'Any copy already sent shows the '
                              'previous details.',
                      'tone': ''})
    if r.voided_at:
        trail.append({'what': 'Voided', 'when': r.voided_at,
                      'who': _who(r.voided_by),
                      'note': r.void_reason or '',
                      'tone': 'void'})
    trail.sort(key=lambda e: e['when'])

    return render(request, 'cash_receipt_detail.html', {
        'r': r,
        'trail': trail,
        # THE SAME TWO THE LIST ROW USES, from the same helper - a
        # second idea about what a void receipt is called is a second
        # thing to keep in agreement.
        'symbol': money_symbol(r.currency),
        'status_pill': 'alv-pill-neutral' if r.is_void else 'alv-pill-good',
        'status_display': 'Void' if r.is_void else 'Issued',
    })


@login_required
@permission_required('auth.can_access_receipts', raise_exception=True)
def cash_receipt_pdf(request, cash_receipt_id):'''

# ==========================================================================
# AND THE NAME HAS TO LEAVE THE MODULE
# ==========================================================================
# pages/views/__init__.py does `from .receipts import *` so the URLconf
# can say views.<name>. A wildcard import obeys __all__, and
# receipts.py has one - so a view that is not listed there DOES NOT
# EXIST as far as the URLconf is concerned.
#
# Found the hard way on 23 October: the round applied cleanly, every
# gate passed, and `reverse('cash_receipt_detail')` raised
# AttributeError on a module that plainly contained the function.
A_WAS = '''    "cash_receipt_pdf",
    "render_cash_receipt_pdf",'''

A_NOW = '''    "cash_receipt_pdf",
    # RV-1, 23 Oct 2026. __init__.py re-exports this module with
    # `import *`, which obeys __all__ - so a view missing from this
    # list is invisible to the URLconf no matter how correct it is.
    "cash_receipt_detail",
    "render_cash_receipt_pdf",'''

# ==========================================================================
# THE ROUTE
# ==========================================================================
U_WAS = '''    path("receipts/<int:cash_receipt_id>/void/", views.cash_receipt_void, name="cash_receipt_void"),'''

U_NOW = '''    # RV-1, 23 Oct 2026 - the record behind the receipt. G2.
    path("receipts/<int:cash_receipt_id>/", views.cash_receipt_detail, name="cash_receipt_detail"),
    path("receipts/<int:cash_receipt_id>/void/", views.cash_receipt_void, name="cash_receipt_void"),'''


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('RV-1 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pv = os.path.join(root, VIEWS)
    v = read(pv)
    if MARK in v:
        print('RV-1  already applied - the receipt has a screen that '
              'shows the record.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # THE SCREEN IS A FILE, NOT A STRING IN HERE.
    pt = os.path.join(root, TPL)
    if not os.path.isfile(pt):
        refuse('%s is not on disk, and this round wires it up' % TPL)

    # EVERYTHING THE VIEW LEANS ON MUST ALREADY BE IN THAT MODULE.
    for want in ('def money_symbol', 'get_object_or_404', 'CashReceipt'):
        if want not in v:
            refuse('%s: %s is not there, and the new view uses it'
                   % (VIEWS, want))

    v = swap(v, V_WAS, V_NOW, '%s (the detail view)' % VIEWS)
    v = swap(v, A_WAS, A_NOW, '%s (__all__)' % VIEWS)
    out[pv] = v

    pu = os.path.join(root, URLS)
    out[pu] = swap(read(pu), U_WAS, U_NOW, '%s (the route)' % URLS)

    # AND RC-1'S ROUTE CENSUS LEARNS THE NINTH ROUTE.
    prc = os.path.join(root, RC)
    out[prc] = swap(
        read(prc),
        """             'cash_receipt_unvoid', 'cash_receipt_pdf'}""",
        """             'cash_receipt_unvoid', 'cash_receipt_pdf',
             # RV-1, 23 Oct 2026 - the record behind the receipt. G2.
             'cash_receipt_detail'}""",
        '%s (the route census)' % RC)

    # AND THE THREE SUITES STOP PINNING NUMBERS THEY DO NOT ASK ABOUT.
    NOTE = ('# THE ROW COUNT, NOT THE OTHER TWO - RV-1, 23 Oct 2026.\n'
            '# This read `= 267, (\\d+), 95`, pinning the BAR and MODAL\n'
            '# counts incidentally. RV-1 adds a page whose bar carries\n'
            '# three controls, N_BAR moved 267 -> 270, and the claim\n'
            '# failed on a number it does not care about.\n')
    for name in CV:
        pcv = os.path.join(root, name)
        src = read(pcv)
        for var in ('_r', '_n'):
            old = ("%s = re.search(r'N_BAR, N_ROW, N_MODAL = 267, "
                   "(\\d+), 95', bh)" % var)
            if old in src:
                src = swap(src, old,
                           NOTE + ("%s = re.search(r'N_BAR, N_ROW, "
                                   "N_MODAL = \\d+, (\\d+), \\d+', bh)"
                                   % var),
                           '%s (the row-count regex)' % name)
                break
        else:
            refuse('%s: no row-count regex of the expected shape' % name)
        out[pcv] = src

    # AND J-2'S JS-ESCAPE CENSUS, BOTH OF ITS NUMBERS.
    pjs = os.path.join(root, JS)
    js = read(pjs)
    jm = re.search(r'(?m)^ALREADY_SAFE = (\d+)', js)
    if not jm:
        refuse('%s: ALREADY_SAFE is not where this round expects it'
               % JS)
    js = swap(js, 'ALREADY_SAFE = %s' % jm.group(1),
              'ALREADY_SAFE = %d   # RV-1, 23 Oct 2026 - plus the three '
              'in cash_receipt_detail.html. A CREATED file has no '
              'backup for this suffix, so the before-reader falls '
              'through to the live file and the screen counts on both '
              'sides.   # (was %s)' % (int(jm.group(1)) + 3, jm.group(1)),
              '%s (ALREADY_SAFE)' % JS)
    # AND X0'S TREE SHAPE.
    ptr2 = os.path.join(root, TR)
    tr = read(ptr2)
    mm = re.search(r'(?m)^MAIN_N = (\d+)', tr)
    if not mm:
        refuse('%s: MAIN_N is not where this round expects it' % TR)
    out[ptr2] = swap(
        tr, 'MAIN_N = %s' % mm.group(1),
        'MAIN_N = %d   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. '
        'This is the shape of the tree, which is what this file is '
        'for.   # (was %s)' % (int(mm.group(1)) + 1, mm.group(1)),
        '%s (MAIN_N)' % TR)

    # AND H7'S TEMPLATE WALK, BOTH HALVES.
    pst = os.path.join(root, ST)
    st = read(pst)
    st = swap(st, "ok(len(tree) == 151, 'a WALK finds 151 templates', "
                  "len(tree))",
              "# RV-1, 23 Oct 2026 - 152, 126. cash_receipt_detail.html\n"
              "# sits flat in pages/templates, so it joins the walk and\n"
              "# the flat listing alike.\n"
              "ok(len(tree) == 152, 'a WALK finds 152 templates', "
              "len(tree))",
              '%s (the walk count)' % ST)
    st = swap(st, "ok(len(top) == 125, '  a flat listing finds 125 - 120 "
                  "was what H7 '",
              "ok(len(top) == 126, '  a flat listing finds 126 - 120 was "
              "what H7 '",
              '%s (the flat count)' % ST)
    out[pst] = st

    # AND THE SAME PAIR ONCE MORE, AS A NAMED CONSTANT THIS TIME.
    prs = os.path.join(root, RSB)
    rs = read(prs)
    gm = re.search(r'GATE_WAS, GATE_NOW = (\d+), (\d+)', rs)
    if not gm:
        refuse('%s: GATE_WAS/GATE_NOW are not where this round expects '
               'them' % RSB)
    out[prs] = swap(
        rs, 'GATE_WAS, GATE_NOW = %s, %s' % (gm.group(1), gm.group(2)),
        'GATE_WAS, GATE_NOW = %d, %d   # RV-1, 23 Oct 2026 - '
        'cash_receipt_detail.html. The same pair as test_js_buttons '
        'and test_recipe_tones: an ordinary pages/templates page joins '
        'the sweep scope and the page count alike.   # (was %s, %s)'
        % (int(gm.group(1)) + 1, int(gm.group(2)) + 1,
           gm.group(1), gm.group(2)),
        '%s (the gate scope)' % RSB)

    # AND RS-1b'S SCOPE PIN, THE SAME TWO NUMBERS AGAIN.
    prt = os.path.join(root, RT)
    rt = read(prt)
    rt = swap(rt,
              'ok(len(sb.templates(False)) == 117 and '
              'len(sb.templates(True)) == 142,',
              '# RV-1, 23 Oct 2026 - 118 of 143. cash_receipt_detail is\n'
              '# an ordinary pages/templates page, so it joins the sweep\n'
              '# scope and the application count alike.\n'
              'ok(len(sb.templates(False)) == 118 and '
              'len(sb.templates(True)) == 143,',
              '%s (the scope pin)' % RT)
    rt = swap(rt, "'  which is %d of %d' % (117, 142),",
              "'  which is %d of %d' % (118, 143),",
              '%s (the scope message)' % RT)
    out[prt] = rt

    # AND PH-2'S LEAD-CARD PIN.
    pph = os.path.join(root, PH)
    out[pph] = swap(
        read(pph), 'ok(lead == 3,',
        '''# RV-1, 23 Oct 2026 - 4. cash_receipt_detail.html takes one on
# its first card, as asset_detail.html does: a DETAIL screen with a
# page title. The WCIM exception below is a chooser, which is not the
# same shape.
ok(lead == 4,''',
        '%s (the lead-card pin)' % PH)

    # AND E11'S BUTTON CENSUS, ALL FOUR NUMBERS.
    pjb = os.path.join(root, JB)
    jb = read(pjb)
    cm = re.search(r'CENSUS_NARROW, CENSUS_WIDE = (\d+), (\d+)', jb)
    hm = re.search(r'HITS_LOOSE, HITS_TIGHT = (\d+), (\d+)', jb)
    if not cm or not hm:
        refuse('%s: the button census pins are not where this round '
               'expects them' % JB)
    jb = swap(jb,
              'CENSUS_NARROW, CENSUS_WIDE = %s, %s'
              % (cm.group(1), cm.group(2)),
              'CENSUS_NARROW, CENSUS_WIDE = %d, %d   # RV-1, 23 Oct '
              '2026 - cash_receipt_detail.html. BOTH halves move: '
              'unlike meal_plan_print this is an ordinary '
              'pages/templates page, so it joins the sweep scope as '
              'well as the application count.   # (was %s, %s)'
              % (int(cm.group(1)) + 1, int(cm.group(2)) + 1,
                 cm.group(1), cm.group(2)),
              '%s (the page census)' % JB)
    jb = swap(jb,
              'HITS_LOOSE, HITS_TIGHT = %s, %s' % (hm.group(1),
                                                   hm.group(2)),
              'HITS_LOOSE, HITS_TIGHT = %d, %d   # RV-1, 23 Oct 2026 - '
              'the Receipt Details bar: View receipt, Edit and Back. '
              'Both matchers rise by the same three.   # (was %s, %s)'
              % (int(hm.group(1)) + 3, int(hm.group(2)) + 3,
                 hm.group(1), hm.group(2)),
              '%s (the scanner totals)' % JB)
    out[pjb] = jb

    # AND NOT A ROW IN EXPECT.
    #
    # EXPECT lists the files J-2 FIXED - each count is how many
    # interpolations it converted from unprotected to escaped, and the
    # suite adds EXPECT + ALREADY_SAFE and compares the sum with the
    # live tree. This screen was born with the filter, so it was never
    # unprotected and J-2 never fixed it. A row here counts it twice,
    # claims three more templates were repaired than were, and moves
    # "there were 147 unprotected before this round" to 150 - the
    # suite said all three of those at once when this was tried.
    out[pjs] = js

    # AND THE HOUSE-TITLE CENSUS, IN BOTH OF ITS PLACES.
    pht = os.path.join(root, HT)
    out[pht] = swap(
        read(pht),
        'ok(len(wearers) == 121,',
        '''# RV-1, 23 Oct 2026 - 122. cash_receipt_detail.html carries a
# .page-title-h2 like every other page with a title.
#
# AND base.html's NOTE SAID 120 WHEN THIS ROUND ARRIVED, against 121
# here. PP-1 moved this pin on 20 October and left the sentence
# behind, so the two numbers the comment above calls "the one thing
# keeping the two honest" had been disagreeing for three days. Both
# say 122 now.
ok(len(wearers) == 122,''',
        '%s (the title census)' % HT)
    out[pht] = out[pht].replace(
        "'121 templates now wear the class, which is the number base\\'s note '",
        "'122 templates now wear the class, which is the number base\\'s note '")

    pbt = os.path.join(root, BASET)
    out[pbt] = swap(
        read(pbt),
        '''      h2.page-title-h2 and h4.page-subtitle-h4 and styles neither. 120 pages
      do - 122 until MN-1 retired four meal-plan screens on 18 Oct 2026,
      three of which wore it, and the planner that replaced them wears
      it too.''',
        '''      h2.page-title-h2 and h4.page-subtitle-h4 and styles neither. 122 pages
      do. It was 122 before 18 Oct 2026, then 120 when MN-1 retired four
      meal-plan screens, three of which wore it, and the planner that
      replaced them wears it too; meal_plan_print joined on 20 Oct and
      cash_receipt_detail on 23 Oct.

      THIS SENTENCE SAID 120 UNTIL 23 Oct 2026 while test_house_title
      said 121 - PP-1 moved the suite and left the note. The two are
      meant to keep each other honest and for three days neither did.''',
        '%s (the title note)' % BASET)

    # AND BL-2'S BACK-LABEL CENSUS LEARNS THE NEW PAGE'S BACK.
    phl = os.path.join(root, HL)
    hl = read(phl)
    hm = re.search(r'LABELS_TOTAL = (\d+)', hl)
    if not hm:
        refuse('%s: LABELS_TOTAL is not where this round expects it'
               % HL)
    out[phl] = swap(
        hl, 'LABELS_TOTAL = %s' % hm.group(1),
        'LABELS_TOTAL = %d   # RV-1, 23 Oct 2026 - the Receipt Details '
        'Back. A new PAGE, and a house Back carries the label span '
        'base hides on a phone, so the tree-wide count moves by '
        'exactly one.   # (was %s)'
        % (int(hm.group(1)) + 1, hm.group(1)),
        '%s (the back-label census)' % HL)

    # AND D-1'S CENSUS LEARNS THE THREE NEW CONTROLS.
    pbh = os.path.join(root, BARH)
    bh = read(pbh)
    bm = re.search(r'N_BAR, N_ROW, N_MODAL = (\d+), (\d+), (\d+)', bh)
    if not bm:
        refuse('%s: the bar census pin is not where this round expects '
               'it' % BARH)
    out[pbh] = swap(
        bh,
        'N_BAR, N_ROW, N_MODAL = %s, %s, %s'
        % (bm.group(1), bm.group(2), bm.group(3)),
        'N_BAR, N_ROW, N_MODAL = %d, %s, %s   # RV-1, 23 Oct 2026 - '
        'the Receipt Details bar: View receipt, Edit and Back. A new '
        'PAGE, so three controls join the census without any existing '
        'bar changing.   # (was %s)'
        % (int(bm.group(1)) + 3, bm.group(2), bm.group(3), bm.group(1)),
        '%s (the bar census)' % BARH)

    # ---- REGISTRATION
    pg = os.path.join(root, PS1)
    g = read(pg)
    g = swap(g, """    'test_print_origin.py'
)""", """    'test_print_origin.py',
    # RV-1, 23 Oct 2026 - the receipt has a screen that shows the
    # record, not only the document. G2, outstanding since 16 Oct.
    'test_receipt_view.py'
)""", '%s (the suites)' % PS1)
    g = swap(g,
             """    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             """    @{ File = 'pages/views/receipts.py'; Text = 'def cash_receipt_detail'; What = 'RV-1: the PDF shows the receipt as issued; nothing showed the record behind it. void_reason was captured, stored, and never once displayed anywhere in the application' },
    @{ File = 'pages/templates/cash_receipt_detail.html'; Text = 'rv-trail'; What = 'RV-1: and the history is built in the VIEW, oldest first, each event present only if it happened - a template that decides which events occurred cannot be asked how many it drew' },
    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             '%s (the sentinels)' % PS1)
    out[pg] = g

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # PT-1, 22 Oct 2026 - the print sheet knows which view sent it.
    'test_print_origin.py',
]""", """    # PT-1, 22 Oct 2026 - the print sheet knows which view sent it.
    'test_print_origin.py',
    # RV-1, 23 Oct 2026 - the receipt has a screen for its record.
    'test_receipt_view.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_printorigin',
]""", """    '.bak_printorigin',
    # RV-1, 23 Oct 2026 - the receipt has a screen for its record.
    '.bak_receiptview',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # RV-1, 23 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nv = T.python_code_only(out[pv], payloads=True)

    # READ ONLY. A detail screen that can write is a second way to
    # change a receipt, and cash_receipt_edit is the first.
    body = nv[nv.index('def cash_receipt_detail'):]
    nxt = re.search(r'\n@login_required', body[1:])
    body = body[:nxt.start() + 1] if nxt else body
    for writes in ('.save(', '.delete(', '.update(', '.create(',
                   'request.POST'):
        if writes in body:
            refuse('%s: cash_receipt_detail names %r. It reads a record; '
                   'cash_receipt_edit owns changing one' % (VIEWS, writes))

    # THE PERMISSION IS THE READING ONE.
    #
    # ASKED OF THE LINES ABOVE THE def, not of the body: a decorator
    # sits before the function it guards, and the first version of
    # this gate sliced from `def` and so could never see it. It
    # refused the round for a permission that was there.
    at = nv.index('def cash_receipt_detail')
    above = nv[max(0, at - 220):at]
    if 'can_access_receipts' not in above:
        refuse('%s: the detail view is not guarded by '
               'can_access_receipts' % VIEWS)
    if 'login_required' not in above:
        refuse('%s: the detail view is not behind a login' % VIEWS)
    if 'can_edit_receipts' in body:
        refuse('%s: reading a receipt record asks for the EDIT '
               'permission, which locks a read-only screen behind a '
               'write right' % VIEWS)

    # AND THE NAME MUST BE EXPORTED, or the URLconf cannot see it.
    #
    # EVERY receipts view the URLconf names, not just this round's -
    # the fault is general and the gate costs nothing to make general.
    # A missing entry raises AttributeError the moment anybody opens
    # the page, and nothing before this check would have caught it.
    all_m = re.search(r'__all__ = \[(.*?)\]', nv, re.S)
    if not all_m:
        refuse('%s: no __all__, so the wildcard re-export in '
               '__init__.py has nothing to obey' % VIEWS)
    exported = set(re.findall(r'"(\w+)"', all_m.group(1)))
    urlconf = out[os.path.join(root, URLS)]
    named = set(re.findall(r'views\.(cash_receipt_\w+)', urlconf))
    unexported = sorted(n for n in named if n not in exported)
    if unexported:
        refuse('%s: the URLconf names %s, and __all__ does not export '
               'them - `from .receipts import *` obeys __all__, so the '
               'view does not exist as far as the URLconf is concerned'
               % (VIEWS, ', '.join(unexported)))

    # THE HISTORY IS BUILT HERE AND SORTED.
    if 'trail' not in body or 'trail.sort(' not in body:
        refuse('%s: the history is not built and ordered in the view'
               % VIEWS)
    # AND void_reason REACHES IT - the one field this whole round is
    # about, and the one nothing has ever displayed.
    if 'void_reason' not in body:
        refuse('%s: void_reason is not read, and it is the field that '
               'has been stored and never shown' % VIEWS)

    # THE TEMPLATE MUST BALANCE - SB-2's lesson, 22 Oct 2026. A tag
    # inside a comment a text gate reads as a comment is still a tag.
    tpl = T.code_only(read(pt))
    for a, b in (('if', 'endif'), ('for', 'endfor'),
                 ('block', 'endblock')):
        o = len(re.findall(r'{%%\s*%s\b' % a, tpl))
        c = len(re.findall(r'{%%\s*%s\b' % b, tpl))
        if o != c:
            refuse('%s: %d {%% %s %%} against %d {%% %s %%}'
                   % (TPL, o, a, c, b))

    # AND IT MUST SET A TAB TITLE - test_heading_prefix's rule.
    # The first draft of this screen had no title block and the sweep
    # said "1 of 116 bad": every page that extends base sets one, and
    # a detail screen with no title is a browser tab that cannot tell
    # itself from any other.
    if '{% block title %}' not in tpl:
        refuse('%s: no {%% block title %%}, so the browser tab falls '
               'back to whatever base says' % TPL)

    # NO BARE max-width - test_print_queries' rule, and this round
    # arrived with one. A bare max-width block fires on PAPER as well
    # as on a phone, because print has a narrow effective width, so
    # the one-column phone layout leaks into every printed copy. A
    # print-leak round fixed 98 of these across the tree; this screen
    # was very nearly the 99th and only the sweep said so.
    for m in re.finditer(r'@media\s*([^{]+)\{', tpl):
        clause = m.group(1).strip()
        if 'max-width' in clause and 'screen' not in clause:
            refuse('%s: `@media %s` is bare, so it fires on paper too. '
                   'The house spelling is `@media screen and '
                   '(max-width: 768px)`' % (TPL, clause))

    # AND IT MUST NOT ADD A TENTH .detail-row.
    #
    # Nine templates each define their own and base defines none -
    # measured 23 October. A tenth copy of a name that already means
    # nine slightly different things makes a system-wide problem worse
    # to save one round's work.
    if re.search(r'\.detail-(row|label|value|group)\s*\{', tpl):
        refuse('%s: it defines a .detail-* component. Nine templates '
               'already do and base does none; promoting it is its own '
               'round. This page owns an rv-* prefix instead' % TPL)

    # ONE BAR, AND BACK IS LAST IN IT - base 3.4.
    bar = tpl[tpl.find('page-action-buttons'):]
    bar = bar[:bar.find('</div>')]
    if tpl.count('page-action-buttons') != 1:
        refuse('%s: %d action bars. One per page.'
               % (TPL, tpl.count('page-action-buttons')))
    if 'action-back' not in tpl:
        refuse('%s: the page has no Back' % TPL)
    if tpl.index('action-back') < tpl.rindex('action-secondary'):
        refuse('%s: Back is not the last control in the bar' % TPL)

    if CHECK:
        print('RV-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        plus %s, which this round CREATES' % TPL)
        print('        the receipt has a screen that shows the record')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('RV-1  applied - the receipt has a screen that shows the '
          'record, not only the document.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      plus %s, which this round CREATES' % TPL)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
