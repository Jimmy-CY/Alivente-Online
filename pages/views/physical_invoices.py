"""
Physical (VAT) invoice generation.

Preview / render endpoints:
  /physical-invoices/preview/              -> hard-coded Assetworth sample (PR-0169)
  /physical-invoices/preview/<tenant_id>/  -> live tenant + profile, upcoming month
                                              (optional ?period=YYYY-MM)
  /physical-invoices/<id>/pdf/             -> a STORED PhysicalInvoice (saved line rows
                                              + authoritative stored totals)

Reusable helpers (carry forward into the cron flow):
  build_invoice_context(...)        -> dict consumed by the template
  build_tenant_invoice_context(...) -> assembled from a tenant + profile (on the fly)
  build_context_from_invoice(...)   -> assembled from a stored PhysicalInvoice
  render_physical_invoice_pdf(...)  -> bytes (the rendered PDF)

PDF engine: xhtml2pdf (pisa), the same pure-Python stack used by pages/views/help.py.
"""

import io
import os
from datetime import date

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

from xhtml2pdf import pisa

from pages.models import tenant as Tenant
from pages.models import PhysicalInvoice

__all__ = [
    "render_invoice_preview",
    "render_invoice_for_tenant",
    "render_stored_invoice_pdf",
    "build_invoice_context",
    "build_tenant_invoice_context",
    "build_context_from_invoice",
    "render_physical_invoice_pdf",
]

TEMPLATE_NAME = "invoices/physical_invoice.html"

# Set to the static-relative path of the Alivente logo to show it (e.g. "images/alivente_logo.png").
LOGO_STATIC_PATH = "invoices/alivente_logo.png"

# Static for now — these move to a global settings record in a later phase.
VAT_RATE = 0.19
PREVIEW_INVOICE_NUMBER = "PR-####"   # numbering is a later phase; placeholder for layout

COMPANY = {
    "name": "Alivente Limited",
    "vat_number": "10283373R",
    "address_lines": ["Dikaiosynis 13A, Engomi", "Nicosia, Cyprus, 2412"],
    "phone": "+357 22222202",
    "website": "www.alivente.com",
}
BANK = {
    "payment_terms": "Payment Terms - SWIFT / Wire Transfer",
    "bank_name": "Hellenic Bank",
    "account_name": "Alivente Limited",
    "account_number": "109-01-856315-01",
    "iban": "CY11 0050 0109 0001 0901 8563 1501",
    "swift": "HEBACY2N",
}


def _money(value):
    return f"{float(value):,.2f}"


def _resolve_logo(static_path):
    if not static_path:
        return None
    return finders.find(static_path) or None


def _company_context():
    return {**COMPANY, "logo_path": _resolve_logo(LOGO_STATIC_PATH)}


def _qty_display(qty):
    """Show a whole-number quantity as an int (1, not 1.00); keep fractions as-is."""
    if qty is None:
        return 1
    try:
        if qty == qty.to_integral_value():
            return int(qty)
    except AttributeError:
        pass
    return qty


def build_invoice_context(*, company, invoice, customer, lines, bank,
                          vat_rate, currency="EUR", currency_symbol="\u20ac"):
    """Assemble the template context. VAT is charged only on vatable lines."""
    prepared = []
    subtotal = 0.0
    vatable_base = 0.0
    for ln in lines:
        line_total = float(ln["unit_price"]) * float(ln.get("qty", 1))
        subtotal += line_total
        if ln.get("vatable"):
            vatable_base += line_total
        prepared.append({
            "service": ln["service"],
            "uom": ln["uom"],
            "description": ln["description"],
            "qty": ln.get("qty", 1),
            "unit_price_display": _money(ln["unit_price"]),
            "total_display": _money(line_total),
        })

    vat = vatable_base * vat_rate
    total = subtotal + vat

    return {
        "currency_symbol": currency_symbol,
        "company": company,
        "invoice": invoice,
        "customer": customer,
        "lines": prepared,
        "bank": bank,
        "totals": {
            "subtotal_display": _money(subtotal),
            "vat_rate_display": f"{vat_rate * 100:.2f}%",
            "vat_display": _money(vat),
            "total_display": _money(total),
            "currency": currency,
        },
    }


def _upcoming_period(today=None):
    """First day of next month relative to `today` (handles Dec -> Jan)."""
    today = today or date.today()
    if today.month == 12:
        return date(today.year + 1, 1, 1)
    return date(today.year, today.month + 1, 1)


def _get_profile(tenant_obj):
    try:
        return tenant_obj.physical_invoice_profile
    except ObjectDoesNotExist:
        return None


def _first_nonblank(*values):
    for v in values:
        if v and str(v).strip():
            return str(v).strip()
    return ""


def _billing_block(tenant_obj):
    """Customer dict + customer-ID, from the profile falling back to tenant fields."""
    profile = _get_profile(tenant_obj)
    name = _first_nonblank(getattr(profile, "billing_name", ""), tenant_obj.tenant_name)
    customer_id = _first_nonblank(getattr(profile, "customer_id_label", ""), tenant_obj.tenant_name)
    tel = _first_nonblank(getattr(profile, "billing_tel", ""), tenant_obj.tenant_contact_number)
    address_raw = (getattr(profile, "billing_address", "") or "").strip()
    address_lines = [ln.strip() for ln in address_raw.splitlines() if ln.strip()]
    return {"name": name, "address_lines": address_lines, "tel": tel}, customer_id


def build_tenant_invoice_context(tenant_obj, period_first=None):
    """
    Build the invoice context on the fly from a live tenant + its profile.

      - rent      <- tenant.tenant_rent (always)
      - communal  <- tenant.tenant_levies, only when tenant.tenant_bill_levies is on
      - billing   <- the profile, falling back to tenant fields where blank
      - month     <- the UPCOMING month (period_first), e.g. "Rent for July 2026"
    """
    period_first = period_first or _upcoming_period()
    month_label = period_first.strftime("%B %Y")
    customer, customer_id = _billing_block(tenant_obj)

    lines = [{
        "service": "RENTAL", "uom": "MONTH",
        "description": f"Rent for {month_label}",
        "qty": 1, "unit_price": tenant_obj.tenant_rent or 0, "vatable": True,
    }]
    if getattr(tenant_obj, "tenant_bill_levies", False) and (tenant_obj.tenant_levies or 0):
        lines.append({
            "service": "COMM", "uom": "MONTH",
            "description": "Communal Fees",
            "qty": 1, "unit_price": tenant_obj.tenant_levies, "vatable": False,
        })

    return build_invoice_context(
        company=_company_context(),
        invoice={
            "number": PREVIEW_INVOICE_NUMBER,
            "date_display": period_first.strftime("%d.%m.%Y"),
            "customer_id": customer_id,
        },
        customer=customer,
        lines=lines,
        bank=BANK,
        vat_rate=VAT_RATE,
    )


def build_context_from_invoice(physical_invoice):
    """
    Build the invoice context from a STORED PhysicalInvoice.

    Line items come from the saved PhysicalInvoiceLine rows; the billing block
    from the tenant's profile (same fallback as the live render); the number
    and date from the invoice itself. Totals are taken from the stored record
    (the authoritative, frozen figures) rather than recomputed.
    """
    pi = physical_invoice
    customer, customer_id = _billing_block(pi.tenant)

    line_dicts = [{
        "service": ln.service,
        "uom": ln.unit_of_measure,
        "description": ln.description,
        "qty": _qty_display(ln.qty),
        "unit_price": ln.unit_price,
        "vatable": ln.vatable,
    } for ln in pi.lines.all()]

    context = build_invoice_context(
        company=_company_context(),
        invoice={
            "number": pi.invoice_number or "DRAFT",
            "date_display": pi.invoice_date.strftime("%d.%m.%Y") if pi.invoice_date else "",
            "customer_id": customer_id,
        },
        customer=customer,
        lines=line_dicts,
        bank=BANK,
        vat_rate=float(pi.vat_rate),
        currency=pi.currency or "EUR",
    )
    # Authoritative totals from the stored record (frozen at approve/send).
    context["totals"]["subtotal_display"] = _money(pi.subtotal)
    context["totals"]["vat_display"] = _money(pi.vat)
    context["totals"]["total_display"] = _money(pi.total)
    return context


def _link_callback(uri, rel):
    if uri.startswith(("http://", "https://", "data:")):
        return uri
    s_url = getattr(settings, "STATIC_URL", "") or ""
    s_root = getattr(settings, "STATIC_ROOT", "") or ""
    m_url = getattr(settings, "MEDIA_URL", "") or ""
    m_root = getattr(settings, "MEDIA_ROOT", "") or ""
    if s_url and uri.startswith(s_url):
        rel_path = uri[len(s_url):]
        path = os.path.join(s_root, rel_path) if s_root else ""
        if not path or not os.path.isfile(path):
            path = finders.find(rel_path) or path
        return path
    if m_url and uri.startswith(m_url):
        return os.path.join(m_root, uri[len(m_url):])
    return uri


def render_physical_invoice_pdf(context):
    """Render the invoice template + context to PDF bytes via xhtml2pdf."""
    html = render_to_string(TEMPLATE_NAME, context)
    buffer = io.BytesIO()
    result = pisa.CreatePDF(src=html, dest=buffer, encoding="utf-8", link_callback=_link_callback)
    if result.err:
        raise RuntimeError("xhtml2pdf failed to render the physical invoice")
    return buffer.getvalue()


def _sample_context():
    return build_invoice_context(
        company=_company_context(),
        invoice={"number": "PR-0169", "date_display": "01.06.2026", "customer_id": "Assetworth LTD"},
        customer={
            "name": "ASSETWORTH LTD",
            "address_lines": ["Eleftheroupoleos 6", "Oriana Court, Flat 16", "2001, Strovolos, Nicosia, Cyprus"],
            "tel": "+357 99343298",
        },
        lines=[
            {"service": "RENTAL", "uom": "MONTH", "description": "Rent for June 2026",
             "qty": 1, "unit_price": 1085.00, "vatable": True},
            {"service": "COMM", "uom": "MONTH", "description": "Communal Fees",
             "qty": 1, "unit_price": 35.00, "vatable": False},
        ],
        bank=BANK,
        vat_rate=VAT_RATE,
    )


def _parse_period_param(request):
    """Optional ?period=YYYY-MM override; defaults to the upcoming month."""
    raw = (request.GET.get("period") or "").strip()
    if raw:
        try:
            y, m = raw.split("-")
            return date(int(y), int(m), 1)
        except (ValueError, TypeError):
            pass
    return _upcoming_period()


@login_required
def render_invoice_preview(request):
    """Preview the layout from the hard-coded Assetworth sample."""
    pdf_bytes = render_physical_invoice_pdf(_sample_context())
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="physical_invoice_preview.pdf"'
    return response


@login_required
def render_invoice_for_tenant(request, tenant_id):
    """Preview a real tenant's invoice for the upcoming month (or ?period=YYYY-MM)."""
    tenant_obj = get_object_or_404(Tenant, pk=tenant_id)
    context = build_tenant_invoice_context(tenant_obj, _parse_period_param(request))
    pdf_bytes = render_physical_invoice_pdf(context)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="invoice_preview_tenant_{tenant_id}.pdf"'
    return response


@login_required
def render_stored_invoice_pdf(request, physical_invoice_id):
    """Render a stored PhysicalInvoice (saved lines + frozen totals) to PDF."""
    pi = get_object_or_404(PhysicalInvoice, pk=physical_invoice_id)
    context = build_context_from_invoice(pi)
    pdf_bytes = render_physical_invoice_pdf(context)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    fname = (pi.invoice_number or f"draft-{pi.pk}").replace(" ", "_")
    response["Content-Disposition"] = f'inline; filename="invoice_{fname}.pdf"'
    return response