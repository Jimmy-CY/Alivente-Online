"""Property Acquisitions - mounted at /acquisitions/ (RA19, 23 Nov 2026)."""
from django.urls import path

from . import api, views

app_name = "acquisitions"

urlpatterns = [
    path("", views.overview, name="overview"),
    path("scenarios/", views.scenario_list, name="scenarios"),
    path("scenarios/new/", views.scenario_edit, name="scenario_new"),
    path("scenarios/new/preview/", views.scenario_preview, name="scenario_preview_new"),
    # RA21 - an area added from the Location rule's list.
    path("areas/add/", views.area_add, name="area_add"),
    path("run/", views.run_now, name="run_now"),          # RA24 - Run search now
    # RA27 - the Run and PC pop-ups follow the runs as they report; the PC
    # search can be started from here once Claude offers it a trigger.
    path("run/progress/", views.run_progress, name="run_progress"),
    path("run/pc/", views.run_pc, name="run_pc"),
    path("scenarios/<int:pk>/", views.scenario_results, name="scenario"),
    path("scenarios/<int:pk>/edit/", views.scenario_edit, name="scenario_edit"),
    path("scenarios/<int:pk>/preview/", views.scenario_preview, name="scenario_preview"),
    path("scenarios/<int:pk>/toggle/", views.scenario_toggle, name="scenario_toggle"),
    path("scenarios/<int:pk>/export.csv", views.scenario_csv, name="scenario_csv"),
    path("property/<int:pk>/", views.property_detail, name="property"),
    path("property/<int:pk>/status/", views.property_status, name="property_status"),
    path("property/<int:pk>/notes/", views.property_notes, name="property_notes"),
    path("property/<int:pk>/viewing/", views.property_viewing, name="property_viewing"),
    path("property/<int:pk>/offer-brief.pdf", views.offer_brief, name="offer_brief"),
    path("price-watch/", views.price_watch, name="price_watch"),
    path("market/", views.market, name="market"),
    path("runs/", views.runs, name="runs"),
    # RA25 - the door Claude's search tasks use (a key, no login: api.py).
    path("api/scenarios/", api.scenarios, name="api_scenarios"),
    path("api/runs/", api.run_start, name="api_run_start"),
    path("api/runs/<int:pk>/report/", api.run_report, name="api_run_report"),
]
