# -*- coding: utf-8 -*-
"""PM-1 - THE PINS THIS BUNDLE MOVED

Five suites pin something FG-1, UC-2 or SG-2 deliberately changed. Each
pin was right when it was written and is now pointing at a thing that has
a different name, a different shape, or a different count.

A pin is not updated by nudging its number until the suite goes quiet.
Each one below either moves to what the thing BECAME, or - where the
claim itself is what changed - is restated. Every one says which round
moved it.

==========================================================================
1. test_button_sweep - A SEGMENTED TOGGLE, PINNED BY WHAT IT IS NOW
==========================================================================
    "The sweep must never touch a segmented toggle: its colour IS the
     state."

The claim is exactly right and SG-2 did not weaken it. What changed is
the toggle: it was a conditional btn-info/btn-outline-info pair and it is
base's .alv-seg now. So the pin asserts the seg, and - which the old pin
could not - that the sweep CANNOT touch it, because an .alv-seg member
carries no `btn` at all and the sweep only ever rewrites `btn`.

==========================================================================
2. test_button_sweep - ONE DEFINITION OF "A VERB"
==========================================================================
The suite re-implements the lone-verb rule independently of
Show-ButtonDrift: its own list of what is not a verb (action-filter,
disabled-btn, Cancel, Help) sits beside the scanner's. PN-1 taught the
scanner that a CHOOSER is not a verb either, and the suite went on not
knowing.

Two copies of one rule is the shape CN-1 spent a round removing from the
filter census this morning. The suite calls sb.is_chooser now, so the
rule has one definition and the next addition to it reaches both.

==========================================================================
3. test_detail_property - A KEPT RULE THAT WAS DELIBERATELY REMOVED
==========================================================================
It pins .view-toggle-group at four rules on property_assets. SG-2 removed
all four, because base sizes .alv-seg and spaces its icons and a page
rule could only disagree. A removal must be NAMED to be allowed; it is
named here and the pin goes.

==========================================================================
4. test_filter_box - TWO COUNTS THAT MOVED BECAUSE A PAGE JOINED
==========================================================================
unit_conversions_management's search box used to be a bare text input
with the page's own .filter-input. UC-2 put it on .form-control inside
the house panel, so the paired count rises and the bare count falls. The
suite's own note says the bare ones are "the ones that were" - a list,
not a number - so the list is what is corrected.

==========================================================================
5. test_filter_frame - base's DECLARATION, AND ONE PROPERTY ON NINE PAGES
==========================================================================
FG-1 added grid-template-columns and justify-content to .filter-grid, so
the declaration the suite pins is two properties longer and nine pages
report justify-content moving from normal to start. That is FG-1's whole
point - a grid that declares its columns - and the suite's "the ONLY
things that moved" list gains the entry that says so.

==========================================================================
6. test_help_pl - A CLAIM PROVED BY A CLASS NAME
==========================================================================
    "the year dropdown no longer offers Budget"
      ... proved by: 'pl-view-toggle' in TPL_SRC

The claim is still true; the evidence was a class name SG-2 renamed. It
asks for .alv-seg now - and for the Budget link, which is the thing the
claim is actually about.

==========================================================================
7. test_live_search - A NAMED EXEMPTION, AS AGREED
==========================================================================
Demetri, 3 Oct: "a named exemption, with the reason". Unit Conversions is
eligible - it renders every row - and will not opt in, because base's
live search owns row.style.display outright and this page composes THREE
narrowings. It joins `projects`, which is exempt for pagination, with its
own reason beside it.

AND THE CHECK READS CODE, NOT THE RECORD OF CODE. It failed on a comment
in that page explaining why the page does not use the feature - the third
time today a gate read one of this bundle's own notes. It strips comments
before looking now.

Backups: .bak_movedpins. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_movedpins'
ROOT = os.getcwd()
CRLF = {}

SWEEP = os.path.join(ROOT, 'test_button_sweep.py')
DETAIL = os.path.join(ROOT, 'test_detail_property.py')
FBOX = os.path.join(ROOT, 'test_filter_box.py')
FRAME = os.path.join(ROOT, 'test_filter_frame.py')
FADD = os.path.join(ROOT, 'test_field_add.py')
SECVIS = os.path.join(ROOT, 'test_secondary_visible.py')
HELPPL = os.path.join(ROOT, 'test_help_pl.py')
LIVE = os.path.join(ROOT, 'test_live_search.py')
FRAME = os.path.join(ROOT, 'test_filter_frame.py')
FADD = os.path.join(ROOT, 'test_field_add.py')
SECVIS = os.path.join(ROOT, 'test_secondary_visible.py')


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
            raise SystemExit('PM1: %s is not a byte copy' % bak)


def swap(path, text, old, new, what):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('PM1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('PM-1 - THE PINS THIS BUNDLE MOVED%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 1 and 2. test_button_sweep
# ==========================================================================
t, raw = read(SWEEP)

if 'sb.is_chooser' in t:
    print('  test_button_sweep.py       already updated')
else:
    t = swap(SWEEP, t, """# The sweep must never touch a segmented toggle: its colour IS the state.
tog = load(os.path.join(TPL, 'finance_pl_act.html'))
check('finance_pl_act keeps its budget/actuals toggle logic',
      "{% if view_mode == 'budget' %}btn-info{%" in tog)
check('.. and the actuals half too',
      "{% if view_mode == 'actuals' %}btn-info{%" in tog)""",
             """# The sweep must never touch a segmented toggle: its colour IS the state.
#
# PINNED BY WHAT IT IS NOW - PM-1, 3 Oct 2026. The claim has not changed
# and SG-2 did not weaken it. The TOGGLE changed: it was a conditional
# Bootstrap pair and it is base's .alv-seg now, so pinning the old class
# names pinned a thing that no longer exists.
#
# And the new pin says something the old one could not. An .alv-seg
# member carries no `btn` at all, and the sweep only ever rewrites `btn`
# - so this control is not merely untouched, it is UNTOUCHABLE by that
# instrument. That is a stronger guarantee than the one it replaces.
tog = load(os.path.join(TPL, 'finance_pl_act.html'))
_seg = re.search(r'<div class="alv-seg"[^>]*>(.*?)</div>', tog, re.S)
check('finance_pl_act keeps its budget/actuals toggle, as a segment',
      bool(_seg))
check('.. with both halves, each current only in its own view',
      bool(_seg) and _seg.group(1).count('aria-current="page"') == 2
      and 'view=budget' in _seg.group(1)
      and 'view=actuals' in _seg.group(1))
check('.. and the sweep cannot touch it - no half carries a btn class',
      bool(_seg) and not re.search(r'class="[^"]*\\bbtn\\b', _seg.group(1)))""",
             'the toggle pin')

    t = swap(SWEEP, t, """                and 'action-filter' not in b.group(2)
                and 'disabled-btn' not in b.group(2)
                and not sb.is_cancel(sb.label_of(b.group(3)))
                and not sb.label_of(b.group(3)).lower().startswith('help')]""",
             """                and 'action-filter' not in b.group(2)
                and 'disabled-btn' not in b.group(2)
                and not sb.is_cancel(sb.label_of(b.group(3)))
                and not sb.label_of(b.group(3)).lower().startswith('help')
                # ONE DEFINITION OF "A VERB" - PM-1, 3 Oct 2026. This list
                # re-implements Show-ButtonDrift's lone-verb rule, and
                # when PN-1 taught the scanner that a CHOOSER is not a
                # verb either, this copy went on not knowing and reported
                # finance_pl_act's year dropdown. Two copies of one rule
                # is what CN-1 spent a round removing from the filter
                # census this morning; the rule is asked of the tool now.
                and not sb.is_chooser(sb.label_of(b.group(3)),
                                      b.group(2))]""",
             'the lone-verb rule')

    if not CHECK:
        back_up(SWEEP, raw)
        write(SWEEP, t)
    print('  test_button_sweep.py       the toggle pin moves; the verb rule '
          'asks the tool')

# ==========================================================================
# 3. test_detail_property
# ==========================================================================
t, raw = read(DETAIL)

if "('.view-toggle-group', 4)" not in t:
    print('  test_detail_property.py    already updated')
else:
    t = swap(DETAIL, t, """    A: (('.asset-thumb', 1), ('.summary-grid', 1), ('.view-toggle-group', 4),
        ('.empty-state-card', 4), ('.photo-upload-controls', 2),""",
             """    # .view-toggle-group IS GONE - SG-2, 3 Oct 2026, named here because a
    # removal must be named to be allowed. Its four rules sized a
    # hand-rolled segmented control; the control is base's .alv-seg now,
    # which base sizes and spaces itself, so a page rule could only
    # disagree with it.
    A: (('.asset-thumb', 1), ('.summary-grid', 1),
        ('.empty-state-card', 4), ('.photo-upload-controls', 2),""",
             'the view-toggle-group pin')

    if not CHECK:
        back_up(DETAIL, raw)
        write(DETAIL, t)
    print('  test_detail_property.py    the removed rules are named, not '
          'pinned')

# ==========================================================================
# 4. test_filter_box
# ==========================================================================
t, raw = read(FBOX)

if 'UC-2' in t:
    print('  test_filter_box.py         already updated')
else:
    t = swap(FBOX, t, """ok(len(paired) + len(bare) == 39,""",
             """# UC-2, 3 Oct 2026 moved unit_conversions_management's search box off
# the page's own .filter-input and onto .form-control inside the house
# panel, so one control crossed from bare to paired. The TOTAL is
# unchanged, which is the useful half of this check: a control did not
# appear or vanish, it changed company.
ok(len(paired) + len(bare) == 39,""",
             'the filter-box total')

    # TWO CONTROLS CROSSED, NOT ONE. The search box lost .filter-input
    # for .form-control, and the From-Unit select gained .form-control
    # beside its .filter-select - so paired rises by two and bare falls
    # by two, with the total unmoved. Counted off the tree rather than
    # guessed: the first draft of this round said 35 and the tree said 36.
    t = swap(FBOX, t, """ok(len(paired) == 34, '  thirty-four pair it with .form-control, and do """,
             """ok(len(paired) == 36, '  thirty-six pair it with .form-control, and do """,
             'the paired count')

    # AND THE BARE TEXT INPUTS ARE DOWN TO ONE. The suite names them
    # rather than counting them, which is the right shape - a list says
    # WHICH page still has one. Celebration Management is the last.
    t = swap(FBOX, t, """ins = [b for b in bare if 'filter-input' in b[1]]
ok(len(ins) == 2,
   '  and exactly two are bare text inputs - the ones that were 68',
   [b[0] for b in ins])""",
             """ins = [b for b in bare if 'filter-input' in b[1]]
ok(len(ins) == 1,
   '  and exactly one is a bare text input - UC-2 took the other, on '
   'unit_conversions_management, into the house panel',
   [b[0] for b in ins])""",
             'the bare count')

    _m = re.search(r"ok\(sorted\(b\[0\] for b in ins\) == \[[^\]]*\],?\s*\n?[^\n]*\n?[^\n]*",
                   t)
    if not _m:
        raise SystemExit('PM1: cannot find the bare-input name list')
    t = swap(FBOX, t, _m.group(0),
             """ok(sorted(b[0] for b in ins) == ['celebration_management.html'],
   '  and it is Celebration Management', sorted(b[0] for b in ins))""",
             'the bare name list')

    if not CHECK:
        back_up(FBOX, raw)
        write(FBOX, t)
    print('  test_filter_box.py         one control crossed from bare to '
          'paired')

# ==========================================================================
# 6. test_help_pl
# ==========================================================================
t, raw = read(HELPPL)

if 'alv-seg' in t:
    print('  test_help_pl.py            already updated')
else:
    t = swap(HELPPL, t, """check('  because the year dropdown no longer offers "Budget"',
      'view=budget' in TPL_SRC and 'pl-view-toggle' in TPL_SRC)""",
             """# THE CLAIM IS UNCHANGED; THE EVIDENCE MOVED - PM-1, 3 Oct 2026. Budget
# is still a control of its own rather than an option in the year
# dropdown, which is what this check is about. It proved that by looking
# for the class name on the control, and SG-2 renamed the control to
# base's .alv-seg. It asks for the segment and the Budget link now - the
# second being the thing the claim is actually about.
check('  because the year dropdown no longer offers "Budget"',
      'view=budget' in TPL_SRC and 'alv-seg' in TPL_SRC)""",
             'the help evidence')

    if not CHECK:
        back_up(HELPPL, raw)
        write(HELPPL, t)
    print('  test_help_pl.py            the claim is proved by what the '
          'control is now')

# ==========================================================================
# 7. test_live_search
# ==========================================================================
t, raw = read(LIVE)

if 'EXEMPT' in t:
    print('  test_live_search.py        already carries the exemption')
else:
    t = swap(LIVE, t, """CANDIDATES = ('unit_conversions_management.html',)""",
             """CANDIDATES = ()
# EXEMPT, BY NAME AND WITH THE REASON - Demetri, 3 Oct 2026.
#
# unit_conversions_management renders every row, so it passes the
# pagination half of the contract and was listed as a candidate. It will
# not opt in, and the reason is the other half: base's live search owns
# row.style.display OUTRIGHT - it walks every row on every keystroke and
# sets display from its own query alone - and this page composes THREE
# narrowings, a search, a from-unit and a scope. A second thing setting
# that property is not a second filter; it is a race, and the last to run
# wins.
#
# The same reason keeps measurement_units_management out, where it is two
# filters rather than three. FL-1's suite proves it in a browser.
#
# `projects` is exempt for the other reason entirely - it paginates - and
# is checked separately below.
EXEMPT = {
    'unit_conversions_management.html':
        'composes three narrowings; base\\'s live search owns display',
    'measurement_units_management.html':
        'composes two; same reason',
}""",
             'the candidate list')

    t = swap(LIVE, t, """for rel in CANDIDATES:
    p = alv_tree.path_of(rel)
    ok('data-live-search' not in read(p),
       '%-40s eligible, still not opted in' % rel)""",
             """for rel in CANDIDATES:
    p = alv_tree.path_of(rel)
    ok('data-live-search' not in read(p),
       '%-40s eligible, still not opted in' % rel)
# AND THE EXEMPT ONES, WHICH ARE A DECISION RATHER THAN A BACKLOG.
#
# READ THE CODE, NOT THE RECORD OF THE CODE. This check failed on a
# COMMENT in unit_conversions_management explaining why that page does
# not use the feature - the third time in one session a gate in this tree
# read one of a round's own notes as the thing the note was about. The
# note is worth keeping and the gate is what was wrong.
for rel, why in sorted(EXEMPT.items()):
    src = re.sub(r'\\{#.*?#\\}', '', read(alv_tree.path_of(rel)), flags=re.S)
    src = re.sub(r'<!--.*?-->', '', src, flags=re.S)
    ok('data-live-search' not in src,
       '%-40s exempt: %s' % (rel, why))""",
             'the candidate loop')

    if not CHECK:
        back_up(LIVE, raw)
        write(LIVE, t)
    print('  test_live_search.py        two named exemptions, and it reads '
          'code not comments')


# ==========================================================================
# 8. test_filter_frame - base's FRAME GAINED TWO DECLARATIONS
# ==========================================================================
# FG-1 gave .filter-grid the columns it had never declared, so base's
# frame is two properties longer than apply_filter_frame.py recorded, and
# nine panels report justify-content moving from normal to start.
#
# THE PATCHER IS NOT EDITED. The suite says why, about the one amendment
# it already carries: "A patcher is the record of what it did on the day
# it ran; rewriting its tables to keep a later suite happy turns the
# record into a diary of the present." So the amendment goes here, beside
# the one AE-1 needed, and the check stays EXACT rather than being
# loosened to compare key sets.
t, raw = read(FRAME)

if 'HOUSE_AMENDED' in t:
    print('  test_filter_frame.py       already carries the amendment')
else:
    t = swap(FRAME, t, """base = read(alv_tree.path_of('base.html'))""",
             """# AND base's OWN FRAME MAY GAIN A DECLARATION, AND IT HAS.
#
# FG-1, 3 Oct 2026. .filter-grid declared display:grid, a gap and
# align-items and NO grid-template-columns - a grid with no columns is a
# grid with ONE column, and the first page that did not set its own
# rendered its fields stacked at the full width of the panel. The columns
# are base's now, capped so a field cannot stretch into a banner.
#
# Recorded the same way AMENDED records AE-1's: by name, with the values,
# so section 1 goes on comparing declaration by declaration.
HOUSE_AMENDED = {
    '.filter-grid': {
        'grid-template-columns': 'repeat(auto-fit, minmax(200px, 240px))',
        'justify-content': 'start',
    },
}
# HOUSE ITSELF IS NOT TOUCHED. It is the record of what H1 lifted, and
# section 2 below asks a question about the PAST with it - whether
# celebration_management, the one copy that had been through a styling
# round, already said all three exactly. Amending that record would make
# a claim about 2 October fail because of something done on the 3rd.
#
# So the amendment produces a SECOND table, used only where the present
# is compared.
HOUSE_NOW = dict((sel, dict(vals, **HOUSE_AMENDED.get(sel, {})))
                 for sel, vals in HOUSE.items())

base = read(alv_tree.path_of('base.html'))""",
             'the base frame amendment')

    t = swap(FRAME, t, """        ok(got == HOUSE[sel], '  %s' % '; '.join('%s: %s' % kv for kv in""",
             """        ok(got == HOUSE_NOW[sel], '  %s' % '; '.join('%s: %s' % kv for kv in""",
             'the present-tense comparison')

    t = swap(FRAME, t, """                if (k == 'grid.cols' and rel == 'act_expense.html'""",
             """                if k == 'grid.just' and v == ('normal', 'start'):
                    # FG-1, 3 Oct 2026. The row packs from the left now.
                    # Without it the slack is shared BETWEEN the tracks
                    # and two fields sit at opposite ends of the panel
                    # with a metre of nothing between them. Every panel
                    # moves, which is the point of putting it in base.
                    continue
                if (k == 'grid.cols' and rel == 'act_expense.html'""",
             'the justify-content move')

    if not CHECK:
        back_up(FRAME, raw)
        write(FRAME, t)
    print('  test_filter_frame.py       base\'s frame amendment, recorded '
          'by name')


# ==========================================================================
# 9. test_field_add - A CLAIM ABOUT ONE ROUND, MEASURED ON THE FILE TODAY
# ==========================================================================
#     "and only the comment changed - the tool itself is untouched"
#
# That is a claim about what the FIELD-ADD round left, and it compared
# Show-ButtonDrift.py AS IT IS TODAY against that round's backup. PN-1
# gave the tool is_chooser, which is a behaviour change and is supposed
# to be - so a true statement about 1 October started failing because of
# something done on the 3rd.
#
# The repair is the rule this tree already wrote down: A SCOPE CLAIM IS
# MEASURED AGAINST THE STATE IT NAMES, NEVER read(path). The file has a
# left() helper for exactly this, used everywhere in it except here.
t, raw = read(FADD)

if 'left_drift' in t:
    print('  test_field_add.py          already scoped to its own round')
else:
    t = swap(FADD, t, """    code = re.sub(r'#.*', '', t)
    if os.path.isfile(d + SUFFIX):
        was_code = re.sub(r'#.*', '', read(d + SUFFIX))""",
             """    # AS THE FIELD-ADD ROUND LEFT IT - PM-1, 3 Oct 2026. This read the
    # tool as it stands now, so every later round that touches it breaks
    # a claim about this one. PN-1 added is_chooser on 3 Oct and did
    # exactly that. as_left_by walks forward to the next backup and
    # returns the file as THIS round left it.
    #
    # The file's own left() does this for templates; the drift tool is
    # not a template, so it is spelled out here.
    left_drift = (as_left_by(d, SUFFIX, read) if as_left_by else read(d))
    code = re.sub(r'#.*', '', left_drift)
    if os.path.isfile(d + SUFFIX):
        was_code = re.sub(r'#.*', '', read(d + SUFFIX))""",
             'the drift-tool scope')

    if not CHECK:
        back_up(FADD, raw)
        write(FADD, t)
    print('  test_field_add.py          the claim is measured on the state '
          'it names')

# ==========================================================================
# 10. test_secondary_visible - ONE BAR MOVED, BY DESIGN
# ==========================================================================
# Sections 4 and 5 render every carried bar under base-as-it-is and
# base-as-it-was and demand the two be identical. finance_pl_act's bar
# now holds an .alv-seg, and PN-1 gave a segment in an action bar the
# BAR'S control metrics - same font, same line-height, same padding as
# the .btn beside it - so its width moved. That is the change, not a
# regression: before it, the seg was 35.5px against 34.8 and three
# quarters of a pixel was enough to push a centred sibling onto what
# measured as a second row.
#
# Named, the way test_filter_frame names AE-1's: the check stays EXACT
# for the other 53 bars.
t, raw = read(SECVIS)

if 'MOVED_BY' in t:
    print('  test_secondary_visible.py  already names the one that moved')
else:
    t = swap(SECVIS, t, """if sync_playwright is not None and FIX:
    _same = _diff = 0
    for rel, blk in CARRIED:""",
             """# ONE BAR IS ALLOWED TO HAVE MOVED - PM-1, 3 Oct 2026.
#
# PN-1 gave .alv-seg in an action bar the bar's control metrics, so the
# segment is 34.8px like every .btn beside it instead of 35.5px, and its
# halves are 16px padded instead of 14. finance_pl_act is the only
# carried bar holding one, so it is the only width that moves.
#
# NAMED, not loosened. The alternative - comparing class lists without
# widths - would stop noticing a bar whose buttons change size by
# accident, which is what sections 4 and 5 are for.
MOVED_BY = {
    'finance_pl_act.html':
        'PN-1, 3 Oct 2026 - a segment in a bar takes the bar height',
}

if sync_playwright is not None and FIX:
    _same = _diff = 0
    for rel, blk in CARRIED:""",
             'the moved-by table')

    t = swap(SECVIS, t, """        if now and was and now['list'] == was['list']:
            _same += 1
        else:
            _diff += 1""",
             """        if now and was and now['list'] == was['list']:
            _same += 1
        elif rel in MOVED_BY:
            _same += 1
            print('        MOVED BY DESIGN %s - %s' % (rel, MOVED_BY[rel]))
        else:
            _diff += 1""",
             'the 390 comparison')

    t = swap(SECVIS, t, """        if not now or not was or now['list'] != was['list']:
            _moved.append(rel)""",
             """        if not now or not was or now['list'] != was['list']:
            if rel not in MOVED_BY:
                _moved.append(rel)""",
             'the desktop comparison')

    if not CHECK:
        back_up(SECVIS, raw)
        write(SECVIS, t)
    print('  test_secondary_visible.py  the one bar that moved is named')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
import ast
import subprocess

FILES = (SWEEP, DETAIL, FBOX, HELPPL, LIVE, FRAME, FADD, SECVIS)
for p in FILES:
    ast.parse(read(p)[0])
print('  all eight suites parse')

# 1. NO PIN WAS SILENCED. Every change either points at what the thing
#    BECAME or restates the claim - none of them deletes a check.
for p in FILES:
    now = read(p)[0]
    was = read(p + SUFFIX)[0]
    n_now = len(re.findall(r'\n\s*(?:check|ok)\(', now))
    n_was = len(re.findall(r'\n\s*(?:check|ok)\(', was))
    if n_now < n_was:
        raise SystemExit('PM1: %s lost %d check(s) - a pin is moved, never '
                         'removed' % (os.path.basename(p), n_was - n_now))
    print('  %-26s %d checks, was %d' % (os.path.basename(p), n_now, n_was))

# 2. THE VERB RULE HAS ONE DEFINITION NOW.
sw = read(SWEEP)[0]
if 'sb.is_chooser' not in sw:
    raise SystemExit('PM1: the suite still decides for itself what a verb is')
print('  the lone-verb rule is asked of Show-ButtonDrift, not re-implemented')

# 3. THE EXEMPTIONS ARE NAMED, WITH REASONS, AND READ CODE.
lv = read(LIVE)[0]
if 'EXEMPT = {' not in lv:
    raise SystemExit('PM1: there is no exemption list')
if lv.count("':") < 2:
    raise SystemExit('PM1: an exemption with no reason is a backlog entry')
if re.sub(r'\{#.*?#\}', '', '') != '':
    pass
if "re.sub(r'\\{#.*?#\\}', '', read(" not in lv:
    raise SystemExit('PM1: the exemption check still reads comments')
print('  both exemptions carry a reason, and the check strips comments first')

# 4. AND THE FIVE SUITES RUN.
bad = []
for who in ('test_button_sweep.py', 'test_detail_property.py',
            'test_filter_box.py', 'test_help_pl.py', 'test_live_search.py',
            'test_filter_frame.py', 'test_field_add.py',
            'test_secondary_visible.py'):
    r = subprocess.run([sys.executable, who], capture_output=True, text=True,
                       cwd=ROOT, timeout=1800)
    tail = [ln for ln in r.stdout.split('\n')
            if 'passed' in ln or re.search(r'^\s*\d+ of \d+', ln)
            or 'checks passed' in ln]
    mark = 'ok  ' if r.returncode == 0 else 'FAIL'
    if r.returncode != 0:
        bad.append(who)
    print('  %s %-26s %s' % (mark, who, tail[-1].strip() if tail else ''))
    if r.returncode != 0:
        for ln in [x for x in r.stdout.split('\n') if 'FAIL' in x][:4]:
            print('       %s' % ln.strip())

print('-' * 74)
if bad:
    print('  STILL RED: %s' % ', '.join(bad))
else:
    print('  A pin is not updated by nudging its number until the suite')
    print('  goes quiet. Each one here points at what the thing became.')
print('=' * 74)
