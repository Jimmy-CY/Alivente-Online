#!/usr/bin/env python3
"""
apply_inactive_guard.py
=======================

Two screens disagreed about which properties exist, and money fell through
the gap.

    finance_pl_act        props.objects.filter(prop_status="Active")
    pro-rata selector     props.objects.all()

So a pro-rata distribution could allocate a real share to a property the P&L
never draws. Found in use: Dikaiosynis (Inactive) was added to Company Tax and
took 20.7% of the charge - EUR 1,448.90 of EUR 7,000 - which then appeared in
no year of the report. The line read 5,551.12 instead of 7,000 and nothing
anywhere said why. The freed share is not redistributed; it simply vanishes.

Three changes
-------------
1. THE SELECTOR now distinguishes two cases, because they need different
   answers:

     inactive, NOT in the distribution  ->  disabled, badged "Inactive",
                                            cannot be ticked
     inactive, ALREADY in it            ->  ticked and enabled, badged
                                            "Inactive - remove", plus a
                                            warning above the list

   The second has to stay tickable: disabling it would make it impossible to
   un-tick, which is exactly the fix. And it stays TICKED, so nothing is
   dropped silently during an unrelated edit - the person removes it
   deliberately, with an effective date, and the others take up its share.

   The JS is taught the difference too. Without that the guard is decoration:
   the country filter mass-ticks every checkbox including disabled ones, and
   `:checked` matches a disabled box perfectly happily.

2. DEACTIVATING A PROPERTY is refused while it still holds pro-rata shares.
   The message names each line type and what it currently allocates. Fix the
   distributions first - on the screen that has the "Applies from" field,
   which a property-status form has no business asking for - then set it
   inactive.

   The reason is the DISTRIBUTION, not the reporting. Since the P&L stopped
   filtering on status, an inactive property keeps its historical years just
   fine. What breaks is the split: the remaining properties would hold shares
   computed for a set that still included this one, so the line stops adding
   up to the charge owed - and the sold property keeps being charged forward.

   Deliberately narrow: only PRO-RATA rows block. An ordinary expense on a
   sold property simply stops being reported, which is fine. A pro-rata row
   leaves the other properties holding shares of a split that no longer adds
   up, which is not.

3. The check reads the OLD status from the database rather than from the bound
   instance. `PropForm(request.POST, instance=prop)` mutates `prop` during
   validation, so by the time `is_valid()` returns, `prop.prop_status` is
   already the new value. (The duplicate-name check just above has the same
   flaw and never fires - left alone here, but worth knowing.)

Files touched
-------------
  pages/views/properties.py                     + _prorata_blockers, the guard
  pages/templates/finance_expense_add.html      selector + JS
  pages/templates/finance_expense_edit.html     selector + JS + warning

Idempotent; backs each file up on first run (.bak_inactive).

    python apply_inactive_guard.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))

PROPS = os.path.join(ROOT, 'pages', 'views', 'properties.py')
TPL = os.path.join(ROOT, 'pages', 'templates')
ADD = os.path.join(TPL, 'finance_expense_add.html')
EDIT = os.path.join(TPL, 'finance_expense_edit.html')

PROPS_SENTINEL = 'def _prorata_blockers'
ADD_SENTINEL = 'is-inactive'
EDIT_SENTINEL = 'is-inactive'


# ---------------------------------------------------------------------------
# 1. properties.py - refuse to deactivate while pro-rata shares remain
# ---------------------------------------------------------------------------

PROPS_ANCHOR = '''@login_required
@permission_required('auth.can_edit_properties', raise_exception=True)
def properties_edit_commit(request, prop_id):
    prop = get_object_or_404(props, pk=prop_id)
    existing_names = props.objects.exclude(prop_id=prop_id).values_list('prop_name', flat=True)

    if request.method == "POST":
        form = PropForm(request.POST, instance=prop)

        if form.is_valid():
'''

PROPS_NEW = '''def _prorata_blockers(prop_id):
    """Pro-rata expense rows on this property, as (line type, yearly amount).

    A pro-rata row is a SHARE of the amount held on its line type. Deactivate
    the property and the P&L stops drawing it - the other properties keep
    shares computed for a split that included this one, so the line quietly
    stops adding up to the charge actually owed.

    Ordinary expenses are deliberately NOT counted. One on a sold property
    just stops being reported, which is correct. Only a distribution breaks.
    """
    from pages.models import expense

    _months = ('jan', 'feb', 'mar', 'apr', 'may', 'jun',
               'jul', 'aug', 'sep', 'oct', 'nov', 'dec')
    out = []
    rows = (expense.objects.select_related('expense_line_types')
            .filter(prop_id=prop_id))
    for row in rows:
        lt = row.expense_line_types
        flag = (getattr(lt, 'expense_line_types_prorata', '') or '').strip().lower()
        if flag != 'yes':
            continue
        total = 0
        for m in _months:
            v = getattr(row, 'expense_' + m, None)
            if v:
                total += float(v)
        if total:
            out.append((str(lt), total))
    out.sort(key=lambda t: -t[1])
    return out


@login_required
@permission_required('auth.can_edit_properties', raise_exception=True)
def properties_edit_commit(request, prop_id):
    prop = get_object_or_404(props, pk=prop_id)
    existing_names = props.objects.exclude(prop_id=prop_id).values_list('prop_name', flat=True)

    # Read the CURRENT status straight from the database, before the form
    # touches anything. PropForm(request.POST, instance=prop) mutates `prop`
    # during is_valid(), so afterwards prop.prop_status is already the new
    # value and comparing the two would always say "unchanged".
    _old_status = (props.objects.filter(pk=prop_id)
                   .values_list('prop_status', flat=True).first())

    if request.method == "POST":
        form = PropForm(request.POST, instance=prop)

        if form.is_valid():
            _new_status = form.cleaned_data.get('prop_status')
            if _old_status == 'Active' and _new_status != 'Active':
                _blockers = _prorata_blockers(prop_id)
                if _blockers:
                    _detail = ', '.join('%s %.2f' % (n, a) for n, a in _blockers)
                    messages.error(
                        request,
                        "This property cannot be set to %s yet: it still holds "
                        "a share of %d pro-rata distribution(s) \\u2014 %s. Those "
                        "shares would carry on being charged to it in every "
                        "future year, while the other properties kept shares of "
                        "a split that still counted it \\u2014 so the line would "
                        "stop adding up to the charge actually owed. Open "
                        "Financial Management > Expenses, edit each of those "
                        "lines, set \\u201cApplies from\\u201d to the date this "
                        "property leaves, and un-tick it: the others take up its "
                        "share, and this one stops from that date while keeping "
                        "its earlier years. Then come back and set it %s."
                        % (_new_status, len(_blockers), _detail, _new_status))
                    return render(request, "properties_edit.html", {
                        'props': [props.objects.get(pk=prop_id)],
                        'existing_names': list(existing_names)
                    })

'''


# ---------------------------------------------------------------------------
# 2. shared CSS + the two selector states
# ---------------------------------------------------------------------------

PILL_CSS = '''
/* Inactive properties in a pro-rata list. The P&L draws Active properties
   only, so a share allocated to an inactive one is money the report never
   shows. Two states, deliberately different:
     .is-inactive         not in the distribution - cannot be added
     .is-inactive-linked  already in it - must stay tickable, so it can be
                          removed, and stays TICKED so nothing is dropped
                          silently during an unrelated edit */
.property-item.inactive-row { background: #fbfbfc; }
.property-item.inactive-row label > span:first-child { color: #868e96; }
.inactive-pill {
    display: inline-block;
    margin-left: 8px;
    padding: 1px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 700;
    background: #e9ecef;
    color: #6c757d;
}
.inactive-pill.needs-removal { background: #f8d7da; color: #a71d2a; }
.prorata-inactive-warning {
    background: #fff3cd;
    border-left: 4px solid #ffc107;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 12px;
    font-size: 13px;
    color: #6c5400;
}
'''

CSS_ANCHOR = '.checkbox-list {\n    background: white;\n'

# --- ADD form: nothing is ever pre-linked, so one state only ---------------

ADD_ROW_OLD = '''                    <div class="property-item" data-country="{{ prop.prop_country }}" data-prop-name="{{ prop.prop_name }}">
                        <input class="property-checkbox" 
                               type="checkbox" 
                               id="prop_{{ prop.prop_id }}" 
                               value="{{ prop.prop_id }}"
                               data-current-value="{{ prop.current_value|default:0 }}">
                        <label for="prop_{{ prop.prop_id }}">
                            <span>{{ prop.prop_name }}<span class="anchor-pill" style="display:none;">Anchor</span></span>
'''

ADD_ROW_NEW = '''                    <div class="property-item{% if prop.prop_status != 'Active' %} inactive-row{% endif %}" data-country="{{ prop.prop_country }}" data-prop-name="{{ prop.prop_name }}">
                        <input class="property-checkbox{% if prop.prop_status != 'Active' %} is-inactive{% endif %}"
                               type="checkbox"
                               id="prop_{{ prop.prop_id }}"
                               value="{{ prop.prop_id }}"
                               data-current-value="{{ prop.current_value|default:0 }}"
                               {% if prop.prop_status != 'Active' %}disabled title="Inactive - the P&amp;L does not report this property, so it cannot take a share"{% endif %}>
                        <label for="prop_{{ prop.prop_id }}">
                            <span>{{ prop.prop_name }}<span class="anchor-pill" style="display:none;">Anchor</span>{% if prop.prop_status != 'Active' %}<span class="inactive-pill">Inactive</span>{% endif %}</span>
'''

# --- EDIT form: two states ------------------------------------------------

EDIT_ROW_OLD = '''                    <div class="property-item {% if prop.prop_id == existing_expense.prop_id %}is-anchor{% endif %}" data-country="{{ prop.prop_country }}" data-prop-name="{{ prop.prop_name }}">
                        <input class="property-checkbox" 
                               type="checkbox" 
                               id="prop_{{ prop.prop_id }}" 
                               value="{{ prop.prop_id }}"
                               data-current-value="{{ prop.current_value|default:0 }}"
                               {% if prop.prop_id in linked_property_ids %}checked{% endif %}
                               {% if prop.prop_id == existing_expense.prop_id %}disabled{% endif %}>
                        <label for="prop_{{ prop.prop_id }}">
                            <span>{{ prop.prop_name }}{% if prop.prop_id == existing_expense.prop_id %}<span class="anchor-pill">Anchor</span>{% else %}<span class="anchor-pill" style="display:none;">Anchor</span>{% endif %}</span>
'''

EDIT_ROW_NEW = '''                    <div class="property-item {% if prop.prop_id == existing_expense.prop_id %}is-anchor{% endif %}{% if prop.prop_status != 'Active' %} inactive-row{% endif %}" data-country="{{ prop.prop_country }}" data-prop-name="{{ prop.prop_name }}">
                        <input class="property-checkbox{% if prop.prop_status != 'Active' and prop.prop_id not in linked_property_ids %} is-inactive{% endif %}{% if prop.prop_status != 'Active' and prop.prop_id in linked_property_ids %} is-inactive-linked{% endif %}"
                               type="checkbox"
                               id="prop_{{ prop.prop_id }}"
                               value="{{ prop.prop_id }}"
                               data-current-value="{{ prop.current_value|default:0 }}"
                               {% if prop.prop_id in linked_property_ids %}checked{% endif %}
                               {% if prop.prop_id == existing_expense.prop_id %}disabled{% endif %}
                               {% if prop.prop_status != 'Active' and prop.prop_id not in linked_property_ids %}disabled title="Inactive - the P&amp;L does not report this property, so it cannot take a share"{% endif %}
                               {% if prop.prop_status != 'Active' and prop.prop_id in linked_property_ids %}title="Inactive, but still in this distribution - un-tick it so the others take up its share"{% endif %}>
                        <label for="prop_{{ prop.prop_id }}">
                            <span>{{ prop.prop_name }}{% if prop.prop_id == existing_expense.prop_id %}<span class="anchor-pill">Anchor</span>{% else %}<span class="anchor-pill" style="display:none;">Anchor</span>{% endif %}{% if prop.prop_status != 'Active' %}<span class="inactive-pill{% if prop.prop_id in linked_property_ids %} needs-removal{% endif %}">{% if prop.prop_id in linked_property_ids %}Inactive &mdash; remove{% else %}Inactive{% endif %}</span>{% endif %}</span>
'''

# --- the warning banner, edit form only -----------------------------------

BANNER_ANCHOR = '''                <div class="checkbox-list">
'''

BANNER_NEW = '''                <div class="prorata-inactive-warning" id="prorata-inactive-warning" style="display:none;">
                  <i class="fas fa-exclamation-triangle"></i>
                  <strong>An inactive property is still in this distribution.</strong>
                  The P&amp;L only reports Active properties, so its share is money the
                  report never shows &mdash; and the others are holding shares of a split
                  that still counts it. Set <em>Applies from</em> above, un-tick it, and
                  recalculate: the remaining properties will take up its share.
                </div>
                <div class="checkbox-list">
'''


# ---------------------------------------------------------------------------
# 3. the JS - a disabled checkbox is still checkable from script
# ---------------------------------------------------------------------------

JS_ALL_OLD = "            $('.property-checkbox').prop('checked', true);\n"
JS_ALL_NEW = ("            // .is-inactive can never be ticked, not even by 'all'.\n"
              "            $('.property-checkbox').not('.is-inactive').prop('checked', true);\n")

JS_EACH_OLD = """                if (itemCountry === selectedCountry || isMainProperty) {
                    $(this).show();
                    checkbox.prop('checked', true);
"""
JS_EACH_NEW = """                if (itemCountry === selectedCountry || isMainProperty) {
                    $(this).show();
                    if (!checkbox.hasClass('is-inactive')) {
                        checkbox.prop('checked', true);
                    }
"""

JS_DISABLED_OLD = """    $(document).on('change', '.property-checkbox', function() {
        if ($(this).prop('disabled')) {
            $(this).prop('checked', true);
        }
    });
"""
JS_DISABLED_NEW = """    $(document).on('change', '.property-checkbox', function() {
        // Re-assert the ANCHOR only. An inactive row is disabled for the
        // opposite reason - it must never end up ticked.
        if ($(this).prop('disabled') && !$(this).hasClass('is-inactive')) {
            $(this).prop('checked', true);
        }
    });
"""

JS_SELECTED_OLD = "        const selectedCheckboxes = $('.property-checkbox:checked');\n"
JS_SELECTED_NEW = ("        // :checked matches a disabled box perfectly happily, so the\n"
                   "        // inactive ones have to be excluded explicitly.\n"
                   "        const selectedCheckboxes = "
                   "$('.property-checkbox:checked').not('.is-inactive');\n")

JS_WARNING = """
    // Show the banner only when an inactive property is actually still in
    // this distribution, and hide it again the moment it is un-ticked.
    function syncInactiveWarning() {
        var banner = document.getElementById('prorata-inactive-warning');
        if (!banner) { return; }
        var still = $('.property-checkbox.is-inactive-linked:checked').length;
        banner.style.display = still ? '' : 'none';
    }
    $(document).on('change', '.property-checkbox', syncInactiveWarning);
    syncInactiveWarning();
"""

JS_WARNING_ANCHOR = """    $(document).on('change', '.property-checkbox', function() {
        // Re-assert the ANCHOR only. An inactive row is disabled for the
        // opposite reason - it must never end up ticked.
        if ($(this).prop('disabled') && !$(this).hasClass('is-inactive')) {
            $(this).prop('checked', true);
        }
    });
"""


# ---------------------------------------------------------------------------

def sniff(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return raw.decode(enc).replace('\r\n', '\n'), enc, nl


def write_back(path, text, enc, nl):
    bak = path + '.bak_inactive'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    with open(path, 'w', encoding=enc, newline='') as fh:
        fh.write(text.replace('\n', nl) if nl == '\r\n' else text)


def main():
    for p in (PROPS, ADD, EDIT):
        if not os.path.exists(p):
            print('! %s not found - run from the project root'
                  % os.path.relpath(p, ROOT))
            return 1

    props_src, props_enc, props_nl = sniff(PROPS)
    add_src, add_enc, add_nl = sniff(ADD)
    edit_src, edit_enc, edit_nl = sniff(EDIT)

    props_done = PROPS_SENTINEL in props_src
    add_done = ADD_SENTINEL in add_src
    edit_done = EDIT_SENTINEL in edit_src

    if props_done and add_done and edit_done:
        print('= already applied - nothing to do')
        return 0

    problems = []

    def need(label, src, anchor, times=1):
        n = src.count(anchor)
        if n != times:
            problems.append('%s: matched %d times, expected %d' % (label, n, times))

    if not props_done:
        need('properties_edit_commit', props_src, PROPS_ANCHOR)
    if not add_done:
        need('add form checkbox-list css', add_src, CSS_ANCHOR)
        need('add form property row', add_src, ADD_ROW_OLD)
        need('add form select-all', add_src, JS_ALL_OLD)
        need('add form country each', add_src, JS_EACH_OLD)
        need('add form disabled handler', add_src, JS_DISABLED_OLD)
        need('add form selection', add_src, JS_SELECTED_OLD)
    if not edit_done:
        need('edit form checkbox-list css', edit_src, CSS_ANCHOR)
        need('edit form property row', edit_src, EDIT_ROW_OLD)
        need('edit form checkbox-list markup', edit_src, BANNER_ANCHOR)
        need('edit form select-all', edit_src, JS_ALL_OLD)
        need('edit form country each', edit_src, JS_EACH_OLD)
        need('edit form disabled handler', edit_src, JS_DISABLED_OLD)
        need('edit form selection', edit_src, JS_SELECTED_OLD)

    if problems:
        for p in problems:
            print('! ' + p)
        print('  Aborting - nothing written.')
        return 1

    if not props_done:
        props_src = props_src.replace(PROPS_ANCHOR, PROPS_NEW, 1)

    if not add_done:
        add_src = add_src.replace(CSS_ANCHOR, PILL_CSS + CSS_ANCHOR, 1)
        add_src = add_src.replace(ADD_ROW_OLD, ADD_ROW_NEW, 1)
        add_src = add_src.replace(JS_ALL_OLD, JS_ALL_NEW, 1)
        add_src = add_src.replace(JS_EACH_OLD, JS_EACH_NEW, 1)
        add_src = add_src.replace(JS_DISABLED_OLD, JS_DISABLED_NEW, 1)
        add_src = add_src.replace(JS_SELECTED_OLD, JS_SELECTED_NEW, 1)

    if not edit_done:
        edit_src = edit_src.replace(CSS_ANCHOR, PILL_CSS + CSS_ANCHOR, 1)
        edit_src = edit_src.replace(EDIT_ROW_OLD, EDIT_ROW_NEW, 1)
        edit_src = edit_src.replace(BANNER_ANCHOR, BANNER_NEW, 1)
        edit_src = edit_src.replace(JS_ALL_OLD, JS_ALL_NEW, 1)
        edit_src = edit_src.replace(JS_EACH_OLD, JS_EACH_NEW, 1)
        edit_src = edit_src.replace(JS_DISABLED_OLD, JS_DISABLED_NEW, 1)
        edit_src = edit_src.replace(JS_SELECTED_OLD, JS_SELECTED_NEW, 1)
        edit_src = edit_src.replace(JS_WARNING_ANCHOR,
                                    JS_WARNING_ANCHOR + JS_WARNING, 1)

    try:
        compile(props_src, 'properties.py', 'exec')
    except SyntaxError as exc:
        print('! patched properties.py does not compile: %s (line %s)'
              % (exc.msg, exc.lineno))
        print('  Nothing written.')
        return 1

    if CHECK:
        print('= check only: every anchor matched and properties.py compiles, '
              'nothing written')
        return 0

    if not props_done:
        write_back(PROPS, props_src, props_enc, props_nl)
        print('+ pages/views/properties.py     deactivation blocked while '
              'pro-rata shares remain')
    if not add_done:
        write_back(ADD, add_src, add_enc, add_nl)
        print('+ pages/templates/finance_expense_add.html    inactive cannot be ticked')
    if not edit_done:
        write_back(EDIT, edit_src, edit_enc, edit_nl)
        print('+ pages/templates/finance_expense_edit.html   inactive flagged, '
              'linked ones removable')

    print('')
    print('Backups: .bak_inactive alongside each file. No migration needed.')
    print('Verify:  python test_inactive_guard.py')
    print('         python manage.py check')
    return 0


if __name__ == '__main__':
    sys.exit(main())
