from django.contrib import admin, messages

from .models import (Area, Criterion, ListingSource, MarketSnapshot, PriceObservation, Property,
                     Scenario, ScenarioMatch, SearchRun, SiteResult, Viewing, Website)
from .scoring import apply_score


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("name", "district")
    list_filter = ("district",)
    search_fields = ("name",)


@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "needs_pc", "is_active", "url")
    list_filter = ("kind", "needs_pc", "is_active")
    search_fields = ("name",)


class CriterionInline(admin.TabularInline):
    model = Criterion
    extra = 0
    fields = ("order", "label", "field", "kind", "operator", "num_min", "num_max", "text_values",
              "points", "full_from", "full_to", "zero_below", "zero_above", "score_bands",
              "group", "rule_text")


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ("name", "property_type", "is_active", "cadence", "run_time", "points_used",
                    "tracked")
    list_filter = ("is_active", "property_type", "cadence")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("areas", "websites")
    inlines = [CriterionInline]
    actions = ["rescore"]
    fieldsets = (
        (None, {"fields": ("name", "slug", "purpose", "property_type", "is_active", "owner")}),
        ("Where to look", {"fields": ("areas", "websites")}),
        ("Unknowns", {"fields": ("unknown_score_cap", "max_unknown_musts")}),
        ("Schedule", {"fields": ("cadence", "run_time", "run_weekday", "blocked_sites", "notify")}),
        ("Summary", {"fields": ("summary_new_listings", "summary_changes", "summary_site_status",
                                "summary_vs_median", "summary_top3", "summary_market_trend",
                                "summary_instructions")}),
    )

    @admin.display(description="Points")
    def points_used(self, obj):
        return f"{obj.points_total():g} / 100"

    @admin.display(description="Tracked")
    def tracked(self, obj):
        return obj.matches.count()

    @admin.action(description="Re-score all listings in the selected scenarios")
    def rescore(self, request, queryset):
        for s in queryset:
            s.rescore_all()
        self.message_user(request, "Re-scored.", messages.SUCCESS)


class SourceInline(admin.TabularInline):
    model = ListingSource
    extra = 0
    fields = ("website", "url", "external_id", "agent", "agent_phone", "first_seen", "last_seen",
              "is_live", "site_status")


class PriceInline(admin.TabularInline):
    model = PriceObservation
    extra = 0
    fields = ("observed_on", "asking_price", "vat_status", "source")


class MatchInline(admin.TabularInline):
    model = ScenarioMatch
    extra = 0
    fields = ("scenario", "status", "score", "is_capped", "passes_musts", "failed_musts",
              "unknown_musts", "date_found", "last_checked")
    readonly_fields = ("score", "is_capped", "passes_musts", "failed_musts", "unknown_musts")


class ViewingInline(admin.TabularInline):
    model = Viewing
    extra = 0


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("title", "property_type", "area", "price_incl_vat", "internal_m2", "plot_m2",
                    "bedrooms", "updated_at")
    list_filter = ("property_type", "area", "is_auction")
    search_fields = ("title", "street", "suburb_text", "sources__external_id", "sources__url")
    readonly_fields = ("price_incl_vat", "price_per_m2", "buildable_m2", "price_per_buildable_m2")
    inlines = [MatchInline, SourceInline, PriceInline, ViewingInline]
    fieldsets = (
        (None, {"fields": ("property_type", "title", "area", "suburb_text", "street")}),
        ("Price", {"fields": ("asking_price", "vat_status", "price_incl_vat", "price_per_m2")}),
        ("Size", {"fields": ("internal_m2", "internal_m2_confirmed", "covered_balcony_m2",
                             "total_m2")}),
        ("Apartment", {"classes": ("collapse",), "fields": (
            "bedrooms", "bathrooms", "guest_wc", "master_ensuite", "open_plan", "parking_spaces",
            "parking_covered", "whole_floor", "floor_level", "lift", "storeroom", "year_built",
            "condition", "title_deeds")}),
        ("Plot", {"classes": ("collapse",), "fields": (
            "plot_m2", "building_density_pct", "site_coverage_pct", "floors_allowed",
            "planning_zone", "road_frontages", "buildable_m2", "price_per_buildable_m2")}),
        ("Auction / bank-owned", {"classes": ("collapse",), "fields": (
            "is_auction", "reserve_price", "auction_date", "offer_deadline", "viewing_date",
            "deposit_pct")}),
        ("Other", {"classes": ("collapse",), "fields": ("extra_facts", "description")}),
    )


@admin.register(ScenarioMatch)
class ScenarioMatchAdmin(admin.ModelAdmin):
    list_display = ("property", "scenario", "status", "score", "is_capped", "passes_musts",
                    "date_found", "last_checked")
    list_filter = ("scenario", "status", "passes_musts")
    search_fields = ("property__title", "flags", "your_comments")
    readonly_fields = ("score", "raw_score", "is_capped", "passes_musts", "failed_musts",
                       "unknown_musts", "breakdown")
    actions = ["shortlist", "reject", "rescore"]

    @admin.action(description="Shortlist")
    def shortlist(self, request, queryset):
        for m in queryset:
            m.set_status_by_user(ScenarioMatch.Status.SHORTLISTED)

    @admin.action(description="Reject")
    def reject(self, request, queryset):
        for m in queryset:
            m.set_status_by_user(ScenarioMatch.Status.REJECTED)

    @admin.action(description="Re-score")
    def rescore(self, request, queryset):
        for m in queryset.select_related("scenario", "property"):
            apply_score(m)


class SiteResultInline(admin.TabularInline):
    model = SiteResult
    extra = 0


@admin.register(SearchRun)
class SearchRunAdmin(admin.ModelAdmin):
    list_display = ("started_at", "scenario", "task_name", "where", "listings_checked",
                    "listings_added", "complete")
    list_filter = ("where", "scenario")
    inlines = [SiteResultInline]

    @admin.display(boolean=True, description="Complete")
    def complete(self, obj):
        return obj.is_complete


@admin.register(MarketSnapshot)
class MarketSnapshotAdmin(admin.ModelAdmin):
    list_display = ("week_start", "area", "property_type", "size_band", "listings_for_sale",
                    "new_this_week", "median_price_per_m2")
    list_filter = ("area", "property_type", "size_band")
