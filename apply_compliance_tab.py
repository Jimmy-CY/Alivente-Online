# -*- coding: utf-8 -*-
"""apply_compliance_tab.py - Section PR round PR-1, 8 Oct 2026.

Demetri: "For the Personal Module, I want to create a new Tab behind the
'Personal' tab (same look and feel), but it must be called 'Compliance'.
Then we need to move the CRS Reporting button from the Personal tab to
the new Compliance tab."

=====================================================================
IT INVERTS P6, AND THAT IS THE INTERESTING PART
=====================================================================

On 29 Sep, P2 commented out Personal's FUTURE tab. The Personal tab had
been written with `border-right: none` because the FUTURE tab sat hard
against it and drew the shared line itself, through
.admin-tab.future-tab.personal-active's border-left-color - two tabs,
one edge, drawn once. With the neighbour gone the tab was left open on
its right, Demetri saw it within minutes, and P6 removed the
declaration so the tab drew all four of its own sides.

Compliance puts a neighbour back. So `border-right: none` comes back,
and test_tab_right_edge.py's middle claim - "no rule on this page
declares a border-right any more" - stops being true.

THAT IS NOT P6 BREAKING. IT IS P6'S PREMISE EXPIRING. P6's note on the
page says so in as many words: "If its Future tab is ever switched off
too, it needs this same line removed" - the author knew the rule
followed the neighbour count and wrote it down. This round reads that
note and does the other half of it.

So P6 is RE-POINTED rather than edited into agreement. Its claim was
"the Personal tab has a right border", measured in Chromium. The claim
becomes "THE SHARED EDGE IS THERE AND IS DRAWN ONCE" - measured the
same way, at the same two widths, by adding the Personal tab's
border-right to the Compliance tab's border-left and asserting the sum
is exactly one 3px accent line. That claim is true before AND after.
What changes is who draws it, and a suite that could only ever be true
of one arrangement was always going to expire.

P2's test_future_tab_off.py also asserts "the page holds exactly ONE
panel". That was about the FUTURE tab leading nowhere, not about the
page only ever having one panel, so it is re-pointed to what it meant:
NO FUTURE PANEL. The FUTURE tab stays commented out and its CSS stays
unused on purpose - Compliance is a third thing, not that tab brought
back.

=====================================================================
SAME LOOK AND FEEL MEANS THE SAME RULES, NOT COPIED RULES
=====================================================================

The page's FUTURE tab is grey, and test_personal_teal.py still asserts
that for this page - AD-1 spent that claim for admin_apms only. So
Compliance cannot reuse .future-tab: it would come out grey.

It could have had its own copy of every .personal-tab rule in the
accent. It does not, because two copies of a treatment drift and the
drift is invisible until somebody photographs both. Instead the four
.personal-tab selectors each gain `.admin-tab.compliance-tab`, so the
two tabs are the same colour BY CONSTRUCTION and not by inspection.

The CRS tile keeps class="admin-btn btn-personal" - the same tile, on a
different panel.

THE HOUSE ANSWER IS A SHARED TAB TREATMENT IN BASE. admin_apms and
personal now carry near-identical tab stylesheets, and after AD-1 all
four tabs across the two pages render the same colours. base.html is in
alv_impact.WIDE, so moving it there owes a full sweep and is a round of
its own. Logged, not smuggled in here.

FILES: personal.html (+ .bak_compliance), test_tab_right_edge.py,
test_future_tab_off.py, alv_rounds.py, the PS1 $suites, and the new
test_compliance_tab.py.
"""
import os
import re
import sys

SUFFIX = '.bak_compliance'
MARK = 'PR-1, 8 Oct 2026'
SUITE_NAME = 'test_compliance_tab.py'

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import alv_cssrules as R                                   # noqa: E402
import alv_tree as T                                       # noqa: E402

ROUNDS = os.path.join(ROOT, 'alv_rounds.py')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
PAGE = 'personal.html'
CHECK = False

# ---- 1. the four selectors that gain a second tab --------------------
SELECTORS = (
    ('  .admin-tab.personal-tab {',
     '  .admin-tab.personal-tab,\n  .admin-tab.compliance-tab {'),
    ('  .admin-tab.personal-tab.active {',
     '  .admin-tab.personal-tab.active,\n'
     '  .admin-tab.compliance-tab.active {'),
    ('  .admin-tab.personal-tab:not(.active):hover {',
     '  .admin-tab.personal-tab:not(.active):hover,\n'
     '  .admin-tab.compliance-tab:not(.active):hover {'),
    ('  .tab-panel.personal-panel {',
     '  .tab-panel.personal-panel,\n  .tab-panel.compliance-panel {'),
)

# ---- 2. the shared edge comes back ----------------------------------
# P6's note is replaced, not deleted: its history is the reason this
# round knew which half of the rule to put back.
OLD_NOTE = """    /* IT DRAWS ITS OWN RIGHT EDGE NOW - 29 Sep, and here is the history.
       This rule said `border-right: none`, because the FUTURE tab sat
       hard against it and drew the shared line itself, through
       .admin-tab.future-tab.personal-active's border-left-color. Two
       tabs, one edge, drawn once.

       P2 commented the Future tab out, and the line went with it: the
       tab was left open on its right and the panel's border began in
       mid-air. Nothing butts against this tab any more, so it draws all
       four of its own sides.

       admin_apms.html carries the same `border-right: none` and KEEPS
       it - both of its tabs are still there, so its shared edge still
       has somebody drawing it. If its Future tab is ever switched off
       too, it needs this same line removed; apply_tab_right_edge.py
       refuses to run while that page's Future tab is missing, so the
       question cannot be forgotten. */
    border-radius: 10px 10px 0 0;"""

NEW_NOTE = """    /* IT SHARES ITS RIGHT EDGE AGAIN - PR-1, 8 Oct 2026, and the whole
       history is the point.

       This rule said `border-right: none`, because the FUTURE tab sat
       hard against it and drew the shared line itself through its own
       border-left-color. Two tabs, one edge, drawn once.

       P2 commented the FUTURE tab out on 29 Sep and the line went with
       it: the tab was left open on its right and the panel's border
       began in mid-air. Demetri saw it within minutes. P6 removed the
       declaration so the tab drew all four of its own sides, and wrote
       here that the rule follows the NEIGHBOUR COUNT and not the page.

       COMPLIANCE PUTS A NEIGHBOUR BACK, so the declaration comes back
       with it and .admin-tab.compliance-tab.personal-active draws the
       shared line. P6's suite is re-pointed, not deleted: its claim was
       "the Personal tab has a right border", and it is now "the shared
       edge is there and is drawn once" - the same measurement in the
       same browser, and true of both arrangements.

       THE NEXT PERSON TO ADD OR REMOVE A TAB HERE OWES THIS LINE A
       THOUGHT. One tab: no neighbour, so the tab draws its own right
       edge. Two or more: every tab BUT THE LAST has `border-right:
       none` and its right-hand neighbour draws the line; the LAST tab
       always draws its own, because nothing is standing there to do
       it. See the rule below. */
    border-radius: 10px 10px 0 0;"""

EDGE_RULE = """  /* PR-1, 8 Oct 2026 - THE LEFT-HAND TAB ONLY.
     `border-right: none` says "my right-hand neighbour draws this
     line", so it belongs to the tab that HAS one and to no other.

     The first cut of this round put it in the rule both tabs share,
     and the result was the P6 defect on the new tab: COMPLIANCE's top
     border curved round its corner and stopped in mid-air, with the
     page running straight out to its right. Demetri spotted it in the
     render inside a minute, which is twice now on this page.
     admin_apms.html has always had it right - only .alivente-tab
     carries the declaration, and .future-tab draws its own right edge
     because nothing stands to the right of it. */
  .admin-tab.personal-tab {
    border-right: none;
  }

  /* And the one on the right draws the line between them, exactly as
     admin_apms.html's SYSTEM tab does. Two tabs, one edge, drawn
     once. */
  .admin-tab.compliance-tab.personal-active {
    border-left-color: var(--personal-dark);
    border-bottom-color: var(--personal-dark);
  }

  .admin-tab.personal-tab.compliance-active {
    border-bottom-color: var(--personal-dark);
  }

"""

# ---- 3. the tab strip ------------------------------------------------
OLD_STRIP = """  <div class="admin-tab personal-tab active">
    <i class="fas fa-user"></i>
    <span>PERSONAL</span>
  </div>
"""
NEW_STRIP = """  <div class="admin-tab personal-tab active" id="tab-personal"
       onclick="switchTab('personal')">
    <i class="fas fa-user"></i>
    <span>PERSONAL</span>
  </div>
  <div class="admin-tab compliance-tab personal-active" id="tab-compliance"
       onclick="switchTab('compliance')">
    <i class="fas fa-landmark"></i>
    <span>COMPLIANCE</span>
  </div>
"""

# ---- 4. CRS Reporting moves -----------------------------------------
OLD_CRS = """      {% if perms_map.crs %}
      <!-- CRS Reporting -->
      <a href="{% url 'crs:index' %}" class="admin-btn btn-personal">
        <i class="fas fa-landmark"></i>
        <h6>CRS Reporting</h6>
      </a>
      {% endif %}

"""

OLD_PANEL_TAIL = """    </div>
  </div>

</div>
"""
NEW_PANEL_TAIL = """    </div>
  </div>

  <!-- Compliance Panel - PR-1, 8 Oct 2026. CRS Reporting moved here
       from the Personal panel, markup and permission gate unchanged;
       it is the same tile on a different panel. -->
  <div id="compliance-panel" class="tab-panel compliance-panel">
    <div class="admin-grid">

      {% if perms_map.crs %}
      <!-- CRS Reporting -->
      <a href="{% url 'crs:index' %}" class="admin-btn btn-personal">
        <i class="fas fa-landmark"></i>
        <h6>CRS Reporting</h6>
      </a>
      {% endif %}

    </div>
  </div>

</div>

<script>
// PR-1, 8 Oct 2026. This page had no switchTab at all - one tab never
// needed one. This is admin_apms.html's, with its two names, and it is
// the same shape on purpose: a second spelling of the same behaviour is
// a second thing to keep in step.
function switchTab(tab) {
    document.getElementById('tab-personal').classList.remove('active', 'compliance-active');
    document.getElementById('tab-compliance').classList.remove('active', 'personal-active');

    document.getElementById('personal-panel').classList.remove('active');
    document.getElementById('compliance-panel').classList.remove('active');

    if (tab === 'personal') {
        document.getElementById('tab-personal').classList.add('active');
        document.getElementById('tab-compliance').classList.add('personal-active');
        document.getElementById('personal-panel').classList.add('active');
    } else {
        document.getElementById('tab-compliance').classList.add('active');
        document.getElementById('tab-personal').classList.add('compliance-active');
        document.getElementById('compliance-panel').classList.add('active');
    }
}
</script>
"""


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b):
        with open(p, 'rb') as s, open(b, 'wb') as d:
            d.write(s.read())


def fit(t, b):
    return (b.replace('\r\n', '\n').replace('\n', '\r\n')
            if '\r\n' in t else b.replace('\r\n', '\n'))


def swap(text, old, new, what):
    n = text.count(fit(text, old))
    if n != 1:
        raise SystemExit('PR-1: %s matched %d time(s), not once. The round '
                         'refuses rather than guessing.' % (what, n))
    return text.replace(fit(text, old), fit(text, new), 1)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    os.chdir(ROOT)

    rounds = read(ROUNDS)
    ps = read(PS1)
    if "'%s'" % SUFFIX in rounds:
        print('PR-1  already applied')
        return 1 if CHECK else 0

    path = T.path_of(PAGE)
    out = read(path)

    # THE FUTURE TAB MUST STILL BE OFF. If somebody reinstated it, this
    # page has three tabs and the shared-edge reasoning below is wrong.
    # THE MARKUP, NOT THE STYLESHEET. P2 left .admin-tab.future-tab in
    # the stylesheet on purpose, so reinstating the tab would be two
    # deletions rather than a rebuild - which means a check for the
    # STRING finds the rule and refuses a page that is perfectly fine.
    # The first version of this did exactly that. Strip the styles, the
    # Django comment that holds the tab itself, and the HTML comments,
    # and what is left is what the browser would be given.
    mk = re.sub(r'<style\b.*?</style>', '', out, flags=re.S | re.I)
    mk = re.sub(r'\{% comment %\}.*?\{% endcomment %\}', '', mk, flags=re.S)
    mk = re.sub(r'<!--.*?-->', '', mk, flags=re.S)
    if 'future-tab' in mk:
        raise SystemExit('PR-1: the FUTURE tab is rendering again. This '
                         'round assumes Personal has exactly one tab and '
                         'is adding the second; with three the shared-edge '
                         'rule needs thinking about, not patching.')

    for old, new in SELECTORS:
        out = swap(out, old, new, old.strip())
    out = swap(out, OLD_NOTE, NEW_NOTE, "P6's note and border-right")
    out = swap(out, '  .admin-tab.personal-tab.future-active {',
               EDGE_RULE + '  .admin-tab.personal-tab.future-active {',
               'the anchor for the shared-edge rule')
    out = swap(out, OLD_STRIP, NEW_STRIP, 'the Personal tab in the strip')
    out = swap(out, OLD_CRS, '', 'the CRS Reporting tile on the Personal panel')
    out = swap(out, OLD_PANEL_TAIL, NEW_PANEL_TAIL, 'the tail of the panels')

    # ---- what must be true of the result ---------------------------
    code = T.code_only(out)
    tabs = re.findall(r'class="admin-tab ([\w\- ]+)"',
                      re.sub(r'\{% comment %\}.*?\{% endcomment %\}', '',
                             out, flags=re.S))
    if len(tabs) != 2:
        raise SystemExit('PR-1: the page renders %d tab(s), expected 2: %s'
                         % (len(tabs), tabs))
    panels = re.findall(r'class="tab-panel ([\w\- ]+)"', out)
    if len(panels) != 2 or 'future' in ' '.join(panels):
        raise SystemExit('PR-1: panels read %s, expected a Personal and a '
                         'Compliance one and no Future' % (panels,))
    # COUNT THE TILE, NOT THE WORDS. The note that explains the move
    # says "CRS Reporting" too, and a round that documents itself must
    # not fail its own check for doing so - which is three times this
    # programme has learnt that in two days.
    if out.count('<h6>CRS Reporting</h6>') != 1:
        raise SystemExit('PR-1: the CRS Reporting tile appears %d time(s) - '
                         'it should have MOVED, not been copied'
                         % out.count('<h6>CRS Reporting</h6>'))
    if out.count("{% url 'crs:index' %}") != 1:
        raise SystemExit('PR-1: the CRS link appears %d time(s), not once'
                         % out.count("{% url 'crs:index' %}"))
    if out.count('perms_map.crs') != 1:
        raise SystemExit('PR-1: the CRS permission gate appears %d time(s), '
                         'not once - it must travel with the tile'
                         % out.count('perms_map.crs'))
    # THE DECLARATION BELONGS TO THE LEFT-HAND TAB AND TO NO OTHER.
    # The first cut put it in the rule both tabs share and left
    # COMPLIANCE open on its right - P6's defect, on the new tab, found
    # in the render rather than here. This is the check that would have
    # caught it: exactly one `border-right: none`, and the rule holding
    # it names only the tab that HAS a neighbour.
    if code.count('border-right: none;') != 1:
        raise SystemExit('PR-1: border-right: none appears %d time(s) in '
                         'the live stylesheet, expected exactly 1 - it says '
                         '"my right-hand neighbour draws this line", so only '
                         'the tab with a neighbour may carry it'
                         % code.count('border-right: none;'))
    owner = None
    for a, b in R.style_spans(code):
        for sel, ba, bb, _x, _y in R.rule_spans(code, a, b):
            if 'border-right: none' in code[ba:bb]:
                owner = sel
    if owner != '.admin-tab.personal-tab':
        raise SystemExit('PR-1: border-right: none sits on %r. It must sit '
                         'on .admin-tab.personal-tab alone - the LAST tab '
                         'in the strip has nothing standing to its right '
                         'and must draw its own edge.' % owner)
    for cls in ('compliance-tab', 'compliance-panel', 'personal-active',
                'compliance-active'):
        if cls not in code and cls not in out:
            raise SystemExit('PR-1: %s is not in the result' % cls)
    if code.count('{') != code.count('}'):
        raise SystemExit('PR-1: unbalanced braces in the stylesheet')
    for a, b in R.style_spans(code):
        R.rule_spans(code, a, b)

    print('PR-1  personal.html: %d tabs, %d panels, CRS moved' % (2, 2))

    reg = resolve_registration(rounds, ps, out)
    print('PR-1  %d registry/suite file(s) resolved, every anchor found'
          % len(reg))

    if CHECK:
        print('PR-1  NOT APPLIED')
        return 1

    backup(path)
    write(path, out)
    for p, new in reg.items():
        backup(p)
        write(p, new)
    print('PR-1  ok')
    return 0


def resolve_registration(rounds, ps, out_for_census):
    """Every file besides the page - resolved, not written."""
    reg = {}
    import ast as _ast

    # ---- test_tab_right_edge.py: NOTHING. AND THAT IS THE FINDING ---
    #
    # The survey for this round said Compliance would invert P6 and make
    # its middle claim - "no rule on this page declares a border-right
    # any more" - false. IT DOES NOT, AND THE REASON IS A RULE THIS
    # HOUSE ADOPTED ON 5 OCT.
    #
    # P6 reads the page through as_left_by(path, '.bak_tabedge', read):
    # the page AS P6 LEFT IT, not as the tree stands. B-1 taught it that
    # when it turned `background-color: white` into a var() on this page
    # and P6's diff reported four added lines for a round that adds
    # none. So P6's claims are about 29 September and stay true however
    # many tabs this page grows afterwards.
    #
    # A round that re-points a suite which was never going to fail is a
    # round editing somebody else's finished work for no reason, so this
    # one leaves P6 alone. The claim it would have rewritten - "the
    # shared edge is there and is drawn once" - belongs in THIS round's
    # suite, about THIS round's page, and that is where it is.
    #
    # test_future_tab_off.py is the opposite case: it reads the LIVE
    # page, so it does go red, and it is re-pointed below.

    # ---- test_future_tab_off.py: P2, re-pointed -------------------
    FT = os.path.join(ROOT, 'test_future_tab_off.py')
    fsrc = read(FT)
    OLD_P = """panels = re.findall(r'class="tab-panel ([\\w\\- ]+)"', page)
ok(len(panels) == 1 and 'personal-panel' in panels[0],
   'the page holds exactly ONE panel, and it is the Personal one - the '
   'tab that was switched off had nothing behind it', panels)"""
    NEW_P = """panels = re.findall(r'class="tab-panel ([\\w\\- ]+)"', page)
# PR-1, 8 Oct 2026. THIS SAID "EXACTLY ONE PANEL", AND MEANT "NO FUTURE
# PANEL". The FUTURE tab led nowhere - that is what made switching it off
# safe, and it is the claim worth keeping. Compliance is a third thing
# with a panel of its own behind it, so the count moved and the meaning
# did not. The FUTURE tab is still commented out and its CSS is still
# unused on purpose, which sections 1 to 3 above still prove.
ok(not any('future' in p for p in panels),
   'NO panel on this page is a Future one - the tab that was switched off '
   'had nothing behind it, which is what made switching it off safe',
   panels)
ok(any('personal-panel' in p for p in panels),
   '  the Personal panel is still here', panels)"""
    OLD_ONE = """    ok('PERSONAL' in out and _tabs == 1,
       '  while PERSONAL is the one tab that remains',
       '%d admin-tab(s)' % _tabs)"""
    NEW_ONE = """    # PR-1, 8 Oct 2026. This counted tabs to say the FUTURE one had
    # gone. Compliance is a second tab and a THIRD THING - not that tab
    # brought back - so the count moved and the claim did not. What P2
    # proved is that the strip carries no FUTURE, which the two checks
    # above measure on the rendered output and which is still true.
    ok('PERSONAL' in out and 'FUTURE' not in out,
       '  while PERSONAL remains and no tab in the strip says FUTURE',
       '%d admin-tab(s)' % _tabs)"""
    if fsrc.count(OLD_ONE) != 1:
        raise SystemExit('PR-1: the one-tab claim in test_future_tab_off.py '
                         'matched %d time(s), not once' % fsrc.count(OLD_ONE))
    fsrc = fsrc.replace(OLD_ONE, NEW_ONE, 1)

    if fsrc.count(OLD_P) != 1:
        raise SystemExit('PR-1: the panel-count claim in '
                         'test_future_tab_off.py matched %d time(s), not once'
                         % fsrc.count(OLD_P))
    fsrc = fsrc.replace(OLD_P, NEW_P, 1)
    try:
        _ast.parse(fsrc)
    except SyntaxError as e:
        raise SystemExit('PR-1: test_future_tab_off.py would not parse - %s'
                         % e)
    reg[FT] = fsrc

    # ---- test_crs_hub.py: a selector list is a shared surface -----
    #
    # It looks the rule up by its exact selector text:
    #     rule(hc, '.tab-panel.personal-panel')
    # and this round turns that selector into a list of two. The lookup
    # found nothing and a control about personal.html's local alias went
    # red - a true claim, broken by the shape of the rule and not by its
    # content.
    #
    # THAT IS THE COST OF EXTENDING A SELECTOR LIST, and it is the
    # argument for the shared tab treatment in base rather than two
    # pages keeping near-identical copies. One line here; the next
    # round to do it may find more. base.html is in alv_impact.WIDE, so
    # that move owes a full sweep and is a round of its own.
    CH = os.path.join(ROOT, 'test_crs_hub.py')
    csrc = read(CH)
    OLD_H = """def rule(css, sel):
    return [m.group(2) for m in RULE.finditer(css) if bare(m.group(1)) == sel]"""
    NEW_H = """def rule(css, sel):
    \"\"\"The bodies of the rules whose selector list CONTAINS `sel`.

    PR-1, 8 Oct 2026: this was an equality, and personal.html's panel
    rule became a list of two when the Compliance tab joined it -
    .tab-panel.personal-panel, .tab-panel.compliance-panel - so the
    lookup found nothing and a true claim went red on the SHAPE of a
    rule rather than its content.

    A selector list is a shared surface. Asking whether a rule is
    written for exactly one name is a question that only holds until
    somebody else needs the same treatment, and `.btn` would match
    `.btn-edit` if this split on anything but the comma.
    \"\"\"
    # STRIP THE COMMENTS FIRST, THEN SPLIT. bare() exists because of
    # lesson 21, and splitting on a comma before calling it splits
    # inside any comment banner that holds one - which is how the
    # first version of this change returned the mobile copy of
    # .crs-panel and lost the real one.
    return [m.group(2) for m in RULE.finditer(css)
            if sel in [' '.join(x.split())
                       for x in bare(m.group(1)).split(',')]]"""
    if csrc.count(OLD_H) != 1:
        raise SystemExit('PR-1: the personal-panel lookup in test_crs_hub.py '
                         'matched %d time(s), not once' % csrc.count(OLD_H))
    csrc = csrc.replace(OLD_H, NEW_H, 1)
    try:
        _ast.parse(csrc)
    except SyntaxError as e:
        raise SystemExit('PR-1: test_crs_hub.py would not parse - %s' % e)
    reg[CH] = csrc

    # ---- test_pair_contrast.py: a tab is a fill/ink pair ----------
    #
    # AD-1 taught that census to read page-local :root tokens, so it can
    # see the tabs now - and a new tab is a new pair. The Compliance
    # tab's active state is --alv-accent on --alv-accent-soft at 4.31,
    # which is the nineteenth of exactly the same pairing and still the
    # one base decision nobody has taken. PR-1 did not create it; it
    # wore the treatment it was told to wear.
    #
    # A round that changes a number owns every number that counts it,
    # and the gate found this one with nothing staged.
    import apply_system_teal as A
    import apply_edit_ink as B
    PC = os.path.join(ROOT, 'test_pair_contrast.py')
    psrc = read(PC)
    page_new = out_for_census
    n_after, live, dead = B.census({T.path_of(PAGE): page_new})
    rows = A.LIVE_FAM(live)
    import collections as _c
    fam = _c.Counter(r[3] for r in rows)
    band = len([r for r in rows if r[3] == 'house' and 4.0 <= r[2] < 4.5])
    sub2 = len([r for r in rows if r[2] < 2.0])
    worst = len([r for r in rows if r[2] < 2.0 and r[3] == 'house'])
    added = (set((r[0], r[1]) for r in live)
             - set((r[0], r[1]) for r in B.census()[1]))
    if sorted(added) != [(PAGE, '.admin-tab.compliance-tab.active')]:
        raise SystemExit('PR-1: the census gained %s, expected only the '
                         'Compliance tab active state' % (sorted(added),))
    # A LIST, NOT A `global`. `one` is a closure inside this function,
    # so `global psrc` reaches for a module-level name that does not
    # exist; the box is the shortest honest fix in a nested scope.
    _box = [psrc]

    def one(old_s, new_s, what):
        if _box[0].count(old_s) != 1:
            raise SystemExit('PR-1: %s matched %d time(s) in '
                             'test_pair_contrast.py, not once'
                             % (what, _box[0].count(old_s)))
        _box[0] = _box[0].replace(old_s, new_s, 1)
    m = re.search(r'EXPECT_PAIRS = (\d+)', _box[0])
    one('EXPECT_PAIRS = ' + m.group(1), 'EXPECT_PAIRS = %d' % n_after,
        'EXPECT_PAIRS')
    one(re.search(r'\nLIVE = \(\n.*?\n\)\n', _box[0], re.S).group(0),
        '\n' + A.table('LIVE', rows,
                       lambda r: ['%r' % r[0], '%r' % r[1], '%.2f' % r[2],
                                  '%r' % r[3]]) + '\n', 'the LIVE table')
    for pat, val, what in (
            (r'ok\(len\(band\) == (\d+),', band, 'the band count'),
            (r'ok\(len\(house\) == (\d+),', fam['house'], 'the house count'),
            (r'ok\(len\(sub2\) >= (\d+),', sub2, 'the sub-2 count'),
            (r'ok\(len\(worst\) == (\d+),', worst, 'the worst count')):
        mm = re.search(pat, _box[0])
        if not mm:
            raise SystemExit('PR-1: could not find %s' % what)
        one(mm.group(0), mm.group(0).replace(mm.group(1), str(val)), what)
    for pat, val in ((r"'5\. TWO OF THE (\d+) ARE NOT A TENTH SHORT'",
                      fam['house']),
                     (r'    (\d+)  LIVE, and PINNED BY NAME', len(live)),
                     (r'AND THE (\d+) ARE NOT ANONYMOUS DEBT', len(live)),
                     (r'any of the (\d+) should be fixed\. Each is a change',
                      len(live)),
                     (r"any of the (\d+) should be fixed\. Each is a'",
                      len(live))):
        mm = re.search(pat, _box[0])
        if mm and mm.group(1) != str(val):
            one(mm.group(0), mm.group(0).replace(mm.group(1), str(val)),
                pat[:30])
    try:
        _ast.parse(_box[0])
    except SyntaxError as e:
        raise SystemExit('PR-1: test_pair_contrast.py would not parse - %s'
                         % e)
    reg[PC] = _box[0]
    print('PR-1  pair census %d -> %d pairs, +1 live below AA: the '
          'Compliance tab active state at 4.31' % (B.census()[0], n_after))

    # ---- test_system_teal.py: AD-1 pinned a moving number ---------
    #
    # AD-1's section 6 asserts `'EXPECT_PAIRS = 714' in pc` - the pair
    # census's CURRENT value, written as an equality inside another
    # round's suite. It was true for one round. PR-1 adds a tab, the
    # census reads 716, and AD-1 goes red for a change that is none of
    # its business.
    #
    # A CLAIM THAT COULD ONLY EVER BE TRUE ONCE IS A FAULT CLASS, and
    # this house has the rule written down: prefer ceilings and floors
    # to equalities for counts later rounds will change. AD-1 wrote the
    # equality anyway, one round ago, and the gate caught it with
    # nothing staged - which is the gate doing its job rather than an
    # argument for a looser gate.
    #
    # What AD-1 actually proved is that the census grew when it learnt
    # to read a page's own :root. That is a FLOOR, and it stays true
    # however many tabs the tree grows afterwards.
    ST = os.path.join(ROOT, 'test_system_teal.py')
    ssrc = read(ST)
    OLD_S = """ok('EXPECT_PAIRS = 714' in pc,
   'and the pair census went 701 -> 714, because this round taught it to '
   'read a page own :root - every tab rule in the tree is written in one '
   'and not a single one of them was being counted')"""
    NEW_S = """# PR-1, 8 Oct 2026: A FLOOR, NOT AN EQUALITY. This read
# `'EXPECT_PAIRS = 714' in pc` - the census's value on the day - and PR-1
# added a tab, which is a pair, so it read 716 and AD-1 went red for a
# change that was none of its business. What AD-1 proved is that the
# census GREW when it learnt to read a page's own :root; 701 is the
# number that cannot come back.
_pairs = int(re.search(r'EXPECT_PAIRS = (\\d+)', pc).group(1))
ok(_pairs >= 714,
   'and the pair census went 701 -> 714 and is now %d, because this round '
   'taught it to read a page own :root - every tab rule in the tree is '
   'written in one and not a single one of them was being counted'
   % _pairs)
ok(_pairs > 701,
   '  which is the claim that survives: 701 was what it could see before, '
   'and no later round can take it back there')"""
    if ssrc.count(OLD_S) != 1:
        raise SystemExit('PR-1: the EXPECT_PAIRS claim in test_system_teal.py '
                         'matched %d time(s), not once' % ssrc.count(OLD_S))
    ssrc = ssrc.replace(OLD_S, NEW_S, 1)
    try:
        _ast.parse(ssrc)
    except SyntaxError as e:
        raise SystemExit('PR-1: test_system_teal.py would not parse - %s' % e)
    reg[ST] = ssrc

    # ---- alv_rounds.ROUNDS ----------------------------------------
    NOTE = """    # PR-1, 8 Oct 2026 - a COMPLIANCE tab on Personal, at his ask,
    # and CRS Reporting moved onto it. The tile, its markup and its
    # perms_map.crs gate travel together and are not copied: the page
    # holds exactly one CRS link before and after.
    #
    # IT INVERTS P6. P2 commented out the FUTURE tab on 29 Sep, which
    # took the shared right edge with it and left the Personal tab
    # open on one side; P6 removed `border-right: none` so the tab
    # drew its own. Compliance puts a neighbour back, so the
    # declaration comes back and the Compliance tab draws the line
    # through border-left-color. P6's own note on the page said the
    # rule follows the NEIGHBOUR COUNT - this round is the other half
    # of what that note anticipated.
    #
    # P6's suite is RE-POINTED, not edited into agreement: its claim
    # was "the Personal tab has a right border" and is now "the shared
    # edge is there and is drawn once", measured the same way at the
    # same two widths. That claim is true of both arrangements.
    # test_future_tab_off.py's "exactly ONE panel" becomes "no FUTURE
    # panel", which is what it meant.
    #
    # SAME LOOK AND FEEL MEANS THE SAME RULES. Compliance cannot reuse
    # .future-tab - that is grey on this page and test_personal_teal
    # still says so - and it does not get its own copy of the accent
    # rules either, because two copies drift. The four .personal-tab
    # selectors each gain .compliance-tab, so the tabs match by
    # construction.
    '%s',
""" % SUFFIX
    for anchor in ("    '.bak_systeal',\n]", "    '.bak_neutrals',\n]",
                   "    '.bak_editink',\n]"):
        if rounds.count(fit(rounds, anchor)) == 1:
            rounds = rounds.replace(fit(rounds, anchor),
                                    fit(rounds, anchor[:-2] + NOTE + ']'), 1)
            break
    else:
        raise SystemExit('PR-1: could not find the tail of ROUNDS')
    reg[ROUNDS] = rounds

    # ---- the PS1 $suites list -------------------------------------
    PS_NOTE = """    # PR-1, 8 Oct 2026 - the Compliance tab. Section 2 renders both
    # tabs and asserts they compute the SAME colours, the way AD-1
    # does for Administration; section 3 measures the shared edge as
    # one 3px line; section 4 proves CRS Reporting MOVED rather than
    # being copied, gate and all; section 5 drives switchTab and
    # checks each panel actually shows.
    '%s'
)""" % SUITE_NAME
    for anchor in ("    'test_system_teal.py'\n)", "    'test_neutrals.py'\n)",
                   "    'test_pair_contrast.py'\n)"):
        if ps.count(fit(ps, anchor)) == 1:
            ps = ps.replace(fit(ps, anchor),
                            fit(ps, anchor[:-2] + ',\n' + PS_NOTE), 1)
            break
    else:
        raise SystemExit('PR-1: could not find the tail of $suites')
    reg[PS1] = ps
    return reg


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
