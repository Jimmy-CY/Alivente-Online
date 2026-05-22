"""
crs.forms — Forms for the CRS module.

CountryConfigurationForm    — Add/Edit for Country Configurations.
ReportingFIForm + FormSet   — Add/Edit for Reporting FIs.
SubmissionStartForm         — Create a new draft Submission.
SubmissionHeaderForm        — Edit Message Header fields on a draft.
SubmissionExcelUploadForm   — Upload (or replace) the customer-data Excel.
"""
from django import forms
from django.forms import inlineformset_factory

from crs.models import (
    CountryConfiguration,
    ReportingFI,
    ReportingFIIN,
    Submission,
)


_INPUT     = {"class": "form-control"}
_INPUT_2CH = {"class": "form-control", "maxlength": "2",
              "style": "text-transform: uppercase;"}
_INPUT_3CH = {"class": "form-control", "maxlength": "3",
              "style": "text-transform: uppercase;"}


# ---------------------------------------------------------------------------
# CountryConfiguration
# ---------------------------------------------------------------------------
class CountryConfigurationForm(forms.ModelForm):
    class Meta:
        model = CountryConfiguration
        fields = [
            "country_code", "country_name", "is_active",
            "oecd_version", "receiving_country_strategy",
            "default_currency", "tin_regex",
            "message_ref_id_template", "fi_doc_ref_id_template",
            "account_doc_ref_id_template", "output_filename_template",
        ]
        widgets = {
            "country_code":               forms.TextInput(attrs={**_INPUT_2CH, "placeholder": "e.g. CY"}),
            "country_name":               forms.TextInput(attrs={**_INPUT, "placeholder": "e.g. Cyprus"}),
            "is_active":                  forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "oecd_version":               forms.TextInput(attrs={**_INPUT, "placeholder": "e.g. 2.0"}),
            "receiving_country_strategy": forms.Select(attrs=_INPUT),
            "default_currency":           forms.TextInput(attrs={**_INPUT_3CH, "placeholder": "e.g. EUR"}),
            "tin_regex":                  forms.TextInput(attrs={**_INPUT, "placeholder": "Optional"}),
            "message_ref_id_template":     forms.TextInput(attrs=_INPUT),
            "fi_doc_ref_id_template":      forms.TextInput(attrs=_INPUT),
            "account_doc_ref_id_template": forms.TextInput(attrs=_INPUT),
            "output_filename_template":    forms.TextInput(attrs=_INPUT),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["country_code"].disabled = True
            self.fields["country_code"].help_text = (
                "Country code cannot be changed after creation."
            )

    def clean_country_code(self):
        value = self.cleaned_data.get("country_code", "")
        if self.instance and self.instance.pk:
            return self.instance.country_code
        return value.upper().strip()

    def clean_default_currency(self):
        return self.cleaned_data.get("default_currency", "").upper().strip()


# ---------------------------------------------------------------------------
# ReportingFI + ReportingFIIN
# ---------------------------------------------------------------------------
class ReportingFIForm(forms.ModelForm):
    class Meta:
        model = ReportingFI
        fields = [
            "name", "name_type",
            "res_country_code",
            "address_country_code", "address_type", "address_free",
            "contact",
            "is_active",
        ]
        widgets = {
            "name":                 forms.TextInput(attrs={**_INPUT, "placeholder": "Legal name of the FI"}),
            "name_type":            forms.Select(attrs=_INPUT),
            "res_country_code":     forms.TextInput(attrs={**_INPUT_2CH, "placeholder": "e.g. CY"}),
            "address_country_code": forms.TextInput(attrs={**_INPUT_2CH, "placeholder": "e.g. CY"}),
            "address_type":         forms.Select(attrs=_INPUT),
            "address_free":         forms.Textarea(attrs={**_INPUT, "rows": 3,
                                                          "placeholder": "Full address, free-text"}),
            "contact":              forms.Textarea(attrs={**_INPUT, "rows": 2,
                                                          "placeholder": "Name, email, phone of CRS contact (optional)"}),
            "is_active":            forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_res_country_code(self):
        return self.cleaned_data.get("res_country_code", "").upper().strip()

    def clean_address_country_code(self):
        return self.cleaned_data.get("address_country_code", "").upper().strip()


class ReportingFIINForm(forms.ModelForm):
    class Meta:
        model = ReportingFIIN
        fields = ["in_type", "in_value", "issued_by"]
        widgets = {
            "in_type":   forms.Select(attrs=_INPUT),
            "in_value":  forms.TextInput(attrs={**_INPUT, "placeholder": "IN value"}),
            "issued_by": forms.TextInput(attrs={**_INPUT_2CH, "placeholder": "e.g. CY"}),
        }

    def clean_issued_by(self):
        return self.cleaned_data.get("issued_by", "").upper().strip()


ReportingFIINFormSet = inlineformset_factory(
    ReportingFI,
    ReportingFIIN,
    form=ReportingFIINForm,
    extra=1,
    can_delete=True,
)


# ---------------------------------------------------------------------------
# Submission — start
# ---------------------------------------------------------------------------
class SubmissionStartForm(forms.Form):
    """Create a draft Submission. The IN dropdown is populated client-side
    based on the selected FI's TINs; server-side validation here ensures
    the submitted IN value is in fact one of that FI's registered TINs."""

    reporting_fi = forms.ModelChoiceField(
        queryset=ReportingFI.objects.filter(is_active=True).order_by("name"),
        widget=forms.Select(attrs={**_INPUT, "id": "id_fi"}),
        empty_label="— Select FI —",
        label="Reporting FI",
    )
    country_config = forms.ModelChoiceField(
        queryset=CountryConfiguration.objects.filter(is_active=True).order_by("country_code"),
        widget=forms.Select(attrs=_INPUT),
        empty_label="— Select Country —",
        label="Country",
    )
    year = forms.IntegerField(
        min_value=2014, max_value=2099,
        label="Reporting Year",
    )
    sending_company_in = forms.CharField(
        max_length=200,
        widget=forms.Select(attrs={**_INPUT, "id": "id_sending_in"}),
        label="Sending Company IN (TIN)",
    )

    def clean(self):
        cleaned = super().clean()
        fi = cleaned.get("reporting_fi")
        in_value = cleaned.get("sending_company_in")
        if fi and in_value:
            valid_tins = list(
                fi.ins.filter(in_type="TIN").values_list("in_value", flat=True)
            )
            if not valid_tins:
                raise forms.ValidationError(
                    f"FI '{fi.name}' has no TIN registered. CRS requires a TIN — "
                    f"please add one to the FI before starting a submission."
                )
            if in_value not in valid_tins:
                raise forms.ValidationError(
                    "Selected IN is not a registered TIN of the chosen FI."
                )
        return cleaned


# ---------------------------------------------------------------------------
# Submission — edit Message Header
# ---------------------------------------------------------------------------
class _SelectWithDisabledChoices(forms.Select):
    """Select widget that renders specific option values with `disabled=disabled`
    so they appear in the dropdown (greyed-out, not clickable) but cannot be
    submitted. Used to keep future-MVP options visible in the UI while limiting
    selectable values to what the current iteration supports."""

    def __init__(self, *args, disabled_values=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.disabled_values = set(disabled_values)

    def create_option(self, name, value, label, selected, index,
                      subindex=None, attrs=None):
        option = super().create_option(
            name, value, label, selected, index,
            subindex=subindex, attrs=attrs,
        )
        if str(value) in self.disabled_values:
            option["attrs"]["disabled"] = "disabled"
        return option


class SubmissionHeaderForm(forms.ModelForm):
    """Editable Message Header fields. message_ref_id is intentionally
    excluded — it's minted at draft creation and immutable per spec."""

    class Meta:
        model = Submission
        # NOTE: `warning` is intentionally omitted from the UI for now. The
        # model field remains on Submission so the XML generator can still
        # emit a <Warning> element if a value is set programmatically; it's
        # just not editable from this form.
        fields = [
            "transmitting_country",
            "receiving_country",
            "document_type",
            "message_type",
            "corr_message_ref_id",
        ]
        widgets = {
            "transmitting_country": forms.TextInput(attrs=_INPUT_2CH),
            "receiving_country":    forms.TextInput(attrs=_INPUT_2CH),
            # MVP supports only OECD1; OECD0/2/3 are shown greyed-out to signal
            # they exist in the spec but aren't selectable in this iteration.
            "document_type":        _SelectWithDisabledChoices(
                                        attrs=_INPUT,
                                        disabled_values=["OECD0", "OECD2", "OECD3"]),
            # MVP supports only CRS701; CRS702/703 shown greyed-out for the
            # same reason.
            "message_type":         _SelectWithDisabledChoices(
                                        attrs=_INPUT,
                                        disabled_values=["CRS702", "CRS703"]),
            "corr_message_ref_id":  forms.TextInput(attrs={**_INPUT,
                                                           "placeholder": "Only used for CRS702 corrections — leave empty for CRS701"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Transmitting Country is always the FI's residence country (set at
        # draft creation in submission_start). Lock it from edits.
        self.fields["transmitting_country"].disabled = True

        # Receiving Country behavior follows the country's filing strategy:
        #   combined_domestic → mirrors Transmitting, locked but visible.
        #   split_by_residence → removed entirely; XML generator sets RC per
        #     file based on each account holder's tax residence.
        strategy = "combined_domestic"
        if self.instance and self.instance.country_config_id:
            strategy = self.instance.country_config.receiving_country_strategy

        if strategy == "split_by_residence":
            del self.fields["receiving_country"]
        else:
            self.fields["receiving_country"].disabled = True

    def clean_transmitting_country(self):
        return self.cleaned_data.get("transmitting_country", "").upper().strip()

    def clean_receiving_country(self):
        return self.cleaned_data.get("receiving_country", "").upper().strip()


# ---------------------------------------------------------------------------
# Submission — Excel upload
# ---------------------------------------------------------------------------
class SubmissionExcelUploadForm(forms.ModelForm):
    """Upload the customer-data Excel file. Validated for type + size."""

    MAX_BYTES = 25 * 1024 * 1024  # 25 MB

    class Meta:
        model = Submission
        fields = ["uploaded_excel"]
        widgets = {
            "uploaded_excel": forms.FileInput(attrs={
                "class": "form-control-file",
                "accept": ".xlsx,.xls",
            }),
        }

    def clean_uploaded_excel(self):
        f = self.cleaned_data.get("uploaded_excel")
        if f and hasattr(f, "name"):
            if not f.name.lower().endswith((".xlsx", ".xls")):
                raise forms.ValidationError("File must be a .xlsx or .xls spreadsheet.")
            if f.size > self.MAX_BYTES:
                raise forms.ValidationError(
                    f"File too large ({f.size // (1024*1024)} MB) — max 25 MB."
                )
        return f