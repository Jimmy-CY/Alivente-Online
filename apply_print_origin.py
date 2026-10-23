# -*- coding: utf-8 -*-
"""apply_print_origin.py - round PT-1, 22 Oct 2026.

THE PRINT SHEET DID NOT KNOW WHICH VIEW SENT IT.

Demetri, 22 October, five findings:

  1. In the Day View, when I press the Print Button, it must not give
     me the date options. It must only be a print of the day that is
     showing below. It cannot be more than that.
  2. In the Week View, the earliest date I can pick is the first day
     of the week displayed below, and the latest is the last day of
     that week. Then the print must only show, and only print, the
     date range selected.
  3. Back from the Print section of the Week View must take me back to
     the Week view, showing the week that I had selected.
  4. The same for the Day View.
  5. The same for the Month View.

FIVE FINDINGS, ONE CAUSE. meal_plan_print takes ?from= and ?to= and
nothing else. It can work out the SHAPE of the sheet from those two
dates - RG-1 does exactly that and it is right to - but it cannot work
out WHERE THE READER CAME FROM, because that is not in the dates. A
day sheet and a one-day range are the same two dates. A week sheet and
a Monday-to-Sunday range are the same two dates. The origin is a
different fact and it has to be carried.

So Back was `{% url 'meal_planner' %}` with no query string at all,
and landed on the planner's default view on today's date. That is
findings 3, 4 and 5, and it is one line.

NOT A ?shape= PARAMETER - RG-1's rule, and it still holds. The sheet's
LAYOUT is still derived from the two dates and nothing here changes
that. What is added is ?view= and ?date=: where to go BACK to, which
no arithmetic on the dates can recover. The planner already reads both
of them, because that is how its own view switcher works.

WHAT EACH FINDING BECOMES.

  1. The range form is not rendered when the origin is the day view.
     Not disabled, not hidden - not rendered, so nothing on the page
     offers a choice that is not on offer.

  2. The two date inputs carry min and max, AND THE SERVER CLAMPS. A
     min attribute is a suggestion to a browser; the clamp is what
     makes the claim true. Both, because the attribute is what stops
     somebody picking the wrong date and the clamp is what stops the
     wrong date working.

     AND THE SHEET IS CROPPED, which overrides RG-1. RG-1 renders
     whole Monday-to-Sunday weeks and greys the days outside the
     range, reasoning that three blank cells at the front of a
     seven-column grid read as missing data rather than as a boundary.
     That reasoning is sound and Demetri has overruled it: "the print
     must only show, and then only print, the date range selected."
     So a narrowed period drops its out-of-range days, drops the
     Monday-to-Sunday heading strip that would then be lying, and
     gives the grid as many columns as it has days.

  3, 4, 5. Back carries ?view= and ?date= and lands where it started.

WHEN NOTHING IS PASSED, NOTHING CHANGES. Somebody who types the print
URL by hand gets the page exactly as it was: form shown, no bounds,
Back to the planner bare. The origin is an addition, not a
requirement.

Idempotent. Every file backed up to .bak_printorigin.
"""
import os
import re
import sys

SUFFIX = '.bak_printorigin'
VIEWS = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
PRINT = os.path.join('pages', 'templates', 'meal_plan_print.html')
PLANNER = os.path.join('pages', 'templates', 'meal_planner.html')
PS1 = 'Push-PendingChanges.ps1'
# RG-2's SUITE, WHICH THIS ROUND MOVES A CLAIM IN.
#
# test_print_range claims the range form's inputs are exactly From and
# To. That was true and this round makes it false, because the origin
# travels with the form as two hidden inputs. It reads the LIVE
# template - not as_left_by - so the claim really does fail, and the
# right answer is to move it rather than relax it: the visible date
# fields are still exactly From and To, and the hidden pair is claimed
# beside them.
RANGE = 'test_print_range.py'
# PP-1's SUITE, FOR THE SAME REASON.
#
# test_print_plan reads the planner's print links with a regex that
# ends at the closing quote right after ?to=. The two dates it checks
# are still exactly right; the quote is not there any more, because
# this round appends the origin. Over-tight anchor, same answer - the
# terminator is loosened and the dates are claimed exactly as before.
PLAN = 'test_print_plan.py'
ME = 'test_print_origin.py'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'PT-1, 22 Oct 2026'
CHECK = False
CREATES = ()

# ==========================================================================
# THE VIEW LEARNS WHERE THE READER CAME FROM
# ==========================================================================
# ANCHORED THROUGH THE DOCSTRING'S LAST LINE. The four lines that
# follow it open the shopping list view too, word for word, and once()
# refused the round - correctly.
V_WAS = '''    quarter.
    """
    today = timezone.now().date()
    monday = today - timedelta(days=today.weekday())
    start = week_of(request.GET.get('from'), monday)
    end = week_of(request.GET.get('to'), start + timedelta(days=6))
    if end < start:
        start, end = end, start'''

V_NOW = '''    quarter.
    """
    today = timezone.now().date()
    monday = today - timedelta(days=today.weekday())
    start = week_of(request.GET.get('from'), monday)
    end = week_of(request.GET.get('to'), start + timedelta(days=6))
    if end < start:
        start, end = end, start

    # WHERE THE READER CAME FROM - PT-1, 22 Oct 2026.
    #
    # NOT the shape of the sheet, which is still worked out from the
    # two dates below exactly as RG-1 left it. This is the one fact no
    # arithmetic on those dates can recover: a day sheet and a one-day
    # range are the same two dates, and a week sheet and a Monday to
    # Sunday range are the same two dates. Back has to know which.
    #
    # The planner already reads ?view= and ?date=; its own switcher
    # uses them. Nothing new is invented here, and anything else in
    # the parameter falls back to no origin at all.
    origin = request.GET.get('view')
    if origin not in ('month', 'week', 'day'):
        origin = ''
    came_from = week_of(request.GET.get('date'), None)

    # THE BOUNDS OF THE PERIOD THE READER WAS LOOKING AT.
    #
    # Demetri, 22 October: "the earliest date that I can pick is the
    # first day of the week displayed below, and the latest date that
    # I can pick is the last day of the week displayed below."
    range_min = range_max = None
    if origin and came_from:
        if origin == 'week':
            range_min = monday_of(came_from)
            range_max = range_min + timedelta(days=6)
        elif origin == 'month':
            range_min = date(came_from.year, came_from.month, 1)
            range_max = (date(came_from.year + (came_from.month == 12),
                              came_from.month % 12 + 1, 1)
                         - timedelta(days=1))
        else:
            range_min = range_max = came_from

    # AND THE SERVER CLAMPS, not only the browser.
    #
    # min and max on a date input are a REQUEST to a browser. They are
    # what stops somebody picking a date outside the week; they are not
    # what stops the date working if they do, and ?from= is a string
    # anybody can type - A5. The attributes and the clamp are two
    # halves of one claim.
    if range_min and range_max:
        start = min(max(start, range_min), range_max)
        end = min(max(end, range_min), range_max)
        if end < start:
            start, end = end, start'''

# ==========================================================================
# AND THE SHEET IS CROPPED TO WHAT WAS ASKED FOR
# ==========================================================================
W_WAS = '''    weeks, cursor = [], grid_start
    while cursor <= grid_end:
        days = []
        for i in range(7):
            when = cursor + timedelta(days=i)
            days.append({'''

W_NOW = '''    # CROPPED WHEN THE READER NARROWED A PERIOD - PT-1, 22 Oct 2026.
    #
    # THIS OVERRIDES RG-1, which renders whole Monday-to-Sunday weeks
    # and greys the days outside the range, on the reasoning that
    # three blank cells at the front of a seven column grid read as
    # missing data rather than as a boundary. That reasoning is sound.
    # Demetri overruled it on 22 October: "the print must only show,
    # and then only print the date range selected."
    #
    # ONLY WHEN THE PERIOD WAS NARROWED. A reader who prints a whole
    # week, month or day gets RG-1's sheet unchanged, because there is
    # nothing out of range in it to drop.
    crop = bool(range_min and range_max
                and (start > range_min or end < range_max))

    weeks, cursor = [], grid_start
    while cursor <= grid_end:
        days = []
        for i in range(7):
            when = cursor + timedelta(days=i)
            if crop and not (start <= when <= end):
                continue
            days.append({'''

W2_WAS = '''        weeks.append({'start': cursor, 'days': days})
        cursor += timedelta(days=7)'''

W2_NOW = '''        # A WEEK WITH NOTHING LEFT IN IT IS NOT AN EMPTY WEEK, IT IS
        # NOT A WEEK - PT-1. Cropping a range to three days in the
        # middle of a month would otherwise leave four blank rows.
        #
        # cols TRAVELS WITH THE ROW. The grid is seven columns by CSS,
        # and a cropped row needs as many as it has days or three days
        # sit squashed at the left with four columns of white beside
        # them. The template cannot count inside a grid-template rule,
        # so the count is handed to it.
        if days:
            weeks.append({'start': cursor, 'days': days,
                          'cols': len(days)})
        cursor += timedelta(days=7)'''

C_WAS = '''    return render(request, 'meal_plan_print.html', {
        'start': start,
        'end': end,
        'weeks': weeks,
        'sheet': sheet,'''

C_NOW = '''    # BACK GOES WHERE IT CAME FROM - PT-1, 22 Oct 2026. Findings 3, 4
    # and 5, which were one line: Back was the bare planner URL, so it
    # landed on the default view on today's date whatever you had been
    # looking at.
    back_url = reverse('meal_planner')
    if origin and came_from:
        back_url = '%s?view=%s&date=%s' % (back_url, origin,
                                           came_from.isoformat())

    return render(request, 'meal_plan_print.html', {
        'start': start,
        'end': end,
        'weeks': weeks,
        'sheet': sheet,
        # PT-1, 22 Oct 2026 - the origin, and what follows from it.
        'origin': origin,
        'came_from': came_from,
        'back_url': back_url,
        # NOT RENDERED AT ALL ON A DAY, rather than disabled or
        # hidden: Demetri, 22 October, "it must not give me the date
        # options... It cannot be more than that."
        'show_range': origin != 'day',
        'range_min': range_min,
        'range_max': range_max,
        'crop': crop,'''

# ==========================================================================
# THE PRINT PAGE
# ==========================================================================
B_WAS = '''        <a href="{% url 'meal_planner' %}" class="btn action-back"
           aria-label="Back to the planner">'''

B_NOW = '''        {# BACK GOES WHERE IT CAME FROM - PT-1, 22 Oct 2026.          #}
        {# This was the bare planner URL, so Back from a printed week  #}
        {# landed on the month view on today's date. The view builds   #}
        {# the whole address, because a template assembling a query    #}
        {# string is a second place that has to agree about the        #}
        {# parameter names.                                            #}
        <a href="{{ back_url }}" class="btn action-back"
           aria-label="Back to the planner">'''

F_WAS = '''    <form method="get" action="" class="pp-range pp-noprint">'''

F_NOW = '''    {# NOT RENDERED ON A DAY - PT-1, 22 Oct 2026. Demetri: "In the   #}
    {# Day View, when I press the Print Button, it must not give me   #}
    {# the date options. It must only be a print of the day that is   #}
    {# showing below. It cannot be more than that."                   #}
    {#                                                                #}
    {# NOT hidden and not disabled. A control that is not on offer    #}
    {# should not be on the page.                                     #}
    {% if show_range %}
    <form method="get" action="" class="pp-range pp-noprint">
        {# THE ORIGIN TRAVELS WITH THE FORM - PT-1. Without these two  #}
        {# the first use of Show these days would lose the week it     #}
        {# was bounded to, and the second would be unbounded.          #}
        {% if origin %}<input type="hidden" name="view" value="{{ origin }}">{% endif %}
        {% if came_from %}<input type="hidden" name="date" value="{{ came_from|date:'Y-m-d' }}">{% endif %}'''

I1_WAS = '''            <input type="date" id="ppFrom" name="from" class="pp-range-date"
                   value="{{ start|date:'Y-m-d' }}">'''

I1_NOW = '''            {# BOUNDED TO THE PERIOD BELOW - PT-1, 22 Oct 2026. And  #}
            {# the server clamps as well: min is a request to a       #}
            {# browser, not a rule, and ?from= is a string anybody    #}
            {# can type.                                              #}
            <input type="date" id="ppFrom" name="from" class="pp-range-date"
                   value="{{ start|date:'Y-m-d' }}"{% if range_min %} min="{{ range_min|date:'Y-m-d' }}" max="{{ range_max|date:'Y-m-d' }}"{% endif %}>'''

I2_WAS = '''            <input type="date" id="ppTo" name="to" class="pp-range-date"
                   value="{{ end|date:'Y-m-d' }}">'''

I2_NOW = '''            <input type="date" id="ppTo" name="to" class="pp-range-date"
                   value="{{ end|date:'Y-m-d' }}"{% if range_min %} min="{{ range_min|date:'Y-m-d' }}" max="{{ range_max|date:'Y-m-d' }}"{% endif %}>'''

E_WAS = '''        <button type="submit" class="btn action-secondary">Show these days</button>
    </form>'''

E_NOW = '''        <button type="submit" class="btn action-secondary">Show these days</button>
    </form>
    {% endif %}'''

G_WAS = '''            {% if sheet != 'week' %}'''

G_NOW = '''            {% if sheet != 'week' and not crop %}'''

R_WAS = '''                <div class="pp-grid">'''

R_NOW = '''                {# AS MANY COLUMNS AS THERE ARE DAYS WHEN CROPPED -  #}
                {# PT-1, 22 Oct 2026. The rule is seven by CSS, and   #}
                {# three days in a seven column grid sit squashed at  #}
                {# the left with four columns of white beside them.   #}
                <div class="pp-grid"{% if crop %} style="grid-template-columns: repeat({{ week.cols }}, minmax(0, 1fr));"{% endif %}>'''

# ==========================================================================
# AND THE PLANNER SAYS WHERE IT IS SENDING THEM FROM
# ==========================================================================
P1_WAS = '''        <a href="{% url 'meal_plan_print' %}?from={{ sl_from|date:'Y-m-d' }}&amp;to={{ sl_to|date:'Y-m-d' }}"
           class="btn action-secondary">'''

P1_NOW = '''        {# AND WHICH VIEW IS SENDING THEM - PT-1, 22 Oct 2026. The   #}
        {# two dates say what to print; they cannot say where Back    #}
        {# should land, because a day and a one-day range are the     #}
        {# same two dates.                                            #}
        <a href="{% url 'meal_plan_print' %}?from={{ sl_from|date:'Y-m-d' }}&amp;to={{ sl_to|date:'Y-m-d' }}&amp;view={{ view_mode }}&amp;date={{ anchor|date:'Y-m-d' }}"
           class="btn action-secondary">'''

P2_WAS = '''                <a class="action-more-item" role="menuitem"
                   href="{% url 'meal_plan_print' %}?from={{ sl_from|date:'Y-m-d' }}&amp;to={{ sl_to|date:'Y-m-d' }}">'''

RG_WAS = '''    c['  From and To, which is what the view reads'] = (
        sorted(re.findall(r'<input[^>]*name="(\\w+)"', form))
        == ['from', 'to'])'''

RG_NOW = '''    # THE DATE FIELDS, NOT EVERY INPUT - PT-1, 22 Oct 2026.
    #
    # This counted every input in the form and required exactly two.
    # PT-1 puts the origin in the form as two hidden inputs, so that
    # Show these days does not lose the week it is bounded to, and
    # this claim failed in the sweep. It is MOVED, not relaxed: the
    # visible date fields are still exactly From and To, and the
    # hidden pair is claimed on the line below.
    c['  From and To, which is what the view reads'] = (
        sorted(re.findall(r'<input[^>]*type="date"[^>]*name="(\\w+)"',
                          form)) == ['from', 'to'])
    c['  and the origin travels hidden beside them - PT-1'] = (
        sorted(re.findall(r'<input[^>]*type="hidden"[^>]*name="(\\w+)"',
                          form)) == ['date', 'view'])'''

PL_WAS = '''            r'href="/meal_plans/print/\\?from=([0-9-]+)&amp;to=([0-9-]+)"','''

PL_NOW = '''            # [^"]*" RATHER THAN " - PT-1, 22 Oct 2026. The link now
            # carries the origin after the two dates, and this regex
            # ended at the quote that used to follow ?to=. What it
            # claims is unchanged: from and to are the period of the
            # view you are on.
            r'href="/meal_plans/print/\\?from=([0-9-]+)&amp;'
            r'to=([0-9-]+)[^"]*"','''

P2_NOW = '''                {# THE SAME FOUR PARAMETERS AS THE BAR'S OWN Print -  #}
                {# PT-1. Two entry points to one page that disagreed   #}
                {# about what it is given would be the next finding.   #}
                <a class="action-more-item" role="menuitem"
                   href="{% url 'meal_plan_print' %}?from={{ sl_from|date:'Y-m-d' }}&amp;to={{ sl_to|date:'Y-m-d' }}&amp;view={{ view_mode }}&amp;date={{ anchor|date:'Y-m-d' }}">'''


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
    raise SystemExit('PT-1 REFUSED: %s' % msg)


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
        print('PT-1  already applied - the print sheet knows which view '
              'sent it.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # THE PLANNER MUST ALREADY KNOW ITS OWN VIEW AND DATE. MV-1 put
    # both in the context; this round only forwards them.
    pl = os.path.join(root, PLANNER)
    if "'view_mode': view_mode" not in v or "'anchor': anchor" not in v:
        refuse('%s: the planner does not publish view_mode and anchor, '
               'and this round forwards them rather than recomputing '
               'them' % VIEWS)

    v = swap(v, V_WAS, V_NOW, '%s (where the reader came from)' % VIEWS)
    v = swap(v, W_WAS, W_NOW, '%s (the crop)' % VIEWS)
    v = swap(v, W2_WAS, W2_NOW, '%s (and the columns)' % VIEWS)
    v = swap(v, C_WAS, C_NOW, '%s (the context)' % VIEWS)
    out[pv] = v

    pp_ = os.path.join(root, PRINT)
    t = read(pp_)
    t = swap(t, B_WAS, B_NOW, '%s (Back)' % PRINT)
    t = swap(t, F_WAS, F_NOW, '%s (the form opens)' % PRINT)
    t = swap(t, I1_WAS, I1_NOW, '%s (From)' % PRINT)
    t = swap(t, I2_WAS, I2_NOW, '%s (To)' % PRINT)
    t = swap(t, E_WAS, E_NOW, '%s (the form closes)' % PRINT)
    t = swap(t, G_WAS, G_NOW, '%s (the weekday strip)' % PRINT)
    t = swap(t, R_WAS, R_NOW, '%s (the grid)' % PRINT)
    out[pp_] = t

    p = read(pl)
    p = swap(p, P1_WAS, P1_NOW, '%s (the bar Print)' % PLANNER)
    p = swap(p, P2_WAS, P2_NOW, '%s (the More menu Print)' % PLANNER)
    out[pl] = p

    # AND RG-2'S CLAIM MOVES WITH THE CHANGE THAT MOVED IT.
    pr = os.path.join(root, RANGE)
    out[pr] = swap(read(pr), RG_WAS, RG_NOW,
                   '%s (the form inputs)' % RANGE)

    # AS DOES PP-1'S, which reads the link this round lengthens.
    ppl = os.path.join(root, PLAN)
    out[ppl] = swap(read(ppl), PL_WAS, PL_NOW,
                    '%s (the link regex)' % PLAN)

    # ---- REGISTRATION
    pg = os.path.join(root, PS1)
    g = read(pg)
    g = swap(g, """    'test_name_width.py'
)""", """    'test_name_width.py',
    # PT-1, 22 Oct 2026 - the print sheet knows which view sent it, so
    # Back lands where it started and a week bounds its own pickers.
    'test_print_origin.py'
)""", '%s (the suites)' % PS1)
    g = swap(g,
             """    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             """    @{ File = 'pages/templates/meal_plan_print.html'; Text = '{{ back_url }}'; What = 'PT-1: Back was the bare planner URL, so Back from a printed week landed on the month view on today date - Demetri reported it for all three views. The origin is carried because no arithmetic on from and to can recover it: a day sheet and a one-day range are the same two dates' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'start = min(max(start, range_min), range_max)'; What = 'PT-1: and the week bounds are CLAMPED on the server, not only offered as min and max to a browser - the attributes stop somebody picking a date outside the week, the clamp stops it working' },
    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             '%s (the sentinels)' % PS1)
    out[pg] = g

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # NL-1, 22 Oct 2026 - a generated name fits the column.
    'test_name_width.py',
]""", """    # NL-1, 22 Oct 2026 - a generated name fits the column.
    'test_name_width.py',
    # PT-1, 22 Oct 2026 - the print sheet knows which view sent it.
    'test_print_origin.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_namewidth',
]""", """    '.bak_namewidth',
    # PT-1, 22 Oct 2026 - the print sheet knows which view sent it.
    '.bak_printorigin',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # PT-1, 22 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nv = T.python_code_only(out[pv], payloads=True)

    # THE SHAPE IS STILL DERIVED. RG-1's rule is that no parameter may
    # say what the dates MEAN, and this round must not have quietly
    # become one.
    if "request.GET.get('shape')" in nv or "'sheet': request" in nv:
        refuse('%s: the sheet shape is being read from a parameter. '
               'RG-1 derives it from the two dates on purpose - a '
               'parameter saying what they mean can disagree with them'
               % VIEWS)
    for want in ("origin = request.GET.get('view')",
                 "came_from = week_of(request.GET.get('date'), None)"):
        if want not in nv:
            refuse('%s: %s is not there' % (VIEWS, want))

    # AND THE CLAMP IS REAL. min= on an input is a request to a
    # browser; without this the bound is decoration.
    if 'start = min(max(start, range_min), range_max)' not in nv:
        refuse('%s: the range is offered to the browser but not '
               'clamped on the server, so a typed ?from= still works'
               % VIEWS)

    # THE DAY VIEW MUST NOT RENDER THE FORM, not hide it.
    nt = T.code_only(out[pp_])
    if '{% if show_range %}' not in nt:
        refuse('%s: the range form is not conditional' % PRINT)
    if 'hidden' in nt.split('{% if show_range %}')[1].split('</form>')[0] \
            and 'type="hidden"' not in nt:
        refuse('%s: the form is hidden rather than not rendered' % PRINT)

    # AND THE TEMPLATE MUST STILL BALANCE - SB-2's lesson, 22 Oct 2026.
    # A tag inside a // comment is still a tag, and every text gate
    # reads one as a comment.
    for name, src in ((PRINT, out[pp_]), (PLANNER, out[pl])):
        body = T.code_only(src)
        for a, b in (('if', 'endif'), ('for', 'endfor'),
                     ('block', 'endblock')):
            o = len(re.findall(r'{%%\s*%s\b' % a, body))
            c = len(re.findall(r'{%%\s*%s\b' % b, body))
            if o != c:
                refuse('%s: %d {%% %s %%} against %d {%% %s %%}'
                       % (name, o, a, c, b))

    # BOTH ENTRY POINTS, OR NEITHER. Two links to one page that
    # disagree about what it is given is the next finding.
    np_ = out[pl]
    if np_.count('&amp;view={{ view_mode }}&amp;date={{ anchor') != 2:
        refuse('%s: %d print link(s) carry the origin, and there are '
               'two' % (PLANNER,
                        np_.count('&amp;view={{ view_mode }}'
                                  '&amp;date={{ anchor')))

    if CHECK:
        print('PT-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        the print sheet knows which view sent it')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('PT-1  applied - the print sheet knows which view sent it.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
