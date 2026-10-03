# -*- coding: utf-8 -*-
"""MC-3 - THE REST OF THE MEAL PLAN COLOURS

Demetri, 3 Oct 2026: "On Calendar view, we have a lot of changes to do to
the colours to bring them in line."

MC-2 took the loudest of them - five filled buttons in five colours.
This round takes the rest, on both views, and it found three things that
are more than colour.

==========================================================================
FINDING 1 - .btn-create's GREEN IS HALF DEAD AND HALF ALIVE
==========================================================================
meal_plans.html writes its primary as

    class="btn btn-create action-primary"

and `.btn.action-primary` in base is (0,2,0) against `.btn-create`'s
(0,1,0), so base wins and the button renders TEAL. The green rule has had
no effect since the day action-primary was added - which is why the page
looks right in a screenshot and wrong in the stylesheet.

But the EMPTY STATE writes

    class="btn btn-create btn-lg"

with no action-primary at all, and there the green is live. One rule,
two fates, and nothing in the file says so. The empty-state button takes
action-primary like its sibling and the whole .btn-create family goes.

==========================================================================
FINDING 2 - A DISABLED BUTTON THAT RENDERS ENABLED
==========================================================================
The no-permission branch writes

    class="btn btn-create-disabled action-primary"

and by the same specificity, base's `.btn.action-primary` paints it solid
teal. A user with no permission to create a meal plan sees a button that
looks exactly like a working one, greyed by nothing at all.

base already has the answer and the sibling page already uses it:
`.disabled-btn`, whose note reads "a switched-off primary is grey, not
pale teal". The span takes `action-primary disabled-btn` and renders
grey, unclickable, with pointer-events: none.

This is a BEHAVIOUR fix wearing a colour round's clothes, and it is named
here rather than slipped in.

==========================================================================
FINDING 3 - ML-1 LEFT FOUR DEAD RULES BEHIND
==========================================================================
.meal-plan-actions, .meal-plan-actions .btn, .meal-plan-actions .btn i
and .btn-action-disabled are all still in meal_plans.html. ML-1 removed
every element that wore them one day ago. They match nothing.

==========================================================================
AND THE SWEEP ITSELF
==========================================================================
Both pages, inside <style> only, never inside a comment:

    #2c3e50 -> --alv-ink          #f8f9fa -> --alv-surface
    #6c757d -> --alv-ink-soft     #e8e8e8 -> --alv-surface-deep
    #adb5bd -> --alv-ink-faint    #e9ecef -> --alv-line
    #ccc    -> --alv-ink-faint    #dee2e6 -> --alv-line
    #495057 -> --alv-ink          #f0f0f0 -> --alv-line-soft
    #e8f4ff -> --alv-accent-soft  #f8f9ff -> --alv-accent-soft
    #5a6fd6 -> --alv-accent-ink   rgba(102,126,234,.1) -> --alv-accent-ring

#28a745 IS NOT IN THAT TABLE, deliberately. It carries two different
intentions on the calendar page - a CREATE button and a "this day has a
meal" dot - and a blanket map would have painted a verb and a status the
same. The create button and its hover are handled by name and take the
accent; the two dots take --alv-good, which is the palette's green and
is what a status marker should be wearing. Twelfth time this week an
instrument has been offered a substring when the thing meant was a
place, and the first time one was refused before it ran.

The neutral drop shadows - rgba(0,0,0,0.06) and 0.08 and 0.1 - stay.
A shadow is a depth, not a hue, and the tree has no token for one.

Backups: .bak_caltone. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_caltone'
ROOT = os.getcwd()
CRLF = {}
LIST = os.path.join(ROOT, 'pages', 'templates', 'meal_plans.html')
CAL = os.path.join(ROOT, 'pages', 'templates', 'meal_plan_calendar.html')

STYLE = re.compile(r'(<style[^>]*>)(.*?)(</style>)', re.S)
COMMENT = re.compile(r'/\*.*?\*/', re.S)

MAP = {
    '#2c3e50': 'var(--alv-ink)',
    '#495057': 'var(--alv-ink)',
    '#6c757d': 'var(--alv-ink-soft)',
    '#adb5bd': 'var(--alv-ink-faint)',
    '#ccc': 'var(--alv-ink-faint)',
    '#f8f9fa': 'var(--alv-surface)',
    '#e8e8e8': 'var(--alv-surface-deep)',
    '#e9ecef': 'var(--alv-line)',
    '#dee2e6': 'var(--alv-line)',
    '#f0f0f0': 'var(--alv-line-soft)',
    '#e8f4ff': 'var(--alv-accent-soft)',
    '#f8f9ff': 'var(--alv-accent-soft)',
    '#5a6fd6': 'var(--alv-accent-ink)',
    'rgba(102, 126, 234, 0.1)': 'var(--alv-accent-ring)',
}


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
            raise SystemExit('MC3: %s is not a byte copy' % bak)


def code_only(t):
    t = re.sub(r'\{#.*?#\}', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), t, flags=re.S)


def swap(path, text, old, new, what):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('MC3: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


def sweep_css(text, mapping):
    """Replace colour literals inside <style> only, never inside a CSS
    comment. Lifted from apply_fsr_palette, which learned the hard way
    that a note NAMING a colour is not a use of it."""
    tally = {k: 0 for k in mapping}

    def one_block(m):
        headp, body, tail = m.group(1), m.group(2), m.group(3)
        parts, last = [], 0
        for c in COMMENT.finditer(body):
            parts.append(('code', body[last:c.start()]))
            parts.append(('note', c.group(0)))
            last = c.end()
        parts.append(('code', body[last:]))
        out = []
        for kind, chunk in parts:
            if kind == 'code':
                for lit, tok in mapping.items():
                    # A WORD BOUNDARY AFTER ')' IS NOT A BOUNDARY. The
                    # first draft appended \b to every literal, which is
                    # right for #f8f9fa - it stops #f8f9fab matching -
                    # and silently wrong for rgba(102, 126, 234, 0.1),
                    # which ends in ')' and is followed by ';'. Two
                    # non-word characters, no boundary between them, so
                    # the purple ring was reported as zero uses and left
                    # on the page. Thirteenth time this week an
                    # instrument has been right about the wrong thing.
                    pat = re.escape(lit)
                    if lit[-1].isalnum():
                        pat += r'\b'
                    n = len(re.findall(pat, chunk))
                    if n:
                        tally[lit] += n
                        chunk = re.sub(pat, tok, chunk)
            out.append(chunk)
        return headp + ''.join(out) + tail

    return STYLE.sub(one_block, text), tally


print('=' * 74)
print('MC-3 - THE REST OF THE MEAL PLAN COLOURS%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# meal_plans.html
# ==========================================================================
t, raw = read(LIST)
L_BEFORE = code_only(t.replace('\r\n', '\n'))

if 'btn-create' not in code_only(t):
    print('  meal_plans.html            already swept')
    L_TALLY = {}
else:
    # ---- FINDING 1. The empty-state button is the only live green. ------
    t = swap(LIST, t,
             """                <a href="{% url 'create_meal_plan' %}" class="btn btn-create btn-lg">""",
             """                {# MC-3, 3 Oct 2026. THE ONLY LIVE GREEN ON THIS PAGE. The    #}
                {# bar's primary writes "btn btn-create action-primary" and    #}
                {# base's .btn.action-primary (0,2,0) outranks .btn-create     #}
                {# (0,1,0), so that one has rendered teal since the day        #}
                {# action-primary was added. This one carried no               #}
                {# action-primary at all, so #28a745 was live here and         #}
                {# nowhere else - one rule with two fates and nothing in the   #}
                {# file saying so.                                             #}
                <a href="{% url 'create_meal_plan' %}" class="btn action-primary btn-lg">""",
             'the empty-state create button')

    # AND THE DEAD HALF OF THE SAME CLASS. The bar's primary carried
    # btn-create too, where it had never had any effect; leaving the name
    # on the element after deleting the rule would leave the next reader
    # looking for a rule that is not there.
    t = swap(LIST, t,
             """        <a href="{% url 'create_meal_plan' %}" class="btn btn-create action-primary">""",
             """        <a href="{% url 'create_meal_plan' %}" class="btn action-primary">""",
             'the bar primary')

    # ---- FINDING 2. A disabled button that renders enabled. -------------
    t = swap(LIST, t,
             """        <span class="btn btn-create-disabled action-primary" title="You don't have permission to create meal plans">""",
             """        {# MC-3. THIS RENDERED AS A WORKING BUTTON. Same specificity    #}
        {# story: base's .btn.action-primary painted it solid teal, so  #}
        {# a user with no permission saw a button that looked exactly   #}
        {# like a live one. base already had the answer and the sibling #}
        {# calendar page already used it - .disabled-btn, whose own     #}
        {# note reads "a switched-off primary is grey, not pale teal",  #}
        {# and which sets pointer-events: none so the span is not a     #}
        {# working control either.                                      #}
        <span class="btn action-primary disabled-btn" title="You don't have permission to create meal plans">""",
             'the no-permission create span')

    t = swap(LIST, t, """.btn-create {
    background: #28a745;
    color: white;
    padding: 12px 30px;
    font-size: 16px;
    font-weight: 500;
    border-radius: 8px;
    border: none;
}

.btn-create:hover {
    background: #218838;
    color: white;
}

.btn-create-disabled {
    background: #6c757d;
    color: white;
    padding: 12px 30px;
    font-size: 16px;
    font-weight: 500;
    border-radius: 8px;
    border: none;
    opacity: 0.6;
    cursor: not-allowed;
    pointer-events: none;
}""",
             """/* .btn-create AND .btn-create-disabled ARE GONE - MC-3, 3 Oct 2026.
   Three rules, four literals (#28a745, #218838, #6c757d, white). Two of
   the three had never applied to the button they were written for,
   because base's .btn.action-primary outranks a single class; the third
   applied only to the empty state, which now wears action-primary like
   everything else. Padding and radius come from the bar rule in base,
   which is what owns the geometry of a button in an action bar. */""",
             'the btn-create rules')

    t = swap(LIST, t, """    .empty-state .btn-create {""",
             """    .empty-state .action-primary {""",
             'the empty-state 768 rule')

    # ---- FINDING 3. ML-1 left four dead rules. --------------------------
    t = swap(LIST, t, """.meal-plan-actions {
    display: flex;
    gap: 6px;
    justify-self: end;
}

.meal-plan-actions .btn {
    padding: 6px 12px;
    font-size: 12px;
    border-radius: 5px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
    font-weight: 500;
}

.meal-plan-actions .btn i {
    font-size: 11px;
}

.btn-action-disabled {
    background: var(--alv-surface-deep);
    color: #6c757d;
    border: none;
    opacity: 0.5;
    cursor: not-allowed;
    pointer-events: none;
}""",
             """/* FOUR DEAD RULES, SWEPT - MC-3. ML-1 moved this page's row actions
   onto base's .row-actions on 2 Oct and removed every element that wore
   .meal-plan-actions or .btn-action-disabled. The rules stayed. They
   matched nothing for a day, and a rule that matches nothing is worse
   than no rule: the next reader has to work out whether it is load
   bearing before they can touch anything near it. */""",
             'the four dead action rules')

    t = swap(LIST, t, """    .meal-plan-actions {
        justify-self: start;
    }
""", '', 'the dead 768 action rule')

    t, L_TALLY = sweep_css(t, MAP)

    if not CHECK:
        back_up(LIST, raw)
        write(LIST, t)
    print('  meal_plans.html            btn-create gone, 4 dead rules swept, '
          '%d literals tokenised'
          % sum(v for v in L_TALLY.values()))

# ==========================================================================
# meal_plan_calendar.html
# ==========================================================================
t, raw = read(CAL)

# THE SENTINEL IS WHAT THE ROUND CHANGED, NOT A NAME THE ROUND KEEPS.
# The first draft asked whether .create-plan-btn was still present - it
# is, and always will be; this round changed its COLOUR, not its name.
# So the second run took the "not yet applied" path and died on an
# anchor it had already consumed. Fourteenth time this week.
if '#28a745' not in code_only(t):
    print('  meal_plan_calendar.html    already swept')
    C_TALLY = {}
else:
    # #28a745 BY NAME, NOT BY SWEEP. Three uses, two intentions.
    t = swap(CAL, t, """.create-plan-btn {
    width: 100%;
    padding: 12px;
    background: #28a745;""",
             """/* MC-3, 3 Oct 2026. #28a745 IS HANDLED BY NAME ON THIS PAGE, not by
   the sweep, because it carries two different intentions here: a CREATE
   button and a "this day has a meal" dot. A blanket map would have
   painted a verb and a status the same colour and called it tidying.
   The button is a verb, so it takes the accent like every other create
   in the tree; the two dots keep a green, but the palette's own
   --alv-good rather than a literal. */
.create-plan-btn {
    width: 100%;
    padding: 12px;
    background: var(--alv-accent);""",
             'the create-plan button')

    t = swap(CAL, t, """.create-plan-btn:hover {
    background: #218838;""",
             """.create-plan-btn:hover {
    background: var(--alv-accent-ink);""",
             'the create-plan hover')

    t = swap(CAL, t, """.create-plan-btn-disabled {
    background: #6c757d;""",
             """.create-plan-btn-disabled {
    background: var(--alv-neutral);""",
             'the create-plan disabled')

    t = swap(CAL, t, """.mini-calendar-day.has-meal::after {
    content: '';
    position: absolute;
    bottom: 3px;
    left: 50%;
    transform: translateX(-50%);
    width: 6px;
    height: 6px;
    background: #28a745;
    border-radius: 50%;
}""",
             """.mini-calendar-day.has-meal::after {
    content: '';
    position: absolute;
    bottom: 3px;
    left: 50%;
    transform: translateX(-50%);
    width: 6px;
    height: 6px;
    /* A STATUS, NOT A VERB - MC-3. This dot and the legend swatch below
       say "there is a meal on this day". They keep a green because that
       is what Demetri reads them by, but it is the palette's green. */
    background: var(--alv-good);
    border-radius: 50%;
}""",
             'the has-meal dot')

    t = swap(CAL, t, """.legend-dot.meal {
    background: #28a745;""",
             """.legend-dot.meal {
    background: var(--alv-good);""",
             'the legend dot')

    t = swap(CAL, t, """.add-recipe-btn-disabled {
    background: #adb5bd !important;""",
             """.add-recipe-btn-disabled {
    background: var(--alv-ink-faint) !important;""",
             'the add-recipe disabled')

    # THE FOUR THE SWEEP CANNOT REACH. sweep_css only enters <style>, and
    # these are an inline style attribute, two more inside one, and a
    # string assigned to element.style in a script.
    t = swap(CAL, t,
             """<p style="color: #adb5bd; text-align: center; padding: 20px;">""",
             """<p style="color: var(--alv-ink-faint); text-align: center; padding: 20px;">""",
             'the inline empty-list paragraph')

    t = swap(CAL, t,
             """border: 1px solid #dee2e6; border-radius: 8px;""",
             """border: 1px solid var(--alv-line); border-radius: 8px;""",
             'the inline recipe list border')

    t = swap(CAL, t,
             """border-bottom: 1px solid #f0f0f0;""",
             """border-bottom: 1px solid var(--alv-line-soft);""",
             'the inline recipe row rule')

    t = swap(CAL, t,
             """element.style.background = '#e8f4ff';""",
             """/* A LITERAL ASSIGNED IN SCRIPT IS STILL A LITERAL - MC-3. The sweep
       only enters <style>, so this one had to be named. */
    element.style.background = 'var(--alv-accent-soft)';""",
             'the script background')

    t, C_TALLY = sweep_css(t, MAP)

    if not CHECK:
        back_up(CAL, raw)
        write(CAL, t)
    print('  meal_plan_calendar.html    7 named, 4 out of reach of the sweep, '
          '%d literals tokenised' % sum(v for v in C_TALLY.values()))

print('-' * 74)
for lit in sorted(set(list(L_TALLY) + list(C_TALLY))):
    a, b = L_TALLY.get(lit, 0), C_TALLY.get(lit, 0)
    if a or b:
        print('    %-26s -> %-26s  list %d, calendar %d'
              % (lit, MAP[lit], a, b))
print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
import alv_tree

NOW = {p: code_only(read(p)[0].replace('\r\n', '\n')) for p in (LIST, CAL)}
WAS = {p: code_only(read(p + SUFFIX)[0].replace('\r\n', '\n'))
       for p in (LIST, CAL)}
BASE = open(alv_tree.path_of('base.html'), encoding='utf-8',
            errors='replace').read()

# 1. EVERY SWEPT LITERAL IS GONE FROM BOTH PAGES.
for p in (LIST, CAL):
    name = os.path.basename(p)
    for lit in MAP:
        pat = re.escape(lit) + (r'\b' if lit[-1].isalnum() else '')
        n = len(re.findall(pat, NOW[p]))
        if n:
            raise SystemExit('MC3: %s still carries %d x %s' % (name, n, lit))
    print('  %-26s none of the %d swept literals survive'
          % (name, len(MAP)))

# 2. AND SO ARE THE ONES HANDLED BY NAME.
for p, lits in ((LIST, ('#28a745', '#218838')),
                (CAL, ('#28a745', '#218838'))):
    name = os.path.basename(p)
    for lit in lits:
        n = len(re.findall(re.escape(lit) + r'\b', NOW[p]))
        if n:
            raise SystemExit('MC3: %s still carries %d x %s' % (name, n, lit))
    print('  %-26s %s gone too' % (name, ' and '.join(lits)))

# 3. EVERY TOKEN THIS ROUND REACHED FOR EXISTS IN base.
for tok in sorted(set(MAP.values()) | {'var(--alv-good)', 'var(--alv-accent)',
                                       'var(--alv-neutral)'}):
    nm = tok[4:-1]
    if '%s:' % nm not in BASE:
        raise SystemExit('MC3: base does not define %s' % nm)
print('  base defines all %d tokens this round reached for'
      % len(set(MAP.values()) | {'var(--alv-good)', 'var(--alv-accent)',
                                 'var(--alv-neutral)'}))

# 4. FINDING 1 AND 2 - .btn-create IS GONE, AND SO IS THE FALSE PRIMARY.
lc = NOW[LIST]
for dead in ('btn-create', 'btn-create-disabled', 'meal-plan-actions',
             'btn-action-disabled'):
    if re.search(r'\b%s\b' % dead, lc):
        raise SystemExit('MC3: meal_plans.html still carries %s' % dead)
print('  meal_plans.html            .btn-create, .btn-create-disabled, '
      '.meal-plan-actions and .btn-action-disabled all gone')

if 'class="btn action-primary disabled-btn"' not in lc:
    raise SystemExit('MC3: the no-permission span is not on .disabled-btn')
if lc.count('action-primary') < 3:
    raise SystemExit('MC3: expected three action-primary uses - the bar, '
                     'the no-permission span and the empty state')
print('  the no-permission span is .action-primary.disabled-btn, and base '
      'paints that grey')

# 5. THE CONTROL. .disabled-btn must actually RESTYLE a primary, or
#    finding 2 has been "fixed" by swapping one invisible class for
#    another. A control that cannot fail is not a control.
m = re.search(r'\.btn\.action-primary\.disabled-btn[^{]*\{([^}]*)\}', BASE)
if not m or 'background' not in m.group(1):
    raise SystemExit('MC3: base does not repaint a disabled primary - '
                     'finding 2 has not been fixed, only renamed')
print('  CONTROL: base really does repaint .btn.action-primary.disabled-btn')

# 6. AND THE OTHER HALF OF THE CONTROL - the OLD markup really did render
#    as a live primary. If .btn-create-disabled had outranked base, there
#    was nothing to fix.
if 'btn-create-disabled action-primary' not in WAS[LIST]:
    raise SystemExit('MC3: the no-permission span never carried '
                     'action-primary - the premise of finding 2 is wrong')
print('  CONTROL: it really did carry action-primary, which outranked the '
      'grey by (0,2,0) to (0,1,0)')

# 7. THE EMPTY-STATE BUTTON CHANGED CLASS AND NOT DESTINATION.
for u in ("{% url 'create_meal_plan' %}", "{% url 'meal_plan_calendar' %}",
          "{% url 'meal_plans' %}"):
    if NOW[LIST].count(u) != WAS[LIST].count(u):
        raise SystemExit('MC3: the %s link count changed' % u)
print('  every link on the list page still goes where it went')

# 8. THE SWEEP NEVER LEFT A <style> BLOCK.
#
#    The first draft of this gate compared everything outside <style>
#    before and after and demanded it be identical. It failed a correct
#    page, because this round ALSO makes four NAMED swaps out there - a
#    class on the bar primary, a class on the no-permission span, a class
#    on the empty-state button, and on the calendar page an inline style
#    and a script assignment. The sweep is not the only thing that ran.
#
#    So the claim is narrowed to what it was always about: the sweep
#    replaces literals, and it must not have replaced one outside a style
#    block. Every swept literal still outside <style> must be exactly as
#    many as it was, and the four named places are checked separately
#    above and below.
for p in (LIST, CAL):
    name = os.path.basename(p)
    out_now = STYLE.sub('', read(p)[0])
    out_was = STYLE.sub('', read(p + SUFFIX)[0])
    for lit in MAP:
        pat = re.escape(lit) + (r'\b' if lit[-1].isalnum() else '')
        a = len(re.findall(pat, out_was))
        b = len(re.findall(pat, out_now))
        # The calendar's four named swaps DO remove three of these from
        # markup and script. Those are declared here by name; anything
        # else moving is the sweep escaping its block.
        allowed = {CAL: {'#adb5bd': 1, '#dee2e6': 1, '#f0f0f0': 1,
                         '#e8f4ff': 1}}.get(p, {}).get(lit, 0)
        if a - b != allowed:
            raise SystemExit('MC3: %s has %d x %s outside <style>, was %d, '
                             'expected a drop of %d'
                             % (name, b, lit, a, allowed))
    print('  %-26s the sweep stayed inside <style>' % name)

# 9. THE SHADOWS STAYED. A depth is not a hue, and the tree has no token
#    for one; a round that quietly ate them would be hard to notice.
for p in (LIST, CAL):
    name = os.path.basename(p)
    for sh in ('rgba(0, 0, 0, 0.0', 'rgba(0, 0, 0, 0.1'):
        if WAS[p].count(sh) != NOW[p].count(sh):
            raise SystemExit('MC3: %s lost a neutral shadow' % name)
print('  every neutral drop shadow is still there')

print('-' * 74)
print('  One rule with two fates, a disabled button that rendered')
print('  enabled, and four rules that had matched nothing for a day.')
print('  None of the three was visible in a screenshot.')
print('=' * 74)
