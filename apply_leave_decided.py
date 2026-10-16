# -*- coding: utf-8 -*-
"""apply_leave_decided.py - round LV-1, 16 Oct 2026.

LEAVE WAS A SCOPE DECISION BEING USED AS A SILENCER.

`Show-ButtonDrift.py` carries two registers for buttons that sit outside
every recognised bar:

    DECIDED   wrapper -> [(label fragment, tone)]   the tool CHECKS these
    LEAVE     wrapper -> reason                     the tool says NOTHING

A LEAVE entry short-circuits EVERY button in its wrapper. Measured today
across all 142 gate pages, the ten LEAVE entries covered **41
buttons**, and the report has never once mentioned any of them:

    .filter-header         16      .pdf-viewer-controls    5
    .filter-header-right    1      .status-action-form     8
    .input-group-append     8      .zoom-controls          3

(The first draft of this table wrote 11 against .input-group-append from
memory. The instrument says 8, and 8 is what is written down. The nine
entries this round removes cover **33** of the 41; the survivor holds
the other 8.)

Of those 33, **25 carry a raw Bootstrap colour** and 8 already wear a
house tone and are simply never checked - three of the eight being
`action-primary` Save buttons on property_assets. Change one of those to
a secondary and no gate in this project would notice. VC-1 pinned the
number at eight on 14 Oct so it could not grow quietly; PH-2 nearly made
it eleven and caught itself; three rounds since have walked past it.
(Eleven is what the first cut of THIS file typed for the register size,
and its own gate refused the run: the register holds TEN. The number a
patcher states about the tree is asked of the tree.)


THE FIX IS A REGISTER THIS FILE ALREADY HAS
============================================================================
DECIDED's own header says what it is for:

    Buttons outside any bar whose tone was decided one at a time, from
    rendered before/after pictures.

That is exactly these. And the journey has been made before: D3, on
23 Sep, moved `selection-buttons`, `fi-trend-controls` and `pd-toolbar`
off LEAVE onto DECIDED with the note *"Moved here so the tool CHECKS
them rather than staying silent about them."* This round finishes that
work rather than inventing a third register beside the two that exist.

    LEAVE: 11 entries -> 1

    FOUR WERE DEAD        btn-group, subtask-actions,
                          project-status-container, passport-filter-header
                          hold no button on any of the 142 pages. Measured.
    FIVE BECOME DECISIONS filter-header, filter-header-right,
                          input-group-append, pdf-viewer-controls,
                          zoom-controls
    ONE IS A REAL ONE     status-action-form


AND THE SAVE BUTTONS ARE WHY DECIDED TAKES A LABEL, NOT A TONE  MEASURED
============================================================================
The first cut of this round wrote `'input-group-append': [('*', S)]`,
and the plan it produced **demoted all three property_assets Saves from
action-primary to action-secondary** - the precise buttons this whole
item exists to protect. DECIDED's value is a LIST of (label fragment,
tone) pairs, first match wins, so the entry is

    'input-group-append': [('save', P), ('*', S)],

and the Saves keep their tone. Re-measured: 25 rows, and not one of them
is a Save.


WHAT THE 25 ARE, AND WHY action-secondary
============================================================================
    14  Clear All        btn-outline-secondary  ->  action-secondary
     3  Cancel           btn-secondary          ->  action-secondary
     5  viewer controls  btn-light              ->  action-secondary
     3  zoom controls    btn-outline-secondary
                         and -primary           ->  action-secondary

THE CLEAR ALLS ARE NOT A DESIGN QUESTION. Every button in those two
wrappers is a Clear All - seventeen of them - and THREE already wear
`btn action-secondary btn-sm`, on cash_receipts, celebration_management
and customer_list. The same control, in the same wrapper, spelled two
ways across seventeen pages, with the silencer hiding both spellings.
This is unfinished work, not a decision.

THE VIEWER AND ZOOM TOOLBARS WERE DECIDED FROM PICTURES. Demetri was
shown all three options rendered at 1280 and 390 and chose the quiet
one. `Fit to Screen` stops being Bootstrap blue - it was the only
non-house colour in either toolbar, sitting on a zoom control - and
nothing becomes a primary, because nothing there goes out or commits.

AND NO NEW CLASS IN BASE. The first proposal was a 42nd name,
`.action-chrome`: paper, --alv-line, --alv-ink-soft, hover filling to
--alv-surface-deep. base's `.btn.action-secondary` is paper, --alv-line,
--alv-ink, hover filling to --alv-surface. **The same rule with half a
step of ink.** Rendered side by side you have to hunt for the
difference. `.action-field-add` earned its name by being
accent-bordered and filling to accent; this would not have earned one,
and TB-1a deleted six names for less.


THE EDITS COME FROM THE INSTRUMENT, NOT FROM A TYPED LIST
============================================================================
The 25 class rewrites are taken from `sb.scan_text()`'s own offsets,
with the NEW registers in force - the same machinery
`apply_button_sweep.py` uses, and for the same reason recorded there:

    scan_text, NOT scan. scan() reads the file from disk; by the time we
    get here the text in hand is already edited, so a disk scan is a
    plan for the PREVIOUS version of the page.

Each edit re-reads the class attribute at the reported offset and
REFUSES if it is not the one the scanner named. A patcher and a plan
that disagree is how this file learned that lesson the first time.
"""
import importlib.util
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_leavedecided'
DRIFT = 'Show-ButtonDrift.py'
VOCAB = 'test_vocabulary.py'
ME = 'test_leave_decided.py'
PATCHER = 'apply_leave_decided.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
BH = 'test_bar_height.py'
BSW = 'test_button_sweep.py'
FG = 'test_filter_get.py'
CHECK = False

CONVERTED_WAS, CONVERTED_NOW = 89, 90
ALIAS_WAS, ALIAS_NOW = 89, 91
ALIAS_P_WAS, ALIAS_S_WAS = 44, 45
ALIAS_P_NOW, ALIAS_S_NOW = 45, 46

N_EDITS = 25
N_LOOSE_WAS, N_LOOSE_NOW = 83, 86
N_SILENCED_WAS, N_SILENCED_NOW = 8, 0
N_ENTRIES_WAS, N_ENTRIES_NOW = 2, 0
LEAVE_WAS, LEAVE_NOW = 10, 1
DEAD = ('btn-group', 'subtask-actions', 'project-status-container',
        'passport-filter-header')
MOVED = ('filter-header', 'filter-header-right', 'input-group-append',
         'pdf-viewer-controls', 'zoom-controls')

# ------------------------------------------------------- Show-ButtonDrift
# THE HEAD ANCHOR IS THE HEAD ONLY. The first cut of this file swallowed
# the first four entries into the head swap and then asked the removal
# loop to take them out again, which refused on the first one. The dict
# OPENING is what gets the new explanation; every entry leaves through
# the loop, and the loop is what the reload then checks.
LEAVE_WAS_TXT = """LEAVE = {"""

LEAVE_NOW_TXT = """# LV-1, 16 Oct 2026 - TEN ENTRIES BECAME ONE.
#
# A LEAVE entry short-circuits EVERY button in its wrapper, and the
# ten covered 33 buttons across the 142 gate pages. 25 of them wore a
# raw Bootstrap colour this report has never once mentioned, and 8 wore
# a house tone and were simply never checked - three of those being
# action-primary Save buttons on property_assets.
#
# FOUR WERE DEAD. btn-group, subtask-actions, project-status-container
# and passport-filter-header hold no button on any gate page. Measured,
# then deleted - a register entry with no element is dead weight exactly
# as a rule with no element is.
#
# FIVE WERE DECISIONS NOBODY HAD WRITTEN DOWN, and they are in DECIDED
# now, which is the register whose own header says it holds the tones
# "decided one at a time, from rendered before/after pictures". D3 made
# this same journey with three entries on 23 Sep, for the same reason:
# moved there so the tool CHECKS them rather than staying silent.
#
# ONE IS LEFT, and it is a real one.
LEAVE = {"""

# AND ONE COMMENT GOES WITH ITS ENTRY. input-group-append is the only
# one of the nine that carries a note of its own; taking the entry and
# leaving the note would put a paragraph about welded inputs above
# btn-group, describing an entry that is not there any more. The note
# itself is not lost - the DECIDED entry that replaces it says the same
# thing and names Save first.
IGA_NOTE = """    # 30 Sep 2026: this still covers the buttons welded to an input
    # whose GEOMETRY is Bootstrap's, which is what the note meant. It
    # no longer covers their COLOUR. property_assets carried three
    # btn-outline-success + buttons under this entry, and the report
    # said "nothing drifting" over them for weeks - Demetri saw the
    # green. base now has .action-field-add and they wear it, so they
    # are not in this count any more. See test_field_add.py.
"""

STATUS_WAS = """    # THAT IS NOT A HYPOTHETICAL. Measured across all 142 pages, EIGHT
    # buttons already wearing a house tone sit inside a LEAVE wrapper and
    # are therefore never checked: three Clear Alls under .filter-header
    # and five under .input-group-append, of which THREE are
    # `action-primary btn-sm` Save buttons on property_assets. Change one
    # of those to a secondary and no gate in this project would notice.
    # test_vocabulary.py pins the number at eight so it cannot grow, and
    # LEAVE-as-a-silencer is the next thing in this line of work.
    'status-action-form': 'the invoice status row - page classes on house '
                          'tokens',
}"""

STATUS_NOW = """    # THAT WAS NOT A HYPOTHETICAL, AND LV-1 CLOSED IT. Eight buttons
    # already wearing a house tone sat inside a LEAVE wrapper and were
    # therefore never checked - three Clear Alls under .filter-header and
    # five under .input-group-append, of which THREE were
    # `action-primary btn-sm` Save buttons on property_assets.
    # test_vocabulary.py pinned the number at eight so it could not grow
    # quietly; it now pins it at ZERO, and keeps the share-grid control
    # that explains why the pin exists at all.
    #
    # WHY THIS ONE STAYS. VC-1 measured the eight invoice status buttons
    # on 14 Oct: btn-delete, btn-duplicate, btn-approve, btn-send and
    # btn-unapprove, each DEFINED BY THE PAGE and each already on house
    # tokens - --alv-bad, --alv-accent, --alv-good, --alv-warn,
    # --alv-on-accent - with a 44px min-height. They are not drift, and
    # not one of them carries a house CLASS, so this entry silences
    # nothing that was being checked. Whether a status row should be five
    # solid fills is a design question for its own round, and this entry
    # is what stops it being an invisible one.
    'status-action-form': 'the invoice status row - page classes on house '
                          'tokens',
}"""

DECIDED_WAS = """    'selection-buttons':       [('*', S)],"""

DECIDED_NOW = """    # LV-1, 16 Oct 2026 - THE FIVE THAT CAME OFF LEAVE.
    #
    # .filter-header and .filter-header-right hold ONE control between
    # them, repeated: Clear All, seventeen times. THREE already wore
    # `btn action-secondary btn-sm` - cash_receipts, celebration_
    # management, customer_list - and fourteen wore btn-outline-secondary.
    # The same control, in the same wrapper, spelled two ways across
    # seventeen pages, with the silencer hiding both spellings. That is
    # unfinished work, not a design question.
    'filter-header':           [('*', S)],
    'filter-header-right':     [('*', S)],
    #
    # .input-group-append TAKES A LABEL, NOT A BLANKET, and this is the
    # one place this round had to think. The wrapper holds the three
    # action-primary Save buttons on property_assets as well as three
    # btn-secondary Cancels and three action-field-add plus buttons. A
    # blanket ('*', S) plans SECONDARY FOR THE SAVES - the exact buttons
    # this whole item exists to protect - and the first cut of this round
    # did precisely that. First match wins, so Save is named first.
    #
    # The Cancels become secondary, which is the pair base already draws
    # beside a primary. The plus buttons keep .action-field-add, which
    # the 30 Sep round gave them when it found them green under this very
    # entry and amended the note to say it no longer covers their COLOUR.
    # That amendment was right and this is the rest of it.
    'input-group-append':      [('save', P), ('*', S)],
    #
    # .pdf-viewer-controls and .zoom-controls ARE WIDGET CHROME, and
    # their tone was decided from pictures: all three options rendered at
    # 1280 and 390, and the quiet one chosen. Fit to Screen stops being
    # btn-outline-primary - it was the only non-house colour in either
    # toolbar and it sat on a zoom control, which neither sends anything
    # nor commits anything. Nothing here becomes a primary.
    'pdf-viewer-controls':     [('*', S)],
    'zoom-controls':           [('*', S)],
    'selection-buttons':       [('*', S)],"""

# ------------------------------------------------------------ the suite
VOCAB_WAS = """silenced = collections.defaultdict(list)"""

VOCAB_NOW = """# LV-1, 16 Oct 2026 - THE PIN IS ZERO NOW, and the census below is
# unchanged so it can say so in the same words it used to say eight.
# .filter-header, .filter-header-right, .input-group-append,
# .pdf-viewer-controls and .zoom-controls moved to DECIDED, where the
# tool CHECKS them; four dead entries were deleted; status-action-form
# is the one that stays, and VC-1's own measurement below is why.
silenced = collections.defaultdict(list)"""

VOCAB_N_WAS = """ok(_n == N_SILENCED and len(silenced) == N_SILENCED_ENTRIES,
   'exactly %d already-decided button(s) sit inside a LEAVE wrapper, on '
   '%d entries' % (N_SILENCED, N_SILENCED_ENTRIES),
   '%d on %d: %s' % (_n, len(silenced),
                     {k: len(v) for k, v in silenced.items()}))
ok(sorted(silenced) == ['filter-header', 'input-group-append'],
   '  and they are .filter-header and .input-group-append, both older '
   'than this round', sorted(silenced))
ok(len([1 for v in silenced.values() for _r, _l, c in v
        if 'action-primary' in c]) == 3,
   '  THREE of them are action-primary Save buttons on property_assets - '
   'change one to a secondary and no gate here would notice')"""

VOCAB_N_NOW = """ok(_n == N_SILENCED and len(silenced) == N_SILENCED_ENTRIES,
   'exactly %d already-decided button(s) sit inside a LEAVE wrapper, on '
   '%d entries' % (N_SILENCED, N_SILENCED_ENTRIES),
   '%d on %d: %s' % (_n, len(silenced),
                     {k: len(v) for k, v in silenced.items()}))
ok(sorted(silenced) == [],
   '  there is no wrapper left that silences a decided button - '
   '.filter-header and .input-group-append both went to DECIDED in LV-1',
   sorted(silenced))
ok(len([1 for v in silenced.values() for _r, _l, c in v
        if 'action-primary' in c]) == 0,
   '  and in particular NOT the three action-primary Save buttons on '
   'property_assets, which were the sharp end of this for three rounds')"""


# ------------------------------------------------- test_button_sweep
# TWO CLAIMS THIS ROUND FALSIFIES, AND A ROUND THAT FALSIFIES A CLAIM
# FIXES IT. Both were found by the sweep, not by this file.
#
# THE FIRST IS A HISTORICAL CLAIM READ FROM A LIVE PAGE. "Nothing on
# the LEAVE list was touched" is a statement about what the BUTTON
# SWEEP did in August, and it was asked of act_expense.html as it
# stands today - so the first later round to retone that Clear All
# falsifies a claim about a round that ran two months earlier. The
# claim is true and stays; it is re-pointed at the sweep's own
# snapshot, which is exactly what the pd-toolbar claim three lines
# below it already does.
BSW_FH_WAS = """# Nothing on the LEAVE list was touched.
_fh = load(os.path.join(TPL, 'act_expense.html'))
check('filter chrome untouched - Clear All is still btn-outline-secondary',
      'btn-outline-secondary' in _fh)"""

BSW_FH_NOW = """# Nothing on the LEAVE list was touched BY THE SWEEP - and that is a
# claim about August, so it is read from the sweep's own copy. LV-1,
# 16 Oct 2026: this was asked of the LIVE page until LEAVE stopped
# being a silencer and that Clear All took action-secondary. A
# historical claim read from a live file is a claim with an expiry
# date on it, and this one reached it.
_fhp = os.path.join(TPL, 'act_expense.html')
_fh = load(_fhp + '.bak_btnsweep') if os.path.exists(_fhp + '.bak_btnsweep') \\
    else load(_fhp)
check('filter chrome untouched BY THE SWEEP - Clear All was still '
      'btn-outline-secondary when it finished',
      'btn-outline-secondary' in _fh)"""

# THE SECOND NAMES A WRAPPER THAT IS NOT ON THE REGISTER ANY MORE.
BSW_CT_WAS = """# Asked with a wrapper that is STILL on the LEAVE list, since the one
# this used before is not any more. The claim is unchanged.
check('CONTROL: a LEAVE wrapper carries its reason into a script-built '
      'button, whether or not a live page still has one',
      [h[5] for h in sb.js_buttons(
          '<script>var h = `<div class="btn-group">'
          '<button class="btn btn-info btn-sm">Edit</button>'
          '</div>`;</script>')] == [_LEAVE_REASON])"""

BSW_CT_NOW = """# Asked with a wrapper that is STILL on the LEAVE list, since the one
# this used before is not any more. The claim is unchanged.
#
# LV-1, 16 Oct 2026 - AND THE NAME IS READ FROM THE REGISTER NOW. This
# control has been re-pointed twice by hand at whichever wrapper
# happened to survive; btn-group was the last of them and this round
# deleted it as dead. Taking the name and the reason from LEAVE itself
# means the next round to change the register re-points this control by
# changing nothing.
_ctrl_wrap, _ctrl_why = sorted(sb.LEAVE.items())[0]
check('CONTROL: a LEAVE wrapper carries its reason into a script-built '
      'button, whether or not a live page still has one',
      [h[5] for h in sb.js_buttons(
          '<script>var h = `<div class="%s">'
          '<button class="btn btn-info btn-sm">Edit</button>'
          '</div>`;</script>' % _ctrl_wrap)] == [_ctrl_why])"""


# ------------------------------------------------ test_filter_get
# THE SAME SHAPE AGAIN, AND THE SWEEP FOUND IT IN A THIRD PLACE. F-1's
# central claim is that nothing on its five filter panels moved except
# the method and the csrf token. Section 3c renders each page twice -
# once from the .bak_filterget templates, once from the LIVE ones - and
# diffs the panel Django actually sent. The "after" side being LIVE
# means a round two months later falsifies a statement about F-1 by
# touching any of those five pages, which is what LV-1 does to five
# Clear All buttons.
#
# The claim is true and stays. It is re-pointed at the page AS F-1 LEFT
# IT, which is what as_left_by answers, so no later round can move it
# again. See test_button_sweep in this same patcher, and the SIXTH
# entry in claude/standard_delivery_preflight.md for why a historical
# claim read from a live file has an expiry date on it.
FG_WAS = """    _before = os.path.join(_scr, 'before')
    os.makedirs(_before)
    _tpl = os.path.join(ROOT, 'pages', 'templates')
    _have = True
    for _n in ('fsr.html', 'invoices.html', 'properties.html',
               'suppliers.html', 'tenant.html', 'base.html'):
        _src = os.path.join(_tpl, _n + SUFFIX)
        if os.path.isfile(_src):
            _sh.copyfile(_src, os.path.join(_before, _n))
        else:
            _have = False
    if not _have:
        skip('the markup diff', 'a backup is missing')
    else:
        _eng = dj.TEMPLATES[0]

        def _use(which):
            _eng['DIRS'] = ([_before] if which == 'before'
                            else [os.path.join(ROOT, 'templates')])"""

FG_NOW = """    _before = os.path.join(_scr, 'before')
    _after = os.path.join(_scr, 'after')
    os.makedirs(_before)
    os.makedirs(_after)
    _tpl = os.path.join(ROOT, 'pages', 'templates')
    _have = True
    for _n in ('fsr.html', 'invoices.html', 'properties.html',
               'suppliers.html', 'tenant.html', 'base.html'):
        _src = os.path.join(_tpl, _n + SUFFIX)
        if os.path.isfile(_src):
            _sh.copyfile(_src, os.path.join(_before, _n))
        else:
            _have = False
        # LV-1, 16 Oct 2026 - AND THE AFTER SIDE IS A SNAPSHOT TOO.
        # It was the LIVE page until LV-1 retoned five Clear All
        # buttons inside these very panels, and a claim about what F-1
        # changed must not be falsified by what a later round changed.
        # as_left_by hands back the page as F-1 left it: the next
        # round's backup, or the live file when no later round has
        # touched it - which is what made this read correctly for two
        # months and then stop.
        _dst = os.path.join(_after, _n)
        _live = os.path.join(_tpl, _n)
        if as_left_by:
            with open(_dst, 'w', encoding='utf-8', newline='') as _fh:
                _fh.write(as_left_by(_live, SUFFIX, read))
        else:
            _sh.copyfile(_live, _dst)
    if not _have:
        skip('the markup diff', 'a backup is missing')
    else:
        _eng = dj.TEMPLATES[0]

        def _use(which):
            _eng['DIRS'] = [_before if which == 'before' else _after]"""


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
    raise SystemExit('LV-1 REFUSED: %s' % msg)


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


def load(name, source, path):
    """Import a module from SOURCE rather than from disk.

    --check must plan against the edited registers without writing them,
    and apply must plan against the edited registers too. Loading the
    text in hand is the only way both do the same thing.
    """
    spec = importlib.util.spec_from_loader(name, loader=None)
    mod = importlib.util.module_from_spec(spec)
    mod.__file__ = path
    exec(compile(source, path, 'exec'), mod.__dict__)
    return mod


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    drift = os.path.join(root, DRIFT)

    # ---------------------------------------------------------------- 0
    # ALREADY APPLIED, asked of the register this round moves.
    src = read(drift)
    if "'zoom-controls':         [('*', S)]" in src \
            or "'zoom-controls':           [('*', S)]" in src:
        print('LV-1  already applied - the five are on DECIDED.')
        return 0

    out = {}

    # ---------------------------------------------------------------- 1
    # THE FOUR ARE DEAD BEFORE THEY ARE DELETED, measured against the
    # live tree rather than assumed - the same control TB-1a ran before
    # deleting six class names.
    old = load('sb_old', src, drift)
    live = {}
    for rel in old.templates(True):
        m = old.markup_of(read(old.resolve(rel)).replace('\r\n', '\n'))
        for b in old.BTN.finditer(m):
            for n in old.innermost_wrapper(m, b.start()):
                if n in old.LEAVE:
                    live[n] = live.get(n, 0) + 1
    alive = [n for n in DEAD if live.get(n)]
    if alive:
        refuse('a LEAVE entry this round deletes still holds a button: %s'
               % {n: live[n] for n in alive})
    missing = [n for n in MOVED if not live.get(n)]
    if missing:
        refuse('a LEAVE entry this round moves to DECIDED holds no '
               'button, so moving it would decide nothing: %s' % missing)
    if len(old.LEAVE) != LEAVE_WAS:
        refuse('%s has %d LEAVE entries, expected %d'
               % (DRIFT, len(old.LEAVE), LEAVE_WAS))

    # ---------------------------------------------------------------- 2
    s = swap(src, LEAVE_WAS_TXT, LEAVE_NOW_TXT, '%s (the LEAVE head)' % DRIFT)
    # the five that move, and the four that die, come out of the dict
    for n in MOVED + DEAD:
        before = s
        s = re.sub(r"(?m)^    '%s':[^\n]*\n(?:[ ]{4,}[^\n]*\n)*?(?=    [#'}])"
                   % re.escape(n), '', s, count=1)
        if s == before:
            refuse('%s: could not remove the LEAVE entry %r' % (DRIFT, n))
    if s.count(fit(s, IGA_NOTE)) != 1:
        refuse('%s: the input-group-append note is not where this round '
               'left it, and removing its entry would orphan it' % DRIFT)
    s = swap(s, IGA_NOTE, '', '%s (the input-group-append note)' % DRIFT)
    s = swap(s, STATUS_WAS, STATUS_NOW, '%s (the status entry)' % DRIFT)
    s = swap(s, DECIDED_WAS, DECIDED_NOW, '%s (DECIDED)' % DRIFT)
    out[drift] = s

    new = load('sb_new', s, drift)
    if len(new.LEAVE) != LEAVE_NOW or 'status-action-form' not in new.LEAVE:
        refuse('%s: LEAVE has %d entries after the move, expected %d and '
               'status-action-form among them'
               % (DRIFT, len(new.LEAVE), LEAVE_NOW))
    for n in MOVED:
        if n not in new.DECIDED:
            refuse('%s: %s did not land in DECIDED' % (DRIFT, n))
    if new.DECIDED['input-group-append'][0][0] != 'save':
        refuse('%s: input-group-append does not name Save FIRST, so a '
               'blanket secondary would demote three deliberate Save '
               'buttons' % DRIFT)

    # ---------------------------------------------------------------- 3
    # THE EDITS COME FROM THE INSTRUMENT. Back to front, so every offset
    # stays valid while the text is rewritten.
    n_edits = 0
    saves = 0
    for rel in new.templates(True):
        path = new.resolve(rel)
        text = read(path)
        flat = text.replace('\r\n', '\n')
        plan = [h for h in new.scan_text(rel, flat)
                if new.drifting(h) and not h[7]]
        if not plan:
            continue
        markup = new.markup_of(flat)
        if len(markup) != len(flat):
            refuse('%s: markup_of changed the length by %d character(s), '
                   'so the scanner offsets no longer address the file'
                   % (rel, len(flat) - len(markup)))
        edits = []
        for _kind, lab, _boot, cls, want, a, z in [h[:7] for h in plan]:
            if 'save' in lab.lower() and 'action-primary' in cls:
                saves += 1
            tag = markup[a:z]
            m = re.search(r'class="([^"]*)"', tag)
            if not m or m.group(1) != cls:
                refuse('%s: the button at offset %d does not carry the '
                       'class the scanner reported.\n  expected %r\n'
                       '  found    %r' % (rel, a, cls,
                                          m.group(1) if m else None))
            # NO BASE OFFSET. markup_of BLANKS style and script blocks
            # to the same number of characters rather than removing
            # them - its own docstring says why - so an offset into the
            # markup IS an offset into the file. The first cut of this
            # loop looked the markup up inside the file with .index()
            # and died on every page that has a <style> block, which is
            # all of them.
            cs = a + m.start(1)
            edits.append((cs, cs + len(cls), cls, want))
        edits.sort(reverse=True)
        for cs, ce, cls, want in edits:
            if flat[cs:ce] != cls:
                refuse('%s: the text at %d is not the class planned' % (rel, cs))
            flat = flat[:cs] + want + flat[ce:]
            n_edits += 1
        out[path] = (flat.replace('\n', '\r\n')
                     if text.count('\r\n') > text.count('\n') - text.count('\r\n')
                     else flat)

    if saves:
        refuse('the plan would retone %d Save button(s) - input-group-append '
               'is not naming Save first' % saves)
    if n_edits != N_EDITS:
        refuse('the plan holds %d edit(s), expected %d' % (n_edits, N_EDITS))

    # ---------------------------------------------------------------- 4
    # GATES over what was written, asked of the CLASS ATTRIBUTE and not
    # of the page: every one of these words also appears in this round's
    # own explanation, and a page-wide test finds its own reasoning.
    for path, txt in out.items():
        if path == drift or not path.endswith('.html'):
            continue
        body = code_only(txt)
        for m in re.finditer(r'<(?:button|a)\b[^>]*class="([^"]*)"', body):
            names = m.group(1).split()
            for gone in ('btn-outline-secondary', 'btn-secondary',
                         'btn-light', 'btn-outline-primary'):
                if gone in names:
                    refuse('%s: a control still carries %s - %r'
                           % (os.path.relpath(path, root), gone,
                              m.group(1)[:50]))
        if 'property_assets' in path:
            n_save = len(re.findall(
                r'class="btn action-primary btn-sm"', body))
            if n_save != 3:
                refuse('%s: %d Save button(s) keep action-primary, '
                       'expected 3' % (os.path.relpath(path, root), n_save))

    # ---------------------------------------------------------------- 5
    p = os.path.join(root, VOCAB)
    s = read(p)
    if 'THE PIN IS ZERO NOW' in s:
        refuse('%s already reads the pin as zero' % VOCAB)
    s = swap(s, VOCAB_WAS, VOCAB_NOW, '%s (the census note)' % VOCAB)
    s = swap(s, VOCAB_N_WAS, VOCAB_N_NOW, '%s (the pin)' % VOCAB)
    # ONE DECLARATION, NOT TWO. test_vocabulary names both numbers on a
    # single line, and the first cut of this round bumped them as if
    # they were separate - the anchor matched nothing and the run
    # refused. A counter is bumped in the shape the file WROTE it.
    s = swap(s, 'N_SILENCED, N_SILENCED_ENTRIES = %d, %d'
             % (N_SILENCED_WAS, N_ENTRIES_WAS),
             'N_SILENCED, N_SILENCED_ENTRIES = %d, %d'
             % (N_SILENCED_NOW, N_ENTRIES_NOW)
             + '   # LV-1, 16 Oct 2026 - five wrappers moved to DECIDED '
               'and four dead ones were deleted, so no wrapper silences '
               'a decided button any more, and no entry holds one.'
               '   # (was %d, %d)' % (N_SILENCED_WAS, N_ENTRIES_WAS),
             '%s (the silenced pin)' % VOCAB)
    out[p] = s

    # ---------------------------------------------------------------- 6
    p = os.path.join(root, PS1)
    s = read(p)
    if ME in s:
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
                  'LV-1, 16 Oct 2026 - this round own suite. LEAVE stops '
                  'being a silencer: ten entries become one, and the '
                  '25 Bootstrap-coloured buttons it was hiding take the '
                  'tone their own siblings already wear.',
                  '%s (the converted count)' % WD)

    p = os.path.join(root, CO)
    s = read(p)
    s = bump(s, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
             'LV-1, 16 Oct 2026 - this round own patcher and suite',
             '%s (the alias count)' % CO)
    s = swap(s, "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_WAS, ALIAS_S_WAS),
             "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_NOW, ALIAS_S_NOW),
             '%s (the alias split)' % CO)
    out[p] = s

    # ---------------------------------------------------------------- 6b
    # THE HEIGHT CENSUS. test_bar_height selects on a HOUSE CLASS, so
    # three of the 25 retoned buttons - the ones that sit in a card or
    # loose on a page - were invisible to it until this round gave them
    # one. They did not appear; they became visible, which is this
    # round's whole thesis arriving in a second instrument.
    p = os.path.join(root, BH)
    out[p] = bump(read(p), 'N_LOOSE, N_LOOSE_H = %d, 11',
                  N_LOOSE_WAS, N_LOOSE_NOW,
                  'LV-1, 16 Oct 2026 - three of the 25 retoned buttons '
                  'sit in a card or loose on a page. This census selects '
                  'on a house class, so it could not see them while a '
                  'LEAVE entry was keeping them Bootstrap-coloured. '
                  'N_LOOSE_H does not move - all three land on heights '
                  'the set already held.',
                  '%s (the loose census)' % BH)

    # ---------------------------------------------------------------- 6c
    p = os.path.join(root, BSW)
    s = read(p)
    s = swap(s, BSW_FH_WAS, BSW_FH_NOW, '%s (the filter chrome claim)' % BSW)
    s = swap(s, BSW_CT_WAS, BSW_CT_NOW, '%s (the LEAVE control)' % BSW)
    out[p] = s

    # ---------------------------------------------------------------- 6d
    p = os.path.join(root, FG)
    out[p] = swap(read(p), FG_WAS, FG_NOW, '%s (the after side)' % FG)

    # ---------------------------------------------------------------- 7
    if CHECK:
        print('LV-1 --check  %d file(s) would change' % len(out))
        for q in sorted(out):
            print('   %s' % os.path.relpath(q, root))
        print('   %d button(s) retoned; LEAVE %d -> %d'
              % (n_edits, LEAVE_WAS, LEAVE_NOW))
        return 0

    for q, t in sorted(out.items()):
        backup(q)
        write(q, t)

    print('LV-1 applied.')
    print('   LEAVE goes from %d entries to %d - four were DEAD, five'
          % (LEAVE_WAS, LEAVE_NOW))
    print('         were decisions nobody had written down, one is real')
    print('   %d buttons it was hiding take action-secondary, planned by'
          % n_edits)
    print('         Show-ButtonDrift itself rather than typed out here')
    print('   the three property_assets Saves KEEP action-primary, because')
    print('         DECIDED names Save before the blanket')
    print('   the silenced count goes %d -> %d' % (N_SILENCED_WAS,
                                                   N_SILENCED_NOW))
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


# ------------------------------------------------------------- registers
SENT_ANCHOR = """    # -------------------------------------------- HL-1, 12 Oct 2026"""

SENT_NEW = """    # ------------------------------------------------- LV-1, 16 Oct 2026
    # A LEAVE entry short-circuited every button in its wrapper. Eleven
    # entries hid 33 buttons; 25 of them wore a raw Bootstrap colour and
    # three of the rest were action-primary Saves nobody was checking.
    @{ File = 'Show-ButtonDrift.py'; Text = "'zoom-controls':           [('*', S)]"; What = 'widget chrome is a DECIDED tone now, not a silence' },
    @{ File = 'Show-ButtonDrift.py'; Text = "'input-group-append':      [('save', P), ('*', S)]"; What = 'and Save is named FIRST, so the three property_assets Saves keep their tone' },
    @{ File = 'pages\\templates\\property_assets.html'; Text = 'btn-secondary btn-sm'; Absent = $true; Code = $true; What = 'the Cancels beside them are house secondary' },
    @{ File = 'pages\\templates\\projects\\project_gantt.html'; Text = 'btn-outline-primary'; Absent = $true; Code = $true; What = 'and Fit to Screen stops being the only Bootstrap blue in a zoom control' },
    # -------------------------------------------- HL-1, 12 Oct 2026"""

SUITE_WAS = """    'test_deed_one_column.py'
)"""

SUITE_NOW = """    'test_deed_one_column.py',
    'test_leave_decided.py'
)"""

TREE_WAS = """    'test_deed_one_column.py',
]"""

TREE_NOW = """    'test_deed_one_column.py',
    # LV-1, 16 Oct 2026 - LEAVE stops being a silencer: ten register
    # entries become one, and the 25 Bootstrap-coloured buttons they were
    # hiding take the house tone. Wide from birth.
    'test_leave_decided.py',
]"""

ROUNDS_WAS = """    '.bak_deedonecol',
]"""

ROUNDS_NOW = """    '.bak_deedonecol',
    # LV-1, 16 Oct 2026 - Show-ButtonDrift's LEAVE register goes from
    # ten entries to one. Four were dead, five become DECIDED tones
    # the tool checks, and the 25 buttons they silenced take
    # action-secondary - planned by the tool, not typed.
    '.bak_leavedecided',
]"""


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
