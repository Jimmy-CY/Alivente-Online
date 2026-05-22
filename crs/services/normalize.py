"""
crs.services.normalize — Atomic field normalization for the Excel parser.

Each normalize_* function follows the same contract:

    Returns (value, error, correction):
        value      — the normalized value (None if missing or unparseable)
        error      — error message string if invalid, else None
        correction — human-readable note if the value was auto-corrected,
                     else None

The parser uses these to extract one cell at a time, log corrections
silently, and surface errors with sheet/row/column context.

Cleaning policy is intentionally minimal per the agreed rule: only remove
characters that would actually cause the OECD XML schema to reject the
upload (XML 1.0 invalid control characters, surrogates, noncharacters).
Smart quotes, em-dashes, accented letters, hyphens, apostrophes are all
preserved — they're valid xsd:string content.
"""
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_DOWN

from crs.services import reference_data as ref


# XML 1.0 forbids most control characters (except tab 0x09, LF 0x0A, CR 0x0D),
# surrogate code points (0xD800-0xDFFF), and the two noncharacters
# (0xFFFE, 0xFFFF). Anything matched here gets stripped.
_XML_INVALID_RE = re.compile(
    "[\x00-\x08\x0B\x0C\x0E-\x1F\uD800-\uDFFF\uFFFE\uFFFF]"
)

_DATE_FORMATS = [
    ("%Y-%m-%d", "YYYY-MM-DD"),
    ("%d/%m/%Y", "DD/MM/YYYY"),
    ("%d-%m-%Y", "DD-MM-YYYY"),
    ("%d.%m.%Y", "DD.MM.YYYY"),
    ("%Y/%m/%d", "YYYY/MM/DD"),
]


def _is_blank(raw):
    """True if raw is None or whitespace-only string."""
    return raw is None or (isinstance(raw, str) and not raw.strip())


# ---------------------------------------------------------------------------
# String — minimal cleanup, schema-compliance only
# ---------------------------------------------------------------------------
def normalize_string(raw, max_length=200):
    """Strip XML-invalid chars, trim ends, length-check."""
    if _is_blank(raw):
        return None, None, None

    s = str(raw)
    stripped_invalid = _XML_INVALID_RE.sub("", s)
    trimmed = stripped_invalid.strip()

    if not trimmed:
        return None, None, None

    correction = None
    if stripped_invalid != s:
        correction = "removed XML-invalid characters"
    elif trimmed != s:
        correction = "trimmed whitespace"

    if len(trimmed) > max_length:
        return trimmed, f"value exceeds max length of {max_length} characters (got {len(trimmed)})", None

    return trimmed, None, correction


# ---------------------------------------------------------------------------
# Amount — strip thousand separators, truncate to 2dp
# ---------------------------------------------------------------------------
def normalize_amount(raw):
    """Parse to Decimal with exactly 2 fractional digits (truncated)."""
    if _is_blank(raw):
        return None, None, None

    corrections = []

    if isinstance(raw, bool):
        # bool is a subclass of int — reject explicitly to avoid TRUE→1.00
        return None, f"'{raw}' is not a valid amount (boolean given)", None

    if isinstance(raw, (int, float, Decimal)):
        try:
            d = Decimal(str(raw))
        except InvalidOperation:
            return None, f"could not parse '{raw}' as a number", None
    else:
        s = str(raw).strip()
        original = s
        # Strip common thousand separators: comma, apostrophe, NBSP, regular space
        cleaned = s.replace(",", "").replace("'", "").replace("\u00A0", "").replace(" ", "")
        try:
            d = Decimal(cleaned)
        except InvalidOperation:
            return None, f"could not parse '{raw}' as a number", None
        if cleaned != original:
            corrections.append("removed thousand separators")

    # Truncate (not round) to 2 decimal places
    quantized = d.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    if quantized != d:
        corrections.append("truncated to 2 decimal places")

    correction = "; ".join(corrections) if corrections else None
    return quantized, None, correction


# ---------------------------------------------------------------------------
# Date — to ISO YYYY-MM-DD
# ---------------------------------------------------------------------------
def normalize_date(raw):
    """Parse to ISO YYYY-MM-DD string (the xsd:date format)."""
    if _is_blank(raw):
        return None, None, None

    # openpyxl returns datetime for date-typed cells
    if isinstance(raw, datetime):
        return raw.date().isoformat(), None, None
    if isinstance(raw, date):
        return raw.isoformat(), None, None

    s = str(raw).strip()

    for fmt, label in _DATE_FORMATS:
        try:
            parsed = datetime.strptime(s, fmt).date()
        except ValueError:
            continue
        iso = parsed.isoformat()
        if label != "YYYY-MM-DD":
            return iso, None, f"reformatted from {label} to YYYY-MM-DD"
        return iso, None, None

    tried = ", ".join(label for _, label in _DATE_FORMATS)
    return None, f"could not parse '{raw}' as a date (tried: {tried})", None


# ---------------------------------------------------------------------------
# Country code — ISO 3166-1 alpha-2
# ---------------------------------------------------------------------------
def normalize_country(raw):
    """Normalize and validate against the 249-code Countries list."""
    if _is_blank(raw):
        return None, None, None

    s_raw = str(raw)
    s = s_raw.strip().upper()
    correction = "uppercased / trimmed" if s != s_raw else None

    if s not in ref.COUNTRIES:
        return None, f"'{raw}' is not a valid ISO 3166-1 alpha-2 country code", None
    return s, None, correction


# ---------------------------------------------------------------------------
# Currency code — ISO 4217
# ---------------------------------------------------------------------------
def normalize_currency(raw):
    """Normalize and validate against the 178-code Currencies list."""
    if _is_blank(raw):
        return None, None, None

    s_raw = str(raw)
    s = s_raw.strip().upper()
    correction = "uppercased / trimmed" if s != s_raw else None

    if s not in ref.CURRENCIES:
        return None, f"'{raw}' is not a valid ISO 4217 currency code", None
    return s, None, correction


# ---------------------------------------------------------------------------
# Boolean — TRUE / FALSE → Python bool
# ---------------------------------------------------------------------------
def normalize_boolean(raw):
    """Parse TRUE/FALSE (case-insensitive) to a Python bool."""
    if _is_blank(raw):
        return None, None, None

    if isinstance(raw, bool):
        return raw, None, None

    s_raw = str(raw)
    s = s_raw.strip().upper()
    correction = "normalized whitespace/case" if s != s_raw else None

    if s in ("TRUE", "1", "Y", "YES"):
        return True, None, correction
    if s in ("FALSE", "0", "N", "NO"):
        return False, None, correction

    return None, f"'{raw}' is not a valid boolean (expected TRUE or FALSE)", None


# ---------------------------------------------------------------------------
# Generic picklist — for Account Type / IN Type / Holder Type / CP Type
# ---------------------------------------------------------------------------
def normalize_choice(raw, valid_set, label):
    """Trim and validate against an allowed set. Case-sensitive match
    (the Excel picklists are case-specific: 'IBAN' not 'iban', 'CRS101' not 'crs101')."""
    if _is_blank(raw):
        return None, None, None

    s_raw = str(raw)
    s = s_raw.strip()
    correction = "trimmed whitespace" if s != s_raw else None

    if s not in valid_set:
        allowed = ", ".join(sorted(valid_set))
        return None, f"'{raw}' is not a valid {label} (allowed: {allowed})", None
    return s, None, correction