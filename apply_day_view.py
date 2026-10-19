# -*- coding: utf-8 -*-
"""apply_day_view.py - round MV-4, 19 Oct 2026.

RELEASE 4, PUSH 1. ONE DAY, IN FULL - AND THE LIST OF SEVEN GOES.

Demetri, testing the live planner: "This daily list is not required..."

MV-3 built the week as seven columns. This is the round that actually
DELETES the vertical list of seven day cards he was talking about - by
narrowing it to one.

AND KEEPING THE CARD ITSELF, which is the decision worth writing down.
That card is 15,000 characters of real work: the servings stepper that
saves on press, MO-1's note row, MO-1's leftover row with the date it
was cooked on and no stepper because a leftover buys nothing, the Add
Recipe and Add Note buttons, and the row actions. None of that is
wrong. What was wrong was SEVEN of them stacked into 4,900px.

So the loop keeps its body and loses its length. For ONE day the card
is exactly the right shape - it is the only view with room for
servings, a photo and a cooked-on date - and the Day view is where
those live now that a week column is 146px and a month cell is 152px.

WHERE IT SHOWS

    Day       always. With its own nav: the day before, the day
              after, Today.
    Week      on a PHONE only, under the day strip MV-3 built - which
              is Demetri's answer to Question A: the week's shape
              across the top, one day open underneath.
    Month     never. MV-2 already gates the whole panel.

WHICH DAY. sel_date, which MV-3 defined once: the anchor when the
anchor is in this week, the Monday otherwise. There is no second rule
here, because a second rule is how two parts of a page come to
disagree about what day it is.

Idempotent. Every file backed up to .bak_dayview.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_dayview'
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_day_view.py'
PATCHER = 'apply_day_view.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'MV-4, 19 Oct 2026'
CHECK = False


# ============================================================== THE VIEW
CTX_WAS = """        # MV-3, 19 Oct 2026 - the day the phone's strip opens on.
        'sel_date': sel_date,"""
CTX_NOW = """        # MV-3, 19 Oct 2026 - the day the phone's strip opens on.
        'sel_date': sel_date,
        # MV-4, 19 Oct 2026 - and the two days either side of it, for
        # the Day view's own nav. Computed here rather than in the
        # template because a template cannot do arithmetic on a date,
        # and because `anchor` already lives here.
        'prev_day': sel_date - timedelta(days=1),
        'next_day': sel_date + timedelta(days=1),
        'sel_count': len(by_date.get(sel_date, [])),"""


# ============================================================ THE MARKUP
# THE HEADER. The week nav is right for the Week and says nothing
# useful in the Day - "19 Oct - 25 Oct" above one Tuesday is a label
# about the wrong thing.
HEAD_WAS = """            <div class="week-detail-header">
                <div class="week-nav">"""
HEAD_NOW = """            <div class="week-detail-header">
                {# THE DAY HAS ITS OWN NAV - MV-4, 19 Oct 2026.        #}
                {# "19 Oct - 25 Oct 2026" above a single Tuesday is a  #}
                {# label about the wrong thing, and the week arrows    #}
                {# would move you seven days when you can see one.     #}
                {% if view_mode == 'day' %}
                <div class="week-nav">
                    <button type="button" class="week-nav-btn"
                            onclick="goDay('{{ prev_day|date:'Y-m-d'|escapejs }}')"
                            aria-label="The day before">
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    <span class="week-title">{{ sel_date|date:"l j M Y" }}</span>
                    <button type="button" class="week-nav-btn"
                            onclick="goDay('{{ next_day|date:'Y-m-d'|escapejs }}')"
                            aria-label="The day after">
                        <i class="fas fa-chevron-right"></i>
                    </button>
                    <button type="button" class="week-nav-btn"
                            onclick="goDay('{{ today|date:'Y-m-d'|escapejs }}')">
                        Today
                    </button>
                </div>
                <span class="week-meta">{{ sel_count }} meal{{ sel_count|pluralize }}</span>
                {% else %}
                <div class="week-nav">"""

HEADEND_WAS = """                <span class="week-meta">{{ meal_count }} meal{{ meal_count|pluralize }}</span>
            </div>"""
HEADEND_NOW = """                <span class="week-meta">{{ meal_count }} meal{{ meal_count|pluralize }}</span>
                {% endif %}{# view_mode == 'day' - MV-4, 19 Oct 2026 #}
            </div>"""

# THE LIST OF SEVEN BECOMES ONE.
LOOP_WAS = """                {% for day in week_days %}
                <div class="day-card">"""
LOOP_NOW = """                {# ONE DAY, NOT SEVEN - MV-4, 19 Oct 2026.             #}
                {#                                                      #}
                {# Demetri: "This daily list is not required..." Seven  #}
                {# of these cards is about 4,900px, so Sunday is four   #}
                {# screens below Monday. MV-3 replaced the SEEING of a  #}
                {# week with seven columns; this is where the list      #}
                {# itself goes.                                         #}
                {#                                                      #}
                {# THE CARD STAYS. It holds the servings stepper that   #}
                {# saves on press, MO-1's note and leftover rows, and   #}
                {# the Add controls - none of which fits in a 146px     #}
                {# column or a 152px cell. For ONE day it is exactly    #}
                {# right, and this is the only view with room for it.   #}
                {#                                                      #}
                {# ON A PHONE IN WEEK VIEW it sits under MV-3's day     #}
                {# strip, which is his own answer to Question A. The    #}
                {# stylesheet hides it in Week above 768px, where the   #}
                {# seven columns say all of it.                         #}
                <div class="day-detail{% if view_mode == 'week' %} in-week{% endif %}">
                {% for day in week_days %}{% if day.is_selected %}
                <div class="day-card">"""

ENDLOOP_WAS = """                {% endfor %}
            </div>
        </div>
        {% endif %}{# view_mode != 'month' - MV-2, 19 Oct 2026 #}"""
ENDLOOP_NOW = """                {% endif %}{% endfor %}
                </div>{# .day-detail - MV-4, 19 Oct 2026 #}
            </div>
        </div>
        {% endif %}{# view_mode != 'month' - MV-2, 19 Oct 2026 #}"""


# =============================================================== THE CSS
CSS_WAS = """/* ==================== THE WEEK ==================== */"""
CSS_NOW = """/* ==================== THE DAY ==================== */
/* MV-4, 19 Oct 2026. The card below is unchanged and that is the
   point: it carries the servings stepper, MO-1's note and leftover
   rows and the Add controls, none of which fits in a 146px week
   column or a 152px month cell. What changed is that there is ONE of
   it instead of seven.

   IN WEEK VIEW IT IS FOR THE PHONE ONLY. Above 768px the seven
   columns say everything a week has to say, and a day card under them
   would be a second answer to the same question. Below it, the
   columns are hidden and this is what the day strip opens. */
@media (min-width: 768px) {
    .day-detail.in-week {
        display: none;
    }
}

/* ==================== THE WEEK ==================== */"""


# ====================================================== THE SENTINEL ROWS
SENT_WAS = """    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'WHICH DAY THE PHONE OPENS ON'; What = 'MV-3: the anchor when it is in this week, the Monday otherwise - one rule, where the anchor already lives' },"""
SENT_NOW = """    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'WHICH DAY THE PHONE OPENS ON'; What = 'MV-3: the anchor when it is in this week, the Monday otherwise - one rule, where the anchor already lives' },
    # ------------------------------------------------- MV-4, 19 Oct 2026
    @{ File = 'pages/templates/meal_planner.html'; Text = 'ONE DAY, NOT SEVEN'; What = 'MV-4: the vertical list of seven day cards is gone - about 4,900px of it - which is what Demetri meant by the daily list not being required' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'THE DAY HAS ITS OWN NAV'; What = 'MV-4: and the Day view moves by days, because week arrows above one Tuesday move you seven' },"""

SUITE_WAS = """    'test_week_cols.py'
)"""
SUITE_NOW = """    'test_week_cols.py',
    # MV-4, 19 Oct 2026 - one day in full. It counts the cards a
    # page draws in each of the three views, because "not
    # required" was a claim about how many there were.
    'test_day_view.py'
)"""

TREE_WAS = """    'test_week_cols.py',
]"""
TREE_NOW = """    'test_week_cols.py',
    # MV-4, 19 Oct 2026 - one day card instead of seven, and the Day
    # view's own nav. Section 3 renders all three views and counts.
    'test_day_view.py',
]"""

RD_WAS = """    '.bak_weekcols',
]"""
RD_NOW = """    '.bak_weekcols',
    # MV-4, 19 Oct 2026 - one day, in full, and the list of seven is
    # gone. The CARD is kept: the stepper, MO-1's note and leftover
    # rows and the Add controls do not fit in a 146px column or a
    # 152px cell, and for one day the card is exactly right.
    '.bak_dayview',
]"""

WD_WAS = """CONVERTED_N = 117   # MV-3, 19 Oct 2026 - this round own suite"""
WD_NOW = """CONVERTED_N = 118   # MV-4, 19 Oct 2026 - this round own suite   # (was 117)   # MV-3, 19 Oct 2026 - this round own suite"""


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
    raise SystemExit('MV-4 REFUSED: %s' % msg)


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



# ============================== TWO REPAIRS THIS ROUND CAUSED
#
# BOTH ARE THE SAME SHAPE: a check that counted something across
# SEVEN day cards, on a page that now draws one.
#
# MO-1 seeded six leftovers and six notes across six days and counted
# them on one request. Its claims are about what a day card's rows
# LOOK LIKE - a leftover wears its pill and names the day the pot was
# cooked on, a note has no stepper, each day has an Add Note - and
# every one of them is still true. They were just asked of a page
# that used to show the whole week at once.
#
# SO THEY ARE ASKED OF EACH DAY, IN THE DAY VIEW. Seven requests
# instead of one, summed - which is the same question about the same
# markup, and the only honest way to ask it now.
MO = 'test_meal_day.py'

MO_WAS = """    body = r.content.decode('utf-8', 'replace')
    ok(body.count('leftover-item') >= 6,
       'six leftover rows are drawn as leftover rows',
       body.count('leftover-item'))
    ok(body.count('note-item') >= 6, '  and six note rows as note rows',
       body.count('note-item'))"""
MO_NOW = """    # SEVEN DAYS, SEVEN REQUESTS - repaired by MV-4, 19 Oct 2026.
    #
    # This read ONE page and counted six leftover rows on it, because
    # the planner drew all seven day cards at once. MV-4 narrowed that
    # to the selected day, so one page now holds one card.
    #
    # THE CLAIM IS UNCHANGED and so is the markup it is about: a
    # leftover row wears its pill and names the day the pot was cooked
    # on, a note row has no stepper, every day has an Add Note. Those
    # are facts about a CARD. Asking each day for its own card is the
    # same question - and a re-pin to `>= 1` would have been a smaller
    # claim pretending to be the same one.
    DAYS = [MON + _dt.timedelta(days=i) for i in range(7)]
    bodies = [cl.get('/meal_plans/planner/?view=day&date='
                     + d.strftime('%Y-%m-%d'))
              .content.decode('utf-8', 'replace') for d in DAYS]
    body = ''.join(bodies)
    ok(body.count('leftover-item') >= 6,
       'six leftover rows are drawn as leftover rows, across the six '
       'days that have one', body.count('leftover-item'))
    ok(body.count('note-item') >= 6, '  and six note rows as note rows',
       body.count('note-item'))
    # COUNTED ON THE ATTRIBUTE, not on the name: `.day-card-header`
    # is also a CSS selector on every one of these pages, so counting
    # the bare name found two per day and the claim read as false.
    ok(len(bodies) == 7 and max(b.count('class="day-card-header"')
                                for b in bodies) == 1,
       '  and no single day draws more than one card - which is the '
       'whole of what MV-4 changed',
       [b.count('class="day-card-header"') for b in bodies])"""

MO_STEP_WAS = """    ok(body.count('class="servings-step"') == 1,
       'exactly ONE servings stepper on a week of thirteen rows - the '"""
MO_STEP_NOW = """    ok(body.count('class="servings-step"') == 1,
       'exactly ONE servings stepper across the week of thirteen rows - '"""

MO_NOTE_WAS = """    ok(body.count('onclick="openNote(') == 7,
       '  an Add Note control under each of the seven days',"""
MO_NOTE_NOW = """    ok(body.count('onclick="openNote(') == 7,
       '  an Add Note control on each of the seven days - one per '
       'page now, where it was seven on one page',"""

# AND MV-3'S OWN CLAIM, which this round made false an hour after it
# was written. It compared the week grid's height against the day
# cards' - and MV-4 hides those cards in Week above 768px, so the
# number it compared against is now zero and 192 < 0 is false.
#
# THE CLAIM WAS ALWAYS ABOUT THE 4,900px, not about what is on the
# page beside it. So it asks the fixed number it was always about.
MV3 = 'test_week_cols.py'
MV3_WAS = """                    ok(m['gridH'] < m['cardsH'],
                       '  %dpx against the %dpx the cards still take'
                       % (m['gridH'], round(m['cardsH'])), m)"""
MV3_NOW = """                    # AGAINST THE 4,900px, NOT AGAINST THE PAGE -
                    # repaired by MV-4, 19 Oct 2026. This compared the
                    # grid with the day cards still on the page, and
                    # MV-4 hides those in Week above 768px, so the
                    # number it compared against became zero an hour
                    # after it was written.
                    #
                    # The claim was never about what happens to be
                    # beside the grid. It is about the 4,900px of
                    # stacked cards the week used to be, which is a
                    # fixed measurement and cannot be hidden.
                    ok(m['gridH'] < 1000,
                       '  %dpx, against the ~4,900px one week of '
                       'stacked day cards measured' % m['gridH'], m)
                    ok(m['cardsH'] == 0,
                       '  and MV-4 draws no day card here at all - the '
                       'seven columns are the whole answer', m)"""


MO_WORDS_WAS = """    ok(body.count('Add Note') == 9,
       '  and the words appear nine times - seven days, the dialog '"""
MO_WORDS_NOW = """    # ASKED OF ONE PAGE - repaired by MV-4, 19 Oct 2026. `body` is
    # seven pages joined now, and three different things say these two
    # words on each of them, so the sum is twenty-one and says nothing.
    # The claim was always about what ONE page holds.
    ok(bodies[0].count('Add Note') == 3,
       '  and on any one page the words appear three times - its day, '"""

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
    if 'day-detail' in t:
        print('MV-4  already applied - one day, not seven.')
        return 0

    # ---------------------------------------------------------------- 1
    sys.path.insert(0, root)
    import alv_tree as T
    if 'sel_date' not in T.python_code_only(v, payloads=True):
        refuse('%s has no sel_date - MV-3 has not been applied, and '
               'this round shows the day MV-3 chooses' % VIEW)
    before_cards = T.code_only(t).count('class="day-card"')
    if before_cards != 1:
        refuse('%s draws %d day-card templates, expected 1 in a loop'
               % (TPL, before_cards))

    # ---------------------------------------------------------------- 2
    v = swap(v, CTX_WAS, CTX_NOW, '%s (the context)' % VIEW)
    out[pv] = v

    t = swap(t, HEAD_WAS, HEAD_NOW, '%s (the day nav)' % TPL)
    t = swap(t, HEADEND_WAS, HEADEND_NOW, '%s (the header closes)' % TPL)
    t = swap(t, LOOP_WAS, LOOP_NOW, '%s (one day, not seven)' % TPL)
    t = swap(t, ENDLOOP_WAS, ENDLOOP_NOW, '%s (the loop closes)' % TPL)
    t = swap(t, CSS_WAS, CSS_NOW, '%s (the day CSS)' % TPL)
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
    # THE TWO REPAIRS, carried by the round that caused them.
    pmo = os.path.join(root, MO)
    mo = read(pmo)
    mo = swap(mo, MO_WAS, MO_NOW, '%s (the week census)' % MO)
    mo = swap(mo, MO_STEP_WAS, MO_STEP_NOW, '%s (the stepper)' % MO)
    mo = swap(mo, MO_NOTE_WAS, MO_NOTE_NOW, '%s (the Add Note)' % MO)
    mo = swap(mo, MO_WORDS_WAS, MO_WORDS_NOW, '%s (the words)' % MO)
    out[pmo] = mo

    p3 = os.path.join(root, MV3)
    out[p3] = swap(read(p3), MV3_WAS, MV3_NOW,
                   '%s (the height comparison)' % MV3)

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

    # THE CARD IS UNCHANGED. This round shortens a loop; a round that
    # also edited the card would be two rounds wearing one name, and
    # the stepper that saves on press is not something to touch by
    # accident.
    def card_of(text):
        i = text.find('<div class="day-card">')
        return text[i:text.find('{% endif %}{% endfor %}', i)] \
            if i >= 0 else ''

    a = card_of(T.code_only(t_before).replace('{% endfor %}',
                                              '{% endif %}{% endfor %}'))
    b = card_of(markup)
    if not b:
        refuse('%s: the day card is gone. This round shortens the '
               'loop; it does not remove the card.' % TPL)
    for keep in ('servings-step', 'stepServings', 'add-recipe-btn',
                 'leftover-item', 'note-item'):
        if keep not in markup:
            refuse('%s: %r left with the loop. The card is what this '
                   'round KEEPS - it holds the stepper, the note row '
                   'and the leftover row, none of which fits anywhere '
                   'else.' % (TPL, keep))

    # ONE DAY. The loop still walks the week, and draws one of it.
    if '{% for day in week_days %}{% if day.is_selected %}' not in markup:
        refuse('%s: the card loop does not narrow to the selected day'
               % TPL)
    if 'sel_date' not in nv:
        refuse('%s: sel_date is gone' % VIEW)

    # THE DAY HAS ITS OWN NAV, and it moves by DAYS.
    # SLICED ON THE NAV, NOT ON THE FIRST `view_mode == 'day'`. MV-1's
    # switcher carries that same test on its own Day link, earlier in
    # the page, and the first cut of this gate measured THAT - found
    # no prev_day in it, and refused the round over the switcher.
    OPEN = ("{% if view_mode == 'day' %}\n"
            '                <div class="week-nav">')
    if OPEN.replace('\n', '\r\n') not in nt and OPEN not in nt:
        refuse('%s: the day nav is not gated to the day view' % TPL)
    nav = nt.replace('\r\n', '\n').split(OPEN, 1)[1] \
            .split('{% else %}', 1)[0]
    if 'goWeek(' in nav:
        refuse('%s: the Day view moves by WEEKS - its arrows would '
               'move you seven days when you can see one' % TPL)
    for want in ('prev_day', 'next_day'):
        if want not in nav:
            refuse('%s: the day nav has no %s' % (TPL, want))

    # IN WEEK VIEW IT IS FOR THE PHONE ONLY.
    if '.day-detail.in-week' not in markup:
        refuse('%s: the day card is not hidden in Week at full size - '
               'it would be a second answer to the question the seven '
               'columns already answer' % TPL)
    if '@media (min-width: 768px)' not in nt:
        refuse('%s: nothing decides that by screen size' % TPL)

    js = T.code_only_js(nt)
    for fn in sorted(set(re.findall(r'onclick="(\w+)\(', markup))):
        if ('function %s(' % fn) not in js:
            refuse('%s: onclick calls %s() and this page does not '
                   'define it' % (TPL, fn))

    for a2, b2 in (('{%', '%}'), ('{{', '}}'), ('{#', '#}')):
        da = nt.count(a2) - t_before.count(a2)
        db = nt.count(b2) - t_before.count(b2)
        if da != db:
            refuse('%s: this round added %d %s and %d %s'
                   % (TPL, da, a2, db, b2))
    o, c = nt.count('/*'), nt.count('*/')
    if o != c:
        refuse('%s: %d /* against %d */' % (TPL, o, c))
    for tag in ('<div', '</div>'):
        d = nt.count(tag) - t_before.count(tag)
        if d != 2:
            refuse('%s: this round opened %d %s, expected 2 - the '
                   'day-detail wrapper and the day nav'
                   % (TPL, d, tag))

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('MV-4 --check')
        print('  day        : one card, its own nav, moves by days')
        print('  week       : the card on a PHONE only, under the strip')
        print('  month      : never - MV-2 gates the whole panel')
        print('  the card   : unchanged, stepper and all')
        print('  files      : %d' % len(out))
        for q in sorted(out):
            print('    %s' % os.path.relpath(q, root))
        print('--check: nothing written.')
        return 0

    for q, val in sorted(out.items()):
        backup(q)
        write(q, val)
        print('  wrote %s' % os.path.relpath(q, root))
    print('MV-4  %d file(s) written, backups end %s' % (len(out), SUFFIX))
    print('Now run:  python test_day_view.py')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
