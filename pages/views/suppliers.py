"""
Suppliers views.

Extracted from the legacy pages/views/main.py during the modular views
split. Covers the suppliers CRUD pages, the per-supplier printable
report, and the bulk report generator.

Functions
---------
- suppliers             : List with optional name/country filters.
- suppliers_add         : Renders the add page.
- suppliers_edit        : Renders the edit page for one supplier.
- suppliers_commit      : POST creates a supplier (SupplierForm).
- suppliers_edit_commit : POST updates an existing supplier.
- suppliers_delete      : POST deletes a supplier (superuser only).
- supplier_report       : Per-supplier printable report page.
- suppliers_rep         : Generates/e-mails the bulk supplier report via
                          the project-root print_supplier.py helper,
                          then redirects home.

Auth tiers
----------
read tier -> auth.can_access_suppliers  (suppliers, supplier_report,
                                         suppliers_rep)
edit tier -> auth.can_edit_suppliers    (add, edit, commit, edit_commit,
                                         delete; delete additionally
                                         requires request.user.is_superuser)
"""

from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import SupplierForm
from ..models import supplier


@login_required
@permission_required('auth.can_access_suppliers', raise_exception=True)
def suppliers(request):
    sup_output = request.POST.get('supname')
    sup_count = request.POST.get('supcount')

    # Start with all suppliers
    sresults = supplier.objects.all().order_by('supplier_country', 'supplier_contact_person')

    # Apply search filter if provided and not "All"
    if sup_output and sup_output != "All":
        sresults = sresults.filter(supplier_contact_person__icontains=sup_output)

    # Apply country filter if provided and not "All"
    if sup_count and sup_count != "All":
        sresults = sresults.filter(supplier_country=sup_count)

    # The Country dropdown in suppliers.html loops over distinct_countries.
    # Nothing ever supplied it, so the loop ran zero times and the filter
    # offered "All Countries" and nothing else - it has never filtered. Django
    # renders an undefined template variable as empty rather than raising,
    # which is why it went unnoticed from May 2026 until 26 Aug.
    #
    # Built from the data, not hardcoded: a supplier in a new country appears
    # in the filter the moment they are saved. order_by BEFORE values_list is
    # deliberate - DISTINCT applies to the selected columns, and Django adds
    # ORDER BY columns to the SELECT, so ordering afterwards can smuggle a
    # second column in and make every row distinct.
    distinct_countries = (
        supplier.objects
        .exclude(supplier_country__isnull=True)
        .exclude(supplier_country__exact="")
        .order_by("supplier_country")
        .values_list("supplier_country", flat=True)
        .distinct()
    )

    # Pass the search values back to template for form preservation
    context = {
        "supplier": sresults,
        "distinct_countries": distinct_countries,
        "selected_supplier": sup_output if sup_output and sup_output != "All" else "",
        "selected_country": sup_count if sup_count and sup_count != "All" else "All",
    }

    return render(request, "suppliers.html", context)


@login_required
@permission_required('auth.can_edit_suppliers', raise_exception=True)
def suppliers_add(request):
    sresults = supplier.objects.all().order_by('supplier_country', 'supplier_contact_person')
    return render(request, "suppliers_add.html", {"supplier": sresults})


@login_required
@permission_required('auth.can_edit_suppliers', raise_exception=True)
def suppliers_edit(request, supplier_id):
    sresults = supplier.objects.filter(pk=supplier_id)
    return render(request, "suppliers_edit.html", {"supplier": sresults})


@login_required
@permission_required('auth.can_edit_suppliers', raise_exception=True)
def suppliers_commit(request):
    if request.method == "POST":
        form = SupplierForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Supplier Added Successfully")
    sresults = supplier.objects.all().order_by('supplier_country', 'supplier_contact_person')
    return render(request, "suppliers.html", {"supplier": sresults})


@login_required
@permission_required('auth.can_edit_suppliers', raise_exception=True)
def suppliers_edit_commit(request, supplier_id):
    sup = supplier.objects.get(pk=supplier_id)
    if request.method == "POST":
        form = SupplierForm(request.POST or None, instance=sup)
        if form.is_valid():
            form.save()
            messages.success(request, "Supplier Edited Successfully")
    sresults = supplier.objects.all().order_by('supplier_country', 'supplier_contact_person')
    return render(request, "suppliers.html", {"supplier": sresults})


@login_required
@permission_required('auth.can_edit_suppliers', raise_exception=True)
def suppliers_delete(request, supplier_id):
    if request.method == 'POST' and request.user.is_superuser:
        try:
            supplier_instance = supplier.objects.get(supplier_id=supplier_id)
            contact_person = supplier_instance.supplier_contact_person
            supplier_instance.delete()
            messages.success(request, f'Supplier "{contact_person}" has been deleted successfully.')
        except supplier.DoesNotExist:
            messages.error(request, 'Supplier not found.')
        except Exception as e:
            messages.error(request, f'Error deleting supplier: {str(e)}')
    else:
        messages.error(request, 'Unauthorized action.')

    return redirect('suppliers')


@login_required
@permission_required('auth.can_access_suppliers', raise_exception=True)
def supplier_report(request, supplier_id):
    today = date.today()
    supplier_obj = get_object_or_404(supplier.objects.only(
        'supplier_id', 'supplier_contact_person', 'supplier_contact_number',
        'supplier_email', 'supplier_company_name', 'supplier_role',
        'supplier_country',
    ), pk=supplier_id)
    context = {
        'today': today,
        'supplier': supplier_obj,
    }
    return render(request, 'supplier_report.html', context)


@login_required
@permission_required('auth.can_access_suppliers', raise_exception=True)
def suppliers_rep(request):
    # Deliberate inline import (do NOT hoist): this resolves to the
    # project-root print_supplier.py reporting helper, NOT anything in
    # this views package. Python's absolute import finds it via sys.path
    # (the project root). Kept inline to make that resolution explicit
    # and local.
    import print_supplier
    sup = request.POST.get('supname')
    rep_output = request.POST.get('d_e')
    # @login_required guarantees an authenticated user here, so email/fname
    # are always available (the former `if request.user.is_authenticated`
    # guard was always true and left these statically unbound-looking).
    email = request.user.email
    fname = request.user.first_name
    print_supplier.supplier_report(sup, rep_output, email, fname)
    messages.success(request, "Report Created Successfully")
    return redirect('home')