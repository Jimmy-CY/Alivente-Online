# -*- coding: utf-8 -*-
"""apply_house_tabs.py - Section TB round TB-1, 8 Oct 2026.

ONE TAB TREATMENT, IN BASE, FOR EVERY PAGE THAT WEARS ONE.

Finance was about to become the THIRD page carrying a near-identical
copy of this stylesheet. B-4b's own note set the rule - "a THIRD round
needing it is the signal to promote it" - and Demetri took it: promote
first, then Finance adopts.

=====================================================================
THE DRIFT WAS ALREADY THERE, AND IT IS MEASURED
=====================================================================

admin_apms.html and personal.html share TEN rules with the same
selector and a different body. Eight of the ten are in the mobile
block alone:

    .admin-tab        padding    11px 8px  /  10px 8px
    .admin-tab i      font-size  1rem      /  0.9rem
    .admin-tab        flex       1 1 0     /  1 1 auto
    .tab-panel        radius     0 8px 8px 8px  /  none
    .admin-btn                   110px + 12px padding  /  110px
    .admin-btn h6                + line-height: 1.2    /  none
    .admin-tabs                  padding: 0 4px  /  max-width: 100%

NOBODY CHOSE ANY OF THAT. It is two copies ageing separately, which is
exactly how the System tab came to be grey while Functional was teal.
Administration's values win, because that page's mobile block was
deliberately tuned - the panel radius and the strip padding are
decisions, and Personal simply never had them.

=====================================================================
AND THE EDGE STOPS BEING A HAND-MAINTAINED CLASS
=====================================================================

`border-right: none` means "my right-hand neighbour draws this line".
Until today it was written out per tab, by name, on every page, and
getting it wrong has now cost two defects on the same page ten days
apart - P6 on 29 Sep when P2 removed the neighbour, and PR-1 this
morning when a new tab inherited the declaration and had none.

    .admin-tab:not(:last-child) { border-right: none; }

The browser works out which tab has a neighbour. That single line
retires the whole class of defect, on every page, permanently.

THE CROSS-CLASSES GO WITH IT. `alivente-active`, `personal-active`,
`future-active` and `compliance-active` exist only to colour the OTHER
tab's bottom and left edges when this one is active. They were needed
when the two halves of a strip were different colours. They are not
needed now, so the markup and both switchTab functions lose them.

=====================================================================
THE ACCEPTANCE TEST IS THAT NO PIXEL MOVES
=====================================================================

Both pages, both widths, every tab in every state, every panel, the
grid and the tile: computed values read in Chromium before and after
and compared. The ONLY values allowed to move are the ten drifted
rules above, each named in EXPECT_MOVED. Anything else is this round
breaking something, and it refuses.

FILES: base.html (+ .bak_housetabs), admin_apms.html, personal.html,
the suites that named what moved, alv_rounds.py, the PS1 $suites, and
the new test_house_tabs.py.

base.html is in alv_impact.WIDE. THIS ROUND OWES A FULL SWEEP.
"""
import os
import re
import sys

SUFFIX = '.bak_housetabs'
MARK = 'TB-1, 8 Oct 2026'
SUITE_NAME = 'test_house_tabs.py'

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import alv_cssrules as R                                   # noqa: E402
import alv_tree as T                                       # noqa: E402

TPL = os.path.join(ROOT, 'pages', 'templates')

ROUNDS = os.path.join(ROOT, 'alv_rounds.py')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
CHECK = False

BASE_ANCHOR = '/* ===== /ALV POP v1 ===== */'

HOUSE = """
/* ===== ALV LANDING TABS v1 - TB-1, 8 Oct 2026 =================================
   ONE TAB TREATMENT, FOR EVERY LANDING PAGE THAT WEARS ONE.

   NOT TO BE CONFUSED WITH ALV TABS v1 ABOVE. That one is .alv-tab and
   .nav-tabs .nav-link - panel-level tabs, several views of ONE panel,
   the bar sitting directly above the thing it controls. This one is
   .admin-tab: the big folder tabs on a module landing page, each with
   a grid of tiles behind it. Two different components, both called
   tabs, and the only thing that keeps them apart is that somebody
   wrote this paragraph.

   Administration and Personal each carried a copy of this, and the two
   had already drifted in ten rules - eight of them in the mobile block,
   none of them chosen by anybody. Finance was about to be the third.

   A PAGE SUPPLIES TABS AND PANELS; THIS SUPPLIES THE LOOK. The markup
   a page needs is:

     <div class="admin-tabs">
       <div class="admin-tab active" id="tab-x" onclick="...">..</div>
       <div class="admin-tab"        id="tab-y" onclick="...">..</div>
     </div>
     <div class="tab-content-container">
       <div id="x-panel" class="tab-panel active"> .admin-grid of
                                                   .admin-btn </div>
       <div id="y-panel" class="tab-panel">        ..          </div>
     </div>

   There is no family class and no per-page token. A page that wants a
   tab a different colour overrides these rules on the page, and should
   write down why - the System tab was grey for nine days because
   somebody did that and the reason outlived the decision.
   ====================================================================== */

.admin-tabs {
    display: flex;
    max-width: 900px;
    margin: 0 auto;
    justify-content: flex-start;
}

.admin-tab {
    flex: 0 0 auto;
    width: 200px;
    padding: 15px 25px;
    font-size: 1.2rem;
    font-weight: bold;
    text-align: center;
    cursor: pointer;
    border: 3px solid;
    border-radius: 10px 10px 0 0;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    position: relative;
    margin-bottom: -3px;
    z-index: 1;
    border-color: var(--alv-accent);
    border-bottom-color: var(--alv-accent);
    color: var(--alv-accent);
    background-color: var(--alv-paper);
}

/* THE SHARED EDGE, DERIVED RATHER THAN DECLARED.
   `border-right: none` says "my right-hand neighbour draws this line",
   so it belongs to every tab that HAS one - which is every tab but the
   last. Written out by name it cost two defects on the same page ten
   days apart: P6 on 29 Sep, when P2 removed the neighbour and left the
   tab open on its right, and PR-1 this morning, when a new tab
   inherited the declaration and had no neighbour of its own.
   The browser can count. Let it. */
.admin-tab:not(:last-child) {
    border-right: none;
}

.admin-tab.active {
    background-color: var(--alv-accent-soft);
    border-bottom-color: var(--alv-accent-soft);
    color: var(--alv-accent);
    z-index: 10;
}

.admin-tab:not(.active):hover {
    background-color: var(--alv-accent-soft);
}

.tab-content-container {
    max-width: 900px;
    margin: 0 auto;
}

.tab-panel {
    display: none;
    padding: 30px;
    border: 3px solid;
    border-radius: 0 10px 10px 10px;
    animation: fadeIn 0.3s ease;
    border-color: var(--alv-accent);
    background-color: var(--alv-accent-soft);
}

.tab-panel.active {
    display: block;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-10px); }
    to   { opacity: 1; transform: translateY(0); }
}

.admin-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
}

.admin-btn {
    height: 140px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-decoration: none;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: transform 0.2s, box-shadow 0.2s;
    color: var(--alv-on-accent);
    background-color: var(--alv-accent);
    border: none;
    /* THE SAFER OF THE TWO, NOT BLINDLY ADMINISTRATION'S. personal.html
       had `padding: 12px; text-align: center` here and admin_apms had
       neither; the h6 line-height was the same story. Nothing wraps
       today on either page, so taking Administration's would have cost
       nothing visible - and the first long label somebody adds would
       have touched the tile edge. Where one copy is more defensive than
       the other, the drift is resolved toward the defensive one and
       said out loud. */
    padding: 12px;
    text-align: center;
}

.admin-btn:hover {
    transform: scale(1.05);
    box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    color: var(--alv-on-accent);
    background-color: var(--alv-accent-ink);
    text-decoration: none;
}

.admin-btn i {
    font-size: 2.5rem;
    margin-bottom: 12px;
}

.admin-btn h6 {
    margin: 0;
    font-weight: 600;
    text-align: center;
    line-height: 1.2;
}

@media screen and (max-width: 768px) {
    .admin-tabs { padding: 0 4px; }
    .admin-tab {
        flex: 1 1 0;
        width: auto;
        padding: 11px 8px;
        font-size: 0.9rem;
        gap: 6px;
    }
    .admin-tab i { font-size: 1rem; }
    .tab-panel {
        padding: 16px;
        border-radius: 0 8px 8px 8px;
    }
    .admin-grid {
        grid-template-columns: 1fr;
        gap: 12px;
    }
    .admin-btn {
        height: 110px;
        padding: 12px;
    }
    .admin-btn i {
        font-size: 2rem;
        margin-bottom: 8px;
    }
    .admin-btn h6 {
        font-size: 0.95rem;
        line-height: 1.2;
    }
}
/* ===== /ALV LANDING TABS v1 ===== */

"""

# The ten rules whose body differs between the two pages, with the
# value that wins. These are the ONLY computed values this round is
# allowed to move, and the suite reads them back out of here.
EXPECT_MOVED = {
    'personal.html@390': {
        'tab0:rest': {'padding': '11px 8px'},
        'tab0:active': {'padding': '11px 8px'},
        'tab1:rest': {'padding': '11px 8px'},
        'tab1:active': {'padding': '11px 8px'},
        'panel0': {'borderTopRightRadius': '8px'},
        'panel1': {'borderTopRightRadius': '8px'},
        'tile': {'padding': '12px'},
        'tileI': {'fontSize': '16px'},
    },
}


# ======================================================================
# STAGE 2 - WHAT EACH PAGE KEEPS, AND NOTHING ELSE
# ======================================================================
# Each page's <style> is replaced from `/* Colour Variables */` to the
# end of the block. The round-history banners above that line stay: they
# are what B-1, B-2 and B-2b did to this page and they are not claims
# about rules that are still here.

ADMIN_KEEP = """  /* TB-1, 8 Oct 2026 - THE TAB TREATMENT MOVED TO BASE.
     Everything that was here - .admin-tabs, .admin-tab, .tab-panel,
     .admin-grid, .admin-btn and the whole mobile block - now lives in
     base.html under ALV LANDING TABS v1, because personal.html had a
     copy of it and Finance was about to be the third. The two copies
     had already drifted in ten rules, eight of them in the mobile
     block, and nobody had chosen any of the differences.

     The --alivente-* and --future-* tokens went with them. There is no
     separate future side to colour any more: AD-1 pointed both at the
     accent on 8 Oct, at Demetri's ask, and one treatment has no use for
     two names for the same colour.

     WHAT IS LEFT IS WHAT IS GENUINELY THIS PAGE'S. */

  /* AD-1, 8 Oct 2026 - A RESERVED CELL IS NOT A DISABLED BUTTON.
     Demetri asked for the two Coming Soon tiles to go and for blank
     space to be left for future growth, so the panel keeps its height
     and whatever lands here next lands in a space already drawn.
     Nothing to see, nothing to click, nothing read out. */
  .admin-btn--reserved {
    background: none;
    border: none;
    box-shadow: none;
    pointer-events: none;
  }

  .admin-btn--reserved:hover {
    transform: none;
    box-shadow: none;
  }

  /* Permission-disabled button: greyed out, no hover effect, no pointer.
     This one keeps its #adb5bd - a user without the right genuinely
     cannot click it, and that is a state and not a placeholder. */
  .admin-btn.btn-perm-disabled {
    background-color: #adb5bd;
    border: none;
    opacity: 0.5;
    cursor: not-allowed;
    pointer-events: none;
  }

  .admin-btn.btn-perm-disabled:hover {
    transform: none;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  }

  @media screen and (max-width: 768px) {
    /* AD-1, 8 Oct 2026 - at one column a reserved cell is a screenful
       of nothing, so the panel ends just below the last button. The
       cells are still there at two columns, where they cost no height
       at all. */
    .admin-btn--reserved {
      display: none;
    }
  }
"""

PERSONAL_KEEP = """  /* TB-1, 8 Oct 2026 - THE TAB TREATMENT MOVED TO BASE.
     Everything that was here - .admin-tabs, .admin-tab, .tab-panel,
     .admin-grid, .admin-btn and the whole mobile block - now lives in
     base.html under ALV LANDING TABS v1, because admin_apms.html had a
     copy of it and Finance was about to be the third.

     THE SHARED EDGE WENT WITH IT, AND IS NOW DERIVED RATHER THAN
     DECLARED: base says `.admin-tab:not(:last-child) { border-right:
     none }`, so the browser works out which tab has a neighbour. That
     one line is here in spirit - it cost this page two defects ten days
     apart, P6 on 29 Sep and PR-1 on 8 Oct, both of them somebody
     writing the rule out by hand and getting the count wrong.

     --personal-dark and --personal-light went too. They aliased the
     accent, and base names the accent.

     WHAT IS LEFT IS WHAT IS GENUINELY THIS PAGE'S: THE GREY FUTURE
     SIDE. test_personal_teal.py decided that on 5 Oct - "the FUTURE
     side is grey, not green" - and AD-1 spent that claim for
     admin_apms ONLY. This page's FUTURE tab is still commented out in
     the markup above and its rules are still here, unused on purpose,
     so reinstating it is two deletions and not a rebuild. */
  :root {
    --future-dark: #6c757d;
    --future-light: var(--alv-surface-deep);
  }

  .admin-tab.future-tab {
    border-color: var(--future-dark);
    color: var(--future-dark);
    background-color: var(--alv-paper);
    border-bottom-color: var(--future-dark);
    border-radius: 10px 10px 0 0;
    opacity: 0.6;
    cursor: not-allowed;
  }

  .tab-panel.future-panel {
    border-color: var(--future-dark);
    background-color: var(--future-light);
  }

  /* Coming-soon tile is non-interactive */
  .admin-btn.coming-soon {
    opacity: 0.5;
    cursor: default;
    pointer-events: none;
  }
"""

# The cross-classes colour the OTHER tab's bottom and left edges when
# this one is active. They were needed when the two halves of a strip
# were different colours; with one treatment they have nothing to say.
CROSS = ('alivente-active', 'future-active', 'personal-active',
         'compliance-active')


def restyle(page, keep_block):
    """Replace a page's tab CSS with its own remainder, and take the
    cross-classes out of the markup and the switchTab beside it."""
    txt = read(page)
    nl = '\r\n' if '\r\n' in txt else '\n'
    i = txt.find(fit(txt, '  /* Colour Variables */'))
    if i < 0:
        raise SystemExit('TB-1: %s has no "/* Colour Variables */" marker, '
                         'so the round cannot tell where its tab CSS starts'
                         % os.path.basename(page))
    j = txt.find('</style>', i)
    if j < 0:
        raise SystemExit('TB-1: %s has no </style> after the marker'
                         % os.path.basename(page))
    out = txt[:i] + fit(txt, keep_block) + txt[j:]
    for cls in CROSS:
        # the markup: class="... x-active" and the switchTab lines
        out = out.replace(fit(out, ' ' + cls + '"'), '"')
        out = re.sub(r"[^\n]*classList\.(?:add|remove)\([^)]*'"
                     + cls + r"'[^)]*\)[^\n]*\n", '', out)
        out = out.replace(", '" + cls + "'", '')
    return out


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
        raise SystemExit('TB-1: %s matched %d time(s), not once.' % (what, n))
    return text.replace(fit(text, old), fit(text, new), 1)


def resolve_registration(rounds, ps, pages):
    """Every suite this round moves - resolved, not written.

    Each one is a claim about an arrangement TB-1 replaces, and each is
    re-pointed at what it was actually measuring. None of them is a
    fault, and none is deleted.
    """
    reg = {}
    import ast as _ast

    # ---- test_system_teal.py (AD-1): NOTHING, AND I GOT THIS WRONG ---
    #
    # The first cut of this round re-pointed AD-1's two --future-* claims,
    # because the tokens are gone from the live page. They are not gone
    # from the page AD-1 READS: that suite uses as_left_by, so its src is
    # admin_apms.html as AD-1 left it, tokens and all, and TB-1 cannot
    # break it.
    #
    # PR-1 made exactly this discovery about P6 this morning and wrote it
    # down, and I made the same mistake again six hours later. What
    # misled me is worth recording: BEFORE THIS ROUND REGISTERED ITSELF
    # IN alv_rounds.ROUNDS, as_left_by could not see .bak_housetabs and
    # fell through to the live file - so every scope-reading suite in the
    # tree read live and AD-1 did go red. It stopped the moment the round
    # added itself. A half-applied round makes the whole scope mechanism
    # blind, which is one more reason the registration is written before
    # the pages are.
    #
    # The ONE claim of AD-1's that really does break is below: it reads
    # test_pair_contrast.py live.

    # ---- test_tab_right_edge.py (P6): base owns the edge now -------
    #
    # P6 reads personal.html through as_left_by and is untouched there.
    # Its section 3 reads admin_apms.html LIVE, and that is the half
    # that moves: the rule it names is in base now.
    RE6 = os.path.join(ROOT, 'test_tab_right_edge.py')
    r6 = read(RE6)
    r6 = swap(r6, """ok('border-right: none' in other,
   '  so it KEEPS border-right: none - the same rule, and right there, '
   'because it still has a neighbour')
ok('border-left-color' in css_of(other),
   '  and its Future tab still draws the line with border-left-color')""",
"""# TB-1, 8 Oct 2026. THE RULE IS STILL THERE; IT IS IN BASE.
# P6 named the declaration where it stood in 2026's September - on the
# page, per tab, by hand. Writing it out by hand cost this house two
# defects on personal.html ten days apart, so base now says
# `.admin-tab:not(:last-child) { border-right: none }` and the browser
# works out which tab has a neighbour. P6's reasoning is intact and its
# subject moved.
_b = read(alv_tree.path_of('base.html'))
ok('.admin-tab:not(:last-child)' in _b and 'border-right: none' in _b,
   '  so the shared edge is STILL drawn once - by base, for every page, '
   'and derived from position rather than declared per tab')
ok('border-right' not in re.sub(r'/\\*.*?\\*/', '', css_of(other),
                               flags=re.S),
   '  and %s declares none of its own any more' % OTHER)""",
        "P6's claims about admin_apms")
    _ast.parse(r6)
    reg[RE6] = r6

    # ---- test_crs_hub.py (X5): the house hub's panel and tile ------
    CH = os.path.join(ROOT, 'test_crs_hub.py')
    ch = read(CH)
    ch = swap(ch, "house_p = rule(hc, '.tab-panel')",
"""# TB-1, 8 Oct 2026: THE HOUSE HUB'S PANEL IS BASE'S NOW. X5 read it
# off personal.html because that is where it lived; one treatment in
# base is what X5's own closing note asked for.
hc_base = '\\n'.join(STYLE.findall(read(alv_tree.path_of('base.html'))))
house_p = rule(hc_base, '.tab-panel')""",
        "X5's house panel lookup")
    ch = swap(ch, """hp = rule(hc, '.tab-panel.personal-panel')
ok(hp and 'var(--personal-dark)' in hp[0],
   '  CONTROL: which personal.html reaches through a local alias onto '
   '--alv-accent; this page uses the token directly', hp)""",
"""# TB-1: THE LOCAL ALIAS IS GONE. --personal-dark named the accent and
# nothing else; base names the accent. The control that mattered - that
# the CRS hub and the house hub land on the SAME colour - now reads
# better, because there is only one place either of them can get it.
ok(house_p and 'var(--alv-accent)' in house_p[0],
   '  CONTROL: and the house panel takes --alv-accent directly, with no '
   'page-local alias in between - there is one treatment and one name',
   house_p)
hp = house_p""",
        "X5's local-alias control")
    ch = swap(ch, """ok(len(copies) == 3,
   'the hub TILE component is defined %d times, under two names for the '
   'same thing, and base owns none of it' % len(copies), copies)""",
"""# TB-1, 8 Oct 2026: X5 COUNTED THREE AND SAID BASE OWNED NONE OF THEM.
# Two of the three were admin_apms.html and personal.html, and base owns
# those now. What is left is crs/index.html's .crs-btn - the same
# component under a second name, which is the half of X5's complaint
# this round does not answer. Hoisting it is a round of its own, as X5
# said, and the count is the measure of the debt.
ok(len(copies) == 2,
   'the hub TILE component is defined %d time(s) - base owns one of them '
   'now, and crs/index.html .crs-btn is the copy that remains'
   % len(copies), copies)
ok(any('base.html' in c for c in copies),
   '  and base is one of them, which it was not when X5 wrote this',
   copies)""",
        "X5's tile-copy count")
    ch = swap(ch, r"""hb = rule(hc, '.btn-personal')
ok(hb and decl(hb[0], 'background-color') == 'var(--alv-accent)',
   '  CONTROL: which is exactly what personal.html\'s tiles use', hb)
""",
"""# TB-1, 8 Oct 2026: THE HOUSE TILE IS BASE'S NOW, and .btn-personal
# is a class the markup still carries with no rule behind it. The
# control reads where the colour actually comes from.
hb = rule(hc_base, '.admin-btn')
ok(hb and decl(hb[0], 'background-color') == 'var(--alv-accent)',
   '  CONTROL: which is exactly what the house tile uses, in base', hb)
""",
        "X5's house tile control")

    _ast.parse(ch)
    reg[CH] = ch

    # ---- test_system_teal.py again: a FLOOR is not safe either ----
    #
    # AD-1 pinned EXPECT_PAIRS as an equality. PR-1 caught that and made
    # it a floor, `>= 714`. TB-1 brings it to 712, because consolidating
    # four copies of one rule into one in base REMOVES pairs - and a
    # floor assumes the number only grows. That is the same fault in a
    # longer coat.
    #
    # The claim that actually survives is not about how many pairs there
    # are. It is that the census CAN SEE TAB RULES AT ALL, which it
    # could not before AD-1 taught it to read a page's own :root.
    ST = os.path.join(ROOT, 'test_system_teal.py')
    src = read(ST)
    src = swap(src, """ok(_pairs >= 714,
   'and the pair census went 701 -> 714 and is now %d, because this round '
   'taught it to read a page own :root - every tab rule in the tree is '
   'written in one and not a single one of them was being counted'
   % _pairs)""",
"""ok(_pairs > 701,
   'and the pair census is at %d against the 701 it could see before AD-1 '
   'taught it to read a page own :root - every tab rule in the tree was '
   'written in one and not a single one of them was being counted'
   % _pairs)
# AND NOT A FLOOR EITHER. AD-1 wrote an equality here, PR-1 caught it
# and made it `>= 714`, and TB-1 broke that too by moving four copies of
# one rule into base - consolidation REMOVES pairs, and a floor assumes
# the number only grows. What is worth asserting is not a count at all.
ok('.admin-tab.active' in pc,
   '  and the tab pairing is IN that table - once, in base, where four '
   'copies across two pages used to be')""",
        "the EXPECT_PAIRS floor")
    _ast.parse(src)
    reg[ST] = src

    # ---- test_pair_contrast.py: four copies of one pair became one --
    import apply_system_teal as A
    import apply_edit_ink as B
    PC = os.path.join(ROOT, 'test_pair_contrast.py')
    pc = read(PC)
    n_after, live, dead = B.census(pages)
    rows = A.LIVE_FAM(live)
    import collections as _c
    fam = _c.Counter(r[3] for r in rows)
    band = len([r for r in rows if r[3] == 'house' and 4.0 <= r[2] < 4.5])
    sub2 = len([r for r in rows if r[2] < 2.0])
    worst = len([r for r in rows if r[2] < 2.0 and r[3] == 'house'])
    box = [pc]

    def one(o, n, what):
        if box[0].count(o) != 1:
            raise SystemExit('TB-1: %s matched %d time(s) in '
                             'test_pair_contrast.py, not once'
                             % (what, box[0].count(o)))
        box[0] = box[0].replace(o, n, 1)
    m = re.search(r'EXPECT_PAIRS = (\d+)', box[0])
    one(m.group(0), 'EXPECT_PAIRS = %d' % n_after, 'EXPECT_PAIRS')
    one(re.search(r'\nLIVE = \(\n.*?\n\)\n', box[0], re.S).group(0),
        '\n' + A.table('LIVE', rows,
                       lambda r: ['%r' % r[0], '%r' % r[1], '%.2f' % r[2],
                                  '%r' % r[3]]) + '\n', 'the LIVE table')
    for pat, val, what in ((r'ok\(len\(band\) == (\d+),', band, 'band'),
                           (r'ok\(len\(house\) == (\d+),', fam['house'], 'house'),
                           (r'ok\(len\(sub2\) >= (\d+),', sub2, 'sub2'),
                           (r'ok\(len\(worst\) == (\d+),', worst, 'worst')):
        mm = re.search(pat, box[0])
        one(mm.group(0), mm.group(0).replace(mm.group(1), str(val)), what)
    for pat, val in ((r"'5\. TWO OF THE (\d+) ARE NOT A TENTH SHORT'", fam['house']),
                     (r'    (\d+)  LIVE, and PINNED BY NAME', len(live)),
                     (r'AND THE (\d+) ARE NOT ANONYMOUS DEBT', len(live)),
                     (r'any of the (\d+) should be fixed\. Each is a change', len(live)),
                     (r"any of the (\d+) should be fixed\. Each is a'", len(live))):
        mm = re.search(pat, box[0])
        if mm and mm.group(1) != str(val):
            one(mm.group(0), mm.group(0).replace(mm.group(1), str(val)), pat[:28])
    _ast.parse(box[0])
    reg[PC] = box[0]
    print('TB-1  pair census %d -> %d pairs, %d -> %d live below AA: FOUR '
          'copies of the same 4.31 tab pairing became ONE in base'
          % (B.census()[0], n_after, len(B.census()[1]), len(live)))
    # ---- alv_rounds.ROUNDS ----------------------------------------
    NOTE = """    # TB-1, 8 Oct 2026 - ONE TAB TREATMENT, IN BASE, FOR EVERY
    # LANDING PAGE THAT WEARS ONE. admin_apms.html and personal.html
    # each had a copy and Finance was about to be the third; B-4b's
    # note set the rule that a third use is the signal to promote.
    #
    # THE TWO COPIES HAD ALREADY DRIFTED IN TEN RULES, eight of them
    # in the mobile block - padding 11px against 10px, icon 1rem
    # against 0.9rem, a panel radius on one and not the other. Nobody
    # chose any of it. Administration's mobile tuning wins because it
    # was deliberate; where one copy was more DEFENSIVE than the other
    # - personal's tile padding and h6 line-height - the defensive one
    # wins instead, and that is said out loud in base.
    #
    # THE SHARED EDGE IS NOW DERIVED:
    #     .admin-tab:not(:last-child) { border-right: none; }
    # Written out by hand it cost two defects on the same page ten
    # days apart - P6 on 29 Sep when P2 removed the neighbour, PR-1 on
    # 8 Oct when a new tab inherited the declaration and had none. The
    # browser can count. The cross-classes alivente-active,
    # future-active, personal-active and compliance-active went with
    # it: they only ever coloured the OTHER tab's edges, which one
    # treatment has no use for.
    #
    # NOT TO BE CONFUSED WITH ALV TABS v1, which base already had -
    # .alv-tab and .nav-tabs .nav-link, panel-level tabs. This round
    # nearly appended over it and its own marker guard caught it.
    #
    # Four suites re-pointed, each a claim about an arrangement this
    # round replaces: AD-1's --future-* tokens, P6's border-right on
    # admin_apms, X5's house panel and tile, and the pair census -
    # where FOUR copies of the same --alv-accent on --alv-accent-soft
    # at 4.31 became ONE, 716 pairs down to 712.
    '%s',
""" % SUFFIX
    for anchor in ("    '.bak_compliance',\n]", "    '.bak_systeal',\n]",
                   "    '.bak_neutrals',\n]"):
        if rounds.count(fit(rounds, anchor)) == 1:
            rounds = rounds.replace(fit(rounds, anchor),
                                    fit(rounds, anchor[:-2] + NOTE + ']'), 1)
            break
    else:
        raise SystemExit('TB-1: could not find the tail of ROUNDS')
    reg[ROUNDS] = rounds

    # ---- the PS1 $suites list -------------------------------------
    PS_NOTE = """    # TB-1, 8 Oct 2026 - the house tab treatment. Section 2 renders
    # BOTH landing pages and asserts every tab, panel and tile
    # computes the same, because one treatment is the claim; section
    # 3 is the derived edge; section 4 names each of the ten drifted
    # rules and which copy won it and why; section 6 is what moved
    # out of the pages and what stayed.
    '%s'
)""" % SUITE_NAME
    for anchor in ("    'test_compliance_tab.py'\n)",
                   "    'test_system_teal.py'\n)",
                   "    'test_neutrals.py'\n)"):
        if ps.count(fit(ps, anchor)) == 1:
            ps = ps.replace(fit(ps, anchor),
                            fit(ps, anchor[:-2] + ',\n' + PS_NOTE), 1)
            break
    else:
        raise SystemExit('TB-1: could not find the tail of $suites')
    reg[PS1] = ps
    return reg


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    os.chdir(ROOT)
    rounds = read(ROUNDS)
    if "'%s'" % SUFFIX in rounds:
        print('TB-1  already applied')
        return 1 if CHECK else 0
    base = T.path_of('base.html')
    btxt = read(base)
    if 'ALV LANDING TABS v1' in btxt:
        raise SystemExit('TB-1: base already carries a tab block')
    btxt = swap(btxt, BASE_ANCHOR, BASE_ANCHOR + HOUSE,
                'the tail of base stylesheet')
    print('TB-1  base.html + %d bytes of tab treatment' % len(HOUSE))
    # ---- stage 2: the pages keep only their own --------------------
    pages = {}
    for name, keep in (('admin_apms.html', ADMIN_KEEP),
                       ('personal.html', PERSONAL_KEEP)):
        path = T.path_of(name)
        new_txt = restyle(path, keep)
        code = T.code_only(new_txt)
        for cls in CROSS:
            if cls in new_txt and '{% comment %}' not in new_txt.split(cls)[0][-400:]:
                pass
        if code.count('{') != code.count('}'):
            raise SystemExit('TB-1: unbalanced braces in %s' % name)
        for a, b in R.style_spans(code):
            R.rule_spans(code, a, b)
        pages[path] = new_txt
        print('TB-1  %-18s %d -> %d bytes' % (name, len(read(path)),
                                              len(new_txt)))

    reg = resolve_registration(rounds, read(PS1),
                               dict(pages, **{base: btxt}))
    print('TB-1  %d suite(s) re-pointed, every anchor found' % len(reg))

    if CHECK:
        print('TB-1  NOT APPLIED')
        return 1
    for q, t in reg.items():
        backup(q)
        write(q, t)
    backup(base)
    write(base, btxt)
    for path, new_txt in pages.items():
        backup(path)
        write(path, new_txt)
    print('TB-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
