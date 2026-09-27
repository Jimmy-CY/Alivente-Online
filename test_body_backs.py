# -*- coding: utf-8 -*-
"""test_body_backs.py - Section H round H3, 27 Sep 2026.

Judges the thirteen Back controls that sit in page BODIES rather than in a
.page-action-buttons bar - hand-rolled headers, wizard done-states, modal
step footers, card footers. G2 fixed the ones in bars and never claimed
these; counted after H2, thirteen still wore a Bootstrap colour class, and
every one is Personal.

THE CLAIM THIS SUITE EXISTS FOR IS NOT "THE COLOUR CAME OFF". It is that
NINE of them lost a WORD and did not lose the INFORMATION: "Back to Recipe"
became "Back", and the destination moved to the aria-label, where a screen
reader still reads it. Section 2 checks that for each one by name. A round
that shortened the label and dropped the destination would pass a
colour-only suite and be worse than what it replaced.

AND FOUR WERE NOT PAGE BACKS AT ALL. Two are wizard steps, one is a modal
step, one resets an AI picker and navigates nowhere. They keep their words
and take .action-secondary. Section 3 asserts their words are UNCHANGED -
a round that swept them would be claiming a judgement it never made.
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

SUFFIX = '.bak_bodybacks'
ME = 'test_body_backs.py'
PATCHER = 'apply_body_backs.py'
PS1 = 'Push-PendingChanges.ps1'
LABEL_CLS = 'action-back-label'

COLOUR = re.compile(r'\bbtn-(?:secondary|success|light|info|primary|dark|'
                    r'warning|danger|outline-secondary|outline-success)\b')
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)

# (file, the fragment that identifies it, the word BEFORE, the word AFTER,
#  the aria-label it must now carry or None)
NINE = [
    ('import_recipe.html', "{% url 'recipe_management' %}",
     'Back to Recipes', 'Back', 'Back to Recipe Management'),
    ('ingredient_families.html', "{% url 'pantry_staples_management' %}",
     'Back', 'Back', 'Back to Pantry Staples'),
    ('pantry_staples.html', "{% url 'recipe_management' %}",
     'Back', 'Back', 'Back to Recipe Management'),
    ('wcim_extras.html', "{% url 'wcim_landing' %}",
     'Back', 'Back', 'Back to What Can I Make?'),
    ('wcim_landing.html', "{% url 'recipe_management' %}",
     'Back', 'Back', 'Back to Recipe Management'),
    ('map_ingredients_nutrition.html', '?reopen_nutrition=1',
     'Back to Recipe', 'Back', 'Back to Recipe'),
    ('map_ingredients_nutrition.html',
     "{% url 'ingredient_base_units_management' %}",
     'Back to Ingredients', 'Back',
     'Back to Ingredient Shopping Units'),
    ('unit_conversions_wizard.html', '?reopen_nutrition=1',
     'Back to Recipe', 'Back', 'Back to Recipe'),
    ('unit_conversions_wizard.html',
     "{% url 'ingredient_base_units_management' %}",
     'Back to Ingredients', 'Back',
     'Back to Ingredient Shopping Units'),
]
# The four that keep their words, and WHY.
FOUR = [
    ('meal_plan_shopping_list.html', "{% url 'view_meal_plan' ",
     'Back to Meal Plan',
     'a card control, and the page already has its own Back in the bar'),
    ('meal_plan_shopping_list.html', 'goBackToReview()', 'Back',
     'a WIZARD STEP, not a page Back'),
    ('view_recipe.html', 'previousStep()', 'Back',
     'a MODAL STEP, not a page Back'),
    ('view_recipe.html', 'aiResetToPicker()', 'Back to goals',
     'it resets an AI picker and navigates nowhere'),
]
# Named so they are never re-investigated.
LEFT_ALONE = {
    '.btn.back-button x8': 'base declares it as a TWIN of .action-back',
    '.rotate-prompt-back x4': 'inside the landscape rotate prompt',
    '.btn-help-back': 'the help shell',
    'act_expense "Back to overview"': 'a drill-down return within the page',
    'connectivity_error "Go Back"': 'an error page with no bar anywhere',
}

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
    """Comments blanked on the RAW text FIRST, then script and style - the
    house order is defeated by accept="image/*" (lesson 61)."""
    t = re.sub(r'<!--.*?-->', _sp, t, flags=re.S)
    t = re.sub(r'\{#.*?#\}', _sp, t, flags=re.S)
    for rx in (STYLE, SCRIPT):
        out, pos = [], 0
        for m in rx.finditer(t):
            out.append(t[pos:m.start(1)])
            out.append(re.sub(r'[^\n]', ' ', m.group(1)))
            pos = m.end(1)
        out.append(t[pos:])
        t = ''.join(out)
    return t


def elements(scan, frag):
    out = []
    for m in re.finditer(r'<(a|button)\b[^>]*>', scan):
        if frag not in m.group(0):
            continue
        tag, d, end = m.group(1), 0, None
        for x in re.finditer(r'</?%s\b' % tag, scan[m.start():]):
            d += 1 if x.group(0) == '<' + tag else -1
            if d == 0:
                end = scan.find('>', m.start() + x.end()) + 1
                break
        if end:
            out.append((m.start(), end))
    return out


def word(html):
    return ' '.join(re.sub(r'<[^>]+>|\{[%{].*?[%}]\}', '', html).split())


def one(text, frag, want_word=None, want_aria=None):
    """The single Back-ish control carrying `frag`.

    FOUR OF THESE PAGES HAVE TWO controls on the same href - the bar Back
    G2 fixed, and the body Back beneath it. Before this round the WORD told
    them apart ("Back" vs "Back to Ingredients"); AFTER it both say "Back",
    so the word cannot, and the ARIA-LABEL is what does. Asking the word to
    do a job it no longer can is how three of these checks first failed."""
    hits = [h for h in elements(blanked(text), frag)
            if re.match(r'(?i)back\b', word(text[h[0]:h[1]]))]
    if len(hits) == 1:
        return text[hits[0][0]:hits[0][1]]
    for pick in ((lambda h: want_aria is not None
                  and re.search(r'aria-label="([^"]*)"', text[h[0]:h[1]])
                  and re.search(r'aria-label="([^"]*)"',
                                text[h[0]:h[1]]).group(1) == want_aria),
                 (lambda h: want_word is not None
                  and word(text[h[0]:h[1]]) == want_word)):
        exact = [h for h in hits if pick(h)]
        if len(exact) == 1:
            return text[exact[0][0]:exact[0][1]]
    return None


# ==========================================================================
head('1. NOT ONE BACK IN THE TREE WEARS A BOOTSTRAP COLOUR')
# ==========================================================================
left = []
for d, _s, fs in os.walk(T):
    for f in sorted(fs):
        if not f.endswith('.html') or f == 'base.html':
            continue
        rel = os.path.relpath(os.path.join(d, f), T).replace(os.sep, '/')
        mk = blanked(read(os.path.join(d, f)))
        for m in re.finditer(r'<(a|button|span)\b[^>]*class="([^"]*)"[^>]*>'
                             r'(.*?)</\1\s*>', mk, re.S):
            if not re.match(r'(?i)(back|go back)\b', word(m.group(3))):
                continue
            col = [c for c in m.group(2).split() if COLOUR.match(c)]
            if col:
                left.append((rel, word(m.group(3))[:24], col))
ok(not left, 'no Back control anywhere still carries one', left)
n_before = 0
for rel in sorted(set([j[0] for j in NINE] + [j[0] for j in FOUR])):
    p = os.path.join(T, rel)
    if not os.path.isfile(p + SUFFIX):
        continue
    for m in re.finditer(r'<(a|button)\b[^>]*class="([^"]*)"[^>]*>(.*?)'
                         r'</\1\s*>', blanked(was(p)), re.S):
        if re.match(r'(?i)back\b', word(m.group(3))) \
                and COLOUR.search(m.group(2)):
            n_before += 1
ok(n_before == 13,
   'CONTROL: there were THIRTEEN to fix - the check above is not passing '
   'on an empty set', n_before)

# ==========================================================================
head('2. THE NINE LOST A WORD, NOT THE INFORMATION')
# ==========================================================================
for rel, frag, before_w, after_w, aria in NINE:
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    a = one(was(p), frag, before_w)
    b = one(now(p), frag, after_w, aria)
    if not ok(a is not None and b is not None,
              '%-34s %r is there before and after' % (rel, frag[:28]),
              'before %s / after %s' % (a is not None, b is not None)):
        continue
    ok(word(a) == before_w, '  it said %r' % before_w, word(a))
    ok(word(b) == after_w, '  and says %r now' % after_w, word(b))
    # THE POINT OF THE ROUND.
    m = re.search(r'aria-label="([^"]*)"', b)
    ok(m is not None and m.group(1) == aria,
       '  its destination survives where a screen reader reads it: %r'
       % aria, m.group(1) if m else 'NO aria-label')
    ok(LABEL_CLS in b,
       '  and the word is inside .%s, so base hides it on a phone'
       % LABEL_CLS)
    ok('action-back' in re.search(r'class="([^"]*)"', b).group(1).split(),
       '  it wears .action-back')
    ok(re.search(r'href=|onclick=', b) is not None,
       '  and still goes where it went')

# ==========================================================================
head('3. THE FOUR THAT ARE NOT PAGE BACKS KEEP THEIR WORDS')
# ==========================================================================
for rel, frag, keeps, why in FOUR:
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    a, b = one(was(p), frag, keeps), one(now(p), frag, keeps)
    if not ok(a is not None and b is not None,
              '%-34s %r is there before and after' % (rel, frag[:26])):
        continue
    ok(word(a) == word(b) == keeps,
       '  keeps %r - %s' % (keeps, why), '%r -> %r' % (word(a), word(b)))
    cls = re.search(r'class="([^"]*)"', b).group(1)
    ok('action-secondary' in cls.split(),
       '  and takes .action-secondary', cls)
    ok(not COLOUR.search(cls), '  with no Bootstrap colour class', cls)
    ok(LABEL_CLS not in b,
       '  and is NOT given the phone label span - it is not a page Back')

# ==========================================================================
head('4. WHAT THIS ROUND DID NOT DO')
# ==========================================================================
print('    Named, so none of them has to be investigated again:')
for what, why in sorted(LEFT_ALONE.items()):
    print('      %-34s %s' % (what, why))
bb = 0
for d, _s, fs in os.walk(T):
    for f in fs:
        if f.endswith('.html'):
            bb += len(re.findall(r'class="[^"]*(?<![\w-])back-button(?![\w-])',
                                 blanked(read(os.path.join(d, f)))))
ok(bb >= 7, '.back-button is worn %d time(s) and is left alone - base '
   'declares it in the SAME rule as .action-back' % bb, bb)
base_css = '\n'.join(STYLE.findall(read(os.path.join(T, 'base.html'))))
ok(re.search(r'\.btn\.action-back\s*,\s*\n?\s*\.btn\.back-button', base_css)
   is not None,
   '  and they really are declared together, which is why it is house',
   'not found')
# THE FIVE PAGES WITH NO BAR ARE G3b's, NOT THIS ROUND's.
NO_BAR = ('import_recipe.html', 'ingredient_families.html',
          'pantry_staples.html', 'wcim_extras.html', 'wcim_landing.html')
nb = [r for r in NO_BAR
      if os.path.isfile(os.path.join(T, r))
      and 'page-action-buttons' not in blanked(now(os.path.join(T, r)))]
ok(len(nb) == 5,
   'the five hand-rolled-header pages still have NO action bar - this '
   'round fixed the class and the word, not where the control sits, and '
   'building a bar where there is none is G3b', nb)

# ==========================================================================
head('5. CONTROLS, AND THE GATE')
# ==========================================================================
ok(len(NINE) == 9 and len(FOUR) == 4,
   'nine page Backs and four that are not, thirteen in all')
ok(word('<a><i class="fas fa-arrow-left"></i> Back to X</a>') == 'Back to X',
   'the word reader strips the icon')
ok(word('<a>{% if x %}Back{% endif %}</a>') == 'Back',
   '  and a template tag')
ok(COLOUR.search('btn action-back') is None,
   'the colour match does not fire on .action-back itself')
ok(COLOUR.search('btn btn-info') is not None, '  and does on btn-info')
mi = os.path.join(T, 'map_ingredients_nutrition.html')
if os.path.isfile(mi + SUFFIX):
    ok(one(was(mi), '?reopen_nutrition=1', 'Back to Recipe') is not None,
       'reverting map_ingredients_nutrition brings "Back to Recipe" back, '
       'so section 2 would FAIL - a revert is caught')
    ok(len([h for h in elements(blanked(now(mi)),
                                "{% url 'ingredient_base_units_management' %}")]) == 2,
       '  CONTROL: two controls on that page share an href - the bar Back '
       'and the done-state one - so the word is what tells them apart')
else:
    skip('the revert check', 'no %s backup' % SUFFIX)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
ok(SUFFIX in ROUNDS and '.bak_celebrations' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_celebrations'),
   '  and after the round before it (lesson 54)')
ps1 = os.path.join(ROOT, PS1)
ok(os.path.isfile(ps1) and ME in read(ps1), '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
