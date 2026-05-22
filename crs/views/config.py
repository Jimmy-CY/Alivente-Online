"""
crs.views.config — Country Configuration management.

Functions:
    country_list   — List view at /crs/countries/.
    country_add    — Form view at /crs/countries/add/.
    country_edit   — Form view at /crs/countries/<pk>/edit/.
    country_delete — POST-only delete at /crs/countries/<pk>/delete/.
                     FK-protected via Submission (PROTECT on_delete). Loose
                     string references from ReportingFI residence/address
                     country codes are NOT blocked here — they're not FKs.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import ProtectedError
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from crs.forms import CountryConfigurationForm
from crs.models import CountryConfiguration


@login_required
@permission_required('auth.can_access_crs', raise_exception=True)
def country_list(request):
    """List all CountryConfiguration rows."""
    countries = CountryConfiguration.objects.order_by("country_code")
    return render(request, "crs/country_list.html", {"countries": countries})


@login_required
@permission_required('auth.can_edit_crs', raise_exception=True)
def country_add(request):
    """Create a new CountryConfiguration."""
    if request.method == "POST":
        form = CountryConfigurationForm(request.POST)
        if form.is_valid():
            country = form.save()
            messages.success(
                request,
                f"Country configuration '{country.country_code} — "
                f"{country.country_name}' added."
            )
            return redirect("crs:country_list")
    else:
        form = CountryConfigurationForm()
    return render(request, "crs/country_form.html", {
        "form": form,
        "mode": "add",
        "title": "Add Country Configuration",
    })


@login_required
@permission_required('auth.can_edit_crs', raise_exception=True)
def country_edit(request, pk):
    """Edit an existing CountryConfiguration."""
    country = get_object_or_404(CountryConfiguration, pk=pk)
    if request.method == "POST":
        form = CountryConfigurationForm(request.POST, instance=country)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Country configuration '{country.country_code} — "
                f"{country.country_name}' updated."
            )
            return redirect("crs:country_list")
    else:
        form = CountryConfigurationForm(instance=country)
    return render(request, "crs/country_form.html", {
        "form": form,
        "mode": "edit",
        "country": country,
        "title": f"Edit {country.country_code} — {country.country_name}",
    })


@login_required
@permission_required('auth.can_edit_crs', raise_exception=True)
def country_delete(request, pk):
    """Delete a CountryConfiguration. POST-only. FK-protected via Submission."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    country = get_object_or_404(CountryConfiguration, pk=pk)
    label = f"{country.country_code} — {country.country_name}"
    try:
        country.delete()
        messages.success(request, f"Country configuration '{label}' deleted.")
    except ProtectedError as exc:
        n = len(exc.protected_objects)
        messages.error(
            request,
            f"Cannot delete '{label}' — {n} submission(s) reference it. "
            f"Delete or reassign those submissions first."
        )
    return redirect("crs:country_list")