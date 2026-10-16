# -*- coding: utf-8 -*-
"""apply_ws_members.py - round WM-1, 16 Oct 2026.

THE MEMBER COUNT BECOMES A CONTROL.

Demetri, testing Administration: the Members cell on Workspace
Management shows an icon and a number. It should be clickable and show
the member names.

NOTHING IS BUILT THAT ALREADY EXISTS
    The names are already on the page - as a `title=` tooltip, which is
    a hover, not a control, and invisible on a phone. `ws.member_list`
    is already in the view, already select_related on user and already
    ordered by username. So this round adds no query, no view change and
    no new component.

    base carries ALV POP v1, and its own description is this finding in
    other words: "A list that opens from a cell - 12 ingredients,
    clicked, showing which twelve." Categories and Measurement Units use
    it. Workspace Members is the third.

THE TOOLTIP GOES WITH IT
    Leaving it would give a hover AND a click on the same element,
    saying the same thing twice - and the hover is the half that does
    not work on the device where the cell is hardest to read.

ONE PILL, NOT A BOX IN A BOX
    The model page wraps a plain text count, so there the trigger draws
    the whole affordance. `.ws-members` is already a pill - background,
    padding 4px 10px, radius 12px - so a trigger wrapped AROUND it would
    paint a second rounded box 8px outside the first on hover. The two
    classes go on ONE span instead. The page's own <style> is inside
    {% block content %}, so it is in the body, after base: on the three
    properties both declare at one class of specificity the page wins and
    the pill keeps its shape. `.alv-pop-trigger:hover` is two classes, so
    the pill itself is what darkens. `.alv-pop` is position: fixed, so it
    is not a flex item of the inline-flex pill it now sits inside.

NOT WS-1. That name is taken by six files. This is WM-1.
"""
import os
import re
import sys

import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_wsmembers'
PAGE = 'workspace_management.html'
MODEL = 'categories_management.html'
VIEW = os.path.join('pages', 'views', 'users.py')
ME = 'test_ws_members.py'
PATCHER = 'apply_ws_members.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
CHECK = False

CONVERTED_WAS, CONVERTED_NOW = 93, 94
ALIAS_WAS, ALIAS_NOW = 97, 99
ALIAS_P_WAS, ALIAS_S_WAS = 48, 49
ALIAS_P_NOW, ALIAS_S_NOW = 49, 50

CELL_WAS = """                    <td data-label="Members">
                        <span class="ws-members" title="{% for m in ws.member_list %}{{ m.user.username }}{% if not forloop.last %}, {% endif %}{% endfor %}">
                            <i class="fas fa-users"></i> {{ ws.member_count }}
                        </span>
                    </td>"""

CELL_NOW = """                    {# WM-1, 16 Oct 2026 - the count is a CONTROL now, not a #}
                    {# hover. Demetri: the member count should be clickable #}
                    {# and show the names. #}
                    {# #}
                    {# The names were already here, as a title= tooltip - a #}
                    {# hover does not exist on a phone, which is where this #}
                    {# cell is hardest to read. ALV POP v1 in base is the #}
                    {# component for exactly this, and its own note says so: #}
                    {# a list that opens from a cell, 12 ingredients clicked #}
                    {# showing which twelve. Categories and Measurement Units #}
                    {# are the other two. No new query: ws.member_list is #}
                    {# already select_related and already ordered. #}
                    {# #}
                    {# ONE PILL, NOT A BOX IN A BOX. The model page wraps a #}
                    {# plain text count, so there the trigger IS the whole #}
                    {# affordance. Here .ws-members is already a pill with #}
                    {# its own background, padding and radius - a trigger #}
                    {# wrapped round it would draw a second rounded box on #}
                    {# hover, 8px outside the first. So the two classes sit #}
                    {# on ONE span: the page wins padding and radius (its #}
                    {# style block is in the body, after base), base gives #}
                    {# the cursor, and .alv-pop-trigger:hover outranks #}
                    {# .ws-members on specificity, so the pill itself is #}
                    {# what darkens. .alv-pop is position: fixed, so it is #}
                    {# not a flex item of the pill it now sits inside. #}
                    <td data-label="Members">
                        <span class="ws-members alv-pop-trigger" aria-expanded="false">
                            <i class="fas fa-users"></i> {{ ws.member_count }}

                            <div class="alv-pop">
                                {% if ws.member_list %}
                                <ul class="alv-pop-list">
                                    {% for m in ws.member_list %}
                                    <li>{{ m.user.get_full_name|default:m.user.username }}</li>
                                    {% endfor %}
                                </ul>
                                {% else %}
                                <div class="alv-pop-empty">
                                    No members
                                </div>
                                {% endif %}
                            </div>
                        </span>
                    </td>"""


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
    raise SystemExit('WM-1 REFUSED: %s' % msg)


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


def swap(text, was, now, where):
    once(text, was, where)
    return text.replace(fit(text, was), fit(text, now), 1)


def bump(text, lit, was, now, note, where):
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


SUITE_WAS = """    'test_home_open.py'
)"""
SUITE_NOW = """    'test_home_open.py',
    'test_ws_members.py'
)"""

TREE_WAS = """    'test_home_open.py',
]"""
TREE_NOW = """    'test_home_open.py',
    # WM-1, 16 Oct 2026 - the Workspace member count becomes a control
    # on ALV POP v1, instead of a title= tooltip that a phone cannot
    # show. Wide from birth.
    'test_ws_members.py',
]"""

ROUNDS_WAS = """    '.bak_homeopen',
]"""
ROUNDS_NOW = """    '.bak_homeopen',
    # WM-1, 16 Oct 2026 - workspace_management's Members cell opens the
    # names it already carried in a tooltip. Third consumer of ALV POP
    # v1, no new query and no new component.
    '.bak_wsmembers',
]"""

# THE VIEW'S COMMENT NAMES THE TOOLTIP THIS ROUND REMOVES.
#
# Leaving it would be the drift that cost a whole round today: a comment
# that gives a reason the tree no longer has. The code does not change -
# the list is the same list, built the same way - only the sentence
# saying what it is for.
#
# The N+1 is NOT fixed here, and is not pretended away either. One query
# per row is what this loop has always done; making it a prefetch is a
# query change, which is a different round and a different conversation.
VIEW_WAS = """    # Pre-fetch members for the count tooltip and edit-page reuse."""
VIEW_NOW = """    # Pre-fetch members for the count POPUP and edit-page reuse.
    # WM-1, 16 Oct 2026 - it was a title= tooltip until this round; the
    # popup reads the same list, so no query changed. One query per row
    # is pre-existing and still here: a prefetch is its own round."""

# ---------------------------------------------------- test_data_table.py
#
# THE ROUND THAT BREAKS A SUITE FIXES IT.
#
# DT-1 deployed green three hours ago. Two things in its suite break the
# moment this bundle lands, and both are faults AS-1's census named this
# morning across 249 suites:
#
#   1. It reads the two shared counters LIVE, so it asserts DT-1's
#      numbers against whatever the NEWEST round wrote. as_left_by is
#      what that is for, and alv_rounds already exposes it.
#
#   2. Its line-ending check asserts a COUNT - `lf <= w_lf`. home.html
#      is a pure LF file, so HM-4 adding eight lines to it raises the LF
#      count, which is not a fault. A count cannot tell a round that
#      ADDED lines from a round that CONVERTED them. The style can.
#
# apply_data_table.py set the precedent for this in the other direction:
# it re-pointed test_system_teal.py when it broke it.
DT = 'test_data_table.py'

DT_COUNT_WAS = """wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
ok('CONVERTED_N = %d' % CONVERTED_NOW in wd,
   'test_waiting_down counts %d converted suites' % CONVERTED_NOW)
co = read(os.path.join(ROOT, 'test_code_only.py'))
ok('ok(len(aliased) == %d,' % ALIAS_NOW in co,
   'test_code_only counts %d files aliasing code_only' % ALIAS_NOW)"""

DT_COUNT_NOW = """# THE SHARED COUNTERS ARE READ AS DT-1 LEFT THEM, NOT LIVE.
#
# WM-1, 16 Oct 2026. These two files hold a hand-kept number that EVERY
# converted round bumps, so a suite that reads them live asserts its own
# number against whatever the NEWEST round wrote. AS-1's census measured
# this fault across 249 suites this morning; this is one of them, and it
# broke within three hours of DT-1 deploying, when AB-1, HM-4 and WM-1
# rode in together. See claude/as1_frozen_after_census_16_oct.md.
def as_dt1_left(name):
    p = os.path.join(ROOT, name)
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


wd = as_dt1_left('test_waiting_down.py')
ok('CONVERTED_N = %d' % CONVERTED_NOW in wd,
   'test_waiting_down counted %d converted suites when DT-1 left it'
   % CONVERTED_NOW)
co = as_dt1_left('test_code_only.py')
ok('ok(len(aliased) == %d,' % ALIAS_NOW in co,
   'test_code_only counted %d files aliasing code_only' % ALIAS_NOW)"""

DT_LF_WAS = """        ok(lf <= w_lf,
           '%-19s bare LF count did not grow: %d -> %d (CRLF %d -> %d)'
           % (p, w_lf, lf, w_crlf, crlf))"""

DT_LF_NOW = """        # THE STYLE, NOT THE COUNT. WM-1, 16 Oct 2026: this asserted
        # `lf <= w_lf`, and HM-4 broke it by legitimately adding eight
        # lines to home.html - a pure LF file, where every added line
        # raises the LF count. A count cannot tell a round that ADDED
        # lines from one that CONVERTED them. A CRLF file must not gain
        # bare LFs; an LF file must not gain CRLFs.
        was_crlf_file = w_crlf > w_lf
        held = (lf <= w_lf) if was_crlf_file else (crlf <= w_crlf)
        ok(held,
           '%-19s kept its %s line endings: CRLF %d -> %d, bare LF %d -> %d'
           % (p, 'CRLF' if was_crlf_file else 'LF',
              w_crlf, crlf, w_lf, lf))"""

# ---------------------------------------------------------- test_pd3.py
#
# A CONTROL CANNOT BE A RE-RENDER OF OLD TEXT AGAINST TODAY'S BASE.
#
# PD-3's second section opens with a control: at 390px the page really
# did have a control under 44px, else the round was aimed at nothing.
# It proves that by rendering the BACKUP's markup - and base LIVE.
#
# That control now fails, and the measurement says why. In the before
# render today:
#
#     select.form-control form-control-sm d-inline-block     44.0
#     button.btn action-secondary document-launcher-btn       50.0
#
# Nothing is under 43.5 any more. The button is 50 because LV-1 gave
# .btn.action-secondary a 44px floor below 768px THIS MORNING, and the
# select is exactly 44.0 from base's own control floor. The old page is
# being measured in a house it never lived in.
#
# WM-1 did not break this - LV-1 did, six hours ago - but WM-1 is the
# round in flight, and a red suite blocks his gate. So it carries the
# fix, and names the cause rather than quietly re-pinning a number.
#
# THE FIX IS TO MOVE THE HISTORICAL CLAIM INTO THE TEXT. "The page had
# no 44px floor of its own" is a fact about the backup's bytes and is
# true for ever. "The old markup still looks wrong today" is a fact
# about base, and base is not this round's to keep still. The live half
# - nothing under 44px NOW - is unchanged, because that one is a claim
# about today and a render is the right instrument for it. This is E19
# and E21 in one place; see claude/OUTSTANDING_MASTER_16_oct.md.
PD = 'test_pd3.py'

PD_WAS = """    small_was = {k: v for k, v in a['ctrl'].items() if v < 43.5}
    small_now = {k: v for k, v in b['ctrl'].items() if v < 43.5}
    ok(bool(small_was),
       'at 390px the page really did have a control under 44px',
       'it did not - then this half of the round is aimed at nothing')
    for k, v in sorted(small_was.items()):
        print('      was  %-52s %.1f' % (k[:52], v))"""

PD_NOW = """    small_was = {k: v for k, v in a['ctrl'].items() if v < 43.5}
    small_now = {k: v for k, v in b['ctrl'].items() if v < 43.5}
    # THE HISTORICAL CLAIM IS A TEXT FACT, NOT A RE-RENDER.
    #
    # WM-1, 16 Oct 2026. This used to assert bool(small_was) - that the
    # BACKUP's markup still measures under 44px today. It does not any
    # more, and the reason is not a fault: LV-1 gave .btn.action-secondary
    # a 44px floor below 768px this morning, so the old launcher button
    # now renders 50px, and base's own control floor puts the old select
    # at exactly 44.0. The old page is being measured in a house it never
    # lived in. A control that re-renders old text against today's base
    # measures today's base; see E19 and E21.
    #
    # So the before is asked of the BACKUP'S BYTES, which cannot move:
    # the page carried no 44px floor of its own, and the round gave it
    # one. The live half below is untouched - nothing under 44px NOW is a
    # claim about today, and a render is the right instrument for that.
    old_css = css_of(OLDRAW) if OLDRAW else ''
    ok(bool(old_css) and re.search(r'min-height:\\s*44px', old_css) is None,
       'the page carried NO 44px floor of its own before this round',
       'it already had one - then this half of the round was aimed at '
       'nothing')
    print('      the before render measures, lowest first:')
    for k, v in sorted(a['ctrl'].items(), key=lambda kv: kv[1])[:4]:
        print('      was  %-52s %.1f' % (k[:52], v))
    print('      (44.0 and up today because LV-1 floored '
          '.btn.action-secondary')
    print('       at 44px below 768px - which is base moving, not this '
          'page)')"""

SENT_ANCHOR = """    # -------------------------------------------- HL-1, 12 Oct 2026"""
SENT_NEW = """    # ------------------------------------------------- WM-1, 16 Oct 2026
    # Demetri, testing Administration: the member count should be
    # clickable and show the names.
    @{ File = 'pages\\templates\\workspace_management.html'; Text = 'alv-pop-trigger'; What = 'WM-1: the member count opens the names' },
    @{ File = 'pages\\templates\\workspace_management.html'; Text = 'ws-members" title='; Absent = $true; Code = $true; What = 'WM-1: and the hover-only tooltip is gone with it' },
    # -------------------------------------------- HL-1, 12 Oct 2026"""


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    page = alv_tree.path_of(PAGE)

    # ---------------------------------------------------------------- 0
    if 'alv-pop-trigger' in code_only(read(page)):
        print('WM-1  already applied - the member count is a control.')
        return 0

    out = {}

    # ---------------------------------------------------------------- 1
    # THE COMPONENT IS READ, NOT REMEMBERED, and so is the page that
    # already uses it.
    base = code_only(read(alv_tree.path_of('base.html')))
    # The name ALV POP v1 is NOT asked for here: it lives in a CSS comment,
    # and code_only strips comments inside <style>. A gate asks for the
    # rules, never for the prose that labels them.
    for need, what in (('.alv-pop-trigger', 'the trigger'),
                       ('.alv-pop {', 'the panel'),
                       ('.alv-pop.show', 'the open state'),
                       ('.alv-pop-list', 'the list'),
                       ('.alv-pop-empty', 'the empty state')):
        if need not in base:
            refuse('base.html no longer carries %s (%s)' % (need, what))
    model = code_only(read(alv_tree.path_of(MODEL)))
    for need in ('alv-pop-trigger', 'alv-pop-list', 'alv-pop-empty'):
        if need not in model:
            refuse('%s no longer uses %s, so this round is copying a cell '
                   'that has changed' % (MODEL, need))

    # The view must still be preparing the list this cell reads.
    vp = os.path.join(root, VIEW)
    v = read(vp)
    if 'ws.member_list = list(' not in v:
        refuse('%s no longer builds member_list, so the popup would be '
               'empty on every row' % VIEW)

    # ---------------------------------------------------------------- 2
    s = read(page)
    s = swap(s, CELL_WAS, CELL_NOW, '%s (the members cell)' % PAGE)
    out[page] = s

    # The comment only - no code moves in the view.
    v2 = swap(v, VIEW_WAS, VIEW_NOW, '%s (the comment)' % VIEW)
    code_was = '\n'.join(ln for ln in v.split('\n')
                         if not ln.strip().startswith('#'))
    code_now = '\n'.join(ln for ln in v2.split('\n')
                         if not ln.strip().startswith('#'))
    if code_was != code_now:
        refuse('%s: the round changed CODE in the view, and it may only '
               'change the comment' % VIEW)
    out[vp] = v2

    # ------------------------------------------------ the suite we break
    dtp = os.path.join(root, DT)
    d = read(dtp)
    if 'from alv_rounds import as_left_by' not in d:
        refuse('%s does not import as_left_by, so re-pointing its counters '
               'would break it instead of fixing it' % DT)
    d = swap(d, DT_COUNT_WAS, DT_COUNT_NOW, '%s (the shared counters)' % DT)
    d = swap(d, DT_LF_WAS, DT_LF_NOW, '%s (the line-ending check)' % DT)
    try:
        import ast
        ast.parse(d)
    except SyntaxError as e:
        refuse('%s would no longer parse - %s' % (DT, e))
    if d.count('as_dt1_left(') != 3:
        refuse('%s: %d use(s) of as_dt1_left, expected the helper and its '
               'two readers' % (DT, d.count('as_dt1_left(')))
    out[dtp] = d

    # ---------------------------------- the suite LV-1 broke this morning
    pdp = os.path.join(root, PD)
    q = read(pdp)
    if 'OLDRAW' not in q or 'def css_of' not in q:
        refuse('%s does not have OLDRAW and css_of, which the honest '
               'control is built from' % PD)
    q = swap(q, PD_WAS, PD_NOW, '%s (the 44px control)' % PD)
    try:
        import ast
        ast.parse(q)
    except SyntaxError as e:
        refuse('%s would no longer parse - %s' % (PD, e))
    if 'ok(bool(small_was),' in q:
        refuse('%s still asserts the old defect by re-render' % PD)
    if 'ok(not small_now,' not in q:
        refuse('%s lost the LIVE half of the claim, which is the half a '
               'render is right for' % PD)
    out[pdp] = q

    # ---------------------------------------------------------------- 3
    b = code_only(s)
    if b.count('alv-pop-trigger') != 1:
        refuse('%s: %d trigger(s), expected 1'
               % (PAGE, b.count('alv-pop-trigger')))
    # ONE ELEMENT, NOT TWO. The two classes must be on the same span -
    # the whole point of the merge - and the tooltip must be gone from it.
    m = re.search(r'<span class="([^"]*\bws-members\b[^"]*)"([^>]*)>', b)
    if not m:
        refuse('%s: the members pill is no longer a span with ws-members on it'
               % PAGE)
    if 'alv-pop-trigger' not in m.group(1):
        refuse('%s: ws-members and alv-pop-trigger are on different elements, '
               'which draws a second rounded box outside the pill' % PAGE)
    if 'title=' in m.group(2):
        refuse('%s: the hover tooltip is still on the control' % PAGE)
    if b.count('alv-pop-list') != 1 or b.count('alv-pop-empty') != 1:
        refuse('%s: the popup is missing its list or its empty state' % PAGE)
    if 'member_list' not in b or 'member_count' not in b:
        refuse('%s: the cell lost the data it is built from' % PAGE)
    # NO NEW QUERY. The round must not reach past member_list.
    if re.search(r'\{%\s*for\s+\w+\s+in\s+ws\.members\b', b):
        refuse('%s: the template iterates ws.members directly, which is a '
               'query per row - member_list is the one the view prepared'
               % PAGE)
    # EVERY {# #} CLOSES ON ITS OWN LINE.
    bad = [i + 1 for i, ln in enumerate(s.split('\n'))
           if ln.count('{#') != ln.count('#}')]
    if bad:
        refuse('%s: a Django comment outlives its line, at %s' % (PAGE, bad))
    # LINE ENDINGS - the style, not the count.
    was = read(page)
    w_crlf, n_crlf = was.count('\r\n'), s.count('\r\n')
    w_lf, n_lf = was.count('\n') - w_crlf, s.count('\n') - n_crlf
    if (w_crlf > w_lf and n_lf > w_lf) or (w_lf >= w_crlf and n_crlf > w_crlf):
        refuse('%s: the file gained a line ending it did not have' % PAGE)

    # ---------------------------------------------------------------- 4
    p = os.path.join(root, PS1)
    t = read(p)
    if ME in t:
        refuse('%s already lists this round' % PS1)
    t = swap(t, SUITE_WAS, SUITE_NOW, '%s (the suite list)' % PS1)
    t = swap(t, SENT_ANCHOR, SENT_NEW, '%s (the gate rows)' % PS1)
    out[p] = t

    p = os.path.join(root, TREE)
    out[p] = swap(read(p), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), ROUNDS_WAS, ROUNDS_NOW, '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, WD)
    out[p] = bump(read(p), 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'WM-1, 16 Oct 2026 - this round own suite. The '
                  'workspace member count becomes a control, after '
                  'Demetri asked for it to be clickable and show the '
                  'names.', '%s (the converted count)' % WD)

    p = os.path.join(root, CO)
    t = read(p)
    t = bump(t, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
             'WM-1, 16 Oct 2026 - this round own patcher and suite',
             '%s (the alias count)' % CO)
    t = swap(t, "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_WAS, ALIAS_S_WAS),
             "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_NOW, ALIAS_S_NOW),
             '%s (the alias split)' % CO)
    out[p] = t

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('WM-1 --check  %d file(s) would change' % len(out))
        for q in sorted(out):
            print('   %s' % os.path.relpath(q, root))
        return 0

    for q, t in sorted(out.items()):
        backup(q)
        write(q, t)

    print('WM-1 applied.')
    print('   the member count opens the names, on ALV POP v1')
    print('   the title= tooltip goes with it - a hover is not a control,')
    print('         and does not exist on a phone')
    print('   no new query: ws.member_list was already select_related')
    print('         and already ordered by username')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
