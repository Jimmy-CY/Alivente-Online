# -*- coding: utf-8 -*-
"""apply_tab_names.py - round TB-1a, 15 Oct 2026.

THE TAB SAYS SYSTEM AND THE CODE SAYS FUTURE.

Demetri, asked where a Back button should land after a full check of the
Administration module, named the destination as he reads it on screen:

  "...it takes me back to the Home page. This should take me back to the
   Administration Page (with the System Tab selected)."

There is no system tab. The label reads SYSTEM; underneath it is `future`
in six places - `id="tab-future"`, `switchTab('future')`,
`panel-future`, and three dead class names. And the tab beside it reads
FUNCTIONAL while its internals say `alivente`.

TWO SIDES, RENAMED ONCE EACH. The page was built with an ALIVENTE side
and a FUTURE side; the labels were later changed to FUNCTIONAL and
SYSTEM and the internals were not. Renaming one and leaving the other
would give the page `tab-system` sitting next to `tab-alivente`, which
reads worse than either.

    tab-alivente   -> tab-functional     panel-alivente -> panel-functional
    tab-future     -> tab-system         panel-future   -> panel-system
    switchTab('alivente') -> ('functional')
    switchTab('future')   -> ('system')


SIX CLASS NAMES THAT STYLE NOTHING, AND WHY THEY GO RATHER THAN MOVE
============================================================================
`alivente-tab`, `alivente-panel`, `btn-alivente`, `future-tab`,
`future-panel` and `btn-future` have no rule on this page, none in
base.html, and none anywhere else in either template root. Ten
occurrences of six names, measured.

The page's own comment says why, at line 86:

    The --alivente-* and --future-* tokens went with them. There is no
    separate future side to colour any more: AD-1 pointed both at the
    [same tone].

The intent was retired and the names were left. **Renaming a dead name
keeps the dead weight with a better spelling**, so they are deleted.
CC-1 put it in one line a day ago: a rule with no element is dead weight
exactly as an element with no rule is a bug.

PERSONAL.HTML IS NOT TOUCHED, AND THAT IS THE CARE THIS ROUND NEEDS.
`.admin-tab.future-tab`, `.tab-panel.future-panel` and two `--future-*`
tokens are page-local to personal.html, kept on purpose for the FUTURE
tab it has commented out since 29 Sep, so reinstating that tab is two
deletions and not a rebuild. Four suites assert on those rules -
test_future_tab_off, test_house_tabs, test_compliance_tab,
test_personal_teal - and every one of them reads THAT page. The patcher
refuses if this round has changed personal.html at all.


WHY IT IS ITS OWN ROUND AND NOT PART OF TB-1b
============================================================================
TB-1b teaches a Back button to ask for a tab by key. If that round ran
first it would have to write down that the key `system` means the id
`future` - a map entry whose whole content is a stale name. Renaming
first means the second round never records the mismatch, and the two
ship in one push.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_tabnames'
PAGE = 'admin_apms.html'
TWIN = 'personal.html'
ME = 'test_tab_names.py'
PATCHER = 'apply_tab_names.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
TRE = 'test_tab_right_edge.py'
CHECK = False

CONVERTED_WAS, CONVERTED_NOW = 82, 83
ALIAS_WAS, ALIAS_NOW = 75, 77
ALIAS_P_WAS, ALIAS_S_WAS = 37, 38
ALIAS_P_NOW, ALIAS_S_NOW = 38, 39

# The six names that style nothing, and the two live ids each side owns.
DEAD = ('alivente-tab', 'alivente-panel', 'btn-alivente',
        'future-tab', 'future-panel', 'btn-future')
RENAMED = (('tab-alivente', 'tab-functional'),
           ('panel-alivente', 'panel-functional'),
           ('tab-future', 'tab-system'),
           ('panel-future', 'panel-system'))

TABS_WAS = """  <div class="admin-tab alivente-tab active" id="tab-alivente" onclick="switchTab('alivente')">
    <i class="fas fa-building"></i>
    <span>FUNCTIONAL</span>
  </div>
  <div class="admin-tab future-tab" id="tab-future" onclick="switchTab('future')">
    <i class="fas fa-cogs"></i>
    <span>SYSTEM</span>
  </div>"""

TABS_NOW = """  <div class="admin-tab active" id="tab-functional" onclick="switchTab('functional')">
    <i class="fas fa-building"></i>
    <span>FUNCTIONAL</span>
  </div>
  <div class="admin-tab" id="tab-system" onclick="switchTab('system')">
    <i class="fas fa-cogs"></i>
    <span>SYSTEM</span>
  </div>"""

PANEL_A_WAS = """  <!-- Alivente Panel -->
  <div id="panel-alivente" class="tab-panel alivente-panel active">"""

PANEL_A_NOW = """  <!-- Functional Panel -->
  <div id="panel-functional" class="tab-panel active">"""

PANEL_F_WAS = """  <!-- Future Panel -->
  <div id="panel-future" class="tab-panel future-panel">"""

PANEL_F_NOW = """  <!-- System Panel -->
  <div id="panel-system" class="tab-panel">"""

SCRIPT_WAS = """    document.getElementById('tab-alivente').classList.remove('active');
    document.getElementById('tab-future').classList.remove('active');

    // Update panels
    document.getElementById('panel-alivente').classList.remove('active');
    document.getElementById('panel-future').classList.remove('active');

    if (tab === 'alivente') {
        document.getElementById('tab-alivente').classList.add('active');
        document.getElementById('panel-alivente').classList.add('active');
    } else {
        document.getElementById('tab-future').classList.add('active');
        document.getElementById('panel-future').classList.add('active');
    }"""

SCRIPT_NOW = """    document.getElementById('tab-functional').classList.remove('active');
    document.getElementById('tab-system').classList.remove('active');

    // Update panels
    document.getElementById('panel-functional').classList.remove('active');
    document.getElementById('panel-system').classList.remove('active');

    if (tab === 'functional') {
        document.getElementById('tab-functional').classList.add('active');
        document.getElementById('panel-functional').classList.add('active');
    } else {
        document.getElementById('tab-system').classList.add('active');
        document.getElementById('panel-system').classList.add('active');
    }"""

# The note that explained the retired tokens now explains the names too.
NOTE_WAS = """     The --alivente-* and --future-* tokens went with them. There is no"""

NOTE_NOW = """     TB-1a, 15 Oct 2026 - AND THE SIX CLASS NAMES WENT TOO. alivente-tab,
     alivente-panel, btn-alivente and their three future-* twins styled
     nothing on this page, nothing in base and nothing anywhere else:
     ten occurrences of six names left behind when the tokens below
     were retired. The two sides are now called functional and system,
     which is what the two labels have said for weeks.

     personal.html keeps ITS .future-tab and .future-panel rules, which
     are its own and are held for the tab it has commented out.

     The --alivente-* and --future-* tokens went with them. There is no"""

# ------------------------------------------------------------- registers
SENT_ANCHOR = """    # -------------------------------------------- HL-1, 12 Oct 2026"""

SENT_NEW = """    # ------------------------------------------------ TB-1a, 15 Oct 2026
    # Demetri named the destination as he reads it - "the System Tab".
    # There was no system tab: the label said SYSTEM and six places
    # underneath said future, and the tab beside it said FUNCTIONAL over
    # six that said alivente.
    @{ File = 'pages\\templates\\admin_apms.html'; Text = 'id="tab-system"'; What = 'the tab labelled SYSTEM is called system in the code as well' },
    @{ File = 'pages\\templates\\admin_apms.html'; Text = 'btn-future'; Absent = $true; Code = $true; What = 'and six class names that styled nothing are gone, not respelled' },
    # -------------------------------------------- HL-1, 12 Oct 2026"""

SUITE_WAS = """    'test_stat_cols.py'
)"""

SUITE_NOW = """    'test_stat_cols.py',
    'test_tab_names.py'
)"""

TREE_WAS = """    'test_stat_cols.py',
]"""

TREE_NOW = """    'test_stat_cols.py',
    # TB-1a, 15 Oct 2026 - the Administration tabs are called what their
    # labels say, and six class names that styled nothing are gone.
    # Wide from birth.
    'test_tab_names.py',
]"""

ROUNDS_WAS = """    '.bak_statcols',
]"""

TRE_WAS = """other = read(alv_tree.path_of(OTHER))
otabs = re.findall(r'class="admin-tab ([\\w\\- ]+)"', markup_of(other))
ok(len(otabs) == 2, '%s still renders two tabs' % OTHER, otabs)
ok(any('future-tab' in t for t in otabs),
   '  one of which is the Future tab that draws the shared edge')"""

TRE_NOW = """# TB-1a, 15 Oct 2026 - TWO VARIABLES, BECAUSE THIS SECTION ASKS TWO
# DIFFERENT QUESTIONS, and reading one file for both is what made a
# correct round look like a regression.
#
# WHAT THIS PAGE RENDERED is a claim about P2a's tree: two tabs, one of
# them wearing the class that drew the shared edge. It is a SNAPSHOT,
# and it is read the way PAGE is read three lines above - the comment
# there already says why, and it held for one of the two files.
#
# WHAT THIS PAGE DECLARES is a claim about the tree as it stands: that
# the edge is base's now and this page keeps no copy. It is an
# INVARIANT and stays live.
#
# TB-1a renamed this page's tabs - alivente and future became functional
# and system - and deleted six class names that styled nothing, so a
# live read of the old class attribute finds no tabs and reports that
# the page stopped rendering them. It renders two, then and now.
other_then = (_alb(alv_tree.path_of(OTHER), SUFFIX, read) if _alb
              else read(alv_tree.path_of(OTHER)))
other = read(alv_tree.path_of(OTHER))
otabs = re.findall(r'class="admin-tab ([\\w\\- ]+)"', markup_of(other_then))
ok(len(otabs) == 2, '%s rendered two tabs when P2a measured it' % OTHER,
   otabs)
ok(any('future-tab' in t for t in otabs),
   '  one of which wore the class that drew the shared edge')
# AND IT STILL RENDERS TWO, asked of the live page without depending on
# a class name a later round was free to retire.
# THE BOUNDARY IS QUOTE, SPACE OR BRACE. class="admin-tabs" is the
# CONTAINER, so a plain substring count makes it a third tab - and
# TB-1b puts a {% if %} straight after the class, so a boundary of
# quote-or-space finds none at all. Both of those were written here
# before this line was right.
_live = len(re.findall(r'class="admin-tab(?=["\\s{])', markup_of(other)))
ok(_live == 2, '  and it still renders two today', _live)"""

ROUNDS_NOW = """    '.bak_statcols',
    # TB-1a, 15 Oct 2026 - admin_apms' two tabs renamed from alivente and
    # future to functional and system, so TB-1b never has to write down
    # that the key system means the id future. Six dead class names go.
    '.bak_tabnames',
]"""


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
    raise SystemExit('TB-1a REFUSED: %s' % msg)


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


def css_of(t):
    return re.sub(r'/\*.*?\*/', ' ', '\n'.join(
        re.findall(r'<style\b[^>]*>(.*?)</style\s*>', t, re.S)), flags=re.S)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    page = alv_tree.path_of(PAGE)

    # ---------------------------------------------------------------- 0
    # ALREADY APPLIED COMES FIRST, asked of the TREE. This file's own
    # docstring carries both spellings, so the question is asked of the
    # page and of its code.
    if 'id="tab-system"' in code_only(read(page)):
        print('TB-1a  already applied - the tabs are called what they say.')
        return 0

    out = {}

    # ---------------------------------------------------------------- 1
    # THE SIX ARE DEAD BEFORE THEY ARE DELETED, asserted rather than
    # assumed - over BOTH template roots, because a rule in any page
    # that reaches this markup would make a deletion a visible change.
    live = []
    for q in alv_tree.templates():
        css = css_of(read(q))
        for name in DEAD:
            if re.search(r'\.' + name + r'(?![\w-])[^{}]*\{', css):
                live.append('%s declares .%s' % (alv_tree.rel(q), name))
    # personal.html's own .future-tab and .future-panel are expected and
    # are NOT this page's: they are scoped to the page that holds them.
    unexpected = [x for x in live if 'personal.html' not in x]
    if unexpected:
        refuse('a class this round deletes is styled somewhere:\n   '
               + '\n   '.join(unexpected))
    if not any('personal.html' in x for x in live):
        refuse('personal.html no longer declares its own future-* rules - '
               'the control that proves the deletions are scoped is gone')

    # ---------------------------------------------------------------- 2
    s = read(page)
    s = swap(s, TABS_WAS, TABS_NOW, '%s (the two tabs)' % PAGE)
    s = swap(s, PANEL_A_WAS, PANEL_A_NOW, '%s (the functional panel)' % PAGE)
    s = swap(s, PANEL_F_WAS, PANEL_F_NOW, '%s (the system panel)' % PAGE)
    s = swap(s, SCRIPT_WAS, SCRIPT_NOW, '%s (switchTab)' % PAGE)
    s = swap(s, NOTE_WAS, NOTE_NOW, '%s (the note)' % PAGE)
    # the five remaining btn-* occurrences, each on its own anchor line
    for cls in ('btn-alivente', 'btn-future'):
        was = 'class="admin-btn %s"' % cls
        n = s.count(was)
        if n == 0:
            refuse('%s: no %s button to clean' % (PAGE, cls))
        s = s.replace(was, 'class="admin-btn"')
        print('   %s: %d x %s -> admin-btn' % (PAGE, n, cls))
    out[page] = s

    # ---------------------------------------------------------------- 3
    # GATES.
    body = code_only(s)
    for name in DEAD:
        if name in body:
            refuse('%s: %s survives in the code' % (PAGE, name))
    for old, new in RENAMED:
        if old in body:
            refuse('%s: %s survives in the code' % (PAGE, old))
        if s.count(new) != 3:
            refuse('%s: %s appears %d time(s), expected 3 - the markup, '
                   'the remove and the add' % (PAGE, new, s.count(new)))
    for key in ("switchTab('functional')", "switchTab('system')"):
        if key not in s:
            refuse('%s: %s is missing' % (PAGE, key))
    # The two panels and the two tabs are still there, and still two.
    # COUNTED WITH A BOUNDARY: class="admin-tabs" is the CONTAINER and a
    # plain substring count makes it a third tab, which is how the first
    # cut of this gate refused a correct round.
    n_tab = len(re.findall(r'class="admin-tab(?=["\s])', s))
    n_panel = len(re.findall(r'class="tab-panel(?=["\s])', s))
    if n_tab != 2 or n_panel != 2:
        refuse('%s: expected two tabs and two panels, found %d and %d'
               % (PAGE, n_tab, n_panel))
    # EXACTLY ONE of each carries `active` on arrival - TB-1b moves that
    # decision into the view, and a page with two active tabs is the
    # defect PR-1 and TB-2 both shipped.
    if s.count('admin-tab active') != 1:
        refuse('%s: %d tab(s) carry active, expected 1'
               % (PAGE, s.count('admin-tab active')))
    if s.count('tab-panel active') != 1:
        refuse('%s: %d panel(s) carry active, expected 1'
               % (PAGE, s.count('tab-panel active')))

    # ---------------------------------------------------------------- 4
    # AND THE TWIN IS UNTOUCHED. Said as a gate, not as an intention.
    twin = alv_tree.path_of(TWIN)
    if twin in out or os.path.exists(twin + SUFFIX):
        refuse('%s: this round must not touch the page that keeps its own '
               'future-* rules' % TWIN)

    # ---------------------------------------------------------------- 5
    p = os.path.join(root, PS1)
    s = read(p)
    if 'test_tab_names.py' in s:
        refuse('%s already lists this round' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suite list)' % PS1)
    s = swap(s, SENT_ANCHOR, SENT_NEW, '%s (the gate rows)' % PS1)
    out[p] = s

    p = os.path.join(root, TREE)
    out[p] = swap(read(p), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), ROUNDS_WAS, ROUNDS_NOW, '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, WD)
    out[p] = bump(read(p), 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'TB-1a, 15 Oct 2026 - this round own suite. The '
                  'Administration tabs are called what their labels say, '
                  'after Demetri asked for a Back button to land on the '
                  'System tab and there was no system tab.',
                  '%s (the converted count)' % WD)

    # THE ONE SUITE THIS ROUND RE-POINTS, and it is a repair rather
    # than a loosening: the check keeps its exact numbers and starts
    # reading the same snapshot its sibling check already read.
    p = os.path.join(root, TRE)
    s = read(p)
    if '_alb(alv_tree.path_of(OTHER)' in s:
        refuse('%s already reads OTHER as the round left it' % TRE)
    out[p] = swap(s, TRE_WAS, TRE_NOW, '%s (the second page)' % TRE)

    p = os.path.join(root, CO)
    s = read(p)
    s = bump(s, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
             'TB-1a, 15 Oct 2026 - this round own patcher and suite',
             '%s (the alias count)' % CO)
    s = swap(s, "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_WAS, ALIAS_S_WAS),
             "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_NOW, ALIAS_S_NOW),
             '%s (the alias split)' % CO)
    out[p] = s

    # ---------------------------------------------------------------- 6
    if CHECK:
        print('TB-1a --check  %d file(s) would change' % len(out))
        for q in sorted(out):
            print('   %s' % os.path.relpath(q, root))
        return 0

    for q, t in sorted(out.items()):
        backup(q)
        write(q, t)

    print('TB-1a applied.')
    print('   the two Administration tabs are called functional and')
    print('         system - what their labels have said for weeks')
    print('   six class names that styled nothing are deleted, not')
    print('         respelled: ten occurrences, measured dead first')
    print('   personal.html is untouched, and keeps its own future-*')
    print('         rules for the tab it has commented out')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
