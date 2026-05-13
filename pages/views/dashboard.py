"""
Dashboard views — extracted from pages/views/main.py.

Views:
  - property_management_dashboard: spoke-and-wheel landing page with a
    property selector and tiles that drill into per-property data.
  - property_detail: dispatcher view; each tile renders a slice of property
    data (tenant, lease, invoices, issues, valuation, revenues, etc.) gated
    by the owning module's access permission.
  - dashboard_pl: dedicated Profit & Loss view (separate URL because it
    needs a more complex monthly grid than property_detail can render).

Helpers (also used by finance.py — and by Properties / Tenants modules
once they split out of main.py):
  - get_property_first_tenant_date_optimized
  - calculate_effective_period
  - calculate_occupancy_metrics_with_period
  - calculate_portfolio_occupancy_with_period
  - calculate_year_metrics
  - calculate_property_revenue
  - calculate_property_budgeted_expenses

Permission model:
  - property_management_dashboard: auth.can_access_dashboard
  - dashboard_pl: auth.can_access_financials
  - property_detail: login_required at the view level, but each box_type
    is further gated against the owning module's permission since the
    dashboard is a cross-module launcher.
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Prefetch, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from pages.models import (
    props, prop_values,
    revenue, revenue_line_types,
    expense, expense_line_types,
    tenant, VacancyPeriod,
    invoices, issues,
    PropertyAsset, AssetMaintenance,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Helpers — occupancy / portfolio / year metrics / revenue / budgeted expenses
# ============================================================================

def get_property_first_tenant_date_optimized(prop):
    """
    Get the date when the property became operational using PREFETCHED data.
    Returns None if property has no tenants.
    """
    # Use prefetched tenant_set instead of querying
    property_tenants = [t for t in prop.tenant_set.all()
                       if t.tenant_lease_start_date is not None]

    if not property_tenants:
        return None

    # Find first tenant by lease start date
    first_tenant = min(property_tenants, key=lambda t: t.tenant_lease_start_date)
    return first_tenant.tenant_lease_start_date


def calculate_effective_period(first_tenant_date, period_start, period_end):
    """
    Calculate the effective period for a property based on when it became operational.
    Never count days before the first tenant.

    Returns: (effective_start, effective_end) or (None, None) if no valid period
    """
    if not first_tenant_date:
        return None, None

    # Property wasn't operational before first tenant
    effective_start = max(first_tenant_date, period_start)
    effective_end = period_end

    # If effective start is after period end, no valid period
    if effective_start > effective_end:
        return None, None

    return effective_start, effective_end


def calculate_occupancy_metrics_with_period(prop, period_start, period_end):
    """
    Calculate occupancy metrics for a specific time period.
    Only counts operational days (after first tenant).
    FIXED: Uses prefetched data and handles OPEN vacancies correctly.
    """
    # Get property's first tenant date using PREFETCHED data
    first_tenant_date = get_property_first_tenant_date_optimized(prop)

    if not first_tenant_date:
        return {
            'occupancy_rate': None,
            'avg_days_to_fill': None,
            'is_currently_vacant': False,
            'current_vacancy_days': 0
        }

    # Calculate effective period (never before first tenant)
    effective_start, effective_end = calculate_effective_period(
        first_tenant_date, period_start, period_end
    )

    if not effective_start:
        return {
            'occupancy_rate': None,
            'avg_days_to_fill': None,
            'is_currently_vacant': False,
            'current_vacancy_days': 0
        }

    # Total days in effective period
    total_days = (effective_end - effective_start).days + 1

    # Use PREFETCHED vacancy data
    all_vacancies = list(prop.vacancy_periods.all())

    # Filter vacancies that overlap with the period
    vacancies = [
        v for v in all_vacancies
        if (v.start_date >= first_tenant_date and  # Only operational vacancies
            v.start_date <= effective_end and
            (v.status == 'FILLED' or v.status == 'OPEN'))
    ]

    # Calculate vacant days in period
    vacant_days_in_period = 0
    total_days_to_fill = 0
    filled_vacancy_count = 0
    is_currently_vacant = False
    current_vacancy_days = 0

    today = datetime.now().date()

    for vacancy in vacancies:
        # Calculate overlap with effective period
        vacancy_start = max(vacancy.start_date, effective_start)

        # FIXED: Handle OPEN vacancies correctly
        if vacancy.status == 'OPEN':
            # For OPEN vacancies, use today or effective_end, whichever is earlier
            vacancy_end = min(today, effective_end)
        else:
            # For FILLED vacancies, use the actual end date
            vacancy_end = min(vacancy.end_date, effective_end)

        # Only count if vacancy actually overlaps with period
        if vacancy_start <= vacancy_end:
            days_in_period = (vacancy_end - vacancy_start).days + 1
            vacant_days_in_period += days_in_period

            # For avg days to fill calculation
            if vacancy.status == 'FILLED':
                # Use the full vacancy duration
                total_days_to_fill += vacancy.days_vacant
                filled_vacancy_count += 1
            elif vacancy.status == 'OPEN':
                # For current vacancy, count days so far
                days_so_far = (today - vacancy.start_date).days + 1
                total_days_to_fill += days_so_far
                filled_vacancy_count += 1
                is_currently_vacant = True
                current_vacancy_days = days_so_far

    # SAFETY CHECK: Vacant days cannot exceed total days
    vacant_days_in_period = min(vacant_days_in_period, total_days)

    # Calculate occupancy rate
    occupied_days = total_days - vacant_days_in_period
    occupancy_rate = (occupied_days / total_days * 100) if total_days > 0 else 0

    # Calculate average days to fill
    avg_days_to_fill = (total_days_to_fill / filled_vacancy_count) if filled_vacancy_count > 0 else 0

    return {
        'occupancy_rate': round(occupancy_rate, 1),
        'avg_days_to_fill': round(avg_days_to_fill, 1),
        'is_currently_vacant': is_currently_vacant,
        'current_vacancy_days': current_vacancy_days
    }


def calculate_portfolio_occupancy_with_period(properties, period_start, period_end):
    """
    Calculate portfolio-wide occupancy metrics for a specific time period.
    """
    total_occupied_days = 0
    total_possible_days = 0
    total_days_to_fill = 0
    property_count = 0  # Count ALL properties for average

    for prop in properties:
        metrics = calculate_occupancy_metrics_with_period(prop, period_start, period_end)

        if metrics['occupancy_rate'] is not None:
            # Get effective period for this property
            first_tenant_date = get_property_first_tenant_date_optimized(prop)
            if first_tenant_date:
                effective_start, effective_end = calculate_effective_period(
                    first_tenant_date, period_start, period_end
                )

                if effective_start:
                    property_total_days = (effective_end - effective_start).days + 1
                    property_occupied_days = int(property_total_days * metrics['occupancy_rate'] / 100)

                    total_possible_days += property_total_days
                    total_occupied_days += property_occupied_days

                    # Add ALL properties' days to fill (including 0)
                    total_days_to_fill += metrics['avg_days_to_fill']
                    property_count += 1

    portfolio_occupancy = (total_occupied_days / total_possible_days * 100) if total_possible_days > 0 else 0
    # Calculate average across ALL properties (not just those with vacancies)
    portfolio_avg_days = (total_days_to_fill / property_count) if property_count > 0 else 0

    return {
        'occupancy_rate': round(portfolio_occupancy, 1),
        'avg_days_to_fill': round(portfolio_avg_days, 1)
    }


def calculate_year_metrics(year):
    """
    OPTIMIZED: Calculate ALL metrics for a specific calendar year.
    Uses prefetch and processes in Python to minimize database queries.
    """
    # Define year boundaries
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)
    today = date.today()

    # If current year, use today as end date
    if year == today.year:
        year_end = today
        is_current_year = True
    else:
        is_current_year = False

    # ==================== FETCH ALL DATA AT ONCE ====================

    # Get all active, non-seasonal properties WITH their tenants prefetched
    active_properties = props.objects.filter(
        prop_status='Active'
    ).prefetch_related(
        Prefetch(
            'tenant_set',
            queryset=tenant.objects.filter(
                tenant_lease_start_date__isnull=False
            ).order_by('tenant_lease_start_date'),
            to_attr='all_tenants'
        )
    )

    # Get all vacancies for this year WITH related objects prefetched
    year_vacancies = VacancyPeriod.objects.filter(
        status='FILLED',
        end_date__year=year
    ).select_related(
        'prop',
        'previous_lease',
        'next_lease'
    )

    # ==================== PROCESS IN PYTHON ====================

    total_available_days = 0
    total_occupied_days = 0
    property_count = 0
    property_details = []

    for prop in active_properties:
        # Skip seasonal properties
        if hasattr(prop, 'exclude_from_metrics') and prop.exclude_from_metrics:
            continue

        # Get tenants from prefetched data
        tenants_list = prop.all_tenants

        if not tenants_list:
            continue

        # Find first tenant (already sorted by start date)
        first_tenant = tenants_list[0]

        # Determine operational start for this property in this year
        operational_start = max(
            first_tenant.tenant_lease_start_date,
            year_start
        )

        # Skip if property wasn't operational yet in this year
        if operational_start > year_end:
            continue

        # This property has data for this year
        property_count += 1

        # Calculate available days (operational days only)
        available_days = (year_end - operational_start).days + 1
        total_available_days += available_days

        # Calculate occupied days for this property in this year
        occupied_days = 0

        for t in tenants_list:
            # Calculate overlap between tenant lease and this year period
            lease_start = max(
                t.tenant_lease_start_date,
                operational_start
            )

            lease_end = min(
                t.tenant_lease_end_date if t.tenant_lease_end_date else year_end,
                year_end
            )

            # Add occupied days if there's an overlap
            if lease_start <= lease_end:
                days = (lease_end - lease_start).days + 1
                occupied_days += days

        total_occupied_days += occupied_days
        vacant_days = available_days - occupied_days

        # Calculate property occupancy
        prop_occupancy = (occupied_days / available_days * 100) if available_days > 0 else 0

        # Store property details for modal
        property_details.append({
            'name': prop.prop_name,
            'available_days': available_days,
            'occupied_days': occupied_days,
            'vacant_days': vacant_days,
            'occupancy_rate': round(prop_occupancy, 1)
        })

    # Calculate overall occupancy rate
    if total_available_days > 0:
        occupancy_rate = (total_occupied_days / total_available_days) * 100
    else:
        occupancy_rate = 0

    # ==================== PROCESS VACANCIES (Already Prefetched) ====================

    vacancy_days_list = []
    vacancy_details = []
    total_vacancy_cost = 0

    for v in year_vacancies:
        # Skip seasonal properties (already checked in queryset, but double-check)
        if hasattr(v.prop, 'exclude_from_metrics') and v.prop.exclude_from_metrics:
            continue

        vacancy_days_list.append(v.days_vacant)

        # Calculate vacancy cost
        monthly_rent = 0
        if v.next_lease:
            monthly_rent = v.next_lease.tenant_rent
        elif v.previous_lease:
            monthly_rent = v.previous_lease.tenant_rent

        vacancy_cost = (v.days_vacant / 30) * monthly_rent
        total_vacancy_cost += vacancy_cost

        # Store vacancy details for modal
        vacancy_details.append({
            'property': v.prop.prop_name,
            'start_date': v.start_date.strftime('%Y-%m-%d'),
            'end_date': v.end_date.strftime('%Y-%m-%d'),
            'days': v.days_vacant,
            'previous_tenant': v.previous_lease.tenant_name if v.previous_lease else 'None',
            'next_tenant': v.next_lease.tenant_name if v.next_lease else 'None',
            'cost': round(vacancy_cost, 2)
        })

    # Calculate average days to fill - SIMPLE AVERAGE across all properties
    # This matches the methodology in vacancy_management_view
    # Properties with no vacancies contribute 0 days to the average
    if property_count > 0:
        avg_days_to_fill = sum(vacancy_days_list) / property_count
    else:
        avg_days_to_fill = 0

    # ==================== RETURN ALL METRICS ====================

    return {
        'year': year,
        'is_current_year': is_current_year,

        # Summary metrics (for chart display)
        'occupancy_rate': round(occupancy_rate, 1),
        'avg_days_to_fill': round(avg_days_to_fill, 1),
        'vacancy_cost': round(total_vacancy_cost, 0),

        # Occupancy details (for modal)
        'total_available_days': total_available_days,
        'total_occupied_days': total_occupied_days,
        'total_vacant_days': total_available_days - total_occupied_days,
        'property_count': property_count,
        'property_details': sorted(property_details, key=lambda x: x['occupancy_rate'], reverse=True),

        # Vacancy details (for modal)
        'vacancy_count': len(vacancy_days_list),
        'vacancy_details': sorted(vacancy_details, key=lambda x: x['start_date']),
    }


def calculate_property_revenue(property_obj):
    """
    Calculate total annual revenue for a property using your revenue model
    ONLY processes Active properties
    """
    # Additional safety check - only calculate for active properties
    if property_obj.prop_status != 'Active':
        return Decimal('0.00')

    # Get all revenue records for this active property
    revenue_records = revenue.objects.filter(prop=property_obj)

    total_revenue = Decimal('0.00')

    for record in revenue_records:
        # Sum all monthly revenue amounts
        monthly_total = (
            (record.revenue_jan or Decimal('0.00')) +
            (record.revenue_feb or Decimal('0.00')) +
            (record.revenue_mar or Decimal('0.00')) +
            (record.revenue_apr or Decimal('0.00')) +
            (record.revenue_may or Decimal('0.00')) +
            (record.revenue_jun or Decimal('0.00')) +
            (record.revenue_jul or Decimal('0.00')) +
            (record.revenue_aug or Decimal('0.00')) +
            (record.revenue_sep or Decimal('0.00')) +
            (record.revenue_oct or Decimal('0.00')) +
            (record.revenue_nov or Decimal('0.00')) +
            (record.revenue_dec or Decimal('0.00'))
        )
        total_revenue += monthly_total

    return total_revenue


def calculate_property_budgeted_expenses(property_obj):
    """
    Calculate total annual budgeted expenses for a property using your expense model
    ONLY processes Active properties
    """
    # Additional safety check - only calculate for active properties
    if property_obj.prop_status != 'Active':
        return Decimal('0.00')

    # Get all budgeted expense records for this active property
    expense_records = expense.objects.filter(prop=property_obj)

    total_expenses = Decimal('0.00')

    for record in expense_records:
        # Sum all monthly expense amounts
        monthly_total = (
            (record.expense_jan or Decimal('0.00')) +
            (record.expense_feb or Decimal('0.00')) +
            (record.expense_mar or Decimal('0.00')) +
            (record.expense_apr or Decimal('0.00')) +
            (record.expense_may or Decimal('0.00')) +
            (record.expense_jun or Decimal('0.00')) +
            (record.expense_jul or Decimal('0.00')) +
            (record.expense_aug or Decimal('0.00')) +
            (record.expense_sep or Decimal('0.00')) +
            (record.expense_oct or Decimal('0.00')) +
            (record.expense_nov or Decimal('0.00')) +
            (record.expense_dec or Decimal('0.00'))
        )
        total_expenses += monthly_total

    return total_expenses


# ============================================================================
# Views — dashboard landing + property detail dispatcher + dashboard P&L
# ============================================================================

@permission_required('auth.can_access_dashboard', raise_exception=True)
@login_required
def property_management_dashboard(request):
    """
    Main property dashboard view with spoke-and-wheel interface
    """
    try:
        # Get all properties for the dropdown
        properties = props.objects.filter(prop_status='Active').order_by('prop_name')

        # Check if a specific property was selected
        selected_property_id = request.GET.get('property')
        selected_property = None

        if selected_property_id:
            try:
                selected_property = props.objects.get(prop_id=selected_property_id)
            except props.DoesNotExist:
                messages.error(request, f"Property with ID {selected_property_id} not found.")

        context = {
            'properties': properties,
            'selected_property': selected_property,
        }

        return render(request, 'property_management_dashboard.html', context)

    except Exception as e:
        messages.error(request, f"Error loading dashboard: {str(e)}")
        return redirect('properties')


@login_required
def property_detail(request, property_id, box_type):
    """
    Dispatcher view for dashboard tiles. Each box_type renders a slice of
    property data, gated by the owning module's access permission.
    """
    # Map box_type to owning module's access permission.
    # Dashboard is a cross-module launcher; each tile is gated by the
    # underlying module's access permission.
    box_type_permissions = {
        'property-report':    'auth.can_access_properties',
        'title-deed':         'auth.can_access_properties',
        'tenant':             'auth.can_access_tenants',
        'lease':              'auth.can_access_tenants',
        'lease-renewals':     'auth.can_access_tenants',
        'open-invoices':      'auth.can_access_invoices',
        'issues':             'auth.can_access_issues',
        'valuation':          'auth.can_access_financials',
        'revenues':           'auth.can_access_financials',
        'budgeted-expenses':  'auth.can_access_financials',
        'actual-expenses':    'auth.can_access_expenses',
        'profit-loss':        'auth.can_access_financials',
    }
    required_perm = box_type_permissions.get(box_type)
    if required_perm and not (request.user.is_superuser or request.user.has_perm(required_perm)):
        raise PermissionDenied

    property_obj = get_object_or_404(props, prop_id=property_id)

    # Get the active tenant for this property (there should only be one)
    active_tenant = tenant.objects.filter(
        prop=property_obj,
        tenant_current='Yes'
    ).first()

    # Get open invoices data for this property
    open_invoices_data = None
    total_invoices_amount = 0

    # Lease renewal data
    lease_renewal_data = None

    # Issues data for this specific property
    property_issues = None
    resolved_count = 0
    unresolved_count = 0
    total_issues_count = 0

    # Valuation data for this specific property
    property_valuation = None

    # Revenue data for this specific property
    property_revenues = None
    total_revenue_amount = 0

    # Budgeted expenses data for this specific property
    property_budgeted_expenses = None
    total_budgeted_expense_amount = 0

    # Actual expenses data for this specific property
    property_actual_expenses = None
    actual_expense_years = []
    selected_actual_year = None

    if active_tenant:
        # Get all unpaid invoices for this tenant
        unpaid_invoices = invoices.objects.filter(
            tenant=active_tenant
        ).exclude(
            invoice_paid='Yes'  # Exclude paid invoices
        ).order_by('invoice_date')

        # Calculate days overdue and prepare data
        open_invoices_data = []
        today = timezone.now().date()

        for invoice in unpaid_invoices:
            # Calculate due date (invoice_date + payment_terms)
            payment_terms = active_tenant.tenant_payment_terms or 0
            due_date = invoice.invoice_date + timedelta(days=payment_terms)

            # Calculate days overdue
            days_overdue = (today - due_date).days if today > due_date else 0

            # Use the actual invoice amount if available, otherwise fall back to tenant rent
            invoice_amount = getattr(invoice, 'invoice_amount', None) or active_tenant.tenant_rent

            open_invoices_data.append({
                'invoice_date': invoice.invoice_date,
                'due_date': due_date,
                'days_overdue': days_overdue,
                'overdue': days_overdue > 0,
                'amount': invoice_amount
            })

            # Add to total amount
            total_invoices_amount += invoice_amount

        # Lease renewal logic for this specific property
        if box_type == 'lease-renewals':
            lease_renewal_data = {
                'tenant': active_tenant,
                'property': property_obj,
                'needs_renewal': False,
                'renewal_date': None,
                'status': 'current',
                'message': None
            }

            if active_tenant.tenant_lease_end_date:
                # Calculate renewal contact date
                renewal_period = active_tenant.tenant_renewal_period or 30
                renewal_contact_date = active_tenant.tenant_lease_end_date - timedelta(days=renewal_period)

                # Check if renewal is needed
                if today >= renewal_contact_date:
                    lease_renewal_data['needs_renewal'] = True
                    lease_renewal_data['renewal_date'] = renewal_contact_date

                    # Check renewal status
                    if active_tenant.tenant_renewal_status == 'declined':
                        lease_renewal_data['status'] = 'declined'
                        lease_renewal_data['message'] = f"TENANT DECLINED RENEWAL - LEASE EXPIRES {active_tenant.tenant_lease_end_date}"
                    elif active_tenant.tenant_renewal_status == 'new_lease_signed':
                        lease_renewal_data['status'] = 'renewed'
                        lease_renewal_data['message'] = "NEW LEASE SIGNED"
                    else:
                        lease_renewal_data['status'] = 'pending'
                        lease_renewal_data['message'] = f"RENEWAL CONTACT REQUIRED BY {renewal_contact_date}"

    elif box_type == 'lease-renewals':
        # No active tenant - property is vacant
        lease_renewal_data = {
            'tenant': None,
            'property': property_obj,
            'status': 'vacant',
            'message': "NO CURRENT TENANT - NEED NEW TENANT"
        }

    # Issues logic - process for any box_type but only use data when box_type is 'issues'
    if box_type == 'issues':
        # Get all issues for this property, ordered by date (most recent first)
        property_issues = issues.objects.filter(
            prop=property_obj
        ).order_by('-issues_date_logged')

        # Calculate issue counts
        total_issues_count = property_issues.count()
        resolved_count = property_issues.filter(issues_status='Resolved').count()

        # Updated logic: Include both "Unresolved" AND "Issue" status as unresolved
        unresolved_count = property_issues.filter(
            issues_status__in=['Unresolved', 'Issue']
        ).count()

    # Valuation logic - process when box_type is 'valuation'
    if box_type == 'valuation':
        # Get valuation data for this property
        try:
            property_valuation = prop_values.objects.get(prop=property_obj)

            # Calculate value change in the view
            if property_valuation.prop_values_current_value and property_valuation.prop_values_purchase_price:
                difference = property_valuation.prop_values_current_value - property_valuation.prop_values_purchase_price
                if property_valuation.prop_values_purchase_price > 0:
                    percentage = (difference / property_valuation.prop_values_purchase_price) * 100
                else:
                    percentage = 0

                # Add calculated values to the valuation object
                property_valuation.value_difference = difference
                property_valuation.value_percentage = percentage
            else:
                property_valuation.value_difference = 0
                property_valuation.value_percentage = 0

        except prop_values.DoesNotExist:
            property_valuation = None

    # Revenue logic - process when box_type is 'revenues'
    if box_type == 'revenues':
        # Get all revenue data for this property
        property_revenues = property_obj.revenue_set.all().order_by('revenue_line_types__revenue_line_types_name', 'revenue_types__revenue_types_name')

        # Calculate total revenue amount
        total_revenue_amount = sum(rev.revenue_amount for rev in property_revenues)

    # Budgeted Expenses logic - process when box_type is 'budgeted-expenses'
    if box_type == 'budgeted-expenses':
        # Get all budgeted expense data for this property, sorted by expense line type
        property_budgeted_expenses = property_obj.expense_set.all().order_by('expense_line_types__expense_line_types_name', 'expense_types__expense_types_name')

        # Calculate total budgeted expense amount
        total_budgeted_expense_amount = sum(exp.expense_amount for exp in property_budgeted_expenses)

    # Actual Expenses logic - process when box_type is 'actual-expenses'
    if box_type == 'actual-expenses':
        # Get selected year from request or default to current year
        selected_actual_year = request.GET.get('year')
        current_year = timezone.now().year

        # Get all years that have actual expenses for this property (approved and paid only)
        actual_expense_years = list(
            property_obj.act_expense_set.filter(
                act_expense_approved='Yes',
                act_expense_paid='Yes'
            ).dates('act_expense_date', 'year', order='DESC').distinct()
        )
        actual_expense_years = [d.year for d in actual_expense_years]

        # Default to the latest year if no year selected
        if not selected_actual_year and actual_expense_years:
            selected_actual_year = actual_expense_years[0]
        elif not selected_actual_year:
            selected_actual_year = current_year
        else:
            selected_actual_year = int(selected_actual_year)

        # Get actual expenses for the selected year (only approved and paid)
        property_actual_expenses = property_obj.act_expense_set.filter(
            act_expense_date__year=selected_actual_year,
            act_expense_approved='Yes',
            act_expense_paid='Yes'
        ).order_by('-act_expense_date')

        # Calculate total actual expenses amount
        total_actual_expense_amount = sum(exp.act_expense_amount for exp in property_actual_expenses)

    # Asset Summary logic - process when box_type is 'property-report'
    if box_type == 'property-report':
        # Get asset summary for this property
        assets = PropertyAsset.objects.filter(property=property_obj).select_related(
            'category', 'subcategory', 'supplier'
        ).prefetch_related('maintenance_records')

        # Asset statistics
        total_assets = assets.count()
        assets_by_category = assets.values('category__name').annotate(
            count=Count('id')
        ).order_by('category__name')

        # Warranty stats
        active_warranties = sum(1 for asset in assets if asset.is_warranty_active())
        expired_warranties = total_assets - active_warranties

        # Total purchase value and maintenance costs
        total_purchase_value = assets.aggregate(
            total=Sum('purchase_price')
        )['total'] or Decimal('0.00')

        total_maintenance_cost = AssetMaintenance.objects.filter(
            asset__property=property_obj
        ).aggregate(
            total=Sum('cost')
        )['total'] or Decimal('0.00')
    else:
        # Initialize as None for other box types
        assets = None
        total_assets = 0
        assets_by_category = []
        active_warranties = 0
        expired_warranties = 0
        total_purchase_value = Decimal('0.00')
        total_maintenance_cost = Decimal('0.00')

    # Map box types to display names
    box_type_display_map = {
        'title-deed': 'Title Deed',
        'property-report': 'Property Report',
        'tenant': 'Tenant Information',
        'actual-expenses': 'Actual Expenses',
        'issues': 'Property Issues',
        'valuation': 'Property Valuation',
        'profit-loss': 'Profit & Loss',
        'revenues': 'Revenues',
        'expenses': 'Budgeted Expenses',
        'open-invoices': 'Open Invoices',
        'lease-renewals': 'Lease Renewals',
        'lease': 'Lease Details',
    }

    context = {
        'property': property_obj,
        'active_tenant': active_tenant,
        'open_invoices_data': open_invoices_data,
        'total_invoices_amount': total_invoices_amount,
        'lease_renewal_data': lease_renewal_data,
        'property_issues': property_issues,
        'resolved_count': resolved_count,
        'unresolved_count': unresolved_count,
        'total_issues_count': total_issues_count,
        'property_valuation': property_valuation,
        'property_revenues': property_revenues,
        'total_revenue_amount': total_revenue_amount,
        'property_budgeted_expenses': property_budgeted_expenses,
        'total_budgeted_expense_amount': total_budgeted_expense_amount,
        'property_actual_expenses': property_actual_expenses,
        'actual_expense_years': actual_expense_years,
        'selected_actual_year': selected_actual_year,
        'total_actual_expense_amount': locals().get('total_actual_expense_amount', 0),
        'assets': assets,
        'total_assets': total_assets,
        'assets_by_category': assets_by_category,
        'active_warranties': active_warranties,
        'expired_warranties': expired_warranties,
        'total_purchase_value': total_purchase_value,
        'total_maintenance_cost': total_maintenance_cost,
        'box_type': box_type,
        'box_type_display': box_type_display_map.get(box_type, box_type.title()),
        'today': timezone.now().date(),
    }

    return render(request, 'property_detail.html', context)


@login_required
@permission_required('auth.can_access_financials', raise_exception=True)
def dashboard_pl(request, property_id):
    """
    Dedicated view for Profit & Loss dashboard
    """
    property_obj = get_object_or_404(props, prop_id=property_id)

    # Get selected year from request
    selected_year = request.GET.get('year', 'budget')

    # Get available years for this property (from actual expenses only since revenues/expenses are budget data)
    actual_expense_years_obj = set(property_obj.act_expense_set.filter(
        act_expense_approved='Yes',
        act_expense_paid='Yes'
    ).dates('act_expense_date', 'year', order='DESC').distinct())

    # Convert to integers and sort
    available_years = sorted([d.year for d in actual_expense_years_obj], reverse=True)

    # Set display name for selected year
    if selected_year == 'budget':
        selected_year_display = 'Budget'
    else:
        try:
            selected_year = int(selected_year)
            selected_year_display = str(selected_year)
        except (ValueError, TypeError):
            selected_year = 'budget'
            selected_year_display = 'Budget'

    # Get revenue and expense line types - using correct model names
    revenue_line_types_queryset = revenue_line_types.objects.all().order_by('revenue_line_types_name')
    expense_line_types_queryset = expense_line_types.objects.all().order_by('expense_line_types_name')

    # Initialize totals dictionaries
    property_revenue_totals = {}
    property_expense_totals = {}

    # Initialize monthly totals
    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    property_revenue_total = {month: 0 for month in months}
    property_revenue_total['year'] = 0
    property_expense_total = {month: 0 for month in months}
    property_expense_total['year'] = 0
    property_actual_expense_total = {month: 0 for month in months}
    property_actual_expense_total['year'] = 0

    # Process revenues for this property (using monthly fields)
    for line_type in revenue_line_types_queryset:
        line_totals = {month: 0 for month in months}
        line_totals['total'] = 0

        # Get revenues for this line type and property
        revenues = property_obj.revenue_set.filter(
            revenue_line_types=line_type
        )

        # Sum revenues by month using the monthly fields
        for rev in revenues:
            line_totals['jan'] += rev.revenue_jan or 0
            line_totals['feb'] += rev.revenue_feb or 0
            line_totals['mar'] += rev.revenue_mar or 0
            line_totals['apr'] += rev.revenue_apr or 0
            line_totals['may'] += rev.revenue_may or 0
            line_totals['jun'] += rev.revenue_jun or 0
            line_totals['jul'] += rev.revenue_jul or 0
            line_totals['aug'] += rev.revenue_aug or 0
            line_totals['sep'] += rev.revenue_sep or 0
            line_totals['oct'] += rev.revenue_oct or 0
            line_totals['nov'] += rev.revenue_nov or 0
            line_totals['dec'] += rev.revenue_dec or 0

        # Calculate total for this line type
        line_totals['total'] = sum(line_totals[month] for month in months)

        property_revenue_totals[line_type.revenue_line_types_id] = line_totals

        # Add to property totals
        for month in months:
            property_revenue_total[month] += line_totals[month]
        property_revenue_total['year'] += line_totals['total']

    # Process budgeted expenses for this property (using monthly fields)
    for line_type in expense_line_types_queryset:
        line_totals = {month: 0 for month in months}
        line_totals['total'] = 0

        # Get expenses for this line type and property
        expenses = property_obj.expense_set.filter(
            expense_line_types=line_type
        )

        # Sum expenses by month using the monthly fields
        for exp in expenses:
            # Your expense model has monthly fields
            line_totals['jan'] += exp.expense_jan or 0
            line_totals['feb'] += exp.expense_feb or 0
            line_totals['mar'] += exp.expense_mar or 0
            line_totals['apr'] += exp.expense_apr or 0
            line_totals['may'] += exp.expense_may or 0
            line_totals['jun'] += exp.expense_jun or 0
            line_totals['jul'] += exp.expense_jul or 0
            line_totals['aug'] += exp.expense_aug or 0
            line_totals['sep'] += exp.expense_sep or 0
            line_totals['oct'] += exp.expense_oct or 0
            line_totals['nov'] += exp.expense_nov or 0
            line_totals['dec'] += exp.expense_dec or 0

        # Calculate total for this line type
        line_totals['total'] = sum(line_totals[month] for month in months)

        property_expense_totals[line_type.expense_line_types_id] = line_totals

        # Add to property totals
        for month in months:
            property_expense_total[month] += line_totals[month]
        property_expense_total['year'] += line_totals['total']

    # Process actual expenses for this property (only if not budget view)
    if selected_year != 'budget':
        actual_expenses = property_obj.act_expense_set.filter(
            act_expense_date__year=selected_year,
            act_expense_approved='Yes',
            act_expense_paid='Yes'
        ).values('act_expense_date', 'act_expense_amount')

        # Sum actual expenses by month
        for exp in actual_expenses:
            month_name = months[exp['act_expense_date'].month - 1]
            property_actual_expense_total[month_name] += exp['act_expense_amount']
            property_actual_expense_total['year'] += exp['act_expense_amount']

    context = {
        'property': property_obj,
        'available_years': available_years,
        'selected_year': selected_year,
        'selected_year_display': selected_year_display,
        'revenue_line_types': revenue_line_types_queryset,  # Updated variable name
        'expense_line_types': expense_line_types_queryset,  # Updated variable name
        'property_revenue_totals': property_revenue_totals,
        'property_expense_totals': property_expense_totals,
        'property_revenue_total': property_revenue_total,
        'property_expense_total': property_expense_total,
        'property_actual_expense_total': property_actual_expense_total,
        'today': timezone.now().date(),
    }

    return render(request, 'dashboard_pl.html', context)