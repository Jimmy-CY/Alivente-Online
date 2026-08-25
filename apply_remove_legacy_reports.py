"""apply_remove_legacy_reports - retire the desktop-era report helpers.

    python apply_remove_legacy_reports.py --check
    python apply_remove_legacy_reports.py

WHAT IS BEING REMOVED, AND WHY
------------------------------
Two project-root modules, open_invoices.py and lease_renewal.py, date from
when this ran on a Windows desktop. Both end with:

    file_path = "C:/Users/DemetrisManias/Desktop/code/djangoproject/static/reports/"
    pdf.output(file_path + "<Report> (<date>).pdf")

That string has no leading slash, so on Linux it is a RELATIVE path. Live
resolves it to /app/C:/Users/... - a directory whose first segment does not
exist. fpdf opens for writing without creating parents, so every caller raises
FileNotFoundError before it can e-mail anything. Confirmed on Live 25 Aug 2026
by Show-LegacyInvoiceUse.ps1: "deepest existing part: (nothing - not even the
first segment)".

Five call sites go with them:

  admin_invoices   Administration > Generate Invoices. The ONLY one with a
                   button. It inserts collection invoices, which the
                   five-minute cron already does - except the cron also sets
                   invoice_amount and this does not. Proven never used: of 152
                   invoices on Live, every one dated on or after the first
                   priced invoice (2026-07-01) carries an amount. Zero
                   unexplained.
  admin_unpaid     Administration > Email Unpaid Report. No template links it.
  admin_renewals   Administration > Email Lease Renewal Report. No template
                   links it. The renewal e-mail you actually receive - subject
                   "Alert - Invoices, Leases and Vacant Properties" - comes
                   from check_lease_renewals.run_notification_function, which
                   builds its own HTML and uses the configurable daily_report
                   recipients. Verified against a received message.
  open_invoices    invoices.py. No template links it; it reads a POST field
                   ('d_e') from a form that no longer exists.
  lease_renewal    issues.py. Same - no link, same POST field, same helper.

send_email.py and pdf_display.py are imported by nothing else, so they go too.
pdf_display calls webbrowser.open(), which on a server would open a browser on
the server.

WHAT IS DEFINITELY STAYING
--------------------------
  open_invoices_report   invoices.py - the on-screen Debtors Age Analysis
  lease_renewal_report   issues.py  - the on-screen Lease Renewal report
Both render real templates and are linked from the Tenants page. They share a
name-stem with the two views being deleted, which is exactly why this script
checks for them explicitly rather than trusting a substring match.

THE MIDDLEWARE TRAP
-------------------
_get_required_permission walks url_permission_map in order and returns the
FIRST entry where

    clean_path == prefix or startswith(prefix + '/') or startswith(prefix + '_')

so ('lease_renewal', ...) also matches lease_renewal_report, and
('open_invoices', ...) would match open_invoices_report. Today the _report
entries sit earlier in the list, which is the only reason the right permission
wins - the file carries a comment about this same hazard for 'projects'.
Removing the two short prefixes is therefore safe, but it is safe by accident
of ordering, so test_remove_legacy_reports.py lifts the matcher out of
middleware.py and proves both reports still resolve.

Idempotent. Every file backed up to .bak_legacyreports; the deleted root
modules are backed up too, not just unlinked. Python is compiled before
anything is written.
"""

import io
import os
import py_compile
import shutil
import sys
import tempfile

CHECK = '--check' in sys.argv

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates', 'admin_apms.html')
ADMIN = os.path.join(ROOT, 'pages', 'views', 'administration.py')
INV = os.path.join(ROOT, 'pages', 'views', 'invoices.py')
ISSUES = os.path.join(ROOT, 'pages', 'views', 'issues.py')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
MIDDLEWARE = os.path.join(ROOT, 'pages', 'middleware.py')

# Paths relative to the project root. home_original.html is a year-old orphan
# copy of the home page (17 Jul 2025) that nothing renders, includes or
# extends - and it holds the last two {% url %} references to the deleted
# views, in the very "d_e" forms those views read. It IS the form that no
# longer exists. home.html, the live one, is untouched.
DOOMED = ['open_invoices.py', 'lease_renewal.py',
          'send_email.py', 'pdf_display.py',
          os.path.join('pages', 'templates', 'home_original.html')]

for p in (TPL, ADMIN, INV, ISSUES, URLS, MIDDLEWARE):
    if not os.path.exists(p):
        sys.exit('! %s not found - run this from the project root'
                 % os.path.relpath(p, ROOT))


def sniff(path):
    raw = open(path, 'rb').read()
    if raw.startswith(b'\xef\xbb\xbf'):
        return raw[3:].decode('utf-8'), 'utf-8-sig', (
            '\r\n' if b'\r\n' in raw else '\n')
    return raw.decode('utf-8'), 'utf-8', ('\r\n' if b'\r\n' in raw else '\n')


FILES = {}
for p in (TPL, ADMIN, INV, ISSUES, URLS, MIDDLEWARE):
    t, e, n = sniff(p)
    FILES[p] = {'text': t.replace('\r\n', '\n'), 'enc': e, 'nl': n}

CHANGES = []


def cut(label, path, old, gone_marker, new=''):
    """Remove `old` (or replace it with `new`), exactly once.

    `gone_marker` is a string that exists in `old` and must NOT survive
    anywhere in the file afterwards - that is how a re-run recognises the edit
    as already applied. Removals cannot use the usual "is the replacement
    present?" test, because the replacement is nothing."""
    d = FILES[path]
    if gone_marker not in old:
        sys.exit('! %s: the marker is not in the text being removed.' % label)
    if gone_marker not in d['text']:
        CHANGES.append(('skip', label))
        return
    n = d['text'].count(old)
    if n != 1:
        sys.exit('! %s: anchor matched %d times in %s (expected 1).\n'
                 '  The file has moved on - re-read it before patching.'
                 % (label, n, os.path.relpath(path, ROOT)))
    CHANGES.append(('apply', label))
    d['text'] = d['text'].replace(old, new, 1)


# =========================================================== 1. THE BUTTON
cut('admin_apms.html: the Generate Invoices button', TPL,
    """
      <!-- Generate Invoices (requires Invoices edit) -->
      {% if perms.auth.can_edit_invoices %}
        <a href="{% url 'admin_invoices' %}" class="admin-btn btn-alivente">
          <i class="fas fa-file-invoice"></i>
          <h6>Generate Invoices</h6>
        </a>
      {% else %}
        <div class="admin-btn btn-perm-disabled" title="You do not have permission to edit Invoices">
          <i class="fas fa-file-invoice"></i>
          <h6>Generate Invoices</h6>
        </div>
      {% endif %}
""",
    'Generate Invoices')

# ==================================================== 2. THE ADMIN VIEWS
# The anchor deliberately stops at the closing paren with NO trailing newline:
# admin_invoices is the last thing in the file and there is no newline after
# it. Adding one back would make this anchor match zero times.
cut('administration.py: admin_unpaid / admin_renewals / admin_invoices',
    ADMIN,
    '''

@login_required
@permission_required('auth.can_access_administration', raise_exception=True)
def admin_unpaid(request):
    # Project-root helper module (resolved via sys.path), not a views import.
    import open_invoices
    rep_output = "Email"
    check = "Yes"
    email = "demetrimanias@gmail.com"
    fname = "Demetri"
    open_invoices.open_invoices(rep_output, check, email, fname)
#   email = "stella.simitopoulos@alivente.com"
#   fname = "Stella"
#   open_invoices.open_invoices(rep_output, check, email, fname)
    return redirect("admin_apms")


@login_required
@permission_required('auth.can_access_administration', raise_exception=True)
def admin_renewals(request):
    # Project-root helper module (resolved via sys.path), not a views import.
    import lease_renewal
    rep_output = "Email"
    check = "Yes"
    email = "demetrimanias@gmail.com"
    fname = "Demetri"
    lease_renewal.lease_renewal(rep_output, check, email, fname)
#   email = "stella.simitopoulos@alivente.com"
#   fname = "Stella"
#   lease_renewal.lease_renewal(rep_output,check, email, fname)
    return redirect("admin_apms")


@login_required
@permission_required('auth.can_access_administration', raise_exception=True)
@permission_required('auth.can_edit_invoices', raise_exception=True)
def admin_invoices(request):
    # Stacked decorators are intentional: requires BOTH
    # can_access_administration AND can_edit_invoices.
    # Project-root helper module (resolved via sys.path), not a views import.
    import open_invoices
    today = date.today()
    months = ('Month', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December')
    open_invoices.create_invoices(months[today.month], today.year, request)
    return redirect("admin_apms")''',
    'def admin_unpaid')

cut('administration.py: their docstring entries', ADMIN,
    """- admin_unpaid           : Email the open-invoices report (project-root
                           open_invoices helper).
- admin_renewals         : Email the lease-renewal report (project-root
                           lease_renewal helper).
- admin_invoices         : Generate the current month's invoices
                           (project-root open_invoices helper).
""",
    'admin_unpaid           : Email')

cut('administration.py: the auth-tier line', ADMIN,
    """can_access_administration -> admin_apms, admin_unpaid, admin_renewals,
                             admin_invoices (also needs can_edit_invoices)
""",
    'admin_unpaid, admin_renewals',
    'can_access_administration -> admin_apms\n')

# `date` was imported for admin_invoices alone - the only date.today() in the
# file lived in it, so the import goes with the view rather than being left as
# a dangling unused name.
cut('administration.py: the now-unused date import', ADMIN,
    'from datetime import date\n\n',
    'from datetime import date')

# ======================================================= 3. THE TWO VIEWS
cut('invoices.py: the open_invoices view', INV,
    '''

@login_required
@permission_required('auth.can_access_invoices', raise_exception=True)
def open_invoices(request):
    # NB: imports the project-root ``open_invoices.py`` reporting helper,
    # not anything in this views file. Absolute imports resolve via sys.path.
    import open_invoices
    rep_output = request.POST.get('d_e')
    check = 'No'
    # @login_required guarantees request.user is authenticated here.
    email = request.user.email
    fname = request.user.first_name
    open_invoices.open_invoices(rep_output, check, email, fname)
    messages.success(request, "Report Created Successfully")
    return redirect('home')
''',
    'def open_invoices(request)')

cut('invoices.py: its docstring entry', INV,
    """- open_invoices            : Generate the open-invoices report via the
                             project-root open_invoices.py helper.
""",
    'open_invoices            : Generate')

cut('invoices.py: the auth-tier line', INV,
    """read tier -> auth.can_access_invoices  (invoices_page, open_invoices,
                                        open_invoices_report)
""",
    'invoices_page, open_invoices,',
    """read tier -> auth.can_access_invoices  (invoices_page,
                                        open_invoices_report)
""")

cut('issues.py: the lease_renewal view', ISSUES,
    '''

@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def lease_renewal(request):
    # Local import: 'lease_renewal' is a root-level report module (distinct
    # from this view of the same name) - hence the deliberate local scope.
    import lease_renewal
    rep_output = request.POST.get('d_e')
    check = 'No'
    if request.user.is_authenticated:
        email = request.user.email
        fname = request.user.first_name
    lease_renewal.lease_renewal(rep_output, check, email, fname)
    messages.success(request, "Report Created Successfully")
    return redirect('home')

''',
    'def lease_renewal(request)')

cut('issues.py: its docstring entry', ISSUES,
    """  Reports (8): lease_agreements, title_deeds, prop_rep,
               lease_agreement_report, tenant_report, tenant_rep,
               lease_renewal_report, lease_renewal
""",
    'lease_renewal_report, lease_renewal\n',
    """  Reports (7): lease_agreements, title_deeds, prop_rep,
               lease_agreement_report, tenant_report, tenant_rep,
               lease_renewal_report
""")

cut('issues.py: the shadowing note', ISSUES,
    """Note: several of the inline imports here are deliberate and must NOT be
hoisted - the root-level report modules (print_lease, print_title,
print_prop, print_tenant, fsr, issues, lease_renewal) share names with
this module's `issues` model import, the `fsr` view, and the
`lease_renewal` view, so they are imported locally to avoid shadowing.
""",
    'fsr, issues, lease_renewal) share names',
    """Note: several of the inline imports here are deliberate and must NOT be
hoisted - the root-level report modules (print_lease, print_title,
print_prop, print_tenant, fsr, issues) share names with this module's
`issues` model import and the `fsr` view, so they are imported locally to
avoid shadowing. The lease_renewal pair is gone: both the root module and
the view that called it were removed on 25 Aug 2026 - the report they
produced could never be written on Live.
""")

# ============================================================== 4. THE URLS
cut('urls.py: the three admin routes', URLS,
    """    path('admin_unpaid/', views.admin_unpaid, name='admin_unpaid'),
    path('admin_renewals/', views.admin_renewals, name='admin_renewals'),
    path('admin_invoices/', views.admin_invoices, name='admin_invoices'),
""",
    "views.admin_unpaid")

cut('urls.py: the open_invoices route', URLS,
    "    path('open_invoices/', views.open_invoices, name='open_invoices'),\n",
    "name='open_invoices')")

cut('urls.py: the lease_renewal route', URLS,
    "    path('lease_renewal/', views.lease_renewal, name='lease_renewal'),\n",
    "name='lease_renewal')")

# ======================================================== 5. THE MIDDLEWARE
# Both of these are PREFIX entries that also match their own _report sibling.
# The siblings have their own entries earlier in the list, so they keep the
# right permission once these go - proved in test_remove_legacy_reports.py.
# The three admin routes had their own entries in the ADMINISTRATION block too.
# Harmless once the URLs are gone, but a permission map listing paths that do
# not exist is the kind of stale rule someone later reasons from.
cut('middleware.py: the three admin permission entries', MIDDLEWARE,
    """            ('admin_unpaid', 'auth.can_access_administration'),
            ('admin_renewals', 'auth.can_access_administration'),
            ('admin_invoices', 'auth.can_access_administration'),
""",
    "('admin_unpaid', 'auth.can_access_administration')")

cut('middleware.py: the lease_renewal permission entry', MIDDLEWARE,
    "            ('lease_renewal', 'auth.can_access_tenants'),\n",
    "('lease_renewal', 'auth.can_access_tenants')")

cut('middleware.py: the open_invoices permission entry', MIDDLEWARE,
    "            ('open_invoices', 'auth.can_access_invoices'),\n",
    "('open_invoices', 'auth.can_access_invoices')")

# ============================================================ SELF-CHECKS
problems = []

# The two survivors must still be there, in full.
survivors = [
    (INV, 'def open_invoices_report', 'the Debtors Age Analysis view'),
    (ISSUES, 'def lease_renewal_report', 'the Lease Renewal report view'),
    (MIDDLEWARE, "('open_invoices_report', 'auth.can_access_tenants')",
     'the Debtors report permission entry'),
    (MIDDLEWARE, "('lease_renewal_report', 'auth.can_access_tenants')",
     'the Lease Renewal report permission entry'),
    (URLS, "name='open_invoices_report'", 'the Debtors report route'),
    (URLS, "name='lease_renewal_report'", 'the Lease Renewal report route'),
]
for path, needle, what in survivors:
    if needle not in FILES[path]['text']:
        problems.append('%s was removed - it must stay' % what)

# And nothing may still reach for the doomed modules.
for path, label in ((ADMIN, 'administration.py'), (INV, 'invoices.py'),
                    (ISSUES, 'issues.py')):
    for mod in ('import open_invoices', 'import lease_renewal'):
        if mod in FILES[path]['text']:
            problems.append('%s still does "%s"' % (label, mod))

for path, label in ((URLS, 'urls.py'),):
    for dead in ('views.admin_unpaid', 'views.admin_renewals',
                 'views.admin_invoices'):
        if dead in FILES[path]['text']:
            problems.append('%s still routes to %s' % (label, dead))

if 'admin_invoices' in FILES[TPL]['text']:
    problems.append('admin_apms.html still links admin_invoices')

live_home = os.path.join(ROOT, 'pages', 'templates', 'home.html')
if not os.path.exists(live_home):
    problems.append('pages/templates/home.html is missing - refusing to touch '
                    'home_original.html without its live counterpart present')

if problems:
    sys.exit('! self-check failed:\n  - ' + '\n  - '.join(problems))

# Compile every Python file before writing any of them.
for path in (ADMIN, INV, ISSUES, URLS, MIDDLEWARE):
    tmp = os.path.join(tempfile.gettempdir(), '_legacy_check.py')
    with io.open(tmp, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(FILES[path]['text'])
    try:
        py_compile.compile(tmp, cfile=tmp + 'c', doraise=True)
    except py_compile.PyCompileError as exc:
        sys.exit('! %s would not compile:\n%s'
                 % (os.path.relpath(path, ROOT), exc))
    finally:
        for f in (tmp, tmp + 'c'):
            if os.path.exists(f):
                os.remove(f)

print('')
for kind, label in CHANGES:
    print('  %-6s %s' % ('OK' if kind == 'apply' else 'ALREADY', label))

still_here = [m for m in DOOMED if os.path.exists(os.path.join(ROOT, m))]
print('')
if still_here:
    print('  files to delete: %s' % ', '.join(still_here))
else:
    print('  ALREADY the deleted files are already gone')
print('')

if CHECK:
    print('--check: nothing written, nothing deleted.')
    sys.exit(0)

for path in (TPL, ADMIN, INV, ISSUES, URLS, MIDDLEWARE):
    d = FILES[path]
    bak = path + '.bak_legacyreports'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    out = d['text'].replace('\n', d['nl']) if d['nl'] != '\n' else d['text']
    with io.open(path, 'w', encoding=d['enc'], newline='') as fh:
        fh.write(out)
    print('  wrote %s' % os.path.relpath(path, ROOT))

for mod in still_here:
    src = os.path.join(ROOT, mod)
    # Backed up rather than merely unlinked: git would restore these, but the
    # backup means a mistake is recoverable without touching git at all.
    shutil.copy2(src, src + '.bak_legacyreports')
    os.remove(src)
    print('  deleted %s  (kept as %s.bak_legacyreports)' % (mod, mod))

print('')
print('Done. Backups: *.bak_legacyreports')
print('Now run:  python test_remove_legacy_reports.py')
