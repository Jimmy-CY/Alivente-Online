"""
crs.services.normalize - Atomic field normalization for the Excel parser.

Each normalize_* function follows the same contract:

    Returns (value, error, correction):
        value      - the normalized value (None if missing or unparseable)
        error      - error message string if invalid, else None
        correction - human-readable note if the value was auto-corrected,
                     else None

The parser uses these to extract one cell at a time, log corrections
silently, and surface errors with sheet/row/column context.

Cleaning policy has two tiers:
  - Default fields (TINs, account numbers, codes): minimal cleanup - only
    remove characters that would make the XML invalid (XML 1.0 control
    characters, surrogates, noncharacters). Accents and punctuation kept.
  - Name / address fields (restrict_charset=True): additionally transliterate
    accents and special Latin letters to ASCII, drop anything outside
    [A-Za-z0-9 plus space ' . , / - ( ) #], and collapse repeated spaces.

Amounts are coerced to whole-number Decimals: thousand separators stripped,
negatives clamped to zero (CRS forbids negative amounts), value rounded to
the nearest integer (CRS reports whole currency units).
"""
import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from crs.services import reference_data as ref


# XML 1.0 forbids most control characters (except tab 0x09, LF 0x0A, CR 0x0D),
# surrogate code points (0xD800-0xDFFF), and the two noncharacters
# (0xFFFE, 0xFFFF). Anything matched here gets stripped.
_XML_INVALID_RE = re.compile(
    "[\x00-\x08\x0B\x0C\x0E-\x1F\uD800-\uDFFF\uFFFE\uFFFF]"
)

# Restricted set for names/addresses: alphanumeric plus space, apostrophe,
# period, comma, slash, hyphen, parentheses, hash. Accents are transliterated
# to base Latin (via the map below + NFKD) first; anything still outside this
# set is removed.
_ALLOWED_RESTRICTED_RE = re.compile(r"[^A-Za-z0-9 #()'.,/\-]")

# Non-decomposing Latin letters and common typographic characters mapped to
# ASCII. Applied before NFKD accent-stripping; anything still outside the
# allowed set after this is dropped. \u escapes keep this source pure-ASCII.
_TRANSLITERATE = {
    "\u00f8": "o",  "\u00d8": "O",    # o with stroke (lower / upper)
    "\u00df": "ss",                    # eszett / sharp s
    "\u00e6": "ae", "\u00c6": "AE",   # ae ligature
    "\u0153": "oe", "\u0152": "OE",   # oe ligature
    "\u0142": "l",  "\u0141": "L",    # l with stroke
    "\u0111": "d",  "\u0110": "D",    # d with stroke
    "\u00f0": "d",  "\u00d0": "D",    # eth
    "\u00fe": "th", "\u00de": "TH",   # thorn
    "\u0131": "i",  "\u0130": "I",    # dotless i / dotted I
    "\u2018": "'",  "\u2019": "'",    # smart single quotes
    "\u201c": "",   "\u201d": "",     # smart double quotes (dropped)
    "\u2013": "-",  "\u2014": "-",    # en dash / em dash
    "\u2026": "...",                   # ellipsis
}

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
# String - minimal cleanup, or restricted charset for names/addresses
# ---------------------------------------------------------------------------
def normalize_string(raw, max_length=200, restrict_charset=False):
    """Strip XML-invalid chars, trim, length-check. When restrict_charset is
    True (names + addresses), transliterate special Latin letters and
    typographic characters to ASCII, strip remaining accents via NFKD, drop
    anything still outside [A-Za-z0-9 plus space ' . , / - ( ) #], and
    collapse repeated spaces left behind by removed characters."""
    if _is_blank(raw):
        return None, None, None

    s = str(raw)
    corrections = []

    work = _XML_INVALID_RE.sub("", s)
    if work != s:
        corrections.append("removed XML-invalid characters")

    if restrict_charset:
        mapped = "".join(_TRANSLITERATE.get(c, c) for c in work)
        decomposed = unicodedata.normalize("NFKD", mapped)
        no_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
        # Turn any surviving whitespace (newlines, tabs) into spaces so word
        # boundaries survive the character filter, drop disallowed chars, then
        # collapse runs of spaces left behind by removed characters.
        spaced = re.sub(r"\s", " ", no_accents)
        filtered = _ALLOWED_RESTRICTED_RE.sub("", spaced)
        collapsed = re.sub(r" {2,}", " ", filtered)
        if collapsed != work:
            corrections.append("normalized accents / removed disallowed characters")
        work = collapsed

    trimmed = work.strip()
    if trimmed != work and not corrections:
        corrections.append("trimmed whitespace")

    if not trimmed:
        return None, None, None

    if len(trimmed) > max_length:
        return trimmed, f"value exceeds max length of {max_length} characters (got {len(trimmed)})", None

    return trimmed, None, ("; ".join(corrections) if corrections else None)


# ---------------------------------------------------------------------------
# Amount - strip thousand separators, clamp negatives to zero, round to integer
# ---------------------------------------------------------------------------
def normalize_amount(raw):
    """Parse to a whole-number Decimal. Strips thousand separators, clamps
    negatives to zero (CRS forbids negative amounts), and rounds to the
    nearest integer (CRS reports whole currency units)."""
    if _is_blank(raw):
        return None, None, None

    corrections = []

    if isinstance(raw, bool):
        # bool is a subclass of int - reject explicitly to avoid TRUE->1
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

    if d < 0:
        d = Decimal("0")
        corrections.append("negative amount set to zero")

    rounded = d.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    if rounded != d:
        corrections.append("rounded to whole number")

    return rounded, None, ("; ".join(corrections) if corrections else None)


# ---------------------------------------------------------------------------
# Date - to ISO YYYY-MM-DD
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
# Country code - ISO 3166-1 alpha-2
# ---------------------------------------------------------------------------
def normalize_country(raw):
    """Normalize and validate against the Countries list."""
    if _is_blank(raw):
        return None, None, None

    s_raw = str(raw)
    s = s_raw.strip().upper()
    correction = "uppercased / trimmed" if s != s_raw else None

    if s not in ref.COUNTRIES:
        return None, f"'{raw}' is not a valid ISO 3166-1 alpha-2 country code", None
    return s, None, correction


# ---------------------------------------------------------------------------
# Currency code - ISO 4217
# ---------------------------------------------------------------------------
def normalize_currency(raw):
    """Normalize and validate against the Currencies list."""
    if _is_blank(raw):
        return None, None, None

    s_raw = str(raw)
    s = s_raw.strip().upper()
    correction = "uppercased / trimmed" if s != s_raw else None

    if s not in ref.CURRENCIES:
        return None, f"'{raw}' is not a valid ISO 4217 currency code", None
    return s, None, correction


# ---------------------------------------------------------------------------
# Boolean - TRUE / FALSE -> Python bool
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
# Generic picklist - for Account Type / IN Type / Holder Type / CP Type
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