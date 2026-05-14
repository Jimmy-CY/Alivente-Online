"""
Properties views — extracted from pages/views/main.py and pages/views/dashboard.py.

Covers:
  - Property CRUD: list page, map view, title-deed file management, add /
    edit pairs (form + commit), plus the supporting AJAX helper
    `get_property_tenant_data` used by the lease-generation modal.
  - Property reports: full property report, title-deed file lookup.
  - Asset management: list / add / edit / delete / detail of PropertyAsset
    records, plus AJAX helpers (subcategory cascade, on-the-fly category /
    subcategory / supplier creation).
  - Asset maintenance records: add / edit / delete of AssetMaintenance
    entries linked to a PropertyAsset.

Helpers (shared with finance.py and dashboard.py via explicit imports):
  - get_vacant_properties(cursor): raw-SQL helper used by the notifications
    dashboard. Takes a mysql cursor and returns the list of active
    properties without a current tenant.
  - calculate_year_metrics(year): aggregates occupancy + vacancy data
    across all active properties for a calendar year. Consumed by
    occupancy_trends_view in finance.py.
  - calculate_property_revenue(property_obj): sums an active property's
    annual budgeted revenue across all monthly columns. Consumed by
    financial_indicators_view in finance.py.

These two helpers relocated from dashboard.py because they're conceptually
property-scoped rather than dashboard-scoped.

Permission note: get_property_tenant_data carries auth.can_access_tenants
because the endpoint returns tenant data. It lives here per the split
plan; a future tenants module will not need to inherit it.
"""

import json
import logging
import os
from datetime import date, datetime
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count, Prefetch, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from pages.forms import PropForm
from pages.models import (
    AssetCategory,
    AssetMaintenance,
    AssetSubcategory,
    AssetSupplier,
    PropertyAsset,
    props,
    revenue,
    tenant,
    VacancyPeriod,
)


logger = logging.getLogger(__name__)


# ============================================================================
# Helpers — shared with finance.py and dashboard.py via explicit imports
# ============================================================================

def get_vacant_properties(cursor):
    """Get properties that are active and available but have no current tenant"""
    # Get properties with current tenants
    cursor.execute("""
        SELECT prop.prop_name
        FROM railway.tenant
        JOIN railway.prop ON prop.prop_id = tenant.prop_id
        WHERE tenant.tenant_current = 'Yes'
    """)
    prop_active_tenant = [row[0] for row in cursor.fetchall()]

    # Get all active properties available for rent
    cursor.execute("""
        SELECT prop.prop_name, prop.prop_country
        FROM railway.prop
        WHERE prop.prop_status = 'Active'
        AND prop.prop_available_for_rent = 'Yes'
        ORDER BY prop.prop_country ASC, prop.prop_name ASC
    """)
    active_properties_data = cursor.fetchall()

    # Find vacant properties
    vacant_properties = []
    for prop_data in active_properties_data:
        prop_name = prop_data[0]
        prop_country = prop_data[1]

        if prop_name not in prop_active_tenant:
            vacant_properties.append({
                'prop_name': prop_name,
                'prop_country': prop_country
            })

    return vacant_properties


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


# ============================================================================
# AJAX — lease generation modal data fetcher
# ============================================================================

@csrf_exempt
@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
@require_http_methods(["POST"])
def get_property_tenant_data(request):
    """
    AJAX endpoint to get property and tenant data for the modal
    """
    try:
        data = json.loads(request.body)
        property_id = data.get('property_id')
        tenant_id = data.get('tenant_id')

        response_data = {}

        # Get property data
        if property_id:
            try:
                property_obj = props.objects.get(prop_id=property_id)

                # Build full address
                address_parts = [
                    property_obj.prop_address1,
                    property_obj.prop_address2,
                    property_obj.prop_suburb,
                    property_obj.prop_city,
                    property_obj.prop_province,
                    property_obj.prop_country,
                    property_obj.prop_pcode
                ]
                full_address = ', '.join([part for part in address_parts if part and part.strip()])

                response_data['property'] = {
                    'prop_id': property_obj.prop_id,
                    'prop_name': property_obj.prop_name or '',
                    'prop_address1': property_obj.prop_address1 or '',
                    'prop_address2': property_obj.prop_address2 or '',
                    'prop_suburb': property_obj.prop_suburb or '',
                    'prop_city': property_obj.prop_city or '',
                    'prop_province': property_obj.prop_province or '',
                    'prop_country': property_obj.prop_country or '',
                    'prop_pcode': property_obj.prop_pcode or '',
                    'prop_floor_area': property_obj.prop_floor_area or '',
                    'prop_year_built': property_obj.prop_year_built or '',
                    'full_address': full_address,
                    'prop_electricity': property_obj.prop_electricity or '',
                    'prop_water': property_obj.prop_water or '',
                    'prop_refuse': property_obj.prop_refuse or '',
                    'prop_sewerage': property_obj.prop_sewerage or '',
                    'prop_insurance': property_obj.prop_insurance or '',
                }
            except props.DoesNotExist:
                response_data['property_error'] = 'Property not found'
                logger.warning(f"Property with ID {property_id} not found")

        # Get tenant data
        if tenant_id:
            try:
                tenant_obj = tenant.objects.get(tenant_id=tenant_id)
                response_data['tenant'] = {
                    'tenant_id': tenant_obj.tenant_id,
                    'tenant_name': tenant_obj.tenant_name or '',
                    'tenant_type': tenant_obj.tenant_type or '',
                    'tenant_contact_person': tenant_obj.tenant_contact_person or '',
                    'tenant_contact_number': tenant_obj.tenant_contact_number or '',
                    'tenant_email': tenant_obj.tenant_email or '',
                    'tenant_lease_start_date': tenant_obj.tenant_lease_start_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_start_date else '',
                    'tenant_lease_end_date': tenant_obj.tenant_lease_end_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_end_date else '',
                    'tenant_rent': float(tenant_obj.tenant_rent) if tenant_obj.tenant_rent else 0,
                    'tenant_deposit': float(tenant_obj.tenant_deposit) if tenant_obj.tenant_deposit else 0,
                    'tenant_levies': float(tenant_obj.tenant_levies) if tenant_obj.tenant_levies else 0,
                    'tenant_payment_terms': tenant_obj.tenant_payment_terms or '',
                    'tenant_rental_type': tenant_obj.tenant_rental_type or '',
                    'tenant_renewal': tenant_obj.tenant_renewal or '',
                    'tenant_renewal_period': tenant_obj.tenant_renewal_period or '',
                }
            except tenant.DoesNotExist:
                response_data['tenant_error'] = 'Tenant not found'
                logger.warning(f"Tenant with ID {tenant_id} not found")
        elif tenant_id is None:
            # Handle case where no tenant_id is provided (new tenant case)
            response_data['tenant'] = None

        return JsonResponse(response_data)

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in get_property_tenant_data: {str(e)}")
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error in get_property_tenant_data: {str(e)}")
        return JsonResponse({'error': 'Server error occurred'}, status=500)


# ============================================================================
# Properties CRUD — list / map / title-deed file mgmt / add / edit pairs
# ============================================================================

@login_required
@permission_required('auth.can_access_properties', raise_exception=True)
def properties_page(request):
    # Get filter values from the new form
    search_query = request.POST.get('search', '').strip()
    selected_country = request.POST.get('country', '')
    selected_status = request.POST.get('status', '')

    # Start with all properties
    results = props.objects.all()

    # Apply cumulative filters (all work together)
    if search_query:
        results = results.filter(prop_name__icontains=search_query)

    if selected_country:
        results = results.filter(prop_country=selected_country)

    if selected_status:
        results = results.filter(prop_status=selected_status)

    # Always order the results
    results = results.order_by('prop_country', 'prop_name')

    # Pass filter values back to template for form persistence
    context = {
        'props': results,
        'search_query': search_query,
        'selected_country': selected_country,
        'selected_status': selected_status,
    }

    return render(request, "properties.html", context)


@login_required
@permission_required('auth.can_access_properties', raise_exception=True)
def properties_map_view(request):
    """Display all properties on an interactive map"""

    # Get all properties from the database
    properties = props.objects.all()

    # Convert properties to JSON format for JavaScript
    properties_data = []
    for prop in properties:
        # Handle Decimal fields properly
        latitude = None
        longitude = None

        if prop.prop_latitude is not None:
            latitude = float(prop.prop_latitude)
        if prop.prop_longitude is not None:
            longitude = float(prop.prop_longitude)

        property_dict = {
            'id': prop.prop_id,
            'name': prop.prop_name,
            'address1': prop.prop_address1,
            'address2': prop.prop_address2,
            'suburb': prop.prop_suburb,
            'city': prop.prop_city,
            'province': prop.prop_province,
            'country': prop.prop_country,
            'pcode': prop.prop_pcode,
            'latitude': latitude,
            'longitude': longitude,
            'floor_area': prop.prop_floor_area,
            'year_built': prop.prop_year_built,
            'status': prop.prop_status,
            'available_for_rent': prop.prop_available_for_rent,
        }
        properties_data.append(property_dict)

    context = {
        'properties_json': json.dumps(properties_data),
        'properties_count': len(properties_data)
    }

    return render(request, 'map_view.html', context)


@login_required
@permission_required('auth.can_access_properties', raise_exception=True)
def properties_title_deed(request):
    properties = props.objects.all().order_by('prop_country','prop_name')

    if request.method == 'POST':
        action = request.POST.get('action')
        prop_id = request.POST.get('property_id')  # Changed from 'prop_id' to match form

        if not prop_id:
            messages.error(request, 'No property selected')
            return redirect('properties_title_deed')

        try:
            property_obj = get_object_or_404(props, pk=prop_id)

            if action == 'delete':
                if property_obj.prop_title_deed:
                    # Delete the file from storage
                    property_obj.prop_title_deed.delete()
                    property_obj.prop_title_deed_status = "No Title Deed"
                    property_obj.save()
                    messages.success(request, f'Title deed deleted for {property_obj.prop_name}!')
                else:
                    messages.warning(request, 'No title deed found to delete.')


            elif action == 'upload':
                if 'title_deed' in request.FILES:
                    uploaded_file = request.FILES['title_deed']

                    # Validate file size (10MB limit)
                    if uploaded_file.size > 10 * 1024 * 1024:
                        messages.error(request, 'File size exceeds 10MB limit')
                        return redirect('properties_title_deed')

                    # Validate file type
                    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
                    file_extension = os.path.splitext(uploaded_file.name)[1].lower()

                    if file_extension not in allowed_extensions:
                        messages.error(request, 'Invalid file type. Please upload PDF or image files only.')
                        return redirect('properties_title_deed')

                    try:
                        # Ensure directory exists
                        upload_path = os.path.join(settings.MEDIA_ROOT, 'properties', 'title_deeds')
                        os.makedirs(upload_path, exist_ok=True)

                        # Delete old file if exists
                        if property_obj.prop_title_deed:
                            property_obj.prop_title_deed.delete(save=False)

                        # Save new file
                        property_obj.prop_title_deed = uploaded_file
                        property_obj.prop_title_deed_status = "Title Deed Uploaded"
                        property_obj.save()

                        messages.success(request, f'Title deed uploaded successfully for {property_obj.prop_name}!')
                    except Exception as e:
                        messages.error(request, f'Error saving file: {str(e)}')
                else:
                    messages.error(request, 'Please select a file to upload')

        except Exception as e:
            messages.error(request, f'Error processing request: {str(e)}')

    context = {
        'properties': properties,
    }
    return render(request, 'properties_title_deed.html', context)


@login_required
@permission_required('auth.can_edit_properties', raise_exception=True)
def properties_add(request):
    results = props.objects.all().order_by('prop_country','prop_name')
    existing_names = list(props.objects.values_list('prop_name', flat=True))
    return render(request, "properties_add.html", {"props":results, "existing_names": existing_names})


@login_required
@permission_required('auth.can_edit_properties', raise_exception=True)
def properties_commit(request):
    if request.method == "POST":
        form = PropForm(request.POST or None)
        if form.is_valid():
            form.save()
    results = props.objects.all().order_by('prop_country','prop_name')
    messages.success(request, "Property Added Successfully")
    return render (request, "properties.html", {"props":results})


@login_required
@permission_required('auth.can_edit_properties', raise_exception=True)
def properties_edit(request, prop_id):
    # Get the current property being edited
    current_property = get_object_or_404(props, pk=prop_id)

    # Get all other property names (excluding the current one)
    existing_names = props.objects.exclude(prop_id=prop_id).values_list('prop_name', flat=True)

    return render(request, "properties_edit.html", {
        "props": [current_property],  # Maintain your existing structure
        "existing_names": list(existing_names)  # Add this for client-side validation
    })


@login_required
@permission_required('auth.can_edit_properties', raise_exception=True)
def properties_edit_commit(request, prop_id):
    prop = get_object_or_404(props, pk=prop_id)
    existing_names = props.objects.exclude(prop_id=prop_id).values_list('prop_name', flat=True)

    if request.method == "POST":
        form = PropForm(request.POST, instance=prop)

        if form.is_valid():
            new_name = form.cleaned_data.get('prop_name')
            current_name = prop.prop_name

            if new_name.lower() != current_name.lower():
                if props.objects.exclude(prop_id=prop_id).filter(prop_name__iexact=new_name).exists():
                    messages.error(request, "A property with this name already exists.")
                    return render(request, "properties_edit.html", {
                        'props': [prop],
                        'existing_names': list(existing_names)
                    })

            form.save()
            messages.success(request, "Property Edited Successfully")
            results = props.objects.all().order_by('prop_country','prop_name')
            return redirect('properties')  # Better to redirect after POST

        # Form is invalid
        messages.error(request, "Please correct the errors below.")
        return render(request, "properties_edit.html", {
            'props': [prop],
            'existing_names': list(existing_names)
        })

    # If not POST, redirect to properties page
    return redirect('properties')


# ============================================================================
# Property reports — full property report + title-deed file lookup
# ============================================================================

@login_required
@permission_required('auth.can_access_properties', raise_exception=True)
def property_report(request, prop_id):
    today = date.today()
    property = get_object_or_404(props.objects.only(
        'prop_id', 'prop_name', 'prop_address1', 'prop_address2', 'prop_suburb',
        'prop_city', 'prop_province', 'prop_country', 'prop_pcode',
        'prop_floor_area', 'prop_year_built', 'prop_status',
        'prop_available_for_rent', 'prop_title_deed',
        'prop_title_deed_status', 'prop_electricity', 'prop_water',
        'prop_refuse', 'prop_property_tax', 'prop_sewerage', 'prop_insurance'
    ), pk=prop_id)

    # Get asset summary for this property
    assets = PropertyAsset.objects.filter(property=property).select_related(
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
        asset__property=property
    ).aggregate(
        total=Sum('cost')
    )['total'] or Decimal('0.00')

    context = {
        'today': today,
        'property': property,
        'assets': assets,
        'total_assets': total_assets,
        'assets_by_category': assets_by_category,
        'active_warranties': active_warranties,
        'expired_warranties': expired_warranties,
        'total_purchase_value': total_purchase_value,
        'total_maintenance_cost': total_maintenance_cost,
    }
    return render(request, 'property_report.html', context)


@login_required
@permission_required('auth.can_access_properties', raise_exception=True)
def title_deed_report(request, prop_id):
    property = get_object_or_404(props, pk=prop_id)

    if not property.prop_title_deed:
        return JsonResponse({'error': 'No title deed available for this property'}, status=404)

    # Return JSON with the file URL and type
    return JsonResponse({
        'file_url': property.prop_title_deed.url,
        'file_name': property.prop_title_deed.name.split('/')[-1],
        'file_type': property.prop_title_deed.name.split('.')[-1].lower()
    })


# ============================================================================
# Asset management — list / add / edit / delete / detail
# ============================================================================

@login_required
@permission_required('auth.can_access_properties', raise_exception=True)
def property_assets(request, prop_id):
    """
    Display all assets for a specific property.
    Grouped by category (default) or by location/room via ?group_by= GET param.
    """
    property_obj = get_object_or_404(props, prop_id=prop_id)

    # Determine grouping mode from GET param
    group_by = request.GET.get('group_by', 'category')
    if group_by not in ('category', 'room'):
        group_by = 'category'

    # Get all assets for this property, prefetch related data
    assets = PropertyAsset.objects.filter(
        property=property_obj
    ).select_related(
        'category', 'subcategory', 'supplier'
    ).prefetch_related(
        'maintenance_records'
    )

    # Order based on grouping mode (drives dict insertion order)
    if group_by == 'room':
        assets = assets.order_by('location_room', 'category__name', 'subcategory__name', 'name')
    else:
        assets = assets.order_by('category__name', 'subcategory__name', 'name')

    # Build the grouped dict
    grouped_assets = {}
    for asset in assets:
        if group_by == 'room':
            key = asset.location_room or '(Unspecified)'
        else:
            key = asset.category.name
        grouped_assets.setdefault(key, []).append(asset)

    # Get all categories for the add form
    categories = AssetCategory.objects.all().order_by('name')
    suppliers = AssetSupplier.objects.all().order_by('name')

    context = {
        'property': property_obj,
        'grouped_assets': grouped_assets,
        'group_by': group_by,
        'total_assets': assets.count(),
        'categories': categories,
        'suppliers': suppliers,
    }

    return render(request, 'property_assets.html', context)


@login_required
@permission_required('auth.can_edit_properties', raise_exception=True)
@require_POST
def add_asset(request, prop_id):
    """Add a new asset to a property"""
    property_obj = get_object_or_404(props, prop_id=prop_id)

    try:
        category_id = request.POST.get('category')
        subcategory_id = request.POST.get('subcategory')
        supplier_id = request.POST.get('supplier')

        category = get_object_or_404(AssetCategory, pk=category_id)
        subcategory = get_object_or_404(AssetSubcategory, pk=subcategory_id)

        # Supplier is optional
        supplier = get_object_or_404(AssetSupplier, pk=supplier_id) if supplier_id else None

        # Purchase date is optional
        purchase_date_str = request.POST.get('purchase_date')
        purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date() if purchase_date_str else None

        # Validate: purchase date required if warranty duration entered
        warranty_duration = request.POST.get('warranty_duration_months')
        if warranty_duration and int(warranty_duration) > 0 and not purchase_date:
            messages.error(request, 'Purchase Date is required when Warranty Duration is entered.')
            return redirect('property_assets', prop_id=prop_id)

        asset = PropertyAsset(
            property=property_obj,
            category=category,
            subcategory=subcategory,
            supplier=supplier,
            name=request.POST.get('name'),
            location_room=request.POST.get('location_room'),
            purchase_date=purchase_date,
            brand_manufacturer=request.POST.get('brand_manufacturer', ''),
            notes=request.POST.get('notes', ''),
            created_by=request.user
        )

        if request.POST.get('purchase_price'):
            asset.purchase_price = Decimal(request.POST.get('purchase_price'))

        if request.FILES.get('purchase_invoice'):
            asset.purchase_invoice = request.FILES['purchase_invoice']

        if warranty_duration:
            asset.warranty_duration_months = int(warranty_duration)

        warranty_expiry = request.POST.get('warranty_expiry_date')
        if warranty_expiry:
            asset.warranty_expiry_date = datetime.strptime(warranty_expiry, '%Y-%m-%d').date()

        asset.save()
        messages.success(request, f'Asset "{asset.name}" added successfully!')

    except Exception as e:
        messages.error(request, f'Error adding asset: {str(e)}')

    return redirect('property_assets', prop_id=prop_id)


@login_required
@permission_required('auth.can_edit_properties', raise_exception=True)
def edit_asset(request, asset_id):
    """Edit an existing asset"""
    asset = get_object_or_404(PropertyAsset, pk=asset_id)

    if request.method == 'POST':
        try:
            # Supplier is optional
            supplier_id = request.POST.get('supplier')
            asset.supplier = get_object_or_404(AssetSupplier, pk=supplier_id) if supplier_id else None

            # Purchase date is optional
            purchase_date_str = request.POST.get('purchase_date')
            asset.purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date() if purchase_date_str else None

            # Validate: purchase date required if warranty duration entered
            warranty_duration = request.POST.get('warranty_duration_months')
            if warranty_duration and int(warranty_duration) > 0 and not asset.purchase_date:
                messages.error(request, 'Purchase Date is required when Warranty Duration is entered.')
                return redirect('edit_asset', asset_id=asset_id)

            asset.category = get_object_or_404(AssetCategory, pk=request.POST.get('category'))
            asset.subcategory = get_object_or_404(AssetSubcategory, pk=request.POST.get('subcategory'))
            asset.name = request.POST.get('name')
            asset.location_room = request.POST.get('location_room')
            asset.brand_manufacturer = request.POST.get('brand_manufacturer', '')
            asset.notes = request.POST.get('notes', '')

            asset.purchase_price = Decimal(request.POST.get('purchase_price')) if request.POST.get('purchase_price') else None

            if request.FILES.get('purchase_invoice'):
                asset.purchase_invoice = request.FILES['purchase_invoice']

            asset.warranty_duration_months = int(warranty_duration) if warranty_duration else None

            warranty_expiry = request.POST.get('warranty_expiry_date')
            asset.warranty_expiry_date = warranty_expiry if warranty_expiry else None

            asset.save()
            messages.success(request, f'Asset "{asset.name}" updated successfully!')
            return redirect('asset_detail', asset_id=asset.id)

        except Exception as e:
            messages.error(request, f'Error updating asset: {str(e)}')

    categories = AssetCategory.objects.all().order_by('name')
    subcategories = AssetSubcategory.objects.filter(category=asset.category).order_by('name')
    suppliers = AssetSupplier.objects.all().order_by('name')

    context = {
        'asset': asset,
        'categories': categories,
        'subcategories': subcategories,
        'suppliers': suppliers,
    }

    return render(request, 'edit_asset.html', context)


@login_required
@permission_required('auth.can_edit_properties', raise_exception=True)
@require_POST
def delete_asset(request, asset_id):
    """Delete an asset"""
    asset = get_object_or_404(PropertyAsset, pk=asset_id)
    property_id = asset.property.prop_id
    asset_name = asset.name

    try:
        asset.delete()
        messages.success(request, f'Asset "{asset_name}" deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting asset: {str(e)}')

    return redirect('property_assets', prop_id=property_id)


@login_required
@permission_required('auth.can_access_properties', raise_exception=True)
def asset_detail(request, asset_id):
    """
    Display detailed information about an asset
    Including maintenance history
    """
    asset = get_object_or_404(
        PropertyAsset.objects.select_related(
            'property', 'category', 'subcategory', 'supplier'
        ).prefetch_related('maintenance_records'),
        pk=asset_id
    )

    # Get maintenance records
    maintenance_records = asset.maintenance_records.all().order_by('-date')

    # Calculate total maintenance cost
    total_maintenance_cost = asset.get_total_maintenance_cost()

    context = {
        'asset': asset,
        'maintenance_records': maintenance_records,
        'total_maintenance_cost': total_maintenance_cost,
    }

    return render(request, 'asset_detail.html', context)


# ============================================================================
# Asset AJAX helpers — subcategory cascade + on-the-fly creation
# ============================================================================

@login_required
@permission_required('auth.can_access_properties', raise_exception=True)
def get_subcategories(request, category_id):
    """
    AJAX endpoint to get subcategories for a category
    Returns JSON
    """
    subcategories = AssetSubcategory.objects.filter(
        category_id=category_id
    ).order_by('name').values('id', 'name')

    return JsonResponse({
        'subcategories': list(subcategories)
    })


@login_required
@permission_required('auth.can_edit_properties', raise_exception=True)
@require_POST
def add_category_ajax(request):
    """AJAX endpoint to add a new category"""
    try:
        category_name = request.POST.get('name')

        if not category_name:
            return JsonResponse({'success': False, 'error': 'Category name is required'})

        # Check if category already exists
        if AssetCategory.objects.filter(name=category_name).exists():
            return JsonResponse({'success': False, 'error': 'Category already exists'})

        category = AssetCategory.objects.create(
            name=category_name,
            created_by=request.user
        )

        return JsonResponse({
            'success': True,
            'category': {
                'id': category.id,
                'name': category.name
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@permission_required('auth.can_edit_properties', raise_exception=True)
@require_POST
def add_subcategory_ajax(request):
    """AJAX endpoint to add a new subcategory"""
    try:
        category_id = request.POST.get('category_id')
        subcategory_name = request.POST.get('name')

        if not category_id or not subcategory_name:
            return JsonResponse({'success': False, 'error': 'Category and subcategory name are required'})

        category = get_object_or_404(AssetCategory, pk=category_id)

        # Check if subcategory already exists for this category
        if AssetSubcategory.objects.filter(category=category, name=subcategory_name).exists():
            return JsonResponse({'success': False, 'error': 'Subcategory already exists for this category'})

        subcategory = AssetSubcategory.objects.create(
            category=category,
            name=subcategory_name,
            created_by=request.user
        )

        return JsonResponse({
            'success': True,
            'subcategory': {
                'id': subcategory.id,
                'name': subcategory.name
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@permission_required('auth.can_edit_properties', raise_exception=True)
@require_POST
def add_supplier_ajax(request):
    """AJAX endpoint to add a new supplier"""
    try:
        supplier_name = request.POST.get('name')

        if not supplier_name:
            return JsonResponse({'success': False, 'error': 'Supplier name is required'})

        # Check if supplier already exists
        if AssetSupplier.objects.filter(name=supplier_name).exists():
            return JsonResponse({'success': False, 'error': 'Supplier already exists'})

        supplier = AssetSupplier.objects.create(
            name=supplier_name,
            created_by=request.user
        )

        return JsonResponse({
            'success': True,
            'supplier': {
                'id': supplier.id,
                'name': supplier.name
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ============================================================================
# Maintenance records — add / edit / delete
# ============================================================================

@login_required
@permission_required('auth.can_edit_properties', raise_exception=True)
@require_POST
def add_maintenance(request, asset_id):
    """Add a maintenance record for an asset"""
    asset = get_object_or_404(PropertyAsset, pk=asset_id)

    try:
        maintenance = AssetMaintenance(
            asset=asset,
            date=request.POST.get('date'),
            maintenance_type=request.POST.get('maintenance_type'),
            description=request.POST.get('description'),
            service_provider=request.POST.get('service_provider', ''),
            created_by=request.user
        )

        if request.POST.get('cost'):
            maintenance.cost = Decimal(request.POST.get('cost'))

        if request.FILES.get('invoice'):
            maintenance.invoice = request.FILES['invoice']

        maintenance.save()
        messages.success(request, 'Maintenance record added successfully!')

    except Exception as e:
        messages.error(request, f'Error adding maintenance record: {str(e)}')

    return redirect('asset_detail', asset_id=asset_id)


@login_required
@permission_required('auth.can_edit_properties', raise_exception=True)
@require_POST
def delete_maintenance(request, maintenance_id):
    """Delete a maintenance record"""
    maintenance = get_object_or_404(AssetMaintenance, pk=maintenance_id)
    asset_id = maintenance.asset.id

    try:
        maintenance.delete()
        messages.success(request, 'Maintenance record deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting maintenance record: {str(e)}')

    return redirect('asset_detail', asset_id=asset_id)


@login_required
@permission_required('auth.can_edit_properties', raise_exception=True)
def edit_maintenance(request, maintenance_id):
    """Edit a maintenance record"""
    maintenance = get_object_or_404(AssetMaintenance, pk=maintenance_id)
    asset_id = maintenance.asset.id

    if request.method == 'POST':
        try:
            maintenance.date = request.POST.get('date')
            maintenance.maintenance_type = request.POST.get('maintenance_type')
            maintenance.description = request.POST.get('description')
            maintenance.service_provider = request.POST.get('service_provider', '')
            maintenance.cost = Decimal(request.POST.get('cost')) if request.POST.get('cost') else None

            if request.FILES.get('invoice'):
                maintenance.invoice = request.FILES['invoice']

            maintenance.save()
            messages.success(request, 'Maintenance record updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating maintenance record: {str(e)}')

    return redirect('asset_detail', asset_id=asset_id)