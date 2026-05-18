"""
Petty Cash views for Alivente Online.

Extracted from pages/views/main.py as part of the modular split.
Covers the simple cash-ledger pages (list / add / commit) and the
report generator.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect, render

from ..forms import PettyForm
from ..models import petty


# NOTE: decorators below assumed to match the pattern used by petty_cash_commit
# and petty_cash_add. Verify against main.py lines 5395-5400 before deploying.
@login_required
@permission_required('auth.can_access_petty_cash', raise_exception=True)
def petty_cash(request):
    presults = petty.objects.all().order_by('petty_cash_date')
    pvalues = petty.objects.values()
    balance = 0
    for x in pvalues:
        if x['petty_cash_dr_cr'] == "DR":
            balance = balance + x['petty_cash_amount']
        elif x['petty_cash_dr_cr'] == "CR":
            balance = balance - x['petty_cash_amount']
    return render(request, "petty_cash.html", {"petty": presults, "balance": balance})


@login_required
@permission_required('auth.can_edit_petty_cash', raise_exception=True)
def petty_cash_commit(request):
    if request.method == "POST":
        form = PettyForm(request.POST or None)
        print(form)  # legacy debug print; safe to remove in a future cleanup
        if form.is_valid():
            form.save()
            messages.success(request, "Transaction Added Successfully")
    presults = petty.objects.all().order_by('petty_cash_date')
    pvalues = petty.objects.values()
    balance = 0
    for x in pvalues:
        if x['petty_cash_dr_cr'] == "DR":
            balance = balance + x['petty_cash_amount']
        elif x['petty_cash_dr_cr'] == "CR":
            balance = balance - x['petty_cash_amount']
    return render(request, "petty_cash.html", {"petty": presults, "balance": balance})


@login_required
@permission_required('auth.can_edit_petty_cash', raise_exception=True)
def petty_cash_add(request):
    presults = petty.objects.all().order_by('petty_cash_date')
    return render(request, "petty_cash_add.html", {"petty": presults})


# NOTE: decorators below assumed to match. Verify against main.py lines 6165-6167.
@login_required
@permission_required('auth.can_access_petty_cash', raise_exception=True)
def petty_cash_rep(request):
    # NB: this imports the project-root ``petty_cash.py`` reporting helper,
    # NOT this views file. Absolute imports resolve via sys.path (where the
    # project root sits) rather than the current package, so the naming stays
    # unambiguous even with this module file now also called petty_cash.py.
    import petty_cash
    rep_output = request.POST.get('d_e')
    if request.user.is_authenticated:
        email = request.user.email
        fname = request.user.first_name
    petty_cash.petty_cash(rep_output, email, fname)
    messages.success(request, "Report Created Successfully")
    return redirect('home')