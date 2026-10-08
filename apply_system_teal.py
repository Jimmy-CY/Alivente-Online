# -*- coding: utf-8 -*-
"""apply_system_teal.py - Section AD round AD-1, 8 Oct 2026.

Demetri: "I want to change the System Tab to conform with our Teal
colours. It must look and behave exactly like the Functional Tab with
regards to colours." And, minutes later: "Remove the two Coming Soon
buttons from System. Just leave blank spaces for future growth."

=====================================================================
THIS OVERTURNS A RECORDED DECISION, AND SAYS SO
=====================================================================

test_personal_teal.py (round PT) carries an UNTOUCHED table and asserts,
in these words, "the FUTURE side is grey, not green":

    UNTOUCHED = {
        'personal.html':   ('--future-dark: #6c757d',),
        'admin_apms.html': ('--future-dark: #6c757d', '#5a6268', '#adb5bd'),
    }

B-4 overturned a decision silently - it converted #ecd9a8 on fsr_details,
which test_fsr_palette names as the Notify round's page-local warn tint,
DECIDED - and it had to be backed out. So this round does the opposite of
quiet: it moves PT's claim for admin_apms, leaves the claim for
personal.html exactly where it is, and writes his instruction and the
date into the table beside it. PT's finding is not wrong. It expired.

=====================================================================
WHAT MOVES - TWO TOKENS CARRY MOST OF IT
=====================================================================

The page already routes the whole System side through two page-local
tokens, so the round repoints those rather than rewriting eleven rules:

    --future-dark   #6c757d                 -> var(--alv-accent)
    --future-light  var(--alv-surface-deep) -> var(--alv-accent-soft)

Three rules do not read them and are changed by hand:

    .btn-future               var(--alv-ink-soft)  -> var(--alv-accent)
    .btn-future:hover         var(--alv-ink-soft)  -> var(--alv-accent-ink)
    .future-tab:not(.active):hover
                              var(--alv-line-soft) -> var(--alv-accent-soft)

The last one matters: today the System tab's hover is a different colour
from Functional's, so "behaves exactly like" was false on hover as well
as at rest.

AND ONE NUMBER GOES DOWN. The System tile is white on --alv-ink-soft at
5.53:1 and becomes white on --alv-accent at 4.91:1. Both clear AA, and
4.91 is what the Functional tile has always read - matching it is the
instruction. Said out loud rather than left for him to find.

The tab's active state goes the other way: --future-dark on
--future-light was 3.95:1 and becomes 4.31:1, which is Functional's
number exactly. Still under AA, as Functional's always has been. That
is the house accent-on-tint pairing and it is ONE BASE DECISION he has
not taken - see test_pair_contrast.py section 5.

=====================================================================
THE TWO TILES, AND WHY A RESERVED CELL IS NOT A DISABLED BUTTON
=====================================================================

He chose to reserve the two cells rather than let the panel shrink, so
the System panel keeps its height and growth lands in a space that is
already drawn. A reserved cell is NOT the Coming Soon tile with its
label removed: it has no fill, no border, no shadow, no hover, it is
aria-hidden, and pointer-events are off. Nothing to see, nothing to
click, nothing read out.

.btn-future-disabled goes with them - one rule, and it carried the
literal #adb5bd. .btn-perm-disabled keeps its #adb5bd and is untouched:
that is a live permission state, not a placeholder.

=====================================================================
AND IT OPENS THE PAIR CENSUS'S EYES
=====================================================================

B-4b's census resolves var() against BASE's :root only, so a rule
written in a page's own token - which is exactly how this page's tabs
are written - resolved to None and was not counted at all. The System
tab's active state was 3.95:1 and no instrument in the tree could see
it; this round moves it to 4.31 and nothing could have seen that either.

A round that improves a number invisibly has not improved anything a
later round cannot undo, so the census learns page-local :root tokens
here. Measured: 701 pairs become 714, and four more read below AA -
three of them the SAME --alv-accent on --alv-accent-soft at 4.31 that
section 5 already calls one base decision. They were always there. The
round that opens the eyes owns what they now see.

FILES: admin_apms.html (+ .bak_systeal), test_personal_teal.py,
apply_edit_ink.py, test_pair_contrast.py, alv_rounds.py, the PS1
$suites, and the new test_system_teal.py.
"""
import os
import re
import sys

SUFFIX = '.bak_systeal'
MARK = 'AD-1, 8 Oct 2026'
SUITE_NAME = 'test_system_teal.py'

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import alv_cssrules as R                                   # noqa: E402
import alv_tree as T                                       # noqa: E402

ROUNDS = os.path.join(ROOT, 'alv_rounds.py')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
PAGE = 'admin_apms.html'
CHECK = False

# Each one must match EXACTLY ONCE or the round refuses. No regexes on
# the page: the anchors are the declarations as they stand.
CSS_EDITS = (
    ('    --future-dark: #6c757d;',
     '    --future-dark: var(--alv-accent);'),
    ('    --future-light: var(--alv-surface-deep);',
     '    --future-light: var(--alv-accent-soft);'),
    ('''  .btn-future {
    background-color: var(--alv-ink-soft);
    border: none;
  }''',
     '''  .btn-future {
    background-color: var(--alv-accent);
    border: none;
  }'''),
    ('''  .btn-future:hover {
    background-color: var(--alv-ink-soft);
  }''',
     '''  .btn-future:hover {
    background-color: var(--alv-accent-ink);
  }'''),
    ('''  .admin-tab.future-tab:not(.active):hover {
    background-color: var(--alv-line-soft);
  }''',
     '''  .admin-tab.future-tab:not(.active):hover {
    background-color: var(--alv-accent-soft);
  }'''),
    # A RESERVED CELL EARNS ITS KEEP ON A DESKTOP AND NOT ON A PHONE.
    # Demetri, after seeing the renders: "On the phone, can we remove
    # the blank spaces and have the tab bottom just below the last
    # button?"
    #
    # At 1280 the grid is two columns, so the two reserved cells sit
    # BESIDE the live tiles and cost nothing - they hold the panel's
    # height and the growth lands in a space already drawn. At 390 the
    # grid is one column, so each of them becomes a full 110px row of
    # nothing and the panel runs a quarter of a screen past its last
    # button. Same markup, opposite effect, and the difference is the
    # column count.
    #
    # It goes in the page's own mobile block rather than a media query
    # of its own, because the page has exactly one and a second would
    # be a second place to look.
    ('''    .admin-btn h6 {
      font-size: 0.95rem;
      line-height: 1.2;
    }
  }''',
     '''    .admin-btn h6 {
      font-size: 0.95rem;
      line-height: 1.2;
    }

    /* AD-1, 8 Oct 2026 - at one column a reserved cell is a screenful
       of nothing, so the panel ends just below the last button. The
       cells are still there at two columns, where they cost no height
       at all. */
    .admin-btn--reserved {
      display: none;
    }
  }'''),
)

# The rule that only the two Coming Soon tiles used.
DEAD_RULE = '''  .btn-future-disabled {
    background-color: #adb5bd;
    border: none;
    opacity: 0.6;
    cursor: default;
  }

'''

RESERVED_RULE = '''  /* AD-1, 8 Oct 2026 - A RESERVED CELL IS NOT A DISABLED BUTTON.
     Demetri asked for the two Coming Soon tiles to go and for blank
     space to be left for future growth, so the panel keeps its height
     and whatever lands here next lands in a space already drawn.
     Nothing to see, nothing to click, nothing read out: no fill, no
     border, no shadow, no hover, aria-hidden in the markup and
     pointer-events off here. It is NOT .btn-future-disabled with the
     label taken out - that rule has gone, and with it the last
     #adb5bd on this page that was not a live permission state. */
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

'''

TILES_OLD = '''      <!-- Placeholder 3 -->
      <div class="admin-btn btn-future-disabled">
        <i class="fas fa-clock"></i>
        <h6>Coming Soon</h6>
      </div>

      <!-- Placeholder 4 -->
      <div class="admin-btn btn-future-disabled">
        <i class="fas fa-clock"></i>
        <h6>Coming Soon</h6>
      </div>
'''

TILES_NEW = '''      <!-- Reserved for growth, AD-1 8 Oct 2026. Empty on purpose:
           it holds the second row so the panel keeps its height.
           aria-hidden because there is nothing here to announce. -->
      <div class="admin-btn admin-btn--reserved" aria-hidden="true"></div>
      <div class="admin-btn admin-btn--reserved" aria-hidden="true"></div>
'''


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


EXPECT_PAIRS_BEFORE = 701
EXPECT_PAIRS_AFTER = 714
# The four the census could not see. THREE OF THEM ARE THE SAME PAIRING:
# --alv-accent on --alv-accent-soft at 4.31, which is the tab treatment
# this whole round is about, on all three pages that wear it.
EXPECT_ADDED = [
    ('admin_apms.html', '.admin-tab.alivente-tab.active'),
    ('admin_apms.html', '.admin-tab.future-tab.active'),
    ('personal.html', '.admin-tab.personal-tab.active'),
    ('view_recipe.html', '.ai-goal-card-icon'),
]


def table(name, rows, cols):
    """A pinned table, written the way test_pair_contrast.py writes it."""
    out = ['%s = (' % name]
    for r in rows:
        out.append('    (%s),' % ', '.join(cols(r)))
    out.append(')')
    return '\n'.join(out)


def resolve_registration(rounds, ps, live, dead, n_pairs):
    """Every file this round has to edit besides the page - resolved,
    not written. {path: new text}, and it raises on any anchor it
    cannot find, so the round refuses before it has moved a byte.

    B-5a wrote 32 pages and THEN discovered B-4b had moved the tail of
    ROUNDS underneath it, and left the tree half-applied. This shape is
    the lesson from that morning.
    """
    reg = {}

    # ---- test_pair_contrast.py: the four numbers this round moved ---
    PC = os.path.join(ROOT, 'test_pair_contrast.py')
    src = read(PC)
    import collections
    fam = collections.Counter(r[3] for r in LIVE_FAM(live))
    band = len([r for r in LIVE_FAM(live)
                if r[3] == 'house' and 4.0 <= r[2] < 4.5])
    sub2 = len([r for r in LIVE_FAM(live) if r[2] < 2.0])
    worst = len([r for r in LIVE_FAM(live) if r[2] < 2.0 and r[3] == 'house'])
    subs = [
        ('EXPECT_PAIRS = %d' % EXPECT_PAIRS_BEFORE,
         'EXPECT_PAIRS = %d' % n_pairs),
        (re.search(r'\nLIVE = \(\n.*?\n\)\n', src, re.S).group(0),
         '\n' + table('LIVE', LIVE_FAM(live),
                      lambda r: ['%r' % r[0], '%r' % r[1], '%.2f' % r[2],
                                 '%r' % r[3]]) + '\n'),
        ("ok(len(band) == 16,", "ok(len(band) == %d," % band),
        ("ok(len(house) == 19, '  %d house pairs in all' % len(house))",
         "ok(len(house) == %d, '  %%d house pairs in all' %% len(house))"
         % fam['house']),
        ("ok(len(sub2) >= 9,", "ok(len(sub2) >= %d," % sub2),
        # The docstring counts the same things the assertions do, and a
        # docstring that disagrees with the code below it is worse than
        # no docstring: it is a confident wrong answer to the question
        # the reader actually came with.
        ('    32  LIVE, and PINNED BY NAME rather than counted.',
         '    %d  LIVE, and PINNED BY NAME rather than counted.'
         % len(live)),
        ('AND THE 32 ARE NOT ANONYMOUS DEBT',
         'AND THE %d ARE NOT ANONYMOUS DEBT' % len(live)),
        ('''    19  HOUSE TOKEN ON HOUSE TOKEN. FIFTEEN are --alv-accent on an
        --alv-accent-soft / --alv-line-soft / --alv-surface-deep
        ground, 4.14 to 4.42 - the house pairing its own accent with
        its own tint and missing AA by a tenth. That is ONE BASE
        DECISION, not fifteen page fixes. --alv-accent-ink on
        --alv-accent-soft reads 6.53:1.

        TWO OF THE NINETEEN ARE NOT A TENTH.''',
         '''    %d  HOUSE TOKEN ON HOUSE TOKEN. EIGHTEEN are --alv-accent on an
        --alv-accent-soft / --alv-line-soft / --alv-surface-deep
        ground, 4.14 to 4.42 - the house pairing its own accent with
        its own tint and missing AA by a tenth. That is ONE BASE
        DECISION, not eighteen page fixes. --alv-accent-ink on
        --alv-accent-soft reads 6.53:1.

        THREE OF THE EIGHTEEN WERE ADDED BY AD-1, 8 Oct 2026, AND IT
        DID NOT CREATE THEM. The tabs on admin_apms and personal are
        written in page-local :root tokens and this census resolved
        var() against base alone, so not one tab rule in the tree was
        being counted. AD-1 taught it to read the page's own :root and
        701 pairs became 714. They were always there.

        TWO OF THE %d ARE NOT A TENTH.''' % (fam['house'], fam['house'])),
        ('count of nineteen.', 'count of %d.' % fam['house']),
        ('''     3  one-offs with no family: #ccc on white, #adb5bd on
        --alv-surface twice.''',
         '''     %d  one-offs with no family: #ccc on white, #adb5bd on
        --alv-surface twice, and the accent on a lilac tint.'''
         % fam['stray']),
        ('NOT PROVED HERE: that any of the 32 should be fixed. Each is a '
         'change',
         'NOT PROVED HERE: that any of the %d should be fixed. Each is a '
         'change' % len(live)),
        ("print('  NOT PROVED HERE: that any of the 32 should be fixed. "
         "Each is a')",
         "print('  NOT PROVED HERE: that any of the %d should be fixed. "
         "Each is a')" % len(live)),
        ("ok(len(worst) == 2,", "ok(len(worst) == %d," % worst),
        ("'5. TWO OF THE NINETEEN ARE NOT A TENTH SHORT'",
         "'5. TWO OF THE %d ARE NOT A TENTH SHORT'" % fam['house']),
        ("'%d of the %d house pairs sit in the 4.0-4.5 band - fifteen of them '",
         "'%d of the %d house pairs sit in the 4.0-4.5 band - EIGHTEEN of '"),
        ("'are --alv-accent on an --alv-accent-soft / --alv-line-soft / '\n"
         "   '--alv-surface-deep ground. THAT IS ONE BASE DECISION, not fifteen '\n"
         "   'page fixes' % (len(band), len(house)))",
         "'them are --alv-accent on an --alv-accent-soft / --alv-line-soft '\n"
         "   '/ --alv-surface-deep ground - THREE of those added by AD-1, "
         "which '\n"
         "   'did not create them, it taught the census to see a page own "
         "token. '\n"
         "   'THAT IS ONE BASE DECISION, not eighteen page fixes'\n"
         "   % (len(band), len(house)))"),
    ]
    for old, new in subs:
        if src.count(old) != 1:
            raise SystemExit('AD-1: %r in test_pair_contrast.py matched %d '
                             'time(s), not once' % (old[:60], src.count(old)))
        src = src.replace(old, new, 1)
    import ast as _ast
    try:
        _ast.parse(src)
    except SyntaxError as e:
        raise SystemExit('AD-1: test_pair_contrast.py would not parse - %s'
                         % e)
    reg[PC] = src

    # ---- test_personal_teal.py: the decision this round overturns ---
    PT = os.path.join(ROOT, 'test_personal_teal.py')
    tsrc = read(PT)
    OLD_T = ("    'admin_apms.html': ('--future-dark: #6c757d', '#5a6268', "
             "'#adb5bd'),\n")
    NEW_T = ("    # AD-1, 8 OCT 2026 - THE ADMIN HALF OF THIS CLAIM IS SPENT,\n"
             "    # and Demetri spent it: \"I want to change the System Tab to\n"
             "    # conform with our Teal colours. It must look and behave\n"
             "    # exactly like the Functional Tab with regards to colours.\"\n"
             "    #\n"
             "    # PT was right on the day. The FUTURE side WAS grey and the\n"
             "    # greens had to go without taking it with them. What PT could\n"
             "    # not know is that he would later want the grey gone too.\n"
             "    # So the claim is MOVED, not deleted: admin_apms now asserts\n"
             "    # the opposite, by name, and personal.html is untouched -\n"
             "    # its FUTURE tab is still commented out and still grey.\n"
             "    #\n"
             "    # B-4 overturned test_fsr_palette's decided #ecd9a8 in\n"
             "    # silence and had to be backed out. This is what the other\n"
             "    # way round looks like.\n"
             "    'admin_apms.html': (),\n")
    if tsrc.count(OLD_T) != 1:
        raise SystemExit('AD-1: the admin_apms line of PT UNTOUCHED matched '
                         '%d time(s), not once' % tsrc.count(OLD_T))
    tsrc = tsrc.replace(OLD_T, NEW_T, 1)
    try:
        _ast.parse(tsrc)
    except SyntaxError as e:
        raise SystemExit('AD-1: test_personal_teal.py would not parse - %s'
                         % e)
    reg[PT] = tsrc

    # ---- alv_rounds.ROUNDS -----------------------------------------
    NOTE = """    # AD-1, 8 Oct 2026 - the System tab, at his ask: "It must look
    # and behave exactly like the Functional Tab with regards to
    # colours." Two page-local tokens carry most of it - --future-dark
    # and --future-light repoint at --alv-accent and
    # --alv-accent-soft - and three rules that do not read them are
    # changed by hand, including the inactive hover, which was a
    # different colour from Functional's and so was false on hover too.
    #
    # ONE NUMBER GOES DOWN AND IT IS MEANT TO. The System tile was
    # white on --alv-ink-soft at 5.53:1 and is now white on
    # --alv-accent at 4.91:1, which is what Functional has always
    # read. Matching it is the instruction.
    #
    # THIS OVERTURNS test_personal_teal.py, WHICH DECIDED THE GREY.
    # PT's claim is moved rather than deleted, with his words and the
    # date beside it. B-4 overturned a decision in silence and had to
    # be backed out.
    #
    # The two Coming Soon tiles become RESERVED CELLS - no fill, no
    # border, no shadow, no hover, aria-hidden, pointer-events off -
    # so the panel keeps its height and growth lands in a space
    # already drawn. .btn-future-disabled goes with them, and with it
    # the last #adb5bd on the page that was not a live permission
    # state.
    #
    # And the pair census learns page-local :root tokens, because
    # every tab rule in the tree is written in one and not a single
    # one of them was being counted. 701 pairs became 714.
    '%s',
""" % SUFFIX
    for anchor in ("    '.bak_neutrals',\n]", "    '.bak_editink',\n]",
                   "    '.bak_amber',\n]"):
        if rounds.count(fit(rounds, anchor)) == 1:
            rounds = rounds.replace(fit(rounds, anchor),
                                    fit(rounds, anchor[:-2] + NOTE + ']'), 1)
            break
    else:
        raise SystemExit('AD-1: could not find the tail of ROUNDS')
    reg[ROUNDS] = rounds

    # ---- the PS1 $suites list --------------------------------------
    PS_NOTE = """    # AD-1, 8 Oct 2026 - the System tab in teal. Section 2 renders
    # both tabs in Chromium and asserts they compute the SAME
    # colours, which is the instruction word for word; section 3 is
    # the tile contrast, including the one number that went down on
    # purpose; section 4 is the reserved cells, which are not
    # disabled buttons; section 5 is the decision this round
    # overturned, and who overturned it.
    '%s'
)""" % SUITE_NAME
    for anchor in ("    'test_neutrals.py'\n)", "    'test_pair_contrast.py'\n)",
                   "    'test_amber.py'\n)"):
        if ps.count(fit(ps, anchor)) == 1:
            ps = ps.replace(fit(ps, anchor),
                            fit(ps, anchor[:-2] + ',\n' + PS_NOTE), 1)
            break
    else:
        raise SystemExit('AD-1: could not find the tail of $suites')
    reg[PS1] = ps
    return reg


def LIVE_FAM(live):
    """The census rows with the family that owns each one appended.

    house  - both colours are house token values. The accent on a house
             tint, 4.14 to 4.48, is ONE BASE DECISION and not N fixes.
    bright - a Bootstrap bright or a recipe orange. B-7 and RC-2.
    stray  - neither, and no family yet.
    """
    import apply_edit_ink as B
    tok = B.base_tokens()
    byval = {}
    for k, v in tok.items():
        h = B.resolve(v, tok)
        if h:
            byval.setdefault(h.lower(), []).append(k)
    BRIGHT = {'#ffc107', '#fd7e14', '#e0a800', '#20c997', '#1976d2',
              '#e65100'}
    out = []
    for page, sel, cr, bg, ink in live:
        if bg.lower() in byval and ink.lower() in byval:
            fam = 'house'
        elif bg.lower() in BRIGHT or ink.lower() in BRIGHT:
            fam = 'bright'
        else:
            fam = 'stray'
        out.append((page, sel, cr, fam))
    return out


def once(text, frag, what):
    n = text.count(fit(text, frag))
    if n != 1:
        raise SystemExit('AD-1: %s matched %d time(s), not once. The round '
                         'refuses rather than guessing which one was meant.'
                         % (what, n))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    os.chdir(ROOT)

    import apply_edit_ink as B

    rounds = read(ROUNDS)
    ps = read(PS1)
    if "'%s'" % SUFFIX in rounds:
        print('AD-1  already applied')
        return 1 if CHECK else 0

    path = T.path_of(PAGE)
    raw = read(path)
    out = raw

    # ---- 1. the colour ---------------------------------------------
    for old, new in CSS_EDITS:
        once(out, old, old.strip().splitlines()[0].strip())
        out = out.replace(fit(out, old), fit(out, new), 1)

    # ---- 2. the two tiles, and the rule only they used --------------
    once(out, TILES_OLD, 'the two Coming Soon tiles')
    out = out.replace(fit(out, TILES_OLD), fit(out, TILES_NEW), 1)
    once(out, DEAD_RULE, '.btn-future-disabled')
    out = out.replace(fit(out, DEAD_RULE), fit(out, RESERVED_RULE), 1)

    # A GATE READS CODE, NOT THE RECORD OF CODE - and this round proved
    # it twice on itself before it ever ran. Both checks below were
    # first written against the raw file, and both refused the round's
    # own correct work: the note that replaces .btn-future-disabled
    # explains what a reserved cell is NOT, and to do that it has to say
    # the class name and the literal it took away. A check that cannot
    # tell a declaration from a sentence about one will stop every round
    # that documents itself properly - which is every round here.
    #
    # T.code_only strips CSS comments, so this counts what the browser
    # will be sent and the prose is free to say whatever it needs to.
    body = T.code_only(out)
    left = [s for s in ('.btn-future-disabled',
                        'class="admin-btn btn-future-disabled"')
            if fit(body, s) in body]
    if left:
        raise SystemExit('AD-1: %s is still live on the page after the cut - '
                         'it had a user this round did not know about.'
                         % left)
    if body.count('#adb5bd') != 1:
        raise SystemExit('AD-1: %d live #adb5bd left on the page, expected 1 '
                         '- .btn-perm-disabled keeps its one and nothing '
                         'else should have had any.' % body.count('#adb5bd'))

    # ---- 3. what the colour change does to the numbers --------------
    tok = B.base_tokens()
    tile_was = B.contrast('#5b6b73', '#ffffff')
    tile_now = B.contrast(tok['--alv-accent'], '#ffffff')
    tab_was = B.contrast('#6c757d', '#e9ecef')
    tab_now = B.contrast(tok['--alv-accent'], tok['--alv-accent-soft'])
    print('AD-1  System tile  %.2f:1 -> %.2f:1   (Functional reads %.2f:1)'
          % (tile_was, tile_now, tile_now))
    print('AD-1  System tab   %.2f:1 -> %.2f:1   (Functional reads %.2f:1)'
          % (tab_was, tab_now, tab_now))
    if tile_now < 4.5:
        raise SystemExit('AD-1: the System tile would read %.2f:1, below AA'
                         % tile_now)
    if tab_now <= tab_was:
        raise SystemExit('AD-1: the tab would go from %.2f to %.2f - this '
                         'round is allowed to lower the tile to match '
                         'Functional, not the tab' % (tab_was, tab_now))

    # ---- 4. the census learns page-local :root tokens ---------------
    ED = os.path.join(ROOT, 'apply_edit_ink.py')
    esrc = read(ED)
    # The anchor is the file's own text, matched as a whole function, so
    # the round cannot half-replace a docstring it misremembered.
    m = re.search(r'def base_tokens\(\):.*?\n    return out\n',
                  esrc, re.S)
    if not m:
        raise SystemExit('AD-1: could not find base_tokens() in '
                         'apply_edit_ink.py')
    NEW_FN = '''def base_tokens(code=None):
    """Every --alv-* declared on a :root rule, name -> value.

    Base's own, plus - when `code` is a page's markup - that page's,
    which override base's for that page.

    AD-1, 8 Oct 2026: THIS USED TO READ BASE ONLY, AND THAT MADE IT
    BLIND TO THE TABS. admin_apms.html and personal.html write their
    tabs through page-local tokens (--alivente-dark, --future-light and
    the rest), so every tab rule resolved to None and was not counted.
    The System tab's active state was 3.95:1 and no instrument in the
    tree could see it. Measured when this was fixed: 701 pairs became
    714 and four more read below AA, three of them the same
    --alv-accent on --alv-accent-soft at 4.31 that section 5 already
    calls one base decision. They were always there.

    A page token that resolves to another token is chased by resolve(),
    so --alivente-dark: var(--alv-accent) lands on #0e7c8b.
    """
    out = {}
    srcs = [T.code_only(read(T.path_of('base.html')))]
    if code is not None:
        srcs.append(code)
    for src in srcs:
        for a, b in R.style_spans(src):
            for sel, ba, bb, _x, _y in R.rule_spans(src, a, b):
                if ':root' not in sel:
                    continue
                for k, v in re.findall(r'(--[\\w-]+)\\s*:\\s*([^;}]+)',
                                       src[ba:bb]):
                    out[k] = v.strip()
    return out
'''
    esrc = esrc[:m.start()] + NEW_FN + esrc[m.end():]
    # and census() must hand the page's own markup to it
    OLD_CEN = '''        code = T.code_only(override.get(p) or read(p))
        for sel, (bg, ink) in pair_table(code, tok).items():'''
    NEW_CEN = '''        code = T.code_only(override.get(p) or read(p))
        # AD-1: the page's OWN :root as well as base's, or every rule
        # written in a page-local token goes uncounted.
        for sel, (bg, ink) in pair_table(code, base_tokens(code)).items():'''
    if esrc.count(OLD_CEN) != 1:
        raise SystemExit('AD-1: census() does not read as expected in '
                         'apply_edit_ink.py')
    esrc = esrc.replace(OLD_CEN, NEW_CEN, 1)
    esrc = esrc.replace('''    tok = base_tokens()
    override = override or {}''', '''    override = override or {}''', 1)
    import ast as _ast
    try:
        _ast.parse(esrc)
    except SyntaxError as e:
        raise SystemExit('AD-1: apply_edit_ink.py would not parse - %s' % e)

    # ---- 5. what the census will read, measured off the PLAN --------
    # A patcher verifies, then writes. The new base_tokens() and the new
    # page are both loaded here as text and run against a copy of the
    # tree in memory - nothing on disk has moved yet.
    ns = {'__file__': ED, '__name__': 'apply_edit_ink_ad1'}
    exec(compile(esrc, ED, 'exec'), ns)                    # noqa: S102
    before_n, before_live, before_dead = B.census()
    after_n, after_live, after_dead = ns['census']({path: out})
    added = sorted(set((r[0], r[1]) for r in after_live)
                   - set((r[0], r[1]) for r in before_live))
    gone = sorted(set((r[0], r[1]) for r in before_live)
                  - set((r[0], r[1]) for r in after_live))
    print('AD-1  pair census %d -> %d pairs, %d -> %d live below AA'
          % (before_n, after_n, len(before_live), len(after_live)))
    if (before_n, after_n) != (EXPECT_PAIRS_BEFORE, EXPECT_PAIRS_AFTER):
        raise SystemExit('AD-1: the census reads %d -> %d pairs, expected '
                         '%d -> %d. It will not write a number it has not '
                         'measured.' % (before_n, after_n,
                                        EXPECT_PAIRS_BEFORE,
                                        EXPECT_PAIRS_AFTER))
    if gone:
        raise SystemExit('AD-1: %s stopped failing. This round changes one '
                         'page colour and opens the census eyes - it is not '
                         'allowed to make a pinned failure disappear.'
                         % (gone,))
    if sorted(added) != sorted(EXPECT_ADDED):
        raise SystemExit('AD-1: the eyes opened onto %s, expected %s'
                         % (added, EXPECT_ADDED))
    if len(after_dead) != len(before_dead):
        raise SystemExit('AD-1: inactive pairs below AA moved %d -> %d - '
                         'this round touches no disabled state'
                         % (len(before_dead), len(after_dead)))
    # AND THE ONE IT IMPROVED, which is the whole reason the eyes matter.
    tab = [r for r in after_live
           if r[0] == PAGE and r[1] == '.admin-tab.future-tab.active']
    if len(tab) != 1 or abs(tab[0][2] - 4.31) > .02:
        raise SystemExit('AD-1: the System tab active state reads %s, '
                         'expected 4.31 - the same as Functional'
                         % ([r[2] for r in tab],))

    reg = resolve_registration(rounds, ps, after_live, after_dead, after_n)
    print('AD-1  %d registry/suite file(s) resolved, every anchor found'
          % len(reg))

    if CHECK:
        print('AD-1  NOT APPLIED')
        return 1

    # ---- NOW, and only now -----------------------------------------
    backup(path)
    write(path, out)
    backup(ED)
    write(ED, esrc)
    for p, new in reg.items():
        backup(p)
        write(p, new)
    print('AD-1  pair census now reads page-local :root tokens')
    print('AD-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
