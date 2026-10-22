# -*- coding: utf-8 -*-
"""apply_msg_base.py - round BM-1, 21 Oct 2026.

EIGHTY-ONE PAGES SPELL THE MESSAGE BAR. FIFTY-FIVE CANNOT SHOW ONE.

MG-1 FIXED THREE PAGES ON 21 OCTOBER AND THE FAULT WAS NEVER THREE
PAGES. The planner, the shopping list and the printable plan wrote
messages and had no loop to show them, so Django kept each one in the
session until some later page iterated it - which is why Demetri kept
finding "Removed ..." on Recipe Management and on the logout screen.
The remedy was a loop on each of the three. It worked, and it left the
same hole open 55 more times.

THE CENSUS, taken off the tree rather than remembered:

    136   templates extend base.html
     81   of them carry a message loop
     55   do not - and every one of those is a page whose view can
          queue a message that will surface somewhere else

The 55 are mostly Add and Edit screens and reports: finance_expense_add,
properties_edit, suppliers_add, petty_cash_add, view_recipe,
import_recipe, every one of the valuation and line-type forms. Exactly
the pages that POST, write a message and redirect.

M1 UNIFIED THE SHAPE. THIS ROUND UNIFIES THE PLACE. On 29 September M1
took 77 loops in sixteen shapes down to one shape, and that one shape
is what the 81 copies carry today - identical, to the byte. A thing
written identically 81 times is written once, in the wrong place.

SO BASE RENDERS IT, AND NOBODY ELSE DOES. One loop, immediately inside
the content container, above {% block content %}.

THE BAR MOVES ON 71 PAGES, AND DEMETRI CHOSE THAT. Surveyed before
building: 71 of the 81 put the bar BELOW the page title, 10 above it.
base cannot know where a page's title is - the title is markup inside
the block - so one loop in base can only sit above the content. He was
shown the same bar on the same three real pages in both positions, at
1280px and at 390px, and picked above:

    "B - into base, above the title"

WHAT IS REMOVED, AND HOW IT IS FOUND. The loop is located by rule, not
by 81 literals - M1 did the same on the same 77 pages and the gates are
what make that honest. Every span this round deletes must flatten to
the ONE house shape, byte for byte, or the round refuses. Three
wrappers come with it: an {% if messages %} holding nothing else, a
<div class="messages"> and a <div class="revenue-messages"> - neither
of which any stylesheet in the tree mentions.

AND THREE SUITES ARE CORRECTED IN THIS PATCHER, because three of them
assert that a page carries the loop ITSELF:

    test_msg_bar.py      MG-1's own suite. Its claim becomes that the
                         three pages INHERIT the bar, and its driven
                         section - a real removal, followed, with the
                         word read off the page that comes back - is
                         left exactly as it was. It is the proof.
    test_message_bar.py  M1 counted "70 pages or more". One, now.
    test_auth_flow.py    login.html's loop, and the comment above it.

WHAT IS LEFT ALONE. generate_lease_agreement builds a static success
bar in JavaScript that wears .alv-message; it is not a Django message
and it stays. meal_plan_print keeps MG-1's print rule hiding the bar on
paper - base renders it now, so the page still needs to suppress it.

THE NAME IS BM-1, NOT MB-1. It was planned and discussed as MB-1 and
check_gates refused it: apply_done_badge.py already owns MB-1, and it
is named in alv_rounds.py and test_done_badge.py. Two rounds with one
name make the register ambiguous, and renaming the OLDER one afterwards
rewrites its comments, which is history edited to make room. So this
one moved. Same round, same contents, different two letters.

Idempotent. Every file backed up to .bak_msgbase.
"""
import os
import re
import sys

SUFFIX = '.bak_msgbase'
BASE = os.path.join('pages', 'templates', 'base.html')
MSGBAR = 'test_msg_bar.py'
MESSAGEBAR = 'test_message_bar.py'
AUTH = 'test_auth_flow.py'
CSSORDER = 'test_css_order.py'
ME = 'test_msg_base.py'
PATCHER = 'apply_msg_base.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'BM-1, 21 Oct 2026'
CHECK = False
CREATES = ()

# THE ONE SHAPE, as M1 left it and as all 81 pages carry it. Written
# here with no indent; the comparison is always made on the flattened
# form, so a page's own indentation never decides whether it matches.
HOUSE = """{% for VAR in messages %}
  <div class="alert alert-{{ VAR.tags }} alert-dismissible fade show alv-message" role="alert">
    {{ VAR }}
    <button type="button" class="close" data-dismiss="alert" aria-label="Close">
      <span aria-hidden="true">&times;</span>
    </button>
  </div>
{% endfor %}"""

BASE_WAS = """      {% block content %}{% endblock %}"""

BASE_NOW = """      {# THE ONE MESSAGE LOOP - BM-1, 21 Oct 2026.                      #}
      {#                                                                #}
      {# ONE loop, here, for every page that extends this file.         #}
      {#                                                                #}
      {# M1 made 77 copies agree on a shape on 29 September. They still #}
      {# agreed on 21 October - 81 pages, one shape, identical to the   #}
      {# byte - which is the definition of a thing that wants to live   #}
      {# in one place.                                                  #}
      {#                                                                #}
      {# AND 55 PAGES HAD NO COPY AT ALL. Their views queue messages    #}
      {# that Django holds in the session until SOME page iterates      #}
      {# them, so the message surfaced on whatever screen came next.    #}
      {# MG-1 fixed three of those on 21 October, one page at a time;   #}
      {# this is the same fix for all of them at once.                  #}
      {#                                                                #}
      {# ABOVE THE TITLE, WHICH IS A MOVE. 71 of the 81 put the bar     #}
      {# under their page title. base cannot know where a page title    #}
      {# is, so one loop can only sit here. Demetri was shown both      #}
      {# positions rendered at 1280px and 390px and chose this.         #}
      {#                                                                #}
      {# ONE COMMENT TAG PER LINE, and this note does not spell one.   #}
      {# Django comment tags DO NOT SPAN LINES. Written as one tag      #}
      {# around all of this, it stopped being a comment and printed     #}
      {# itself across the top of all 136 pages. The before-and-after   #}
      {# renders caught it; nothing else would have. A tag spelled      #}
      {# inside a comment ends it early and does the same thing.        #}
      {#                                                                #}
      {# `msg`, not `message`: 76 of the 81 spelled it that way.        #}
      {#                                       [test_msg_base.py]       #}
      {% for msg in messages %}
        <div class="alert alert-{{ msg.tags }} alert-dismissible fade show alv-message" role="alert">
          {{ msg }}
          <button type="button" class="close" data-dismiss="alert" aria-label="Close">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
      {% endfor %}
      {% block content %}{% endblock %}"""

# ==========================================================================
# CS-1's CONTROL, WHICH THIS ROUND USED UP
# ==========================================================================
# test_css_order section 7 plants a colliding rule into a template and
# checks section 5 catches it. Section 5 reads each page AS CS-1 LEFT IT
# - the earliest later round's backup of it, or the live file when no
# later round has one - so the plant is only visible on a page NO LATER
# ROUND HAS TOUCHED. The suite looks for that property rather than
# hard-coding a name, and says why: DR-1 broke this control on 4 October
# by backing up the page it used to use.
#
# THIS ROUND BACKS UP 81 TEMPLATES and took the last candidate with it.
#
# SO THE CONTROL PLANTS WHERE SECTION 5 READS. That is the property it
# actually needed all along - the comment above it says so in as many
# words, "a page section 5 actually SCANS" - and it was approximated by
# "a page no later round has touched" because that was the only case
# anybody had met. Planting into the file now() reads from is the same
# control, in the one place it cannot be invisible, and it no longer
# depends on some page in the tree happening to be untouched.
CS_SRC_WAS = """def now(p):
    \"\"\"The file as CS-1 left it.\"\"\"
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)"""

CS_SRC_NOW = """def now(p):
    \"\"\"The file as CS-1 left it.\"\"\"
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def source_of(p):
    \"\"\"The PATH now() reads from - BM-1, 21 Oct 2026.

    now() returns the file as CS-1 left it: the earliest later round's
    backup of it, or the file itself. Section 7 has to write into
    whichever of those it is, or its plant is invisible to section 5
    and the control reports a fault that is its own.
    \"\"\"
    if not as_left_by:
        return p
    import alv_rounds as _r
    later = (_r.ROUNDS[_r.ROUNDS.index(SUFFIX) + 1:]
             if SUFFIX in _r.ROUNDS else [])
    for s in later:
        if os.path.isfile(p + s):
            return p + s
    return p"""

CS_PICK_WAS = """    victim = None
    for q in alv_tree.templates():
        if alv_tree.rel(q) == BASE:
            continue
        if now(q) != read(q):
            continue                      # a later round owns this file"""

CS_PICK_NOW = """    # BM-1, 21 Oct 2026 - PLANT WHERE SECTION 5 READS, which is what
    # the note below always meant. This used to require a page NO LATER
    # ROUND HAD TOUCHED, because on such a page now() is the live file
    # and the plant lands where section 5 will look. BM-1 backs up 81
    # templates - it takes the message loop off every page that spells
    # one - and there was no such page left. The control now writes
    # into source_of(q), which IS where section 5 reads, so it holds
    # however much of the tree a later round has touched.
    victim = None
    for q in alv_tree.templates():
        if alv_tree.rel(q) == BASE:
            continue"""

CS_PLANT_WAS = """    print('        planting into %s' % alv_tree.rel(victim))
    vname = alv_tree.rel(victim)
    copy = os.path.join(SCRATCH, 'victim.html')
    shutil.copyfile(victim, copy)
    try:
        text = read(victim)"""

CS_PLANT_NOW = """    into = source_of(victim)
    print('        planting into %s%s' % (alv_tree.rel(victim),
                                          '' if into == victim
                                          else '  (via %s)'
                                          % os.path.basename(into)))
    vname = alv_tree.rel(victim)
    copy = os.path.join(SCRATCH, 'victim.html')
    shutil.copyfile(into, copy)
    try:
        text = read(into)"""

CS_WRITE_WAS = """        with open(victim, 'w', encoding='utf-8', newline='') as fh:
            fh.write(planted)"""

CS_WRITE_NOW = """        with open(into, 'w', encoding='utf-8', newline='') as fh:
            fh.write(planted)"""

CS_PUT_WAS = """    finally:
        shutil.copyfile(copy, victim)
    ok(read(victim) == text, 'the control was put back exactly')"""

CS_PUT_NOW = """    finally:
        shutil.copyfile(copy, into)
    ok(read(into) == text, 'the control was put back exactly')"""

CS_MSG_WAS = """    if not ok(victim is not None,
              'a page no later round has touched was found to plant into',
              'every template now has a backup from a round after CS-1 - '
              'the control needs one that does not'):
        return"""

CS_MSG_NOW = """    if not ok(victim is not None,
              'a page section 5 scans was found to plant into',
              'no template in the tree has rules section 5 would read'):
        return"""


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
    raise SystemExit('BM-1 REFUSED: %s' % msg)


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


def flat(s):
    return ' '.join(s.split())


def shape(block, var):
    """The block with its variable name normalised, flattened.

    This is the ONLY thing that decides whether a span may be deleted,
    so it is deliberately blunt: whitespace gone, `msg` or `message`
    made the same word, and then compared to one literal.
    """
    f = flat(block)
    for w, n in (('for %s in' % var, 'for VAR in'),
                 ('{{ %s ' % var, '{{ VAR '),
                 ('{{ %s.' % var, '{{ VAR.'),
                 ('{{ %s}}' % var, '{{ VAR}}'),
                 ('{{%s ' % var, '{{VAR ')):
        f = f.replace(w, n)
    return f


def loops(t):
    """Every {% for X in messages %} ... {% endfor %}, nesting-aware.

    Lifted from apply_message_bar.py, which swept the same 77 pages on
    29 September - including its hard-won last four lines: the match
    ends at `{% endfor`, not at the `%}` after it, and a slice taken
    without this left an orphan `%}` on all 77 pages.
    """
    out = []
    for m in re.finditer(r'\{%\s*for\s+(\w+)\s+in\s+messages\s*%\}', t):
        depth, i = 1, m.end()
        while depth:
            nxt = re.search(r'\{%\s*(for|endfor)\b', t[i:])
            if not nxt:
                refuse('a messages loop never closes')
            depth += 1 if nxt.group(1) == 'for' else -1
            i += nxt.end()
        close = t.find('%}', i)
        if close < 0:
            refuse('an endfor never closes')
        out.append((m.group(1), m.start(), close + 2))
    return out


def widen(t, s, e):
    """Grow the span over a wrapper that exists ONLY to hold the loop.

    Three of them in the tree: an {% if messages %} with nothing else
    inside it, a <div class="messages"> and a <div
    class="revenue-messages" style="margin-bottom:16px;">. No
    stylesheet in the tree names either class - asked, not assumed,
    by the gate below.
    """
    while True:
        pre, post = t[:s], t[e:]
        mi = re.search(r'\{%\s*if\s+messages\s*%\}\s*$', pre)
        mdv = re.search(r'<div[^>]*>\s*$', pre)
        pi = re.match(r'\s*\{%\s*endif\s*%\}', post)
        pd = re.match(r'\s*</div>', post)
        if mi and pi:
            s, e = mi.start(), e + pi.end()
            continue
        if mdv and pd:
            s, e = mdv.start(), e + pd.end()
            continue
        return s, e


def trim(t, s, e):
    """Take the blank line the span leaves behind with it, so removing
    a block does not leave a hole where one used to be."""
    while s > 0 and t[s - 1] in ' \t':
        s -= 1
    m = re.match(r'[ \t]*\r?\n', t[e:])
    if m and (s == 0 or t[s - 1] == '\n'):
        e += m.end()
    return s, e


# THE THREE COMMENT RUNS MG-1 WROTE. They explain why THAT page carries
# a loop, and this round takes the loop away, so they go with it. By
# exact literal: a rule that deleted comments near a span would be a
# rule nobody could predict.
MG1_NOTE = """{# THE MESSAGE BAR - MG-1, 21 Oct 2026.                              #}
{#                                                                  #}
{# Django queues a message and keeps it in the session until a      #}
{# template ITERATES it. The three Meal Plans pages - the planner,  #}
{# shopping list and the printable plan carried none between them.  #}
{# So twelve messages.success() calls in meal_planning.py queued up #}
{# and surfaced on whatever page came next: Recipe Management, or   #}
{# the logout screen. Demetri reported exactly that.                #}
{#                                                                  #}
{# `msg`, not `message`: 73 pages spell it this way and 5 do not.   #}
{# This is not the place to found a third dialect.                  #}
{#                                        [test_msg_bar.py]         #}
"""


# ---- login.html's COMMENT. A1 found two faults on 1 October and said
# so in one note: the word Login twice, and no red bar on a failed
# login. The second half named THIS PAGE's missing loop as the cause.
# The cause is the same; the remedy is now base's, and a note that
# still points at a loop nobody can find is worse than no note.
LOGIN_WAS = """{# ONE HEADING, AND A MESSAGE LOOP THAT IS NOT OPTIONAL - A1, 1 Oct 2026. #}
{# Demetri: the word Login showed twice, and a failed login showed no red  #}
{# bar. Those are ONE bug. This page had no messages loop, so the error    #}
{# the view queued was never iterated here and surfaced on the NEXT page   #}
{# that had a loop - the screen after the next SUCCESSFUL login. That is   #}
{# the stale "You Have Successfully Logged In" he also reported.           #}
{#                                             [test_auth_flow.py]         #}"""

LOGIN_NOW = """{# ONE HEADING, AND A MESSAGE LOOP THAT IS NOT OPTIONAL - A1, 1 Oct 2026. #}
{# Demetri: the word Login showed twice, and a failed login showed no red  #}
{# bar. Those are ONE bug. This page had no messages loop, so the error    #}
{# the view queued was never iterated here and surfaced on the NEXT page   #}
{# that had a loop - the screen after the next SUCCESSFUL login. That is   #}
{# the stale "You Have Successfully Logged In" he also reported.           #}
{#                                                                         #}
{# BM-1, 21 Oct 2026 - THE LOOP A1 ADDED HERE IS GONE, AND THE BAR IS NOT. #}
{# base renders it for every page now, this one included, because 55 other #}
{# pages had A1's bug and nobody had counted them. Do not add one back:    #}
{# two loops means every message twice.                                    #}
{#                               [test_auth_flow.py] [test_msg_base.py]    #}"""

# ---- MG-1's SUITE. Its subject does not change - the three Meal Plans
# pages must show a message - but where the bar comes from does.
MSGBAR_CLAIMS_WAS = """def claims(bundle):
    c = {}
    for p in FILES:
        name = os.path.basename(p)
        code = T.code_only(bundle[p])
        c['%s renders a message bar' % name] = (code.count(LOOP) == 1)
    return c"""

MSGBAR_CLAIMS_NOW = """def claims(bundle):
    # BM-1, 21 Oct 2026 - INHERITED, NOT SPELLED. MG-1 put a loop on
    # each of these three pages and the fault was never three pages:
    # 55 more had it. base renders the bar now, so what MG-1 proved -
    # that a message written by the planner LANDS on the planner - is
    # asked of the rendered page in section 3, and what is asked here
    # is that the page does not spell a second loop of its own. Two
    # loops would show every message twice.
    c = {}
    for p in FILES:
        name = os.path.basename(p)
        code = T.code_only(bundle[p])
        c['%s renders a message bar' % name] = (
            code.count(LOOP) == 0 and BASE_HAS_LOOP)
    return c"""

MSGBAR_TOP_WAS = """for p in FILES:
    name = os.path.basename(p)
    body = NOW[p]
    # .find(), NOT .index(). Against the reverted tree there is no bar
    # on any of these three pages, and .index() raised ValueError -
    # the suite CRASHED rather than failing, which blocks a push
    # exactly as hard and says far less about why. test_pick_note
    # crashed on the same thing on 20 October.
    i = body.find('{% block content %}')
    at = body.find('alv-message')
    ok(at >= 0 and i >= 0 and at - i < 1400,
       '%s puts it at the top of the content' % name,
       'block at %d, message at %d' % (i, at))
    ok('class="alert' in body, '  and it is the house alert' % ())"""

MSGBAR_TOP_NOW = """# BM-1, 21 Oct 2026 - THE PLACE MOVED TO base. This asked where each
# of the three pages put the bar inside its own content. base puts it
# in one place for all of them now, so the question is asked once, of
# base, and the three are asked only that they do not spell one.
#
# .find(), NOT .index(), throughout. Against the reverted tree there is
# no bar in base at all, and .index() raised ValueError - the suite
# CRASHED rather than failing, which blocks a push exactly as hard and
# says far less about why. test_pick_note crashed on the same thing on
# 20 October.
_bi = BASETXT.find('{% block content %}')
_bl = BASETXT.find(LOOP)
ok(_bl >= 0 and _bi >= 0 and _bl < _bi,
   'base renders the bar ABOVE the page content, which is the only '
   'place one loop can sit', 'loop at %d, block at %d' % (_bl, _bi))
ok('class="alert' in BASETXT, '  and it is the house alert')
for p in FILES:
    name = os.path.basename(p)
    ok(T.code_only(NOW[p]).count(LOOP) == 0,
       '%s spells none of its own - two loops would show every '
       'message twice' % name)"""

MSGBAR_HOUSE_WAS = """# THE HOUSE SPELLING, read off the tree rather than trusted.
import collections                                          # noqa: E402
shapes = collections.Counter()
for p in T.templates():
    s = read(p)
    if 'alv-message' not in s:
        continue
    i = s.index('alv-message')
    j = s.rfind('{% for', 0, i)
    if j < 0:
        continue
    k = s.find('{% endfor %}', i)
    shapes[re.sub(r'\\s+', ' ', s[j:k + 12]).strip()] += 1
house, n = shapes.most_common(1)[0]
# .find() AGAIN, for the same reason: against the reverted tree the
# planner has no loop to compare, and a missing block is a FAILED
# claim here, not a ValueError.
_at = NOW[PLANNER].find(LOOP)
_end = (NOW[PLANNER].find('{% endfor %}', _at) if _at >= 0 else -1)
mine = (re.sub(r'\\s+', ' ', NOW[PLANNER][_at:_end + 12]).strip()
        if _at >= 0 and _end > _at else '(no loop on the planner)')
ok(mine == house,
   'and all three use the block %d other pages already use' % n,
   '\\n  house: %s\\n  mine : %s' % (house[:88], mine[:88]))"""

MSGBAR_HOUSE_NOW = """# THE HOUSE SPELLING, read off the tree rather than trusted.
# BM-1, 21 Oct 2026 - there is exactly ONE page left that spells it,
# and it is base. This used to count how many pages already used the
# block MG-1 copied; the answer is 1, and that is the whole round.
#
# FOUND BY THE LOOP, NOT BY THE CLASS. The first `alv-message` in
# base.html is in its STYLESHEET, 138,000 characters before the loop,
# so anchoring on the class walked backwards into the sidebar and off
# the end. Ask for the tag.
import collections                                          # noqa: E402
shapes = collections.Counter()
spelt = []
for p in T.templates():
    s = read(p)
    found = 0
    for m in re.finditer(r'\\{%\\s*for\\s+\\w+\\s+in\\s+messages\\s*%\\}', s):
        k = s.find('{% endfor %}', m.start())
        if k < 0:
            continue
        shapes[re.sub(r'\\s+', ' ', s[m.start():k + 12]).strip()] += 1
        found += 1
    if found:
        spelt.append((os.path.basename(p), found))
ok(len(shapes) == 1, 'ONE shape in the tree spells the message loop',
   '%d shape(s): %r' % (len(shapes), [x[:70] for x in shapes]))
ok(spelt == [('base.html', 1)],
   'and ONE page spells it, once - base. There were 81 on 21 October',
   spelt[:6])
house, n = shapes.most_common(1)[0] if shapes else ('', 0)"""

MSGBAR_CTL_WAS = """BEFORE = dict((p, was(p)) for p in FILES)
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: before this round not one of the three did',
   'what held: %r' % (held,))
for p in FILES:
    ok('alv-message' not in T.code_only(BEFORE[p]),
       'CONTROL: %s really had no bar at all' % os.path.basename(p))"""

MSGBAR_CTL_NOW = """BEFORE = dict((p, was(p)) for p in FILES)
for p in FILES:
    ok('alv-message' not in T.code_only(BEFORE[p]),
       'CONTROL: %s really had no bar at all before MG-1'
       % os.path.basename(p))
# BM-1, 21 Oct 2026 - THE CONTROL IS STILL MG-1's BACKUP, and that is
# the point: these three pages had no bar before MG-1 and have none of
# their own after BM-1, for opposite reasons. claims() now asks about
# base, which .bak_msgbar2 says nothing about, so re-asking it of the
# backup would compare this round's tree with itself. The round that
# took the loops away carries its own control, in test_msg_base.py."""

# ---- AND THE THINGS THE CORRECTED CLAIMS ASK ABOUT. The subject of
# this suite is now partly base, so base has to be read.
MSGBAR_HEAD_WAS = """NOW = dict((p, read(p)) for p in FILES)
LOOP = '{% for msg in messages %}'"""

MSGBAR_HEAD_NOW = """NOW = dict((p, read(p)) for p in FILES)
LOOP = '{% for msg in messages %}'
# BM-1, 21 Oct 2026 - base is part of the subject now. It renders the
# bar for every page that extends it, so a claim about whether the
# planner can show a message is a claim about base and about the
# planner not spelling a second loop of its own.
BASE = T.path_of('base.html')
BASETXT = read(BASE)
BASE_HAS_LOOP = (T.code_only(BASETXT).count(LOOP) == 1)"""


# ---- M1's SUITE. It counted PAGES, and the number was the finding.
M1_WAS = """ok(pages >= 70, '  and that is %d pages, not a handful' % pages, pages)"""

M1_NOW = """# BM-1, 21 Oct 2026 - M1 UNIFIED THE SHAPE, BM-1 UNIFIED THE PLACE.
# This read `pages >= 70` and it was the finding at the time: one
# shape, written out seventy-odd times. The shape never drifted - 81
# pages, identical to the byte, on 21 October - which is what made it
# safe to move into base. The claim is now the opposite number for the
# same reason.
ok(pages == 1, '  and that is %d page - base, and nobody else. It was 81 '
   'on 21 October and they never drifted, which is what made moving '
   'them safe' % pages, pages)"""

# ---- THE LOGIN SUITE. A1's finding stands; the loop it named does not.
AUTH_WAS = """ok('{% for msg in messages %}' in m and 'alv-message' in m,
   'it has the house message loop - which is what makes the red bar possible')"""

AUTH_NOW = """# BM-1, 21 Oct 2026 - A1 PUT A LOOP ON THIS PAGE AND base OWNS IT NOW.
# The finding does not change: a failed login must show a red bar.
# Where the bar comes from does, so the claim is asked of base and of
# this page NOT spelling a second one - and section 5 posts a real
# failed login and reads the bar off the page that comes back, which
# is the only form of this claim that was ever about the application.
_bs = read(alv_tree.path_of('base.html'))
ok('{% for msg in messages %}' in _bs and 'alv-message' in _bs,
   'base carries the house message loop - which is what makes the red '
   'bar possible, here and on the 55 pages that never had one')
ok('{% for msg in messages %}' not in m,
   '  and login.html spells none of its own - two loops would show a '
   'failed login twice')"""

AUTH_CTL_WAS = """    ok('{% for msg in messages %}' not in bm,
       'CONTROL: the backup had NO message loop at all - which is why the '
       'error the view queued surfaced on a later page')"""

AUTH_CTL_NOW = """    # BM-1, 21 Oct 2026 - THE BACKUP IS STILL A1's, and this still
    # reads as A1 wrote it. It must: the backup predates the loop A1
    # added, so it has none for a different reason than today's page
    # has none. What separates them is base, which the claim above
    # asks about and this backup knows nothing of.
    ok('{% for msg in messages %}' not in bm,
       'CONTROL: the backup had NO message loop at all, and no base to '
       'inherit one from - which is why the error the view queued '
       'surfaced on a later page')"""



def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pbase = os.path.join(root, BASE)
    b = read(pbase)

    if MARK in b and '{% for msg in messages %}' in b:
        print('BM-1  already applied - base renders the message bar.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- THE FINDING, ASKED OF THE TREE. Not a number in a docstring.
    pages, loops_n, shapes = [], 0, set()
    for q in T.templates():
        if os.path.abspath(q) == os.path.abspath(pbase):
            continue
        t = read(q)
        ls = loops(t)
        if not ls:
            continue
        pages.append(q)
        for var, s, e in ls:
            loops_n += 1
            shapes.add(shape(t[s:e], var))
    if len(shapes) != 1:
        refuse('the %d loop(s) across %d page(s) are %d shapes, not one - '
               'M1 left them as one and this round moves a shape, not a '
               'family of them' % (loops_n, len(pages), len(shapes)))
    if flat(list(shapes)[0]) != flat(HOUSE):
        refuse('the shape on the tree is not the one this round carries:'
               '\n  tree: %s\n  mine: %s'
               % (list(shapes)[0][:110], flat(HOUSE)[:110]))
    if len(pages) < 60:
        refuse('only %d page(s) carry the loop - this round expected the '
               'whole tree, so something has already moved' % len(pages))
    if loops_n != len(pages):
        refuse('%d loop(s) across %d page(s) - a page with two is a page '
               'this round has not looked at' % (loops_n, len(pages)))

    # ---- NOBODY STYLES THE WRAPPERS. Asked before they are deleted.
    styled = []
    for q in T.templates():
        s = read(q)
        for cls in ('.messages', '.revenue-messages'):
            if re.search(re.escape(cls) + r'\s*[,{]', s):
                styled.append((os.path.relpath(q, root), cls))
    if styled:
        refuse('a wrapper this round removes is styled somewhere: %r'
               % (styled[:4],))

    # ---- BASE GETS THE ONE LOOP.
    out[pbase] = swap(b, BASE_WAS, BASE_NOW, 'base.html (the bar)')

    # ---- AND THE 81 GIVE THEIRS UP.
    removed = 0
    for q in pages:
        t = read(q)
        ls = loops(t)
        parts, last = [], 0
        for var, s, e in ls:
            block = t[s:e]
            if shape(block, var) != flat(HOUSE):
                refuse('%s: the span is not the house shape - %s'
                       % (os.path.relpath(q, root), shape(block, var)[:90]))
            s, e = widen(t, s, e)
            s, e = trim(t, s, e)
            parts.append(t[last:s])
            last = e
            removed += 1
        parts.append(t[last:])
        n = ''.join(parts)
        if MG1_NOTE.strip() and fit(n, MG1_NOTE) in n:
            n = n.replace(fit(n, MG1_NOTE), '')
        if loops(n):
            refuse('%s: a loop survived the removal'
                   % os.path.relpath(q, root))
        if n.count('{%') != n.count('%}'):
            refuse('%s: the tags stopped balancing - %d {%% against %d %%}'
                   % (os.path.relpath(q, root), n.count('{%'),
                      n.count('%}')))
        out[q] = n
    if removed != loops_n:
        refuse('removed %d of %d loop(s)' % (removed, loops_n))

    # ---- login.html's COMMENT, half of which this round makes untrue.
    plogin = T.path_of('login.html')
    lg = out.get(plogin, read(plogin))
    lg = swap(lg, LOGIN_WAS, LOGIN_NOW, 'login.html (the note)')
    out[plogin] = lg

    # ---- MG-1's SUITE. Its claim was that the three pages carry the
    # loop. They inherit it now, which is a different claim about the
    # same thing, and its DRIVEN section is left untouched on purpose -
    # a real removal, followed, with the word read off the page that
    # comes back is the only evidence that survives this move.
    pmb = os.path.join(root, MSGBAR)
    s = read(pmb)
    s = swap(s, MSGBAR_HEAD_WAS, MSGBAR_HEAD_NOW, '%s (the head)' % MSGBAR)
    s = swap(s, MSGBAR_CLAIMS_WAS, MSGBAR_CLAIMS_NOW,
             '%s (the claim)' % MSGBAR)
    s = swap(s, MSGBAR_TOP_WAS, MSGBAR_TOP_NOW, '%s (the place)' % MSGBAR)
    s = swap(s, MSGBAR_HOUSE_WAS, MSGBAR_HOUSE_NOW,
             '%s (the census)' % MSGBAR)
    s = swap(s, MSGBAR_CTL_WAS, MSGBAR_CTL_NOW, '%s (the control)' % MSGBAR)
    out[pmb] = s

    # ---- M1's SUITE. It counted pages; there is one now.
    pm1 = os.path.join(root, MESSAGEBAR)
    out[pm1] = swap(read(pm1), M1_WAS, M1_NOW, '%s (the count)' % MESSAGEBAR)

    # ---- THE LOGIN SUITE.
    pau = os.path.join(root, AUTH)
    a = read(pau)
    a = swap(a, AUTH_WAS, AUTH_NOW, '%s (the loop)' % AUTH)
    a = swap(a, AUTH_CTL_WAS, AUTH_CTL_NOW, '%s (the control)' % AUTH)
    out[pau] = a

    # ---- CS-1's CONTROL
    pcs = os.path.join(root, CSSORDER)
    cs = read(pcs)
    for a2, b2, w in ((CS_SRC_WAS, CS_SRC_NOW, 'source_of'),
                      (CS_PICK_WAS, CS_PICK_NOW, 'the pick'),
                      (CS_MSG_WAS, CS_MSG_NOW, 'the message'),
                      (CS_PLANT_WAS, CS_PLANT_NOW, 'the plant'),
                      (CS_WRITE_WAS, CS_WRITE_NOW, 'the write'),
                      (CS_PUT_WAS, CS_PUT_NOW, 'putting it back')):
        cs = swap(cs, a2, b2, '%s (%s)' % (CSSORDER, w))
    out[pcs] = cs

    # ---- REGISTRATION
    pg = os.path.join(root, PS1)
    g = read(pg)
    g = swap(g, """    'test_photo_floor.py'
)""", """    'test_photo_floor.py',
    # BM-1, 21 Oct 2026 - one message loop in base, 81 copies gone,
    # and the 55 pages that could not show a message can now.
    'test_msg_base.py'
)""", '%s (the suites)' % PS1)
    g = swap(g,
             """    @{ File = 'pages/models.py'; Text = 'DISPLAY_FLOOR';""",
             """    @{ File = 'pages/templates/base.html'; Text = 'THE ONE MESSAGE LOOP - BM-1'; What = 'BM-1: base renders the message bar for every page that extends it - 81 identical copies removed, and the 55 pages that had none can show a message at last' },
    @{ File = 'pages/models.py'; Text = 'DISPLAY_FLOOR';""",
             '%s (the sentinels)' % PS1)
    out[pg] = g

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # PX-2, 21 Oct 2026 - the upscale done once, properly, here.
    'test_photo_floor.py',
]""", """    # PX-2, 21 Oct 2026 - the upscale done once, properly, here.
    'test_photo_floor.py',
    # BM-1, 21 Oct 2026 - the message bar, once, in base.
    'test_msg_base.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # PX-2, 21 Oct 2026 - a floor under every display copy.
    '.bak_photofloor',
]""", """    # PX-2, 21 Oct 2026 - a floor under every display copy.
    '.bak_photofloor',
    # BM-1, 21 Oct 2026 - one message loop, in base.
    '.bak_msgbase',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    nn = re.search(r'CONVERTED_N = (\d+)', w)
    out[pw] = swap(w, 'CONVERTED_N = %s' % nn.group(1),
                   'CONVERTED_N = %d   # BM-1, 21 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(nn.group(1)) + 1, nn.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nb = out[pbase]
    if len(loops(nb)) != 1:
        refuse('base carries %d loop(s), and this round is about there '
               'being exactly one' % len(loops(nb)))
    var, s, e = loops(nb)[0]
    if shape(nb[s:e], var) != flat(HOUSE):
        refuse('base loop is not the shape the 81 pages agreed on')
    # A DJANGO COMMENT TAG DOES NOT SPAN LINES, and one that tries is
    # not a comment - it is text, printed across the top of all 136
    # pages. This round wrote one and the renders caught it. A gate is
    # cheaper than a render.
    for ln, line in enumerate(nb.split('\n'), 1):
        if line.count('{#') != line.count('#}'):
            refuse('base.html line %d opens or closes a comment tag it '
                   'does not finish on the same line - Django comments '
                   'do not span lines, and the text would print: %r'
                   % (ln, line.strip()[:70]))
        if line.count('{#') > 1 or line.count('#}') > 1:
            refuse('base.html line %d carries more than one comment tag, '
                   'so the first close ends it and the rest prints: %r'
                   % (ln, line.strip()[:70]))
    if nb.index('{% for msg in messages %}') > nb.index('{% block content %}'):
        refuse('base renders the bar AFTER the page content, which is the '
               'one place it must not be')
    # IT MUST BE INSIDE THE CONTAINER. Outside it the bar loses the
    # page gutter and runs edge to edge on a desktop.
    if 'class="container"' in nb:
        if nb.index('class="container"') > nb.index('{% for msg in messages %}'):
            refuse('base renders the bar outside the content container')
    # AND NOBODY ELSE RENDERS ONE.
    left = []
    for q, val in out.items():
        if q == pbase or not q.endswith('.html'):
            continue
        if loops(val):
            left.append(os.path.relpath(q, root))
    for q in T.templates():
        if os.path.abspath(q) == os.path.abspath(pbase) or q in out:
            continue
        if loops(read(q)):
            left.append(os.path.relpath(q, root))
    if left:
        refuse('a page still spells the loop itself: %r' % (left[:5],))
    # THE PRINTABLE PLAN STILL HIDES IT ON PAPER. base renders it now,
    # so the suppression matters more, not less.
    pp = T.path_of('meal_plan_print.html')
    pv = out.get(pp, read(pp))
    pc = T.code_only(pv)
    if '@media print' not in pc or '.alv-message' not in \
            pc[pc.index('@media print'):]:
        refuse('meal_plan_print stopped hiding the bar on paper')
    # THE STATIC LEASE BANNER IS NOT A DJANGO MESSAGE AND STAYS.
    pl = T.path_of('generate_lease_agreement.html')
    lv = out.get(pl, read(pl))
    if 'id="lease-success-message"' not in lv:
        refuse('the lease page static banner was removed, and it is not a '
               'Django message')

    if CHECK:
        print('BM-1  --check: %d file(s) would change, none written.'
              % len(out))
        print('        %d loop(s) removed from %d page(s), one shape'
              % (removed, len(pages)))
        print('        base renders it once, above the content')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('BM-1  applied - the message bar is written once, in base.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
