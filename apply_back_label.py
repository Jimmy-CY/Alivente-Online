# -*- coding: utf-8 -*-
"""apply_back_label.py - Section D, round D7: one rule for the Back word,
instead of seventy-seven.

    python apply_back_label.py --check     dry run, nothing written
    python apply_back_label.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

Decided 24 Sep, from claude/d7_back_label_survey.md.

THE PLAN CALLED THIS "78 pages with an unscoped .action-back-label".
Re-measured: 78 is right only if you count base itself. It is 77 pages -
62 property and 15 Personal - and they are not seventy-seven decisions.
They are ONE rule, copied seventy-seven times:

    rules per page                                   exactly one, on all 77
    written `.action-back-label { display: none; }`   76
    already scoped (preview_imported_recipe)           1
    a body that is anything but `display: none`        0
    inside @media screen and (max-width: 768px)       75
    inside that plus `and (orientation: portrait)`     2

WHY THEY ALL EXIST. Base's rule was three ancestors deep:

    .page-action-buttons .action-back .action-back-label

The label only ever appears inside a back button, but base would only
hide it when that button ALSO sat inside the action bar. Parsed, the 100
label elements in the system fall out like this:

    inside .action-back, inside .page-action-buttons    85   base reached
    inside .action-back, OUTSIDE .page-action-buttons   14   base did NOT
    inside .btn.back-button, outside both                1   base did NOT

So "just scope all 78" would have been a REGRESSION on fourteen pages:
their unscoped copy is the only thing hiding the word.

AND ONE OF THEM IS NOT LATENT. resolved_issues_report.html wears the
label on a .btn.back-button, outside the bar, and is one of the nineteen
templates with no rule of their own. Nothing hides it. It SHOWS THE WORD
on a phone, today, in production.

THE ANSWER IS THE SELECTOR, NOT THE SEVENTY-SEVEN COPIES.

    .action-back .action-back-label,
    .back-button .action-back-label { display: none; }

.back-button comes too because base already settled it, in its own words
beside the paint rules: ".back-button is what four report pages call
theirs. Same thing, different name, so it gets the same treatment rather
than a rewrite of four templates' markup." test_button_sweep.py names
resolved_issues_report as one of exactly two Backs under that name.

  NO PAGE MARKUP MOVES. Not one attribute. 85 pages see no change at all;
  14 are hidden by base instead of by themselves; one is fixed.

  SPECIFICITY IS SAFE. Base goes from 0,3,0 to 0,2,0 and every page rule
  it replaces is 0,1,0.

  THE CUT STARTS AFTER THE COMMENT. Three of the 77 have a comment above
  them, and all three describe the ACTION ROW, not the label. A cutter
  that takes the whitespace run back to the previous brace eats them.
  This one stops at the last */.

THE ONE "VISIBLE CHANGE" THIS ROUND WAS AGREED TO MAKE DOES NOT EXIST.
The survey said finance_expense_types and finance_revenue_types put
their rule inside `and (orientation: portrait)`, so those two showed the
word on a phone held sideways and joining the standard would take it
away. Rendered at 700x375 against the OLD base, both measured `none`:
their Back button sits inside .page-action-buttons, base's old rule had
no orientation, and it was already hiding the word in both. Their
portrait-only rule was redundant in every orientation, not one.

So the round changes NOTHING a person can see, anywhere, except the page
it fixes. Lesson 20 - a written finding is a measurement too - caught on
this round's own survey, by the suite, before delivery.
test_back_label.py measures all 95 wearers sideways as well as upright.

AGREED: all 77, the 15 Personal included. Base's widened rule covers them
either way; leaving their copies behind only means doing the identical
deletion twice. They are named in this file, the way D6 named
passport_management, rather than crossed silently.
"""
# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------

import os
import re
import sys

CHECK = '--check' in sys.argv
T = os.path.join('pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
SUFFIX = '.bak_backlabel'
SUITE = 'test_back_label.py'
PS1 = 'Push-PendingChanges.ps1'
ROUNDS_FILE = 'alv_rounds.py'
BASE = os.path.join(T, 'base.html')

CRLF = {}
planned = {}
report = []
problems = []
cut_log = []


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    CRLF[p] = '\r\n' in raw
    return raw.replace('\r\n', '\n')


def write(p, text):
    if CRLF.get(p):
        text = text.replace('\n', '\r\n')
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


def style_spans(text):
    """(start, end) of every <style> block's CONTENTS.

    The cut must never see markup: every one of these pages carries
    <span class="action-back-label"> in the Back button itself, and that
    span is what the round is protecting. The cutter is not shown it."""
    return [(m.start(1), m.end(1)) for m in
            re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S | re.I)]


# FROM THE START OF THE SELECTOR'S LINE TO THE END OF THE CLOSING BRACE.
#
# The SELECTOR is on one line on all 77 - that is what makes this safe to
# anchor at a line start. The BODY is not: 28 pages write the rule on one
# line and 49 break it over three. A first draft required `{...}` to hold
# no newline and found 28 of the 77, which is the whole round quietly
# doing a third of its job - so the body may span lines, and cannot cross
# a brace, which is what stops it swallowing the rule after it.
#
# Starting at the line's start and not at the previous brace is what
# leaves the three preceding comments alone.
LINE = re.compile(r'(?m)^[ \t]*[^\n{}]*\.action-back-label[^\n{}]*'
                  r'\{[^{}]*\}[ \t]*\n')

# ==========================================================================
# BASE TAKES THE SCOPE OFF
# ==========================================================================
BASE_OLD = ('        .page-action-buttons .action-back .action-back-label'
            ' { display: none; }\n')
BASE_NEW = """        /* ===== ALV BACK LABEL v1 ===== 24 Sep 2026
           The word beside the arrow on a Back button, hidden below 768px
           so the button is a 44px square. 3.4 asks for the square; this
           is what makes room for it.

           THIS RULE USED TO BE THREE ANCESTORS DEEP -
           `.page-action-buttons .action-back .action-back-label` - and 77
           pages each wrote `.action-back-label { display: none }`,
           unscoped, to make up the difference. Measured 24 Sep: one rule
           per page, the same declaration on every one of them, and of the
           100 label elements in the system base could reach only 85. Of
           the other fifteen, fourteen sit in a .action-back that is not
           inside the bar - so deleting their copy WITHOUT widening this
           would have put the word back on a phone - and one sat on a
           .btn.back-button with no rule at all, which is why
           resolved_issues_report SHOWED THE WORD.

           The label only ever appears inside a back button. That is what
           it is scoped to now, and nothing else. .back-button comes too:
           base already settled, beside the paint rules above, that it "is
           what four report pages call theirs - same thing, different
           name", and gave it the same treatment rather than rewriting
           four templates.
           See test_back_label.py. */
        .action-back .action-back-label,
        .back-button .action-back-label { display: none; }
        /* ===== /ALV BACK LABEL v1 ===== */
"""

# ==========================================================================
# THE 15 PERSONAL PAGES, NAMED
#
# 3.9 and test_modal_heads both hold the line that the Personal side waits
# for its own round. This round crosses it on purpose and with the user's
# word, for a deletion that is identical on all 77 - so the fifteen are
# written down here rather than slipped in among the sixty-two.
# ==========================================================================
PERSONAL = (
    'categories_management.html', 'celebration_dashboard.html',
    'celebration_management.html', 'create_meal_plan.html',
    'ingredient_base_units_management.html', 'meal_plan_calendar.html',
    'meal_plan_shopping_list.html', 'meal_plans.html',
    'measurement_units_management.html', 'passport_management.html',
    'preview_imported_recipe.html', 'recipe_management.html',
    'unit_conversions_management.html', 'view_meal_plan.html',
    'view_recipe.html',
)
# The two that hid the word only in portrait. Named because the survey
# expected them to be the round's one visible change, and rendering them
# sideways against the old base proved they never were: base was already
# hiding the word in both orientations. Kept in the report so the claim
# and its correction stay together.
LANDSCAPE = ('finance_expense_types.html', 'finance_revenue_types.html')

# ==========================================================================
# LATER - the suites whose findings this round moved
# ==========================================================================
LATER = {}

# test_small_three.py, D2. Its proof that workspace_management's stray
# class name was harmless rested on OTHER pages carrying an unscoped copy
# ("someone else's page is the proof that it is not a theory") and on
# base's rule being the three-deep one. Both move today. Neither is
# lowered: the count is asked of the BACKUPS, where those pages still
# carry it, and the scope check is asked of the new selector.
LATER['test_small_three.py'] = [
    ("        if re.search(r'(?m)^\\s*\\.action-back-label\\s*\\{[^}]*"
     "display:\\s*none',\n"
     "                     read(os.path.join(base_, f))):\n"
     "            _unscoped.append(f)\n"
     "ok(len(_unscoped) > 50,\n"
     "   '%d other pages carry an UNSCOPED .action-back-label hide rule'\n"
     "   % len(_unscoped), len(_unscoped))\n",
     "        p_ = os.path.join(base_, f)\n"
     "        if re.search(r'(?m)^\\s*\\.action-back-label\\s*\\{[^}]*"
     "display:\\s*none',\n"
     "                     read(p_)):\n"
     "            _unscoped.append(f)\n"
     "        # LATER - Section D round D7, 24 Sep. Round D7 deleted all\n"
     "        # 77 of those copies and widened base's rule to reach the\n"
     "        # back button wherever it sits. The CLAIM is unchanged and\n"
     "        # still has to be true - it is asked of the file as it\n"
     "        # stood before D7, which is what D7's backup holds.\n"
     "        elif os.path.isfile(p_ + '.bak_backlabel') and re.search(\n"
     "                r'(?m)^\\s*\\.action-back-label\\s*\\{[^}]*"
     "display:\\s*none',\n"
     "                read(p_ + '.bak_backlabel')):\n"
     "            _was_unscoped.append(f)\n"
     "ok(not _unscoped,\n"
     "   'no page carries an unscoped .action-back-label hide rule any '\n"
     "   'more - D7 removed every one', _unscoped[:6])\n"
     "ok(len(_was_unscoped) > 50,\n"
     "   '  CONTROL: %d of them did, and that is what made this page\\'s '\n"
     "   'stray class name a real risk rather than a theory'\n"
     "   % len(_was_unscoped), len(_was_unscoped))\n"),
    ("_unscoped = []\n", "_unscoped, _was_unscoped = [], []\n"),
    ("ok(re.search(r'\\.page-action-buttons\\s+\\.action-back\\s+"
     "\\.action-back-label',\n"
     "             B_NOW) is not None,\n"
     "   \"  while base's own rule is scoped to .action-back - which is why \"\n"
     "   'nothing was broken YET')\n",
     "# LATER - Section D round D7, 24 Sep. Base's rule was\n"
     "# `.page-action-buttons .action-back .action-back-label` and is now\n"
     "# `.action-back .action-back-label, .back-button .action-back-label`.\n"
     "# The point of this check - that base hides the span only INSIDE a\n"
     "# back button, which is what makes a Help button wearing the class\n"
     "# inert - is exactly the same, and is now true in more places.\n"
     "ok(re.search(r'\\.action-back\\s+\\.action-back-label\\s*,\\s*'\n"
     "             r'\\.back-button\\s+\\.action-back-label',\n"
     "             B_NOW) is not None,\n"
     "   \"  while base's own rule is scoped to the back button - which is \"\n"
     "   'why nothing was broken YET')\n"
     "ok(re.search(r'\\.page-action-buttons\\s+\\.action-back\\s+'\n"
     "             r'\\.action-back-label', B_NOW) is None,\n"
     "   '  and it is no longer scoped to the BAR as well, which is what '\n"
     "   'left fourteen pages out of reach')\n"),
    # AND THE SAME FAULT ONE MORE TIME. base's new block SAYS what the
    # selector used to be, in the paragraph explaining why it changed, so
    # a check that reads base raw finds the old selector in the PROSE and
    # reports it as surviving. D6 met this as a class name in an HTML
    # comment; the patcher's own self-check met it an hour ago. Ask the
    # CSS, not the file.
    ("ok(re.search(r'\\.page-action-buttons\\s+\\.action-back\\s+'\n"
     "             r'\\.action-back-label', B_NOW) is None,\n",
     "ok(re.search(r'\\.page-action-buttons\\s+\\.action-back\\s+'\n"
     "             r'\\.action-back-label',\n"
     "             re.sub(r'/\\*.*?\\*/', '', B_NOW, flags=re.S)) is None,\n"),
]

# The three table suites, C3 and D4. Each holds a FLOOR on how many
# `.action-` rules its page still defines, and each page handed over one
# more today. The floor moves with the decision, by exactly one, named -
# never lowered quietly, which is what those suites' own paragraphs say
# a floor is for.
FLOOR_NOTE = (
    "                           # 8 UNTIL ROUND D7, 24 Sep: base took the\n"
    "                           # Back word's hide rule, rescoped from\n"
    "                           # `.page-action-buttons .action-back\n"
    "                           # .action-back-label` to the back button\n"
    "                           # itself. This page wrote\n"
    "                           # `.action-back-label { display: none }`\n"
    "                           # unscoped, as 76 others did. The floor\n"
    "                           # moved with the decision, by exactly\n"
    "                           # that one rule.\n"
    "                           ('.action-', 7, 'page-header buttons'),\n")
CONTROL_OLD = ("check('  CONTROL: the eight that remain are page-specific, "
               "not base\\'s',\n      group('.action-') == 8)\n")
CONTROL_NEW = ("check('  CONTROL: the seven that remain are page-specific, "
               "not base\\'s',\n      group('.action-') == 7)\n")
WHY_OLD = ("# WHY EIGHT AND NOT ELEVEN. A floor alone records a number, "
           "not a reason - and\n# this one has now moved once, which is "
           "exactly when a check earns an\n# explanation.")
WHY_NEW = ("# WHY SEVEN AND NOT ELEVEN. A floor alone records a number, "
           "not a reason - and\n# this one has now moved twice - the "
           "button sweep, then round D7 - which is\n# exactly when a check "
           "earns an explanation.")
for _f, _second in (('test_table_properties.py',
                     "                           ('.btn-', 4, "
                     "'page-header button colours')):\n"),
                    ('test_table_suppliers.py',
                     "                           ('.modal', 10, "
                     "'delete modal')):\n"),
                    ('test_table_tenants.py',
                     "                           ('.btn-', 4, "
                     "'page-header button colours')):\n")):
    _e = [("                           ('.action-', 8, "
           "'page-header buttons'),\n" + _second, FLOOR_NOTE + _second)]
    if _f != 'test_table_tenants.py':
        _e.append((CONTROL_OLD, CONTROL_NEW))
        _e.append((WHY_OLD, WHY_NEW))
    LATER[_f] = _e

# test_action_standard.py, 21 Sep. Its check for the label being hidden on
# a phone is a SUBSTRING of the whole rule, so it would have gone on
# passing against `.back-button .action-back-label { display: none; }` -
# and would go on passing against any selector at all ending that way.
# This is the fault D6 hit from the other side (a mention is not a use);
# here it is a substring that is not a selector. Made exact.
LATER['test_action_standard.py'] = [
    ("check('  losing only its label',\n"
     "      '.action-back-label { display: none; }' in MOBILE)\n",
     "# LATER - Section D round D7, 24 Sep. This was a SUBSTRING test: the\n"
     "# text it looked for is the tail of any selector ending in\n"
     "# .action-back-label, so it could not tell base's rule from a page's\n"
     "# unscoped copy pasted in beside it. D7 rewrote the rule, so it is\n"
     "# asked for the SELECTOR now, and a control proves it can tell.\n"
     "_LBL = re.compile(r'\\.action-back\\s+\\.action-back-label\\s*,\\s*'\n"
     "                  r'\\.back-button\\s+\\.action-back-label\\s*\\{'\n"
     "                  r'[^}]*display:\\s*none')\n"
     "check('  losing only its label, wherever the Back button sits',\n"
     "      _LBL.search(MOBILE) is not None)\n"
     "check('    CONTROL: an unscoped copy would NOT satisfy it',\n"
     "      _LBL.search('.action-back-label { display: none; }') is None)\n"),
]

# test_admin_banner.py, 20 Sep. Its closing note describes a state that
# two rounds have now left behind: D2 made workspace_management's Help a
# bare label, so the stray class name is gone, not merely inert.
LATER['test_admin_banner.py'] = [
    ("print('  NOTED, NOT FIXED: workspace_management spells its Help "
     "button\\'s')\n"
     "print('  label .action-back-label. base only hides that span inside "
     "an')\n"
     "print('  .action-back, so it is inert - a wrong name, not a wrong "
     "render.')\n",
     "# LATER - Section D round D7, 24 Sep. Both halves of this note are\n"
     "# spent. D2 made workspace_management's Help a bare label, so the\n"
     "# stray class name is gone rather than inert; D7 rescoped base's\n"
     "# rule to the back button itself. A note that describes a state two\n"
     "# rounds have left behind is how the next survey gets its count\n"
     "# wrong - which is the fault D7 was fixing.\n"
     "print('  CLOSED: workspace_management\\'s Help no longer spells its')\n"
     "print('  label .action-back-label - D2 made it bare text - and D7')\n"
     "print('  rescoped base\\'s rule to .action-back / .back-button.')\n"),
]

# ==========================================================================
# WORK
# ==========================================================================
if not os.path.isfile(BASE):
    problems.append('%s not found' % BASE)
else:
    b = read(BASE)
    if 'ALV BACK LABEL v1' in b:
        report.append('%-42s already holds the block' % 'base.html')
    elif b.count(BASE_OLD) != 1:
        problems.append('base.html: the anchor was found %d time(s)'
                        % b.count(BASE_OLD))
    else:
        planned[BASE] = (b, b.replace(BASE_OLD, BASE_NEW, 1))
        report.append('%-42s the scope comes off: + ALV BACK LABEL v1'
                      % 'base.html')

pages = []
for d, dirs, fs in os.walk(T):
    dirs[:] = [x for x in dirs if x != '__pycache__']
    for f in fs:
        if f.endswith('.html') and '.bak' not in f:
            pages.append(os.path.join(d, f))

done = n_cut = 0
for path in sorted(pages):
    if os.path.abspath(path) == os.path.abspath(BASE):
        continue
    src = read(path)
    rel = os.path.relpath(path, T).replace(os.sep, '/')
    name = os.path.basename(path)
    hits = []
    for s, e in style_spans(src):
        for m in LINE.finditer(src[s:e]):
            hits.append((s + m.start(), s + m.end(), m.group(0)))
    if not hits:
        continue
    if len(hits) != 1:
        problems.append('%s: the rule was found %d time(s) - measured as '
                        'exactly one on all 77, so a different number '
                        'means the page moved under this round'
                        % (rel, len(hits)))
        continue
    a, z, line = hits[0]
    cur = src[:a] + src[z:]
    tag = ('PERSONAL ' if name in PERSONAL else
           'LANDSCAPE' if name in LANDSCAPE else '         ')
    cut_log.append((rel, tag, ' '.join(line.split())))
    planned[path] = (src, cur)
    n_cut += 1

report.append('%-42s %d page(s) hand the rule back to base'
              % ('pages/templates/*.html', n_cut))

# --- LATER ---------------------------------------------------------------
for sv, edits in sorted(LATER.items()):
    if not os.path.isfile(sv):
        problems.append('%s not found' % sv)
        continue
    src_ = read(sv)
    cur_, n_, done_ = src_, 0, 0
    for old_, new_ in edits:
        # An INSERTION keeps its anchor, so ask whether the RESULT is
        # already here first and fall back to the anchor only for a
        # removal (lesson 27).
        if new_ and new_ in cur_:
            done_ += 1
            continue
        if old_ not in cur_:
            done_ += 1
            continue
        if cur_.count(old_) != 1:
            problems.append('%s: anchor found %d time(s): %r'
                            % (sv, cur_.count(old_), old_.strip()[:52]))
            continue
        cur_ = cur_.replace(old_, new_, 1)
        n_ += 1
    if n_:
        try:
            compile(cur_, sv, 'exec')
        except SyntaxError as e:
            problems.append('%s would not compile: line %s' % (sv, e.lineno))
        planned[sv] = (src_, cur_)
        report.append('%-42s LATER: %d edit(s)' % (sv, n_))
    elif done_ == len(edits):
        report.append('%-42s LATER: already done' % sv)

# ==========================================================================
# SELF-CHECKS: what this round must NOT have done
# ==========================================================================
for path, (src, cur) in list(planned.items()):
    if path.endswith('.py') or path.endswith('.ps1'):
        continue
    name = os.path.basename(path)
    if cur.count('{') != cur.count('}'):
        problems.append('%s: braces are unbalanced' % name)
    if sorted(re.findall(r'\bid="([^"]+)"', cur)) \
            != sorted(re.findall(r'\bid="([^"]+)"', src)):
        problems.append('%s: an id changed' % name)
    if cur.count('{%') != src.count('{%') or cur.count('{{') != src.count('{{'):
        problems.append('%s: a Django tag changed' % name)
    if path == BASE:
        if cur.count('ALV BACK LABEL v1') != 2:
            problems.append('base.html: the block is not opened and closed '
                            'exactly once')
        # COMMENTS OUT FIRST. The new block SAYS what the old selector was,
        # in the paragraph that explains why it changed, and a check that
        # reads the file raw calls that paragraph a surviving rule. D6 met
        # this from the other side - the words .alv-modal-head in an HTML
        # comment counted as a page wearing the class - and the answer is
        # the same: ask the CSS, not the prose.
        if '.page-action-buttons .action-back .action-back-label' in \
                re.sub(r'/\*.*?\*/', '', cur, flags=re.S):
            problems.append('base.html: the three-deep selector survived')
        continue
    # THE SPAN IS THE POINT. A cut that reached the markup would take the
    # word away everywhere instead of hiding it on a phone.
    mk_a = re.sub(r'<style[^>]*>.*?</style>', '', cur, flags=re.S | re.I)
    mk_b = re.sub(r'<style[^>]*>.*?</style>', '', src, flags=re.S | re.I)
    if mk_a != mk_b:
        problems.append('%s: the markup moved - this round cuts CSS only'
                        % name)
    if mk_a.count('action-back-label') != mk_b.count('action-back-label'):
        problems.append('%s: a label span was lost' % name)
    # And the three comments that sit above the rule on three pages.
    if src.count('/*') != cur.count('/*'):
        problems.append('%s: a comment went with the rule - the cut is '
                        'meant to stop at the last */' % name)

# ==========================================================================
# REGISTERED, AND ON THE GATE
# ==========================================================================
if os.path.isfile(ROUNDS_FILE):
    r = read(ROUNDS_FILE)
    if "'%s'" % SUFFIX in r:
        report.append('%-42s already lists this round' % ROUNDS_FILE)
    elif r.count("    '.bak_modal',\n]") != 1:
        problems.append('%s: cannot find the end of ROUNDS (.bak_modal) - '
                        'apply_modal_overlay.py first' % ROUNDS_FILE)
    else:
        planned[ROUNDS_FILE] = (r, r.replace(
            "    '.bak_modal',\n]",
            "    '.bak_modal',\n    '%s',\n]" % SUFFIX, 1))
        report.append('%-42s learns %s' % (ROUNDS_FILE, SUFFIX))
else:
    problems.append('%s missing' % ROUNDS_FILE)

GATE_NOTE = """    # Section D round D7: base hides the Back word wherever the button
    # sits, and 77 pages stop each writing the rule unscoped,
    'test_back_label.py'"""
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-42s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        if not m:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            planned[PS1] = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-42s + %s' % (PS1, SUITE))
else:
    problems.append('%s missing' % PS1)

# ==========================================================================
print('\n' + '=' * 78)
print('SECTION D, ROUND D7 - ONE RULE FOR THE BACK WORD - %s'
      % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 78)
for line in report:
    print('  ' + line)
if cut_log:
    n_p = sum(1 for _r, t, _l in cut_log if t.strip() == 'PERSONAL')
    n_l = sum(1 for _r, t, _l in cut_log if t.strip() == 'LANDSCAPE')
    print('\n  EVERY RULE THIS ROUND REMOVED (%d), and the page it sat on.'
          % len(cut_log))
    print('  PERSONAL marks the %d that cross into 2.K by agreement.'
          ' LANDSCAPE' % n_p)
    print('  marks the %d written portrait-only - base was already hiding'
          ' the' % n_l)
    print('  word sideways on both, so they change nothing either.')
    for rel, tag, line in cut_log:
        print('    %s %-44s %s' % (tag, rel[:44], line[:44]))
print('')
if problems:
    print('!' * 78)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 78)
    for p in sorted(set(problems)):
        print('  FAIL %s' % p)
    sys.exit(1)
if not planned:
    print('  Nothing to do - this round has already been applied.')
    sys.exit(0)
if CHECK:
    print('  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)
for path, (src, text) in sorted(planned.items()):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        CRLF[bak] = CRLF.get(path)
        write(bak, src)
    write(path, text)
print('  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
print('')
print('  Next:  python %s' % SUITE)
