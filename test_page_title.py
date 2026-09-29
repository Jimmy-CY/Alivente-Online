# -*- coding: utf-8 -*-
"""test_page_title.py - Section G round G1, 27 Sep 2026.

Judges the removal of 16 coloured page banners and their replacement with
.page-title-h2 and .page-subtitle-h4, which base already defines and 66 pages
already use.

THIS ROUND IS VISIBLE ON PURPOSE, so there is no no-pixel invariant to assert.
What can be asserted is that the house standard is now worn, the local
inventions are gone, and nothing that was held back was touched.

THE INVENTORY WAS WRONG TWICE BEFORE IT WAS RIGHT, and section 5 pins the
corrected one so it cannot drift back:
  1. A substring match counted .map-page-header as .page-header, putting
     map_view and property_detail on the list. Neither has a banner - both
     declare a plain flex row with no background. base's own standards block
     warns that a word boundary fires on a hyphen (lesson 30).
  2. A hand-rolled tag walker lost its place on a nested conditional and missed
     preview_imported_recipe, which does have one.
The list came in the end from a real HTML parser: each page's first heading,
its actual ancestors, and whether any of them is painted.

WHAT RENDERING CAUGHT THAT READING DID NOT. Lifting the three control groups
out of their banners and stopping there ships household_member_management's
Add Person, Help and Back as bare GREEN TEXT LINKS - its whole button
appearance came from .hm-btn-white, a dialect named for the banner, and that
dialect dies with the banner's CSS. Section 3 asserts the house classes took
over and the dialect is gone from markup AND stylesheet.
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
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)
# ------------------------------------------------------------------------

import os
import re
import sys
import alv_tree

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_pagetitle'
ME = 'test_page_title.py'
PATCHER = 'apply_page_title.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(T, 'base.html')

TITLE_CLS = 'page-title-h2'
SUB_CLS = 'page-subtitle-h4'
BAR_CLS = 'page-action-buttons'

# (template, the banner class it wore, the controls it held or None)
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
# A SUBTITLE IS A MODE LABEL OR A RECORD, NEVER A DESCRIPTION. Counted
# before this round: 38 pages carried a .page-subtitle-h4 and 37 were a short
# UPPERCASE mode label on an Add/Edit screen - ADD EXPENSE, EDIT REVENUE,
# ADD NEW PROPERTY - median three words. Every management screen in the
# house, Properties included, carries a title and nothing else.
#
# The first form of this round moved the old banner's descriptive sentence
# into the h4 on fourteen pages. test_heading_standard, which states the rule
# as "an h4 shouts and an h5 does not", went red on all fourteen - and it
# was right. The sentences come off. These five keep an h4 because it
# carries a MODE LABEL or DATA, which is what the house uses one for.
SUBTITLED = {
    'create_meal_plan.html': 'a mode label - CREATE / EDIT MEAL PLAN',
    'household_member_management.html': 'the workspace name',
    'map_ingredients_nutrition.html': 'the recipe being scoped',
    'meal_plan_shopping_list.html': 'the plan, its dates and its day count',
    'unit_conversions_wizard.html': 'the recipe being scoped',
}
HELD = {'view_meal_plan.html': 'page-header',
        'view_recipe.html': 'recipe-header-content'}
DIALECT = ('hm-btn-white', 'hm-btn-primary', 'hm-btn-icon', 'hm-btn-label')
# The banners whose white text failed contrast, measured before removal.
FAILING = {'household_member_management.html': 3.13,
           'ingredient_base_units_management.html': 2.13,
           'map_ingredients_nutrition.html': 2.13,
           'meal_plan_shopping_list.html': 2.13,
           'unit_conversions_wizard.html': 1.63,
           'categories_management.html': None}   # teal gradient, passed
# The two class names that a SUBSTRING match wrongly swept in.
NOT_BANNERS = {'map_view.html': 'map-page-header',
               'property_detail.html': 'page-header'}
# Same greens, NOT a page banner, NOT in this round: what legitimately stays
# behind in three of those files. Measured, then pinned here.
KEEPS = {'ingredient_base_units_management.html': ['.nm-header'],
         'map_ingredients_nutrition.html': ['.progress-bar-fill'],
         'unit_conversions_wizard.html': ['.progress-bar-fill']}

HTML_C = re.compile(r'<!--.*?-->', re.S)
DJ_CB = re.compile(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', re.S | re.I)
DJ_C = re.compile(r'\{#.*?#\}', re.S)
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')
PROTECT = re.compile(r'<[^>]*>|\{%.*?%\}|\{\{.*?\}\}|&[#0-9A-Za-z]+;', re.S)

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


def _sp(m):
    return re.sub(r'[^\n]', ' ', m.group(0))


def blanked(t):
    for rx in (HTML_C, DJ_CB, DJ_C):
        t = rx.sub(_sp, t)
    return t


def wears(text, cls):
    """By EXACT class token. A substring match is what put two pages that have
    no banner at all onto the first inventory."""
    return sum(1 for m in re.finditer(r'class="([^"]*)"', blanked(text))
               if cls in m.group(1).split())


def css_of(text):
    return '\n'.join(STYLE.findall(blanked(text)))


def rules_for(text, cls):
    return sum(1 for m in RULE.finditer(css_of(text))
               if re.search(r'(?<![\w-])\.' + re.escape(cls) + r'(?![\w-])',
                            ' '.join(m.group(1).split())))


GRAD = re.compile(r'linear-gradient\([^)]*#(28a745|20c997|ffc107|fd7e14)', re.I)


def grad_selectors(text):
    """Which SELECTORS carry a failing gradient. The first form of this check
    searched the whole stylesheet, so three files read as failures because a
    modal header and two progress bars use the same greens the banners did -
    neither is a page banner and neither is in this round (lesson: a
    whole-file search cannot tell one rule from another)."""
    out = []
    for m in RULE.finditer(css_of(text)):
        if GRAD.search(m.group(2)):
            out.append(' '.join(m.group(1).split()))
    return out


def upper_text(html):
    out, pos = [], 0
    for m in PROTECT.finditer(html):
        out.append(html[pos:m.start()].upper())
        out.append(m.group(0))
        pos = m.end()
    out.append(html[pos:].upper())
    return ''.join(out)


def title_of(text):
    m = re.search(r'<h2[^>]*class="[^"]*' + TITLE_CLS + r'[^"]*"[^>]*>(.*?)</h2>',
                  text, re.S)
    return m.group(1) if m else None


# ==========================================================================
head('1. THE ROUND IS ON DISK, AND THE BANNERS ARE GONE')
# ==========================================================================
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS empty')
ok(ROUNDS.index('.bak_surfdeep') < ROUNDS.index(SUFFIX)
   if ('.bak_surfdeep' in ROUNDS and SUFFIX in ROUNDS) else False,
   '  and AFTER F2a-3 - order is the real property, not recency (lesson 54)')

subs = 0
for rel, cls, lift in JOBS:
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    a, b = was(p), now(p)
    ok(wears(a, cls) == 1 and wears(b, cls) == 0,
       '%-40s .%s worn 1 -> 0' % (rel, cls),
       'before %d, after %d' % (wears(a, cls), wears(b, cls)))
    ok(rules_for(a, cls) > 0 and rules_for(b, cls) == 0,
       '  and its %d local rule(s) went with it' % rules_for(a, cls),
       'after: %d' % rules_for(b, cls))
    ok(wears(b, TITLE_CLS) >= 1, '  it now wears .%s' % TITLE_CLS)
    want_sub = rel in SUBTITLED
    got_sub = wears(b, SUB_CLS) >= 1
    subs += 1 if got_sub else 0
    ok(got_sub == want_sub,
       '  subtitle %s' % (SUBTITLED[rel] if want_sub
                          else 'dropped - a description is not a house h4'),
       'want %s got %s' % (want_sub, got_sub))
ok(subs == 5, 'five keep an h4 - a mode label or a record - and eleven '
   'carry a title alone, as Properties does', subs)
# The descriptive sentences really were there, or dropping them proves
# nothing.
_lost = [r for r, _, _ in JOBS
         if r not in SUBTITLED and os.path.isfile(os.path.join(T, r))
         and re.search(r'<p[^>]*>\s*[A-Za-z]', was(os.path.join(T, r)))]
ok(len(_lost) >= 9,
   'CONTROL: %d of the eleven really did carry a sentence to drop'
   % len(_lost), _lost)
ok(len(JOBS) == 16, 'sixteen banners in all', len(JOBS))

# ==========================================================================
head('2. THE TITLES FOLLOW THE HOUSE CONVENTIONS, WHICH WERE COUNTED FIRST')
# ==========================================================================
# 87 house page titles are uppercase, 1 is mixed only because it holds an
# ampersand entity, 0 are lower. 0 of 88 carry an icon.
for rel, cls, lift in JOBS:
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        continue
    t = title_of(now(p))
    if t is None:
        ok(False, '%-40s has a .%s heading' % (rel, TITLE_CLS))
        continue
    letters = [c for c in re.sub(PROTECT, '', t) if c.isalpha()]
    ok(letters and all(c.isupper() for c in letters),
       '%-40s title is uppercase' % rel,
       ' '.join(re.sub(PROTECT, '', t).split())[:50])
    ok('<i ' not in t and 'fa-' not in t,
       '  and carries no icon - 0 of 88 house titles do')
ok('{% if mode ==' in (title_of(now(os.path.join(T, 'preview_imported_recipe.html'))) or ''),
   'preview_imported_recipe keeps its THREE-BRANCH conditional heading - a '
   'prototype of this round flattened it into one sentence (lesson 52)')
_t = title_of(now(os.path.join(T, 'preview_imported_recipe.html'))) or ''
ok(_t.count('{% if') + _t.count('{% elif') + _t.count('{% else') == 3
   and '{% endif %}' in _t,
   '  all three branches and the endif are intact',
   ' '.join(_t.split())[:110])

# ==========================================================================
head('3. THE LIFTED CONTROLS BROUGHT THEIR STYLING WITH THEM')
# ==========================================================================
for rel, cls, lift in JOBS:
    if not lift:
        continue
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        continue
    b = now(p)
    ok(wears(b, BAR_CLS) >= 1, '%-40s controls sit in .%s' % (rel, BAR_CLS))
    ok(wears(b, lift) == 0, '  and .%s is gone' % lift)
    ok(rules_for(b, lift) == 0, '  along with its rules')

hm = os.path.join(T, 'household_member_management.html')
if os.path.isfile(hm):
    b = now(hm)
    ok(wears(b, 'action-primary') == 1 and wears(b, 'action-secondary') == 1
       and wears(b, 'action-back') == 1,
       'Household Members wears ONE primary (Add Person), ONE secondary '
       '(Help) and ONE back',
       'primary %d, secondary %d, back %d'
       % (wears(b, 'action-primary'), wears(b, 'action-secondary'),
          wears(b, 'action-back')))
    for d in DIALECT:
        ok(wears(b, d) == 0 and rules_for(b, d) == 0,
           '  .%s is gone from markup and stylesheet' % d,
           'worn %d, rules %d' % (wears(b, d), rules_for(b, d)))
    ok('action-back-label' in b,
       '  and Back keeps the label base hides on a small screen')
    ok(wears(was(hm), 'hm-btn-white') >= 3,
       '  it really did wear the dialect before - lifting alone would have '
       'left three bare green text links at 3.13 on white',
       wears(was(hm), 'hm-btn-white'))
else:
    skip('household_member_management', 'not on disk')

# --------------------------------------------------------------------------
# THREE THINGS ONLY THE RENDER SAW. Reading the file said all three were
# fine; the picture said otherwise. Pinned here so a later round cannot put
# them back without the gate going red.
# --------------------------------------------------------------------------
cd = os.path.join(T, 'celebration_dashboard.html')
if os.path.isfile(cd):
    b, a = now(cd), was(cd)
    ok(wears(a, 'action-primary') == 1 and wears(b, 'action-primary') == 0
       and wears(b, 'action-secondary') == 1,
       'Celebrations Dashboard: Help moved off .action-primary',
       'was primary %d / now primary %d, secondary %d'
       % (wears(a, 'action-primary'), wears(b, 'action-primary'),
          wears(b, 'action-secondary')))
    ok('btn-light' not in b and 'btn-sm' not in b,
       '  and its btn-light/btn-sm, written for a teal ground, are gone')
    ok('style="color:var(--alv-accent-ink);"' not in b
       and 'style="color:#495057;"' not in b,
       '  along with the inline icon colours that went with them')
else:
    skip('celebration_dashboard', 'not on disk')

# Help is NOT a primary action anywhere in this app. Counted, not assumed.
HELP = re.compile(r'<(?:button|a)\b[^>]*class="([^"]*)"[^>]*>\s*'
                  r'(?:<i[^>]*>\s*</i>)?\s*Help\s*<', re.S | re.I)
prim = []
for fn in sorted(os.listdir(T)):
    if not fn.endswith('.html'):
        continue
    for m in HELP.finditer(blanked(read(os.path.join(T, fn)))):
        if 'action-primary' in m.group(1).split():
            prim.append(fn)
ok(not prim,
   'no page in the tree puts Help on .action-primary - 29 use '
   '.action-secondary, 21 the overflow menu', prim)

mc = os.path.join(T, 'meal_plan_calendar.html')
if os.path.isfile(mc):
    b, a = now(mc), was(mc)
    ok(wears(a, 'btn-header-disabled') == 1,
       'Meal Plan Calendar: the disabled New Meal Plan wore '
       '.btn-header-disabled', wears(a, 'btn-header-disabled'))
    ok(re.search(r'rgba\(255,\s*255,\s*255', css_of(a), re.I) is not None,
       '  which painted white on white once the teal went - an EMPTY BOX, '
       'and the render is the only thing that said so')
    ok(wears(b, 'btn-header-disabled') == 0
       and rules_for(b, 'btn-header-disabled') == 0,
       '  it is gone from markup and stylesheet',
       'worn %d, rules %d' % (wears(b, 'btn-header-disabled'),
                              rules_for(b, 'btn-header-disabled')))
    ok(wears(b, 'disabled-btn') == 1,
       '  and wears the house .disabled-btn instead, as properties.html does',
       wears(b, 'disabled-btn'))
else:
    skip('meal_plan_calendar', 'not on disk')

# --------------------------------------------------------------------------
# NOTHING THE BANNER HELD WENT MISSING. Reading the first heading and the
# first paragraph and dropping the rest lost real content on four pages, and
# a diff does not read as loss when what vanished is {{ x }}.
# --------------------------------------------------------------------------
CARRIED = {
    'household_member_management.html': ['{{ workspace.name }}'],
    'map_ingredients_nutrition.html': ['{{ scoped_recipe.recipe_name }}'],
    'unit_conversions_wizard.html': ['{{ scoped_recipe.recipe_name }}'],
    'meal_plan_shopping_list.html': ['{{ meal_plan.start_date|date:"M d" }}',
                                     '{{ meal_plan.end_date|date:"M d, Y" }}',
                                     '{{ meal_plan.days.count|pluralize }}'],
}
DEAD_PILLS = {'household_member_management.html': 'hm-badge',
              'map_ingredients_nutrition.html': 'recipe-scope-pill',
              'unit_conversions_wizard.html': 'recipe-scope-pill',
              'meal_plan_shopping_list.html': 'page-header-meta'}
for rel in sorted(CARRIED):
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    b, a = now(p), was(p)
    sub = re.search(r'<h4[^>]*class="[^"]*' + SUB_CLS + r'[^"]*"[^>]*>(.*?)</h4>',
                    b, re.S)
    ok(sub is not None, '%-40s has a subtitle to carry into' % rel)
    for tag in CARRIED[rel]:
        ok(tag in a, '  the banner held %s' % tag)
        ok(sub is not None and tag in sub.group(1),
           '  and the subtitle carries it now')
    d = DEAD_PILLS[rel]
    ok(wears(a, d) == 1, '  .%s was the teal-ground pill that held it' % d,
       wears(a, d))
    ok(wears(b, d) == 0 and rules_for(b, d) == 0,
       '  .%s is gone from markup and stylesheet - it painted '
       'rgba(255,255,255,.2) and would now be white on white' % d,
       'worn %d, rules %d' % (wears(b, d), rules_for(b, d)))
ok(all(len(re.findall(r'class="[^"]*' + SUB_CLS, now(os.path.join(T, r))))
       == (1 if r in SUBTITLED else 0) for r, _, _ in JOBS
       if os.path.isfile(os.path.join(T, r))),
   'no page carries two subtitles - every house page that has one has ONE')
# And the five that keep one shout it, or hold data whose case is not ours.
for rel in sorted(SUBTITLED):
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        continue
    m = re.search(r'<h4[^>]*class="[^"]*' + SUB_CLS + r'[^"]*"[^>]*>(.*?)</h4>',
                  now(p), re.S)
    lit = re.sub(r'\{\{.*?\}\}|\{%.*?%\}|<[^>]+>|&[#0-9A-Za-z]+;', '',
                 m.group(1) if m else '', flags=re.S).strip()
    alpha = [c for c in lit if c.isalpha()]
    # The suite that states this rule separates a LABEL from a RECORD the
    # same way: a line that is mostly interpolation takes its case from the
    # data, and no rule here can set it. Shopping List's literal text is the
    # word "day" between three template tags.
    ok(len(alpha) < 6 or all(c.isupper() for c in alpha),
       '%-40s its h4 shouts, or is data whose case is not ours' % rel,
       repr(lit[:50]))

cm = os.path.join(T, 'create_meal_plan.html')
if os.path.isfile(cm):
    b = now(cm)
    ok(title_of(b) == 'MEAL PLANS',
       'Create Meal Plan takes the Add/Edit shape - h2 is the MODULE, as '
       'properties_add is PROPERTIES and act_expense_add is ACTUAL EXPENSES',
       title_of(b))
    h4 = re.search(r'<h4[^>]*class="[^"]*' + SUB_CLS + r'[^"]*"[^>]*>(.*?)</h4>',
                   b, re.S)
    h4 = h4.group(1) if h4 else ''
    ok('{% if edit_mode %}' in h4 and '{% else %}' in h4
       and 'EDIT MEAL PLAN' in h4 and 'CREATE MEAL PLAN' in h4,
       '  and its h4 keeps BOTH branches of the mode label - the generic '
       'path read the first heading, took the edit branch and dropped the '
       'create branch, which would have shipped Create with no heading',
       h4)
    ok('Plan your meals for the week' not in b
       and 'Update your meal plan details' not in b,
       '  its two descriptive sentences are gone - a description is not a '
       'house h4')
else:
    skip('create_meal_plan', 'not on disk')

# ==========================================================================
head('4. WHAT THE BANNERS TOOK WITH THEM')
# ==========================================================================
BANNER_OF = dict((rel, cls) for rel, cls, _ in JOBS)
gone = 0
for rel in FAILING:
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        continue
    had, has = grad_selectors(was(p)), grad_selectors(now(p))
    cls = BANNER_OF[rel]
    on_banner = [s for s in had
                 if re.search(r'(?<![\w-])\.' + re.escape(cls) + r'(?![\w-])', s)]
    if FAILING[rel] is None:
        ok(not had, '%-40s had no failing gradient to lose' % rel, had)
        continue
    ok(len(on_banner) == 1,
       '%-40s its %.2f gradient was on .%s' % (rel, FAILING[rel], cls),
       'carriers %s' % (had,))
    ok(not [s for s in has
            if re.search(r'(?<![\w-])\.' + re.escape(cls) + r'(?![\w-])', s)],
       '  and that rule is gone')
    ok(has == KEEPS.get(rel, []),
       '  what stays behind is exactly %s - no page banner among them'
       % (KEEPS.get(rel, []) or 'nothing'), has)
    gone += 1
ok(gone == 5, 'five failing banner gradients removed, worst of them 1.63', gone)
ok(sum(len(v) for v in KEEPS.values()) == 3,
   'three same-green gradients survive on a modal header and two progress '
   'bars - out of scope here, noted for the Bootstrap-family round')

# ==========================================================================
head('5. THE INVENTORY, PINNED - it was wrong twice')
# ==========================================================================
for rel, cls in NOT_BANNERS.items():
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    c = css_of(now(p))
    m = re.search(r'(?<![\w-])\.' + re.escape(cls)
                  + r'(?![\w-])\s*\{([^}]*)\}', c)
    ok(m is not None and not re.search(
        r'background(-color)?\s*:\s*(?!none|transparent|inherit)', m.group(1)),
       '%-40s .%s paints NOTHING - a substring match put it on the first '
       'inventory' % (rel, cls),
       ' '.join(m.group(1).split())[:70] if m else '(no rule)')
    ok(not os.path.isfile(p + SUFFIX), '  and this round never touched it')

for rel, cls in HELD.items():
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    ok(wears(now(p), cls) == 1,
       '%-40s still wears .%s - held back for a reading of its own'
       % (rel, cls))
    ok(not os.path.isfile(p + SUFFIX), '  and has no backup')

# ==========================================================================
head('6. CONTROLS - checks that would catch a vacuous suite')
# ==========================================================================
ok(len(JOBS) == 16 and len(HELD) == 2,
   'sixteen done, two held - eighteen painted banners in all')
ok(wears('<div class="map-page-header">x</div>', 'page-header') == 0,
   'the class counter is not fooled by a hyphen - map-page-header is not '
   'page-header (lesson 30)')
ok(wears('<div class="page-header wide">x</div>', 'page-header') == 1,
   '  and does find it beside another class')
ok(upper_text('a &amp; b') == 'A &amp; B',
   'the uppercaser leaves an entity alone - &AMP; is not an entity')
ok(upper_text("{% if x %}hi{% endif %}") == "{% if x %}HI{% endif %}",
   '  and leaves a Django tag alone while uppercasing its body')
ok(upper_text('<i class="fa-x"></i> hi') == '<i class="fa-x"></i> HI',
   '  and leaves markup alone')
ok(upper_text('{{ plan.name }}') == '{{ plan.name }}',
   '  and never touches a variable')

base_css = css_of(read(BASE))
ok(re.search(r'\.' + TITLE_CLS + r'\s*\{', base_css) is not None,
   'base defines .%s - this round invents nothing' % TITLE_CLS)
ok(re.search(r'\.' + SUB_CLS + r'\s*\{', base_css) is not None,
   '  and .%s' % SUB_CLS)
n = 0
for d, _x, fs in alv_tree.walk3():
    for f in fs:
        if f.endswith('.html') and '.bak_' not in f:
            if wears(now(os.path.join(d, f)), TITLE_CLS):
                n += 1
ok(n >= 70, '%d pages now wear the house title, up from 66' % n, n)

# A REVERT MUST FAIL A CHECK, NOT CRASH (lesson 55).
try:
    src = os.path.join(T, 'categories_management.html')
    if os.path.isfile(src + SUFFIX):
        dst = os.path.join(SCRATCH, 'r.html')
        _shutil.copyfile(src + SUFFIX, dst)
        rev = read(dst)
        ok(wears(rev, 'page-header') == 1 and wears(rev, TITLE_CLS) == 0,
           'reverting categories_management puts its banner back, so the '
           'check that says it is gone would FAIL - a revert is caught')
        ok(title_of(rev) is None,
           '  and the title helper returns None rather than raising on it')
    else:
        skip('revert test', 'no backup to revert from')
except Exception as e:
    ok(False, 'the revert test ran without crashing', repr(e))

p1 = os.path.join(ROOT, PS1)
if os.path.isfile(p1):
    ok(ME in read(p1), '%s is on the push gate' % ME)
else:
    skip(PS1, 'not on disk')

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
