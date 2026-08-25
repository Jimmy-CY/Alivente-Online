"""test_remove_legacy_reports - the legacy helpers are gone, the real ones stay.

    python test_remove_legacy_reports.py

The risk in this change is not the deletion; it is deleting one thing and
taking its healthy namesake with it. Two pairs share a name-stem:

    open_invoices   (removed)   vs  open_invoices_report   (KEEP)
    lease_renewal   (removed)   vs  lease_renewal_report   (KEEP)

and the middleware permission map matches on PREFIX, so the short names
silently also matched their `_report` siblings. This suite lifts
_get_required_permission's matcher verbatim out of middleware.py and runs it,
rather than reasoning about which entry wins.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates', 'admin_apms.html')
ADMIN = os.path.join(ROOT, 'pages', 'views', 'administration.py')
INV = os.path.join(ROOT, 'pages', 'views', 'invoices.py')
ISSUES = os.path.join(ROOT, 'pages', 'views', 'issues.py')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
MID = os.path.join(ROOT, 'pages', 'middleware.py')

for p in (TPL, ADMIN, INV, ISSUES, URLS, MID):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the project root'
                 % os.path.relpath(p, ROOT))


def read(p):
    return open(p, encoding='utf-8-sig').read().replace('\r\n', '\n')


TPL_SRC, ADMIN_SRC = read(TPL), read(ADMIN)
INV_SRC, ISSUES_SRC = read(INV), read(ISSUES)
URLS_SRC, MID_SRC = read(URLS), read(MID)

results = []


def check(label, ok):
    results.append((label, bool(ok)))


# ==================================================== THE LEGACY IS REALLY GONE
check('the Generate Invoices button is gone from Administration',
      'Generate Invoices' not in TPL_SRC and 'admin_invoices' not in TPL_SRC)

for name, src, label in (('admin_unpaid', ADMIN_SRC, 'administration.py'),
                         ('admin_renewals', ADMIN_SRC, 'administration.py'),
                         ('admin_invoices', ADMIN_SRC, 'administration.py')):
    check('%s: def %s is gone' % (label, name), ('def %s' % name) not in src)

check('invoices.py: def open_invoices is gone',
      re.search(r'^def open_invoices\(', INV_SRC, re.M) is None)
check('issues.py: def lease_renewal is gone',
      re.search(r'^def lease_renewal\(', ISSUES_SRC, re.M) is None)

check('nothing imports the open_invoices helper any more',
      'import open_invoices' not in ADMIN_SRC
      and 'import open_invoices' not in INV_SRC)
check('nothing imports the lease_renewal helper any more',
      'import lease_renewal' not in ADMIN_SRC
      and 'import lease_renewal' not in ISSUES_SRC)

for mod in ('open_invoices.py', 'lease_renewal.py',
            'send_email.py', 'pdf_display.py'):
    check('%s is deleted from the project root' % mod,
          not os.path.exists(os.path.join(ROOT, mod)))

# The orphan template that held the last two {% url %} refs to the deleted
# views - and, in the same breath, the live home page it was a copy of.
check('pages/templates/home_original.html is deleted',
      not os.path.exists(os.path.join(ROOT, 'pages', 'templates',
                                      'home_original.html')))
check('  and pages/templates/home.html - the live one - is untouched',
      os.path.exists(os.path.join(ROOT, 'pages', 'templates', 'home.html')))

for route in ("views.admin_unpaid", "views.admin_renewals",
              "views.admin_invoices"):
    check('urls.py no longer routes to %s' % route, route not in URLS_SRC)
check("urls.py no longer has the bare open_invoices route",
      "name='open_invoices')" not in URLS_SRC)
check("urls.py no longer has the bare lease_renewal route",
      "name='lease_renewal')" not in URLS_SRC)

# The unused import went with the only view that used it.
check('administration.py dropped the now-unused date import',
      'from datetime import date' not in ADMIN_SRC)
check('  and really has no date.today() left',
      'date.today()' not in ADMIN_SRC)

# Docstrings are part of the change: a module index that lists views which no
# longer exist is a lie the next reader has to disprove.
check('administration.py docstring no longer lists the removed views',
      'admin_unpaid' not in ADMIN_SRC and 'admin_renewals' not in ADMIN_SRC)
check('invoices.py docstring no longer lists open_invoices',
      'open_invoices            : Generate' not in INV_SRC)
check('issues.py docstring no longer lists the lease_renewal view',
      'lease_renewal_report, lease_renewal\n' not in ISSUES_SRC)
check('  and its Reports count was corrected to 7',
      'Reports (7):' in ISSUES_SRC)
check('  the shadowing note explains what happened',
      'could never be written on Live' in ISSUES_SRC)

# ================================================= THE SURVIVORS ARE UNTOUCHED
check('invoices.py still has open_invoices_report',
      'def open_invoices_report' in INV_SRC)
check('issues.py still has lease_renewal_report',
      'def lease_renewal_report' in ISSUES_SRC)
check('  and it still renders its template',
      "render(request, 'lease_renewal_report.html'" in ISSUES_SRC)
check('urls.py still routes open_invoices_report',
      "name='open_invoices_report'" in URLS_SRC)
check('urls.py still routes lease_renewal_report',
      "name='lease_renewal_report'" in URLS_SRC)

tpl_dir = os.path.join(ROOT, 'pages', 'templates')
tenant_html = os.path.join(tpl_dir, 'tenant.html')
if os.path.exists(tenant_html):
    t = read(tenant_html)
    check('the Tenants page still links both surviving reports',
          "url 'open_invoices_report'" in t
          and "url 'lease_renewal_report'" in t)
else:
    check('tenant.html exists', False)

# No template anywhere may still reverse a URL name we deleted - a dead
# {% url %} raises NoReverseMatch and takes the whole page down.
dead_names = ('admin_unpaid', 'admin_renewals', 'admin_invoices')
offenders = []
for f in sorted(os.listdir(tpl_dir)):
    if not f.endswith('.html'):
        continue
    s = read(os.path.join(tpl_dir, f))
    for nm in dead_names:
        if ("url '%s'" % nm) in s or ('url "%s"' % nm) in s:
            offenders.append('%s -> %s' % (f, nm))
    # the two short names need an exact-quote match so the _report siblings
    # are not mistaken for them
    for nm in ('open_invoices', 'lease_renewal'):
        if ("url '%s'" % nm) in s or ('url "%s"' % nm) in s:
            offenders.append('%s -> %s' % (f, nm))
check('no template reverses a deleted URL name%s'
      % (' (%s)' % ', '.join(offenders[:3]) if offenders else ''),
      not offenders)

# ===================================== THE MIDDLEWARE MATCHER, RUN FOR REAL
# Lifted by LINE, then dedented as a block. A regex that starts mid-line loses
# the first line's indentation while the rest keeps it, which will not compile.
_lines = MID_SRC.split('\n')
_start = next((i for i, l in enumerate(_lines)
               if l.strip() == 'for prefix, permission in url_permission_map:'),
              None)
_end = None
if _start is not None:
    for i in range(_start + 1, len(_lines)):
        if _lines[i].strip() == 'return None':
            _end = i
            break
m = None
if _start is not None and _end is not None:
    import textwrap
    body = textwrap.dedent('\n'.join(_lines[_start:_end + 1]))
    m = body
check('the permission matcher was found in middleware.py', m is not None)

# Scoped to the url_permission_map literal. A file-wide tuple scrape picks up
# ~16 unrelated pairs from other lists, and those can satisfy a match that the
# real map would not - a test passing on the wrong data.
_i = MID_SRC.index('url_permission_map = [')
_j = MID_SRC.index('\n        ]', _i)
MAP = re.findall(r"\(\s*'([^']+)'\s*,\s*'([^']+)'\s*\)", MID_SRC[_i:_j])
check('  and the map has entries (%d found)' % len(MAP), len(MAP) > 50)
check('  scoped to the map itself, not the whole file',
      len(MAP) < len(re.findall(r"\(\s*'([^']+)'\s*,\s*'([^']+)'\s*\)",
                                MID_SRC)))

if m:
    src = ('def _match(clean_path, url_permission_map):\n'
           + '\n'.join('    ' + l for l in body.split('\n')))
    ns = {}
    exec(compile(src, 'permission_matcher', 'exec'), ns)
    match = ns['_match']

    # The whole point of the change: the short prefixes are gone, and the
    # _report siblings must still resolve to the same permission as before.
    check('open_invoices_report still resolves to can_access_tenants',
          match('open_invoices_report', MAP) == 'auth.can_access_tenants')
    check('lease_renewal_report still resolves to can_access_tenants',
          match('lease_renewal_report', MAP) == 'auth.can_access_tenants')
    check('  neither falls through to None',
          match('open_invoices_report', MAP) is not None
          and match('lease_renewal_report', MAP) is not None)

    # The deleted paths must no longer have a DEDICATED entry. Note the test is
    # on the entry, not on match() returning None: a broader prefix can still
    # legitimately cover a path. ('lease', ...) covers lease_renewal via the
    # prefix + '_' rule, which is correct and harmless now the URL is gone -
    # asserting None here would have been a wrong expectation, not a bug.
    prefixes = [p for p, _ in MAP]
    for dead in ('open_invoices', 'lease_renewal', 'admin_unpaid',
                 'admin_renewals', 'admin_invoices'):
        check('  %s has no entry of its own left' % dead,
              dead not in prefixes)
    check('open_invoices is covered by nothing at all',
          match('open_invoices', MAP) is None)
    check('lease_renewal is still covered by the broader "lease" prefix',
          match('lease_renewal', MAP) == 'auth.can_access_tenants')

    # Guard the neighbours the prefix rule could have caught.
    check('invoices still resolves to can_access_invoices',
          match('invoices', MAP) == 'auth.can_access_invoices')
    check('invoices_commit still resolves to can_access_invoices',
          match('invoices_commit', MAP) == 'auth.can_access_invoices')
    check('lease_agreements still resolves to can_access_tenants',
          match('lease_agreements', MAP) == 'auth.can_access_tenants')
    check('physical-invoices still resolves to can_access_invoices',
          match('physical-invoices/list', MAP) == 'auth.can_access_invoices')

    # And prove the matcher we lifted really is prefix-based, so the checks
    # above are testing the hazard rather than a stricter rule.
    check('the matcher really is prefix-based (the hazard is real)',
          match('invoices_commit', [('invoices', 'X')]) == 'X')

# ============================================== EVERYTHING STILL COMPILES
import py_compile
import tempfile
for path in (ADMIN, INV, ISSUES, URLS, MID):
    tmp = os.path.join(tempfile.gettempdir(), '_legacy_test.py')
    open(tmp, 'w', encoding='utf-8').write(read(path))
    try:
        py_compile.compile(tmp, cfile=tmp + 'c', doraise=True)
        check('%s compiles' % os.path.basename(path), True)
    except py_compile.PyCompileError as exc:
        check('%s compiles (%s)' % (os.path.basename(path), exc), False)
    finally:
        for f in (tmp, tmp + 'c'):
            if os.path.exists(f):
                os.remove(f)

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
