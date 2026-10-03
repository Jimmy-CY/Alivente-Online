# -*- coding: utf-8 -*-
"""SG-2 - BUDGET / ACTUALS BECOMES A SEGMENTED CONTROL

The last hand-rolled segmented control in the tree, and the one that has
been on the outstanding list longest:

    finance_pl_act's Budget/Actuals pair - btn-info / btn-outline-info
    with no house role, a hand-rolled segmented control. base has had
    ALV-SEG v1 since 2 Sep for exactly this.

==========================================================================
WHAT IT RENDERS AS TODAY, WHICH IS NOT WHAT THE STYLESHEET SUGGESTS
==========================================================================
    <a class="btn {% if view_mode == 'budget' %}btn-info
                  {% else %}btn-outline-info{% endif %}">

The SELECTED half is teal, because the page carries a local rule
overriding Bootstrap's .btn-info to #0e7c8b. The UNSELECTED half has no
local rule at all, so it is Bootstrap's raw .btn-outline-info - #17a2b8,
a blue-cyan that appears nowhere in the palette and that nobody chose.

Reading the stylesheet you would think this control was house-coloured.
Half of it is; the other half is whatever Bootstrap shipped.

==========================================================================
IT IS THE SAME CONTROL MC-1 AND UC-2 ALREADY CONVERTED
==========================================================================
Budget and Actuals are two views of one page - which is what .alv-seg is
for, in its own words: "a segment here is a PAGE-level choice, worn in an
action bar ... it is not a verb you press to make something happen; it is
which view you are looking at."

These are LINKS, each carrying the whole query string, so the current one
is marked aria-current="page" - the same marking MC-1 used for the
List/Calendar switch. UC-2's scope buttons use aria-pressed because they
are buttons that do not navigate. base fills either.

WHAT GOES: the .btn-group wrapper, .pl-view-toggle (which never had a
rule of its own), both btn-info/btn-outline-info branches, and the local
.btn-info rule and its hover - which become dead the moment the markup
stops asking for them. #0e7c8b leaves with them, as a literal; the
control is var(--alv-accent) now, which is the same colour said once in
the place that owns it.

THE LINKS THEMSELVES DO NOT CHANGE. Each still carries year, view,
single and every selected property, in that order. A control that
quietly dropped a query parameter while being restyled would lose the
reader's property selection on every toggle, and the gate below compares
both hrefs against the backup character for character.

Backups: .bak_plseg. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_plseg'
ROOT = os.getcwd()
CRLF = {}
TPL = os.path.join(ROOT, 'pages', 'templates', 'finance_pl_act.html')
# THE EIGHTH, FOUND BY THIS ROUND'S OWN LAST GATE - Demetri agreed on
# 3 Oct to take it in the same bundle. Property Assets carries the
# identical control with the identical defect, and every census of
# btn-info in this tree has missed it for a month because the class name
# is ASSEMBLED ACROSS A TEMPLATE TAG:
#
#     class="btn btn-{% if group_by == 'category' %}info{% else %}outline-info{% endif %}"
#
# There is no string "btn-info" anywhere in that file. Twenty-second time
# this week that an instrument was asked for a substring when the thing
# meant was a construct - and the first time the construct was split by
# the template language itself.
ASSETS = os.path.join(ROOT, 'pages', 'templates', 'property_assets.html')

QS = ("{% if single_mode %}&single=1{% endif %}"
      "{% if selected_properties %}&{% for prop_id in selected_properties %}"
      "properties={{ prop_id }}{% if not forloop.last %}&{% endif %}"
      "{% endfor %}{% endif %}")


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
            raise SystemExit('SG2: %s is not a byte copy' % bak)


# CO-1, 3 Oct 2026 - this was written out here, as it was in 46
# other files. It lives in alv_tree now, with the repair that
# stops `accept="image/*"` reading as a comment opener and hiding
# 94 lines of the Add Passport form from every gate in the tree.
import alv_tree
code_only = alv_tree.code_only


def swap(text, old, new, what):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(TPL):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('SG2: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('SG-2 - BUDGET / ACTUALS BECOMES A SEGMENT%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(TPL)
BEFORE = code_only(t.replace('\r\n', '\n'))

# THE PREMISE: the unselected half really has no local rule, so it really
# is Bootstrap's raw colour.
if 'alv-seg' not in BEFORE:
    if re.search(r'\.btn-outline-info\s*[,{]', BEFORE):
        raise SystemExit('SG2: the page DOES style .btn-outline-info - the '
                         'premise that the unselected half is Bootstrap raw '
                         'is wrong')
    print('  the page styles .btn-info and NOT .btn-outline-info - the '
          'unselected half is Bootstrap raw')

if 'alv-seg' in BEFORE:
    print('  finance_pl_act             already wears the seg')
else:
    t = swap(t, """    <!-- Budget / Actuals toggle -->
    <div class="btn-group pl-view-toggle" role="group" aria-label="Budget or Actuals">
        <a class="btn {%% if view_mode == 'budget' %%}btn-info{%% else %%}btn-outline-info{%% endif %%}"
           href="?year={{ selected_year }}&view=budget%s">
            Budget
        </a>
        <a class="btn {%% if view_mode == 'actuals' %%}btn-info{%% else %%}btn-outline-info{%% endif %%}"
           href="?year={{ selected_year }}&view=actuals%s">
            Actuals
        </a>
    </div>""" % (QS, QS),
             """    {# BUDGET / ACTUALS - SG-2, 3 Oct 2026. The last hand-rolled      #}
    {# segmented control in the tree, and the one longest on the       #}
    {# outstanding list. base has had ALV-SEG since 2 Sep for exactly  #}
    {# this: two views of one page, which is a PAGE-level choice and   #}
    {# not a verb you press.                                           #}
    {#                                                                 #}
    {# IT DID NOT LOOK LIKE A HOUSE CONTROL AND IT DID NOT LOOK LIKE A #}
    {# BOOTSTRAP ONE EITHER. The selected half was teal, from a local  #}
    {# rule overriding .btn-info; the unselected half had no local     #}
    {# rule at all, so it was Bootstrap's raw .btn-outline-info -      #}
    {# its own blue-cyan, in no palette, that nobody chose. Reading     #}
    {# the stylesheet you would think the whole control was house      #}
    {# coloured. Half of it was.                                       #}
    {#                                                                 #}
    {# aria-current, not a class: these are links, so this is the same #}
    {# marking MC-1 gave the List/Calendar switch. UC-2's scope        #}
    {# buttons use aria-pressed because they do not navigate.          #}
    <div class="alv-seg" role="group" aria-label="Budget or Actuals">
        <a href="?year={{ selected_year }}&view=budget%s"
           {%% if view_mode == 'budget' %%}aria-current="page"{%% endif %%}>
            Budget
        </a>
        <a href="?year={{ selected_year }}&view=actuals%s"
           {%% if view_mode == 'actuals' %%}aria-current="page"{%% endif %%}>
            Actuals
        </a>
    </div>""" % (QS, QS),
             'the Budget/Actuals toggle')

    t = swap(t, """.btn-info {
    background-color: #0e7c8b;
    color: white;
    border: 1px solid #0e7c8b;
    transition: all 0.3s ease;
    border-radius: 6px;
    font-weight: 500;
    padding: 8px 16px;
}

@media (hover: hover) and (pointer: fine) {
    .btn-info:hover {
        background-color: var(--alv-accent-ink);
        border-color: var(--alv-accent-ink);
        color: white;
        text-decoration: none;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
}""",
             """/* .btn-info AND ITS HOVER ARE GONE - SG-2, 3 Oct 2026. They existed
   only to repaint the Budget/Actuals pair, and that pair is .alv-seg
   now, so both rules became dead the moment the markup stopped asking
   for them. The literal #0e7c8b went with them: the control is
   var(--alv-accent), which is the same colour said once, in the place
   that owns it. */""",
             'the btn-info rules')

    if not CHECK:
        back_up(TPL, raw)
        write(TPL, t)
    print('  finance_pl_act             Budget/Actuals on .alv-seg, two '
          'dead rules swept')


# ==========================================================================
# THE EIGHTH - property_assets, same control, same defect.
# ==========================================================================
ta, rawa = read(ASSETS)
BEFORE_A = code_only(ta.replace('\r\n', '\n'))


def swap_a(text, old, new, what):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(ASSETS):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('SG2: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


if 'alv-seg' in BEFORE_A:
    print('  property_assets            already wears the seg')
else:
    ta = swap_a(ta, """        <div class="btn-group btn-group-sm view-toggle-group" role="group">
            <a href="?group_by=category{% if request.GET.next %}&next={{ request.GET.next }}{% endif %}"
               class="btn btn-{% if group_by == 'category' %}info{% else %}outline-info{% endif %}">
                <i class="fas fa-tag"></i> Category
            </a>
            <a href="?group_by=room{% if request.GET.next %}&next={{ request.GET.next }}{% endif %}"
               class="btn btn-{% if group_by == 'room' %}info{% else %}outline-info{% endif %}">
                <i class="fas fa-door-open"></i> Location/Room
            </a>
        </div>""",
             """        {# THE EIGHTH HAND-ROLLED SEGMENTED CONTROL - SG-2, 3 Oct 2026.  #}
        {# The same Budget/Actuals shape finance_pl_act had, and hidden   #}
        {# from every census of btn-info for a month because the class    #}
        {# name was ASSEMBLED ACROSS A TEMPLATE TAG: the literal "btn-"  #}
        {# was followed by a conditional choosing between "info" and     #}
        {# "outline-info", so the string "btn-info" never appeared in    #}
        {# this file at all and no search for it could ever match.       #}
        {# SG-2's own closing gate swept for the CONSTRUCT and found it. #}
        {#                                                                #}
        {# The syntax is NAMED here and not written - B-1c's rule. The    #}
        {# first draft of this note quoted the tags, which put a live     #}
        {# conditional inside a comment and moved this template's tag     #}
        {# census by one of each. test_entry_sections counts those to     #}
        {# notice a round orphaning a branch, and it duly noticed prose.  #}
        <div class="alv-seg" role="group" aria-label="Group assets by">
            <a href="?group_by=category{% if request.GET.next %}&next={{ request.GET.next }}{% endif %}"
               {% if group_by == 'category' %}aria-current="page"{% endif %}>
                <i class="fas fa-tag"></i> Category
            </a>
            <a href="?group_by=room{% if request.GET.next %}&next={{ request.GET.next }}{% endif %}"
               {% if group_by == 'room' %}aria-current="page"{% endif %}>
                <i class="fas fa-door-open"></i> Location/Room
            </a>
        </div>""",
             'the Group by toggle')

    ta = swap_a(ta, """.view-toggle-group .btn {
    padding: 6px 14px;
}
.view-toggle-group .btn i {
    margin-right: 4px;
}
""",
             """/* .view-toggle-group's two rules are gone - SG-2. base sizes .alv-seg
   and spaces its icons, so these could only disagree with it.
   .view-toggle-row and .view-toggle-label stay: they are the row and
   its "Group by:" caption, which base has no opinion about. */
""",
             'the toggle-group rules')

    ta = swap_a(ta, """    .view-toggle-group {
        width: 100%;
    }
    .view-toggle-group .btn {
        flex: 1;
    }
""", '', 'the toggle-group phone rules')

    if not CHECK:
        back_up(ASSETS, rawa)
        write(ASSETS, ta)
    print('  property_assets            Group by on .alv-seg, three dead '
          'rules swept')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
import alv_tree

NOW = read(TPL)[0]
CODE = code_only(NOW)
WAS = code_only(read(TPL + SUFFIX)[0])
BASE = code_only(open(alv_tree.path_of('base.html'), encoding='utf-8',
                      errors='replace').read())

# 1. ONE SEG, TWO HALVES, AND base FILLS THE CURRENT ONE.
if CODE.count('class="alv-seg"') != 1:
    raise SystemExit('SG2: %d segs, expected one'
                     % CODE.count('class="alv-seg"'))
seg = CODE[CODE.index('<div class="alv-seg"'):]
seg = seg[:seg.index('</div>')]
if len(re.findall(r'<a\s', seg)) != 2:
    raise SystemExit('SG2: %d halves, expected two' % len(re.findall(r'<a\s', seg)))
if seg.count('aria-current="page"') != 2:
    raise SystemExit('SG2: expected one conditional aria-current per half, '
                     'found %d' % seg.count('aria-current="page"'))
if '.alv-seg > [aria-current="page"]' not in BASE:
    raise SystemExit('SG2: base does not fill a current segment')
print('  one seg, two halves, each marked aria-current when it is the view')

# 2. THE OLD NAMES ARE GONE - MARKUP AND RULES.
for dead in ('btn-info', 'btn-outline-info', 'pl-view-toggle'):
    if re.search(r'\b%s\b' % dead, CODE):
        raise SystemExit('SG2: %s is still in the code' % dead)
print('  no btn-info, btn-outline-info or pl-view-toggle')

# 3. #0e7c8b LEFT WITH THEM - counted, because the page uses it elsewhere
#    and a claim that it is gone from the page would be claiming more than
#    this round did.
got = WAS.count('#0e7c8b') - CODE.count('#0e7c8b')
if got != 2:
    raise SystemExit('SG2: dropped %d uses of #0e7c8b, expected 2 (%d '
                     'before, %d after)'
                     % (got, WAS.count('#0e7c8b'), CODE.count('#0e7c8b')))
print('  #0e7c8b dropped twice; the %d still on the page are other rules'
      % CODE.count('#0e7c8b'))

# 4. THE LINKS DID NOT CHANGE. A control restyled into dropping a query
#    parameter would lose the reader's property selection on every
#    toggle, and look perfect doing it.
for view in ('budget', 'actuals'):
    want = '?year={{ selected_year }}&view=%s%s' % (view, QS)
    if CODE.count(want) != 1:
        raise SystemExit('SG2: the %s link is not the link it was' % view)
    if WAS.count(want) != 1:
        raise SystemExit('SG2: the %s link was not what this round read'
                         % view)
for part in ('single=1', 'properties={{ prop_id }}', 'forloop.last',
             'selected_year'):
    if CODE.count(part) != WAS.count(part):
        raise SystemExit('SG2: %r appears %d times, was %d'
                         % (part, CODE.count(part), WAS.count(part)))
print('  both links carry year, view, single and every selected property, '
      'exactly as before')

# 5. THE CONTROL: the unselected half really was Bootstrap raw.
if re.search(r'\.btn-outline-info\s*[,{]', WAS):
    raise SystemExit('SG2: the page did style it - the premise is wrong')
if '.btn-info {' not in WAS:
    raise SystemExit('SG2: the page did NOT style .btn-info - then the '
                     'selected half was not teal either and this round has '
                     'misread what it replaced')
print('  CONTROL: .btn-info was styled locally and .btn-outline-info was '
      'not - half house, half Bootstrap')

# 5b. AND THE EIGHTH, WHICH THIS ROUND ALSO TOOK.
A = code_only(read(ASSETS)[0])
AW = code_only(read(ASSETS + SUFFIX)[0])
if A.count('class="alv-seg"') != 1:
    raise SystemExit('SG2: property_assets has %d segs, expected one'
                     % A.count('class="alv-seg"'))
if re.search(r'\bview-toggle-group\b', A):
    raise SystemExit('SG2: .view-toggle-group survives in property_assets')
if "btn-{% if group_by" in A:
    raise SystemExit('SG2: the assembled class name is still there')
if "btn-{% if group_by" not in AW:
    raise SystemExit('SG2: property_assets never assembled its class across '
                     'a template tag - the premise of taking it is wrong')
# AND A CLAIM THIS ROUND IS NOT ENTITLED TO MAKE. btn-outline-info also
# dresses a camera-capture label further down the page, which this round
# never touched.
if 'btn-outline-info' not in A:
    raise SystemExit('SG2: btn-outline-info vanished from property_assets '
                     'entirely - this round owns the view toggle, not the '
                     'camera capture label')
for part in ('?group_by=category', '?group_by=room',
             'request.GET.next'):
    if A.count(part) != AW.count(part):
        raise SystemExit('SG2: property_assets link %r changed' % part)
print('  property_assets: one seg, the assembled class gone, both links '
      'unchanged, and the camera label left alone')

# 6. AND THE TREE NOW HAS ONE SEGMENTED CONTROL. Measured across both
#    roots, because "the last one" is a claim about everywhere.
hand = []
for rel in sorted(alv_tree.templates()):
    src = code_only(open(alv_tree.path_of(rel), encoding='utf-8',
                         errors='replace').read())
    # SWEEP FOR THE CONSTRUCT. The btn-group version of this census is
    # what missed property_assets; this one looks for a class attribute
    # that BUILDS a Bootstrap tone out of a conditional, whatever the
    # wrapper is called.
    if re.search(r'class="[^"]*btn-\{%\s*if', src) or re.search(
            r'class="[^"]*\{%\s*if[^"]*%\}(?:info|primary|secondary)\b',
            src):
        hand.append(rel)
print('  %d hand-rolled view toggles left in %d templates'
      % (len(hand), len(alv_tree.templates())))
for h in hand[:4]:
    print('    still hand-rolled: %s' % os.path.basename(h))

print('-' * 74)
print('  The stylesheet said teal and the browser said half teal, half')
print('  Bootstrap. A control nobody had ever decided the colour of.')
print('=' * 74)
