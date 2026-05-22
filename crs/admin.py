"""
crs.admin — Django admin registrations for the CRS module.
"""
from django.contrib import admin

from crs.models import (
    CountryConfiguration,
    ReportingFI,
    ReportingFIIN,
    Submission,
)


# ===========================================================================
# CountryConfiguration
# ===========================================================================
@admin.register(CountryConfiguration)
class CountryConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "country_code", "country_name", "is_active",
        "default_currency", "oecd_version", "updated_at",
    )
    list_filter = ("is_active", "oecd_version")
    search_fields = ("country_code", "country_name")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Identity", {
            "fields": ("country_code", "country_name", "is_active"),
        }),
        ("Schema", {
            "fields": ("oecd_version",),
        }),
        ("Reference ID Templates", {
            "fields": (
                "message_ref_id_template",
                "fi_doc_ref_id_template",
                "account_doc_ref_id_template",
                "output_filename_template",
            ),
            "description": (
                "Tokens: [SENDING_FI_IN], [YEAR], [YYYYMMDDHHMM], "
                "[CURRENT_DATE], [UUID]. Resolved at submission time."
            ),
        }),
        ("Defaults", {
            "fields": ("default_currency",),
        }),
        ("Validation", {
            "fields": ("tin_regex",),
            "classes": ("collapse",),
        }),
        ("Audit", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


# ===========================================================================
# ReportingFI
# ===========================================================================
class ReportingFIINInline(admin.TabularInline):
    """Inline editor for INs on the ReportingFI detail page."""
    model = ReportingFIIN
    extra = 1
    fields = ("in_type", "in_value", "issued_by")


@admin.register(ReportingFI)
class ReportingFIAdmin(admin.ModelAdmin):
    list_display = (
        "name", "res_country_code", "address_country_code",
        "is_active", "updated_at",
    )
    list_filter = ("is_active", "res_country_code")
    search_fields = ("name", "ins__in_value")
    readonly_fields = ("created_at", "updated_at")
    inlines = [ReportingFIINInline]

    fieldsets = (
        ("Identity", {
            "fields": ("name", "name_type", "is_active"),
        }),
        ("Tax Residence", {
            "fields": ("res_country_code",),
        }),
        ("Address", {
            "fields": ("address_country_code", "address_free", "address_type"),
            "description": (
                "AddressFree mode — CountryCode is required, the rest of the "
                "address goes in the free-text field."
            ),
        }),
        ("Contact", {
            "fields": ("contact",),
            "description": (
                "Contact details for the person handling CRS submissions at "
                "this FI. Used to populate the Message Header's Contact "
                "element at XML generation time."
            ),
        }),
        ("Audit", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


# ===========================================================================
# Submission
# ===========================================================================
@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "__str__", "status", "year", "reporting_fi",
        "country_config", "created_at",
    )
    list_filter = ("status", "country_config", "year", "message_type", "document_type")
    search_fields = (
        "message_ref_id",
        "reporting_fi__name",
        "reporting_fi__ins__in_value",
    )
    readonly_fields = (
        "created_by",
        "xml_generated_at", "closed_at",
        "submitted_externally_at", "acknowledged_at",
        "created_at", "updated_at",
    )
    autocomplete_fields = ("reporting_fi",)  # FI dropdown could be long

    fieldsets = (
        ("Selection", {
            "fields": (
                "reporting_fi", "country_config", "year",
                "sending_company_in", "created_by",
            ),
        }),
        ("Message Header", {
            "fields": (
                "transmitting_country", "receiving_country",
                "document_type", "message_type",
                "message_ref_id", "corr_message_ref_id",
                "warning",
            ),
        }),
        ("Files", {
            "fields": ("uploaded_excel", "generated_xml"),
        }),
        ("Lifecycle", {
            "fields": (
                "status",
                "xml_generated_at", "closed_at",
                "submitted_externally_at", "acknowledged_at",
                "acknowledgement_notes",
            ),
        }),
        ("Audit", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def save_model(self, request, obj, form, change):
        """Auto-stamp created_by on first save."""
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)