# -*- coding: utf-8 -*-
"""apply_week_cols.py - round MV-3, 19 Oct 2026.

RELEASE 4, PUSH 1. THE WEEK IS SEVEN COLUMNS.

Demetri, testing the live planner: "This daily list is not required..."

THE MEASUREMENT HE WAS REACTING TO. One week of day cards is about
4,900px tall. Sunday is four screens below Monday, and the number of
days you can see at once is ZERO - on a page whose whole job is
showing you the week. Seven columns is about 420px.

WHAT A COLUMN HOLDS. A day header, the meals as chips, and a + at the
foot. No servings stepper and no row actions: a column is 152px at
1200px and the stepper alone is 90px of it. Those live in the Day
view, which MV-4 builds, and the chip menu RD-1 adds in the second
push of this release.

THE PHONE CANNOT HAVE SEVEN COLUMNS. 358px of usable width divided by
seven is 51px - the same wall the Month hit, and Month answers it with
dots. Week cannot: it is the view you use standing in the kitchen, and
a dot does not tell you what is for dinner.

So the phone gets a DAY STRIP - Demetri's answer to Question A. The
week's shape stays across the top, seven small buttons with a mark per
meal, and the selected day opens in full underneath. You can still see
that Saturday is busy; you can also read what is on it.

WHICH DAY IS SELECTED. The anchor, when the anchor is in this week -
so arriving from Month on the 22nd shows the 22nd - and the Monday
otherwise. One rule, in the view, where the anchor already lives.

Idempotent. Every file backed up to .bak_weekcols.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_weekcols'
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_week_cols.py'
PATCHER = 'apply_week_cols.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'MV-3, 19 Oct 2026'
CHECK = False


# ============================================================== THE VIEW
SEL_WAS = """    week_days = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        week_days.append({
            'date': d,
            'day_name': d.strftime('%A'),
            'day_short': d.strftime('%a'),
            'day_num': d.day,
            'is_today': d == today,
            'entries': by_date.get(d, []),
        })
"""
SEL_NOW = """    # WHICH DAY THE PHONE OPENS ON - MV-3, 19 Oct 2026.
    #
    # Seven columns is 51px on a phone, so the week there is a day
    # strip with ONE day open underneath it - Demetri's answer to
    # Question A. Something has to be that day.
    #
    # THE ANCHOR, WHEN IT IS IN THIS WEEK. Arriving from the Month on
    # the 22nd should open the 22nd, not the Monday; and ?week= alone
    # names a week and not a day, so the Monday is right then.
    sel_date = anchor if week_start <= anchor <= week_end else week_start

    week_days = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        mine = by_date.get(d, [])
        week_days.append({
            'date': d,
            'day_name': d.strftime('%A'),
            'day_short': d.strftime('%a'),
            # TWO LETTERS FOR THE STRIP. %a is three - Mon, Tue - and
            # seven of those at 51px is wider than the strip.
            'day_two': d.strftime('%a')[:2],
            'day_num': d.day,
            'is_today': d == today,
            'is_selected': d == sel_date,
            'entries': mine,
            'count': len(mine),
            # ONE MARK PER MEAL, carrying what it is, capped at four
            # the way the month's are - a fifth wraps a 51px button.
            'dots': ['is-note' if not e.recipe_id
                     else 'is-leftover' if e.leftover_of_id
                     else '' for e in mine[:4]],
        })
"""

CTX_WAS = """        'week_days': week_days,"""
CTX_NOW = """        'week_days': week_days,
        # MV-3, 19 Oct 2026 - the day the phone's strip opens on.
        'sel_date': sel_date,"""


# ============================================================ THE MARKUP
GRID_WAS = """                <div id="plannerStatus" class="planner-status" role="status" aria-live="polite"></div>

                {% for day in week_days %}"""
GRID_NOW = """                <div id="plannerStatus" class="planner-status" role="status" aria-live="polite"></div>

                {# ------------------------------- SEVEN COLUMNS - MV-3 #}
                {#                                                      #}
                {# Demetri: "This daily list is not required..."        #}
                {#                                                      #}
                {# MEASURED: one week of the day cards below is about   #}
                {# 4,900px tall, so Sunday is four screens under Monday #}
                {# and the number of days you can see at once is ZERO.  #}
                {# Seven columns is about 420px.                        #}
                {#                                                      #}
                {# NO STEPPER AND NO ROW ACTIONS HERE. A column is      #}
                {# 152px at 1200px and the stepper alone is 90px of it. #}
                {# They live in the Day view, which MV-4 builds.        #}
                {% if view_mode == 'week' %}
                <div class="week-grid">
                    {% for day in week_days %}
                    <div class="week-col{% if day.is_today %} is-today{% endif %}">
                        <div class="week-col-head">
                            <span class="week-col-dow">{{ day.day_short }}</span>
                            <span class="week-col-num">{{ day.day_num }}</span>
                        </div>
                        <div class="week-col-body">
                            {% for e in day.entries %}
                            <span class="week-chip{% if e.leftover_of_id %} is-leftover{% elif not e.recipe_id %} is-note{% endif %}">{% if e.recipe_id %}{{ e.recipe.recipe_name }}{% else %}{{ e.note }}{% endif %}</span>
                            {% empty %}
                            <span class="week-col-empty">&mdash;</span>
                            {% endfor %}
                        </div>
                        {% if perms.auth.can_edit_recipes %}
                        <div class="week-col-foot">
                            <button type="button" class="week-col-add"
                                    onclick="openPicker('{{ day.date|date:'Y-m-d'|escapejs }}', '{{ day.day_name|escapejs }} {{ day.day_num }}')"
                                    aria-label="Add a meal to {{ day.day_name }} {{ day.day_num }}">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>

                {# --------------------------- AND THE PHONE'S STRIP - MV-3 #}
                {#                                                          #}
                {# 358px over seven columns is 51px, which is the wall the  #}
                {# Month hit and answered with dots. Week cannot: it is the #}
                {# view you use standing in the kitchen and a dot does not  #}
                {# say what is for dinner.                                  #}
                {#                                                          #}
                {# So the week's SHAPE stays across the top - you can still #}
                {# see that Saturday is busy - and one day opens in full    #}
                {# underneath, which is the day-card list below, narrowed   #}
                {# by MV-4 to the selected day.                             #}
                <div class="day-strip" role="group" aria-label="The week">
                    {% for day in week_days %}
                    <button type="button"
                            class="day-strip-btn{% if day.is_selected %} is-selected{% endif %}{% if day.is_today %} is-today{% endif %}"
                            onclick="goDay('{{ day.date|date:'Y-m-d'|escapejs }}', 'week')"
                            {% if day.is_selected %}aria-current="date"{% endif %}
                            aria-label="{{ day.day_name }} {{ day.day_num }}, {{ day.count }} meal{{ day.count|pluralize }}">
                        <span class="day-strip-dow">{{ day.day_two }}</span>
                        <span class="day-strip-num">{{ day.day_num }}</span>
                        <span class="day-strip-dots" aria-hidden="true">{% for d in day.dots %}<span class="day-strip-dot {{ d }}"></span>{% endfor %}</span>
                    </button>
                    {% endfor %}
                </div>
                {% endif %}

                {% for day in week_days %}"""


# =============================================================== THE CSS
CSS_WAS = """/* ==================== THE MONTH ==================== */"""
CSS_NOW = """/* ==================== THE WEEK ==================== */
/* SEVEN COLUMNS - MV-3, 19 Oct 2026. The day cards below this are
   about 4,900px for one week; this is about 420px, and the whole
   point of a planner is seeing the week at once.

   The same grid shape as the month, for the same reason: one grid,
   one child per column, and no row wrapper for a display:contents
   rule to hand its children to. MC-4 is why that sentence exists. */
.week-grid {
    display: grid;
    grid-template-columns: repeat(7, minmax(0, 1fr));
    gap: 1px;
    background: var(--alv-line-soft);
    border: 1px solid var(--alv-line);
    border-radius: var(--alv-radius-sm);
    overflow: hidden;
    margin-bottom: 16px;
}

.week-col {
    background: var(--alv-paper);
    display: flex;
    flex-direction: column;
    min-height: 190px;
}

.week-col-head {
    background: var(--alv-surface);
    border-bottom: 1px solid var(--alv-line);
    padding: 6px 4px;
    text-align: center;
}

.week-col.is-today .week-col-head {
    background: var(--alv-accent-soft);
}

/* --alv-ink-soft, NOT --alv-ink-faint. The faint token reads 2.85:1
   on this ground and AA wants 4.5; ink-soft reads 5.25. A weekday
   heading is a WORD somebody reads, not a mark. test_pair_contrast
   caught the month's copy of exactly this on the first sweep after
   the round was written. */
.week-col-dow {
    display: block;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--alv-ink-soft);
}

.week-col-num {
    font-size: 15px;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    color: var(--alv-ink);
}

.week-col.is-today .week-col-num {
    color: var(--alv-accent-ink);
}

.week-col-body {
    flex: 1;
    padding: 5px 4px;
    display: flex;
    flex-direction: column;
    gap: 2px;
}

/* THE SAME CHIP THE MONTH DRAWS, in the same three colours, because a
   meal should not change its appearance when you change zoom level. */
.week-chip {
    display: block;
    font-size: 11px;
    line-height: 1.35;
    padding: 2px 5px;
    border-radius: 3px;
    border-left: 2px solid var(--alv-accent);
    background: var(--alv-accent-soft);
    color: var(--alv-accent-ink);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.week-chip.is-note {
    background: var(--alv-warn-soft);
    color: var(--alv-warn-ink);
    border-left-color: var(--alv-warn);
}

.week-chip.is-leftover {
    background: var(--alv-surface-deep);
    color: var(--alv-ink-soft);
    border-left-color: var(--alv-neutral);
}

/* AN EMPTY DAY SAYS SO. A blank column and a broken column look the
   same, which is the fault PK-1's empty state exists for. */
.week-col-empty {
    color: var(--alv-ink-faint);
    font-size: 12px;
    text-align: center;
    padding: 6px 0;
}

.week-col-foot {
    padding: 0 4px 6px;
}

.week-col-add {
    width: 100%;
    border: 1px dashed var(--alv-line);
    background: none;
    border-radius: 4px;
    color: var(--alv-ink-faint);
    font-size: 13px;
    line-height: 1;
    padding: 6px 0;
}

.week-col-add:hover {
    background: var(--alv-surface);
    color: var(--alv-accent);
    border-color: var(--alv-accent-line);
}

.week-col-add:focus-visible {
    outline: 2px solid var(--alv-accent);
    outline-offset: 1px;
}

/* ---- THE DAY STRIP, which is the WEEK on a phone - MV-3.

   358px over seven columns is 51px. The Month answers that with dots
   because a month at a glance is about shape; the Week cannot,
   because it is the view you use standing in the kitchen. So the
   shape stays across the top and one day opens in full below it.

   Hidden above 768px, where the seven columns say all of it. */
.day-strip {
    display: none;
}

@media screen and (max-width: 767px) {
    .week-grid {
        display: none;
    }

    .day-strip {
        display: grid;
        grid-template-columns: repeat(7, minmax(0, 1fr));
        gap: 3px;
        margin-bottom: 12px;
    }

    .day-strip-btn {
        border: 1px solid var(--alv-line);
        border-radius: 5px;
        background: var(--alv-paper);
        padding: 4px 0 3px;
        /* 44px, THE HOUSE RULE, and this is the control the week is
           navigated with on a phone. */
        min-height: 44px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 1px;
    }

    .day-strip-btn.is-selected {
        background: var(--alv-accent);
        border-color: var(--alv-accent);
    }

    .day-strip-dow {
        font-size: 8.5px;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        /* ink-soft, for the reason .week-col-dow gives above. */
        color: var(--alv-ink-soft);
    }

    .day-strip-num {
        font-size: 12px;
        font-weight: 600;
        font-variant-numeric: tabular-nums;
        color: var(--alv-ink);
    }

    .day-strip-btn.is-today .day-strip-num {
        color: var(--alv-accent-ink);
    }

    .day-strip-btn.is-selected .day-strip-dow,
    .day-strip-btn.is-selected .day-strip-num {
        color: var(--alv-on-accent);
    }

    .day-strip-dots {
        display: flex;
        gap: 2px;
        min-height: 5px;
    }

    .day-strip-dot {
        width: 4px;
        height: 4px;
        border-radius: 50%;
        background: var(--alv-accent);
    }

    .day-strip-dot.is-note {
        background: var(--alv-warn);
    }

    .day-strip-dot.is-leftover {
        background: var(--alv-neutral);
    }

    .day-strip-btn.is-selected .day-strip-dot {
        background: var(--alv-on-accent);
    }
}

/* ==================== THE MONTH ==================== */"""


# ====================================================== THE SENTINEL ROWS
SENT_WAS = """    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'THREE SHOWN, THE REST COUNTED'; What = 'MV-2: a cell shows three names then +n more - his own answer to what a full day looks like' },"""
SENT_NOW = """    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'THREE SHOWN, THE REST COUNTED'; What = 'MV-2: a cell shows three names then +n more - his own answer to what a full day looks like' },
    # ------------------------------------------------- MV-3, 19 Oct 2026
    @{ File = 'pages/templates/meal_planner.html'; Text = 'class="week-grid"'; What = 'MV-3: the week is seven columns - 4,900px of day cards becomes about 420px, after Demetri said the daily list was not required' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'class="day-strip"'; What = 'MV-3: and on a phone the week is a day strip with one day open, because seven columns is 51px there' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'WHICH DAY THE PHONE OPENS ON'; What = 'MV-3: the anchor when it is in this week, the Monday otherwise - one rule, where the anchor already lives' },"""

SUITE_WAS = """    'test_month_view.py'
)"""
SUITE_NOW = """    'test_month_view.py',
    # MV-3, 19 Oct 2026 - the week as seven columns. It RENDERS
    # the week and measures its height, because "the daily list
    # is not required" was a complaint about 4,900px and a
    # number is the only answer to it.
    'test_week_cols.py'
)"""

TREE_WAS = """    'test_month_view.py',
]"""
TREE_NOW = """    'test_month_view.py',
    # MV-3, 19 Oct 2026 - seven columns at full size, a day strip on a
    # phone. Section 3 measures the page height both ways, which is
    # the claim Demetri actually made.
    'test_week_cols.py',
]"""

RD_WAS = """    '.bak_monthview',
]"""
RD_NOW = """    '.bak_monthview',
    # MV-3, 19 Oct 2026 - the week is seven columns. "This daily list
    # is not required": one week of day cards is about 4,900px, so
    # Sunday is four screens below Monday and you can see no days at
    # once. On a phone it is a day strip with one day open, which is
    # his own answer to the question.
    '.bak_weekcols',
]"""

WD_WAS = """CONVERTED_N = 116   # MV-2, 19 Oct 2026"""
WD_NOW = """CONVERTED_N = 117   # MV-3, 19 Oct 2026 - this round own suite   # (was 116)   # MV-2, 19 Oct 2026"""


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
    raise SystemExit('MV-3 REFUSED: %s' % msg)


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



# ================================================ ONE TREE-WIDE RE-PIN
# N_OTHER COUNTS NON-BORDER USES OF THE PANEL-WASH TOKEN across the
# live corpus - backgrounds, gradient stops and custom properties -
# and this round adds one:
#
#   .week-chip.is-leftover  background: var(--alv-surface-deep)
#
# 93 -> 94. A RE-PIN AND NOT A REPAIR. A leftover should be the
# quietest thing in a column, and --alv-surface-deep is the house
# token for exactly that wash - MV-2's .month-chip.is-leftover takes
# it for the same reason an hour earlier, and the month and the week
# must not teach two vocabularies for one meal.
#
# MV-2 ADDED NONE, which is worth saying because it looks like it
# should have: its month chip gained a use and the mini-calendar CSS
# it deleted lost one, so the count did not move. This round has
# nothing to delete, so its one shows.
SB = 'test_surface_border.py'
# AND THE PAIR CENSUS. The week grid adds four rules that set both a
# ground and an ink: .week-col-head (with its is-today variant),
# .week-chip and .day-strip-btn.is-selected. 702 -> 706, measured with
# this round applied and MV-2 before it.
#
# A RE-PIN AND NOT A REPAIR: all four are house pairs off base's own
# tokens and the AA table below the count is untouched. The two rules
# in this round that DID read below AA - .week-col-dow and
# .day-strip-dow at 2.85:1, both weekday headings, both words somebody
# reads - were moved to --alv-ink-soft at 5.25:1 rather than pinned.
PAIR = 'test_pair_contrast.py'
PAIR_WAS = """EXPECT_PAIRS = 702   # MV-2, 19 Oct 2026"""
PAIR_NOW = """EXPECT_PAIRS = 706   # MV-3, 19 Oct 2026 - the week grid adds four rules that set both a ground and an ink, all house pairs off base tokens, so the AA table below is untouched. The two weekday headings that read 2.85:1 were REPAIRED to ink-soft, not pinned.   # (was 702)   # MV-2, 19 Oct 2026"""

SB_WAS = """N_CONVERT, N_PAGES, N_FALLBACK, N_OTHER = 78, 43, 3, 93"""
SB_NOW = """# MV-3, 19 Oct 2026 - N_OTHER was 93. The week column's leftover chip
# takes the panel-wash as its background, which is what a leftover
# should look like and is the token MV-2's month chip already uses for
# it. One more non-border use in the live corpus; F2a still settled
# the 96 it settled.
N_CONVERT, N_PAGES, N_FALLBACK, N_OTHER = 78, 43, 3, 94"""

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
    if 'week-grid' in t:
        print('MV-3  already applied - the week is seven columns.')
        return 0

    # ---------------------------------------------------------------- 1
    sys.path.insert(0, root)
    import alv_tree as T
    if 'month_weeks' not in T.python_code_only(v, payloads=True):
        refuse('%s has no month_weeks - MV-2 has not been applied, and '
               'this round sits beside the month it built' % VIEW)
    if 'day-card' not in T.code_only(t):
        refuse('%s has no day cards, so there is no 4,900px to replace'
               % TPL)

    # ---------------------------------------------------------------- 2
    v = swap(v, SEL_WAS, SEL_NOW, '%s (the selected day)' % VIEW)
    v = swap(v, CTX_WAS, CTX_NOW, '%s (the context)' % VIEW)
    out[pv] = v

    t = swap(t, GRID_WAS, GRID_NOW, '%s (the week grid)' % TPL)
    t = swap(t, CSS_WAS, CSS_NOW, '%s (the week CSS)' % TPL)
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

    # ---------------------------------------------------------- 3b
    psb = os.path.join(root, SB)
    out[psb] = swap(read(psb), SB_WAS, SB_NOW, '%s (N_OTHER)' % SB)

    ppc = os.path.join(root, PAIR)
    out[ppc] = swap(read(ppc), PAIR_WAS, PAIR_NOW,
                    '%s (EXPECT_PAIRS)' % PAIR)

    # ---------------------------------------------------------------- 4
    for k, val in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.relpath(k, root), e.lineno, e.msg))

    nt = out[pt]
    markup = T.code_only(nt)
    nv = T.python_code_only(out[pv], payloads=True)

    # SEVEN COLUMNS, ONE GRID, NO ROW WRAPPER - MC-4's lesson, applied
    # to the second grid this release builds.
    if 'grid-template-columns: repeat(7, minmax(0, 1fr));' not in markup:
        refuse('%s: the week is not a seven column grid' % TPL)
    if re.search(r'display:\s*contents', markup):
        refuse('%s: something carries display:contents. MC-4 is the '
               'round where that handed thirty-five cells to a plain '
               'div.' % TPL)

    # NO STEPPER IN A COLUMN. 152px does not hold one, and a control
    # that is there but unusable is worse than one that is not.
    g = markup.find('class="week-grid"')
    gend = markup.find('class="day-strip"', g)
    grid = markup[g:gend] if gend > g else markup[g:g + 4000]
    for dead in ('servings-step', 'stepServings', 'action-more',
                 'row-action'):
        if dead in grid:
            refuse('%s: the week column carries %r - a column is 152px '
                   'and the stepper alone is 90px of it. Those belong '
                   'to the Day view.' % (TPL, dead))

    # THE PHONE GETS THE STRIP AND NOT THE COLUMNS.
    if '.day-strip {\n    display: none;\n}' not in markup:
        refuse('%s: the day strip is not hidden at full size' % TPL)
    phone = markup.split('@media screen and (max-width: 767px)')
    if not any('.week-grid {' in p and 'display: none;' in
               p.split('.week-grid {')[1].split('}')[0]
               for p in phone[1:]):
        refuse('%s: the seven columns are not hidden on a phone, where '
               'each would be 51px' % TPL)

    # ONE RULE DECIDES THE SELECTED DAY, and it is in the view.
    if 'sel_date = anchor if week_start <= anchor <= week_end' not in nv:
        refuse('%s: the selected day is not the anchor-in-week rule'
               % VIEW)
    if markup.count('aria-current="date"') != 1:
        refuse('%s: the strip marks %d selected days, expected 1'
               % (TPL, markup.count('aria-current="date"')))

    # EVERY onclick NAMES A FUNCTION THIS PAGE DEFINES.
    js = T.code_only_js(nt)
    for fn in sorted(set(re.findall(r'onclick="(\w+)\(', markup))):
        if ('function %s(' % fn) not in js:
            refuse('%s: onclick calls %s() and this page does not '
                   'define it' % (TPL, fn))

    for a, b in (('{%', '%}'), ('{{', '}}'), ('{#', '#}')):
        da = nt.count(a) - t_before.count(a)
        db = nt.count(b) - t_before.count(b)
        if da != db:
            refuse('%s: this round added %d %s and %d %s'
                   % (TPL, da, a, db, b))
    o, c = nt.count('/*'), nt.count('*/')
    if o != c:
        refuse('%s: %d /* against %d */' % (TPL, o, c))
    if nt.count('{') - nt.count('}') != t_before.count('{') \
            - t_before.count('}'):
        refuse('%s: the braces do not balance as they did' % TPL)

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('MV-3 --check')
        print('  week       : 7 columns, no stepper, no row actions')
        print('  phone      : the day strip, one day open underneath')
        print('  selected   : the anchor when it is in this week, else '
              'the Monday')
        print('  files      : %d' % len(out))
        for q in sorted(out):
            print('    %s' % os.path.relpath(q, root))
        print('--check: nothing written.')
        return 0

    for q, val in sorted(out.items()):
        backup(q)
        write(q, val)
        print('  wrote %s' % os.path.relpath(q, root))
    print('MV-3  %d file(s) written, backups end %s' % (len(out), SUFFIX))
    print('Now run:  python test_week_cols.py')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
