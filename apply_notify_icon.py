# -*- coding: utf-8 -*-
"""apply_notify_icon.py - round NV-1c, 16 Oct 2026.

A VERB THE VOCABULARY DID NOT HAVE.

Demetri, after a full check of the Issues module:

  "On the Issues modules, in Comments, I think that I want to change the
   Edit and Notify Now Buttons to be inline with our standards. We have
   a standard for Edit. We will need to create a standard for Notify
   (maybe just a bell with a Notify Now hover)."

Both controls are labelled buttons on base's `.status-btn`, in a place
where the whole application draws `icon-action-btn` inside
`.row-actions`. He asked for icon-only, on every width, and that is what
this does.


NOTIFY IS ADVANCE, AND ITS COLOUR IS ALREADY DECIDED
============================================================================
`alv_rowactions.FAMILY` has no `notify`. It joins ADVANCE, beside `send`
- the record moves on - so Edit (CHANGE) sits before it and the strip
reads in the house order without anything being told what that order is.

AND THE ADVANCE FAMILY SPLITS BY CONSEQUENCE, which is the part that
decides the colour. base already says so:

    .icon-send                       accent    it goes out
    .icon-approve  .icon-unlock      good      it is now allowed
    .icon-unapprove .icon-lock
      .icon-reset-pw                 WARN      someone will notice

Notify Now emails everyone configured except the clicker, immediately,
with a five-minute cooldown per comment. That is the third group, and it
is the same reading the page reached page-locally in an earlier round -
amber ink on a quiet outline, because "this one has consequences".
`.icon-notify` is `.icon-lock`'s rule with a different name, so the page
stops carrying a private spelling of a house decision.

AND IT TAKES ITS OWN NAME RATHER THAN BORROWING .icon-lock, because a
class carries ONE PICTURE: .icon-lock is fa-user-slash. base states that
rule four times in the block this round writes into, and .icon-edit had
already broken it once.


WHY base AND NOT THE PAGE
============================================================================
The earlier round put the Notify TONE on the page on purpose, and said
why: "PAGE-LOCAL BECAUSE THERE IS ONE ASKER... If a second page wants a
cautioning inline button, that is when this becomes .status-btn-warn in
base."

That reasoning held for a BUTTON variant. It does not hold for a
ROW-ACTION ICON: all forty-one `.icon-*` classes live in base, and
`Show-RowActionDrift` and `alv_rowactions` read those names as the shared
vocabulary. A forty-second living on one page would be the drift the
vocabulary exists to prevent, and the page's own private rule would then
be the second spelling.

So the page-local pair goes, and `#ecd9a8` goes with it. After this
round `fsr_details.html` SPELLS NO COLOUR BY HAND AT ALL - it was the
one page in the application with a standing hex exception, recorded in
two suites, and the round that owns the decision is the one allowed to
retire it. Both of those suites are re-pointed here, by this patcher,
because a round that falsifies a claim fixes the claim.


TWO THINGS THAT WERE CHECKED RATHER THAN ASSUMED                 MEASURED
============================================================================
1. `.row-actions` IS SAFE ON A PHONE. base declares it once at top level
   - `display: inline-flex` - and once more inside `@media print`, and
   NOT in the 768px block. The 768px block hides `.desktop-action-cell`
   and shows `.mobile-action-bar`, which is a TABLE pattern; a comment
   thread is not a table and keeps its strip at every width, which is
   what icon-only on every width requires.

2. THE SCRIPT WRITES INTO THE BUTTON. `btn.innerHTML = 'Sending...'` put
   a nine-character word inside what is now a 44px square. It writes a
   spinning glyph instead. The failure paths restore `originalLabel`,
   which is read before the swap and is now the bell, so they needed
   nothing.

THE THREE JS HOOKS SURVIVE UNTOUCHED. `comment-edit-btn`,
`notify-urgent-btn` and `notify-urgent-cell` are how the script finds
these controls; they are kept on the elements beside the new house
classes. The classes that find are not the classes that paint.


AND ITEM FIVE OF THE SAME BATCH, WHICH IS A NOTE AND NOT A FEATURE
============================================================================
  "In the Actions Column of the Physical Invoices, should we not have the
   ability to duplicate an Invoice, like we have the ability to duplicate
   a receipt?"

It is there, and `test_invoice_order` has pinned it since it shipped: a
draft customer invoice draws pdf, duplicate, approve, delete. It is
absent on TENANT rows because

    unique_together = [('tenant', 'period_year', 'period_month')]

makes a tenant invoice unique per tenant per month, so a copy dated today
collides with the month the prepare cron already bills. The view refuses
it in as many words. Customer invoices have `tenant = NULL` and NULLs are
never equal to each other, which is the one case the constraint permits -
that is WHY the guard exists rather than an oversight.

Demetri's ruling: drop it, and say why on the screen. So a tenant row
draws the house DISABLED MIRROR - the pattern the action columns already
use for a permission the reader lacks - titled with the reason. The
column reads one width on every row and the asymmetry reads as
deliberate.

THE MIRROR IS THE DESKTOP STRIP'S ALONE. An action COLUMN should read
one width per row; the phone bar is a grid that sizes to its children,
so a disabled cell there buys nothing. That is why the duplicate action
appears TWICE on this page and the mirror once.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alv_tree

code_only = alv_tree.code_only
python_code_only = alv_tree.python_code_only

SUFFIX = '.bak_notifyicon'
BASE = 'base.html'
PAGE = 'fsr_details.html'
IPAGE = 'physical_invoice_list.html'
RA = 'alv_rowactions.py'
ME = 'test_notify_icon.py'
PATCHER = 'apply_notify_icon.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
BH = 'test_bar_height.py'
AM = 'test_amber.py'
FP = 'test_fsr_palette.py'
NB = 'test_notify_btns.py'
CHECK = False

CONVERTED_WAS, CONVERTED_NOW = 86, 87
ALIAS_WAS, ALIAS_NOW = 83, 85
ALIAS_P_WAS, ALIAS_S_WAS = 41, 42
ALIAS_P_NOW, ALIAS_S_NOW = 42, 43

# THE CENSUS. The two comment controls were .status-btn, which
# test_bar_height does not select; as icon-action-btns they join it. They
# sit in no table, so they land in the LOOSE set, and the physical
# invoice mirror lands in the TABLE ROW set.
ROW_WAS_N, ROW_NOW_N = 112, 113
LOOSE_WAS_N, LOOSE_NOW_N = 81, 83

# ---------------------------------------------------------------- base
ICON_ANCHOR = """.icon-unlock       { color: var(--alv-good); border-color: var(--alv-good-line); }
.icon-unlock:hover { background-color: var(--alv-good); border-color: var(--alv-good); color: var(--alv-on-accent); }
.icon-color-unlock { color: var(--alv-good); }"""

ICON_NEW = ICON_ANCHOR + """

/* Notify: THE ADVANCE FAMILY SPLITS BY CONSEQUENCE, added by NV-1c on
   16 Oct 2026 after Demetri asked for a standard for Notify - "maybe
   just a bell with a Notify Now hover".

   WHY --alv-warn AND NOT THE ACCENT. The three tones above are not
   decoration: .icon-send is accent because the thing goes out,
   .icon-approve and .icon-unlock are good because something becomes
   allowed, and .icon-unapprove, .icon-lock and .icon-reset-pw are warn
   because SOMEBODY WILL NOTICE. Notify Now emails everyone configured
   except the clicker, immediately, with a five-minute cooldown per
   comment. It is the third group.

   And fsr_details had already reached that reading on its own, in a
   page-local rule, in as many words: amber ink on a quiet outline
   because this one has consequences. This is that decision moved to
   where the other forty-one live, not a new one.

   WHY ITS OWN NAME AND NOT .icon-lock, whose rule this is byte for
   byte: A CLASS CARRIES ONE PICTURE. .icon-lock is fa-user-slash; this
   is fa-bell. base states that rule beside .icon-upload,
   .icon-document, .icon-reset-pw and .icon-permissions, and .icon-edit
   had already broken it once.         [test_icon_buttons.py 1b] */
.icon-notify       { color: var(--alv-warn); border-color: var(--alv-warn-line); }
.icon-notify:hover { background-color: var(--alv-warn); border-color: var(--alv-warn); color: var(--alv-on-accent); }
.icon-color-notify { color: var(--alv-warn); }"""

# --------------------------------------------------------- alv_rowactions
RA_WAS = """    'unlock': ADVANCE, 'permissions': ADVANCE, 'reset-pw': ADVANCE,"""

RA_NOW = """    'unlock': ADVANCE, 'permissions': ADVANCE, 'reset-pw': ADVANCE,
    # NV-1c, 16 Oct 2026 - Notify Now emails everyone configured except
    # the clicker. The record moves on, so ADVANCE, beside send - and
    # Edit is CHANGE, so the comment strip reads edit-then-notify
    # without the markup being told that.
    'notify': ADVANCE,"""

# --------------------------------------------------------- fsr_details
EDIT_WAS = """                                        {% if idresults.issues_details_user == user_initials and not idresults.issues_details_last_notified_at %}
                                        <button type="button" class="comment-edit-btn status-btn"
                                                data-comment-id="{{ idresults.issues_details_id }}"
                                                data-comment-text="{{ idresults.issues_details_comment|default:'' }}"
                                                onclick="openEditCommentModal(this)"
                                                title="Edit your comment">
                                            <i class="fas fa-pencil-alt"></i> Edit
                                        </button>
                                        {% endif %}
                                        <span class="notify-urgent-cell" data-comment-id="{{ idresults.issues_details_id }}">
                                            {% if idresults.is_in_urgent_cooldown %}
                                                <span class="notified-badge alv-pill alv-pill-neutral">Notified {{ idresults.urgent_cooldown_minutes_ago }} min ago</span>
                                            {% else %}
                                                <button type="button" class="notify-urgent-btn status-btn" data-comment-id="{{ idresults.issues_details_id }}"><i class="fas fa-bell"></i> Notify Now</button>
                                            {% endif %}
                                        </span>"""

EDIT_NOW = """                                        <span class="row-actions">
                                        {% if idresults.issues_details_user == user_initials and not idresults.issues_details_last_notified_at %}
                                        <button type="button" class="comment-edit-btn icon-action-btn icon-edit"
                                                data-comment-id="{{ idresults.issues_details_id }}"
                                                data-comment-text="{{ idresults.issues_details_comment|default:'' }}"
                                                onclick="openEditCommentModal(this)"
                                                title="Edit your comment"
                                                aria-label="Edit your comment">
                                            <i class="fas fa-pencil-alt"></i>
                                        </button>
                                        {% endif %}
                                        <span class="notify-urgent-cell" data-comment-id="{{ idresults.issues_details_id }}">
                                            {% if idresults.is_in_urgent_cooldown %}
                                                <span class="notified-badge alv-pill alv-pill-neutral">Notified {{ idresults.urgent_cooldown_minutes_ago }} min ago</span>
                                            {% else %}
                                                <button type="button" class="notify-urgent-btn icon-action-btn icon-notify" data-comment-id="{{ idresults.issues_details_id }}" title="Notify Now" aria-label="Notify Now"><i class="fas fa-bell"></i></button>
                                            {% endif %}
                                        </span>
                                        </span>"""

CSS_WAS = """   ONE RULE STAYS, and it is a TONE rather than a component. Notify Now
   sends a notification, so it should not look identical to a button that
   opens a text box - but it was a SOLID slab of #ffc107, written inline on
   the element, and amber means "needs attention" in five other places
   here: --alv-warn, .alv-pill-attn, .alv-age-2, .alv-grade-4 and the
   flagged stat tile. #ffc107 is not even base's warn, which is #8e6207.
   Amber INK on a quiet outlined button says "this one has consequences"
   while leaving the colour's meaning intact.

   PAGE-LOCAL BECAUSE THERE IS ONE ASKER. base has twice declined to build
   on one, most recently two days ago when a compact stat density was
   proposed, approved, built and then dropped after measuring. If a second
   page wants a cautioning inline button, that is when this becomes
   .status-btn-warn in base. Written in base's tokens either way. */
.notify-urgent-btn.status-btn {
    color: var(--alv-warn);
    border-color: #ecd9a8;
}
.notify-urgent-btn.status-btn:hover {
    background: var(--alv-warn-soft);
    color: var(--alv-warn);
}"""

CSS_NOW = """   NV-1c, 16 Oct 2026 - AND NOW NO RULE STAYS. The page declares no
   colour at all any more, and no appearance for either control.

   The rule that used to sit here was right about the TONE and wrong
   about the place. It said: amber ink on a quiet outline, because this
   one has consequences - and it said PAGE-LOCAL BECAUSE THERE IS ONE
   ASKER, with the condition for promoting it written down: "if a second
   page wants a cautioning inline button, that is when this becomes
   .status-btn-warn in base."

   That condition has not happened, and this round does not pretend it
   has. What changed is the SHAPE. Demetri asked for these two to be
   icon-only, inline with our standards, and a ROW-ACTION ICON is not an
   inline button variant: all forty-one .icon-* classes live in base, and
   Show-RowActionDrift and alv_rowactions read those names as the shared
   vocabulary. A forty-second living on this page would be exactly the
   drift that vocabulary exists to prevent.

   So the tone went to base as .icon-notify - .icon-lock's rule under
   its own name, because a class carries one picture - and #ecd9a8 went
   with it. This page now spells NO hex by hand, which test_amber and
   test_fsr_palette both recorded as a standing exception and are
   re-pointed by this round's patcher.

   .comment-edit-btn, .notify-urgent-btn, .notified-badge and
   .notify-urgent-cell carry NO appearance - they are JS hooks and
   nothing else, and they are kept on the elements beside the house
   classes. The classes that find are not the classes that paint. */"""

JS_WAS = """        var originalLabel = btn.innerHTML;
        btn.innerHTML = 'Sending...';"""

JS_NOW = """        var originalLabel = btn.innerHTML;
        // NV-1c, 16 Oct 2026 - a spinning glyph, not a nine-character
        // word: the button is a 44px square now. originalLabel is read
        // on the line above, so it is the bell, and the three failure
        // paths below restore it unchanged.
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';"""

# ------------------------------------------------- physical_invoice_list
MIRROR_WAS = """              {% if perms.auth.can_edit_invoices and row.is_customer %}
                <form method="post" action="{% url 'customer_invoice_duplicate' row.pk %}" class="pi-inline-form"
                      onsubmit="return confirm('Create a new draft copy of this invoice, dated today?');">
                  {% csrf_token %}
                  <button type="submit" class="icon-action-btn icon-duplicate" title="Duplicate as new draft">
                    <i class="fas fa-copy"></i>
                  </button>
                </form>
              {% endif %}"""

MIRROR_NOW = """              {% if perms.auth.can_edit_invoices and row.is_customer %}
                <form method="post" action="{% url 'customer_invoice_duplicate' row.pk %}" class="pi-inline-form"
                      onsubmit="return confirm('Create a new draft copy of this invoice, dated today?');">
                  {% csrf_token %}
                  <button type="submit" class="icon-action-btn icon-duplicate" title="Duplicate as new draft">
                    <i class="fas fa-copy"></i>
                  </button>
                </form>
              {% elif perms.auth.can_edit_invoices %}
                {# NV-1c, 16 Oct 2026 - Demetri asked why a physical invoice #}
                {# cannot be duplicated like a receipt. A CUSTOMER one can, #}
                {# and has since it shipped. A TENANT one cannot: #}
                {# unique_together on (tenant, period_year, period_month) #}
                {# makes it one per tenant per month, so a copy dated today #}
                {# collides with the month the prepare cron already bills. #}
                {# Customer invoices have tenant = NULL and NULLs are never #}
                {# equal, which is the one case the constraint permits. #}
                {# The house disabled mirror, so the column reads one width #}
                {# on every row and the asymmetry reads as deliberate. #}
                <span class="icon-action-btn icon-disabled"
                      title="Duplicate is for customer invoices only - a tenant invoice is one per tenant per month">
                  <i class="fas fa-copy"></i>
                </span>
              {% endif %}"""

# ------------------------------------------------------------- re-points
AM_WAS = """head('8. ANOTHER ROUND DECIDED #ecd9a8, AND B-4 DOES NOT OVERTURN IT')"""

AM_NOW = """head('8. B-4 LEFT #ecd9a8 ALONE, AND NV-1C RETIRED IT')"""

AM_CLAIM_WAS = """    ok('#ecd9a8' in T.code_only(read(fsr)),
       "fsr_details.html still spells #ecd9a8 by hand - the Notify round's "
       'page-local warn tint, decided deliberately')"""

AM_CLAIM_NOW = """    # NV-1c, 16 Oct 2026 - THE ROUND THAT OWNED THAT DECISION RETIRED
    # IT. B-4's restraint is still the point of this section and still
    # asserted below: it did not touch the page, and it named the
    # literal on its leave list with the reason. What changed is that
    # the Notify round came back, moved its tone into base as
    # .icon-notify - because a row-action icon is not an inline button
    # variant - and took #ecd9a8 with it. fsr_details now spells NO hex
    # by hand at all, which is strictly better than the exception this
    # section was written to protect.
    ok('#ecd9a8' not in T.code_only(read(fsr)),
       'fsr_details.html spells no hex by hand at all - NV-1c moved the '
       "Notify tone into base as .icon-notify and took the page's tint "
       'with it')"""

FP_WAS = """    allowed = ['#ecd9a8'] if 'details' in name else []"""

FP_NOW = """    # NV-1c, 16 Oct 2026 - NO EXCEPTION ANY MORE. fsr_details kept
    # ONE literal, the Notify round's page-local warn tint. That round
    # came back on 16 Oct, moved its tone into base as .icon-notify and
    # took #ecd9a8 with it, so both pages now spell nothing by hand.
    allowed = []"""

FP_CLAIM_WAS = """check('the Notify round\\'s warn tint is untouched', '#ecd9a8' in DNC)
check('  and its buttons still carry base\\'s inline button',
      DNC.count('status-btn') >= 2)"""

FP_CLAIM_NOW = """# NV-1c, 16 Oct 2026 - the Notify round retired its own tint when
# Demetri asked for its two controls to be icon-only. B-4 never touched
# it; the round that owned it did.
check('the Notify round retired its own page-local tint',
      '#ecd9a8' not in DNC)
check('  and its two controls are row-action icons now, not inline '
      'buttons', DNC.count('icon-action-btn') >= 2
      and 'status-btn' not in DNC)"""


# ------------------------------------- the superseded round's own suite
# test_notify_btns is the suite of the round whose page-local tone this
# one retires, and it REFUSES outright when the markup it was written
# for is gone: `if 'notify-urgent-btn status-btn' not in F: sys.exit(1)`.
# It is on the gate, so leaving it refusing is not an option.
#
# EVERY CLAIM IT MAKES IS STILL TRUE. Notify is not a slab; it carries
# warn ink; the two controls are the same shape and differ only by
# consequence; the three JS hooks survive with no appearance attached.
# What moved is WHERE the tone is declared - base, as .icon-notify -
# so the suite is re-pointed at the new class and keeps its reasoning,
# its .bak_notify control and its render.
NB_GUARD_WAS = """if 'notify-urgent-btn status-btn' not in F:
    print('\\n! not patched - run apply_notify_btns.py first.')
    sys.exit(1)"""

NB_GUARD_NOW = """# NV-1c, 16 Oct 2026 - THE CLASS MOVED, THE CLAIMS DID NOT. Demetri
# asked for these two controls to be icon-only, and a row-action icon is
# not an inline button variant: all forty-one .icon-* classes live in
# base, so the tone went there as .icon-notify and this page stopped
# carrying a private spelling of it. Every check below still asks what
# it asked; it asks it of icon-action-btn instead of status-btn.
if 'notify-urgent-btn icon-action-btn icon-notify' not in F:
    print('\\n! not patched - run apply_notify_btns.py and then '
          'apply_notify_icon.py first.')
    sys.exit(1)"""

NB_HEX_WAS = """check("CONTROL: the round's prose still names #ffc107", '#ffc107' in F)
check('CONTROL: .. and it is gone once stripped', '#ffc107' not in FC)"""

NB_HEX_NOW = """# NV-1c re-pointed the literal this control uses. #ffc107 left the
# prose with the rule that quoted it; #ecd9a8 is named in NV-1c's own
# comment, as the tint it retired, and is the hex this page now carries
# in prose and nowhere else. The control's purpose is unchanged: the
# stripper must remove a comment and leave the code.
check("CONTROL: the round's prose still names #ecd9a8", '#ecd9a8' in F)
check('CONTROL: .. and it is gone once stripped', '#ecd9a8' not in FC)"""

NB_PAIR_WAS = """, 'comment-edit-btn status-btn' in FC)"""

NB_PAIR_NOW = """,
      'comment-edit-btn icon-action-btn icon-edit' in FC)"""

NB_PAIR2_WAS = """check('Notify Now is too', 'notify-urgent-btn status-btn' in FC)"""

NB_PAIR2_NOW = """check('Notify Now is too, and base names the verb',
      'notify-urgent-btn icon-action-btn icon-notify' in FC)"""

NB_TONE_WAS = """check('the warn tone is written in TOKENS',
      'var(--alv-warn)' in F and 'var(--alv-warn-soft)' in F)
check('  and is page-local, since base has one asker',
      '.status-btn-warn' not in FC and '.notify-urgent-btn.status-btn' in F)"""

NB_TONE_NOW = """check('the warn tone is written in TOKENS, in BASE',
      'var(--alv-warn)' in BC and '.icon-notify' in BC)
check('  and the page declares no tone at all any more - the condition '
      'this round set for promoting it was a SECOND page wanting a '
      'cautioning inline button, and that still has not happened; what '
      'changed is that a row-action icon is not a button variant',
      '.status-btn-warn' not in BC
      and '.notify-urgent-btn.status-btn' not in F)"""

NB_FIX_WAS = """    AFTER = ('<button class="comment-edit-btn status-btn" id="e">Edit</button>'
             '<button class="notify-urgent-btn status-btn" id="n">Notify Now</button>'"""

NB_FIX_NOW = """    AFTER = ('<button class="comment-edit-btn icon-action-btn icon-edit"'
             ' id="e"><i class="fas fa-pencil-alt"></i></button>'
             '<button class="notify-urgent-btn icon-action-btn icon-notify"'
             ' id="n"><i class="fas fa-bell"></i></button>'"""

NB_HOOK_WAS = """check('  except the one TONE, which is the point',
      '.notify-urgent-btn.status-btn {' in FC)"""

NB_HOOK_NOW = """check('  and now with NO exception - the tone that used to sit here '
      'is base .icon-notify, so all four hook names carry no '
      'appearance whatever',
      not re.search(r'(?m)^\.notify-urgent-btn', FC))"""

# ------------------------------------------------------------- registers
SENT_ANCHOR = """    # -------------------------------------------- HL-1, 12 Oct 2026"""

SENT_NEW = """    # ------------------------------------------------ NV-1c, 16 Oct 2026
    # Demetri asked for Edit and Notify Now in the Issues comments to be
    # icon-only, and for a standard for Notify - a bell with a Notify
    # Now hover. ADVANCE splits by consequence, so the bell is warn.
    @{ File = 'pages\\templates\\base.html'; Text = '.icon-notify'; What = 'Notify is in the shared icon vocabulary, not on one page' },
    @{ File = 'alv_rowactions.py'; Text = "'notify': ADVANCE"; What = 'and the vocabulary sorts it after Edit without the markup saying so' },
    @{ File = 'pages\\templates\\fsr_details.html'; Text = 'status-btn'; Absent = $true; Code = $true; What = 'the two comment controls are icon-only at every width' },
    @{ File = 'pages\\templates\\physical_invoice_list.html'; Text = 'Duplicate is for customer invoices only'; What = 'and a tenant invoice says on screen why it has no copy' },
    # -------------------------------------------- HL-1, 12 Oct 2026"""

SUITE_WAS = """    'test_deed_table.py'
)"""

SUITE_NOW = """    'test_deed_table.py',
    'test_notify_icon.py'
)"""

TREE_WAS = """    'test_deed_table.py',
]"""

TREE_NOW = """    'test_deed_table.py',
    # NV-1c, 16 Oct 2026 - Notify joins the icon vocabulary as an ADVANCE
    # that someone will notice, and the two comment controls go
    # icon-only. Wide from birth.
    'test_notify_icon.py',
]"""

ROUNDS_WAS = """    '.bak_deedtable',
]"""

ROUNDS_NOW = """    '.bak_deedtable',
    # NV-1c, 16 Oct 2026 - .icon-notify in base, 'notify': ADVANCE in the
    # vocabulary, the two fsr_details comment controls icon-only, the
    # page's last hand-spelled colour retired, and a tenant invoice row
    # that says why it cannot be duplicated.
    '.bak_notifyicon',
]"""


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
    raise SystemExit('NV-1c REFUSED: %s' % msg)


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


def swap(text, was, now, where):
    once(text, was, where)
    return text.replace(fit(text, was), fit(text, now), 1)


def bump(text, lit, was, now, note, where):
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


def css_of(t):
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style\s*>', t, re.S))


def js_of(t):
    return '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script\s*>', t, re.S))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    base = alv_tree.path_of(BASE)
    page = alv_tree.path_of(PAGE)
    ipage = alv_tree.path_of(IPAGE)

    # ---------------------------------------------------------------- 0
    # ALREADY APPLIED, asked of base's own rule rather than of any word
    # this file's docstring also carries.
    if re.search(r'(?m)^\.icon-notify\s+\{', css_of(read(base))):
        print('NV-1c  already applied - .icon-notify is in base.')
        return 0

    out = {}

    # ---------------------------------------------------------------- 1
    # .row-actions MUST BE SAFE AT EVERY WIDTH, which is what icon-only
    # on every width rests on. Asserted against base, live.
    bsrc = read(base)
    bcss = css_of(code_only(bsrc))
    def block(css, opener):
        """The contents of one at-rule, brace matched."""
        m = re.search(opener, css)
        if not m:
            return None
        depth, j = 1, m.end()
        while depth and j < len(css):
            if css[j] == '{':
                depth += 1
            elif css[j] == '}':
                depth -= 1
            j += 1
        return css[m.end():j - 1]

    # COUNTED AS DECLARATIONS, NOT AS RULE OPENINGS. The print one is a
    # GROUP MEMBER - `.alv-table .cell-actions, .row-actions, .no-print
    # { display: none !important }` - so an anchored `.row-actions {`
    # finds one of the two and refuses a correct round. That is the same
    # mistake NV-1b made on `.title-deeds-table td`, twice in one day.
    own = len(re.findall(r'(?m)^[ \t]*\.row-actions\s*\{', bcss))
    if own != 1:
        refuse('base opens a rule on .row-actions alone %d time(s), '
               'expected 1 - the top-level inline-flex' % own)
    pr = block(bcss, r'@media print\s*\{')
    if pr is None or not re.search(r'\.row-actions\s*[,{]', pr):
        refuse('base no longer hides .row-actions in @media print, and '
               'this round relies on print being the ONLY place it is '
               'touched')
    ph = block(bcss, r'@media screen and \(max-width: 768px\)\s*\{')
    if ph is None:
        refuse('base has no 768px block, so this round cannot check the '
               'thing it rests on')
    if re.search(r'\.row-actions\s*[,{]', ph):
        refuse('base now touches .row-actions inside the 768px block, so '
               'a row-action strip is no longer something that survives '
               'a phone - and this round makes two controls icon-only at '
               'every width on exactly that basis')
    for need in ('.icon-lock', '--alv-warn-line', '.icon-disabled',
                 '.icon-action-btn'):
        if need not in bcss:
            refuse('base does not declare %s, and .icon-notify is its '
                   'rule under another name' % need)

    # ---------------------------------------------------------------- 2
    out[base] = swap(bsrc, ICON_ANCHOR, ICON_NEW, '%s (the icon block)'
                     % BASE)

    p = os.path.join(root, RA)
    s = read(p)
    if "'notify'" in python_code_only(s):
        refuse('%s already knows the verb notify' % RA)
    out[p] = swap(s, RA_WAS, RA_NOW, '%s (FAMILY)' % RA)

    # ---------------------------------------------------------------- 3
    s = read(page)
    s = swap(s, EDIT_WAS, EDIT_NOW, '%s (the comment strip)' % PAGE)
    s = swap(s, CSS_WAS, CSS_NOW, '%s (the page-local tone)' % PAGE)
    s = swap(s, JS_WAS, JS_NOW, '%s (the spinner)' % PAGE)
    out[page] = s

    # GATES ON THE PAGE.
    body = code_only(s)
    if 'status-btn' in body:
        refuse('%s: status-btn survives in the code - %r'
               % (PAGE, re.search(r'[^\n]*status-btn[^\n]*',
                                  body).group(0)[:90]))
    if re.search(r'#[0-9a-fA-F]{3,8}\b', css_of(body)):
        refuse('%s: a colour is still spelled by hand - %s'
               % (PAGE, sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b',
                                              css_of(body))))))
    for hook in ('comment-edit-btn', 'notify-urgent-btn',
                 'notify-urgent-cell', 'notified-badge'):
        if hook not in body:
            refuse('%s: the JS hook %s is gone, and the script finds '
                   'these controls by it' % (PAGE, hook))
    for cls in ('icon-action-btn icon-edit', 'icon-action-btn icon-notify'):
        if body.count(cls) != 1:
            refuse('%s: %s appears %d time(s), expected 1'
                   % (PAGE, cls, body.count(cls)))
    if body.count('class="row-actions"') != 1:
        refuse('%s: %d row-action strip(s), expected 1'
               % (PAGE, body.count('class="row-actions"')))
    # THE LABEL IS GONE FROM BOTH, which is what icon-only means - ASKED
    # OF THE TWO BUTTONS, not of the page. `</i> Edit` also appears on
    # line 28, where an Edit Issue button in the page header is none of
    # this round's business, and a page-wide test refused a correct
    # round on it.
    for cls, what in (('icon-edit', 'Edit'), ('icon-notify', 'Notify')):
        m = re.search(r'<button\b[^>]*\b%s\b[^>]*>(.*?)</button>' % cls,
                      body, re.S)
        if not m:
            refuse('%s: no %s button carries %s' % (PAGE, what, cls))
        inner = re.sub(r'<i\b[^>]*>\s*</i>', '', m.group(1)).strip()
        if inner:
            refuse('%s: the %s control still draws %r beside its glyph, '
                   'so it is not icon-only' % (PAGE, what, inner[:40]))
    # AND THE SPINNER IS WHAT THE SCRIPT WRITES.
    # SCOPED TO THE BUTTON, not to every innerHTML on the page. The
    # script also replaces the CELL's contents with the Notified badge,
    # which is correct and is not a control - and a gate over the whole
    # script refused a correct round on it. The question is what goes
    # INSIDE the 44px square.
    js = js_of(body)
    ALLOWED = ("originalLabel", "''", '""',
               '\'<i class="fas fa-spinner fa-spin"></i>\'')
    for m in re.finditer(r'\bbtn\.innerHTML\s*=\s*([^;\n]+)', js):
        rhs = m.group(1).strip()
        if rhs not in ALLOWED:
            refuse('%s: the script writes %s into the button. A 44px '
                   'square holds a glyph, not a sentence.' % (PAGE, rhs))
    if '\'<i class="fas fa-spinner fa-spin"></i>\'' not in js:
        refuse('%s: the busy state is not a spinner' % PAGE)
    if js.count('btn.innerHTML = originalLabel') != 3:
        refuse('%s: %d failure path(s) restore the label, expected 3 - '
               'and originalLabel is read before the swap, so it is the '
               'bell' % (PAGE, js.count('btn.innerHTML = originalLabel')))

    # ---------------------------------------------------------------- 4
    s = read(ipage)
    s = swap(s, MIRROR_WAS, MIRROR_NOW, '%s (the disabled mirror)' % IPAGE)
    out[ipage] = s
    ibody = code_only(s)
    # TWO duplicate actions, because the desktop strip and the phone bar
    # each carry one. The first cut of this gate expected one.
    n_dup = ibody.count("{% url 'customer_invoice_duplicate' row.pk %}")
    if n_dup != 2:
        refuse('%s: the duplicate action appears %d time(s), expected 2 - '
               'the desktop strip and the phone bar' % (IPAGE, n_dup))
    if ibody.count('icon-action-btn icon-disabled') != 1:
        refuse('%s: %d disabled mirror(s), expected 1 - the desktop '
               'strip alone, because an action COLUMN reads one width '
               'per row and the phone bar is a grid that sizes to its '
               'children'
               % (IPAGE, ibody.count('icon-action-btn icon-disabled')))
    if 'Duplicate is for customer invoices only' not in ibody:
        refuse('%s: the mirror does not say why' % IPAGE)

    # ---------------------------------------------------------------- 5
    p = os.path.join(root, PS1)
    s = read(p)
    if ME in s:
        refuse('%s already lists this round' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suite list)' % PS1)
    s = swap(s, SENT_ANCHOR, SENT_NEW, '%s (the gate rows)' % PS1)
    out[p] = s

    p = os.path.join(root, TREE)
    out[p] = swap(read(p), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), ROUNDS_WAS, ROUNDS_NOW, '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, WD)
    out[p] = bump(read(p), 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'NV-1c, 16 Oct 2026 - this round own suite. Notify joins '
                  'the icon vocabulary as an ADVANCE that someone will '
                  'notice, after Demetri asked for a standard for it - a '
                  'bell with a Notify Now hover.',
                  '%s (the converted count)' % WD)

    p = os.path.join(root, BH)
    s = read(p)
    s = bump(s, 'N_BAR, N_ROW, N_MODAL = 267, %d, 95',
             ROW_WAS_N, ROW_NOW_N,
             'NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, '
             'in the desktop strip, which is inside a table.',
             '%s (the table-row census)' % BH)
    s = bump(s, 'N_LOOSE, N_LOOSE_H = %d, 11', LOOSE_WAS_N, LOOSE_NOW_N,
             'NV-1c, 16 Oct 2026 - the two comment controls. They were '
             '.status-btn, which this census does not select, and they '
             'sit in a comment thread rather than a table, so they land '
             'in the loose set. 34px was already one of its eleven '
             'heights, so N_LOOSE_H does not move.',
             '%s (the loose census)' % BH)
    out[p] = s

    p = os.path.join(root, CO)
    s = read(p)
    s = bump(s, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
             'NV-1c, 16 Oct 2026 - this round own patcher and suite',
             '%s (the alias count)' % CO)
    s = swap(s, "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_WAS, ALIAS_S_WAS),
             "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_NOW, ALIAS_S_NOW),
             '%s (the alias split)' % CO)
    out[p] = s

    # ---------------------------------------------------------------- 6
    # THE TWO SUITES THIS ROUND FALSIFIES, RE-POINTED HERE. Both record
    # #ecd9a8 as a standing exception on this page, and the round that
    # owned that decision is the one retiring it.
    p = os.path.join(root, AM)
    s = read(p)
    if "'#ecd9a8' not in T.code_only" in s:
        refuse('%s already reads the tint as retired' % AM)
    s = swap(s, AM_WAS, AM_NOW, '%s (section 8 head)' % AM)
    s = swap(s, AM_CLAIM_WAS, AM_CLAIM_NOW, '%s (the tint claim)' % AM)
    out[p] = s

    p = os.path.join(root, NB)
    s = read(p)
    if 'icon-action-btn icon-notify' in s:
        refuse('%s already reads the new class' % NB)
    s = swap(s, NB_GUARD_WAS, NB_GUARD_NOW, '%s (the guard)' % NB)
    s = swap(s, NB_HEX_WAS, NB_HEX_NOW, '%s (the stripper control)' % NB)
    s = swap(s, NB_PAIR_WAS, NB_PAIR_NOW, '%s (the Edit control)' % NB)
    s = swap(s, NB_PAIR2_WAS, NB_PAIR2_NOW, '%s (the Notify control)' % NB)
    s = swap(s, NB_TONE_WAS, NB_TONE_NOW, '%s (where the tone lives)' % NB)
    s = swap(s, NB_FIX_WAS, NB_FIX_NOW, '%s (the render fixture)' % NB)
    s = swap(s, NB_HOOK_WAS, NB_HOOK_NOW, '%s (the hook appearance)' % NB)
    out[p] = s

    p = os.path.join(root, FP)
    s = read(p)
    if 'allowed = []' in s:
        refuse('%s already allows no literal' % FP)
    s = swap(s, FP_WAS, FP_NOW, '%s (the census allowance)' % FP)
    s = swap(s, FP_CLAIM_WAS, FP_CLAIM_NOW, '%s (the tint claim)' % FP)
    out[p] = s

    # ---------------------------------------------------------------- 7
    if CHECK:
        print('NV-1c --check  %d file(s) would change' % len(out))
        for q in sorted(out):
            print('   %s' % os.path.relpath(q, root))
        return 0

    for q, t in sorted(out.items()):
        backup(q)
        write(q, t)

    print('NV-1c applied.')
    print('   .icon-notify is in base - .icon-lock rule under its own')
    print('         name, because a class carries one picture')
    print('   the vocabulary knows the verb: notify is ADVANCE, so the')
    print('         strip reads Edit then Notify without being told')
    print('   both comment controls are icon-only at EVERY width, which')
    print('         is safe because .row-actions is never in the 768px')
    print('         block - checked before it was relied on')
    print('   fsr_details spells NO colour by hand now, and the two')
    print('         suites that recorded that exception are re-pointed')
    print('   a tenant invoice row says why it has no Duplicate')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
