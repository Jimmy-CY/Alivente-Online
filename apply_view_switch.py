# -*- coding: utf-8 -*-
"""apply_view_switch.py - round MV-1, 19 Oct 2026.

RELEASE 4, PUSH 1. THREE ZOOM LEVELS ON ONE CALENDAR.

Demetri, testing the live planner: "why does this still have the time
calendar?" and "This daily list is not required...". Then, on the
design: "Monthly Calendar first - full page."

This is the switcher. MV-2, MV-3 and MV-4 are the three views it
switches between, and all four ship in one push - a control whose
three links render the same old list is a half-built feature sitting
on production.

ONE ANCHOR DATE, NOT THREE PARAMETERS. Month, Week and Day are three
zoom levels on the SAME DAY, so they travel on one `?date=`:

    ?view=month&date=2026-10-19     October
    ?view=week&date=2026-10-19      the week of the 19th
    ?view=day&date=2026-10-19       the 19th

Switch from the week of 19 Oct to Month and you land on October;
switch to Day and you land on the 19th. Three separate parameters
would each have to be kept in step by every link that moves the date -
the week arrows, the month arrows, Today, the picker's return, the
shopping list's range - which is six places to forget one.

?week= AND ?year=/?month= STILL WORK. MN-1 kept this screen's url
names pointing here on 18 Oct so that old links would not break; the
same reasoning applies to its query string, and `?week=` is what the
Shopping List and the Copy Week dialog already send.

SERVER-RENDERED, ON BASE'S OWN COMPONENT. `.alv-seg` with
`aria-current="page"`, the shape finance_expense has used since PN-1 -
not JavaScript. The URL stays shareable and the control works with
JavaScript off. MC-1 is the round that taught this screen what happens
when a view toggle is written by hand: both halves were in the markup
and the inactive one was white on white.

AND THE VIEW IS NOT REMEMBERED. You land on Month every time. A
remembered view needs a cookie or a user setting, and "why am I on Day
view?" three days later is a worse problem than one click.

Idempotent. Every file backed up to .bak_viewswitch.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_viewswitch'
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_view_switch.py'
PATCHER = 'apply_view_switch.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'MV-1, 19 Oct 2026'
VIEWS = ('month', 'week', 'day')
CHECK = False


# ============================================================== THE VIEW
ANCHOR_WAS = """def meal_planner(request):
    \"\"\"One week of dates, and the meals on them.\"\"\"

    today = timezone.now().date()
"""
ANCHOR_NOW = """def meal_planner(request):
    \"\"\"The calendar, at one of three zoom levels.

    MV-1, 19 Oct 2026 - it was one week of dates, and a mini calendar
    beside it to navigate with. Demetri, testing it: the daily list is
    not required, and the Monthly Calendar comes first, full page.
    \"\"\"

    today = timezone.now().date()

    # ---- ONE ANCHOR DATE FOR THREE VIEWS - MV-1, 19 Oct 2026.
    #
    # Month, Week and Day are three zoom levels on the SAME DAY, so
    # they travel on ONE parameter. Three would each have to be kept
    # in step by every link that moves the date - the week arrows, the
    # month arrows, Today, the picker's return - which is six places
    # to forget one.
    #
    # ?week= IS STILL READ, and second, because the Shopping List link
    # and the Copy Week dialog already send it and MN-1 kept this
    # screen's old addresses working on purpose.
    #
    # THE ADDRESS BAR IS A STRING SOMEBODY CAN TYPE - A5. Every one of
    # these falls back rather than raising.
    anchor = None
    for _param in ('date', 'week'):
        _raw = request.GET.get(_param)
        if not _raw:
            continue
        try:
            anchor = datetime.strptime(_raw, '%Y-%m-%d').date()
            break
        except (TypeError, ValueError):
            anchor = None
    if anchor is None:
        anchor = today

    # ---- WHICH VIEW - MV-1. Month is the landing view, by Demetri's
    # own words on 19 Oct: "Monthly Calendar first - full page". That
    # overrides the earlier answer of Week, which is dead.
    #
    # A LIST AND NOT A FREE STRING. `?view=<anything>` reaching a
    # template that branches on it is how a page ends up rendering
    # nothing at all.
    view_mode = request.GET.get('view', 'month')
    if view_mode not in ('month', 'week', 'day'):
        view_mode = 'month'
"""

YM_WAS = """    try:
        year = int(request.GET.get('year', today.year))
        if not 1900 <= year <= 2200:
            raise ValueError('out of range')
    except (TypeError, ValueError):
        year = today.year
    try:
        month = int(request.GET.get('month', today.month))
        if not 1 <= month <= 12:
            raise ValueError('out of range')
    except (TypeError, ValueError):
        month = today.month"""
YM_NOW = """    # FROM THE ANCHOR, NOT FROM TODAY - MV-1, 19 Oct 2026. These
    # defaulted to the current month, which was right while the month
    # was only a navigation strip beside a week. Month is the landing
    # VIEW now, so arriving with ?date=2026-12-03 and being shown
    # October would be the page ignoring the address it was given.
    try:
        year = int(request.GET.get('year', anchor.year))
        if not 1900 <= year <= 2200:
            raise ValueError('out of range')
    except (TypeError, ValueError):
        year = anchor.year
    try:
        month = int(request.GET.get('month', anchor.month))
        if not 1 <= month <= 12:
            raise ValueError('out of range')
    except (TypeError, ValueError):
        month = anchor.month"""

WEEK_WAS = """    asked = request.GET.get('week')
    if asked:
        try:
            week_start = datetime.strptime(asked, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            week_start = today
    else:
        week_start = today
"""
WEEK_NOW = """    # THE WEEK IS THE ANCHOR'S WEEK - MV-1, 19 Oct 2026. This block
    # read ?week= for itself; the anchor above now does that for all
    # three views, so there is one reading of the date instead of two
    # that could disagree.
    week_start = anchor
"""

CTX_WAS = """        'household_size': household_size(request.user),"""
CTX_NOW = """        'household_size': household_size(request.user),
        # MV-1, 19 Oct 2026 - the switcher. `anchor` is what every one
        # of its three links carries, so the date survives the switch.
        'view_mode': view_mode,
        'anchor': anchor,"""


# ============================================================ THE MARKUP
SEG_WAS = """        <a href="{% url 'recipe_management' %}" class="btn action-back" aria-label="Back to Recipes">
            <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
        </a>
    </div>
"""
SEG_NOW = """        <a href="{% url 'recipe_management' %}" class="btn action-back" aria-label="Back to Recipes">
            <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
        </a>
    </div>

    {# THE VIEW SWITCHER - MV-1, 19 Oct 2026.                        #}
    {#                                                               #}
    {# base owns .alv-seg, its pressed state and its focus ring, so  #}
    {# this page writes none of that - only the bar that holds it.   #}
    {# finance_expense has used exactly this shape since PN-1.       #}
    {#                                                               #}
    {# LINKS, NOT BUTTONS. The view is in the URL, so it survives a  #}
    {# refresh, it can be sent to somebody, and the control works    #}
    {# with JavaScript off. MC-1 is why this page does not roll its  #}
    {# own toggle: the last hand-written one had both halves in the  #}
    {# markup and painted the inactive one white on white.           #}
    {#                                                               #}
    {# EVERY LINK CARRIES THE ANCHOR, so switching zoom level keeps  #}
    {# the day you were looking at.                                  #}
    <div class="planner-view-bar">
        <div class="alv-seg" role="group" aria-label="Calendar view">
            <a href="?view=month&amp;date={{ anchor|date:'Y-m-d' }}"
               {% if view_mode == 'month' %}aria-current="page"{% endif %}>
                <i class="fas fa-calendar-alt"></i> Month
            </a>
            <a href="?view=week&amp;date={{ anchor|date:'Y-m-d' }}"
               {% if view_mode == 'week' %}aria-current="page"{% endif %}>
                <i class="fas fa-calendar-week"></i> Week
            </a>
            <a href="?view=day&amp;date={{ anchor|date:'Y-m-d' }}"
               {% if view_mode == 'day' %}aria-current="page"{% endif %}>
                <i class="fas fa-calendar-day"></i> Day
            </a>
        </div>
    </div>
"""


# ======================================= A DEAD RULE PF-2 LEFT BEHIND
# PK-1 put base's .alv-seg in the picker as a course strip and wrote
# one rule to let it wrap. PF-2 replaced that strip with five
# dropdowns three hours ago and did not take the rule with it, so
# `.picker-filter .alv-seg` now matches nothing on this page.
#
# IT IS HARMLESS AND IT IS STILL DRIFT. A selector that matches
# nothing is a claim about the page that has stopped being true, and
# the next person to read it will look for a segmented control in the
# picker and not find one.
#
# MV-1 CARRIES IT BECAUSE MV-1 FOUND IT. This round's own gate refuses
# to run against a page that already has an .alv-seg - it was written
# to catch a second switcher, and it caught this instead. And MV-1 is
# the round that puts a REAL .alv-seg back on this page, so leaving a
# stale selector for a different one would be actively misleading.
DEAD_WAS = """
/* THE FILTER STRIP. PK-1 built it for one course bar; PF-2 put five
   dropdowns in it, by Demetri's choice, because fourteen courses
   already wrapped to two rows and five dimensions of chips would have
   been six rows with the recipes below the fold.

   base owns no multiselect - recipe_management rolled its own - so
   the rules are here, and they are the same shape so the two screens
   read alike. */
.picker-filter {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
}

.picker-filter .alv-seg {
    flex-wrap: wrap;
}
"""
DEAD_NOW = """
/* THE FILTER STRIP. PK-1 built it for one course bar; PF-2 put five
   dropdowns in it, by Demetri's choice, because fourteen courses
   already wrapped to two rows and five dimensions of chips would have
   been six rows with the recipes below the fold.

   base owns no multiselect - recipe_management rolled its own - so
   the rules are here, and they are the same shape so the two screens
   read alike.

   `.picker-filter .alv-seg { flex-wrap: wrap }` USED TO FOLLOW THIS.
   It let PK-1's course strip wrap onto a second row. PF-2 replaced
   that strip and left the rule, so it matched nothing; MV-1 removed
   it on the same day, having tripped over it. A selector that matches
   nothing is a claim about the page that has stopped being true. */
.picker-filter {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
}
"""


# =============================================================== THE CSS
CSS_WAS = """.week-nav {"""
CSS_NOW = """/* THE VIEW BAR - MV-1, 19 Oct 2026. Nothing but the box that holds
   base's component: .alv-seg brings its own border, radius, type,
   pressed state and focus ring, and a page that restated any of them
   would be the hand-rolled toggle MC-1 removed, wearing a new name.

   Centred, because the switcher is about the whole page rather than
   about one panel in it, and the page title above it is centred too. */
.planner-view-bar {
    display: flex;
    justify-content: center;
    margin: 0 0 16px;
}

@media screen and (max-width: 767px) {
    /* FULL WIDTH ON A PHONE, three equal thirds. At 390px the three
       labels and their icons measure 232px, which centred leaves two
       small targets either side of a big one. Demetri gets all three
       views at every width - his words - so all three get the same
       thumb. */
    .planner-view-bar .alv-seg {
        display: flex;
        width: 100%;
    }

    .planner-view-bar .alv-seg > * {
        flex: 1;
        justify-content: center;
        min-height: 44px;
    }
}

.week-nav {"""


# ====================================================== THE SENTINEL ROWS
SENT_WAS = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="pickerAuthor"'; What = 'PF-2: and all five filters are there - course, category, protein with vegetarian, author and favourites' },"""
SENT_NOW = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="pickerAuthor"'; What = 'PF-2: and all five filters are there - course, category, protein with vegetarian, author and favourites' },
    # ------------------------------------------------- MV-1, 19 Oct 2026
    @{ File = 'pages/templates/meal_planner.html'; Text = 'aria-label="Calendar view"'; What = 'MV-1: Month, Week and Day on base .alv-seg - server-rendered links, not JavaScript, so the view is in the URL' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'ONE ANCHOR DATE FOR THREE VIEWS'; What = 'MV-1: and the three zoom levels travel on one ?date=, so switching keeps the day you were looking at' },"""

SUITE_WAS = """    'test_pick_filter.py'
)"""
SUITE_NOW = """    'test_pick_filter.py',
    # MV-1, 19 Oct 2026 - the view switcher. Section 3 DRIVES all
    # three links and asks the view which day it landed on,
    # because a switcher that loses the date is worse than none.
    'test_view_switch.py'
)"""

TREE_WAS = """    'test_pick_filter.py',
]"""
TREE_NOW = """    'test_pick_filter.py',
    # MV-1, 19 Oct 2026 - three zoom levels on one calendar, after
    # Demetri said the daily list was not required and asked for the
    # Monthly Calendar first, full page.
    'test_view_switch.py',
]"""

RD_WAS = """    '.bak_pickfilter',
]"""
RD_NOW = """    '.bak_pickfilter',
    # MV-1, 19 Oct 2026 - RELEASE 4. The switcher: Month, Week and Day
    # on base's .alv-seg, server-rendered, with one ?date= carrying
    # the day between them. Month lands first, by his own words.
    '.bak_viewswitch',
]"""

WD_WAS = """CONVERTED_N = 115   # PF-2, 19 Oct 2026 - this round own suite"""
WD_NOW = """CONVERTED_N = 116   # MV-1, 19 Oct 2026 - this round own suite   # (was 115)   # PF-2, 19 Oct 2026 - this round own suite"""


# ============================================================== HELPERS
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
    raise SystemExit('MV-1 REFUSED: %s' % msg)


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



# ================================= THE REST OF THE PAGE'S NAVIGATION
# A VIEW THAT ONLY SURVIVES THE SWITCHER IS NOT IN THE URL.
#
# goWeek and goMonth build their own address and neither carried
# `view`, so in Week view the week arrow dropped the parameter and
# view_mode fell back to Month. You would press "the week before" and
# land on the month.
#
# THIS SUITE DID NOT CATCH IT. Section 3 drove the three switcher
# links and proved the DAY survived them; it never pressed anything
# else on the page. A control that is tested only against itself is
# tested against the half that was never in doubt - MV-2 tripped over
# this an hour later while reading the same file.
#
# So the view rides on every address this page builds, from the one
# place that knows it.
NAV_WAS = """function goWeek(week) {
    window.location.href = '{% url "meal_planner" %}?year={{ year }}&month={{ month }}&week=' + encodeURIComponent(week);
}

function goMonth(year, month) {
    window.location.href = '{% url "meal_planner" %}?year=' + year + '&month=' + month
        + '&week={{ week_start|date:"Y-m-d"|escapejs }}';
}"""
NAV_NOW = """// EVERY ADDRESS THIS PAGE BUILDS CARRIES THE VIEW - MV-1,
// 19 Oct 2026. Neither of these did, so pressing the week arrow while
// in Week view dropped `view` and landed you on the Month.
//
// ONE PLACE KNOWS IT. A second copy of `?view=` in each function is
// two places to forget it, and this round is the one proving that is
// how it gets forgotten.
var plannerView = '{{ view_mode|escapejs }}';

function plannerUrl(params) {
    var p = new URLSearchParams(params);
    p.set('view', plannerView);
    return '{% url "meal_planner" %}?' + p.toString();
}

function goWeek(week) {
    window.location.href = plannerUrl({
        year: '{{ year }}', month: '{{ month }}', week: week});
}

function goMonth(year, month) {
    window.location.href = plannerUrl({
        year: year, month: month,
        week: '{{ week_start|date:"Y-m-d"|escapejs }}'});
}

// AND A DAY, which Month and the day strip both need to send. It
// goes on ?date=, the one parameter all three views read.
function goDay(dateStr, view) {
    var p = new URLSearchParams({date: dateStr});
    p.set('view', view || plannerView);
    window.location.href = '{% url "meal_planner" %}?' + p.toString();
}"""

def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pv = os.path.join(root, VIEW)
    pt = os.path.join(root, TPL)
    v = read(pv)
    t = read(pt)
    t_before = t

    # ---------------------------------------------------------------- 0
    if 'ONE ANCHOR DATE FOR THREE VIEWS' in v:
        print('MV-1  already applied - the planner has three views.')
        return 0

    # ---------------------------------------------------------------- 1
    # THE FAULT MUST BE THERE: one view, and no way to ask for another.
    sys.path.insert(0, root)
    import alv_tree as T
    if 'view_mode' in T.python_code_only(v, payloads=True):
        refuse('%s already has a view_mode' % VIEW)
    # ASKED OF THE MARKUP, NOT OF THE STYLESHEET. The first cut
    # searched the whole file for `alv-seg` and refused this round
    # over a dead CSS rule - which was worth finding, and is not an
    # element. A page HAVING a seg and a page having a RULE about one
    # are different facts.
    if 'class="alv-seg"' in T.code_only(t):
        refuse('%s already carries an .alv-seg element - MC-1 removed '
               "this page's hand-rolled toggle and MV-1 is what puts a "
               'standard one back' % TPL)

    # ---------------------------------------------------------------- 2
    v = swap(v, ANCHOR_WAS, ANCHOR_NOW, '%s (the anchor)' % VIEW)
    v = swap(v, YM_WAS, YM_NOW, '%s (year and month)' % VIEW)
    v = swap(v, WEEK_WAS, WEEK_NOW, '%s (the week)' % VIEW)
    v = swap(v, CTX_WAS, CTX_NOW, '%s (the context)' % VIEW)
    out[pv] = v

    t = swap(t, SEG_WAS, SEG_NOW, '%s (the switcher)' % TPL)
    t = swap(t, DEAD_WAS, DEAD_NOW, '%s (PF-2 dead rule)' % TPL)
    t = swap(t, CSS_WAS, CSS_NOW, '%s (the view bar)' % TPL)
    t = swap(t, NAV_WAS, NAV_NOW, '%s (the navigation)' % TPL)
    out[pt] = t

    # ---------------------------------------------------------------- 3
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
    out[pw] = swap(read(pw), WD_WAS, WD_NOW, '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------------- 4
    # THE GATES.
    for k, val in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.relpath(k, root), e.lineno, e.msg))

    nv = T.python_code_only(out[pv], payloads=True)
    nt = out[pt]
    markup = T.code_only(nt)

    # THE VIEW IS A LIST AND NOT A FREE STRING. `?view=<anything>`
    # reaching a template that branches on it is how a page renders
    # nothing at all.
    if "if view_mode not in ('month', 'week', 'day')" not in nv:
        refuse('%s does not clamp view_mode to the three it knows'
               % VIEW)
    if "view_mode = request.GET.get('view', 'month')" not in nv:
        refuse("%s: month is not the default view, and Demetri's own "
               'words on 19 Oct were "Monthly Calendar first"' % VIEW)

    # EVERY LINK CARRIES THE ANCHOR. A switcher that loses the date is
    # worse than no switcher: you press Week and land on this week.
    links = re.findall(r'href="\?view=(\w+)&amp;date=\{\{ anchor', markup)
    if sorted(links) != sorted(VIEWS):
        refuse('%s: the switcher links are %r, expected one per view '
               'and every one carrying the anchor' % (TPL, links))

    # ON BASE'S COMPONENT, AND THE PAGE REDEFINES NOTHING OF IT.
    if 'class="alv-seg" role="group"' not in markup:
        refuse("%s: the switcher is not base's .alv-seg" % TPL)
    if re.search(r'(?m)^\s*\.alv-seg\s*\{', markup):
        refuse('%s: the page writes its own .alv-seg rule. base owns '
               'the component; this round owns the bar around it.'
               % TPL)
    if re.search(r'\.picker-filter\s+\.alv-seg', markup):
        refuse('%s: the dead .picker-filter .alv-seg rule survived - it '
               'matched nothing after PF-2 and would now read as a rule '
               'about THIS switcher' % TPL)
    if markup.count('aria-current="page"') < 1:
        refuse('%s: nothing marks the current view' % TPL)

    # SERVER-RENDERED. A switcher built from buttons and JavaScript
    # cannot be linked to and does not survive a refresh.
    # ASKED OF THE SWITCHER ITSELF. The first cut looked for
    # `planner-view-bar` and `addEventListener` anywhere in the file
    # and refused the round over PF-2's picker handler, which has
    # nothing to do with this control. A page having JavaScript and
    # THIS BAR having JavaScript are different facts.
    # BOUNDED BY WHAT COMES AFTER IT, not by a count of close tags.
    # The bar sits between the action buttons and .calendar-layout; a
    # slice that ran past it took in the whole page and refused this
    # round over the Copy Week menu's onclick.
    # SLICED ON THE CLASS ATTRIBUTE, not on the bare name. This round
    # writes `planner-view-bar` TWICE - once as a CSS selector near
    # the top of the file and once as the element near the bottom -
    # and a slice from the first occurrence ran through the whole
    # action bar, refusing the round over the Copy Week menu.
    bar = markup.split('class="planner-view-bar"', 1)[-1] \
                .split('calendar-layout', 1)[0]
    for dead in ('onclick=', 'data-toggle=', '<button'):
        if dead in bar:
            refuse('%s: the switcher carries %r. The view is in the '
                   'URL; a control that needs JavaScript cannot be '
                   'linked to and does not survive a refresh.'
                   % (TPL, dead))
    js = T.code_only_js(nt)
    if re.search(r'planner-view-bar["\']\s*\)', js):
        refuse('%s: JavaScript reaches for the view bar' % TPL)
    # EVERY ADDRESS THIS PAGE BUILDS CARRIES THE VIEW. The switcher
    # is not the only navigation on the screen, and a view that only
    # survives its own control is not in the URL.
    for fn in ('goWeek', 'goMonth', 'goDay'):
        body_js = js.split('function %s(' % fn)[-1].split('\nfunction ')[0]
        if 'plannerUrl(' not in body_js and "p.set('view'" not in body_js:
            refuse('%s: %s() builds an address without the view, so '
                   'pressing it drops you back to Month' % (TPL, fn))
    if markup.count('<a href="?view=') != 3:
        refuse('%s: the three views are not three links' % TPL)

    # TEMPLATE TAGS BALANCE.
    for a, b in (('{%', '%}'), ('{{', '}}'), ('{#', '#}')):
        if (nt.count(a) - t_before.count(a)
                != nt.count(b) - t_before.count(b)):
            refuse('%s: this round added %d %s and %d %s'
                   % (TPL, nt.count(a) - t_before.count(a), a,
                      nt.count(b) - t_before.count(b), b))
    o, c = nt.count('/*'), nt.count('*/')
    if o != c:
        refuse('%s: %d /* against %d */' % (TPL, o, c))
    for tag in ('<div', '</div>'):
        d = nt.count(tag) - t_before.count(tag)
        if d != 2:
            refuse('%s: this round opened %d %s, expected 2 - the bar '
                   'and the seg' % (TPL, d, tag))

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('MV-1 --check')
        print('  views      : %s, landing on month' % ', '.join(VIEWS))
        print('  anchor     : ?date=, then ?week=, then today')
        print('  switcher   : %d link(s), each carrying the anchor'
              % len(links))
        print('  files      : %d' % len(out))
        for q in sorted(out):
            print('    %s' % os.path.relpath(q, root))
        print('--check: nothing written.')
        return 0

    for q, val in sorted(out.items()):
        backup(q)
        write(q, val)
        print('  wrote %s' % os.path.relpath(q, root))
    print('MV-1  %d file(s) written, backups end %s' % (len(out), SUFFIX))
    print('Now run:  python test_view_switch.py')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
