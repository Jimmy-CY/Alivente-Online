"""
crs.models — Persistent data layer for the CRS reporting module.

Models in this file:
    CountryConfiguration — per-country reporting rules (TIN regex,
        reference-ID templates, file-naming template, default currency,
        OECD schema version). One row per country.
    ReportingFI — master record for a Financial Institution that files
        CRS reports. Captured manually once per FI; selected by FK from
        each Submission. Multi-IN handled via the ReportingFIIN child.
    ReportingFIIN — one of potentially several Identification Numbers
        attached to a ReportingFI (TIN / GIIN / EIN / BRN / LEI / Other),
        each tagged with the issuing country.
    Submission — a single CRS submission cycle for one (FI x Country x
        Year). Holds the Message Header data, the lifecycle state, and
        FK references plus the durable XML output. Customer account
        data uploaded as Excel is transient — held in temp storage
        during draft, deleted on closure.
"""
from datetime import date

from django.conf import settings
from django.db import models


# ===========================================================================
# Choice enumerations sourced from the OECD CRS XML Schema v2.0
# ===========================================================================
NAME_TYPE_CHOICES = [
    ("legal", "Legal Name"),
    ("dba",   "Doing Business As"),
    ("alias", "Alias"),
    ("aka",   "Also Known As"),
]

ADDRESS_TYPE_CHOICES = [
    ("residentialOrBusiness", "Residential or Business"),
    ("residential",           "Residential"),
    ("business",              "Business"),
    ("registeredOffice",      "Registered Office"),
    ("unspecified",           "Unspecified"),
]

IN_TYPE_CHOICES = [
    ("TIN",   "TIN — Tax Identification Number"),
    ("GIIN",  "GIIN — Global Intermediary Identification Number"),
    ("EIN",   "EIN — Employer Identification Number"),
    ("BRN",   "BRN — Business Registration Number"),
    ("LEI",   "LEI — Legal Entity Identifier"),
    ("Other", "Other"),
]

DOC_TYPE_INDIC_CHOICES = [
    ("OECD0", "OECD0 — Resent Data"),
    ("OECD1", "OECD1 — New Data"),
    ("OECD2", "OECD2 — Corrected Data"),
    ("OECD3", "OECD3 — Deletion of Data"),
]

MESSAGE_TYPE_INDIC_CHOICES = [
    ("CRS701", "CRS701 — New Information"),
    ("CRS702", "CRS702 — Corrections / Deletions"),
    ("CRS703", "CRS703 — Nil Reporting"),
]

SUBMISSION_STATUS_CHOICES = [
    ("draft",                "Draft"),
    ("closed",               "Closed"),
    ("submitted_externally", "Submitted Externally"),
    ("acknowledged",         "Acknowledged"),
    ("rejected",             "Rejected"),
]


# ===========================================================================
# File upload path helpers (used by Submission's FileFields)
# ===========================================================================
def excel_upload_path(instance, filename):
    """Temp storage for uploaded customer-data Excel.

    Deleted at submission closure. The 'temp' marker in the path is a
    hint for any future cleanup sweep over abandoned drafts.
    """
    return f"crs/submissions/{instance.id or 'new'}/temp/{filename}"


def xml_output_path(instance, filename):
    """Legacy upload_to for Submission.generated_xml. Kept so historical
    migrations referencing this name remain importable; current models no
    longer use it (XML files live on SubmissionXMLFile, via xml_file_path)."""
    submission_id = getattr(instance, "id", None) or "new"
    return f"crs/submissions/{submission_id}/xml/{filename}"


def xml_file_path(instance, filename):
    """Storage path for a SubmissionXMLFile, grouped under the parent submission.
    instance is the SubmissionXMLFile; instance.submission_id is the FK."""
    submission_id = instance.submission_id or "new"
    return f"crs/submissions/{submission_id}/xml/{filename}"


# ===========================================================================
# CountryConfiguration
# ===========================================================================
class CountryConfiguration(models.Model):
    """Per-country reporting rules for CRS submissions.

    Reference-ID and filename templates use [TOKEN] placeholders that
    are substituted at submission time. Common tokens:
    [SENDING_FI_IN], [YEAR], [YYYYMMDDHHMM], [CURRENT_DATE], [UUID].
    """

    # ----- Identity --------------------------------------------------------
    country_code = models.CharField(
        max_length=2,
        unique=True,
        help_text="ISO 3166-1 alpha-2 country code, e.g. 'CY' for Cyprus.",
    )
    country_name = models.CharField(
        max_length=100,
        help_text="Human-readable country name, e.g. 'Cyprus'.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive configurations cannot be used for new submissions.",
    )

# ----- Schema version --------------------------------------------------
    oecd_version = models.CharField(
        max_length=10,
        default="2.0",
        help_text="OECD CRS XML schema version for submissions to this country.",
    )
    # ----- Filing strategy -------------------------------------------------
    RECEIVING_COUNTRY_STRATEGY_CHOICES = [
        ("combined_domestic", "Combined Domestic File"),
        ("split_by_residence", "Split by Residence"),
    ]
    receiving_country_strategy = models.CharField(
        max_length=20,
        choices=RECEIVING_COUNTRY_STRATEGY_CHOICES,
        default="combined_domestic",
        help_text=(
            "How XML files are generated for this country. "
            "'Combined Domestic File' produces one XML with ReceivingCountry "
            "= TransmittingCountry (the FI's country) and lets the tax "
            "authority handle bilateral split downstream. "
            "'Split by Residence' produces one XML per receiving country, "
            "each containing only accounts whose holders are tax-resident "
            "in that country."
        ),
    )
    # ----- TIN validation --------------------------------------------------
    tin_regex = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Regex for validating TINs issued by this country. Optional.",
    )

    # ----- Reference-ID and filename templates -----------------------------
    message_ref_id_template = models.CharField(
        max_length=200,
        default="[SENDING_FI_IN].[YEAR]_[UUID]",
        help_text="Template for MessageRefID. Tokens resolved at submission time.",
    )
    fi_doc_ref_id_template = models.CharField(
        max_length=200,
        default="[SENDING_FI_IN].[YEAR]_[YYYYMMDDHHMM]_[UUID]",
        help_text="Template for ReportingFI DocRefID.",
    )
    account_doc_ref_id_template = models.CharField(
        max_length=200,
        default="[SENDING_FI_IN].[YEAR]_[YYYYMMDDHHMM]_[UUID]",
        help_text="Template for each AccountReport DocRefID.",
    )
    output_filename_template = models.CharField(
        max_length=200,
        default="[SENDING_FI_IN]_[CURRENT_DATE].xml",
        help_text="Template for the generated XML filename.",
    )

    # ----- Defaults applied to new submissions -----------------------------
    default_currency = models.CharField(
        max_length=3,
        default="EUR",
        help_text="Default currency for new submissions (ISO 4217 alpha-3).",
    )

    # ----- Audit timestamps ------------------------------------------------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["country_code"]
        verbose_name = "Country Configuration"
        verbose_name_plural = "Country Configurations"

    def __str__(self):
        status = "" if self.is_active else " (inactive)"
        return f"{self.country_code} — {self.country_name}{status}"


# ===========================================================================
# ReportingFI
# ===========================================================================
class ReportingFI(models.Model):
    """Master record for a Financial Institution that files CRS reports.

    Captured manually once per FI via the admin or (later) a user-facing
    form. Selected by FK from each Submission. Identification Numbers
    are held in the child ReportingFIIN table — a single FI may carry
    multiple INs (e.g. local TIN + global GIIN) each tagged with the
    issuing country.
    """

    # ----- Identity --------------------------------------------------------
    name = models.CharField(
        max_length=200,
        help_text="Legal name of the FI (OECD Name element; max 200 chars).",
    )
    name_type = models.CharField(
        max_length=20,
        choices=NAME_TYPE_CHOICES,
        default="legal",
        help_text="OECD nameType qualifier. Defaults to 'legal' for FIs.",
    )

    # ----- Tax residence ---------------------------------------------------
    res_country_code = models.CharField(
        max_length=2,
        help_text="ResCountryCode — ISO 3166-1 alpha-2 tax residence of the FI.",
    )

    # ----- Address (AddressFree mode, mirroring the Excel template choice) -
    address_country_code = models.CharField(
        max_length=2,
        help_text="Address CountryCode — ISO 3166-1 alpha-2 (Validation per spec).",
    )
    address_free = models.TextField(
        help_text="Free-text address string (OECD AddressFree element; up to 4000 chars).",
    )
    address_type = models.CharField(
        max_length=30,
        choices=ADDRESS_TYPE_CHOICES,
        default="registeredOffice",
        help_text="OECD legalAddressType qualifier. Defaults to 'registeredOffice' for FIs.",
    )

    # ----- Contact ---------------------------------------------------------
    contact = models.TextField(
        blank=True,
        default="",
        help_text=(
            "Free-text contact details for the person at the FI handling CRS "
            "submissions (name, email, phone). Used to populate the Message "
            "Header's Contact element at XML generation time. Optional per spec."
        ),
    )

    # ----- Status ----------------------------------------------------------
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive FIs cannot be selected for new submissions.",
    )

    # ----- Audit timestamps ------------------------------------------------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Reporting Financial Institution"
        verbose_name_plural = "Reporting Financial Institutions"

    def __str__(self):
        status = "" if self.is_active else " (inactive)"
        return f"{self.name}{status}"


# ===========================================================================
# ReportingFIIN
# ===========================================================================
class ReportingFIIN(models.Model):
    """One Identification Number attached to a ReportingFI.

    Per the OECD spec (§IIIb), an Organisation may carry multiple INs —
    a local TIN plus a global GIIN is the common case. Each IN can
    optionally be tagged with the issuing country and a type label.
    """

    fi = models.ForeignKey(
        ReportingFI,
        on_delete=models.CASCADE,
        related_name="ins",
        help_text="The ReportingFI this IN belongs to.",
    )
    in_value = models.CharField(
        max_length=200,
        help_text="The identification number itself (max 200 chars per spec).",
    )
    issued_by = models.CharField(
        max_length=2,
        blank=True,
        default="",
        help_text="ISO 3166-1 alpha-2 country code of the issuing jurisdiction. Optional.",
    )
    in_type = models.CharField(
        max_length=20,
        choices=IN_TYPE_CHOICES,
        blank=True,
        default="",
        help_text="Type of identification number. Optional.",
    )

    # ----- Audit timestamps ------------------------------------------------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["in_type", "in_value"]
        unique_together = [("fi", "in_value")]
        verbose_name = "Reporting FI Identification Number"
        verbose_name_plural = "Reporting FI Identification Numbers"

    def __str__(self):
        prefix = f"{self.in_type}: " if self.in_type else ""
        suffix = f" ({self.issued_by})" if self.issued_by else ""
        return f"{prefix}{self.in_value}{suffix}"


# ===========================================================================
# Submission
# ===========================================================================
class Submission(models.Model):
    """A single CRS submission cycle for one (FI x Country x Year).

    Captures the Message Header data (§I of the OECD spec), references
    the selected ReportingFI and CountryConfiguration, holds the uploaded
    Excel in temporary storage during the draft phase, and stores the
    generated XML as the durable output artefact.

    Lifecycle states:
        draft   — Excel uploaded/replaceable; XML can be generated and
                  regenerated freely.
        closed  — User confirmed XML is final. Temp Excel and any parsing
                  artefacts are deleted; only the XML and metadata remain.
        submitted_externally — User-stamped after the XML has been filed
                  with the tax authority through the external channel.
        acknowledged / rejected — User-stamped terminal states.

    Customer account data (account holders, controlling persons, payments)
    is NEVER persisted as relational rows — it lives only in the transient
    Excel during draft and gets baked into the generated XML on closure.
    """

    # ===== Selection (set at draft creation) ===============================
    reporting_fi = models.ForeignKey(
        ReportingFI,
        on_delete=models.PROTECT,
        related_name="submissions",
        help_text="The FI on whose behalf this submission is filed.",
    )
    country_config = models.ForeignKey(
        CountryConfiguration,
        on_delete=models.PROTECT,
        related_name="submissions",
        help_text="The country whose reporting rules and templates apply.",
    )
    year = models.PositiveSmallIntegerField(
        help_text="Reporting year (e.g. 2025). ReportingPeriod is computed "
                  "as Dec 31 of this year.",
    )
    sending_company_in = models.CharField(
        max_length=200,
        help_text="Snapshot of the FI IN used as SendingCompanyIN in the "
                  "Message Header. Frozen at draft creation; not updated "
                  "if the FI's INs change later.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="crs_submissions",
        help_text="User who created this submission.",
    )

    # ===== Message Header (§I) =============================================
    transmitting_country = models.CharField(
        max_length=2,
        help_text="TransmittingCountry — ISO 3166-1 alpha-2. Defaults to "
                  "the FI's residence country at draft creation.",
    )
    receiving_country = models.CharField(
        max_length=2,
        help_text="ReceivingCountry — ISO 3166-1 alpha-2. For domestic "
                  "reporting (Cyprus FI → Cyprus tax authority), same as "
                  "TransmittingCountry.",
    )
    document_type = models.CharField(
        max_length=10,
        choices=DOC_TYPE_INDIC_CHOICES,
        default="OECD1",
        help_text="DocSpec DocTypeIndic. MVP uses OECD1 (new data).",
    )
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPE_INDIC_CHOICES,
        default="CRS701",
        help_text="MessageTypeIndic. MVP uses CRS701 (new information).",
    )
    message_ref_id = models.CharField(
        max_length=170,
        unique=True,
        help_text="MessageRefID — minted from the country config's template "
                  "at draft creation, immutable thereafter. Must be unique "
                  "in time and space per OECD spec.",
    )
    corr_message_ref_id = models.CharField(
        max_length=170,
        blank=True,
        default="",
        help_text="CorrMessageRefID — only used for CRS702 correction "
                  "messages. Empty for MVP (CRS701 only).",
    )
    warning = models.TextField(
        blank=True,
        default="",
        help_text="Optional free-text Warning element on the Message Header.",
    )

    # ===== Files ===========================================================
    uploaded_excel = models.FileField(
        upload_to=excel_upload_path,
        null=True, blank=True,
        help_text="Transient — uploaded customer data Excel. Deleted on "
                  "submission closure.",
    )


    # ===== Lifecycle =======================================================
    status = models.CharField(
        max_length=30,
        choices=SUBMISSION_STATUS_CHOICES,
        default="draft",
        help_text="Current lifecycle state.",
    )

    # ===== Audit / lifecycle timestamps ====================================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    xml_generated_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Set when XML is built; also used as the Message Header "
                  "Timestamp value in the XML.",
    )
    closed_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Set when the user closes the submission (temp data purged).",
    )
    submitted_externally_at = models.DateTimeField(
        null=True, blank=True,
        help_text="User-stamped after filing the XML with the tax authority.",
    )
    acknowledged_at = models.DateTimeField(
        null=True, blank=True,
        help_text="User-stamped after receiving acknowledgement/rejection.",
    )
    acknowledgement_notes = models.TextField(
        blank=True,
        default="",
        help_text="Notes captured after external submission (receipt details, "
                  "rejection reasons, reference numbers).",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Submission"
        verbose_name_plural = "Submissions"

    def __str__(self):
        fi = self.reporting_fi.name if self.reporting_fi_id else "—"
        cc = self.country_config.country_code if self.country_config_id else "??"
        return f"{cc} {self.year} — {fi} ({self.get_status_display()})"

    @property
    def reporting_period(self):
        """ReportingPeriod for the OECD Message Header — Dec 31 of self.year."""
        return date(self.year, 12, 31)


class SubmissionXMLFile(models.Model):
    """One generated CRS XML file belonging to a Submission.

    For combined_domestic submissions: exactly one row per submission,
    with receiving_country == submission's TransmittingCountry.

    For split_by_residence submissions: N rows per submission, one per
    distinct reportable receiving country produced by the slice enumeration.

    Lifecycle: created at XML generation; deleted at Close (per the data
    minimization policy — XML is purged when the submission moves to
    read-only state).
    """
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="xml_files",
    )
    receiving_country = models.CharField(
        max_length=2,
        help_text="ReceivingCountry ISO 3166-1 alpha-2 in this file's MessageSpec.",
    )
    file = models.FileField(
        upload_to=xml_file_path,
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    size = models.PositiveIntegerField(
        help_text="File size in bytes at generation time.",
    )
    account_count = models.PositiveIntegerField(
        help_text="Number of <AccountReport> elements in this file.",
    )

    class Meta:
        ordering = ["receiving_country"]
        unique_together = [("submission", "receiving_country")]
        verbose_name = "Submission XML file"
        verbose_name_plural = "Submission XML files"

    def __str__(self):
        return f"{self.submission} → {self.receiving_country}"