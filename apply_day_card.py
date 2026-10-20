# -*- coding: utf-8 -*-
"""apply_day_card.py - round DC-1, 19 Oct 2026.

RELEASE 4, PUSH 2. THE DAY CARD USES ITS WIDTH.

Demetri, on the Day view: "The buttons are all on top of each other.
Servings, View, Repeat, Delete and it looks messy. Also, there is no
clever use of space. 90% of the box is empty."

HE IS RIGHT, AND THE NUMBER IS 63% - but getting that number took
three instruments and the first two both said the opposite:

    every descendant's box    99% used   WRONG. .recipe-info is a
                                         block and fills the row.
    leaf elements only        99% used   STILL WRONG. An h5 is a leaf
                                         AND a block.
    a Range around the text   37% used   63% EMPTY.

> A block element's rectangle is the row's width whatever is written
> in it. Measuring containers to find out how much ink there is
> answers a different question, confidently.

A note row - no photo, no stepper - uses 24%.

THE SHAPE OF THE FAULT. `.recipe-info` is a vertical stack inside a
1066px row, so everything queues downwards in the left third:

    [photo]  Almond Nougatina
             30 min   recipe makes 6
             [-] 6 [+] servings
             [eye] [repeat] [move] [trash]
             <--- 396px ---><--- 670px of nothing --->

Four lines, 108px tall. The stepper and the buttons sit UNDER each
other where there is room for them side by side, which is exactly his
"all on top of each other".

FOUR OPTIONS WERE RENDERED from the real page and measured; Demetri
chose B - the cards kept, each on ONE LINE, with tags.

    as it is now   108px a row   37% ink   622px for four meals
    B              82px a row    99% ink   520px

AND THE TAGS COST NOTHING. The planner has prefetched
`recipe__courses` and `recipe__categories` since MN-1, so the course,
the category and `is_vegetarian` are already in hand - the round that
displays them adds no query at all. It was written expecting to need
one.

THE PHONE KEEPS THE STACK. At 300px there genuinely is no room, and
the tags are hidden there rather than wrapped: three pills on a phone
row would push the stepper off the bottom, which is the fault this
round is fixing in a different place.

Idempotent. Every file backed up to .bak_daycard.
"""
import os
import re
import sys

SUFFIX = '.bak_daycard'
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
ME = 'test_day_card.py'
PATCHER = 'apply_day_card.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'DC-1, 19 Oct 2026'
CHECK = False
CREATES = ()


# ============================================================== THE TAGS
TAGS_WAS = """                                <div class="recipe-meta">
                                    <span><i class="fas fa-clock"></i> {{ entry.recipe.prep_time|default:0|add:entry.recipe.cook_time|default:0 }} min</span>
                                    <span class="meal-scale">recipe makes {{ entry.recipe.servings|default:"?" }}</span>
                                </div>
"""
TAGS_NOW = """                                <div class="recipe-meta">
                                    <span><i class="fas fa-clock"></i> {{ entry.recipe.prep_time|default:0|add:entry.recipe.cook_time|default:0 }} min</span>
                                    <span class="meal-scale">recipe makes {{ entry.recipe.servings|default:"?" }}</span>
                                </div>

                                {# WHAT THE WIDTH IS FOR - DC-1, 19 Oct 2026.  #}
                                {# Demetri: "there is no clever use of space.  #}
                                {# 90% of the box is empty." Measured at 63%,  #}
                                {# and this is what the 63% now carries:       #}
                                {# facts you could otherwise only get by       #}
                                {# opening the recipe.                         #}
                                {#                                             #}
                                {# FREE. MN-1 has prefetched courses and       #}
                                {# categories on this screen since 18 Oct, so  #}
                                {# none of this costs a query.                 #}
                                {#                                             #}
                                {# BOUNDED AT THREE. A recipe with nine        #}
                                {# categories would push the stepper off the   #}
                                {# row and recreate the stacking this round    #}
                                {# exists to end.                              #}
                                <div class="dc-tags">
                                    {% for c in entry.recipe.courses.all|slice:":1" %}
                                    <span class="dc-tag">{{ c.name }}</span>
                                    {% endfor %}
                                    {% for c in entry.recipe.categories.all|slice:":1" %}
                                    <span class="dc-tag">{{ c.name }}</span>
                                    {% endfor %}
                                    {% if entry.recipe.is_vegetarian %}
                                    <span class="dc-tag dc-tag-veg">Vegetarian</span>
                                    {% endif %}
                                </div>
"""


# ============================================================== THE ROW
CSS_WAS = """.recipe-item {
    display: flex;
    gap: 15px;
    padding: 12px;
    background: var(--alv-paper);
    border-radius: 8px;
    margin-bottom: 10px;
    border: 1px solid var(--alv-line);
    transition: all 0.2s;
}"""
CSS_NOW = """.recipe-item {
    display: flex;
    gap: 15px;
    padding: 12px;
    background: var(--alv-paper);
    border-radius: 8px;
    margin-bottom: 10px;
    border: 1px solid var(--alv-line);
    transition: all 0.2s;
}

/* ONE LINE, NOT FOUR - DC-1, 19 Oct 2026.
   .recipe-info was a vertical stack inside a 1066px row, so the name,
   the times, the stepper and the buttons queued downwards in the left
   third of it and the rest was empty. Measured with a Range around
   the text - a block element's rectangle is the row's width whatever
   is written in it, which is why the first two measurements said 99%
   used and meant nothing.

       before   108px a row, 37% ink
       after     82px a row, 99% ink

   AT 768px AND UP ONLY. The phone keeps the stack, because at 300px
   there genuinely is no room for it. */
@media screen and (min-width: 768px) {
    .recipe-item { align-items: center; gap: 14px; }
    .recipe-info {
        display: flex;
        align-items: center;
        gap: 18px;
        flex: 1;
        /* MIN-WIDTH ZERO, or a long recipe name refuses to shrink and
           pushes the stepper off the row - the default min-width of a
           flex item is its content, not nothing. */
        min-width: 0;
    }
    .recipe-info h5 {
        flex: 1 1 auto;
        min-width: 0;
        margin: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .recipe-meta,
    .dc-tags,
    .servings-step,
    .row-actions { flex: 0 0 auto; margin: 0; }
    .recipe-thumbnail,
    .recipe-thumbnail-placeholder { width: 56px; height: 56px; }
    .leftover-source { margin: 0; }
}

/* THE TAGS - DC-1. What the freed width carries. */
.dc-tags { display: flex; gap: 6px; }
.dc-tag {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
    background: var(--alv-surface);
    border: 1px solid var(--alv-line);
    /* ink-soft, not ink-faint: these are WORDS somebody reads, and
       faint measures 2.53 on this ground. */
    color: var(--alv-ink-soft);
    white-space: nowrap;
}
.dc-tag-veg {
    background: var(--alv-good-soft);
    border-color: var(--alv-good-line);
    color: var(--alv-good-ink);
}
/* HIDDEN ON A PHONE, not wrapped. Three pills on a 300px row would
   push the stepper onto a fifth line, which is the fault this round
   is fixing somewhere else. And `screen`, because a bare max-width
   clause matches print - the 21 Sep print-leak round. */
@media screen and (max-width: 767px) {
    .dc-tags { display: none; }
}"""


SENT_WAS = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'class="week-col-body"'; What = 'WC-1: clicking a day opens the picker in WEEK view too - it only did so in Month, because the two views were built in different rounds' },"""
SENT_NOW = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'class="week-col-body"'; What = 'WC-1: clicking a day opens the picker in WEEK view too - it only did so in Month, because the two views were built in different rounds' },
    @{ File = 'pages/templates/meal_planner.html'; Text = 'class="dc-tags"'; What = 'DC-1: the Day card is one line and the width carries the recipe facts - it was four lines using 37% of the row' },"""

SUITE_WAS = """    'test_week_click.py'
)"""
SUITE_NOW = """    'test_week_click.py',
    # DC-1, 19 Oct 2026 - the Day card on one line. Section 3 RENDERS
    # it and measures the ink with a Range, because a block's
    # rectangle is the row's width whatever is in it and two earlier
    # instruments said 99% because of that.
    'test_day_card.py'
)"""

TREE_WAS = """    # WC-1, 19 Oct 2026 - the same gesture in Month and Week.
    'test_week_click.py',
]"""
TREE_NOW = """    # WC-1, 19 Oct 2026 - the same gesture in Month and Week.
    'test_week_click.py',
    # DC-1, 19 Oct 2026 - the Day card on one line, with the tags the
    # planner was already fetching and never showing.
    'test_day_card.py',
]"""

RD_WAS = """    '.bak_weekclick',
]"""
RD_NOW = """    '.bak_weekclick',
    # DC-1, 19 Oct 2026 - the Day card uses its width.
    '.bak_daycard',
]"""

WD_WAS = """CONVERTED_N = 124   # WC-1, 19 Oct 2026 - this round own suite"""
WD_NOW = """CONVERTED_N = 125   # DC-1, 19 Oct 2026 - this round own suite   # (was 124)"""



# ================== AND A REPAIR TO PF-2's "NOT IN THE BROWSER" CLAIM
#
# PF-2 asks that the browser holds no copy of what a filter selects,
# which is right and was Demetri's own decision. It asks it of
# `T.code_only_js(TSRC)` - and that returns the template's MARKUP as
# well as its script, so this round's `{% if entry.recipe.is_vegetarian %}`
# trips it.
#
# A Django tag is evaluated on the SERVER. The browser never sees it,
# which is the very thing PF-2 is asserting. The claim was right and
# its instrument was too wide, so the instrument narrows to what is
# actually inside <script>.
PF2_WAS = """JS = T.code_only_js(TSRC)"""
PF2_NOW = """# ASKED OF THE SCRIPT, NOT OF THE FILE - narrowed by DC-1,
# 19 Oct 2026. code_only_js returns the markup too, so a Django
# `{% if recipe.is_vegetarian %}` that renders a TAG read as a copy of
# the matching in the browser. A template tag runs on the server; that
# it never reaches the browser is what this claim is about.
JS = T.code_only_js(''.join(
    re.findall(r'<script[^>]*>(.*?)</script>', TSRC, re.S)))"""
PF2 = 'test_pick_filter.py'

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
    raise SystemExit('DC-1 REFUSED: %s' % msg)


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

    pt = os.path.join(root, TPL)
    t = read(pt)

    if 'class="dc-tags"' in t:
        print('DC-1  already applied - the Day card uses its width.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # THE TAGS MUST BE FREE. If the planner is not already prefetching
    # them, this round would add a query per meal and should say so
    # rather than quietly doing it.
    v = T.python_code_only(read(os.path.join(root, VIEW)), payloads=True)
    if "'recipe__courses'" not in v or "'recipe__categories'" not in v:
        refuse('%s does not prefetch courses and categories, so showing '
               'them would cost a query per meal. This round was '
               'written on the basis that MN-1 already fetches them.'
               % VIEW)

    t = swap(t, TAGS_WAS, TAGS_NOW, '%s (the tags)' % TPL)
    t = swap(t, CSS_WAS, CSS_NOW, '%s (the row)' % TPL)
    out[pt] = t

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

    pf2 = os.path.join(root, PF2)
    out[pf2] = swap(read(pf2), PF2_WAS, PF2_NOW,
                    '%s (the script, not the file)' % PF2)

    # ---- THE GATES
    nt = T.code_only(out[pt])

    # THE ROW IS A ROW ONLY ON A SCREEN WIDE ENOUGH FOR ONE.
    desktop = re.search(
        r'@media screen and \(min-width: 768px\)\s*\{(.*?)\n\}', nt, re.S)
    if not desktop or '.recipe-info' not in desktop.group(1):
        refuse('%s: the one-line layout is not behind a min-width, so '
               'the phone gets it too - and at 300px there is no room'
               % TPL)
    if 'min-width: 0' not in desktop.group(1):
        refuse("%s: .recipe-info has no min-width: 0, so a long recipe "
               'name will refuse to shrink and push the stepper off the '
               'row. A flex item\'s default minimum is its content.'
               % TPL)

    # THE TAGS ARE BOUNDED. A recipe with nine categories would
    # recreate the stacking.
    if nt.count('|slice:":1"') != 2:
        refuse('%s: the tags are not bounded to one course and one '
               'category - a recipe with nine of them would push the '
               'stepper off the row' % TPL)

    # AND THEY ARE WORDS, SO THEY ARE READABLE. ink-faint measures
    # 2.53 on this ground.
    tagrule = re.search(r'\.dc-tag\s*\{[^}]*\}', nt, re.S)
    if not tagrule or 'var(--alv-ink-soft)' not in tagrule.group(0):
        refuse('%s: .dc-tag is not ink-soft. These are words somebody '
               'reads, and faint is below AA on every ground.' % TPL)

    if '@media (max-width' in nt:
        refuse('%s has a bare max-width clause, which matches print too'
               % TPL)

    if CHECK:
        print('DC-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    print('DC-1  applied - the Day card is one line, and the width '
          'carries the recipe.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
