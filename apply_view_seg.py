# -*- coding: utf-8 -*-
"""MC-1 - THE LIST/CALENDAR SWITCH BECOMES A SEGMENTED CONTROL

Demetri, on Live, 3 Oct 2026:

    "Can we move the List/Calendar Switch button up and make it conform to
     our standards. Is it better to have a button that toggles between
     List and Calendar?
     I should have the List/Calendar toggle in the Calendar view to be
     able to switch to List view again."

Three sentences, and the third one is a BUG REPORT, not a preference.

==========================================================================
WHY THE LIST HALF IS INVISIBLE ON THE CALENDAR PAGE
==========================================================================
The toggle IS in the Calendar view. Both halves are in the markup, have
been all along. What the Calendar page's copy of the CSS says is:

    .view-toggle          { background: rgba(255, 255, 255, 0.2); }
    .view-toggle .toggle-btn { color: rgba(255, 255, 255, 0.7); }

White ink on a white page. The control was written for a coloured header
bar that this page used to have and no longer does; when the bar went, the
ink stayed. Only the ACTIVE half survives the removal, because .active
hands it `background: white; color: var(--alv-accent-ink)` - so on the
Calendar page you see one calendar icon floating alone, and there is no
way back to the list.

This is the same shape as the .filter-bar lesson and the #5a6fd6 one: a
rule that outlived the surface it was written against. The repair is not
to recolour it. It is to stop the page from owning a control at all.

==========================================================================
WHAT REPLACES IT - HIS ANSWER, NOT A GUESS
==========================================================================
Asked two segments or one toggling button, he chose TWO SEGMENTS; asked
where, he chose IN THE ACTION BAR. So:

    [+ Create New Meal Plan]  [List | Calendar]          [<- Back]

base already has that control. ALV-SEG v1, worn today by
finance_expense.html, and its own note says what it is for:

    "A segment here is a PAGE-level choice, worn in an action bar ...
     it is not a verb you press to make something happen; it is which
     view you are looking at, so the pressed one is filled and the rest
     are quiet, and nothing here carries a semantic colour."

That is this control exactly. The current view is marked aria-current,
which is both the standard's hook for the fill AND the thing a screen
reader needs; the old one said `class="active"` and told assistive tech
nothing.

==========================================================================
WHAT GOES
==========================================================================
Removed from BOTH pages, and named here so the removal is allowed:

  meal_plans.html            .view-toggle-row, .view-toggle,
                             .view-toggle .toggle-btn and its :hover,
                             .active and .active:hover - with the
                             literals #6c757d, #495057, #dee2e6 and the
                             stray purple #5a6fd6, which was the LAST
                             purple hover left in the Personal module.

  meal_plan_calendar.html    the same six rules, with rgba(255,255,255,
                             0.2), rgba(255,255,255,0.7), rgba(255,255,
                             255,0.1), white and #f8f9fa - the white-on-
                             white set above.

  both                       the 768px fragments that tuned the padding
                             of a control that no longer exists, and the
                             .view-toggle-row DIV that held it on its own
                             centred row.

The seg sits before .action-back, which carries `margin-left: auto`, so
Back stays hard right and nothing else in either bar moves.

Backups: .bak_viewseg. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_viewseg'
ROOT = os.getcwd()
CRLF = {}

LIST = os.path.join(ROOT, 'pages', 'templates', 'meal_plans.html')
CAL = os.path.join(ROOT, 'pages', 'templates', 'meal_plan_calendar.html')


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
            raise SystemExit('MC1: %s is not a byte copy' % bak)


def code_only(t):
    """Blank every comment, preserving length - all THREE syntaxes. A
    template carries Django comments, HTML comments and CSS/JS block
    comments, and an instrument that strips two of the three can still
    read prose as code. This round's notes NAME .view-toggle, so a gate
    that searched the raw text would find the thing it just removed."""
    t = re.sub(r'\{#.*?#\}', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), t, flags=re.S)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('MC1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


# --------------------------------------------------------------------------
# THE CONTROL. Two of these, differing only in which half is current - and
# the href pair is the same on both pages, which is the point: the seg does
# not know which page it is on, it only knows which view is current.
# --------------------------------------------------------------------------
def seg(indent, current):
    p = ' ' * indent
    cur = ' aria-current="page"'
    return (
        '%s<div class="alv-seg" role="group" aria-label="View">\n'
        '%s    <a href="{%% url \'meal_plans\' %%}"%s\n'
        '%s       onclick="sessionStorage.setItem(\'meal_plan_view_preference\', \'list\')">\n'
        '%s        <i class="fas fa-list"></i> List\n'
        '%s    </a>\n'
        '%s    <a href="{%% url \'meal_plan_calendar\' %%}"%s\n'
        '%s       onclick="sessionStorage.setItem(\'meal_plan_view_preference\', \'calendar\')">\n'
        '%s        <i class="fas fa-calendar-alt"></i> Calendar\n'
        '%s    </a>\n'
        '%s</div>\n'
        % (p,
           p, cur if current == 'list' else '',
           p, p, p,
           p, cur if current == 'calendar' else '',
           p, p, p,
           p)
    )


NOTE = """/* VIEW TOGGLE - MC-1, 3 Oct 2026. This page no longer owns the switch.
   .view-toggle, .view-toggle-row, .toggle-btn and every literal they
   carried are gone; the control is base's .alv-seg, worn in the action
   bar, the same two-segment control finance_expense wears. A view
   switch is a PAGE-level choice, which is what .alv-seg is for, and the
   current half is marked aria-current rather than class="active" - the
   standard's hook for the fill and the thing a screen reader needs, in
   one attribute instead of neither. */"""

print('=' * 74)
print('MC-1 - THE LIST/CALENDAR SWITCH BECOMES A SEGMENT%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# meal_plans.html
# ==========================================================================
t, raw = read(LIST)

if 'alv-seg' in t:
    print('  meal_plans.html            already wears the seg')
else:
    t = swap(t, """/* View toggle on its own row */
.view-toggle-row {
    display: flex;
    justify-content: center;
    margin-bottom: 24px;
}
""", '', 'the list page toggle row', LIST)

    t = swap(t, """/* View Toggle Styles */
.view-toggle {
    display: flex;
    background: var(--alv-surface-deep);
    border-radius: 8px;
    padding: 4px;
}

.view-toggle .toggle-btn {
    padding: 10px 16px;
    border-radius: 6px;
    color: #6c757d;
    text-decoration: none;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 6px;
}

.view-toggle .toggle-btn:hover {
    color: #495057;
    background: #dee2e6;
}

.view-toggle .toggle-btn.active {
    background: var(--alv-accent);
    color: white;
}

.view-toggle .toggle-btn.active:hover {
    background: #5a6fd6;
}""", NOTE, 'the list page toggle rules', LIST)

    t = swap(t, """    }  .view-toggle-row {
        margin-bottom: 18px;
    }
    .view-toggle .toggle-btn {
        padding: 9px 14px;
    }
""", '    }\n', 'the list page 768 fragment', LIST)

    t = swap(t, """
    <!-- View Toggle (List vs Calendar) — its own row -->
    <div class="view-toggle-row">
        <div class="view-toggle">
            <a href="{% url 'meal_plans' %}" class="toggle-btn active" title="List View" onclick="sessionStorage.setItem('meal_plan_view_preference', 'list')">
                <i class="fas fa-list"></i>
            </a>
            <a href="{% url 'meal_plan_calendar' %}" class="toggle-btn" title="Calendar View" onclick="sessionStorage.setItem('meal_plan_view_preference', 'calendar')">
                <i class="fas fa-calendar-alt"></i>
            </a>
        </div>
    </div>
""", '', 'the list page toggle markup', LIST)

    t = swap(t, """        {% endif %}

        <a href="{% url 'recipe_management' %}" class="btn action-back" aria-label="Back to Recipes">""",
             '        {%% endif %%}\n\n%s\n        <a href="{%% url \'recipe_management\' %%}" class="btn action-back" aria-label="Back to Recipes">'
             % seg(8, 'list').rstrip('\n'),
             'the list page back link', LIST)

    if not CHECK:
        back_up(LIST, raw)
        write(LIST, t)
    print('  meal_plans.html            seg in the bar, six rules and the row gone')

# ==========================================================================
# meal_plan_calendar.html
# ==========================================================================
t, raw = read(CAL)

if 'alv-seg' in t:
    print('  meal_plan_calendar.html    already wears the seg')
else:
    t = swap(t, """/* View toggle on its own row */
.view-toggle-row {
    display: flex;
    justify-content: center;
    margin: 0 0 20px 0;
}
""", '', 'the calendar toggle row', CAL)

    t = swap(t, """
    .view-toggle-row {
        margin-bottom: 16px;
    }
    .view-toggle .toggle-btn {
        padding: 9px 14px;
    }
""", '', 'the calendar 768 fragment', CAL)

    t = swap(t, """/* View Toggle Styles */
.view-toggle {
    display: flex;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 4px;
}

.view-toggle .toggle-btn {
    padding: 10px 16px;
    border-radius: 6px;
    color: rgba(255, 255, 255, 0.7);
    text-decoration: none;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 6px;
}

.view-toggle .toggle-btn:hover {
    color: white;
    background: rgba(255, 255, 255, 0.1);
}

.view-toggle .toggle-btn.active {
    background: white;
    color: var(--alv-accent-ink);
}

.view-toggle .toggle-btn.active:hover {
    background: #f8f9fa;
}""",
             NOTE + """

/* AND THE REASON THIS PAGE'S COPY WAS WORSE THAN THE LIST PAGE'S: the
   ink above was rgba(255,255,255,0.7) on rgba(255,255,255,0.2) - white
   on white. It was written for a coloured header bar this page used to
   have; the bar went and the ink stayed, so only the ACTIVE half, which
   paints itself a background, was visible at all. Demetri reported it
   as "I should have the List/Calendar toggle in the Calendar view to be
   able to switch to List view again" - the toggle was there; the half
   he needed was not readable. */""",
             'the calendar toggle rules', CAL)

    t = swap(t, """
    <!-- View Toggle (List vs Calendar) — its own row -->
    <div class="view-toggle-row">
        <div class="view-toggle">
            <a href="{% url 'meal_plans' %}" class="toggle-btn" title="List View" onclick="sessionStorage.setItem('meal_plan_view_preference', 'list')">
                <i class="fas fa-list"></i>
            </a>
            <a href="{% url 'meal_plan_calendar' %}" class="toggle-btn active" title="Calendar View" onclick="sessionStorage.setItem('meal_plan_view_preference', 'calendar')">
                <i class="fas fa-calendar-alt"></i>
            </a>
        </div>
    </div>
""", '', 'the calendar toggle markup', CAL)

    t = swap(t, """            {% endif %}

            <a href="{% url 'recipe_management' %}" class="btn action-back" aria-label="Back to Recipes">""",
             '            {%% endif %%}\n\n%s\n            <a href="{%% url \'recipe_management\' %%}" class="btn action-back" aria-label="Back to Recipes">'
             % seg(12, 'calendar').rstrip('\n'),
             'the calendar back link', CAL)

    if not CHECK:
        back_up(CAL, raw)
        write(CAL, t)
    print('  meal_plan_calendar.html    seg in the bar, the white-on-white set gone')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
CODE = {}
for p in (LIST, CAL):
    CODE[p] = read(p)[0]

# 1. THE SEG IS THERE, ONCE, ON EACH PAGE, AND IT IS IN THE BAR.
for p, name in ((LIST, 'meal_plans.html'), (CAL, 'meal_plan_calendar.html')):
    t = CODE[p]
    n = t.count('class="alv-seg"')
    if n != 1:
        raise SystemExit('MC1: %s has %d segs, not one' % (name, n))
    bar = t.index('<div class="page-action-buttons">')
    end = t.index('</div>', t.index('action-back"'))
    if not (bar < t.index('class="alv-seg"') < end):
        raise SystemExit('MC1: %s has the seg outside the action bar' % name)
    print('  %-26s one seg, inside the action bar' % name)

# 2. EXACTLY ONE HALF IS CURRENT, AND IT IS THE RIGHT ONE.
for p, name, want in ((LIST, 'meal_plans.html', 'meal_plans'),
                      (CAL, 'meal_plan_calendar.html', 'meal_plan_calendar')):
    t = CODE[p]
    seg_html = t[t.index('<div class="alv-seg"'):]
    seg_html = seg_html[:seg_html.index('</div>')]
    halves = re.findall(r"\{% url '(\w+)' %\}([^>]*)>", seg_html)
    if len(halves) != 2:
        raise SystemExit('MC1: %s seg has %d halves, not two' % (name, len(halves)))
    cur = [h for h, rest in halves if 'aria-current' in rest]
    if cur != [want]:
        raise SystemExit('MC1: %s marks %r current, expected [%r]'
                         % (name, cur, want))
    print('  %-26s two halves, %s is current' % (name, want))

# 3. THE OLD CONTROL IS GONE - CLASS AND RULES, NOT JUST THE MARKUP.
#    code_only so a note NAMING .view-toggle does not read as the rule.
for p, name in ((LIST, 'meal_plans.html'), (CAL, 'meal_plan_calendar.html')):
    live = code_only(CODE[p])
    for dead in ('view-toggle-row', 'view-toggle', 'toggle-btn'):
        if dead in live:
            raise SystemExit('MC1: %s still carries %s in code' % (name, dead))
    print('  %-26s no .view-toggle, .view-toggle-row, .toggle-btn' % name)

# 4. THE LITERALS THE REMOVAL TOOK WITH IT.
#
#    AND A GATE THAT CLAIMS ONLY WHAT THE ROUND DID. The first draft of
#    this one asserted #dee2e6 was gone from meal_plans.html and failed:
#    the page uses it twice, once on the toggle hover and once on the
#    empty-state icon, and this round touched one of them. Ninth time an
#    instrument has been asked for a substring when the thing meant was
#    a construct. So each literal is counted BEFORE and AFTER against
#    this round's own backup, and the gate asserts the DROP - which is
#    the only thing the round is entitled to claim.
DROP = {
    LIST: {'#5a6fd6': 1, '#495057': 1, '#dee2e6': 1, '#6c757d': 1},
    CAL: {'rgba(255, 255, 255, 0.2)': 1, 'rgba(255, 255, 255, 0.7)': 1,
          'rgba(255, 255, 255, 0.1)': 1, '#f8f9fa': 1},
}
for p, wanted in DROP.items():
    name = os.path.basename(p)
    live = code_only(CODE[p])
    was = code_only(read(p + SUFFIX)[0])
    for lit, n in sorted(wanted.items()):
        got = was.count(lit) - live.count(lit)
        if got != n:
            raise SystemExit('MC1: %s dropped %d uses of %s, expected %d '
                             '(%d before, %d after)'
                             % (name, got, lit, n,
                                was.count(lit), live.count(lit)))
    print('  %-26s dropped one use each of %s'
          % (name, ', '.join(sorted(wanted))))

# 5. THE CONTROL: the white-on-white pair REALLY WAS in the calendar page
#    before this round, or the premise of the bug report is wrong.
before = read(CAL + SUFFIX)[0]
if 'rgba(255, 255, 255, 0.7)' not in before:
    raise SystemExit('MC1: the calendar page never had the white ink - the '
                     'premise of this round is wrong')
print('  CONTROL: the calendar page did carry white ink on a white ground')

# 6. BOTH PAGES POINT AT BOTH VIEWS. The bug was a one-way street; the
#    gate that catches a one-way street is this one, not the markup count.
for p, name in ((LIST, 'meal_plans.html'), (CAL, 'meal_plan_calendar.html')):
    t = CODE[p]
    for url in ("{% url 'meal_plans' %}", "{% url 'meal_plan_calendar' %}"):
        if url not in t:
            raise SystemExit('MC1: %s cannot reach %s' % (name, url))
    print('  %-26s reaches both views' % name)

print('-' * 74)
print('  The toggle was never missing from the Calendar page. The half he')
print('  needed was white ink on a white ground, left behind by a header')
print('  bar that had been removed. Tenth instrument this week to be')
print('  right about a surface that no longer exists.')
print('=' * 74)
