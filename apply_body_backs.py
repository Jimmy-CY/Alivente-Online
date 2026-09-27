# -*- coding: utf-8 -*-
"""SECTION H, ROUND H3 - THE BACK CONTROLS THAT ARE NOT IN AN ACTION BAR

G2 fixed the Back controls INSIDE .page-action-buttons. A second population
sits in page BODIES - hand-rolled headers, wizard done-states, modal step
footers, card footers - and G2 never claimed them. Counted after H2:
thirteen still wear a Bootstrap colour class, and every one is Personal.

THEY ARE NOT ALL THE SAME THING, and treating them as one would be the
mistake this round exists to avoid.

  NINE ARE PAGE BACKS. They become `btn action-back`, say "Back", and keep
  their destination in the aria-label - where a screen reader has the page
  to read it from and the eye does not need it. Four of those nine are an
  {% if %}/{% else %} PAIR on a wizard's done-state: only ever ONE renders,
  so there is no ambiguity on screen from both saying "Back".

  FOUR ARE NOT PAGE BACKS AT ALL, and they keep their words:
    meal_plan_shopping_list  "Back to Meal Plan" - a card control, and the
                             page already has its own Back in the bar. Two
                             controls both saying "Back" would be worse
                             than one saying where it goes.
    meal_plan_shopping_list  "Back" (goBackToReview) - a WIZARD STEP
    view_recipe              "Back" (previousStep)   - a MODAL STEP
    view_recipe              "Back to goals" (aiResetToPicker) - it resets a
                             picker; it navigates nowhere
  Those four take .action-secondary, which is what the house gives a
  non-primary control in a footer.

WHAT THIS ROUND DOES NOT DO. It does not move anything into an action bar.
Five of these pages have no bar at all - import_recipe, ingredient_families,
pantry_staples, wcim_extras, wcim_landing, the hand-rolled-header family -
and building one where there is none is G3b, a round of its own. H3 fixes
the CLASS and the WORD; where the control sits is G3b's business.

ALSO LEFT, and named so they are not re-investigated:
  .btn.back-button x8        base declares it as a TWIN of .action-back -
                             these are already house
  .rotate-prompt-back x4     inside the landscape rotate prompt
  .btn-help-back             the help shell
  act_expense "Back to overview"   a drill-down return within the page
  connectivity_error "Go Back"     an error page with no bar anywhere
  properties_edit / property_assets  .action-secondary already, and they
                             are secondary navigation, not the page Back

Backups: .bak_bodybacks. Idempotent. --check prints and writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.getcwd()
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_bodybacks'
CRLF = {}

LABEL_CLS = 'action-back-label'
COLOUR = re.compile(r'\bbtn-(?:secondary|success|light|info|primary|dark|'
                    r'warning|danger|outline-secondary|outline-success)\b')

# (file, a fragment unique to THIS control, new classes, new visible label
#  or None to keep it, aria-label or None to leave alone)
#
# Located by the control's OWN href or onclick, not by whitespace: an
# anchor written with \n does not match a CRLF file (lesson 70), and the
# indentation of a button is not a fact worth depending on.
JOBS = [
    # ---- nine page Backs: the word becomes "Back" ----------------------
    ('import_recipe.html', "{% url 'recipe_management' %}",
     'btn action-back', 'Back', 'Back to Recipe Management'),
    ('ingredient_families.html', "{% url 'pantry_staples_management' %}",
     'btn action-back', 'Back', 'Back to Pantry Staples'),
    ('pantry_staples.html', "{% url 'recipe_management' %}",
     'btn action-back', 'Back', 'Back to Recipe Management'),
    ('wcim_extras.html', "{% url 'wcim_landing' %}",
     'btn action-back', 'Back', 'Back to What Can I Make?'),
    ('wcim_landing.html', "{% url 'recipe_management' %}",
     'btn action-back', 'Back', 'Back to Recipe Management'),
    # the two done-state pairs - an {% if %}/{% else %}, one renders
    ('map_ingredients_nutrition.html', '?reopen_nutrition=1',
     'btn action-back', 'Back', 'Back to Recipe'),
    ('map_ingredients_nutrition.html',
     "{% url 'ingredient_base_units_management' %}",
     'btn action-back', 'Back', 'Back to Ingredient Shopping Units'),
    ('unit_conversions_wizard.html', '?reopen_nutrition=1',
     'btn action-back', 'Back', 'Back to Recipe'),
    ('unit_conversions_wizard.html',
     "{% url 'ingredient_base_units_management' %}",
     'btn action-back', 'Back', 'Back to Ingredient Shopping Units'),
    # ---- four that are NOT page Backs: they keep their words -----------
    ('meal_plan_shopping_list.html', "{% url 'view_meal_plan' ",
     'btn action-secondary', None, None),
    ('meal_plan_shopping_list.html', 'goBackToReview()',
     'btn action-secondary', None, None),
    ('view_recipe.html', 'previousStep()',
     'btn action-secondary', None, None),
    ('view_recipe.html', 'aiResetToPicker()',
     'btn action-secondary', None, None),
]
# How many of the nine keep a destination only a screen reader hears.
PAGE_BACKS = [j for j in JOBS if j[3] == 'Back']
KEEP_WORD = [j for j in JOBS if j[3] is None]

HTML_C = re.compile(r'<!--.*?-->', re.S)
DJ_C = re.compile(r'\{#.*?#\}', re.S)
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
ARROW = re.compile(r'<i\b[^>]*fa-arrow-left[^>]*>\s*</i\s*>', re.S)


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


def blanked(t):
    """Comments blanked on the RAW text FIRST, then script and style bodies
    - the house order is defeated by accept="image/*" (lesson 61)."""
    t = HTML_C.sub(_sp, t)
    t = DJ_C.sub(_sp, t)
    for rx in (STYLE, SCRIPT):
        out, pos = [], 0
        for m in rx.finditer(t):
            out.append(t[pos:m.start(1)])
            out.append(re.sub(r'[^\n]', ' ', m.group(1)))
            pos = m.end(1)
        out.append(t[pos:])
        t = ''.join(out)
    return t


def element(scan, frag):
    """(start, end) of the <a>/<button> whose OWN tag contains `frag`.
    Raises unless exactly one does."""
    hits = []
    for m in re.finditer(r'<(a|button)\b[^>]*>', scan):
        if frag not in m.group(0):
            continue
        tag = m.group(1)
        d, end = 0, None
        for x in re.finditer(r'</?%s\b' % tag, scan[m.start():]):
            d += 1 if x.group(0) == '<' + tag else -1
            if d == 0:
                end = scan.find('>', m.start() + x.end()) + 1
                break
        if end:
            hits.append((m.start(), end))
    return hits


def fix(html, classes, label, aria):
    """One control. The class becomes the house one, the visible word may
    become Back inside the span base hides on a phone, and the destination
    moves to the aria-label. The href, the onclick and every template tag
    are untouched."""
    out = re.sub(r'class="[^"]*"', 'class="%s"' % classes, html, count=1)
    if aria:
        if 'aria-label=' in out:
            out = re.sub(r'aria-label="[^"]*"', 'aria-label="%s"' % aria,
                         out, count=1)
        else:
            m = re.match(r'<(a|button)\b', out)
            out = (out[:m.end()] + ' aria-label="%s"' % aria + out[m.end():])
    if label:
        a = ARROW.search(out)
        if not a:
            raise SystemExit('H3: a control with no left arrow: %s'
                             % html[:70])
        close = out.rfind('</')
        out = (out[:a.end()]
               + '<span class="%s"> %s</span>' % (LABEL_CLS, label)
               + out[close:])
    return out


def patch(rel):
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        raise SystemExit('H3: %s is not on disk' % rel)
    text = read(path)
    before = text
    jobs = [j for j in JOBS if j[0] == rel]
    done = 0
    # back to front, so an earlier edit cannot move a later offset
    spans = []
    for _f, frag, classes, label, aria in jobs:
        # THE DISCRIMINATOR IS THE COLOUR CLASS. The bar Back that G2 fixed
        # shares its href with the done-state Back beneath it, so matching
        # on the href alone found two controls on four pages. What this
        # round is FOR is the one still wearing a Bootstrap colour - and a
        # control with none left is one already done.
        hits = [h for h in element(blanked(text), frag)
                if COLOUR.search(text[h[0]:h[1]])]
        hits = [h for h in hits
                if re.match(r'(?i)\s*back\b',
                            re.sub(r'<[^>]+>|\{[%{].*?[%}]\}', '',
                                   text[h[0]:h[1]]).strip())]
        if len(hits) != 1:
            # ALREADY APPLIED IS A PER-CONTROL QUESTION, not a per-file one.
            # Asking "does this FILE still contain a Bootstrap colour class"
            # says yes on every one of these pages, because plenty of other
            # controls on them do - so a second run raised instead of
            # reporting nothing to do.
            if len(hits) == 0 and any(
                    classes.split()[-1] in text[h[0]:h[1]]
                    for h in element(blanked(text), frag)):
                continue                                # already applied
            raise SystemExit('H3: %s - %r found %d matching control(s), '
                             'wanted 1' % (rel, frag, len(hits)))
        spans.append((hits[0], classes, label, aria))
    if not spans:
        return None
    for (s, e), classes, label, aria in sorted(spans, key=lambda x: -x[0][0]):
        text = text[:s] + fix(text[s:e], classes, label, aria) + text[e:]
        done += 1

    # --- self-checks BEFORE anything is written --------------------------
    for tag in set(re.findall(r'\{\{.*?\}\}|\{%.*?%\}', before, re.S)):
        if before.count(tag) != text.count(tag):
            raise SystemExit('H3: %s - %s appeared %d times and now %d'
                             % (rel, tag.strip()[:50], before.count(tag),
                                text.count(tag)))
    for what in ('href=', 'onclick=', '<a ', '<button'):
        if before.count(what) != text.count(what):
            raise SystemExit('H3: %s - %s went %d -> %d'
                             % (rel, what, before.count(what),
                                text.count(what)))
    for _f, frag, classes, label, aria in jobs:
        if not element(blanked(text), frag):
            raise SystemExit('H3: %s - %r vanished' % (rel, frag))
    left = sorted(set(c for m in re.finditer(r'class="([^"]*)"',
                                             blanked(text))
                      for c in m.group(1).split() if COLOUR.match(c)
                      and re.match(r'(?i)\s*back\b',
                                   '')))
    if not CHECK:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            CRLF[bak] = CRLF.get(path)
            write(bak, before)
        write(path, text)
    return done


LATER = [
    ('alv_rounds.py',
     "    '.bak_celebrations',\n]",
     "    '.bak_celebrations',\n    '.bak_bodybacks',\n]"),
    ('Push-PendingChanges.ps1',
     "    'test_celebrations.py'",
     "    'test_celebrations.py'\n    'test_body_backs.py'"),
]


def patch_later():
    done = 0
    for name, old, new in LATER:
        path = os.path.join(HERE, name)
        text = read(path)
        if new in text:
            continue
        if text.count(old) != 1:
            raise SystemExit('H3/LATER: anchor matched %d times in %s'
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
    print('SECTION H, ROUND H3 - THE BACKS THAT ARE NOT IN AN ACTION BAR '
          '- %s' % ('CHECK ONLY' if CHECK else 'APPLYING'))
    print('=' * 74)
    total = 0
    for rel in sorted(set(j[0] for j in JOBS)):
        n = patch(rel)
        if n is None:
            print('  %-38s already applied' % rel)
            continue
        print('  %-38s %d control(s)' % (rel, n))
        total += n
    later = patch_later()
    print('-' * 74)
    print('  %d control(s): %d page Backs now say "Back" with the '
          'destination\n  in the aria-label, and %d keep their words '
          'because they are not page\n  Backs. %d LATER edit(s).'
          % (total, len(PAGE_BACKS), len(KEEP_WORD), later))
    print('=' * 74)


if __name__ == '__main__':
    main()
