"""
crs.views.main — Landing page for the CRS module.

Functions:
    index — Section-cards summary view at /crs/. Shows three cards
            (Country Configurations, Reporting FIs, Submissions) with
            quick counts from the database. Cards render as
            "coming-soon" until each section's list view is built.
"""
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.staticfiles import finders
from django.http import FileResponse, Http404
from django.shortcuts import render

from crs.models import CountryConfiguration, ReportingFI, Submission


@login_required
@permission_required('auth.can_access_crs', raise_exception=True)
def index(request):
    """CRS module landing page."""
    context = {
        "country_count":      CountryConfiguration.objects.filter(is_active=True).count(),
        "fi_count":           ReportingFI.objects.filter(is_active=True).count(),
        "submission_count":   Submission.objects.count(),
        "draft_count":        Submission.objects.filter(status="draft").count(),
        "closed_count":       Submission.objects.filter(status="closed").count(),
        "submitted_count":    Submission.objects.filter(status="submitted_externally").count(),
        "acknowledged_count": Submission.objects.filter(status="acknowledged").count(),
        "rejected_count":     Submission.objects.filter(status="rejected").count(),
    }
    return render(request, "crs/index.html", context)


@permission_required("auth.can_access_crs", raise_exception=True)
def download_template(request):
    path = finders.find("crs/templates/crs_template.xlsx")
    if not path:
        raise Http404("CRS template not found")
    return FileResponse(
        open(path, "rb"),
        as_attachment=True,
        filename="crs_template.xlsx",
    )