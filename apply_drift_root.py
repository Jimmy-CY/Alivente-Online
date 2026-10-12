# -*- coding: utf-8 -*-
"""apply_drift_root.py - round E-10, 11 Oct 2026.

THE CLASSIFIER COULD NOT OPEN A FILE IT WAS HANDED, SO FOR A FORTNIGHT
TWELVE BUTTONS DISAGREED WITH IT IN SILENCE.

`Show-ButtonDrift.py` builds one path, once:

    TPL = os.path.join(ROOT, 'pages', 'templates')

and then resolves EVERY name it is given against it. Hand `scan()` the
label 'crs/submission_detail.html' - which is what alv_tree.rel()
produces for the CRS app, a second Django template root - and it opens

    pages/templates/crs/submission_detail.html

which has never existed. FileNotFoundError.

WHAT THAT HID, IN THREE PLACES
------------------------------
1. test_disabled_state.py, section 5, widened: eight failures, one per
   CRS page, every one of them `the scan raised [Errno 2]`. Its handler
   turns a crash into a line of drift, so eight unopenable pages read as
   eight drifting buttons. The entry on alv_tree.WAITING said twelve,
   which was right, and said nothing about the cause.

2. apply_no_primary.py, a shipped round, already walks the WHOLE tree
   and calls sbd.scan(rel) inside

       except Exception:
           continue

   It has been crashing on eight of 125 pages, swallowing it, and then
   printing 'no button disagrees with the classifier'. A control that
   cannot fail is worse than no control, and this one was printing a
   reassurance.

3. test_disabled_state's closing paragraph, every run:

       base has no [disabled] rule for .action-danger or .action-back,
       so a disabled button in either tone still needs the class.
       NOTHING IN THE TREE IS IN THAT POSITION TODAY.

   False, and false since the CRS app arrived.

RESOLUTION IS WIDENED. THE CENSUS IS NOT.
-----------------------------------------
TPL is named in nine places and they are two different jobs.

  RESOLUTION - a name the tool was handed. All seven go through
      alv_tree, including the three that are DORMANT because they
      iterate names the tool's own census produced. A dormant narrow
      lookup is invisible until the tree widens under it; that lesson
      has been paid for twice and this is the cheap half of it.
      `--full crs/submission_detail.html` starts working as a side
      effect.

  CENSUS - os.walk(TPL), its relpath, and the isdir guard. UNCHANGED,
      and TPL keeps its value, because apply_button_sweep.py line 67 is
      `TPL = sb.TPL` and test_button_sweep.py line 114 is
      `FILES = sb.templates(False)` - and that suite is held BECAUSE
      its narrow root is a stated position, not debt: its os.walk(TPL)
      rebuilds a pre-sweep tree from that round's own backups.

So: the tool keeps its own scope and stops lying about a name it was
given. What guards the CRS app is test_disabled_state's section 5,
which walks alv_tree - and that is what this round releases.

A CLASS IS A TOKEN, NOT A SUBSTRING
-----------------------------------
footers() matched `class="[^"]*modal-footer[^"]*"`, so it caught
`<div class="xml-modal-footer">` - the XML Viewer's own footer - and
plan_footer then read Close as the cancel and promoted Download to
action-primary: a solid teal Download link.

Counted: `xml-modal-footer` is the ONLY wrapper in 151 templates whose
name contains `modal-footer` without being it, and switching the
matcher to a class TOKEN moves exactly ONE page out of 150 - that one.
Wrapper census across the tree: 89 -> 88.

THE TWELVE, AND WHAT THEY ACTUALLY ARE
--------------------------------------
Not one finding. Measured in Chromium against base's stylesheet and the
Bootstrap 4.1.3 fixture, in a page bar, a .modal-footer and a loose
card, with the fixture's remote stylesheet refused:

  SIX ARE STILL WEARING BOOTSTRAP. The three CRS delete-confirmation
      modals carry `btn btn-secondary` Cancel beside `btn btn-danger`
      Delete. Base loads Bootstrap 4.1.3, so those render SOLID:
      rgb(108,117,125) and rgb(220,53,69), white text. Every equivalent
      modal in the rest of the app is rgb(255,255,255) with a soft
      border. Visible, on three screens, and it survived the button
      sweep only because the sweep could not see the app.

  FOUR ARE NOT A DEFECT AT ALL. `btn action-danger` and
      `btn action-secondary action-danger` measure IDENTICAL across
      eleven computed properties in all three wrappers: .action-danger
      is declared after .action-secondary and overrides the three
      declarations they share, and .btn.action-danger is already in
      base's min-height:44px list, so the phone tap target is right
      either way. The pair is a class-list convention here. They are
      paired anyway, because the tree being a fixed point of the
      classifier is what lets the suite be released - but presenting
      these four as drift would have oversold the round.

  ONE IS THE ROUND. crs/submission_detail.html's Close button, off
      until XSD validation passes:

          <button type="button" class="btn action-danger" disabled>

      Base greys a switched-off button through two blocks that name
      action-primary and action-secondary and NO danger tone. Measured:

          btn action-danger        + disabled   text rgb(179,38,30)
          btn action-secondary     + disabled   text rgb(138,151,157)
          btn action-primary       + disabled   text rgb(138,151,157)
          btn action-secondary
            action-danger          + disabled   text rgb(138,151,157)

      It was the ONLY switched-off button in the application that was
      not grey, and all of its dimming came from Bootstrap's
      .btn:disabled{opacity:.65}.

      Base gets the rule, in the same five shapes the primary block
      already uses, because the colour of a switched-off button belongs
      where the other two tones keep it and not in a class list on one
      page. The page gets the pair as well, and `disabled-btn`, because
      the classifier asks for all three and the tree has to be a fixed
      point of it - measured: 553 hits, 0 drift, and 0 again on a
      second pass over the round's own output.

  ONE IS THE PROMOTION, AND IT IS NOT TAKEN. The xml-modal-footer
      Download stays rgb(255,255,255). The matcher change removes the
      ask rather than arguing with it.

WHAT THIS ROUND DOES NOT DO
---------------------------
It does not widen the tool's census, so `Show-ButtonDrift.py --strict`
on the push gate sees exactly what it saw before. It does not touch the
recipe side, which the tool excludes by name and lists as an agreed
follow-up - 57 drifting buttons there, unchanged and still excluded. It
does not give base an [disabled] rule for .action-back: measured, there
are ZERO switched-off action-back controls in the tree, and a rule for
nothing is a control that cannot fail.

FOUR STILL HELD after this: test_back_label, test_small_three,
test_modal_heads and test_surface_deep - the last waiting on F2b, and
test_button_sweep beside them on a narrow root that is a decision.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SUFFIX = '.bak_driftroot'
SUITE = 'test_drift_root.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
X0 = 'test_tree_roots.py'
SBD = 'Show-ButtonDrift.py'
DS = 'test_disabled_state.py'
NP = 'apply_no_primary.py'
HC = 'test_held_contrast.py'
BH = 'test_bar_height.py'
PC = 'test_pair_contrast.py'
BASE = 'base.html'
CHECK = False

# A ROUND THAT CHANGES A NUMBER OWNS EVERY NUMBER THAT COUNTS IT, and
# the sweep is how the list of them is found rather than guessed. Every
# one of these was MEASURED by running the suite against the applied
# tree, not reasoned about.
#
# D-1's heights: its census selects `.action-primary, .action-secondary,
# .action-back, .action-filter, .action-more-btn, .icon-action-btn` and
# NOT .action-danger - a third place the danger tone was invisible. The
# twelve buttons this round pairs become visible to it: seven in modals
# (six Bootstrap Cancels and Deletes, plus submission_detail's own
# modal Delete) and four loose in cards. NOT TAKEN HERE: one unpaired
# `btn action-danger btn-sm` survives on act_expense.html and is still
# invisible to that selector. Widening someone else's census is their
# round; this one re-pins the numbers it moved and names what it found.
MODAL_WAS, MODAL_NOW = 91, 98
LOOSE_WAS, LOOSE_NOW = 78, 82

# B-4b's pair census: base's new block sets a background AND a colour
# under five selectors, so the tree-wide census rises by five and the
# five join the INACTIVE exemption - WCAG 1.4.3 exempts text that is
# part of an inactive user interface component, which is precisely what
# a switched-off danger is. test_recipe_spice reads EXPECT_PAIRS off
# this file rather than keeping a copy, so it needs nothing.
PAIRS_WAS, PAIRS_NOW = 711, 716
INACTIVE_WAS, INACTIVE_NOW = 20, 25
NEW_INACTIVE = (
    "    ('base.html', '.action-danger.disabled-btn', 2.53),\n"
    "    ('base.html', '.btn.action-danger.disabled-btn', 2.53),\n"
    "    ('base.html', '.btn.action-danger:disabled', 2.53),\n"
    "    ('base.html', '.btn.action-danger[disabled]', 2.53),\n"
    "    ('base.html', '.btn.action-danger[aria-disabled=\"true\"]', 2.53),\n")

RELEASED = ('test_disabled_state.py',)

# The twelve, by file and by what they carry. Counted here so the
# patcher refuses rather than half-applies.
BOOTSTRAP_PAGES = ('crs/country_list.html', 'crs/fi_list.html',
                   'crs/submission_list.html')
DANGER_PAGE = 'crs/submission_detail.html'
N_BARE_DANGER = 4          # plus the one disabled, handled separately
N_FOOTER_SUBSTRING = 89    # wrappers the substring matcher finds
N_FOOTER_TOKEN = 88        # and the token matcher, tree-wide

CEILING_WAS, CEILING_NOW = 43, 42
CONVERTED_WAS, CONVERTED_NOW = 61, 63
WAITING_WAS, WAITING_NOW = 6, 5


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
    raise SystemExit('E-10 REFUSED: %s' % msg)


def once(text, lit, where):
    n = text.count(lit)
    if n != 1:
        refuse('%s: %r appears %d time(s), expected exactly 1'
               % (where, lit[:60], n))
    return n


# -------------------------------------------------------------- base.html
# The same five shapes the primary block covers, for the same reason.
DANGER_OFF = """
      /* AND A SWITCHED-OFF DANGER. E-10, 11 Oct 2026.
         The two blocks above name action-primary and action-secondary and
         no danger tone, so `btn action-danger` carrying the disabled
         attribute kept its soft red border and its red text and took the
         whole of its dimming from Bootstrap's .btn:disabled{opacity:.65}.

         Measured on crs/submission_detail.html's Close button - off until
         XSD validation passes on every file:

             btn action-danger      + disabled   text rgb(179, 38, 30)
             btn action-secondary   + disabled   text rgb(138, 151, 157)
             btn action-primary     + disabled   text rgb(138, 151, 157)

         It was the only switched-off button in the application that was
         not grey. The colour is half of "disabled"; it belongs where the
         other two tones keep it, not in a class list on one page.

         test_disabled_state.py printed "nothing in the tree is in that
         position today" on every run while that button existed - its
         census could not open the CRS app, and its own tone list named
         only primary and secondary, so neither half of it could see.

         NOT action-back. Measured the same day: ZERO switched-off
         action-back controls exist in the tree, and a rule for nothing
         is a control that cannot fail. */
      .action-danger.disabled-btn,
      .btn.action-danger.disabled-btn,
      .btn.action-danger:disabled,
      .btn.action-danger[disabled],
      .btn.action-danger[aria-disabled="true"] {
        background: var(--alv-disabled-bg, var(--alv-surface-deep));
        border-color: var(--alv-disabled-bg, var(--alv-surface-deep));
        color: var(--alv-disabled-ink, var(--alv-ink-faint));
        box-shadow: none;
      }
"""

# --------------------------------------------------- Show-ButtonDrift.py
RESOLVER = '''

def resolve(name):
    """The file a NAME means, under whichever template root holds it.

    E-10, 11 Oct 2026. Every one of these used to be
    `os.path.join(TPL, name)`, and TPL is pages/templates alone. Handed
    'crs/submission_detail.html' - which is what alv_tree.rel() calls
    the CRS app's pages, and what every widened census hands back - that
    named a file which has never existed, and scan() died with a
    FileNotFoundError rather than a verdict.

    THIS WIDENS RESOLUTION, NOT SCOPE. templates() below still walks TPL
    and only TPL, because apply_button_sweep.py reads `sb.TPL` and
    test_button_sweep.py reads `sb.templates(False)` - and that suite's
    narrow root is a decision: it rebuilds a pre-sweep tree from its own
    backups. The tool keeps its scope and stops lying about a name it
    was given.

    base= is pinned to this file's directory rather than left to the cwd,
    so the resolver and TPL cannot disagree about which repo they are in.
    """
    return alv_tree.join(name, base=ROOT)
'''

FOOTER_OLD = """def footers(m):
    return [('modal footer', a, z)
            for a, z in spans(m, r'<div[^>]*class="[^"]*modal-footer[^"]*"'
                                 r'[^>]*>')]"""

FOOTER_NEW = '''# A CLASS IS A TOKEN, NOT A SUBSTRING - E-10, 11 Oct 2026.
#
# This matched `[^"]*modal-footer[^"]*`, so it caught
# `<div class="xml-modal-footer">` - the XML Viewer's own footer on
# crs/submission_detail.html - and plan_footer then read Close as the
# cancel and promoted Download to action-primary: a solid teal Download
# link, asked for by a substring.
#
# COUNTED BEFORE CHANGING IT, because the same loose match is what lets
# this function see `class="modal-footer mt-3"` and every other spelling
# with a second class. `xml-modal-footer` is the ONLY wrapper in 151
# templates whose name contains `modal-footer` without being it; the
# tree-wide wrapper census goes 89 -> 88 and exactly ONE page of 150
# changes its plan. The docstring at the top of this file is about a
# matcher that could not see two thirds of the bars. This is the other
# direction of the same error, and it is one instance wide.
FOOTER_DIV = (r'<div[^>]*class="[^"]*(?<![-\\w])modal-footer(?![-\\w])'
              r'[^"]*"[^>]*>')


def footers(m):
    return [('modal footer', a, z) for a, z in spans(m, FOOTER_DIV)]'''

# ---------------------------------------------------- apply_no_primary.py
SWALLOW_OLD = """    except Exception:
        continue
for d in drift[:8]:"""

SWALLOW_NEW = """    # E-10, 11 Oct 2026 - WAS a bare `except Exception: continue`.
    # This gate walks the WHOLE tree, and sbd.scan() could not open the
    # eight CRS pages, so it crashed on eight of 125 and then printed
    # that nothing disagrees with the classifier. It printed that for a
    # fortnight while twelve buttons did. A control that cannot fail is
    # worse than no control, so a crash is now reported as what it is.
    except Exception as _e:
        drift.append('%s: the scan raised %s' % (rel, str(_e)[:48]))
for d in drift[:8]:"""


def widen_suite(text):
    """test_disabled_state's own census, onto alv_tree.

    THE WALK IS NOT THE ONLY NARROW SITE, and X0 shipped without the
    inverse on day one: a census that takes a label back and rebuilds a
    path from it resolves against whichever root it happens to know.
    test_waiting_down counts those and names the file, which is how the
    one left here was found - `BASE = os.path.join(T, 'base.html')`,
    harmless today because base lives under the first root, and a
    dormant narrow lookup is invisible until the tree widens under it.
    """
    n = 0
    if 'import alv_tree' not in text:
        once(text, 'import sys\n', DS)
        text = text.replace('import sys\n', 'import sys\n\nimport alv_tree\n',
                            1)
        n += 1
    for old, new in (
            ('    for dirpath, _d, names in os.walk(T):',
             '    for dirpath, _d, names in alv_tree.walk3():'),
            ("            rel = os.path.relpath(os.path.join(dirpath, n), T)\n"
             "            rel = rel.replace(os.sep, '/')",
             '            rel = alv_tree.rel(os.path.join(dirpath, n))'),
            ("BASE = os.path.join(T, 'base.html')",
             "BASE = alv_tree.path_of('base.html')")):
        once(text, old, DS)
        text = text.replace(old, new, 1)
        n += 1
    if 'os.walk(T)' in text:
        refuse('%s still walks its own root after widening' % DS)
    if re.search(r'os\.path\.join\(\s*T\s*,', text):
        refuse('%s still resolves a label against its own root - '
               'test_waiting_down counts these' % DS)
    return text, n


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    sys.path.insert(0, root)
    import alv_tree as T

    sbd_p = os.path.join(root, SBD)
    base_p = T.path_of(BASE)
    danger_p = T.path_of(DANGER_PAGE)

    # ---------------------------------------------------------------- 0
    # A PATCHER VERIFIES, THEN WRITES - and the already-applied check
    # comes FIRST, before any gate that would be false on a tree this
    # round has already finished with.
    if 'def resolve(name):' in read(sbd_p):
        print('E-10  already applied')
        return 0

    if not os.path.isfile(os.path.join(root, SUITE)):
        refuse('%s is not on disk - the suite ships with the round' % SUITE)

    # ---------------------------------------------------------------- 1
    # THE TOOL. Resolution widens; the census does not.
    sbd = read(sbd_p)
    once(sbd, "TPL = os.path.join(ROOT, 'pages', 'templates')", SBD)

    joins = re.findall(r'os\.path\.join\(TPL,\s*(\w+)\)', sbd)
    if len(joins) != 6:
        refuse('%s has %d `os.path.join(TPL, x)` site(s), expected the six '
               'this round surveyed: %s' % (SBD, len(joins), joins))
    walks = sbd.count('os.walk(TPL)')
    if walks != 1:
        refuse('%s walks TPL %d time(s) - the census this round LEAVES '
               'ALONE is meant to be exactly one' % (SBD, walks))

    nsbd = sbd.replace(
        "ROOT = os.path.dirname(os.path.abspath(__file__))\n"
        "TPL = os.path.join(ROOT, 'pages', 'templates')",
        "ROOT = os.path.dirname(os.path.abspath(__file__))\n"
        "sys.path.insert(0, ROOT)\n"
        "import alv_tree                                       # noqa: E402\n"
        "\n"
        "# pages/templates ONLY, and deliberately. templates() below is\n"
        "# this tool's own SCOPE, and two callers read it as such:\n"
        "# apply_button_sweep.py takes `sb.TPL` and test_button_sweep.py\n"
        "# takes `sb.templates(False)`, whose narrow root rebuilds a\n"
        "# pre-sweep tree from that round's own backups. Widening a scope\n"
        "# somebody is standing on is a different round. What E-10 widens\n"
        "# is resolve(), below - the way back from a NAME to a file.\n"
        "TPL = os.path.join(ROOT, 'pages', 'templates')", 1)
    if nsbd == sbd:
        refuse('%s: the ROOT/TPL block is not where this round expects' % SBD)

    # THE REWRITE FIRST, THE DOCSTRING AFTERWARDS. The resolver's own
    # docstring QUOTES the call it replaces, so inserting it before the
    # substitution hands the substitution a seventh site to rewrite -
    # inside prose. The first run of this patcher refused on exactly
    # that, which is the gate working.
    nsbd, k = re.subn(r'os\.path\.join\(TPL,\s*(\w+)\)',
                      lambda m: 'resolve(%s)' % m.group(1), nsbd)
    if k != 6:
        refuse('%s: rewrote %d resolution site(s), expected 6' % (SBD, k))

    anchor = '\n\ndef read(p):'
    once(nsbd, anchor, SBD)
    nsbd = nsbd.replace(anchor, RESOLVER + anchor, 1)
    if nsbd.count('os.walk(TPL)') != 1:
        refuse('%s: the census walk did not survive the rewrite' % SBD)

    once(nsbd, FOOTER_OLD, SBD)
    nsbd = nsbd.replace(FOOTER_OLD, FOOTER_NEW, 1)

    # THE COUNT THE MATCHER CHANGE RESTS ON, measured against the tree
    # rather than taken from the header. One wrapper, one page.
    loose = re.compile(r'<div[^>]*class="[^"]*modal-footer[^"]*"[^>]*>')
    tight = re.compile(r'<div[^>]*class="[^"]*(?<![-\w])modal-footer'
                       r'(?![-\w])[^"]*"[^>]*>')
    n_loose = n_tight = 0
    odd = []
    for p in T.templates():
        mk = read(p)
        a, b = len(loose.findall(mk)), len(tight.findall(mk))
        n_loose += a
        n_tight += b
        if a != b:
            odd.append(T.rel(p))
    if (n_loose, n_tight) != (N_FOOTER_SUBSTRING, N_FOOTER_TOKEN):
        refuse('the footer wrapper census is %d substring / %d token, and '
               'this round was built on %d / %d'
               % (n_loose, n_tight, N_FOOTER_SUBSTRING, N_FOOTER_TOKEN))
    if odd != [DANGER_PAGE]:
        refuse('the token matcher changes %s, and this round was built on '
               'exactly %s' % (odd, [DANGER_PAGE]))

    # ---------------------------------------------------------------- 2
    # BASE TAKES THE SWITCHED-OFF DANGER.
    b = read(base_p)
    if '.action-danger.disabled-btn' in b:
        refuse('%s already carries a switched-off danger rule' % BASE)
    m = re.search(r'\n(\s*)\.action-primary\.disabled-btn,'
                  r'[\s\S]{0,600}?\n\s*\}\r?\n', b)
    if not m:
        refuse('%s: the switched-off PRIMARY block is not where this round '
               'expects to sit beneath it' % BASE)
    crlf = '\r\n' in b
    block = DANGER_OFF
    if crlf:
        block = block.replace('\n', '\r\n')
    nb = b[:m.end()] + block + b[m.end():]
    # THE COLOUR RULE IT HAS TO BEAT must come EARLIER in the sheet, or
    # :hover of equal specificity wins on a button that can still be
    # hovered - a bare `disabled` attribute does not stop that.
    for sel in ('.action-danger:hover', '.action-danger,'):
        i = nb.find(sel)
        if i < 0 or i > nb.find('.action-danger.disabled-btn'):
            refuse('%s: %s does not sit above the new switched-off block'
                   % (BASE, sel))

    # ---------------------------------------------------------------- 3
    # THE TWELVE.
    pages = {}
    for rel in BOOTSTRAP_PAGES:
        p = T.path_of(rel)
        t = read(p)
        for old, new in (
                ('class="btn btn-secondary" data-dismiss="modal">Cancel',
                 'class="btn action-secondary" data-dismiss="modal">Cancel'),
                ('class="btn btn-danger"',
                 'class="btn action-secondary action-danger"')):
            once(t, old, rel)
            t = t.replace(old, new, 1)
        if 'btn-danger' in t or 'btn-secondary' in t:
            refuse('%s still carries a Bootstrap tone after the sweep' % rel)
        pages[p] = t

    t = read(danger_p)
    off_old = 'class="btn action-danger" disabled>'
    once(t, off_old, DANGER_PAGE)
    t = t.replace(
        off_old,
        'class="btn action-secondary action-danger disabled-btn" disabled>', 1)
    bare = 'class="btn action-danger"'
    if t.count(bare) != N_BARE_DANGER:
        refuse('%s carries %d bare action-danger after the disabled one, '
               'expected %d' % (DANGER_PAGE, t.count(bare), N_BARE_DANGER))
    t = t.replace(bare, 'class="btn action-secondary action-danger"')
    if re.search(r'class="btn action-danger(?![-\w])', t):
        refuse('%s still carries an unpaired action-danger' % DANGER_PAGE)
    # AND THE PROMOTION THIS ROUND REFUSES. Download stays paper.
    if 'id="xmlViewerDownload" href="#" class="btn action-secondary"' not in t:
        refuse('%s: the XML Viewer Download is not where this round leaves '
               'it alone' % DANGER_PAGE)
    pages[danger_p] = t

    # ---------------------------------------------------------------- 4
    # THE SUITE, WIDENED AND EXTENDED.
    ds = read(os.path.join(root, DS))
    nds, n = widen_suite(ds)
    if n < 3:
        refuse('%s: widening changed %d thing(s) - that is a no-op'
               % (DS, n))

    # THE TONE LIST WAS THE OTHER HALF OF THE BLINDNESS. Section 3 only
    # looks at buttons whose class list carries one of these, and the
    # one button this round is about carried neither. Measured: adding
    # the danger tone adds exactly ONE control to the census, and it is
    # that button.
    tones_old = "TONES = ('action-primary', 'action-secondary')"
    once(nds, tones_old, DS)
    nds = nds.replace(
        tones_old,
        "# E-10, 11 Oct 2026 - action-danger joins. WIDENING THE WALK WAS\n"
        "# HALF THE FIX. Section 3 skips any button whose class list\n"
        "# carries none of these, and crs/submission_detail.html's\n"
        "# switched-off Close carried `btn action-danger` - neither of the\n"
        "# two. So the one control in the tree that this suite exists to\n"
        "# notice was invisible to it twice over, and its closing\n"
        "# paragraph said so was nothing. Measured: the danger tone adds\n"
        "# exactly ONE control to section 3's census - 10 static to 11 -\n"
        "# and it is that button.\n"
        "TONES = ('action-primary', 'action-secondary', 'action-danger')", 1)

    # AND THE CONTROL THAT WAS BUILT ON THE DEFECT. Section 1 proved its
    # own search was not vacuous with
    #     '.btn.action-danger[disabled]' not in B
    # and the extra read 'danger has no attribute rule'. Base now has
    # one, so the control goes false on the round that fixes the thing
    # it was leaning on. Repointed to action-back, which base really
    # does not cover - and section 7 counts how many controls are in
    # that position, which is the shape this whole round is about.
    ctrl_old = """check('  CONTROL: and the search would notice one missing',
      '.btn.action-danger[disabled]' not in B,
      'danger has no attribute rule - so this is not vacuous')"""
    once(nds, ctrl_old, DS)
    nds = nds.replace(
        ctrl_old,
        """# E-10, 11 Oct 2026 - WAS the danger tone. Base now greys a
# switched-off danger, so this control went false on the round that
# fixed what it was leaning on. action-back is the tone base really
# does not cover, and section 7 counts what is in that position
# instead of asserting it.
check('  CONTROL: and the search would notice one missing',
      '.btn.action-back[disabled]' not in B,
      'action-back has no attribute rule - so this is not vacuous')""", 1)

    tail_old = """print('  base has no [disabled] rule for .action-danger or .action-back, so')
print('  a disabled button in either tone still needs the class. Nothing in')
print('  the tree is in that position today; section 1 says so out loud.')"""
    once(nds, tail_old, DS)
    nds = nds.replace(
        tail_old,
        """# E-10, 11 Oct 2026 - THIS PARAGRAPH WAS FALSE, and had been since
# the CRS app arrived. crs/submission_detail.html's Close button was
# exactly that position - `btn action-danger` with the disabled
# attribute and no class - and this suite could not see the page,
# could not see the tone, and printed a reassurance instead. Base now
# carries the rule. What is still true is said below, and COUNTED.
print('  base greys a switched-off primary, secondary and - since E-10 -')
print('  danger. It has no [disabled] rule for .action-back, and section 7')
print('  counts how many switched-off action-back controls exist rather')
print('  than asserting there are none: that sentence is what hid a real')
print('  button for a fortnight.')""", 1)

    # ---------------------------------------------------------------- 4b
    # A SHARED TOOL THAT GAINS A DEPENDENCY OWNS EVERY HARNESS THAT
    # COPIES IT.
    #
    # test_button_sweep rebuilds a pre-sweep tree in a temp directory
    # three separate times and copies Show-ButtonDrift.py into it. The
    # moment the tool imports alv_tree, all three copies run a tool
    # whose import fails - and the failure arrives as an EMPTY REPORT,
    # not an error: the harness greps stdout for lines, finds none, and
    # says '--check and a real run report the same 0 line(s)'. Six
    # checks in that suite went red together and not one of them said
    # 'ImportError'. Found by running it, which is the only way this
    # shape is ever found.
    #
    # The copy lists are widened; the experiment is not. Each temp tree
    # holds pages/templates and nothing else, and alv_tree.roots()
    # SKIPS a root that is not on disk - so resolve() there returns
    # exactly what os.path.join(TPL, ...) returned, and the rebuilt
    # tree stays the narrow experiment it is meant to be.
    bs = read(os.path.join(root, 'test_button_sweep.py'))
    for old, new in (
            ("    for _n in ('Show-ButtonDrift.py', 'apply_button_sweep.py'):",
             "    # E-10, 11 Oct 2026 - alv_tree.py joins: the tool imports\n"
             "    # it now, and a tool that cannot import reports NOTHING\n"
             "    # rather than failing, which is how this was found.\n"
             "    for _n in ('Show-ButtonDrift.py', 'apply_button_sweep.py',\n"
             "               'alv_tree.py'):"),
            ("    shutil.copy2(os.path.join(ROOT, 'Show-ButtonDrift.py'), tmp)",
             "    for _dep in ('Show-ButtonDrift.py', 'alv_tree.py'):\n"
             "        shutil.copy2(os.path.join(ROOT, _dep), tmp)"),
            ("    for _f in ('Show-ButtonDrift.py', 'apply_button_sweep.py'):",
             "    for _f in ('Show-ButtonDrift.py', 'apply_button_sweep.py',\n"
             "               'alv_tree.py'):")):
        once(bs, old, 'test_button_sweep.py')
        bs = bs.replace(old, new, 1)
    nbs = bs

    # ---------------------------------------------------------------- 4c
    # THE TWO CENSUSES THE TWELVE WALK INTO. Found by the sweep, which
    # is the only honest way to find them.
    bh = read(os.path.join(root, BH))
    old_bh = 'N_BAR, N_ROW, N_MODAL = 265, 110, %d' % MODAL_WAS
    once(bh, old_bh, BH)
    bh = bh.replace(
        old_bh,
        'N_BAR, N_ROW, N_MODAL = 265, 110, %d   # E-10, 11 Oct 2026 - the\n'
        '# seven buttons this round paired in CRS modals become visible to\n'
        '# a census that selects the two position tones and not the danger\n'
        '# tone.   # (was %d)' % (MODAL_NOW, MODAL_WAS), 1)
    old_lo = 'N_LOOSE, N_LOOSE_H = %d, 12' % LOOSE_WAS
    once(bh, old_lo, BH)
    nbh = bh.replace(
        old_lo,
        'N_LOOSE, N_LOOSE_H = %d, 12   # E-10 - and the four loose in\n'
        '# cards on crs/submission_detail.html, for the same reason. The\n'
        '# twelve distinct heights are unchanged.   # (was %d)'
        % (LOOSE_NOW, LOOSE_WAS), 1)

    pc = read(os.path.join(root, PC))
    old_p = 'EXPECT_PAIRS = %d' % PAIRS_WAS
    once(pc, old_p, PC)
    pc = pc.replace(
        old_p,
        'EXPECT_PAIRS = %d   # E-10, 11 Oct 2026 - base switched-off\n'
        '# danger sets a background AND a colour, under five selectors.\n'
        '#   # (was %d)' % (PAIRS_NOW, PAIRS_WAS), 1)
    old_i = 'EXPECT_INACTIVE = %d' % INACTIVE_WAS
    once(pc, old_i, PC)
    pc = pc.replace(
        old_i,
        'EXPECT_INACTIVE = %d   # E-10 - the same five. WCAG 1.4.3\n'
        '# exempts text that is part of an inactive user interface\n'
        '# component, which is what a switched-off danger is.   # (was %d)'
        % (INACTIVE_NOW, INACTIVE_WAS), 1)
    i_anchor = ("    ('base.html', '.action-primary.disabled-btn', 2.53),\n")
    once(pc, i_anchor, PC)
    npc = pc.replace(i_anchor, i_anchor + NEW_INACTIVE, 1)

    # ---------------------------------------------------------------- 5
    # THE SWALLOW.
    np = read(os.path.join(root, NP))
    once(np, SWALLOW_OLD, NP)
    nnp = np.replace(SWALLOW_OLD, SWALLOW_NEW, 1)

    # ---------------------------------------------------------------- 6
    # THE REGISTERS.
    tree = read(os.path.join(root, TREE))
    for name in RELEASED:
        line = [l for l in tree.split('\n')
                if l.strip().startswith("'%s':" % name)]
        if len(line) != 1:
            refuse('%s is not on alv_tree.WAITING exactly once' % name)
        start = tree.index(line[0])
        end = tree.index("',\n", start) + 3
        tree = tree[:start] + tree[end:]

    # A STALE REASON IS DEBT IN THE SAME WAY A STALE COUNT IS. This one
    # is wrong twice: the tool's census returns 117, not 120, and the
    # tree holds 151, not 146.
    stale = ("    'test_button_sweep.py':\n"
             "        'pages  its own census says 120 templates, not 146',")
    once(tree, stale, TREE)
    tree = tree.replace(
        stale,
        "    'test_button_sweep.py':\n"
        "        'pages  narrow BY DESIGN - its walk rebuilds a pre-sweep '\n"
        "        'tree from .bak_btnsweep, so widening it would copy the '\n"
        "        'second template root into a tree the sweep never '\n"
        "        'covered. 117 in the tool census against 151 in the '\n"
        "        'tree, and that gap is a stated position. [reason '\n"
        "        'replaced E-10, 11 Oct 2026 - it said 120 and 146, and '\n"
        "        'both numbers had moved]',", 1)

    conv = "    'test_held_contrast.py',\n]"
    once(tree, conv, TREE)
    ntree = tree.replace(
        conv,
        "    'test_held_contrast.py',\n"
        "    # E-10, 11 Oct 2026 - it was never held by its own walk. Its\n"
        "    # walk was fine; Show-ButtonDrift could not RESOLVE the names\n"
        "    # the walk handed it, so eight CRS pages came back as\n"
        "    # FileNotFoundError and the suite read eight crashes as eight\n"
        "    # drifting buttons. Twelve really did drift, behind them.\n"
        "    'test_disabled_state.py',\n"
        "    # E-10 - and this round's own suite.\n"
        "    'test_drift_root.py',\n]", 1)

    rounds = read(os.path.join(root, ROUNDS))
    r_anchor = "    '.bak_heldcon',\n"
    once(rounds, r_anchor, ROUNDS)
    nrounds = rounds.replace(r_anchor, r_anchor + "    '%s',\n" % SUFFIX, 1)

    ps = read(os.path.join(root, PS1))
    p_anchor = "    'test_held_contrast.py'\n)"
    once(ps, p_anchor, PS1)
    nps = ps.replace(
        p_anchor,
        "    'test_held_contrast.py',\n    '%s'\n)" % SUITE, 1)

    # SENTINELS. A standard that is only in a suite is a standard the
    # next page copied from an old one will quietly leave - the gate's
    # own words, twice over. These three discriminate: the rule is
    # absent from every backed-up base, and the two Bootstrap tones are
    # present in every backed-up copy of the page they came off.
    s_anchor = (
        "    # NO SENTINEL ON 'border-radius: 6px'. One was written and")
    once(nps, s_anchor, PS1)
    nps = nps.replace(
        s_anchor,
        "    # ------------------------------------------- E-10, 11 Oct 2026\n"
        "    # The colour of a switched-off button belongs where the other\n"
        "    # two tones keep it. Before this, `btn action-danger` with the\n"
        "    # disabled attribute rendered faint RED - the only switched-off\n"
        "    # button in the application that was not grey.\n"
        "    @{ File = 'pages\\templates\\base.html'; "
        "Text = '.btn.action-danger[disabled]'; "
        "What = 'a switched-off danger greys, like a primary and a "
        "secondary' },\n"
        "    # And the three CRS delete modals, which the button sweep never\n"
        "    # saw because the tool could not resolve a name under the\n"
        "    # second template root. Solid Bootstrap grey beside solid\n"
        "    # Bootstrap red, measured, on three screens.\n"
        "    @{ File = 'crs\\templates\\crs\\country_list.html'; "
        "Text = 'btn btn-danger'; "
        "What = 'the CRS delete modals wear house tones, not Bootstrap'; "
        "Absent = $true; Code = $true },\n"
        "    @{ File = 'crs\\templates\\crs\\submission_list.html'; "
        "Text = 'btn btn-secondary'; "
        "What = 'and their Cancel is paper, not solid grey'; "
        "Absent = $true; Code = $true },\n"
        + s_anchor, 1)

    # A ROUND THAT CHANGES A NUMBER OWNS EVERY NUMBER THAT COUNTS IT.
    x0 = read(os.path.join(root, X0))
    old_c = 'WALKERS_OWN_ROOT_MAX = %d' % CEILING_WAS
    once(x0, old_c, X0)
    nx0 = x0.replace(
        old_c,
        'WALKERS_OWN_ROOT_MAX = %d   # E-10, 11 Oct 2026 - one more\n'
        '# census converted, and it may only FALL. Show-ButtonDrift.py is\n'
        '# still on this list and stays there: E-10 widened the way it\n'
        '# RESOLVES a name, not the root it walks.   # (was %d)'
        % (CEILING_NOW, CEILING_WAS), 1)

    wd = read(os.path.join(root, WD))
    for was, now, why in (
            ('CONVERTED_N = %d' % CONVERTED_WAS,
             'CONVERTED_N = %d   # E-10, 11 Oct 2026 - one released plus '
             'this round own suite   # (was %d)'
             % (CONVERTED_NOW, CONVERTED_WAS), 'CONVERTED_N'),
            ('WAITING_N = %d' % WAITING_WAS,
             'WAITING_N = %d   # E-10, 11 Oct 2026 - one off   # (was %d)'
             % (WAITING_NOW, WAITING_WAS), 'WAITING_N'),
            ('CEILING = %d' % CEILING_WAS,
             'CEILING = %d   # E-10, 11 Oct 2026 - one more census   '
             '# (was %d)' % (CEILING_NOW, CEILING_WAS), 'CEILING')):
        once(wd, was, WD)
        wd = wd.replace(was, now, 1)
    nwd = wd

    # AND E-1b's OWN SUITE, WHICH PINNED TWO AGGREGATES.
    #
    # `len(WAITING) == 6` and `WALKERS_OWN_ROOT_MAX == 43` were both true
    # the moment E-1b shipped and both false the moment any later round
    # releases a suite - which is this one, one round later. E-1b made
    # exactly this repair to E-1a's suite and wrote the rule down while
    # doing it: a pinned COUNT moves, a pinned DECISION does not, and a
    # pinned AGGREGATE was never either. Then it pinned two.
    #
    # What E-1b claims is that ITS TWO came off and that the ceiling
    # FELL. Both survive as claims about E-1b forever; neither needs a
    # number from the future.
    hc = read(os.path.join(root, HC))
    old_w = """check('WAITING now holds %d' % WAITING_AFTER,
      len(alv_tree.WAITING) == WAITING_AFTER, '%d' % len(alv_tree.WAITING))
check('  CONTROL: and is not empty', len(alv_tree.WAITING) > 0)"""
    once(hc, old_w, HC)
    hc = hc.replace(
        old_w,
        """# E-10, 11 Oct 2026 - WAS `len(WAITING) == WAITING_AFTER`. E-1b
# repaired this exact shape in test_held_four and wrote the rule down
# in the same round: a pinned AGGREGATE was never a count or a
# decision. What E-1b claims is that ITS TWO came off, checked one by
# one above, and that claim is true forever.
check('neither of the two this round released is still held',
      not [n for n in RELEASED if n in alv_tree.WAITING],
      '%s' % [n for n in RELEASED if n in alv_tree.WAITING])
check('  CONTROL: and WAITING is not empty - %d still held'
      % len(alv_tree.WAITING), len(alv_tree.WAITING) > 0)""", 1)

    old_ceil = """check('the walker ceiling is %d' % CEILING_AFTER,
      pin(x0, 'WALKERS_OWN_ROOT_MAX') == CEILING_AFTER,
      '%s' % pin(x0, 'WALKERS_OWN_ROOT_MAX'))"""
    once(hc, old_ceil, HC)
    nhc = hc.replace(
        old_ceil,
        """# E-10, 11 Oct 2026 - WAS `== CEILING_AFTER`, pinned at 43. The
# ceiling is the whole programme's number and it falls every time any
# round converts a census. What matters here - that the two files
# agree, and that E-1b's conversion made it FALL - is checked below
# and against this round's own backup, and both hold forever.
check('the walker ceiling is a real number in both places',
      pin(x0, 'WALKERS_OWN_ROOT_MAX') is not None,
      '%s' % pin(x0, 'WALKERS_OWN_ROOT_MAX'))""", 1)

    # ---------------------------------------------------------------- 7
    if CHECK:
        print('')
        print('E-10  check only - nothing written')
        print('E-10  would widen %d resolution site(s) in %s and leave the'
              % (len(joins), SBD))
        print('E-10  census walking TPL alone')
        print('E-10  would match a footer by class TOKEN - wrapper census')
        print('E-10  %d -> %d, one page of 150 changing its plan'
              % (N_FOOTER_SUBSTRING, N_FOOTER_TOKEN))
        print('E-10  would give base the switched-off danger, in the five')
        print('E-10  shapes the primary block already uses')
        print('E-10  would pair %d Bootstrap tone(s) on %d page(s) and %d'
              % (len(BOOTSTRAP_PAGES) * 2, len(BOOTSTRAP_PAGES),
                 N_BARE_DANGER + 1))
        print('E-10  action-danger class list(s) on %s' % DANGER_PAGE)
        print('E-10  would widen and release %s' % ', '.join(RELEASED))
        print('E-10  WAITING %d -> %d, CONVERTED %d -> %d, ceiling %d -> %d'
              % (WAITING_WAS, WAITING_NOW, CONVERTED_WAS, CONVERTED_NOW,
                 CEILING_WAS, CEILING_NOW))
        return 0

    for p, txt in [(sbd_p, nsbd), (base_p, nb)] + list(pages.items()) \
            + [(os.path.join(root, 'test_button_sweep.py'), nbs),
               (os.path.join(root, BH), nbh),
               (os.path.join(root, PC), npc),
               (os.path.join(root, DS), nds),
               (os.path.join(root, NP), nnp),
               (os.path.join(root, TREE), ntree),
               (os.path.join(root, ROUNDS), nrounds),
               (os.path.join(root, WD), nwd),
               (os.path.join(root, X0), nx0),
               (os.path.join(root, HC), nhc),
               (os.path.join(root, PS1), nps)]:
        backup(p)
        write(p, txt)

    print('')
    print('E-10  %s resolves a name through alv_tree now - %d site(s).'
          % (SBD, len(joins)))
    print('E-10  Its census still walks TPL and only TPL, because two')
    print('E-10  callers stand on that scope.')
    print('E-10  A footer is matched by class TOKEN: wrapper census %d -> %d,'
          % (N_FOOTER_SUBSTRING, N_FOOTER_TOKEN))
    print('E-10  one page of 150 changing its plan, and the XML Viewer')
    print('E-10  Download stays paper instead of going teal by substring.')
    print('E-10  base greys a switched-off danger. It was the only')
    print('E-10  switched-off button in the app that was not grey.')
    print('E-10  %d Bootstrap tone(s) off %d CRS modal(s); %d action-danger'
          % (len(BOOTSTRAP_PAGES) * 2, len(BOOTSTRAP_PAGES),
             N_BARE_DANGER + 1))
    print('E-10  class list(s) paired on %s - four of them' % DANGER_PAGE)
    print('E-10  measure identical either way and are said to be.')
    print('E-10  %s widened and released.' % ', '.join(RELEASED))
    print('E-10  WAITING %d -> %d, CONVERTED %d -> %d, ceiling %d -> %d'
          % (WAITING_WAS, WAITING_NOW, CONVERTED_WAS, CONVERTED_NOW,
             CEILING_WAS, CEILING_NOW))
    print('E-10  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
