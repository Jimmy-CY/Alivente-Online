#!/usr/bin/env python
"""
install_analysis_endpoint.py — one-shot patcher that wires the Expenses-vs-Rent
Analysis JSON endpoint (Approved + Paid expenses) into the Alivente project.

Run from the project root (where manage.py lives):

    python install_analysis_endpoint.py             # apply (backs up each file)
    python install_analysis_endpoint.py --dry-run   # preview only, writes nothing

What it does:
  1. adds `tenant, revenue` to the expenses views module's models import,
  2. appends the act_expense_analysis_data view to that module,
  3. adds the URL route next to act_expense_report_data,
  4. exports the new view from pages/views/__init__.py if names are listed there.

Safe: idempotent (re-running makes no further changes) and non-destructive
(every file it edits is copied to <file>.bak_analysis first, once).
TIP: commit or stash your work first, so you can `git diff` / revert cleanly.
"""
import os
import re
import sys

DRY = '--dry-run' in sys.argv


# ---- the view to inject (Approved + Paid) -----------------------------------
VIEW_CODE = '''

@login_required
@permission_required('auth.can_access_expenses', raise_exception=True)
def act_expense_analysis_data(request):
    """
    JSON for the Expenses-vs-Rent Analysis modal. Per property, per available
    year: collected rent (the rent of the lease covering each month; 0 for
    vacant months), months let (x/12), actual (ad-hoc) expenses, and rent source.

    Rent source: 'lease' (year-accurate from the lease rows), 'no-lease'
    (tenanted property with no lease that year -> rent 0), or 'revenue'
    (genuinely seasonal property with no leases at all -> current Financials
    "Rental" figure). Actual expenses = Approved + Paid act_expense rows, to
    match the "Expenses by Property" report.
    """
    MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
              'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

    def rent_from_leases(leases, year):
        total, let_months = 0.0, 0
        for m in range(1, 13):
            d = date(year, m, 1)
            covering = [l for l in leases
                        if l.tenant_lease_start_date and l.tenant_lease_end_date
                        and l.tenant_lease_start_date <= d <= l.tenant_lease_end_date]
            if covering:
                lease = max(covering, key=lambda l: l.tenant_lease_start_date)
                if lease.tenant_rent:
                    total += float(lease.tenant_rent)
                    let_months += 1
        return total, let_months

    def rent_from_revenue(rev_rows):
        per_month = [0.0] * 12
        for r in rev_rows:
            for i, m in enumerate(MONTHS):
                v = getattr(r, 'revenue_' + m)
                if v:
                    per_month[i] += float(v)
        return sum(per_month), sum(1 for v in per_month if v > 0)

    available_years = [
        d.year for d in act_expense.objects
            .exclude(act_expense_date__isnull=True)
            .dates('act_expense_date', 'year', order='DESC')
    ]

    properties = []
    for p in props.objects.all().order_by('prop_country', 'prop_name'):
        leases = list(tenant.objects.filter(prop=p))
        has_lease = bool(leases)
        rev_rows = None
        year_data = {}
        any_data = False

        for y in available_years:
            actual = (act_expense.objects
                      .filter(prop=p, act_expense_date__year=y,
                              act_expense_approved='Yes', act_expense_paid='Yes')
                      .aggregate(t=Sum('act_expense_amount'))['t'] or 0)
            actual = float(actual)

            if has_lease:
                rent, let_months = rent_from_leases(leases, y)
                source = 'lease' if let_months else 'no-lease'
            else:
                if rev_rows is None:
                    rev_rows = list(revenue.objects.filter(
                        prop=p,
                        revenue_line_types__revenue_line_types_name__icontains='rental',
                    ))
                rent, let_months = rent_from_revenue(rev_rows)
                source = 'revenue' if rent else 'none'

            if rent or actual:
                any_data = True
            year_data[str(y)] = {
                'rent': round(rent, 2),
                'months_let': let_months,
                'actual': round(actual, 2),
                'source': source,
            }

        if any_data:
            properties.append({
                'prop_id': p.prop_id,
                'prop_name': p.prop_name or '(Unnamed property)',
                'years': year_data,
            })

    return JsonResponse({
        'available_years': available_years,
        'properties': properties,
    })
'''

URL_LINE_TMPL = ("{indent}path('act_expense_analysis_data/', "
                 "views.act_expense_analysis_data, name='act_expense_analysis_data'),")


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def find_py(root, needle):
    """First .py under root whose text contains `needle`."""
    for dirpath, _, files in os.walk(root):
        if '__pycache__' in dirpath:
            continue
        for fn in sorted(files):
            if fn.endswith('.py'):
                p = os.path.join(dirpath, fn)
                try:
                    if needle in read(p):
                        return p
                except Exception:
                    pass
    return None


def backup(p):
    b = p + '.bak_analysis'
    if not os.path.exists(b) and not DRY:
        with open(b, 'w', encoding='utf-8') as f:
            f.write(read(p))
    return b


def write(p, text, note):
    if DRY:
        print(f"   [dry-run] would write {p}  ({note})")
        return
    backup(p)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"   [OK] {note}  -> {p} (backup: {os.path.basename(p)}.bak_analysis)")


def main():
    root = os.getcwd()
    if not os.path.exists(os.path.join(root, 'manage.py')):
        print("!! Run this from the project root (the folder with manage.py).")
        sys.exit(1)

    print("Installing the Analysis endpoint" + (" (dry run)" if DRY else "") + " ...")

    # 1) Views module (the file that defines act_expense_report_data) ----------
    vm = find_py(os.path.join(root, 'pages'), 'def act_expense_report_data(')
    if not vm:
        print("!! Could not find the expenses views module (no file defines "
              "act_expense_report_data). Nothing changed.")
        sys.exit(1)
    print(f"Views module: {vm}")
    vtext = read(vm)

    # 1a) models import: ensure tenant, revenue present
    if re.search(r'\bact_expense_analysis_data\b', vtext):
        print("   [skip] view already present in the module")
    else:
        m = re.search(r'^(from \.\.models import )([^\n]+)$', vtext, re.M)
        if not m:
            print("   [WARN] couldn't find `from ..models import ...` — add "
                  "`tenant, revenue` to that import manually.")
        else:
            names = [n.strip() for n in m.group(2).split(',')]
            for extra in ('tenant', 'revenue'):
                if extra not in names:
                    names.append(extra)
            new_import = m.group(1) + ', '.join(names)
            if new_import != m.group(0):
                vtext = vtext[:m.start()] + new_import + vtext[m.end():]
                print("   [OK] models import now includes tenant, revenue")
            else:
                print("   [skip] models import already has tenant, revenue")
        # 1b) append the view
        if not vtext.endswith('\n'):
            vtext += '\n'
        vtext += VIEW_CODE
        write(vm, vtext, "appended act_expense_analysis_data view")

    # 2) urls.py (file that names act_expense_report_data) ---------------------
    uf = find_py(os.path.join(root, 'pages'), "name='act_expense_report_data'") \
        or find_py(os.path.join(root, 'pages'), 'name="act_expense_report_data"')
    if not uf:
        print("!! Could not find the urls file. Add this route manually:\n"
              "   " + URL_LINE_TMPL.format(indent=''))
    else:
        print(f"URLs file: {uf}")
        utext = read(uf)
        if 'act_expense_analysis_data' in utext:
            print("   [skip] URL route already present")
        else:
            um = re.search(r'^(\s*)path\(\s*[\'"]act_expense_report_data/.*$',
                           utext, re.M)
            if not um:
                print("   [WARN] couldn't find the report_data route; add manually:\n"
                      "   " + URL_LINE_TMPL.format(indent=''))
            else:
                indent = um.group(1)
                insert_at = um.end()
                new_line = "\n" + URL_LINE_TMPL.format(indent=indent)
                utext = utext[:insert_at] + new_line + utext[insert_at:]
                write(uf, utext, "added act_expense_analysis_data route")

    # 3) views package export (only if names are listed explicitly) -----------
    init_p = os.path.join(root, 'pages', 'views', '__init__.py')
    if os.path.exists(init_p):
        itext = read(init_p)
        module_name = os.path.splitext(os.path.basename(vm))[0]
        if 'act_expense_analysis_data' in itext:
            print("   [skip] view already exported from pages/views/__init__.py")
        elif re.search(rf'from \.{re.escape(module_name)} import \*', itext):
            print("   [skip] __init__ uses `import *` — new view is auto-exported")
        else:
            im = re.search(r'^(\s*)act_expense_report_data\b.*$', itext, re.M)
            if im:
                indent = im.group(1)
                itext = itext[:im.end()] + "\n" + indent + \
                    "act_expense_analysis_data," + itext[im.end():]
                write(init_p, itext, "exported act_expense_analysis_data from __init__")
            else:
                sm = re.search(r'^(from \S+ import )(.*\bact_expense_report_data\b.*)$',
                               itext, re.M)
                if sm:
                    newline = sm.group(0).replace(
                        'act_expense_report_data',
                        'act_expense_report_data, act_expense_analysis_data', 1)
                    itext = itext[:sm.start()] + newline + itext[sm.end():]
                    write(init_p, itext, "exported act_expense_analysis_data from __init__")
                else:
                    print("   [WARN] pages/views/__init__.py exists but I couldn't "
                          "find where act_expense_report_data is exported. If the "
                          "URL errors with AttributeError, add act_expense_analysis_data "
                          "next to act_expense_report_data there.")
    else:
        print("   [info] no pages/views/__init__.py (single-module views) — "
              "no export step needed")

    print("\nDone." + (" (dry run — nothing written)" if DRY else
          "  Now add the URL test in your browser: /act_expense_analysis_data/"))


if __name__ == '__main__':
    main()