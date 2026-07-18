#!/usr/bin/env python
"""
upgrade_analysis_ytd.py — Step 1 of 2 (BACKEND).

Replaces the act_expense_analysis_data view with a version that returns, for
every property and year, BOTH full-year figures and YTD figures (trimmed to
January..last-completed-month of the current year), plus metadata the modal
needs (current_year, ytd_cutoff_month, ytd_month_name). It also computes one
extra earlier year so the oldest selectable year keeps its rent-change baseline.

Nothing else in your data or app changes — the endpoint just returns more.

Run from the project root (where manage.py lives):

    python upgrade_analysis_ytd.py             # apply (backs up the file once)
    python upgrade_analysis_ytd.py --dry-run   # preview only, writes nothing

Safe: idempotent (re-running makes no further changes) and non-destructive
(the file it edits is copied to <file>.bak_ytd first, once).
"""
import os
import sys

DRY = '--dry-run' in sys.argv

VIEW_CODE = '''@login_required
@permission_required('auth.can_access_expenses', raise_exception=True)
def act_expense_analysis_data(request):
    """
    JSON for the Expenses-vs-Rent Analysis modal.

    For every property and year returns BOTH full-year figures (rent,
    months_let, actual) and YTD figures (rent_ytd, months_let_ytd, actual_ytd)
    trimmed to January..<last completed month of the current year>. The front
    end uses the YTD figures whenever the current, unfinished year is being
    viewed, so an in-progress year is compared like-for-like against the same
    window of earlier years.

    Actual expenses = Approved + Paid act_expense rows.
    Rent includes levies: lease rent = tenant_rent + tenant_levies (when
    present); the revenue fallback sums both the Rental and Levies lines.
    Rent source: 'lease' | 'no-lease' | 'revenue' | 'none'.
    """
    # analysis endpoint version: ytd+levies-v2
    MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
              'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    MONTH_ABBR = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    today = date.today()
    current_year = today.year
    ytd_cutoff = today.month - 1  # last completed month; 0 in January

    def rent_from_leases(leases, year, upto):
        total, let_months = 0.0, 0
        for m in range(1, upto + 1):
            d = date(year, m, 1)
            covering = [l for l in leases
                        if l.tenant_lease_start_date and l.tenant_lease_end_date
                        and l.tenant_lease_start_date <= d <= l.tenant_lease_end_date]
            if covering:
                lease = max(covering, key=lambda l: l.tenant_lease_start_date)
                amt = (lease.tenant_rent or 0) + (lease.tenant_levies or 0)
                if amt:
                    total += float(amt)
                    let_months += 1
        return total, let_months

    def rent_from_revenue(rev_rows, upto):
        per_month = [0.0] * 12
        for r in rev_rows:
            for i, m in enumerate(MONTHS):
                v = getattr(r, 'revenue_' + m)
                if v:
                    per_month[i] += float(v)
        s = sum(per_month[:upto])
        months = sum(1 for v in per_month[:upto] if v > 0)
        return s, months

    def actual_sum(prop, year, upto):
        if upto < 1:
            return 0.0
        val = (act_expense.objects
               .filter(prop=prop, act_expense_date__year=year,
                       act_expense_date__month__lte=upto,
                       act_expense_approved='Yes', act_expense_paid='Yes')
               .aggregate(t=Sum('act_expense_amount'))['t'] or 0)
        return float(val)

    available_years = [
        d.year for d in act_expense.objects
            .exclude(act_expense_date__isnull=True)
            .dates('act_expense_date', 'year', order='DESC')
    ]

    # Also compute one earlier year, so the oldest selectable year still has a
    # prior-year baseline for its rent-change figure.
    years_to_compute = list(available_years)
    if available_years:
        years_to_compute = sorted(
            set(available_years) | {min(available_years) - 1}, reverse=True)

    properties = []
    for p in props.objects.all().order_by('prop_country', 'prop_name'):
        leases = list(tenant.objects.filter(prop=p))
        has_lease = bool(leases)
        rev_rows = None
        year_data = {}
        any_data = False

        for y in years_to_compute:
            if has_lease:
                rent_f, let_f = rent_from_leases(leases, y, 12)
                source = 'lease' if let_f else 'no-lease'
            else:
                if rev_rows is None:
                    rev_rows = list(revenue.objects.filter(
                        prop=p,
                        revenue_line_types__revenue_line_types_name__iregex=r'rental|levies',
                    ))
                rent_f, let_f = rent_from_revenue(rev_rows, 12)
                source = 'revenue' if rent_f else 'none'
            actual_f = actual_sum(p, y, 12)

            if ytd_cutoff >= 1:
                if has_lease:
                    rent_y, let_y = rent_from_leases(leases, y, ytd_cutoff)
                else:
                    rent_y, let_y = rent_from_revenue(rev_rows, ytd_cutoff)
                actual_y = actual_sum(p, y, ytd_cutoff)
            else:
                rent_y, let_y, actual_y = 0.0, 0, 0.0

            if (y in available_years) and (rent_f or actual_f):
                any_data = True
            year_data[str(y)] = {
                'rent': round(rent_f, 2), 'months_let': let_f, 'actual': round(actual_f, 2),
                'rent_ytd': round(rent_y, 2), 'months_let_ytd': let_y, 'actual_ytd': round(actual_y, 2),
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
        'current_year': current_year,
        'ytd_cutoff_month': ytd_cutoff,
        'ytd_month_name': MONTH_ABBR[ytd_cutoff - 1] if ytd_cutoff >= 1 else '',
        'properties': properties,
    })
'''


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def find_py(root, needle):
    for dp, _, files in os.walk(root):
        if '__pycache__' in dp:
            continue
        for fn in sorted(files):
            if fn.endswith('.py'):
                p = os.path.join(dp, fn)
                try:
                    if needle in read(p):
                        return p
                except Exception:
                    pass
    return None


def main():
    root = os.getcwd()
    if not os.path.exists(os.path.join(root, 'manage.py')):
        print("!! Run from the project root (the folder with manage.py).")
        sys.exit(1)

    vm = find_py(os.path.join(root, 'pages'), 'def act_expense_analysis_data(')
    if not vm:
        print("!! Couldn't find the file defining act_expense_analysis_data. "
              "Run install_analysis_endpoint.py first. Nothing changed.")
        sys.exit(1)
    print("Views module: " + vm + (" (dry run)" if DRY else ""))
    text = read(vm)

    if 'ytd+levies-v2' in text:
        print("   [skip] endpoint already at ytd+levies-v2 — nothing to do.")
        return

    lines = text.split('\n')
    def_idx = next((i for i, l in enumerate(lines)
                    if l.startswith('def act_expense_analysis_data(')), -1)
    if def_idx == -1:
        print("!! Couldn't locate the def line. Nothing changed.")
        sys.exit(1)

    # include any decorator lines directly above the def
    start = def_idx
    while start - 1 >= 0 and lines[start - 1].startswith('@'):
        start -= 1

    # end = first non-blank, non-indented line after the def (next top-level), else EOF
    end = len(lines)
    for j in range(def_idx + 1, len(lines)):
        l = lines[j]
        if l.strip() == '':
            continue
        if l[:1] not in (' ', '\t'):
            end = j
            break

    new_lines = lines[:start] + VIEW_CODE.rstrip('\n').split('\n') + [''] + lines[end:]
    new_text = '\n'.join(new_lines)

    if DRY:
        print("   [dry-run] would replace act_expense_analysis_data "
              "(lines %d-%d) with the YTD version. Nothing written." % (start + 1, end))
        return

    bak = vm + '.bak_ytd'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8') as f:
            f.write(text)
    with open(vm, 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("   [OK] act_expense_analysis_data upgraded (backup: "
          + os.path.basename(vm) + ".bak_ytd)")
    print("\nDone. Restart the dev server, then visit /act_expense_analysis_data/ "
          "— each year should now include rent_ytd / actual_ytd and the response "
          "should carry current_year / ytd_cutoff_month / ytd_month_name.")


if __name__ == '__main__':
    main()