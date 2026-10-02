# -*- coding: utf-8 -*-
"""SECTION ML, ROUND ML-1 - THE MEAL PLANS ROW, ON THE HOUSE COMPONENT

Demetri, with a screenshot of Meal Plans: "This table also needs to be
addressed."

Five filled buttons per row, each with a rule and a colour of its own:

    View        #007bff   Bootstrap blue
    Edit        #ffc107   Bootstrap amber, on #000 text
    List        #28a745   Bootstrap green
    Duplicate   #0e7c8b   THE HOUSE ACCENT, hard-coded
    Delete      #dc3545   Bootstrap red

The page carries 34 local rules and 24 literal colours across 16 distinct
hexes, for a component base has owned for weeks and that 33 other pages
and 170 other controls already use.

==========================================================================
WHAT IT BECOMES
==========================================================================
    .row-actions                 the strip, from base
    .icon-action-btn icon-view       fa-eye
    .icon-action-btn icon-edit       fa-pencil-alt
    .icon-action-btn icon-list       fa-shopping-cart
    .icon-action-btn icon-duplicate  fa-copy
    .icon-action-btn icon-delete     fa-trash
    .icon-action-btn icon-disabled   where the permission is missing

and, on a phone, base's `.mobile-action-bar` - which is already a
`repeat(3, 1fr)` grid with a 6px gap, EXACTLY the shape this page built
for itself in the 768 block. Five actions over three columns is 3 + 2,
which is what it does today.

ONE NEW NAME IN base, AND NO NEW COLOUR. There is no icon name for a
shopping list, so `.icon-list` is added - on `var(--alv-view)`, the colour
`.icon-view`, `.icon-manage` and `.icon-event` already share. base's own
note against .icon-manage says why that is the right move: "the third NAME
on an existing colour, and for the same reason". This is the fifth. The
round adds a name so the markup reads correctly and adds nothing to the
palette.

==========================================================================
AND THE TWO HANDLERS GO THE WAY J-2 TOOK THE OTHERS
==========================================================================
    onclick="confirmDuplicate(this, '{{ plan.plan_name|escapejs }}')"

J-1 made that safe and it is not broken. But the mobile bar duplicates
every action, so leaving the onclick would mean writing the plan name into
a JS string TEN times per page instead of five - and J-2 settled what the
house does with a value in a handler two hours ago: it does not put it
there. The name becomes `data-plan-name`, the buttons already carry
`data-duplicate-url` and `data-delete-url`, and ONE delegated listener per
action serves the desktop strip and the phone bar together.

confirmDelete() and confirmDuplicate() keep their signatures and their
bodies. Only who calls them changes.

Backups: .bak_mealrow. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_mealrow'
CRLF = {}
ROOT = os.getcwd()


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('ML1: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('ML1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


def code_only(text):
    def blank(m):
        return re.sub(r'[^\n]', ' ', m.group(0))
    text = re.sub(r'<!--.*?-->', blank, text, flags=re.S)
    text = re.sub(r'\{#.*?#\}', blank, text, flags=re.S)
    return re.sub(r'/\*.*?\*/', blank, text, flags=re.S)


print('=' * 74)
print('SECTION ML, ROUND ML-1 - THE MEAL PLANS ROW%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

MP = alv_tree.path_of('meal_plans.html')
BASE = alv_tree.path_of('base.html')
mp, mp_raw = read(MP)

css0 = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>',
                            code_only(mp), re.S))
R0 = len(re.findall(r'(?m)^\s*\.[\w.-][^\n{}]*\{', css0))
L0 = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', css0))
print('  before: %d rules, %d literal colours' % (R0, L0))
print('-' * 74)

# ==========================================================================
# 1. base GAINS ONE NAME. No colour.
# ==========================================================================
bs, bs_raw = read(BASE)
ANCHOR = '''/* Event: the fourth NAME on --alv-view, added by Section H round H2 for'''
if '.icon-list' in bs:
    print('  base.html                already has .icon-list')
else:
    bs = swap(bs, ANCHOR,
              '''/* List: the FIFTH NAME on --alv-view, added by ML-1 on 2 Oct 2026 for
   Meal Plans' shopping-list row action (fa-shopping-cart). A shopping list
   is something the row SHOWS you, which is what --alv-view means here, and
   there was no name that read correctly on that button - "manage" does not
   describe a list of what to buy.

   THE RULE base ALREADY STATES, three names above this one: a new NAME on
   an existing colour, not a sixth colour. Nothing is added to the palette.
   The name exists so the markup says what the control is. */
.icon-list       { color: var(--alv-view); border-color: var(--alv-accent-line); }
.icon-list:hover { background-color: var(--alv-view); border-color: var(--alv-view); color: var(--alv-on-accent); }
.icon-color-list { color: var(--alv-view); }

''' + ANCHOR, 'the icon-event note', BASE)
    if not CHECK:
        back_up(BASE, bs_raw)
        write(BASE, bs)
    print('  base.html                .icon-list - 1 name, 0 colours')

# ==========================================================================
# 2. THE ROW. Desktop strip + phone bar, both from base.
# ==========================================================================
# THE ANCHOR CONTAINS TWO LINES THAT END IN A SPACE, and A-BAR was bitten
# by exactly this four hours ago: a trailing space inside a triple-quoted
# literal is stripped on the way to disk by every editor and tool in this
# chain, so the anchor reads '<button type="button"\n' where the file says
# '<button type="button" \n' and matches 0 times. Spelled out by
# concatenation, so what is on disk cannot be quietly tidied.
_BTN = '                <button type="button"' + ' ' + '\n'

OLD_ROW = """            <!-- Actions -->
            <div class="meal-plan-actions">
                <a href="{% url 'view_meal_plan' plan.meal_plan_id %}" class="btn btn-view">
                    <i class="fas fa-eye"></i> View
                </a>
                {% if perms.auth.can_edit_personal %}
                <a href="{% url 'edit_meal_plan' plan.meal_plan_id %}" class="btn btn-edit">
                    <i class="fas fa-edit"></i> Edit
                </a>
                {% else %}
                <span class="btn btn-action-disabled" title="No permission to edit">
                    <i class="fas fa-edit"></i> Edit
                </span>
                {% endif %}
                <a href="{% url 'meal_plan_shopping_list' plan.meal_plan_id %}" class="btn btn-shopping">
                    <i class="fas fa-shopping-cart"></i> List
                </a>
                {% if perms.auth.can_edit_personal %}
""" + _BTN + """                        class="btn btn-duplicate"
                        data-duplicate-url="{% url 'duplicate_meal_plan' plan.meal_plan_id %}"
                        onclick="confirmDuplicate(this, '{{ plan.plan_name|escapejs }}')">
                    <i class="fas fa-copy"></i> Duplicate
                </button>
""" + _BTN + """                        class="btn btn-delete"
                        data-delete-url="{% url 'delete_meal_plan' plan.meal_plan_id %}"
                        onclick="confirmDelete(this, '{{ plan.plan_name|escapejs }}')">
                    <i class="fas fa-trash"></i> Delete
                </button>
                {% else %}
                <span class="btn btn-action-disabled" title="No permission to duplicate">
                    <i class="fas fa-copy"></i> Duplicate
                </span>
                <span class="btn btn-action-disabled" title="No permission to delete">
                    <i class="fas fa-trash"></i> Delete
                </span>
                {% endif %}
            </div>
"""

NEW_ROW = '''            <!-- Actions - ML-1, 2 Oct 2026. Five filled buttons in five
                 colours became base's row-action strip: the same five
                 actions, the same order, on .icon-action-btn. The page's
                 own btn-view / btn-edit / btn-shopping / btn-duplicate /
                 btn-delete rules and their ten literal colours went with
                 them.

                 THE NAME TRAVELS AS AN ATTRIBUTE, NOT IN A HANDLER -
                 J-2's answer, applied here because the phone bar below
                 repeats every action and an onclick would mean writing
                 the plan name into a JS string ten times a row instead
                 of carrying it once. One delegated listener per action
                 serves both strips. -->
            <div class="row-actions">
                <a href="{% url 'view_meal_plan' plan.meal_plan_id %}" class="icon-action-btn icon-view" title="View"><i class="fas fa-eye"></i></a>
                {% if perms.auth.can_edit_personal %}
                <a href="{% url 'edit_meal_plan' plan.meal_plan_id %}" class="icon-action-btn icon-edit" title="Edit"><i class="fas fa-pencil-alt"></i></a>
                {% else %}
                <span class="icon-action-btn icon-disabled" title="No permission to edit"><i class="fas fa-pencil-alt"></i></span>
                {% endif %}
                <a href="{% url 'meal_plan_shopping_list' plan.meal_plan_id %}" class="icon-action-btn icon-list" title="Shopping List"><i class="fas fa-shopping-cart"></i></a>
                {% if perms.auth.can_edit_personal %}
                <button type="button" class="icon-action-btn icon-duplicate js-duplicate-plan"
                        data-duplicate-url="{% url 'duplicate_meal_plan' plan.meal_plan_id %}"
                        data-plan-name="{{ plan.plan_name }}" title="Duplicate"><i class="fas fa-copy"></i></button>
                <button type="button" class="icon-action-btn icon-delete js-delete-plan"
                        data-delete-url="{% url 'delete_meal_plan' plan.meal_plan_id %}"
                        data-plan-name="{{ plan.plan_name }}" title="Delete"><i class="fas fa-trash"></i></button>
                {% else %}
                <span class="icon-action-btn icon-disabled" title="No permission to duplicate"><i class="fas fa-copy"></i></span>
                <span class="icon-action-btn icon-disabled" title="No permission to delete"><i class="fas fa-trash"></i></span>
                {% endif %}
            </div>

            <!-- And the phone bar, from base. .mobile-action-bar is already
                 a repeat(3, 1fr) grid with a 6px gap - the exact shape this
                 page had written for itself in its own 768 block. Five
                 actions over three columns is 3 + 2, which is what it has
                 always done. -->
            <div class="mobile-action-bar">
                <a href="{% url 'view_meal_plan' plan.meal_plan_id %}" class="mobile-action-btn">
                    <i class="fas fa-eye mobile-action-icon icon-color-view"></i>
                    <span class="mobile-action-label">View</span>
                </a>
                {% if perms.auth.can_edit_personal %}
                <a href="{% url 'edit_meal_plan' plan.meal_plan_id %}" class="mobile-action-btn">
                    <i class="fas fa-pencil-alt mobile-action-icon icon-color-edit"></i>
                    <span class="mobile-action-label">Edit</span>
                </a>
                {% else %}
                <span class="mobile-action-btn mobile-action-disabled">
                    <i class="fas fa-pencil-alt mobile-action-icon"></i>
                    <span class="mobile-action-label">Edit</span>
                </span>
                {% endif %}
                <a href="{% url 'meal_plan_shopping_list' plan.meal_plan_id %}" class="mobile-action-btn">
                    <i class="fas fa-shopping-cart mobile-action-icon icon-color-list"></i>
                    <span class="mobile-action-label">List</span>
                </a>
                {% if perms.auth.can_edit_personal %}
                <button type="button" class="mobile-action-btn js-duplicate-plan"
                        data-duplicate-url="{% url 'duplicate_meal_plan' plan.meal_plan_id %}"
                        data-plan-name="{{ plan.plan_name }}">
                    <i class="fas fa-copy mobile-action-icon icon-color-duplicate"></i>
                    <span class="mobile-action-label">Duplicate</span>
                </button>
                <button type="button" class="mobile-action-btn js-delete-plan"
                        data-delete-url="{% url 'delete_meal_plan' plan.meal_plan_id %}"
                        data-plan-name="{{ plan.plan_name }}">
                    <i class="fas fa-trash mobile-action-icon icon-color-delete"></i>
                    <span class="mobile-action-label">Delete</span>
                </button>
                {% else %}
                <span class="mobile-action-btn mobile-action-disabled">
                    <i class="fas fa-copy mobile-action-icon"></i>
                    <span class="mobile-action-label">Duplicate</span>
                </span>
                <span class="mobile-action-btn mobile-action-disabled">
                    <i class="fas fa-trash mobile-action-icon"></i>
                    <span class="mobile-action-label">Delete</span>
                </span>
                {% endif %}
            </div>
'''

LISTENERS = '''
// THE TWO LISTENERS - ML-1, 2 Oct 2026.
//
// Delegated on document, so one of each serves the desktop icon strip AND
// the phone action bar without the markup repeating a handler. The plan
// name arrives as an attribute, which the browser's own parser decodes -
// there is no JS string here to close early on an apostrophe, which is
// what J-2 was about.
document.addEventListener('click', function (e) {
    var btn = e.target.closest && e.target.closest('.js-duplicate-plan');
    if (!btn) { return; }
    e.preventDefault();
    confirmDuplicate(btn, btn.getAttribute('data-plan-name') || '');
});

document.addEventListener('click', function (e) {
    var btn = e.target.closest && e.target.closest('.js-delete-plan');
    if (!btn) { return; }
    e.preventDefault();
    confirmDelete(btn, btn.getAttribute('data-plan-name') || '');
});

'''

if 'ML-1, 2 Oct 2026' in mp:
    print('  meal_plans.html          already done')
else:
    mp = swap(mp, OLD_ROW, NEW_ROW, 'the actions block', MP)
    mp = swap(mp, '''function confirmDelete(button, mealPlanName) {''',
              LISTENERS.lstrip('\n')
              + '''function confirmDelete(button, mealPlanName) {''',
              'the head of confirmDelete', MP)

    # ----------------------------------------------------------------
    # The ten rules the page no longer needs, and their colours.
    # ----------------------------------------------------------------
    # THIS FILE IS CRLF, and the first draft of this loop matched `\n`.
    # read() decodes the raw bytes without normalising, so every line here
    # ends `\r\n` and a pattern ending `\}\n` matches nothing - the
    # patcher reported ".btn-view appears 0 times" on a rule plainly sitting
    # in the file. The line ending is part of the data; the pattern asks for
    # whichever one this file actually uses.
    NL = '\r\n' if CRLF.get(MP) else '\n'
    for sel in ('btn-view', 'btn-edit', 'btn-shopping', 'btn-duplicate',
                'btn-delete'):
        for suffix in ('', ':hover'):
            pat = re.compile(r'(?m)^\.' + sel + re.escape(suffix)
                             + r'\s*\{[^}]*\}' + re.escape(NL)
                             + r'(?:' + re.escape(NL) + r')?')
            n = len(pat.findall(mp))
            if n != 1:
                raise SystemExit('ML1: .%s%s appears %d times, not once'
                                 % (sel, suffix, n))
            mp = pat.sub('', mp, count=1)

    # And the phone block's rules for them.
    mp = swap(mp, '''    /* Action buttons in card — 3-col grid (2 rows: 3 + 2) */
    .meal-plan-actions {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr);
        gap: 6px;
        width: 100%;
        justify-self: stretch !important;
    }
    .meal-plan-actions .btn,
    .meal-plan-actions .btn-action-disabled {
        padding: 10px 4px;
        font-size: 12px;
        justify-content: center;
        text-align: center;
        white-space: nowrap;
    }
''', '''    /* THE PHONE GRID IS base's NOW - ML-1, 2 Oct 2026. These seven
       declarations described .mobile-action-bar exactly: a repeat(3, 1fr)
       grid with a 6px gap, stretched, with its buttons centred. base says
       all of it, and says the rest of the bar too - the top rule, the icon
       size, the label, the disabled state. The page keeps one line, below,
       because base has no opinion about a card that is not a table. */
    .row-actions { display: none !important; }
''', 'the phone action grid', MP)

    if not CHECK:
        back_up(MP, mp_raw)
        write(MP, mp)
    print('  meal_plans.html          row onto .row-actions + '
          '.mobile-action-bar, 10 rules out')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
mp = read(MP)[0]
code = code_only(mp)
css = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', code, re.S))

# THE FIVE BESPOKE BUTTON NAMES ARE GONE, AND SO ARE THEIR COLOURS.
for sel in ('btn-view', 'btn-edit', 'btn-shopping', 'btn-duplicate',
            'btn-delete'):
    if sel in code:
        raise SystemExit('ML1: .%s is still on the page' % sel)
print('  the five bespoke button names are gone')

# AGAINST THE BACKUP, NOT AGAINST A CENSUS TAKEN AT THE TOP OF THIS RUN.
# The figures printed above are read from the file as it stands when the
# patcher starts - which on a SECOND run is the already-patched file, so
# the first draft of this gate compared 43 with 43 and failed a tree it had
# correctly left alone. The backup is the only honest "before".
was = code_only(read(MP + SUFFIX)[0])
css_was = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', was, re.S))
RW = len(re.findall(r'(?m)^\s*\.[\w.-][^\n{}]*\{', css_was))
LW = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', css_was))
R1 = len(re.findall(r'(?m)^\s*\.[\w.-][^\n{}]*\{', css))
L1 = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', css))
if R1 >= RW or L1 >= LW:
    raise SystemExit('ML1: rules %d -> %d, colours %d -> %d - neither fell'
                     % (RW, R1, LW, L1))
print('  rules %d -> %d, literal colours %d -> %d' % (RW, R1, LW, L1))

# PER-LITERAL, NOT PRESENCE. This page keeps literals in rules this round
# never touched, so "gone" would be a claim about the wrong thing.
for lit in ('#007bff', '#ffc107', '#28a745', '#dc3545', '#0056b3',
            '#e0a800', '#218838', '#c82333'):
    a = css.lower().count(lit)
    b = css_was.lower().count(lit)
    if a >= b:
        raise SystemExit('ML1: %s appears %d times, was %d' % (lit, a, b))
print('  and each of the eight button literals fell')

# THE FIVE ACTIONS ARE ALL STILL THERE, TWICE - once per strip.
# EIGHT, NOT FIVE, IN EACH STRIP - and the count is worth spelling out
# because the first draft said seven and was simply wrong. Five actions,
# but View and List are always available while Edit, Duplicate and Delete
# each render as a control OR as a disabled one depending on the
# permission: 2 + 3 x 2 = 8 controls written per strip, of which 5 ever
# render at once.
for cls, n in (('icon-action-btn', 8), ('mobile-action-btn', 8)):
    c = code.count(cls)
    if c != n:
        raise SystemExit('ML1: %s appears %d times, expected %d'
                         % (cls, c, n))
for url in ('view_meal_plan', 'edit_meal_plan', 'meal_plan_shopping_list',
            'duplicate_meal_plan', 'delete_meal_plan'):
    a = len(re.findall(r"\{%\s*url '" + url + r"'", code))
    b = len(re.findall(r"\{%\s*url '" + url + r"'", was))
    if a != b * 2:
        raise SystemExit('ML1: %s is linked %d times, was %d - the phone bar '
                         'should have doubled it' % (url, a, b))
print('  every one of the five actions appears in BOTH strips')

# EVERY ICON NAME IS ONE base DEFINES.
bs = read(BASE)[0]
used = set(re.findall(r'\bicon-(?:action-btn|color-)?([a-z]+)\b', code))
used -= {'action', 'btn'}
missing = [u for u in sorted(used)
           if ('.icon-%s' % u) not in bs and ('.icon-color-%s' % u) not in bs]
if missing:
    raise SystemExit('ML1: base defines no %s'
                     % ', '.join('.icon-%s' % m for m in missing))
print('  and all %d icon names used are ones base defines' % len(used))

# .icon-list IS A NAME, NOT A COLOUR.
m = re.search(r'\.icon-list\s*\{([^}]*)\}', bs)
if not m:
    raise SystemExit('ML1: base has no .icon-list')
if 'var(--alv-view)' not in m.group(1):
    raise SystemExit('ML1: .icon-list is not on --alv-view')
if re.search(r'#[0-9a-fA-F]{3,6}\b', m.group(1)):
    raise SystemExit('ML1: .icon-list carries a literal colour')
a = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', code_only(bs)))
b = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', code_only(read(BASE + SUFFIX)[0])))
if a != b:
    raise SystemExit('ML1: base gained %d literal colour(s)' % (a - b))
print('  .icon-list is a NAME on --alv-view - base gained no colour (%d)'
      % a)

# NO HANDLER CARRIES THE PLAN NAME.
if re.search(r'onclick="confirm(?:Delete|Duplicate)\(', code):
    raise SystemExit('ML1: a handler still carries the plan name')
for cls in ('.js-duplicate-plan', '.js-delete-plan'):
    if ("e.target.closest('%s')" % cls) not in mp:
        raise SystemExit('ML1: no delegated listener for %s' % cls)
n = len(re.findall(r'data-plan-name="\{\{ plan\.plan_name \}\}"', code))
if n != 4:
    raise SystemExit('ML1: %d data-plan-name, expected 4' % n)
print('  the plan name travels as an attribute, on all 4 buttons')

# THE MARKUP STILL CLOSES.
for path, label in ((MP, 'meal_plans.html'), (BASE, 'base.html')):
    c = code_only(read(path)[0])
    body = re.sub(r'<(script|style)\b.*?</\1>', '', c, flags=re.S)
    d = len(re.findall(r'<div\b', body)) - len(re.findall(r'</div\s*>', body))
    if d:
        raise SystemExit('ML1: %s has %+d unbalanced <div>' % (label, d))
    for tag, close in (('if', 'endif'), ('for', 'endfor')):
        x = len(re.findall(r'\{%\s*' + tag + r'\b', c))
        y = len(re.findall(r'\{%\s*' + close + r'\s*%\}', c))
        if x != y:
            raise SystemExit('ML1: %s has %s %d vs %s %d'
                             % (label, tag, x, close, y))
    s = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', c, re.S))
    if s.count('{') != s.count('}'):
        raise SystemExit('ML1: %s CSS does not balance' % label)
print('  every <div>, {% if %}, {% for %} and every brace still closes')

print('-' * 74)
print('  Five colours became one component, and the row reads as a row')
print('  rather than as five things competing for the eye.')
print('=' * 74)
