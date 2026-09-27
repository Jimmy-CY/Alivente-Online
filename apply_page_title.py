# -*- coding: utf-8 -*-
"""apply_page_title.py - Section G round G1, 27 Sep 2026.

THE COLOURED BANNERS COME OFF. 16 of them, across 16 pages, with two more
held back for a reading of their own.

WHY THIS ROUND IS THE OPPOSITE OF WHAT I FIRST PROPOSED.
Asked why Personal did not look like the rest of the app, I proposed defining a
house page-head COMPONENT in base - one teal banner - and migrating every
Personal banner onto it. I rendered sixteen before and after and the result
looked like one coherent system. It was one coherent system the rest of the app
does not have. The correction came back as a question: we do not have coloured
banners anywhere else, can these not be standardised to the rest of the system,
like Properties?

Measured across every template that renders a content block:

    .page-title-h2, which base ALREADY DEFINES        66 pages
    <h2><center>, the same look via a dead element    22 pages
    a COLOURED BANNER                                 19 pages
    a bare h1/h2 with no standard at all              19 pages

base has owned the whole thing all along:

    .page-title-h2    { text-align:center; margin:.5rem 0 1rem; font-size:1.25rem }
    .page-subtitle-h4 { text-align:center; margin:.25rem 0 .75rem;
                        color:var(--alv-ink-soft); font-size:1rem }

So the banners are the outlier and they are REMOVED, not standardised. Lesson
20 in its purest form: a written finding is a measurement too. "There is no
house page header" was true of the BANNER and false of the page TITLE.

TWO CONVENTIONS, BOTH COUNTED BEFORE BEING FOLLOWED.
  - Casing:  87 house page titles are UPPERCASE, 1 is mixed only because it
             contains an ampersand entity, 0 are lower. So the titles are
             uppercased - in the markup, because .page-title-h2 sets no
             text-transform and PROPERTIES is literal text.
  - Icons:   0 of 88 house page titles carry one. Every banner heading does.
             They come off.

WHAT EACH PAGE GETS
    <h2 class="page-title-h2">TITLE</h2>
    <h4 class="page-subtitle-h4">subtitle</h4>        where there was a <p>
    <div class="page-action-buttons"> ... </div>      where the banner held
                                                      controls

FOUR PAGES KEEP THEIR CONTROLS BUT NOT THEIR PLACE. celebration_dashboard
(.header-actions), household_member_management (.hm-actions) and
meal_plan_calendar (.calendar-header-actions) hold buttons INSIDE the banner,
positioned absolutely or floated. They lift into .page-action-buttons, which is
where every other page in the app keeps them and which gives them 44px on a
phone.

THE CONDITIONAL HEADING IS CARRIED THROUGH, NOT FLATTENED.
preview_imported_recipe's <h1> is

    {% if mode == 'create' %}Create New Recipe{% elif ... %}...{% endif %}

and so is its subtitle. A prototype render of this round flattened all three
branches into one sentence - CREATE NEW RECIPE EDIT RECIPE REVIEW IMPORTED
RECIPE - which is lesson 52 exactly: stripping a conditional is not evaluating
it false. The uppercasing here walks TEXT NODES ONLY, leaving every {% %} and
{{ }} and every &entity; untouched.

THE INVENTORY WAS WRONG TWICE BEFORE IT WAS RIGHT, AND BOTH FAILURES ARE THE
HOUSE FAILURES.
  1. The first census matched class names as SUBSTRINGS, so .map-page-header
     counted as .page-header. That put map_view and property_detail on the
     list. Neither has a banner: both declare a plain flex layout row with no
     background at all. base's own standards block warns about exactly this -
     a word boundary fires on a hyphen (lesson 30).
  2. The rewrite walked the markup by hand and LOST ITS PLACE on a nested
     conditional, missing preview_imported_recipe, which does have one.

The list below comes from a real HTML parser: find each page's first heading,
walk its actual ancestors, ask whether any is painted. EIGHTEEN pages, eight
class names, eight of them gradients - and every one is Personal. The Property
side has no coloured banner anywhere, which is the whole reason these go.

TWO ARE HELD BACK, ON PURPOSE (lesson 43 - when in doubt a round deletes
nothing):
  - view_meal_plan's .page-header holds three stat chips and no subtitle and
    renders low on the page - shaped like a summary strip, not a banner.
  - view_recipe's .recipe-header-content is a rich recipe header, not a page
    banner in the same sense. Both want reading on their own.

WHAT THIS FIXES FOR FREE. Six of the seventeen banners are green or amber
gradients whose white text fails contrast - unit_conversions_wizard's amber at
1.63 is the lowest measured anywhere in the app, and household_member_
management's green is 3.13. Deleting the banner deletes the failure.
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
SUFFIX = '.bak_pagetitle'
CHECK = '--check' in sys.argv

TITLE_CLS = 'page-title-h2'
SUB_CLS = 'page-subtitle-h4'
BAR_CLS = 'page-action-buttons'

# (template, banner class, the container of controls to lift or None)
JOBS = [
    ('categories_management.html', 'page-header', None),
    ('celebration_calendar.html', 'calendar-header', None),
    ('celebration_dashboard.html', 'dashboard-header', 'header-actions'),
    ('celebration_management.html', 'celebration-header', None),
    ('create_meal_plan.html', 'page-header', None),
    ('household_member_management.html', 'hm-header', 'hm-actions'),
    ('import_recipe.html', 'import-header', None),
    ('ingredient_base_units_management.html', 'page-header', None),
    ('map_ingredients_nutrition.html', 'page-header', None),
    ('meal_plan_calendar.html', 'calendar-header', 'calendar-header-actions'),
    ('meal_plan_shopping_list.html', 'page-header', None),
    ('meal_plans.html', 'page-header', None),
    ('measurement_units_management.html', 'page-header', None),
    ('preview_imported_recipe.html', 'preview-header', None),
    ('unit_conversions_management.html', 'page-header', None),
    ('unit_conversions_wizard.html', 'page-header', None),
]

# CONTROLS DRESSED FOR A TEAL BANNER DO NOT WORK ON PAPER.
# Lifting the three control groups out and stopping there was measured and it
# is not good enough. celebration_dashboard and meal_plan_calendar survive it -
# both already carry .action-primary and .action-back, which base defines, so
# their local btn-light and btn-secondary are simply outranked. household_
# member_management does NOT: its entire button appearance came from a local
# dialect named for the banner it sat on - .hm-btn-white - and that dialect
# dies with the banner's CSS. Rendered, its three controls became bare GREEN
# TEXT LINKS with no button shape at all, and green text is 3.13 on white.
#
# So the lift carries the styling with it. The mapping is written out rather
# than inferred, and each string must match exactly once. Note the two
# identical class strings distinguished by their ELEMENT: the <button> is a
# Help action, the <a> is Back.
#
# This also discharges part of what was recorded as E5 - household_member_
# management's hm-btn-label Help dialect.
#
# THREE MORE CAME OUT OF THE RENDER, not out of reading the file:
#
#   * Help on .action-primary. Base paints .action-primary a FILLED TEAL
#     pill - the page's one main action. Inside the banner a local rule
#     overrode that to white-on-teal, so nobody could see what the class
#     said. Delete the rule and Help comes back as a primary. Counted the
#     house: 29 pages put Help on .action-secondary, 21 put it in the
#     overflow menu, and the only two on .action-primary are these two
#     Personal pages. Help is not a primary action anywhere in this app.
#   * celebration_dashboard's btn-light/btn-sm and its inline icon colours
#     were written for a teal ground. Properties' own control bar is
#     'btn action-secondary' and 'btn action-back' with no inline colour.
#   * meal_plan_calendar's .btn-header-disabled paints
#     rgba(255,255,255,.3) on rgba(255,255,255,.7) - readable ON TEAL,
#     and an EMPTY WHITE BOX once the teal is gone. Rendered, that is
#     exactly what it became. The house spells a disabled primary
#     'btn action-primary disabled-btn' (properties.html line 40).
NORMALISE = {
    'celebration_dashboard.html': [
        ('<button type="button" class="btn btn-light btn-sm action-primary"',
         '<button type="button" class="btn action-secondary"'),
        ('<i class="fas fa-question-circle" style="color:var(--alv-accent-ink);">'
         '</i> Help',
         '<i class="fas fa-question-circle"></i> Help'),
        ('class="btn btn-light btn-sm action-back"', 'class="btn action-back"'),
        ('<i class="fas fa-arrow-left" style="color:var(--alv-accent-ink);"></i>'
         '<span class="action-back-label" style="color:#495057;"> Back</span>',
         '<i class="fas fa-arrow-left"></i>'
         '<span class="action-back-label"> Back</span>'),
    ],
    'meal_plan_calendar.html': [
        ('<span class="btn btn-header-disabled action-primary"',
         '<span class="btn action-primary disabled-btn"'),
    ],
    'household_member_management.html': [
        ('<button type="button" class="hm-btn-white hm-btn-primary"',
         '<button type="button" class="btn action-primary"'),
        ('<button type="button" class="hm-btn-white hm-btn-icon"',
         '<button type="button" class="btn action-secondary"'),
        ('<a href="{% url \'personal_page\' %}" class="hm-btn-white hm-btn-icon"',
         '<a href="{% url \'personal_page\' %}" class="btn action-back"'),
        ('<i class="fas fa-plus"></i> <span class="hm-btn-label">Add Person</span>',
         '<i class="fas fa-plus"></i> Add Person'),
        ('<i class="fas fa-question-circle"></i> <span class="hm-btn-label">'
         'Help</span>',
         '<i class="fas fa-question-circle"></i> Help'),
        ('<i class="fas fa-arrow-left"></i> <span class="hm-btn-label">'
         'Back</span>',
         '<i class="fas fa-arrow-left"></i>'
         '<span class="action-back-label"> Back</span>'),
    ],
}
# The local dialect goes with the markup that wore it.
NORMALISE_CSS = {
    'household_member_management.html': ['hm-btn-white', 'hm-btn-primary',
                                         'hm-btn-icon', 'hm-btn-label'],
    'meal_plan_calendar.html': ['btn-header-disabled'],
}

# --------------------------------------------------------------------------
# WHAT THE BANNER HELD BESIDES A TITLE.
#
# The first form of this round read the banner's first <h> and its first <p>
# and THREW THE REST AWAY. Rendered, four pages lost real content and nobody
# reading the diff would have seen it, because what vanished was a Django
# tag, not a sentence:
#
#   household_member_management   the workspace badge
#   map_ingredients_nutrition     "Mapping ingredients for: <recipe>"
#   unit_conversions_wizard       "Setting conversions for: <recipe>"
#   meal_plan_shopping_list       the date range and the day count
#
# All four were painted for a TEAL ground - rgba(255,255,255,.2) pills with
# inherited white text - so carrying the markup across unchanged would have
# put white on white. Counted the house instead: 53 pages carry a
# .page-subtitle-h4 and every one of them carries EXACTLY ONE, and
# workspace_edit.html line 93 already spells a scoped one as
# "EDIT WORKSPACE - {{ workspace.name }}". So the context line folds into
# the subtitle, em dash and all, and its pill class goes with the banner.
#
# `drop` must match inside the banner exactly once. `add` is appended to the
# subtitle. The LOSS GATE below then proves nothing else went missing.
CARRY = {
    'household_member_management.html': {
        'drop': ('{% if workspace %}<span class="hm-badge">'
                 '<i class="fas fa-layer-group"></i> {{ workspace.name }}'
                 '</span>{% endif %}'),
        'add': '{% if workspace %} &mdash; {{ workspace.name }}{% endif %}',
        'css': ['hm-badge'],
    },
    'map_ingredients_nutrition.html': {
        'drop': ('{% if scoped_recipe %}\n'
                 '        <div class="recipe-scope-pill">\n'
                 '            <i class="fas fa-utensils"></i>\n'
                 '            Mapping ingredients for: '
                 '<strong>{{ scoped_recipe.recipe_name }}</strong>\n'
                 '        </div>\n'
                 '        {% endif %}'),
        'add': ('{% if scoped_recipe %} &mdash; mapping ingredients for '
                '<strong>{{ scoped_recipe.recipe_name }}</strong>{% endif %}'),
        'css': ['recipe-scope-pill'],
    },
    'unit_conversions_wizard.html': {
        'drop': ('{% if scoped_recipe %}\n'
                 '        <div class="recipe-scope-pill">\n'
                 '            <i class="fas fa-utensils"></i>\n'
                 '            Setting conversions for: '
                 '<strong>{{ scoped_recipe.recipe_name }}</strong>\n'
                 '        </div>\n'
                 '        {% endif %}'),
        'add': ('{% if scoped_recipe %} &mdash; setting conversions for '
                '<strong>{{ scoped_recipe.recipe_name }}</strong>{% endif %}'),
        'css': ['recipe-scope-pill'],
    },
    'meal_plan_shopping_list.html': {
        'drop': ('<div class="page-header-meta">\n'
                 '            <span>\n'
                 '                <i class="fas fa-calendar"></i>\n'
                 '                {{ meal_plan.start_date|date:"M d" }} - '
                 '{{ meal_plan.end_date|date:"M d, Y" }}\n'
                 '            </span>\n'
                 '            <span>\n'
                 '                <i class="fas fa-utensils"></i>\n'
                 '                {% if meal_plan.days.count %}'
                 '{{ meal_plan.days.count }}{% else %}0{% endif %} '
                 'day{{ meal_plan.days.count|pluralize }}\n'
                 '            </span>\n'
                 '        </div>'),
        'add': (' &mdash; {{ meal_plan.start_date|date:"M d" }} - '
                '{{ meal_plan.end_date|date:"M d, Y" }} &mdash; '
                '{% if meal_plan.days.count %}{{ meal_plan.days.count }}'
                '{% else %}0{% endif %} '
                'day{{ meal_plan.days.count|pluralize }}'),
        'css': ['page-header-meta'],
    },
}

# A BANNER WHOSE HEADING IS CHOSEN BY A TEMPLATE TAG. create_meal_plan wraps
# TWO <h1>/<p> pairs in an {% if %}, so "first heading, first paragraph" took
# the edit branch and dropped the create branch whole - the Create Meal Plan
# page would have shipped with no heading at all. (preview_imported_recipe
# survives the generic path because its conditional sits INSIDE one <h1>.)
# Written out, with the block it replaces pinned: edit the template and this
# round stops rather than flattening it.
CONDITIONAL = {
    'create_meal_plan.html': {
        'was': ('{% if edit_mode %}\n'
                '        <h1><i class="fas fa-edit"></i> Edit Meal Plan</h1>\n'
                '        <p>Update your meal plan details</p>\n'
                '        {% else %}\n'
                '        <h1><i class="fas fa-calendar-plus"></i> '
                'Create Meal Plan</h1>\n'
                '        <p>Plan your meals for the week</p>\n'
                '        {% endif %}'),
        # The house form for an Add/Edit screen, counted across 37 pages:
        # h2 is the MODULE (ACTUAL EXPENSES, PROPERTIES, REVENUE) and h4 is
        # the MODE LABEL in capitals (ADD EXPENSE, ADD NEW PROPERTY, EDIT
        # REVENUE), median three words. This page is one of those screens,
        # so it takes that shape rather than a sentence.
        'title': 'MEAL PLANS',
        'sub': ('{% if edit_mode %}EDIT MEAL PLAN'
                '{% else %}CREATE MEAL PLAN{% endif %}'),
    },
}

# --------------------------------------------------------------------------
# THE SUBTITLE IS NOT A DESCRIPTION. Counted: 38 pages in this tree carry a
# .page-subtitle-h4, and 37 of them are a SHORT MODE LABEL IN CAPITALS on an
# Add/Edit screen - ADD EXPENSE, EDIT REVENUE, ADD NEW PROPERTY - median
# three words. Every management screen in the house, Properties included,
# carries a title and NOTHING ELSE. The first form of this round put the old
# banner's descriptive sentence into the h4 on fourteen pages, and
# test_heading_standard - which states the rule as "an h4 shouts, an h5
# does not" - went red on all fourteen.
#
# So the sentences come off, and an h4 survives only where it carries DATA
# the banner was showing. workspace_edit.html line 93 is the house precedent
# for that shape: "EDIT WORKSPACE - {{ workspace.name }}".
#
# None  -> no subtitle at all, like Properties.
# a str -> emitted verbatim in place of the <h4> line, conditional and all.
SUBTITLE = {
    'categories_management.html': None,
    'celebration_calendar.html': None,
    'celebration_dashboard.html': None,
    'celebration_management.html': None,
    'create_meal_plan.html': 'KEEP',          # a mode label - see CONDITIONAL
    'household_member_management.html':
        '{% if workspace %}<h4 class="page-subtitle-h4">{{ workspace.name }}'
        '</h4>{% endif %}\n',
    'import_recipe.html': None,
    'ingredient_base_units_management.html': None,
    'map_ingredients_nutrition.html':
        '{% if scoped_recipe %}<h4 class="page-subtitle-h4">MAPPING '
        'INGREDIENTS FOR {{ scoped_recipe.recipe_name }}</h4>{% endif %}\n',
    'meal_plan_calendar.html': None,
    'meal_plan_shopping_list.html':
        '<h4 class="page-subtitle-h4">{{ meal_plan.plan_name }} &mdash; '
        '{{ meal_plan.start_date|date:"M d" }} - '
        '{{ meal_plan.end_date|date:"M d, Y" }} &mdash; '
        '{% if meal_plan.days.count %}{{ meal_plan.days.count }}'
        '{% else %}0{% endif %} day{{ meal_plan.days.count|pluralize }}'
        '</h4>\n',
    'meal_plans.html': None,
    'measurement_units_management.html': None,
    'preview_imported_recipe.html': None,
    'unit_conversions_management.html': None,
    'unit_conversions_wizard.html':
        '{% if scoped_recipe %}<h4 class="page-subtitle-h4">SETTING '
        'CONVERSIONS FOR {{ scoped_recipe.recipe_name }}</h4>{% endif %}\n',
}

# Held back - see the docstring. Asserted untouched by the suite.
HELD = {
    'view_meal_plan.html': 'page-header',
    'view_recipe.html': 'recipe-header-content',
}

HTML_C = re.compile(r'<!--.*?-->', re.S)
DJ_CB = re.compile(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', re.S | re.I)
DJ_C = re.compile(r'\{#.*?#\}', re.S)
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')
ICON = re.compile(r'<i\b[^>]*>\s*</i>\s*', re.I)

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


def _sp(m):
    return re.sub(r'[^\n]', ' ', m.group(0))


def blanked(text):
    """Markup comments to spaces, SAME LENGTH, on the raw text - so a banner
    that only appears inside a comment is never rewritten (lesson 34), and so
    offsets still index into `text`."""
    t = text
    for rx in (HTML_C, DJ_CB, DJ_C):
        t = rx.sub(_sp, t)
    if len(t) != len(text):
        raise SystemExit('G1: comment blanking changed length')
    return t


def div_end(text, start):
    """Index just past the </div> that closes the <div> opened at `start`."""
    i, d = text.index('>', start) + 1, 1
    while i < len(text) and d:
        n = re.compile(r'<div\b|</div\s*>', re.I).search(text, i)
        if not n:
            raise SystemExit('G1: unbalanced <div> from offset %d' % start)
        d += 1 if not n.group(0).startswith('</') else -1
        i = n.end()
    if d:
        raise SystemExit('G1: unbalanced <div> from offset %d' % start)
    return i


# TEXT NODES ONLY. Everything between < and >, every {% %} and {{ }}, and
# every &entity; is left exactly as it was - uppercasing &amp; would give
# &AMP; and uppercasing a Django tag would break it.
PROTECT = re.compile(r'<[^>]*>|\{%.*?%\}|\{\{.*?\}\}|&[#0-9A-Za-z]+;', re.S)


def upper_text(html):
    out, pos = [], 0
    for m in PROTECT.finditer(html):
        out.append(html[pos:m.start()].upper())
        out.append(m.group(0))
        pos = m.end()
    out.append(html[pos:].upper())
    return ''.join(out)


def drop_rules(css, names):
    """Every rule whose selector mentions one of `names`, gone."""
    out, pos, n = [], 0, 0
    for m in RULE.finditer(css):
        sel = ' '.join(m.group(1).split())
        if any(re.search(r'(?<![\w-])\.' + re.escape(x) + r'(?![\w-])', sel)
               for x in names):
            out.append(css[pos:m.start()])
            pos = m.end()
            n += 1
    out.append(css[pos:])
    return ''.join(out), n


def patch(rel, cls, lift):
    path = os.path.join(ROOT, rel)
    text = read(path)
    scan = blanked(text)

    hits = [m for m in re.finditer(
        r'<div[^>]*class="([^"]*)"[^>]*>', scan)
        if re.search(r'(?<![\w-])' + re.escape(cls) + r'(?![\w-])', m.group(1))]
    if not hits:
        if 'class="%s"' % TITLE_CLS in text:
            return None                     # already applied
        raise SystemExit('G1: %s - no <div> wears .%s' % (rel, cls))
    if len(hits) != 1:
        raise SystemExit('G1: %s - .%s is worn %d times, expected 1'
                         % (rel, cls, len(hits)))
    m = hits[0]
    end = div_end(scan, m.start())
    block = text[m.start():end]
    # A banner is not always one <div>. household_member_management wraps its
    # heading, subtitle and workspace badge in an inner <div> before the
    # actions group, so removing its banner removes THREE. The arithmetic
    # below is taken from the block itself rather than assumed.
    block_divs = len(re.findall(r'<div\b', blanked(block)))

    # --- the controls, if this banner holds any ---------------------------
    lifted = ''
    if lift:
        lb = blanked(block)
        mm = [x for x in re.finditer(r'<div[^>]*class="([^"]*)"[^>]*>', lb)
              if re.search(r'(?<![\w-])' + re.escape(lift) + r'(?![\w-])',
                           x.group(1))]
        if len(mm) != 1:
            raise SystemExit('G1: %s - .%s is worn %d times inside the banner'
                             % (rel, lift, len(mm)))
        e2 = div_end(lb, mm[0].start())
        inner = block[block.index('>', mm[0].start()) + 1:e2 - len('</div>')]
        inner = inner.strip()
        for a, b in NORMALISE.get(rel, []):
            if inner.count(a) != 1:
                raise SystemExit('G1: %s - normalise anchor matched %d times: '
                                 '%s' % (rel, inner.count(a), a[:60]))
            inner = inner.replace(a, b)
        lifted = '<div class="%s">%s</div>\n' % (BAR_CLS, inner)
        block = block[:mm[0].start()] + block[e2:]

    # --- what the banner held besides a title ------------------------------
    orig_block = block          # what the gate at the foot of this step reads
    # ANCHORS ARE WRITTEN WITH \n; THE FILE MAY NOT BE. Three of the five
    # files these anchors read are CRLF, and a CRLF file matched an LF anchor
    # zero times - the round stopped rather than doing the wrong thing, which
    # is what the exact-count check is for.
    eol = (lambda s: s.replace('\n', '\r\n')) if '\r\n' in block else (lambda s: s)

    carry = CARRY.get(rel)
    if carry:
        drop = eol(carry['drop'])
        if block.count(drop) != 1:
            raise SystemExit('G1: %s - carry anchor matched %d times'
                             % (rel, block.count(drop)))
        block = block.replace(drop, '')

    # --- title and subtitle ----------------------------------------------
    cond = CONDITIONAL.get(rel)
    if cond:
        was_ = eol(cond['was'])
        if block.count(was_) != 1:
            raise SystemExit('G1: %s - the conditional heading has changed '
                             '(anchor matched %d times)'
                             % (rel, block.count(was_)))
        title, sub = cond['title'], cond['sub']
        block = block.replace(was_, '')
    else:
        bb = blanked(block)
        h = re.search(r'<h([1-6])[^>]*>(.*?)</h\1\s*>', bb, re.S)
        if not h:
            raise SystemExit('G1: %s - the banner holds no heading' % rel)
        title = block[h.start(2):h.end(2)]
        title = ICON.sub('', title).strip()         # 0 of 88 house titles
        title = upper_text(title)                   # 87 of 88 are uppercase
        p = re.search(r'<p[^>]*>(.*?)</p\s*>', bb, re.S)
        sub = block[p.start(1):p.end(1)].strip() if p else ''
        block = (block[:h.start()] + block[h.end():]) if h else block

    # --- the subtitle, decided by the table, not by the old markup --------
    if rel not in SUBTITLE:
        raise SystemExit('G1: %s - no SUBTITLE decision recorded' % rel)
    want = SUBTITLE[rel]
    if want == 'KEEP':                      # the CONDITIONAL mode label
        h4 = '<h4 class="%s">%s</h4>\n' % (SUB_CLS, sub)
    elif want is None:                      # like Properties - title alone
        h4 = ''
    else:
        h4 = want

    new = '<h2 class="%s">%s</h2>\n' % (TITLE_CLS, title) + h4 + lifted

    # --- THE LOSS GATE ----------------------------------------------------
    # Every Django tag the banner held must still be somewhere in what
    # replaces it. Four pages lost one silently before this gate existed,
    # and a diff does not read as loss when what vanished is {{ x }}.
    #
    # A DESCRIPTIVE SENTENCE IS NOT DATA. The sentences deliberately come
    # off (see SUBTITLE), so the gate is about template tags only - and the
    # tags that were only ever WRAPPING a dropped sentence go with it, which
    # is why each of those is named rather than waved through.
    DROPPED_WITH_THE_SENTENCE = {
        'create_meal_plan.html': ('{% if edit_mode %}', '{% else %}',
                                  '{% endif %}'),
        'household_member_management.html': ('{% if can_edit %}',
                                             '{% endif %}'),
    }
    allow = DROPPED_WITH_THE_SENTENCE.get(rel, ())
    for tag in set(re.findall(r'\{\{.*?\}\}|\{%.*?%\}', orig_block, re.S)):
        if tag not in new and tag not in allow and tag not in lifted:
            raise SystemExit('G1: %s - the banner held %s and nothing that '
                             'replaces it does' % (rel, tag.strip()[:70]))

    before = text
    text = text[:m.start()] + new + text[end:]

    # --- the banner's own CSS goes with it --------------------------------
    names = ([cls] + ([lift] if lift else []) + NORMALISE_CSS.get(rel, [])
             + (carry['css'] if carry else []))
    parts, dropped = [], 0
    pos = 0
    for sm in STYLE.finditer(blanked(text)):
        body, n = drop_rules(text[sm.start(1):sm.end(1)], names)
        parts.append(text[pos:sm.start(1)])
        parts.append(body)
        pos = sm.end(1)
        dropped += n
    parts.append(text[pos:])
    text = ''.join(parts)

    # --- self-checks BEFORE anything is written ---------------------------
    if 'class="%s"' % TITLE_CLS not in text:
        raise SystemExit('G1: %s - the new title is not in the output' % rel)
    if re.search(r'(?<![\w-])\.' + re.escape(cls) + r'(?![\w-])',
                 '\n'.join(STYLE.findall(blanked(text)))):
        raise SystemExit('G1: %s - a rule for .%s survived' % (rel, cls))
    for dead in NORMALISE_CSS.get(rel, []):
        if re.search(r'class="[^"]*(?<![\w-])' + re.escape(dead) + r'(?![\w-])',
                     blanked(text)):
            raise SystemExit('G1: %s - .%s still worn after normalising'
                             % (rel, dead))
    # The SUBTITLE table decides, not the old markup: a page that had a
    # descriptive sentence is meant to come out with no h4 at all.
    if bool(h4) != ('class="%s"' % SUB_CLS in text):
        raise SystemExit('G1: %s - subtitle wanted=%s but emitted=%s'
                         % (rel, bool(h4), 'class="%s"' % SUB_CLS in text))
    want = (len(re.findall(r'<div\b', blanked(before))) - block_divs
            + (1 if lift else 0))
    got = len(re.findall(r'<div\b', blanked(text)))
    if got != want:
        raise SystemExit('G1: %s - <div> count is %d, expected %d (banner held '
                         '%d, lifted %d back)'
                         % (rel, got, want, block_divs, 1 if lift else 0))

    if not CHECK:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            CRLF[bak] = CRLF.get(path)
            write(bak, before)
        write(path, text)
    return (title, bool(h4), bool(lift), dropped)


def guard_held():
    """The three held back must still carry their banner, untouched."""
    for rel, cls in HELD.items():
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            raise SystemExit('G1: %s is not in this tree' % rel)
        t = blanked(read(path))
        if not re.search(r'class="[^"]*(?<![\w-])' + re.escape(cls)
                         + r'(?![\w-])', t):
            raise SystemExit('G1: %s no longer wears .%s - it was held back '
                             'on purpose, so something else took it' % (rel, cls))
        if os.path.exists(path + SUFFIX):
            raise SystemExit('G1: %s has a backup - it was meant to be held '
                             'back' % rel)


LATER = [
    ('alv_rounds.py',
     "    '.bak_surfdeep',\n]",
     "    '.bak_surfdeep',\n    '.bak_pagetitle',\n]"),
    ('Push-PendingChanges.ps1',
     "    'test_surface_deep.py'",
     "    'test_surface_deep.py'\n    'test_page_title.py'"),
]


def patch_later():
    done = 0
    for name, old, new in LATER:
        path = os.path.join(HERE, name)
        text = read(path)
        if new in text:              # decided by the NEW text alone (47)
            continue
        if text.count(old) != 1:
            raise SystemExit('G1/LATER: anchor matched %d times in %s'
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
    print('=' * 74)
    print('SECTION G, ROUND G1 - THE COLOURED BANNERS COME OFF - %s'
          % ('CHECK ONLY' if CHECK else 'APPLYING'))
    print('=' * 74)
    guard_held()
    done = subs = lifts = rules = 0
    for rel, cls, lift in JOBS:
        r = patch(rel, cls, lift)
        if r is None:
            print('  %-42s already applied' % rel)
            continue
        title, has_sub, has_lift, n = r
        done += 1
        subs += 1 if has_sub else 0
        lifts += 1 if has_lift else 0
        rules += n
        flat = re.sub(r'<[^>]+>', '', title)
        flat = re.sub(r'\{[{%].*?[}%]\}', '~', flat, flags=re.S)
        print('  %-42s %-30s %s%s  -%d rule(s)'
              % (rel, ' '.join(flat.split())[:30],
                 'sub ' if has_sub else '    ', 'lift' if has_lift else '    ',
                 n))
    later = patch_later()
    print('-' * 74)
    print('  %d banner(s) removed; %d subtitle(s) emitted; %d control group(s) '
          'lifted;\n  %d local rule(s) deleted; %d LATER edit(s).'
          % (done, subs, lifts, rules, later))
    print()
    print('  HELD BACK, and asserted still present:')
    for rel, cls in HELD.items():
        print('    %-44s .%s' % (rel, cls))
    print('=' * 74)


if __name__ == '__main__':
    main()
