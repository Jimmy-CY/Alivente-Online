# -*- coding: utf-8 -*-
"""apply_ra16_meal_send_drag.py - round RA16, 23 Nov 2026.

RELEASE RA16 - THE MEAL PLANNER: A LOOK BEFORE YOU ADD, A MEAL DRAGGED TO
ANOTHER DAY, AND THE PLAN SENT.

    Demetri, 23 Nov: "When i click on a day on the calendar, and it shows
    me the recipes, I want to include a small icon on the top right of
    each recipe box with the "eye" icon ... they see just the quick-view
    of the recipe." - "I want to be able to drag-and-drop Chicken - Cajun
    Garlic to another day on my calendar (instead of using the "Move To"
    option. We can leave the move-to in place" - "For the Monthly, Weekly
    and Daily Meal plans, I want to add a "Share" button where I can
    email, Whatsapp, etc the plan." Then: "Let's go ahead !!"

    - The Add a meal picker: an eye at the top right of every recipe card
      opens the quick view OVER the picker, with Back to list and Add to
      <the day>; the rest of the card still adds (picker rows carry the
      quick-view address).
    - Month and Week: a meal drags onto another day. The day under the
      pointer is outlined; letting go posts Move (move_meal_entry, with
      dragged=1 and the order the day was left in), so leftovers travel
      as before; the page offers Undo once. Move to... stays, and is the
      phone's way. test_week_drag follows: WD-1 kept the columns apart on
      purpose, and this reverses it.
    - Send... on the bar (and Send this plan... in the phone menu): the
      plan in view as text - "Mon (23rd Nov): Chicken Kritharaki", a
      day's other meals lined up under its first - for WhatsApp, Copy,
      or the phone's own share menu; or an email to the household roster
      (B9): the Day like the Day view, the Week as the list, the Month as
      a calendar. Called Send because Share is MS-1's. New module
      pages/views/recipes/meal_send.py; route meal_plans/send/.
    - Help: the eye, dragging to another day, Sending a plan.

The suite and the new module ship beside this patcher. Stands on RA15.
Idempotent. Edits backed up to .bak_ra16. No migration.
"""
import os
import sys

SUFFIX = '.bak_ra16'
MARK = 'RA16, 23 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_ra16_meal_send_drag.py',
    'pages/views/recipes/meal_send.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_ra14_trip_tabs_tap.py',
    # RA15, 23 Nov 2026 - the activity log.
    'test_ra15_activity_log.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_ra14_trip_tabs_tap.py',
    # RA15, 23 Nov 2026 - the activity log.
    'test_ra15_activity_log.py',
    # RA16, 23 Nov 2026 - the planner: the eye, drag to a day, Send.
    'test_ra16_meal_send_drag.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # RA15, 23 Nov 2026 - the activity log.
    '.bak_ra15',
]

''',
         r'''    # RA15, 23 Nov 2026 - the activity log.
    '.bak_ra15',
    # RA16, 23 Nov 2026 - the planner: the eye, drag to a day, Send.
    '.bak_ra16',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #ffc107; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-mobile-alt" style="color:#e6a817;"></i> It works on a phone.</strong> The picker, the stepper, the chip menu, the calendar button and the day cards are all built for a narrow screen, which is where a week usually gets planned.
''',
         r'''      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-eye" style="color:#0e7c8b;"></i> Have a look before you add.</strong> Every recipe in the <strong>Add a meal</strong> picker has an <strong><i class="fas fa-eye"></i></strong> at its top right. Press it to read the recipe without adding it; <strong>Back to list</strong> returns you to the picker with your search and filters as they were, and <strong>Add to</strong> the day adds it from there. Pressing anywhere else on the card still adds it straight away.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #ffc107; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-mobile-alt" style="color:#e6a817;"></i> It works on a phone.</strong> The picker, the stepper, the chip menu, the calendar button and the day cards are all built for a narrow screen, which is where a week usually gets planned.
'''),
        (r'''
    <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
      <i class="fas fa-info-circle"></i> <strong>Drag to reorder:</strong> the grip at the left of each meal reorders that day - the same handle the ingredient and instruction lists use - and in the week view the meals themselves drag up and down their own column. <strong>Not yet, and coming:</strong> dragging a meal from one day to another. That writes a date rather than an order, so for now it is <strong>Move</strong> on the chip menu.
''',
         r'''
    <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
      <i class="fas fa-info-circle"></i> <strong>Drag to reorder:</strong> the grip at the left of each meal reorders that day - the same handle the ingredient and instruction lists use - and in the week view the meals themselves drag up and down their own column. <strong>To another day:</strong> in the month or the week, drag a meal onto any other day. The day under the pointer is outlined, and once you let go the page shows <strong>Moved &hellip; &middot; Undo</strong>. Its leftovers go with it, the same as <strong>Move to&hellip;</strong> on the chip menu, which is still there &mdash; and is the way to do it on a phone, where the month shows dots rather than names.
'''),
        (r'''    <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
      <i class="fas fa-lightbulb"></i> <strong>Tip:</strong> print the month at the start of it and the week on the Sunday. The month is the one that goes on the fridge; the week is the one that tells you what to take out of the freezer.
''',
         r'''    <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
      <i class="fas fa-lightbulb"></i> <strong>Tip:</strong> print the month at the start of it and the week on the Sunday. The month is the one that goes on the fridge; the week is the one that tells you what to take out of the freezer.
    </div>
  </article>

  <article data-tab-slug="mp-send"
           data-tab-name="Sending a plan"
           data-tab-icon="fa-paper-plane">
    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #28a745; padding-bottom:6px;"><i class="fas fa-paper-plane" style="color:#28a745;"></i> Sending the plan to someone</h6>

    <p style="font-size:13px; color:#6c757d; margin-bottom:16px;"><strong>Send&hellip;</strong> on the planner's bar sends the plan you are looking at &mdash; the day, the week or the month &mdash; by email, WhatsApp, or anywhere you can paste text. It is not the same as <strong>Share</strong> beside your plan's name, which lets another Alivente user open and change the plan itself.</p>

    <div style="display:flex; flex-direction:column; gap:12px; margin-bottom:20px;">

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #28a745; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-list" style="color:#28a745;"></i> What you see first is what goes.</strong> The dialog shows the plan as text, one line a day &mdash; <em>Mon (23rd Nov): Chicken Kritharaki</em> &mdash; with a day's second and third meals lined up under the first. Days with nothing planned are left out.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fab fa-whatsapp" style="color:#0e7c8b;"></i> WhatsApp, Copy, or your phone's own share menu.</strong> <strong>WhatsApp</strong> opens a message with the plan in it, for you to choose who it goes to. <strong>Copy as text</strong> puts it on the clipboard. On a phone, <strong>More apps&hellip;</strong> offers whatever else you have installed.
      </div>

      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #0e7c8b; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-envelope" style="color:#0e7c8b;"></i> By email, laid out properly.</strong> Tick who it goes to &mdash; yourself, or anyone in the household with an email address &mdash; and press <strong>Send email</strong>. A day arrives looking like the Day view, with each recipe's photo, time, servings and tags; a week arrives as the list; a month arrives as a calendar. Only the household can be chosen, because the email comes from Alivente's own address; for anyone else use WhatsApp or Copy.
      </div>

'''),
    ]),
    (os.path.join('pages', 'templates', 'meal_planner.html'), [
        (r'''    .mp-share-list label { display: flex; align-items: center; gap: 12px; min-height: 44px; margin: 0; cursor: pointer; }
    .mp-whose-note { font-size: 13px; color: var(--alv-ink-soft); }
</style>

''',
         r'''    .mp-share-list label { display: flex; align-items: center; gap: 12px; min-height: 44px; margin: 0; cursor: pointer; }
    .mp-whose-note { font-size: 13px; color: var(--alv-ink-soft); }
    /* RA16, 23 Nov 2026 - the picker's eye, the drop target, Undo and
       Send. No colour here that is not a token. */
    .recipe-option.has-eye { padding-right: 46px; }
    .pick-eye { position: absolute; top: 6px; right: 6px; width: 34px; height: 34px; display: inline-flex; align-items: center; justify-content: center; padding: 0; border-radius: 50%; border: 1px solid var(--alv-line); background: var(--alv-paper); color: var(--alv-accent-ink); }
    .pick-eye:hover { background: var(--alv-accent-soft); border-color: var(--alv-accent-line); }
    .pick-eye:focus-visible { outline: 2px solid var(--alv-accent-ring); outline-offset: 2px; }
    .ql-pickfoot { display: flex; justify-content: flex-end; gap: 8px; }
    #quickLookModal.is-over { z-index: 1060; }
    .modal-backdrop.is-over { z-index: 1055; }
    .month-grid.is-draggable .month-chip { cursor: grab; }
    .month-cell .sortable-ghost { opacity: 0.4; }
    .month-cell.is-drop, .week-col-body.is-drop { outline: 2px dashed var(--alv-accent); outline-offset: -3px; background: var(--alv-accent-soft); }
    .mp-undo { display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 8px 14px; margin: 0 0 12px; padding: 6px 14px; border: 1px solid var(--alv-good-line); border-radius: var(--alv-radius-sm); background: var(--alv-good-soft); color: var(--alv-good-ink); }
    .mp-undo form { margin: 0; }
    .send-preview { white-space: pre-wrap; font-family: Consolas, Menlo, monospace; font-size: 13px; max-height: 260px; overflow: auto; margin: 0 0 14px; padding: 10px 12px; border: 1px solid var(--alv-line); border-radius: var(--alv-radius-sm); background: var(--alv-surface); color: var(--alv-ink); }
    .send-ways { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 16px; }
    .send-h { margin: 0 0 4px; font-size: 14px; font-weight: 600; color: var(--alv-ink-strong); }
    .send-people { list-style: none; margin: 0 0 8px; padding: 0; }
    .send-people label { display: flex; align-items: center; gap: 12px; min-height: 44px; margin: 0; cursor: pointer; }
    .send-status { min-height: 18px; margin: 8px 0 0; font-size: 13px; color: var(--alv-ink-soft); }
    .send-status.is-bad { color: var(--alv-bad-ink); }
</style>

'''),
        (r'''            <i class="fas fa-print"></i> Print
        </a>
        {% if perms.auth.can_edit_recipes %}
        {# BACK ON THE BAR - CP-2, 21 Oct 2026.                       #}
''',
         r'''            <i class="fas fa-print"></i> Print
        </a>
        {# SEND - RA16, 23 Nov 2026. Demetri: "add a "Share" button where #}
        {# I can email, Whatsapp, etc the plan". Called Send because     #}
        {# Share is already MS-1's - who else can open this plan.        #}
        {# Whatever view is on screen is what goes.                      #}
        <button type="button" class="btn action-secondary"
                data-toggle="modal" data-target="#sendModal" onclick="sendLoad()">
            <i class="fas fa-paper-plane"></i> Send&hellip;
        </button>
        {% if perms.auth.can_edit_recipes %}
        {# BACK ON THE BAR - CP-2, 21 Oct 2026.                       #}
'''),
        (r'''                    <i class="fas fa-print"></i> Print this plan
                </a>
                {# AND HELP - HP-1, 21 Oct 2026.                          #}
                {#                                                        #}
''',
         r'''                    <i class="fas fa-print"></i> Print this plan
                </a>
                {# AND SEND, for the same reason as Print - RA16. #}
                <button type="button" class="action-more-item" role="menuitem"
                        data-toggle="modal" data-target="#sendModal" onclick="sendLoad()">
                    <i class="fas fa-paper-plane"></i> Send this plan...
                </button>
                {# AND HELP - HP-1, 21 Oct 2026.                          #}
                {#                                                        #}
'''),
        (r'''    <div class="calendar-layout">

        {# ------------------------------------------------ the month #}
        {#                                                             #}
''',
         r'''    <div class="calendar-layout">

        {# UNDO A DROP - RA16, 23 Nov 2026. Offered once, on the page the  #}
        {# drop landed on, at the top of the calendar: test_bar_first reads #}
        {# the bar down to the switcher, and test_view_switch the switcher  #}
        {# down to here, and neither wants this button in what it reads.    #}
        {# It posts the same Move with the old date, so    #}
        {# leftovers come back with their meal too.                        #}
        {% if move_undo and perms.auth.can_edit_recipes %}
        <div class="mp-undo" role="status" data-move-undo>
            <span>Moved &ldquo;{{ move_undo.what }}&rdquo; to {{ move_undo.to|date:"D j M" }}{% if move_undo.leftovers %}, with its leftovers{% endif %}</span>
            <form method="POST" action="{% url 'move_meal_entry' %}">
                {% csrf_token %}
                <input type="hidden" name="view" value="{{ view_mode }}">
                <input type="hidden" name="from_date" value="{{ anchor|date:'Y-m-d' }}">
                <input type="hidden" name="meal_entry_id" value="{{ move_undo.id }}">
                <input type="hidden" name="date" value="{{ move_undo.back|date:'Y-m-d' }}">
                <input type="hidden" name="undo" value="1">
                <button type="submit" class="btn action-secondary"><i class="fas fa-undo"></i> Undo</button>
            </form>
        </div>
        {% endif %}

        {# ------------------------------------------------ the month #}
        {#                                                             #}
'''),
        (r'''                {% for week in month_weeks %}{% for cell in week %}{% if cell %}
                <div class="month-cell{% if cell.is_today %} is-today{% endif %}{% if cell.in_week %} in-week{% endif %}"
                     {% if perms.auth.can_edit_recipes %}role="button" tabindex="0"
                     aria-label="{{ cell.count }} meal{{ cell.count|pluralize }} on {{ cell.date|date:'l j F' }} - add one"
''',
         r'''                {% for week in month_weeks %}{% for cell in week %}{% if cell %}
                <div class="month-cell{% if cell.is_today %} is-today{% endif %}{% if cell.in_week %} in-week{% endif %}"
                     data-day="{{ cell.date|date:'Y-m-d' }}"
                     {% if perms.auth.can_edit_recipes %}role="button" tabindex="0"
                     aria-label="{{ cell.count }} meal{{ cell.count|pluralize }} on {{ cell.date|date:'l j F' }} - add one"
'''),
        (r'''{% endif %}


{# SORTABLE 1.15.0 - RO-1, 21 Oct 2026. The version and the URL are    #}
''',
         r'''{% endif %}

{# ------------------------------------------------- SEND, RA16 #}
{# OUTSIDE the edit-tier block on purpose: a reader can send too,  #}
{# only the email half is an editor's.                            #}
{# Demetri, 23 Nov 2026: email, WhatsApp, etc. The text is asked   #}
{# for when the dialog opens (meal_plan_send), so the planner page #}
{# itself costs no extra query. WhatsApp is a real link whose href #}
{# is filled in when the text arrives, so the click is the user's  #}
{# own and no pop-up blocker stands in the way.                    #}
<div class="modal fade" id="sendModal" tabindex="-1" role="dialog"
     aria-labelledby="sendTitle" aria-hidden="true">
    <div class="modal-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header alv-modal-head">
                <h5 class="modal-title" id="sendTitle">
                    <i class="fas fa-paper-plane"></i> Send this plan
                </h5>
                <button type="button" class="close" data-dismiss="modal"
                        aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="modal-body">
                <pre class="send-preview" id="sendPreview" aria-label="What will be sent">Loading...</pre>
                <div class="send-ways">
                    <a class="btn action-secondary" id="sendWhatsApp" href="#"
                       target="_blank" rel="noopener">
                        <i class="fab fa-whatsapp"></i> WhatsApp
                    </a>
                    <button type="button" class="btn action-secondary" onclick="sendCopy()">
                        <i class="fas fa-copy"></i> Copy as text
                    </button>
                    {# THE PHONE'S OWN SHARE MENU, where there is one - #}
                    {# Messages, Viber, Mail, whatever is installed.     #}
                    <button type="button" class="btn action-secondary" id="sendNative"
                            onclick="sendNative()" hidden>
                        <i class="fas fa-share-alt"></i> More apps...
                    </button>
                </div>
                {% if perms.auth.can_edit_recipes %}
                <p class="send-h">Email it to</p>
                <ul class="send-people" id="sendPeople"></ul>
                {% endif %}
                <p class="send-status" id="sendStatus" role="status" aria-live="polite"></p>
            </div>
            {# THE EMAIL IS THE DIALOG'S ONE PRIMARY, so it sits in the  #}
            {# footer - test_calendar_grid's button gate keeps a modal  #}
            {# body's own buttons quiet.                                #}
            <div class="modal-footer">
                <button type="button" class="btn action-secondary"
                        data-dismiss="modal">Close</button>
                {% if perms.auth.can_edit_recipes %}
                <button type="button" class="btn action-primary" id="sendEmailBtn"
                        onclick="sendEmail()">
                    <i class="fas fa-envelope"></i> Send email
                </button>
                {% endif %}
            </div>
        </div>
    </div>
</div>

<script>
// RA16, 23 Nov 2026 - SEND. One fetch per opening: the plan may have
// changed since the page was drawn, and the dialog says what will go.
var sendWords = null;

function sendStatus(msg, bad) {
    var s = document.getElementById('sendStatus');
    if (!s) { return; }
    s.textContent = msg || '';
    s.classList.toggle('is-bad', !!bad);
}

function sendLoad() {
    sendWords = null;
    sendStatus('');
    var pre = document.getElementById('sendPreview');
    var wa = document.getElementById('sendWhatsApp');
    var nat = document.getElementById('sendNative');
    if (pre) { pre.textContent = 'Loading...'; }
    if (wa) { wa.setAttribute('href', '#'); }
    if (nat) { nat.hidden = !navigator.share; }
    fetch('{% url "meal_plan_send" %}?view={{ view_mode }}&date={{ anchor|date:"Y-m-d" }}', {
        credentials: 'same-origin',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
        .then(function (r) { if (!r.ok) { throw new Error(r.status); } return r.json(); })
        .then(function (d) {
            sendWords = d;
            if (pre) { pre.textContent = d.text; }
            if (wa) {
                wa.setAttribute('href', 'https://wa.me/?text=' +
                    encodeURIComponent(d.whatsapp));
            }
            sendPeople(d.people || []);
        })
        .catch(function () {
            if (pre) { pre.textContent = ''; }
            sendStatus('Could not load the plan. Close this and try again.', true);
        });
}

// BUILT, NOT INTERPOLATED - a name is a person's words (SL-4).
function sendPeople(people) {
    var ul = document.getElementById('sendPeople');
    var btn = document.getElementById('sendEmailBtn');
    if (!ul) { return; }
    while (ul.firstChild) { ul.removeChild(ul.firstChild); }
    people.forEach(function (p) {
        var li = document.createElement('li');
        var lab = document.createElement('label');
        var box = document.createElement('input');
        box.type = 'checkbox';
        box.value = p.email;
        var span = document.createElement('span');
        span.textContent = p.name + ' - ' + p.email;
        lab.appendChild(box);
        lab.appendChild(span);
        li.appendChild(lab);
        ul.appendChild(li);
    });
    if (!people.length) {
        var li2 = document.createElement('li');
        li2.className = 'text-muted';
        li2.textContent = 'Nobody in the household has an email address yet.';
        ul.appendChild(li2);
    }
    if (btn) { btn.hidden = !people.length; }
}

document.addEventListener('click', function (e) {
    var wa = e.target.closest('#sendWhatsApp');
    if (wa && !sendWords) { e.preventDefault(); }
});

function sendCopy() {
    if (!sendWords) { return; }
    var done = function () { sendStatus('Copied. Paste it wherever you like.'); };
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(sendWords.text).then(done, function () {
            sendStatus('Your browser would not copy. Select the text above instead.', true);
        });
    } else {
        sendStatus('Your browser would not copy. Select the text above instead.', true);
    }
}

function sendNative() {
    if (!sendWords || !navigator.share) { return; }
    navigator.share({ title: sendWords.subject, text: sendWords.text })
        .catch(function () { /* cancelled - nothing to say */ });
}

function sendEmail() {
    var boxes = document.querySelectorAll('#sendPeople input:checked');
    var to = [].map.call(boxes, function (b) { return b.value; });
    if (!to.length) { sendStatus('Tick who to send it to.', true); return; }
    var btn = document.getElementById('sendEmailBtn');
    if (btn) { btn.disabled = true; }
    sendStatus('Sending...');
    fetch('{% url "meal_plan_send" %}', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json',
                   'X-CSRFToken': '{{ csrf_token }}' },
        body: JSON.stringify({ view: '{{ view_mode }}',
                               date: '{{ anchor|date:"Y-m-d" }}', to: to })
    })
        .then(function (r) { return r.json(); })
        .then(function (d) {
            sendStatus(d.success ? d.message : d.error, !d.success);
        })
        .catch(function () { sendStatus('The email could not be sent. Try again.', true); })
        .then(function () { if (btn) { btn.disabled = false; } });
}
</script>


{# SORTABLE 1.15.0 - RO-1, 21 Oct 2026. The version and the URL are    #}
'''),
        (r'''        box.appendChild(small);
        card.appendChild(box);
        list.insertBefore(card, empty);
    });
''',
         r'''        box.appendChild(small);
        card.appendChild(box);

        // THE EYE - RA16, 23 Nov 2026. Demetri: "include a small icon
        // on the top right of each recipe box with the "eye" icon. If
        // the user presses this, then they see just the quick-view of
        // the recipe." The rest of the card still adds, as PS-1 made
        // it; the eye stops its own click from reaching the card.
        if (r.view) {
            var eye = document.createElement('button');
            eye.type = 'button';
            eye.className = 'pick-eye';
            eye.title = 'Quick view';
            eye.setAttribute('aria-label', 'Quick view of ' + r.name);
            eye.innerHTML = '<i class="fas fa-eye" aria-hidden="true"></i>';
            eye.onclick = function (ev) {
                ev.stopPropagation();
                pickPeek(card, r.view);
            };
            card.classList.add('has-eye');
            card.appendChild(eye);
        }
        list.insertBefore(card, empty);
    });
'''),
        (r'''    }
}

// CLICK IS THE ADD - PS-1, 19 Oct 2026.
''',
         r'''    }
}

// THE QUICK VIEW, OVER THE PICKER - RA16, 23 Nov 2026.
//
// RD-1's dialog, opened ON TOP of the picker rather than instead of
// it, so closing it puts you back in the list with your search and
// filters as you left them. Bootstrap 4.1 does not stack dialogs, so
// this one and its backdrop are lifted a layer (.is-over), and when it
// closes the page is told the picker is still open (modal-open), or
// the list underneath would stop scrolling.
//
// ITS FOOTER IS THE PICKER'S: Back to list, and Add to <the day>.
// Opening the whole recipe from here would leave the planner.
var pickPeekCard = null;

function pickPeek(card, url) {
    var box = document.getElementById('quickLookContent');
    var modal = document.getElementById('quickLookModal');
    if (!box || !modal || !window.jQuery) { window.location.href = url; return; }
    pickPeekCard = card;
    box.innerHTML = '<div class="modal-body text-center ql-none">' +
        '<i class="fas fa-spinner fa-spin fa-2x"></i></div>';
    modal.classList.add('is-over');
    window.jQuery(modal).modal('show');
    var drops = document.querySelectorAll('.modal-backdrop');
    if (drops.length > 1) { drops[drops.length - 1].classList.add('is-over'); }
    fetch(url, {credentials: 'same-origin'})
        .then(function (r) {
            if (!r.ok) { throw new Error(r.status); }
            return r.text();
        })
        .then(function (html) {
            box.innerHTML = html;
            pickPeekFoot(box);
        })
        .catch(function () {
            box.innerHTML = '<div class="modal-body ql-none">' +
                'Could not load the recipe.</div>';
        });
}

function pickPeekFoot(box) {
    var foot = box.querySelector('.modal-footer');
    if (!foot) {
        foot = document.createElement('div');
        foot.className = 'modal-footer';
        box.appendChild(foot);
    }
    while (foot.firstChild) { foot.removeChild(foot.firstChild); }
    foot.classList.add('ql-pickfoot');
    var back = document.createElement('button');
    back.type = 'button';
    back.className = 'btn action-secondary';
    back.textContent = 'Back to list';
    back.setAttribute('data-dismiss', 'modal');
    var add = document.createElement('button');
    add.type = 'button';
    add.className = 'btn action-primary';
    var day = document.getElementById('pickerDayName');
    add.textContent = 'Add to ' + ((day && day.textContent) || 'this day');
    add.onclick = function () {
        if (pickPeekCard) { pickAdd(pickPeekCard); }
        window.jQuery('#quickLookModal').modal('hide');
    };
    foot.appendChild(back);
    foot.appendChild(add);
}

// AND PUT THE PAGE BACK WHEN IT CLOSES. Bound when the document is
// parsed, for RL-1's reason: jQuery arrives at the END of base.
(function () {
    function bindPeek() {
        var el = document.getElementById('quickLookModal');
        if (!el || !window.jQuery) { return; }
        window.jQuery(el).on('hidden.bs.modal', function () {
            el.classList.remove('is-over');
            pickPeekCard = null;
            var picker = document.getElementById('pickerModal');
            if (picker && picker.classList.contains('show')) {
                document.body.classList.add('modal-open');
            }
        });
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bindPeek);
    } else {
        bindPeek();
    }
})();

// CLICK IS THE ADD - PS-1, 19 Oct 2026.
'''),
        (r'''// yes, the week too.
//
// ONE SORTABLE PER COLUMN, WITH NO SHARED GROUP, so nothing crosses
// from Tuesday to Wednesday. Dragging between columns writes a DATE
// and not an order, which is what Move on the chip menu already does.
//
// THE SAME ENDPOINT AS THE DAY CARD. A column is a date, and
// reorder_meal_day has taken a date and an order since RO-1 - it
// refuses an order that is not exactly the rows on that date, which
// is as true of a column as of a card.
(function () {
    if (typeof Sortable === 'undefined') { return; }
    var cols = document.querySelectorAll('.week-col-body[data-day]');
    if (!cols.length) { return; }
    [].forEach.call(cols, function (col) {
        if (!col.querySelector('.week-chip')) { return; }
        col.classList.add('is-draggable');
        new Sortable(col, {
            draggable: '.week-chip',
            ghostClass: 'sortable-ghost',
            dragClass: 'sortable-drag',
            chosenClass: 'sortable-chosen',
            animation: 150,
            onStart: function () { window.__alvDragEnded = 0; },
            onEnd: function () {
                window.__alvDragEnded = Date.now();
                saveColumnOrder(col);
            }
        });
    });
}());
''',
         r'''// yes, the week too.
//
// THE SAME ENDPOINT AS THE DAY CARD for an order. A column is a date,
// and reorder_meal_day has taken a date and an order since RO-1.
//
// AND NOW ACROSS DAYS - RA16, 23 Nov 2026. WD-1 kept each column to
// itself on purpose: a drop on another day writes a DATE, which is
// Move, and Move carries leftovers with their meal. Demetri, 23 Nov:
// "I want to be able to drag-and-drop Chicken - Cajun Garlic to
// another day on my calendar (instead of using the "Move To" option."
// So the columns - and the month's cells - share one group, and a drop
// on ANOTHER day posts to move_meal_entry, the very endpoint Move to...
// uses, so the leftovers still travel. A drop on the SAME column is
// still an order, as before. The day under the pointer is outlined
// while you drag, and the page the drop lands on offers Undo.
//
// THE DAY-DROP GROUP. Touch waits 200ms before a drag starts, so a
// finger can still scroll the page and a tap still opens the menu.
var MEAL_DRAG = {
    group: 'meal-days',
    ghostClass: 'sortable-ghost',
    dragClass: 'sortable-drag',
    chosenClass: 'sortable-chosen',
    animation: 150,
    delay: 200,
    delayOnTouchOnly: true
};

function dropMark(el) {
    document.querySelectorAll('.is-drop').forEach(function (x) {
        if (x !== el) { x.classList.remove('is-drop'); }
    });
    if (el) { el.classList.add('is-drop'); }
}

function dropMove(chip, target) {
    var ids = [].map.call(target.querySelectorAll('[data-chip]'),
        function (c) { return c.getAttribute('data-chip'); });
    var f = document.createElement('form');
    f.method = 'POST';
    f.action = '{% url "move_meal_entry" %}';
    f.hidden = true;
    var put = function (k, v) {
        var i = document.createElement('input');
        i.type = 'hidden'; i.name = k; i.value = v;
        f.appendChild(i);
    };
    put('csrfmiddlewaretoken', '{{ csrf_token }}');
    put('view', '{{ view_mode }}');
    put('from_date', '{{ anchor|date:"Y-m-d" }}');
    put('meal_entry_id', chip.getAttribute('data-chip'));
    put('date', target.getAttribute('data-day'));
    put('order', ids.join(','));
    put('dragged', '1');
    document.body.appendChild(f);
    f.submit();
}

function dragEnded(evt, sameList) {
    window.__alvDragEnded = Date.now();
    dropMark(null);
    if (evt.to !== evt.from) {
        dropMove(evt.item, evt.to);
        return;
    }
    if (sameList) { sameList(evt.from); }
}

(function () {
    if (typeof Sortable === 'undefined') { return; }
    var cols = document.querySelectorAll('.week-col-body[data-day]');
    if (!cols.length) { return; }
    [].forEach.call(cols, function (col) {
        col.classList.add('is-draggable');
        new Sortable(col, Object.assign({}, MEAL_DRAG, {
            draggable: '.week-chip',
            onStart: function () { window.__alvDragEnded = 0; },
            onMove: function (evt) {
                dropMark(evt.to !== evt.from ? evt.to : null);
            },
            onEnd: function (evt) { dragEnded(evt, saveColumnOrder); }
        }));
    });
}());

// THE MONTH - RA16. Its cells take a drop from another day; inside a
// cell there is no reordering (sort: false), because a cell can show
// "+2 more" and an order written from part of a day would be a guess.
// Below 768px the cells show dots, not chips, so there is nothing to
// drag on a phone - Move to... is the phone's way, as before.
(function () {
    if (typeof Sortable === 'undefined') { return; }
    var grid = document.querySelector('.month-grid');
    if (!grid) { return; }
    var cells = grid.querySelectorAll('.month-cell[data-day]');
    if (!cells.length) { return; }
    grid.classList.add('is-draggable');
    [].forEach.call(cells, function (cell) {
        new Sortable(cell, Object.assign({}, MEAL_DRAG, {
            draggable: '.month-chip',
            sort: false,
            onStart: function () { window.__alvDragEnded = 0; },
            onMove: function (evt) {
                dropMark(evt.to !== evt.from ? evt.to : null);
            },
            onEnd: function (evt) { dragEnded(evt, null); }
        }));
    });
}());
'''),
    ]),
    (os.path.join('pages', 'urls.py'), [
        (r'''    path('meal_plans/print/', views.meal_plan_print,
         name='meal_plan_print'),
    path('meal_plans/send_shopping_list/', views.send_meal_plan_shopping_list, name='send_meal_plan_shopping_list'),
    path('meal_plans/add/', views.add_meal_entry, name='add_meal_entry'),
''',
         r'''    path('meal_plans/print/', views.meal_plan_print,
         name='meal_plan_print'),
    # RA16, 23 Nov 2026 - Send the plan in view: its text for WhatsApp
    # and Copy (GET), or an email to the household roster (POST).
    path('meal_plans/send/', views.meal_plan_send, name='meal_plan_send'),
    path('meal_plans/send_shopping_list/', views.send_meal_plan_shopping_list, name='send_meal_plan_shopping_list'),
    path('meal_plans/add/', views.add_meal_entry, name='add_meal_entry'),
'''),
    ]),
    (os.path.join('pages', 'views', 'recipes', '__init__.py'), [
        (r'''from .shopping import *
from .meal_planning import *
from .spellcheck import *
from .recipe_crud import *
''',
         r'''from .shopping import *
from .meal_planning import *
from .meal_send import *     # RA16, 23 Nov 2026 - Send the plan.
from .spellcheck import *
from .recipe_crud import *
'''),
    ]),
    (os.path.join('pages', 'views', 'recipes', 'meal_planning.py'), [
        (r'''        ).order_by('name'),
    }
    # MS-1, 12 Nov 2026 - the Share dialog, on your own plan only.
    cal = getattr(request, 'meal_calendar', None)
''',
         r'''        ).order_by('name'),
    }
    # RA16, 23 Nov 2026 - THE UNDO FOR A DROP, offered once. Popped, so
    # a refresh or the next page does not offer it again.
    undo = request.session.pop('meal_move_undo', None)
    if isinstance(undo, dict) and undo.get('id'):
        try:
            back = datetime.strptime(undo.get('back', ''), '%Y-%m-%d').date()
            to = datetime.strptime(undo.get('to', ''), '%Y-%m-%d').date()
            context['move_undo'] = {
                'id': int(undo['id']), 'what': str(undo.get('what', '')),
                'back': back, 'to': to,
                'leftovers': int(undo.get('leftovers') or 0)}
        except (TypeError, ValueError):
            pass
    # MS-1, 12 Nov 2026 - the Share dialog, on your own plan only.
    cal = getattr(request, 'meal_calendar', None)
'''),
        (r'''        frontier = nxt

    with transaction.atomic():
        for child in travelling:
            child.date = child.date + delta
            child.save(update_fields=['date'])
        entry.date = when
        entry.save(update_fields=['date'])

    if travelling:
''',
         r'''        frontier = nxt

    was = entry.date
    with transaction.atomic():
        for child in travelling:
            child.date = child.date + delta
            child.save(update_fields=['date'])
        entry.date = when
        entry.save(update_fields=['date'])
        # DROPPED, NOT TYPED - RA16, 23 Nov 2026. A drag onto another
        # day posts here with dragged=1 and the order the target day
        # was left in, so the meal lands where it was let go rather
        # than wherever its old sort_order happens to put it. Ids that
        # are not on that day are ignored; rows the drag did not list
        # (leftovers that travelled in) go after.
        if request.POST.get('dragged') == '1':
            _drop_order(when, request.POST.get('order', ''))

    # AND IT CAN BE UNDONE - RA16. A drop is one careless flick away
    # from a wrong day in a way a typed date is not, so the planner
    # offers Undo once, on the page the move lands on. The session
    # holds only the row id and the two dates.
    if request.POST.get('dragged') == '1':
        request.session['meal_move_undo'] = {
            'id': entry.meal_entry_id, 'what': what,
            'back': was.strftime('%Y-%m-%d'),
            'to': when.strftime('%Y-%m-%d'),
            'leftovers': len(travelling)}
        return redirect(planner_back(request, when))

    if request.POST.get('undo') == '1':
        messages.success(request, 'Put "%s" back on %s'
                         % (what, when.strftime('%A, %d %B')))
        return redirect(planner_back(request, when))

    if travelling:
'''),
        (r'''                         % (what, when.strftime('%A, %d %B')))
    return redirect(planner_back(request, when))


''',
         r'''                         % (what, when.strftime('%A, %d %B')))
    return redirect(planner_back(request, when))


def _drop_order(when, raw):
    """Write the order a drop left a day in - RA16, 23 Nov 2026."""
    want = []
    for piece in (raw or '').split(','):
        piece = piece.strip()
        if piece.isdigit() and int(piece) not in want:
            want.append(int(piece))
    rows = list(MC.entries().filter(date=when)
                .order_by('sort_order', 'meal_entry_id'))
    if not want or not rows:
        return
    by_id = {r.meal_entry_id: r for r in rows}
    ordered = [by_id[i] for i in want if i in by_id]
    ordered += [r for r in rows if r.meal_entry_id not in want]
    for i, r in enumerate(ordered):
        if r.sort_order != i:
            r.sort_order = i
            r.save(update_fields=['sort_order'])


'''),
        (r'''            'minutes': (r.prep_time or 0) + (r.cook_time or 0),
            'photo': r.photo_url or '',
        })
    return JsonResponse({
''',
         r'''            'minutes': (r.prep_time or 0) + (r.cook_time or 0),
            'photo': r.photo_url or '',
            # RA16, 23 Nov 2026 - the card's eye opens this.
            'view': reverse('recipe_quicklook', args=[r.recipe_id]),
        })
    return JsonResponse({
'''),
    ]),
    (os.path.join('test_week_drag.py'), [
        (r'''

def save_column(js):
    a = js.find('function saveColumnOrder')
''',
         r'''

# RA16, 23 Nov 2026 - THE OPTIONS ARE SHARED NOW. The week columns and
# the month cells are bound with one object, MEAL_DRAG, so the four
# class names and the animation are read off it rather than off the
# column binding.
def drag_options(js):
    a = js.find('var MEAL_DRAG')
    b = js.find('function dropMark')
    return js[a:b] if 0 <= a < b else ''


def save_column(js):
    a = js.find('function saveColumnOrder')
'''),
        (r'''    col = column_binding(js)
    sav = save_column(js)
    g = d[GUIDE]
    return {
''',
         r'''    col = column_binding(js)
    sav = save_column(js)
    opt = drag_options(js) or col
    g = d[GUIDE]
    return {
'''),
        (r'''        '  dragging the chips themselves, with no grip in a 152px column':
            "draggable: '.week-chip'" in col,
        '  and NOT across days - no shared group':
            bool(col) and 'group' not in col,
        '  with the same four class names the rest of the app drags with':
            ("ghostClass: 'sortable-ghost'" in col
             and "dragClass: 'sortable-drag'" in col
             and "chosenClass: 'sortable-chosen'" in col
             and 'animation: 150' in col),
        '  and nothing is marked draggable until Sortable answers':
            bool(col) and "typeof Sortable === 'undefined'" in col,
''',
         r'''        '  dragging the chips themselves, with no grip in a 152px column':
            "draggable: '.week-chip'" in col,
        # RA16, 23 Nov 2026 - THIS WAS "and NOT across days - no shared
        # group", WD-1's design, and Demetri reversed it: "I want to be
        # able to drag-and-drop Chicken - Cajun Garlic to another day".
        # The columns share MEAL_DRAG's group now, and a drop on another
        # day is a Move (test_ra16_meal_send_drag drives it).
        '  and ACROSS days now, in one shared group - RA16':
            bool(col) and 'MEAL_DRAG' in col
            and "group: 'meal-days'" in opt,
        '  with the same four class names the rest of the app drags with':
            ("ghostClass: 'sortable-ghost'" in opt
             and "dragClass: 'sortable-drag'" in opt
             and "chosenClass: 'sortable-chosen'" in opt
             and 'animation: 150' in opt),
        '  and nothing is marked draggable until Sortable answers':
            bool(col) and "typeof Sortable === 'undefined'" in col,
'''),
        (r'''        'the guide says the week drags':
            'the meals themselves drag up and down their own column' in g,
        '  and names crossing days as what is still coming':
            'dragging a meal from one day to another' in g,
    }

''',
         r'''        'the guide says the week drags':
            'the meals themselves drag up and down their own column' in g,
        # RA16 - the guide no longer calls it "coming"; it says how.
        '  and says a meal drags to another day now - RA16':
            'drag a meal onto any other day' in g,
    }

'''),
        (r'''
# TWO BINDINGS, TWO GUARDS, ONE FLAG.
ok(JS.count("typeof Sortable === 'undefined'") == 2,
   'both bindings on this page guard on the library - the day card and '
   'the week columns', JS.count("typeof Sortable === 'undefined'"))

# WHO MAY DRAG, ASKED OF THE TEMPLATE AND NOT ASSUMED. The first draft
''',
         r'''
# TWO BINDINGS, TWO GUARDS, ONE FLAG.
# THREE SINCE RA16 - the month's cells are bound too.
ok(JS.count("typeof Sortable === 'undefined'") == 3,
   'all three bindings on this page guard on the library - the day '
   'card, the week columns and (RA16) the month cells',
   JS.count("typeof Sortable === 'undefined'"))

# WHO MAY DRAG, ASKED OF THE TEMPLATE AND NOT ASSUMED. The first draft
'''),
        (r'''   '  and all three kinds are still coloured - meal, note, leftover')

ok("if (!col.querySelector('.week-chip')) { return; }" in COL,
   'an empty column is not bound at all - there is nothing in it to '
   'put in an order')

# AND THE TAGS STILL BALANCE. BM-1's lesson, 22 October: a template
''',
         r'''   '  and all three kinds are still coloured - meal, note, leftover')

# RA16 - AN EMPTY COLUMN IS BOUND NOW. WD-1 skipped it because there
# was nothing in it to order; since a meal can be dropped onto another
# day, an empty day is exactly where one may go.
ok("if (!col.querySelector('.week-chip')) { return; }" not in COL,
   'an empty column IS bound now - RA16 - it is somewhere a meal can '
   'be dropped')

# AND THE TAGS STILL BALANCE. BM-1's lesson, 22 October: a template
'''),
        (r'''        ok(cur == 'grab', '  and the chip offers a grab cursor - %s' % cur)
        empty = pg.evaluate("""() => {
            let n = 0;
            document.querySelectorAll('.week-col-body[data-day]')
                .forEach(c => {
                    if (!c.querySelector('.week-chip')
                        && c.classList.contains('is-draggable')) { n += 1; }
                });
            return n;
        }""")
        ok(empty == 0,
           '  and a column with no meals in it was not bound at all',
           empty)
        pg.close()

''',
         r'''        ok(cur == 'grab', '  and the chip offers a grab cursor - %s' % cur)
        empty = pg.evaluate("""() => {
            let n = 0, b = 0;
            document.querySelectorAll('.week-col-body[data-day]')
                .forEach(c => {
                    if (!c.querySelector('.week-chip')) {
                        n += 1;
                        if (c.classList.contains('is-draggable')) { b += 1; }
                    }
                });
            return [n, b];
        }""")
        ok(empty[0] > 0 and empty[0] == empty[1],
           '  and a column with no meals in it IS bound - RA16, a drop '
           'target - %d of %d' % (empty[1], empty[0]), empty)
        pg.close()

'''),
        (r'''               'an onclick that opens one - %s' % pick, pick)

            # ---- AND NOTHING LANDED IN THE NEIGHBOURING COLUMN. No
            #      shared group, measured rather than asserted.
            others = pg.evaluate("""(wed) => {
                const out = {};
''',
         r'''               'an onclick that opens one - %s' % pick, pick)

            # ---- AND NOTHING LANDED IN THE NEIGHBOURING COLUMN. A drag
            #      WITHIN a column stays an order; RA16's group only
            #      lets a meal leave when it is let go over another day.
            others = pg.evaluate("""(wed) => {
                const out = {};
'''),
    ]),
    (os.path.join('test_bar_first.py'), [
        (r'''    # first - the whole of what BO-1 claimed - are unchanged, and
    # section 3 still reads the order off the rendered page.
    c['THE BAR READS PSSSSB - the finding'] = (seq == 'PSSSSB')
    c['  which is house order'] = bool(seq) and bool(HOUSE.match(seq))
    # NOT HERE: "exactly one primary". SPSB had one too - it is the
''',
         r'''    # first - the whole of what BO-1 claimed - are unchanged, and
    # section 3 still reads the order off the rendered page.
    # RA16, 23 Nov 2026 - PSSSSSB. Send... joined the secondaries,
    # after Print (Demetri: email, WhatsApp, etc the plan).
    c['THE BAR READS PSSSSSB - the finding'] = (seq == 'PSSSSSB')
    c['  which is house order'] = bool(seq) and bool(HOUSE.match(seq))
    # NOT HERE: "exactly one primary". SPSB had one too - it is the
'''),
    ]),
    (os.path.join('test_copy_menus.py'), [
        (r'''ok(bool(re.match(r'^P*S*F*B*$', seq)),
   'the bar is in house order: %s' % seq, seq)
ok(seq.count('S') == 4,
   'and carries four secondaries - Copy, Saved Menus, Print, Help',
   seq)
ok(seq.count('P') == 1, 'and exactly one primary, which is the verb', seq)
''',
         r'''ok(bool(re.match(r'^P*S*F*B*$', seq)),
   'the bar is in house order: %s' % seq, seq)
# RA16, 23 Nov 2026 - FIVE: Send... joined them, after Print.
ok(seq.count('S') == 5,
   'and carries five secondaries - Copy, Saved Menus, Print, Send, Help',
   seq)
ok(seq.count('P') == 1, 'and exactly one primary, which is the verb', seq)
'''),
    ]),
    (os.path.join('test_drift_root.py'), [
        (r'''                   'crs/submission_list.html')
CRS_N = 8
N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 93, 92   # GL-3, 29 Oct 2026 - the Greek Details pop-up brings one .modal-footer to Tenant Edit and one to Tenant Add. Both matchers rise by the same two.   # (was 91, 90)   # CR-2, 27 Oct 2026 - the receipt email pop-up brings one .modal-footer to Receipts and one to Receipt Details. Both matchers rise by the same two.   # (was N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 89, 88)   # CP-2, 21 Oct 2026 - three dialogs leave the planner and two arrive, so one .modal-footer wrapper goes. BOTH matchers fall by the same one, which is what an ordinary wrapper does and is the point of keeping the pair.   # (was 90, 89)   # RD-1 and RD-2, 19 Oct 2026 - the recipe quick-look dialog and the Move dialog each bring one .modal-footer. BOTH matchers rise by the same 2, which is what an ordinary wrapper does.   # (was 88, 87)   # MO-1, 19 Oct 2026 - two more dialogs on the planner - a planned night, and leftovers. Both matchers rise by the same 2, which is what an ordinary wrapper does.   # (was 86, 85)   # MW-1, 19 Oct 2026 - the planner gains three dialogs - copy a week, save a Menu, apply a Menu - and each brings one .modal-footer. Both matchers rise by the same 3, which is what an ordinary wrapper does.   # (was 83, 82)   # RT-1, 18 Oct 2026 - six .modal-footer wrappers went with the four meal-plan screens MN-1 retired, and the planner brought none. BOTH matchers fall by the same six, which is the point of keeping the pair: the wrappers that left were ordinary ones.   # (was 89, 88)   # CC-2, 17 Oct 2026 - the contact detail modal adds one .modal-footer. Both matchers rise by the same one.   # (was 88, 87)   # CC-1, 15 Oct 2026 - the celebration day sheet adds one .modal-footer. Both matchers rise by the same one.   # (was 87, 86)   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers went, and each took one .modal-footer wrapper with it. Both matchers fall by the same two, which is itself the point: the wrappers that left were ordinary ones.   # (was 89, 88)
GREY = 'rgb(233, 236, 239)'
GREY_INK = 'rgb(138, 151, 157)'
''',
         r'''                   'crs/submission_list.html')
CRS_N = 8
N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 94, 93   # RA16, 23 Nov 2026 - the planner's Send dialog brings one .modal-footer. Both matchers rise by the same one.   # (was 93, 92)   # GL-3, 29 Oct 2026 - the Greek Details pop-up brings one .modal-footer to Tenant Edit and one to Tenant Add. Both matchers rise by the same two.   # (was 91, 90)   # CR-2, 27 Oct 2026 - the receipt email pop-up brings one .modal-footer to Receipts and one to Receipt Details. Both matchers rise by the same two.   # (was N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 89, 88)   # CP-2, 21 Oct 2026 - three dialogs leave the planner and two arrive, so one .modal-footer wrapper goes. BOTH matchers fall by the same one, which is what an ordinary wrapper does and is the point of keeping the pair.   # (was 90, 89)   # RD-1 and RD-2, 19 Oct 2026 - the recipe quick-look dialog and the Move dialog each bring one .modal-footer. BOTH matchers rise by the same 2, which is what an ordinary wrapper does.   # (was 88, 87)   # MO-1, 19 Oct 2026 - two more dialogs on the planner - a planned night, and leftovers. Both matchers rise by the same 2, which is what an ordinary wrapper does.   # (was 86, 85)   # MW-1, 19 Oct 2026 - the planner gains three dialogs - copy a week, save a Menu, apply a Menu - and each brings one .modal-footer. Both matchers rise by the same 3, which is what an ordinary wrapper does.   # (was 83, 82)   # RT-1, 18 Oct 2026 - six .modal-footer wrappers went with the four meal-plan screens MN-1 retired, and the planner brought none. BOTH matchers fall by the same six, which is the point of keeping the pair: the wrappers that left were ordinary ones.   # (was 89, 88)   # CC-2, 17 Oct 2026 - the contact detail modal adds one .modal-footer. Both matchers rise by the same one.   # (was 88, 87)   # CC-1, 15 Oct 2026 - the celebration day sheet adds one .modal-footer. Both matchers rise by the same one.   # (was 87, 86)   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers went, and each took one .modal-footer wrapper with it. Both matchers fall by the same two, which is itself the point: the wrappers that left were ordinary ones.   # (was 89, 88)
GREY = 'rgb(233, 236, 239)'
GREY_INK = 'rgb(138, 151, 157)'
'''),
    ]),
    (os.path.join('test_meal_guide3.py'), [
        (r'''# buttons sit in on the planner bar, and a guide that disagrees with
# the screen about order is a guide somebody stops trusting.
ORDER = ('mp-overview', 'mp-calendar', 'mp-build', 'mp-week',
         'mp-shopping', 'mp-print', 'mp-permissions', 'mp-tips')
# The four things MH-2 promised and MW-1 and MO-1 built.
BUILT = ('repeating a whole week', 'saved menus',
''',
         r'''# buttons sit in on the planner bar, and a guide that disagrees with
# the screen about order is a guide somebody stops trusting.
# RA16, 23 Nov 2026 - AND A NINTH, after Printing: Sending a plan, the
# order Print and Send sit in on the bar.
ORDER = ('mp-overview', 'mp-calendar', 'mp-build', 'mp-week',
         'mp-shopping', 'mp-print', 'mp-send', 'mp-permissions', 'mp-tips')
# The four things MH-2 promised and MW-1 and MO-1 built.
BUILT = ('repeating a whole week', 'saved menus',
'''),
        (r'''    c['NOTHING THE PLANNER DOES IS DESCRIBED AS COMING'] = (
        bool(tabs) and not [w2 for w2 in BUILT for s in coming if w2 in s])
    c['  and what is NOT built is still named as coming'] = (
        any(OUTSTANDING in s.lower() for s in coming))
    # WD-1, 22 Oct 2026 - the coming sentence is no longer about
    # reordering anything: the week reorders. It is about crossing days,
    # which writes a date. Asking for the word 'reordering' here would
    # ask the guide to keep promising a thing that now ships.
    c['  and it is about crossing days, not ordering them'] = (
        any('from one day to another' in s.lower() for s in coming)
        and not any('reordering' in s.lower() for s in coming))

    # ---- 5. two tips, and they are about the two free things
''',
         r'''    c['NOTHING THE PLANNER DOES IS DESCRIBED AS COMING'] = (
        bool(tabs) and not [w2 for w2 in BUILT for s in coming if w2 in s])
    # RA16, 23 Nov 2026 - THE LAST PROMISE IS KEPT. Dragging a meal
    # from one day to another ships, so the guide stops promising it and
    # says how - the claim this was ("still named as coming") would now
    # ask the guide to promise a thing that is built.
    c['  and the last promise is kept - described now, not promised'] = (
        not any(OUTSTANDING in s.lower() for s in coming)
        and 'drag a meal onto any other day' in whole)
    # WD-1, 22 Oct 2026 - the coming sentence is no longer about
    # reordering anything: the week reorders. It is about crossing days,
    # which writes a date. Asking for the word 'reordering' here would
    # ask the guide to keep promising a thing that now ships.
    # (WD-1's "about crossing days, not ordering them" went with it:
    # there is no coming sentence left to be about either.)

    # ---- 5. two tips, and they are about the two free things
'''),
        (r'''    ok(got == ['Overview', 'The Calendar', 'Adding a Meal',
               'Moving a Week', 'Shopping List', 'Printing',
               'Who Can Do What', 'Tips'],
       '%d named tabs, in order, out of the real parser'
       % len(ORDER), got)
''',
         r'''    ok(got == ['Overview', 'The Calendar', 'Adding a Meal',
               'Moving a Week', 'Shopping List', 'Printing',
               'Sending a plan', 'Who Can Do What', 'Tips'],
       '%d named tabs, in order, out of the real parser'
       % len(ORDER), got)
'''),
        (r'''       'THROUGH THE RENDERER TOO: the guide promises nothing the '
       'planner already does', stale)
    ok(any(OUTSTANDING in s.lower() for s in coming),
       '  and still names what is not built', coming[:2])

    # THE CONTROL ON THE PROMISE GATE. An absence claim passes on a
''',
         r'''       'THROUGH THE RENDERER TOO: the guide promises nothing the '
       'planner already does', stale)
    # RA16, 23 Nov 2026 - and nothing is left to promise: crossing days
    # was the last outstanding thing, and it ships.
    ok(not any(OUTSTANDING in s.lower() for s in coming),
       '  and no longer promises dragging to another day - RA16 built it',
       coming[:2])

    # THE CONTROL ON THE PROMISE GATE. An absence claim passes on a
'''),
        (r'''                # mp-print has no 'before' to compare against either -
                # MH-5 creates it, as MH-3 created mp-week.
                if slug in ('mp-week', 'mp-print'):
                    continue
                a = shot(_br, old_by_slug[slug], w)
''',
         r'''                # mp-print has no 'before' to compare against either -
                # MH-5 creates it, as MH-3 created mp-week.
                # RA16, 23 Nov 2026 - nor mp-send, which RA16 creates.
                if slug in ('mp-week', 'mp-print', 'mp-send'):
                    continue
                a = shot(_br, old_by_slug[slug], w)
'''),
    ]),
    (os.path.join('test_meal_guide5.py'), [
        (r'''FILES = (HELP, MH, G3)

ORDER = ('mp-overview', 'mp-calendar', 'mp-build', 'mp-week',
         'mp-shopping', 'mp-print', 'mp-permissions', 'mp-tips')

# THE PROSE OF A SCREEN THAT IS GONE. This is the finding: each of
''',
         r'''FILES = (HELP, MH, G3)

# RA16, 23 Nov 2026 - AND A NINTH, after Printing: Sending a plan, the
# order Print and Send sit in on the bar.
ORDER = ('mp-overview', 'mp-calendar', 'mp-build', 'mp-week',
         'mp-shopping', 'mp-print', 'mp-send', 'mp-permissions', 'mp-tips')

# THE PROSE OF A SCREEN THAT IS GONE. This is the finding: each of
'''),
        (r'''    # asked as a delta it fails the control for being right. It is
    # asked in section 4, where an unchanging claim belongs.
    c['  and the word coming appears nowhere else'] = (
        len(coming) == 1)

    # ---- 8. the two suites that count tabs moved with them
''',
         r'''    # asked as a delta it fails the control for being right. It is
    # asked in section 4, where an unchanging claim belongs.
    # RA16, 23 Nov 2026 - NONE NOW. The one left was dragging a meal
    # from one day to another, and it ships.
    c['  and the word coming appears nowhere - RA16 kept the last'] = (
        len(coming) == 0)

    # ---- 8. the two suites that count tabs moved with them
'''),
        (r'''    ok(got == ['Overview', 'The Calendar', 'Adding a Meal',
               'Moving a Week', 'Shopping List', 'Printing',
               'Who Can Do What', 'Tips'],
       '%d named tabs, in order, out of the real parser'
       % len(ORDER), got)
''',
         r'''    ok(got == ['Overview', 'The Calendar', 'Adding a Meal',
               'Moving a Week', 'Shopping List', 'Printing',
               'Sending a plan', 'Who Can Do What', 'Tips'],
       '%d named tabs, in order, out of the real parser'
       % len(ORDER), got)
'''),
        (r'''# this changed in this round - MH-3 wrote the sentence - so neither is
# a delta; both are the thing the delta must not have broken.
ok(any(OUTSTANDING in x.lower() for x in coming_sentences(block)),
   'what is NOT built is still named as outstanding')
ok('def reorder_meal_day' in view and 'def move_meal_entry' in view,
   'CONTROL: ordering and MOVING are two endpoints, which is why one '
''',
         r'''# this changed in this round - MH-3 wrote the sentence - so neither is
# a delta; both are the thing the delta must not have broken.
# RA16, 23 Nov 2026 - BUILT NOW, so the guide must not still promise it.
ok(not any(OUTSTANDING in x.lower() for x in coming_sentences(block)),
   'what RA16 built is no longer named as outstanding')
ok('def reorder_meal_day' in view and 'def move_meal_entry' in view,
   'CONTROL: ordering and MOVING are two endpoints, which is why one '
'''),
    ]),
    (os.path.join('test_meal_help.py'), [
        (r'''# It sits after Shopping List, which is the order the two buttons sit
# in on the planner bar.
TABS = ('Overview', 'The Calendar', 'Adding a Meal', 'Moving a Week',
        'Shopping List', 'Printing', 'Who Can Do What', 'Tips')

passed = failed = skipped = 0
''',
         r'''# It sits after Shopping List, which is the order the two buttons sit
# in on the planner bar.
# RA16, 23 Nov 2026 - AND NINE. 'Sending a plan' follows Printing, the
# order Print and Send sit in on the planner bar.
TABS = ('Overview', 'The Calendar', 'Adding a Meal', 'Moving a Week',
        'Shopping List', 'Printing', 'Sending a plan', 'Who Can Do What',
        'Tips')

passed = failed = skipped = 0
'''),
        (r'''    # above and the other is the honest remainder. The claim is the
    # same claim - that the guide still says what it cannot do.
    ok(any('dragging a meal from one day to another' in s.lower()
           for s in coming),
       '  while what is NOT built is still named as outstanding',
       coming[:2])
    # AND IT REALLY IS NOT BUILT. Without this, the line above would
''',
         r'''    # above and the other is the honest remainder. The claim is the
    # same claim - that the guide still says what it cannot do.
    # RA16, 23 Nov 2026 - THE REMAINDER SHIPPED. Dragging a meal to
    # another day is built, so the guide describes it and promises it no
    # longer.
    ok(not any('dragging a meal from one day to another' in s.lower()
               for s in coming)
       and 'drag a meal onto any other day' in whole,
       '  and what RA16 built is described, not still promised',
       coming[:2])
    # AND IT REALLY IS NOT BUILT. Without this, the line above would
'''),
    ]),
    (os.path.join('test_pick_reload.py'), [
        (r'''    js = T.code_only_js(bundle[TPL])
    c = {}
    c['there is exactly one close handler'] = (
        js.count("on('hidden.bs.modal'") == 1)
    c['IT BINDS AFTER THE DOCUMENT IS PARSED - the finding, in one '
      'line'] = ("document.addEventListener('DOMContentLoaded', bind)"
''',
         r'''    js = T.code_only_js(bundle[TPL])
    c = {}
    # RA16, 23 Nov 2026 - TWO NOW, AND THE SECOND IS NOT THE PICKER'S.
    # The quick view opens over the picker from the card's eye, and its
    # own close handler (bindPeek) puts modal-open back for the picker
    # underneath. The picker still has exactly one.
    c['there is exactly one close handler on the picker, one on the quick '
      'view over it'] = (
        js.count("on('hidden.bs.modal'") == 2
        and js.count("getElementById('pickerModal');\n        if (!el") == 1)
    c['IT BINDS AFTER THE DOCUMENT IS PARSED - the finding, in one '
      'line'] = ("document.addEventListener('DOMContentLoaded', bind)"
'''),
    ]),
    (os.path.join('test_back_date.py'), [
        (r'''GATE = os.path.join(ROOT, PS1)
FILES = (TPL, VIEW)
N_FORMS = 9

passed = failed = skipped = 0
''',
         r'''GATE = os.path.join(ROOT, PS1)
FILES = (TPL, VIEW)
N_FORMS = 10   # RA16, 23 Nov 2026 - the Undo for a dropped meal is a form that sends both.   # (was 9)

passed = failed = skipped = 0
'''),
    ]),
    (os.path.join('test_pair_contrast.py'), [
        (r'''MARK = 'B-4b, 8 Oct 2026'

EXPECT_PAIRS = 758   # RA15, 23 Nov 2026 - user_activity.html, the Activity page: its tabs, the usage grid's four shades and its pill each set a fill and an ink, all AA.   # (was 752)   # RC-3, 12 Nov 2026 - cook mode on the recipe page: the full-screen step view sets the paper fill and its ink, and its Next button the accent fill and the on-accent ink. Two rules, pairs base already uses.   # (was 750)   # CR-2, 27 Oct 2026 - the receipt email pop-up, on Receipts and on Receipt Details: the message box and the Printed warning each set a fill and its ink, pairs base already uses.   # (was 746)   # ES-11, 26 Oct 2026 - the yellow signed-leases bar left Home and Notifications, and with it .lsa-strip's fill+ink pair on each page.   # (was 748)   # ES-9, 26 Oct 2026 - Home's Waiting for you icon chip, .ins-ic--wait, sets the warn-soft fill and warn-ink together, a pair base already uses.   # (was 747)   # ES-7, 25 Oct 2026 - two notes set a fill and an ink together: .hm-note on the Signature and Stamp screen and .ls-saved-note on the signing page, both on the accent pair this table already knows.   # (was 745)   # ES-6, 25 Oct 2026 - three more rules in ES-6's pages set a fill and an ink together, measured by this census on the full tree.   # (was 742)   # ES-4, 24 Oct 2026 - eleven in the public signing pages' own stylesheet. A standalone page cannot inherit a surface, so every one it draws sets both halves of the pair itself - which is exactly why this census asks about them.   # (was 731)   # ES-3a, 23 Oct 2026 - the lease signing register: three signer dots mirroring the good, bad and neutral pills, and the waiting-on-you note. Four rules, no new pairings.   # (was 727)   # MN-2, 21 Oct 2026 - the Saved Menus dialog gains the preset row CP-2 built for Copy, and .mn-preset[aria-pressed=true] sets a fill and an ink together exactly as .cp-preset does. One more pair, of tokens this table already knows.   # (was 726)   # RG-2, 21 Oct 2026 - two more rules set a fill and an ink together: the date field, which wears the paper token on the ink one like every other field in the system, and the line explaining the second Print press, which sits on the surface wash.   # (was 724)   # RG-1, 21 Oct 2026 - the printed sheet is drawn again from four layouts, and five more of its rules set a fill and an ink together: the pill in its three states, the today marker and the dimmed cell. Every one is a token pair this table already knows.   # (was 719)   # PP-1, 20 Oct 2026 - the printable plan sets
# both a ground and an ink on six rules. All house pairs off base's
# own tokens, so the AA table below is untouched and the gross count
''',
         r'''MARK = 'B-4b, 8 Oct 2026'

EXPECT_PAIRS = 761   # RA16, 23 Nov 2026 - meal_planner.html: the picker's eye, the Undo strip after a dropped meal and the Send dialog's preview each set a fill and an ink, all AA.   # (was 758)   # RA15, 23 Nov 2026 - user_activity.html, the Activity page: its tabs, the usage grid's four shades and its pill each set a fill and an ink, all AA.   # (was 752)   # RC-3, 12 Nov 2026 - cook mode on the recipe page: the full-screen step view sets the paper fill and its ink, and its Next button the accent fill and the on-accent ink. Two rules, pairs base already uses.   # (was 750)   # CR-2, 27 Oct 2026 - the receipt email pop-up, on Receipts and on Receipt Details: the message box and the Printed warning each set a fill and its ink, pairs base already uses.   # (was 746)   # ES-11, 26 Oct 2026 - the yellow signed-leases bar left Home and Notifications, and with it .lsa-strip's fill+ink pair on each page.   # (was 748)   # ES-9, 26 Oct 2026 - Home's Waiting for you icon chip, .ins-ic--wait, sets the warn-soft fill and warn-ink together, a pair base already uses.   # (was 747)   # ES-7, 25 Oct 2026 - two notes set a fill and an ink together: .hm-note on the Signature and Stamp screen and .ls-saved-note on the signing page, both on the accent pair this table already knows.   # (was 745)   # ES-6, 25 Oct 2026 - three more rules in ES-6's pages set a fill and an ink together, measured by this census on the full tree.   # (was 742)   # ES-4, 24 Oct 2026 - eleven in the public signing pages' own stylesheet. A standalone page cannot inherit a surface, so every one it draws sets both halves of the pair itself - which is exactly why this census asks about them.   # (was 731)   # ES-3a, 23 Oct 2026 - the lease signing register: three signer dots mirroring the good, bad and neutral pills, and the waiting-on-you note. Four rules, no new pairings.   # (was 727)   # MN-2, 21 Oct 2026 - the Saved Menus dialog gains the preset row CP-2 built for Copy, and .mn-preset[aria-pressed=true] sets a fill and an ink together exactly as .cp-preset does. One more pair, of tokens this table already knows.   # (was 726)   # RG-2, 21 Oct 2026 - two more rules set a fill and an ink together: the date field, which wears the paper token on the ink one like every other field in the system, and the line explaining the second Print press, which sits on the surface wash.   # (was 724)   # RG-1, 21 Oct 2026 - the printed sheet is drawn again from four layouts, and five more of its rules set a fill and an ink together: the pill in its three states, the today marker and the dimmed cell. Every one is a token pair this table already knows.   # (was 719)   # PP-1, 20 Oct 2026 - the printable plan sets
# both a ground and an ink on six rules. All house pairs off base's
# own tokens, so the AA table below is untouched and the gross count
'''),
    ]),
    (os.path.join('test_planner_back.py'), [
        (r'''# this one did: 11 -> 16 and 8 -> 9, by one named round.
N_REWROTE = 11
N_REDIRECTS = 18   # CP-2, 21 Oct 2026 - copy_meal_range asks the helper twice: once for the address every refusal returns to, and once for the one a successful copy returns to, which is the LANDING date rather than the day you started on.   # (was 16)
N_FORMS = 9
VIEWS = ('month', 'week', 'day')

''',
         r'''# this one did: 11 -> 16 and 8 -> 9, by one named round.
N_REWROTE = 11
N_REDIRECTS = 20   # RA16, 23 Nov 2026 - move_meal_entry asks the helper twice more: once for where a dropped meal lands (the page Undo is offered on), once for where an Undo lands.   # (was N_REDIRECTS = 18)   # CP-2, 21 Oct 2026 - copy_meal_range asks the helper twice: once for the address every refusal returns to, and once for the one a successful copy returns to, which is the LANDING date rather than the day you started on.   # (was 16)
N_FORMS = 10   # RA16, 23 Nov 2026 - the Undo for a dropped meal.   # (was 9)
VIEWS = ('month', 'week', 'day')

'''),
    ]),
]


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
    raise SystemExit('RA16 REFUSED: %s' % msg)


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

    pq = os.path.join(root, PS1)
    if "'test_ra16_meal_send_drag.py'" in read(pq):
        print('RA16 already applied.')
        return 0
    if "'test_ra15_activity_log.py'" not in read(pq):
        refuse('RA15 (apply_ra15_activity_log.py) is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('RA16 --check: %d file(s) would change, none written; %d '
              'ship with it.' % (len(out), len(CREATES)))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('RA16 applied - the planner: the eye, drag to another day, Send. No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
