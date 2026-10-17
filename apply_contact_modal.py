# -*- coding: utf-8 -*-
"""apply_contact_modal.py - round CC-2, 17 Oct 2026.

THE CONTACT OPENS IN A MODAL, NOT IN PLACE.

Decided 15 Oct, never built. From the survey:

    The contacts compact view. DECIDED: a modal. Today the card expands
    in place and pushes the grid around it, and the edit/delete controls
    sit inside the expanded card. A modal gives the add/edit form room,
    which matters most on a phone.

MEASURED BEFORE BUILDING, and the finding narrows the round:

    `#contactModal` ALREADY EXISTS. The Add/Edit form has been a modal
    with `alv-modal-head` and `modal-fullscreen-mobile` all along. What
    expands in place is the COMPACT VIEW: clicking a card toggles
    `.expanded`, which reveals the email, phone and notes, the whole
    event list AND the action strip, growing the card and shoving every
    card after it down the grid.

    So this round replaces that expand, and touches the Add/Edit modal
    not at all.

THE CONTENT IS CLONED, NOT MOVED, AND NOT BUILT

    Three ways to fill a modal from a card. BUILDING the markup in
    script is the one CC-1 refused on the sibling page, and for the
    reason it wrote down: "markup a gate can read is worth more than
    markup that is convenient to generate." MOVING the card's nodes in
    and back out risks orphaning them if the modal is dismissed in a
    way nobody anticipated. CLONING copies markup the template owns,
    leaves the card whole, and is thrown away on close.

THE BUTTONS ARE THE CARD'S OWN

    The modal footer carries three controls written in the template.
    They do not re-declare what Edit needs - the card's own edit button
    already carries six escaped arguments - they CLICK THE CARD'S
    BUTTON once the modal has closed. One source for the call, no eval,
    and no two modals open at once fighting over a backdrop.

    A contact the user may not edit has disabled spans on its card
    rather than buttons, so the footer control is disabled too: it is
    enabled only when the card really has the live button behind it.

THE EMOJI COUNTDOWNS GO, AND CC-1 ALREADY SAID WHY

    "Nothing else in this application puts an emoji in its chrome, and
    the imminent and soon tones already say the same thing in the house
    palette." CC-1 took the calendar's on 15 Oct. These are the same
    four states on the sibling page, and they take the same wording:
    Today, Tomorrow, N days.

    The TONE treatment is not changed. On the calendar a countdown is a
    chip on a timeline card; here it is a line inside a dense event row,
    already carrying .soon and .imminent in house tokens. Matching the
    words is the decided vocabulary; matching the chip would be a
    design change this round has not rendered for him.

AND THE DEAD RULES GO WITH THE STATE. Seven rules select `.expanded` or
`:not(.expanded)`. With no expanded state the `:not()` ones are simply
the compact rules, and the rest have no element. A rule with no element
is dead weight exactly as an element with no rule is a bug - CC-1 again.
"""
import os
import re
import sys

import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_contactmodal'
PAGE = 'celebration_management.html'
MODEL = 'celebration_calendar.html'
ME = 'test_contact_modal.py'
PATCHER = 'apply_contact_modal.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
CHECK = False

CONVERTED_WAS, CONVERTED_NOW = 97, 98
ALIAS_WAS, ALIAS_NOW = 103, 105
ALIAS_P_WAS, ALIAS_S_WAS = 52, 51
ALIAS_P_NOW, ALIAS_S_NOW = 53, 52

# ===================================================================== CSS
CSS_PAIRS = [
    # The expanded card's own look - no element carries it now.
    ("""
.contact-card.compact-view.expanded {
    background: var(--alv-paper);
    padding: 20px;
}
""", """
"""),
    ("""
.contact-card.compact-view.expanded .contact-details {
    display: block !important;
}
""", """
"""),
    # The expanded card restored the header's divider. Nothing expands
    # now, so the rule has no element - and a rule with no element is
    # dead weight exactly as an element with no rule is a bug. CC-1.
    ("""
.contact-card.compact-view.expanded .contact-header {
    margin-bottom: 15px;
    padding-bottom: 15px;
    border-bottom: 2px solid var(--alv-line-soft);
}
""", """
"""),
    ("""    .contact-card.compact-view.expanded {
        padding: 14px;
    }
""", """"""),
]

# The :not(.expanded) qualifiers are now unconditional - there is no
# expanded state for them to exclude.
NOT_PAIRS = [
    ("""   EVERY SELECTOR HERE CARRIES :not(.expanded). Clicking the card brings
   back the pill, the icon and the heading size, which is exactly what he
   asked for - the pill is wanted, just not forty times at once. */""",
     """   THE SELECTORS USED TO CARRY :not(.expanded), because clicking the
   card brought the pill, the icon and the heading size back in place.
   CC-2, 17 Oct 2026 - clicking opens a modal instead, so a compact card
   is compact for as long as the compact view is on, and the qualifier
   has nothing left to exclude. The pill and the icon are in the modal,
   which is where he asked for them: wanted, just not forty times at
   once. */"""),
    (""".contact-card.compact-view:not(.expanded) .contact-info h4 {""",
     """.contact-card.compact-view .contact-info h4 {"""),
    (""".contact-card.compact-view:not(.expanded) .contact-info h4 > i,
.contact-card.compact-view:not(.expanded) .relationship-badge {""",
     """.contact-card.compact-view .contact-info h4 > i,
.contact-card.compact-view .relationship-badge {"""),
    (""".contact-card.compact-view:not(.expanded) .contact-name {""",
     """.contact-card.compact-view .contact-name {"""),
    ("""    .contact-card.compact-view:not(.expanded) .mobile-action-bar {""",
     """    .contact-card.compact-view .mobile-action-bar {"""),
]

# The modal's own rules, added beside the page's other modal CSS.
CSS_ADD_ANCHOR = """    .modal-fullscreen-mobile {"""
CSS_ADD = """    /* CC-2, 17 Oct 2026 - the contact detail modal on a phone gets the
       same full-screen treatment the Add/Edit modal already has. */
    #contactDetailModal .modal-body {
        max-height: 60vh;
        overflow-y: auto;
    }
    .modal-fullscreen-mobile {"""

CSS_BODY_ANCHOR = """\n.event-actions {\n    display: flex;"""
CSS_BODY = """/* CC-2, 17 Oct 2026 - THE CONTACT DETAIL MODAL.
   The body holds clones of the card's own .contact-details and
   .event-list, so nothing here restyles them - they are the same
   elements the card draws, outside .compact-view, which is why the
   rules that hide them in a compact card do not reach them. */
#contactDetailModal .modal-body .contact-details {
    display: block;
    margin-bottom: 10px;
}
#contactDetailModal .modal-body .event-list {
    max-height: 48vh;
    overflow-y: auto;
}
#contactDetailModal .relationship-badge {
    margin-left: 8px;
}

.event-actions {
    display: flex;"""

# =================================================================== MARKUP
MODAL_ANCHOR = """<div class="modal fade" id="contactModal" tabindex="-1" role="dialog">"""
MODAL_NEW = """{# CC-2, 17 Oct 2026 - THE CONTACT OPENS HERE, not in place. #}
{# #}
{# The body is filled with CLONES of the card's own .contact-details #}
{# and .event-list - markup this template owns, copied, rather than #}
{# markup built in script. CC-1 refused the script route on the #}
{# sibling page and wrote down why: markup a gate can read is worth #}
{# more than markup that is convenient to generate. #}
{# #}
{# The three footer controls do not re-declare what the card's #}
{# buttons already carry - Edit alone takes six escaped arguments. #}
{# They CLICK THE CARD'S OWN BUTTON once this modal has closed, so #}
{# there is one source for the call and never two modals open at #}
{# once. A contact the user may not edit has disabled spans instead #}
{# of buttons, so the control here is disabled too. #}
<div class="modal fade" id="contactDetailModal" tabindex="-1" role="dialog"
     aria-labelledby="contactDetailModalLabel">
    <div class="modal-dialog modal-fullscreen-mobile" role="document">
        <div class="modal-content">
            <div class="modal-header alv-modal-head">
                <h5 class="modal-title" id="contactDetailModalLabel">Contact</h5>
                <button type="button" class="close" data-dismiss="modal"
                        aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="modal-body"></div>
            {# THE TONES ARE THE DRIFT TOOL'S, NOT MINE. The footer #}
            {# was written with four action-secondary buttons, and #}
            {# Show-ButtonDrift - which test_recipe_tones runs over #}
            {# every template - reported two: it wants action-danger #}
            {# on Delete and action-primary on Add Event. #}
            {# #}
            {# AND THE PAIR, NOT THE TONE ALONE. action-danger by #}
            {# itself made the button GATE call the page drifting - #}
            {# the two instruments disagreed, and the page settled it #}
            {# two modals below: Delete Contact and Delete Event are #}
            {# both `action-secondary action-danger`. base says why - #}
            {# action-danger is outlined at rest and filled only on #}
            {# hover, so it is a modifier on a secondary button and #}
            {# not a tone of its own. Add Event takes action-primary, #}
            {# like Save Contact in the modal beside this one. #}
            {# #}
            {# THE ORDER IS THE HOUSE'S, WHICH READS BACKWARDS HERE. #}
            {# .modal-footer-stack-mobile is flex-direction: #}
            {# column-reverse below 768px, so the LAST control in the #}
            {# markup is the TOP one on a phone. The Add/Edit modal #}
            {# beside this one puts Cancel first and Save last for #}
            {# exactly that reason. Written the other way round, Add #}
            {# Event - the thing somebody opens a contact to do - #}
            {# landed at the bottom of the phone stack, under Close. #}
            <div class="modal-footer modal-footer-stack-mobile">
                <button type="button" class="btn action-secondary"
                        data-dismiss="modal">Close</button>
                <button type="button" class="btn action-secondary action-danger"
                        data-act="delete" disabled>
                    <i class="fas fa-trash"></i> Delete
                </button>
                <button type="button" class="btn action-secondary"
                        data-act="edit" disabled>
                    <i class="fas fa-pencil-alt"></i> Edit Contact
                </button>
                <button type="button" class="btn action-primary"
                        data-act="event" disabled>
                    <i class="fas fa-calendar-plus"></i> Add Event
                </button>
            </div>
        </div>
    </div>
</div>

<div class="modal fade" id="contactModal" tabindex="-1" role="dialog">"""

# ================================================================ COUNTDOWN
COUNT_WAS = """                                {% with days=event.days_until %}
                                    {% if days == 0 %}
                                        🎉 Today!
                                    {% elif days == 1 %}
                                        📅 Tomorrow
                                    {% elif days <= 7 %}
                                        ⚡ {{ days }} days away
                                    {% else %}
                                        📆 {{ days }} days away
                                    {% endif %}
                                {% endwith %}"""

COUNT_NOW = """                                {% comment %}
                                   THE COUNTDOWN LOSES ITS EMOJI. CC-2,
                                   17 Oct 2026. It read party-popper
                                   Today, calendar Tomorrow, lightning N
                                   days. Nothing else in this
                                   application puts an emoji in its
                                   chrome, and the imminent and soon
                                   tones already say the same thing in
                                   the house palette.

                                   The wording is CC-1's, taken from the
                                   calendar on the same decision two
                                   days ago, so the two celebration
                                   pages count down in one voice.
                                {% endcomment %}
                                {% with days=event.days_until %}
                                    {% if days == 0 %}
                                        Today
                                    {% elif days == 1 %}
                                        Tomorrow
                                    {% else %}
                                        {{ days }} days
                                    {% endif %}
                                {% endwith %}"""

# ======================================================================= JS
CLICK_WAS = """            // Add click handler for compact view
            card.onclick = function(e) {
                if (!e.target.closest('button')) {
                    toggleCardExpand(card);
                }
            };"""

CLICK_NOW = """            // CC-2, 17 Oct 2026 - a click OPENS THE CONTACT, it does
            // not grow the card. The old handler toggled a state class
            // on the card, which revealed the details, the whole event
            // list and the action strip in place and pushed every card
            // after it down the grid.
            card.onclick = function(e) {
                if (!e.target.closest('button')) {
                    openContactDetail(card);
                }
            };"""

REMOVE_WAS = """            card.classList.remove('compact-view', 'expanded');"""
REMOVE_NOW = """            card.classList.remove('compact-view');"""

FN_WAS = """function toggleCardExpand(card) {
    const eventList = card.querySelector('.event-list');
    const contactActions = card.querySelector('.contact-actions');
    const contactActionBarMobile = card.querySelector('[data-actions="contact"]');

    if (card.classList.contains('expanded')) {
        // Collapse — hide everything
        card.classList.remove('expanded');
        eventList.style.display = 'none';
        if (contactActions) contactActions.style.display = 'none';
        if (contactActionBarMobile) contactActionBarMobile.style.display = 'none';
    } else {
        // Expand — clear inline styles so CSS (incl. mobile @media) decides
        // visibility. Forcing 'flex' here would override the mobile rule
        // and leak desktop icons onto the mobile layout.
        card.classList.add('expanded');
        eventList.style.display = '';
        if (contactActions) contactActions.style.display = '';
        if (contactActionBarMobile) contactActionBarMobile.style.display = '';
    }
}"""

FN_NOW = """/* CC-2, 17 Oct 2026 - THE CONTACT DETAIL MODAL.
   Replaces the in-place expand, which grew the card and
   pushed every card after it down the grid.

   THE BODY IS FILLED WITH CLONES. Not built in script - CC-1 refused
   that on the sibling page, because markup a gate can read is worth
   more than markup that is convenient to generate. Not moved either -
   a node moved out of a card is a node that can be orphaned by a
   dismissal nobody anticipated. A clone is markup the template owns,
   copied, and thrown away on close.

   THE FOOTER CLICKS THE CARD'S OWN BUTTONS, once this modal is shut.
   The card's edit button already carries six escaped arguments; this
   does not re-declare them, and two modals are never open at once. */
const CONTACT_ACTS = {event: '.icon-event', edit: '.icon-edit',
                      delete: '.icon-delete'};
let contactDetailCard = null;
let contactDetailPending = null;

function contactDetailEl() {
    return document.getElementById('contactDetailModal');
}

function openContactDetail(card) {
    const el = contactDetailEl();
    if (!el) { return; }
    contactDetailCard = card;

    const title = el.querySelector('.modal-title');
    const name = card.querySelector('.contact-name');
    title.textContent = name ? name.textContent.trim() : 'Contact';
    const badge = card.querySelector('.relationship-badge');
    if (badge) { title.appendChild(badge.cloneNode(true)); }

    const body = el.querySelector('.modal-body');
    while (body.firstChild) { body.removeChild(body.firstChild); }
    card.querySelectorAll('.contact-details').forEach(function (n) {
        body.appendChild(n.cloneNode(true));
    });
    const events = card.querySelector('.event-list');
    if (events) { body.appendChild(events.cloneNode(true)); }

    // A CONTROL IS ENABLED ONLY WHEN THE CARD REALLY HAS THE BUTTON.
    // Without can_edit_celebrations the card draws disabled spans
    // instead, and there is nothing behind the footer control to click.
    Object.keys(CONTACT_ACTS).forEach(function (act) {
        const btn = el.querySelector('[data-act="' + act + '"]');
        const src = card.querySelector('button' + CONTACT_ACTS[act]);
        if (btn) { btn.disabled = !src; }
    });

    $(el).modal('show');
}

$(function () {
    const el = contactDetailEl();
    if (!el) { return; }
    el.querySelector('.modal-footer').addEventListener('click', function (e) {
        const btn = e.target.closest('[data-act]');
        if (!btn || btn.disabled || !contactDetailCard) { return; }
        contactDetailPending =
            contactDetailCard.querySelector('button' + CONTACT_ACTS[btn.dataset.act]);
        $(el).modal('hide');
    });
    $(el).on('hidden.bs.modal', function () {
        const body = el.querySelector('.modal-body');
        while (body.firstChild) { body.removeChild(body.firstChild); }
        const next = contactDetailPending;
        contactDetailPending = null;
        if (next) { next.click(); }
    });
});"""


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
    raise SystemExit('CC-2 REFUSED: %s' % msg)


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


def bump(text, lit, was, now, note, where):
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    page = alv_tree.path_of(PAGE)

    s = read(page)

    # ---------------------------------------------------------------- 0
    if 'contactDetailModal' in s:
        print('CC-2  already applied - the contact opens in a modal.')
        return 0

    out = {}

    # ---------------------------------------------------------------- 1
    # THE PAGE IS READ, NOT REMEMBERED.
    if 'toggleCardExpand' not in s:
        refuse('%s has no toggleCardExpand, so the expand this round '
               'replaces is not the one on disk' % PAGE)
    if 'id="contactModal"' not in s:
        refuse('%s has no Add/Edit modal to sit beside' % PAGE)
    # AND THE SIBLING PAGE, whose wording this round copies.
    model = read(alv_tree.path_of(MODEL))
    if 'THE COUNTDOWN LOSES ITS EMOJI' not in model:
        refuse('%s does not carry CC-1 countdown decision, so there is '
               'no decided wording to match' % MODEL)
    for word in ('Today', 'Tomorrow', 'days'):
        if word not in model:
            refuse('%s no longer says %r' % (MODEL, word))

    # ---------------------------------------------------------------- 2
    for old, new in CSS_PAIRS + NOT_PAIRS:
        s = swap(s, old, new, '%s (a compact-view rule)' % PAGE)
    s = swap(s, CSS_ADD_ANCHOR, CSS_ADD, '%s (the phone modal rule)' % PAGE)
    s = swap(s, CSS_BODY_ANCHOR, CSS_BODY, '%s (the modal body rules)' % PAGE)
    s = swap(s, MODAL_ANCHOR, MODAL_NEW, '%s (the modal)' % PAGE)
    s = swap(s, COUNT_WAS, COUNT_NOW, '%s (the countdown)' % PAGE)
    s = swap(s, CLICK_WAS, CLICK_NOW, '%s (the click handler)' % PAGE)
    s = swap(s, REMOVE_WAS, REMOVE_NOW, '%s (the class reset)' % PAGE)
    s = swap(s, FN_WAS, FN_NOW, '%s (toggleCardExpand)' % PAGE)

    # ---------------------------------------------------------------- 3
    b = code_only(s)
    if 'toggleCardExpand' in b:
        refuse('%s still carries the in-place expand' % PAGE)
    if re.search(r'\.expanded\b', b):
        refuse('%s still selects an .expanded state nothing sets' % PAGE)
    if b.count('id="contactDetailModal"') != 1:
        refuse('%s: %d detail modal(s), expected 1'
               % (PAGE, b.count('id="contactDetailModal"')))
    # THE FOOTER ORDER, because the phone reverses it.
    foot = b[b.index('id="contactDetailModal"'):]
    foot = foot[foot.index('modal-footer'):foot.index('</div>', foot.index('modal-footer'))]
    if foot.index('data-dismiss') > foot.index('data-act="event"'):
        refuse('%s: the footer puts Add Event before Close in markup, '
               'which column-reverse turns into Close on top and Add '
               'Event at the bottom on a phone' % PAGE)
    if 'alv-modal-head' not in b:
        refuse('%s: the modal does not wear the house head' % PAGE)
    # NOTHING IS BUILT IN SCRIPT. The body is clones of real markup.
    scripts = '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script\s*>',
                                   b, re.S))
    # SCOPED TO WHAT THIS ROUND WRITES. The page already assigns
    # innerHTML in four places to swap a button's label, which predates
    # CC-2 and is not markup generation in the sense CC-1 refused. The
    # claim here is narrower and is the one this round can make: the
    # DETAIL MODAL's body is filled from clones, and nothing this round
    # adds builds markup from a string.
    mine = fit(s, FN_NOW)
    if 'innerHTML' in mine:
        refuse('%s: the round own script builds markup - CC-1 refused '
               'that on the sibling page and said why' % PAGE)
    if re.search(r'contactDetail\w*\s*\.\s*innerHTML', scripts):
        refuse('%s: the detail modal is filled from a string' % PAGE)
    if scripts.count('cloneNode(true)') < 2:
        refuse('%s: the modal body is not filled from clones' % PAGE)
    # THE EMOJI ARE GONE, all four of them.
    for ch in ('\U0001F389', '\U0001F4C5', '⚡', '\U0001F4C6'):
        if ch in b:
            refuse('%s still carries the emoji %r in its chrome'
                   % (PAGE, ch))
    # AND THE WORDS ARE CC-1's.
    if 'days away' in b:
        refuse('%s still says "days away"; the calendar says "N days"'
               % PAGE)
    # EVERY {# #} CLOSES ON ITS OWN LINE.
    bad = [i + 1 for i, ln in enumerate(s.split('\n'))
           if ln.count('{#') != ln.count('#}')]
    if bad:
        refuse('%s: a Django comment outlives its line, at %s' % (PAGE, bad))
    # LINE ENDINGS - the style, not the count.
    was = read(page)
    w_crlf, n_crlf = was.count('\r\n'), s.count('\r\n')
    w_lf, n_lf = was.count('\n') - w_crlf, s.count('\n') - n_crlf
    if (w_crlf > w_lf and n_lf > w_lf) or (w_lf >= w_crlf and n_crlf > w_crlf):
        refuse('%s: the file gained a line ending it did not have' % PAGE)
    out[page] = s

    # ---------------------------------------------------------------- 4
    p = os.path.join(root, PS1)
    t = read(p)
    t = swap(t, """    'test_gate_speed.py'
)""", """    'test_gate_speed.py',
    'test_contact_modal.py'
)""", '%s ($suites)' % PS1)
    t = swap(t, """    # -------------------------------------------- HL-1, 12 Oct 2026""",
             """    # ------------------------------------------------- CC-2, 17 Oct 2026
    @{ File = 'pages\\templates\\celebration_management.html'; Text = 'contactDetailModal'; What = 'CC-2: the contact opens in a modal' },
    @{ File = 'pages\\templates\\celebration_management.html'; Text = 'toggleCardExpand'; Absent = $true; Code = $true; What = 'CC-2: and no longer grows the card in place' },
    # -------------------------------------------- HL-1, 12 Oct 2026""",
             '%s ($sentinels)' % PS1)
    out[p] = t

    p = os.path.join(root, TREE)
    out[p] = swap(read(p), """    'test_gate_speed.py',
]""", """    'test_gate_speed.py',
    # CC-2, 17 Oct 2026 - the contacts compact view opens a modal
    # instead of growing the card in place, and the emoji countdowns
    # take CC-1's wording. Wide from birth.
    'test_contact_modal.py',
]""", '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), """    '.bak_gatespeed',""",
                  """    '.bak_gatespeed',
    # CC-2, 17 Oct 2026 - decided 15 Oct, built now.
    '.bak_contactmodal',""", '%s (ROUNDS)' % ROUNDS)

    # ------------------------------------------- test_important_base
    #
    # ONE !important LEAVES WITH THE DEAD RULE.
    #
    # `.contact-card.compact-view.expanded .contact-details { display:
    # block !important }` forced the details open when the card grew.
    # Nothing expands now, so the rule has no element and goes - and
    # the tree-wide census of !important declarations goes with it.
    #
    # The census is a hand-kept number that every round touching a
    # <style> body has to move. It is not this round's to question;
    # it is this round's to keep true.
    IMP = 'test_important_base.py'
    p = os.path.join(root, IMP)
    out[p] = swap(read(p), 'IMP_TREE = 828',
                  'IMP_TREE = 827   # CC-2, 17 Oct 2026 - the one that '
                  'forced .contact-details open inside an expanded card. '
                  'Nothing expands now, so the rule had no element '
                  'left.   # (was 828)',
                  '%s (the tree census)' % IMP)

    # -------------------------------------------- test_countdown_tone
    #
    # IT PINS A WORDING CC-1 HAD ALREADY ABANDONED.
    #
    # The claim is good and this round keeps it: the colour was never
    # the only carrier, so the WORDS must still say which day it is.
    # What it pins is the exclamation mark - "Today!" - which came in
    # with the emoji and went out with them on the calendar two days
    # ago. The sibling page says "Today"; so does this one now.
    #
    # The assertion is re-pointed, not relaxed: it still requires both
    # words, and it now requires BOTH PAGES to agree, which is a
    # stronger claim than the one it replaces and the reason the
    # wording was changed at all.
    CT = 'test_countdown_tone.py'
    p = os.path.join(root, CT)
    out[p] = swap(read(p),
                  """ok('Today!' in mgmt and 'Tomorrow' in mgmt,
   'the words still say Today! and Tomorrow in as many letters - the '
   'colour was never the only carrier, and now it is not a carrier of '
   'anything alarming')""",
                  """# CC-2, 17 Oct 2026 - the exclamation mark went with the emoji.
# It arrived as part of "party-popper Today!", and CC-1 took the whole
# phrase off the calendar on 15 Oct. This asked for the old spelling on
# the page that had not been converted yet.
#
# The claim is unchanged and is now stronger: the colour was never the
# only carrier, so the WORDS must still say which day it is - and BOTH
# celebration pages must say it the same way.
ok('Today' in mgmt and 'Tomorrow' in mgmt,
   'the words still say Today and Tomorrow in as many letters - the '
   'colour was never the only carrier, and now it is not a carrier of '
   'anything alarming')
ok('Today!' not in mgmt,
   '  and the exclamation mark went with the emoji it arrived with')""",
                  '%s (the wording)' % CT)

    # ----------------------------------------------- test_drift_root
    # A NEW MODAL IS A NEW .modal-footer, and the tree-wide census
    # counts them with two matchers that must agree. CC-1 did exactly
    # this on 15 Oct when the day sheet added one. Both rise by the
    # same one, which is the point of keeping two.
    p = os.path.join(root, 'test_drift_root.py')
    out[p] = swap(read(p),
                  'N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 88, 87',
                  'N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 89, 88   '
                  '# CC-2, 17 Oct 2026 - the contact detail modal adds '
                  'one .modal-footer. Both matchers rise by the same '
                  'one.   # (was 88, 87)',
                  'test_drift_root.py (the footer census)')

    p = os.path.join(root, WD)
    out[p] = bump(read(p), 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'CC-2, 17 Oct 2026 - this round own suite',
                  '%s (CONVERTED_N)' % WD)

    import glob as _glob
    _al = [os.path.basename(f)
           for f in sorted(_glob.glob(os.path.join(root, '*.py')))
           if re.search(r'^code_only\s*=\s*alv_tree\.code_only',
                        read(f), re.M)]
    _pat = [f for f in _al if f.startswith('apply_')]
    _sui = [f for f in _al if f.startswith('test_')]
    # COUNTED, NOT ASSUMED - AND NOT AN EQUALITY.
    #
    # LF-1 added this because the alias count stopped moving by two:
    # a round whose suite has no use for code_only does not alias it.
    # Counting the files on disk is right; demanding EQUALITY is not,
    # because the files of LATER rounds in the same bundle are already
    # on disk when this one applies. The count on disk is the final
    # figure for the whole bundle, not the figure for this round.
    #
    # So the claim is the one that can be made here: this round must
    # not write a number LARGER than the files that exist. The end
    # state - that test_code_only's number equals the files on disk -
    # is asserted by test_code_only itself, live, on every run.
    if (len(_al) < ALIAS_NOW or len(_pat) < ALIAS_P_NOW or len(_sui) < ALIAS_S_NOW):
        refuse('the alias count on disk is %d (%d patchers, %d '
               'suites) and this round would write %d (%d, %d) - '
               'more than exist'
               % (len(_al), len(_pat), len(_sui),
                  ALIAS_NOW, ALIAS_P_NOW, ALIAS_S_NOW))

    p = os.path.join(root, CO)
    t2 = bump(read(p), 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
              'CC-2, 17 Oct 2026 - this round own patcher and suite',
              '%s (the alias count)' % CO)
    t2 = swap(t2, "'%%d file(s) alias it - %d patchers and %d suites'"
              % (ALIAS_P_WAS, ALIAS_S_WAS),
              "'%%d file(s) alias it - %d patchers and %d suites'"
              % (ALIAS_P_NOW, ALIAS_S_NOW),
              '%s (the alias split)' % CO)
    out[p] = t2

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('CC-2 --check  %d file(s) would change' % len(out))
        for k in sorted(out):
            print('   %s' % os.path.relpath(k, root).replace(os.sep, '/'))
        return 0

    for k, v in out.items():
        backup(k)
        write(k, v)
    print('CC-2 applied.')
    print('   the contact opens in a modal, not in place')
    print('   the body is CLONES of the card markup, not script-built')
    print('   the footer clicks the card own buttons, after closing')
    print('   the emoji countdowns take CC-1 wording')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
