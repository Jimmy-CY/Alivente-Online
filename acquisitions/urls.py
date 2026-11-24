"""Property Acquisitions - mounted at /acquisitions/ (RA19, 23 Nov 2026)."""
from django.urls import path

from . import views

app_name = "acquisitions"

urlpatterns = [
    path("", views.overview, name="overview"),
    path("scenarios/", views.scenario_list, name="scenarios"),
    path("scenarios/new/", views.scenario_edit, name="scenario_new"),
    path("scenarios/new/preview/", views.scenario_preview, name="scenario_preview_new"),
    # RA21 - an area added from the Location rule's list.
    path("areas/add/", views.area_add, name="area_add"),
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
    path("auctions/", views.auctions, name="auctions"),
    path("runs/", views.runs, name="runs"),
]
