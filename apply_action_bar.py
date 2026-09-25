# -*- coding: utf-8 -*-
"""apply_action_bar.py - Section E round E3, 25 Sep 2026.

THE ACTION BAR IS THE HOUSE CONTAINER UNDER ANOTHER NAME.

base.html already defines the whole .action-* family - .action-back,
.action-primary, .action-secondary, .action-more-btn, .action-more-menu,
.action-filter, .action-danger - and the container they live in,
.page-action-buttons. That container is not a minority pattern: EIGHTY-FIVE
templates wear it. base gives it a flex row with an 8px gap, pins Back to
the right because "Back is navigation, not an action on the data", collapses
on :has(.action-more-btn), draws focus-visible rings, and on a phone makes
every control in it 44x44.

Ten Personal templates use a local container instead - seven named
.action-bar, three named .action-buttons - and then restate base's own
children beneath it at higher specificity. Fifty-seven rules to re-describe
a component base owns.

IT ALSO COSTS THEM PART OF THE PHONE STANDARD - BUT LESS THAN THE SURVEY
SAID. base delivers 44px through `.page-action-buttons .btn { min-height:
44px }`, and none of that reaches a bar called something else, so each of
these pages wrote its own height. Seven of the ten DECLARE 38px.

The survey concluded from that "not one of the ten meets 44px". RENDERED
AT 390px, TWO CONTROLS OUT OF TWENTY-SEVEN WERE ACTUALLY UNDER:

    unit_conversions_management.html   More actions   38px
    view_meal_plan.html                More actions   38px

Everything else reached 44 anyway - padding and line-height carried the
buttons past a declaration that said 38. A DECLARATION IS NOT A PIXEL, and
this is the third time in two rounds that reading values out of CSS has
overstated what a browser draws.

So the honest case for this round is the duplication: one component under
three names, forty-two rules restating what base already owns, and two
real tap targets as well.

WHAT THIS ROUND DOES. Renames the container to .page-action-buttons, deletes
the local rules base already provides, keeps the few that are genuinely
local, and flattens an inner wrapper base has no rule for. The bar's layout
becomes the house layout: actions left, Back right, as on the other 85.

TWO TRAPS FOUND BY READING THE RULES RATHER THAN THE NAMES:

 1. meal_plan_shopping_list's `.action-bar, .step-indicator, ...` sits
    inside @media print and says `display: none !important`. Deleting that
    rule would have printed the action bar onto the shopping list - a
    regression visible only on paper. A GROUPED SELECTOR IS RENAMED, NEVER
    DELETED: the other names in it are not ours to drop.

 2. `.action-buttons .btn` in view_meal_plan LOOKS like a container rule
    with no .action-* child, which would mark it for deletion. It is the
    rule breaking the tap target, so deleting it is right - but only
    because base defines `.page-action-buttons .btn` to replace it. The
    classifier asks what BASE provides, not what the selector looks like.

WHAT THIS ROUND DOES NOT DO: view_recipe.html defines .action-buttons four
times and NOTHING WEARS IT - zero class attributes, no interpolation, no
script. It was surveyed as "a centred footer row wearing the page-bar name"
and a rename was agreed; measured, there is nothing to rename. It is an
ORPHAN and it belongs to E6 with the other 199. Recorded, not touched.
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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_actionbar'
CHECK = '--check' in sys.argv

HOUSE = 'page-action-buttons'
OLD = ('action-bar', 'action-buttons')

# Children that base does NOT define, so a rule about them is genuinely
# this page's own and is re-scoped rather than dropped.
LOCAL_ONLY = ('.action-count-badge', '.action-disabled',
              '.action-label-short', '.action-label-full')

# Per-file (rules deleted, rules re-scoped, class attributes renamed).
# The survey knows these; the patcher asserts them - lesson 35.
# The first version of this table was hand-counted off a printed
# classification and was wrong for three of the ten - it forgot that
# unwrapping removes a class attribute before the rename runs, so the
# three UNWRAP files rename ONE bar, not two. The patcher's own assertion
# caught it on the first dry run, which is what the assertion is for.
# These come from a separate counting script, not from this file's output.
EXPECTED = {
    'create_meal_plan.html': (4, 0, 1),
    'ingredient_base_units_management.html': (4, 10, 1),
    'map_ingredients_nutrition.html': (1, 0, 1),
    'meal_plan_shopping_list.html': (4, 1, 1),
    'meal_plans.html': (4, 0, 1),
    'measurement_units_management.html': (4, 0, 1),
    'unit_conversions_management.html': (8, 0, 1),
    'unit_conversions_wizard.html': (1, 0, 1),
    'view_meal_plan.html': (12, 0, 1),
}
# The inner wrapper base has no rule for. Its buttons become direct
# children of the bar, which is what base's rules expect and what the
# other 85 templates already do.
UNWRAP = ('view_meal_plan.html',)

# IN THESE THREE, .action-buttons IS NOT THIS COMPONENT AT ALL. It is the
# per-row action cell - it sits inside <td style="text-align: center">,
# holds .view-actions and .action-btn btn-edit, and calls
# enterEditMode(item...). The name is shared; the thing is not.
#
# The first version of this round treated all three as page bars or inner
# wrappers, because they were named like one. It renamed a row cell to
# .page-action-buttons on one page and UNWRAPPED A DIV OUT OF A <td> on two
# others, deleting the rules that laid those cells out. Every static check
# passed. What caught it was a 16px box in the rendered before-picture that
# had no business being in an action bar - .action-btn btn-edit, a row
# button - which is only visible because section 2 measures boxes.
#
# Lesson 39, three times in one round: classify by what a thing DOES.
ROW_CELL = {'categories_management.html',
            'ingredient_base_units_management.html',
            'measurement_units_management.html'}

LEAVE = {
    ('categories_management.html', '.action-buttons'):
        'a per-row action cell inside <td> - .view-actions, '
        '.action-btn btn-edit, enterEditMode(item). This page already '
        'wears the house container on its real bar. Row actions are D3.',
    ('ingredient_base_units_management.html', '.action-buttons'):
        'the same per-row action cell inside <td>. Only its .action-bar '
        'is this round\'s business.',
    ('measurement_units_management.html', '.action-buttons'):
        'the same per-row action cell inside <td>. Only its .action-bar '
        'is this round\'s business.',
    ('view_recipe.html', '.action-buttons'):
        'defined four times and worn by nothing - an orphan, not a '
        'component. Belongs to E6 with the other 199.',
    ('base.html', '.page-action-buttons'):
        'the house container itself. E3 changes no base rule: everything '
        'these ten pages need is already there.',
}

CSS_COMMENT = re.compile(r'/\*.*?\*/', re.S)
HTML_COMMENT = re.compile(r'<!--.*?-->', re.S)
STYLE = re.compile(r'<style[^>]*>(.*?)</style>', re.S | re.I)
RULE = re.compile(r'([^{}]+)\{([^{}]*)\}')
TOKEN = re.compile(r'(?<![\w-])\.(action-bar|action-buttons)(?![\w-])')
CLASSATTR = re.compile(r'class="([^"]*)"')

CRLF = {}


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8')


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def blanked(text):
    """Comments to spaces, SAME LENGTH, so offsets still line up.
    A mention is not a use (lesson 34)."""
    def spaces(m):
        return re.sub(r'[^\n]', ' ', m.group(0))
    return HTML_COMMENT.sub(spaces, CSS_COMMENT.sub(spaces, text))


def verdict(selector):
    """'keep' to re-scope this rule, 'drop' to delete it.

    A GROUPED SELECTOR IS ALWAYS KEPT. The other names in the list belong
    to other components and deleting the rule would take their styling
    with it - which is how a print rule nearly stopped hiding the bar."""
    if ',' in selector:
        return 'keep'
    if any(c in selector for c in LOCAL_ONLY):
        return 'keep'
    return 'drop'


def patch_css(text, rel=''):
    """Returns (new_text, dropped, kept). Works on the blanked copy to
    find rules, and edits the real one at the same offsets."""
    scan = blanked(text)
    edits, dropped, kept = [], 0, 0
    for blk in STYLE.finditer(scan):
        body_at = blk.start(1)
        for m in RULE.finditer(blk.group(1)):
            sel = m.group(1)
            if not TOKEN.search(sel):
                continue
            if rel in ROW_CELL and '.action-bar' not in sel:
                continue          # the row cell's own rules stay
            a, b = body_at + m.start(), body_at + m.end()
            if verdict(' '.join(sel.split())) == 'keep':
                edits.append((a, b, TOKEN.sub('.' + HOUSE, text[a:b])))
                kept += 1
            else:
                # take the whole rule and the blank line it sat on
                end = b
                while end < len(text) and text[end] in ' \t':
                    end += 1
                if end < len(text) and text[end] == '\r':
                    end += 1
                if end < len(text) and text[end] == '\n':
                    end += 1
                start = a
                while start > 0 and text[start - 1] in ' \t':
                    start -= 1
                edits.append((start, end, ''))
                dropped += 1
    for a, b, to in sorted(edits, reverse=True):
        text = text[:a] + to + text[b:]
    return text, dropped, kept


# NOT EVERY .action-buttons IS A PAGE BAR. Three templates had no
# .action-bar at all, so the survey called their .action-buttons the page
# bar - an inference from what was ABSENT, not a reading of what the
# element does. Two of the three are page bars; the third is not.
#
# categories_management.html already wears the house container on its real
# bar, at the top of the page, around Add Category. Its .action-buttons is
# somewhere else entirely: a per-item edit group holding .view-actions and
# .action-btn btn-edit, calling enterEditMode(item...). Renaming it gave
# the page TWO .page-action-buttons, one of them a row of row-actions
# wearing a page component's name.
#
# Lesson 39 again - classify by what a thing DOES. The marker is the
# child that gives it away, and it is checked, not assumed.
# .action-buttons is out of scope entirely in the ROW_CELL templates -
# not renamed, not deleted, not re-scoped. Only .action-bar is this
# round's business there. The marker is checked, never assumed.
ROW_MARK = 'view-actions'


def patch_classes(text, rel=''):
    """Rename the exact class TOKEN - never a regex on the file. base's
    own standards block records what that costs: a substring count of
    'action-bar' also catches 'mobile-action-bar', and reported 26 where
    the answer was 7. This round's survey made the same mistake again."""
    out, n, at = [], 0, 0
    for m in CLASSATTR.finditer(text):
        names = m.group(1).split()
        if not any(o in names for o in OLD):
            continue
        if rel in ROW_CELL and 'action-buttons' in names:
            continue
        new = [HOUSE if x in OLD else x for x in names]
        # a page that already wears the house name keeps it once
        seen, uniq = set(), []
        for x in new:
            if x not in seen:
                seen.add(x)
                uniq.append(x)
        out.append((m.start(1), m.end(1), ' '.join(uniq)))
        n += 1
    for a, b, to in sorted(out, reverse=True):
        text = text[:a] + to + text[b:]
    return text, n


def unwrap(text, rel):
    """Remove the inner <div class="action-buttons"> and its matching
    </div>, keeping the children. Depth-counted, and the div balance is
    asserted afterwards - test_div_balance polices the whole tree."""
    scan = blanked(text)
    hits = [m for m in CLASSATTR.finditer(scan)
            if 'action-buttons' in m.group(1).split()]
    if not hits:
        return text, 0
    if len(hits) != 1:
        raise SystemExit('E3: %s has %d inner wrappers, expected 1'
                         % (rel, len(hits)))
    m = hits[0]
    open_at = scan.rfind('<div', 0, m.start())
    open_end = scan.find('>', m.end()) + 1
    depth, i = 1, open_end
    while i < len(scan) and depth:
        o = scan.find('<div', i)
        c = scan.find('</div>', i)
        if c == -1:
            raise SystemExit('E3: %s - no closing </div> for the wrapper'
                             % rel)
        if o != -1 and o < c:
            depth += 1
            i = o + 4
        else:
            depth -= 1
            i = c + 6
            close_at = c
    before_open, before_close = text.count('<div'), text.count('</div>')
    text = text[:close_at] + text[close_at + 6:]
    text = text[:open_at] + text[open_end:]
    if (text.count('<div') != before_open - 1
            or text.count('</div>') != before_close - 1):
        raise SystemExit('E3: %s - unwrap did not remove exactly one pair'
                         % rel)
    return text, 1


def patch(rel):
    path = os.path.join(ROOT, rel)
    text = read(path)
    before = text
    if rel in ROW_CELL and ROW_MARK not in text:
        raise SystemExit(
            'E3: %s is listed as holding a row action cell, but %r is not '
            'in it. The classification is checked, not assumed - re-read '
            'the page before writing anything.' % (rel, ROW_MARK))
    if rel in UNWRAP:
        text, _ = unwrap(text, rel)
    text, dropped, kept = patch_css(text, rel)
    text, renamed = patch_classes(text, rel)
    want = EXPECTED[rel]
    if (dropped, kept, renamed) != (0, 0, 0) and (dropped, kept, renamed) != want:
        raise SystemExit(
            'E3: %s gave (drop %d, keep %d, rename %d), the survey says '
            '%s. Re-survey before writing anything.'
            % (rel, dropped, kept, renamed, want))
    if text == before:
        return (0, 0, 0)
    if not CHECK:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            CRLF[bak] = CRLF.get(path)      # a backup is a copy (lesson 46)
            write(bak, before)
        write(path, text)
    return (dropped, kept, renamed)


LATER = [
    # A CHECK THAT SAYS "I AM THE NEWEST ROUND" IS A SCHEDULED FAILURE.
    # test_purple asserted ROUNDS[-1] == its own suffix. E3 falsified it
    # by existing, which every following round would also have done. It
    # was green on the laptop only because E3 is not there yet - so this
    # would have failed the gate the moment E3 landed, for no reason.
    # Order is the real property: as_left_by() walks ROUNDS forwards, so
    # what matters is that a round sits AFTER its predecessor.
    ('test_purple.py',
     """ok(ROUNDS and ROUNDS[-1] == SUFFIX,
   '%s is the LAST round in ROUNDS' % SUFFIX, ROUNDS[-3:] if ROUNDS else '')""",
     """# LATER - Section E round E3, 25 Sep. Was ROUNDS[-1] == SUFFIX, which
# is true only until the next round is written. Order, not recency. [E3]
ok(SUFFIX in ROUNDS and '.bak_pershead' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_pershead'),
   'alv_rounds lists %s after .bak_pershead' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else '')"""),
    # test_banner_pages held .action-bar open by asserting that at least
    # 25 templates still used it - and it counted with
    # r'class="[^"]*\baction-bar\b', which is the SUBSTRING TRAP base's
    # own standards block warns about: \b matches a hyphen, so the count
    # included every mobile-action-bar. Its own comment called the number
    # "its own survey". It was 26; it is 19 now only because E3 removed
    # the seven real ones, and 19 was never a count of this component.
    #
    # It reads the files NOW, so E3 really does falsify it (lesson 40 -
    # run it first, which is how this was found). What replaces it counts
    # EXACT TOKENS and states what is actually there.
    ('test_banner_pages.py',
     """    check('  and the other .action-bar pages are untouched - a name base does '
          'not define, on a name-count that is its own survey',
          len(_ab) >= 25, '%d still use it' % len(_ab))""",
     """    # LATER - Section E round E3, 25 Sep. THE NAME IS GONE. Counted by
    # exact class token instead of by substring: NO template wears
    # action-bar any more - the seven that did now wear the house
    # container. What the old substring count was really seeing:
    #   16 x mobile-action-bar  - a different component, base defines it
    #    3 x a locally-named bar of their own:
    #         celebration_management  contact-action-bar-mobile,
    #                                 event-action-bar-mobile
    #         preview_imported_recipe preview-action-bar
    #         view_recipe             recipe-action-bar
    # Those four names are the same problem under four more names, and
    # they are a round of their own. Named here so they cannot grow back
    # quietly. [E3]
    _tok = lambda t, w: any(
        w in m.group(1).split()
        for m in re.finditer(r'class="([^"]*)"', t))
    _texts = {n: markup_of(read(os.path.join(T, n))) for n in _all}
    _exact = sorted(n for n in _all if _tok(_texts[n], 'action-bar'))
    _mob = sorted(n for n in _all if _tok(_texts[n], 'mobile-action-bar'))
    check('  NO template wears action-bar any more - E3 moved all seven '
          'onto the house container', not _exact, ', '.join(_exact[:5]))
    check('  and the 16 mobile-action-bar pages are untouched - a '
          'different component, which base does define',
          len(_mob) >= 14, '%d wear it' % len(_mob))""",
     ),
    ('alv_rounds.py',
     "    '.bak_purple',\n]",
     "    '.bak_purple',\n    '.bak_actionbar',\n]"),
    ('Push-PendingChanges.ps1',
     "    'test_purple.py'",
     "    'test_purple.py'\n    'test_action_bar.py'"),
]


def patch_later():
    done = 0
    for name, old, new in LATER:
        path = os.path.join(HERE, name)
        text = read(path)
        if new in text:          # already-applied is the NEW text alone
            continue             # (lesson 47 - an anchor can prefix it)
        if text.count(old) != 1:
            raise SystemExit('E3/LATER: anchor matched %d times in %s'
                             % (text.count(old), name))
        if not CHECK:
            bak = path + SUFFIX
            if not os.path.exists(bak):
                CRLF[bak] = CRLF.get(path)
                write(bak, text)
            write(path, text.replace(old, new))
        done += 1
    return done


def main():
    print('=' * 70)
    print('SECTION E, ROUND E3 - THE ACTION BAR JOINS THE HOUSE - %s'
          % ('CHECK ONLY' if CHECK else 'APPLYING'))
    print('=' * 70)
    td = tk = tr = files = 0
    for rel in sorted(EXPECTED):
        d, k, r = patch(rel)
        if d or k or r:
            files += 1
            print('  %-40s drop %2d  keep %2d  rename %d' % (rel, d, k, r))
        else:
            print('  %-40s already applied' % rel)
        td += d
        tk += k
        tr += r
    later = patch_later()
    print('-' * 70)
    print('  %d rule(s) deleted, %d re-scoped, %d class attribute(s) '
          'renamed,\n  across %d file(s); %d LATER edit(s). base is '
          'unchanged.' % (td, tk, tr, files, later))
    print()
    print('  LEAVE, with the reason:')
    for (rel, what), why in sorted(LEAVE.items()):
        print('    %s  %s' % (rel, what))
        for line in re.findall(r'.{1,62}(?:\s|$)', why):
            if line.strip():
                print('        %s' % line.strip())
    print('=' * 70)


if __name__ == '__main__':
    main()
