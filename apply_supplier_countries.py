"""apply_supplier_countries - the Country filter has never filtered.

    python apply_supplier_countries.py --check
    python apply_supplier_countries.py

THE BUG
-------
suppliers.html builds the Country dropdown like this:

    <option value="All">All Countries</option>
    {% for country in distinct_countries %}
      <option value="{{ country }}">{{ country }}</option>
    {% endfor %}

and pages/views/suppliers.py supplies a context of exactly three keys:

    supplier, selected_supplier, selected_country

`distinct_countries` is never set. Django renders an undefined variable as
empty rather than raising, so the loop runs zero times, the dropdown offers
"All Countries" and nothing else, and the filter cannot filter. Seen on Live
26 Aug 2026; suppliers.py has not been touched since May, so it has been that
way the whole time.

The view even accepts the value - `if sup_count and sup_count != "All"` - so
the filtering half works. Only the list of things to filter BY was missing.

WHY BUILD IT FROM THE DATA
--------------------------
properties.html solves the same problem by hardcoding:

    <option value="Cyprus">Cyprus</option>
    <option value="Greece">Greece</option>
    <option value="Spain">Spain</option>

which works until a property is bought in a fourth country, at which point it
is silently unfilterable - the same failure in slow motion. A distinct query
cannot drift from the data because it IS the data. (Properties is not changed
here; it belongs to its own round.)

ORDER BEFORE VALUES_LIST
------------------------
    .order_by(...).values_list(...).distinct()

not the other way round. DISTINCT applies to the selected columns, and Django
adds ORDER BY columns to the SELECT - so ordering after values_list can put a
second column into the SELECT and make every row distinct. The order here is
deliberate, and test_supplier_countries.py runs the real queryset against a
real database to prove it.

Idempotent. Backs up to .bak_countries.
"""

import io
import os
import shutil
import sys

CHECK = '--check' in sys.argv

ROOT = os.path.dirname(os.path.abspath(__file__))
VIEW = os.path.join(ROOT, 'pages', 'views', 'suppliers.py')
PAGE = os.path.join(ROOT, 'pages', 'templates', 'suppliers.html')

for p in (VIEW, PAGE):
    if not os.path.exists(p):
        sys.exit('! %s not found - run this from the project root'
                 % os.path.relpath(p, ROOT))

# Only worth doing if the template really does ask for it.
if 'distinct_countries' not in open(PAGE, encoding='utf-8-sig',
                                   errors='replace').read():
    sys.exit('! suppliers.html no longer loops over distinct_countries.\n'
             '  Nothing to supply - re-read the template first.')

raw = open(VIEW, 'rb').read()
ENC = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
NL = '\r\n' if b'\r\n' in raw else '\n'
text = raw.decode(ENC).replace('\r\n', '\n')

MARKER = '"distinct_countries": distinct_countries,'

if MARKER in text:
    print('')
    print('  ALREADY  the view already supplies distinct_countries.')
    sys.exit(0)

OLD = '''    # Pass the search values back to template for form preservation
    context = {
        "supplier": sresults,
        "selected_supplier": sup_output if sup_output and sup_output != "All" else "",
        "selected_country": sup_count if sup_count and sup_count != "All" else "All",
    }'''

NEW = '''    # The Country dropdown in suppliers.html loops over distinct_countries.
    # Nothing ever supplied it, so the loop ran zero times and the filter
    # offered "All Countries" and nothing else - it has never filtered. Django
    # renders an undefined template variable as empty rather than raising,
    # which is why it went unnoticed from May 2026 until 26 Aug.
    #
    # Built from the data, not hardcoded: a supplier in a new country appears
    # in the filter the moment they are saved. order_by BEFORE values_list is
    # deliberate - DISTINCT applies to the selected columns, and Django adds
    # ORDER BY columns to the SELECT, so ordering afterwards can smuggle a
    # second column in and make every row distinct.
    distinct_countries = (
        supplier.objects
        .exclude(supplier_country__isnull=True)
        .exclude(supplier_country__exact="")
        .order_by("supplier_country")
        .values_list("supplier_country", flat=True)
        .distinct()
    )

    # Pass the search values back to template for form preservation
    context = {
        "supplier": sresults,
        "distinct_countries": distinct_countries,
        "selected_supplier": sup_output if sup_output and sup_output != "All" else "",
        "selected_country": sup_count if sup_count and sup_count != "All" else "All",
    }'''

n = text.count(OLD)
if n != 1:
    sys.exit('! the context block matched %d times (expected 1).\n'
             '  pages/views/suppliers.py has moved on - re-read it first.' % n)

text = text.replace(OLD, NEW, 1)

# ------------------------------------------------------- verify before writing
problems = []
if MARKER not in text:
    problems.append('the context key is missing from the result')
i_order = text.find('.order_by("supplier_country")')
i_values = text.find('.values_list("supplier_country"')
if not (0 <= i_order < i_values):
    problems.append('order_by must come BEFORE values_list (order=%d values=%d)'
                    % (i_order, i_values))
if '.distinct()' not in text:
    problems.append('the queryset is not distinct')
try:
    compile(text, VIEW, 'exec')
except SyntaxError as e:
    problems.append('suppliers.py would not compile: line %s: %s'
                    % (e.lineno, e.msg))
if problems:
    sys.exit('! self-check failed:\n  - ' + '\n  - '.join(problems))

print('')
print('  OK      the view now supplies distinct_countries')
print('  OK      built from the data, so it cannot drift from it')
print('  OK      suppliers.py compiles')
print('')
print('  The template already had the loop; only the list was missing.')
print('')

if CHECK:
    print('--check: nothing written.')
    sys.exit(0)

bak = VIEW + '.bak_countries'
if not os.path.exists(bak):
    shutil.copy2(VIEW, bak)
with io.open(VIEW, 'w', encoding=ENC, newline='') as fh:
    fh.write(text.replace('\n', NL) if NL != '\n' else text)
print('  wrote pages/views/suppliers.py  (backup: .bak_countries)')
print('')
print('Now run:  python test_supplier_countries.py')
