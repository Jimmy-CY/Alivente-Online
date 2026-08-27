"""apply_button_sweep.py - make the markup agree with base.html about buttons.

    python apply_button_sweep.py --check     dry run, writes nothing
    python apply_button_sweep.py             apply

Run from the project root. Idempotent: running twice changes nothing the
second time. Every file it touches is backed up to <name>.bak_btnsweep.

WHAT THIS DOES, AND WHY IN THIS ORDER
-------------------------------------
1.  base.html gets ONE new rule: a disabled .action-primary is grey.
2.  38 action bars are renamed to .page-action-buttons.
3.  262 buttons drop their Bootstrap colour class and carry a house tone.
4.  Page-local CSS that base.html now duplicates exactly is deleted.

Order matters. Steps 2 and 3 must land together: base.html's TONES are
hoisted (every page already carries .action-primary, so base reaches them
all the moment it defines them) but base.html's LAYOUT is opt-in, scoped to
.page-action-buttons. Ship 3 without 2 and a page gets house colours inside
a hand-rolled bar. Ship 2 without 3 and it gets house layout around
Bootstrap colours. Both look half broken, in different ways.

THE PLAN COMES FROM THE SCANNER
-------------------------------
This file does not classify anything. It imports Show-ButtonDrift and edits
at the offsets that scanner reports, so the same logic that produced the
plan performs it and `Show-ButtonDrift.py --strict` returning zero is a real
proof rather than a coincidence.

That matters because THE CLASS STRING ALONE IS AMBIGUOUS. Four of them mean
different things in different places - `class="btn btn-info"` is a primary
on eleven pages, a secondary on one and a Back link on another. A
find-and-replace would be silently wrong.

WHAT IT DELIBERATELY LEAVES ALONE
---------------------------------
  - segmented toggles, whose colour is `{% if view_mode == 'budget' %}`
    template logic; flattening them to one tone deletes the active state
  - .action-more-item dropdown rows, which base styles directly
  - the recipe / meal-plan / ingredient / WCIM / celebration side
  - both `(OLD DO NOT USE)` templates
Each skip is COUNTED AND PRINTED. A sweep that silently narrows its own
scope reports success over work it never did.
"""

import collections
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    import importlib.util
    _spec = importlib.util.spec_from_file_location(
        'showbuttondrift', os.path.join(HERE, 'Show-ButtonDrift.py'))
    sb = importlib.util.module_from_spec(_spec)
    _saved, sys.argv = sys.argv, ['showbuttondrift']
    _spec.loader.exec_module(sb)
    sys.argv = _saved
except Exception as exc:                                  # pragma: no cover
    sys.exit('! could not load Show-ButtonDrift.py (%s)\n'
             '  Both files must sit in the project root.' % exc)

TPL = sb.TPL
CHECK = '--check' in sys.argv
SUFFIX = '.bak_btnsweep'

if not os.path.isdir(TPL):
    sys.exit('! pages/templates not found - run from the project root')

# ---------------------------------------------------------------------------
# encoding is preserved per file, not guessed once
# ---------------------------------------------------------------------------


def load(path):
    raw = open(path, 'rb').read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    text = raw.decode('utf-8-sig' if bom else 'utf-8', errors='replace')
    crlf = '\r\n' in text
    return text.replace('\r\n', '\n'), bom, crlf


def save(path, text, bom, crlf):
    if crlf:
        text = text.replace('\n', '\r\n')
    data = text.encode('utf-8')
    if bom:
        data = b'\xef\xbb\xbf' + data
    open(path, 'wb').write(data)


def backup(path):
    if not os.path.exists(path + SUFFIX):
        shutil.copy2(path, path + SUFFIX)


# ---------------------------------------------------------------------------
# 1.  base.html - a switched-off primary must look switched off
# ---------------------------------------------------------------------------

MARKER = 'a switched-off primary is grey, not pale teal'

DISABLED_RULE = """
      /* %s.
         .disabled-btn used to set only opacity/cursor/pointer-events, so a
         button's grey came entirely from Bootstrap's .btn-secondary. Once
         that class is swept off, `.action-primary.disabled-btn` alone would
         render solid teal at 60%% - a washed-out button that still reads as
         clickable. The colour is half of "disabled"; it has to live here.

         Three shapes of switched-off button exist in this codebase and all
         three are covered: the class, the `disabled` attribute, and
         aria-disabled. Counted, not assumed. */
      .action-primary.disabled-btn,
      .btn.action-primary.disabled-btn,
      .btn.action-primary:disabled,
      .btn.action-primary[disabled],
      .btn.action-primary[aria-disabled="true"] {
        background: var(--alv-disabled-bg, #e8eaec);
        border-color: var(--alv-disabled-bg, #e8eaec);
        color: var(--alv-disabled-ink, #8a939b);
        box-shadow: none;
      }
""" % MARKER

ANCHOR = """      .disabled-btn {
        opacity: .6;
        cursor: not-allowed;
        pointer-events: none;
      }
"""


def patch_base():
    path = os.path.join(TPL, 'base.html')
    text, bom, crlf = load(path)
    if MARKER in text:
        return 0, 'already present'
    n = text.count(ANCHOR)
    if n != 1:
        sys.exit('! base.html: the .disabled-btn anchor matched %d times, '
                 'expected exactly 1.\n'
                 '  base.html has changed since this patcher was written - '
                 'stopping rather than guessing.' % n)
    text = text.replace(ANCHOR, ANCHOR + DISABLED_RULE)
    if not CHECK:
        backup(path)
        save(path, text, bom, crlf)
    return 1, 'would be added' if CHECK else 'added'



# ---------------------------------------------------------------------------
# 1b.  base.html - a Back link outside a bar, and a disabled secondary
# ---------------------------------------------------------------------------

MARKER2 = 'a Back link outside a bar is still a button'

SHAPE_RULE = """      /* %s.
         Splitting layout from tone left a gap. TONE is unscoped, so a Back
         anywhere gets the house colour; LAYOUT is scoped to
         .page-action-buttons, so a Back with no bar to live in falls back to
         Bootstrap's shape. Measured: 8px/16px, weight 600, radius 8px inside
         a bar; 6px/12px, weight 400, radius 4px outside one. That is why
         Back reads as bare text on FSR Details and Resolved Issues.

         POSITION IS LOAD-BEARING. This sits BEFORE .page-action-buttons so
         the bar's own rules still win inside a bar - on a phone the bar
         shrinks Back to a 44px icon with no padding, and a later rule of
         equal specificity (0,2,0) would silently undo that. */
      .btn.action-back,
      .btn.back-button {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: var(--alv-radius);
        font-family: var(--alv-font-ui);
        font-size: 14px;
        font-weight: 600;
      }

      /* .disabled-btn dims; it does not grey. On a primary that is now
         handled above. A secondary needs it too - properties_title_deed.html
         has a "Document Not Available" twin that would otherwise render as a
         live outlined button at 60%% opacity. */
      .btn.action-secondary.disabled-btn,
      .btn.action-secondary:disabled,
      .btn.action-secondary[disabled] {
        background: var(--alv-disabled-bg, #e8eaec);
        border-color: var(--alv-disabled-bg, #e8eaec);
        color: var(--alv-disabled-ink, #8a939b);
      }

""" % MARKER2

# Newline-anchored ON PURPOSE. The bare 6-space string is a SUBSTRING of the
# 8-space copy inside @media (max-width:768px), so text.count() found two and
# a replace would have inserted the rule into the mobile block as well.
ANCHOR2 = "\n      .page-action-buttons {"


def patch_base_shape():
    path = os.path.join(TPL, 'base.html')
    text, bom, crlf = load(path)
    if MARKER2 in text:
        return 0, 'already present'
    n = text.count(ANCHOR2)
    if n != 1:
        sys.exit('! base.html: the .page-action-buttons anchor matched %d '
                 'times, expected exactly 1. Stopping rather than guessing.'
                 % n)
    text = text.replace(ANCHOR2, SHAPE_RULE + ANCHOR2)
    if not CHECK:
        backup(path)
        save(path, text, bom, crlf)
    return 1, 'would be added' if CHECK else 'added'








# ---------------------------------------------------------------------------
# 5.  named repairs - each one anchored, asserted, and listed by hand
# ---------------------------------------------------------------------------
# Everything above works by rule. These do not: they are specific corrections
# to specific pages, agreed one at a time from rendered screenshots. Listing
# them explicitly is the point - a rule broad enough to catch these would be
# broad enough to catch things nobody looked at.

# Pages carrying the duplicate bottom bar this patcher itself created. The TOP
# bar stays: its submit button names its form explicitly (form="projectForm"),
# so the page keeps a working submit when the bottom row goes. Checked on all
# five before writing this - had the top button been a link or a JS proxy,
# deleting the bottom row would have broken saving on five screens.
DROP_SECOND_BAR = (
    'projects/projects_edit.html',
    'projects/project_tasks_edit.html',
    'projects/project_subtasks_add.html',
    'finance_valuations_add.html',
    'finance_valuations_edit.html',
    # Found afterwards, in a screenshot, and NOT this sweep's doing - both
    # bars on these two were already called .page-action-buttons before the
    # sweep ran. The list above was assembled from the pages the round-two
    # rename had broken, so it could only ever contain faults I had already
    # caused. Show-ButtonDrift now MEASURES this instead: any page with two
    # standard bars is reported and gates --strict, which is what should
    # have found these rather than a person clicking through the app twice.
    'projects/projects_add.html',
    'projects/project_tasks_add.html',
)

_BACK_ARROW = '<i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>'

REPAIRS = [
    ('fsr_details.html',
     'Back had no arrow - 92 of the 98 Backs in this system carry one',
     '<a href="#" onclick="handleBackButton(); return false;" '
     'class="btn action-back">Back</a>',
     '<a href="#" onclick="handleBackButton(); return false;" '
     'class="btn action-back">' + _BACK_ARROW + '</a>'),

    ('resolved_issues_report.html',
     'Back had no arrow',
     '<a href="{% url \'fsr\' %}" class="btn back-button" role="button">Back</a>',
     '<a href="{% url \'fsr\' %}" class="btn back-button" role="button">'
     + _BACK_ARROW + '</a>'),

    # This page's buttons sat in .header-actions, which THREE BANNER pages
    # also use. Three attempts were wrong before this one:
    #
    #   - Retoning the two buttons by name oscillated. .header-actions is in
    #     DECIDED as "everything secondary", so the repair set Submit FSR to
    #     primary and the tone pass set it straight back, for ever.
    #   - Moving .header-actions into BAR_NAMES would have dragged the three
    #     banner pages into a round we agreed to defer, and turned their Back
    #     transparent on a coloured banner - the dashboard problem again.
    #   - REPLACING the class with .page-action-buttons fixed the tone but
    #     broke two things it did not mention. This page carries its own
    #     `@media print { .header-actions { display: none } }` - drop the
    #     class and the buttons START PRINTING on a report page - and its own
    #     mobile block. It also could not converge: the anchor named
    #     `action-secondary`, the tone pass then made that button primary, so
    #     on the next run neither the old nor the new string was present and
    #     the patcher stopped dead rather than recognising its own work.
    #
    # The real distinction: this page's row IS a bar (Submit + Back on plain
    # white). The other three are rows inside a coloured banner. So ADD the
    # bar name beside the existing one. The ordinary rules now reach the row
    # - one non-Back button, so Submit FSR becomes the primary and Back goes
    # quiet - while every page-local rule keyed to .header-actions, print
    # included, keeps working. The anchor mentions no tone, so it recognises
    # its own output and a second run is a no-op.
    ('friday_status_report.html',
     'its row is a bar as well as a header row - name it as both',
     '<div class="header-actions">',
     '<div class="page-action-buttons header-actions">'),

    # Print Report is the page's verb, so it leads. Back follows, and
    # margin-left:auto carries it to the right edge - which only works if it
    # comes SECOND in the DOM. The order here is layout, not tidiness.
    #
    # btn-back and btn-print are page-local leftovers still painting their own
    # box: that is why this Back had a frame no other Back has. The CSS pass
    # kept their rules correctly, because base.html does not define those
    # selectors - they were dead in intent but live in effect.
    #
    # "Back to Issues" becomes "Back": measured, 92 of 98 Backs say plain
    # Back, and on a phone the bar hides the label entirely, so the extra
    # words buy nothing where space is tight.
    ('comments_report.html',
     'Print Report leads; Back loses its stray box and its long label',
     '<a href="{% url \'fsr\' %}" class="btn action-back btn-back" '
     'aria-label="Back to Issues">\n'
     '            <i class="fas fa-arrow-left"></i>'
     '<span class="action-back-label"> Back to Issues</span>\n'
     '        </a>\n'
     '        <button class="btn action-primary btn-print" '
     'onclick="window.print()">\n'
     '            <i class="fas fa-print"></i> Print Report\n'
     '        </button>',
     '<button class="btn action-primary" onclick="window.print()">\n'
     '            <i class="fas fa-print"></i> Print Report\n'
     '        </button>\n'
     '        <a href="{% url \'fsr\' %}" class="btn action-back" '
     'aria-label="Back to Issues">\n'
     '            <i class="fas fa-arrow-left"></i>'
     '<span class="action-back-label"> Back</span>\n'
     '        </a>'),
    # A delete-confirmation page, and the only one of eight where the two bars
    # were not duplicates of each other. Read top to bottom the page goes:
    # heading, action bar, project info, "Are you sure? This cannot be
    # undone", task details, "Warning: this task has N subtasks and deleting
    # it deletes all of them", second action bar.
    #
    # The TOP button sits above both warnings and carries form="deleteForm",
    # so it submits the same form - it is not a duplicate footer, it is a way
    # to delete a task and its subtasks without ever seeing what you agreed
    # to. Removing it leaves Back at the top, where Back sits on every other
    # page, and the explicit "Yes, Delete Task" confirmation below the
    # consequences.
    #
    # It also takes `action-primary--danger` with it. I called that class
    # dead - "nothing in the codebase defines it" - having checked base.html
    # and nowhere else. It was defined twelve lines into THIS PAGE'S own
    # <style>, and it was painting that button solid #dc3545. The class was
    # not dead; my search was. The second repair below removes the two rules
    # now that nothing carries the class, which is a different claim and a
    # true one.
    ('projects/project_tasks_delete.html',
     'the delete moves below the warnings it is warning you about',
     '<!-- Action Buttons: Back+1 (Delete is the primary danger action) -->\n<div class="page-action-buttons">\n  <button type="submit" form="deleteForm" class="btn action-secondary action-danger action-primary--danger">\n    <i class="fas fa-trash"></i> Delete Task\n  </button>\n',
     '<!-- Action Buttons: Back only. The delete lives BELOW the warnings,\n     where the reader has already seen what it will do. -->\n<div class="page-action-buttons">\n'),
    # ORDER MATTERS: this runs after the repair above, which removes the only
    # markup carrying the class. Run it first and it would delete a rule that
    # was still painting a live button - which is exactly the mistake the
    # comment above admits to, made in the other direction.
    ('projects/project_tasks_delete.html',
     'the danger rules are orphaned now that nothing carries the class',
     '\n/* Danger variant */\n.action-primary--danger {\n    background: #dc3545;\n    border-color: #dc3545;\n}\n\n@media (hover: hover) and (pointer: fine) {\n    .action-primary--danger:hover {\n        background: #c82333;\n        border-color: #bd2130;\n        color: white;\n        transform: translateY(-1px);\n        box-shadow: 0 2px 4px rgba(220,53,69,0.3);\n    }\n}\n',
     '\n'),
]


def drop_second_bar(fname, text):
    """Remove the SECOND .page-action-buttons on a page that has two."""
    m = sb.markup_of(text)
    found = [(a, z) for n, a, z in sb.bars(m) if n == sb.STANDARD_BAR]
    if len(found) < 2:
        return text, 0
    if len(found) != 2:
        sys.exit('! %s has %d standard bars, expected exactly 2 - stopping '
                 'rather than guessing which one to remove.'
                 % (fname, len(found)))
    a, z = found[1]
    seg = m[a:z]
    if 'type="submit"' not in seg:
        sys.exit('! %s: the second bar holds no submit button, so it is not '
                 'the duplicate this repair was written for. Stopping.' % fname)
    if re.search(r'\sform="', seg):
        sys.exit('! %s: the second bar submits a form of its own, so it may '
                 'not be a duplicate of the first. Stopping.' % fname)
    e = z
    while e < len(text) and text[e] in ' \t\r\n':
        e += 1
    return text[:a] + text[e:], 1


def named_repairs(fname, text):
    """(text, applied, [(file, what) skipped]).

    A repair has THREE states, not two, and the two-state version cost us a
    test run on the real tree.

      1. the anchor is there            -> apply it
      2. the result is already there    -> nothing to do
      3. NEITHER is there               -> this page is not at the stage the
                                           repair was written against

    State 3 is normal and expected the moment anything rebuilds an older
    version of the tree - and both the --check-vs-apply harness and the
    idempotence harness do exactly that, from `.bak_btnsweep` files that may
    have been written in any earlier round. These anchors were written
    against the page as the sweep leaves it, so on a pre-sweep copy they
    match nothing and the patcher used to `sys.exit` mid-run. Five checks
    failed and not one of them was about the sweep.

    It is still REPORTED, never silent: a repair that stops matching because
    somebody edited the page is the thing this guard exists to catch, and
    "it quietly did nothing" is how that would get missed. Matching MORE
    than once is still a hard stop - that one has bitten already.
    """
    n, skipped = 0, []
    if fname in DROP_SECOND_BAR:
        text, k = drop_second_bar(fname, text)
        n += k
    for f, what, old, new in REPAIRS:
        if f != fname:
            continue
        c = text.count(old)
        if c == 0:
            if new not in text:
                skipped.append((fname, what))
            continue                       # already applied, or not yet due
        if c != 1:
            sys.exit('! %s: repair anchor matched %d times, expected exactly '
                     '1.\n  (%s)\n  Stopping rather than guessing.'
                     % (fname, c, what))
        text = text.replace(old, new)
        n += 1
    return text, n, skipped

# ---------------------------------------------------------------------------
# 2 + 3.  per template: rename the bar, retone the buttons
# ---------------------------------------------------------------------------

def bar_renames(markup):
    """(start, end, old, new) for the class attribute of each drifting bar."""
    # A page that ALREADY has a .page-action-buttons does not get a second
    # one. Round two renamed .form-footer-actions and .form-action-row - a
    # form's Save/Cancel row really is the same component as a page bar - but
    # on six pages that already had a bar at the top the result was two
    # identical bars, one above the form and one below it. Before the sweep
    # the duplication was camouflaged, because a header bar and a form footer
    # looked like different things; afterwards they were the same thing twice.
    # The check already existed for the redundant-wrapper case; it should
    # have existed here.
    has_standard = any(n == sb.STANDARD_BAR for n, _a, _z in sb.bars(markup))
    out = []
    for name, a, _z in sb.bars(markup):
        if name == sb.STANDARD_BAR or has_standard:
            continue
        m = re.match(r'<div[^>]*?class="([^"]*)"', markup[a:])
        if not m:
            continue
        old = m.group(1)
        # Keep every other class on the div. Only the bar name is replaced,
        # because a wrapper often carries a page hook as well
        # (`page-action-bar-inner` sits inside a positioning shell).
        new = ' '.join(sb.STANDARD_BAR if c == name else c
                       for c in old.split())
        s = a + m.start(1)
        out.append((s, s + len(old), old, new))
    return out


def redundant_parent(markup, a, z):
    """The enclosing div, when it wraps this bar and nothing else.

    fsr.html / fsr_add.html / fsr_details.html nest the bar:

        <div class="page-action-bar">          <- positions the row
          <div class="page-action-bar-inner">  <- IS the row
            ...buttons...

    Rename the inner and the outer is still `justify-content: flex-end`,
    which shrink-wraps the renamed bar; `flex-wrap: wrap` then breaks it
    onto two rows. Measured on fsr.html: 2 rows where 1 was expected.

    So the outer has to go. Returns the offsets of its opening and closing
    tags, but only when it contains this bar AND NOTHING ELSE - if it holds
    a heading or anything besides whitespace, it is doing a job and stays.
    """
    best = None
    for m in re.finditer(r'<div[^>]*>', markup[:a]):
        depth, end = 0, None
        for d in re.finditer(r'<div\b|</div>', markup[m.start():]):
            if d.group(0) == '</div>':
                depth -= 1
                if depth == 0:
                    end = m.start() + d.end()
                    break
            else:
                depth += 1
        if end is None or end < z:
            continue
        inside = markup[m.end():a] + markup[z:end - len('</div>')]
        if inside.strip():
            continue
        if best is None or m.start() > best[0]:
            best = (m.start(), m.end(), end - len('</div>'), end)
    return best


def rename_css(text, old):
    """Rewrite `.old-bar-name` to `.page-action-buttons` in the page's CSS.

    Renaming the wrapper in the markup alone leaves every page rule that
    names the old class matching nothing. Those rules are not "kept", they
    are dead - and a dead rule reads as a live one to the next person.
    """
    # <script> as well as <style>: finance_pl_act.html does
    # `document.querySelector('.pl-action-bar')`. Renaming the class in the
    # markup and the CSS but not the JavaScript leaves a selector that
    # silently matches nothing - the dropdown just stops working, with no
    # error and nothing for a test to see.
    n = 0
    out = []
    last = 0
    for sm in re.finditer(r'<style[^>]*>(.*?)</style>'
                          r'|<script[^>]*>(.*?)</script>',
                          text, re.S | re.I):
        if sm.group(2) is not None:
            new, k = re.subn(r'(?<=[\'"\s.#])%s\b' % re.escape(old),
                             sb.STANDARD_BAR, sm.group(2))
            n += k
            out.append(text[last:sm.start(2)])
            out.append(new)
            last = sm.end(2)
            continue
        block = sm.group(1)
        new, k = re.subn(r'\.%s\b' % re.escape(old),
                         '.' + sb.STANDARD_BAR, block)
        n += k
        out.append(text[last:sm.start(1)])
        out.append(new)
        last = sm.end(1)
    out.append(text[last:])
    return ''.join(out), n


def sweep_template(fname, text):
    """Returns (new text, buttons changed, inline styles removed, unwraps).

    Writes nothing. The caller owns the file, so --check and a real run walk
    the SAME code path and cannot disagree - see main().
    """
    markup = sb.markup_of(text)

    edits = []
    # scan_text, NOT scan. scan() reads the file from disk; by the time we
    # get here the caller has already applied the named repairs to `text`,
    # so a disk scan is a plan for the PREVIOUS version of the page. That is
    # how friday_status_report.html took two runs to settle: run 1 renamed
    # its wrapper in memory, then planned against a disk copy where the
    # wrapper was still .header-actions and the two buttons were not in a
    # bar at all - so the retone silently did nothing and only landed on the
    # next run. Worse, the repair changes the file's LENGTH, so every offset
    # after it was shifted; the class-match guard below caught nothing only
    # because the shifted text happened to still parse. This is the same
    # fault as --check-vs-apply, in the one place it was left unfixed.
    for h in sb.scan_text(fname, text):
        _kind, _lab, _boot, cls, want, s, e, why = h
        if why or not sb.drifting(h):
            continue
        tag = markup[s:e]
        m = re.search(r'class="([^"]*)"', tag)
        if not m or m.group(1) != cls:
            sys.exit('! %s: the button at offset %d does not carry the class '
                     'the scanner reported.\n'
                     '  expected %r\n  found    %r\n'
                     '  Stopping - the plan and the file disagree.'
                     % (fname, s, cls, m.group(1) if m else None))
        cs = s + m.start(1)
        edits.append((cs, cs + len(cls), cls, want))

    renamed = bar_renames(markup)
    edits.extend(renamed)

    # A tone on something that is not a button. base.html's tone selectors
    # are deliberately unpaired as well as paired (`.action-secondary,
    # .btn.action-secondary`) so they reach buttons that lack `.btn` - which
    # means they also paint any DIV wearing the class. fsr.html and
    # tenant.html both wrap their Reports dropdown in
    # `<div class="ui-menu action-secondary">`, and base gives that wrapper
    # a border and 8px/16px of padding: a box drawn around the button
    # inside it. The button already carries the tone; the wrapper should not.
    for d in re.finditer(r'<(?:div|section|form|li|td)\b[^>]*class="([^"]*)"',
                         markup):
        cls = d.group(1)
        keep = [c for c in cls.split() if c not in sb.TONES]
        if len(keep) != len(cls.split()):
            s = d.start(1)
            edits.append((s, s + len(cls), cls, ' '.join(keep)))

    # Drop a wrapper that exists only to hold the bar. Done as a pair of
    # empty-string edits so it rides the same back-to-front pass.
    unwrapped = 0
    for name, a, z in sb.bars(markup):
        par = redundant_parent(markup, a, z)
        if par and sb.wrapper_name(
                re.match(r'<div[^>]*class="([^"]*)"',
                         markup[par[0]:par[1]]).group(1)
                if re.match(r'<div[^>]*class="([^"]*)"',
                            markup[par[0]:par[1]]) else ''):
            edits.append((par[2], par[3], markup[par[2]:par[3]], ''))
            edits.append((par[0], par[1], markup[par[0]:par[1]], ''))
            unwrapped += 1

    # Back to front, so every offset stays valid while we edit.
    edits.sort(key=lambda x: -x[0])
    for s, e, old, new in edits:
        assert text[s:e] == old, (fname, s, text[s:e], old)
        text = text[:s] + new + text[e:]

    # The page's own CSS has to follow the markup, or its rules go dead.
    for _s, _e, old, _new in renamed:
        for cls in old.split():
            if cls in sb.BAR_NAMES and cls != sb.STANDARD_BAR:
                text, _k = rename_css(text, cls)

    # Inline styles that .disabled-btn now covers. Left behind, they say the
    # same thing twice and drift apart the next time one of them is edited.
    inline = 0
    if edits:
        text, inline = re.subn(
            r'\s*style="opacity:\s*0?\.6;\s*cursor:\s*not-allowed;'
            r'\s*pointer-events:\s*none;?\s*"', '', text)

    return text, len(edits), inline, unwrapped


# ---------------------------------------------------------------------------
# 4.  page-local CSS that base.html now says, identically
# ---------------------------------------------------------------------------

def blank_comments(css):
    """Comments out, LENGTH KEPT, so offsets into the block stay valid.

    Stripping them outright shifted every later rule and the patcher cut the
    wrong bytes. Same lesson as markup_of.
    """
    return re.sub(r'/\*.*?\*/', lambda m: re.sub(r'[^\n]', ' ', m.group(0)),
                  css, flags=re.S)


# `background` and `background-color` are the same declaration written two
# ways; so are `border` and its longhand when only a colour differs. Compare
# the shorthand each page actually used.
ALIAS = {'background-color': 'background'}


def declarations(body):
    out = {}
    for part in body.split(';'):
        if ':' not in part:
            continue
        k, v = part.split(':', 1)
        k = k.strip().lower()
        v = re.sub(r'\s*!\s*important\s*$', '', ' '.join(v.split()).lower())
        out[ALIAS.get(k, k)] = v.strip()
    return out


def rules_of(css, media=''):
    """{(media condition, selector): {property: value}}, nesting-aware.

    Keyed by the media condition as well as the selector, because a rule
    inside `@media (max-width: 768px)` and the same selector outside it are
    different rules. v1 of this function ignored that and punted every
    @media rule to manual review - which was 350 of the 400, i.e. all the
    ones that actually matter.
    """
    out = {}
    i, n = 0, len(css)
    while i < n:
        at = re.compile(r'@media([^{]*)\{').search(css, i)
        rule = re.compile(r'([^{}@]+)\{([^{}]*)\}').search(css, i)
        if at and (not rule or at.start() < rule.start()):
            depth, j = 1, at.end()
            while j < n and depth:
                if css[j] == '{':
                    depth += 1
                elif css[j] == '}':
                    depth -= 1
                j += 1
            cond = ' '.join(at.group(1).split())
            for k, v in rules_of(css[at.end():j - 1],
                                 (media + ' and ' + cond).strip(' and ')).items():
                out.setdefault(k, {}).update(v)
            i = j
            continue
        if not rule:
            break
        for sel in rule.group(1).split(','):
            sel = ' '.join(sel.split())
            if sel:
                out.setdefault((media, sel), {}).update(
                    declarations(rule.group(2)))
        i = rule.end()
    return out


def base_rules():
    text, _b, _c = load(os.path.join(TPL, 'base.html'))
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', text, re.S | re.I))
    return rules_of(blank_comments(css))


BASE = base_rules()


# Every deletion that moves something by more than 6px, so a visible change
# is named rather than discovered on Live.
NOTABLE = []

# Longest name first, and anchored with \b. Plain `.replace('.page-action-bar',
# ...)` rewrote `.page-action-bar-inner` into `.page-action-buttons-inner` - a
# name base.html does not define - so nine real duplicates read as "keep" and
# two visible changes (fsr's bar gap, 16px -> 8px) never reached the dry-run
# report. A prefix is not a name.
_BARS_LONGEST_FIRST = sorted((n for n in sb.BAR_NAMES if n != sb.STANDARD_BAR),
                             key=len, reverse=True)


def normalise(sel):
    for n in _BARS_LONGEST_FIRST:
        sel = re.sub(r'\.%s\b' % re.escape(n), '.' + sb.STANDARD_BAR, sel)
    return sel


def as_px(v):
    m = re.fullmatch(r'(-?[\d.]+)(px|rem|em)?', (v or '').strip())
    if not m:
        return None
    return float(m.group(1)) * (16 if m.group(2) in ('rem', 'em') else 1)


def media_at(css, pos):
    """The @media condition in force at this offset, '' at top level."""
    stack, i = [], 0
    while i < pos:
        at = re.compile(r'@media([^{]*)\{').search(css, i)
        if not at or at.start() >= pos:
            break
        depth, j = 1, at.end()
        while j < len(css) and depth:
            if css[j] == '{':
                depth += 1
            elif css[j] == '}':
                depth -= 1
            j += 1
        if at.end() <= pos < j:
            stack.append(' '.join(at.group(1).split()))
            i = at.end()
        else:
            i = j
    return ' and '.join(stack)


def redundant_css(fname, text):
    """(rules deleted, rules kept) for one template.

    A page-local rule goes only when base.html DEFINES EVERY SELECTOR IN IT,
    under the same media condition. Then base is the single source for those
    elements and the page's copy is a second opinion.

    An earlier version also demanded the declarations match value for value.
    That deleted 20 rules out of 500 and left the job undone, because these
    are not duplicates - they are the same design hand-copied and drifted.
    Measured across the module:

        127 numeric differences, 122 of them 6px or smaller
        ~630 non-numeric, concentrated in justify-content (119) and
             align-items (115) - which IS the agreed layout change
        260 selectors base.html does not define at all

    So value-equality is the wrong test: the differences are the drift being
    removed. Selector coverage is the right one. Those 260 uncovered
    selectors - .action-back-label, .action-more-item-danger:hover, page
    hooks - are kept, because deleting a rule nothing replaces is how a
    sweep silently breaks a page.
    """
    gone, keep = [], []
    cuts = []
    owned = re.compile(r'\.(%s)\b' % '|'.join(sb.BAR_NAMES + sb.HOUSE))

    for sm in re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S | re.I):
        block, base_off = blank_comments(sm.group(1)), sm.start(1)
        for m in re.finditer(r'([^{}@]+)\{([^{}]*)\}', block):
            sels = [' '.join(s.split()) for s in m.group(1).split(',')]
            sels = [s for s in sels if s]
            if not sels or not any(owned.search(s) for s in sels):
                continue
            media = media_at(block, m.start())
            want = declarations(m.group(2))
            if not want:
                continue
            covered, shifts = True, []
            for s in sels:
                norm = normalise(s)
                have = BASE.get((media, norm))
                if not have:
                    covered = False
                    break
                for k, v in want.items():
                    a, b = as_px(v), as_px(have.get(k, ''))
                    if a is not None and b is not None and abs(a - b) > 6:
                        shifts.append((norm, k, v, have.get(k)))
            if covered:
                gone.append(sels[0])
                cuts.append((base_off + m.start(), base_off + m.end()))
                NOTABLE.extend((fname,) + s for s in shifts)
            else:
                keep.append((sels[0], 'base.html does not define this - '
                                      'page-specific, left in place'))

    for s, e in sorted(cuts, reverse=True):
        text = text[:s] + text[e:]
    return text, gone, keep


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

def main():
    print('')
    print('=' * 74)
    print(' BUTTON SWEEP - property management module%s'
          % ('   [--check, nothing will be written]' if CHECK else ''))
    print('=' * 74)
    print('')

    n, how = patch_base()
    print('  base.html            disabled-primary rule: %s' % how)
    n2, how2 = patch_base_shape()
    print('  base.html            Back-outside-a-bar shape rule: %s' % how2)
    print('')

    files = sb.templates(False)
    touched = buttons = renames = inlines = unwraps = 0
    deleted = review = repaired = 0
    css_rows = []
    # The text each page ENDS this run with. The reason tally at the
    # bottom used to re-read from disk, which meant --check counted the
    # old file and a real run counted the new one - the same two-readers
    # split that made --check lie about the fsr gap.
    ended = {}
    not_due = []

    # ONE pass per file, holding the text in memory: markup sweep, then the
    # CSS pass over the RESULT of that sweep, then a single write.
    #
    # These used to be two loops, each re-reading from disk. Under --check
    # nothing was written between them, so the CSS pass saw the ORIGINAL
    # wrapper names while a real run saw the renamed ones - and the dry run
    # reported 253 deletions where applying did 262, hiding two visible
    # changes. A dry run that predicts something other than the real run is
    # worse than no dry run, so there is now only one path and --check is
    # nothing but "do not call save()".
    for f in files:
        path = os.path.join(TPL, f)
        text, bom, crlf = load(path)
        before = text

        text, fixed, skipped = named_repairs(f, text)
        if fixed:
            repaired += fixed
            print('  %-40s %3d named repair(s)' % (f, fixed))
        not_due.extend(skipped)

        plan = [h for h in sb.scan_text(f, text) if sb.drifting(h) and not h[7]]
        rens = bar_renames(sb.markup_of(text))
        if plan or rens:
            text, _got, inline, unw = sweep_template(f, text)
            touched += 1
            buttons += len(plan)
            renames += len(rens)
            inlines += inline
            unwraps += unw
            print('  %-40s %3d button(s)%s' % (
                f, len(plan), '   + bar renamed' if rens else ''))

        text, gone, keep = redundant_css(f, text)
        deleted += len(gone)
        review += len(keep)
        if gone:
            css_rows.append((f, len(gone)))

        ended[f] = text
        if text != before and not CHECK:
            backup(path)
            save(path, text, bom, crlf)

    print('')
    print('  %d template(s), %d button(s), %d bar(s) renamed, '
          '%d inline style(s) removed' % (touched, buttons, renames, inlines))
    if repaired:
        print('  %d named repair(s) applied' % repaired)
    if not_due:
        # Never silent. A repair that stops matching because somebody edited
        # the page is exactly what this guard is for; the only reason to
        # tolerate it is that a rebuilt older copy of the tree legitimately
        # has not reached the stage these anchors were written against.
        print('  %d named repair(s) found nothing to anchor to - this page '
              'is not at the' % len(not_due))
        print('  stage they were written against (normal on a rebuilt '
              'pre-sweep tree):')
        for _f, _what in not_due:
            print('     %-40s %s' % (_f[:40], _what[:34]))
    if unwraps:
        print('  %d redundant wrapper div(s) removed - a bar inside a bar '
              'wraps to two rows' % unwraps)

    print('')
    print('  page-local CSS')
    print('  ' + '-' * 68)
    for f, n_gone in css_rows:
        print('  %-40s %2d rule(s) deleted' % (f, n_gone))
    print('  ' + '-' * 68)
    print('  %d rule(s) deleted - base.html defines those selectors' % deleted)
    print('  %d rule(s) kept - base.html does not define them (page-specific)'
          % review)
    # Count what is PRINTED, not what was collected: the list is
    # deduplicated, so len(NOTABLE) can be larger than the lines below and a
    # header that disagrees with its own list is the kind of small lie that
    # trains you to stop reading the output.
    shown, seen = [], set()
    for f, sel, prop, was, now in NOTABLE:
        k = (f, sel, prop)
        if k not in seen:
            seen.add(k)
            shown.append((f, sel, prop, was, now))
    if shown:
        print('')
        print('  %d deletion(s) move something by more than 6px. Named here so'
              % len(shown))
        print('  a visible change is not discovered on Live:')
        for f, sel, prop, was, now in shown:
            print('     %-34s %-26s %s  %s -> %s'
                  % (f[:34], sel[:26], prop, was, now))

    # Print the REASONS, not one rolled-up number under a round-one label.
    # "73 buttons: colour is template logic, or a menu row" was true of three
    # of them; the other seventy were the row actions, filter chrome and
    # segmented toggles that were reviewed and left on purpose. A header that
    # disagrees with its own contents trains you to stop reading the output.
    reasons = collections.Counter()
    for f in files:
        for h in sb.scan_text(f, ended[f]):
            if h[7]:
                reasons[h[7]] += 1
    recipes = len(sb.templates(True)) - len(files)
    print('')
    print('  deliberately not touched - %d button(s), by reason:'
          % sum(reasons.values()))
    for why, n in reasons.most_common():
        print('     %3d   %s' % (n, why))
    print('     %3d   template(s) on the recipe / meal-plan side '
          '(agreed follow-up)' % recipes)
    print('')

    if CHECK:
        print('  --check: nothing was written.')
    else:
        print('  Backups: *%s   Now run: python test_button_sweep.py' % SUFFIX)
    print('')

    if '--review' in sys.argv:
        print('=' * 74)
        print(' LEFT ALONE - base.html does not say the same thing')
        print('=' * 74)
        for f in files:
            _g, keep = redundant_css(f)
            if keep:
                print('')
                print('  %s' % f)
                for sel, why in keep:
                    print('     %-46s %s' % (sel[:46], why))
        print('')
    return 0


if __name__ == '__main__':
    sys.exit(main())
