"""PF-1 - NINETEEN THOUSAND OPTIONS NOBODY CAN SEE.

   Demetri, 5 Oct 2026: "the Ingredients page is very sluggish."

   He noticed it just after rotating the USDA key, and the two are
   unrelated: this page makes no USDA call when it loads. Every nutrition
   figure on it comes from a stored column, and USDA is only reached when
   Search is pressed inside the mapping modal. He simply spent time on the
   page while testing the new key.

   WHAT IT ACTUALLY COSTS, measured on a replica of the same shape before
   anything was changed:

       today                941 KB   24,700 DOM nodes   18,700 options
       pickers on demand    233 KB    5,252 DOM nodes        0 options
                            390 ms                      156 ms

   and the replica carries none of the real page's tooltip CSS, modals or
   inline JSON, so the live page is worse than that.

   THE CAUSE. The Shopping Units page renders 374 rows, and every row
   carries two complete <select> elements as its inline-edit controls: one
   listing all 19 ingredient categories, one listing all 31 measurement
   units. 374 x 50 = 18,700 <option> elements. All of them are hidden
   behind `.edit-mode` until that row's Edit is pressed, and only one row
   is ever edited at a time.

   The same shape is on the Families page: an "Add an ingredient" picker
   per family, each listing all 374 ingredients.

   THE FIX CHANGES NO BEHAVIOUR. The options are rendered ONCE into a
   <template>, the row selects ship empty, and the first time a select is
   needed its options are cloned in. Same options, same order, same values,
   same form submission - the browser simply stops building them up front.

   WHERE THE SELECTED VALUE COMES FROM NOW. The per-row options carried
   `selected` on the matching one. A shared template cannot, so after
   filling, the select's value is set from `data-original-value` - which
   every one of these already carries, because cancelEdit has always used
   it to put the row back. Nothing new had to be added to the markup to
   make this work; the information was already there.

   TWO TRIGGERS, because the two pages differ:

     Shopping Units  - enterEditMode(), which is the single entry point
                       for a row going editable, and already exists.
     Families        - first focus on the picker, because that select is
                       visible from the start rather than behind an Edit.
                       Filling on focus is indistinguishable from being
                       full: the options come from a template already in
                       the document, so there is no fetch and no wait.

   WHAT IS DELIBERATELY NOT TOUCHED. fsr_details.html and tenant_edit.html
   have the same shape with a handful of properties in a short loop. The
   gain would be invisible and it is two more pages to re-test. And the
   374 rows stay: the page's live search filters them client-side, so
   paginating would make the page lighter and the SEARCH slower, which is
   the wrong trade. Demetri: "Keep all 374 and the live search".

   FILES: ingredient_base_units_management.html, ingredient_families.html.
                                                  [test_picker_lazy.py]
"""
import os
import re
import sys

import alv_tree as T

SUFFIX = '.bak_pickerlazy'

UNITS_PAGE = 'ingredient_base_units_management.html'
FAMILIES_PAGE = 'ingredient_families.html'


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def backup(path):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def fit(text, block):
    return block.replace('\n', '\r\n') if '\r\n' in text else block


def page(name):
    hits = [p for p in T.templates() if T.rel(p) == name]
    if len(hits) != 1:
        raise SystemExit('PF-1: %s matched %d templates' % (name, len(hits)))
    return hits[0]


def one(pattern, text, what):
    """The single match, or a refusal. A round that edits the second of
    two look-alike blocks is worse than one that does nothing."""
    found = list(re.finditer(pattern, text, re.S))
    if len(found) != 1:
        raise SystemExit('PF-1: %s matched %d times, expected 1'
                         % (what, len(found)))
    return found[0]


# ------------------------------------------------------- the units page

UNITS_TEMPLATES = '''
<!-- PF-1, 5 Oct 2026 - the pickers, rendered ONCE.
     These used to be rendered inside every one of the 374 rows: 19
     category options and 31 unit options each, 18,700 <option> elements
     in all, every one of them hidden behind .edit-mode until that row's
     Edit was pressed. Measured at 941 KB and 24,700 DOM nodes.
     enterEditMode() clones them into a row the first time it needs them.
     The row's `selected` option is restored from data-original-value,
     which cancelEdit has always relied on. -->
<template id="categoryOptionsTpl"><option value="">-- Select Category --</option>{% for cat in categories %}<option value="{{ cat.ingredient_category_id }}">{{ cat.name }}</option>{% endfor %}</template>
<template id="unitOptionsTpl"><option value="">-- Select Unit --</option>{% for unit in all_units %}<option value="{{ unit.measurement_unit_id }}">{{ unit.name }}</option>{% endfor %}</template>
'''

UNITS_JS_OLD = '''function enterEditMode(ingredientId) {
    const row = document.getElementById(`ingredient-row-${ingredientId}`);
    row.classList.add('edit-mode');
}'''

UNITS_JS_NEW = '''// PF-1, 5 Oct 2026 - fill the row's pickers the first time it is edited.
//
// They used to be rendered into all 374 rows up front: 18,700 <option>
// elements that nobody could see until this function ran, and only ever
// for one row at a time. The options now live in two <template> elements
// at the end of the page and are cloned in here.
//
// The value is restored from data-original-value rather than from a
// `selected` attribute, because a shared template cannot carry one. That
// attribute was already on every select - cancelEdit has always used it.
function fillPicker(select, templateId) {
    if (!select || select.options.length) return;      // already filled
    const tpl = document.getElementById(templateId);
    if (!tpl) return;                                  // nothing to fill from
    select.appendChild(tpl.content.cloneNode(true));
    select.value = select.dataset.originalValue || '';
}

function enterEditMode(ingredientId) {
    const row = document.getElementById(`ingredient-row-${ingredientId}`);
    fillPicker(row.querySelector('.category-edit'), 'categoryOptionsTpl');
    fillPicker(row.querySelector('.unit-edit'), 'unitOptionsTpl');
    row.classList.add('edit-mode');
}'''


def do_units(check):
    path = page(UNITS_PAGE)
    text = read(path)
    done = 0

    # 1. the category select loses its option list
    m = one(r'(<select class="category-edit category-input"[^>]*>)'
            r'.*?(</select>)', text, 'the category select')
    if '{% for cat in categories %}' in m.group(0):
        text = text[:m.start()] + m.group(1) + m.group(2) + text[m.end():]
        done += 1

    # 2. and so does the unit select
    m = one(r'(<select class="unit-edit unit-select"[^>]*>).*?(</select>)',
            text, 'the unit select')
    if '{% for unit in all_units %}' in m.group(0):
        text = text[:m.start()] + m.group(1) + m.group(2) + text[m.end():]
        done += 1

    # 3. the templates go in once, beside the shared tooltip element that
    #    is already there for the same reason - one of a thing, not 374.
    anchor = '<div class="row-tooltip" id="rowTooltip"></div>'
    if 'id="categoryOptionsTpl"' not in text:
        a = fit(text, anchor)
        n = text.count(a)
        if n != 1:
            raise SystemExit('PF-1: the tooltip anchor appears %d times' % n)
        text = text.replace(a, a + fit(text, UNITS_TEMPLATES), 1)
        done += 1

    # 4. enterEditMode fills them
    old, new = fit(text, UNITS_JS_OLD), fit(text, UNITS_JS_NEW)
    if new not in text:
        n = text.count(old)
        if n != 1:
            raise SystemExit('PF-1: enterEditMode matched %d times' % n)
        text = text.replace(old, new, 1)
        done += 1

    if done and not check:
        backup(path)
        write(path, text)
    return done


# ---------------------------------------------------- the families page

FAM_TEMPLATE = '''
<!-- PF-1, 5 Oct 2026 - the ingredient picker, rendered ONCE.
     It used to be rendered inside every family card, each copy listing
     all 374 ingredients. Filled on first focus, which is
     indistinguishable from being full: the options are already in the
     document, so there is no fetch and no wait. -->
<template id="familyIngredientOptionsTpl">{% for ing in all_ingredients %}<option value="{{ ing.ingredient_id }}">{{ ing.name }}{% if ing.family %} (currently in: {{ ing.family.name }}){% endif %}</option>{% endfor %}</template>
<script>
(function () {
    // One listener, on the document, rather than one per family card -
    // the same reasoning as the templates themselves.
    document.addEventListener('focusin', function (e) {
        var sel = e.target;
        if (!sel.classList || !sel.classList.contains('family-add-picker')) return;
        if (sel.dataset.filled) return;
        var tpl = document.getElementById('familyIngredientOptionsTpl');
        if (!tpl) return;
        sel.appendChild(tpl.content.cloneNode(true));
        sel.dataset.filled = '1';
    });
})();
</script>
'''


def do_families(check):
    path = page(FAMILIES_PAGE)
    text = read(path)
    done = 0

    m = one(r'(<select name="ingredient_id" class="form-control form-control-sm '
            r'family-add-picker" required>).*?(</select>)',
            text, 'the family ingredient picker')
    if '{% for ing in all_ingredients %}' in m.group(0):
        keep = ('<option value="">&mdash; Add an ingredient &mdash;</option>')
        text = (text[:m.start()] + m.group(1) + keep + m.group(2)
                + text[m.end():])
        done += 1

    if 'id="familyIngredientOptionsTpl"' not in text:
        m2 = re.search(r'\{%\s*endblock\s*%\}\s*$', text)
        if not m2:
            raise SystemExit('PF-1: ingredient_families.html has no closing '
                             'endblock to put the template before')
        text = text[:m2.start()] + fit(text, FAM_TEMPLATE) + text[m2.start():]
        done += 1

    if done and not check:
        backup(path)
        write(path, text)
    return done


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    units = do_units(check)
    fams = do_families(check)

    print('PF-1  Shopping Units edits : %d' % units)
    print('PF-1  Families edits       : %d' % fams)

    if check:
        if units or fams:
            print('PF-1  NOT APPLIED')
            return 1
        print('PF-1  applied')
        return 0
    if units not in (0, 4) or fams not in (0, 2):
        print('PF-1  REFUSED: partial application (units %d/4, families %d/2)'
              % (units, fams))
        return 2
    print('PF-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
