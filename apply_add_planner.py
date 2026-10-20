# -*- coding: utf-8 -*-
"""apply_add_planner.py - round AP-1, 20 Oct 2026.

RELEASE 4, PUSH 3. PUT A RECIPE ON A DAY WITHOUT LEAVING THE LIBRARY.

Demetri, asked what should happen after adding from Recipe Management:
"stay put, with a toast - Fakes Soupa added to Sat 24 Oct - and an
Undo." And, asked where the control goes: "Beside the heart on the
photo."

FOUR HEARTS, SO FOUR ICONS. The page draws every card twice - server
rendered, and again as a JavaScript template literal that redraws
after a search, a filter or Load more. A round that lands in two of
the four works until you type in the search box.

BESIDE THE HEART MEANS BESIDE THE HEART, and the heart is in two
different places: an overlay on the photograph in the grid, and the
actions group in the list row, which has no photograph to overlay.
The icon follows it rather than inventing a third position.

BOTH OVERLAYS GO TO 44px ON A PHONE - his answer. The heart has been
28px there, under the house floor, since it was written. Measured
before it was changed: the image is 172x120 at 390px and the heart
sits at 6,6, so two 44px targets and a gap come to 100px of 172 and
fit with room. Enlarging the heart is a visible change to an existing
control and was taken as a decision, not slipped in.

THREE THINGS THIS ROUND CANNOT REUSE, which is why it is the big one.

    no toast        base owns no toast and no snackbar. It cannot be
                    Django messages either: those need a page render
                    and the whole point is that you stay put.
    no mini month   MV-2 deleted the only one in the application on
                    the 19th, measured, because it cost the planner a
                    third of its width. Inside a popover it costs
                    nothing, so this one is drawn in JavaScript.
    no undo         add_meal_entry's JSON branch returns the DAY, not
                    the row it just created - it does not even keep
                    the object. Undo had nothing to point at.

THE TOAST GOES IN BASE. base already owns .modal-overlay,
.alv-modal-head and RD-2's chip menu, and its own comment records what
happened the last time a screen hand-rolled a copy of shared furniture:
an eleven-rule overlay in JavaScript where .alv-modal-head could never
reach it. Every screen gets a toast out of this.

ONE POPOVER, MOVED TO THE PRESSED ICON - RD-2's pattern, for RD-2's
reason: 324 recipes times two layouts is 648 popovers if each card
carries its own, and only ever one of them is open.

AND IT POSTS THE WAY THIS PAGE ALREADY POSTS: getCookie('csrftoken')
in an X-CSRFToken header, which is what toggleFavourite and
duplicateRecipe do. The BODY is form-encoded rather than JSON, because
add_meal_entry reads request.POST and a JSON body leaves that empty -
the same URLSearchParams shape the planner's own JavaScript uses.

NOT data-recipe-id, ON PURPOSE. test_js_handlers counts every
data-recipe-id on this page and pairs it with a data-recipe-name; its
census is about the delete and duplicate buttons. These icons carry
data-plan-id, so a control with a different errand does not move
somebody else's number.

Idempotent. Every file backed up to .bak_addplanner.
"""
import os
import re
import sys

SUFFIX = '.bak_addplanner'
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
BASE = os.path.join('pages', 'templates', 'base.html')
RM = os.path.join('pages', 'templates', 'recipe_management.html')
ME = 'test_add_planner.py'
PATCHER = 'apply_add_planner.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'AP-1, 20 Oct 2026'
CHECK = False
CREATES = ()

N_ICONS = 4


# =====================================================================
# 1. THE ENDPOINT HANDS BACK THE ROW IT MADE
# =====================================================================

ADD_WAS = """    last = MealEntry.objects.filter(date=when).aggregate(
        Max('sort_order'))['sort_order__max']
    MealEntry.objects.create(
        date=when, recipe=recipe, servings=servings,
        sort_order=(last or 0) + 1, created_by=request.user)

    # THE DIALOG WANTS THE DAY BACK, NOT A REDIRECT - PS-1,
    # 19 Oct 2026. The form post is unchanged and still redirects;
    # this branch exists for the picker, which stays open.
    if request.POST.get('json'):
        return JsonResponse(day_payload(when))"""
ADD_NOW = """    last = MealEntry.objects.filter(date=when).aggregate(
        Max('sort_order'))['sort_order__max']
    # KEPT, WHICH IT WAS NOT - AP-1, 20 Oct 2026. The row was created
    # and dropped on the floor, so the JSON branch could describe the
    # DAY and never the thing it had just added. An Undo needs
    # something to point at.
    entry = MealEntry.objects.create(
        date=when, recipe=recipe, servings=servings,
        sort_order=(last or 0) + 1, created_by=request.user)

    # THE DIALOG WANTS THE DAY BACK, NOT A REDIRECT - PS-1,
    # 19 Oct 2026. The form post is unchanged and still redirects;
    # this branch exists for the picker, which stays open.
    #
    # AP-1 ADDS ONE KEY AND MOVES NOTHING. The picker reads the keys
    # it knows and ignores the rest, so added_id reaches the library
    # without the picker noticing it went past.
    if request.POST.get('json'):
        payload = day_payload(when)
        payload['added_id'] = entry.meal_entry_id
        payload['added_name'] = recipe.recipe_name
        # WITH THE WEEKDAY - AP-1, 20 Oct 2026. Demetri's words were
        # "Fakes Soupa added to Sat 24 Oct", and the weekday is the
        # half that tells you whether you meant it. day_label itself
        # is untouched: it is the vocabulary of every other message on
        # the planner and this is one toast, not a new dialect.
        payload['added_label'] = '%s %s' % (when.strftime('%a'),
                                            day_label(when))
        return JsonResponse(payload)"""


# =====================================================================
# 2. THE TOAST, IN BASE
# =====================================================================

TOAST_WAS = """/* ===== /ALV LANDING TABS v1 ===== */"""
TOAST_NOW = """/* ===== /ALV LANDING TABS v1 ===== */

/* ===== THE TOAST - AP-1, 20 Oct 2026 =============================
   A thing that happened, said without taking the page away, and a
   chance to put it back.

   IN BASE, because base owns the shared furniture: .modal-overlay,
   .alv-modal-head and RD-2's chip menu are all here, and base's own
   note records what it cost the last time a screen kept a private
   copy of one. Nothing about this is specific to recipes.

   IT IS NOT django messages. Those arrive with a page render, and
   the whole point of Demetri's answer - "stay put, with a toast and
   an Undo" - is that no page is rendered.

   NO COLOUR HERE THAT IS NOT A TOKEN. */
.alv-toast-dock {
    position: fixed;
    left: 50%;
    bottom: 24px;
    transform: translateX(-50%);
    z-index: 2000;
    display: flex;
    flex-direction: column;
    gap: 8px;
    /* THE DOCK IS NOT A TARGET, only the toasts in it - otherwise an
       invisible strip across the foot of every page would eat clicks
       meant for whatever is under it. */
    pointer-events: none;
}
.alv-toast {
    pointer-events: auto;
    display: flex;
    align-items: center;
    gap: 14px;
    max-width: min(92vw, 520px);
    padding: 12px 16px;
    border-radius: var(--alv-radius-sm);
    background: var(--alv-ink);
    color: var(--alv-on-accent);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.22);
    font-size: 14px;
    line-height: 1.35;
}
.alv-toast-text { flex: 1 1 auto; }
.alv-toast-undo {
    flex: 0 0 auto;
    border: 0;
    background: none;
    color: var(--alv-on-accent);
    font: inherit;
    font-weight: 600;
    text-decoration: underline;
    cursor: pointer;
    /* 44px, because it is a thumb target and it is the control that
       takes something back. */
    min-height: 44px;
    padding: 0 6px;
}
.alv-toast-undo:focus-visible {
    outline: 2px solid var(--alv-on-accent);
    outline-offset: 2px;
}
/* AND screen, NOT a bare max-width - a clause naming no media type
   matches print too, which test_print_queries has enforced since the
   21 September print-leak round. */
@media screen and (max-width: 767px) {
    .alv-toast-dock {
        left: 12px;
        right: 12px;
        bottom: 12px;
        transform: none;
    }
    .alv-toast { max-width: none; }
}
@media (prefers-reduced-motion: no-preference) {
    .alv-toast { animation: alv-toast-in 160ms ease-out; }
}
@keyframes alv-toast-in {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: none; }
}"""

TOASTJS_WAS = """<script>
/* alv-sticky-cue"""
TOASTJS_NOW = """<script>
/* alv-toast -------------------------------------------------------
   window.alvToast(text, {undo: fn, seconds: n})

   AP-1, 20 Oct 2026. One dock, made on first use; one toast per
   call; the Undo slot only appears when something can be undone.

   PLAIN DOM, SO THERE IS NOTHING TO WAIT FOR. PS-1 learned on the
   19th that a top-level call into jQuery throws when it has not
   loaded and takes every statement after it down with it, and RL-1
   learned the next day that guarding it turns "not loaded yet" into
   "silently never". This touches neither.

   THE UNDO FIRES ONCE. A second press of a button already gone from
   the screen is still possible with a keyboard, and removing the
   same row twice is a 404 the person did not cause. */
(function () {
    function dock() {
        var d = document.getElementById('alvToastDock');
        if (!d) {
            d = document.createElement('div');
            d.id = 'alvToastDock';
            d.className = 'alv-toast-dock';
            /* POLITE, NOT ASSERTIVE. A confirmation is not an alert. */
            d.setAttribute('aria-live', 'polite');
            document.body.appendChild(d);
        }
        return d;
    }

    window.alvToast = function (text, opts) {
        opts = opts || {};
        var box = document.createElement('div');
        box.className = 'alv-toast';
        var span = document.createElement('span');
        span.className = 'alv-toast-text';
        /* SET AS TEXT, NEVER AS MARKUP - a recipe name is somebody
           else's text. The word this round must not write is the one
           its own gate forbids, so the gate reads as one thing. */
        span.textContent = text;
        box.appendChild(span);

        var timer = null;
        function close() {
            if (timer) { clearTimeout(timer); timer = null; }
            if (box.parentNode) { box.parentNode.removeChild(box); }
        }

        if (typeof opts.undo === 'function') {
            var b = document.createElement('button');
            b.type = 'button';
            b.className = 'alv-toast-undo';
            b.textContent = 'Undo';
            var spent = false;
            b.addEventListener('click', function () {
                if (spent) { return; }
                spent = true;
                close();
                opts.undo();
            });
            box.appendChild(b);
        }

        dock().appendChild(box);
        timer = setTimeout(close, (opts.seconds || 7) * 1000);
        return close;
    };
})();
</script>

<script>
/* alv-sticky-cue"""


# =====================================================================
# 3. THE ICON, FOUR TIMES
# =====================================================================

GRID_HEART = """            <button type="button"
                    class="recipe-favourite-btn {% if recipe.recipe_id in user_favourites %}is-favourite{% endif %}"
                    onclick="toggleFavourite({{ recipe.recipe_id }}, this)"
                    title="{% if recipe.recipe_id in user_favourites %}Remove from Favourites{% else %}Add to Favourites{% endif %}">
                <i class="fas fa-heart"></i>
            </button>
"""
GRID_PLAN = """            {# BESIDE THE HEART - AP-1, 20 Oct 2026, which is where  #}
            {# Demetri put it. A SIBLING of the photo link RD-3 made, #}
            {# never a child of it, so pressing this never opens the  #}
            {# quick-look: closest() cannot reach a trigger it is not #}
            {# inside.                                                #}
            {% if perms.auth.can_edit_recipes %}
            <button type="button" class="recipe-plan-btn"
                    data-plan-id="{{ recipe.recipe_id }}"
                    data-plan-name="{{ recipe.recipe_name }}"
                    title="Add to the planner"
                    aria-label="Add {{ recipe.recipe_name }} to the planner">
                <i class="fas fa-calendar-plus"></i>
            </button>
            {% endif %}
"""

LIST_HEART = """            <button type="button"
                    class="recipe-list-action-btn recipe-list-favourite-btn {% if recipe.recipe_id in user_favourites %}is-favourite{% endif %}"
                    onclick="toggleFavourite({{ recipe.recipe_id }}, this)"
                    title="{% if recipe.recipe_id in user_favourites %}Remove from Favourites{% else %}Add to Favourites{% endif %}">
                <i class="fas fa-heart"></i>
            </button>
"""
LIST_PLAN = """            {# BESIDE THE HEART - AP-1, 20 Oct 2026. The list row has #}
            {# no photograph to lie on, so the icon follows the heart  #}
            {# into the actions group rather than inventing a third    #}
            {# position for itself.                                    #}
            {% if perms.auth.can_edit_recipes %}
            <button type="button"
                    class="recipe-list-action-btn recipe-list-plan-btn"
                    data-plan-id="{{ recipe.recipe_id }}"
                    data-plan-name="{{ recipe.recipe_name }}"
                    title="Add to the planner"
                    aria-label="Add {{ recipe.recipe_name }} to the planner">
                <i class="fas fa-calendar-plus"></i>
            </button>
            {% endif %}
"""

JSGRID_HEART = """                <button type="button"
                        class="recipe-favourite-btn ${recipe.is_favourite ? 'is-favourite' : ''}"
                        onclick="toggleFavourite(${recipe.recipe_id}, this)"
                        title="${recipe.is_favourite ? 'Remove from Favourites' : 'Add to Favourites'}">
                    <i class="fas fa-heart"></i>
                </button>
"""
JSGRID_PLAN = """                ${USER_CAN_EDIT_RECIPES ? `
                <button type="button" class="recipe-plan-btn"
                        data-plan-id="${recipe.recipe_id}"
                        data-plan-name="${escapeHtml(recipe.recipe_name)}"
                        title="Add to the planner"
                        aria-label="Add ${escapeHtml(recipe.recipe_name)} to the planner">
                    <i class="fas fa-calendar-plus"></i>
                </button>` : ''}
"""

JSLIST_HEART = """                <button type="button"
                        class="recipe-list-action-btn recipe-list-favourite-btn ${recipe.is_favourite ? 'is-favourite' : ''}"
                        onclick="toggleFavourite(${recipe.recipe_id}, this)"
                        title="${recipe.is_favourite ? 'Remove from Favourites' : 'Add to Favourites'}">
                    <i class="fas fa-heart"></i>
                </button>
"""
JSLIST_PLAN = """                ${USER_CAN_EDIT_RECIPES ? `
                <button type="button"
                        class="recipe-list-action-btn recipe-list-plan-btn"
                        data-plan-id="${recipe.recipe_id}"
                        data-plan-name="${escapeHtml(recipe.recipe_name)}"
                        title="Add to the planner"
                        aria-label="Add ${escapeHtml(recipe.recipe_name)} to the planner">
                    <i class="fas fa-calendar-plus"></i>
                </button>` : ''}
"""


# =====================================================================
# 4. THE CONSTANT THE BUILDERS NEED
# =====================================================================
#
# IT DID NOT EXIST. The page declares USER_CAN_EDIT_PERSONAL and
# nothing else, and the first draft of the two builders above read
# USER_CAN_EDIT_RECIPES - a ReferenceError the first time a search
# redrew a card, taking every statement after it in that block with
# it. PS-1 paid exactly that on the 19th.
#
# AND IT IS THE RIGHT PERMISSION, not the convenient one.
# add_meal_entry is decorated with can_edit_recipes; can_edit_personal
# guards editing a recipe, which is a different question - and the
# difference is what made the popover 403 before it carried its own
# token.
CONST_WAS = """const USER_CAN_EDIT_PERSONAL = {% if perms.auth.can_edit_personal %}true{% else %}false{% endif %};"""
CONST_NOW = """const USER_CAN_EDIT_PERSONAL = {% if perms.auth.can_edit_personal %}true{% else %}false{% endif %};
// AP-1, 20 Oct 2026 - the permission add_meal_entry really asks for.
const USER_CAN_EDIT_RECIPES = {% if perms.auth.can_edit_recipes %}true{% else %}false{% endif %};"""

# =====================================================================
# 5. THE RULES
# =====================================================================

CSS_WAS = """/* Favourite Heart Button */"""
CSS_NOW = """/* THE PLANNER ICON - AP-1, 20 Oct 2026 ---------------------------
   Beside the heart, which is where Demetri put it, so it takes the
   heart's own geometry and steps one target to the right: 8 for the
   edge, 32 for the heart, 8 for the gap.

   IT IS A SIBLING OF RD-3's PHOTO LINK, never a child, so pressing it
   cannot open the quick-look. That is a fact about where the element
   sits rather than a guard that has to be maintained. */
.recipe-plan-btn {
    position: absolute;
    top: 8px;
    left: 48px;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: none;
    background: rgba(255, 255, 255, 0.9);
    color: var(--alv-accent-ink);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 14px;
    z-index: 2;
}
.recipe-plan-btn:hover { background: var(--alv-paper); color: var(--alv-accent); }
.recipe-plan-btn:focus-visible {
    outline: 2px solid var(--alv-accent);
    outline-offset: 2px;
}
/* IN THE LIST ROW IT IS NOT AN OVERLAY. There is no photograph to lie
   on, so it joins the actions group and wears that group's shape -
   which is why it does not carry .recipe-plan-btn at all. */
.recipe-list-plan-btn { color: var(--alv-accent-ink); }
.recipe-list-plan-btn:hover { color: var(--alv-accent); }

/* THE POPOVER - one for the page, moved to whichever icon was
   pressed. RD-2's pattern and RD-2's reason: 324 recipes in two
   layouts is 648 of these if each card carries its own, and only ever
   one is open. */
.plan-pop {
    position: absolute;
    z-index: 1200;
    width: 280px;
    padding: 12px;
    border: 1px solid var(--alv-line);
    border-radius: var(--alv-radius-sm);
    background: var(--alv-paper);
    box-shadow: 0 8px 26px rgba(0, 0, 0, 0.16);
}
.plan-pop[hidden] { display: none; }
.plan-pop-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 13px;
    font-weight: 600;
    color: var(--alv-ink);
    margin-bottom: 10px;
}
.plan-pop-x {
    border: 0;
    background: none;
    color: var(--alv-ink-soft);
    font-size: 20px;
    line-height: 1;
    cursor: pointer;
    min-width: 44px;
    min-height: 44px;
}
.plan-pop-quick { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
.plan-quick {
    flex: 1 1 auto;
    min-height: 44px;
    padding: 0 10px;
    border: 1px solid var(--alv-accent-line);
    border-radius: 999px;
    background: var(--alv-accent-soft);
    color: var(--alv-accent-ink);
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
}
.plan-quick:hover { background: var(--alv-paper); }
.plan-cal-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 6px;
    font-size: 13px;
    font-weight: 600;
    color: var(--alv-ink);
}
.plan-cal-nav {
    min-width: 36px;
    min-height: 36px;
    border: 1px solid var(--alv-line);
    border-radius: var(--alv-radius-sm);
    background: var(--alv-surface);
    color: var(--alv-ink-soft);
    cursor: pointer;
}
.plan-cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; }
.plan-cal-dow {
    text-align: center;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--alv-ink-faint);
    padding-bottom: 2px;
}
.plan-day {
    min-height: 34px;
    border: 1px solid transparent;
    border-radius: var(--alv-radius-sm);
    background: none;
    color: var(--alv-ink);
    font-size: 12px;
    cursor: pointer;
}
.plan-day:hover { background: var(--alv-accent-soft); }
.plan-day.is-today { border-color: var(--alv-accent); font-weight: 700; }
.plan-day.is-blank { visibility: hidden; cursor: default; }
.plan-day:focus-visible {
    outline: 2px solid var(--alv-accent);
    outline-offset: -2px;
}

/* Favourite Heart Button */"""

PHONE_WAS = """    .recipe-favourite-btn { width: 28px; height: 28px; font-size: 13px; top: 6px; left: 6px; }"""
PHONE_NOW = """    /* BOTH OVERLAYS ARE 44px HERE - AP-1, 20 Oct 2026, and the heart
       grows with the new icon rather than sitting beside it two
       thirds the size. It has been 28px since it was written, under
       the house floor for a thumb, and putting a 44px control next to
       it would have made that visible instead of fixing it.
       MEASURED FIRST: the image is 172x120 at 390px, so 6 + 44 + 6 +
       44 is 100 of 172 and both fit with room to spare. */
    .recipe-favourite-btn { width: 44px; height: 44px; font-size: 15px; top: 6px; left: 6px; }
    .recipe-plan-btn { width: 44px; height: 44px; font-size: 15px; top: 6px; left: 56px; }
    /* THE POPOVER IS A SHEET ON A PHONE. 280px floating beside a 44px
       button on a 390px screen is a popover half off the edge. */
    .plan-pop { position: fixed; left: 12px; right: 12px; bottom: 12px; top: auto; width: auto; }"""

# =====================================================================
# 6. THE POPOVER, AND ITS BEHAVIOUR, IN A BLOCK OF THEIR OWN
# =====================================================================

POP_WAS = """{% include 'recipe_quicklook_shell.html' %}"""
POP_NOW = """{# ONE POPOVER, MOVED TO THE PRESSED ICON - AP-1, 20 Oct 2026.  #}
{# RD-2's pattern: 324 recipes in two layouts is 648 of these if  #}
{# each card carries its own, and only one is ever open.          #}
{#                                                                #}
{# THE ROUTES COME FROM THE URLCONF and ride on the element,      #}
{# because RD-1's shell head records what the alternative costs:  #}
{# WCIM built a path by hand and a route that moves takes it with #}
{# it silently.                                                   #}
{% if perms.auth.can_edit_recipes %}
<div id="planPop" class="plan-pop" role="dialog"
     aria-labelledby="planPopTitle" hidden
     data-add-url="{% url 'add_meal_entry' %}"
     data-remove-url="{% url 'remove_meal_entry' %}">
    {# ITS OWN TOKEN, AND IT HAS TO BE ITS OWN. The only csrf_token  #}
    {# on this page sits behind can_edit_personal, which is a        #}
    {# DIFFERENT permission from the one that draws this icon, so    #}
    {# somebody who may plan meals but not edit recipes got the icon #}
    {# and a 403. Found by driving it, not by reading it.            #}
    {#                                                               #}
    {# RENDERING THE TAG ALSO SETS THE COOKIE, which is the other    #}
    {# half: getCookie returned an empty string because nothing on   #}
    {# the page had asked Django for a token at all.                 #}
    {% csrf_token %}
    <div class="plan-pop-head">
        <span id="planPopTitle">Add to the planner</span>
        <button type="button" class="plan-pop-x" id="planPopClose"
                aria-label="Close">&times;</button>
    </div>
    <div class="plan-pop-quick">
        <button type="button" class="plan-quick" data-plan-when="today">Tonight</button>
        <button type="button" class="plan-quick" data-plan-when="tomorrow">Tomorrow</button>
        <button type="button" class="plan-quick" data-plan-when="saturday">This Saturday</button>
    </div>
    <div class="plan-cal-head">
        <button type="button" class="plan-cal-nav" id="planPrev"
                aria-label="The month before"><i class="fas fa-chevron-left"></i></button>
        <span id="planCalLabel"></span>
        <button type="button" class="plan-cal-nav" id="planNext"
                aria-label="The month after"><i class="fas fa-chevron-right"></i></button>
    </div>
    <div class="plan-cal-grid" id="planCalGrid"></div>
</div>

{# A BLOCK OF ITS OWN, LIKE RD-1's SHELL - AP-1, 20 Oct 2026.     #}
{# This was first written into the page's big script block, where #}
{# it sat downstream of everything above it: anything that throws #}
{# up there takes every statement after it, which is the fault    #}
{# PS-1 shipped on the 19th when a top-level jQuery call killed   #}
{# PF-2's outside-click handler. A block of its own cannot be     #}
{# taken down by somebody else's line, and the suite caught this  #}
{# by pressing the icon on a page served without jQuery.          #}
<script>
(function () {
    var pop = null, forId = null, forName = '', shown = new Date();

    function el(id) { return document.getElementById(id); }

    function iso(d) {
        return d.getFullYear() + '-' +
            String(d.getMonth() + 1).padStart(2, '0') + '-' +
            String(d.getDate()).padStart(2, '0');
    }

    // THE SHORTCUTS, AS DATES. "This Saturday" means the Saturday of
    // the week you are in, and on a Saturday it means today - not a
    // week away, which is what counting forward from tomorrow gives.
    function when(code) {
        var d = new Date();
        d.setHours(12, 0, 0, 0);
        if (code === 'tomorrow') { d.setDate(d.getDate() + 1); }
        if (code === 'saturday') { d.setDate(d.getDate() + ((6 - d.getDay()) + 7) % 7); }
        return d;
    }

    function draw() {
        var grid = el('planCalGrid');
        if (!grid) { return; }
        // EMPTIED BY REMOVING CHILDREN, not by assigning markup. A
        // round whose comment spells the word its own gate forbids
        // makes that gate unreadable - check_gates said so twice
        // before this ran, both times about a COMMENT. To a substring
        // search, a note about a thing is the thing.
        while (grid.firstChild) { grid.removeChild(grid.firstChild); }
        el('planCalLabel').textContent = shown.toLocaleDateString(
            undefined, {month: 'long', year: 'numeric'});
        ['M', 'T', 'W', 'T', 'F', 'S', 'S'].forEach(function (n) {
            var h = document.createElement('div');
            h.className = 'plan-cal-dow';
            h.textContent = n;
            grid.appendChild(h);
        });
        var first = new Date(shown.getFullYear(), shown.getMonth(), 1);
        // MONDAY FIRST, like every other calendar in this application.
        var lead = (first.getDay() + 6) % 7;
        var days = new Date(shown.getFullYear(), shown.getMonth() + 1, 0)
            .getDate();
        var today = iso(new Date());
        for (var i = 0; i < lead; i++) {
            var b = document.createElement('button');
            b.type = 'button';
            b.className = 'plan-day is-blank';
            b.disabled = true;
            grid.appendChild(b);
        }
        for (var day = 1; day <= days; day++) {
            var d = new Date(shown.getFullYear(), shown.getMonth(), day);
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'plan-day' + (iso(d) === today ? ' is-today' : '');
            btn.textContent = day;
            btn.setAttribute('data-plan-date', iso(d));
            grid.appendChild(btn);
        }
    }

    function close() {
        if (pop) { pop.hidden = true; }
        forId = null;
    }

    function open(btn) {
        pop = el('planPop');
        if (!pop) { return; }
        forId = btn.getAttribute('data-plan-id');
        forName = btn.getAttribute('data-plan-name') || 'That recipe';
        el('planPopTitle').textContent = 'Add ' + forName;
        shown = new Date();
        draw();
        pop.hidden = false;
        // PLACED UNDER THE ICON THAT OPENED IT, in page coordinates,
        // because the card it belongs to scrolls.
        var r = btn.getBoundingClientRect();
        pop.style.top = (r.bottom + window.scrollY + 6) + 'px';
        pop.style.left = Math.max(
            8, Math.min(r.left + window.scrollX,
                        window.scrollX + document.documentElement.clientWidth
                        - pop.offsetWidth - 8)) + 'px';
        var x = el('planPopClose');
        if (x) { x.focus(); }
    }

    // THE TOKEN COMES FROM THE POPOVER'S OWN FIELD, and falls back to
    // the cookie for any page that sets one. Reading the cookie alone
    // was the first spelling and it returned an empty string here,
    // because nothing on this page had asked for a token.
    function token() {
        var f = pop && pop.querySelector('[name=csrfmiddlewaretoken]');
        if (f && f.value) { return f.value; }
        return (typeof getCookie === 'function' &&
                getCookie('csrftoken')) || '';
    }

    function body(obj) {
        var p = new URLSearchParams();
        Object.keys(obj).forEach(function (k) { p.append(k, obj[k]); });
        return p;
    }

    // FORM-ENCODED, NOT JSON. add_meal_entry reads request.POST, and
    // a JSON body leaves that empty - the planner's own JavaScript
    // posts the same way.
    function add(dateStr) {
        var id = forId, name = forName;
        if (!id || !pop) { return; }
        var addUrl = pop.getAttribute('data-add-url');
        var rmUrl = pop.getAttribute('data-remove-url');
        close();
        fetch(addUrl, {
            method: 'POST',
            headers: {'X-CSRFToken': token()},
            body: body({recipe_id: id, date: dateStr, json: '1'})
        })
            .then(function (r) {
                if (!r.ok) { throw new Error(r.status); }
                return r.json();
            })
            .then(function (d) {
                var label = d.added_label || dateStr;
                window.alvToast(name + ' added to ' + label, {
                    undo: function () {
                        fetch(rmUrl, {
                            method: 'POST',
                            headers: {'X-CSRFToken': token()},
                            // meal_entry_id, WHICH IS WHAT THE
                            // ENDPOINT READS. The first spelling sent
                            // entry_id, the lookup missed, the view
                            // redirected - and the toast said
                            // "Removed again" anyway, because it never
                            // asked. An Undo that reports a success it
                            // did not have is worse than no Undo.
                            body: body({meal_entry_id: d.added_id,
                                        json: '1'})
                        }).then(function (r) {
                            if (!r.ok || r.redirected) {
                                throw new Error(r.status);
                            }
                            window.alvToast('Removed again.');
                        }).catch(function () {
                            window.alvToast(
                                'That could not be undone. It is on '
                                + label + '.');
                        });
                    }
                });
            })
            .catch(function () {
                window.alvToast('That could not be added. Please try again.');
            });
    }

    document.addEventListener('click', function (e) {
        var icon = e.target.closest('[data-plan-id]');
        if (icon) {
            // THE CARD AROUND IT MAY BE CLICKABLE. RD-3 made the
            // photograph a trigger and this icon is its sibling -
            // stopping here costs nothing and says so out loud.
            e.preventDefault();
            e.stopPropagation();
            open(icon);
            return;
        }
        var day = e.target.closest('[data-plan-date]');
        if (day) { add(day.getAttribute('data-plan-date')); return; }
        var quick = e.target.closest('[data-plan-when]');
        if (quick) { add(iso(when(quick.getAttribute('data-plan-when')))); return; }
        if (e.target.closest('#planPopClose')) { close(); return; }
        if (e.target.closest('#planPrev')) {
            shown = new Date(shown.getFullYear(), shown.getMonth() - 1, 1);
            draw();
            return;
        }
        if (e.target.closest('#planNext')) {
            shown = new Date(shown.getFullYear(), shown.getMonth() + 1, 1);
            draw();
            return;
        }
        // OUTSIDE CLOSES IT, which is the other half of a popover.
        if (pop && !pop.hidden && !e.target.closest('#planPop')) { close(); }
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && pop && !pop.hidden) { close(); }
    });
})();
</script>
{% endif %}

{% include 'recipe_quicklook_shell.html' %}"""

SENT_WAS = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'grid-template-columns: 1fr'; Absent = $true; Code = $true; What = 'DB-1: and the one rule it held is gone - .calendar-layout stopped being a grid when MV-2 deleted the mini calendar beside it' },"""
SENT_NOW = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'grid-template-columns: 1fr'; Absent = $true; Code = $true; What = 'DB-1: and the one rule it held is gone - .calendar-layout stopped being a grid when MV-2 deleted the mini calendar beside it' },
    @{ File = 'pages/templates/recipe_management.html'; Text = 'data-plan-id='; What = 'AP-1: a recipe goes on a day without leaving the library - beside the heart on all FOUR card renderings, because this page draws every card twice and the JavaScript copies redraw after a search' },
    @{ File = 'pages/templates/base.html'; Text = 'window.alvToast'; What = 'AP-1: and base owns the toast, the way it owns the modal overlay - a confirmation that does not take the page away, with an Undo, because django messages need a render and the whole point is staying put' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = "payload['added_id']"; What = 'AP-1: the add endpoint hands back the row it just made - it created one and dropped it, so an Undo had nothing to point at' },"""

SUITE_WAS = """    'test_quick_look.py'
)"""
SUITE_NOW = """    'test_quick_look.py',
    # AP-1, 20 Oct 2026 - a recipe goes on a day from the library.
    # Section 3 DRIVES it: press the icon, press a day, read the
    # toast, press Undo, and ask the database what is left.
    'test_add_planner.py'
)"""

TREE_WAS = """    # RD-3, 20 Oct 2026 - the photograph opens the recipe, and a
    # second recipe dialog that nobody could open goes out with it.
    'test_quick_look.py',
]"""
TREE_NOW = """    # RD-3, 20 Oct 2026 - the photograph opens the recipe, and a
    # second recipe dialog that nobody could open goes out with it.
    'test_quick_look.py',
    # AP-1, 20 Oct 2026 - a recipe goes on a day from the library,
    # and base learns a toast.
    'test_add_planner.py',
]"""

RD_WAS = """    # RD-3, 20 Oct 2026 - the photograph opens the recipe; the dead
    # iframe dialog and its 39 !important declarations go with it.
    '.bak_quicklook',
]"""
RD_NOW = """    # RD-3, 20 Oct 2026 - the photograph opens the recipe; the dead
    # iframe dialog and its 39 !important declarations go with it.
    '.bak_quicklook',
    # AP-1, 20 Oct 2026 - a recipe goes on a day from the library.
    '.bak_addplanner',
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
    raise SystemExit('AP-1 REFUSED: %s' % msg)


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


def after(text, anchor, addition, where):
    """Put `addition` immediately after `anchor`, which must be unique."""
    once(text, anchor, where)
    a = fit(text, anchor)
    return text.replace(a, a + fit(text, addition))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    prm = os.path.join(root, RM)
    rm = read(prm)

    if 'data-plan-id=' in rm:
        print('AP-1  already applied - a recipe goes on a day from here.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- THE GROUND THIS ROUND STANDS ON
    code = T.code_only(rm)
    # A DECLARATION IS NOT A USE. The first spelling counted five
    # hearts where there are four: the fifth is
    # `function toggleFavourite(`, the thing itself rather than a
    # place it is called. Push 2 paid this twice in Python with a
    # `(?<!def )` lookbehind; this is its JavaScript twin.
    hearts = len(re.findall(r'(?<!function )toggleFavourite\(', code))
    if hearts != N_ICONS:
        refuse('%s: %d heart(s), expected %d - the icon goes beside '
               'each of them and this is not the page this round was '
               'written for' % (RM, hearts, N_ICONS))
    if 'recipe-photo-link' not in code:
        refuse('%s: RD-3 has not run, and this icon sits beside the '
               'photo link it made - RD-3 goes first' % RM)

    pv = os.path.join(root, VIEW)
    v = read(pv)
    if 'added_id' in T.python_code_only(v, payloads=True):
        refuse('%s: something already returns added_id' % VIEW)
    v = swap(v, ADD_WAS, ADD_NOW, '%s (the add endpoint)' % VIEW)
    out[pv] = v

    pb = os.path.join(root, BASE)
    b = read(pb)
    if 'alv-toast' in b:
        refuse('%s: base already owns a toast' % BASE)
    b = swap(b, TOAST_WAS, TOAST_NOW, '%s (the toast rules)' % BASE)
    b = swap(b, TOASTJS_WAS, TOASTJS_NOW, '%s (the toast itself)' % BASE)
    out[pb] = b

    rm = after(rm, GRID_HEART, GRID_PLAN, '%s (the grid card)' % RM)
    rm = after(rm, LIST_HEART, LIST_PLAN, '%s (the list row)' % RM)
    rm = after(rm, JSGRID_HEART, JSGRID_PLAN,
               '%s (the grid builder)' % RM)
    rm = after(rm, JSLIST_HEART, JSLIST_PLAN,
               '%s (the list builder)' % RM)
    rm = swap(rm, CONST_WAS, CONST_NOW, '%s (the permission)' % RM)
    rm = swap(rm, CSS_WAS, CSS_NOW, '%s (the rules)' % RM)
    rm = swap(rm, PHONE_WAS, PHONE_NOW, '%s (the phone rules)' % RM)
    rm = swap(rm, POP_WAS, POP_NOW, '%s (the popover)' % RM)
    out[prm] = rm

    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, SENT_WAS, SENT_NOW, '%s (the sentinels)' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suites)' % PS1)
    out[pp] = s
    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)
    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), RD_WAS, RD_NOW, '%s (ROUNDS)' % ROUNDS)
    pw = os.path.join(root, WD)
    w = read(pw)
    n_was = re.search(r'CONVERTED_N = (\d+)', w)
    w = swap(w, 'CONVERTED_N = %s' % n_was.group(1),
             'CONVERTED_N = %d   # AP-1, 20 Oct 2026 - this round own '
             'suite   # (was %s)'
             % (int(n_was.group(1)) + 1, n_was.group(1)),
             '%s (CONVERTED_N)' % WD)
    out[pw] = w

    # ---- THE GATES
    nc = T.code_only(out[prm])

    if nc.count('data-plan-id=') != N_ICONS:
        refuse('%s: %d icon(s), expected %d - the page draws every '
               'card twice and the JavaScript copies redraw after a '
               'filter' % (RM, nc.count('data-plan-id='), N_ICONS))

    # NOT INSIDE RD-3's TRIGGER. The grid icon is an overlay on the
    # same container as the photo link; inside it, pressing it would
    # open the quick-look as well.
    for m in re.finditer(r'<a class="recipe-photo-link".*?</a>', nc, re.S):
        if 'data-plan-id=' in m.group(0):
            refuse('%s: the icon sits INSIDE the photo link, so '
                   'pressing it would open the quick-look too' % RM)

    # AND IT IS ASKED OF THE PERMISSION, in all four. A control that
    # refuses is worse than a control that is not there.
    for m in re.finditer(r'data-plan-id=', nc):
        head = nc[max(0, m.start() - 320):m.start()]
        if 'can_edit_recipes' not in head and \
                'USER_CAN_EDIT_RECIPES' not in head:
            refuse('%s: an icon is drawn for somebody who may not add '
                   'a meal' % RM)

    # SOMEBODY ELSE'S CENSUS IS NOT MOVED. test_js_handlers pairs
    # every data-recipe-id with a data-recipe-name and counts both.
    was_ids = T.code_only(read(prm)).count('data-recipe-id="')
    if nc.count('data-recipe-id="') != was_ids:
        refuse('%s: the data-recipe-id count moved from %d to %d - '
               'these icons carry data-plan-id precisely so it does '
               'not' % (RM, was_ids, nc.count('data-recipe-id="')))

    nb = T.code_only(out[pb])
    if 'window.alvToast' not in T.code_only_js(out[pb]):
        refuse('%s: the toast has no entry point' % BASE)
    if '.alv-toast-undo' not in nb:
        refuse('%s: the toast has no Undo slot' % BASE)
    # A RECIPE NAME IS SOMEBODY ELSE'S TEXT. The toast must set it as
    # text, never as markup, and this round writes the forbidden word
    # nowhere - so the gate means one thing.
    # ASKED OF THE TOAST, NOT OF base. The first spelling asked the
    # whole file and refused instantly: base is 279KB of other
    # people's JavaScript and of course some of it assigns markup.
    # A gate that cannot pass against a correct tree is not a gate.
    jsb = T.code_only_js(out[pb])
    at = jsb.find('window.alvToast')
    toast_js = jsb[max(0, at - 1200):at + 2200]
    if 'innerHTML' in toast_js:
        refuse('%s: the toast builds its text as markup' % BASE)
    if 'textContent' not in toast_js:
        refuse('%s: the toast does not set its text as text' % BASE)

    njs = T.code_only_js(out[prm])

    # THE CONSTANT THE BUILDERS READ IS DECLARED. Without it the first
    # redraw after a search throws and takes the rest of the block.
    if 'USER_CAN_EDIT_RECIPES' not in njs:
        refuse('%s: the builders read a permission nothing declares'
               % RM)
    if njs.count('const USER_CAN_EDIT_RECIPES') != 1:
        refuse('%s: the permission is declared %d time(s), expected 1'
               % (RM, njs.count('const USER_CAN_EDIT_RECIPES')))

    # ONE POPOVER, AND ITS ROUTES COME FROM THE URLCONF.
    if nc.count('id="planPop"') != 1:
        refuse('%s: %d popover(s), expected 1 - RD-2 put one menu on '
               'the page for 648 chips and this is the same question'
               % (RM, nc.count('id="planPop"')))
    for attr in ('data-add-url=', 'data-remove-url='):
        if attr not in nc:
            refuse('%s: the popover does not carry %s, so a path would '
                   'have to be typed into the JavaScript' % (RM, attr))
    seg_js = njs.split('ADD TO THE PLANNER', 1)[-1][:4000]
    if "fetch('/" in seg_js or 'fetch("/' in seg_js:
        refuse('%s: this round types a path into a fetch' % RM)

    # THE UNDO POSTS THE FIELD THE ENDPOINT READS - asked of
    # remove_meal_entry itself, across the two files, because a field
    # name that does not match fails SILENTLY: the view redirects and
    # a careless .then() calls that success.
    rv = T.python_code_only(read(pv), payloads=True)
    seg_rm = rv[rv.index('def remove_meal_entry'):]
    seg_rm = seg_rm[:seg_rm.index('return redirect')]
    wanted = re.findall(r"request\.POST\.get\('([a-z_]+)'\)", seg_rm)
    wanted = [w for w in wanted if w != 'json']
    if not wanted:
        refuse('%s: remove_meal_entry reads no identifier, so this '
               'round cannot know what to send it' % VIEW)
    if ('body({%s:' % wanted[0]) not in njs and \
            ('%s: d.added_id' % wanted[0]) not in njs:
        refuse('%s: the Undo posts something other than %s, which is '
               'what remove_meal_entry reads - the lookup would miss '
               'and the view would redirect' % (RM, wanted[0]))

    # AND IT CHECKS BEFORE IT CELEBRATES.
    if 'r.redirected' not in njs:
        refuse('%s: the Undo does not check the response, so a '
               'redirect would be reported as a removal' % RM)

    # IT CARRIES ITS OWN TOKEN. Borrowing the page's one meant
    # borrowing another feature's PERMISSION, and the icon 403'd for
    # anybody who had this round's permission and not that one.
    popblk = nc[nc.index('id="planPop"'):]
    popblk = popblk[:popblk.index('</div>', popblk.index('plan-cal-grid'))]
    if 'csrf_token' not in popblk:
        refuse('%s: the popover borrows a token rendered behind a '
               'different permission' % RM)
    if 'csrfmiddlewaretoken' not in njs:
        refuse('%s: the JavaScript does not read the popover own '
               'token' % RM)

    # THE SHORTCUTS ARE THE THREE THAT WERE AGREED.
    for w8 in ('today', 'tomorrow', 'saturday'):
        if 'data-plan-when="%s"' % w8 not in nc:
            refuse('%s: the %s shortcut is missing' % (RM, w8))

    # AND THE TOAST IS ASKED FOR WITH AN UNDO, which is the half of
    # his answer that is easy to leave out.
    seg = njs.split('ADD TO THE PLANNER', 1)[-1]
    if 'window.alvToast(' not in seg:
        refuse('%s: nothing says what happened' % RM)
    if 'undo:' not in seg:
        refuse('%s: the toast offers no Undo' % RM)

    # BOTH OVERLAYS ARE 44px ON A PHONE - his answer, and the heart
    # grows with it rather than sitting beside it two thirds the size.
    # THE RULES REPLACE THE HEART'S OWN PHONE RULE IN PLACE, so they
    # are in whatever block that rule was in by construction. Slicing
    # on a guessed media query asked a different question and refused
    # a correct tree - the breakpoint here is 768, not 767.
    if '.recipe-favourite-btn { width: 44px; height: 44px' not in nc:
        refuse('%s: the heart is not 44px on a phone' % RM)
    if '.recipe-plan-btn { width: 44px; height: 44px' not in nc:
        refuse('%s: the new icon is not 44px on a phone' % RM)
    if '.recipe-favourite-btn { width: 28px' in nc:
        refuse('%s: the 28px heart rule survived, so whichever comes '
               'last wins and it may not be the 44' % RM)

    if CHECK:
        print('AP-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('AP-1  applied - a recipe goes on a day from the library.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
