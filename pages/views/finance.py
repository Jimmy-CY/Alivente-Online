"""
Finance views — extracted from pages/views/main.py.

PHASE 1 — Financial-budgeting CRUD:
  - Revenue: list / add / edit / commit / types / line types
  - Expense: list / add / edit / commit / delete / types / line types
  - Valuations: list / add / edit / commit (with optional pro-rata cascade)

PHASE 2 — Reports:
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
  5. Always redirect/render with a flash message — never leave a 500 white screen

Report views are read-only and don't need the atomic pattern.

Occupancy/portfolio helper functions live in pages/views/dashboard.py and are
imported below. They moved out of main.py during the dashboard split.
"""
import decimal
import json
import logging
from calendar import monthrange
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import Min, OuterRef, Prefetch, Subquery, Sum
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from pages.forms import (
    RevenueForm, RevenueTypesForm, RevenueLineForm,
    ExpenseTypesForm, ExpenseLineForm, ValuesForm,
)
from pages.models import (
    props, prop_values,
    revenue, revenue_types, revenue_line_types,
    expense, expense_types, expense_line_types,
    tenant, act_expense, VacancyPeriod,
)

# Helpers live in dashboard.py (occupancy + portfolio calculations).
from .dashboard import (
    calculate_year_metrics,
    calculate_property_revenue,
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
    if prop_output is None or prop_output == "All":
        props_data = props.objects.prefetch_related(
            Prefetch(
                'revenue_set',
                queryset=revenue.objects.select_related('revenue_line_types', 'revenue_types'),
            )
        ).all().order_by('prop_country', 'prop_name')
    else:
        props_data = props.objects.prefetch_related(
            Prefetch(
                'revenue_set',
                queryset=revenue.objects.select_related('revenue_line_types', 'revenue_types'),
            )
        ).all().order_by('prop_country', 'prop_name').filter(prop_name=prop_output)
    return render(request, "finance_revenue.html", {"props_data": props_data})


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
def finance_revenue_add(request):
    return render(request, "finance_revenue_add.html", {
        "props_data": props.objects.all().order_by('prop_country', 'prop_name'),
        "revenue_types": revenue_types.objects.all(),
        "revenue_line_types": revenue_line_types.objects.all(),
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

            revenue.objects.update_or_create(
                prop_id=prop_id,
                revenue_line_types_id=rlt_id,
                revenue_types_id=rt_id,
                defaults=monthly_data,
            )
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
    return render(request, "finance_revenue_edit.html", {
        "rev": rev,
        "props_data": props.objects.all().order_by('prop_country', 'prop_name'),
        "revenue_types": revenue_types.objects.all(),
        "revenue_line_types": revenue_line_types.objects.all(),
        "form": RevenueForm(instance=rev),
    })


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
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

            for key, value in monthly_data.items():
                setattr(rev, key, value)
            rev.save()

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
    return render(request, "finance_expense.html", {"props_data": props_data})


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
                    expense.objects.update_or_create(
                        prop_id=property_data['prop_id'],
                        expense_line_types_id=elt_id,
                        expense_types_id=et_id,
                        defaults=monthly_data,
                    )

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

            expense.objects.update_or_create(
                prop_id=prop_id,
                expense_line_types_id=elt_id,
                expense_types_id=et_id,
                defaults=monthly_data,
            )
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

    linked_property_ids = list(
        expense.objects.filter(
            expense_line_types_id=existing_expense.expense_line_types_id,
            expense_types_id=existing_expense.expense_types_id,
        ).values_list('prop_id', flat=True)
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

                expense.objects.filter(
                    expense_line_types_id=existing_expense.expense_line_types_id,
                    expense_types_id=existing_expense.expense_types_id,
                ).delete()

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
                    expense.objects.create(**monthly_data)

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

            for field, value in monthly_data.items():
                setattr(existing_expense, field, value)
            existing_expense.save()

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
def finance_expense_delete(request, expense_id):
    """
    Delete a budgeted expense row.

    Hard delete — mirrors the mark_deleted pattern from act_expense. Budgeted
    expenses are planning data (not financial transactions), so a true
    audit-trail soft delete isn't required here.

    For pro-rata expenses, this deletes only the single row clicked. Other
    properties in the same pro-rata group remain. To remove the whole
    distribution, the user deletes each row individually.
    """
    if request.method != "POST":
        return redirect('finance_expense')

    try:
        exp = get_object_or_404(expense, expense_id=expense_id)
        with transaction.atomic():
            prop_name = exp.prop.prop_name if exp.prop else f"#{exp.expense_id}"
            type_name = exp.expense_types.expense_types_name if exp.expense_types else ""
            exp.delete()
        label = f"{prop_name}" + (f" — {type_name}" if type_name else "")
        messages.success(request, f"Expense '{label}' deleted successfully.")
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
def delete_expense_line_type(request, expense_line_type_id):
    """Delete an Expense Line Type and all its linked expenses."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        with transaction.atomic():
            elt = get_object_or_404(expense_line_types, expense_line_types_id=expense_line_type_id)
            linked = expense.objects.filter(expense_line_types=elt)
            expense_count = linked.count()
            linked.delete()

            name = elt.expense_line_types_name
            elt.delete()

            if expense_count > 0:
                message = f'Expense line type "{name}" and {expense_count} linked expense(s) have been deleted successfully.'
            else:
                message = f'Expense line type "{name}" has been deleted successfully.'

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

        for p in affected:
            p['share_percentage'] = round((p['current_value'] / total_current_value) * 100, 2)
            p['new_amount'] = round((new_pr_amount * p['current_value']) / total_current_value, 2)
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

@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def finance_valuations(request):
    props_list = props.objects.all().order_by('prop_country', 'prop_name')
    valuations = prop_values.objects.all()
    valuations_dict = {v.prop_id: v for v in valuations}

    pur_balance = sum(
        v.prop_values_purchase_price for v in valuations
        if v.prop_values_purchase_price is not None
    )
    cur_balance = sum(
        v.prop_values_current_value for v in valuations
        if v.prop_values_current_value is not None
    )

    return render(request, "finance_valuations.html", {
        "props": props_list,
        "prop_values": valuations_dict,
        "pur_balance": pur_balance,
        "cur_balance": cur_balance,
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
                form.save()
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
def finance_valuations_edit_commit(request, prop_values_id):
    vresult = get_object_or_404(prop_values, pk=prop_values_id)

    if request.method != "POST":
        return redirect('finance_valuations')

    try:
        with transaction.atomic():
            form = ValuesForm(request.POST, instance=vresult)
            if form.is_valid():
                form.save()
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

        affected_expenses = expense.objects.filter(
            prop_id=pv.prop_id,
            expense_line_types__expense_line_types_prorata='Yes',
        ).select_related('expense_line_types')

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
            })

        line_types_payload = []
        total_affected_expense_records = 0

        for lt_id in line_type_ids:
            try:
                lt = expense_line_types.objects.get(expense_line_types_id=lt_id)
            except expense_line_types.DoesNotExist:
                continue

            pr_amount = float(lt.expense_line_types_pr_amount or 0)
            lt_expenses = expense.objects.filter(expense_line_types_id=lt_id).select_related('prop')
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
                except props.DoesNotExist:
                    p_name = 'Unknown'

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

            line_types_payload.append({
                'line_type_id': lt_id,
                'line_type_name': lt.expense_line_types_name,
                'pr_amount': pr_amount,
                'total_current_value_old': total_cv_old,
                'total_current_value_new': total_cv_new,
                'property_count': len(prop_rows),
                'properties': prop_rows,
            })

        line_types_payload.sort(key=lambda lt: lt['line_type_name'].lower())

        return JsonResponse({
            'success': True,
            'prop_id': pv.prop_id,
            'prop_name': prop_name,
            'old_current_value': old_cv,
            'new_current_value': new_cv,
            'affected_line_types_count': len(line_types_payload),
            'affected_expense_count': total_affected_expense_records,
            'line_types': line_types_payload,
        })
    except Exception as e:
        logger.exception("preview_valuation_change failed")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@permission_required('auth.can_edit_financials', raise_exception=True)
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
            form.save()

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
# PHASE 2 — Reports (read-only views; no atomic pattern needed)
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
        return JsonResponse({"expenses": expenses})

    return render(request, "finance/cashflow_forecast.html")


@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def occupancy_trends_view(request):
    """
    Display occupancy, days to fill, and vacancy cost trends over time
    """
    from datetime import date
    from django.db.models import Min

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
def financial_indicators_view(request):
    """
    Display the Financial Indicators Dashboard - ONLY for Active Properties
    Using Portfolio-Wide Calculations with Occupancy Metrics
    OPTIMIZED: Reduced queries with prefetch_related
    """
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX request for property data
        try:
            from datetime import datetime, timedelta

            # Financial indicators show annual data (no time period selection)
            today = datetime.now().date()
            current_year = datetime.now().year

            # OPTIMIZATION: Prefetch related data in one query
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
                'total_purchase_price': Decimal('0.00'),
                'total_current_value': Decimal('0.00'),
                'total_floor_area': 0,
                'property_count': 0
            }

            for prop in properties:
                # Get revenue totals using your existing revenue model structure
                revenue_total = calculate_property_revenue(prop)

                # Get ONLY budgeted expense totals using your existing expense model
                budgeted_expense_total = calculate_property_budgeted_expenses(prop)

                # Get property values - ONLY for active properties
                # Use prefetched data
                property_values_list = list(prop.prop_values_set.all())
                property_values = property_values_list[0] if property_values_list else None
                purchase_price = property_values.prop_values_purchase_price if property_values else 0
                current_value = property_values.prop_values_current_value if property_values else 0

                # Add to portfolio totals
                portfolio_totals['total_revenue'] += revenue_total
                portfolio_totals['total_budgeted_expenses'] += budgeted_expense_total
                portfolio_totals['total_purchase_price'] += purchase_price or 0
                portfolio_totals['total_current_value'] += current_value or 0
                portfolio_totals['total_floor_area'] += prop.prop_floor_area or 0
                portfolio_totals['property_count'] += 1

                # Calculate individual property indicators for display purposes
                gross_roi = (revenue_total / purchase_price * 100) if purchase_price > 0 else 0
                net_roi = ((revenue_total - budgeted_expense_total) / purchase_price * 100) if purchase_price > 0 else 0
                expense_ratio = (budgeted_expense_total / revenue_total * 100) if revenue_total > 0 else 0
                rent_per_sqm = (revenue_total / 12 / prop.prop_floor_area) if prop.prop_floor_area and prop.prop_floor_area > 0 else 0
                value_increase = ((current_value - purchase_price) / purchase_price * 100) if purchase_price > 0 and current_value > 0 else 0

                # Store individual property data
                properties_data.append({
                    'id': prop.prop_id,
                    'name': prop.prop_name or f"Property {prop.prop_id}",
                    'status': prop.prop_status,
                    'grossROI': round(float(gross_roi), 2),
                    'netROI': round(float(net_roi), 2),
                    'expensesToRevenue': round(float(expense_ratio), 2),
                    'rentPerSqm': round(float(rent_per_sqm), 2),
                    'valueIncrease': round(float(value_increase), 2),
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
                    ((portfolio_totals['total_revenue'] - portfolio_totals['total_budgeted_expenses']) /
                     portfolio_totals['total_purchase_price'] * 100)
                    if portfolio_totals['total_purchase_price'] > 0 else 0
                ), 2),
                'expensesToRevenue': round(float(
                    (portfolio_totals['total_budgeted_expenses'] / portfolio_totals['total_revenue'] * 100)
                    if portfolio_totals['total_revenue'] > 0 else 0
                ), 2),
                'rentPerSqm': round(float(
                    (portfolio_totals['total_revenue'] / 12 / portfolio_totals['total_floor_area'])
                    if portfolio_totals['total_floor_area'] > 0 else 0
                ), 2),
                'valueIncrease': round(float(
                    ((portfolio_totals['total_current_value'] - portfolio_totals['total_purchase_price']) /
                     portfolio_totals['total_purchase_price'] * 100)
                    if portfolio_totals['total_purchase_price'] > 0 and portfolio_totals['total_current_value'] > 0 else 0
                ), 2)
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
                'message': f'Showing {len(properties_data)} active properties - Financial Indicators (annual data)'
            })

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return JsonResponse({'error': str(e)}, status=500)

    # Regular page load
    context = {
        'page_title': 'Financial Indicators Dashboard - Portfolio-Wide Analysis (Active Properties)'
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
            from datetime import datetime, timedelta

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

            # OPTIMIZATION: Prefetch related data in one query
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
            import traceback
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

    # Create a list of revenue items with monthly breakdown
    revenue_items = []
    total_amount = 0

    for rev in revenues:
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

        for i, month_name_field in enumerate(months, 1):
            month_value = getattr(rev, f'revenue_{month_name_field}', 0)

            if month_value and month_value > 0:
                # If specific month is requested, only show that month
                if month and int(month) != i:
                    continue

                revenue_items.append({
                    'revenue_id': rev.revenue_id,
                    'property': rev.prop,
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

    # Create a list of expense items with monthly breakdown
    expense_items = []
    total_amount = 0

    for exp in expenses:
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

        for i, month_field in enumerate(months, 1):
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

    # Create budget expense items with monthly breakdown (similar to budget_expense_details_view)
    budget_expense_items = []
    for exp in budget_expenses:
        months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

        for i, month_name in enumerate(months, 1):
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
    # Get selected year from request (default to 'budget')
    selected_year = request.GET.get('year', 'budget')

    # Get selected properties from request
    selected_properties = request.GET.getlist('properties')

    # Handle year parameter - can be 'budget' or a year number
    if selected_year != 'budget':
        try:
            selected_year = int(selected_year)
            # Ensure only 2024, 2025, or 2026 is selectable
            if selected_year not in [2024, 2025, 2026]:
                selected_year = 'budget'
        except (ValueError, TypeError):
            selected_year = 'budget'

    # FULLY OPTIMIZED: Single query with comprehensive prefetching
    all_properties = props.objects.filter(prop_status="Active").select_related().prefetch_related(
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

    # OPTIMIZED: Single queries for line types
    revenue_line_types_list = list(revenue_line_types.objects.all())
    expense_line_types_list = list(expense_line_types.objects.all())

    # OPTIMIZED: Use prefetched data instead of separate queries
    revenues = []
    expenses = []

    for prop in properties:
        revenues.extend(prop.revenue_set.all())
        expenses.extend(prop.expense_set.all())

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

    # OPTIMIZED: Pre-group revenues by line type
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

    # OPTIMIZED: Pre-group revenues by property
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

    # FULLY OPTIMIZED: Actual expenses with single aggregate query
    actual_expense_prop_totals = {}
    if selected_year != 'budget':
        from django.db.models import Sum

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

    # OPTIMIZED: Pre-group expenses by line type
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

    # OPTIMIZED: Pre-group expenses by property
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
    if selected_year == 'budget':
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

    # FULLY OPTIMIZED: Property values using prefetched data - NO additional queries
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
        'actual_expense_totals': actual_expense_totals,
        'actual_expense_prop_totals': actual_expense_prop_totals,
        'selected_year': selected_year,
        'selected_properties': selected_properties,
        'available_years': [2026, 2025, 2024],
    })
