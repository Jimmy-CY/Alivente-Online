"""test_supplier_countries - does the Country filter actually have options?

    python test_supplier_countries.py

The static half checks the view supplies the key. That is necessary and not
sufficient: the bug being fixed was invisible precisely because a missing
context key looks like a working page.

So the second half LIFTS the queryset expression verbatim out of
pages/views/suppliers.py and runs it against a real (in-memory SQLite)
database with duplicates, a NULL and a blank in it. Lifted, not retyped - if
the view changes, this test changes with it or fails.

The third half renders the real <select> markup out of suppliers.html through
Django's own template engine and counts the options, which is the thing the
user actually sees.
"""

import os
import re
import sys
import textwrap

ROOT = os.path.dirname(os.path.abspath(__file__))
VIEW = os.path.join(ROOT, 'pages', 'views', 'suppliers.py')
PAGE = os.path.join(ROOT, 'pages', 'templates', 'suppliers.html')

for p in (VIEW, PAGE):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the project root'
                 % os.path.relpath(p, ROOT))

results = []


def check(label, ok):
    results.append((label, bool(ok)))


SRC = open(VIEW, encoding='utf-8-sig', errors='replace').read().replace(
    '\r\n', '\n')
TPL = open(PAGE, encoding='utf-8-sig', errors='replace').read().replace(
    '\r\n', '\n')

# ==================================================================== STATIC
check('the template still asks for distinct_countries',
      re.search(r'\{%\s*for\s+\w+\s+in\s+distinct_countries\s*%\}', TPL)
      is not None)
check('the view now supplies it',
      '"distinct_countries": distinct_countries,' in SRC)
check('  it is built from the model, not hardcoded',
      'supplier.objects' in SRC and 'distinct_countries = (' in SRC)
check('  nulls are excluded', 'supplier_country__isnull=True' in SRC)
check('  and blanks too', 'supplier_country__exact=""' in SRC)

i_order = SRC.find('.order_by("supplier_country")')
i_values = SRC.find('.values_list("supplier_country"')
check('  order_by comes BEFORE values_list', 0 <= i_order < i_values)
check('  and the result is distinct', '.distinct()' in SRC)

check('the filtering half was already there',
      'sresults.filter(supplier_country=sup_count)' in SRC)

try:
    compile(SRC, VIEW, 'exec')
    check('suppliers.py compiles', True)
except SyntaxError as e:
    check('suppliers.py compiles (line %s: %s)' % (e.lineno, e.msg), False)

# ======================================================= THE REAL QUERYSET
# Lift the expression out of the file rather than restating it here.
m = re.search(r'^(    distinct_countries = \(\n(?:.*\n)*?    \)\n)', SRC, re.M)
check('the queryset expression could be lifted from the view',
      m is not None)

try:
    import django
    from django.conf import settings
    HAVE_DJANGO = True
except ImportError:
    HAVE_DJANGO = False

if HAVE_DJANGO and m:
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth',
                            '__main__'],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
            TEMPLATES=[{'BACKEND':
                        'django.template.backends.django.DjangoTemplates',
                        'DIRS': [], 'APP_DIRS': False, 'OPTIONS': {}}],
            USE_TZ=False, DEFAULT_AUTO_FIELD='django.db.models.AutoField')
        django.setup()

    from django.db import models, connection

    class supplier(models.Model):          # noqa: N801 - mirrors the app's name
        supplier_contact_person = models.CharField(max_length=200, blank=True)
        supplier_country = models.CharField(max_length=100, null=True,
                                            blank=True)

        class Meta:
            app_label = '__main__'

    with connection.schema_editor() as se:
        se.create_model(supplier)

    # Deliberately awkward data: duplicates, a NULL, a blank, and an order
    # that is not insertion order.
    for person, country in (('Alex', 'Cyprus'), ('Billy', 'Cyprus'),
                            ('Nikos', 'Greece'), ('Ana', 'Spain'),
                            ('Dup', 'Greece'), ('NoCountry', None),
                            ('BlankCountry', '')):
        supplier.objects.create(supplier_contact_person=person,
                                supplier_country=country)

    ns = {'supplier': supplier}
    exec(textwrap.dedent(m.group(1)), ns)          # noqa: S102 - lifted code
    got = list(ns['distinct_countries'])

    check('the lifted queryset runs against a real database', True)
    check('  it returns each country ONCE (%r)' % got,
          got == ['Cyprus', 'Greece', 'Spain'])
    check('  duplicates collapsed - two Cyprus rows, one option',
          got.count('Cyprus') == 1)
    check('  the NULL country is not offered', None not in got)
    check('  and neither is the blank one', '' not in got)
    check('  they come back alphabetically', got == sorted(got))

    # ---------------------------------------------- and through the template
    sel = re.search(r'<select[^>]*name="supcount".*?</select>', TPL, re.S | re.I)
    check('the real <select> markup was found in suppliers.html',
          sel is not None)
    if sel:
        from django.template import Template, Context
        html = Template(sel.group(0)).render(
            Context({'distinct_countries': got, 'selected_country': 'Greece'}))
        opts = re.findall(r'<option[^>]*>([^<]*)</option>', html)
        check('  rendered, the dropdown has %d options, not 1' % len(opts),
              len(opts) == 4)
        check('  "All Countries" is still first',
              opts and opts[0].strip() == 'All Countries')
        for c in ('Cyprus', 'Greece', 'Spain'):
            check('  %s is offered' % c, c in [o.strip() for o in opts])
        check('  the current selection is marked selected',
              re.search(r'<option value="Greece"[^>]*selected', html)
              is not None)

        # The failure being fixed: with the key absent, this is what happened.
        empty = Template(sel.group(0)).render(Context({}))
        n_empty = len(re.findall(r'<option', empty))
        check('CONTROL: with distinct_countries absent it renders %d option'
              % n_empty, n_empty == 1)
else:
    print('')
    print('  SKIP  Django not importable - the live queryset check is skipped')

# ====================================================================== out
print('')
bad = 0
for label, ok in results:
    print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad += 0 if ok else 1
print('')
print('%d of %d failed' % (bad, len(results)) if bad
      else 'All %d checks passed.' % len(results))
sys.exit(1 if bad else 0)
