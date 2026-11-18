# -*- coding: utf-8 -*-
"""apply_recipe_units_null.py - round RU-1, 18 Nov 2026.

RELEASE 99 - RECIPES: ADDING A MEASUREMENT WORKS AGAIN.

    Demetri, 18 Nov: "I can't seem to add a measurement in recipes" - the
    Add measurement box said Error: 'NoneType' object has no attribute
    'strip'.

    Two faults, one after the other:
    1. With Abbreviation (or a plural) left blank, the views saved None.
       Since migration 0095 (N1, 30 Sep) those columns are NOT NULL, so
       MySQL refused the row. Blank is now stored as '' - in the Add
       measurement box on the recipe import page, and on the Measurement
       Units page's Add and Edit.
    2. The failed try then cleared the remembered name while the box
       stayed open, so the next Add sent no name, and the server called
       .strip() on None. The box now reads the name from itself and keeps
       it until it succeeds; the server reads every field null-safe and
       answers a missing name in a sentence. The Add ingredient box gets
       the same retry fix.

    Also: the phone Travel help says the app fetches its new look by
    itself after an update (promised on 17 Nov).

The suite ships beside this patcher. Stands on CY-5 (apply_cycle_look.py).
Idempotent. Edits backed up to .bak_units1. No migration.
"""
import os
import sys

SUFFIX = '.bak_units1'
MARK = 'RU-1, 18 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_recipe_units_null.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_quotes.py',
    # CY-5, 17 Nov 2026 - Release 98: the Cycle Tracker redesign.
    'test_cycle_look.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_quotes.py',
    # CY-5, 17 Nov 2026 - Release 98: the Cycle Tracker redesign.
    'test_cycle_look.py',
    # RU-1, 18 Nov 2026 - Release 99: adding a measurement works again.
    'test_recipe_units_null.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # CY-5, 17 Nov 2026 - Release 98: the Cycle Tracker redesign.
    '.bak_cyclelook',
]

''',
         r'''    # CY-5, 17 Nov 2026 - Release 98: the Cycle Tracker redesign.
    '.bak_cyclelook',
    # RU-1, 18 Nov 2026 - Release 99: adding a measurement works again.
    '.bak_units1',
]

'''),
    ]),
    (os.path.join('pages', 'templates', 'preview_imported_recipe.html'), [
        (r'''
function confirmAddMeasurement() {
    const name = pendingMeasurementName;
    const namePlural = document.getElementById('newMeasurementNamePlural').value.trim();
    const abbreviation = document.getElementById('newMeasurementAbbr').value.trim();
''',
         r'''
function confirmAddMeasurement() {
    // RU-1, 18 Nov 2026 - the name is read from the box itself (it is
    // read-only and was filled when the box opened), so it is there on a
    // second try too. Before, a failed try cleared the remembered name,
    // the box stayed open, and pressing Add again sent no name at all -
    // "Error: 'NoneType' object has no attribute 'strip'".
    const name = (document.getElementById('newMeasurementName').value || pendingMeasurementName || '').trim();
    const namePlural = document.getElementById('newMeasurementNamePlural').value.trim();
    const abbreviation = document.getElementById('newMeasurementAbbr').value.trim();
'''),
        (r'''    .then(data => {
        if (data.success) {
            existingMeasurements.push(name);
            existingMeasurements.sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
''',
         r'''    .then(data => {
        if (data.success) {
            pendingMeasurementInput = null;
            pendingMeasurementName = null;
            existingMeasurements.push(name);
            existingMeasurements.sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
'''),
        (r'''    })
    .finally(() => {
        // Re-enable button
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = '<i class="fas fa-check"></i> Add Measurement';
        
        // Clear pending context
        pendingMeasurementInput = null;
        pendingMeasurementName = null;
    });
}
''',
         r'''    })
    .finally(() => {
        // Re-enable button. RU-1 - the context is cleared only after a
        // success, so the box can be corrected and Add pressed again.
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = '<i class="fas fa-check"></i> Add Measurement';
    });
}
'''),
        (r'''
function confirmAddIngredient() {
    const name = pendingIngredientName;
    const categoryId = document.getElementById('newIngredientCategory').value;
    const shoppingUnitId = document.getElementById('newIngredientShoppingUnit').value;
''',
         r'''
function confirmAddIngredient() {
    // RU-1, 18 Nov 2026 - as for measurements: the name comes from the box.
    const name = (document.getElementById('newIngredientName').value || pendingIngredientName || '').trim();
    const categoryId = document.getElementById('newIngredientCategory').value;
    const shoppingUnitId = document.getElementById('newIngredientShoppingUnit').value;
'''),
        (r'''    .then(data => {
        if (data.success) {
            existingIngredients.push(name);
            existingIngredients.sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
''',
         r'''    .then(data => {
        if (data.success) {
            pendingIngredientInput = null;
            pendingIngredientName = null;
            existingIngredients.push(name);
            existingIngredients.sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
'''),
        (r'''    })
    .finally(() => {
        // Re-enable button
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = '<i class="fas fa-check"></i> Add Ingredient';
        
        // Clear pending context
        pendingIngredientInput = null;
        pendingIngredientName = null;
    });
}
''',
         r'''    })
    .finally(() => {
        // Re-enable button. RU-1 - the context is cleared only after a
        // success, so Add can be pressed again after an error.
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = '<i class="fas fa-check"></i> Add Ingredient';
    });
}
'''),
    ]),
    (os.path.join('pages', 'views', 'recipes', 'units.py'), [
        (r'''    if request.method == 'POST':
        data = json.loads(request.body)
        unit_name = data.get('name', '').strip()
        name_plural = data.get('name_plural', '').strip()
        abbreviation = data.get('abbreviation', '').strip()
        abbreviation_plural = data.get('abbreviation_plural', '').strip()
        unit_type = data.get('unit_type', 'other')

''',
         r'''    if request.method == 'POST':
        data = json.loads(request.body)
        # RU-1, 18 Nov 2026 - null-safe, as in add_measurement_ajax.
        unit_name = (data.get('name') or '').strip()
        name_plural = (data.get('name_plural') or '').strip()
        abbreviation = (data.get('abbreviation') or '').strip()
        abbreviation_plural = (data.get('abbreviation_plural') or '').strip()
        unit_type = data.get('unit_type', 'other')

'''),
        (r'''        unit = MeasurementUnit.objects.create(
            name=unit_name,
            name_plural=name_plural if name_plural else None,
            abbreviation=abbreviation if abbreviation else None,
            abbreviation_plural=abbreviation_plural if abbreviation_plural else None,
            unit_type=unit_type
        )
''',
         r'''        unit = MeasurementUnit.objects.create(
            name=unit_name,
            name_plural=name_plural,
            abbreviation=abbreviation,
            abbreviation_plural=abbreviation_plural,
            unit_type=unit_type
        )
'''),
        (r'''        data = json.loads(request.body)
        unit_id = data.get('unit_id')
        new_name = data.get('name', '').strip()
        new_name_plural = data.get('name_plural', '').strip()
        new_abbreviation = data.get('abbreviation', '').strip()
        new_abbreviation_plural = data.get('abbreviation_plural', '').strip()
        new_unit_type = data.get('unit_type', 'other')

''',
         r'''        data = json.loads(request.body)
        unit_id = data.get('unit_id')
        # RU-1, 18 Nov 2026 - null-safe, as in add_measurement_ajax.
        new_name = (data.get('name') or '').strip()
        new_name_plural = (data.get('name_plural') or '').strip()
        new_abbreviation = (data.get('abbreviation') or '').strip()
        new_abbreviation_plural = (data.get('abbreviation_plural') or '').strip()
        new_unit_type = data.get('unit_type', 'other')

'''),
        (r'''            # Update unit with plural fields
            unit.name = new_name
            unit.name_plural = new_name_plural if new_name_plural else None
            unit.abbreviation = new_abbreviation if new_abbreviation else None
            unit.abbreviation_plural = new_abbreviation_plural if new_abbreviation_plural else None
            unit.unit_type = new_unit_type
            unit.save()
''',
         r'''            # Update unit with plural fields
            unit.name = new_name
            unit.name_plural = new_name_plural
            unit.abbreviation = new_abbreviation
            unit.abbreviation_plural = new_abbreviation_plural
            unit.unit_type = new_unit_type
            unit.save()
'''),
        (r'''@require_POST
def add_measurement_ajax(request):
    """Add new measurement unit via AJAX (inline from recipe forms)."""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        name_plural = data.get('name_plural', '').strip()
        abbreviation = data.get('abbreviation', '').strip()
        abbreviation_plural = data.get('abbreviation_plural', '').strip()
        unit_type = data.get('unit_type', 'other')

        if not name:
            return JsonResponse({'success': False, 'message': 'Name is required'})

        # Check if already exists
''',
         r'''@require_POST
def add_measurement_ajax(request):
    """Add new measurement unit via AJAX (inline from recipe forms).

    RU-1, 18 Nov 2026 - Demetri: "I can't seem to add a measurement in
    recipes" (Error: 'NoneType' object has no attribute 'strip'). A field
    sent as null came back from data.get(key, '') as None, and .strip()
    on None is that error. Every field is now read with (value or ''), an
    unknown unit type falls back to 'other', and a missing name gets a
    plain sentence instead of a Python error.
    """
    try:
        data = json.loads(request.body)

        def text(key):
            return str(data.get(key) or '').strip()
        name = text('name')
        name_plural = text('name_plural')
        abbreviation = text('abbreviation')
        abbreviation_plural = text('abbreviation_plural')
        unit_type = text('unit_type') or 'other'
        if unit_type not in dict(MeasurementUnit.UNIT_TYPE_CHOICES):
            unit_type = 'other'

        if not name:
            return JsonResponse({'success': False, 'message': 'The measurement has no name - close this box and choose Add again from the list.'})

        # Check if already exists
'''),
        (r'''                return JsonResponse({'success': False, 'message': f'A unit with abbreviation "{abbreviation}" already exists'})

        # Create new measurement with all fields
        measurement = MeasurementUnit.objects.create(
            name=name,
            name_plural=name_plural if name_plural else None,
            abbreviation=abbreviation if abbreviation else None,
            abbreviation_plural=abbreviation_plural if abbreviation_plural else None,
            unit_type=unit_type
        )
''',
         r'''                return JsonResponse({'success': False, 'message': f'A unit with abbreviation "{abbreviation}" already exists'})

        # Create new measurement with all fields. RU-1 - a blank optional
        # field is stored as '' : since migration 0095 (N1) these columns
        # are NOT NULL, and None made MySQL refuse the row ('Column
        # 'abbreviation' cannot be null') whenever Abbreviation was left
        # empty.
        measurement = MeasurementUnit.objects.create(
            name=name,
            name_plural=name_plural,
            abbreviation=abbreviation,
            abbreviation_plural=abbreviation_plural,
            unit_type=unit_type
        )
'''),
        (r'''    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip().lower()

        if not name:
''',
         r'''    try:
        data = json.loads(request.body)
        name = (data.get('name') or '').strip().lower()

        if not name:
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''{% block top %}<h1>Help</h1>{% endblock %}
{% block content %}
<section class="tv-card"><p class="tv-h2">Install it</p><p style="margin: 0">On Android, in Chrome: the menu (&#8942;) &rarr; <b>Add to Home screen</b> / <b>Install app</b>. On an iPhone, in Safari: Share &rarr; <b>Add to Home Screen</b>. It stays signed in for 30 days on the phone.</p></section>
<section class="tv-card"><p class="tv-h2">Today</p><p style="margin: 0">While you are away: today&rsquo;s and tomorrow&rsquo;s bookings &mdash; flights, check-ins and check-outs, the car. Before a trip: how many days to go and the first day. Deadlines to cancel for free or to pay show under Coming up.</p></section>
<section class="tv-card"><p class="tv-h2">Passes</p><p style="margin: 0">Three tabs at the top. <b>Next</b>: the flight you need now, your own pass first &mdash; swipe for the others on the same flight. <b>Coming up</b>: the flights after it; tap one to open its pass. <b>Used</b>: every pass, kept for good, stamped USED with the barcode greyed &mdash; <b>Show the barcode anyway</b> brings it back. A pass is used six hours after its flight was due to land, so a delay does not take it away; on a connection the next pass takes over at the first flight&rsquo;s landing time (<b>Then</b> and <b>Earlier today</b> keep both one tap away). <b>Done with this pass</b> moves on at once; <b>Not flown yet</b> brings a used pass back. After the flight, <b>Add to Google Wallet</b> explains that airlines stop offering the pass to Wallet. The barcode is drawn again from the airline&rsquo;s own code, so the scanner reads it off the screen. Turn the brightness up. While Passes is open the screen stays on, and turning the phone does not flip the pass. Passes you have opened stay on the phone and work with no signal.</p></section>
''',
         r'''{% block top %}<h1>Help</h1>{% endblock %}
{% block content %}
<section class="tv-card"><p class="tv-h2">Install it</p><p style="margin: 0">On Android, in Chrome: the menu (&#8942;) &rarr; <b>Add to Home screen</b> / <b>Install app</b>. On an iPhone, in Safari: Share &rarr; <b>Add to Home Screen</b>. It stays signed in for 30 days on the phone. After Travel is updated, the app fetches its new look by itself the next time it opens with a signal.</p></section>
<section class="tv-card"><p class="tv-h2">Today</p><p style="margin: 0">While you are away: today&rsquo;s and tomorrow&rsquo;s bookings &mdash; flights, check-ins and check-outs, the car. Before a trip: how many days to go and the first day. Deadlines to cancel for free or to pay show under Coming up.</p></section>
<section class="tv-card"><p class="tv-h2">Passes</p><p style="margin: 0">Three tabs at the top. <b>Next</b>: the flight you need now, your own pass first &mdash; swipe for the others on the same flight. <b>Coming up</b>: the flights after it; tap one to open its pass. <b>Used</b>: every pass, kept for good, stamped USED with the barcode greyed &mdash; <b>Show the barcode anyway</b> brings it back. A pass is used six hours after its flight was due to land, so a delay does not take it away; on a connection the next pass takes over at the first flight&rsquo;s landing time (<b>Then</b> and <b>Earlier today</b> keep both one tap away). <b>Done with this pass</b> moves on at once; <b>Not flown yet</b> brings a used pass back. After the flight, <b>Add to Google Wallet</b> explains that airlines stop offering the pass to Wallet. The barcode is drawn again from the airline&rsquo;s own code, so the scanner reads it off the screen. Turn the brightness up. While Passes is open the screen stays on, and turning the phone does not flip the pass. Passes you have opened stay on the phone and work with no signal.</p></section>
'''),
    ]),
]


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('RU-1 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pq = os.path.join(root, PS1)
    if "'test_recipe_units_null.py'" in read(pq):
        print('RU-1 already applied.')
        return 0
    if "'test_cycle_look.py'" not in read(pq):
        refuse('CY-5 (apply_cycle_look.py, Release 98) is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('RU-1 --check: %d file(s) would change, none written; %d '
              'ship with it.' % (len(out), len(CREATES)))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('RU-1 applied - adding a measurement works again.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
