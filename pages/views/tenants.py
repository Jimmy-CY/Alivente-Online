"""
Tenants views.

Extracted from the legacy pages/views/main.py during the modular views
split. Tenant deletion relies on the post_save / post_delete handlers
in manage_vacancy_periods.py for vacancy-period cleanup.

Functions
---------
- tenant_page            : List view with property / tenant / status
                           filters.
- tenant_add             : Add form.
- tenant_edit            : Edit form.
- tenant_commit          : Add save (TenantForm).
- tenant_edit_commit     : Edit save (TenantForm).
- tenant_lease_agreement : Upload / delete the lease-agreement document.
- lease_timeline_view    : Per-property tenant lease timeline UI.
- tenant_payment_days_view : How many days each tenant actually
                           takes to pay, against agreed terms.
- duplicate_tenant_view  : Duplicate a tenant for renewal / new lease.
- delete_tenant_view     : Delete a tenant (signals handle vacancy
                           cleanup).

Physical invoice
----------------
The two physical-invoice flags live on the tenant model, but the
PhysicalInvoiceProfile (customer id / billing block / water cycle) is a
separate OneToOne, so TenantForm cannot carry it. _apply_physical_invoice_fields
upserts both after the form has saved, and duplicate_tenant_view copies them
across to a renewal.

Auth tiers
----------
read tier -> auth.can_access_tenants  (tenant_page,
                                       tenant_lease_agreement,
                                       lease_timeline_view,
                                       tenant_payment_days_view)
edit tier -> auth.can_edit_tenants    (add, edit, commit, edit_commit,
                                       duplicate, delete)
"""

import os
from datetime import date, datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import TenantForm
from ..models import PhysicalInvoiceProfile, invoices, props, tenant


def _apply_physical_invoice_fields(request, tenant_obj):
    """Persist the two physical-invoice flags and the PhysicalInvoiceProfile
    from a submitted tenant form.

    The flags are model fields on the tenant; the profile is a separate
    OneToOne and so is read straight from request.POST here. A profile row is
    only created when physical invoicing is switched on (or one already
    exists, so that turning it back off still records the change).
    """
    tenant_obj.tenant_physical_invoice_required = (
        'tenant_physical_invoice_required' in request.POST
    )
    tenant_obj.tenant_bill_levies = 'tenant_bill_levies' in request.POST
    tenant_obj.save(update_fields=[
        'tenant_physical_invoice_required', 'tenant_bill_levies',
    ])

    required = tenant_obj.tenant_physical_invoice_required
    if not required and not PhysicalInvoiceProfile.objects.filter(tenant=tenant_obj).exists():
        return  # nothing to store, and no existing profile to update

    # Water cycle interval (months) — default 2 if blank/invalid.
    raw_interval = request.POST.get('water_cycle_interval_months') or 2
    try:
        interval = int(raw_interval)
    except (TypeError, ValueError):
        interval = 2
    if interval < 1:
        interval = 1

    # Water cycle anchor — optional ISO date from the date input.
    raw_anchor = request.POST.get('water_cycle_anchor')
    anchor = None
    if raw_anchor:
        try:
            anchor = datetime.strptime(raw_anchor, '%Y-%m-%d').date()
        except ValueError:
            anchor = None

    profile, _ = PhysicalInvoiceProfile.objects.get_or_create(tenant=tenant_obj)
    profile.customer_id_label = (request.POST.get('customer_id_label') or '').strip()
    profile.billing_name = (request.POST.get('billing_name') or '').strip()
    profile.billing_address = (request.POST.get('billing_address') or '').strip()
    profile.billing_tel = (request.POST.get('billing_tel') or '').strip()
    profile.client_email_body = (request.POST.get('client_email_body') or '').strip()
    profile.water_enabled = 'water_enabled' in request.POST
    profile.water_cycle_anchor = anchor
    profile.water_cycle_interval_months = interval
    profile.save()


@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def tenant_page(request):
    # Get filter values from the new form
    selected_property = request.POST.get('propname', '').strip()
    selected_tenant = request.POST.get('tenantname', '').strip()
    selected_status = request.POST.get('act', '').strip()

    # Start with all properties and tenants
    all_properties = props.objects.all().order_by('prop_country', 'prop_name')
    all_tenants = tenant.objects.all().order_by('tenant_name')

    # Filter tenants based on the selected criteria
    filtered_tenants = all_tenants

    # Apply tenant name filter
    if selected_tenant:
        filtered_tenants = filtered_tenants.filter(tenant_name=selected_tenant)

    # Apply status filter
    if selected_status:
        filtered_tenants = filtered_tenants.filter(tenant_current=selected_status)

    # Filter properties based on the selected property
    filtered_properties = all_properties
    if selected_property:
        filtered_properties = filtered_properties.filter(prop_name=selected_property)

    # Build the table rows: secondary sort by lease end date (newest first,
    # oldest last) WITHIN each property group, and attach a colour class for
    # the new Lease End Date column.
    #   - Inactive tenant       -> red  (regardless of the date)
    #   - Active, end < today   -> red  (lease has passed)
    #   - Active, end >= today  -> green (today still counts as valid)
    #   - No end date           -> no colour
    # The property grouping itself is driven by the template's outer props
    # loop, so this ordering only sequences tenants inside each group.
    today = datetime.now().date()
    tenant_rows = list(
        filtered_tenants.order_by('-tenant_lease_end_date', 'tenant_name')
    )
    for _t in tenant_rows:
        _end = _t.tenant_lease_end_date
        if _t.tenant_current != 'Yes':
            _t.lease_class = 'lease-end-red'
        elif _end and _end < today:
            _t.lease_class = 'lease-end-red'
        elif _end:
            _t.lease_class = 'lease-end-green'
        else:
            _t.lease_class = ''

    # Pass filter values back to template for form persistence
    context = {
        'tenant': filtered_tenants,
        'tenant_rows': tenant_rows,
        'props': filtered_properties,
        'selected_property': selected_property,
        'selected_tenant': selected_tenant,
        'selected_status': selected_status,
    }

    return render(request, "tenant.html", context)


@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
def tenant_add(request):
    results = props.objects.all().order_by('prop_country', 'prop_name')
    tresults = tenant.objects.all().order_by('tenant_name')
    return render(request, "tenant_add.html", {"props": results, "tenant": tresults})


@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
def tenant_edit(request, tenant_id):
    tresults = tenant.objects.filter(pk=tenant_id)
    results = props.objects.all().order_by('prop_country', 'prop_name')
    return render(request, "tenant_edit.html", {"props": results, "tenant": tresults})


@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
def tenant_commit(request):
    props_list = props.objects.all().order_by('prop_country', 'prop_name')

    if request.method == "POST":
        form = TenantForm(request.POST)

        if form.is_valid():
            try:
                new_tenant = form.save()
                _apply_physical_invoice_fields(request, new_tenant)
                messages.success(request, f"Tenant {new_tenant.tenant_name} added successfully")
                return redirect('tenant')
            except ValidationError as e:
                # Clean up the error message
                clean_error = str(e).replace('__all__: ', '')
                messages.error(request, clean_error)
                return render(request, "tenant_add.html", {
                    'form': form,
                    'props': props_list,
                    'form_data': request.POST
                })
            except Exception as e:
                messages.error(request, f"Error saving tenant: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    clean_error = str(error).replace('__all__: ', '')
                    messages.error(request, clean_error)

    return render(request, "tenant_add.html", {
        'form': TenantForm(request.POST if request.method == "POST" else None),
        'props': props_list,
        'form_data': request.POST if request.method == "POST" else None
    })


@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
def tenant_edit_commit(request, tenant_id):
    ten = tenant.objects.get(pk=tenant_id)
    if request.method == "POST":
        form = TenantForm(request.POST, instance=ten)
        if form.is_valid():
            try:
                ten = form.save()
                _apply_physical_invoice_fields(request, ten)
                messages.success(request, "Tenant edited successfully")
                return redirect('tenant')
            except ValidationError as e:
                messages.error(request, str(e).replace('__all__: ', ''))
                return redirect('tenant_edit', tenant_id=tenant_id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, str(error).replace('__all__: ', ''))
            return redirect('tenant_edit', tenant_id=tenant_id)
    return redirect('tenant')


@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def tenant_lease_agreement(request):
    tenants = tenant.objects.all().order_by('prop__prop_country', 'prop__prop_name', 'tenant_name')

    if request.method == 'POST':
        action = request.POST.get('action')
        tenant_id = request.POST.get('tenant_id')

        if not tenant_id:
            messages.error(request, 'No tenant selected')
            return redirect('tenant_lease_agreement')

        try:
            tenant_obj = get_object_or_404(tenant, pk=tenant_id)

            if action == 'delete':
                if tenant_obj.tenant_lease_agreement:
                    # Delete the file from storage
                    tenant_obj.tenant_lease_agreement.delete()
                    tenant_obj.tenant_lease_agreement_status = "No Lease Agreement"
                    tenant_obj.save()
                    messages.success(request, f'Lease agreement deleted for {tenant_obj.tenant_name}!')
                else:
                    messages.warning(request, 'No lease agreement found to delete.')

            elif action == 'upload':
                if 'lease_agreement' in request.FILES:
                    uploaded_file = request.FILES['lease_agreement']

                    # Validate file size (10MB limit)
                    if uploaded_file.size > 10 * 1024 * 1024:
                        messages.error(request, 'File size exceeds 10MB limit')
                        return redirect('tenant_lease_agreement')

                    # Validate file type
                    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
                    file_extension = os.path.splitext(uploaded_file.name)[1].lower()

                    if file_extension not in allowed_extensions:
                        messages.error(request, 'Invalid file type. Please upload PDF or image files only.')
                        return redirect('tenant_lease_agreement')

                    try:
                        # Ensure directory exists
                        upload_path = os.path.join(settings.MEDIA_ROOT, 'tenants', 'lease_agreements')
                        os.makedirs(upload_path, exist_ok=True)

                        # Delete old file if exists
                        if tenant_obj.tenant_lease_agreement:
                            tenant_obj.tenant_lease_agreement.delete(save=False)

                        # Save new file
                        tenant_obj.tenant_lease_agreement = uploaded_file
                        tenant_obj.tenant_lease_agreement_status = "Lease Agreement Uploaded"
                        tenant_obj.save()

                        messages.success(request, f'Lease agreement uploaded successfully for {tenant_obj.tenant_name}!')
                    except Exception as e:
                        messages.error(request, f'Error saving file: {str(e)}')
                else:
                    messages.error(request, 'Please select a file to upload')

        except Exception as e:
            messages.error(request, f'Error processing request: {str(e)}')

    context = {
        'tenants': tenants,
    }
    return render(request, 'tenant_lease_agreement.html', context)


@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def lease_timeline_view(request):
    # Get all properties with their tenants
    properties = props.objects.filter(prop_status='Active').prefetch_related(
        'tenant_set'
    ).order_by('prop_country', 'prop_name')

    # Build timeline data
    timeline_data = []

    for prop in properties:
        tenants = prop.tenant_set.all().order_by('tenant_lease_start_date')

        for t in tenants:
            if t.tenant_lease_start_date:
                timeline_data.append({
                    'property_id': prop.prop_id,
                    'property_name': prop.prop_name,
                    'tenant_id': t.tenant_id,
                    'tenant_name': t.tenant_name,
                    'start_date': t.tenant_lease_start_date.isoformat(),
                    'end_date': t.tenant_lease_end_date.isoformat() if t.tenant_lease_end_date else None,
                    'is_active': t.tenant_current == 'Yes',
                    'rent': float(t.tenant_rent) if t.tenant_rent else 0,
                })

    context = {
        'properties': properties,
        'timeline_data': timeline_data,
    }

    return render(request, 'lease_timeline.html', context)


@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
def duplicate_tenant_view(request, tenant_id):
    """
    Duplicate an existing tenant to create a renewal or new lease.
    Copies all tenant details except ID and lease dates.
    """
    try:
        # Get the original tenant
        original_tenant = tenant.objects.get(pk=tenant_id)

        # Create a new tenant instance with copied data
        new_tenant = tenant()

        # Copy all fields EXCEPT primary key and dates
        new_tenant.prop = original_tenant.prop
        new_tenant.tenant_type = original_tenant.tenant_type
        new_tenant.tenant_name = original_tenant.tenant_name
        new_tenant.tenant_contact_person = original_tenant.tenant_contact_person
        new_tenant.tenant_contact_number = original_tenant.tenant_contact_number
        new_tenant.tenant_email = original_tenant.tenant_email
        new_tenant.tenant_deposit = original_tenant.tenant_deposit
        new_tenant.tenant_rental_type = original_tenant.tenant_rental_type
        new_tenant.tenant_renewal = original_tenant.tenant_renewal
        new_tenant.tenant_renewal_period = original_tenant.tenant_renewal_period
        new_tenant.tenant_rent = original_tenant.tenant_rent
        new_tenant.tenant_levies = original_tenant.tenant_levies
        new_tenant.tenant_payment_terms = original_tenant.tenant_payment_terms

        # Carry the physical-invoice flags across to the renewal
        new_tenant.tenant_physical_invoice_required = original_tenant.tenant_physical_invoice_required
        new_tenant.tenant_bill_levies = original_tenant.tenant_bill_levies

        # Set lease dates to None - user will fill these in
        new_tenant.tenant_lease_start_date = None
        new_tenant.tenant_lease_end_date = None

        # Set as inactive initially - user will activate after setting dates
        new_tenant.tenant_current = 'No'

        # Reset renewal status
        new_tenant.tenant_renewal_status = 'pending'

        # Don't copy lease agreement - user may need to upload new one
        new_tenant.tenant_lease_agreement = None
        new_tenant.tenant_lease_agreement_status = None

        # Save the new tenant
        new_tenant.save()

        # Copy the physical-invoice profile (OneToOne) if the original has one
        try:
            src_profile = original_tenant.physical_invoice_profile
        except PhysicalInvoiceProfile.DoesNotExist:
            src_profile = None
        if src_profile is not None:
            PhysicalInvoiceProfile.objects.create(
                tenant=new_tenant,
                customer_id_label=src_profile.customer_id_label,
                billing_name=src_profile.billing_name,
                billing_address=src_profile.billing_address,
                billing_tel=src_profile.billing_tel,
                client_email_body=src_profile.client_email_body,
                water_enabled=src_profile.water_enabled,
                water_cycle_anchor=src_profile.water_cycle_anchor,
                water_cycle_interval_months=src_profile.water_cycle_interval_months,
            )

        # Redirect to edit page for the new tenant
        messages.success(
            request,
            f'Tenant duplicated successfully! Please update the lease dates and set to Active when ready.'
        )
        return redirect('tenant_edit', tenant_id=new_tenant.tenant_id)

    except tenant.DoesNotExist:
        messages.error(request, 'Tenant not found.')
        return redirect('tenant')
    except Exception as e:
        messages.error(request, f'Error duplicating tenant: {str(e)}')
        return redirect('tenant')


@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
def delete_tenant_view(request, tenant_id):
    """
    Delete a tenant and automatically recalculate vacancy periods.
    Requires can_edit_tenants permission.
    """

    try:
        tenant_to_delete = tenant.objects.get(pk=tenant_id)
        tenant_name = tenant_to_delete.tenant_name
        property_name = tenant_to_delete.prop.prop_name

        # Delete the tenant (signal will handle vacancy cleanup)
        tenant_to_delete.delete()

        messages.success(
            request,
            f'Tenant "{tenant_name}" from {property_name} has been deleted. Vacancy periods have been automatically recalculated.'
        )
        return redirect('tenant')

    except tenant.DoesNotExist:
        messages.error(request, 'Tenant not found.')
        return redirect('tenant')
    except Exception as e:
        messages.error(request, f'Error deleting tenant: {str(e)}')
        return redirect('tenant')


# Days past the agreed terms before a tenant is flagged as slow.
#
# Not zero, deliberately. Terms across this portfolio are 0 - rent is due on
# the invoice date - so a knife-edge at zero would flag every tenant who pays
# on the 2nd rather than the 1st, and the colour would stop carrying any
# information. A week absorbs weekends, bank value dating and the ordinary
# rhythm of a standing order without hiding real drift: a tenant averaging 10+
# days past terms is genuinely behaving differently from one averaging 2.
PAYMENT_GRACE_DAYS = 7


@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def tenant_payment_days_view(request):
    """How many days does each tenant actually take to pay?

    Measures `invoice_paid_date - invoice_date` per invoice and summarises it
    per tenant against the terms agreed on the lease
    (`tenant.tenant_payment_terms`).

    Two things to know about the numbers.

    First, the history is short. `invoice_paid_date` was only added on
    3 Aug 2026 (migration 0088); anything marked paid before then has no date
    and is not recoverable. Rent is monthly, so each tenant contributes roughly
    one measurement a month - about six before an average means much. `n` is on
    every row so a thin average is never mistaken for a settled one.

    Second, terms of 0 days is a real answer - due on the invoice date - so
    every test here is `is not None`, never truthiness. Reading 0 as "not set"
    would quietly drop exactly the tenants who pay on presentation.

    The paid date is stamped when the invoice is marked Paid. Here the bank is
    checked and invoices marked daily, so it is a faithful proxy for the day
    the money arrived.
    """
    show_all = request.GET.get('all') == '1'
    today = date.today()

    tenants = tenant.objects.select_related('prop').order_by('tenant_name')
    if not show_all:
        tenants = tenants.filter(tenant_current__iexact='Yes')

    rows, no_data, outstanding = [], [], []

    for t in tenants:
        invs = list(invoices.objects.filter(tenant=t).order_by('invoice_date'))

        measured = []
        for inv in invs:
            if inv.invoice_paid_date and inv.invoice_date:
                measured.append({
                    'invoice_date': inv.invoice_date,
                    'paid_date': inv.invoice_paid_date,
                    'days': (inv.invoice_paid_date - inv.invoice_date).days,
                    'amount': inv.effective_amount,
                })

        for inv in invs:
            if (inv.invoice_paid or '').strip().lower() != 'yes' and inv.invoice_date:
                outstanding.append({
                    'tenant': t,
                    'invoice': inv,
                    'age': (today - inv.invoice_date).days,
                })

        if not measured:
            # Say WHY rather than leaving a blank row - the usual reason is a
            # payment made before the paid date was ever recorded, which is a
            # gap in history, not a gap in the tenant's behaviour.
            recent = []
            for inv in sorted(invs, key=lambda i: (i.invoice_date is None,
                                                   i.invoice_date), reverse=True)[:6]:
                if inv.invoice_paid_date:
                    why = 'measurable'
                elif (inv.invoice_paid or '').strip().lower() == 'yes':
                    why = 'marked paid, but no paid date recorded'
                else:
                    why = 'not paid yet'
                recent.append({'invoice': inv, 'why': why})
            no_data.append({'tenant': t, 'recent': recent})
            continue

        days = [m['days'] for m in measured]
        ordered = sorted(days)
        mid = len(ordered) // 2
        median = (float(ordered[mid]) if len(ordered) % 2
                  else (ordered[mid - 1] + ordered[mid]) / 2.0)

        avg = sum(days) / float(len(days))
        terms = t.tenant_payment_terms
        vs_terms = (avg - terms) if terms is not None else None

        if vs_terms is None:
            band = 'unknown'
        elif vs_terms <= PAYMENT_GRACE_DAYS:
            band = 'ontime'
        elif vs_terms <= PAYMENT_GRACE_DAYS * 2:
            band = 'slight'
        else:
            band = 'late'

        rows.append({
            'tenant': t,
            'n': len(days),
            'provisional': len(days) < 6,
            'avg': avg,
            'median': median,
            'best': min(days),
            'worst': max(days),
            'last': days[-1],
            'terms': terms,
            'vs_terms': vs_terms,
            'band': band,
            'measured': list(reversed(measured)),
        })

    # Slowest first: that is the order worth reading.
    rows.sort(key=lambda r: r['avg'], reverse=True)
    outstanding.sort(key=lambda o: o['age'], reverse=True)

    all_days = [m['days'] for r in rows for m in r['measured']]
    summary = {
        'tenants_measured': len(rows),
        'payments_measured': len(all_days),
        'portfolio_avg': (sum(all_days) / float(len(all_days))) if all_days else None,
        'flagged': len([r for r in rows if r['band'] in ('slight', 'late')]),
        'missing_terms': len([r for r in rows if r['terms'] is None]),
        'not_measurable': len(no_data),
        'outstanding_total': sum(float(o['invoice'].effective_amount or 0)
                                 for o in outstanding),
    }

    context = {
        'rows': rows,
        'no_data': no_data,
        'outstanding': outstanding,
        'summary': summary,
        'show_all': show_all,
        'today': today,
        'grace': PAYMENT_GRACE_DAYS,
        'data_starts': date(2026, 8, 3),
    }
    return render(request, 'tenant_payment_days.html', context)
