"""
Suppliers views for Alivente Online.

Extracted from pages/views/main.py as part of the modular split.
Covers the suppliers CRUD pages, the per-supplier printable report,
and the bulk report generator.
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

    # Pass the search values back to template for form preservation
    context = {
        "supplier": sresults,
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
        else:
            print(form.errors.as_data())  # legacy debug; safe to remove in a future cleanup
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
    # NB: imports the project-root ``print_supplier.py`` reporting helper,
    # not anything in this views file. Absolute imports resolve via sys.path.
    import print_supplier
    sup = request.POST.get('supname')
    rep_output = request.POST.get('d_e')
    if request.user.is_authenticated:
        email = request.user.email
        fname = request.user.first_name
    print_supplier.supplier_report(sup, rep_output, email, fname)
    messages.success(request, "Report Created Successfully")
    return redirect('home')