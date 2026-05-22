"""
crs.views.fi — Reporting FI management.

Functions:
    fi_list   — List view at /crs/fis/. Annotates IN counts.
    fi_add    — Form view at /crs/fis/add/ with inline IN formset.
    fi_edit   — Form view at /crs/fis/<pk>/edit/ with inline IN formset.
    fi_delete — POST-only delete at /crs/fis/<pk>/delete/. FK-protected
                via Submission. Child INs cascade-delete with the parent.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import Count, ProtectedError
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from crs.forms import ReportingFIForm, ReportingFIINFormSet
from crs.models import ReportingFI


@login_required
@permission_required('auth.can_access_crs', raise_exception=True)
def fi_list(request):
    """List all ReportingFI rows with IN counts."""
    fis = (
        ReportingFI.objects
        .annotate(in_count=Count("ins"))
        .order_by("name")
    )
    return render(request, "crs/fi_list.html", {"fis": fis})


@login_required
@permission_required('auth.can_edit_crs', raise_exception=True)
def fi_add(request):
    """Create a new ReportingFI with inline INs."""
    if request.method == "POST":
        form = ReportingFIForm(request.POST)
        formset = ReportingFIINFormSet(request.POST, prefix="ins")
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                fi_obj = form.save()
                formset.instance = fi_obj
                formset.save()
            messages.success(request, f"Reporting FI '{fi_obj.name}' added.")
            return redirect("crs:fi_list")
    else:
        form = ReportingFIForm()
        formset = ReportingFIINFormSet(prefix="ins")
    return render(request, "crs/fi_form.html", {
        "form": form,
        "formset": formset,
        "mode": "add",
        "title": "Add Reporting FI",
    })


@login_required
@permission_required('auth.can_edit_crs', raise_exception=True)
def fi_edit(request, pk):
    """Edit an existing ReportingFI with inline INs."""
    fi_obj = get_object_or_404(ReportingFI, pk=pk)
    if request.method == "POST":
        form = ReportingFIForm(request.POST, instance=fi_obj)
        formset = ReportingFIINFormSet(request.POST, instance=fi_obj, prefix="ins")
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
            messages.success(request, f"Reporting FI '{fi_obj.name}' updated.")
            return redirect("crs:fi_list")
    else:
        form = ReportingFIForm(instance=fi_obj)
        formset = ReportingFIINFormSet(instance=fi_obj, prefix="ins")
    return render(request, "crs/fi_form.html", {
        "form": form,
        "formset": formset,
        "mode": "edit",
        "fi": fi_obj,
        "title": f"Edit {fi_obj.name}",
    })


@login_required
@permission_required('auth.can_edit_crs', raise_exception=True)
def fi_delete(request, pk):
    """Delete a ReportingFI. POST-only. FK-protected via Submission."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    fi_obj = get_object_or_404(ReportingFI, pk=pk)
    name = fi_obj.name
    try:
        fi_obj.delete()
        messages.success(request, f"Reporting FI '{name}' deleted.")
    except ProtectedError as exc:
        n = len(exc.protected_objects)
        messages.error(
            request,
            f"Cannot delete '{name}' — {n} submission(s) reference it. "
            f"Delete or reassign those submissions first."
        )
    return redirect("crs:fi_list")