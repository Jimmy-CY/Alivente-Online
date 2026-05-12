"""
Finance views — extracted from pages/views/main.py.

Covers everything financial-budgeting (not actual-expense or invoices):
  - Revenue: list / add / edit / commit / types / line types
  - Expense: list / add / edit / commit / delete / types / line types
  - Valuations: list / add / edit / commit (with optional pro-rata cascade)

Commit views follow a consistent pattern:
  1. Validate POST + required fields
  2. Wrap mutating work in transaction.atomic() so partial writes can't escape
  3. Catch specific exceptions (model.DoesNotExist, JSONDecodeError) with
     focused user-facing messages
  4. Catch-all logs the traceback and surfaces a generic error message
  5. Always redirect/render with a flash message — never leave a 500 white screen
"""

import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import Prefetch, Subquery, OuterRef
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