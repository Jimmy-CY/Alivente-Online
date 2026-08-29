"""
Finance views - extracted from pages/views/main.py.

PHASE 1 - Financial-budgeting CRUD:
  - Revenue: list / add / edit / commit / types / line types
  - Expense: list / add / edit / commit / delete / types / line types
  - Valuations: list / add / edit / commit (with optional pro-rata cascade)

PHASE 2 - Reports:
  - Cash flow: cashflow_forecast
  - Occupancy: occupancy_trends_view
  - Indicators: financial_indicators_view
  - Vacancy: vacancy_management_view
  - Drill-downs: revenue_details_view, budget_expense_details_view, total_expense_details_view
  - P&L: finance_pl_act

Commit views follow a consistent pattern:
  1. Validate POST + required fields
  2. Wrap mutating work in transaction.atomic() so partial writes can't escape
  3. Catch specific exceptions (model.DoesNotExist, JSONDecodeError) with
     focused user-facing messages
  4. Catch-all logs the traceback and surfaces a generic error message
  5. Always redirect/render with a flash message - never leave a 500 white screen

Report views are read-only and don't need the atomic pattern.

Helper functions are imported from two view modules after the dashboard
and properties splits out of main.py:
  - dashboard.py: occupancy + portfolio calculations + budgeted expenses
  - properties.py: calculate_year_metrics, calculate_property_revenue
"""

import decimal
import json
import logging
import traceback
from calendar import monthrange
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import (Count, Min, OuterRef, Prefetch, Q, Subquery, Sum)
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from pages.forms import (
    RevenueForm, RevenueTypesForm, RevenueLineForm,
    ExpenseTypesForm, ExpenseLineForm, ValuesForm,
)
from pages.models import (
    _FH_MONTHS,
    props, prop_values,
    revenue, revenue_types, revenue_line_types,
    expense, expense_types, expense_line_types,
    tenant, act_expense, VacancyPeriod,
    FinancialFigureHistory, FH_BASELINE_DATE,
    record_expense_history, record_revenue_history,
    ensure_expense_baseline, ensure_revenue_baseline,
    ensure_expense_opening, ensure_revenue_opening,
    purge_figure_history, prorata_reconcile,
    record_valuation_history, property_value_as_of,
    resolve_year_months_bulk, lease_revenue_rows, current_lease_revenue,
    property_annual_lease_revenue, property_annual_budgeted_expenses,
    property_annual_actual_expenses, _lease_month,
)

# Helpers split across two modules after the dashboard / properties splits.
from .properties import (
    calculate_year_metrics,
    calculate_property_revenue,
)
from .dashboard import (
    calculate_property_budgeted_expenses,
    calculate_occupancy_metrics_with_period,
    get_property_first_tenant_date_optimized,
    calculate_effective_period,
    calculate_portfolio_occupancy_with_period,
)

# ============================================================================
# Shared
# ============================================================================

MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

logger = logging.getLogger(__name__)


# ---- Financial history (Phase 1) : effective date + user, both fail-safe ----
def _fh_date_or_today(raw):
    """Parse a YYYY-MM-DD string, falling back to today. Never raises.

    Split out of _fh_eff_date because the line-type delete arrives as a JSON
    body rather than a form-encoded POST, so there is no request.POST to read.
    """
    raw = (raw or '').strip()
    if raw:
        try:
            return datetime.strptime(raw, '%Y-%m-%d').date()
        except ValueError:
            pass
    return date.today()


def _fh_eff_date(request):
    """Effective date for a budgeted/revenue change: the form's 'effective_date'
    (YYYY-MM-DD) if supplied, otherwise today. Never raises."""
    return _fh_date_or_today(request.POST.get('effective_date'))


def _fh_user(request):
    u = getattr(request, 'user', None)
    return u if (u is not None and getattr(u, 'is_authenticated', False)) else None


def _fh_save_expense(exp, before_months, before_amount, eff, user,
                     source='budget'):
    """Baseline first, then the new version.

    The order is load-bearing. ensure_expense_baseline asks whether ANY history
    exists for the source; write the new snapshot first and it would find one,
    conclude a baseline is already there, and skip - leaving exactly the gap it
    is meant to close.
    """
    ensure_expense_baseline(exp, before_months, before_amount, user=user)
    record_expense_history(exp, eff, source=source, user=user)


def _fh_save_revenue(rev, before_months, before_amount, eff, user):
    """Baseline first, then the new version - see _fh_save_expense."""
    ensure_revenue_baseline(rev, before_months, before_amount, user=user)
    record_revenue_history(rev, eff, source='direct', user=user)


def _fh_new_expense(exp, eff, user, source, created):
    """History for a row that has just been through update_or_create.

    Only a genuinely NEW row gets an opening snapshot. If update_or_create
    matched an existing row then that row already carries history - every row
    on Live has its seed, and every row created from here on gets its opening
    snapshot at birth - so there is nothing left to open.
    """
    if created:
        ensure_expense_opening(exp, user=user)
    record_expense_history(exp, eff, source=source, user=user)


def _fh_new_revenue(rev, eff, user, source, created):
    """See _fh_new_expense."""
    if created:
        ensure_revenue_opening(rev, user=user)
    record_revenue_history(rev, eff, source=source, user=user)


def _expense_has_past(expense_id):
    """Does this row's history carry anything at all?

    One row, asked directly - the list page answers the same question for
    every row at once in _fh_attach_expense_history. Both go through the same
    definition: a snapshot carries something when any of the twelve months or
    the amount is set and not zero.

    Fails CLOSED: if the history cannot be read, the answer is "yes, it has a
    past", which keeps a row rather than removing one on a guess.
    """
    try:
        _q = Q()
        for _f in ('amount',) + tuple(_FH_MONTHS):
            _q |= Q(**{_f + '__isnull': False}) & ~Q(**{_f: 0})
        return (FinancialFigureHistory.objects
                .filter(kind=FinancialFigureHistory.KIND_BUDGET,
                        source_pk=expense_id)
                .filter(_q).exists())
    except Exception:
        logger.exception('_expense_has_past failed - assuming it has one')
        return True


def _fh_attach_expense_history(properties):
    """Hang a snapshot count and earliest date on each prefetched expense row.

    The delete dialog offers to remove a row's past, so it should be able to
    say how much past there is. One extra query for the whole page, and the
    rows come from the prefetch cache, so attributes set here are the ones the
    template sees.

    Fail-safe: a history problem must not stop the Expenses list rendering.
    """
    try:
        summary = {
            r['source_pk']: (r['n'], r['first'])
            for r in (FinancialFigureHistory.objects
                      .filter(kind=FinancialFigureHistory.KIND_BUDGET)
                      .values('source_pk')
                      .annotate(n=Count('financial_figure_history_id'),
                                first=Min('effective_date')))
        }
    except Exception:
        logger.exception('_fh_attach_expense_history failed (list still renders)')
        summary = {}

    # WHICH ROWS HAVE A PAST WORTH KEEPING.
    #
    # A closed pro-rata row is kept so the P&L can still colour the years it
    # carried a share in. That reasoning needs there to BE such a year. A row
    # whose every snapshot is zero or empty anchors nothing, and the Expenses
    # list was drawing it as an ordinary expense of zero with Delete greyed
    # out - a record the system could neither justify nor release.
    #
    # One more query for the whole page: the source_pks that have at least one
    # snapshot carrying something. A Q across the thirteen columns rather than
    # thirteen queries or a Python pass over every snapshot ever written.
    try:
        _q = Q()
        for _f in ('amount',) + tuple(_FH_MONTHS):
            _q |= Q(**{_f + '__isnull': False}) & ~Q(**{_f: 0})
        carried = set(FinancialFigureHistory.objects
                      .filter(kind=FinancialFigureHistory.KIND_BUDGET)
                      .filter(_q)
                      .values_list('source_pk', flat=True))
    except Exception:
        # Fail-safe in the same direction as the count above: if this cannot
        # be worked out, every row is treated as HAVING a past, which is the
        # conservative answer - it keeps Delete greyed out rather than
        # offering to remove something whose history we could not read.
        logger.exception('_fh_attach_expense_history: past scan failed')
        carried = None

    for _prop_row in properties:
        for _exp_row in _prop_row.expense_set.all():
            _n, _first = summary.get(_exp_row.expense_id, (0, None))
            _exp_row.fh_count = _n
            _exp_row.fh_from = _first
            _exp_row.is_closed = not (_exp_row.expense_amount or 0)
            _exp_row.fh_has_past = (True if carried is None
                                    else _exp_row.expense_id in carried)
            # SPENT: it holds nothing and never did. Only these may be
            # removed, and only these are offered a Delete.
            _exp_row.is_spent = _exp_row.is_closed and not _exp_row.fh_has_past
    return properties


def carries_a_share(qs):
    """The rows in `qs` that actually hold money.

    An un-ticked pro-rata row is CLOSED, not deleted - _fh_close_expense
    zeroes the amount and all twelve months and keeps the row, so the P&L can
    still colour earlier years. That is deliberate. What is not deliberate is
    that three screens then read "a row exists" as "this property is in the
    distribution", so a released property came back ticked, the inactive
    banner kept firing, and the next recalculation handed its share back.

    One helper for all three, so they cannot drift apart again.

    A NULL amount counts as no share too: it is a row that has never carried
    anything. Both are excluded by the same test.
    """
    return qs.exclude(expense_amount=0).exclude(expense_amount__isnull=True)


def _fh_close_expense(exp):
    """Zero a budgeted expense row, returning what it held beforehand.

    Used when a property is un-ticked from a pro-rata group. Deleting the row
    instead would take its PAST with it - the P&L only re-colours rows that
    still exist, so every prior year would silently lose that property's share.
    Zeroing keeps the row and its history, and stops it contributing from the
    effective date forward.

    The caller snapshots the result through _fh_save_expense, which writes a
    baseline first if the row never had one, so even a row closed on its very
    first edit keeps its past.
    """
    before = {m: getattr(exp, 'expense_' + m) for m in MONTHS}
    before_amount = exp.expense_amount
    exp.expense_amount = 0
    for month in MONTHS:
        setattr(exp, 'expense_' + month, 0)
    exp.save()
    return before, before_amount


# ============================================================================
# Finance landing
# ============================================================================

@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def finance(request):
    return render(request, "finance.html", {})


# ============================================================================
# Revenue
# ============================================================================

@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def finance_revenue(request):
    prop_output = request.POST.get('propname')
    base = props.objects.prefetch_related(
        Prefetch(
            'revenue_set',
            queryset=revenue.objects.select_related('revenue_line_types', 'revenue_types'),
        )
    ).all().order_by('prop_country', 'prop_name')
    if prop_output and prop_output != "All":
        base = base.filter(prop_name=prop_output)
    props_data = list(base)
    # Phase 3: Rental/Levies come from the LEASE (read-only) for leased properties;
    # the revenue table is used for seasonal / no-lease properties and for any
    # manual (non rental/levies) revenue line types.
    for _p in props_data:
        _rent, _lev, _has, _active = current_lease_revenue(_p)
        _disp = []
        if _has:
            _disp.append({'line_type': 'Rental', 'rev_type': 'From lease', 'amount': _rent,
                          'editable': False, 'from_lease': True, 'vacant': not _active, 'revenue_id': None})
            _disp.append({'line_type': 'Levies', 'rev_type': 'From lease', 'amount': _lev,
                          'editable': False, 'from_lease': True, 'vacant': not _active, 'revenue_id': None})
            for _r in _p.revenue_set.all():
                if not (_r.revenue_line_types and _r.revenue_line_types.lease_role):
                    _disp.append({'line_type': _r.revenue_line_types.revenue_line_types_name,
                                  'rev_type': _r.revenue_types.revenue_types_name if _r.revenue_types else '',
                                  'amount': _r.revenue_amount, 'editable': True, 'from_lease': False,
                                  'vacant': False, 'revenue_id': _r.revenue_id})
        else:
            for _r in _p.revenue_set.all():
                _disp.append({'line_type': _r.revenue_line_types.revenue_line_types_name,
                              'rev_type': _r.revenue_types.revenue_types_name if _r.revenue_types else '',
                              'amount': _r.revenue_amount, 'editable': True, 'from_lease': False,
                              'vacant': False, 'revenue_id': _r.revenue_id})
        _p.display_revenues = _disp
    return render(request, "finance_revenue.html", {"props_data": props_data})


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_revenue_add(request):
    # Which properties have any lease -> the form disables Rental/Levies for them
    # (rent/levies come from the lease). Seasonal / no-lease keep them selectable.
    _leased_ids = list(tenant.objects.values_list('prop_id', flat=True).distinct())
    return render(request, "finance_revenue_add.html", {
        "props_data": props.objects.all().order_by('prop_country', 'prop_name'),
        "revenue_types": revenue_types.objects.all(),
        "revenue_line_types": revenue_line_types.objects.all(),
        "leased_prop_ids": json.dumps([str(_i) for _i in _leased_ids if _i is not None]),
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_revenue_commit(request):
    if request.method != "POST":
        return redirect('finance_revenue_add')

    prop_id = request.POST.get('prop')
    rlt_id = request.POST.get('revenue_line_types')
    rt_id = request.POST.get('revenue_types')
    revenue_amount = request.POST.get('revenue_amount')

    if not all([prop_id, rlt_id, rt_id, revenue_amount]):
        messages.error(request, "Missing required fields. Please fill in all marked items.")
        return redirect('finance_revenue_add')

    # Rent/levies for a leased property come from the lease, not a manual revenue
    # row. Block adding a Rental/Levies line type for any property that has leases.
    _rlt = revenue_line_types.objects.filter(pk=rlt_id).first()
    if _rlt and _rlt.lease_role and tenant.objects.filter(prop_id=prop_id).exists():
        messages.info(request, "Rent and levies for a leased property come from the lease \u2014 add or edit the lease instead of a revenue row.")
        return redirect('finance_revenue_add')

    try:
        with transaction.atomic():
            revenue_type = revenue_types.objects.get(revenue_types_id=rt_id)

            monthly_data = {
                'prop_id': prop_id,
                'revenue_line_types_id': rlt_id,
                'revenue_types_id': rt_id,
                'revenue_amount': revenue_amount,
            }
            for month in MONTHS:
                if getattr(revenue_type, f'revenue_types_{month}') == "Yes":
                    monthly_data[f'revenue_{month}'] = revenue_amount

            _fh_rev, _fh_created = revenue.objects.update_or_create(
                prop_id=prop_id,
                revenue_line_types_id=rlt_id,
                revenue_types_id=rt_id,
                defaults=monthly_data,
            )
            _fh_eff = _fh_eff_date(request)
            _fh_who = _fh_user(request)
            transaction.on_commit(
                lambda o=_fh_rev, c=_fh_created, e=_fh_eff, u=_fh_who:
                    _fh_new_revenue(o, e, u, 'direct', c))
            messages.success(request, "Revenue added successfully.")
            return redirect('finance_revenue')

    except revenue_types.DoesNotExist:
        messages.error(request, "Invalid revenue type.")
        return redirect('finance_revenue_add')
    except Exception as e:
        logger.exception("finance_revenue_commit failed")
        messages.error(request, f"Couldn't save the revenue: {e}")
        return redirect('finance_revenue_add')


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_revenue_edit(request, revenue_id):
    rev = get_object_or_404(revenue, pk=revenue_id)
    if rev.revenue_line_types and rev.revenue_line_types.lease_role and tenant.objects.filter(prop=rev.prop).exists():
        messages.info(request, "Rent and levies come from the lease for this property \u2014 edit the lease to change them.")
        return redirect('finance_revenue')
    return render(request, "finance_revenue_edit.html", {
        "rev": rev,
        "props_data": props.objects.all().order_by('prop_country', 'prop_name'),
        "revenue_types": revenue_types.objects.all(),
        "revenue_line_types": revenue_line_types.objects.all(),
        "form": RevenueForm(instance=rev),
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
@require_POST
def finance_revenue_edit_commit(request, revenue_id):
    rev = get_object_or_404(revenue, pk=revenue_id)

    if request.method != "POST":
        return redirect('finance_revenue_edit', revenue_id=revenue_id)

    prop_id = request.POST.get('prop')
    rlt_id = request.POST.get('revenue_line_types')
    rt_id = request.POST.get('revenue_types')
    revenue_amount = request.POST.get('revenue_amount')

    if not all([prop_id, rlt_id, rt_id, revenue_amount]):
        messages.error(request, "Missing required fields. Please fill in all marked items.")
        return redirect('finance_revenue_edit', revenue_id=revenue_id)

    try:
        with transaction.atomic():
            revenue_type = revenue_types.objects.get(revenue_types_id=rt_id)

            monthly_data = {
                'prop_id': prop_id,
                'revenue_line_types_id': rlt_id,
                'revenue_types_id': rt_id,
                'revenue_amount': revenue_amount,
            }
            for month in MONTHS:
                if getattr(revenue_type, f'revenue_types_{month}') == "Yes":
                    monthly_data[f'revenue_{month}'] = revenue_amount
                else:
                    monthly_data[f'revenue_{month}'] = None

            # See the expense edit: the pre-edit values are the line's only
            # record of its own past until a baseline exists.
            _fh_before = {m: getattr(rev, 'revenue_' + m) for m in MONTHS}
            _fh_before_amount = rev.revenue_amount

            for key, value in monthly_data.items():
                setattr(rev, key, value)
            rev.save()
            _fh_eff = _fh_eff_date(request)
            _fh_who = _fh_user(request)
            transaction.on_commit(
                lambda o=rev, b=_fh_before, a=_fh_before_amount,
                       e=_fh_eff, u=_fh_who: _fh_save_revenue(o, b, a, e, u))

            messages.success(request, "Revenue updated successfully.")
            return redirect('finance_revenue')

    except revenue_types.DoesNotExist:
        messages.error(request, "Invalid revenue type.")
        return redirect('finance_revenue_edit', revenue_id=revenue_id)
    except Exception as e:
        logger.exception("finance_revenue_edit_commit failed")
        messages.error(request, f"Couldn't update the revenue: {e}")
        return redirect('finance_revenue_edit', revenue_id=revenue_id)


# ============================================================================
# Revenue types
# ============================================================================

@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def finance_revenue_types(request):
    return render(request, "finance_revenue_types.html", {
        "rtresults": revenue_types.objects.all(),
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_revenue_types_add(request):
    return render(request, "finance_revenue_types_add.html", {
        "rtresults": revenue_types.objects.all().order_by('revenue_types_name'),
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_revenue_types_commit(request):
    if request.method == "POST":
        form = RevenueTypesForm(request.POST or None)
        try:
            with transaction.atomic():
                if form.is_valid():
                    form.save()
                    messages.success(request, "Revenue type added successfully.")
                else:
                    messages.error(request, "Please correct the errors below.")
        except Exception as e:
            logger.exception("finance_revenue_types_commit failed")
            messages.error(request, f"Couldn't save the revenue type: {e}")
    return render(request, "finance_revenue_types.html", {
        "rtresults": revenue_types.objects.all(),
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_revenue_types_edit(request, revenue_types_id):
    return render(request, "finance_revenue_types_edit.html", {
        "rtresults": revenue_types.objects.filter(pk=revenue_types_id),
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_revenue_types_edit_commit(request, revenue_types_id):
    rev = get_object_or_404(revenue_types, pk=revenue_types_id)
    all_types = revenue_types.objects.all().order_by('revenue_types_name')

    if request.method == "POST":
        name = request.POST.get('revenue_types_name', '').strip()

        if revenue_types.objects.filter(
            revenue_types_name__iexact=name
        ).exclude(pk=revenue_types_id).exists():
            messages.error(request, "No duplicate Revenue Types Allowed")
            return render(request, "finance_revenue_types.html", {
                "rtresults": all_types, "rev": rev, "name_error": True,
            })

        try:
            with transaction.atomic():
                form = RevenueTypesForm(request.POST, instance=rev)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Revenue Type Edited Successfully")
                    return redirect('finance_revenue_types')
                else:
                    messages.error(request, "Please correct the errors below.")
        except Exception as e:
            logger.exception("finance_revenue_types_edit_commit failed")
            messages.error(request, f"Couldn't update the revenue type: {e}")

    return render(request, "finance_revenue_types.html", {
        "rtresults": all_types, "rev": rev,
    })


# ============================================================================
# Revenue line types
# ============================================================================

@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def finance_revenue_line_types(request):
    return render(request, "finance_revenue_line_types.html", {
        "rltresults": revenue_line_types.objects.all(),
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_revenue_line_types_add(request):
    return render(request, "finance_revenue_line_types_add.html", {
        "rltresults": revenue_line_types.objects.all().order_by('revenue_line_types_name'),
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_revenue_line_types_commit(request):
    if request.method == "POST":
        form = RevenueLineForm(request.POST or None)
        try:
            with transaction.atomic():
                if form.is_valid():
                    form.save()
                    messages.success(request, "Revenue Line Type added successfully.")
                else:
                    messages.error(request, "Please correct the errors below.")
        except Exception as e:
            logger.exception("finance_revenue_line_types_commit failed")
            messages.error(request, f"Couldn't save the revenue line type: {e}")
    return render(request, "finance_revenue_line_types.html", {
        "rltresults": revenue_line_types.objects.all(),
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_revenue_line_types_edit(request, revenue_line_types_id):
    return render(request, "finance_revenue_line_types_edit.html", {
        "rltresults": revenue_line_types.objects.filter(pk=revenue_line_types_id),
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_revenue_line_types_edit_commit(request, revenue_line_types_id):
    rev = get_object_or_404(revenue_line_types, pk=revenue_line_types_id)
    all_types = revenue_line_types.objects.all().order_by('revenue_line_types_name')

    if request.method == "POST":
        name = request.POST.get('revenue_line_types_name', '').strip()

        if revenue_line_types.objects.filter(
            revenue_line_types_name__iexact=name
        ).exclude(pk=revenue_line_types_id).exists():
            messages.error(request, "No duplicate Revenue Line Types Allowed")
            return render(request, "finance_revenue_line_types.html", {
                "rltresults": all_types, "rev": rev, "name_error": True,
            })

        try:
            with transaction.atomic():
                form = RevenueLineForm(request.POST, instance=rev)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Revenue Line Type Edited Successfully")
                    return redirect('finance_revenue_line_types')
                else:
                    messages.error(request, "Please correct the errors below.")
        except Exception as e:
            logger.exception("finance_revenue_line_types_edit_commit failed")
            messages.error(request, f"Couldn't update the revenue line type: {e}")

    return render(request, "finance_revenue_line_types.html", {
        "rltresults": all_types, "rev": rev,
    })


# ============================================================================
# Expense
# ============================================================================

def expense_matrix(line_type_id, today_year=None):
    """One line type, resolved year by year, property by property.

    Returns {line_type, years, rows, totals, grand_total, first_year} where a
    row is {prop_id, prop_name, cells, total} and a cell is either a Decimal
    or None. NONE MEANS "not in the distribution that year" - a figure of
    zero is reported as None, deliberately, so the screen can draw a dash and
    the reader can tell a property that left from one that cost nothing.

    THE FIGURES COME FROM THE SAME RESOLVER THE P&L USES,
    resolve_year_months_bulk, rather than a second implementation of
    effective dating. Two answers to "what did this row carry in 2024" is one
    more than this system can afford.

    IT DOES NOT PRO-RATE. property_annual_budgeted_expenses counts a
    property's budget only from the month it came into service, which is
    right for the P&L - it is answering "what did this cost me". This screen
    answers "how is this charge split", and the charge is distributed by
    value whether or not the property was owned all year. Pro-rating here
    would leave a column summing to less than the charge under a footer
    claiming to be the charge. The template says so under the table.

    Carries no decorators: it is a helper, not a view.
    """
    from django.db.models import Min as _Min

    rows_qs = (expense.objects
               .filter(expense_line_types_id=line_type_id)
               .select_related('prop'))
    by_prop = {}
    for e in rows_qs:
        by_prop.setdefault(e.prop_id, {'prop_name': (e.prop.prop_name
                                                     if e.prop else 'Unknown'),
                                       'sources': []})
        by_prop[e.prop_id]['sources'].append(e)
    if not by_prop:
        return {'line_type': None, 'years': [], 'rows': [], 'totals': [],
                'grand_total': Decimal('0'), 'first_year': None}

    try:
        lt = expense_line_types.objects.get(expense_line_types_id=line_type_id)
    except expense_line_types.DoesNotExist:
        lt = None

    # The earliest year this line type actually CHANGED in.
    #
    # NOT the earliest history row. FH_BASELINE_DATE is 2000-01-01 and it is a
    # SENTINEL, not a date: _ensure_baseline writes one row at it the first
    # time a long-standing figure is edited, meaning "and it held this before
    # anybody recorded a change". Reading it as data made this table open on
    # the year 2000 and draw twenty-eight identical columns - the same figure
    # restated once a year for a quarter of a century, which is the baseline
    # being resolved forward, not a history.
    #
    # A baseline says the figure reaches back indefinitely, so it gives no
    # earliest year at all. With nothing but baselines, nothing has ever
    # changed and there is no past worth a column: start at the current year.
    _now = today_year or date.today().year
    _src_ids = [e.expense_id for v in by_prop.values() for e in v['sources']]
    _first = (FinancialFigureHistory.objects
              .filter(kind=FinancialFigureHistory.KIND_BUDGET,
                      source_pk__in=_src_ids)
              .exclude(effective_date=FH_BASELINE_DATE)
              .aggregate(_m=_Min('effective_date'))['_m'])
    first_year = _first.year if _first else _now
    if first_year > _now:
        first_year = _now
    years = list(range(first_year, _now + 2))          # through NEXT year

    prop_ids = list(by_prop.keys())
    cells = {pid: [] for pid in prop_ids}
    for y in years:
        vals_map = resolve_year_months_bulk(
            prop_ids, FinancialFigureHistory.KIND_BUDGET, y)
        for pid in prop_ids:
            total = Decimal('0')
            for e in by_prop[pid]['sources']:
                vals = vals_map.get(e.expense_id)
                if vals is not None:
                    for v in vals:
                        total += (v or 0)
                else:
                    # No history for this row: its live cells apply, which is
                    # the same fallback the P&L takes.
                    for m in MONTHS:
                        total += (getattr(e, 'expense_' + m, 0) or 0)
            cells[pid].append(total if total else None)

    rows = []
    for pid in prop_ids:
        _c = cells[pid]
        rows.append({
            'prop_id': pid,
            'prop_name': by_prop[pid]['prop_name'],
            'cells': _c,
            'total': sum((v for v in _c if v is not None), Decimal('0')),
        })
    # A property that carried nothing in ANY year is not a contributor to
    # this distribution and would draw a row of dashes.
    rows = [r for r in rows if r['total']]
    rows.sort(key=lambda r: (r['prop_name'] or '').lower())

    # Summed from the rows the table draws, not from a second query - the
    # lesson the Valuations round left, where a TOTAL counted a valuation the
    # table never showed.
    totals = [sum((r['cells'][i] for r in rows if r['cells'][i] is not None),
                  Decimal('0')) for i in range(len(years))]
    return {
        'line_type': lt,
        'years': years,
        'rows': rows,
        'totals': totals,
        'grand_total': sum(totals, Decimal('0')),
        'first_year': first_year,
    }


@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def finance_expense(request):
    prop_output = request.POST.get('propname')
    if prop_output is None or prop_output == "All":
        props_data = props.objects.prefetch_related(
            Prefetch(
                'expense_set',
                queryset=expense.objects.select_related('expense_line_types', 'expense_types'),
            )
        ).all().order_by('prop_country', 'prop_name')
    else:
        props_data = props.objects.prefetch_related(
            Prefetch(
                'expense_set',
                queryset=expense.objects.select_related('expense_line_types', 'expense_types'),
            )
        ).all().order_by('prop_country', 'prop_name').filter(prop_name=prop_output)
    props_data = _fh_attach_expense_history(list(props_data))

    # The second view. Chosen by a GET parameter rather than by JavaScript so
    # the state is in the URL - it can be linked, bookmarked and reloaded, and
    # the matrix is not built at all when nobody is looking at it.
    view_mode = 'matrix' if request.GET.get('view') == 'matrix' else 'property'
    matrix = None
    matrix_line_types = list(
        expense_line_types.objects
        .filter(expense_line_types_id__in=expense.objects.values(
            'expense_line_types_id'))
        .order_by('expense_line_types_name'))
    selected_lt = None
    if view_mode == 'matrix' and matrix_line_types:
        try:
            selected_lt = int(request.GET.get('lt') or 0)
        except (TypeError, ValueError):
            selected_lt = 0
        if selected_lt not in [l.expense_line_types_id for l in matrix_line_types]:
            selected_lt = matrix_line_types[0].expense_line_types_id
        matrix = expense_matrix(selected_lt)

    return render(request, "finance_expense.html", {
        "props_data": props_data,
        "view_mode": view_mode,
        "matrix": matrix,
        "matrix_line_types": matrix_line_types,
        "selected_lt": selected_lt,
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_expense_add(request):
    props_data = props.objects.all().order_by('prop_country', 'prop_name').annotate(
        current_value=Coalesce(
            Subquery(
                prop_values.objects.filter(prop_id=OuterRef('prop_id'))
                .values('prop_values_current_value')[:1]
            ),
            0,
        )
    )
    return render(request, "finance_expense_add.html", {
        "props_data": props_data,
        "expense_types": expense_types.objects.all(),
        "expense_line_types": expense_line_types.objects.all().order_by('expense_line_types_name'),
        "countries": props.objects.values_list('prop_country', flat=True).distinct().order_by('prop_country'),
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_expense_commit(request):
    if request.method != "POST":
        return redirect('finance_expense_add')

    prop_id = request.POST.get('prop')
    elt_id = request.POST.get('expense_line_types')
    et_id = request.POST.get('expense_types')
    expense_amount = request.POST.get('expense_amount')
    prorata_data = request.POST.get('prorata_calculation_data')

    if not all([prop_id, elt_id, et_id, expense_amount]):
        messages.error(request, "Missing required fields. Please fill in all marked items.")
        return redirect('finance_expense_add')

    try:
        with transaction.atomic():
            expense_type = expense_types.objects.get(expense_types_id=et_id)

            if prorata_data and prorata_data != 'undefined':
                parsed = json.loads(prorata_data)
                selected_properties = parsed.get('selected_properties', [])

                if not selected_properties:
                    messages.error(request, "No properties selected for pro-rata distribution.")
                    return redirect('finance_expense_add')

                # The shares must add up to the charge. Whatever the browser
                # sent, reconcile against the posted total before saving - see
                # prorata_reconcile. This is why Company Tax read 6,599.98.
                _pr_total = parsed.get('pro_rata_amount')
                if _pr_total is not None and selected_properties:
                    _pr_fixed = prorata_reconcile(
                        _pr_total,
                        [p.get('calculated_amount') for p in selected_properties])
                    for _pr_row, _pr_amt in zip(selected_properties, _pr_fixed):
                        _pr_row['calculated_amount'] = _pr_amt

                for property_data in selected_properties:
                    monthly_data = {
                        'prop_id': property_data['prop_id'],
                        'expense_line_types_id': elt_id,
                        'expense_types_id': et_id,
                        'expense_amount': property_data['calculated_amount'],
                    }
                    for month in MONTHS:
                        if getattr(expense_type, f'expense_types_{month}') == "Yes":
                            monthly_data[f'expense_{month}'] = property_data['calculated_amount']
                    _fh_exp, _fh_created = expense.objects.update_or_create(
                        prop_id=property_data['prop_id'],
                        expense_line_types_id=elt_id,
                        expense_types_id=et_id,
                        defaults=monthly_data,
                    )
                    _fh_eff = _fh_eff_date(request)
                    _fh_who = _fh_user(request)
                    transaction.on_commit(
                        lambda o=_fh_exp, c=_fh_created, e=_fh_eff, u=_fh_who:
                            _fh_new_expense(o, e, u, 'prorata', c))

                messages.success(request, f"{len(selected_properties)} pro-rata expenses created successfully.")
                return redirect('finance_expense')

            monthly_data = {
                'prop_id': prop_id,
                'expense_line_types_id': elt_id,
                'expense_types_id': et_id,
                'expense_amount': expense_amount,
            }
            for month in MONTHS:
                if getattr(expense_type, f'expense_types_{month}') == "Yes":
                    monthly_data[f'expense_{month}'] = expense_amount

            _fh_exp, _fh_created = expense.objects.update_or_create(
                prop_id=prop_id,
                expense_line_types_id=elt_id,
                expense_types_id=et_id,
                defaults=monthly_data,
            )
            _fh_eff = _fh_eff_date(request)
            _fh_who = _fh_user(request)
            transaction.on_commit(
                lambda o=_fh_exp, c=_fh_created, e=_fh_eff, u=_fh_who:
                    _fh_new_expense(o, e, u, 'budget', c))
            messages.success(request, "Expense added successfully.")
            return redirect('finance_expense')

    except expense_types.DoesNotExist:
        messages.error(request, "Invalid expense type.")
        return redirect('finance_expense_add')
    except json.JSONDecodeError:
        messages.error(request, "Invalid pro-rata data — please recalculate.")
        return redirect('finance_expense_add')
    except Exception as e:
        logger.exception("finance_expense_commit failed")
        messages.error(request, f"Couldn't save the expense: {e}")
        return redirect('finance_expense_add')


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_expense_edit(request, expense_id):
    try:
        existing_expense = expense.objects.get(expense_id=expense_id)
    except expense.DoesNotExist:
        messages.error(request, "Expense not found")
        return redirect('finance_expense')

    props_data = props.objects.all().order_by('prop_country', 'prop_name').annotate(
        current_value=Coalesce(
            Subquery(
                prop_values.objects.filter(prop_id=OuterRef('prop_id'))
                .values('prop_values_current_value')[:1]
            ),
            0,
        )
    )

    # Which boxes are pre-ticked. A row closed by a previous un-tick is
    # still here - kept on purpose, so earlier years keep their share - but
    # it is no longer in the distribution, and ticking it again is how the
    # share got handed back.
    linked_property_ids = list(
        carries_a_share(expense.objects.filter(
            expense_line_types_id=existing_expense.expense_line_types_id,
            expense_types_id=existing_expense.expense_types_id,
        )).values_list('prop_id', flat=True)
    )

    return render(request, "finance_expense_edit.html", {
        "props_data": props_data,
        "expense_types": expense_types.objects.all(),
        "expense_line_types": expense_line_types.objects.all().order_by('expense_line_types_name'),
        "existing_expense": existing_expense,
        "linked_property_ids": linked_property_ids,
        "countries": props.objects.values_list('prop_country', flat=True).distinct().order_by('prop_country'),
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
@require_POST
def finance_expense_edit_commit(request, expense_id):
    try:
        existing_expense = expense.objects.get(expense_id=expense_id)
    except expense.DoesNotExist:
        messages.error(request, "Expense not found.")
        return redirect('finance_expense')

    if request.method != "POST":
        return redirect('finance_expense_edit', expense_id=expense_id)

    prop_id = request.POST.get('prop')
    elt_id = request.POST.get('expense_line_types')
    et_id = request.POST.get('expense_types')
    expense_amount = request.POST.get('expense_amount')
    prorata_data = request.POST.get('prorata_calculation_data')

    if not all([prop_id, elt_id, et_id, expense_amount]):
        messages.error(request, "Missing required fields. Please fill in all marked items.")
        return redirect('finance_expense_edit', expense_id=expense_id)

    try:
        with transaction.atomic():
            expense_type = expense_types.objects.get(expense_types_id=et_id)

            if prorata_data and prorata_data != 'undefined':
                parsed = json.loads(prorata_data)
                selected_properties = parsed.get('selected_properties', [])

                if not selected_properties:
                    messages.error(request, "No properties selected for pro-rata distribution.")
                    return redirect('finance_expense_edit', expense_id=expense_id)

                # The shares must add up to the charge. Whatever the browser
                # sent, reconcile against the posted total before saving - see
                # prorata_reconcile. This is why Company Tax read 6,599.98.
                _pr_total = parsed.get('pro_rata_amount')
                if _pr_total is not None and selected_properties:
                    _pr_fixed = prorata_reconcile(
                        _pr_total,
                        [p.get('calculated_amount') for p in selected_properties])
                    for _pr_row, _pr_amt in zip(selected_properties, _pr_fixed):
                        _pr_row['calculated_amount'] = _pr_amt

                # Resolve the date and user NOW - request state should not be
                # read from inside an on_commit callback.
                _fh_eff = _fh_eff_date(request)
                _fh_who = _fh_user(request)

                # Every row currently in the group, under its ORIGINAL key,
                # captured before anything moves - so a change of line type or
                # expense type leaves nothing stranded.
                _fh_old_group = list(expense.objects.filter(
                    expense_line_types_id=existing_expense.expense_line_types_id,
                    expense_types_id=existing_expense.expense_types_id,
                ).order_by('expense_id'))
                _fh_kept = set()

                for property_data in selected_properties:
                    monthly_data = {
                        'prop_id': property_data['prop_id'],
                        'expense_line_types_id': elt_id,
                        'expense_types_id': et_id,
                        'expense_amount': property_data['calculated_amount'],
                    }
                    # All twelve, not just the "Yes" ones - otherwise a month
                    # left over from a previous expense type survives the edit.
                    for month in MONTHS:
                        monthly_data[f'expense_{month}'] = (
                            property_data['calculated_amount']
                            if getattr(expense_type, f'expense_types_{month}') == "Yes"
                            else None)

                    # Match on the natural key the add screen already treats as
                    # unique. Updating in place is the entire point: history is
                    # keyed on expense_id, so recreating the row orphans it.
                    _fh_matches = list(expense.objects.filter(
                        prop_id=property_data['prop_id'],
                        expense_line_types_id=elt_id,
                        expense_types_id=et_id,
                    ).order_by('expense_id'))

                    if _fh_matches:
                        _fh_exp = _fh_matches[0]
                        _fh_before = {m: getattr(_fh_exp, 'expense_' + m) for m in MONTHS}
                        _fh_before_amount = _fh_exp.expense_amount
                        for field, value in monthly_data.items():
                            setattr(_fh_exp, field, value)
                        _fh_exp.save()
                        _fh_kept.add(_fh_exp.expense_id)
                        transaction.on_commit(
                            lambda o=_fh_exp, b=_fh_before, a=_fh_before_amount,
                                   e=_fh_eff, u=_fh_who:
                                _fh_save_expense(o, b, a, e, u, 'prorata'))

                        # A duplicate under the same natural key should not
                        # exist - the add screen's update_or_create assumes it
                        # cannot - but if one ever does, close it rather than
                        # leave a second live row contributing silently.
                        for _fh_dup in _fh_matches[1:]:
                            _fh_kept.add(_fh_dup.expense_id)
                            _fh_b, _fh_a = _fh_close_expense(_fh_dup)
                            transaction.on_commit(
                                lambda o=_fh_dup, b=_fh_b, a=_fh_a,
                                       e=_fh_eff, u=_fh_who:
                                    _fh_save_expense(o, b, a, e, u, 'prorata'))
                    else:
                        _fh_exp = expense.objects.create(**monthly_data)
                        _fh_kept.add(_fh_exp.expense_id)
                        transaction.on_commit(
                            lambda o=_fh_exp, e=_fh_eff, u=_fh_who:
                                _fh_new_expense(o, e, u, 'prorata', True))

                # Un-ticked, or left behind by a change of line/expense type.
                # Zeroed rather than deleted, so earlier years keep the share
                # this property genuinely carried.
                for _fh_old in _fh_old_group:
                    if _fh_old.expense_id in _fh_kept:
                        continue
                    _fh_b, _fh_a = _fh_close_expense(_fh_old)
                    transaction.on_commit(
                        lambda o=_fh_old, b=_fh_b, a=_fh_a,
                               e=_fh_eff, u=_fh_who:
                            _fh_save_expense(o, b, a, e, u, 'prorata'))

                messages.success(request, f"{len(selected_properties)} pro-rata expenses updated successfully.")
                return redirect('finance_expense')

            monthly_data = {
                'prop_id': prop_id,
                'expense_line_types_id': elt_id,
                'expense_types_id': et_id,
                'expense_amount': expense_amount,
                'expense_jan': None, 'expense_feb': None, 'expense_mar': None,
                'expense_apr': None, 'expense_may': None, 'expense_jun': None,
                'expense_jul': None, 'expense_aug': None, 'expense_sep': None,
                'expense_oct': None, 'expense_nov': None, 'expense_dec': None,
            }
            for month in MONTHS:
                if getattr(expense_type, f'expense_types_{month}') == "Yes":
                    monthly_data[f'expense_{month}'] = expense_amount

            # Capture what the row held BEFORE the edit. If this is the
            # line's first ever change, that value exists in no snapshot
            # anywhere, and without one every earlier month resolves to
            # nothing - which is how a whole year of Company Tax vanished.
            _fh_before = {m: getattr(existing_expense, 'expense_' + m) for m in MONTHS}
            _fh_before_amount = existing_expense.expense_amount

            for field, value in monthly_data.items():
                setattr(existing_expense, field, value)
            existing_expense.save()
            # Resolve the date and user NOW, not at commit time - request state
            # should not be read from inside an on_commit callback.
            _fh_eff = _fh_eff_date(request)
            _fh_who = _fh_user(request)
            transaction.on_commit(
                lambda o=existing_expense, b=_fh_before, a=_fh_before_amount,
                       e=_fh_eff, u=_fh_who: _fh_save_expense(o, b, a, e, u))

            messages.success(request, "Expense updated successfully.")
            return redirect('finance_expense')

    except expense_types.DoesNotExist:
        messages.error(request, "Invalid expense type.")
        return redirect('finance_expense_edit', expense_id=expense_id)
    except json.JSONDecodeError:
        messages.error(request, "Invalid pro-rata data — please recalculate.")
        return redirect('finance_expense_edit', expense_id=expense_id)
    except Exception as e:
        logger.exception("finance_expense_edit_commit failed")
        messages.error(request, f"Couldn't update the expense: {e}")
        return redirect('finance_expense_edit', expense_id=expense_id)


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
@require_POST
def finance_expense_delete(request, expense_id):
    """
    Delete a budgeted expense row.

    Hard delete - mirrors the mark_deleted pattern from act_expense. Budgeted
    expenses are planning data (not financial transactions), so a true
    audit-trail soft delete isn't required here.

    For pro-rata expenses, this deletes only the single row clicked. Other
    properties in the same pro-rata group remain. To remove the whole
    distribution, the user deletes each row individually.
    """
    if request.method != "POST":
        return redirect('finance_expense')

    # Two very different meanings of "delete", and only the person clicking
    # knows which one they mean:
    #   close  it stops from a date; every earlier year keeps its figures
    #   purge  it never happened; the row AND its history go
    # Defaults to close, so a stray POST cannot destroy an audit trail.
    mode = (request.POST.get('delete_mode') or 'close').strip().lower()

    try:
        exp = get_object_or_404(expense, expense_id=expense_id)

        # A pro-rata row is a SHARE of the amount held on the line type, not a
        # figure in its own right. Remove one row and the rest still hold
        # shares computed for a larger split, so the line quietly stops adding
        # up to the charge actually owed - and nothing flags it.
        #
        # Un-ticking the property on the edit screen re-divides the amount
        # across the others and closes this row with the same zero snapshot.
        # That is the correct operation, so it is the only one offered.
        #
        # Blocked for BOTH modes. One slice of a distribution is never
        # independently a mistake: either the whole distribution is wrong (in
        # which case the line type is deleted) or one property does not belong
        # (in which case it is un-ticked).
        # ... EXCEPT when the row holds nothing and never did.
        #
        # The paragraph above is exactly right about a LIVE row. A CLOSED one
        # holds no share - the others were re-divided when it was un-ticked -
        # so removing it changes no figure anywhere. And if its history is
        # empty too, there is no past for the row to anchor. The guard was
        # testing what the row IS rather than what it HOLDS.
        _is_prorata = ((getattr(exp.expense_line_types,
                                'expense_line_types_prorata', '')
                        or '').strip().lower() == 'yes')
        _closed = not (exp.expense_amount or 0)
        _has_past = _expense_has_past(exp.expense_id)

        if _is_prorata and not (_closed and not _has_past):
            # Two different situations, and they need different advice.
            if _closed and _has_past:
                messages.error(
                    request,
                    "That row is already closed, and it is kept on purpose: "
                    "earlier years still report the share it carried. "
                    "Removing it would take that past with it.")
            else:
                messages.error(
                    request,
                    "That is a pro-rata expense, so it cannot be deleted on "
                    "its own \u2014 the other properties would be left holding "
                    "shares of a larger split and the line would no longer "
                    "add up. Edit the line and un-tick the property instead: "
                    "the rest take up its share, and this one stops from the "
                    "date you choose.")
            return redirect('finance_expense')

        if _is_prorata:
            # Spent: closed, and with nothing behind it. Closing it again
            # would do nothing, so the only meaningful operation is removal.
            mode = 'purge'

        with transaction.atomic():
            prop_name = exp.prop.prop_name if exp.prop else f"#{exp.expense_id}"
            type_name = exp.expense_types.expense_types_name if exp.expense_types else ""
            label = f"{prop_name}" + (f" — {type_name}" if type_name else "")

            if mode == 'purge':
                purge_figure_history(FinancialFigureHistory.KIND_BUDGET,
                                     exp.expense_id)
                exp.delete()
                note = "removed completely, history included"
            else:
                _fh_eff = _fh_eff_date(request)
                _fh_who = _fh_user(request)
                _fh_before, _fh_before_amount = _fh_close_expense(exp)
                transaction.on_commit(
                    lambda o=exp, b=_fh_before, a=_fh_before_amount,
                           e=_fh_eff, u=_fh_who:
                        _fh_save_expense(o, b, a, e, u, 'closed'))
                note = (f"stopped from {_fh_eff:%d %b %Y}; "
                        f"earlier years keep their figures")

        messages.success(request, f"Expense '{label}' {note}.")
    except Exception as e:
        logger.exception("finance_expense_delete failed")
        messages.error(request, f"Couldn't delete the expense: {e}")

    return redirect('finance_expense')


# ============================================================================
# Expense types
# ============================================================================

@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def finance_expense_types(request):
    return render(request, "finance_expense_types.html", {
        "etresults": expense_types.objects.all(),
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_expense_types_add(request):
    return render(request, "finance_expense_types_add.html", {
        "etresults": expense_types.objects.all().order_by('expense_types_name'),
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_expense_types_commit(request):
    if request.method == "POST":
        form = ExpenseTypesForm(request.POST or None)
        try:
            with transaction.atomic():
                if form.is_valid():
                    form.save()
                    messages.success(request, "Expense type added successfully.")
                else:
                    messages.error(request, "Please correct the errors below.")
        except Exception as e:
            logger.exception("finance_expense_types_commit failed")
            messages.error(request, f"Couldn't save the expense type: {e}")
    return render(request, "finance_expense_types.html", {
        "etresults": expense_types.objects.all(),
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_expense_types_edit(request, expense_types_id):
    return render(request, "finance_expense_types_edit.html", {
        "etresults": expense_types.objects.filter(pk=expense_types_id),
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_expense_types_edit_commit(request, expense_types_id):
    exp = get_object_or_404(expense_types, pk=expense_types_id)
    all_types = expense_types.objects.all().order_by('expense_types_name')

    if request.method == "POST":
        name = request.POST.get('expense_types_name', '').strip()

        if expense_types.objects.filter(
            expense_types_name__iexact=name
        ).exclude(pk=expense_types_id).exists():
            messages.error(request, "No duplicate Expense Types Allowed")
            return render(request, "finance_expense_types.html", {
                "etresults": all_types, "exp": exp, "name_error": True,
            })

        try:
            with transaction.atomic():
                form = ExpenseTypesForm(request.POST, instance=exp)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Expense Type Edited Successfully")
                    return redirect('finance_expense_types')
                else:
                    messages.error(request, "Please correct the errors below.")
        except Exception as e:
            logger.exception("finance_expense_types_edit_commit failed")
            messages.error(request, f"Couldn't update the expense type: {e}")

    return render(request, "finance_expense_types.html", {
        "etresults": all_types, "exp": exp,
    })


# ============================================================================
# Expense line types
# ============================================================================

@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def finance_expense_line_types(request):
    return render(request, "finance_expense_line_types.html", {
        "eltresults": expense_line_types.objects.all().order_by('expense_line_types_name'),
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_expense_line_types_add(request):
    return render(request, "finance_expense_line_types_add.html", {
        "eltresults": expense_line_types.objects.all(),
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_expense_line_types_commit(request):
    if request.method == "POST":
        form = ExpenseLineForm(request.POST or None)
        try:
            with transaction.atomic():
                if form.is_valid():
                    form.save()
                    messages.success(request, "Expense Line Type added successfully.")
                else:
                    messages.error(request, "Please correct the errors below.")
        except Exception as e:
            logger.exception("finance_expense_line_types_commit failed")
            messages.error(request, f"Couldn't save the expense line type: {e}")
    return render(request, "finance_expense_line_types.html", {
        "eltresults": expense_line_types.objects.all(),
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_expense_line_types_edit(request, expense_line_types_id):
    linked_expense_count = expense.objects.filter(
        expense_line_types_id=expense_line_types_id
    ).count()
    return render(request, "finance_expense_line_types_edit.html", {
        "eltresults": expense_line_types.objects.filter(pk=expense_line_types_id),
        "linked_expense_count": linked_expense_count,
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_expense_line_types_edit_commit(request, expense_line_types_id):
    exp = get_object_or_404(expense_line_types, pk=expense_line_types_id)
    all_types = expense_line_types.objects.all().order_by('expense_line_types_name')

    if request.method == "POST":
        name = request.POST.get('expense_line_types_name', '').strip()

        if expense_line_types.objects.filter(
            expense_line_types_name__iexact=name
        ).exclude(pk=expense_line_types_id).exists():
            messages.error(request, "No duplicate Expense Line Types Allowed")
            return render(request, "finance_expense_line_types.html", {
                "eltresults": all_types, "exp": exp, "name_error": True,
            })

        try:
            with transaction.atomic():
                form = ExpenseLineForm(request.POST, instance=exp)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Expense Line Type Edited Successfully")
                    return redirect('finance_expense_line_types')
                else:
                    messages.error(request, "Please correct the errors below.")
        except Exception as e:
            logger.exception("finance_expense_line_types_edit_commit failed")
            messages.error(request, f"Couldn't update the expense line type: {e}")

    return render(request, "finance_expense_line_types.html", {
        "eltresults": all_types, "exp": exp,
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def check_expenses_for_line_type(request, expense_line_type_id):
    """Return JSON listing every Expense linked to a given Expense Line Type."""
    try:
        elt = get_object_or_404(expense_line_types, expense_line_types_id=expense_line_type_id)
        linked = expense.objects.filter(expense_line_types=elt)

        if not linked.exists():
            return JsonResponse({'has_expenses': False, 'expense_count': 0, 'expenses': []})

        expenses_data = []
        for exp in linked:
            total_amount = 0
            monthly_amounts = []
            for month in MONTHS:
                month_value = getattr(exp, f'expense_{month}', None)
                if month_value:
                    total_amount += month_value
                    monthly_amounts.append(f'{month.capitalize()}: {month_value}')

            display_amount = exp.expense_amount if exp.expense_amount else total_amount

            expenses_data.append({
                'id': exp.expense_id,
                'expense_type': str(exp.expense_types) if exp.expense_types else 'N/A',
                'property': str(exp.prop) if exp.prop else 'N/A',
                'base_amount': str(exp.expense_amount) if exp.expense_amount else '0.00',
                'total_monthly': str(total_amount),
                'display_amount': str(display_amount),
                'monthly_breakdown': monthly_amounts,
            })

        return JsonResponse({
            'has_expenses': True,
            'expense_count': linked.count(),
            'expenses': expenses_data,
        })
    except Exception as e:
        logger.exception("check_expenses_for_line_type failed")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
@require_POST
def delete_expense_line_type(request, expense_line_type_id):
    """Delete an Expense Line Type and all its linked expenses."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    # The choice arrives as a JSON body from the delete modal. Same two
    # meanings as a single expense - see finance_expense_delete - except that
    # "close" cannot remove the line type: its expenses have to survive to
    # carry their history, and they point at it. So the line type stays,
    # holding nothing.
    payload = {}
    if request.body:
        try:
            payload = json.loads(request.body.decode('utf-8') or '{}') or {}
        except (ValueError, UnicodeDecodeError):
            payload = {}
    mode = str(payload.get('mode') or 'close').strip().lower()

    try:
        with transaction.atomic():
            elt = get_object_or_404(expense_line_types, expense_line_types_id=expense_line_type_id)
            linked = list(expense.objects.filter(expense_line_types=elt))
            expense_count = len(linked)
            name = elt.expense_line_types_name

            if mode == 'purge':
                for _fh_exp in linked:
                    purge_figure_history(FinancialFigureHistory.KIND_BUDGET,
                                         _fh_exp.expense_id)
                expense.objects.filter(expense_line_types=elt).delete()
                elt.delete()
                if expense_count > 0:
                    message = (f'Expense line type "{name}" and {expense_count} '
                               f'linked expense(s) removed completely, '
                               f'history included.')
                else:
                    message = f'Expense line type "{name}" has been deleted successfully.'
            elif expense_count == 0:
                # Nothing carries history, so there is nothing to preserve.
                elt.delete()
                message = f'Expense line type "{name}" has been deleted successfully.'
            else:
                _fh_eff = _fh_date_or_today(payload.get('effective_date'))
                _fh_who = _fh_user(request)
                for _fh_exp in linked:
                    _fh_b, _fh_a = _fh_close_expense(_fh_exp)
                    transaction.on_commit(
                        lambda o=_fh_exp, b=_fh_b, a=_fh_a,
                               e=_fh_eff, u=_fh_who:
                            _fh_save_expense(o, b, a, e, u, 'closed'))
                message = (f'{expense_count} expense(s) on "{name}" stopped from '
                           f'{_fh_eff:%d %b %Y}. The line type was kept so that '
                           f'earlier years keep their figures.')

            messages.success(request, message)
            return JsonResponse({
                'success': True,
                'message': message,
                'deleted_expenses': expense_count,
            })
    except Exception as e:
        logger.exception("delete_expense_line_type failed")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def preview_prorata_amount_change(request, expense_line_types_id):
    """Compute the before/after pro-rata distribution for a preview modal."""
    try:
        new_pr_amount = float(request.GET.get('new_pr_amount', 0))
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid new_pr_amount'}, status=400)

    try:
        line_type = expense_line_types.objects.get(expense_line_types_id=expense_line_types_id)
    except expense_line_types.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Expense Line Type not found'}, status=404)

    try:
        old_pr_amount = float(line_type.expense_line_types_pr_amount or 0)
        linked_expenses = expense.objects.filter(
            expense_line_types_id=expense_line_types_id
        ).select_related('prop')

        affected = []
        for exp in linked_expenses:
            pv = prop_values.objects.filter(prop_id=exp.prop_id).first()
            current_value = float(pv.prop_values_current_value) if pv else 0
            affected.append({
                'prop_id': exp.prop_id,
                'prop_name': exp.prop.prop_name if exp.prop else 'Unknown',
                'current_value': current_value,
                'old_amount': float(exp.expense_amount or 0),
            })

        if not affected:
            return JsonResponse({
                'success': True,
                'line_type_name': line_type.expense_line_types_name,
                'old_pr_amount': old_pr_amount,
                'new_pr_amount': new_pr_amount,
                'total_current_value': 0,
                'affected_count': 0,
                'properties': [],
            })

        total_current_value = sum(p['current_value'] for p in affected)
        if total_current_value <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Total current value of linked properties is zero. Cannot recalculate.',
            }, status=400)

        # Reconciled, so the preview totals the charge rather than two cents
        # short of it - and so it shows exactly what the save will store.
        _raw = [(new_pr_amount * p['current_value']) / total_current_value
                for p in affected]
        _fixed = prorata_reconcile(new_pr_amount, _raw)
        for p, _amt in zip(affected, _fixed):
            p['share_percentage'] = round((p['current_value'] / total_current_value) * 100, 2)
            p['new_amount'] = float(_amt)
            p['delta'] = round(p['new_amount'] - p['old_amount'], 2)

        affected.sort(key=lambda p: p['prop_name'].lower())

        return JsonResponse({
            'success': True,
            'line_type_name': line_type.expense_line_types_name,
            'old_pr_amount': old_pr_amount,
            'new_pr_amount': new_pr_amount,
            'total_current_value': total_current_value,
            'affected_count': len(affected),
            'properties': affected,
        })
    except Exception as e:
        logger.exception("preview_prorata_amount_change failed")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
@require_POST
def finance_expense_line_types_edit_and_recalc_commit(request, expense_line_types_id):
    """Save the Line Type AND cascade new amounts to all linked Expenses."""
    if request.method != "POST":
        return redirect('finance_expense_line_types')

    try:
        line_type = expense_line_types.objects.get(expense_line_types_id=expense_line_types_id)
    except expense_line_types.DoesNotExist:
        messages.error(request, "Expense Line Type not found")
        return redirect('finance_expense_line_types')

    new_name = request.POST.get('expense_line_types_name', '').strip()

    if expense_line_types.objects.filter(
        expense_line_types_name__iexact=new_name
    ).exclude(pk=expense_line_types_id).exists():
        messages.error(request, "No duplicate Expense Line Types Allowed")
        return redirect('finance_expense_line_types_edit', expense_line_types_id=expense_line_types_id)

    preview_raw = request.POST.get('prorata_preview_data', '')

    try:
        preview_data = json.loads(preview_raw) if preview_raw else None
    except json.JSONDecodeError:
        messages.error(request, "Invalid preview data")
        return redirect('finance_expense_line_types_edit', expense_line_types_id=expense_line_types_id)

    if not preview_data or 'properties' not in preview_data:
        messages.error(request, "No preview data supplied — cannot recalculate")
        return redirect('finance_expense_line_types_edit', expense_line_types_id=expense_line_types_id)

    try:
        with transaction.atomic():
            line_type.expense_line_types_name = new_name
            line_type.expense_line_types_description = request.POST.get('expense_line_types_description', '')
            line_type.expense_line_types_prorata = request.POST.get('expense_line_types_prorata', 'No')
            line_type.expense_line_types_pr_amount = float(
                request.POST.get('expense_line_types_pr_amount', 0) or 0
            )
            line_type.save()

            # Resolve once, before the loop - request state should not be read
            # from inside an on_commit callback, which runs after the response
            # is on its way.
            _fh_eff = _fh_eff_date(request)
            _fh_who = _fh_user(request)

            for prop_data in preview_data['properties']:
                pid = prop_data['prop_id']
                new_amount = prop_data['new_amount']

                linked = expense.objects.filter(
                    expense_line_types_id=expense_line_types_id,
                    prop_id=pid,
                )

                for exp in linked:
                    try:
                        exp_type = expense_types.objects.get(expense_types_id=exp.expense_types_id)
                    except expense_types.DoesNotExist:
                        continue

                    exp.expense_amount = new_amount
                    for month in MONTHS:
                        if getattr(exp_type, f'expense_types_{month}') == "Yes":
                            setattr(exp, f'expense_{month}', new_amount)
                        else:
                            setattr(exp, f'expense_{month}', None)
                    exp.save()
                    transaction.on_commit(
                        lambda o=exp, e=_fh_eff, u=_fh_who:
                            record_expense_history(o, e, source='prorata_line',
                                                   user=u))

        messages.success(
            request,
            f"Line Type saved and {preview_data.get('affected_count', 0)} "
            f"Expense record(s) recalculated successfully."
        )
        return redirect('finance_expense_line_types')

    except Exception as e:
        logger.exception("finance_expense_line_types_edit_and_recalc_commit failed")
        messages.error(request, f"Error during recalculation: {e}")
        return redirect('finance_expense_line_types_edit', expense_line_types_id=expense_line_types_id)


# ============================================================================
# Valuations
# ============================================================================

def _val_div(value, arg):
    """`divide_by` from custom_filters, reproduced exactly.

    Not "close enough": the template used that filter, so the view has to
    produce the same number to the last bit. Note the quirks that are copied
    deliberately - a falsy `value` becomes 0, a falsy `arg` becomes 1 (so
    dividing by zero returns the value rather than None), and the arithmetic
    goes through Decimal before returning a float.
    """
    try:
        value = Decimal(str(value)) if value else Decimal('0')
        arg = Decimal(str(arg)) if arg else Decimal('1')
        if arg == 0:
            return None
        return float(value / arg)
    except (ValueError, TypeError, InvalidOperation):
        return None


def _val_gain(purchase, current):
    """Percentage gain, and the class that colours it.

    The template computed this through `subtract`, then `multiply:100`, then
    `divide_by` - four `{% with %}` deep - and coloured the result with an
    inline `#28a745` / `#dc3545`. The arithmetic is the same here; the colour
    becomes a CLASS, so the page stops carrying Bootstrap hexes in a style
    attribute where no stylesheet can reach them.
    """
    if not purchase or not current:
        return None, ''
    gain = float(current or 0) - float(purchase or 0)          # `subtract`
    pct = _val_div(float(gain or 0) * 100.0, purchase)         # `multiply`, `divide_by`
    if pct is None:
        return None, ''
    return pct, 'val-gain-up' if pct >= 0 else 'val-gain-down'


def _valuation_rows(props_list, valuations_dict):
    """One row per property that has a valuation, in the order props came in.

    The template did this itself, with `{% with valuation=prop_values|get_item:
    property.prop_id %}{% if valuation %}` - so it could never tell whether it
    had drawn any rows, and the page could not have an empty state.

    `get_item` returns 0 (not None) for a missing key, and 0 is falsy, so the
    `{% if %}` skipped it. `.get(pk)` returning None skips it here for the same
    reason; the behaviour is identical and the reason is worth writing down
    because the two defaults are not the same value.
    """
    rows = []
    for p in props_list:
        v = valuations_dict.get(p.prop_id)
        if not v:
            continue
        area = p.prop_floor_area
        purchase = v.prop_values_purchase_price
        current = v.prop_values_current_value
        pct, gain_class = _val_gain(purchase, current)
        rows.append({
            'prop_values_id': v.prop_values_id,
            'prop_name': p.prop_name,
            'floor_area': area,
            'purchase': purchase,
            'current': current,
            # The template guarded on the INPUTS, not the result, so a
            # quotient of zero would still have printed. It cannot arise -
            # a zero purchase price is falsy and fails the guard - but the
            # guard is copied as it was rather than as it might have been.
            'price_sqm': _val_div(purchase, area) if (area and purchase) else None,
            'price_sqm_known': bool(area and purchase),
            'value_sqm': _val_div(current, area) if (area and current) else None,
            'value_sqm_known': bool(area and current),
            'gain_pct': pct if pct is not None else 0,
            'gain_known': pct is not None,
            'gain_class': gain_class,
        })
    return rows


@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def finance_valuations(request):
    props_list = props.objects.all().order_by('prop_country', 'prop_name')
    valuations_dict = {v.prop_id: v for v in prop_values.objects.all()}

    rows = _valuation_rows(props_list, valuations_dict)

    # THE TOTALS ARE THE SUM OF THE ROWS ON SCREEN. They used to sum every
    # prop_values record, so a valuation whose property was gone was counted
    # in the total and drawn nowhere - a portfolio total that did not equal
    # its own column.
    pur_balance = sum(r['purchase'] for r in rows if r['purchase'] is not None)
    cur_balance = sum(r['current'] for r in rows if r['current'] is not None)
    total_pct, total_class = _val_gain(pur_balance, cur_balance)

    return render(request, "finance_valuations.html", {
        "rows": rows,
        "pur_balance": pur_balance,
        "cur_balance": cur_balance,
        "total_gain_pct": total_pct if total_pct is not None else 0,
        "total_gain_known": total_pct is not None,
        "total_gain_class": total_class,
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_valuations_add(request):
    return render(request, "finance_valuations_add.html", {
        'props': props.objects.all().order_by('prop_country', 'prop_name'),
        'prop_values': prop_values.objects.all(),
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
@require_POST
def finance_valuations_commit(request):
    if request.method != "POST":
        return redirect('finance_valuations')

    prop_id = request.POST.get('prop_id')

    if prop_values.objects.filter(prop_id=prop_id).exists():
        messages.error(request, "A valuation already exists for this property. Please edit the existing valuation.")
        return redirect('finance_valuations')

    try:
        with transaction.atomic():
            form = ValuesForm(request.POST)
            if form.is_valid():
                # Resolved here rather than inside the callback, which runs
                # after commit - request state has no business being read then.
                _fh_eff = _fh_eff_date(request)
                _fh_who = _fh_user(request)
                _pv = form.save()
                transaction.on_commit(
                    lambda o=_pv, e=_fh_eff, u=_fh_who:
                        record_valuation_history(o, e, user=u))
                messages.success(request, "Valuation added successfully.")
                return redirect('finance_valuations')
            else:
                messages.error(request, "Please correct the errors below.")
                return redirect('finance_valuations_add')
    except Exception as e:
        logger.exception("finance_valuations_commit failed")
        messages.error(request, f"Couldn't save the valuation: {e}")
        return redirect('finance_valuations_add')


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_valuations_edit(request, prop_values_id):
    vresults = get_object_or_404(prop_values, pk=prop_values_id)
    return render(request, "finance_valuations_edit.html", {
        "props": props.objects.all().order_by('prop_country', 'prop_name'),
        "vresults": vresults,
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
@require_POST
def finance_valuations_edit_commit(request, prop_values_id):
    vresult = get_object_or_404(prop_values, pk=prop_values_id)

    if request.method != "POST":
        return redirect('finance_valuations')

    try:
        with transaction.atomic():
            form = ValuesForm(request.POST, instance=vresult)
            if form.is_valid():
                # Resolved here rather than inside the callback, which runs
                # after commit - request state has no business being read then.
                _fh_eff = _fh_eff_date(request)
                _fh_who = _fh_user(request)
                _pv = form.save()
                transaction.on_commit(
                    lambda o=_pv, e=_fh_eff, u=_fh_who:
                        record_valuation_history(o, e, user=u))
                messages.success(request, "Valuation updated successfully.")
                return redirect('finance_valuations')
            else:
                messages.error(request, "Please correct the errors below.")
                return redirect('finance_valuations_edit', prop_values_id=prop_values_id)
    except Exception as e:
        logger.exception("finance_valuations_edit_commit failed")
        messages.error(request, f"Couldn't update the valuation: {e}")
        return redirect('finance_valuations_edit', prop_values_id=prop_values_id)


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def preview_valuation_change(request, prop_values_id):
    """Compute the full Pro-Rata impact of a Current Value change."""
    try:
        new_cv = float(request.GET.get('new_current_value', 0))
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid new_current_value'}, status=400)

    try:
        pv = prop_values.objects.get(prop_values_id=prop_values_id)
    except prop_values.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Property Value record not found'}, status=404)

    try:
        try:
            prop_obj = props.objects.get(prop_id=pv.prop_id)
            prop_name = prop_obj.prop_name
        except props.DoesNotExist:
            prop_name = 'Unknown'

        old_cv = float(pv.prop_values_current_value or 0)

        # Which distributions this valuation actually reaches. A closed row
        # is not one of them - showing its line type would draw a group in
        # which nothing moves.
        affected_expenses = carries_a_share(expense.objects.filter(
            prop_id=pv.prop_id,
            expense_line_types__expense_line_types_prorata='Yes',
        )).select_related('expense_line_types')

        line_type_ids = set(e.expense_line_types_id for e in affected_expenses)

        if not line_type_ids:
            return JsonResponse({
                'success': True,
                'prop_id': pv.prop_id,
                'prop_name': prop_name,
                'old_current_value': old_cv,
                'new_current_value': new_cv,
                'affected_line_types_count': 0,
                'affected_expense_count': 0,
                'line_types': [],
                'has_inactive': False,
                'inactive_property_names': [],
                'inactive_new_amount': 0,
            })

        line_types_payload = []
        total_affected_expense_records = 0

        for lt_id in line_type_ids:
            try:
                lt = expense_line_types.objects.get(expense_line_types_id=lt_id)
            except expense_line_types.DoesNotExist:
                continue

            pr_amount = float(lt.expense_line_types_pr_amount or 0)
            # THE DENOMINATOR. Everything below divides by the total current
            # value of THIS set, so a property that carries nothing must not
            # be in it - every other property was funding its share.
            lt_expenses = carries_a_share(
                expense.objects.filter(expense_line_types_id=lt_id)
            ).select_related('prop')
            unique_prop_ids = set(e.prop_id for e in lt_expenses)
            total_affected_expense_records += lt_expenses.count()

            prop_rows = []
            total_cv_old = 0
            total_cv_new = 0

            for pid in unique_prop_ids:
                pv_row = prop_values.objects.filter(prop_id=pid).first()
                cv_old = float(pv_row.prop_values_current_value) if pv_row else 0

                try:
                    p_obj = props.objects.get(prop_id=pid)
                    p_name = p_obj.prop_name
                    # The property object is already in hand; its status costs
                    # nothing more to read. A property that does not exist is a
                    # different fault and is NOT reported as inactive here -
                    # inventing a status for a missing row would be worse than
                    # saying nothing.
                    p_inactive = (p_obj.prop_status != 'Active')
                except props.DoesNotExist:
                    p_name = 'Unknown'
                    p_inactive = False

                cv_new = new_cv if pid == pv.prop_id else cv_old
                existing = next((e for e in lt_expenses if e.prop_id == pid), None)
                old_amount = float(existing.expense_amount) if existing else 0

                total_cv_old += cv_old
                total_cv_new += cv_new

                prop_rows.append({
                    'prop_id': pid,
                    'prop_name': p_name,
                    'current_value_old': cv_old,
                    'current_value_new': cv_new,
                    'old_amount': old_amount,
                    'is_edited_property': (pid == pv.prop_id),
                    'is_inactive': p_inactive,
                })

            if total_cv_new <= 0:
                return JsonResponse({
                    'success': False,
                    'error': (
                        f"Total Current Value in '{lt.expense_line_types_name}' distribution "
                        f"would be zero after this change. Cannot recalculate."
                    ),
                }, status=400)

            for r in prop_rows:
                r['share_percentage_old'] = round(
                    (r['current_value_old'] / total_cv_old * 100) if total_cv_old > 0 else 0, 2
                )
                r['share_percentage_new'] = round((r['current_value_new'] / total_cv_new) * 100, 2)
                r['new_amount'] = round((pr_amount * r['current_value_new']) / total_cv_new, 2)
                r['delta'] = round(r['new_amount'] - r['old_amount'], 2)

            prop_rows.sort(key=lambda r: (not r['is_edited_property'], r['prop_name'].lower()))

            # What this distribution would put on properties the P&L does
            # not report. Summed HERE, from the same rows the table draws, so
            # the warning and the figures beneath it cannot disagree.
            _inactive = [r for r in prop_rows if r['is_inactive']]
            line_types_payload.append({
                'line_type_id': lt_id,
                'line_type_name': lt.expense_line_types_name,
                'pr_amount': pr_amount,
                'total_current_value_old': total_cv_old,
                'total_current_value_new': total_cv_new,
                'property_count': len(prop_rows),
                'properties': prop_rows,
                'inactive_count': len(_inactive),
                'inactive_names': [r['prop_name'] for r in _inactive],
                'inactive_new_amount': round(
                    sum(r['new_amount'] for r in _inactive), 2),
                'inactive_share': round(
                    sum(r['share_percentage_new'] for r in _inactive), 2),
            })

        line_types_payload.sort(key=lambda lt: lt['line_type_name'].lower())

        # Rolled up across every distribution, so the preview can say the
        # whole of it once rather than making the reader open each group.
        _inactive_names = sorted({n for _lt in line_types_payload
                                  for n in _lt['inactive_names']})
        return JsonResponse({
            'success': True,
            'prop_id': pv.prop_id,
            'prop_name': prop_name,
            'old_current_value': old_cv,
            'new_current_value': new_cv,
            'affected_line_types_count': len(line_types_payload),
            'affected_expense_count': total_affected_expense_records,
            'line_types': line_types_payload,
            'has_inactive': bool(_inactive_names),
            'inactive_property_names': _inactive_names,
            'inactive_new_amount': round(
                sum(_lt['inactive_new_amount'] for _lt in line_types_payload), 2),
        })
    except Exception as e:
        logger.exception("preview_valuation_change failed")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
@require_POST
def finance_valuations_edit_and_recalc_commit(request, prop_values_id):
    """Save the valuation AND cascade new amounts to all linked Pro-Rata Expenses."""
    if request.method != "POST":
        return redirect('finance_valuations')

    try:
        pv = prop_values.objects.get(prop_values_id=prop_values_id)
    except prop_values.DoesNotExist:
        messages.error(request, "Property Value record not found")
        return redirect('finance_valuations')

    preview_raw = request.POST.get('valuation_preview_data', '')

    try:
        preview_data = json.loads(preview_raw) if preview_raw else None
    except json.JSONDecodeError:
        messages.error(request, "Invalid preview data")
        return redirect('finance_valuations_edit', prop_values_id=prop_values_id)

    if not preview_data or 'line_types' not in preview_data:
        messages.error(request, "No preview data supplied — cannot recalculate")
        return redirect('finance_valuations_edit', prop_values_id=prop_values_id)

    try:
        with transaction.atomic():
            form = ValuesForm(request.POST, instance=pv)
            if not form.is_valid():
                messages.error(request, f"Form errors: {form.errors}")
                return redirect('finance_valuations_edit', prop_values_id=prop_values_id)
            # Resolve once - request state should not be read from inside an
            # on_commit callback.
            _fh_eff = _fh_eff_date(request)
            _fh_who = _fh_user(request)

            _pv = form.save()
            transaction.on_commit(
                lambda o=_pv, e=_fh_eff, u=_fh_who:
                    record_valuation_history(o, e, user=u))

            for lt_payload in preview_data['line_types']:
                lt_id = lt_payload['line_type_id']
                for prop_data in lt_payload['properties']:
                    pid = prop_data['prop_id']
                    new_amount = prop_data['new_amount']

                    linked = expense.objects.filter(
                        expense_line_types_id=lt_id,
                        prop_id=pid,
                    )

                    for exp in linked:
                        try:
                            exp_type = expense_types.objects.get(expense_types_id=exp.expense_types_id)
                        except expense_types.DoesNotExist:
                            continue

                        exp.expense_amount = new_amount
                        for month in MONTHS:
                            if getattr(exp_type, f'expense_types_{month}') == "Yes":
                                setattr(exp, f'expense_{month}', new_amount)
                            else:
                                setattr(exp, f'expense_{month}', None)
                        exp.save()
                        transaction.on_commit(
                            lambda o=exp, e=_fh_eff, u=_fh_who:
                                record_expense_history(o, e,
                                                       source='prorata_valuation',
                                                       user=u))

        lt_count = preview_data.get('affected_line_types_count', 0)
        exp_count = preview_data.get('affected_expense_count', 0)
        messages.success(
            request,
            f"Valuation saved. {exp_count} Expense record(s) across "
            f"{lt_count} Pro-Rata distribution(s) recalculated successfully."
        )
        return redirect('finance_valuations')

    except Exception as e:
        logger.exception("finance_valuations_edit_and_recalc_commit failed")
        messages.error(request, f"Error during recalculation: {e}")
        return redirect('finance_valuations_edit', prop_values_id=prop_values_id)


# =============================================================================
# PHASE 2 - Reports (read-only views; no atomic pattern needed)
# Cash flow forecast, occupancy trends, financial indicators, vacancy,
# drill-downs, and P&L statements. Moved from main.py.
# =============================================================================


@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def cashflow_forecast(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        horizon_months = int(request.GET.get("horizon", 12))
        today = date.today()

        # Calculate horizon cutoff date
        horizon_year = today.year + (today.month + horizon_months - 1) // 12
        horizon_month = (today.month + horizon_months - 1) % 12 + 1
        horizon_last_day = monthrange(horizon_year, horizon_month)[1]
        cutoff_date = date(horizon_year, horizon_month, horizon_last_day)

        expenses = []

        # Handle budget expenses - they repeat every year
        for exp in expense.objects.select_related("prop", "expense_line_types").all():
            month_fields = [
                ("expense_jan", 1), ("expense_feb", 2), ("expense_mar", 3),
                ("expense_apr", 4), ("expense_may", 5), ("expense_jun", 6),
                ("expense_jul", 7), ("expense_aug", 8), ("expense_sep", 9),
                ("expense_oct", 10), ("expense_nov", 11), ("expense_dec", 12),
            ]

            for field, month_idx in month_fields:
                amount = getattr(exp, field)
                if amount and amount > decimal.Decimal("0.00"):
                    # Generate expenses for each year within the horizon
                    current_year = today.year
                    while True:
                        last_day = monthrange(current_year, month_idx)[1]
                        due_date = date(current_year, month_idx, last_day)

                        # Break if beyond our cutoff date
                        if due_date > cutoff_date:
                            break

                        # Only include if the date is today or in the future
                        if due_date >= today:
                            days_ahead = (due_date - today).days
                            if days_ahead <= 30:
                                color = "red"
                            elif days_ahead <= 90:
                                color = "orange"
                            else:
                                color = "green"

                            expenses.append({
                                "id": f"{exp.expense_id}-{current_year}-{month_idx}",
                                "property": exp.prop.prop_name,
                                "amount": float(amount),
                                "due_date": due_date.strftime("%Y-%m-%d"),
                                "description": exp.expense_line_types.expense_line_types_name,
                                "line_type": exp.expense_line_types.expense_line_types_name,
                                "color": color,
                            })

                        current_year += 1

        expenses.sort(key=lambda x: x["due_date"])
        payload = {"expenses": expenses}
        if request.GET.get("revenue") == "1":
            from ..services.portfolio_insights import net_cashflow_revenue
            payload["revenue"] = net_cashflow_revenue(today=today, months=horizon_months)
        return JsonResponse(payload)

    return render(request, "finance/cashflow_forecast.html")


@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def occupancy_trends_view(request):
    """
    Display occupancy, days to fill, and vacancy cost trends over time
    """
    # Get the first tenant date across all properties
    first_tenant_date = tenant.objects.filter(
        tenant_lease_start_date__isnull=False
    ).aggregate(
        first_date=Min('tenant_lease_start_date')
    )['first_date']

    if not first_tenant_date:
        # No tenants yet
        return render(request, 'occupancy_trends.html', {
            'error': 'No tenant data available yet'
        })

    # Get current year
    today = date.today()
    current_year = today.year
    first_year = first_tenant_date.year

    # Calculate all metrics for each year
    yearly_data = []

    for year in range(first_year, current_year + 1):
        year_metrics = calculate_year_metrics(year)
        yearly_data.append(year_metrics)

    context = {
        'yearly_data': yearly_data,
        'yearly_data_json': json.dumps(yearly_data),
        'current_year': current_year,
        'first_year': first_year,
    }

    return render(request, 'occupancy_trends.html', context)


@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def _financial_indicators_trend(request):
    """JSON: per-year Financial Indicators for the portfolio and each active
    property, for the trend chart. Auto basis — each year uses budgeted plus
    whatever actual (ad-hoc) spend exists for it, so completed years reflect real
    spend, the current year is actual-so-far + budget, and future years are budget
    only. Value Increase is intentionally excluded (valuations are not dated)."""
    today = datetime.now().date()
    current_year = today.year
    _lease_min = tenant.objects.exclude(tenant_lease_start_date__isnull=True).aggregate(
        _m=Min('tenant_lease_start_date'))['_m']
    earliest = _lease_min.year if _lease_min else current_year
    years = list(range(earliest, current_year + 2))
    properties = list(props.objects.filter(prop_status='Active').prefetch_related('prop_values_set'))

    meta = {}
    for prop in properties:
        pv_list = list(prop.prop_values_set.all())
        pv = pv_list[0] if pv_list else None
        meta[prop.prop_id] = {
            'name': prop.prop_name or ('Property %s' % prop.prop_id),
            'purchase': float(pv.prop_values_purchase_price) if pv and pv.prop_values_purchase_price else 0.0,
            'area': float(prop.prop_floor_area) if prop.prop_floor_area else 0.0,
            'grossROI': [], 'netROI': [], 'expensesToRevenue': [], 'rentPerSqm': [],
        }

    portfolio = {'grossROI': [], 'netROI': [], 'expensesToRevenue': [], 'rentPerSqm': []}
    for y in years:
        t_rev = t_exp = t_pur = t_area = 0.0
        for prop in properties:
            rev = float(property_annual_lease_revenue(prop, y))
            bud = float(property_annual_budgeted_expenses(prop, y))
            act = float(property_annual_actual_expenses(prop, y))
            exp = bud + act
            pm = meta[prop.prop_id]
            pur = pm['purchase']
            area = pm['area']
            pm['grossROI'].append(round(rev / pur * 100, 2) if pur > 0 else None)
            pm['netROI'].append(round((rev - exp) / pur * 100, 2) if pur > 0 else None)
            pm['expensesToRevenue'].append(round(exp / rev * 100, 2) if rev > 0 else None)
            pm['rentPerSqm'].append(round(rev / 12 / area, 2) if area > 0 else None)
            t_rev += rev
            t_exp += exp
            t_pur += pur
            t_area += area
        portfolio['grossROI'].append(round(t_rev / t_pur * 100, 2) if t_pur > 0 else None)
        portfolio['netROI'].append(round((t_rev - t_exp) / t_pur * 100, 2) if t_pur > 0 else None)
        portfolio['expensesToRevenue'].append(round(t_exp / t_rev * 100, 2) if t_rev > 0 else None)
        portfolio['rentPerSqm'].append(round(t_rev / 12 / t_area, 2) if t_area > 0 else None)

    prop_series = []
    for prop in properties:
        pm = meta[prop.prop_id]
        prop_series.append({
            'id': prop.prop_id,
            'name': pm['name'],
            'grossROI': pm['grossROI'],
            'netROI': pm['netROI'],
            'expensesToRevenue': pm['expensesToRevenue'],
            'rentPerSqm': pm['rentPerSqm'],
        })

    return JsonResponse({
        'years': years,
        'current_year': current_year,
        'portfolio': portfolio,
        'properties': prop_series,
    })


def financial_indicators_view(request):
    """
    Display the Financial Indicators Dashboard - ONLY for Active Properties
    Using Portfolio-Wide Calculations with Occupancy Metrics
    Reduced queries with prefetch_related
    """
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if request.GET.get('trend'):
            return _financial_indicators_trend(request)
        # AJAX request for property data
        try:
            today = datetime.now().date()
            current_year = today.year
            # Year + basis selectors (year-aware, effective-dated — mirrors the P&L).
            _lease_min = tenant.objects.exclude(tenant_lease_start_date__isnull=True).aggregate(
                _m=Min('tenant_lease_start_date'))['_m']
            _earliest_year = _lease_min.year if _lease_min else current_year
            available_years = list(range(_earliest_year, current_year + 2))[::-1]
            try:
                selected_year = int(request.GET.get('year'))
            except (TypeError, ValueError):
                selected_year = current_year
            if selected_year not in available_years:
                selected_year = current_year if current_year in available_years else available_years[0]
            basis = request.GET.get('basis', 'budget')
            if basis not in ('budget', 'actuals'):
                basis = 'budget' 

            # Prefetch related data in one query
            properties = props.objects.filter(prop_status='Active').prefetch_related(
                Prefetch('tenant_set', queryset=tenant.objects.all()),
                Prefetch('vacancy_periods', queryset=VacancyPeriod.objects.select_related('previous_lease', 'next_lease').all()),
                'prop_values_set'
            )

            properties_data = []

            # Portfolio-wide totals for all active properties
            portfolio_totals = {
                'total_revenue': Decimal('0.00'),
                'total_budgeted_expenses': Decimal('0.00'),
                'total_expense_basis': Decimal('0.00'),
                'total_purchase_price': Decimal('0.00'),
                'total_current_value': Decimal('0.00'),
                'total_purchase_for_value': Decimal('0.00'),
                'total_floor_area': 0,
                'total_revenue_prev': Decimal('0.00'),
                'rent_rate_cur': Decimal('0.00'),
                'rent_rate_prev': Decimal('0.00'),
                'occupancy_sum': 0.0,
                'leased_count': 0,
                'property_count': 0
            }

            for prop in properties:
                # Year-aware, matching the P&L: lease revenue + effective-dated budget.
                # Actuals basis also folds in that year's actual (ad-hoc) expenses.
                revenue_total = property_annual_lease_revenue(prop, selected_year)
                budgeted_expense_total = property_annual_budgeted_expenses(prop, selected_year)
                actual_expense_total = property_annual_actual_expenses(prop, selected_year) if basis == 'actuals' else Decimal('0.00')
                expense_basis_total = budgeted_expense_total + actual_expense_total

                # Get property values - ONLY for active properties
                # Use prefetched data
                property_values_list = list(prop.prop_values_set.all())
                property_values = property_values_list[0] if property_values_list else None
                purchase_price = property_values.prop_values_purchase_price if property_values else 0
                current_value = property_values.prop_values_current_value if property_values else 0
                # Value Increase is year-aware: use the valuation in force at the
                # END of the selected year (effective-dated history). None => no
                # dated valuation applies to that year yet -> N/A, skipped from score.
                value_as_of = property_value_as_of(prop, selected_year)

                # Active = held in the selected year. Leased props become active
                # in their first-ever lease year; seasonal / no-lease props (e.g.
                # Ionion) are active in any year they earned revenue. Not-held-yet
                # years are excluded from BOTH the ranking and the portfolio totals.
                _leases = list(prop.tenant_set.all())
                _has_leases = len(_leases) > 0
                if _has_leases:
                    _starts = [l.tenant_lease_start_date for l in _leases if l.tenant_lease_start_date]
                    _active = bool(_starts) and selected_year >= min(_starts).year
                else:
                    _active = bool(revenue_total and revenue_total > 0)
                prev_revenue = property_annual_lease_revenue(prop, selected_year - 1)

                # Portfolio totals — held properties only, so the aggregate is
                # genuinely "as of the selected year".
                if _active:
                    portfolio_totals['total_revenue'] += revenue_total
                    portfolio_totals['total_budgeted_expenses'] += budgeted_expense_total
                    portfolio_totals['total_expense_basis'] += expense_basis_total
                    portfolio_totals['total_purchase_price'] += purchase_price or 0
                    portfolio_totals['total_floor_area'] += prop.prop_floor_area or 0
                    # Portfolio Value Increase is apples-to-apples: sum the
                    # year-aware value AND its matching purchase price only for
                    # properties that actually have a dated valuation for the year.
                    if value_as_of is not None and purchase_price and purchase_price > 0:
                        portfolio_totals['total_current_value'] += value_as_of
                        portfolio_totals['total_purchase_for_value'] += purchase_price
                    portfolio_totals['total_revenue_prev'] += prev_revenue or Decimal('0.00')
                    portfolio_totals['property_count'] += 1

                # Calculate individual property indicators for display purposes
                gross_roi = (revenue_total / purchase_price * 100) if purchase_price > 0 else 0
                net_roi = ((revenue_total - expense_basis_total) / purchase_price * 100) if purchase_price > 0 else 0
                # Zero-revenue held year = spending with no income = the WORST cost
                # efficiency. Sentinel (front-end shows ∞ and grades it worst)
                # instead of 0%, which would wrongly reward a vacant year.
                expense_ratio = (expense_basis_total / revenue_total * 100) if revenue_total > 0 else Decimal('99999999')
                rent_per_sqm = (revenue_total / 12 / prop.prop_floor_area) if prop.prop_floor_area and prop.prop_floor_area > 0 else 0
                value_increase = ((value_as_of - purchase_price) / purchase_price * 100) if (value_as_of is not None and purchase_price and purchase_price > 0) else None

                # Occupancy (Option 1: signed-lease OR assumed-continuation);
                # N/A for seasonal / no-lease props. Portfolio occupancy = simple
                # mean over held, leased properties.
                if _has_leases:
                    _covered = 0
                    _prev_covered = 0
                    for _m in range(1, 13):
                        if _lease_month(_leases, selected_year, _m, today)[0] in ('lease', 'assumed'):
                            _covered += 1
                        if _lease_month(_leases, selected_year - 1, _m, today)[0] in ('lease', 'assumed'):
                            _prev_covered += 1
                    occupancy_val = round(_covered / 12.0 * 100.0, 1)
                    if _active:
                        portfolio_totals['occupancy_sum'] += occupancy_val
                        portfolio_totals['leased_count'] += 1
                else:
                    occupancy_val = None
                    _covered = 0
                    _prev_covered = 0

                # Rent Growth compares AVERAGE MONTHLY rent year-over-year
                # (revenue / months actually held), NOT total revenue. So a first
                # full year after a partial start reads as the real change in the
                # monthly rent rate, not a phantom jump (12 months vs 1 month is no
                # longer +1100%). Leased properties normalise by lease/assumed month
                # coverage; seasonal / no-lease properties compare full-season totals.
                # No prior baseline (property not held the year before) => N/A (None),
                # which is skipped from the score, same as seasonal Occupancy.
                # _cur_rate / _prev_rate = the property's average MONTHLY rent this
                # year / last year, on the same basis as the per-property Rent
                # Growth. They also feed the PORTFOLIO Rent Growth so the portfolio
                # row is monthly-normalised too (a property that joined mid-prior-
                # year contributes its monthly rate, not a stub annual total).
                _cur_rate = _prev_rate = None
                if _has_leases:
                    if _covered > 0 and _prev_covered > 0 and prev_revenue and prev_revenue > 0:
                        _cur_rate = revenue_total / Decimal(_covered)
                        _prev_rate = prev_revenue / Decimal(_prev_covered)
                        rent_growth = ((_cur_rate - _prev_rate) / _prev_rate * 100) if _prev_rate > 0 else None
                    else:
                        rent_growth = None
                else:
                    if prev_revenue and prev_revenue > 0:
                        # Seasonal / no-lease: full-season totals spread to a monthly
                        # scale (÷12) so they combine with leased rates in the
                        # portfolio sum; the per-property ratio is unchanged.
                        _cur_rate = revenue_total / Decimal(12)
                        _prev_rate = prev_revenue / Decimal(12)
                        rent_growth = ((revenue_total - prev_revenue) / prev_revenue * 100)
                    else:
                        rent_growth = None
                # Portfolio monthly rent run-rate — only held props with a valid
                # year-over-year basis (matches which props get a per-property number).
                if _active and _cur_rate is not None and _prev_rate is not None and _prev_rate > 0:
                    portfolio_totals['rent_rate_cur'] += _cur_rate
                    portfolio_totals['rent_rate_prev'] += _prev_rate

                # Store individual property data
                properties_data.append({
                    'id': prop.prop_id,
                    'name': prop.prop_name or f"Property {prop.prop_id}",
                    'status': prop.prop_status,
                    'grossROI': round(float(gross_roi), 2),
                    'netROI': round(float(net_roi), 2),
                    'expensesToRevenue': round(float(expense_ratio), 2),
                    'rentPerSqm': round(float(rent_per_sqm), 2),
                    'valueIncrease': round(float(value_increase), 2) if value_increase is not None else None,
                    'occupancy': occupancy_val,
                    'rentGrowth': round(float(rent_growth), 1) if rent_growth is not None else None,
                    'active': _active,
                    'revenue': float(revenue_total),
                    'expenses': float(budgeted_expense_total),
                    'profit': float(revenue_total - budgeted_expense_total)
                })

            # Calculate TRUE PORTFOLIO-WIDE indicators (FINANCIAL ONLY)
            portfolio_indicators = {
                'grossROI': round(float(
                    (portfolio_totals['total_revenue'] / portfolio_totals['total_purchase_price'] * 100)
                    if portfolio_totals['total_purchase_price'] > 0 else 0
                ), 2),
                'netROI': round(float(
                    ((portfolio_totals['total_revenue'] - portfolio_totals['total_expense_basis']) /
                     portfolio_totals['total_purchase_price'] * 100)
                    if portfolio_totals['total_purchase_price'] > 0 else 0
                ), 2),
                'expensesToRevenue': round(float(
                    (portfolio_totals['total_expense_basis'] / portfolio_totals['total_revenue'] * 100)
                    if portfolio_totals['total_revenue'] > 0 else 0
                ), 2),
                'rentPerSqm': round(float(
                    (portfolio_totals['total_revenue'] / 12 / portfolio_totals['total_floor_area'])
                    if portfolio_totals['total_floor_area'] > 0 else 0
                ), 2),
                'valueIncrease': round(float(
                    ((portfolio_totals['total_current_value'] - portfolio_totals['total_purchase_for_value']) /
                     portfolio_totals['total_purchase_for_value'] * 100)
                    if portfolio_totals['total_purchase_for_value'] > 0 else 0
                ), 2),
                'occupancy': round(
                    portfolio_totals['occupancy_sum'] / portfolio_totals['leased_count'], 1
                ) if portfolio_totals['leased_count'] else 0,
                'rentGrowth': round(float(
                    (portfolio_totals['rent_rate_cur'] - portfolio_totals['rent_rate_prev'])
                    / portfolio_totals['rent_rate_prev'] * 100
                ), 1) if portfolio_totals['rent_rate_prev'] > 0 else 0
            }

            return JsonResponse({
                'properties': properties_data,
                'portfolio_indicators': portfolio_indicators,
                'portfolio_totals': {
                    'total_revenue': float(portfolio_totals['total_revenue']),
                    'total_expenses': float(portfolio_totals['total_budgeted_expenses']),
                    'total_purchase_price': float(portfolio_totals['total_purchase_price']),
                    'total_current_value': float(portfolio_totals['total_current_value']),
                    'total_floor_area': portfolio_totals['total_floor_area'],
                    'property_count': portfolio_totals['property_count']
                },
                'total_active_properties': len(properties_data),
                'available_years': available_years,
                'selected_year': selected_year,
                'basis': basis,
                'message': f'Showing {len(properties_data)} active properties - Financial Indicators ({selected_year}, {basis})'
            })

        except Exception as e:
            print(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)

    # Regular page load — provide the year list + current selections for the controls.
    _today2 = datetime.now().date()
    _lease_min2 = tenant.objects.exclude(tenant_lease_start_date__isnull=True).aggregate(
        _m=Min('tenant_lease_start_date'))['_m']
    _earliest2 = _lease_min2.year if _lease_min2 else _today2.year
    _years = list(range(_earliest2, _today2.year + 2))[::-1]
    try:
        _sel_year = int(request.GET.get('year'))
    except (TypeError, ValueError):
        _sel_year = _today2.year
    if _sel_year not in _years:
        _sel_year = _today2.year if _today2.year in _years else _years[0]
    _basis = request.GET.get('basis', 'budget')
    if _basis not in ('budget', 'actuals'):
        _basis = 'budget'
    context = {
        'page_title': 'Financial Indicators Dashboard - Portfolio-Wide Analysis (Active Properties)',
        'available_years': _years,
        'selected_year': _sel_year,
        'current_year': _today2.year,
        'basis': _basis,
    }
    return render(request, 'finance/financial_indicators.html', context)


@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def vacancy_management_view(request):
    """
    Display the Vacancy Management Dashboard - Occupancy Metrics Only
    Shows Occupancy Rate, Avg Days to Fill, and Vacancy Cost
    ONLY for properties included in occupancy tracking
    """
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX request for property data
        try:
            # GET TIME PERIOD PARAMETER
            time_period = request.GET.get('period', 'past_year')  # Default: past_year
            today = datetime.now().date()
            current_year = datetime.now().year

            # Calculate period boundaries
            if time_period == 'past_year':
                period_start = today - timedelta(days=365)
                period_end = today
            elif time_period == 'last_3_years':
                period_start = today - timedelta(days=365 * 3)
                period_end = today
            else:  # 'all_time'
                # For all_time, we'll use property-specific start dates
                period_start = datetime(2000, 1, 1).date()
                period_end = today

            # Prefetch related data in one query
            properties = props.objects.filter(
                prop_status='Active',
                prop_include_in_occupancy=True  # ONLY properties included in occupancy tracking
            ).prefetch_related(
                Prefetch('tenant_set', queryset=tenant.objects.all()),
                Prefetch('vacancy_periods', queryset=VacancyPeriod.objects.select_related('previous_lease', 'next_lease').all())
            )

            properties_data = []

            # Calculate vacancy costs
            vacancy_costs = {}
            total_vacancy_cost = Decimal('0.00')

            for prop in properties:
                # Calculate occupancy metrics
                occupancy_metrics = calculate_occupancy_metrics_with_period(
                    prop, period_start, period_end
                )

                # CALCULATE VACANCY COSTS for this property
                property_vacancy_cost = Decimal('0.00')
                total_days_vacant = 0

                # Get property's first tenant date
                first_tenant_date = get_property_first_tenant_date_optimized(prop)

                if first_tenant_date:
                    # Calculate effective period for this property
                    effective_start, effective_end = calculate_effective_period(
                        first_tenant_date, period_start, period_end
                    )

                    if effective_start:
                        # Use PREFETCHED vacancy data
                        all_vacancies = list(prop.vacancy_periods.all())
                        vacancies = [
                            v for v in all_vacancies
                            if (v.start_date >= first_tenant_date and
                                v.start_date <= effective_end and
                                (v.status == 'FILLED' or v.status == 'OPEN'))
                        ]

                        for vacancy in vacancies:
                            # Calculate overlap with effective period
                            vacancy_start = max(vacancy.start_date, effective_start)
                            vacancy_end = min(
                                vacancy.end_date if vacancy.end_date else datetime.now().date(),
                                effective_end
                            )

                            if vacancy_start <= vacancy_end:
                                days_in_period = (vacancy_end - vacancy_start).days + 1
                            else:
                                continue

                            # Determine which rent to use
                            rent_to_use = None

                            if vacancy.next_lease and vacancy.next_lease.tenant_rent:
                                rent_to_use = vacancy.next_lease.tenant_rent
                            elif vacancy.previous_lease and vacancy.previous_lease.tenant_rent:
                                rent_to_use = vacancy.previous_lease.tenant_rent

                            if rent_to_use:
                                daily_rent = Decimal(str(rent_to_use)) / Decimal('30')
                                vacancy_cost = Decimal(str(days_in_period)) * daily_rent
                                property_vacancy_cost += vacancy_cost
                                total_days_vacant += days_in_period

                total_vacancy_cost += property_vacancy_cost

                vacancy_costs[prop.prop_id] = {
                    'total_cost': float(property_vacancy_cost),
                    'days_vacant': total_days_vacant
                }

                # Store individual property data
                properties_data.append({
                    'id': prop.prop_id,
                    'name': prop.prop_name or f"Property {prop.prop_id}",
                    'status': prop.prop_status,
                    'occupancyRate': occupancy_metrics['occupancy_rate'],
                    'avgDaysToFill': occupancy_metrics['avg_days_to_fill'],
                    'isCurrentlyVacant': occupancy_metrics['is_currently_vacant'],
                    'currentVacancyDays': occupancy_metrics['current_vacancy_days'],
                    'vacancyCost': vacancy_costs[prop.prop_id]['total_cost']
                })

            # Calculate portfolio occupancy
            portfolio_occupancy = calculate_portfolio_occupancy_with_period(
                properties, period_start, period_end
            )

            # Calculate vacancy cost average (for modal comparison)
            num_properties = len(properties)
            vacancy_cost_average = (
                float(total_vacancy_cost) / num_properties
                if num_properties > 0 else 0
            )

            # Portfolio indicators - OCCUPANCY ONLY
            portfolio_indicators = {
                'occupancyRate': portfolio_occupancy['occupancy_rate'],
                'avgDaysToFill': portfolio_occupancy['avg_days_to_fill'],
                'vacancyCost': round(float(total_vacancy_cost), 2),
                'vacancyCostAverage': round(vacancy_cost_average, 2),
            }

            return JsonResponse({
                'properties': properties_data,
                'portfolio_indicators': portfolio_indicators,
                'vacancy_costs': vacancy_costs,
                'total_vacancy_cost': float(total_vacancy_cost),
                'time_period': time_period,
                'period_start': period_start.strftime('%Y-%m-%d'),
                'period_end': period_end.strftime('%Y-%m-%d'),
                'total_active_properties': len(properties_data),
                'message': f'Showing {len(properties_data)} properties included in occupancy tracking'
            })

        except Exception as e:
            print(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)

    # Regular page load
    context = {
        'page_title': 'Vacancy Management Dashboard - Occupancy Performance'
    }
    return render(request, 'finance/vacancy_management.html', context)


@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def revenue_details_view(request):
    """
    View to show revenue details breakdown for budgeted/fixed revenues
    """
    year = request.GET.get('year', datetime.now().year)  # Just for display
    month = request.GET.get('month')
    line_type = request.GET.get('line_type')
    property_id = request.GET.get('property_id')
    prop = request.GET.get('prop', 'all')
    properties = request.GET.get('properties', '')  # Handle comma-separated properties

    # Get all revenue records (no year filtering needed for budgeted revenues)
    revenues = revenue.objects.all().select_related('prop', 'revenue_line_types', 'revenue_types')

    # Filter by line type if specified
    if line_type:
        revenues = revenues.filter(revenue_line_types_id=line_type)

    # Filter by property
    if properties:  # Handle comma-separated properties
        try:
            property_ids = [int(prop_id.strip()) for prop_id in properties.split(',') if prop_id.strip()]
            revenues = revenues.filter(prop_id__in=property_ids)
        except ValueError:
            pass  # Invalid property IDs, show no results
    elif property_id and property_id != 'all':
        revenues = revenues.filter(prop_id=property_id)
    elif prop and prop != 'all':
        revenues = revenues.filter(prop_id=prop)

    # Get line type name for header
    line_type_name = "Revenue"
    if line_type:
        try:
            line_type_obj = revenue_line_types.objects.get(revenue_line_types_id=line_type)
            line_type_name = line_type_obj.revenue_line_types_name
        except revenue_line_types.DoesNotExist:
            line_type_name = "Unknown"

    # Get month name for subtitle
    month_names = {
        '1': 'January', '2': 'February', '3': 'March', '4': 'April',
        '5': 'May', '6': 'June', '7': 'July', '8': 'August',
        '9': 'September', '10': 'October', '11': 'November', '12': 'December'
    }
    month_name = month_names.get(str(month), "All Months") if month else "All Months"

    # Phase 3: revenue for the drill-down comes from LEASES (same engine as the
    # P&L), so this popup matches the table. Iterate the selected PROPERTIES (a
    # leased property may have no revenue-table row for Rental/Levies). Seasonal
    # / ancillary lines fall back to the revenue table inside lease_revenue_rows.
    try:
        _year_int = int(year)
    except (TypeError, ValueError):
        _year_int = None

    if properties:
        try:
            _target_ids = [int(pid.strip()) for pid in properties.split(',') if pid.strip()]
        except ValueError:
            _target_ids = []
        _target_props = list(props.objects.filter(prop_id__in=_target_ids))
    elif property_id and property_id != 'all':
        _target_props = list(props.objects.filter(prop_id=property_id))
    elif prop and prop != 'all':
        _target_props = list(props.objects.filter(prop_id=prop))
    else:
        _target_props = list(props.objects.all())

    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
              'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

    # Create a list of revenue items with monthly breakdown
    revenue_items = []
    total_amount = 0

    for _pobj in _target_props:
        _rows = lease_revenue_rows(_pobj, _year_int) if _year_int is not None else list(_pobj.revenue_set.all())
        for rev in _rows:
            if line_type and str(getattr(rev, 'revenue_line_types_id', '')) != str(line_type):
                continue
            for i, month_name_field in enumerate(months, 1):
                month_value = getattr(rev, 'revenue_' + month_name_field, 0)
                if month_value and month_value > 0:
                    if month and int(month) != i:
                        continue
                    revenue_items.append({
                        'revenue_id': getattr(rev, 'revenue_id', None),
                        'property': _pobj,
                        'amount': float(month_value),
                    })
                    total_amount += float(month_value)

    context = {
        'revenue_items': revenue_items,
        'total_amount': total_amount,
        'selected_year': year,
        'selected_month': month,
        'selected_line_type': line_type,
        'line_type_name': line_type_name,
        'month_name': month_name,
    }

    return render(request, 'revenue_details.html', context)


@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def budget_expense_details_view(request):
    """
    View to show budgeted expense details breakdown
    """
    year = request.GET.get('year', datetime.now().year)  # Just for display
    month = request.GET.get('month')
    line_type = request.GET.get('line_type')
    property_id = request.GET.get('property_id')
    prop = request.GET.get('prop', 'all')
    properties = request.GET.get('properties', '')  # Handle comma-separated properties

    # Get all budgeted expense records (no year filtering needed for budgeted expenses)
    expenses = expense.objects.all().select_related('prop', 'expense_line_types', 'expense_types')

    # Filter by line type if specified
    if line_type:
        expenses = expenses.filter(expense_line_types_id=line_type)

    # Filter by property
    if properties:  # Handle comma-separated properties
        try:
            property_ids = [int(prop_id.strip()) for prop_id in properties.split(',') if prop_id.strip()]
            expenses = expenses.filter(prop_id__in=property_ids)
        except ValueError:
            pass  # Invalid property IDs, show no results
    elif property_id and property_id != 'all':
        expenses = expenses.filter(prop_id=property_id)
    elif prop and prop != 'all':
        expenses = expenses.filter(prop_id=prop)

    # Get line type name for header
    line_type_name = "Budget Expenses"
    if line_type:
        try:
            line_type_obj = expense_line_types.objects.get(expense_line_types_id=line_type)
            line_type_name = line_type_obj.expense_line_types_name
        except expense_line_types.DoesNotExist:
            line_type_name = "Unknown"

    # Get month name for subtitle
    month_names = {
        '1': 'January', '2': 'February', '3': 'March', '4': 'April',
        '5': 'May', '6': 'June', '7': 'July', '8': 'August',
        '9': 'September', '10': 'October', '11': 'November', '12': 'December'
    }
    month_name = month_names.get(str(month), "All Months") if month else "All Months"

    # Phase 2: resolve budgeted figures to the selected year (same as the P&L).
    try:
        _year_int = int(year)
    except (TypeError, ValueError):
        _year_int = None
    _year_map = (resolve_year_months_bulk(
        list(expenses.values_list('prop_id', flat=True).distinct()),
        FinancialFigureHistory.KIND_BUDGET, _year_int) if _year_int is not None else None)

    # Create a list of expense items with monthly breakdown
    expense_items = []
    total_amount = 0

    for exp in expenses:
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

        for i, month_field in enumerate(months, 1):
            if _year_map is not None and exp.expense_id in _year_map:
                month_value = _year_map[exp.expense_id][i - 1]
            else:
                month_value = getattr(exp, f'expense_{month_field}', 0)

            if month_value and month_value > 0:
                # If specific month is requested, only show that month
                if month and int(month) != i:
                    continue

                expense_items.append({
                    'expense_id': exp.expense_id,
                    'property': exp.prop,
                    'amount': float(month_value),
                })
                total_amount += float(month_value)

    context = {
        'expense_items': expense_items,
        'total_amount': total_amount,
        'selected_year': year,
        'selected_month': month,
        'selected_line_type': line_type,
        'line_type_name': line_type_name,
        'month_name': month_name,
    }

    return render(request, 'budget_expense_details.html', context)


@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def total_expense_details_view(request):
    """
    View to show combined actual + budgeted expense details
    """
    year = request.GET.get('year', datetime.now().year)
    month = request.GET.get('month')
    property_id = request.GET.get('property_id')
    prop = request.GET.get('prop', 'all')

    # Get actual expenses
    actual_expenses = act_expense.objects.filter(
        act_expense_date__year=year
    ).select_related('prop')

    # Get budget expenses
    budget_expenses = expense.objects.filter(
        expense_types__expense_types_name__icontains=str(year)
    ).select_related('prop', 'expense_line_types', 'expense_types')

    # Filter by month if specified
    if month:
        actual_expenses = actual_expenses.filter(act_expense_date__month=month)

    # Filter by property
    if property_id:
        actual_expenses = actual_expenses.filter(prop_id=property_id)
        budget_expenses = budget_expenses.filter(prop_id=property_id)
    elif prop != 'all':
        actual_expenses = actual_expenses.filter(prop_id=prop)
        budget_expenses = budget_expenses.filter(prop_id=prop)

    # Order by date
    actual_expenses = actual_expenses.order_by('-act_expense_date')

    # Phase 2: resolve budgeted figures to the selected year.
    try:
        _year_int = int(year)
    except (TypeError, ValueError):
        _year_int = None
    _year_map = (resolve_year_months_bulk(
        list(budget_expenses.values_list('prop_id', flat=True).distinct()),
        FinancialFigureHistory.KIND_BUDGET, _year_int) if _year_int is not None else None)

    # Create budget expense items with monthly breakdown (similar to budget_expense_details_view)
    budget_expense_items = []
    for exp in budget_expenses:
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

        for i, month_name in enumerate(months, 1):
            if _year_map is not None and exp.expense_id in _year_map:
                month_value = _year_map[exp.expense_id][i - 1]
            else:
                month_value = getattr(exp, f'expense_{month_name}', 0)
            if month_value and month_value > 0:
                # If specific month is requested, only show that month
                if month and int(month) != i:
                    continue

                budget_expense_items.append({
                    'expense_id': exp.expense_id,
                    'property': exp.prop,
                    'expense_line_type': exp.expense_line_types,
                    'expense_type': exp.expense_types,
                    'month': i,
                    'month_name': month_name.capitalize(),
                    'amount': month_value,
                    'description': f"{exp.expense_line_types.expense_line_types_name} - {month_name.capitalize()} {year}",
                    'type': 'budget'
                })

    # Get line types and properties for context
    expense_line_types_list = expense_line_types.objects.all()
    properties = props.objects.all()

    context = {
        'actual_expenses': actual_expenses,
        'budget_expense_items': budget_expense_items,
        'expense_line_types': expense_line_types_list,
        'properties': properties,
        'selected_year': year,
        'selected_month': month,
        'selected_property': property_id,
        'prop': prop,
    }

    return render(request, 'total_expense_details.html', context)


@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def finance_pl_act(request):
    # Phase 2: the P&L is always viewed FOR A YEAR now. The old "Budget" dropdown
    # entry is replaced by a Budget/Actuals toggle (`view`): 'budget' shows the
    # budgeted revenue/expenses for the year; 'actuals' also adds that year's
    # actual expenses. Budgeted figures are resolved from history per year.
    _pl_today = date.today()
    _lease_min = tenant.objects.exclude(tenant_lease_start_date__isnull=True).aggregate(
        _m=Min('tenant_lease_start_date'))['_m']
    _earliest_year = _lease_min.year if _lease_min else _pl_today.year
    # earliest lease year .. current year + 1 (one future "next-year outlook"), newest first
    AVAILABLE_YEARS = list(range(_earliest_year, _pl_today.year + 2))[::-1]

    view_mode = request.GET.get('view', 'budget')
    if view_mode not in ('budget', 'actuals'):
        view_mode = 'budget'

    # Single-property mode: the per-property P&L opens the main P&L pre-filtered
    # to one property, with the property picker hidden.
    single_mode = request.GET.get('single') in ('1', 'true', 'yes', 'on')

    # Get selected properties from request
    selected_properties = request.GET.getlist('properties')

    # Year: default to the current year, falling back to the newest available.
    try:
        selected_year = int(request.GET.get('year'))
    except (TypeError, ValueError):
        selected_year = date.today().year
    if selected_year not in AVAILABLE_YEARS:
        selected_year = date.today().year if date.today().year in AVAILABLE_YEARS else AVAILABLE_YEARS[0]

    # Phase 2.1: for the current (unfinished) year, mark the months that have not
    # elapsed yet as projections. Column positions in the table are Jan=2..Dec=13.
    _today = date.today()
    is_current_year = (selected_year == _today.year)
    if is_current_year:
        _first_proj = _today.month
        projected_cols = list(range(_first_proj + 1, 14))
        _ABBR = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        projection_label = 'Dec' if _first_proj == 12 else (_ABBR[_first_proj - 1] + '–Dec')
        projection_note = ("The amber columns (%s %d) haven't finished yet — these figures "
                           "are projections and may change." % (projection_label, selected_year))
    elif selected_year > _today.year:
        projected_cols = list(range(2, 14))
        projection_label = 'Jan–Dec'
        projection_note = ("%d is a future year — the whole year is a projection "
                           "(next-year outlook) assuming your current leases continue at "
                           "today's rent." % selected_year)
    else:
        projected_cols = []
        projection_label = ''
        projection_note = ''

    # Single query with comprehensive prefetching
    # No prop_status filter here, deliberately. The P&L reports a YEAR, and a
    # property's status TODAY says nothing about whether it earned or cost money
    # in 2024. Filtering made a sold property vanish from every closed year at
    # once - the same failure as deleting a row, one level up.
    #
    # The effective-dated figures decide instead: close a sold property's
    # expenses from the sale date and its later years resolve to zero, and the
    # template already drops an all-zero line. lease_monthly_rent_levies stops
    # projecting assumed rent for an inactive property, so nothing is invented
    # forward either.
    all_properties = props.objects.all().select_related().prefetch_related(
        'prop_values_set',
        Prefetch('revenue_set', queryset=revenue.objects.select_related('revenue_line_types', 'revenue_types')),
        Prefetch('expense_set', queryset=expense.objects.select_related('expense_line_types', 'expense_types'))
    )

    # If no properties selected, default to ALL properties
    if not selected_properties:
        selected_properties = [str(prop.prop_id) for prop in all_properties]

    # Convert to integers and filter
    selected_prop_ids = [int(pid) for pid in selected_properties if pid.isdigit()]
    properties = all_properties.filter(prop_id__in=selected_prop_ids)

    # Single queries for line types
    revenue_line_types_list = list(revenue_line_types.objects.all())
    expense_line_types_list = list(expense_line_types.objects.all())

    # Use prefetched data instead of separate queries
    revenues = []
    expenses = []

    # Phase 3: REVENUE comes from the leases (rent + levies per month), not the
    # budgeted revenue table. Seasonal / no-lease properties fall back to the
    # table. Budgeted EXPENSES still resolve from the effective-dated history.
    _rental_lt = next((lt for lt in revenue_line_types_list if lt.lease_role == 'rent'), None)
    _levies_lt = next((lt for lt in revenue_line_types_list if lt.lease_role == 'levies'), None)
    for prop in properties:
        revenues.extend(lease_revenue_rows(prop, selected_year, _rental_lt, _levies_lt))
        expenses.extend(prop.expense_set.all())

    _fh_exp_map = resolve_year_months_bulk(selected_prop_ids, FinancialFigureHistory.KIND_BUDGET, selected_year)
    for _e in expenses:
        _vals = _fh_exp_map.get(_e.expense_id)
        if _vals is not None:
            for _i, _m in enumerate(MONTHS):
                setattr(_e, 'expense_' + _m, _vals[_i])

    # ========= REVENUE SECTION =========
    revenue_totals = {
        'jan': sum(r.revenue_jan or 0 for r in revenues),
        'feb': sum(r.revenue_feb or 0 for r in revenues),
        'mar': sum(r.revenue_mar or 0 for r in revenues),
        'apr': sum(r.revenue_apr or 0 for r in revenues),
        'may': sum(r.revenue_may or 0 for r in revenues),
        'jun': sum(r.revenue_jun or 0 for r in revenues),
        'jul': sum(r.revenue_jul or 0 for r in revenues),
        'aug': sum(r.revenue_aug or 0 for r in revenues),
        'sep': sum(r.revenue_sep or 0 for r in revenues),
        'oct': sum(r.revenue_oct or 0 for r in revenues),
        'nov': sum(r.revenue_nov or 0 for r in revenues),
        'dec': sum(r.revenue_dec or 0 for r in revenues),
    }
    revenue_totals['year'] = sum(revenue_totals.values())

    # Pre-group revenues by line type
    revenues_by_line_type = {}
    for rev in revenues:
        line_type_id = rev.revenue_line_types.revenue_line_types_id
        if line_type_id not in revenues_by_line_type:
            revenues_by_line_type[line_type_id] = []
        revenues_by_line_type[line_type_id].append(rev)

    # Calculate revenue totals by line type
    revenue_totals_by_line = {'all': {}}
    for lt in revenue_line_types_list:
        line_revenues = revenues_by_line_type.get(lt.revenue_line_types_id, [])
        monthly_totals = {
            'jan': sum(r.revenue_jan or 0 for r in line_revenues),
            'feb': sum(r.revenue_feb or 0 for r in line_revenues),
            'mar': sum(r.revenue_mar or 0 for r in line_revenues),
            'apr': sum(r.revenue_apr or 0 for r in line_revenues),
            'may': sum(r.revenue_may or 0 for r in line_revenues),
            'jun': sum(r.revenue_jun or 0 for r in line_revenues),
            'jul': sum(r.revenue_jul or 0 for r in line_revenues),
            'aug': sum(r.revenue_aug or 0 for r in line_revenues),
            'sep': sum(r.revenue_sep or 0 for r in line_revenues),
            'oct': sum(r.revenue_oct or 0 for r in line_revenues),
            'nov': sum(r.revenue_nov or 0 for r in line_revenues),
            'dec': sum(r.revenue_dec or 0 for r in line_revenues),
        }
        monthly_totals['total'] = sum(monthly_totals.values())
        revenue_totals_by_line['all'][lt.revenue_line_types_id] = monthly_totals

    # Pre-group revenues by property
    revenues_by_property = {}
    for rev in revenues:
        prop_id = rev.prop.prop_id
        if prop_id not in revenues_by_property:
            revenues_by_property[prop_id] = []
        revenues_by_property[prop_id].append(rev)

    # Calculate property-specific revenue totals
    revenue_prop_totals = {}
    for prop in properties:
        prop_revenues = revenues_by_property.get(prop.prop_id, [])
        monthly_totals = {
            'jan': sum(r.revenue_jan or 0 for r in prop_revenues),
            'feb': sum(r.revenue_feb or 0 for r in prop_revenues),
            'mar': sum(r.revenue_mar or 0 for r in prop_revenues),
            'apr': sum(r.revenue_apr or 0 for r in prop_revenues),
            'may': sum(r.revenue_may or 0 for r in prop_revenues),
            'jun': sum(r.revenue_jun or 0 for r in prop_revenues),
            'jul': sum(r.revenue_jul or 0 for r in prop_revenues),
            'aug': sum(r.revenue_aug or 0 for r in prop_revenues),
            'sep': sum(r.revenue_sep or 0 for r in prop_revenues),
            'oct': sum(r.revenue_oct or 0 for r in prop_revenues),
            'nov': sum(r.revenue_nov or 0 for r in prop_revenues),
            'dec': sum(r.revenue_dec or 0 for r in prop_revenues),
        }
        monthly_totals['year'] = sum(monthly_totals.values())
        revenue_prop_totals[prop.prop_id] = monthly_totals

        # Add property-specific revenue line type totals
        revenue_totals_by_line[prop.prop_id] = {}
        for lt in revenue_line_types_list:
            prop_line_revenues = [r for r in prop_revenues if r.revenue_line_types.revenue_line_types_id == lt.revenue_line_types_id]
            line_monthly_totals = {
                'jan': sum(r.revenue_jan or 0 for r in prop_line_revenues),
                'feb': sum(r.revenue_feb or 0 for r in prop_line_revenues),
                'mar': sum(r.revenue_mar or 0 for r in prop_line_revenues),
                'apr': sum(r.revenue_apr or 0 for r in prop_line_revenues),
                'may': sum(r.revenue_may or 0 for r in prop_line_revenues),
                'jun': sum(r.revenue_jun or 0 for r in prop_line_revenues),
                'jul': sum(r.revenue_jul or 0 for r in prop_line_revenues),
                'aug': sum(r.revenue_aug or 0 for r in prop_line_revenues),
                'sep': sum(r.revenue_sep or 0 for r in prop_line_revenues),
                'oct': sum(r.revenue_oct or 0 for r in prop_line_revenues),
                'nov': sum(r.revenue_nov or 0 for r in prop_line_revenues),
                'dec': sum(r.revenue_dec or 0 for r in prop_line_revenues),
            }
            line_monthly_totals['total'] = sum(line_monthly_totals.values())
            revenue_totals_by_line[prop.prop_id][lt.revenue_line_types_id] = line_monthly_totals

    # ========= EXPENSE SECTION =========
    # Initialize actual expense totals
    actual_expense_totals = {
        'jan': 0, 'feb': 0, 'mar': 0, 'apr': 0, 'may': 0, 'jun': 0,
        'jul': 0, 'aug': 0, 'sep': 0, 'oct': 0, 'nov': 0, 'dec': 0, 'year': 0
    }

    # Actual expenses with single aggregate query
    actual_expense_prop_totals = {}
    if view_mode == 'actuals':
        # Single query to get all actual expenses with month grouping
        actual_expenses_aggregated = act_expense.objects.filter(
            act_expense_date__year=selected_year,
            act_expense_approved="Yes",
            act_expense_paid="Yes",
            prop_id__in=selected_prop_ids
        ).values('prop_id', 'act_expense_date__month').annotate(
            total_amount=Sum('act_expense_amount')
        ).order_by('prop_id', 'act_expense_date__month')

        # Calculate monthly totals for all properties in one pass
        month_mapping = {
            1: 'jan', 2: 'feb', 3: 'mar', 4: 'apr', 5: 'may', 6: 'jun',
            7: 'jul', 8: 'aug', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dec'
        }

        # Initialize all property totals
        for prop in properties:
            actual_expense_prop_totals[prop.prop_id] = {month: 0 for month in month_mapping.values()}
            actual_expense_prop_totals[prop.prop_id]['year'] = 0

        # Process aggregated results
        for result in actual_expenses_aggregated:
            prop_id = result['prop_id']
            month_num = result['act_expense_date__month']
            amount = result['total_amount'] or 0

            if prop_id in actual_expense_prop_totals:
                month_name = month_mapping[month_num]
                actual_expense_prop_totals[prop_id][month_name] = amount
                actual_expense_prop_totals[prop_id]['year'] += amount

        # Calculate overall monthly totals
        for month_name in month_mapping.values():
            actual_expense_totals[month_name] = sum(
                actual_expense_prop_totals[prop.prop_id][month_name]
                for prop in properties
            )

        actual_expense_totals['year'] = sum(actual_expense_totals.values())

    # Calculate budgeted expense totals
    expense_totals = {
        'jan': sum(e.expense_jan or 0 for e in expenses),
        'feb': sum(e.expense_feb or 0 for e in expenses),
        'mar': sum(e.expense_mar or 0 for e in expenses),
        'apr': sum(e.expense_apr or 0 for e in expenses),
        'may': sum(e.expense_may or 0 for e in expenses),
        'jun': sum(e.expense_jun or 0 for e in expenses),
        'jul': sum(e.expense_jul or 0 for e in expenses),
        'aug': sum(e.expense_aug or 0 for e in expenses),
        'sep': sum(e.expense_sep or 0 for e in expenses),
        'oct': sum(e.expense_oct or 0 for e in expenses),
        'nov': sum(e.expense_nov or 0 for e in expenses),
        'dec': sum(e.expense_dec or 0 for e in expenses),
    }
    expense_totals['year'] = sum(expense_totals.values())

    # Pre-group expenses by line type
    expenses_by_line_type = {}
    for exp in expenses:
        line_type_id = exp.expense_line_types.expense_line_types_id
        if line_type_id not in expenses_by_line_type:
            expenses_by_line_type[line_type_id] = []
        expenses_by_line_type[line_type_id].append(exp)

    # Calculate expense totals by line type
    expense_totals_by_line = {'all': {}}
    for elt in expense_line_types_list:
        line_expenses = expenses_by_line_type.get(elt.expense_line_types_id, [])
        monthly_totals = {
            'jan': sum(e.expense_jan or 0 for e in line_expenses),
            'feb': sum(e.expense_feb or 0 for e in line_expenses),
            'mar': sum(e.expense_mar or 0 for e in line_expenses),
            'apr': sum(e.expense_apr or 0 for e in line_expenses),
            'may': sum(e.expense_may or 0 for e in line_expenses),
            'jun': sum(e.expense_jun or 0 for e in line_expenses),
            'jul': sum(e.expense_jul or 0 for e in line_expenses),
            'aug': sum(e.expense_aug or 0 for e in line_expenses),
            'sep': sum(e.expense_sep or 0 for e in line_expenses),
            'oct': sum(e.expense_oct or 0 for e in line_expenses),
            'nov': sum(e.expense_nov or 0 for e in line_expenses),
            'dec': sum(e.expense_dec or 0 for e in line_expenses),
        }
        monthly_totals['total'] = sum(monthly_totals.values())
        expense_totals_by_line['all'][elt.expense_line_types_id] = monthly_totals

    # Pre-group expenses by property
    expenses_by_property = {}
    for exp in expenses:
        prop_id = exp.prop.prop_id
        if prop_id not in expenses_by_property:
            expenses_by_property[prop_id] = []
        expenses_by_property[prop_id].append(exp)

    # Calculate property-specific expense totals
    expense_prop_totals = {}
    for prop in properties:
        prop_expenses = expenses_by_property.get(prop.prop_id, [])
        monthly_totals = {
            'jan': sum(e.expense_jan or 0 for e in prop_expenses),
            'feb': sum(e.expense_feb or 0 for e in prop_expenses),
            'mar': sum(e.expense_mar or 0 for e in prop_expenses),
            'apr': sum(e.expense_apr or 0 for e in prop_expenses),
            'may': sum(e.expense_may or 0 for e in prop_expenses),
            'jun': sum(e.expense_jun or 0 for e in prop_expenses),
            'jul': sum(e.expense_jul or 0 for e in prop_expenses),
            'aug': sum(e.expense_aug or 0 for e in prop_expenses),
            'sep': sum(e.expense_sep or 0 for e in prop_expenses),
            'oct': sum(e.expense_oct or 0 for e in prop_expenses),
            'nov': sum(e.expense_nov or 0 for e in prop_expenses),
            'dec': sum(e.expense_dec or 0 for e in prop_expenses),
        }
        monthly_totals['year'] = sum(monthly_totals.values())
        expense_prop_totals[prop.prop_id] = monthly_totals

        # Add property-specific expense line type totals
        expense_totals_by_line[prop.prop_id] = {}
        for elt in expense_line_types_list:
            prop_line_expenses = [e for e in prop_expenses if e.expense_line_types.expense_line_types_id == elt.expense_line_types_id]
            line_monthly_totals = {
                'jan': sum(e.expense_jan or 0 for e in prop_line_expenses),
                'feb': sum(e.expense_feb or 0 for e in prop_line_expenses),
                'mar': sum(e.expense_mar or 0 for e in prop_line_expenses),
                'apr': sum(e.expense_apr or 0 for e in prop_line_expenses),
                'may': sum(e.expense_may or 0 for e in prop_line_expenses),
                'jun': sum(e.expense_jun or 0 for e in prop_line_expenses),
                'jul': sum(e.expense_jul or 0 for e in prop_line_expenses),
                'aug': sum(e.expense_aug or 0 for e in prop_line_expenses),
                'sep': sum(e.expense_sep or 0 for e in prop_line_expenses),
                'oct': sum(e.expense_oct or 0 for e in prop_line_expenses),
                'nov': sum(e.expense_nov or 0 for e in prop_line_expenses),
                'dec': sum(e.expense_dec or 0 for e in prop_line_expenses),
            }
            line_monthly_totals['total'] = sum(line_monthly_totals.values())
            expense_totals_by_line[prop.prop_id][elt.expense_line_types_id] = line_monthly_totals

    # ========= PROFIT CALCULATION =========
    if view_mode == 'budget':
        profit_totals = {
            'jan': revenue_totals['jan'] - expense_totals['jan'],
            'feb': revenue_totals['feb'] - expense_totals['feb'],
            'mar': revenue_totals['mar'] - expense_totals['mar'],
            'apr': revenue_totals['apr'] - expense_totals['apr'],
            'may': revenue_totals['may'] - expense_totals['may'],
            'jun': revenue_totals['jun'] - expense_totals['jun'],
            'jul': revenue_totals['jul'] - expense_totals['jul'],
            'aug': revenue_totals['aug'] - expense_totals['aug'],
            'sep': revenue_totals['sep'] - expense_totals['sep'],
            'oct': revenue_totals['oct'] - expense_totals['oct'],
            'nov': revenue_totals['nov'] - expense_totals['nov'],
            'dec': revenue_totals['dec'] - expense_totals['dec'],
            'year': revenue_totals['year'] - expense_totals['year']
        }
    else:
        profit_totals = {
            'jan': revenue_totals['jan'] - expense_totals['jan'] - actual_expense_totals['jan'],
            'feb': revenue_totals['feb'] - expense_totals['feb'] - actual_expense_totals['feb'],
            'mar': revenue_totals['mar'] - expense_totals['mar'] - actual_expense_totals['mar'],
            'apr': revenue_totals['apr'] - expense_totals['apr'] - actual_expense_totals['apr'],
            'may': revenue_totals['may'] - expense_totals['may'] - actual_expense_totals['may'],
            'jun': revenue_totals['jun'] - expense_totals['jun'] - actual_expense_totals['jun'],
            'jul': revenue_totals['jul'] - expense_totals['jul'] - actual_expense_totals['jul'],
            'aug': revenue_totals['aug'] - expense_totals['aug'] - actual_expense_totals['aug'],
            'sep': revenue_totals['sep'] - expense_totals['sep'] - actual_expense_totals['sep'],
            'oct': revenue_totals['oct'] - expense_totals['oct'] - actual_expense_totals['oct'],
            'nov': revenue_totals['nov'] - expense_totals['nov'] - actual_expense_totals['nov'],
            'dec': revenue_totals['dec'] - expense_totals['dec'] - actual_expense_totals['dec'],
            'year': revenue_totals['year'] - expense_totals['year'] - actual_expense_totals['year']
        }

    # Property values using prefetched data - NO additional queries
    prop_values_map = {}
    total_current_value = 0

    for prop in properties:
        # Use the prefetched prop_values_set data
        prop_values_list = list(prop.prop_values_set.all())
        if prop_values_list:
            prop_vals = prop_values_list[0]
            prop_values_map[prop.prop_id] = prop_vals
            if prop_vals.prop_values_current_value is not None:
                total_current_value += prop_vals.prop_values_current_value
        else:
            prop_values_map[prop.prop_id] = None

    # ------------------------------------------------- CONSOLIDATED INDICATORS
    # These divide a YEAR's money by a stock figure - purchase price, floor
    # area, valuation - so who belongs in the denominator is a question about
    # that year, not about today.
    #
    # A property that earned nothing and cost nothing in the selected year was
    # not part of the portfolio then. An ACTIVE property always carries
    # expenses, so a property with nothing at all against it is either inactive
    # or not held yet; both are out. Testing the money rather than prop_status
    # means a property bought later is handled by the same rule, with no extra
    # code and no reliance on a status field being right.
    #
    # Expenses-to-Revenue is NOT gated, deliberately: both its sides come from
    # these same totals, so a silent property contributes zero to each and
    # already cancels out.
    ind_props, ind_skipped = [], []
    for prop in properties:
        _rev = (revenue_prop_totals.get(prop.prop_id) or {}).get('year') or 0
        _exp = (expense_prop_totals.get(prop.prop_id) or {}).get('year') or 0
        _act = (actual_expense_prop_totals.get(prop.prop_id) or {}).get('year') or 0
        if _rev or _exp or _act:
            ind_props.append(prop)
        else:
            ind_skipped.append(prop.prop_name)

    ind_purchase_total = 0
    ind_area_total = 0
    # Value Increase is read AS AT the selected year now. It used to sum
    # prop_values_current_value regardless of the year on screen, so 2022 showed
    # today's uplift. Purchase and valuation are accumulated together and only
    # for properties that actually have a dated valuation for the year, so the
    # two sides of the ratio always describe the same set of properties - the
    # same apples-to-apples rule the Detailed Property Data portfolio row uses.
    ind_value_total = 0
    ind_value_purchase = 0
    # Counted, because this is a SECOND denominator and it must not be silent
    # either. A property with no valuation dated this year or earlier leaves
    # BOTH sides of Value Increase, so that one chip can cover fewer properties
    # than the other four - and the note under the chips has to say so. Older
    # years are where this bites: valuation history has to start somewhere.
    ind_value_count = 0
    for prop in ind_props:
        _pv = prop_values_map.get(prop.prop_id)
        _purchase = (_pv.prop_values_purchase_price if _pv else 0) or 0
        ind_purchase_total += _purchase
        ind_area_total += (prop.prop_floor_area or 0)
        _as_of = property_value_as_of(prop, selected_year)
        if _as_of is not None and _purchase > 0:
            ind_value_total += _as_of
            ind_value_purchase += _purchase
            ind_value_count += 1

    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'properties': [{'id': p.prop_id, 'name': p.prop_name} for p in properties],
            'revenue_totals': revenue_totals,
            'expense_totals': expense_totals,
            'actual_expense_totals': actual_expense_totals,
            'profit_totals': profit_totals,
            'selected_properties': selected_properties,
        })

    return render(request, 'finance_pl_act.html', {
        'properties': properties,
        'all_properties': all_properties,
        'revenue_line_types': revenue_line_types_list,
        'revenue_totals': revenue_totals,
        'revenue_totals_by_line': revenue_totals_by_line,
        'revenue_prop_totals': revenue_prop_totals,
        'expense_line_types': expense_line_types_list,
        'expense_totals': expense_totals,
        'expense_totals_by_line': expense_totals_by_line,
        'expense_prop_totals': expense_prop_totals,
        'profit_totals': profit_totals,
        'prop_values_map': prop_values_map,
        'total_current_value': total_current_value,
        # Indicator denominators, pre-summed over the properties that actually
        # contributed to this year. Deliberately computed here rather than in
        # the template: the chips used to do five-deep {% with %} arithmetic on
        # a filtered queryset, which is neither testable nor readable.
        'ind_purchase_total': ind_purchase_total,
        'ind_area_total': ind_area_total,
        'ind_value_total': ind_value_total,
        'ind_value_purchase': ind_value_purchase,
        'ind_value_count': ind_value_count,
        'ind_count': len(ind_props),
        'ind_total_count': len(properties),
        'ind_skipped': ind_skipped,
        # The split Select All only needs to exist when there is something
        # inactive to split off.
        'has_inactive': any(
            (getattr(p, 'prop_status', 'Active') or 'Active') != 'Active'
            for p in all_properties),
        'actual_expense_totals': actual_expense_totals,
        'actual_expense_prop_totals': actual_expense_prop_totals,
        'selected_year': selected_year,
        'view_mode': view_mode,
        'current_year': date.today().year,
        'is_current_year': is_current_year,
        'projected_cols': projected_cols,
        'projection_label': projection_label,
        'projection_note': projection_note,
        'single_mode': single_mode,
        'single_property': (properties.first() if single_mode else None),
        'selected_properties': selected_properties,
        'available_years': AVAILABLE_YEARS,
    })