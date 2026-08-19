"""Exercise the patched database error page.

Imports the real middleware module and calls the real renderer. The thing most
likely to go wrong here is the classification quietly defaulting the wrong way
- so every branch gets an assertion, including the deliberate fallbacks.
"""

import importlib.util
import sys

import django
from django.conf import settings

settings.configure(
    DEBUG=False,
    DATABASES={},
    INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
    DEFAULT_CHARSET='utf-8',
    USE_TZ=True,
)
django.setup()

from django.db import DatabaseError, InterfaceError, OperationalError, ProgrammingError  # noqa: E402

spec = importlib.util.spec_from_file_location('mw', 'pages/middleware.py')
mw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mw)
M = mw.DatabaseConnectionMiddleware


def render(exc, debug=False):
    settings.DEBUG = debug
    # The renderer touches no instance state, so an unbound call is enough and
    # avoids constructing the middleware with a fake get_response.
    resp = M._render_connectivity_error(M, None, exc)
    return resp, resp.content.decode('utf-8')


def wrapped(errno, msg):
    """A Django-wrapped driver error, the shape the ORM actually raises."""
    inner = Exception(errno, msg)
    outer = ProgrammingError(str((errno, msg)))
    outer.__cause__ = inner
    return outer


results = []


def check(label, ok):
    results.append((label, bool(ok)))


# ---- the case from the log: unknown column after an un-run migration -------
REAL = OperationalError(1054, "Unknown column 'act_expense.act_expense_verify_status' in 'field list'")
resp, html = render(REAL)
check('1054 classified as schema', M._classify_db_exception(REAL) == 'schema')
check('1054 page says out of date', 'Database Out Of Date' in html)
check('1054 uses the schema code', 'DB_SCHEMA_503' in html)
check('1054 does NOT offer a refresh', 'location.reload()' not in html)
check('1054 says refreshing will not help', 'Refreshing will not help' in html)
check('1054 still offers Go Home', 'Go Home' in html)

# ---- connectivity keeps the old wording, exactly -------------------------
GONE = OperationalError(2006, 'MySQL server has gone away')
resp2, html2 = render(GONE)
check('2006 classified as connectivity', M._classify_db_exception(GONE) == 'connectivity')
check('2006 keeps the original wording',
      "We're experiencing temporary connectivity issues" in html2)
check('2006 keeps the original code', 'DB_CONNECTION_503' in html2)
check('2006 still offers a refresh', 'location.reload()' in html2)

# ---- charset and encoding -------------------------------------------------
check('charset declared on the response',
      'charset=utf-8' in resp2['Content-Type'].lower())
check('status is still 503', resp2.status_code == 503)
try:
    resp2.content.decode('utf-8')
    decodes = True
except UnicodeDecodeError:
    decodes = False
check('body is valid UTF-8', decodes)
# The mojibake signature must not survive a latin-1 misread any more, because
# the browser is now told the encoding.
check('no stray emoji left to be mangled',
      '⚠' not in html2 and '\U0001f504' not in html2)

# ---- fallbacks ------------------------------------------------------------
check('no exception -> connectivity (back-compat)',
      M._classify_db_exception(None) == 'connectivity')
check('unknown errno -> connectivity (conservative)',
      M._classify_db_exception(OperationalError(9999, 'who knows')) == 'connectivity')
check('InterfaceError -> connectivity',
      M._classify_db_exception(InterfaceError('cursor closed')) == 'connectivity')
check('ProgrammingError with no errno -> schema',
      M._classify_db_exception(ProgrammingError('relation does not exist')) == 'schema')
check('bare DatabaseError -> connectivity',
      M._classify_db_exception(DatabaseError('something')) == 'connectivity')
check('table missing (1146) -> schema',
      M._classify_db_exception(OperationalError(1146, "Table 'x' doesn't exist")) == 'schema')
check('too many connections (1040) -> connectivity',
      M._classify_db_exception(OperationalError(1040, 'Too many connections')) == 'connectivity')

# Django wraps driver errors; the number lives on __cause__.
w = wrapped(1054, "Unknown column 'foo' in 'field list'")
check('errno read from __cause__ when wrapped',
      M._classify_db_exception(w) == 'schema')

# ---- DEBUG detail ---------------------------------------------------------
_, html_off = render(REAL, debug=False)
_, html_on = render(REAL, debug=True)
check('DEBUG off: no exception detail leaked',
      'act_expense_verify_status' not in html_off)
check('DEBUG on: exception shown', 'act_expense_verify_status' in html_on)
check('DEBUG on: detail is HTML-escaped',
      '&#x27;' in html_on or '&quot;' in html_on or '&amp;' in html_on
      or "'" not in "Unknown column 'x'")

# Escaping proof with a hostile message.
_, html_x = render(OperationalError(1054, '<script>alert(1)</script>'), debug=True)
check('DEBUG on: no raw script tag injected', '<script>alert(1)</script>' not in html_x)

# ---- the page is still well-formed ---------------------------------------
for label, h in (('schema', html), ('connectivity', html2)):
    check('%s page has one <h1>' % label, h.count('<h1>') == 1)
    check('%s page has no leftover format keys' % label,
          '__HEADING__' not in h and '__BODY__' not in h and '__DETAIL__' not in h and '' == '' and '%(' not in h.split('</html>')[0])

print('')
bad = 0
for label, ok in results:
    print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad += 0 if ok else 1
print('')
print('%d of %d failed' % (bad, len(results)) if bad else 'All %d checks passed.' % len(results))

# Write both pages out so they can be looked at.
open('error_schema.html', 'w', encoding='utf-8').write(render(REAL, debug=True)[1])
open('error_connectivity.html', 'w', encoding='utf-8').write(html2)
print('Wrote error_schema.html and error_connectivity.html')
sys.exit(1 if bad else 0)
