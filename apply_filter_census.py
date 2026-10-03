# -*- coding: utf-8 -*-
"""CN-1 - THE FILTER CENSUS GETS ONE HOME

Outstanding item 4, logged 1 October:

    Five suites each keep their own count of pages carrying the house
    filter, and none knows about the others.

It came due today. FL-1 and UC-2 took the tree from fifteen filtered
pages to eighteen, and four suites that each type "15" went red at once.
Demetri, 3 Oct: consolidate it properly.

==========================================================================
THE WORK IS MOSTLY ALREADY DONE, IN THE WRONG PLACE
==========================================================================
test_filters_in_rc.py already carries _house_pages(), which derives the
list from the tree, and its own note already says what should happen:

    "One source of truth, five claims checked against it ... outstanding
     item 4 is about where the NUMBER lives, not about loosening any of
     them."

So this round does not invent a census. It MOVES the one that exists into
alv_tree, where crs_pages() and crs_outstanding() already live, and has
the four suites ask for it instead of typing a number.

==========================================================================
AND test_filters_in_rc's JOB CHANGES, WHICH IS THE POINT
==========================================================================
Today it reads each suite's source, pulls the digit out with a regex, and
checks the four digits agree with the tree. That is a cross-check between
four independent copies - useful exactly as long as the copies exist.

Once nobody types the number, that check has nothing to compare. So it
becomes the opposite claim, and a stronger one: NO SUITE STATES THE
NUMBER AT ALL. A digit reappearing in any of them is the defect, and the
suite says so by name.

The comparisons themselves are untouched. test_filters_in_rc's note is
right that item 4 is about where the number lives; what each suite
asserts ABOUT those pages is what caught IB-1 half-done, and none of it
is loosened here.

==========================================================================
WHAT IT IS NOT
==========================================================================
It is not a change to any page. No template is touched. The only files
that move are alv_tree.py and four suites.

Backups: .bak_filtercensus. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_filtercensus'
ROOT = os.getcwd()
CRLF = {}

TREE = os.path.join(ROOT, 'alv_tree.py')
ONCLOSE = os.path.join(ROOT, 'test_filter_on_close.py')
CHIPS = os.path.join(ROOT, 'test_recipe_chips.py')
RFILTER = os.path.join(ROOT, 'test_recipe_filter.py')
INRC = os.path.join(ROOT, 'test_filters_in_rc.py')


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
            raise SystemExit('CN1: %s is not a byte copy' % bak)


def swap(path, text, old, new, what):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('CN1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('CN-1 - THE FILTER CENSUS GETS ONE HOME%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 1. alv_tree LEARNS THE CENSUS.
# ==========================================================================
t, raw = read(TREE)

if 'house_filter_pages' in t:
    print('  alv_tree.py                already owns the census')
else:
    t = swap(TREE, t, '''def rel(path, base=None):
    """A stable, printable label for a template.''',
             '''def house_filter_pages(base=None):
    """Every page carrying the house filter: a Filter button AND the panel.

    OUTSTANDING ITEM 4, CLOSED - CN-1, 3 Oct 2026. Four suites each typed
    this number. FL-1 and UC-2 took the tree from fifteen filtered pages
    to eighteen and all four went red at once, which is the third time
    this list has moved and the first time anyone has had to change four
    files to record it.

    The function itself is lifted unchanged from test_filters_in_rc.py,
    which has derived it correctly since 2 Oct while the suites beside it
    went on typing a digit. Its own note said where this belonged:
    "outstanding item 4 is about where the NUMBER lives, not about
    loosening any of them."

    MARKUP ONLY. A page NAMING .alv-filter in a comment or a stylesheet
    does not carry one - a gate reads code, not the record of code - so
    <style>, <script> and HTML comments come out before looking. base is
    excluded: it DEFINES the control and wears none.
    """
    out = []
    for p in templates(base):
        if os.path.basename(p) == 'base.html':
            continue
        with open(p, encoding='utf-8', errors='replace') as fh:
            s = fh.read()
        s = re.sub(r'<style\\b.*?</style>', '', s, flags=re.S)
        s = re.sub(r'<script\\b.*?</script>', '', s, flags=re.S)
        s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
        if 'action-filter' in s and 'alv-filter' in s:
            out.append(rel(p, base))
    return sorted(out)


def rel(path, base=None):
    """A stable, printable label for a template.''',
             'the census function')

    if 'import re' not in t.split('\n\n')[0] and '\nimport re' not in t:
        t = swap(TREE, t, 'import os\n', 'import os\nimport re\n',
                 'the re import')

    if not CHECK:
        back_up(TREE, raw)
        write(TREE, t)
    print('  alv_tree.py                house_filter_pages() lives here now')

# ==========================================================================
# 2. THE THREE SUITES STOP TYPING THE NUMBER.
# ==========================================================================
NOTE = ('    # THE NUMBER IS NOT TYPED HERE ANY MORE - CN-1, 3 Oct 2026.\n'
        '    # alv_tree.house_filter_pages() derives it from the tree, so a\n'
        '    # page gaining a filter costs nothing instead of turning four\n'
        '    # suites red. Outstanding item 4.\n')

for path, old, new, what in (
    (ONCLOSE,
     "ok(len(auto) + len(manual) == 15, 'fifteen pages carry the house filter',",
     "ok(len(auto) + len(manual) == len(alv_tree.house_filter_pages()),\n"
     "   'every page carrying the house filter is accounted for',",
     'the on-close count'),
    (CHIPS,
     "ok(len(house) == 15, 'fifteen pages wear the house filter', len(house))",
     "ok(len(house) == len(alv_tree.house_filter_pages()),\n"
     "   'every page wearing the house filter is accounted for', len(house))",
     'the chips count'),
    (RFILTER,
     "ok(len(house) == 15, 'fifteen pages have one, all the same', len(house))",
     "ok(len(house) == len(alv_tree.house_filter_pages()),\n"
     "   'every page with one has it the same way', len(house))",
     'the recipe-filter count'),
):
    t, raw = read(path)
    name = os.path.basename(path)
    if 'house_filter_pages' in t:
        print('  %-26s already asks the tree' % name)
        continue
    t = swap(path, t, old, new, what)
    # IMPORTED INSIDE A try, NOT AT THE MARGIN. All three wrap the import
    # so a missing alv_tree fails with a sentence instead of a traceback,
    # which means it is indented - and a check anchored on a line
    # beginning 'import alv_tree' found none of them.
    if not re.search(r'(?m)^\s*import alv_tree\b', t):
        raise SystemExit('CN1: %s does not import alv_tree' % name)
    if not CHECK:
        back_up(path, raw)
        write(path, t)
    print('  %-26s asks the tree instead' % name)

# ==========================================================================
# 3. test_filters_in_rc FLIPS ITS CLAIM.
# ==========================================================================
t, raw = read(INRC)

if 'types the number' in t:
    print('  test_filters_in_rc.py      already checks that nobody types it')
else:
    t = swap(INRC, t, '''def _house_pages():
    """Pages carrying the house filter: a Filter button AND the panel.
    Markup only - a page NAMING .alv-filter in a comment or a stylesheet
    does not carry one, and a gate reads code, not the record of code."""
    out = []
    for p in alv_tree.templates():
        if os.path.basename(p) == 'base.html':
            continue
        t = read(p)
        t = re.sub(r'<style\\b.*?</style>', '', t, flags=re.S)
        t = re.sub(r'<script\\b.*?</script>', '', t, flags=re.S)
        t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
        if 'action-filter' in t and 'alv-filter' in t:
            out.append(alv_tree.rel(p))
    return sorted(out)


_HOUSE = _house_pages()''',
             '''# THIS FUNCTION MOVED - CN-1, 3 Oct 2026. It now lives in alv_tree as
# house_filter_pages(), which is where the note two paragraphs up said it
# belonged: "outstanding item 4 is about where the NUMBER lives". The
# body is unchanged; only its address is.
_HOUSE = alv_tree.house_filter_pages()''',
             'the local census')

    t = swap(INRC, t, '''_CLAIMS = {
    'test_filter_on_close.py':
        r'ok\\(len\\(auto\\) \\+ len\\(manual\\) == (\\d+)',
    'test_recipe_chips.py': r'ok\\(len\\(house\\) == (\\d+)',
    'test_recipe_filter.py': r'ok\\(len\\(house\\) == (\\d+)',
}
ok(bool(_HOUSE), 'the tree carries the house filter on %d page(s)'
   % len(_HOUSE))
for who, pat in sorted(_CLAIMS.items()):
    src = re.sub(r'(?m)#.*$', '', read(os.path.join(ROOT, who)))
    found = [int(x) for x in re.findall(pat, src)]
    if not ok(bool(found), '%-26s states a page count' % who):
        continue
    ok(all(n == len(_HOUSE) for n in found),
       '%-26s says %s, the tree says %d'
       % (who, '/'.join(str(n) for n in found), len(_HOUSE)))''',
             '''# AND THE CLAIM IS NOW THE OPPOSITE ONE - CN-1, 3 Oct 2026.
#
# This used to pull the digit out of each suite and check the four agreed
# with the tree. That was the right check for as long as four independent
# copies existed. Now that none of them types the number, there is
# nothing to compare - so the claim becomes the stronger one: NO SUITE
# STATES IT AT ALL, and a digit reappearing in any of them is the defect.
#
# The comparisons each suite makes ABOUT those pages are untouched. Those
# are what caught IB-1 half-done; item 4 was only ever about where the
# number lived.
_CLAIMS = {
    'test_filter_on_close.py':
        r'ok\\(len\\(auto\\) \\+ len\\(manual\\) == (\\d+)',
    'test_recipe_chips.py': r'ok\\(len\\(house\\) == (\\d+)',
    'test_recipe_filter.py': r'ok\\(len\\(house\\) == (\\d+)',
}
ok(bool(_HOUSE), 'the tree carries the house filter on %d page(s)'
   % len(_HOUSE))
for who, pat in sorted(_CLAIMS.items()):
    src = re.sub(r'(?m)#.*$', '', read(os.path.join(ROOT, who)))
    typed = re.findall(pat, src)
    ok(not typed, '%-26s types the number nowhere' % who,
       'found %s' % typed)
    ok('house_filter_pages' in src,
       '%-26s asks alv_tree for it instead' % who)''',
             'the claims block')

    if not CHECK:
        back_up(INRC, raw)
        write(INRC, t)
    print('  test_filters_in_rc.py      checks that nobody types it')


# ==========================================================================
# 4. TWO MORE THINGS THE CENSUS MOVING EXPOSED.
# ==========================================================================
# Both are the same shape as the counts above: an instrument that was
# right for as long as the set did not change.

t, raw = read(CHIPS)
if 'len(rows) == 15' not in t:
    print('  test_recipe_chips.py       its second count already asks the '
          'tree')
else:
    # THE SUITE COUNTS TWICE. The first count is the pages wearing the
    # filter; the second is the pages that put their chips on base's row,
    # and its own note says "both numbers move together". Only the first
    # was converted above.
    # THE ANCHOR CARRIES AN ESCAPED APOSTROPHE - base\'s - and writing
    # that through a heredoc into a patcher into a triple-quoted string
    # lost the backslash twice. Built with chr(92) so no layer can eat it.
    BS = chr(92)
    OLD_ROWS = ("ok(len(rows) == 15,\n"
                "   'and all fifteen put their chips on base" + BS + "'s row"
                " - no page keeps its own',")
    NEW_ROWS = ("ok(len(rows) == len(alv_tree.house_filter_pages()),\n"
                "   'and every one of them puts its chips on base" + BS + "'s"
                " row - no page keeps its own',")
    t = swap(CHIPS, t, OLD_ROWS, NEW_ROWS, 'the chip-row count')
    if not CHECK:
        back_up(CHIPS, raw)
        write(CHIPS, t)
    print('  test_recipe_chips.py       its chip-row count asks the tree too')

t, raw = read(ONCLOSE)
if 'def _has_apply_button' in t:
    print('  test_filter_on_close.py    already looks for a BUTTON')
else:
    # AN APPLY BUTTON IS A BUTTON, NOT THE WORD "APPLY".
    #
    # The test was `>\s*(?:<i></i>\s*)?Apply\b` - any text beginning
    # "Apply" after any tag. It was correct for two days and then
    # unit_conversions_management joined the census, and that page has a
    # LABEL in its Add Conversion modal reading "Apply this conversion
    # to:". The suite reported a page waiting for an Apply button that
    # has no Apply button at all.
    #
    # Twenty-fourth time this week that an instrument was asked for a
    # substring when the thing meant was a construct - and this one only
    # became wrong because the set it ran over grew.
    t = swap(ONCLOSE, t, r"""    if re.search(r'>\s*(?:<i[^>]*>\s*</i>\s*)?Apply\b', nocom(t)):""",
             """    if _has_apply_button(nocom(t)):""",
             'the apply test')

    t = swap(ONCLOSE, t, """auto, manual = [], []""",
             """def _has_apply_button(src):
    \"\"\"A control the reader presses to apply the filter.

    NOT THE WORD "APPLY" ANYWHERE. The first form of this test matched
    any text beginning "Apply" after any tag, and when
    unit_conversions_management joined the census it matched a LABEL in
    that page's Add Conversion modal - "Apply this conversion to:" - and
    reported a page waiting for a button it does not have.

    A button, a submit input, or a link styled as one. The label has to
    BE Apply, not merely begin with it, so "Apply this conversion to:"
    is not one and "Apply Filters" is.\"\"\"
    for m in re.finditer(r'<button[^>]*>(.*?)</button>', src, re.S):
        txt = re.sub(r'<[^>]+>', ' ', m.group(1))
        if re.match(r'^\s*Apply(\s+Filters?)?\s*$', txt, re.I):
            return True
    for m in re.finditer(r'<input[^>]*>', src):
        if re.search(r'type="submit"', m.group(0)) and re.search(
                r'value="\s*Apply(\s+Filters?)?\s*"', m.group(0), re.I):
            return True
    return False


auto, manual = [], []""",
             'the apply helper')

    if not CHECK:
        back_up(ONCLOSE, raw)
        write(ONCLOSE, t)
    print('  test_filter_on_close.py    looks for a BUTTON, not the word')

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
import importlib

for p in (TREE, ONCLOSE, CHIPS, RFILTER, INRC):
    ast.parse(read(p)[0])
print('  all five files parse')

sys.path.insert(0, ROOT)
import alv_tree
importlib.reload(alv_tree)

HOUSE = alv_tree.house_filter_pages()
if len(HOUSE) < 10:
    raise SystemExit('CN1: the census found only %d pages - it is not '
                     'reading the tree' % len(HOUSE))
print('  the census finds %d pages' % len(HOUSE))

# 1. THE FOUR RECIPES PANELS ARE IN IT. They are the reason it moved.
for want in ('ingredient_base_units_management.html',
             'categories_management.html',
             'measurement_units_management.html',
             'unit_conversions_management.html'):
    if want not in HOUSE:
        raise SystemExit('CN1: %s is not in the census, and this bundle '
                         'just gave it a filter' % want)
print('  including all four Recipes panels, which is why it moved')

# 2. base IS NOT. It defines the control and wears none.
if any('base.html' in p for p in HOUSE):
    raise SystemExit('CN1: base is in the census')

# 3. AND A PAGE THAT ONLY NAMES THE CLASS IS NOT EITHER. The census reads
#    markup; a gate reads code, not the record of code.
named = []
for p in alv_tree.templates():
    rel = alv_tree.rel(p)
    if rel in HOUSE:
        continue
    with open(p, encoding='utf-8', errors='replace') as fh:
        s = fh.read()
    if 'action-filter' in s and 'alv-filter' in s:
        named.append(rel)
print('  %d page(s) name the class without wearing it, and are excluded'
      % len(named))

# 4. NOBODY TYPES THE NUMBER.
for who, pat in (('test_filter_on_close.py',
                  r'len\(auto\) \+ len\(manual\) == (\d+)'),
                 ('test_recipe_chips.py', r'ok\(len\(house\) == (\d+)'),
                 ('test_recipe_filter.py', r'ok\(len\(house\) == (\d+)')):
    src = re.sub(r'(?m)#.*$', '', read(os.path.join(ROOT, who))[0])
    if re.findall(pat, src):
        raise SystemExit('CN1: %s still types the number' % who)
    if 'house_filter_pages' not in src:
        raise SystemExit('CN1: %s does not ask the tree' % who)
print('  none of the three types it; all three ask the tree')

# 5. THE CONTROL. The old function and the new one must agree, or this
#    round has quietly changed which pages count while claiming only to
#    have moved the code.
def old_census():
    out = []
    for p in alv_tree.templates():
        if os.path.basename(p) == 'base.html':
            continue
        with open(p, encoding='utf-8', errors='replace') as fh:
            s = fh.read()
        s = re.sub(r'<style\b.*?</style>', '', s, flags=re.S)
        s = re.sub(r'<script\b.*?</script>', '', s, flags=re.S)
        s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
        if 'action-filter' in s and 'alv-filter' in s:
            out.append(alv_tree.rel(p))
    return sorted(out)


if old_census() != HOUSE:
    raise SystemExit('CN1: the moved census answers differently:\n   only '
                     'old: %s\n   only new: %s'
                     % (sorted(set(old_census()) - set(HOUSE)),
                        sorted(set(HOUSE) - set(old_census()))))
print('  CONTROL: the moved census answers exactly as the one it replaced')

# 6. AND THE FOUR SUITES RUN.
for who in ('test_filter_on_close.py', 'test_recipe_chips.py',
            'test_recipe_filter.py', 'test_filters_in_rc.py'):
    r = subprocess.run([sys.executable, who], capture_output=True, text=True,
                       cwd=ROOT, timeout=1800)
    tail = [ln for ln in r.stdout.split('\n') if 'passed' in ln]
    mark = 'ok  ' if r.returncode == 0 else 'FAIL'
    print('  %s %-26s %s' % (mark, who, tail[-1].strip() if tail else ''))
    if r.returncode != 0:
        bad = [ln for ln in r.stdout.split('\n') if 'FAIL' in ln][:4]
        print('       %s' % '\n       '.join(bad))

# 7. THE APPLY HELPER, ON A FIXTURE. The label that broke it, and the
#    button it is actually looking for.
_oc = read(ONCLOSE)[0]
_ns = {'re': re}
exec(_oc[_oc.index('def _has_apply_button'):_oc.index('auto, manual = [], []')],
     _ns)
_apply = _ns['_has_apply_button']
for src, want, why in (
    ('<label><i class="fas fa-tag"></i> Apply this conversion to:</label>',
     False, 'a LABEL beginning "Apply" is not an Apply button'),
    ('<button class="btn">Apply</button>', True, 'a button reading Apply is'),
    ('<button class="btn"><i class="fas fa-check"></i> Apply Filters</button>',
     True, 'and so is one reading Apply Filters'),
    ('<input type="submit" value="Apply">', True, 'and a submit input'),
    ('<button>Apply the discount to every line</button>', False,
     'a button whose label merely BEGINS with Apply is not one'),
):
    got = _apply(src)
    if got != want:
        raise SystemExit('CN1: the apply helper said %s for %r - %s'
                         % (got, src[:50], why))
    print('    %-5s %s' % (str(want), why))
print('  CONTROL: the helper separates the label from the button')

print('-' * 74)
print('  Item 4 was logged on 1 October. It took three more filtered')
print('  pages and four red suites to come due, and the function that')
print('  fixes it had been sitting in one of those four since 2 October.')
print('=' * 74)
