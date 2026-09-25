# -*- coding: utf-8 -*-
"""apply_purple.py - Section E round E2, 25 Sep 2026.

THE IMPORTED PURPLE PALETTE GOES. The Personal side was built on a
palette that came in with a template pack - #667eea, #764ba2, #6f42c1 and
their relatives - and it spread to four Property templates too, including
customer_invoice_form.html, the one the house standard points at.

WHY THIS IS AN ACCESSIBILITY ROUND, WHICH THE SURVEY FIRST DENIED.
The survey measured the PURPLES and found them all comfortable: white on
#6f42c1 is 6.51, on #764ba2 6.37, on #7c3aed 5.70. It concluded that E2
was cosmetic. It had not measured #667eea, the BLUE half of the same
palette and the most-used member of it - 39 standalone uses across 11
templates, as link text, icon colour, tile fill and border.

    #667eea as TEXT on white   3.66   FAIL
    white TEXT on #667eea      3.66   FAIL
    --alv-accent      #0e7c8b  4.91   PASS
    --alv-accent-ink  #0a5e6a  7.44   PASS

D9 had already written that 3.66 into base.html three rounds ago, when it
flattened the five avatars - and fixed only the avatars, because avatars
were the round. The number sat in our own source the whole time.

Lesson 20 - a written finding is a measurement too - on the survey's own
author. It is recorded rather than tidied away.

THE MAPPING follows the house convention, verified in base.html and
customer_invoice_form.html: --alv-accent fills and borders, --alv-accent-ink
inks text, --alv-accent-soft backs a tag.

    linear-gradient(135deg, #667eea 0%, #764ba2 100%)  ->  var(--alv-accent)
    linear-gradient(135deg, #6f42c1 0%, #5a32a3 100%)  ->  var(--alv-accent)
    #667eea #6f42c1 #7c3aed  as fill or border         ->  var(--alv-accent)
    #667eea #6f42c1          as color:                 ->  var(--alv-accent-ink)
    #5a32a3 #5e37a6 #563098 #3d2466 #7b1fa2 #6a1b9a    ->  var(--alv-accent-ink)
    #f3e5f5 #f3eefb                                    ->  var(--alv-accent-soft)
    rgba(124, 58, 237, .12)     -> color-mix(in srgb, var(--alv-accent) 12%, transparent)

THE GRADIENTS GO FLAT, not re-hued. Thirteen copies of one gradient is
thirteen copies of one decision, and D9 gave the avatar the same answer.

AN EARLIER DRAFT OF THIS PARAGRAPH SAID "no page header anywhere in the
system is painted with a gradient". THAT WAS FALSE, and test_finance_headings
caught it by failing: its floor of eight gradient banners dropped to six
when this round flattened the purple ones. SEVEN REMAIN, in the green and
amber of the same imported pack, and six of them fail their own white text:

    household_member_management.html      .hm-header    3.13  FAIL
    ingredient_base_units_management.html .page-header  2.13  FAIL
    ingredient_base_units_management.html .nm-header    2.13  FAIL
    map_ingredients_nutrition.html        .page-header  2.13  FAIL
    meal_plan_shopping_list.html          .page-header  2.13  FAIL
    unit_conversions_wizard.html          .page-header  1.63  FAIL
    categories_management.html            .page-header  4.91  passes

They are NOT purple, and the agreed scope of this round is the purple. So
they stay, named here and asserted by name in test_finance_headings, and
they are the whole content of a round of their own. A survey's floor is
worth more than its ceiling: this one turned a claim into six numbers.

A MENTION IS NOT A USE (lesson 34). base.html carries #667eea inside D9's
own comment explaining the avatar fix. Comments are blanked before any
site is found, so base.html is not edited by this round at all.

THIS ROUND DELETES NOTHING (lesson 43) - with one exception that is a
COLLAPSE, not a deletion, and is named below.
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
SUFFIX = '.bak_purple'
CHECK = '--check' in sys.argv

ACCENT = 'var(--alv-accent)'
INK = 'var(--alv-accent-ink)'
SOFT = 'var(--alv-accent-soft)'
ONACC = 'var(--alv-on-accent)'
MIX12 = 'color-mix(in srgb, var(--alv-accent) 12%, transparent)'

# Per-file count of literal/gradient sites. The survey knows the number,
# so the patcher asserts it - lesson 35, where a regex that matched a
# third of the files looked exactly like one that worked.
EXPECTED = {
    'celebration_calendar.html': 6,
    'celebration_dashboard.html': 6,
    'celebration_management.html': 7,
    'create_meal_plan.html': 5,
    'customer_invoice_form.html': 4,
    'home.html': 4,
    'meal_plan_calendar.html': 18,
    'meal_plans.html': 3,
    'measurement_units_management.html': 3,
    'preview_imported_recipe.html': 2,
    'recipe_management.html': 5,
    'unit_conversions_management.html': 4,
    'view_meal_plan.html': 8,
    'view_recipe.html': 4,
    'finance/financial_indicators.html': 4,
}

# Named, with the reason, so an exception cannot become an escape hatch.
LEAVE = {
    ('base.html', '#4a3aa7'):
        '--alv-series-6, a chart series token from D5. Series colours are '
        'deliberately distinct hues and this one is doing its job.',
    ('base.html', '--alv-tag-plum'):
        "the HOUSE's own plum tag component, already tokenised, and its "
        'ink measures 6.41 on its own soft background.',
    ('base.html', '#667eea'):
        "inside D9's comment explaining the avatar fix. A mention is not "
        'a use (lesson 34) - blanked before any site is found.',
    ('act_expense.html', '#4a3aa7'):
        'SERIES_FALLBACK - the documented fallback array anTok() reads '
        'through. Not an escaped literal; D5 built it that way.',
    ('finance/financial_indicators.html', '#4a3aa7'):
        'the same SERIES_FALLBACK array. [D5]',
    ('finance/financial_indicators.html', '#6f42c1'):
        "the valueIncrease metric colour, one of SEVEN that identify the "
        'indicators apart. Making it the accent would collide with '
        "yieldPct, which is already #0e7c8b. Three of those seven fail "
        'contrast as text (#28a745 3.13, #ffc107 1.63, #20c997 2.13) and '
        'the set needs its own round - see claude/e2_purple_survey.md.',
}

CSS_COMMENT = re.compile(r'/\*.*?\*/', re.S)
HTML_COMMENT = re.compile(r'<!--.*?-->', re.S)

GRAD_HERO = re.compile(
    r'linear-gradient\(135deg,\s*#667eea\s*0%,\s*#764ba2\s*100%\)', re.I)
GRAD_UNIT = re.compile(
    r'linear-gradient\(135deg,\s*#6f42c1\s*0%,\s*#5a32a3\s*100%\)', re.I)
LITERAL = re.compile(
    r'#(?:667eea|764ba2|6f42c1|5a32a3|5e37a6|563098|7c3aed|7b1fa2|6a1b9a'
    r'|f3e5f5|f3eefb|3d2466)\b'
    r'|rgba\(\s*124,\s*58,\s*237[^)]*\)', re.I)
PROPERTY = re.compile(r'([a-zA-Z-]+)\s*:\s*[^;:{}]*$')

ALWAYS_INK = {'#5a32a3', '#5e37a6', '#563098', '#3d2466',
              '#7b1fa2', '#6a1b9a'}
ALWAYS_SOFT = {'#f3e5f5', '#f3eefb'}

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
    """The text with every comment turned to spaces, SAME LENGTH.

    Same length is the point: sites are found in the blanked copy and
    applied to the real one at identical offsets, so a literal that lives
    only in prose is never repainted. Lesson 34, which bit three times in
    one day before it was written down."""
    def spaces(m):
        return re.sub(r'[^\n]', ' ', m.group(0))
    return HTML_COMMENT.sub(spaces, CSS_COMMENT.sub(spaces, text))


def target_for(line, at, literal, rel):
    """Which token replaces this literal, from the CSS PROPERTY it sits
    on - not from a substring of the line. 'border-left-color' contains
    the word color and is not ink."""
    low = literal.lower()
    if low in ALWAYS_SOFT:
        return SOFT
    if low.startswith('rgba'):
        return MIX12
    if low in ALWAYS_INK:
        return INK
    m = PROPERTY.search(line[:at])
    prop = m.group(1).lower() if m else ''
    if prop == 'color':
        return INK
    if prop.startswith('--'):
        return INK if 'dark' in prop else ACCENT
    return ACCENT


def sites(text, rel):
    """(start, end, replacement) for every paint this round changes."""
    scan = blanked(text)
    spans = []
    for pat in (GRAD_HERO, GRAD_UNIT):
        for m in pat.finditer(scan):
            spans.append((m.start(), m.end(), ACCENT))
    taken = [(a, b) for a, b, _ in spans]

    starts = [0]
    for ch in scan:
        starts.append(starts[-1] + 1)
    line_start = 0
    for line in scan.split('\n'):
        for m in LITERAL.finditer(line):
            a = line_start + m.start()
            b = line_start + m.end()
            if any(a >= x and b <= y for x, y in taken):
                continue
            lit = m.group(0).lower()
            if (rel, lit) in LEAVE or (rel, '#' + lit.lstrip('#')) in LEAVE:
                continue
            spans.append((a, b, target_for(line, m.start(), lit, rel)))
        line_start += len(line) + 1
    return sorted(spans)


# The one COLLAPSE. .preview-header paints itself three ways on a Django
# branch: edit is a pink gradient whose worst stop measures 2.04 against
# its own white text, create is green at 2.13, and the third branch is
# ALREADY the house teal at 4.91. Two of three fail; the third is right.
# No other page in the system paints its header by mode, so the branch
# goes and the header takes the house paint like every other one.
#
# This is invisible to any scan that reads CSS RULES instead of the file:
# D10 swept the property side and E1 measured modal headers, and neither
# could see a colour that lives inside {% if %}.
PREVIEW_OLD = """.preview-header {
    {% if mode == 'edit' %}
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    {% elif mode == 'create' %}
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    {% else %}
    background: linear-gradient(135deg, #0e7c8b 0%, #0a5e6a 100%);
    {% endif %}
    color: white;"""
PREVIEW_NEW = """.preview-header {
    background: %s;
    color: %s;""" % (ACCENT, ONACC)


def patch(rel):
    path = os.path.join(ROOT, rel)
    text = read(path)
    before = text

    collapsed = 0
    if rel == 'preview_imported_recipe.html':
        hits = text.count(PREVIEW_OLD)
        if hits == 0 and PREVIEW_NEW in text:
            pass                      # already applied
        elif hits != 1:
            raise SystemExit(
                'E2: .preview-header anchor matched %d times in %s - it '
                'must match exactly once' % (hits, rel))
        else:
            text = text.replace(PREVIEW_OLD, PREVIEW_NEW)
            collapsed = 1

    spans = sites(text, rel)
    want = EXPECTED[rel]
    if spans and len(spans) != want:
        raise SystemExit(
            'E2: %s has %d sites, the survey says %d. Re-survey before '
            'writing anything.' % (rel, len(spans), want))
    for a, b, to in reversed(spans):
        text = text[:a] + to + text[b:]

    if text == before:
        return 0, 0
    if not CHECK:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            # A BACKUP IS A COPY (lesson 13), AND THAT INCLUDES ITS LINE
            # ENDINGS. write() restores CRLF from CRLF[path], which read()
            # set - but the backup is a DIFFERENT path, absent from that
            # map, so it defaulted to LF. Nine of this round's twenty-one
            # backups came out LF against CRLF originals, and every suite
            # still passed, because read() normalises newlines. It was the
            # delivery cmp against the laptop that saw it.
            CRLF[bak] = CRLF.get(path)
            write(bak, before)
        write(path, text)
    return len(spans), collapsed


# LATER - E1 shipped two comments saying "fifteen" where the measured
# figure is eleven. The patcher's own body documents the 15-vs-11
# discrepancy correctly; these two sentences did not get the correction.
# No check asserts either number, so nothing failed - which is exactly
# how a wrong number survives. Folded in here by the user's decision.
LATER = [
    # The round registers itself: its suffix on alv_rounds.ROUNDS so that
    # as_left_by() can place it, and its suite on the push gate. A suite
    # on disk and not on the gate fails test_standards_doc - "every suite
    # on disk is on the gate" - so these two are part of the round, not
    # an afterthought, and they travel with a backup like everything else.
    ('alv_rounds.py',
     "    '.bak_pershead',\n]",
     "    '.bak_pershead',\n    '.bak_purple',\n]"),
    ('Push-PendingChanges.ps1',
     "    'test_personal_heads.py'",
     "    'test_personal_heads.py'\n    'test_purple.py'"),
    # D9 deferred what was left of the purple to 2.K by asserting that at
    # least forty such rules REMAINED. E2 is 2.K arriving, so that line is
    # spent - and it reads the files NOW, not as D9 left them, so this
    # round really does falsify it (lesson 40: only a check that reads NOW
    # can be broken by a later round, and that one was run first to be
    # sure). What replaces it is strictly stronger: none remain at all.
    ('test_avatar.py',
     "ok(others >= 40,\n"
     "   'the %d purple rules that remain paint page headers, calendar '\n"
     "   'highlights, hover states and badges on the Personal side - a look, '\n"
     "   'not a component, and 2.K\\'s by agreement' % others, others)",
     "# LATER - Section E round E2, 25 Sep. 2.K ARRIVED. This held the\n"
     "# deferral by requiring that forty-odd purple rules still existed.\n"
     "# E2 took the imported palette out of the system, so the floor is\n"
     "# now a ceiling of zero: not one rule anywhere paints with #667eea\n"
     "# or #764ba2. The two literals that survive E2 are a mention inside\n"
     "# D9's own comment (stripped by nocomment above) and a metric colour\n"
     "# in financial_indicators - neither is a rule, and neither is here.\n"
     "ok(others == 0,\n"
     "   'not one rule anywhere still paints with the imported purple - '\n"
     "   'E2 took the palette out, and D9\\'s deferral to 2.K is spent',\n"
     "   others)"),
    # Its floor of eight was the count BEFORE this round flattened the
    # purple banners. Lowering a floor teaches nothing; the six that remain
    # are green and amber, they are named, and six of the seven rules on
    # them fail their own white text. A named set cannot quietly grow.
    ('test_finance_headings.py',
     "print('        %d template(s) still carry a coloured page banner - "
     "the purple '\n"
     "      'nine\\n        in Administration, and the Personal ones. Their "
     "modules '\n"
     "      'inherit this.' % len(_left))\n"
     "check('and the number is a floor, not a silence', len(_left) >= 8,",
     "# LATER - Section E round E2, 25 Sep. The floor was eight while the\n"
     "# purple banners were still there; E2 flattened those, and what is\n"
     "# left is the GREEN AND AMBER of the same imported pack, on six\n"
     "# templates. Six of their seven rules fail their own white text -\n"
     "# 3.13, 2.13 x4 and 1.63 - and they are a round of their own. Named,\n"
     "# because a floor lets a set grow back in silence.\n"
     "print('        %d template(s) still carry a gradient page banner - '\n"
     "      'green and amber,\\n        from the same imported pack the "
     "purple came from. Six of\\n        their seven rules fail their own "
     "white text. [E2]' % len(_left))\n"
     "_EXPECT_BANNERS = {\n"
     "    'categories_management.html',\n"
     "    'household_member_management.html',\n"
     "    'ingredient_base_units_management.html',\n"
     "    'map_ingredients_nutrition.html',\n"
     "    'meal_plan_shopping_list.html',\n"
     "    'unit_conversions_wizard.html',\n"
     "}\n"
     "check('and it is exactly the six named green/amber banners [E2]',\n"
     "      set(_left) == _EXPECT_BANNERS,"),
    ('test_modal_heads.py',
     'of its remaining headers to .alv-modal-head - fifteen of which were\n'
     '# failing their own white text',
     'of its remaining headers to .alv-modal-head - eleven of which were\n'
     '# failing their own white text (the class names suggested fifteen;\n'
     '# rendered it is eleven, and rendering is what counts)'),
    ('apply_personal_heads.py',
     'pop-up headers join the house, and fifteen contrast failures go '
     'with them.',
     'pop-up headers join the house, and eleven contrast failures go '
     'with them.'),
]


def patch_later():
    done = 0
    for name, old, new in LATER:
        path = os.path.join(HERE, name)
        text = read(path)
        # ALREADY-APPLIED IS DECIDED BY THE NEW TEXT ALONE. The first
        # version also required the old text to be gone, which is false
        # whenever an anchor is a PREFIX of its replacement - as the gate
        # line is: 'test_personal_heads.py' survives inside
        # 'test_personal_heads.py'\n'test_purple.py'. The patcher then
        # reported work left to do on an applied tree, and a second real
        # run would have registered the suite twice.
        if new in text:
            continue
        n = text.count(old)
        if n != 1:
            raise SystemExit(
                'E2/LATER: anchor matched %d times in %s - it must match '
                'exactly once' % (n, name))
        if not CHECK:
            bak = path + SUFFIX
            if not os.path.exists(bak):
                CRLF[bak] = CRLF.get(path)     # a backup is a copy
                write(bak, text)
            write(path, text.replace(old, new))
        done += 1
    return done


def main():
    print('=' * 70)
    print('SECTION E, ROUND E2 - THE IMPORTED PURPLE PALETTE - %s'
          % ('CHECK ONLY' if CHECK else 'APPLYING'))
    print('=' * 70)
    total = files = collapses = 0
    for rel in sorted(EXPECTED):
        n, c = patch(rel)
        total += n
        collapses += c
        if n or c:
            files += 1
            print('  %-38s %3d site(s)%s'
                  % (rel, n, '  + the .preview-header collapse' if c else ''))
        else:
            print('  %-38s already applied' % rel)
    later = patch_later()
    print('-' * 70)
    print('  %d site(s) across %d file(s); %d collapse; %d LATER edit(s)'
          % (total, files, collapses, later))
    print()
    print('  LEAVE, with the reason:')
    for (rel, lit), why in sorted(LEAVE.items()):
        print('    %s  %s' % (rel, lit))
        for line in re.findall(r'.{1,62}(?:\s|$)', why):
            print('        %s' % line.strip())
    print('=' * 70)


if __name__ == '__main__':
    main()
